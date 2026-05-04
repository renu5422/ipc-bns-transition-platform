# API Design

---

# Base URL

```text
/api/v1
```

---

# Overview

The API layer powers the IPC-BNS Transition Platform by handling:

- authentication
- legal section search
- IPC ↔ BNS mapping retrieval
- AI-assisted legal explanations
- admin management operations

The API follows a modular REST-based architecture.

---

# Authentication Endpoints

---

## POST `/api/v1/auth/login`

Authenticate user and return access token.

### Request

```json
{
  "username": "string",
  "password": "string"
}
```

### Response

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "role": "admin"
}
```

---

## POST `/api/v1/auth/logout`

Logout current user session.

### Response

```json
{
  "message": "Logged out successfully"
}
```

---

# Search Endpoints

---

## GET `/api/v1/search`

Search IPC or BNS mappings.

### Query Parameters

```text
?q={query}
```

### Example

```text
/api/v1/search?q=IPC 302
```

---

### Response

```json
{
  "query": "IPC 302",

  "count": 1,

  "results": [
    {
      "id": "1",

      "ipc_code": "IPC-302",
      "ipc_title": "Murder",

      "bns_code": "BNS-101",
      "bns_title": "Homicide",

      "description": "Punishment for murder",

      "chapter": "Offences Against Human Body",

      "keywords": [
        "murder",
        "homicide"
      ]
    }
  ]
}
```

---

# AI Endpoints

---

## POST `/api/v1/ai/explain`

Generate AI-assisted explanation for IPC ↔ BNS mapping.

### Request

```json
{
  "ipc_code": "IPC-302"
}
```

---

### Response

```json
{
  "ipc_code": "IPC-302",

  "bns_code": "BNS-101",

  "ai_summary": "This section relates to unlawful killing offenses and explains how IPC provisions transition into BNS equivalents."
}
```

---

## POST `/api/v1/ai/suggest`

Generate intelligent search suggestions.

### Request

```json
{
  "query": "murder"
}
```

---

### Response

```json
{
  "suggestions": [
    "IPC-302",
    "BNS-101",
    "homicide"
  ]
}
```

---

# Admin Endpoints

---

## GET `/api/v1/admin/users`

Retrieve registered users.

### Authorization

```text
Bearer token required
Admin role required
```

---

### Response

```json
{
  "count": 1,

  "users": [
    {
      "id": "1",
      "username": "admin",
      "role": "admin"
    }
  ]
}
```

---

## POST `/api/v1/admin/upload`

Upload new IPC ↔ BNS mapping dataset.

### Authorization

```text
Bearer token required
Admin role required
```

---

### Accepted Format

```text
JSON
```

---

### Response

```json
{
  "message": "Mapping uploaded successfully"
}
```

---

# Error Response Format

All errors follow a consistent structure.

### Example

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Query parameter is required"
  }
}
```

---

# Security Design

Security protections include:

- protected admin endpoints
- token-based authentication
- input sanitization
- request validation
- secure role enforcement

Future improvements:

- rate limiting
- audit logging
- refresh tokens

---

# Performance Goals

Target performance requirements:

- search response < 1 second
- lightweight API payloads
- scalable search structure

---

# API Design Goals

The API is designed for:

- maintainability
- modularity
- scalability
- AI integration support
- secure request handling
- frontend/backend separation