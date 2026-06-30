"""
Mapping API contract tests — /mapping, /mapping/contradiction, /mapping/impact
"""
import pytest
from fastapi.testclient import TestClient


class TestMappingRoute:
    def test_ipc302_returns_mapping(self, client):
        resp = client.get("/mapping", params={"code": "IPC-302"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        assert data["mappings"][0]["ipc_code"] == "IPC-302"

    def test_response_has_required_fields(self, client):
        resp = client.get("/mapping", params={"code": "IPC-302"})
        m = resp.json()["mappings"][0]
        for field in ("ipc_code","ipc_title","bns_code","bns_title","confidence","chapter"):
            assert field in m, f"Missing field: {field}"

    def test_confidence_is_high_for_exact_code(self, client):
        resp = client.get("/mapping", params={"code": "IPC-302"})
        assert resp.json()["mappings"][0]["confidence"] == "HIGH"

    def test_unknown_code_returns_404(self, client):
        resp = client.get("/mapping", params={"code": "IPC-9999"})
        assert resp.status_code == 404

    def test_empty_code_returns_400(self, client):
        resp = client.get("/mapping", params={"code": ""})
        assert resp.status_code == 400

    def test_missing_code_returns_422(self, client):
        resp = client.get("/mapping")
        assert resp.status_code == 422

    def test_direction_param_accepted(self, client):
        resp = client.get("/mapping", params={"code": "IPC-302", "direction": "ipc_to_bns"})
        assert resp.status_code == 200

    def test_invalid_direction_returns_422(self, client):
        resp = client.get("/mapping", params={"code": "IPC-302", "direction": "invalid"})
        assert resp.status_code == 422


class TestContradictionRoute:
    def test_clean_data_has_no_contradictions(self, client):
        resp = client.get("/mapping/contradiction", params={"code": "IPC-302"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_contradictions"] is False
        assert data["count"] == 0

    def test_response_has_required_fields(self, client):
        resp = client.get("/mapping/contradiction", params={"code": "IPC-302"})
        data = resp.json()
        for field in ("section_code", "has_contradictions", "count", "contradictions"):
            assert field in data

    def test_empty_code_returns_400(self, client):
        resp = client.get("/mapping/contradiction", params={"code": ""})
        assert resp.status_code == 400

    def test_missing_code_returns_422(self, client):
        resp = client.get("/mapping/contradiction")
        assert resp.status_code == 422


class TestImpactRoute:
    def test_ipc302_returns_impact(self, client):
        resp = client.get("/mapping/impact", params={"section_id": "IPC-302"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_records" in data
        assert "unique_chapters" in data
        assert "impacted_sections" in data

    def test_total_records_matches_dataset(self, client):
        resp = client.get("/mapping/impact", params={"section_id": "IPC-302"})
        assert resp.json()["total_records"] >= 1

    def test_unique_chapters_is_list(self, client):
        resp = client.get("/mapping/impact", params={"section_id": "IPC-302"})
        assert isinstance(resp.json()["unique_chapters"], list)

    def test_empty_section_id_returns_400(self, client):
        resp = client.get("/mapping/impact", params={"section_id": ""})
        assert resp.status_code == 400

    def test_missing_section_id_returns_422(self, client):
        resp = client.get("/mapping/impact")
        assert resp.status_code == 422
