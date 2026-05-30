# LexScout — Architecture

## Overview

LexScout is a 5-agent AI pipeline built with LangGraph. Each agent has a single responsibility and passes structured state to the next. Bright Data provides all live web data — no static databases.

## Pipeline

```
User Query + Country
       │
       ▼
┌─────────────────┐
│  Agent 1        │  Groq llama-3.3-70b
│  Classifier     │  → category, jurisdictions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 2        │  Groq + Bright Data SERP API
│  Law Finder     │  → searches indiacode.nic.in / law.cornell.edu / eur-lex.europa.eu
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 3        │  Groq + Bright Data Browser API
│  Precedent      │  → scrapes indiankanoon.org / courtlistener.com / curia.europa.eu
│  Hunter         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 4        │  Groq llama-3.3-70b
│  Action Builder │  → complaint letter + portal URL + legal aid
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 5        │  AI/ML API Mistral-7B
│  Synthesizer    │  → final action plan assembly
└────────┬────────┘
         │
         ▼
   Legal Action Plan
   (laws + precedents + complaint + portal + legal aid)
```

## Bright Data Integration

| Agent | Bright Data Product | Target Sites |
|---|---|---|
| Law Finder | SERP API | indiacode.nic.in · law.cornell.edu · eur-lex.europa.eu |
| Precedent Hunter | Web Unlocker | indiankanoon.org · courtlistener.com · curia.europa.eu |
| Action Builder | Scraping Browser | consumerhelpline.gov.in · ftc.gov · cybercrime.gov.in |
| Action Builder | Browser Automation | nalsa.gov.in · lawhelp.org · e-justice.europa.eu |

## State Schema

Each agent reads from and writes to a shared `LexScoutState` TypedDict passed through the LangGraph `StateGraph`. Key fields:

```python
class LexScoutState(TypedDict):
    query: str
    country: str
    category: str
    jurisdictions: list[str]
    laws: list[dict]
    precedents: list[dict]
    complaint_draft: str
    portal_url: str
    legal_aid_contacts: list[dict]
    executive_summary: str
    next_steps: list[str]
    urgency: str
    pipeline_errors: list[str]
```

## Key Files

| File | Purpose |
|---|---|
| `backend/agents.py` | All 5 agent node functions + StateGraph definition |
| `backend/tool_functions.py` | 4 Bright Data async functions (SERP, Unlocker, Scraping Browser, Automation) |
| `backend/main.py` | FastAPI app — `POST /query` entry point |
| `backend/mcp_server.py` | MCP server exposing 4 BD tools over stdio for agent integration |
| `frontend/index.html` | Single-file UI — Speechmatics voice input + 5 result sections |

## Voice Input

Speechmatics Real-time API (`wss://eu2.rt.speechmatics.com/v2`) streams audio from the browser's `MediaRecorder` as `audio/webm;codecs=opus` over WebSocket. Transcripts are pasted directly into the query textarea as the user speaks.

## Deployment

Backend runs on Railway via `backend/railway.toml`. The `rootDirectory` is set to `backend/` so Railway installs from `requirements.txt` and runs `uvicorn main:app`.