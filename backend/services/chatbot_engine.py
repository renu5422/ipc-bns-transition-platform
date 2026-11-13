"""LangChain-powered chatbot engine for the IPC-BNS platform (Week 6).

Architecture (retrieval-grounded, per README "Future Chatbot Layer"):

    question -> MappingService.search() -> format_context()
             -> LCEL chain (CHAT_PROMPT | llm | StrOutputParser)
             -> answer + cited sources + confidence

The LLM is pluggable:
- If OPENAI_API_KEY / ANTHROPIC_API_KEY is set (and the matching
  langchain integration package is installed), a real chat model is used.
- Otherwise a ``DeterministicLegalLLM`` composes answers purely from the
  retrieved context — fully offline, repeatable, and testable, in line
  with the platform's deterministic-fallback principle.
"""

import os
import re
from typing import Any

from langchain_core.language_models.llms import LLM
from langchain_core.output_parsers import StrOutputParser

from backend.services.mapping_service import MappingService
from backend.services.prompts import (
    CHAT_PROMPT,
    CONTEXT_BEGIN,
    CONTEXT_END,
    SUMMARY_PROMPT,
    format_context,
)

_PAIR_RE = re.compile(r"^\[([A-Za-z0-9()\-]+) -> ([A-Za-z0-9()\-]+)\] (.+)$", re.MULTILINE)
_NO_CONTEXT = "(no matching mapping records found)"

# Matches IPC-302, IPC 302, ipc302, BNS-101, bns_101 ...
_CODE_RE = re.compile(r"\b(IPC|BNS)[\s\-_]?(\d{1,4}[A-Za-z]?)\b", re.IGNORECASE)


def extract_references(text: str) -> list[str]:
    """Detect and normalise IPC/BNS section references in free text."""
    seen: list[str] = []
    for prefix, num in _CODE_RE.findall(text or ""):
        code = f"{prefix.upper()}-{num.upper()}"
        if code not in seen:
            seen.append(code)
    return seen


def _extract_context(prompt: str) -> str:
    start = prompt.find(CONTEXT_BEGIN)
    end = prompt.find(CONTEXT_END)
    if start == -1 or end == -1:
        return ""
    return prompt[start + len(CONTEXT_BEGIN):end].strip()


class DeterministicLegalLLM(LLM):
    """Offline fallback LLM.

    Composes grounded answers directly from the structured context block
    that the prompt templates produce. No network, no randomness — the
    same input always yields the same output, which keeps the chatbot
    usable and testable without API keys.
    """

    @property
    def _llm_type(self) -> str:
        return "deterministic-legal"

    def _call(self, prompt: str, stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any) -> str:
        context = _extract_context(prompt)
        pairs = _PAIR_RE.findall(context)

        if not pairs or _NO_CONTEXT in context:
            return (
                "I cannot find a validated IPC-BNS mapping for this query in "
                "the current dataset. Please refine your query with a section "
                "code (e.g. IPC-302) or offence keywords."
            )

        if "legal summarisation engine" in prompt:
            return self._summarise(context, pairs[0])
        return self._answer(pairs)

    @staticmethod
    def _answer(pairs: list[tuple[str, str, str]]) -> str:
        lines = [f"Based on the validated mapping data ({len(pairs)} record(s) matched):"]
        cited = []
        for ipc, bns, titles in pairs:
            ipc_title, _, bns_title = titles.partition(" -> ")
            lines.append(
                f"- {ipc} ({ipc_title.strip()}) maps to {bns} ({bns_title.strip()})."
            )
            cited.extend([ipc, bns])
        lines.append("Cited sections: " + ", ".join(cited) + ".")
        return "\n".join(lines)

    @staticmethod
    def _summarise(context: str, pair: tuple[str, str, str]) -> str:
        ipc, bns, titles = pair
        ipc_title, _, bns_title = titles.partition(" -> ")
        chapter_m = re.search(r"chapter: (.+)", context)
        desc_m = re.search(r"description: (.+)", context)
        chapter = chapter_m.group(1).strip() if chapter_m else "unknown chapter"
        desc = desc_m.group(1).strip() if desc_m else ""
        return (
            f"{ipc} ({ipc_title.strip()}) has transitioned to {bns} "
            f"({bns_title.strip()}) under the chapter '{chapter}'. {desc}"
        ).strip()


def resolve_default_llm() -> Any:
    """Pick the best available LLM: Anthropic > OpenAI > deterministic."""
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=os.getenv("CHATBOT_MODEL", "claude-haiku-4-5"), temperature=0)
        except ImportError:
            pass
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=os.getenv("CHATBOT_MODEL", "gpt-4o-mini"), temperature=0)
        except ImportError:
            pass
    return DeterministicLegalLLM()


def _confidence(top_score: float) -> str:
    if top_score >= 10:
        return "high"
    if top_score >= 3:
        return "medium"
    if top_score > 0:
        return "low"
    return "none"


class ChatbotEngine:
    """Retrieval-grounded Q&A + summary generation over the mapping data."""

    def __init__(
        self,
        llm: Any = None,
        mapping_service: MappingService | None = None,
        top_k: int = 3,
    ) -> None:
        self._svc = mapping_service or MappingService()
        self._llm = llm if llm is not None else resolve_default_llm()
        self._top_k = top_k
        parser = StrOutputParser()
        self._chat_chain = CHAT_PROMPT | self._llm | parser
        self._summary_chain = SUMMARY_PROMPT | self._llm | parser

    @property
    def model_name(self) -> str:
        return getattr(self._llm, "_llm_type", type(self._llm).__name__)

    def ask(self, question: str) -> dict[str, Any]:
        """Answer an analyst question, grounded in retrieved mapping records."""
        question = (question or "").strip()
        if not question:
            raise ValueError("question must not be empty")

        # Retrieve by extracted section codes first, then the raw question,
        # so natural-language queries containing codes still match exactly.
        queries = extract_references(question) + [question]
        hits: list[dict[str, Any]] = []
        for query in queries:
            for hit in self._svc.search(query, limit=self._top_k):
                if all(h["id"] != hit["id"] for h in hits):
                    hits.append(hit)
        hits.sort(key=lambda h: -h["score"])
        hits = hits[: self._top_k]
        records = [h["record"] for h in hits]
        answer = self._chat_chain.invoke(
            {"context": format_context(records), "question": question}
        )
        return {
            "answer": answer,
            "sources": [
                {
                    "id": h["record"]["id"],
                    "ipc_code": h["record"].get("ipc_code", ""),
                    "bns_code": h["record"].get("bns_code", ""),
                    "score": h["score"],
                }
                for h in hits
            ],
            "confidence": _confidence(hits[0]["score"] if hits else 0.0),
            "model": self.model_name,
        }

    def summarize(self, section_code: str) -> dict[str, Any]:
        """Generate an analyst-facing summary for one section code."""
        section_code = (section_code or "").strip()
        if not section_code:
            raise ValueError("section code must not be empty")

        hits = self._svc.search(section_code, limit=1)
        if not hits or hits[0]["score"] < 10:  # require exact code match
            raise LookupError(f"no mapping record found for '{section_code}'")

        record = hits[0]["record"]
        summary = self._summary_chain.invoke({"context": format_context([record])})
        return {
            "code": section_code,
            "ipc_code": record.get("ipc_code", ""),
            "bns_code": record.get("bns_code", ""),
            "summary": summary,
            "model": self.model_name,
        }
