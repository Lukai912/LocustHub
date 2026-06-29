from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_token
from app.models.schemas import (
    ApprovalResolve,
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

    @router.post("/auth/login", tags=["Auth"], summary="Login and return demo bearer token")
    def login(_: LoginRequest) -> dict:
        """Return the configured demo token used by the MVP management UI."""
        return {"access_token": deps["settings"].demo_token, "token_type": "bearer"}

    @router.get("/me", tags=["Auth"], summary="Get current demo user")
    def me(_: str = Depends(require_token)) -> dict:
        """Return the authenticated MVP user profile and tenant context."""
        return {"id": "user-admin", "username": "admin", "tenant_id": "tenant-demo", "role": "admin"}

    @router.get("/tenants", tags=["Tenants"], summary="List tenants")
    def tenants(_: str = Depends(require_token)) -> list[dict]:
        """List all tenants visible to the demo administrator."""
        return repo.list_table("tenants")

    @router.post("/tenants", tags=["Tenants"], summary="Create tenant")
    def create_tenant(payload: TenantCreate, _: str = Depends(require_token)) -> dict:
        """Create a tenant and initialize its default quota record."""
        return repo.insert_tenant(payload.model_dump())

    @router.get("/projects", tags=["Projects"], summary="List projects")
    def projects(_: str = Depends(require_token)) -> list[dict]:
        """List projects across tenants for the MVP admin view."""
        return repo.list_table("projects")

    @router.post("/projects", tags=["Projects"], summary="Create project")
    def create_project(payload: ProjectCreate, _: str = Depends(require_token)) -> dict:
        """Create a project under a tenant."""
        return repo.insert_project(payload.model_dump())

    @router.post("/scripts", tags=["Scripts"], summary="Create script version")
    def create_script(payload: ScriptVersionCreate, _: str = Depends(require_token)) -> dict:
        """Store a Locust script version and its optional Python requirements."""
        return repo.insert_script_version(payload.model_dump())

    @router.get("/scripts/{script_id}/versions", tags=["Scripts"], summary="List script versions")
    def script_versions(script_id: str, _: str = Depends(require_token)) -> list[dict]:
        """List versions for a script id placeholder used by the MVP data model."""
        return [item for item in repo.list_table("script_versions") if item["id"] == script_id]

    @router.get("/test-plans", tags=["Test Plans"], summary="List test plans")
    def test_plans(_: str = Depends(require_token)) -> list[dict]:
        """List load test plans that can be used to create test runs."""
        return repo.list_table("test_plans")

    @router.post("/test-plans", tags=["Test Plans"], summary="Create test plan")
    def create_test_plan(payload: TestPlanCreate, _: str = Depends(require_token)) -> dict:
        """Create a reusable Locust test plan with target, load, and worker settings."""
        return repo.insert_test_plan(payload.model_dump())

    @router.post("/test-runs", tags=["Test Runs"], summary="Create test run")
    def create_test_run(payload: TestRunCreate, _: str = Depends(require_token)) -> dict:
        """Create a run by copying execution settings from a test plan."""
        return repo.create_run_from_plan(payload.model_dump())

    @router.get("/test-runs", tags=["Test Runs"], summary="List test runs")
    def test_runs(_: str = Depends(require_token)) -> list[dict]:
        """List all test runs and their current lifecycle status."""
        return repo.list_table("test_runs")

    @router.get("/test-runs/{run_id}", tags=["Test Runs"], summary="Get test run")
    def test_run(run_id: str, _: str = Depends(require_token)) -> dict:
        """Return a single test run by id."""
        run = repo.get_by_id("test_runs", run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")
        return run

    @router.post("/test-runs/{run_id}/start", tags=["Test Runs"], summary="Start test run")
    def start_run(run_id: str, _: str = Depends(require_token)) -> dict:
        """Validate admission, create the runtime lane, and begin collecting metrics."""
        try:
            return runner.start(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @router.post("/test-runs/{run_id}/collect", tags=["Metrics"], summary="Collect one metrics sample")
    def collect_run(run_id: str, _: str = Depends(require_token)) -> dict:
        """Collect one sample from the configured metrics backend for a running test."""
        return {"samples": runner.collect(run_id, samples=1)}

    @router.post("/test-runs/{run_id}/stop", tags=["Test Runs"], summary="Stop test run and archive report")
    def stop_run(run_id: str, _: str = Depends(require_token)) -> dict:
        """Collect final metrics, archive reports, destroy the lane, and mark the run completed."""
        try:
            return runner.stop(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @router.get("/test-runs/{run_id}/locust/stats", tags=["Metrics"], summary="Get Locust UI compatible stats")
    def locust_stats(run_id: str, _: str = Depends(require_token)) -> dict:
        """Return the latest stats using Locust UI field names for frontend reuse."""
        snapshots = repo.run_snapshots(run_id)
        stats = repo.latest_request_stats(run_id)
        workers = repo.latest_workers(run_id)
        latest = snapshots[-1] if snapshots else None
        return metrics.format_locust_stats(latest, stats, workers)

    @router.get("/test-runs/{run_id}/locust/workers", tags=["Metrics"], summary="Get latest worker states")
    def locust_workers(run_id: str, _: str = Depends(require_token)) -> list[dict]:
        """Return the latest worker status rows collected for the run."""
        return repo.latest_workers(run_id)

    @router.get("/test-runs/{run_id}/lane", tags=["Runtime Lanes"], summary="Get runtime lane")
    def lane(run_id: str, _: str = Depends(require_token)) -> dict:
        """Return the stored namespace, service account, and manifest for a run lane."""
        lane = repo.get_lane_by_run(run_id)
        if not lane:
            raise HTTPException(status_code=404, detail="Lane not found")
        return lane

    @router.get("/test-runs/{run_id}/report", tags=["Reports"], summary="Get archived report summary")
    def report(run_id: str, _: str = Depends(require_token)) -> dict:
        """Return the report summary and artifact ids after a run has been archived."""
        report = repo.get_report(run_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not archived")
        return report

    @router.get("/target-whitelists", tags=["Governance"], summary="List target whitelist entries")
    def targets(_: str = Depends(require_token)) -> list[dict]:
        """List approved and pending load test targets."""
        return repo.list_table("target_whitelists")

    @router.post("/target-whitelists", tags=["Governance"], summary="Create target whitelist request")
    def create_target(payload: TargetWhitelistCreate, _: str = Depends(require_token)) -> dict:
        """Create a pending target whitelist entry that must be approved before use."""
        return repo.insert_target(payload.model_dump())

    @router.post("/target-whitelists/{target_id}/approve", tags=["Governance"], summary="Approve target whitelist entry")
    def approve_target(target_id: str, _: str = Depends(require_token)) -> dict:
        """Approve a target so test plans for the project can run against it."""
        target = repo.approve_target(target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        return target

    @router.get("/approval-requests", tags=["Governance"], summary="List approval requests")
    def approval_requests(_: str = Depends(require_token)) -> list[dict]:
        """List pending and resolved approval requests for target and quota governance."""
        return repo.list_table("approval_requests")

    @router.post("/approval-requests/{approval_id}/resolve", tags=["Governance"], summary="Resolve approval request")
    def resolve_approval_request(approval_id: str, payload: ApprovalResolve, _: str = Depends(require_token)) -> dict:
        """Approve or reject a governance request and update its linked resource."""
        approval = repo.resolve_approval_request(approval_id, payload.status, payload.actor)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")
        return approval

    @router.get("/dns-resolution-snapshots", tags=["Governance"], summary="List DNS/IP admission snapshots")
    def dns_resolution_snapshots(_: str = Depends(require_token)) -> list[dict]:
        """List DNS resolution and IP risk decisions captured during admission."""
        return repo.list_table("dns_resolution_snapshots")

    @router.get("/quota-usage-snapshots", tags=["Governance"], summary="List quota usage snapshots")
    def quota_usage_snapshots(_: str = Depends(require_token)) -> list[dict]:
        """List resource and traffic quota decisions captured during admission."""
        return repo.list_table("quota_usage_snapshots")

    @router.get("/tenant-quotas", tags=["Governance"], summary="List tenant quotas")
    def quotas(_: str = Depends(require_token)) -> list[dict]:
        """List resource and traffic quotas used by admission control."""
        return repo.list_table("tenant_quotas")

    @router.put("/tenant-quotas/{tenant_id}", tags=["Governance"], summary="Update tenant quota")
    def update_quota(tenant_id: str, payload: QuotaUpdate, _: str = Depends(require_token)) -> dict:
        """Update admission limits for one tenant."""
        return repo.update_quota(tenant_id, payload.model_dump())

    @router.post("/ci/performance-runs", tags=["CI Baselines"], summary="Create CI performance baseline run")
    def create_ci_run(payload: BaselineRunCreate, _: str = Depends(require_token)) -> dict:
        """Create and start a CI-triggered performance run, then evaluate MVP thresholds."""
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
