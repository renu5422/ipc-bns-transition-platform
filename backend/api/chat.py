# TARGET PATH IN REPO: backend/api/chat.py
"""Chat API — conversational access to the validated mapping pipeline.

Routes:
    POST /chat          — ask a question, get a grounded, cited answer
    POST /chat/summary  — generate an AI summary for one section code
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.services.chatbot_engine import ChatbotEngine

router = APIRouter(prefix="/chat", tags=["chatbot"])

_engine: ChatbotEngine | None = None


def get_engine() -> ChatbotEngine:
    """Lazily build a singleton engine (overridable in tests)."""
    global _engine
    if _engine is None:
        _engine = ChatbotEngine()
    return _engine


# ── Schemas ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceModel(BaseModel):
    id: str
    ipc_code: str
    bns_code: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceModel]
    confidence: str  # high | medium | low | none
    model: str


class SummaryRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)


class SummaryResponse(BaseModel):
    code: str
    ipc_code: str
    bns_code: str
    summary: str
    model: str


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, engine: ChatbotEngine = Depends(get_engine)) -> ChatResponse:
    try:
        return ChatResponse(**engine.ask(req.question))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/summary", response_model=SummaryResponse)
def summary(req: SummaryRequest, engine: ChatbotEngine = Depends(get_engine)) -> SummaryResponse:
    try:
        return SummaryResponse(**engine.summarize(req.code))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
