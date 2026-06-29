from fastapi.testclient import TestClient

from app.main import create_app


def auth_headers(token: str = "dev-token") -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_mvp_run_lifecycle():
    client = TestClient(create_app())

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    plans = client.get("/api/v1/test-plans", headers=auth_headers())
    assert plans.status_code == 200
    plan = plans.json()[0]

    create_run = client.post(
        "/api/v1/test-runs",
        headers=auth_headers(),
        json={
            "tenant_id": plan["tenant_id"],
            "project_id": plan["project_id"],
            "test_plan_id": plan["id"],
            "source": "manual",
        },
    )
    assert create_run.status_code == 200
    run = create_run.json()

    started = client.post(f"/api/v1/test-runs/{run['id']}/start", headers=auth_headers())
    assert started.status_code == 200
    assert started.json()["status"] == "RUNNING"

    stats = client.get(f"/api/v1/test-runs/{run['id']}/locust/stats", headers=auth_headers())
    assert stats.status_code == 200
    stats_body = stats.json()
    assert stats_body["total_rps"] > 0
    assert stats_body["stats"][0]["current_rps"] > 0
    assert "response_time_percentile_0.95" in stats_body["stats"][0]

    stopped = client.post(f"/api/v1/test-runs/{run['id']}/stop", headers=auth_headers())
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "COMPLETED"

    report = client.get(f"/api/v1/test-runs/{run['id']}/report", headers=auth_headers())
    assert report.status_code == 200
    assert report.json()["report_status"] == "archived"


def test_openapi_documents_core_api_groups_and_fields():
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    start_run = spec["paths"]["/api/v1/test-runs/{run_id}/start"]["post"]
    locust_stats = spec["paths"]["/api/v1/test-runs/{run_id}/locust/stats"]["get"]
    assert start_run["summary"] == "Start test run"
    assert "Test Runs" in start_run["tags"]
    assert locust_stats["summary"] == "Get Locust UI compatible stats"
    assert "Metrics" in locust_stats["tags"]
    test_plan_schema = spec["components"]["schemas"]["TestPlanCreate"]["properties"]
    assert test_plan_schema["target_host"]["description"]
    assert test_plan_schema["worker_count"]["description"]


def test_unapproved_target_goes_to_approval_pending():
    client = TestClient(create_app())

    tenant = "tenant-demo"
    project = "project-demo"
    script = client.post(
        "/api/v1/scripts",
        headers=auth_headers(),
        json={
            "tenant_id": tenant,
            "project_id": project,
            "name": "Unapproved target script",
            "locustfile": "from locust import HttpUser\n",
            "requirements": "",
        },
    ).json()
    plan = client.post(
        "/api/v1/test-plans",
        headers=auth_headers(),
        json={
            "tenant_id": tenant,
            "project_id": project,
            "script_version_id": script["id"],
            "name": "Unapproved Plan",
            "target_host": "https://not-approved.example",
            "users": 5,
            "spawn_rate": 1,
            "run_time_seconds": 30,
            "worker_count": 1,
        },
    ).json()
    run = client.post(
        "/api/v1/test-runs",
        headers=auth_headers(),
        json={
            "tenant_id": tenant,
            "project_id": project,
            "test_plan_id": plan["id"],
            "source": "manual",
        },
    ).json()

    started = client.post(f"/api/v1/test-runs/{run['id']}/start", headers=auth_headers())
    assert started.status_code == 200
    assert started.json()["status"] == "APPROVAL_PENDING"


def test_ci_baseline_reuses_test_run_engine():
    client = TestClient(create_app())
    plan = client.get("/api/v1/test-plans", headers=auth_headers()).json()[0]

    response = client.post(
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
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"
    assert response.json()["conclusion"] in {"passed", "failed"}
