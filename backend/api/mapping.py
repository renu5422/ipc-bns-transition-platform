"""
Mapping API — IPC ↔ BNS cross-reference routes.

Endpoints:
  GET /mapping          — look up BNS sections for an IPC code (or vice versa)
  GET /contradiction    — detect conflicts for a given IPC or BNS code
  GET /impact           — dependency impact for a given section
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.mapping_service import mapping_service


router = APIRouter(prefix="/mapping", tags=["mapping"])


# ── Response models ─────────────────────────────────────────────────────────

class MappingResult(BaseModel):
    ipc_code: str
    ipc_title: str
    bns_code: str
    bns_title: str
    description: str
    chapter: str
    keywords: list[str]
    ai_summary: str
    confidence: str


class MappingResponse(BaseModel):
    query_code: str
    direction: str
    count: int
    mappings: list[MappingResult]


class ContradictionItem(BaseModel):
    type: str
    code: str
    conflicting_ids: list[str]
    description: str


class ContradictionResponse(BaseModel):
    section_code: str
    has_contradictions: bool
    count: int
    contradictions: list[ContradictionItem]


class ImpactItem(BaseModel):
    section_id: str
    ipc_code: str
    bns_code: str
    ipc_title: str
    relationship: str
    chapter: str


class ImpactResponse(BaseModel):
    section_id: str
    total_records: int
    unique_chapters: list[str]
    impacted_sections: list[ImpactItem]
    validation_rules: list[str]


# ── Routes ──────────────────────────────────────────────────────────────────

@router.get("", response_model=MappingResponse)
def get_mapping(
    code: str = Query(..., description="IPC or BNS section code, e.g. IPC-302 or BNS-101"),
    direction: str = Query("ipc_to_bns", regex="^(ipc_to_bns|bns_to_ipc)$"),
):
    """
    Return all mapping records matching the given IPC or BNS code.
    Uses the same normalised matching as the search endpoint.
    """
    if not code or not code.strip():
        raise HTTPException(status_code=400, detail="code must not be empty.")

    results = mapping_service.search(code.strip(), limit=20)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No mappings found for code '{code}'. "
                   "Check the section code format (e.g. IPC-302, BNS-101).",
        )

    mappings = []
    for r in results:
        rec = r["record"]
        # Filter by direction: for ipc_to_bns, prefer records where ipc_code matches
        score = r["score"]
        confidence = "HIGH" if score >= 10 else "MEDIUM" if score >= 3 else "LOW"
        mappings.append(MappingResult(
            ipc_code=rec.get("ipc_code", ""),
            ipc_title=rec.get("ipc_title", ""),
            bns_code=rec.get("bns_code", ""),
            bns_title=rec.get("bns_title", ""),
            description=rec.get("description", ""),
            chapter=rec.get("chapter", ""),
            keywords=rec.get("keywords", []),
            ai_summary=rec.get("ai_summary", ""),
            confidence=confidence,
        ))

    return MappingResponse(
        query_code=code.strip(),
        direction=direction,
        count=len(mappings),
        mappings=mappings,
    )


@router.get("/contradiction", response_model=ContradictionResponse)
def get_contradictions(
    code: str = Query(..., description="IPC or BNS section code to check for conflicts"),
):
    """
    Detect contradictions (duplicate or conflicting mappings) for a given code.
    """
    if not code or not code.strip():
        raise HTTPException(status_code=400, detail="code must not be empty.")

    all_contradictions = mapping_service.detect_contradictions()

    from backend.services.mapping_service import _normalize
    norm = _normalize(code.strip())

    relevant = [
        c for c in all_contradictions
        if c.get("code") == norm or norm in c.get("code", "")
    ]

    items = [
        ContradictionItem(
            type=c["type"],
            code=c["code"],
            conflicting_ids=c["ids"],
            description=(
                f"Duplicate {'IPC' if c['type'] == 'duplicate_ipc' else 'BNS'} "
                f"code '{c['code']}' found in {len(c['ids'])} records: {', '.join(c['ids'])}"
            ),
        )
        for c in relevant
    ]

    return ContradictionResponse(
        section_code=code.strip(),
        has_contradictions=len(items) > 0,
        count=len(items),
        contradictions=items,
    )


@router.get("/impact", response_model=ImpactResponse)
def get_impact(
    section_id: str = Query(..., description="IPC or BNS section code for impact analysis"),
):
    """
    Return impact analysis: total records, unique chapters, and related sections
    that share a chapter or keywords with the given section.
    """
    if not section_id or not section_id.strip():
        raise HTTPException(status_code=400, detail="section_id must not be empty.")

    analysis = mapping_service.analyze_impact()

    # Find related sections: those sharing chapter or keyword with the queried section
    target_results = mapping_service.search(section_id.strip(), limit=1)
    impacted: list[ImpactItem] = []

    if target_results:
        target_rec = target_results[0]["record"]
        target_chapter = target_rec.get("chapter", "")
        target_keywords = set(target_rec.get("keywords", []))

        for rec in mapping_service._records:
            if rec.get("id") == target_results[0]["id"]:
                continue  # skip self
            rec_keywords = set(rec.get("keywords", []))
            same_chapter = rec.get("chapter", "") == target_chapter
            keyword_overlap = bool(rec_keywords & target_keywords)
            if same_chapter or keyword_overlap:
                relationship = "same_chapter" if same_chapter else "keyword_overlap"
                if same_chapter and keyword_overlap:
                    relationship = "same_chapter+keyword_overlap"
                impacted.append(ImpactItem(
                    section_id=rec["id"],
                    ipc_code=rec.get("ipc_code", ""),
                    bns_code=rec.get("bns_code", ""),
                    ipc_title=rec.get("ipc_title", ""),
                    relationship=relationship,
                    chapter=rec.get("chapter", ""),
                ))

    return ImpactResponse(
        section_id=section_id.strip(),
        total_records=analysis["total_records"],
        unique_chapters=analysis["unique_chapters"],
        impacted_sections=impacted,
        validation_rules=analysis["validation_rules"],
    )
