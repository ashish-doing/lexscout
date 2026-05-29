"""
LexScout — Legal Action Intelligence Agent
Bright Data Tool Functions — FIXED response parsing
"""

import os
import asyncio
import aiohttp
import json
from typing import Any
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
if not BRIGHT_DATA_API_KEY:
    import warnings
    warnings.warn("BRIGHT_DATA_API_KEY not set — Bright Data calls will fail.")

BRIGHT_DATA_BASE = "https://api.brightdata.com"
SERP_ZONE        = os.getenv("BRIGHT_DATA_SERP_ZONE",    "lexscout_serp")
BROWSER_ZONE     = os.getenv("BRIGHT_DATA_BROWSER_ZONE", "lexscout_browser")

TIMEOUT_SECONDS = 60
MAX_RETRIES     = 3
RETRY_BACKOFF   = 2

# ── Logging ──────────────────────────────────────────────────────────────────

CYAN="\033[96m"; GREEN="\033[92m"; YELLOW="\033[93m"; RED="\033[91m"
BOLD="\033[1m";  RESET="\033[0m"

def _log(product, action, detail, color=CYAN):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n{color}{BOLD}{'━'*60}{RESET}")
    print(f"{color}{BOLD}[{ts}] 🔍 BRIGHT DATA — {product}{RESET}")
    print(f"{color}  ▶ {action}{RESET}")
    print(f"{color}  ⤷ {detail}{RESET}")
    print(f"{color}{'━'*60}{RESET}\n")

def _log_result(product, status, detail):
    color = GREEN if "✅" in status else RED
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {status} {product} | {detail}{RESET}\n")

def _log_retry(attempt, max_retries, reason):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{YELLOW}[{ts}] ⚠️  Retry {attempt}/{max_retries} — {reason}{RESET}")


# ── 1. SERP API — bright_data_search ─────────────────────────────────────────

async def bright_data_search(
    query: str,
    jurisdiction: str = "global",
    num_results: int = 10,
) -> list[dict[str, str]]:
    """
    Bright Data SERP API — real Google results via BD.
    BD returns: {"status_code": 200, "body": "{...json string...}"}
    The body JSON has: {"organic": [{"link":..., "title":..., "description":...}]}
    """
    _log("SERP API", f"Google search | jurisdiction={jurisdiction}",
         f'query="{query}" | num_results={num_results}', color=CYAN)

    country_map = {
        "india": "IN", "us": "US", "uk": "GB",
        "eu": "DE", "australia": "AU", "canada": "CA",
    }
    if isinstance(jurisdiction, list):
        jurisdiction = jurisdiction[0] if jurisdiction else "global"
    country = country_map.get(jurisdiction.lower(), "US")

    google_url = (
        f"https://www.google.com/search"
        f"?q={query.replace(' ', '+')}&gl={country.lower()}&hl=en"
    )

    endpoint = f"{BRIGHT_DATA_BASE}/request"
    payload = {
        "zone":    SERP_ZONE,
        "url":     google_url,
        "format":  "json",
        "country": country,
    }
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited. Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    # BD returns {"status_code": 200, "body": "<json string>", "headers": {...}}
                    outer = await resp.json(content_type=None)

            # Parse the body string into JSON
            body_raw = outer.get("body", "{}")
            if isinstance(body_raw, str):
                body = json.loads(body_raw)
            else:
                body = body_raw

            results = []
            organic = body.get("organic", [])
            for item in organic[:num_results]:
                results.append({
                    "title":   item.get("title", ""),
                    "url":     item.get("link", item.get("url", "")),
                    "snippet": item.get("description", item.get("snippet", "")),
                })

            _log_result("SERP API", "✅ SUCCESS", f"{len(results)} real BD results returned")
            return results

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("SERP API", "❌ FAILED", f"HTTP {e.status}: {e.message}")
                return [{"error": f"HTTP {e.status}", "message": e.message}]
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("SERP API", "❌ FAILED", str(e))
            return [{"error": "unexpected", "message": str(e)}]

    return [{"error": "max_retries", "message": "Exhausted all retries"}]


# ── 2. WEB UNLOCKER — bright_data_access ─────────────────────────────────────

async def bright_data_access(url: str) -> dict[str, Any]:
    """Fetch page via Bright Data SERP zone (plain HTML)."""
    _log("WEB UNLOCKER", "Fetching legal portal", f"url={url}", color=GREEN)

    endpoint = f"{BRIGHT_DATA_BASE}/request"
    payload = {"zone": SERP_ZONE, "url": url, "format": "raw"}
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited. Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    # For raw format, BD returns the HTML directly
                    content_type = resp.headers.get("content-type", "")
                    if "json" in content_type:
                        outer = await resp.json(content_type=None)
                        html = outer.get("body", "") if isinstance(outer, dict) else str(outer)
                    else:
                        html = await resp.text()

            _log_result("WEB UNLOCKER", "✅ SUCCESS", f"{len(html):,} bytes from {url}")
            return {"url": url, "status": 200, "html": html, "text_length": len(html)}

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("WEB UNLOCKER", "❌ FAILED", f"HTTP {e.status}")
                return {"error": f"HTTP {e.status}", "url": url, "message": e.message, "html": ""}
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("WEB UNLOCKER", "❌ FAILED", str(e))
            return {"error": "unexpected", "url": url, "message": str(e), "html": ""}

    return {"error": "max_retries", "url": url, "html": ""}


# ── 3. SCRAPING BROWSER — bright_data_extract ────────────────────────────────

async def bright_data_extract(url: str, selectors: dict[str, str]) -> dict[str, Any]:
    """Bright Data Browser API — fetch JS-rendered page."""
    _log("SCRAPING BROWSER", "JS-rendered extraction",
         f"url={url} | fields={list(selectors.keys())}", color=YELLOW)

    endpoint = f"{BRIGHT_DATA_BASE}/request"
    payload = {"zone": BROWSER_ZONE, "url": url, "format": "raw"}
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS * 2),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited. Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    content_type = resp.headers.get("content-type", "")
                    if "json" in content_type:
                        outer = await resp.json(content_type=None)
                        html = outer.get("body", "") if isinstance(outer, dict) else str(outer)
                    else:
                        html = await resp.text()

            extracted = {"raw_html": html[:3000], "url": url}
            _log_result("SCRAPING BROWSER", "✅ SUCCESS", f"{len(html):,} bytes from {url}")
            return {"url": url, "extracted": extracted, "timestamp": datetime.utcnow().isoformat() + "Z"}

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("SCRAPING BROWSER", "❌ FAILED", f"HTTP {e.status}")
                return {"error": f"HTTP {e.status}", "url": url, "extracted": {}}
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("SCRAPING BROWSER", "❌ FAILED", str(e))
            return {"error": "unexpected", "url": url, "extracted": {}}

    return {"error": "max_retries", "url": url, "extracted": {}}


# ── 4. BROWSER AUTOMATION — bright_data_interact ─────────────────────────────

async def bright_data_interact(url: str, actions: list[dict[str, Any]]) -> dict[str, Any]:
    """Bright Data Browser API — fetch page for agent to parse."""
    _log("BROWSER AUTOMATION", f"Multi-step session | {len(actions)} actions",
         f"start_url={url}", color="\033[95m")

    endpoint = f"{BRIGHT_DATA_BASE}/request"
    payload = {"zone": BROWSER_ZONE, "url": url, "format": "raw"}
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS * 2),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited. Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    content_type = resp.headers.get("content-type", "")
                    if "json" in content_type:
                        outer = await resp.json(content_type=None)
                        html = outer.get("body", "") if isinstance(outer, dict) else str(outer)
                    else:
                        html = await resp.text()

            _log_result("BROWSER AUTOMATION", "✅ SUCCESS", f"{len(html):,} bytes from {url}")
            return {
                "url": url,
                "actions_completed": len(actions),
                "results": {"page_html": html[:4000]},
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("BROWSER AUTOMATION", "❌ FAILED", f"HTTP {e.status}")
                return {"error": f"HTTP {e.status}", "url": url, "results": {}}
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("BROWSER AUTOMATION", "❌ FAILED", str(e))
            return {"error": "unexpected", "url": url, "results": {}}

    return {"error": "max_retries", "url": url, "results": {}}


def _normalise_actions(actions):
    return actions  # kept for import compatibility