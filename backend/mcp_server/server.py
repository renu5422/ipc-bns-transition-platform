"""MCP server exposing the IPC->BNS transition platform as Model Context Protocol tools.

Week 8 deliverable: wraps the existing service layer (MappingService,
ChatbotEngine, LegalTransitionAgent) behind five MCP tools so that any
MCP-capable client (Claude Desktop, Claude Code, custom agents) can search
mappings, fetch section details, detect contradictions, summarize sections,
and run the full agentic Q&A pipeline.

Run over stdio (the default MCP transport):

    python -m backend.mcp_server.server

Design notes
------------
* Services are lazy singletons: importing this module does NOT load the
  mapping dataset or build any LLM client. Each is constructed on first use,
  which keeps imports cheap and makes the module trivially testable.
* Every tool body lives in a plain, directly-callable module-level function.
  ``mcp.tool()`` is applied by *calling* the decorator on the function after
  its definition, so the module-level names always refer to the undecorated
  callables. Tests import and call them directly -- no stdio, no transport.
* The default LLM inside ChatbotEngine / LegalTransitionAgent is the
  offline DeterministicLegalLLM, so no API keys are required.
"""

from __future__ import annotations

import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from backend.services.agent_graph import LegalTransitionAgent
from backend.services.chatbot_engine import ChatbotEngine
from backend.services.mapping_service import MappingService

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("ipc-bns-legal-intelligence")

# ---------------------------------------------------------------------------
# Lazy service singletons
# ---------------------------------------------------------------------------

_svc: MappingService | None = None
_engine: ChatbotEngine | None = None
_agent: LegalTransitionAgent | None = None


def _get_service() -> MappingService:
    """Return the shared MappingService, creating it on first use."""
    global _svc
    if _svc is None:
        _svc = MappingService()
    return _svc


def _get_engine() -> ChatbotEngine:
    """Return the shared ChatbotEngine (deterministic offline LLM by default)."""
    global _engine
    if _engine is None:
        _engine = ChatbotEngine(mapping_service=_get_service())
    return _engine


def _get_agent() -> LegalTransitionAgent:
    """Return the shared LegalTransitionAgent (full audit-trace pipeline)."""
    global _agent
    if _agent is None:
        _agent = LegalTransitionAgent(mapping_service=_get_service())
    return _agent


def _normalize_code(code: str) -> str:
    """Normalize a section code: 'ipc 302' / 'IPC_302' / ' ipc-302 ' -> 'IPC-302'."""
    normalized = re.sub(r"[\s_]+", "-", code.strip().upper())
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized


def _record_as_dict(record: Any) -> dict[str, Any]:
    """Best-effort conversion of a mapping record to a plain JSON-safe dict."""
    if isinstance(record, dict):
        return dict(record)
    if hasattr(record, "__dict__"):
        return dict(vars(record))
    return {"record": str(record)}


# ---------------------------------------------------------------------------
# Tool implementations (plain, directly-callable functions)
# ---------------------------------------------------------------------------


def search_sections(query: str, limit: int = 5) -> dict:
    """Search IPC/BNS section mappings by keyword, code, or free text.

    Args:
        query: Free-text search query (e.g. "murder", "IPC-302", "consent").
        limit: Maximum number of results to return (default 5).

    Returns:
        A dict with the query, result count, and scored results. Each result
        contains an ``id``, a relevance ``score``, and the full mapping
        ``record`` (ipc_code, bns_code, titles, description, chapter, ...).
    """
    hits = _get_service().search(query, limit=limit)
    return {
        "query": query,
        "count": len(hits),
        "results": [
            {
                "id": hit["id"],
                "score": hit["score"],
                "record": _record_as_dict(hit["record"]),
            }
            for hit in hits
        ],
    }


def get_mapping(code: str) -> dict:
    """Look up the IPC<->BNS mapping(s) for a specific section code.

    Args:
        code: A section code such as "IPC-302", "BNS-101", "ipc 375".
              Case, spaces, and underscores are normalized automatically.

    Returns:
        On success: {"code": <normalized>, "count": N, "mappings": [record, ...]}.
        On failure: {"error": "<message>", "code": <normalized>}.
    """
    normalized = _normalize_code(code)
    if not normalized:
        return {"error": "Empty section code.", "code": normalized}

    hits = _get_service().search(normalized, limit=10)
    strong_hits = [hit for hit in hits if hit["score"] >= 10]

    # Prefer records whose ipc_code / bns_code exactly matches the query.
    exact: list[dict[str, Any]] = []
    for hit in strong_hits:
        record = _record_as_dict(hit["record"])
        codes = {
            _normalize_code(str(record.get("ipc_code", ""))),
            _normalize_code(str(record.get("bns_code", ""))),
        }
        if normalized in codes:
            exact.append(record)

    mappings = exact or [_record_as_dict(hit["record"]) for hit in strong_hits]
    if not mappings:
        return {"error": f"No mapping found for section code '{normalized}'.", "code": normalized}
    return {"code": normalized, "count": len(mappings), "mappings": mappings}


def detect_contradictions() -> dict:
    """Scan the full IPC->BNS mapping dataset for contradictions.

    Detects issues such as duplicate or conflicting code assignments across
    the mapping records.

    Returns:
        {"count": N, "contradictions": [{"type", "code", "ids"}, ...]}.
        An empty list means the dataset is internally consistent.
    """
    contradictions = _get_service().detect_contradictions()
    return {"count": len(contradictions), "contradictions": contradictions}


def summarize_section(code: str) -> dict:
    """Produce a plain-language summary of a specific IPC or BNS section.

    Args:
        code: The section code to summarize (e.g. "IPC-302" or "BNS-101").

    Returns:
        On success: {"code", "ipc_code", "bns_code", "summary", "model"}.
        If the code is unknown or empty: {"error": "<message>", "code": <input>}.
    """
    try:
        return _get_engine().summarize(_normalize_code(code))
    except (LookupError, ValueError) as exc:
        return {"error": str(exc), "code": code}


def ask_legal_agent(question: str) -> dict:
    """Ask the multi-step legal transition agent a question (full audit trace).

    Runs the complete pipeline: reference extraction -> retrieval ->
    contradiction check -> answer synthesis. Slower than a plain search but
    returns provenance for every step.

    Args:
        question: A natural-language legal question, e.g.
            "What replaced IPC-302 under the BNS?"

    Returns:
        {"answer", "references", "sources", "contradictions", "confidence",
         "trace", "model"} -- ``trace`` lists every pipeline step executed.
    """
    return _get_agent().run(question)


# ---------------------------------------------------------------------------
# Tool registration (applied post-definition so module names stay plain
# callables for direct use in tests)
# ---------------------------------------------------------------------------

mcp.tool()(search_sections)
mcp.tool()(get_mapping)
mcp.tool()(detect_contradictions)
mcp.tool()(summarize_section)
mcp.tool()(ask_legal_agent)


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
