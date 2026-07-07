# TARGET PATH IN REPO: tests/test_mcp_server.py
"""Tests for the Week 8 MCP server (backend/mcp_server/server.py).

These tests call the tool implementation functions directly -- no stdio
transport, no network, no API keys. The services fall back to the offline
DeterministicLegalLLM automatically, and the default MappingService loads
the real dataset from data/ipc_bns_mapping.json (which contains
IPC-302 -> BNS-101 and IPC-375 -> BNS-63).
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")

from backend.mcp_server import server
from backend.mcp_server.server import (
    ask_legal_agent,
    detect_contradictions,
    get_mapping,
    mcp,
    search_sections,
    summarize_section,
)


def test_server_name() -> None:
    assert mcp.name == "ipc-bns-legal-intelligence"


def test_search_sections_returns_results_for_murder() -> None:
    result = search_sections("murder", limit=10)
    assert isinstance(result, dict)
    assert result["query"] == "murder"
    assert result["count"] >= 1
    assert len(result["results"]) == result["count"]
    top = result["results"][0]
    assert set(top) >= {"id", "score", "record"}
    # Many sections mention murder (302, 307, 300, 303, 364...); the
    # exact-code record must be among the top hits, not necessarily first.
    top_codes = [r["record"]["ipc_code"] for r in result["results"]]
    assert "IPC-302" in top_codes


def test_get_mapping_known_code() -> None:
    result = get_mapping("IPC-302")
    assert "error" not in result
    assert result["code"] == "IPC-302"
    assert result["count"] >= 1
    record = result["mappings"][0]
    assert record["ipc_code"] == "IPC-302"
    assert record["bns_code"] == "BNS-101"


def test_get_mapping_normalizes_code() -> None:
    result = get_mapping("ipc 302")
    assert "error" not in result
    assert result["code"] == "IPC-302"
    assert result["mappings"][0]["bns_code"] == "BNS-101"


def test_get_mapping_unknown_code_returns_error_dict() -> None:
    result = get_mapping("IPC-99999")
    assert isinstance(result, dict)
    assert "error" in result
    assert "IPC-99999" in result["error"]


def test_summarize_section_mentions_both_codes() -> None:
    result = summarize_section("IPC-302")
    assert "error" not in result
    assert result["ipc_code"] == "IPC-302"
    assert result["bns_code"] == "BNS-101"
    summary = result["summary"]
    assert "IPC-302" in summary
    assert "BNS-101" in summary


def test_summarize_section_unknown_code_returns_error_dict() -> None:
    result = summarize_section("IPC-99999")
    assert isinstance(result, dict)
    assert "error" in result


def test_ask_legal_agent_trace_has_four_steps() -> None:
    result = ask_legal_agent("What replaced IPC-302 under the BNS?")
    assert set(result) >= {
        "answer",
        "references",
        "sources",
        "contradictions",
        "confidence",
        "trace",
        "model",
    }
    assert isinstance(result["trace"], list)
    assert len(result["trace"]) == 4
    assert "IPC-302" in result["references"]


def test_detect_contradictions_returns_dict_with_list() -> None:
    result = detect_contradictions()
    assert isinstance(result, dict)
    assert isinstance(result["contradictions"], list)
    assert result["count"] == len(result["contradictions"])


def test_services_are_lazy_singletons() -> None:
    svc_first = server._get_service()
    assert server._get_service() is svc_first
    assert server._get_engine() is server._get_engine()
    assert server._get_agent() is server._get_agent()
