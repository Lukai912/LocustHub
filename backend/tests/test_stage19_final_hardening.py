from pathlib import Path

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


def make_client(monkeypatch, tmp_path) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def test_ready_endpoint_exposes_runtime_configuration(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database_backend"] == "sqlite"
    assert body["artifact_storage_provider"] == "local"
    assert body["lane_runtime_backend"] == "local"


def test_api_routes_have_swagger_summary_and_docstrings(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    missing = []
    for route in client.app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/v1"):
            continue
        if not route.tags or not route.summary or not route.description:
            missing.append(route.path)

    assert missing == []


def test_runbook_documents_stage19_operational_entrypoints():
    runbook = (REPO_ROOT / "docs/full-deployment-runbook.md").read_text(encoding="utf-8")

    for required in ["/ready", "/docs", "--baseline-profile-id", "ci:run", "Stage19"]:
        assert required in runbook
