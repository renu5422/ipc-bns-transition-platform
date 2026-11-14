"""Tests for the post-generation grounding check (item 13)."""

import os
from typing import Any

import pytest
from langchain_core.language_models.llms import LLM

from backend.api.agent import AgentResponse
from backend.api.chat import ChatResponse
from backend.services.agent_graph import LegalTransitionAgent
from backend.services.chatbot_engine import ChatbotEngine, DeterministicLegalLLM
from backend.services.grounding import (
    REFUSAL_MESSAGE,
    cap_confidence,
    check_grounding,
    extract_references,
    grounded_codes,
)

RECORD = {"id": "r1", "ipc_code": "IPC-302", "bns_code": "BNS-101"}
SUBSECTION_RECORD = {"id": "r2", "ipc_code": "IPC-304A", "bns_code": "BNS-106(1)"}


class FixedLLM(LLM):
    """Mock LLM returning a fixed answer (e.g. a hallucinated citation)."""

    answer: str = ""

    @property
    def _llm_type(self) -> str:
        return "fixed-mock"

    def _call(self, prompt: str, stop: list[str] | None = None,
              run_manager: Any = None, **kwargs: Any) -> str:
        return self.answer


HALLUCINATING = "IPC-302 maps to BNS-101. See also BNS-999 for aggravated cases."


# ── Helper unit tests ──────────────────────────────────────────────────────

class TestCheckGrounding:
    def test_grounded_answer(self):
        result = check_grounding("IPC-302 maps to BNS-101.", [RECORD])
        assert result == {
            "grounded": True,
            "cited_codes": ["IPC-302", "BNS-101"],
            "ungrounded_codes": [],
        }

    def test_ungrounded_code_is_reported(self):
        result = check_grounding(HALLUCINATING, [RECORD])
        assert result["grounded"] is False
        assert result["ungrounded_codes"] == ["BNS-999"]

    def test_no_codes_in_answer_is_grounded(self):
        result = check_grounding("Murder is now covered by the new code.", [RECORD])
        assert result["grounded"] is True
        assert result["cited_codes"] == []

    def test_no_records_and_a_cited_code_is_ungrounded(self):
        assert check_grounding("IPC-302 maps to BNS-101", [])["ungrounded_codes"] == [
            "IPC-302", "BNS-101",
        ]

    @pytest.mark.parametrize("cited", ["BNS-106", "BNS-106(1)", "BNS-106(2)", "bns 106"])
    def test_subsections_normalise_to_section(self, cited):
        assert check_grounding(f"see {cited}", [SUBSECTION_RECORD])["grounded"] is True

    def test_letter_suffix_is_significant(self):
        result = check_grounding("IPC-304 applies", [SUBSECTION_RECORD])
        assert result["ungrounded_codes"] == ["IPC-304"]
        assert check_grounding("IPC-304A applies", [SUBSECTION_RECORD])["grounded"]

    def test_record_codes_in_loose_format_are_normalised(self):
        assert grounded_codes([{"ipc_code": "IPC 302", "bns_code": "bns_101"}]) == {
            "IPC-302", "BNS-101",
        }

    def test_codes_echoed_from_question_are_allowed(self):
        result = check_grounding("IPC-999 has no validated mapping.", [], "what is IPC-999?")
        assert result["grounded"] is True

    def test_refusal_example_code_is_not_a_citation(self):
        assert check_grounding(REFUSAL_MESSAGE, [])["grounded"] is True

    @pytest.mark.parametrize("before,after", [
        ("high", "low"), ("medium", "low"), ("low", "low"), ("none", "none"),
    ])
    def test_cap_confidence(self, before, after):
        assert cap_confidence(before) == after

    def test_extract_references_reexported_from_engine(self):
        from backend.services.chatbot_engine import extract_references as engine_fn
        assert engine_fn is extract_references


# ── ChatbotEngine integration ──────────────────────────────────────────────

class TestChatbotEngineGrounding:
    def test_deterministic_llm_answer_is_grounded(self, tmp_service):
        engine = ChatbotEngine(llm=DeterministicLegalLLM(), mapping_service=tmp_service)
        result = engine.ask("what replaced IPC-302?")
        assert result["grounded"] is True
        assert result["ungrounded_codes"] == []
        assert result["confidence"] == "high"
        assert "WARNING" not in result["answer"]

    def test_deterministic_refusal_is_grounded(self, tmp_service):
        engine = ChatbotEngine(llm=DeterministicLegalLLM(), mapping_service=tmp_service)
        result = engine.ask("spacecraft launch permits")
        assert result["grounded"] is True
        assert result["confidence"] == "none"

    def test_hallucinated_code_is_flagged(self, tmp_service):
        engine = ChatbotEngine(llm=FixedLLM(answer=HALLUCINATING), mapping_service=tmp_service)
        result = engine.ask("what replaced IPC-302?")
        assert result["grounded"] is False
        assert result["ungrounded_codes"] == ["BNS-999"]
        assert result["confidence"] == "low"  # capped from high
        assert result["answer"].startswith(HALLUCINATING)  # flagged, not replaced
        assert "flagged for human review" in result["answer"]
        assert "BNS-999" in result["answer"].split("WARNING")[1]

    def test_response_model_accepts_and_defaults_fields(self, tmp_service):
        engine = ChatbotEngine(llm=FixedLLM(answer=HALLUCINATING), mapping_service=tmp_service)
        model = ChatResponse(**engine.ask("IPC-302"))
        assert model.grounded is False and model.ungrounded_codes == ["BNS-999"]
        legacy = ChatResponse(answer="a", sources=[], confidence="none", model="m")
        assert legacy.grounded is True and legacy.ungrounded_codes == []


# ── LangGraph agent path ───────────────────────────────────────────────────

class TestAgentGrounding:
    def test_trace_includes_grounding_step(self, tmp_service):
        result = LegalTransitionAgent(mapping_service=tmp_service).run("IPC-302")
        assert result["trace"][-1].startswith("grounding_check:")
        assert result["grounded"] is True
        assert result["ungrounded_codes"] == []

    def test_refuse_branch_also_runs_grounding_check(self, tmp_service):
        result = LegalTransitionAgent(mapping_service=tmp_service).run("spacecraft permits")
        assert result["trace"][-1].startswith("grounding_check:")
        assert result["grounded"] is True

    def test_hallucinated_code_is_flagged_in_agent(self, tmp_service):
        agent = LegalTransitionAgent(
            llm=FixedLLM(answer=HALLUCINATING), mapping_service=tmp_service
        )
        result = agent.run("what replaced IPC-302?")
        assert result["grounded"] is False
        assert result["ungrounded_codes"] == ["BNS-999"]
        assert result["confidence"] == "low"
        assert "BNS-999" in result["trace"][-1]
        assert "flagged for human review" in result["answer"]
        AgentResponse(**result)  # API contract still validates


# ── Live LLM (opt-in) ──────────────────────────────────────────────────────

@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set (live LLM test)"
)
@pytest.mark.parametrize("question", [
    "What replaced IPC-302, and which BNS sections cover attempt to murder and dowry death?",
    "List every BNS section that deals with theft and robbery.",
])
def test_live_anthropic_no_unflagged_ungrounded_codes(mapping_service, question):
    pytest.importorskip("langchain_anthropic")
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model=os.getenv("CHATBOT_MODEL", "claude-haiku-4-5"), temperature=0)
    result = ChatbotEngine(llm=llm, mapping_service=mapping_service).ask(question)

    answer = result["answer"].split("\n\nWARNING:")[0]
    allowed = grounded_codes(result["sources"]) | set(extract_references(question))
    unsupported = [c for c in extract_references(answer) if c not in allowed]
    if unsupported:
        assert result["grounded"] is False
        assert set(unsupported) <= set(result["ungrounded_codes"])
        assert result["confidence"] in ("low", "none")
    else:
        assert result["grounded"] is True
