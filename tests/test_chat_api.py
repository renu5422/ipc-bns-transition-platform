# TARGET PATH IN REPO: tests/test_chat_api.py
"""Contract tests for the Chat API — POST /chat, POST /chat/summary."""

from typing import Any

from fastapi.testclient import TestClient
from langchain_core.language_models.llms import LLM

from backend.api.chat import get_engine
from backend.main import app
from backend.services.chatbot_engine import ChatbotEngine


class MockLLM(LLM):
    @property
    def _llm_type(self) -> str:
        return "mock"

    def _call(self, prompt: str, stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any) -> str:
        return "MOCKED ANSWER"


class TestChatRoute:
    def test_known_topic_returns_200(self, client):
        resp = client.post("/chat", json={"question": "what replaced murder IPC-302"})
        assert resp.status_code == 200

    def test_response_contract(self, client):
        resp = client.post("/chat", json={"question": "murder"})
        data = resp.json()
        for field in ("answer", "sources", "confidence", "model"):
            assert field in data, f"Missing field: {field}"

    def test_answer_cites_sections(self, client):
        data = client.post("/chat", json={"question": "IPC-302"}).json()
        assert "IPC-302" in data["answer"]
        assert data["confidence"] == "high"

    def test_sources_have_required_fields(self, client):
        data = client.post("/chat", json={"question": "murder"}).json()
        assert len(data["sources"]) > 0
        for field in ("id", "ipc_code", "bns_code", "score"):
            assert field in data["sources"][0]

    def test_unknown_topic_returns_none_confidence(self, client):
        data = client.post("/chat", json={"question": "zxqv flurbo quantum warp"}).json()
        assert data["confidence"] == "none"
        assert data["sources"] == []

    def test_empty_question_returns_422(self, client):
        resp = client.post("/chat", json={"question": ""})
        assert resp.status_code == 422

    def test_whitespace_question_returns_422(self, client):
        resp = client.post("/chat", json={"question": "   "})
        assert resp.status_code == 422

    def test_missing_question_returns_422(self, client):
        resp = client.post("/chat", json={})
        assert resp.status_code == 422

    def test_engine_is_overridable_with_mock_llm(self, tmp_service):
        app.dependency_overrides[get_engine] = lambda: ChatbotEngine(
            llm=MockLLM(), mapping_service=tmp_service
        )
        try:
            with TestClient(app) as mock_client:
                data = mock_client.post("/chat", json={"question": "murder"}).json()
            assert data["answer"] == "MOCKED ANSWER"
            assert data["model"] == "mock"
        finally:
            app.dependency_overrides.pop(get_engine, None)


class TestSummaryRoute:
    def test_known_code_returns_200(self, client):
        resp = client.post("/chat/summary", json={"code": "IPC-302"})
        assert resp.status_code == 200

    def test_summary_contract(self, client):
        data = client.post("/chat/summary", json={"code": "IPC-302"}).json()
        for field in ("code", "ipc_code", "bns_code", "summary", "model"):
            assert field in data, f"Missing field: {field}"

    def test_summary_mentions_both_codes(self, client):
        data = client.post("/chat/summary", json={"code": "IPC-302"}).json()
        assert "IPC-302" in data["summary"]
        assert "BNS-101" in data["summary"]

    def test_unknown_code_returns_404(self, client):
        resp = client.post("/chat/summary", json={"code": "IPC-9999"})
        assert resp.status_code == 404

    def test_empty_code_returns_422(self, client):
        resp = client.post("/chat/summary", json={"code": ""})
        assert resp.status_code == 422


class TestHealthVersionBump:
    def test_health_reports_app_version(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert data["version"] == app.version  # stays valid across bumps
