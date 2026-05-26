"""
LexScout MCP Server
Exposes the 4 Bright Data tool functions as MCP tools.
Run with: python mcp_server.py
"""

import asyncio
import json
import logging
import sys
from typing import Any

# pip install mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from tool_functions import (
    bright_data_access,
    bright_data_extract,
    bright_data_interact,
    bright_data_search,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP] %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("lexscout-mcp")

app = Server("lexscout-bright-data")

# ─────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────

TOOLS: list[Tool] = [
    Tool(
        name="bright_data_search",
        description=(
            "Search Google for legal statutes, cases, and government portals "
            "using Bright Data SERP API. Returns a list of {title, url, snippet}."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type":        "string",
                    "description": "Search query, e.g. 'Photography privacy law India site:indiacode.nic.in'",
                },
                "jurisdiction": {
                    "type":        "string",
                    "description": "Country hint: india, us, uk, eu, australia, canada",
                    "default":     "global",
                },
                "num_results": {
                    "type":        "integer",
                    "description": "Number of results (default 10, max 100)",
                    "default":     10,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="bright_data_access",
        description=(
            "Fetch a legal portal page using Bright Data Web Unlocker "
            "(bypasses anti-bot protection). Returns raw HTML. "
            "Works on indiacode.nic.in, law.cornell.edu, eur-lex.europa.eu."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type":        "string",
                    "description": "Full URL of the legal page to fetch.",
                },
            },
            "required": ["url"],
        },
    ),
    Tool(
        name="bright_data_extract",
        description=(
            "Extract structured data from a JS-rendered legal case page "
            "using Bright Data Scraping Browser. "
            "Use for indiankanoon.org, courtlistener.com, curia.europa.eu."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type":        "string",
                    "description": "Full URL to scrape.",
                },
                "selectors": {
                    "type":        "object",
                    "description": "Map of field names to CSS selectors.",
                    "example":     {"case_title": "h1", "date": ".date", "outcome": "#order"},
                },
            },
            "required": ["url", "selectors"],
        },
    ),
    Tool(
        name="bright_data_interact",
        description=(
            "Automate multi-step browser interactions on legal aid portals "
            "and government complaint sites using Bright Data Scraping Browser. "
            "Supports: navigate, click, type, wait, extract_text, extract_links."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type":        "string",
                    "description": "Starting URL for the automation session.",
                },
                "actions": {
                    "type":        "array",
                    "description": "Ordered list of action objects.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type":     {"type": "string"},
                            "selector": {"type": "string"},
                            "url":      {"type": "string"},
                            "text":     {"type": "string"},
                            "ms":       {"type": "integer"},
                            "output":   {"type": "string"},
                        },
                        "required": ["type"],
                    },
                },
            },
            "required": ["url", "actions"],
        },
    ),
]


# ─────────────────────────────────────────────
# HANDLERS
# ─────────────────────────────────────────────

@app.list_tools()
async def list_tools(_: ListToolsRequest) -> ListToolsResult:
    log.info("list_tools called — returning %d tools", len(TOOLS))
    return ListToolsResult(tools=TOOLS)


@app.call_tool()
async def call_tool(req: CallToolRequest) -> CallToolResult:
    name   = req.params.name
    args   = req.params.arguments or {}
    log.info("call_tool: %s  args=%s", name, list(args.keys()))

    try:
        if name == "bright_data_search":
            result = await bright_data_search(
                query=args["query"],
                jurisdiction=args.get("jurisdiction", "global"),
                num_results=int(args.get("num_results", 10)),
            )
        elif name == "bright_data_access":
            result = await bright_data_access(url=args["url"])
            # Truncate HTML for MCP transport
            if isinstance(result, dict) and "html" in result:
                result["html"] = result["html"][:6000] + "\n...[truncated]"
        elif name == "bright_data_extract":
            selectors = args.get("selectors", {})
            if isinstance(selectors, str):
                selectors = json.loads(selectors)
            result = await bright_data_extract(url=args["url"], selectors=selectors)
        elif name == "bright_data_interact":
            actions = args.get("actions", [])
            if isinstance(actions, str):
                actions = json.loads(actions)
            result = await bright_data_interact(url=args["url"], actions=actions)
        else:
            result = {"error": f"Unknown tool: {name}"}

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        )

    except Exception as exc:
        log.exception("Tool %s raised an exception", name)
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(exc)}))]
        )


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

async def main() -> None:
    log.info("LexScout MCP Server starting (stdio transport) …")
    async with stdio_server() as streams:
        await app.run(*streams, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())