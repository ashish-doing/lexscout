# ⚖️ LexScout — Legal Action Intelligence Agent

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Syne&weight=800&size=28&duration=3000&pause=1000&color=00D4FF&center=true&vCenter=true&width=800&lines=LexScout+%E2%80%94+Legal+Action+Intelligence+Agent;Bright+Data+Web+Data+UNLOCKED+Hackathon+2026" alt="LexScout" />

<br/>

<p>
  <img src="https://img.shields.io/badge/Bright%20Data-SERP%20API-FF6B00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Bright%20Data-Web%20Unlocker-FF6B00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Bright%20Data-Scraping%20Browser-FF6B00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Speechmatics-Real--time%20STT-6B4FFF?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gemini-1.5%20Flash-4285F4?style=for-the-badge&logo=google" />
  <img src="https://img.shields.io/badge/LangGraph-0.2+-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

<p>
  <a href="https://lexscout-production.up.railway.app"><img src="https://img.shields.io/badge/%F0%9F%9A%80%20Live%20Demo-Railway-0B0D0E?style=for-the-badge&logo=railway" /></a>
  <a href="https://github.com/ashish-doing/lexscout"><img src="https://img.shields.io/badge/%F0%9F%93%81%20GitHub-ashish--doing%2Flexscout-181717?style=for-the-badge&logo=github" /></a>
  <a href="https://youtube.com/YOUR_DEMO_LINK_HERE"><img src="https://img.shields.io/badge/%F0%9F%8E%AC%20Demo%20Video-YouTube-FF0000?style=for-the-badge&logo=youtube" /></a>
</p>

<br/>

> **Bright Data Web Data UNLOCKED Hackathon 2026 — Submission · Deadline: May 30, 2026**
>
> A 5-agent AI pipeline that converts a plain-language legal situation into a complete, jurisdiction-specific action plan — statutes, case precedents, a drafted complaint letter, the exact filing portal, and legal aid contacts — in under 30 seconds. Powered entirely by Bright Data's live web infrastructure.

<br/>

</div>

---

## The Problem

**250 million people** face legal violations every year and never act on them — not because the laws don't protect them, but because the system is too expensive, too opaque, and too fragmented to navigate alone.

A domestic worker photographed without consent doesn't know Section 66E exists. A gig worker whose wages were illegally deducted doesn't know which Labour Commissioner to file with. A consumer defrauded online doesn't know they can file on `consumerhelpline.gov.in` for free.

**The gap:** Rich legal data exists publicly. A tool that turns it into action doesn't.

---

## The Solution

Describe your situation in plain language. LexScout returns:

| Output | Example |
|---|---|
| 📜 **Relevant Laws** | Payment of Wages Act 1936 §7; Industrial Disputes Act 1947 §25F |
| ⚖️ **Case Precedents** | *Workmen v. Reptakos Brett & Co. (1992)* — employer liable for unlawful deductions |
| 📝 **Complaint Letter** | Full formal letter with legal citations, ready to file |
| 🌐 **Filing Portal** | `https://clc.gov.in/` — live-scraped, verified link |
| 🤝 **Legal Aid** | NALSA + local orgs with phone, email, website |
| 🗺️ **Action Plan** | 5 concrete next steps ordered by urgency |

**Free. Instant. No lawyer needed.**

---

## Screenshots

> Screenshots will be added after the demo video is recorded.
>
> _Showing: query input → 5-agent loading sequence → laws with timeline → case precedent cards → complaint letter → portal link → legal aid contacts_

---

## Bright Data Integration

Static legal databases go stale within months. Laws get amended. Complaint portals change URLs. Case databases add thousands of new judgments daily. **LexScout cannot exist without live web data** — Bright Data is the infrastructure that makes this possible.

All four Bright Data products are used, each mapped to a dedicated agent in the pipeline:

### 🔍 `bright_data_search()` — SERP API → Law Discovery

| | |
|---|---|
| **Agent** | Law Finder (Agent 2) |
| **Targets** | `indiacode.nic.in` · `law.cornell.edu` · `eur-lex.europa.eu` |
| **What it does** | Searches government legal databases for statutes matching the user's legal category and jurisdiction |
| **Why Bright Data** | Legal government portals block generic scrapers with rate limits and geo-restrictions. SERP API surfaces authoritative results reliably |
| **Output** | Raw results → Gemini extracts `{law_name, article, created, last_amended, covers}` |

### 🔓 `bright_data_access()` — Web Unlocker → Case Scraping

| | |
|---|---|
| **Agent** | Precedent Hunter (Agent 3) |
| **Targets** | `indiankanoon.org` · `courtlistener.com` · `curia.europa.eu` |
| **What it does** | Fetches full rendered page content from case law databases behind Cloudflare, CAPTCHAs, and browser fingerprinting |
| **Why Bright Data** | Indian Kanoon and CourtListener implement heavy bot-detection. Web Unlocker handles JS rendering, fingerprint rotation, and residential IP routing |
| **Output** | Raw HTML → Gemini parses `{case_name, outcome, year, relevance, citation}` |

### 🖥️ `bright_data_extract()` — Scraping Browser → Portal Extraction

| | |
|---|---|
| **Agent** | Action Builder (Agent 4) — portal step |
| **Targets** | `consumerhelpline.gov.in` · `ftc.gov` · `cybercrime.gov.in` |
| **What it does** | Navigates government complaint portals that render forms dynamically via JS and extracts the exact filing URL |
| **Why Bright Data** | Government portals load complaint URLs dynamically — a static HTTP request returns a blank page. Scraping Browser renders them fully |
| **Output** | `portal_url` — the verified, live complaint filing link |

### 🤖 `bright_data_interact()` — Browser Automation → Legal Aid

| | |
|---|---|
| **Agent** | Action Builder (Agent 4) — legal aid step |
| **Targets** | `nalsa.gov.in/lsas` · `lawhelp.org` · `e-justice.europa.eu` |
| **What it does** | Multi-step browser navigation: search → filter by category → paginate → extract contact info |
| **Why Bright Data** | Legal aid directories require real browser navigation. Static scrapers fail completely |
| **Output** | `legal_aid_contacts[]` — list of `{organization, phone, email, website, free_service}` |

---

## Partner Integrations

### 🎤 Speechmatics — Real-time Voice Input

LexScout supports voice-to-text query input via the **Speechmatics Real-time API** (`wss://eu2.rt.speechmatics.com/v2`).

- Click the 🎤 mic button next to the search box
- MediaRecorder streams audio as `audio/webm;codecs=opus` over WebSocket
- Speechmatics transcribes in real time using the `enhanced` operating point
- Transcript is pasted directly into the query textarea as you speak
- Red pulse animation shows active recording state; click again to stop

This makes LexScout accessible to users who cannot type — particularly important for the rural and low-literacy demographics who face the most legal vulnerability.

### 🧠 Google Gemini 1.5 Flash — AI Synthesis Engine

Gemini powers all reasoning inside the 5-agent pipeline:

| Agent | Gemini Task |
|---|---|
| Classifier | Identify legal category + jurisdiction from plain-language input |
| Law Finder | Parse Bright Data SERP results → structured law objects |
| Precedent Hunter | Parse Bright Data HTML → structured case objects |
| Action Builder | Draft jurisdiction-specific complaint letter |
| Synthesizer | Write executive summary, urgency score, next steps |

---

## Architecture

```
User (browser) ──🎤 Speechmatics RT API──► textarea
       │
       ▼  POST /query  {"query": "...", "country": "India"}
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│               LexScout StateGraph  (LangGraph)               │
│                                                              │
│  ┌─────────────────┐                                         │
│  │   Agent 1       │                                         │
│  │   Classifier    │  Gemini 1.5F                            │
│  │                 │  → category, jurisdictions              │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │   Agent 2       │  bright_data_search()                   │
│  │   Law Finder    │  ← Bright Data SERP API                 │
│  │                 │  Targets: indiacode.nic.in              │
│  │  + Gemini       │           law.cornell.edu               │
│  │  → laws[]       │           eur-lex.europa.eu             │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │   Agent 3       │  bright_data_access()                   │
│  │ Precedent Hunter│  ← Bright Data Web Unlocker             │
│  │                 │  Targets: indiankanoon.org              │
│  │  + Gemini       │           courtlistener.com             │
│  │  → precedents[] │           curia.europa.eu               │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────┐        │
│  │                  Agent 4                         │        │
│  │             Action Builder                       │        │
│  │                                                  │        │
│  │  bright_data_extract()  ← Scraping Browser       │        │
│  │  → portal_url (live complaint filing link)       │        │
│  │                                                  │        │
│  │  bright_data_interact() ← Browser Automation     │        │
│  │  → legal_aid_contacts[] (structured orgs)        │        │
│  │                                                  │        │
│  │  Gemini 1.5F → complaint_draft                   │        │
│  └────────┬─────────────────────────────────────────┘        │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │   Agent 5       │  Gemini 1.5F                            │
│  │   Synthesizer   │  → executive_summary                    │
│  │                 │  → next_steps[]                         │
│  │                 │  → urgency                              │
│  └────────┬────────┘                                         │
└───────────┼──────────────────────────────────────────────────┘
            ▼
┌──────────────────────────────────────────────────────────────┐
│                     Final JSON Response                      │
│  laws[] · precedents[] · complaint_draft · portal_url        │
│  legal_aid[] · executive_summary · next_steps[] · urgency    │
└──────────────────────────────────────────────────────────────┘
            ▼
     HTML Frontend — dark theme, animated, mobile-responsive
     5 collapsible sections · staggered fade-in · voice input
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Data** | Bright Data SERP API | Live legal statute search |
| **Data** | Bright Data Web Unlocker | Case law database access |
| **Data** | Bright Data Scraping Browser | Portal URL extraction |
| **Data** | Bright Data Browser Automation | Legal aid directory navigation |
| **Voice** | Speechmatics Real-time API | WebSocket speech-to-text |
| **LLM** | Google Gemini 1.5 Flash | Classification, parsing, drafting, synthesis |
| **Orchestration** | LangGraph StateGraph | 5-agent pipeline with shared state |
| **Backend** | FastAPI + Uvicorn | REST API, CORS, request validation |
| **Validation** | Pydantic v2 | Request/response schema |
| **Frontend** | Pure HTML5 + CSS3 + Vanilla JS | Zero-dependency UI, dark theme |
| **Fonts** | Google Fonts — Syne, DM Mono | Typography |
| **Deployment** | Railway.app | Live public URL for submission |
| **Language** | Python 3.11 | Windows 11 + PowerShell |

---

## Supported Scope

| Dimension | Values |
|---|---|
| **Jurisdictions** | 🇮🇳 India · 🇺🇸 USA · 🇪🇺 EU |
| **Legal Categories** | Privacy · Employment · Consumer Rights · IP · Criminal |
| **Law Databases** | indiacode.nic.in · law.cornell.edu · eur-lex.europa.eu |
| **Case Databases** | indiankanoon.org · courtlistener.com · curia.europa.eu |
| **Filing Portals** | cybercrime.gov.in · consumerhelpline.gov.in · ftc.gov · clc.gov.in + more |
| **Legal Aid** | nalsa.gov.in · lawhelp.org · e-justice.europa.eu |

---

## Project Structure

```
lexscout/
├── backend/
│   ├── agents.py            # LangGraph StateGraph — all 5 agent nodes
│   ├── main.py              # FastAPI app — POST /query endpoint
│   ├── tool_functions.py    # 4 Bright Data async tool functions
│   ├── langgraph_agent.py   # LangChain @tool wrappers + graph definition
│   ├── mcp_server.py        # MCP server exposing 4 BD tools over stdio
│   ├── requirements.txt     # Pinned Python dependencies
│   ├── Procfile             # Railway/Render deployment
│   ├── railway.toml         # Railway IaC config
│   └── render.yaml          # Render.com IaC config
├── frontend/
│   ├── index.html           # Main UI — voice input, 5 result sections
│   └── pitch.html           # 5-slide pitch deck
├── .env.example             # Environment variable template
├── .gitignore
├── LICENSE
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- [Google AI Studio](https://aistudio.google.com/app/apikey) API key (free tier works)
- [Bright Data](https://brightdata.com) account with SERP, Web Unlocker, and Scraping Browser zones

### 1. Clone

```powershell
git clone https://github.com/ashish-doing/lexscout.git
cd lexscout
```

### 2. Install

```powershell
cd backend
pip install -r requirements.txt
```

### 3. Configure

```powershell
copy ..\env.example .env
notepad .env
```

```env
GEMINI_API_KEY=your_gemini_api_key_here

BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
BRIGHT_DATA_SERP_ZONE=serp_api1
BRIGHT_DATA_UNLOCKER_ZONE=web_unlocker1
BRIGHT_DATA_SB_ZONE=scraping_browser1

ENV=development
PORT=8000
```

### 4. Run

```powershell
uvicorn main:app --reload --port 8000
```

Backend: `http://localhost:8000` · Swagger: `http://localhost:8000/docs`

### 5. Frontend

Open `frontend/index.html` directly in your browser — no build step needed.

### 6. Test

```powershell
curl -X POST http://localhost:8000/query `
  -H "Content-Type: application/json" `
  -d '{"query": "Someone took my photo without permission in a restaurant. I am in Delhi.", "country": "India"}'
```

---

## API Reference

### `POST /query`

**Request:**
```json
{
  "query": "My employer deducted salary without notice. I work in Mumbai.",
  "country": "India"
}
```

**Response (200):**
```json
{
  "laws": [{"law_name": "Payment of Wages Act, 1936", "article": "Section 7", ...}],
  "precedents": [{"case_name": "Workmen v. Reptakos Brett & Co. (1992)", ...}],
  "action_plan": {
    "complaint_draft": "To The Regional Labour Commissioner...",
    "portal_url": "https://clc.gov.in/",
    "legal_aid_contacts": [{"organization": "NALSA", "phone": "15100", ...}],
    "next_steps": ["Step 1: Document all deductions...", ...]
  },
  "meta": {
    "bright_data_tools_used": [
      "bright_data_search  → SERP API",
      "bright_data_access  → Web Unlocker",
      "bright_data_extract → Scraping Browser",
      "bright_data_interact→ Browser Automation"
    ],
    "elapsed_seconds": 18.4
  }
}
```

### Other Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Root health check |
| `GET` | `/health` | Health + API key status |
| `GET` | `/supported` | Jurisdictions, categories, data sources |
| `GET` | `/docs` | Swagger interactive docs |

---

## Deployment

### Railway.app (recommended, < 5 min)

1. Push to GitHub
2. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub** → `ashish-doing/lexscout`
3. Railway reads `backend/railway.toml` automatically
4. Add env vars: `GEMINI_API_KEY` + `BRIGHT_DATA_API_KEY` + zone names
5. Live URL: **[https://lexscout-production.up.railway.app](https://lexscout-production.up.railway.app)**

### Render.com (alternative)

[render.com](https://render.com) → **New Web Service** → connect repo → Render detects `backend/render.yaml` → add env vars → deploy.

---

## Demo Video

▶ **[Watch the 3-minute demo on YouTube](https://youtube.com/YOUR_DEMO_LINK_HERE)**

```
0:00–0:20  LexScout homepage — explain the problem
0:20–0:35  Click 🎤 mic → speak the scenario (Speechmatics live transcription)
0:35–0:50  Select India, click Analyze
0:50–1:30  Loading sequence — terminal shows all 4 Bright Data product logs:
             ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
             [14:32:01] 🔍 BRIGHT DATA — SERP API
               ▶ Google search | jurisdiction=india
               ⤷ query="Photography privacy law India..."
             ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
             [Bright Data Web Unlocker] Accessing: indiankanoon.org
             [Bright Data Scraping Browser] Extracting: cybercrime.gov.in
             [Bright Data Browser Automation] Navigating: nalsa.gov.in
1:30–2:00  Laws with history timeline — IT Act Section 66E
2:00–2:20  Case precedent cards + citations
2:20–2:40  Complaint letter + Copy button
2:40–3:00  Portal URL + legal aid contacts — close with impact stat
```

---

## Impact

| Metric | Value |
|---|---|
| Addressable users | 500M+ people who face legal issues annually without counsel |
| Cost reduction | From ₹3,000–₹15,000/hr → ₹0 |
| Time to action | From weeks (lawyer consultation) → 30 seconds |
| Scale path | 50+ jurisdictions via Bright Data's global proxy network |
| B2B path | API for legal aid NGOs, court assistance programs, HR platforms |
| Accessibility | Voice input via Speechmatics for low-literacy and rural users |

---

## Author

**Ashish Kumar** — B.Tech ECE, IIIT Guwahati (Batch 2024)

[![GitHub](https://img.shields.io/badge/GitHub-ashish--doing-181717?style=flat-square&logo=github)](https://github.com/ashish-doing)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-ashish--kumar-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/ashish-kumar-014aaa3b9)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-ashish--doing-FF9D00?style=flat-square&logo=huggingface)](https://huggingface.co/ashish-doing)

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built for the **Bright Data Web Data UNLOCKED Hackathon — May 2026**

*Powered by Bright Data · Speechmatics · Google Gemini · LangGraph*

⚖️ *Know your rights. Take action.*

</div>
