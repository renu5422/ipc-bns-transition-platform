"""Tests for the post-generation grounding check (item 13)."""

import json
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
    is_grounded,
)
from backend.services.mapping_service import MappingService

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

    @pytest.mark.parametrize("cited", ["BNS-106(1)", "bns 106 (1)", "BNS_106( 1 )"])
    def test_exact_subsection_is_grounded(self, cited):
        assert check_grounding(f"see {cited}", [SUBSECTION_RECORD])["grounded"] is True

    def test_wrong_subsection_is_flagged(self):
        result = check_grounding("see BNS-106(2)", [SUBSECTION_RECORD])
        assert result["grounded"] is False
        assert result["ungrounded_codes"] == ["BNS-106(2)"]

    @pytest.mark.parametrize("cited", ["BNS-106", "bns 106"])
    def test_bare_parent_of_retrieved_subsection_is_grounded(self, cited):
        assert check_grounding(f"see {cited}", [SUBSECTION_RECORD])["grounded"] is True

    def test_subsection_of_bare_record_is_ungrounded(self):
        """Chosen rule: a bare record does not vouch for a specific subsection."""
        result = check_grounding("BNS-101(1) applies", [RECORD])
        assert result["ungrounded_codes"] == ["BNS-101(1)"]

    def test_mixed_answer_lists_only_wrong_subsection(self):
        result = check_grounding(
            "BNS-106(1) covers rash acts; BNS-106(2) covers hit-and-run.",
            [SUBSECTION_RECORD],
        )
        assert result["cited_codes"] == ["BNS-106(1)", "BNS-106(2)"]
        assert result["ungrounded_codes"] == ["BNS-106(2)"]

    def test_nested_subsections_match_exactly(self):
        rec = {"ipc_code": "IPC-379", "bns_code": "BNS-137(1)(a)"}
        assert check_grounding("BNS-137(1)(a)", [rec])["grounded"]
        assert check_grounding("BNS-137", [rec])["grounded"]
        assert check_grounding("BNS-137(1)(b)", [rec])["ungrounded_codes"] == ["BNS-137(1)(b)"]
        assert check_grounding("BNS-137(1)", [rec])["ungrounded_codes"] == ["BNS-137(1)"]

    def test_subsection_letter_case_is_normalised(self):
        rec = {"ipc_code": "IPC-420", "bns_code": "BNS-326(a)"}
        assert check_grounding("BNS-326(A)", [rec])["grounded"]

    def test_subsection_from_question_is_allowed_exactly(self):
        question = "what is BNS-106(2)?"
        assert check_grounding("BNS-106(2) is not in the dataset.", [], question)["grounded"]
        assert not check_grounding("BNS-106(3) instead", [], question)["grounded"]


class TestExtractReferencesSubsections:
    @pytest.mark.parametrize("text,default,keep", [
        ("BNS-106(1)", ["BNS-106"], ["BNS-106(1)"]),
        ("bns 106 (2)", ["BNS-106"], ["BNS-106(2)"]),
        ("BNS-137(1)(a)", ["BNS-137"], ["BNS-137(1)(a)"]),
        ("BNS-326(A)", ["BNS-326"], ["BNS-326(a)"]),
        ("IPC-302 (Murder) and IPC-376 (Rape)", ["IPC-302", "IPC-376"], ["IPC-302", "IPC-376"]),
        ("IPC-304A", ["IPC-304A"], ["IPC-304A"]),
        ("Section 106(1)", [], []),
    ])
    def test_default_drops_and_keep_preserves_subsections(self, text, default, keep):
        assert extract_references(text) == default
        assert extract_references(text, keep_subsections=True) == keep

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


SUB_RECORD_FULL = {
    "id": "sub-1",
    "ipc_code": "IPC-304A",
    "ipc_title": "Death by negligence",
    "bns_code": "BNS-106(1)",
    "bns_title": "Death by negligence",
    "description": "Causing death by negligence.",
    "chapter": "Offences Against Human Body",
    "keywords": ["negligence"],
    "ai_summary": "Negligent death.",
}
WRONG_SUB = "IPC-304A maps to BNS-106(1); hit-and-run falls under BNS-106(2)."


@pytest.fixture
def sub_service(tmp_path):
    f = tmp_path / "sub.json"
    f.write_text(json.dumps([SUB_RECORD_FULL]), encoding="utf-8")
    return MappingService(f)


class TestWrongSubsectionBothPaths:
    def test_chat_path_flags_wrong_subsection(self, sub_service):
        engine = ChatbotEngine(llm=FixedLLM(answer=WRONG_SUB), mapping_service=sub_service)
        result = engine.ask("what replaced IPC-304A?")
        assert result["grounded"] is False
        assert result["ungrounded_codes"] == ["BNS-106(2)"]
        assert result["confidence"] == "low"
        assert "BNS-106(2)" in result["answer"].split("WARNING")[1]

    def test_agent_path_flags_wrong_subsection(self, sub_service):
        agent = LegalTransitionAgent(llm=FixedLLM(answer=WRONG_SUB), mapping_service=sub_service)
        result = agent.run("what replaced IPC-304A?")
        assert result["grounded"] is False
        assert result["ungrounded_codes"] == ["BNS-106(2)"]
        assert result["confidence"] == "low"
        assert "BNS-106(2)" in result["trace"][-1]

    def test_deterministic_subsection_answer_is_grounded(self, sub_service):
        llm = DeterministicLegalLLM()
        for runner in (ChatbotEngine(llm=llm, mapping_service=sub_service).ask,
                       LegalTransitionAgent(llm=llm, mapping_service=sub_service).run):
            result = runner("IPC-304A")
            assert "BNS-106(1)" in result["answer"]
            assert result["grounded"] is True


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
    allowed = grounded_codes(result["sources"]) | set(
        extract_references(question, keep_subsections=True)
    )
    cited = extract_references(answer, keep_subsections=True)
    unsupported = [c for c in cited if not is_grounded(c, allowed)]
    if unsupported:
        assert result["grounded"] is False
        assert set(unsupported) <= set(result["ungrounded_codes"])
        assert result["confidence"] in ("low", "none")
    else:
        assert result["grounded"] is True
