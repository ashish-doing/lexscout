# ⚖️ LexScout — Legal Action Intelligence Agent

> **Bright Data Web Data UNLOCKED Hackathon 2026** submission  
> _Deadline: May 30, 2026_

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What is LexScout?

LexScout converts a plain-language description of a legal problem into **complete, actionable legal intelligence** — in one API call.

A user types:
> _"My employer deducted salary without notice and refuses to show my employment contract. I work in Mumbai."_

LexScout returns:

| Output | Example |
|---|---|
| 📜 **Relevant laws** | Payment of Wages Act 1936, §7; Industrial Disputes Act 1947, §25F |
| ⚖️ **Case precedents** | _Workmen v. Reptakos Brett & Co. (1992)_ |
| 📝 **Complaint draft** | Full formal letter with exact legal citations, ready to paste |
| 🌐 **Filing portal** | https://clc.gov.in/ |
| 🤝 **Legal aid** | NALSA, local bar association contacts |
| 🗺️ **Action plan** | 5 concrete next steps |

---

## Architecture

```
POST /query
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LexScout StateGraph (LangGraph)                     │
│                                                                             │
│  ┌───────────────┐   ┌───────────────┐   ┌──────────────────────────────┐  │
│  │   Agent 1     │   │   Agent 2     │   │        Agent 3               │  │
│  │  Classifier   │──▶│  Law Finder   │──▶│    Precedent Hunter          │  │
│  │               │   │               │   │                              │  │
│  │  Gemini 1.5F  │   │ bright_data_  │   │  bright_data_access()        │  │
│  │               │   │ search()      │   │  (Web Unlocker)              │  │
│  │  → category   │   │ (SERP API)    │   │                              │  │
│  │  → jurisdicts │   │               │   │  Targets:                    │  │
│  └───────────────┘   │  Targets:     │   │  indiankanoon.org            │  │
│                      │  indiacode    │   │  courtlistener.com           │  │
│                      │  law.cornell  │   │  curia.europa.eu             │  │
│                      │  eur-lex      │   └──────────────┬───────────────┘  │
│                      └───────────────┘                  │                  │
│                                                         ▼                  │
│  ┌───────────────┐   ┌─────────────────────────────────────────────────┐   │
│  │   Agent 5     │   │                    Agent 4                      │   │
│  │  Synthesizer  │◀──│               Action Builder                    │   │
│  │               │   │                                                 │   │
│  │  Gemini 1.5F  │   │  bright_data_extract()  → portal URL           │   │
│  │               │   │  (Scraping Browser)                             │   │
│  │  → executive  │   │                                                 │   │
│  │    summary    │   │  bright_data_interact() → legal aid contacts    │   │
│  │  → next_steps │   │  (Browser Automation)                           │   │
│  └───────┬───────┘   │                                                 │   │
│          │           │  Gemini 1.5F            → complaint draft       │   │
│          ▼           └─────────────────────────────────────────────────┘   │
│   Final JSON                                                                │
│   Response                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## How Bright Data Powers LexScout

LexScout uses **four** distinct Bright Data capabilities, each mapped to a
named placeholder function in `agents.py` that wires directly to the MCP layer.

### 1. `bright_data_search()` → **SERP API**
- **Where:** Agent 2 — Law Finder
- **What it does:** Searches legal statute databases (`indiacode.nic.in`,
  `law.cornell.edu`, `eur-lex.europa.eu`) for acts and regulations that match
  the user's legal category and jurisdiction.
- **Why Bright Data:** Legal databases block generic scrapers. The SERP API
  surfaces structured results from these authoritative sources without hitting
  bot-detection walls.
- **Output fed to:** Gemini to extract structured `{law_name, article, covers}` objects.

### 2. `bright_data_access()` → **Web Unlocker**
- **Where:** Agent 3 — Precedent Hunter
- **What it does:** Fetches full page content from case law databases
  (`indiankanoon.org`, `courtlistener.com`, `curia.europa.eu`), which
  implement heavy anti-bot protection including Cloudflare, CAPTCHAs, and
  fingerprinting.
- **Why Bright Data:** Web Unlocker handles JS rendering, fingerprint rotation,
  and residential IP routing — the only reliable way to read these pages at scale.
- **Output fed to:** Gemini to parse case names, outcomes, and citations.

### 3. `bright_data_extract()` → **Scraping Browser**
- **Where:** Agent 4 — Action Builder (portal URL step)
- **What it does:** Navigates government complaint portals
  (`consumerhelpline.gov.in`, `ftc.gov`, EDPB member pages) and extracts the
  exact online filing form URL using a structured schema.
- **Why Bright Data:** These portals render their complaint forms dynamically via
  JavaScript. Scraping Browser renders them fully and returns structured data
  against a user-defined schema — no fragile CSS selectors needed.
- **Output:** `portal_url` — the direct link included in the response and complaint letter.

### 4. `bright_data_interact()` → **Browser Automation**
- **Where:** Agent 4 — Action Builder (legal aid step)
- **What it does:** Navigates legal aid directories (`nalsa.gov.in`,
  `lawhelp.org`, `e-justice.europa.eu`), filters results by legal category,
  and extracts structured contact information (org name, phone, email, website).
- **Why Bright Data:** These directories require multi-step navigation — search,
  filter, paginate — which static scrapers cannot handle. Browser Automation
  drives a real browser, executes the interactions, and returns clean data.
- **Output:** `legal_aid_contacts[]` list in the final response.

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| LLM | Google Gemini 1.5 Flash (`google-generativeai`) |
| Orchestration | LangGraph `StateGraph` |
| API Framework | FastAPI + Uvicorn |
| Data Layer | Bright Data (SERP, Web Unlocker, Scraping Browser, Browser Automation) |
| Deployment | Railway.app / Render.com |

---

## Supported Scope

| Dimension | Values |
|---|---|
| **Jurisdictions** | India · USA · EU |
| **Categories** | Privacy · Employment · Consumer Rights · IP · Criminal |

---

## Project Structure

```
lexscout/
├── main.py              # FastAPI app — single POST /query endpoint
├── agents.py            # LangGraph StateGraph with 5 agent nodes
├── requirements.txt     # Pinned Python dependencies
├── Procfile             # Render.com / Heroku deployment
├── railway.toml         # Railway.app deployment config
├── render.yaml          # Render.com IaC config
├── env.example          # Environment variable template
├── LICENSE              # MIT License
└── README.md            # This file
```

---

## Setup & Local Development

### Prerequisites
- Python 3.11
- A [Google AI Studio](https://aistudio.google.com/) API key (free tier works)

### 1. Clone & create virtualenv

```powershell
# Windows PowerShell
git clone https://github.com/YOUR_USERNAME/lexscout.git
cd lexscout

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Configure environment variables

```powershell
# Copy the template
copy env.example .env

# Edit .env and add your Gemini key
notepad .env
```

`.env` should contain:
```
GEMINI_API_KEY=your_gemini_api_key_here
ENV=development
PORT=8000
```

### 3. Run the API

```powershell
uvicorn main:app --reload --port 8000
```

API will be live at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

### 4. Test with curl

```powershell
curl -X POST http://localhost:8000/query `
  -H "Content-Type: application/json" `
  -d '{"query": "My employer deducted salary without notice. I work in Mumbai.", "country": "India"}'
```

Or use the Swagger UI at `/docs`.

---

## API Reference

### `POST /query`

**Request body:**
```json
{
  "query": "Plain-language legal situation (15–2000 chars)",
  "country": "India | USA | EU"
}
```

**Response (200):**
```json
{
  "query": "...",
  "category": "Employment",
  "jurisdictions": ["India"],
  "executive_summary": "...",
  "urgency": "High",
  "laws": [
    {
      "law_name": "Payment of Wages Act, 1936",
      "article": "Section 7",
      "jurisdiction": "India",
      "created": "1936",
      "last_amended": "2017",
      "what_changed": "...",
      "covers": "..."
    }
  ],
  "precedents": [
    {
      "case_name": "Workmen v. Reptakos Brett & Co. (1992)",
      "outcome": "...",
      "year": 1992,
      "relevance": "...",
      "jurisdiction": "India",
      "citation": "AIR 1992 SC 504"
    }
  ],
  "action_plan": {
    "next_steps": ["Step 1: ...", "Step 2: ..."],
    "complaint_draft": "To the Regional Labour Commissioner...",
    "portal_url": "https://clc.gov.in/",
    "legal_aid_contacts": [
      {
        "organization": "National Legal Services Authority (NALSA)",
        "phone": "15100",
        "email": "nalsa-dla@nic.in",
        "website": "https://nalsa.gov.in/",
        "specialization": "Employment, consumer, criminal cases",
        "free_service": true
      }
    ]
  },
  "disclaimer": "This analysis is AI-generated...",
  "meta": {
    "agents_run": ["Classifier", "Law Finder", "Precedent Hunter", "Action Builder", "Synthesizer"],
    "elapsed_seconds": 14.2
  }
}
```

### Other endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Root health check |
| `GET` | `/health` | Health check with Gemini key status |
| `GET` | `/supported` | Lists all supported jurisdictions, categories, data sources |
| `GET` | `/docs` | Swagger interactive docs |
| `GET` | `/redoc` | ReDoc documentation |

---

## Deployment

### Railway.app (< 5 minutes)

1. Push this repo to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Select your repo.
4. Add environment variable: `GEMINI_API_KEY=your_key`
5. Railway picks up `railway.toml` automatically — deploy starts.
6. Your public URL appears in the Railway dashboard within ~2 minutes.

### Render.com (< 5 minutes)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New** → **Web Service**.
3. Connect your GitHub repo.
4. Render detects `render.yaml` and pre-fills all settings.
5. Add environment variable: `GEMINI_API_KEY=your_key`
6. Click **Create Web Service**.

---

## Wiring Bright Data MCP (Chat 2)

All four Bright Data functions in `agents.py` are clearly marked with
`# ── REPLACE THIS BODY with the real MCP call ──` comments.

To activate live data:
1. Replace each function body with the corresponding `mcp_bright_data.*` call.
2. No other changes needed — the pipeline, state schema, and API contract stay identical.

---

## Demo

🎬 **Demo Video:** _[PLACEHOLDER — link to be added before May 30 submission]_

---

## License

[MIT](LICENSE) © 2026 LexScout Contributors