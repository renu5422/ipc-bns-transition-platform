"""Contract tests for JWT auth — POST /login, GET /me."""


def _login(client, username="analyst", password="nyayasetu2026"):
    return client.post("/login", json={"username": username, "password": password})


class TestLogin:
    def test_valid_credentials_return_token(self, client):
        resp = _login(client)
        assert resp.status_code == 200
        data = resp.json()
        for field in ("access_token", "token_type", "expires_in"):
            assert field in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_wrong_password_returns_401(self, client):
        assert _login(client, password="wrong").status_code == 401

    def test_unknown_user_returns_401(self, client):
        assert _login(client, username="intruder").status_code == 401

    def test_missing_fields_return_422(self, client):
        assert client.post("/login", json={}).status_code == 422


class TestMe:
    def test_me_with_valid_token(self, client):
        token = _login(client).json()["access_token"]
        resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == {"username": "analyst", "role": "analyst"}

    def test_me_without_token_returns_401(self, client):
        assert client.get("/me").status_code == 401

    def test_me_with_garbage_token_returns_401(self, client):
        resp = client.get("/me", headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401


class TestLogout:
    def test_logout_returns_message(self, client):
        assert client.post("/logout").json() == {"message": "Logged out"}
