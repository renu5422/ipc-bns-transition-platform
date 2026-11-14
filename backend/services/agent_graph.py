"""LangGraph multi-step legal transition agent (Week 7).

Implements the README workflow pipeline as an explicit state graph:

    extract_references -> retrieve_mappings -> validate -> compose_answer
                                   \\ (no hits) ------------^
    compose_answer | refuse -> grounding_check

Each node appends to an audit ``trace`` (README "Audit/Trace Layer"), so
every answer is reviewable step by step. The LLM is only used in the
compose step; extraction, retrieval, validation, and the final
``grounding_check`` (every cited IPC/BNS code must appear in the retrieved
records — see ``backend.services.grounding``) are deterministic.
"""

from typing import Any, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START, StateGraph

from backend.services.chatbot_engine import (
    _confidence,
    extract_references,
    resolve_default_llm,
)
from backend.services.grounding import (
    REFUSAL_MESSAGE,
    cap_confidence,
    check_grounding,
    warning_for,
)
from backend.services.mapping_service import MappingService
from backend.services.prompts import CHAT_PROMPT, format_context


class AgentState(TypedDict, total=False):
    question: str
    references: list[str]          # normalised section codes found in the text
    hits: list[dict[str, Any]]     # retrieval results (id, score, record)
    contradictions: list[dict[str, Any]]
    confidence: str                # high | medium | low | none
    answer: str
    grounded: bool
    ungrounded_codes: list[str]    # cited codes absent from retrieved records
    trace: list[str]               # audit trail, one entry per step


class LegalTransitionAgent:
    """Multi-step agent over the validated mapping pipeline."""

    def __init__(
        self,
        llm: Any = None,
        mapping_service: MappingService | None = None,
        top_k: int = 3,
    ) -> None:
        self._svc = mapping_service or MappingService()
        self._llm = llm if llm is not None else resolve_default_llm()
        self._top_k = top_k
        self._compose_chain = CHAT_PROMPT | self._llm | StrOutputParser()
        self._graph = self._build_graph()

    @property
    def model_name(self) -> str:
        return getattr(self._llm, "_llm_type", type(self._llm).__name__)

    # ── Nodes ──────────────────────────────────────────────────────────────

    def _extract_node(self, state: AgentState) -> AgentState:
        refs = extract_references(state["question"])
        return {
            "references": refs,
            "trace": state.get("trace", []) + [f"extract: found {len(refs)} reference(s) {refs}"],
        }

    def _retrieve_node(self, state: AgentState) -> AgentState:
        hits: list[dict[str, Any]] = []
        queries = state.get("references") or [state["question"]]
        for query in queries:
            for hit in self._svc.search(query, limit=self._top_k):
                if all(h["id"] != hit["id"] for h in hits):
                    hits.append(hit)
        hits.sort(key=lambda h: -h["score"])
        hits = hits[: self._top_k]
        return {
            "hits": hits,
            "trace": state["trace"] + [f"retrieve: {len(hits)} mapping record(s) matched"],
        }

    def _validate_node(self, state: AgentState) -> AgentState:
        matched_ids = {h["id"] for h in state["hits"]}
        contradictions = [
            c for c in self._svc.detect_contradictions()
            if any(rec_id in matched_ids for rec_id in c.get("ids", []))
        ]
        confidence = _confidence(state["hits"][0]["score"] if state["hits"] else 0.0)
        if contradictions and confidence == "high":
            confidence = "medium"  # contradictions cap confidence
        return {
            "contradictions": contradictions,
            "confidence": confidence,
            "trace": state["trace"] + [
                f"validate: {len(contradictions)} contradiction(s), confidence={confidence}"
            ],
        }

    def _compose_node(self, state: AgentState) -> AgentState:
        records = [h["record"] for h in state["hits"]]
        answer = self._compose_chain.invoke(
            {"context": format_context(records), "question": state["question"]}
        )
        if state.get("contradictions"):
            answer += (
                "\n\nWARNING: contradictory mapping records were detected for "
                "these sections — flagged for human review."
            )
        return {
            "answer": answer,
            "trace": state["trace"] + ["compose: answer generated"],
        }

    def _refuse_node(self, state: AgentState) -> AgentState:
        return {
            "answer": REFUSAL_MESSAGE,
            "contradictions": [],
            "confidence": "none",
            "trace": state["trace"] + ["compose: no mappings — refused gracefully"],
        }

    def _grounding_node(self, state: AgentState) -> AgentState:
        records = [h["record"] for h in state.get("hits", [])]
        result = check_grounding(state["answer"], records, state["question"])
        ungrounded = result["ungrounded_codes"]
        update: AgentState = {
            "grounded": result["grounded"],
            "ungrounded_codes": ungrounded,
        }
        if ungrounded:
            update["confidence"] = cap_confidence(state["confidence"])
            update["answer"] = state["answer"] + "\n\n" + warning_for(ungrounded)
            note = f"ungrounded {ungrounded} — flagged for human review"
        else:
            note = f"all {len(result['cited_codes'])} cited code(s) grounded"
        update["trace"] = state["trace"] + [f"grounding_check: {note}"]
        return update

    # ── Graph wiring ──────────────────────────────────────────────────────

    @staticmethod
    def _route_after_retrieve(state: AgentState) -> str:
        return "validate" if state["hits"] else "refuse"

    def _build_graph(self):
        g = StateGraph(AgentState)
        g.add_node("extract", self._extract_node)
        g.add_node("retrieve", self._retrieve_node)
        g.add_node("validate", self._validate_node)
        g.add_node("compose", self._compose_node)
        g.add_node("refuse", self._refuse_node)
        g.add_node("grounding_check", self._grounding_node)

        g.add_edge(START, "extract")
        g.add_edge("extract", "retrieve")
        g.add_conditional_edges(
            "retrieve", self._route_after_retrieve,
            {"validate": "validate", "refuse": "refuse"},
        )
        g.add_edge("validate", "compose")
        g.add_edge("compose", "grounding_check")
        g.add_edge("refuse", "grounding_check")
        g.add_edge("grounding_check", END)
        return g.compile()

    # ── Public API ────────────────────────────────────────────────────────

    def run(self, question: str) -> dict[str, Any]:
        question = (question or "").strip()
        if not question:
            raise ValueError("question must not be empty")

        final: AgentState = self._graph.invoke({"question": question, "trace": []})
        return {
            "answer": final["answer"],
            "references": final.get("references", []),
            "sources": [
                {
                    "id": h["record"]["id"],
                    "ipc_code": h["record"].get("ipc_code", ""),
                    "bns_code": h["record"].get("bns_code", ""),
                    "score": h["score"],
                }
                for h in final.get("hits", [])
            ],
            "contradictions": final.get("contradictions", []),
            "confidence": final["confidence"],
            "trace": final["trace"],
            "model": self.model_name,
            "grounded": final.get("grounded", True),
            "ungrounded_codes": final.get("ungrounded_codes", []),
        }
