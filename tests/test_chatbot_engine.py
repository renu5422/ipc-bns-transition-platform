# TARGET PATH IN REPO: tests/test_chatbot_engine.py
"""Unit tests for the LangChain ChatbotEngine (Week 6)."""

from typing import Any

import pytest
from langchain_core.language_models.llms import LLM

from backend.services.chatbot_engine import (
    ChatbotEngine,
    DeterministicLegalLLM,
    _confidence,
)
from backend.services.prompts import (
    CHAT_PROMPT,
    CONTEXT_BEGIN,
    CONTEXT_END,
    format_context,
)


class MockLLM(LLM):
    """Injectable fake LLM — proves the engine is LLM-agnostic."""

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _call(self, prompt: str, stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any) -> str:
        return "MOCKED ANSWER"


@pytest.fixture
def engine(tmp_service) -> ChatbotEngine:
    """Engine with deterministic LLM over the minimal single-record dataset."""
    return ChatbotEngine(mapping_service=tmp_service)


class TestAsk:
    def test_answer_cites_both_codes(self, engine):
        result = engine.ask("what happened to murder sections")
        assert "IPC-302" in result["answer"]
        assert "BNS-101" in result["answer"]

    def test_result_contract(self, engine):
        result = engine.ask("murder")
        for field in ("answer", "sources", "confidence", "model"):
            assert field in result

    def test_sources_reference_matched_record(self, engine):
        result = engine.ask("murder")
        assert result["sources"][0]["ipc_code"] == "IPC-302"
        assert result["sources"][0]["bns_code"] == "BNS-101"
        assert result["sources"][0]["score"] > 0

    def test_exact_code_query_is_high_confidence(self, engine):
        assert engine.ask("IPC-302")["confidence"] == "high"

    def test_natural_language_with_code_is_high_confidence(self, engine):
        """Regression: codes embedded in sentences must still match exactly."""
        result = engine.ask("what replaced IPC-302?")
        assert result["confidence"] == "high"
        assert "BNS-101" in result["answer"]

    def test_unknown_topic_refuses_gracefully(self, engine):
        result = engine.ask("helicopter licensing rules")
        assert result["confidence"] == "none"
        assert result["sources"] == []
        assert "cannot find" in result["answer"].lower()

    def test_empty_question_raises(self, engine):
        with pytest.raises(ValueError):
            engine.ask("   ")

    def test_injected_llm_is_used(self, tmp_service):
        eng = ChatbotEngine(llm=MockLLM(), mapping_service=tmp_service)
        result = eng.ask("murder")
        assert result["answer"] == "MOCKED ANSWER"
        assert result["model"] == "mock"


class TestSummarize:
    def test_summary_mentions_both_codes(self, engine):
        result = engine.summarize("IPC-302")
        assert "IPC-302" in result["summary"]
        assert "BNS-101" in result["summary"]

    def test_summary_handles_subsection_codes(self, tmp_path):
        """Regression: codes with parentheses like BNS-106(1) must parse."""
        import json
        from backend.services.mapping_service import MappingService
        record = {
            "id": "sub-1", "ipc_code": "IPC-304A", "ipc_title": "Causing death by negligence",
            "bns_code": "BNS-106(1)", "bns_title": "Causing death by negligence",
            "description": "Causing death by a rash or negligent act.",
            "chapter": "Offences Against Human Body",
            "keywords": ["negligence", "rash act", "death"],
            "ai_summary": "Negligence causing death.",
            "validation_rules": ["keyword_match"],
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
        }
        f = tmp_path / "sub.json"
        f.write_text(json.dumps([record]), encoding="utf-8")
        eng = ChatbotEngine(mapping_service=MappingService(f))
        result = eng.summarize("IPC-304A")
        assert "BNS-106(1)" in result["summary"]
        assert "cannot find" not in result["summary"].lower()

    def test_summary_mentions_chapter(self, engine):
        result = engine.summarize("IPC-302")
        assert "Offences Against Human Body" in result["summary"]

    def test_bns_code_also_resolves(self, engine):
        result = engine.summarize("BNS-101")
        assert result["ipc_code"] == "IPC-302"

    def test_unknown_code_raises_lookup_error(self, engine):
        with pytest.raises(LookupError):
            engine.summarize("IPC-9999")

    def test_empty_code_raises_value_error(self, engine):
        with pytest.raises(ValueError):
            engine.summarize("")


class TestDeterministicLLM:
    def test_same_input_same_output(self):
        llm = DeterministicLegalLLM()
        prompt = CHAT_PROMPT.format(context="[IPC-302 -> BNS-101] Murder -> Homicide", question="q")
        assert llm.invoke(prompt) == llm.invoke(prompt)

    def test_no_context_refuses(self):
        llm = DeterministicLegalLLM()
        prompt = CHAT_PROMPT.format(context="(no matching mapping records found)", question="q")
        assert "cannot find" in llm.invoke(prompt).lower()


class TestPromptsAndHelpers:
    def test_chat_prompt_contains_grounding_markers(self):
        rendered = CHAT_PROMPT.format(context="CTX", question="Q")
        assert CONTEXT_BEGIN in rendered
        assert CONTEXT_END in rendered
        assert "Never invent section numbers" in rendered

    def test_format_context_empty(self):
        assert "no matching" in format_context([])

    @pytest.mark.parametrize(
        "score,expected",
        [(12.0, "high"), (10.0, "high"), (5.0, "medium"), (1.0, "low"), (0.0, "none")],
    )
    def test_confidence_thresholds(self, score, expected):
        assert _confidence(score) == expected
