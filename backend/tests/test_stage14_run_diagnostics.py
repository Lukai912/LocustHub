from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


AUTH = {"Authorization": "Bearer dev-token"}


def make_client(monkeypatch, tmp_path) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def create_running_run(client: TestClient) -> str:
    created = client.post(
        "/api/v1/test-runs",
        headers=AUTH,
        json={"tenant_id": "tenant-demo", "project_id": "project-demo", "test_plan_id": "plan-demo", "source": "manual"},
    )
    run_id = created.json()["id"]
    assert client.post(f"/api/v1/test-runs/{run_id}/start", headers=AUTH).status_code == 200
    assert client.post(f"/api/v1/test-runs/{run_id}/collect", headers=AUTH).status_code == 200
    return run_id


def test_run_diagnostics_include_events_lane_metrics_and_recommendations(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    run_id = create_running_run(client)

    response = client.get(f"/api/v1/test-runs/{run_id}/diagnostics", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["run"]["id"] == run_id
    assert body["lane"]["test_run_id"] == run_id
    assert body["latest_snapshot"]["run_id"] == run_id
    assert body["events"][0]["status"] == "CREATED"
    assert any(event["status"] == "RUNNING" for event in body["events"])
    assert body["recommendations"]


def test_rerun_creates_new_run_from_same_plan(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    run_id = create_running_run(client)

    response = client.post(f"/api/v1/test-runs/{run_id}/rerun", headers=AUTH)

    assert response.status_code == 200
    new_run = response.json()
    assert new_run["id"] != run_id
    assert new_run["test_plan_id"] == "plan-demo"
    assert new_run["source"] == "manual"
    assert new_run["status"] == "CREATED"
