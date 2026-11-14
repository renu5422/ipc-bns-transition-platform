"""Unit tests for the LangGraph LegalTransitionAgent (Week 7)."""

import pytest

from backend.services.agent_graph import LegalTransitionAgent, extract_references
from backend.services.mapping_service import MappingService


@pytest.fixture
def agent(tmp_service) -> LegalTransitionAgent:
    """Agent with deterministic LLM over the minimal single-record dataset."""
    return LegalTransitionAgent(mapping_service=tmp_service)


class TestExtractReferences:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("what replaced IPC-302?", ["IPC-302"]),
            ("compare IPC 302 with BNS-101", ["IPC-302", "BNS-101"]),
            ("lowercase ipc302 works too", ["IPC-302"]),
            ("underscore bns_101 works", ["BNS-101"]),
            ("IPC-302 twice IPC-302 is deduped", ["IPC-302"]),
            ("what about IPC-498A cruelty?", ["IPC-498A"]),
            ("sedition ipc 124a", ["IPC-124A"]),
            ("no references here", []),
        ],
    )
    def test_extraction_and_normalisation(self, text, expected):
        assert extract_references(text) == expected


class TestAgentRun:
    def test_result_contract(self, agent):
        result = agent.run("what replaced IPC-302?")
        for field in ("answer", "references", "sources", "contradictions",
                      "confidence", "trace", "model"):
            assert field in result

    def test_full_pipeline_trace_has_four_steps(self, agent):
        result = agent.run("IPC-302")
        assert len(result["trace"]) == 5
        for step in ("extract", "retrieve", "validate", "compose", "grounding_check"):
            assert any(t.startswith(step) for t in result["trace"])

    def test_exact_reference_high_confidence(self, agent):
        result = agent.run("what replaced IPC-302?")
        assert result["references"] == ["IPC-302"]
        assert result["confidence"] == "high"
        assert result["sources"][0]["bns_code"] == "BNS-101"

    def test_answer_cites_codes(self, agent):
        result = agent.run("IPC-302")
        assert "IPC-302" in result["answer"]
        assert "BNS-101" in result["answer"]

    def test_keyword_query_without_reference_still_works(self, agent):
        result = agent.run("murder punishment")
        assert result["references"] == []
        assert len(result["sources"]) > 0

    def test_unknown_topic_refuses_via_refuse_branch(self, agent):
        result = agent.run("spacecraft launch permits")
        assert result["confidence"] == "none"
        assert result["sources"] == []
        assert "cannot find" in result["answer"].lower()
        assert any("refused" in t for t in result["trace"])

    def test_empty_question_raises(self, agent):
        with pytest.raises(ValueError):
            agent.run("   ")


class TestContradictionHandling:
    def test_duplicate_ipc_flags_contradiction(self, duplicate_ipc_file):
        agent = LegalTransitionAgent(
            mapping_service=MappingService(duplicate_ipc_file)
        )
        result = agent.run("IPC-302")
        assert len(result["contradictions"]) > 0
        assert result["contradictions"][0]["type"] == "duplicate_ipc"
        assert "human review" in result["answer"]

    def test_contradiction_caps_confidence_below_high(self, duplicate_ipc_file):
        agent = LegalTransitionAgent(
            mapping_service=MappingService(duplicate_ipc_file)
        )
        assert agent.run("IPC-302")["confidence"] != "high"

    def test_clean_data_has_no_contradictions(self, agent):
        assert agent.run("IPC-302")["contradictions"] == []
