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


def create_archived_run(client: TestClient) -> str:
    created = client.post(
        "/api/v1/test-runs",
        headers=AUTH,
        json={"tenant_id": "tenant-demo", "project_id": "project-demo", "test_plan_id": "plan-demo", "source": "manual"},
    )
    assert created.status_code == 200
    run_id = created.json()["id"]
    assert client.post(f"/api/v1/test-runs/{run_id}/start", headers=AUTH).status_code == 200
    for _ in range(3):
        assert client.post(f"/api/v1/test-runs/{run_id}/collect", headers=AUTH).status_code == 200
    assert client.post(f"/api/v1/test-runs/{run_id}/stop", headers=AUTH).status_code == 200
    return run_id


def test_report_summary_exposes_downloadable_artifacts_and_logs(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    run_id = create_archived_run(client)

    response = client.get(f"/api/v1/test-runs/{run_id}/report", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    artifact_names = {item["name"] for item in body["artifacts"]}
    assert {"HTML Report", "Requests CSV", "Failures CSV", "Exceptions CSV", "History CSV", "Master Log"} <= artifact_names
    assert body["log_preview"].startswith("Run ")
    assert body["artifacts"][0]["download_url"].startswith(f"/api/v1/artifacts/{body['artifacts'][0]['id']}/download")


def test_artifact_download_is_tenant_scoped(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    run_id = create_archived_run(client)
    report = client.get(f"/api/v1/test-runs/{run_id}/report", headers=AUTH).json()
    html = next(item for item in report["artifacts"] if item["name"] == "HTML Report")

    download = client.get(html["download_url"], headers=AUTH)
    viewer_download = client.get(html["download_url"], headers={"Authorization": "Bearer dev-token-viewer"})

    assert download.status_code == 200
    assert "text/html" in download.headers["content-type"]
    assert "LocustHub Report" in download.text
    assert viewer_download.status_code == 200


def test_locust_stats_include_history_and_error_rows(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    created = client.post(
        "/api/v1/test-runs",
        headers=AUTH,
        json={"tenant_id": "tenant-demo", "project_id": "project-demo", "test_plan_id": "plan-demo", "source": "manual"},
    )
    run_id = created.json()["id"]
    client.post(f"/api/v1/test-runs/{run_id}/start", headers=AUTH)
    for _ in range(6):
        client.post(f"/api/v1/test-runs/{run_id}/collect", headers=AUTH)

    response = client.get(f"/api/v1/test-runs/{run_id}/locust/stats", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert len(body["history"]) >= 6
    assert body["history"][-1]["p95"] >= body["history"][0]["p95"]
    assert body["errors"][0]["error"] == "Simulated 500 response"
