from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import admin, auth, search
from backend.api.mapping import router as mapping_router
from backend.services.mapping_service import MappingService

app = FastAPI(
    title="IPC-BNS Transition Platform API",
    version="1.1.0",
    description="AI-assisted legal migration platform for IPC ↔ BNS cross-referencing.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(mapping_router)


@app.get("/health")
def health():
    svc = MappingService()
    return {
        "status": "ok",
        "version": "1.1.0",
        "mapping_count": len(svc._records),
    }
