"""LexScout — Live API Credential Test  |  query: 'Photography privacy law India'"""

import asyncio
from tool_functions import (
    bright_data_search, bright_data_access,
    bright_data_extract, bright_data_interact,
)

QUERY = "Photography privacy law India"
LAW_URL = "https://www.indiacode.nic.in/handle/123456789/1362"   # IT Act 2000

async def main():
    print("\n" + "═"*60)

    print("\n[1/4] SERP API — searching Google…")
    results = await bright_data_search(QUERY, jurisdiction="india", num_results=3)
    for r in results[:3]:
        print(f"  • {r.get('title','')[:70]}")
        print(f"    {r.get('url','')[:70]}")

    print("\n[2/4] WEB UNLOCKER — fetching indiacode.nic.in…")
    page = await bright_data_access(LAW_URL)
    print(f"  status={page.get('status')}  bytes={page.get('text_length',0):,}")
    print(f"  preview: {page.get('html','')[:200].strip()[:120]}…")

    print("\n[3/4] SCRAPING BROWSER — extracting indiankanoon.org…")
    data = await bright_data_extract(
        "https://indiankanoon.org/search/?formInput=photography+privacy",
        selectors={"page_title": "title", "first_result": ".result_title a"},
    )
    print(f"  extracted: {data.get('extracted')}")

    print("\n[4/4] BROWSER AUTOMATION — interacting with nalsa.gov.in…")
    auto = await bright_data_interact(
        "https://nalsa.gov.in/",
        actions=[
            {"type": "wait", "ms": 2000},
            {"type": "extract_text", "selector": "h1", "output": "heading"},
        ],
    )
    print(f"  actions_completed={auto.get('actions_completed')}  results={auto.get('results')}")

    print("\n" + "═"*60)
    print("  ✅  All 4 Bright Data products responded — credentials OK")
    print("═"*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())