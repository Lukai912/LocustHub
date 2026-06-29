import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


def make_client(monkeypatch, tmp_path) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("DEMO_TOKEN", "dev-token")
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def auth_headers(token: str = "dev-token") -> dict:
    return {"Authorization": f"Bearer {token}"}


def demo_plan(client: TestClient) -> dict:
    return client.get("/api/v1/test-plans", headers=auth_headers()).json()[0]


def test_ci_baseline_uses_request_thresholds_and_persists_result(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    plan = demo_plan(client)

    response = client.post(
        "/api/v1/ci/performance-runs",
        headers=auth_headers(),
        json={
            "tenant_id": plan["tenant_id"],
            "project_id": plan["project_id"],
            "test_plan_id": plan["id"],
            "ci_provider": "github-actions",
            "pipeline_id": "pipeline-42",
            "job_id": "perf",
            "commit_sha": "abc123",
            "branch": "main",
            "max_p95_ms": 1,
            "max_fail_ratio": 0.001,
            "min_total_rps": 999,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conclusion"] == "failed"
    assert {item["metric"] for item in body["violations"]} == {"p95", "fail_ratio", "total_rps"}

    result = client.get(f"/api/v1/ci/performance-runs/{body['test_run_id']}/result", headers=auth_headers())

    assert result.status_code == 200
    assert result.json()["baseline_run_id"] == body["baseline_run_id"]
    assert result.json()["conclusion"] == "failed"


def test_ci_result_endpoint_is_tenant_scoped(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    plan = demo_plan(client)
    created = client.post(
        "/api/v1/ci/performance-runs",
        headers=auth_headers(),
        json={
            "tenant_id": plan["tenant_id"],
            "project_id": plan["project_id"],
            "test_plan_id": plan["id"],
            "ci_provider": "local",
            "pipeline_id": "pipeline-1",
            "job_id": "perf",
            "commit_sha": "local",
            "branch": "main",
        },
    ).json()

    response = client.get(f"/api/v1/ci/performance-runs/{created['test_run_id']}/result", headers=auth_headers("dev-token-viewer"))

    assert response.status_code == 200
    assert response.json()["test_run_id"] == created["test_run_id"]


def test_ci_baseline_script_exits_zero_for_passed_result(tmp_path):
    output = tmp_path / "result.json"
    payload = {"conclusion": "passed", "test_run_id": "run-1", "baseline_run_id": "baseline-1", "violations": []}

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
            "--output",
            str(output),
            "--mock-response-json",
            json.dumps(payload),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(output.read_text(encoding="utf-8")) == payload


def test_ci_baseline_script_exits_nonzero_for_failed_result(tmp_path):
    output = tmp_path / "result.json"
    payload = {
        "conclusion": "failed",
        "test_run_id": "run-1",
        "baseline_run_id": "baseline-1",
        "violations": [{"metric": "p95", "operator": "<=", "expected": 1, "actual": 120}],
    }

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
            "--output",
            str(output),
            "--mock-response-json",
            json.dumps(payload),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "failed" in result.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["conclusion"] == "failed"

