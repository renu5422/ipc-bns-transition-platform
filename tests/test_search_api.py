"""
Search API — contract + negative tests.

Covers:
  - JSON schema contract for every successful response (Capability #12: Schema Validation)
  - Negative paths: missing query, empty query, bad limit (Capability #13: Negative Testing)
  - Status code assertions for all routes (Capability #14: Contract Testing)
  - Determinism: same query always returns identical results (Engineering Principle #1)

Run:  pytest tests/test_search_api.py -v
"""

import json
from pathlib import Path

import jsonschema
import pytest

# ── Load the response schema once ─────────────────────────────────────────
SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "search_response_schema.json"
SEARCH_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def assert_valid_schema(data: dict) -> None:
    """Raise AssertionError with a readable message if schema validation fails."""
    try:
        jsonschema.validate(instance=data, schema=SEARCH_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise AssertionError(f"Schema validation failed: {exc.message}\nPath: {list(exc.path)}") from exc


# ── Happy-path contract tests ──────────────────────────────────────────────

class TestSearchContract:
    """Every successful response must conform to the JSON schema contract."""

    def test_murder_query_returns_valid_schema(self, client):
        resp = client.get("/search", params={"q": "murder"})
        assert resp.status_code == 200
        assert_valid_schema(resp.json())

    def test_ipc_section_query_returns_valid_schema(self, client):
        resp = client.get("/search", params={"q": "IPC-302"})
        assert resp.status_code == 200
        assert_valid_schema(resp.json())

    def test_bns_section_query_returns_valid_schema(self, client):
        resp = client.get("/search", params={"q": "BNS-101"})
        assert resp.status_code == 200
        assert_valid_schema(resp.json())

    def test_no_results_query_still_valid_schema(self, client):
        resp = client.get("/search", params={"q": "xyznonexistentsection999"})
        assert resp.status_code == 200
        data = resp.json()
        assert_valid_schema(data)
        assert data["count"] == 0
        assert data["results"] == []

    @pytest.mark.parametrize("keyword", [
        "theft", "rape", "assault", "homicide", "chapter"
    ])
    def test_various_keywords_return_valid_schema(self, client, keyword):
        resp = client.get("/search", params={"q": keyword})
        assert resp.status_code == 200
        assert_valid_schema(resp.json())

    def test_response_count_matches_results_length(self, client):
        resp = client.get("/search", params={"q": "murder"})
        data = resp.json()
        assert data["count"] == len(data["results"])

    def test_query_echoed_in_response(self, client):
        resp = client.get("/search", params={"q": "murder"})
        # Query may be sanitised but should not be empty
        assert resp.json()["query"]

    def test_results_have_positive_scores(self, client):
        resp = client.get("/search", params={"q": "murder"})
        for item in resp.json()["results"]:
            assert item["score"] > 0, f"Expected positive score, got {item['score']}"

    def test_results_sorted_by_descending_score(self, client):
        resp = client.get("/search", params={"q": "murder"})
        scores = [r["score"] for r in resp.json()["results"]]
        assert scores == sorted(scores, reverse=True), "Results must be sorted by descending score"


# ── Limit parameter tests ──────────────────────────────────────────────────

class TestSearchLimit:
    def test_default_limit_applied(self, client):
        resp = client.get("/search", params={"q": "murder"})
        assert len(resp.json()["results"]) <= 10

    def test_custom_limit_one(self, client):
        resp = client.get("/search", params={"q": "murder", "limit": 1})
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 1

    def test_custom_limit_50(self, client):
        resp = client.get("/search", params={"q": "murder", "limit": 50})
        assert resp.status_code == 200

    def test_limit_above_max_rejected(self, client):
        resp = client.get("/search", params={"q": "murder", "limit": 51})
        assert resp.status_code == 422  # FastAPI validation rejects out-of-range

    def test_limit_zero_rejected(self, client):
        resp = client.get("/search", params={"q": "murder", "limit": 0})
        assert resp.status_code == 422

    def test_limit_negative_rejected(self, client):
        resp = client.get("/search", params={"q": "murder", "limit": -1})
        assert resp.status_code == 422


# ── Negative tests ─────────────────────────────────────────────────────────

class TestSearchNegative:
    """Bad inputs must return clear error codes, never 500."""

    def test_missing_query_param_returns_422(self, client):
        resp = client.get("/search")
        assert resp.status_code == 422

    def test_empty_query_string_returns_400(self, client):
        resp = client.get("/search", params={"q": ""})
        assert resp.status_code == 400

    def test_whitespace_only_query_returns_400(self, client):
        resp = client.get("/search", params={"q": "   "})
        assert resp.status_code == 400

    def test_special_characters_sanitised_not_crashed(self, client):
        resp = client.get("/search", params={"q": "<script>alert('xss')</script>"})
        # Should not crash — either 200 with 0 results or 400
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            assert_valid_schema(resp.json())

    def test_very_long_query_does_not_crash(self, client):
        long_q = "murder " * 200
        resp = client.get("/search", params={"q": long_q})
        assert resp.status_code in (200, 400, 422)

    def test_sql_injection_attempt_sanitised(self, client):
        resp = client.get("/search", params={"q": "'; DROP TABLE sections; --"})
        assert resp.status_code in (200, 400)

    def test_numeric_only_query_handled_gracefully(self, client):
        resp = client.get("/search", params={"q": "12345"})
        assert resp.status_code == 200
        assert_valid_schema(resp.json())


# ── Determinism tests ──────────────────────────────────────────────────────

class TestSearchDeterminism:
    """Same query must always return identical results — core engineering principle."""

    @pytest.mark.parametrize("query", ["murder", "IPC-302", "theft", "assault"])
    def test_same_query_returns_same_results(self, client, query):
        r1 = client.get("/search", params={"q": query}).json()
        r2 = client.get("/search", params={"q": query}).json()
        assert r1["results"] == r2["results"], (
            f"Non-deterministic results for query='{query}'"
        )

    def test_result_order_is_stable_across_runs(self, client):
        ids_run1 = [r["id"] for r in client.get("/search", params={"q": "murder"}).json()["results"]]
        ids_run2 = [r["id"] for r in client.get("/search", params={"q": "murder"}).json()["results"]]
        assert ids_run1 == ids_run2
