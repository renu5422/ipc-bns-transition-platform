# Architecture

The IPC-BNS Transition Platform helps legal analysts move references from the
Indian Penal Code (IPC) to the Bharatiya Nyaya Sanhita (BNS). It combines a
deterministic mapping engine with retrieval-grounded AI features, served by a
FastAPI backend, a Next.js frontend and an MCP server.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, axios |
| Backend | FastAPI, Pydantic v2, Uvicorn |
| AI | LangChain Core (LCEL prompts), LangGraph (agent state graph) |
| LLM | Anthropic or OpenAI via LangChain when an API key is set; offline `DeterministicLegalLLM` otherwise |
| ML | scikit-learn TF-IDF + cosine similarity, pandas, numpy, joblib, matplotlib |
| Data | JSON dataset (`data/ipc_bns_mapping.json`); optional SQLAlchemy 2.0 layer (SQLite by default) |
| Auth | JWT (HS256, python-jose), bcrypt (passlib) |
| Tool protocol | MCP (`mcp` FastMCP, stdio transport) |
| Delivery | Docker / docker compose, GitHub Actions CI |

## High-level view

```text
Browser (Next.js)          MCP client (Claude Desktop, Claude Code, ...)
      |  HTTP + Bearer JWT          |  stdio
      v                             v
FastAPI app (backend/main.py)   MCP server (backend/mcp_server/server.py)
  routers: auth, search, mapping,       tools: search_sections, get_mapping,
  chat, agent, rank, admin              detect_contradictions, summarize_section,
      |                                 ask_legal_agent
      +--------------+------------------+
                     v
            Service layer (backend/services)
  MappingService  ChatbotEngine  LegalTransitionAgent  DiagnosticsService
                     |                      MLRankingModel (backend/ml)
                     v
            data/ipc_bns_mapping.json   (optional: SQLite via backend/db)
```

## Backend

`backend/main.py` creates the FastAPI app (version `1.5.0`), configures CORS
from `CORS_ORIGINS`, logs every request with method, path, status and latency,
and converts unhandled exceptions into a generic `500`. It mounts seven routers;
see [API Design](api_design.md) for the full route list.

### Services

| Module | Responsibility |
|---|---|
| `services/mapping_service.py` | Loads the JSON dataset into memory; deterministic keyword/code scoring (`search`), duplicate-code detection (`detect_contradictions`), impact analysis, schema validation |
| `services/db_mapping_service.py` | `DBMappingService`, a `MappingService` subclass that loads records from the `section_mappings` table instead of JSON. Used by the DB test suite; the API currently reads JSON |
| `services/prompts.py` | LangChain `PromptTemplate`s with explicit context markers and grounding rules (answer only from context, cite codes, refuse when context is insufficient) |
| `services/chatbot_engine.py` | `ChatbotEngine`: extracts section codes from the question, retrieves top-k records, runs `prompt \| llm \| parser`, returns answer, sources and confidence |
| `services/agent_graph.py` | `LegalTransitionAgent`: LangGraph pipeline with an audit trace |
| `services/diagnostics_service.py` | Self-checks behind `/admin/*` (data loaded, schema valid, ranking determinism, SHA-256 data fingerprint) |

### LLM selection

`resolve_default_llm()` picks, in order: Anthropic (`ANTHROPIC_API_KEY`),
OpenAI (`OPENAI_API_KEY`), else `DeterministicLegalLLM`. The model name can be
overridden with `CHATBOT_MODEL`. The deterministic LLM composes answers purely
from the retrieved context, so the chat, agent and MCP features work offline and
produce repeatable output for tests.

### Agent pipeline

```text
START -> extract -> retrieve --(hits)--> validate -> compose -> END
                        \--(no hits)--> refuse ---------------> END
```

- **extract**: regex-normalises IPC/BNS references (`ipc 302` -> `IPC-302`)
- **retrieve**: top-k records via `MappingService.search`
- **validate**: finds duplicate-code contradictions among the hits; contradictions cap confidence at `medium`
- **compose**: the only LLM step; appends a human-review warning when contradictions exist
- **refuse**: fixed "no validated mapping" answer with confidence `none`

Every node appends a line to `trace`, which is returned to the caller.

In v1.5.x the chatbot also runs a grounding check: every IPC/BNS code in an LLM
answer must exist in the retrieved records, otherwise the answer is refused or
flagged for review.

### ML ranking

`backend/ml/ranking_model.py` builds a TF-IDF corpus from each record's codes,
titles, description, chapter, keywords and summary, and ranks queries by cosine
similarity. `POST /rank` fits the model in memory on first use, so no trained
artifact is required. `python -m backend.ml.train` evaluates the model (top-1
accuracy and MRR on queries generated from the records), saves a joblib
artifact and writes `docs/ml_evaluation.png`.

### Persistence

The API serves the JSON dataset held in memory. `backend/db` provides an
optional SQLAlchemy layer: `database.py` (engine from `DATABASE_URL`, default
`sqlite:///./data/ipc_bns.db`), `models.py` (`SectionMappingORM`) and `seed.py`
(idempotent upsert from JSON, `python -m backend.db.seed`). See
[Data Model](data_model.md).

## Frontend

Next.js App Router pages under `frontend/src/app`: `search`, `section`,
`dashboard`, `chat`, `admin` and `login`. All HTTP calls go through
`frontend/src/services/api.ts`, an axios client that attaches the stored JWT as a
Bearer header and clears it on any `401` (except from `/login`). The API base
URL comes from `NEXT_PUBLIC_API_URL`.

## Request flow examples

Public search:

```text
GET /search?q=IPC 302 -> validate + sanitise -> MappingService.search -> scored records
```

Authenticated agent question:

```text
POST /agent (Bearer JWT) -> get_current_user -> LegalTransitionAgent.run
  -> extract -> retrieve -> validate -> compose -> answer + sources + trace
```

## Deployment and CI

- `docker compose up --build` runs the backend on port 8000 and the frontend on
  port 3000. The backend image has a `HEALTHCHECK` on `/health`.
- GitHub Actions (`.github/workflows/ci.yml`) runs flake8 and the pytest suite
  with a coverage gate; v1.5.x adds a Playwright end-to-end job.

## Design principles

- **Deterministic core**: search, contradiction detection and ranking are
  reproducible; the LLM only phrases answers.
- **Grounded AI**: prompts restrict the model to retrieved records and require
  refusal when the context is insufficient.
- **Traceability**: agent responses carry sources, confidence and a step-by-step trace.
- **Works offline**: no API keys are needed to run or test any feature.
