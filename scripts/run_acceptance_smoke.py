#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
for site_packages in (REPO_ROOT / ".venv" / "lib").glob("python*/site-packages"):
    sys.path.insert(0, str(site_packages))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LocustHub local MVP acceptance smoke checks.")
    parser.add_argument("--output", default="docs/reports/final-acceptance-smoke.json")
    return parser.parse_args()


def auth_headers(token: str = "dev-token") -> dict:
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    args = parse_args()
    run_id = uuid.uuid4().hex
    db_path = Path(f"/private/tmp/locusthub-acceptance-smoke-{run_id}.db")
    artifact_root = Path(f"/private/tmp/locusthub-acceptance-smoke-artifacts-{run_id}")
    db_path.unlink(missing_ok=True)
    os.environ.update(
        {
            "DATABASE_BACKEND": "sqlite",
            "DATABASE_PATH": str(db_path),
            "ARTIFACT_ROOT": str(artifact_root),
            "DEMO_TOKEN": "dev-token",
        }
    )
    get_settings.cache_clear()
    client = TestClient(create_app())

    checks = {}
    health = client.get("/health")
    health.raise_for_status()
    checks["health"] = health.json()

    openapi = client.get("/openapi.json")
    openapi.raise_for_status()
    checks["openapi"] = {"paths": len(openapi.json()["paths"])}

    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    login.raise_for_status()
    token = login.json()["access_token"]
    me = client.get("/api/v1/me", headers=auth_headers(token))
    me.raise_for_status()
    checks["auth"] = me.json()

    plan = client.get("/api/v1/test-plans", headers=auth_headers(token)).json()[0]
    created = client.post(
        "/api/v1/test-runs",
        headers=auth_headers(token),
        json={
            "tenant_id": plan["tenant_id"],
            "project_id": plan["project_id"],
            "test_plan_id": plan["id"],
            "source": "manual",
        },
    )
    created.raise_for_status()
    run = created.json()
    started = client.post(f"/api/v1/test-runs/{run['id']}/start", headers=auth_headers(token))
    started.raise_for_status()
    stats = client.get(f"/api/v1/test-runs/{run['id']}/locust/stats", headers=auth_headers(token))
    stats.raise_for_status()
    stopped = client.post(f"/api/v1/test-runs/{run['id']}/stop", headers=auth_headers(token))
    stopped.raise_for_status()
    stats_body = stats.json()
    checks["load_test"] = {
        "run_status": stopped.json()["status"],
        "total_rps": stats_body["total_rps"],
        "p95": stats_body["stats"][0]["response_time_percentile_0.95"],
    }

    report = client.get(f"/api/v1/test-runs/{run['id']}/report", headers=auth_headers(token))
    report.raise_for_status()
    report_body = report.json()
    checks["report"] = {
        "report_status": report_body["report_status"],
        "total_requests": report_body["total_requests"],
        "total_failures": report_body["total_failures"],
        "p95_response_time": report_body["p95_response_time"],
    }

    baseline = client.post(
        "/api/v1/ci/performance-runs",
        headers=auth_headers(token),
        json={
            "tenant_id": plan["tenant_id"],
            "project_id": plan["project_id"],
            "test_plan_id": plan["id"],
            "ci_provider": "local",
            "pipeline_id": "acceptance",
            "job_id": "smoke",
            "commit_sha": "local",
            "branch": "main",
        },
    )
    baseline.raise_for_status()
    result = client.get(f"/api/v1/ci/performance-runs/{baseline.json()['test_run_id']}/result", headers=auth_headers(token))
    result.raise_for_status()
    result_body = result.json()
    checks["ci_baseline"] = {
        "status": result_body["status"],
        "conclusion": result_body["conclusion"],
        "violations": result_body["violations"],
    }

    verifier = subprocess.run(
        [sys.executable, "scripts/verify_deployment_package.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    checks["deployment_package"] = {"ready": verifier.returncode == 0, "output": verifier.stdout.strip()}

    status = "passed" if all(
        [
            checks["health"]["status"] == "ok",
            checks["auth"]["username"] == "admin",
            checks["load_test"]["run_status"] == "COMPLETED",
            checks["load_test"]["total_rps"] > 0,
            checks["report"]["report_status"] == "archived",
            checks["deployment_package"]["ready"],
        ]
    ) else "failed"
    final_report = {"status": status, "checks": checks}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(final_report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"LocustHub acceptance smoke {status}: {output}")
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
