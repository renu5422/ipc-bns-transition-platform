import re
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.mapping_service import mapping_service

router = APIRouter()


def validate_search_query(query: str) -> str:
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    return query.strip()


def sanitize_input(query: str) -> str:
    return re.sub(r"[^\w\s\-]", "", query)


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[dict]


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(...), limit: int = Query(10, ge=1, le=50)):
    query = validate_search_query(q)
    query = sanitize_input(query)
    results = mapping_service.search(query, limit=limit)
    return SearchResponse(query=query, count=len(results), results=results)
