# Architecture

---

# Overview

The IPC-BNS Transition Platform is a modern AI-assisted legal search application designed to help users transition from Indian Penal Code (IPC) references to Bharatiya Nyaya Sanhita (BNS) equivalents.

The system combines:

- structured legal search
- AI-assisted explanations
- secure access control
- scalable modular architecture

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, Uvicorn |
| AI Layer | AI explanation service |
| Data Layer | JSON storage (future PostgreSQL support) |
| Authentication | Token-based authentication |

---

# High-Level Architecture

```text
Browser
   ↓
Next.js Frontend
   ↓
FastAPI Backend
   ↓
Search Service
   ↓
AI Service
   ↓
JSON Storage / Future Database
```

---

# System Layers

| Layer | Responsibility |
|---|---|
| UI Layer | pages, search UI, result rendering |
| API Layer | routing, validation, authentication |
| Service Layer | business logic, mapping lookup |
| AI Layer | legal explanation generation |
| Data Layer | IPC ↔ BNS mapping storage |

---

# Frontend Responsibilities

Frontend handles:

- search interface
- AI explanation rendering
- authentication UI
- responsive design
- client-side validation

---

# Backend Responsibilities

Backend handles:

- search requests
- authentication validation
- admin operations
- mapping lookup logic
- AI explanation requests
- request validation

---

# Service Architecture

| Service | Responsibility |
|---|---|
| mapping_service.py | IPC ↔ BNS lookup logic |
| search_service.py | query handling and filtering |
| ai_service.py | AI-generated explanations |
| auth_service.py | authentication logic |

---

# Data Flow

```text
User Query
    ↓
Frontend Search Request
    ↓
Backend API Endpoint
    ↓
Search Service
    ↓
Mapping Service
    ↓
Mapping Result
    ↓
AI Service Enhancement
    ↓
Formatted Response
    ↓
Frontend Rendering
```

---

# Security Design

Security measures include:

- protected admin routes
- token authentication
- input sanitization
- request validation
- secure config handling

Future improvements:

- rate limiting
- audit logging
- RBAC expansion

---

# Scalability Plan

Current MVP uses JSON storage for simplicity and fast iteration.

Future scalability options:

- PostgreSQL migration
- caching layer
- Elasticsearch integration
- advanced AI search assistance

---

# Architecture Goals

The architecture prioritizes:

- maintainability
- modularity
- scalability
- fast search performance
- secure request handling
- controlled AI integration