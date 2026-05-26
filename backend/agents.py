"""
agents.py — LexScout LangGraph Agent Pipeline
==============================================
5 specialised agents wired into a LangGraph StateGraph:

  1. Classifier      — Gemini classifies query → {category, jurisdictions}
  2. Law Finder      — Bright Data SERP API   → relevant statutes & acts
  3. Precedent Hunter— Bright Data Web Unlocker → recent case outcomes
  4. Action Builder  — Bright Data Scraping Browser + Browser Automation
                       + Gemini → complaint draft, portal URL, legal aid
  5. Synthesizer     — Gemini → executive summary + final structured JSON

FIX SUMMARY (4 bugs fixed vs original):
  FIX 1 — law_finder_node:       removed accidental double-assignment
           `_LAW_DB_SITE_hints = _LAW_DB_SITE_HINTS.get(...)` typo
  FIX 2 — precedent_hunter_node: bright_data_access() returns dict {"html":...}
           not a plain str — unpack with result.get("html", "")
  FIX 3 — action_builder_node:   bright_data_extract() returns {"extracted":{...}}
           not a flat dict — unpack the inner "extracted" key
  FIX 4 — action_builder_node:   bright_data_interact() returns {"results":{...}}
           not {"contacts":[...]} — unpack correctly + pass to Gemini to structure
  CHANGE — Bright Data stubs removed; real implementations imported from tool_functions.py
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

# ── Import real Bright Data implementations from Chat 2 ──────────────────
from tool_functions import (
    bright_data_search,
    bright_data_access,
    bright_data_extract,
    bright_data_interact,
)

# ─────────────────────────────── bootstrap ────────────────────────────────
load_dotenv()
logger = logging.getLogger("lexscout.agents")

from groq import Groq

_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not _GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set — LLM calls will fail at runtime.")

_groq_client: Optional[Groq] = None

def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=_GROQ_API_KEY)
    return _groq_client

async def _gemini(prompt: str) -> str:
    """LLM call via Groq (drop-in replacement for Gemini)."""
    import asyncio
    client = _get_client()
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4096,
        )
    )
    return response.choices[0].message.content

# ═══════════════════════════════════════════════════════════════════════════
#  STATE SCHEMA
# ═══════════════════════════════════════════════════════════════════════════

class LexScoutState(TypedDict):
    """Shared state flowing through all five LangGraph nodes."""
    query: str
    category: str
    jurisdictions: List[str]
    laws: List[Dict[str, Any]]
    precedents: List[Dict[str, Any]]
    complaint_draft: str
    portal_url: str
    legal_aid: List[Dict[str, Any]]
    final_response: Dict[str, Any]
    errors: List[str]


# ═══════════════════════════════════════════════════════════════════════════
#  UTILITY
# ═══════════════════════════════════════════════════════════════════════════

def _parse_json(text: str, fallback: Any) -> Any:
    """Strips markdown fences then parses JSON. Returns fallback on error."""
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1]
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        return json.loads(cleaned.strip())
    except Exception as exc:
        logger.debug("JSON parse failed (%s) — returning fallback.", exc)
        return fallback


def _append_error(state: LexScoutState, msg: str) -> None:
    state["errors"] = state.get("errors", []) + [msg]


# ═══════════════════════════════════════════════════════════════════════════
#  AGENT 1 — CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════

_CATEGORIES = ["Privacy", "Employment", "Consumer Rights", "IP", "Criminal"]
_JURISDICTIONS = ["India", "USA", "EU"]


async def classifier_node(state: LexScoutState) -> LexScoutState:
    logger.info("▶ Agent 1 — Classifier")

    prompt = f"""You are a senior legal classification expert.
Analyse the legal situation below and output ONLY a valid JSON object.

Legal Query:
\"\"\"{state['query']}\"\"\"

Supported categories  : {_CATEGORIES}
Supported jurisdictions: {_JURISDICTIONS}

Rules:
  • "category" must be exactly one item from the supported categories list.
  • "jurisdictions" must be a non-empty list; infer from context clues
    (place names, currency, legislation references, etc.).
    If the query is ambiguous or country-agnostic, default to the country
    hint already stored in the jurisdictions field: {state.get('jurisdictions', ['India'])}.
  • "reasoning" is a single sentence explaining your classification.

Respond with ONLY this JSON (no markdown, no prose):
{{
  "category": "<one of the supported categories>",
  "jurisdictions": ["<one or more supported jurisdictions>"],
  "reasoning": "<one sentence>"
}}"""

    try:
        raw = await _gemini(prompt)
        parsed = _parse_json(raw, None)

        if (
            parsed
            and isinstance(parsed.get("category"), str)
            and parsed["category"] in _CATEGORIES
            and isinstance(parsed.get("jurisdictions"), list)
            and all(j in _JURISDICTIONS for j in parsed["jurisdictions"])
        ):
            state["category"] = parsed["category"]
            state["jurisdictions"] = parsed["jurisdictions"]
            logger.info(
                "  Category=%s | Jurisdictions=%s | Reason: %s",
                state["category"],
                state["jurisdictions"],
                parsed.get("reasoning", "—"),
            )
        else:
            raise ValueError(f"Unexpected classification payload: {parsed!r}")

    except Exception as exc:
        logger.error("Classifier error — using fallback. %s", exc)
        _append_error(state, f"Classifier fallback triggered: {exc}")
        state["category"] = state.get("category") or "Consumer Rights"

    return state


# ═══════════════════════════════════════════════════════════════════════════
#  AGENT 2 — LAW FINDER
# ═══════════════════════════════════════════════════════════════════════════

_LAW_DB_SITE_HINTS: Dict[str, str] = {
    "India": "site:indiacode.nic.in OR site:legalaffairs.gov.in",
    "USA":   "site:law.cornell.edu OR site:uscode.house.gov",
    "EU":    "site:eur-lex.europa.eu",
}

_LAW_SCHEMA = """[
  {{
    "law_name"     : "Full official name of the act / regulation",
    "article"      : "Most relevant section or article number",
    "jurisdiction" : "<jurisdiction>",
    "created"      : "Year enacted (string)",
    "last_amended" : "Year last amended, or 'N/A'",
    "what_changed" : "Brief description of the last significant amendment",
    "covers"       : "How this law addresses <category> situations"
  }}
]"""


async def law_finder_node(state: LexScoutState) -> LexScoutState:
    logger.info("▶ Agent 2 — Law Finder")
    all_laws: List[Dict[str, Any]] = []

    for jurisdiction in state["jurisdictions"]:
        # FIX 1: was `site_hint = _LAW_DB_SITE_hints = _LAW_DB_SITE_HINTS.get(...)`
        # The extra `_LAW_DB_SITE_hints =` was a typo creating a spurious variable.
        site_hint = _LAW_DB_SITE_HINTS.get(jurisdiction, "")
        query = f"{state['category']} law act regulations {jurisdiction} {site_hint}"
        targets = [site_hint] if site_hint else []

        serp_results = await bright_data_search(query, jurisdiction.lower())

        if serp_results:
            parse_prompt = f"""You are a legal research assistant.
Below are web-search results from legal databases about {state['category']} laws in {jurisdiction}.

Search results (JSON):
{json.dumps(serp_results, indent=2)[:4000]}

Extract all identifiable laws / acts and return ONLY a JSON array.
Each element must follow this schema exactly:
{_LAW_SCHEMA.replace('<jurisdiction>', jurisdiction).replace('<category>', state['category'])}

Return ONLY the JSON array, no prose."""

            try:
                raw = await _gemini(parse_prompt)
                laws = _parse_json(raw, [])
                if isinstance(laws, list):
                    all_laws.extend(laws)
            except Exception as exc:
                logger.error("Law structuring error (%s): %s", jurisdiction, exc)
                _append_error(state, f"Law Finder parse error [{jurisdiction}]: {exc}")

        else:
            logger.info("  No SERP results for %s — Gemini fallback", jurisdiction)
            fallback_prompt = f"""You are a legal expert specialising in {jurisdiction} law.
List the 3 most important and directly applicable laws / regulations for
a {state['category']} case in {jurisdiction}.

Return ONLY a JSON array — no markdown, no prose:
{_LAW_SCHEMA.replace('<jurisdiction>', jurisdiction).replace('<category>', state['category'])}"""

            try:
                raw = await _gemini(fallback_prompt)
                laws = _parse_json(raw, [])
                if isinstance(laws, list):
                    for law in laws:
                        law["jurisdiction"] = jurisdiction
                    all_laws.extend(laws)
            except Exception as exc:
                logger.error("Law fallback error (%s): %s", jurisdiction, exc)
                _append_error(state, f"Law Finder fallback error [{jurisdiction}]: {exc}")

    state["laws"] = all_laws
    logger.info("  Total laws found: %d", len(all_laws))
    return state


# ═══════════════════════════════════════════════════════════════════════════
#  AGENT 3 — PRECEDENT HUNTER
# ═══════════════════════════════════════════════════════════════════════════

_CASE_DB_URL_TEMPLATES: Dict[str, str] = {
    "India": "https://indiankanoon.org/search/?formInput={q}",
    "USA":   "https://www.courtlistener.com/?q={q}&type=o&order_by=score+desc",
    "EU":    "https://curia.europa.eu/juris/liste.jsf?language=en&num={q}",
}

_PRECEDENT_SCHEMA = """[
  {{
    "case_name"   : "Official case title with year, e.g. Smith v. Jones (2022)",
    "outcome"     : "Clear plain-English description of the court's decision",
    "year"        : <integer year>,
    "relevance"   : "How this precedent applies to <category> situations",
    "jurisdiction": "<jurisdiction>",
    "citation"    : "Official legal citation, e.g. AIR 2022 SC 1234"
  }}
]"""


async def precedent_hunter_node(state: LexScoutState) -> LexScoutState:
    logger.info("▶ Agent 3 — Precedent Hunter")
    all_precedents: List[Dict[str, Any]] = []

    law_names = [law.get("law_name", "") for law in state["laws"] if law.get("law_name")]
    query_fragment = " ".join(law_names[:2]) if law_names else state["category"]

    for jurisdiction in state["jurisdictions"]:
        url_template = _CASE_DB_URL_TEMPLATES.get(jurisdiction)
        if not url_template:
            continue

        search_url = url_template.replace(
            "{q}", f"{state['category']} {query_fragment}".replace(" ", "+")
        )

        # FIX 2: bright_data_access() returns dict {"html": ..., "status": ..., "url": ...}
        # Original code treated it as a plain string — this caused silent empty results.
        result = await bright_data_access(search_url)
        page_content = result.get("html", "") if isinstance(result, dict) else ""

        if page_content:
            parse_prompt = f"""You are a legal research assistant.
Below is the content of a legal case-search results page for
{state['category']} cases in {jurisdiction}.

Page content (first 3000 chars):
{page_content[:3000]}

Extract up to 4 relevant cases and return ONLY a JSON array:
{_PRECEDENT_SCHEMA.replace('<jurisdiction>', jurisdiction).replace('<category>', state['category'])}

Return ONLY the JSON array."""
            try:
                raw = await _gemini(parse_prompt)
                cases = _parse_json(raw, [])
                if isinstance(cases, list):
                    all_precedents.extend(cases)
            except Exception as exc:
                logger.error("Precedent parse error (%s): %s", jurisdiction, exc)
                _append_error(state, f"Precedent Hunter parse error [{jurisdiction}]: {exc}")

        else:
            logger.info("  No Web Unlocker content for %s — Gemini fallback", jurisdiction)
            fallback_prompt = f"""You are a legal research expert.
Provide 3 real, landmark or widely-cited court cases related to
{state['category']} in {jurisdiction}.
Laws involved: {', '.join(law_names[:3]) or 'general applicable law'}

Return ONLY a JSON array — no markdown, no prose:
{_PRECEDENT_SCHEMA.replace('<jurisdiction>', jurisdiction).replace('<category>', state['category'])}"""

            try:
                raw = await _gemini(fallback_prompt)
                cases = _parse_json(raw, [])
                if isinstance(cases, list):
                    for case in cases:
                        case["jurisdiction"] = jurisdiction
                    all_precedents.extend(cases)
            except Exception as exc:
                logger.error("Precedent fallback error (%s): %s", jurisdiction, exc)
                _append_error(state, f"Precedent Hunter fallback error [{jurisdiction}]: {exc}")

    state["precedents"] = all_precedents
    logger.info("  Total precedents found: %d", len(all_precedents))
    return state


# ═══════════════════════════════════════════════════════════════════════════
#  AGENT 4 — ACTION BUILDER
# ═══════════════════════════════════════════════════════════════════════════

_PORTAL_SEEDS: Dict[str, Dict[str, str]] = {
    "India": {
        "Privacy":         "https://privacyindia.gov.in/",
        "Consumer Rights": "https://consumerhelpline.gov.in/",
        "Employment":      "https://clc.gov.in/",
        "IP":              "https://ipindia.gov.in/",
        "Criminal":        "https://cybercrime.gov.in/",
    },
    "USA": {
        "Privacy":         "https://www.ftc.gov/about-ftc/contact-ftc",
        "Consumer Rights": "https://www.consumerfinance.gov/complaint/",
        "Employment":      "https://www.eeoc.gov/filing-charge-discrimination",
        "IP":              "https://www.copyright.gov/registration/",
        "Criminal":        "https://www.ic3.gov/",
    },
    "EU": {
        "Privacy":         "https://www.edpb.europa.eu/about-edpb/about-edpb/members_en",
        "Consumer Rights": "https://ec.europa.eu/consumers/odr/",
        "Employment":      "https://www.eurofound.europa.eu/",
        "IP":              "https://www.euipo.europa.eu/en",
        "Criminal":        "https://www.europol.europa.eu/report-a-crime",
    },
}

_LEGAL_AID_SEEDS: Dict[str, str] = {
    "India": "https://nalsa.gov.in/lsas",
    "USA":   "https://www.lawhelp.org/",
    "EU":    "https://e-justice.europa.eu/49/EN/legal_aid",
}


async def action_builder_node(state: LexScoutState) -> LexScoutState:
    logger.info("▶ Agent 4 — Action Builder")

    primary_jurisdiction = state["jurisdictions"][0]
    category = state["category"]

    # ── A. Complaint portal URL ───────────────────────────────────────────
    portal_seed = (
        _PORTAL_SEEDS
        .get(primary_jurisdiction, {})
        .get(category, "")
    )
    portal_url = portal_seed

    if portal_seed:
        portal_schema = {
            "complaint_form_url": "Direct URL to the online complaint submission form",
            "online_portal_url":  "Main portal homepage URL",
            "phone":              "Helpline phone number if present",
            "email":              "Contact email if present",
        }
        try:
            extracted = await bright_data_extract(portal_seed, portal_schema)
            # FIX 3: bright_data_extract() returns {"url":..., "extracted":{...}, "timestamp":...}
            # Original code called .get() directly on the outer dict — missed the inner "extracted".
            if isinstance(extracted, dict):
                inner = extracted.get("extracted", extracted)
                portal_url = (
                    inner.get("complaint_form_url")
                    or inner.get("online_portal_url")
                    or portal_seed
                )
        except Exception as exc:
            logger.error("Portal extract error: %s", exc)
            _append_error(state, f"Action Builder portal extract error: {exc}")

    state["portal_url"] = portal_url or "Refer to the relevant government authority website."

    # ── B. Legal aid contacts ─────────────────────────────────────────────
    legal_aid_seed = _LEGAL_AID_SEEDS.get(primary_jurisdiction, "")
    legal_aid_contacts: List[Dict[str, Any]] = []

    if legal_aid_seed:
        actions = [
            {"type": "navigate",     "url": legal_aid_seed},
            {"type": "wait",         "ms": 2000},
            {"type": "extract_text", "selector": ".contact, .legal-aid, .organisation",
             "output": "contact_info"},
        ]
        try:
            aid_data = await bright_data_interact(legal_aid_seed, actions)
            # FIX 4: bright_data_interact() returns {"results": {"contact_info": "..."}}
            # Original code looked for aid_data.get("contacts") which never existed.
            if aid_data and isinstance(aid_data.get("results"), dict):
                contacts_raw = aid_data["results"].get("contact_info", "")
                if contacts_raw:
                    structure_prompt = f"""Structure this legal aid contact info as a JSON array:

{contacts_raw[:2000]}

Return ONLY a JSON array — no markdown, no prose:
[{{"organization": "...", "phone": "...", "email": "...", "website": "...", "free_service": true}}]"""
                    raw = await _gemini(structure_prompt)
                    parsed = _parse_json(raw, [])
                    if isinstance(parsed, list):
                        legal_aid_contacts = parsed
        except Exception as exc:
            logger.error("Legal aid interact error: %s", exc)
            _append_error(state, f"Action Builder legal aid interact error: {exc}")

    # Gemini fallback — always runs when Bright Data returns nothing (demo mode)
    if not legal_aid_contacts:
        logger.info("  No Browser Automation data — Gemini fallback for legal aid")
        aid_prompt = f"""You are a legal aid directory expert.
List 3 real, active legal aid organisations that handle {category} cases in {primary_jurisdiction}.

Return ONLY a JSON array — no markdown, no prose:
[
  {{
    "organization": "Full official name",
    "phone":        "Contact phone number or 'N/A'",
    "email":        "Contact email or 'N/A'",
    "website":      "https://... organisation URL",
    "specialization":"Types of legal cases they handle",
    "free_service": true
  }}
]"""
        try:
            raw = await _gemini(aid_prompt)
            contacts = _parse_json(raw, [])
            if isinstance(contacts, list):
                legal_aid_contacts = contacts
        except Exception as exc:
            logger.error("Legal aid fallback error: %s", exc)
            _append_error(state, f"Action Builder legal aid fallback: {exc}")

    state["legal_aid"] = legal_aid_contacts

    # ── C. Draft complaint letter ─────────────────────────────────────────
    laws_block = "\n".join(
        f"  • {law.get('law_name', 'Unknown Act')}, "
        f"{law.get('article', '')}: {law.get('covers', '')}"
        for law in state["laws"][:5]
    ) or "  (no specific statutes identified)"

    precedents_block = "\n".join(
        f"  • {p.get('case_name', 'Unknown Case')} "
        f"({p.get('year', '?')}): {p.get('outcome', '')}"
        for p in state["precedents"][:3]
    ) or "  (no case precedents identified)"

    complaint_prompt = f"""You are an expert legal drafter.
Write a formal, professional complaint letter for the situation below.

━━━━━━━━━━━━━━━━━━  BRIEF  ━━━━━━━━━━━━━━━━━━
SITUATION   : {state['query']}
JURISDICTION: {', '.join(state['jurisdictions'])}
CATEGORY    : {category}

APPLICABLE LAWS:
{laws_block}

SUPPORTING PRECEDENTS:
{precedents_block}

FILING PORTAL: {state['portal_url']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Requirements for the letter:
1. Address it to the appropriate authority (use the portal context).
2. Open with a formal subject line.
3. State the facts concisely in numbered paragraphs.
4. Cite every applicable law by full name and exact article / section.
5. Reference at least two case precedents as supporting authority.
6. State the specific relief / remedy being sought.
7. Close professionally with a signature block.

Use these placeholders:
  [YOUR FULL NAME], [YOUR ADDRESS], [YOUR PHONE], [YOUR EMAIL], [DATE]

Output the letter in plain text — ready to copy-paste into the portal."""

    try:
        draft = await _gemini(complaint_prompt)
        state["complaint_draft"] = draft
        logger.info("  Complaint draft generated (%d chars)", len(draft))
    except Exception as exc:
        logger.error("Complaint draft error: %s", exc)
        state["complaint_draft"] = "[Complaint letter temporarily unavailable — please retry in 30 seconds.]"
        _append_error(state, f"Action Builder complaint draft: {exc}")

    return state


# ═══════════════════════════════════════════════════════════════════════════
#  AGENT 5 — SYNTHESIZER
# ═══════════════════════════════════════════════════════════════════════════

async def synthesizer_node(state: LexScoutState) -> LexScoutState:
    logger.info("▶ Agent 5 — Synthesizer")

    summary_prompt = f"""You are a senior legal advisor producing a concise briefing.

Situation : {state['query']}
Category  : {state['category']}
Jurisdictions: {', '.join(state['jurisdictions'])}
Laws identified : {len(state['laws'])}
Precedents found: {len(state['precedents'])}

Return ONLY a JSON object — no markdown, no prose:
{{
  "executive_summary": "<Exactly 3 sentences summarising the legal situation, the applicable framework, and the recommended course of action.>",
  "next_steps": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ...",
    "Step 4: ...",
    "Step 5: ..."
  ],
  "urgency": "High | Medium | Low",
  "disclaimer": "This analysis is AI-generated for informational purposes only and does not constitute legal advice. Consult a qualified lawyer before taking action."
}}"""

    try:
        raw = await _gemini(summary_prompt)
        synthesis = _parse_json(raw, {})
    except Exception as exc:
        logger.error("Synthesizer Gemini error: %s", exc)
        _append_error(state, f"Synthesizer error: {exc}")
        synthesis = {}

    state["final_response"] = {
        "query":         state["query"],
        "category":      state["category"],
        "jurisdictions": state["jurisdictions"],
        "executive_summary": synthesis.get(
            "executive_summary",
            "Legal analysis complete. Review the laws and precedents provided.",
        ),
        "urgency":    synthesis.get("urgency", "Medium"),
        "disclaimer": synthesis.get(
            "disclaimer",
            "This is AI-generated information only. Consult a qualified lawyer.",
        ),
        "laws":       state["laws"],
        "precedents": state["precedents"],
        "action_plan": {
            "next_steps":         synthesis.get("next_steps", []),
            "complaint_draft":    state["complaint_draft"],
            "portal_url":         state["portal_url"],
            "legal_aid_contacts": state["legal_aid"],
        },
        "meta": {
            "agents_run": [
                "Classifier",
                "Law Finder",
                "Precedent Hunter",
                "Action Builder",
                "Synthesizer",
            ],
            "bright_data_tools_used": [
                "bright_data_search   → Bright Data SERP API (law databases)",
                "bright_data_access   → Bright Data Web Unlocker (case databases)",
                "bright_data_extract  → Bright Data Scraping Browser (portal URLs)",
                "bright_data_interact → Bright Data Browser Automation (legal aid)",
            ],
            "pipeline_errors": state.get("errors", []),
        },
    }

    logger.info("▶ Pipeline complete — final response assembled.")
    return state


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD AND COMPILE THE LANGGRAPH StateGraph
# ═══════════════════════════════════════════════════════════════════════════

def build_graph() -> Any:
    """
    Topology (linear):
      START → classifier → law_finder → precedent_hunter
            → action_builder → synthesizer → END
    """
    workflow = StateGraph(LexScoutState)

    workflow.add_node("classifier",       classifier_node)
    workflow.add_node("law_finder",       law_finder_node)
    workflow.add_node("precedent_hunter", precedent_hunter_node)
    workflow.add_node("action_builder",   action_builder_node)
    workflow.add_node("synthesizer",      synthesizer_node)

    workflow.add_edge(START,              "classifier")
    workflow.add_edge("classifier",       "law_finder")
    workflow.add_edge("law_finder",       "precedent_hunter")
    workflow.add_edge("precedent_hunter", "action_builder")
    workflow.add_edge("action_builder",   "synthesizer")
    workflow.add_edge("synthesizer",      END)

    return workflow.compile()


# Compiled graph singleton — imported by main.py
lexscout_graph = build_graph()
logger.info("LexScout StateGraph compiled and ready.")