# Contributing to LexScout

## Setup
1. Fork the repo
2. `cp .env.example backend/.env` and add your keys
3. `cd backend && pip install -r requirements.txt`
4. `uvicorn main:app --reload`

## Architecture
5 LangGraph agents in `backend/agents.py`:
- Agent 1: Classifier (Groq) — categorizes legal situation
- Agent 2: Law Finder (Groq + Bright Data SERP) — finds applicable statutes
- Agent 3: Precedent Hunter (Groq + Bright Data Browser) — finds case law
- Agent 4: Action Builder (Groq) — drafts complaint letter + finds portal
- Agent 5: Synthesizer (AI/ML API Mistral-7B) — assembles final plan

## Adding a new jurisdiction
1. Add country to `_SUPPORTED_COUNTRIES` in `backend/main.py`
2. Add law databases to `backend/agents.py` search targets
3. Update frontend country dropdown in `frontend/index.html`

## Pull Request Guidelines
- One feature per PR
- Test with at least one query per jurisdiction
- Update README if adding new capabilities

## Reporting Issues
Open a GitHub issue with: query used, country, error message, terminal logs.