"""
LexScout — LangGraph Integration
Wraps the 4 Bright Data async functions as LangGraph-compatible tools
and wires them into a StateGraph agent.
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI          # swap for ChatAnthropic if preferred
from langgraph.graph import END, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

# ── Import your 4 Bright Data functions ──────────────────────────────────────
from tool_functions import (
    bright_data_access,
    bright_data_extract,
    bright_data_interact,
    bright_data_search,
)


# ─────────────────────────────────────────────
# 1. LANGGRAPH TOOL WRAPPERS
#    @tool decorator turns async functions into LangChain StructuredTools.
#    The docstring becomes the tool description the LLM sees.
# ─────────────────────────────────────────────

@tool
async def search_legal_sources(query: str, jurisdiction: str = "global") -> str:
    """
    Search for legal statutes, case law, and government portals via Google (Bright Data SERP API).

    Use this when you need to FIND relevant legal URLs for a topic.
    Returns a JSON list of {title, url, snippet}.

    Args:
        query:        Search query, e.g. 'Photography privacy law India site:indiacode.nic.in'
        jurisdiction: Country/region hint — 'india', 'us', 'uk', 'eu', 'australia', 'canada'
    """
    results = await bright_data_search(query, jurisdiction)
    return json.dumps(results, ensure_ascii=False, indent=2)


@tool
async def access_legal_portal(url: str) -> str:
    """
    Fetch a legal portal page, bypassing anti-bot measures (Bright Data Web Unlocker).

    Use this when you have a specific URL and need its raw HTML/text content.
    Works on: indiacode.nic.in, law.cornell.edu, eur-lex.europa.eu, etc.

    Args:
        url: Full URL of the legal page to fetch.
    """
    result = await bright_data_access(url)
    # Truncate HTML to avoid flooding context — return first 8000 chars
    if "html" in result:
        result["html"] = result["html"][:8000] + (
            "\n...[truncated]" if len(result.get("html", "")) > 8000 else ""
        )
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
async def extract_case_data(url: str, selectors_json: str) -> str:
    """
    Extract structured data from a JS-rendered legal case page (Bright Data Scraping Browser).

    Use this for indiankanoon.org, courtlistener.com, curia.europa.eu — sites that need JS.

    Args:
        url:             Full URL of the case/statute page.
        selectors_json:  JSON string mapping field names to CSS selectors.
                         Example: '{"case_title": "h1", "date": ".date", "outcome": "#order"}'
    """
    try:
        selectors = json.loads(selectors_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "invalid selectors_json — must be valid JSON"})
    result = await bright_data_extract(url, selectors)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
async def interact_with_portal(url: str, actions_json: str) -> str:
    """
    Automate multi-step browser interactions on legal aid portals and complaint forms
    (Bright Data Scraping Browser automation mode).

    Use this to navigate, click, fill forms, and extract contact information from
    government legal aid directories and complaint portals.

    Args:
        url:          Starting URL of the portal.
        actions_json: JSON array of action objects. Supported types:
                      navigate, click, type, wait, extract_text, extract_links.
                      Example: '[{"type":"click","selector":"#search-btn"},
                                 {"type":"extract_text","selector":".contact","output":"contact"}]'
    """
    try:
        actions = json.loads(actions_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "invalid actions_json — must be valid JSON array"})
    result = await bright_data_interact(url, actions)
    return json.dumps(result, ensure_ascii=False, indent=2)


# Collect all tools into one list for easy registration
LEXSCOUT_TOOLS = [
    search_legal_sources,
    access_legal_portal,
    extract_case_data,
    interact_with_portal,
]


# ─────────────────────────────────────────────
# 2. AGENT STATE
# ─────────────────────────────────────────────

class LexScoutState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    jurisdiction: str
    query: str


# ─────────────────────────────────────────────
# 3. STATEGRAPH DEFINITION
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are LexScout, an expert Legal Action Intelligence Agent.
You help users understand their legal rights and find relevant laws, case precedents,
and legal aid resources.

You have access to 4 powerful research tools:
1. search_legal_sources   — Google search via Bright Data SERP API
2. access_legal_portal    — Fetch law pages via Bright Data Web Unlocker
3. extract_case_data      — Extract structured data via Bright Data Scraping Browser
4. interact_with_portal   — Automate portal navigation via Bright Data Browser Automation

Research workflow:
1. SEARCH for relevant legal sources first
2. ACCESS specific pages to read statutes or decisions
3. EXTRACT structured data from case law databases
4. INTERACT with portals to find complaint mechanisms or legal aid contacts

Always cite the URLs of the laws and cases you reference.
Be concise, accurate, and practical — focus on actionable legal information.
"""


def build_lexscout_graph(llm_model: str = "gpt-4o") -> StateGraph:
    """Build and compile the LexScout LangGraph agent."""

    # Bind tools to the LLM so it can call them
    llm = ChatOpenAI(model=llm_model, temperature=0)
    llm_with_tools = llm.bind_tools(LEXSCOUT_TOOLS)

    # ── Nodes ────────────────────────────────

    async def agent_node(state: LexScoutState) -> dict:
        """LLM reasoning node — decides which tool to call next."""
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(LEXSCOUT_TOOLS)

    # ── Routing ──────────────────────────────

    def should_continue(state: LexScoutState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    # ── Graph ────────────────────────────────

    graph = StateGraph(LexScoutState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")   # always return to agent after tool execution

    return graph.compile()


# ─────────────────────────────────────────────
# 4. QUICK DEMO RUNNER
# ─────────────────────────────────────────────

async def run_demo_query(query: str, jurisdiction: str = "india") -> None:
    """Run a single query through the LexScout agent and print the result."""
    print(f"\n{'═'*70}")
    print(f"  LexScout Query  |  jurisdiction={jurisdiction}")
    print(f"  {query}")
    print(f"{'═'*70}\n")

    agent = build_lexscout_graph()
    initial_state: LexScoutState = {
        "messages":     [HumanMessage(content=query)],
        "jurisdiction": jurisdiction,
        "query":        query,
    }

    async for event in agent.astream(initial_state):
        for node, data in event.items():
            if node == "agent" and data.get("messages"):
                last = data["messages"][-1]
                if hasattr(last, "content") and last.content:
                    print(f"[AGENT] {last.content}")
            elif node == "tools" and data.get("messages"):
                print(f"[TOOLS] {len(data['messages'])} tool result(s) returned")

    print(f"\n{'═'*70}\n")


if __name__ == "__main__":
    asyncio.run(
        run_demo_query(
            "What are my rights if a photographer takes my photo in a public place in India?",
            jurisdiction="india",
        )
    )