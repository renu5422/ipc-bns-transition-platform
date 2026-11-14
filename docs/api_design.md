# API Design

REST API served by FastAPI (`backend/main.py`, version `1.5.0`). Routes are
mounted at the root; there is no `/api/v1` prefix. Interactive OpenAPI docs are
served at `/docs` when the backend is running.

- Content type: `application/json`
- Auth: `Authorization: Bearer <JWT>` on protected routes (see [Security Plan](security_plan.md))
- Errors: FastAPI's standard `{"detail": ...}` body. Request validation failures
  return `422`; unhandled exceptions return a generic `500` without internals.

## Route summary

| Method | Path | Auth | Module | Purpose |
|---|---|---|---|---|
| POST | `/login` | Public | `api/auth.py` | Exchange credentials for a JWT |
| POST | `/logout` | Public | `api/auth.py` | Stateless; the client discards the token |
| GET | `/me` | **JWT** | `api/auth.py` | Current user identity |
| GET | `/health` | Public | `main.py` | Liveness, version, dataset size |
| GET | `/search` | Public | `api/search.py` | Keyword / code search over mappings |
| GET | `/mapping` | Public | `api/mapping.py` | IPC/BNS mapping lookup by code |
| GET | `/mapping/contradiction` | Public | `api/mapping.py` | Duplicate-code conflicts for a code |
| GET | `/mapping/impact` | Public | `api/mapping.py` | Related sections (same chapter / shared keywords) |
| POST | `/chat` | **JWT** | `api/chat.py` | Retrieval-grounded Q&A |
| POST | `/chat/summary` | **JWT** | `api/chat.py` | Summary for one section code |
| POST | `/agent` | **JWT** | `api/agent.py` | LangGraph multi-step pipeline with audit trace |
| POST | `/rank` | **JWT** | `api/ml.py` | TF-IDF cosine ranking |
| GET | `/admin/diagnostics` | **JWT** | `api/admin.py` | Dataset loaded / schema valid |
| GET | `/admin/health` | **JWT** | `api/admin.py` | Per-workflow self-checks |
| GET | `/admin/config/verify` | **JWT** | `api/admin.py` | Data fingerprint and duplicate codes |
| GET | `/admin/users` | **JWT** | `api/admin.py` | Placeholder, returns `{"users": []}` |
| POST | `/admin/upload` | **JWT** | `api/admin.py` | Placeholder, returns `{"message": "Not implemented"}` |

Protection is applied with `Depends(get_current_user)`, either on a single route
(`/me`) or on the whole router (`/chat`, `/agent`, `/rank`, `/admin`). A missing,
invalid or expired token returns `401` with `WWW-Authenticate: Bearer`.

## Authentication

### POST /login

```json
{ "username": "analyst", "password": "..." }
```

`200`:

```json
{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 3600 }
```

`401` on wrong credentials. `expires_in` equals `AUTH_TOKEN_TTL_MINUTES * 60`.

### GET /me

`200`: `{ "username": "analyst", "role": "analyst" }`

### POST /logout

`200`: `{ "message": "Logged out" }`. There is no server-side revocation; tokens
are stateless and expire on their own.

## Health

### GET /health

```json
{ "status": "ok", "version": "1.5.0", "mapping_count": 482 }
```

`mapping_count` is the number of records loaded from `data/ipc_bns_mapping.json`.

## Search and mapping (public)

### GET /search

| Param | Type | Default | Notes |
|---|---|---|---|
| `q` | string | required | Blank returns `400`. Characters other than letters, digits, whitespace and `-` are stripped. |
| `limit` | int | 10 | 1 to 50 |

```json
{
  "query": "IPC-302",
  "count": 1,
  "results": [ { "id": "1", "score": 10.0, "record": { "...": "full mapping record" } } ]
}
```

Scoring (`MappingService.search`): +10 for an exact normalised IPC or BNS code
match, +1 per token occurrence in titles, description, chapter and summary, +2
per token occurrence in keywords. Ties break on `id`, so ordering is deterministic.

### GET /mapping

| Param | Default | Notes |
|---|---|---|
| `code` | required | e.g. `IPC-302`, `BNS-101` |
| `direction` | `ipc_to_bns` | `ipc_to_bns` or `bns_to_ipc`; echoed back, does not filter results |

Returns `{ query_code, direction, count, mappings[] }`. Each mapping has
`ipc_code, ipc_title, bns_code, bns_title, description, chapter, keywords,
ai_summary, confidence`, where `confidence` is `HIGH` (score >= 10), `MEDIUM`
(>= 3) or `LOW`. Returns `404` if nothing matches.

### GET /mapping/contradiction

Param `code`. Returns `{ section_code, has_contradictions, count, contradictions[] }`;
each item is `{ type: "duplicate_ipc" | "duplicate_bns", code, conflicting_ids[], description }`.

### GET /mapping/impact

Param `section_id` (an IPC or BNS code). Returns:

```json
{
  "section_id": "IPC-302",
  "total_records": 482,
  "unique_chapters": ["..."],
  "impacted_sections": [
    { "section_id": "7", "ipc_code": "...", "bns_code": "...", "ipc_title": "...",
      "relationship": "same_chapter | keyword_overlap | same_chapter+keyword_overlap",
      "chapter": "..." }
  ],
  "validation_rules": ["..."]
}
```

## AI routes (JWT required)

### POST /chat

Request: `{ "question": "What replaced IPC-302?" }` (1 to 2000 characters).

```json
{
  "answer": "...",
  "sources": [ { "id": "1", "ipc_code": "IPC-302", "bns_code": "BNS-101", "score": 10.0 } ],
  "confidence": "high | medium | low | none",
  "model": "deterministic-legal"
}
```

`model` names the LLM in use; it is `deterministic-legal` when no LLM API key is
configured. Answers are grounded in the retrieved records, and a grounding
check verifies that every IPC/BNS code cited by the LLM appears in those records
(subsections matched exactly). Ungrounded codes are flagged for review, not
refused: confidence is capped at low, and `/chat` and `/agent` responses carry
`grounded` (bool) and `ungrounded_codes` (list).

### POST /chat/summary

Request: `{ "code": "IPC-302" }` (1 to 50 characters). Response:
`{ code, ipc_code, bns_code, summary, model }`. Returns `404` unless the code is
an exact match for a mapping record.

### POST /agent

Request: `{ "question": "..." }` (1 to 2000 characters).

```json
{
  "answer": "...",
  "references": ["IPC-302"],
  "sources": [ { "id": "1", "ipc_code": "IPC-302", "bns_code": "BNS-101", "score": 10.0 } ],
  "contradictions": [],
  "confidence": "high",
  "trace": [
    "extract: found 1 reference(s) ['IPC-302']",
    "retrieve: 1 mapping record(s) matched",
    "validate: 0 contradiction(s), confidence=high",
    "compose: answer generated"
  ],
  "model": "deterministic-legal"
}
```

### POST /rank

Request: `{ "query": "murder", "top_k": 5 }` (`top_k` 1 to 50). Response:
`{ query, results: [ { id, ml_score, ipc_code, bns_code, ipc_title } ], model: "tfidf-cosine" }`.
Returns `503` if the dataset cannot be loaded.

## Admin routes (JWT required)

- `GET /admin/diagnostics`: `{ status: "healthy" | "degraded", checks: { mapping_data_loaded, schema_valid }, mapping_count }`
- `GET /admin/health`: status of retrieval, ranking determinism, contradiction detection and impact analysis
- `GET /admin/config/verify`: `{ ok, data_fingerprint (SHA-256), duplicate_ipc_codes, duplicate_bns_codes }`
- `GET /admin/users`, `POST /admin/upload`: placeholders, not implemented

## MCP interface

The same services are exposed to MCP clients over stdio by
`backend/mcp_server/server.py` (server name `ipc-bns-legal-intelligence`):

| Tool | Behaviour |
|---|---|
| `search_sections(query, limit=5)` | Same search as `GET /search` |
| `get_mapping(code)` | Exact-code mapping lookup |
| `detect_contradictions()` | Duplicate-code scan of the full dataset |
| `summarize_section(code)` | Same as `POST /chat/summary` |
| `ask_legal_agent(question)` | Same pipeline as `POST /agent` |

The MCP server runs as a local process launched by the client and does not use
JWT auth. See `backend/mcp_server/README.md` for client registration.
