"""
MappingService — unit tests.

Covers:
  - Search: keyword match, section-code match, scoring order, limit, empty/zero-limit
  - Contradiction detection: duplicate IPC codes, duplicate BNS codes, clean data
  - Impact analysis: total_records, unique_chapters, validation_rules
  - Schema validation: all-fields present, missing-field detection
  - Record validation: empty critical lists, invalid validation_rules type
  - Determinism: same query → same result across repeated calls

Run:  pytest tests/test_mapping_service.py -v
"""

import pytest
from backend.services.mapping_service import MappingService


# ── Search ─────────────────────────────────────────────────────────────────

class TestSearch:

    def test_keyword_murder_returns_results(self, mapping_service):
        results = mapping_service.search("murder")
        assert len(results) > 0

    def test_ipc_section_code_returns_result(self, mapping_service):
        results = mapping_service.search("IPC-302")
        assert any(r["record"]["ipc_code"] == "IPC-302" for r in results)

    def test_ipc_section_code_with_space_normalised(self, mapping_service):
        r1 = mapping_service.search("IPC-302")
        r2 = mapping_service.search("IPC 302")
        assert r1[0]["score"] == r2[0]["score"]

    def test_results_sorted_descending_by_score(self, mapping_service):
        results = mapping_service.search("murder")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_default_limit_is_ten(self, mapping_service):
        results = mapping_service.search("a")
        assert len(results) <= 10

    def test_custom_limit_respected(self, mapping_service):
        results = mapping_service.search("murder", limit=1)
        assert len(results) <= 1

    def test_empty_query_returns_empty_list(self, mapping_service):
        assert mapping_service.search("") == []

    def test_zero_limit_returns_empty_list(self, mapping_service):
        assert mapping_service.search("murder", limit=0) == []

    def test_negative_limit_returns_empty_list(self, mapping_service):
        assert mapping_service.search("murder", limit=-1) == []

    def test_no_match_query_returns_empty(self, mapping_service):
        assert mapping_service.search("xyznonexistentsection999") == []

    @pytest.mark.parametrize("query", [
        "murder", "IPC-302", "BNS-101", "theft", "assault"
    ])
    def test_parametrized_queries_return_list(self, mapping_service, query):
        results = mapping_service.search(query)
        assert isinstance(results, list)

    def test_each_result_has_id_score_record(self, mapping_service):
        results = mapping_service.search("murder")
        for r in results:
            assert "id" in r
            assert "score" in r
            assert "record" in r

    def test_scores_are_positive(self, mapping_service):
        results = mapping_service.search("murder")
        for r in results:
            assert r["score"] > 0


# ── Determinism ────────────────────────────────────────────────────────────

class TestDeterminism:

    @pytest.mark.parametrize("query", ["murder", "IPC-302", "theft"])
    def test_same_query_identical_results(self, mapping_service, query):
        r1 = mapping_service.search(query)
        r2 = mapping_service.search(query)
        assert r1 == r2, f"Non-deterministic output for query='{query}'"

    def test_result_order_stable(self, mapping_service):
        ids1 = [r["id"] for r in mapping_service.search("murder")]
        ids2 = [r["id"] for r in mapping_service.search("murder")]
        assert ids1 == ids2


# ── Contradiction detection ────────────────────────────────────────────────

class TestContradictionDetection:

    def test_no_contradictions_in_clean_data(self, tmp_service):
        assert tmp_service.detect_contradictions() == []

    def test_duplicate_ipc_codes_flagged(self, duplicate_ipc_file):
        svc = MappingService(duplicate_ipc_file)
        contradictions = svc.detect_contradictions()
        types = [c["type"] for c in contradictions]
        assert "duplicate_ipc" in types

    def test_contradiction_entry_has_type_code_ids(self, duplicate_ipc_file):
        svc = MappingService(duplicate_ipc_file)
        for c in svc.detect_contradictions():
            assert "type" in c
            assert "code" in c
            assert "ids" in c
            assert len(c["ids"]) > 1

    def test_production_data_has_no_contradictions(self, mapping_service):
        contradictions = mapping_service.detect_contradictions()
        assert contradictions == [], (
            f"Production data has contradictions: {contradictions}"
        )


# ── Impact analysis ────────────────────────────────────────────────────────

class TestImpactAnalysis:

    def test_returns_total_records(self, mapping_service):
        result = mapping_service.analyze_impact()
        assert result["total_records"] == len(mapping_service._records)

    def test_returns_unique_chapters_list(self, mapping_service):
        result = mapping_service.analyze_impact()
        assert isinstance(result["unique_chapters"], list)
        assert len(result["unique_chapters"]) > 0

    def test_returns_validation_rules_list(self, mapping_service):
        result = mapping_service.analyze_impact()
        assert isinstance(result["validation_rules"], list)

    def test_invalid_validation_rules_type_ignored(self, tmp_path):
        import json
        data = [{
            "id": "x", "ipc_code": "IPC-1", "ipc_title": "T",
            "bns_code": "BNS-1", "bns_title": "T", "description": "D",
            "chapter": "C", "keywords": ["k"], "ai_summary": "S",
            "validation_rules": "not-a-list",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }]
        f = tmp_path / "bad.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        svc = MappingService(f)
        assert svc.analyze_impact()["validation_rules"] == []


# ── Schema validation ──────────────────────────────────────────────────────

class TestSchemaValidation:

    def test_production_data_passes_schema(self, mapping_service):
        assert mapping_service.validate_schema() is True

    def test_minimal_valid_record_passes_schema(self, tmp_service):
        assert tmp_service.validate_schema() is True

    def test_missing_field_fails_schema(self, tmp_path):
        import json
        record = {
            "id": "bad", "ipc_code": "IPC-1", "ipc_title": "T",
            # bns_code intentionally missing
            "bns_title": "T", "description": "D", "chapter": "C",
            "keywords": ["k"], "ai_summary": "S", "validation_rules": ["r"],
        }
        f = tmp_path / "missing.json"
        f.write_text(json.dumps([record]), encoding="utf-8")
        assert MappingService(f).validate_schema() is False


# ── Record validation ──────────────────────────────────────────────────────

class TestRecordValidation:

    def test_no_issues_with_valid_data(self, tmp_service):
        assert tmp_service.validate_records() == []

    def test_empty_keywords_flagged(self, empty_lists_file):
        svc = MappingService(empty_lists_file)
        issues = svc.validate_records()
        assert len(issues) == 1
        assert "keywords" in issues[0]["missing_fields"]

    def test_empty_validation_rules_flagged(self, empty_lists_file):
        svc = MappingService(empty_lists_file)
        issues = svc.validate_records()
        assert "validation_rules" in issues[0]["missing_fields"]

    def test_invalid_validation_rules_type_flagged(self, tmp_path):
        import json
        record = {
            "id": "x", "ipc_code": "IPC-1", "ipc_title": "T",
            "bns_code": "BNS-1", "bns_title": "T", "description": "D",
            "chapter": "C", "keywords": ["k"], "ai_summary": "S",
            "validation_rules": "not-a-list",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        f = tmp_path / "bad.json"
        f.write_text(json.dumps([record]), encoding="utf-8")
        issues = MappingService(f).validate_records()
        assert issues[0]["invalid_field"] == "validation_rules"


# ── Empty / missing data file ──────────────────────────────────────────────

class TestEdgeCases:

    def test_missing_data_file_loads_empty(self, tmp_path):
        svc = MappingService(tmp_path / "nonexistent.json")
        assert svc._records == []

    def test_corrupt_json_loads_empty(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("this is not json", encoding="utf-8")
        svc = MappingService(f)
        assert svc._records == []

    def test_empty_json_array_loads(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("[]", encoding="utf-8")
        svc = MappingService(f)
        assert svc._records == []
        assert svc.search("murder") == []
        assert svc.detect_contradictions() == []
