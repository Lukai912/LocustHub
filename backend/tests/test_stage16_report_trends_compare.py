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


def archive_run(client: TestClient, samples: int) -> str:
    created = client.post(
        "/api/v1/test-runs",
        headers=AUTH,
        json={"tenant_id": "tenant-demo", "project_id": "project-demo", "test_plan_id": "plan-demo", "source": "manual"},
    )
    run_id = created.json()["id"]
    assert client.post(f"/api/v1/test-runs/{run_id}/start", headers=AUTH).status_code == 200
    for _ in range(samples):
        assert client.post(f"/api/v1/test-runs/{run_id}/collect", headers=AUTH).status_code == 200
    assert client.post(f"/api/v1/test-runs/{run_id}/stop", headers=AUTH).status_code == 200
    return run_id


def test_reports_endpoint_returns_history_trend(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    first_run_id = archive_run(client, samples=1)
    second_run_id = archive_run(client, samples=5)

    response = client.get("/api/v1/reports", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert [item["run_id"] for item in body["items"]] == [second_run_id, first_run_id]
    assert [point["run_id"] for point in body["trend"]] == [first_run_id, second_run_id]
    assert body["trend"][1]["p95_response_time"] >= body["trend"][0]["p95_response_time"]
    assert body["items"][0]["artifacts"]


def test_report_compare_returns_metric_deltas(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    base_run_id = archive_run(client, samples=1)
    candidate_run_id = archive_run(client, samples=5)

    response = client.get(
        "/api/v1/reports/compare",
        headers=AUTH,
        params={"base_run_id": base_run_id, "candidate_run_id": candidate_run_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["base"]["run_id"] == base_run_id
    assert body["candidate"]["run_id"] == candidate_run_id
    assert body["deltas"]["p95_response_time"]["delta"] >= 0
    assert "fail_ratio" in body["deltas"]


def test_report_compare_enforces_tenant_scope(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    base_run_id = archive_run(client, samples=1)
    candidate_run_id = archive_run(client, samples=2)
    other_tenant = client.post("/api/v1/tenants", headers=AUTH, json={"name": "Other Tenant", "slug": "other"}).json()
    other_user = client.post(
        "/api/v1/users",
        headers=AUTH,
        json={"tenant_id": other_tenant["id"], "username": "other-viewer", "password": "secret", "role": "viewer"},
    ).json()

    response = client.get(
        "/api/v1/reports/compare",
        headers={"Authorization": f"Bearer {other_user['token']}"},
        params={"base_run_id": base_run_id, "candidate_run_id": candidate_run_id},
    )

    assert response.status_code == 403
