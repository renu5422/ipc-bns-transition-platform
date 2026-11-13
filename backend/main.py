import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import admin, auth, search
from backend.api.agent import router as agent_router
from backend.api.chat import router as chat_router
from backend.api.mapping import router as mapping_router
from backend.api.ml import router as ml_router
from backend.services.mapping_service import MappingService

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("ipc_bns")

app = FastAPI(
    title="IPC-BNS Transition Platform API",
    version="1.5.0",
    description="AI-assisted legal migration platform for IPC-BNS cross-referencing.",
)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path,
                response.status_code, elapsed_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. The incident has been logged."},
    )


app.include_router(auth.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(mapping_router)
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(ml_router)


@app.get("/health")
def health():
    svc = MappingService()
    return {
        "status": "ok",
        "version": app.version,
        "mapping_count": len(svc._records),
    }
