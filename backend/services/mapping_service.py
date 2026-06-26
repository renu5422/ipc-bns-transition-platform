import json
import re
from pathlib import Path
from typing import Any

_DEFAULT_DATA = Path(__file__).parent.parent.parent / "data" / "ipc_bns_mapping.json"


def _normalize(code: str) -> str:
    return re.sub(r"[\s\-_]+", "", code.lower())


def _tokenize(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).split()


class MappingService:
    def __init__(self, data_path: Path | None = None) -> None:
        self._path = Path(data_path) if data_path else _DEFAULT_DATA
        self._records: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict[str, Any]]:
        try:
            with open(self._path, encoding="utf-8") as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not query or limit <= 0:
            return []
        norm_query = _normalize(query)
        tokens = _tokenize(query)
        results = []
        for record in self._records:
            score = self._score(record, norm_query, tokens)
            if score > 0:
                results.append({"id": record["id"], "score": score, "record": record})
        results.sort(key=lambda x: (-x["score"], x["id"]))
        return results[:limit]

    def _score(self, record: dict, norm_query: str, tokens: list[str]) -> float:
        score = 0.0
        for field in ("ipc_code", "bns_code"):
            if _normalize(record.get(field, "")) == norm_query:
                score += 10.0
        text = " ".join(
            str(record.get(f, ""))
            for f in ("ipc_title", "bns_title", "description", "chapter", "ai_summary")
        ).lower()
        kw_text = " ".join(
            record.get("keywords", []) if isinstance(record.get("keywords"), list) else []
        ).lower()
        for token in tokens:
            score += text.count(token) * 1.0
            score += kw_text.count(token) * 2.0
        return score

    def rank(self, query: str) -> list[dict[str, Any]]:
        return self.search(query)

    def validate_records(self) -> list[dict[str, Any]]:
        issues = []
        for i, record in enumerate(self._records):
            entry: dict[str, Any] = {"index": i, "id": record.get("id", "")}
            if "validation_rules" in record and not isinstance(record["validation_rules"], list):
                entry["invalid_field"] = "validation_rules"
                issues.append(entry)
                continue
            missing = [
                field for field in ("keywords", "validation_rules")
                if isinstance(record.get(field), list) and len(record[field]) == 0
            ]
            if missing:
                entry["missing_fields"] = missing
                issues.append(entry)
        return issues

    def analyze_impact(self) -> dict[str, Any]:
        all_rules: list[str] = []
        for record in self._records:
            rules = record.get("validation_rules", [])
            if isinstance(rules, list):
                all_rules.extend(str(r) for r in rules)
        return {
            "total_records": len(self._records),
            "validation_rules": all_rules,
            "unique_chapters": list({r.get("chapter", "") for r in self._records}),
        }

    def detect_contradictions(self) -> list[dict[str, Any]]:
        seen_ipc: dict[str, list[str]] = {}
        seen_bns: dict[str, list[str]] = {}
        for record in self._records:
            ni = _normalize(record.get("ipc_code", ""))
            nb = _normalize(record.get("bns_code", ""))
            seen_ipc.setdefault(ni, []).append(record["id"])
            seen_bns.setdefault(nb, []).append(record["id"])
        contradictions = []
        for code, ids in seen_ipc.items():
            if len(ids) > 1:
                contradictions.append({"type": "duplicate_ipc", "code": code, "ids": ids})
        for code, ids in seen_bns.items():
            if len(ids) > 1:
                contradictions.append({"type": "duplicate_bns", "code": code, "ids": ids})
        return contradictions

    def validate_schema(self) -> bool:
        required = {
            "id", "ipc_code", "ipc_title", "bns_code", "bns_title",
            "description", "chapter", "keywords", "ai_summary", "validation_rules",
        }
        return all(required.issubset(r.keys()) for r in self._records)


mapping_service = MappingService()
