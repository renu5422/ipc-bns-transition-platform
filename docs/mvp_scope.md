# Product Scope

## Problem

Since 1 July 2024 the Bharatiya Nyaya Sanhita (BNS) has replaced the Indian
Penal Code (IPC). Existing case files, charge sheets and research still cite IPC
sections, and analysts need to find the BNS equivalent quickly and with a
traceable source.

## Users

- Legal analysts and researchers migrating IPC references to BNS
- Developers and AI assistants that need the mapping as a tool (via MCP)

## Core flows

1. **Look up a section**: enter `IPC 302` or a keyword such as `murder`; see
   the matching BNS section, chapter, keywords and summary.
2. **Check related sections**: view sections in the same chapter or with shared
   keywords, and any conflicting (duplicate-code) mappings.
3. **Ask a question** (signed in): ask in natural language and get an answer
   that cites the mapping records it used, with a confidence level.
4. **Run the agent** (signed in): get an answer plus contradictions and a
   step-by-step audit trace.
5. **Use from an AI client**: call the same capabilities as MCP tools.

## In scope (v1.5.0)

| Area | Capability |
|---|---|
| Search | Code and keyword search with deterministic scoring |
| Mapping | IPC/BNS lookup, contradiction detection, impact analysis |
| Chat | Retrieval-grounded Q&A and per-section summaries with cited sources; grounding check on cited codes (v1.5.x) |
| Agent | LangGraph pipeline: extract, retrieve, validate, compose or refuse, with trace |
| ML ranking | TF-IDF cosine ranking with an offline evaluation script |
| MCP | Five tools over stdio for MCP-capable clients |
| Auth | JWT login for one analyst account; AI, ML and admin routes protected |
| Admin | Diagnostics, self-checks and data fingerprint |
| Frontend | Search, section detail, dashboard, chat, admin and login pages |
| Delivery | Docker compose, GitHub Actions CI with coverage gate and Playwright E2E (v1.5.x) |

All features run offline without LLM API keys; a real Anthropic or OpenAI model
is used when a key is configured.

## Out of scope

- Multiple users, sign-up, or role-based permissions
- Editing or uploading mappings through the UI or API (`/admin/upload` is a placeholder)
- Full statutory text; records hold titles, descriptions and summaries only
- Vector search / embeddings-based RAG
- Multilingual content
- Legal advice: answers describe the mapping data and are not a legal opinion

## Success criteria

- Searching `IPC 302` returns the mapped BNS section.
- Chat and agent answers cite only codes present in the retrieved records, and
  refuse when no validated mapping is found.
- Agent responses include sources, contradictions, confidence and trace.
- Protected routes return `401` without a valid token.
- CI passes lint, unit/API tests with the coverage gate, and E2E tests.

## Known limitations

- The mapping dataset is curated in JSON; the database layer exists but the API
  does not read from it yet.
- Auth is demo-grade (single account, token in `localStorage`); see
  [Security Plan](security_plan.md).
- Search is lexical; synonyms not present in titles, descriptions or keywords
  will not match.
