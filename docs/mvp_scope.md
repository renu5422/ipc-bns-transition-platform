# MVP Scope

---

# Product Vision

The IPC-BNS Transition Platform is a modern AI-assisted legal search platform designed to help legal professionals, students, and researchers quickly map IPC sections to their Bharatiya Nyaya Sanhita (BNS) equivalents.

The platform combines:

- fast legal search
- structured mapping visualization
- AI-assisted legal explanations
- secure role-based access
- scalable architecture

---

# Core User Flow

```text
User enters IPC/BNS code or keyword
        ↓
System searches mappings
        ↓
Matching section displayed
        ↓
AI-generated explanation shown
        ↓
User understands IPC ↔ BNS transition
```

---

# In Scope (MVP)

## Priority 1 (Critical)

- search IPC section by code
- search BNS section by code
- keyword-based search
- display mapped section details
- fast search response (<1 second)

---

## Priority 2 (Important)

- login/logout system
- role separation (`admin` vs `user`)
- secure protected routes

---

## Priority 3 (AI Layer)

- AI-generated legal explanation
- AI-assisted search suggestions

---

## Priority 4 (Optional if time permits)

- admin upload/update mapping JSON
- search filters

---

# Out of Scope (MVP)

The following are intentionally excluded from MVP:

- multi-agent systems
- autonomous AI workflows
- vector databases
- semantic RAG pipelines
- multilingual support
- analytics dashboards
- mobile native app
- notifications
- complex admin CMS

---

# Success Criteria

The MVP is successful if:

- user can search `IPC 302`
- matching BNS section appears in under 1 second
- search results are accurate
- AI explanation generates successfully
- authentication works reliably
- admin routes remain protected
- application deploys successfully

---

# MVP Constraints

To maintain delivery speed:

- JSON storage used instead of PostgreSQL
- lightweight AI integration only
- minimal authentication complexity
- clean UI prioritized over excessive animations

---

# Risk Management

Potential risks:

- overengineering AI features
- feature explosion
- architecture complexity growth
- unfinished implementation

Mitigation strategy:

- prioritize core search first
- limit AI to one feature initially
- keep services modular
- avoid unnecessary infrastructure complexity