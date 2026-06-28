from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_token
from app.models.schemas import (
    BaselineRunCreate,
    LoginRequest,
    ProjectCreate,
    QuotaUpdate,
    ScriptVersionCreate,
    TargetWhitelistCreate,
    TenantCreate,
    TestPlanCreate,
    TestRunCreate,
)


def create_router(deps: dict) -> APIRouter:
    repo = deps["repo"]
    runner = deps["runner"]
    metrics = deps["metrics"]
    router = APIRouter()

    @router.post("/auth/login")
    def login(_: LoginRequest) -> dict:
        return {"access_token": deps["settings"].demo_token, "token_type": "bearer"}

    @router.get("/me")
    def me(_: str = Depends(require_token)) -> dict:
        return {"id": "user-admin", "username": "admin", "tenant_id": "tenant-demo", "role": "admin"}

    @router.get("/tenants")
    def tenants(_: str = Depends(require_token)) -> list[dict]:
        return repo.list_table("tenants")

    @router.post("/tenants")
    def create_tenant(payload: TenantCreate, _: str = Depends(require_token)) -> dict:
        return repo.insert_tenant(payload.model_dump())

    @router.get("/projects")
    def projects(_: str = Depends(require_token)) -> list[dict]:
        return repo.list_table("projects")

    @router.post("/projects")
    def create_project(payload: ProjectCreate, _: str = Depends(require_token)) -> dict:
        return repo.insert_project(payload.model_dump())

    @router.post("/scripts")
    def create_script(payload: ScriptVersionCreate, _: str = Depends(require_token)) -> dict:
        return repo.insert_script_version(payload.model_dump())

    @router.get("/scripts/{script_id}/versions")
    def script_versions(script_id: str, _: str = Depends(require_token)) -> list[dict]:
        return [item for item in repo.list_table("script_versions") if item["id"] == script_id]

    @router.get("/test-plans")
    def test_plans(_: str = Depends(require_token)) -> list[dict]:
        return repo.list_table("test_plans")

    @router.post("/test-plans")
    def create_test_plan(payload: TestPlanCreate, _: str = Depends(require_token)) -> dict:
        return repo.insert_test_plan(payload.model_dump())

    @router.post("/test-runs")
    def create_test_run(payload: TestRunCreate, _: str = Depends(require_token)) -> dict:
        return repo.create_run_from_plan(payload.model_dump())

    @router.get("/test-runs")
    def test_runs(_: str = Depends(require_token)) -> list[dict]:
        return repo.list_table("test_runs")

    @router.get("/test-runs/{run_id}")
    def test_run(run_id: str, _: str = Depends(require_token)) -> dict:
        run = repo.get_by_id("test_runs", run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")
        return run

    @router.post("/test-runs/{run_id}/start")
    def start_run(run_id: str, _: str = Depends(require_token)) -> dict:
        try:
            return runner.start(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @router.post("/test-runs/{run_id}/collect")
    def collect_run(run_id: str, _: str = Depends(require_token)) -> dict:
        return {"samples": runner.collect(run_id, samples=1)}

    @router.post("/test-runs/{run_id}/stop")
    def stop_run(run_id: str, _: str = Depends(require_token)) -> dict:
        try:
            return runner.stop(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @router.get("/test-runs/{run_id}/locust/stats")
    def locust_stats(run_id: str, _: str = Depends(require_token)) -> dict:
        snapshots = repo.run_snapshots(run_id)
        stats = repo.latest_request_stats(run_id)
        workers = repo.latest_workers(run_id)
        latest = snapshots[-1] if snapshots else None
        return metrics.format_locust_stats(latest, stats, workers)

    @router.get("/test-runs/{run_id}/locust/workers")
    def locust_workers(run_id: str, _: str = Depends(require_token)) -> list[dict]:
        return repo.latest_workers(run_id)

    @router.get("/test-runs/{run_id}/report")
    def report(run_id: str, _: str = Depends(require_token)) -> dict:
        report = repo.get_report(run_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not archived")
        return report

    @router.get("/target-whitelists")
    def targets(_: str = Depends(require_token)) -> list[dict]:
        return repo.list_table("target_whitelists")

    @router.post("/target-whitelists")
    def create_target(payload: TargetWhitelistCreate, _: str = Depends(require_token)) -> dict:
        return repo.insert_target(payload.model_dump())

    @router.post("/target-whitelists/{target_id}/approve")
    def approve_target(target_id: str, _: str = Depends(require_token)) -> dict:
        target = repo.approve_target(target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        return target

    @router.get("/tenant-quotas")
    def quotas(_: str = Depends(require_token)) -> list[dict]:
        return repo.list_table("tenant_quotas")

    @router.put("/tenant-quotas/{tenant_id}")
    def update_quota(tenant_id: str, payload: QuotaUpdate, _: str = Depends(require_token)) -> dict:
        return repo.update_quota(tenant_id, payload.model_dump())

    @router.post("/ci/performance-runs")
    def create_ci_run(payload: BaselineRunCreate, _: str = Depends(require_token)) -> dict:
        run = repo.create_run_from_plan(
            {
                "tenant_id": payload.tenant_id,
                "project_id": payload.project_id,
                "test_plan_id": payload.test_plan_id,
                "source": "ci",
            }
        )
        started = runner.start(run["id"])
        violations = []
        stats = repo.run_snapshots(run["id"])
        latest = stats[-1] if stats else {}
        if latest.get("current_p95", 0) > 500:
            violations.append({"metric": "p95", "operator": "<=", "expected": 500, "actual": latest["current_p95"]})
        baseline = repo.insert_baseline_run(
            {
                "tenant_id": payload.tenant_id,
                "project_id": payload.project_id,
                "test_run_id": run["id"],
                "ci_provider": payload.ci_provider,
                "pipeline_id": payload.pipeline_id,
                "job_id": payload.job_id,
                "commit_sha": payload.commit_sha,
                "branch": payload.branch,
                "status": started["status"],
                "conclusion": "failed" if violations else "passed",
                "violations": violations,
            }
        )
        return {"test_run_id": run["id"], "baseline_run_id": baseline["id"], "status": started["status"], "conclusion": baseline["conclusion"], "violations": violations}

    return router
