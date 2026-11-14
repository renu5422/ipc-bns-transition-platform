"""Post-generation grounding check for chatbot and agent answers.

Every IPC/BNS section code cited in an LLM answer must come from the
mapping records that were retrieved for that question. Codes that do not
are reported as *ungrounded* so the caller can flag the answer for human
review instead of silently passing a possibly hallucinated mapping.

Normalisation (formatting only): ``extract_references(text,
keep_subsections=True)`` yields ``PREFIX-NUMBER[LETTER][(sub)...]`` —
prefix and section letter upper-cased, subsection parts lower-cased, inner
whitespace removed (``bns 106 (1)`` / ``BNS_106(1)`` -> ``BNS-106(1)``,
``BNS-326(A)`` -> ``BNS-326(a)``). Text without an IPC/BNS prefix (e.g.
"Section 106(1)") is not a citation and is ignored.

Matching rules (allowed = ``ipc_code`` and ``bns_code`` of every retrieved
record, plus codes the analyst wrote in the question):

- Cited code WITH a subsection (``BNS-106(2)``): grounded only if exactly
  that code, subsection included, is allowed. A record ``BNS-106(1)`` does
  NOT ground ``BNS-106(2)``.
- Cited bare section (``BNS-106``): grounded if the bare section or any of
  its subsections is allowed — a parent-level citation is not a false claim.
- Retrieved bare section (``BNS-106``) vs cited subsection (``BNS-106(1)``):
  UNGROUNDED. The record does not show that subsection exists or is the
  relevant one, so the extra specificity is unverified.
- Nested subsections are matched exactly (``BNS-137(1)(a)`` grounds
  ``BNS-137(1)(a)`` and bare ``BNS-137``, but not ``BNS-137(1)``).
- Letter suffixes are strict: ``IPC-304A`` and ``IPC-304`` are different
  sections.

The canonical refusal message is excluded before extraction because its
"e.g. IPC-302" example is instructional, not a citation.
"""

import re
from typing import Any, Iterable

# Matches IPC-302, IPC 302, ipc302, BNS-101, bns_101, BNS-106(1), BNS-137(1)(a) ...
# A subsection is a number, a single letter, or a roman numeral (ii, iv ...) so
# that parenthesised titles such as "IPC-376 (Rape)" are not mistaken for one.
_SUB = r"\(\s?(?:\d{1,3}[A-Za-z]?|[A-Za-z]|[ivxIVX]{2,5})\s?\)"
_CODE_RE = re.compile(
    rf"\b(IPC|BNS)[\s\-_]?(\d{{1,4}}[A-Za-z]?)\b((?:\s?{_SUB})*)",
    re.IGNORECASE,
)

REFUSAL_MESSAGE = (
    "I cannot find a validated IPC-BNS mapping for this query in "
    "the current dataset. Please refine your query with a section "
    "code (e.g. IPC-302) or offence keywords."
)

UNGROUNDED_WARNING = (
    "WARNING: this answer cites section code(s) not present in the retrieved "
    "mapping records ({codes}) — flagged for human review."
)


def extract_references(text: str, keep_subsections: bool = False) -> list[str]:
    """Detect and normalise IPC/BNS section references in free text.

    By default subsections are dropped (``BNS-106(1)`` -> ``BNS-106``), which
    is what retrieval wants. ``keep_subsections=True`` keeps them, normalised
    as described in the module docstring, for the grounding comparison.
    """
    seen: list[str] = []
    for prefix, num, subs in _CODE_RE.findall(text or ""):
        code = f"{prefix.upper()}-{num.upper()}"
        if keep_subsections:
            code += re.sub(r"\s", "", subs).lower()
        if code not in seen:
            seen.append(code)
    return seen


def _base(code: str) -> str:
    return code.split("(", 1)[0]


def grounded_codes(records: Iterable[dict[str, Any]]) -> set[str]:
    """Normalised IPC and BNS codes (subsections kept) of the retrieved records."""
    allowed: set[str] = set()
    for record in records:
        for field in ("ipc_code", "bns_code"):
            allowed.update(
                extract_references(str(record.get(field) or ""), keep_subsections=True)
            )
    return allowed


def is_grounded(code: str, allowed: set[str]) -> bool:
    """Apply the matching rules from the module docstring to one cited code."""
    if code in allowed:
        return True
    if "(" in code:
        return False  # subsection citations need an exact match
    return any(_base(a) == code for a in allowed)


def check_grounding(
    answer: str,
    records: Iterable[dict[str, Any]],
    question: str = "",
) -> dict[str, Any]:
    """Return ``{"grounded", "cited_codes", "ungrounded_codes"}`` for an answer."""
    text = (answer or "").replace(REFUSAL_MESSAGE, "")
    cited = extract_references(text, keep_subsections=True)
    allowed = grounded_codes(records) | set(
        extract_references(question, keep_subsections=True)
    )
    ungrounded = [code for code in cited if not is_grounded(code, allowed)]
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
