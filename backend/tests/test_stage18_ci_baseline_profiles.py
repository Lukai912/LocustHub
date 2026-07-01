import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


AUTH = {"Authorization": "Bearer dev-token"}
REPO_ROOT = Path(__file__).resolve().parents[2]


def make_client(monkeypatch, tmp_path) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def demo_plan(client: TestClient) -> dict:
    return client.get("/api/v1/test-plans", headers=AUTH).json()[0]


def test_ci_baseline_profile_can_drive_thresholds(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    plan = demo_plan(client)
    profile = client.post(
        "/api/v1/ci/baseline-profiles",
        headers=AUTH,
        json={
            "tenant_id": plan["tenant_id"],
            "project_id": plan["project_id"],
            "name": "strict profile",
            "max_p95_ms": 1,
            "max_fail_ratio": 0.001,
            "min_total_rps": 999,
        },
    )

    response = client.post(
        "/api/v1/ci/performance-runs",
        headers=AUTH,
        json={
            "tenant_id": plan["tenant_id"],
            "project_id": plan["project_id"],
            "test_plan_id": plan["id"],
            "baseline_profile_id": profile.json()["id"],
            "ci_provider": "github-actions",
        },
    )

    assert profile.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["baseline_profile_id"] == profile.json()["id"]
    assert body["conclusion"] == "failed"
    assert {item["metric"] for item in body["violations"]} == {"p95", "fail_ratio", "total_rps"}


def test_ci_api_token_requires_ci_run_scope(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    plan = demo_plan(client)
    token = client.post("/api/v1/api-tokens", headers=AUTH, json={"name": "reports", "scopes": ["reports:read"]}).json()["token"]

    response = client.post(
        "/api/v1/ci/performance-runs",
        headers={"Authorization": f"Bearer {token}"},
        json={"tenant_id": plan["tenant_id"], "project_id": plan["project_id"], "test_plan_id": plan["id"]},
    )

    assert response.status_code == 403
    assert "ci:run" in response.json()["detail"]


def test_ci_baseline_script_sends_profile_id_in_payload(tmp_path):
    output = tmp_path / "result.json"
    payload = {"conclusion": "passed", "test_run_id": "run-1", "baseline_run_id": "baseline-1", "violations": []}
    capture = tmp_path / "payload.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_ci_baseline.py",
            "--api-base-url",
            "http://example.invalid/api/v1",
            "--token",
            "dev-token",
            "--tenant-id",
            "tenant-demo",
            "--project-id",
            "project-demo",
            "--test-plan-id",
            "plan-demo",
            "--baseline-profile-id",
            "profile-strict",
            "--output",
            str(output),
            "--mock-response-json",
            json.dumps(payload),
            "--capture-payload",
            str(capture),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(capture.read_text(encoding="utf-8"))["baseline_profile_id"] == "profile-strict"
