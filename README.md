# IPC-BNS Legal Intelligence Platform

AI-assisted legal migration and validation platform for translating legal references from the Indian Penal Code (IPC) to the Bharatiya Nyaya Sanhita (BNS) with traceable, engineering-grade validation.

## Problem Statement

The IPC-to-BNS transition introduces operational risk for legal teams, investigators, and compliance workflows:
- legacy case records and legal templates still reference IPC sections,
- migrated sections may not be one-to-one and can require contextual interpretation,
- manual migration is time-consuming and inconsistent across teams,
- poor migration quality can produce downstream drafting and review errors.

This project addresses those risks through a structured migration pipeline that combines deterministic rules, AI-assisted analysis, and measurable validation.

> **Dataset disclaimer:** the IPC↔BNS mapping shipped in `data/ipc_bns_mapping.json` is a research-grade dataset built for engineering and evaluation purposes. It requires review by qualified legal professionals before any real-world reliance.

## Architecture Layers

The platform is organised as explicit, independently testable layers:

### 1. Data & Mapping Layer

- **482 mapping records** covering **438 of the 511 IPC base sections**, including:
  - subsection-level BNS targets (165 records map to codes like `BNS-106(1)`, `BNS-61(2)`),
  - **17 omissions** marked explicitly (e.g. `IPC-377 → BNS-OMITTED-377`),
  - **Prevention of Corruption Act repeals** marked explicitly (`IPC-161`, `IPC-165A → BNS-REPEALED-161`).
- Each record carries `keywords`, `chapter`, `ai_summary`, and `validation_rules` metadata.
- `DataLoader` (`backend/services/data_loader.py`) loads the dataset into a Pandas DataFrame with code normalisation.
- **SQLite mirror** (`backend/db`) on SQLAlchemy 2.0 (typed `Mapped`/`mapped_column` ORM): `seed.py` is idempotent (uses `Session.merge`, safe to re-run), and `DBMappingService` serves the same API from the database instead of JSON.

### 2. Deterministic Reasoning Layer

`MappingService` (`backend/services/mapping_service.py`) provides repeatable, rule-based retrieval:
- exact IPC/BNS code match: **+10** per matched field,
- keyword hits: **+2** per occurrence, free-text hits: **+1** per occurrence,
- confidence bands: score **≥ 10 → high**, **≥ 3 → medium**, **> 0 → low**, else none,
- `extract_references()` normalises free-text citations (`IPC 302`, `ipc302`, `IPC-498A` all resolve to `IPC-302` / `IPC-498A`).

No model is involved in this layer — the same input always yields the same ranking.

### 3. Validation & Contradiction Layer

- `detect_contradictions()` flags duplicate normalised IPC or BNS codes across records.
- `validate_records()` / `validate_schema()` enforce field completeness and schema integrity.
- In the agent pipeline, detected contradictions **cap confidence** (high → medium) and append a human-review warning to the answer.
- Exposed via `GET /mapping/contradiction`, `GET /mapping/impact`, and `GET /admin/diagnostics`.

Detected contradictions are surfaced as structured review output rather than silently resolved, supporting legal quality control.

### 4. AI Reasoning Layer

- **ChatbotEngine** (LangChain LCEL, `backend/services/chatbot_engine.py`): retrieval-grounded Q&A and section summaries with cited sources and a confidence label.
- **LegalTransitionAgent** (LangGraph, `backend/services/agent_graph.py`): explicit state graph `extract → retrieve → validate → compose`, with a **refuse branch** when no mappings match. Only the final compose step uses an LLM; extraction, retrieval, and validation are deterministic.
- **ML ranking** (`backend/ml`): scikit-learn TF-IDF + cosine similarity model behind `POST /rank`, with Matplotlib evaluation (`docs/ml_evaluation.png`).
- **LLM resolution order:** Anthropic (`claude-haiku-4-5` default) → OpenAI (`gpt-4o-mini` default) → `DeterministicLegalLLM`, a fully offline fallback that composes grounded answers from retrieved context only. The platform is usable and testable with no API keys.

### 5. Audit / Trace Layer

Every agent run returns a step-by-step `trace` (one entry per graph node: extract, retrieve, validate, compose/refuse) plus references, sources with scores, contradictions, and confidence — so every answer is reviewable.

### 6. API & Auth Layer

FastAPI application (`backend/main.py`, version **1.4.0**) with request logging middleware and a global exception handler.

Public: `POST /login` · `POST /logout` · `GET /health` · `GET /search` · `GET /mapping` · `GET /mapping/contradiction` · `GET /mapping/impact`

Auth required 🔒 (`Authorization: Bearer <token>` from `POST /login`): `GET /me` · `POST /chat` · `POST /chat/summary` · `POST /agent` · `POST /rank` · `GET /admin/*`

JWT bearer auth protects the chat, agent, ranking and admin endpoints. Set `AUTH_SECRET_KEY` in production (the dev default is forgeable); the frontend keeps the JWT in `localStorage`, which is demo-grade — prefer httpOnly cookies for production. Demo analyst account (configurable via `AUTH_USERNAME` / `AUTH_PASSWORD`):

```
username: analyst
password: nyayasetu2026
```

### 7. MCP Integration Layer

`backend/mcp_server` exposes the platform to MCP clients (Claude Desktop, Claude Code) via five tools: `search_sections`, `get_mapping`, `detect_contradictions`, `summarize_section`, `ask_legal_agent`.

```
python -m backend.mcp_server.server
```

See `backend/mcp_server/README.md` for registration instructions.

### 8. Frontend Layer

Next.js 14 + TypeScript + Tailwind CSS + lucide-react. Pages: landing, search, chat (with a **Chat / Agent (audit trace)** mode toggle), section detail, dashboard, admin, login.

### 9. Quality & Ops Layer

- **pytest suite:** 207 passing backend tests (`tests/`), plus a Playwright E2E spec (`tests/e2e/test_search_flow.py`).
- **E2E smoke script:** `scripts/e2e_smoke.py` walks the full analyst journey (login → mapping lookup → verification → chat/agent → rank) against a running backend.
- **CI:** GitHub Actions (`.github/workflows/ci.yml`) — flake8 lint + full test run with coverage artifact.
- **Docker:** `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`.

## Workflow Pipeline

1. **Input Ingestion** — accept legal text or section references.
2. **Reference Extraction** — detect and normalize IPC/BNS references.
3. **Candidate Mapping Generation** — retrieve candidates from canonical mapping data.
4. **Deterministic Rule Pass** — exact-code and keyword scoring with explicit precedence.
5. **AI-Assisted Reasoning Pass** — grounded composition where deterministic output needs explanation.
6. **Validation & Scoring** — confidence bands from deterministic scores.
7. **Contradiction Detection** — flag conflicting mappings; cap confidence and mark for review.
8. **Human Review Output** — ranked suggestions with citations, confidence, and audit trail.

## Tech Stack

- **Backend:** FastAPI, Python 3.10+, SQLAlchemy 2.0 (SQLite), Pandas
- **AI/Agents:** LangChain (grounded chatbot), LangGraph (multi-step agent with audit trace), MCP server, deterministic offline fallback LLM
- **ML:** Scikit-learn TF-IDF ranking model (NumPy/Pandas/Matplotlib evaluation)
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, lucide-react
- **Data/Rules:** JSON mapping assets + SQLite mirror (`backend/db`)
- **Ops:** Docker + docker-compose, GitHub Actions CI, pytest (207 tests) + Playwright E2E

## Running with Docker

```
docker compose up --build
# backend -> http://localhost:8000  |  frontend -> http://localhost:3000
```

Optional: set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `docker-compose.yml` to enable a real LLM; otherwise the deterministic fallback is used.

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### E2E Smoke Test

With the backend running:

```bash
python scripts/e2e_smoke.py
```

## Repository Structure

```text
ipc-bns-transition-platform/
├── frontend/   # Next.js + TypeScript UI
├── backend/    # FastAPI services, DB, ML, MCP server
├── data/       # IPC-BNS mapping and rule data
├── tests/      # pytest suite + Playwright E2E
├── scripts/    # E2E smoke script
└── docs/       # Architecture, API, security, and design docs
```

## Documentation

- [Architecture](docs/architecture.md)
- [MVP Scope](docs/mvp_scope.md)
- [API Design](docs/api_design.md)
- [Security Plan](docs/security_plan.md)
- [Data Model](docs/data_model.md)
