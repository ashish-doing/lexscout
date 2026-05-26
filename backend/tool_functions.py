"""
LexScout — Legal Action Intelligence Agent
Bright Data Tool Functions (Production-Ready)
All 4 async tools: SERP, Web Unlocker, Scraping Browser, Browser Automation
"""

import os
import asyncio
import aiohttp
import json
import time
from typing import Any
from dotenv import load_dotenv
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

load_dotenv()

BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
if not BRIGHT_DATA_API_KEY:
    import warnings
    warnings.warn('BRIGHT_DATA_API_KEY not set — Bright Data calls will use Gemini fallbacks.')

BRIGHT_DATA_BASE      = "https://api.brightdata.com"
SERP_ZONE             = os.getenv("BRIGHT_DATA_SERP_ZONE",    "serp_api1")
UNLOCKER_ZONE         = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE","web_unlocker1")
SCRAPING_BROWSER_HOST = os.getenv("BRIGHT_DATA_SB_HOST",      "brd.superproxy.io")
SCRAPING_BROWSER_PORT = int(os.getenv("BRIGHT_DATA_SB_PORT",  "9222"))

TIMEOUT_SECONDS = 60
MAX_RETRIES     = 3
RETRY_BACKOFF   = 2   # seconds (doubles each retry)

# ─────────────────────────────────────────────
# LOGGING HELPERS
# ─────────────────────────────────────────────

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _log(product: str, action: str, detail: str, color: str = CYAN) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    bar = "━" * 60
    print(f"\n{color}{BOLD}{bar}{RESET}")
    print(f"{color}{BOLD}[{ts}] 🔍 BRIGHT DATA — {product}{RESET}")
    print(f"{color}  ▶ {action}{RESET}")
    print(f"{color}  ⤷ {detail}{RESET}")
    print(f"{color}{bar}{RESET}\n")

def _log_result(product: str, status: str, detail: str) -> None:
    color = GREEN if "✅" in status else RED
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {status} {product} | {detail}{RESET}\n")

def _log_retry(attempt: int, max_retries: int, reason: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{YELLOW}[{ts}] ⚠️  Retry {attempt}/{max_retries} — {reason}{RESET}")

# ─────────────────────────────────────────────
# 1. SERP API  ─ bright_data_search
# ─────────────────────────────────────────────

async def bright_data_search(
    query: str,
    jurisdiction: str = "global",
    num_results: int = 10,
) -> list[dict[str, str]]:
    """
    Bright Data SERP API — Google search for legal sources.

    Args:
        query:        Search string, e.g. "Photography privacy law India site:indiacode.nic.in"
        jurisdiction: Hint label (e.g. 'india', 'eu', 'us'). Sets Google country if recognised.
        num_results:  Number of organic results to return (max 100).

    Returns:
        List of {"title": ..., "url": ..., "snippet": ...}
    """
    _log(
        "SERP API",
        f"Google search  |  jurisdiction={jurisdiction}",
        f'query="{query}"  |  num_results={num_results}',
        color=CYAN,
    )

    country_map = {
        "india": "in", "us": "us", "uk": "gb",
        "eu": "de", "australia": "au", "canada": "ca",
    }
    country = country_map.get(jurisdiction.lower(), "us")

    endpoint = f"{BRIGHT_DATA_BASE}/serp/google/search"
    params = {
        "query":   query,
        "country": country,
        "num":     num_results,
        "hl":      "en",
    }
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited (429). Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = await resp.json()

            results = []
            organic = data.get("organic", [])
            for item in organic[:num_results]:
                results.append({
                    "title":   item.get("title", ""),
                    "url":     item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })

            _log_result("SERP API", "✅ SUCCESS", f"{len(results)} results returned")
            return results

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("SERP API", "❌ FAILED", f"HTTP {e.status}: {e.message}")
                return [{"error": f"HTTP {e.status}", "message": e.message}]
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except asyncio.TimeoutError:
            if attempt == MAX_RETRIES:
                _log_result("SERP API", "❌ FAILED", "Timeout after retries")
                return [{"error": "timeout", "message": "Request timed out"}]
            _log_retry(attempt, MAX_RETRIES, "Timeout")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("SERP API", "❌ FAILED", str(e))
            return [{"error": "unexpected", "message": str(e)}]

    return [{"error": "max_retries", "message": "Exhausted all retries"}]


# ─────────────────────────────────────────────
# 2. WEB UNLOCKER  ─ bright_data_access
# ─────────────────────────────────────────────

async def bright_data_access(url: str) -> dict[str, Any]:
    """
    Bright Data Web Unlocker — fetches a legal portal page bypassing blocks.

    Targets: indiacode.nic.in, law.cornell.edu, eur-lex.europa.eu, etc.

    Args:
        url: Full URL of the legal page to fetch.

    Returns:
        {"url": ..., "status": ..., "html": ..., "text_length": ...}
    """
    _log(
        "WEB UNLOCKER",
        "Fetching legal portal (anti-bot bypass)",
        f"url={url}",
        color=GREEN,
    )

    endpoint = f"{BRIGHT_DATA_BASE}/request"
    payload = {
        "zone":    UNLOCKER_ZONE,
        "url":     url,
        "format":  "raw",
        "country": "us",
    }
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited (429). Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    if resp.status == 403:
                        _log_result("WEB UNLOCKER", "❌ FAILED", f"403 Forbidden — check zone config for {url}")
                        return {"error": "forbidden", "url": url, "status": 403}
                    resp.raise_for_status()
                    html = await resp.text()

            _log_result("WEB UNLOCKER", "✅ SUCCESS", f"{len(html):,} bytes fetched from {url}")
            return {
                "url":         url,
                "status":      200,
                "html":        html,
                "text_length": len(html),
            }

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("WEB UNLOCKER", "❌ FAILED", f"HTTP {e.status}: {e.message}")
                return {"error": f"HTTP {e.status}", "url": url, "message": e.message}
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except asyncio.TimeoutError:
            if attempt == MAX_RETRIES:
                _log_result("WEB UNLOCKER", "❌ FAILED", "Timeout after retries")
                return {"error": "timeout", "url": url}
            _log_retry(attempt, MAX_RETRIES, "Timeout")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("WEB UNLOCKER", "❌ FAILED", str(e))
            return {"error": "unexpected", "url": url, "message": str(e)}

    return {"error": "max_retries", "url": url}


# ─────────────────────────────────────────────
# 3. SCRAPING BROWSER  ─ bright_data_extract
# ─────────────────────────────────────────────

async def bright_data_extract(
    url: str,
    selectors: dict[str, str],
) -> dict[str, Any]:
    """
    Bright Data Scraping Browser — JS-rendered extraction via CDP/Playwright.

    Targets: indiankanoon.org, courtlistener.com, curia.europa.eu

    Args:
        url:       Full URL to load and extract from.
        selectors: Dict mapping field names to CSS selectors.
                   e.g. {"case_title": "h1.judgement-title",
                          "date":       ".date-of-judgement",
                          "outcome":    "#final-order"}

    Returns:
        {"url": ..., "extracted": {field: value, ...}, "timestamp": ...}
    """
    _log(
        "SCRAPING BROWSER",
        "JS-rendered extraction (CDP protocol)",
        f"url={url}  |  fields={list(selectors.keys())}",
        color=YELLOW,
    )

    # Scraping Browser uses Playwright over the Bright Data proxy
    # We drive it via the REST Dataset/Browser API endpoint
    endpoint = f"{BRIGHT_DATA_BASE}/scraping-browser/scrape"
    payload = {
        "zone": os.getenv("BRIGHT_DATA_SB_ZONE", "scraping_browser1"),
        "url":  url,
        "actions": [
            {"type": "wait_for_selector", "selector": "body"},
            # Extract each selector as a separate extract action
            *[
                {
                    "type":     "extract",
                    "selector": css,
                    "property": "innerText",
                    "output":   field_name,
                }
                for field_name, css in selectors.items()
            ],
        ],
    }
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS * 2),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited (429). Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = await resp.json()

            extracted = data.get("results", data)
            _log_result(
                "SCRAPING BROWSER", "✅ SUCCESS",
                f"{len(extracted)} fields extracted from {url}",
            )
            return {
                "url":       url,
                "extracted": extracted,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("SCRAPING BROWSER", "❌ FAILED", f"HTTP {e.status}: {e.message}")
                return {"error": f"HTTP {e.status}", "url": url, "message": e.message}
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except asyncio.TimeoutError:
            if attempt == MAX_RETRIES:
                _log_result("SCRAPING BROWSER", "❌ FAILED", "Timeout after retries")
                return {"error": "timeout", "url": url}
            _log_retry(attempt, MAX_RETRIES, "Timeout")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("SCRAPING BROWSER", "❌ FAILED", str(e))
            return {"error": "unexpected", "url": url, "message": str(e)}

    return {"error": "max_retries", "url": url}


# ─────────────────────────────────────────────
# 4. BROWSER AUTOMATION  ─ bright_data_interact
# ─────────────────────────────────────────────

async def bright_data_interact(
    url: str,
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Bright Data Scraping Browser (Automation mode) — multi-step browser actions.

    Targets: legal-aid directories, government complaint portals.

    Args:
        url:     Starting URL for the automation session.
        actions: Ordered list of action dicts. Supported types:
                 {"type": "navigate",      "url": "https://..."}
                 {"type": "click",         "selector": "button#search"}
                 {"type": "type",          "selector": "input#q", "text": "lawyer"}
                 {"type": "wait",          "ms": 2000}
                 {"type": "extract_text",  "selector": ".contact", "output": "contact_info"}
                 {"type": "extract_links", "selector": "a.portal-link", "output": "portal_links"}

    Returns:
        {"url": ..., "actions_completed": int, "results": {output_key: value, ...}}
    """
    _log(
        "SCRAPING BROWSER (Automation)",
        f"Multi-step browser session  |  {len(actions)} actions",
        f"start_url={url}  |  action_types={[a['type'] for a in actions]}",
        color="\033[95m",  # Magenta
    )

    endpoint = f"{BRIGHT_DATA_BASE}/scraping-browser/scrape"
    payload = {
        "zone": os.getenv("BRIGHT_DATA_SB_ZONE", "scraping_browser1"),
        "url":  url,
        "actions": [
            {"type": "wait_for_selector", "selector": "body"},
            *_normalise_actions(actions),
        ],
    }
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type":  "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS * 3),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF ** attempt
                        _log_retry(attempt, MAX_RETRIES, f"Rate-limited (429). Waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = await resp.json()

            results = data.get("results", {})
            completed = data.get("actions_completed", len(actions))
            _log_result(
                "SCRAPING BROWSER (Automation)", "✅ SUCCESS",
                f"{completed} actions completed  |  {len(results)} outputs captured",
            )
            return {
                "url":               url,
                "actions_completed": completed,
                "results":           results,
                "timestamp":         datetime.utcnow().isoformat() + "Z",
            }

        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES:
                _log_result("SCRAPING BROWSER (Automation)", "❌ FAILED", f"HTTP {e.status}")
                return {"error": f"HTTP {e.status}", "url": url, "message": e.message}
            _log_retry(attempt, MAX_RETRIES, f"HTTP {e.status}")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except asyncio.TimeoutError:
            if attempt == MAX_RETRIES:
                _log_result("SCRAPING BROWSER (Automation)", "❌ FAILED", "Timeout")
                return {"error": "timeout", "url": url}
            _log_retry(attempt, MAX_RETRIES, "Timeout")
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

        except Exception as e:
            _log_result("SCRAPING BROWSER (Automation)", "❌ FAILED", str(e))
            return {"error": "unexpected", "url": url, "message": str(e)}

    return {"error": "max_retries", "url": url}


def _normalise_actions(actions: list[dict]) -> list[dict]:
    """Translate our action schema → Bright Data Scraping Browser action schema."""
    bd_actions = []
    for act in actions:
        t = act.get("type")
        if t == "navigate":
            bd_actions.append({"type": "navigate", "url": act["url"]})
        elif t == "click":
            bd_actions.append({"type": "click", "selector": act["selector"]})
        elif t == "type":
            bd_actions.append({
                "type":     "type",
                "selector": act["selector"],
                "text":     act.get("text", ""),
            })
        elif t == "wait":
            bd_actions.append({"type": "wait", "ms": act.get("ms", 1000)})
        elif t == "extract_text":
            bd_actions.append({
                "type":     "extract",
                "selector": act["selector"],
                "property": "innerText",
                "output":   act.get("output", "extracted_text"),
            })
        elif t == "extract_links":
            bd_actions.append({
                "type":     "extract",
                "selector": act["selector"],
                "property": "href",
                "output":   act.get("output", "extracted_links"),
                "multiple": True,
            })
        # Unknown types are passed through as-is for forward compatibility
        else:
            bd_actions.append(act)
    return bd_actions