from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


ADMIN = {"Authorization": "Bearer dev-token"}


def make_client(monkeypatch, tmp_path) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def test_admin_can_create_user_and_user_can_login(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    created = client.post(
        "/api/v1/users",
        headers=ADMIN,
        json={"tenant_id": "tenant-demo", "username": "perf-user", "password": "secret", "role": "project_member"},
    )
    login = client.post("/api/v1/auth/login", json={"username": "perf-user", "password": "secret"})

    assert created.status_code == 200
    assert created.json()["role"] == "project_member"
    assert login.status_code == 200
    assert login.json()["access_token"].startswith("user-token-")


def test_api_tokens_can_be_created_used_and_revoked(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    created = client.post("/api/v1/api-tokens", headers=ADMIN, json={"name": "ci token", "scopes": ["runs:write"]})
    token = created.json()["token"]
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    revoked = client.post(f"/api/v1/api-tokens/{created.json()['id']}/revoke", headers=ADMIN)
    denied = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert created.status_code == 200
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert revoked.status_code == 200
    assert revoked.json()["revoked_at"]
    assert denied.status_code == 401


def test_non_admin_cannot_create_users(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.post(
        "/api/v1/users",
        headers={"Authorization": "Bearer dev-token-viewer"},
        json={"tenant_id": "tenant-demo", "username": "blocked", "password": "secret", "role": "viewer"},
    )

    assert response.status_code == 403
