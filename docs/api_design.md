# API Design

Base URL:

```text
/api/v1
```

---

# Authentication

## POST /api/v1/auth/login

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

## POST /api/v1/auth/logout

Invalidate current session/token.

### Response

```json
{
  "message": "Logged out successfully"
}
```

---

# Search

## GET /api/v1/search

Search IPC/BNS mappings.

### Query Params

```text
?q={query}
```

### Example

```text
/api/v1/search?q=IPC 302
```

### Response

```json
{
  "query": "IPC 302",
  "count": 1,
  "results": [
    {
      "id": "1",
      "ipc_code": "IPC 302",
      "ipc_title": "Murder",

      "bns_code": "BNS 101",
      "bns_title": "Homicide",

      "description": "Punishment for murder",

      "keywords": [
        "murder",
        "homicide"
      ]
    }
  ]
}
```

---

# Admin

## GET /api/v1/admin/users

Get all registered users.

### Authorization

```text
Bearer Token Required
Admin Role Required
```

---

## POST /api/v1/admin/upload

Upload IPC ↔ BNS mapping dataset.

### Authorization

```text
Bearer Token Required
Admin Role Required
```

### Accepted Format

```text
JSON
```

---

# Security Notes

- validate all inputs
- sanitize search queries
- restrict admin endpoints
- avoid exposing sensitive data
- implement rate limiting later