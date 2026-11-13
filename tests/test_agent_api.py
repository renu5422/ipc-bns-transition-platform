# TARGET PATH IN REPO: tests/test_agent_api.py
"""Contract tests for the Agent API — POST /agent."""


import pytest

@pytest.fixture(autouse=True)
def _authenticated_client(client, auth_headers):
    """These endpoints require a JWT — attach it for every test here."""
    client.headers.update(auth_headers)
    yield
    client.headers.pop("Authorization", None)


class TestAgentRoute:
    def test_known_reference_returns_200(self, client):
        resp = client.post("/agent", json={"question": "what replaced IPC-302?"})
        assert resp.status_code == 200

    def test_response_contract(self, client):
        data = client.post("/agent", json={"question": "IPC-302"}).json()
        for field in ("answer", "references", "sources", "contradictions",
                      "confidence", "trace", "model"):
            assert field in data, f"Missing field: {field}"

    def test_references_extracted(self, client):
        data = client.post("/agent", json={"question": "compare IPC 302 and murder"}).json()
        assert "IPC-302" in data["references"]

    def test_trace_is_audit_trail(self, client):
        data = client.post("/agent", json={"question": "IPC-302"}).json()
        assert isinstance(data["trace"], list)
        assert len(data["trace"]) >= 3

    def test_unknown_topic_returns_none_confidence(self, client):
        data = client.post("/agent", json={"question": "zxqv flurbo quantum warp"}).json()
        assert data["confidence"] == "none"
        assert data["sources"] == []

    def test_empty_question_returns_422(self, client):
        resp = client.post("/agent", json={"question": ""})
        assert resp.status_code == 422

    def test_whitespace_question_returns_422(self, client):
        resp = client.post("/agent", json={"question": "   "})
        assert resp.status_code == 422

    def test_missing_question_returns_422(self, client):
        resp = client.post("/agent", json={})
        assert resp.status_code == 422


class TestAuthRequired:
    def test_requires_token(self, client):
        client.headers.pop("Authorization", None)
        resp = client.post("/agent", json={"question": "x"})
        assert resp.status_code == 401
