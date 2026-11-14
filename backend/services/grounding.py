"""Post-generation grounding check for chatbot and agent answers.

Every IPC/BNS section code cited in an LLM answer must come from the
mapping records that were retrieved for that question. Codes that do not
are reported as *ungrounded* so the caller can flag the answer for human
review instead of silently passing a possibly hallucinated mapping.

Normalisation rule (section-level granularity):
- Codes are normalised with ``extract_references`` on both sides, giving
  ``PREFIX-NUMBER[LETTER]`` (``ipc 302`` / ``IPC_302`` -> ``IPC-302``).
- Parenthesised subsections are dropped: a record code ``BNS-106(1)`` grounds
  answer citations ``BNS-106`` and ``BNS-106(2)`` alike. Subsection-level
  hallucinations are therefore out of scope for this check.
- Letter suffixes are significant: ``IPC-304A`` is a different section from
  ``IPC-304`` and does not ground it (nor vice versa).

Allowed codes = both ``ipc_code`` and ``bns_code`` of every retrieved record,
plus codes the analyst wrote in the question (echoing the question back,
e.g. "IPC-999 has no validated mapping", is not a fabricated mapping). The
canonical refusal message is excluded before extraction because its
"e.g. IPC-302" example is instructional, not a citation.
"""

import re
from typing import Any, Iterable

# Matches IPC-302, IPC 302, ipc302, BNS-101, bns_101 ...
_CODE_RE = re.compile(r"\b(IPC|BNS)[\s\-_]?(\d{1,4}[A-Za-z]?)\b", re.IGNORECASE)

REFUSAL_MESSAGE = (
    "I cannot find a validated IPC-BNS mapping for this query in "
    "the current dataset. Please refine your query with a section "
    "code (e.g. IPC-302) or offence keywords."
)

UNGROUNDED_WARNING = (
    "WARNING: this answer cites section code(s) not present in the retrieved "
    "mapping records ({codes}) — flagged for human review."
)


def extract_references(text: str) -> list[str]:
    """Detect and normalise IPC/BNS section references in free text."""
    seen: list[str] = []
    for prefix, num in _CODE_RE.findall(text or ""):
        code = f"{prefix.upper()}-{num.upper()}"
        if code not in seen:
            seen.append(code)
    return seen


def grounded_codes(records: Iterable[dict[str, Any]]) -> set[str]:
    """Normalised IPC and BNS codes of the retrieved records."""
    allowed: set[str] = set()
    for record in records:
        allowed.update(extract_references(str(record.get("ipc_code") or "")))
        allowed.update(extract_references(str(record.get("bns_code") or "")))
    return allowed


def check_grounding(
    answer: str,
    records: Iterable[dict[str, Any]],
    question: str = "",
) -> dict[str, Any]:
    """Return ``{"grounded", "cited_codes", "ungrounded_codes"}`` for an answer."""
    text = (answer or "").replace(REFUSAL_MESSAGE, "")
    cited = extract_references(text)
    allowed = grounded_codes(records) | set(extract_references(question))
    ungrounded = [code for code in cited if code not in allowed]
    return {
        "grounded": not ungrounded,
        "cited_codes": cited,
        "ungrounded_codes": ungrounded,
    }


def cap_confidence(confidence: str) -> str:
    """Ungrounded answers are never more than ``low`` confidence."""
    return "low" if confidence in ("high", "medium") else confidence


def warning_for(ungrounded: list[str]) -> str:
    return UNGROUNDED_WARNING.format(codes=", ".join(ungrounded))
