# TARGET PATH IN REPO: backend/api/ml.py
"""FastAPI router exposing the ML (TF-IDF cosine) ranking endpoint.

The ranker is a lazy in-process singleton: on the first request the model
is fitted in memory from ``data/ipc_bns_mapping.json``. The trained joblib
artifact produced by ``python -m backend.ml.train`` is NOT required, so
the endpoint works on a fresh checkout. Tests (and alternative wiring)
can override the :func:`get_ranker` dependency via
``app.dependency_overrides``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.ml.ranking_model import MLRankingModel

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_PATH: Path = REPO_ROOT / "data" / "ipc_bns_mapping.json"

router = APIRouter(prefix="/rank", tags=["ml"])

_ranker: MLRankingModel | None = None


class RankRequest(BaseModel):
    """Request body for the ranking endpoint."""

    query: str = Field(..., min_length=1, description="Free-text search query.")
    top_k: int = Field(5, ge=1, le=50, description="Maximum number of results.")


class RankResultItem(BaseModel):
    """One ranked mapping record (flattened for API consumers)."""

    id: str
    ml_score: float
    ipc_code: str
    bns_code: str
    ipc_title: str


class RankResponse(BaseModel):
    """Response body for the ranking endpoint."""

    query: str
    results: list[RankResultItem]
    model: str = "tfidf-cosine"


def _load_records(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    """Read mapping records from the JSON dataset (list or wrapped list)."""
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        for value in raw.values():
            if isinstance(value, list):
                raw = value
                break
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"No mapping records found in {path}")
    return raw


def get_ranker() -> MLRankingModel:
    """Return the cached ranker, fitting it in memory on first use.

    Overridable FastAPI dependency (see ``app.dependency_overrides``).

    Raises:
        HTTPException: 503 if the dataset is missing or unreadable.
    """
    global _ranker
    if _ranker is not None and _ranker.is_fitted:
        return _ranker
    try:
        _ranker = MLRankingModel().fit(_load_records())
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Ranking model unavailable: {exc}",
        ) from exc
    return _ranker


def reset_ranker(model: MLRankingModel | None = None) -> None:
    """Replace (or clear) the cached ranker. Useful for tests or retraining."""
    global _ranker
    _ranker = model


@router.post("", response_model=RankResponse)
def rank_mappings(
    payload: RankRequest,
    ranker: MLRankingModel = Depends(get_ranker),
) -> RankResponse:
    """Rank IPC->BNS mapping records against a query by TF-IDF cosine similarity."""
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="query must not be blank.")

    try:
        hits = ranker.rank(query, top_k=payload.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = [
        RankResultItem(
            id=hit["id"],
            ml_score=hit["ml_score"],
            ipc_code=str(hit["record"].get("ipc_code", "")),
            bns_code=str(hit["record"].get("bns_code", "")),
            ipc_title=str(hit["record"].get("ipc_title", "")),
        )
        for hit in hits
    ]
    return RankResponse(query=query, results=results)
