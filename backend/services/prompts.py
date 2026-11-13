"""Prompt templates for the IPC-BNS chatbot engine (Week 6).

All prompts are LangChain ``PromptTemplate`` objects so they can be piped
directly into any LLM via LCEL (``prompt | llm | parser``).

Prompt-engineering principles applied:
- The model is grounded ONLY in retrieved mapping records (no free recall),
  keeping answers citation-aware and bounded by the validated pipeline.
- Context is wrapped in explicit BEGIN/END markers so models do not bleed
  instructions into answers, and so the deterministic fallback LLM can
  reliably extract it.
- The model must refuse when context is insufficient rather than
  hallucinate legal mappings.
"""

from langchain_core.prompts import PromptTemplate

CONTEXT_BEGIN = "=== BEGIN MAPPING CONTEXT ==="
CONTEXT_END = "=== END MAPPING CONTEXT ==="

CHAT_SYSTEM_RULES = """\
You are a legal-transition assistant for the IPC to BNS migration platform.
Rules you must follow:
1. Answer ONLY from the mapping records provided in the context block.
2. Always cite the IPC and BNS section codes you used.
3. If the context does not contain the answer, say you cannot find a \
validated mapping and suggest the user refine their query.
4. Never invent section numbers, punishments, or legal interpretations.
5. Keep answers concise and structured for legal analysts."""

CHAT_PROMPT = PromptTemplate.from_template(
    CHAT_SYSTEM_RULES
    + "\n\n"
    + CONTEXT_BEGIN
    + "\n{context}\n"
    + CONTEXT_END
    + "\n\nAnalyst question: {question}\n\nAnswer:"
)

SUMMARY_PROMPT = PromptTemplate.from_template(
    """You are a legal summarisation engine. Summarise the following IPC-BNS \
mapping record for a legal analyst in 2-3 sentences. Mention both section \
codes, the chapter, and what changed in the transition. Do not add facts \
that are not in the record.

"""
    + CONTEXT_BEGIN
    + "\n{context}\n"
    + CONTEXT_END
    + "\n\nSummary:"
)


def format_record(record: dict) -> str:
    """Render one mapping record as a compact context block."""
    keywords = record.get("keywords") or []
    return (
        f"[{record.get('ipc_code', '?')} -> {record.get('bns_code', '?')}] "
        f"{record.get('ipc_title', '')} -> {record.get('bns_title', '')}\n"
        f"  chapter: {record.get('chapter', '')}\n"
        f"  description: {record.get('description', '')}\n"
        f"  keywords: {', '.join(str(k) for k in keywords)}\n"
        f"  summary: {record.get('ai_summary', '')}"
    )


def format_context(records: list[dict]) -> str:
    """Render retrieved mapping records into the prompt context block."""
    if not records:
        return "(no matching mapping records found)"
    return "\n\n".join(format_record(r) for r in records)
