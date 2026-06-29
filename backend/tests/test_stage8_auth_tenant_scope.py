from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def make_client(monkeypatch, tmp_path) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("DEMO_TOKEN", "dev-token")
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login_checks_password_and_returns_persisted_user_token(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    bad = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401

    good = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert good.status_code == 200
    assert good.json()["access_token"] == "dev-token"


def test_invalid_bearer_token_is_rejected(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/api/v1/projects", headers=auth_headers("not-in-users"))

    assert response.status_code == 401


def test_me_returns_persisted_user_context(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/api/v1/me", headers=auth_headers("dev-token-viewer"))

    assert response.status_code == 200
    assert response.json() == {
        "id": "user-viewer",
        "username": "viewer",
        "tenant_id": "tenant-demo",
        "role": "viewer",
    }


def test_non_admin_user_only_sees_own_tenant_projects(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    other_tenant = client.post(
        "/api/v1/tenants",
        headers=auth_headers("dev-token"),
        json={"name": "Other Tenant", "slug": "other"},
    ).json()
    client.post(
        "/api/v1/projects",
        headers=auth_headers("dev-token"),
        json={"tenant_id": other_tenant["id"], "name": "Other Project", "slug": "other-project"},
    )

    response = client.get("/api/v1/projects", headers=auth_headers("dev-token-viewer"))

    assert response.status_code == 200
    projects = response.json()
    assert [project["tenant_id"] for project in projects] == ["tenant-demo"]


def test_non_admin_user_cannot_create_cross_tenant_project(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    other_tenant = client.post(
        "/api/v1/tenants",
        headers=auth_headers("dev-token"),
        json={"name": "Other Tenant", "slug": "other"},
    ).json()

    response = client.post(
        "/api/v1/projects",
        headers=auth_headers("dev-token-viewer"),
        json={"tenant_id": other_tenant["id"], "name": "Blocked", "slug": "blocked"},
    )

    assert response.status_code == 403
