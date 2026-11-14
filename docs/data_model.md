# Data Model

## Source of truth

`data/ipc_bns_mapping.json` is a JSON array of mapping records (482 in v1.5.0).
`MappingService` loads it into memory at startup; every API route, the chatbot,
the agent, the ML ranker and the MCP server read from this dataset.

`data/sample_sections.json` holds a single example record in the same shape and
is not read by the application.

## Mapping record

```json
{
  "id": "1",
  "ipc_code": "IPC-302",
  "ipc_title": "Murder",
  "bns_code": "BNS-101",
  "bns_title": "Homicide",
  "description": "Punishment for murder and unlawful killing offenses.",
  "chapter": "Offences Against Human Body",
  "keywords": ["murder", "homicide", "killing"],
  "ai_summary": "This section explains offenses related to unlawful killing and corresponding punishments.",
  "validation_rules": ["keyword_match", "chapter_match"],
  "created_at": "2026-05-02T10:00:00Z",
  "updated_at": "2026-05-02T10:00:00Z"
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | Unique record id |
| `ipc_code` | string | `IPC-<number>` |
| `ipc_title` | string | IPC section title |
| `bns_code` | string | `BNS-<number>` |
| `bns_title` | string | BNS section title |
| `description` | string | Short description of the offence |
| `chapter` | string | Chapter name; used for impact analysis |
| `keywords` | string[] | Search keywords; weighted 2x in scoring |
| `ai_summary` | string | Pre-written plain-language summary |
| `validation_rules` | string[] | Rule tags attached to the record |
| `created_at`, `updated_at` | string | ISO 8601 timestamps |

`MappingService.validate_schema()` requires every record to contain `id`,
`ipc_code`, `ipc_title`, `bns_code`, `bns_title`, `description`, `chapter`,
`keywords`, `ai_summary` and `validation_rules`. `/admin/diagnostics` reports
the result.

## Code normalisation

Codes are compared after lower-casing and removing spaces, hyphens and
underscores, so `IPC-302`, `ipc 302` and `IPC_302` match the same record. The
chatbot and agent extract references from free text with the pattern
`(IPC|BNS)[ -_]?<1-4 digits + optional letter>` and normalise them to
`IPC-302` form.

## Derived data

These are computed at request time, not stored:

| Concept | Source | Shape |
|---|---|---|
| Search hit | `MappingService.search` | `{ id, score, record }` |
| Contradiction | `MappingService.detect_contradictions` | `{ type: "duplicate_ipc" \| "duplicate_bns", code, ids[] }`; raised when a normalised code appears in more than one record |
| Impact | `/mapping/impact` | Records sharing the target's chapter and/or any keyword |
| Confidence | chatbot / agent | `high` (top score >= 10, i.e. exact code match), `medium` (>= 3), `low` (> 0), `none`; contradictions cap the agent at `medium` |
| ML score | `MLRankingModel.rank` | TF-IDF cosine similarity in `[0, 1]` |

## Database layer (optional)

`backend/db` mirrors the JSON record in a relational table for deployments that
prefer a database. The API does not use it yet.

Table `section_mappings` (`SectionMappingORM`):

| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR(64) | Primary key |
| `ipc_code` | VARCHAR(32) | Indexed |
| `ipc_title` | VARCHAR(255) | |
| `bns_code` | VARCHAR(32) | Indexed |
| `bns_title` | VARCHAR(255) | |
| `description` | TEXT | |
| `chapter` | VARCHAR(255) | |
| `keywords` | JSON | list of strings |
| `ai_summary` | TEXT | |
| `validation_rules` | JSON | list of strings |
| `created_at`, `updated_at` | VARCHAR(64) | ISO 8601 strings |

- Connection: `DATABASE_URL`, default `sqlite:///./data/ipc_bns.db`.
- Seeding: `python -m backend.db.seed [path]` upserts by `id`, so re-running is idempotent.
- `SectionMappingORM.to_dict()` returns the exact JSON record shape, so
  `DBMappingService` reuses all `MappingService` logic unchanged.

## Users

There is no user table. One analyst account is configured through environment
variables (see [Security Plan](security_plan.md)).
