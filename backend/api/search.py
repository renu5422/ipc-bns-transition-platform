from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/search")
async def search_sections(q: str = Query(..., min_length=1)):
    # TODO: implement IPC/BNS section search
    return {"query": q, "results": []}
