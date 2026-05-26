# ⚖️ LexScout — Legal Action Intelligence Agent

<p align="center">
  <img src="https://img.shields.io/badge/Bright%20Data-SERP%20API-FF6B00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Bright%20Data-Web%20Unlocker-FF6B00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Bright%20Data-Scraping%20Browser-FF6B00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gemini-1.5%20Flash-4285F4?style=for-the-badge&logo=google" />
  <img src="https://img.shields.io/badge/LangGraph-0.2+-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

<p align="center">
  <strong>Bright Data Web Data UNLOCKED Hackathon 2026 — Submission</strong><br>
  <em>Deadline: May 30, 2026</em>
</p>

<p align="center">
  <a href="https://YOUR_RAILWAY_URL_HERE">🚀 Live Demo</a> •
  <a href="https://github.com/ashish-doing/lexscout">📁 GitHub</a> •
  <a href="https://youtube.com/YOUR_DEMO_LINK_HERE">🎬 Demo Video</a> •
  <a href="#quick-start">⚡ Quick Start</a>
</p>

> **Know your rights. Take action.**

---

## 🔥 The Problem

**250 million people** face legal violations every year and cannot act on them.

Not because the laws don't protect them — they do. But because the legal system is:

- **Inaccessible** — Average lawyer consultation costs ₹3,000–₹15,000 per hour in India. $300+ in the USA.
- **Opaque** — Laws change. Case precedents are buried across thousands of court databases. Complaint portals move. Legal aid directories go stale.
- **Fragmented** — India alone has 40 million+ pending court cases. Existing tools like Indian Kanoon or LexisNexis are static search engines — they find documents, they don't tell you what to do.

A domestic worker photographed without consent doesn't know Section 66E exists. A gig worker whose wages were illegally deducted doesn't know which Labour Commissioner to file with. A consumer defrauded online doesn't know they can file on `consumerhelpline.gov.in` for free.

**The gap:** Rich legal data exists publicly. A tool that turns it into action doesn't.

---

## 💡 The Solution

**LexScout** is a 5-agent AI pipeline that converts a plain-language description of any legal situation into a complete, jurisdiction-specific action plan — in under 30 seconds.

A user types:
> *"My employer deducted 15% of my salary without notice and denied me access to my employment contract. I work in Mumbai."*

LexScout returns:

| Output | Example |
|---|---|
| 📜 **Relevant Laws** | Payment of Wages Act 1936 §7; Industrial Disputes Act 1947 §25F |
| ⚖️ **Case Precedents** | *Workmen v. Reptakos Brett & Co. (1992)* — employer liable for unlawful deductions |
| 📝 **Complaint Letter** | Full formal letter with exact legal citations, ready to paste and file |
| 🌐 **Filing Portal** | `https://clc.gov.in/` — live-scraped, verified link |
| 🤝 **Legal Aid** | NALSA + 2 local legal aid orgs with phone, email, website |
| 🗺️ **Action Plan** | 5 concrete next steps ordered by urgency |

**Free. Instant. No lawyer needed.**

---

## 🤖 How Bright Data Powers LexScout

Static legal databases go stale within months. Laws get amended. Complaint portals change URLs. Case databases add thousands of new judgments daily. **LexScout cannot exist without live web data** — and Bright Data is the only infrastructure that makes this possible at scale.

All four Bright Data products are used, each mapped to a dedicated agent:

### 1. `bright_data_search()` → **SERP API**
- **Agent:** Law Finder (Agent 2)
- **Targets:** `indiacode.nic.in`, `law.cornell.edu`, `eur-lex.europa.eu`
- **What it does:** Searches government legal databases for statutes and regulations matching the user's legal category and jurisdiction. Returns structured results: title, URL, and snippet.
- **Why Bright Data:** Legal government portals block generic scrapers with rate limits and geo-restrictions. SERP API surfaces authoritative results from these sites reliably and at speed.
- **Output:** Raw search results → fed to Gemini to extract `{law_name, article, created, last_amended, covers}` objects.

### 2. `bright_data_access()` → **Web Unlocker**
- **Agent:** Precedent Hunter (Agent 3)
- **Targets:** `indiankanoon.org`, `courtlistener.com`, `curia.europa.eu`
- **What it does:** Fetches full rendered page content from case law databases that use Cloudflare, CAPTCHAs, and browser fingerprinting to block scraping.
- **Why Bright Data:** Indian Kanoon and CourtListener implement heavy bot-detection. Web Unlocker handles JS rendering, fingerprint rotation, and residential IP routing — making these pages reliably readable.
- **Output:** Raw HTML → fed to Gemini to parse `{case_name, outcome, year, relevance, citation}` objects.

### 3. `bright_data_extract()` → **Scraping Browser**
- **Agent:** Action Builder (Agent 4) — portal step
- **Targets:** `consumerhelpline.gov.in`, `ftc.gov`, `cybercrime.gov.in`, EDPB member pages
- **What it does:** Navigates government complaint portals (which render forms dynamically via JS) and extracts the exact filing URL using a structured CSS selector schema.
- **Why Bright Data:** Government portals load complaint form URLs dynamically — a static HTTP request returns a blank page. Scraping Browser renders them fully and returns structured data without fragile manual selectors.
- **Output:** `portal_url` — the verified, live complaint filing link included in the response.

### 4. `bright_data_interact()` → **Browser Automation**
- **Agent:** Action Builder (Agent 4) — legal aid step
- **Targets:** `nalsa.gov.in/lsas`, `lawhelp.org`, `e-justice.europa.eu`
- **What it does:** Navigates legal aid directories with multi-step interactions (search → filter by category → paginate → extract), returning structured contact information.
- **Why Bright Data:** Legal aid directories require real browser navigation — click search, select jurisdiction, filter by case type. Static scrapers fail completely. Browser Automation drives a real browser and returns clean structured data.
- **Output:** `legal_aid_contacts[]` — list of `{organization, phone, email, website, free_service}` objects.

---

## 🏗️ Architecture

```
POST /query
{"query": "My employer deducted salary...", "country": "India"}
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    LexScout StateGraph (LangGraph)                        │
│                                                                           │
│  ┌─────────────────┐                                                      │
│  │    Agent 1      │                                                      │
│  │   Classifier    │                                                      │
│  │                 │                                                      │
│  │  Gemini 1.5F    │                                                      │
│  │  → category     │  e.g. "Employment"                                   │
│  │  → jurisdictions│  e.g. ["India"]                                      │
│  └────────┬────────┘                                                      │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                      │
│  │    Agent 2      │                                                      │
│  │   Law Finder    │                                                      │
│  │                 │                                                      │
│  │  bright_data_   │ ← Bright Data SERP API                              │
│  │  search()       │   Targets: indiacode.nic.in                         │
│  │                 │            law.cornell.edu                           │
│  │  + Gemini       │            eur-lex.europa.eu                         │
│  │  → laws[]       │                                                      │
│  └────────┬────────┘                                                      │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                      │
│  │    Agent 3      │                                                      │
│  │ Precedent Hunter│                                                      │
│  │                 │                                                      │
│  │  bright_data_   │ ← Bright Data Web Unlocker                          │
│  │  access()       │   Targets: indiankanoon.org                         │
│  │                 │            courtlistener.com                         │
│  │  + Gemini       │            curia.europa.eu                           │
│  │  → precedents[] │                                                      │
│  └────────┬────────┘                                                      │
│           │                                                               │
│           ▼                                                               │
│  ┌──────────────────────────────────────────────┐                        │
│  │                  Agent 4                     │                        │
│  │             Action Builder                   │                        │
│  │                                              │                        │
│  │  bright_data_extract()  ← Scraping Browser  │                        │
│  │  → portal_url (live complaint filing link)   │                        │
│  │                                              │                        │
│  │  bright_data_interact() ← Browser Automation│                        │
│  │  → legal_aid_contacts[] (structured orgs)    │                        │
│  │                                              │                        │
│  │  Gemini 1.5F → complaint_draft (letter)      │                        │
│  └────────┬─────────────────────────────────────┘                        │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                      │
│  │    Agent 5      │                                                      │
│  │  Synthesizer    │                                                      │
│  │                 │                                                      │
│  │  Gemini 1.5F    │                                                      │
│  │  → executive    │                                                      │
│  │    summary      │                                                      │
│  │  → next_steps[] │                                                      │
│  │  → urgency      │                                                      │
│  └────────┬────────┘                                                      │
│           │                                                               │
└───────────┼───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          Final JSON Response                              │
│  laws[] · precedents[] · complaint_draft · portal_url · legal_aid[]      │
│  executive_summary · next_steps[] · urgency · disclaimer                 │
└───────────────────────────────────────────────────────────────────────────┘
            │
            ▼
     HTML Frontend
     (Dark theme, animated, mobile-responsive)
     5 collapsible sections — fade in staggered
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Data Infrastructure** | Bright Data SERP API | Live legal statute search |
| **Data Infrastructure** | Bright Data Web Unlocker | Case law database access |
| **Data Infrastructure** | Bright Data Scraping Browser | Portal URL extraction |
| **Data Infrastructure** | Bright Data Browser Automation | Legal aid directory navigation |
| **LLM** | Google Gemini 1.5 Flash | Classification, parsing, drafting, synthesis |
| **Orchestration** | LangGraph StateGraph | 5-agent pipeline with shared state |
| **Backend** | FastAPI + Uvicorn | REST API, CORS, request validation |
| **Validation** | Pydantic v2 | Request/response schema |
| **Frontend** | Pure HTML5 + CSS3 + Vanilla JS | Zero-dependency UI, dark theme |
| **Fonts** | Google Fonts — Syne, DM Mono | Typography |
| **Deployment** | Railway.app | Live public URL for submission |
| **Language** | Python 3.11 | Windows 11 + PowerShell dev environment |

---

## 🌍 Supported Scope

| Dimension | Values |
|---|---|
| **Jurisdictions** | 🇮🇳 India · 🇺🇸 USA · 🇪🇺 EU |
| **Legal Categories** | Privacy · Employment · Consumer Rights · IP · Criminal |
| **Law Databases** | indiacode.nic.in · law.cornell.edu · eur-lex.europa.eu |
| **Case Databases** | indiankanoon.org · courtlistener.com · curia.europa.eu |
| **Filing Portals** | cybercrime.gov.in · consumerhelpline.gov.in · ftc.gov · clc.gov.in + more |
| **Legal Aid** | nalsa.gov.in · lawhelp.org · e-justice.europa.eu |

---

## 📁 Project Structure

```
lexscout/
├── backend/
│   ├── agents.py            # LangGraph StateGraph — all 5 agent nodes
│   ├── main.py              # FastAPI app — POST /query endpoint
│   ├── tool_functions.py    # 4 Bright Data async functions (real implementations)
│   ├── langgraph_agent.py   # LangChain tool wrappers + alternative graph
│   ├── mcp_server.py        # MCP server exposing 4 BD tools over stdio
│   ├── requirements.txt     # Pinned Python dependencies
│   ├── Procfile             # Railway/Render deployment
│   ├── railway.toml         # Railway IaC config (rootDirectory = backend)
│   └── render.yaml          # Render.com IaC config
├── frontend/
│   ├── index.html           # Main LexScout UI (single file, no framework)
│   └── pitch.html           # 5-slide pitch deck
├── .env.example             # Environment variable template
├── .gitignore
├── LICENSE                  # MIT
└── README.md                # This file
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key (free tier works)
- A [Bright Data](https://brightdata.com) account with credits

### 1. Clone the repo

```powershell
git clone https://github.com/ashish-doing/lexscout.git
cd lexscout
```

### 2. Install dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 3. Configure environment

```powershell
copy ..\env.example .env
notepad .env
```

Fill in your `.env`:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Bright Data (get from brightdata.com → Proxies & Scraping → your zones)
BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
BRIGHT_DATA_SERP_ZONE=serp_api1
BRIGHT_DATA_UNLOCKER_ZONE=web_unlocker1
BRIGHT_DATA_SB_ZONE=scraping_browser1

# Server
ENV=development
PORT=8000
```

### 4. Run the backend

```powershell
uvicorn main:app --reload --port 8000
```

Backend live at: `http://localhost:8000`  
Swagger docs at: `http://localhost:8000/docs`

### 5. Open the frontend

Open `frontend/index.html` directly in your browser — no build step needed.

Or serve it:
```powershell
cd ..\frontend
python -m http.server 3000
# Visit http://localhost:3000
```

### 6. Test with a query

```powershell
curl -X POST http://localhost:8000/query `
  -H "Content-Type: application/json" `
  -d '{"query": "Someone took my photo without permission in a restaurant. I am in Delhi.", "country": "India"}'
```

---

## 📡 API Reference

### `POST /query` — Main endpoint

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
  "query": "My employer deducted salary...",
  "category": "Employment",
  "jurisdictions": ["India"],
  "executive_summary": "Your situation involves unlawful wage deduction...",
  "urgency": "High",
  "disclaimer": "This is AI-generated information only...",
  "laws": [
    {
      "law_name": "Payment of Wages Act, 1936",
      "article": "Section 7",
      "jurisdiction": "India",
      "created": "1936",
      "last_amended": "2017",
      "what_changed": "Extended coverage to all wage workers",
      "covers": "Prohibits unauthorized deductions from wages"
    }
  ],
  "precedents": [
    {
      "case_name": "Workmen v. Reptakos Brett & Co. (1992)",
      "outcome": "Supreme Court ruled employer liable for unlawful deductions",
      "year": 1992,
      "relevance": "Directly applicable to unauthorized salary deduction cases",
      "jurisdiction": "India",
      "citation": "AIR 1992 SC 504"
    }
  ],
  "action_plan": {
    "next_steps": [
      "Step 1: Document all deductions with pay slips and bank statements",
      "Step 2: Send a written notice to HR within 7 days",
      "Step 3: File complaint at clc.gov.in",
      "Step 4: Contact NALSA for free legal representation",
      "Step 5: Escalate to Labour Court if no response in 30 days"
    ],
    "complaint_draft": "To The Regional Labour Commissioner...[full letter]",
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
  "meta": {
    "agents_run": ["Classifier", "Law Finder", "Precedent Hunter", "Action Builder", "Synthesizer"],
    "bright_data_tools_used": [
      "bright_data_search  → SERP API",
      "bright_data_access  → Web Unlocker",
      "bright_data_extract → Scraping Browser",
      "bright_data_interact→ Browser Automation"
    ],
    "elapsed_seconds": 18.4,
    "pipeline_errors": []
  }
}
```

### Other endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Root health check |
| `GET` | `/health` | Health + Gemini key status |
| `GET` | `/supported` | Lists jurisdictions, categories, data sources |
| `GET` | `/docs` | Swagger interactive docs |
| `GET` | `/redoc` | ReDoc documentation |

---

## 🚀 Deployment

### Railway.app (recommended, < 5 min)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select `ashish-doing/lexscout`
4. Railway reads `backend/railway.toml` automatically
5. Add environment variable: `GEMINI_API_KEY=your_key`
6. Add: `BRIGHT_DATA_API_KEY=your_key` + zone names
7. Public URL appears in Railway dashboard within ~2 minutes

### Render.com (alternative)

1. Push repo to GitHub
2. [render.com](https://render.com) → **New Web Service** → connect repo
3. Render detects `backend/render.yaml` and pre-fills settings
4. Add environment variables → **Create Web Service**

---

## 🎬 Demo Video

▶ **[Watch the 3-minute demo on YouTube](https://youtube.com/YOUR_DEMO_LINK_HERE)**

### Demo script
```
0:00–0:20  Show LexScout homepage — explain the problem
0:20–0:40  Type scenario: "Someone took my photo without permission in a restaurant"
           Select country: India
0:40–1:30  Show loading sequence + terminal logs (Bright Data calls visible):
           [Bright Data SERP API] Searching: Privacy law India...
           [Bright Data Web Unlocker] Accessing: indiankanoon.org...
           [Bright Data Scraping Browser] Extracting from: cybercrime.gov.in...
           [Bright Data Browser Automation] Navigating: nalsa.gov.in...
1:30–2:00  Show law results: IT Act Section 66E with history timeline
2:00–2:20  Show case precedent card + citation
2:20–2:40  Show complaint letter + Copy button
2:40–3:00  Show portal URL + legal aid contacts — close with impact
```

---

## 📊 Impact

| Metric | Value |
|---|---|
| Addressable users | 500M+ people who face legal issues annually without counsel |
| Cost reduction | From ₹3,000–₹15,000/hr → ₹0 |
| Time to action | From weeks (lawyer consultation) → 30 seconds |
| Scale path | Add 50+ jurisdictions via Bright Data's global proxy network |
| B2B path | API for legal aid NGOs, court assistance programs, HR platforms |
| WhatsApp path | Deliver action plans via WhatsApp Business API (500M India users) |

---

## 👤 Author

**Ashish Kumar**  
B.Tech ECE, IIIT Guwahati (Batch 2024)
- GitHub: [@ashish-doing](https://github.com/ashish-doing)
- LinkedIn: [linkedin.com/in/ashish-kumar-014aaa3b9](https://linkedin.com/in/ashish-kumar-014aaa3b9)
- HuggingFace: [huggingface.co/ashish-doing](https://huggingface.co/ashish-doing)

---

## 📄 License

[MIT](LICENSE) © 2026 Ashish Kumar

---

<p align="center">
  Built for the <strong>Bright Data Web Data UNLOCKED Hackathon — May 2026</strong><br>
  ⚖️ <em>Know your rights. Take action.</em>
</p>