"""
main.py — LexScout FastAPI Application
=======================================
Single endpoint:  POST /query
Health endpoints: GET /  |  GET /health
Meta endpoint:    GET /supported

Run locally:
    uvicorn main:app --reload --port 8000

Production (Railway / Render):
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Load .env before importing agents (agents.py reads GEMINI_API_KEY on import)
load_dotenv()

# ─────────────────────────────── Logging ──────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("lexscout.main")

# ─────────────────────────────── Agent import ─────────────────────────────
# Deferred to after load_dotenv() so GEMINI_API_KEY is available
from agents import LexScoutState, lexscout_graph  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════
#  APPLICATION LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║   LexScout API  —  starting up           ║")
    logger.info("╚══════════════════════════════════════════╝")
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("⚠  GEMINI_API_KEY not set — requests will fail.")
    yield
    logger.info("LexScout API shutting down — goodbye.")


# ═══════════════════════════════════════════════════════════════════════════
#  APP FACTORY
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="LexScout — Legal Action Intelligence API",
    description=(
        "5-agent LangGraph pipeline powered by Gemini 1.5 Flash + Bright Data.\n\n"
        "Converts a plain-language legal situation into:\n"
        "- Relevant laws & articles\n"
        "- Recent case precedents\n"
        "- Draft complaint letter (exact citations)\n"
        "- Complaint portal URL\n"
        "- Nearby legal aid contacts\n"
        "- 5-step action plan\n\n"
        "Supported jurisdictions: **India · USA · EU**  \n"
        "Supported categories: **Privacy · Employment · Consumer Rights · IP · Criminal**"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Allow all origins — tighten in production if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
#  PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=15,
        max_length=2000,
        description="Plain-language description of the legal situation.",
        examples=[
            "My employer deducted salary without any prior notice and refuses "
            "to give a reason. I have been working in Bangalore for 3 years.",
            "A website collected my personal data without consent and sold it "
            "to third parties. I am based in Germany.",
        ],
    )
    country: str = Field(
        default="India",
        description="Primary jurisdiction hint. Accepted: 'India', 'USA', 'EU'.",
        examples=["India", "USA", "EU"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": (
                    "My employer deducted 15% of my salary without notice and "
                    "denied me access to my employment contract. I work in Mumbai."
                ),
                "country": "India",
            }
        }
    }


class HealthResponse(BaseModel):
    status: str
    version: str
    agents: int
    gemini_key_set: bool


class SupportedResponse(BaseModel):
    jurisdictions: list
    categories: list
    law_databases: list
    case_databases: list


# ═══════════════════════════════════════════════════════════════════════════
#  HELPER — VALIDATE COUNTRY
# ═══════════════════════════════════════════════════════════════════════════

_SUPPORTED_COUNTRIES = {"India", "USA", "EU"}


def _validate_country(country: str) -> str:
    """
    Returns the country if it is in the supported set, otherwise returns 'India'.
    Logs a warning on fallback so the caller can be aware.
    """
    if country in _SUPPORTED_COUNTRIES:
        return country
    logger.warning(
        "Country %r not in supported set %s — defaulting to 'India'.",
        country,
        _SUPPORTED_COUNTRIES,
    )
    return "India"


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════


@app.get(
    "/",
    response_model=HealthResponse,
    summary="Root health check",
    tags=["Health"],
)
async def root() -> Dict[str, Any]:
    return {
        "status": "online",
        "version": "1.0.0",
        "agents": 5,
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["Health"],
)
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agents": 5,
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
    }


@app.get(
    "/supported",
    response_model=SupportedResponse,
    summary="Supported jurisdictions, categories, and data sources",
    tags=["Meta"],
)
async def supported() -> Dict[str, Any]:
    return {
        "jurisdictions": ["India", "USA", "EU"],
        "categories":    ["Privacy", "Employment", "Consumer Rights", "IP", "Criminal"],
        "law_databases": [
            "indiacode.nic.in  (India)",
            "law.cornell.edu   (USA)",
            "eur-lex.europa.eu (EU)",
        ],
        "case_databases": [
            "indiankanoon.org    (India)",
            "courtlistener.com  (USA)",
            "curia.europa.eu    (EU)",
        ],
        "bright_data_tools": [
            "SERP API           → law database search",
            "Web Unlocker       → case database scraping",
            "Scraping Browser   → complaint portal extraction",
            "Browser Automation → legal aid directory navigation",
        ],
    }


@app.post(
    "/query",
    summary="Run the full 5-agent legal intelligence pipeline",
    tags=["Core"],
    responses={
        200: {"description": "Successful legal analysis"},
        422: {"description": "Validation error — check query length / country value"},
        500: {"description": "Internal pipeline error"},
    },
)
async def run_query(payload: QueryRequest, request: Request) -> JSONResponse:
    """
    **Main endpoint** — executes all five LangGraph agents in sequence.

    ### What you get back
    | Field | Description |
    |---|---|
    | `executive_summary` | 3-sentence overview |
    | `laws` | Relevant statutes with article numbers |
    | `precedents` | Recent case outcomes |
    | `action_plan.complaint_draft` | Ready-to-file complaint letter |
    | `action_plan.portal_url` | Where to submit the complaint |
    | `action_plan.legal_aid_contacts` | Nearby legal aid orgs |
    | `action_plan.next_steps` | 5 concrete action steps |

    ### Notes
    - Processing time: ~10–30 s (5 Gemini calls + 4 Bright Data operations)
    - Bright Data tools currently use placeholder implementations.
      Wire real MCP calls into `agents.py` to activate live data.
    """
    start_ts = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    country = _validate_country(payload.country)

    logger.info(
        "→ /query | ip=%s | country=%s | query=%r",
        client_ip,
        country,
        payload.query[:80] + ("…" if len(payload.query) > 80 else ""),
    )

    # ── Build initial LangGraph state ─────────────────────────────────────
    initial_state: LexScoutState = {
        "query":           payload.query,
        "category":        "",
        "jurisdictions":   [country],   # Classifier may expand this list
        "laws":            [],
        "precedents":      [],
        "complaint_draft": "",
        "portal_url":      "",
        "legal_aid":       [],
        "final_response":  {},
        "errors":          [],
    }

    # ── Execute pipeline ──────────────────────────────────────────────────
    try:
        result: LexScoutState = await lexscout_graph.ainvoke(initial_state)
    except Exception as exc:
        elapsed = round(time.perf_counter() - start_ts, 2)
        logger.error(
            "Pipeline exception after %.2fs: %s",
            elapsed,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error":           "Pipeline execution failed",
                "message":         str(exc),
                "elapsed_seconds": elapsed,
            },
        ) from exc

    elapsed = round(time.perf_counter() - start_ts, 2)

    # ── Attach timing to response ─────────────────────────────────────────
    final: Dict[str, Any] = result.get("final_response", {})
    meta = final.get("meta", {})
    meta["elapsed_seconds"] = elapsed
    final["meta"] = meta

    logger.info(
        "← /query done | %.2fs | category=%s | laws=%d | precedents=%d | errors=%d",
        elapsed,
        result.get("category", "?"),
        len(result.get("laws", [])),
        len(result.get("precedents", [])),
        len(result.get("errors", [])),
    )

    return JSONResponse(content=final, status_code=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════
#  ENTRY POINT (local dev)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "production").lower() == "development",
        log_level="info",
    )