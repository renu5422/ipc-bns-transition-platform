# Security Plan

This document describes the security controls implemented in v1.5.0 and the
known gaps. The platform is a research/demo deployment with a single analyst
account; it is not hardened for production use.

## Authentication

Implemented in `backend/api/auth.py`.

| Control | Implementation |
|---|---|
| Login | `POST /login` checks username and password against one configured analyst account |
| Password storage | bcrypt hash via passlib `CryptContext`; the configured password is hashed at startup and verified with `verify()` |
| Tokens | JWT signed with HS256 (python-jose). Claims: `sub` (username) and `exp` |
| Token lifetime | `AUTH_TOKEN_TTL_MINUTES`, default 60 |
| Verification | `get_current_user` dependency: requires a Bearer header, verifies signature and expiry, requires a `sub` claim; otherwise `401` with `WWW-Authenticate: Bearer` |
| Logout | Stateless; the client deletes its token. Tokens remain valid until `exp` |

Configuration (environment variables):

| Variable | Purpose |
|---|---|
| `AUTH_USERNAME` | Analyst username |
| `AUTH_PASSWORD` | Analyst password (hashed with bcrypt at startup) |
| `AUTH_SECRET_KEY` | JWT signing key. **Must be set to a strong random value in production**; the built-in default is for local development only |
| `AUTH_TOKEN_TTL_MINUTES` | Token lifetime in minutes |

## Authorization

There is one role (`analyst`). Routes are either public or require a valid JWT.

| Access | Routes |
|---|---|
| Public | `POST /login`, `POST /logout`, `GET /health`, `GET /search`, `GET /mapping`, `GET /mapping/contradiction`, `GET /mapping/impact` |
| JWT required | `GET /me`, `POST /chat`, `POST /chat/summary`, `POST /agent`, `POST /rank`, all `/admin/*` routes |

Read-only mapping lookups stay public; routes that invoke an LLM, the ML model
or diagnostics are protected at router level with `Depends(get_current_user)`.

## Input validation

- Pydantic models on every request body: questions 1 to 2000 characters, summary
  codes 1 to 50, `top_k` 1 to 50; login fields must be non-empty.
- `GET /search`: blank queries return `400`; characters other than letters,
  digits, whitespace and `-` are stripped; `limit` is bounded to 1 to 50.
- `GET /mapping`: `direction` is restricted to `ipc_to_bns` or `bns_to_ipc`.
- No SQL is built from user input; the API reads an in-memory dataset.

## AI safety

- Prompts (`backend/services/prompts.py`) restrict the model to the retrieved
  mapping records, require citing section codes, and require refusal when the
  context is insufficient.
- The agent refuses when retrieval finds nothing and flags answers for human
  review when contradictory mappings are detected.
- v1.5.x adds a grounding check: any IPC/BNS code in an LLM answer that is not
  in the retrieved records causes the answer to be refused or flagged.
- Without an LLM API key, the offline deterministic LLM is used, so no data
  leaves the host.

## Transport, CORS and error handling

- CORS origins come from `CORS_ORIGINS` (default `http://localhost:3000`).
- Unhandled exceptions are logged server-side and returned as a generic `500`
  without stack traces.
- Each request is logged with method, path, status and latency; request bodies
  and tokens are not logged.
- TLS is expected to be terminated by the hosting platform or a reverse proxy;
  the app itself serves plain HTTP.

## Secrets

- Secrets (`AUTH_SECRET_KEY`, `AUTH_PASSWORD`, `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`) are read from environment variables, not from code.
- `.env` files must not be committed; `.env.example` documents the variables.

## Frontend token storage

The JWT is stored in `localStorage` (`frontend/src/services/api.ts`). This is
demo-grade: any XSS on the frontend origin could read the token. The client
clears the token on any `401`. A production deployment should use an `httpOnly`,
`Secure`, `SameSite` cookie instead.

## Not yet done

- No rate limiting or lockout on `POST /login`.
- No token revocation, refresh tokens or server-side sessions.
- Single hard-configured account; no user store or role-based permissions
  (`/admin/users` and `/admin/upload` are placeholders).
- JWT kept in `localStorage` rather than an `httpOnly` cookie.
- No security headers (CSP, HSTS) configured by the app.
- No audit log of authenticated actions beyond request logging.
- MCP server has no authentication; it is intended to run locally under the
  user's own MCP client.
