# IPC-BNS Transition Platform

A web application to help legal professionals map Indian Penal Code (IPC) sections to their Bharatiya Nyaya Sanhita (BNS) equivalents.

## Project Structure
```
ipc-bns-app/
├── frontend/   # Next.js 14 + TypeScript
├── backend/    # FastAPI (Python)
├── data/       # IPC-BNS mapping JSON files
└── docs/       # Architecture, API design, security docs
```

## Quick Start

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

## Documentation
- [Architecture](docs/architecture.md)
- [MVP Scope](docs/mvp_scope.md)
- [API Design](docs/api_design.md)
- [Security Plan](docs/security_plan.md)
- [Data Model](docs/data_model.md)
