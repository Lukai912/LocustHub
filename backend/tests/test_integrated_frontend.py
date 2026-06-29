from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def make_client_with_frontend_dist(monkeypatch, tmp_path: Path) -> TestClient:
    dist = tmp_path / "frontend-dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        '<!doctype html><html><body><div id="app"></div><script src="/assets/app.js"></script></body></html>',
        encoding="utf-8",
    )
    (assets / "app.js").write_text("window.__LOCUSTHUB__ = true;", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(dist))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def test_fastapi_serves_built_admin_console(monkeypatch, tmp_path):
    client = make_client_with_frontend_dist(monkeypatch, tmp_path)

    index = client.get("/")
    asset = client.get("/assets/app.js")

    assert index.status_code == 200
    assert '<div id="app"></div>' in index.text
    assert asset.status_code == 200
    assert "window.__LOCUSTHUB__ = true" in asset.text


def test_frontend_routes_fall_back_without_swallowing_api(monkeypatch, tmp_path):
    client = make_client_with_frontend_dist(monkeypatch, tmp_path)

    frontend_route = client.get("/test-runs/run-demo")
    health = client.get("/health")
    api = client.get("/api/v1/me", headers={"Authorization": "Bearer dev-token"})
    missing_api = client.get("/api/v1/not-found")

    assert frontend_route.status_code == 200
    assert '<div id="app"></div>' in frontend_route.text
    assert health.json() == {"status": "ok", "app": "LocustHub"}
    assert api.status_code == 200
    assert missing_api.status_code == 404
