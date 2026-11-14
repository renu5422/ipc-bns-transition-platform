"""Auth contract tests for the Admin API — GET /admin/diagnostics.

Headers are passed per request so the Authorization header never leaks into
the session-scoped ``client`` shared by other test modules.
"""


class TestAdminDiagnosticsAuth:
    def test_no_token_returns_401(self, client):
        resp = client.get("/admin/diagnostics")
        assert resp.status_code == 401
        assert resp.headers.get("WWW-Authenticate") == "Bearer"

    def test_garbage_token_returns_401(self, client):
        resp = client.get(
            "/admin/diagnostics",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert resp.status_code == 401
        assert resp.headers.get("WWW-Authenticate") == "Bearer"

    def test_valid_token_returns_200(self, client, auth_headers):
        resp = client.get("/admin/diagnostics", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_valid_token_does_not_leak_into_client(self, client, auth_headers):
        client.get("/admin/diagnostics", headers=auth_headers)
        assert "Authorization" not in client.headers
