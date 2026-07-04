# TARGET PATH IN REPO: backend/api/agent.py
"""Agent API — multi-step LangGraph pipeline with audit trace.

Route:
    POST /agent — run the extract→retrieve→validate→compose pipeline
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.services.agent_graph import LegalTransitionAgent

router = APIRouter(prefix="/agent", tags=["agent"])

_agent: LegalTransitionAgent | None = None


def get_agent() -> LegalTransitionAgent:
    """Lazily build a singleton agent (overridable in tests)."""
    global _agent
    if _agent is None:
        _agent = LegalTransitionAgent()
    return _agent


class AgentRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceModel(BaseModel):
    id: str
    ipc_code: str
    bns_code: str
    score: float


class AgentResponse(BaseModel):
    answer: str
    references: list[str]
    sources: list[SourceModel]
    contradictions: list[dict]
    confidence: str  # high | medium | low | none
    trace: list[str]
    model: str


@router.post("", response_model=AgentResponse)
def run_agent(
    req: AgentRequest, agent: LegalTransitionAgent = Depends(get_agent)
) -> AgentResponse:
    try:
        return AgentResponse(**agent.run(req.question))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
