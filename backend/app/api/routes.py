from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.core.security import require_token, verify_password
from app.models.schemas import (
    ApprovalResolve,
    BaselineRunCreate,
    LoginRequest,
    ProjectCreate,
    QuotaUpdate,
    ScriptValidationRequest,
    ScriptVersionCreate,
    TargetWhitelistCreate,
    TenantCreate,
    TestPlanClone,
    TestPlanCreate,
    TestRunCreate,
)
from app.services.scripts import validate_locustfile


def create_router(deps: dict) -> APIRouter:
    repo = deps["repo"]
    runner = deps["runner"]
    metrics = deps["metrics"]
    artifacts = deps["artifacts"]
    router = APIRouter()

    def current_user(token: str = Depends(require_token)) -> dict:
        user = repo.get_user_by_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid bearer token")
        return user

    def ensure_admin(user: dict) -> None:
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")

    def ensure_tenant_access(tenant_id: str, user: dict) -> None:
        if user["role"] != "admin" and user["tenant_id"] != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant access denied")

    def scoped_rows(table: str, user: dict) -> list[dict]:
        rows = repo.list_table(table)
        if user["role"] == "admin":
            return rows
        if table == "tenants":
            return [row for row in rows if row["id"] == user["tenant_id"]]
        return [row for row in rows if row.get("tenant_id") == user["tenant_id"]]

    def require_scoped_record(table: str, item_id: str, user: dict, detail: str) -> dict:
        item = repo.get_by_id(table, item_id)
        if not item:
            raise HTTPException(status_code=404, detail=detail)
        tenant_id = item.get("tenant_id")
        if tenant_id:
            ensure_tenant_access(tenant_id, user)
        return item

    def enrich_report(report: dict) -> dict:
        artifact_fields = [
            ("html_artifact_id", "HTML Report", "html"),
            ("requests_csv_artifact_id", "Requests CSV", "requests_csv"),
            ("failures_csv_artifact_id", "Failures CSV", "failures_csv"),
            ("exceptions_csv_artifact_id", "Exceptions CSV", "exceptions_csv"),
            ("history_csv_artifact_id", "History CSV", "history_csv"),
            ("logs_artifact_id", "Master Log", "master_log"),
        ]
        enriched = dict(report)
        enriched_artifacts = []
        for field, name, kind in artifact_fields:
            artifact_id = report.get(field)
            if not artifact_id:
                continue
            artifact = repo.get_artifact(artifact_id)
            if not artifact:
                continue
            enriched_artifacts.append(
                {
                    "id": artifact["id"],
                    "name": name,
                    "kind": kind,
                    "content_type": artifact["content_type"],
                    "size_bytes": artifact["size_bytes"],
                    "checksum": artifact["checksum"],
                    "download_url": f"/api/v1/artifacts/{artifact['id']}/download",
                }
            )
        enriched["artifacts"] = enriched_artifacts
        enriched["log_preview"] = ""
        if report.get("logs_artifact_id"):
            log_artifact = repo.get_artifact(report["logs_artifact_id"])
            if log_artifact:
                try:
                    # Log previews are best-effort; download links remain
                    # available even if an external object store is temporarily
                    # unreachable from the control plane.
                    enriched["log_preview"] = artifacts.read_text(log_artifact["object_key"])[:4000]
                except Exception:
                    enriched["log_preview"] = ""
        return enriched

    @router.post("/auth/login", tags=["Auth"], summary="Login and return bearer token")
    def login(payload: LoginRequest) -> dict:
        """Validate credentials against the persisted users table and return its token."""
        user = repo.get_user_by_username(payload.username)
        if not user or not verify_password(payload.username, payload.password, user.get("password_hash")):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return {"access_token": user["token"], "token_type": "bearer"}

    @router.get("/me", tags=["Auth"], summary="Get current user")
    def me(user: dict = Depends(current_user)) -> dict:
        """Return the authenticated user profile and tenant context from storage."""
        return {"id": user["id"], "username": user["username"], "tenant_id": user["tenant_id"], "role": user["role"]}

    @router.get("/tenants", tags=["Tenants"], summary="List tenants")
    def tenants(user: dict = Depends(current_user)) -> list[dict]:
        """List tenants visible to the current user."""
        return scoped_rows("tenants", user)

    @router.post("/tenants", tags=["Tenants"], summary="Create tenant")
    def create_tenant(payload: TenantCreate, user: dict = Depends(current_user)) -> dict:
        """Create a tenant and initialize its default quota record."""
        ensure_admin(user)
        return repo.insert_tenant(payload.model_dump())

    @router.get("/projects", tags=["Projects"], summary="List projects")
    def projects(user: dict = Depends(current_user)) -> list[dict]:
        """List projects visible to the current user."""
        return scoped_rows("projects", user)

    @router.post("/projects", tags=["Projects"], summary="Create project")
    def create_project(payload: ProjectCreate, user: dict = Depends(current_user)) -> dict:
        """Create a project under a tenant."""
        ensure_tenant_access(payload.tenant_id, user)
        return repo.insert_project(payload.model_dump())

    @router.get("/scripts", tags=["Scripts"], summary="List script versions")
    def scripts(user: dict = Depends(current_user)) -> list[dict]:
        """List Locust script versions visible to the current user."""
        return scoped_rows("script_versions", user)

    @router.post("/scripts", tags=["Scripts"], summary="Create script version")
    def create_script(payload: ScriptVersionCreate, user: dict = Depends(current_user)) -> dict:
        """Store a Locust script version and its optional Python requirements."""
        ensure_tenant_access(payload.tenant_id, user)
        return repo.insert_script_version(payload.model_dump())

    @router.post("/scripts/validate", tags=["Scripts"], summary="Validate Locustfile")
    def validate_script(payload: ScriptValidationRequest, user: dict = Depends(current_user)) -> dict:
        """Statically validate Locustfile syntax, HttpUser usage, and task decorators."""
        return validate_locustfile(payload.locustfile)

    @router.get("/scripts/{script_id}/versions", tags=["Scripts"], summary="List script versions")
    def script_versions(script_id: str, user: dict = Depends(current_user)) -> list[dict]:
        """List versions for a script id placeholder used by the MVP data model."""
        return [item for item in scoped_rows("script_versions", user) if item["id"] == script_id]

    @router.get("/test-plans", tags=["Test Plans"], summary="List test plans")
    def test_plans(user: dict = Depends(current_user)) -> list[dict]:
        """List load test plans that can be used to create test runs."""
        return scoped_rows("test_plans", user)

    @router.post("/test-plans", tags=["Test Plans"], summary="Create test plan")
    def create_test_plan(payload: TestPlanCreate, user: dict = Depends(current_user)) -> dict:
        """Create a reusable Locust test plan with target, load, and worker settings."""
        ensure_tenant_access(payload.tenant_id, user)
        return repo.insert_test_plan(payload.model_dump())

    @router.post("/test-plans/{plan_id}/clone", tags=["Test Plans"], summary="Clone test plan")
    def clone_test_plan(plan_id: str, payload: TestPlanClone, user: dict = Depends(current_user)) -> dict:
        """Copy an existing plan so users can tune load settings without re-entering every field."""
        plan = require_scoped_record("test_plans", plan_id, user, "Test plan not found")
        cloned = repo.clone_test_plan(plan["id"], payload.name)
        if not cloned:
            raise HTTPException(status_code=404, detail="Test plan not found")
        return cloned

    @router.post("/test-runs", tags=["Test Runs"], summary="Create test run")
    def create_test_run(payload: TestRunCreate, user: dict = Depends(current_user)) -> dict:
        """Create a run by copying execution settings from a test plan."""
        ensure_tenant_access(payload.tenant_id, user)
        return repo.create_run_from_plan(payload.model_dump())

    @router.get("/test-runs", tags=["Test Runs"], summary="List test runs")
    def test_runs(user: dict = Depends(current_user)) -> list[dict]:
        """List all test runs and their current lifecycle status."""
        return scoped_rows("test_runs", user)

    @router.get("/test-runs/{run_id}", tags=["Test Runs"], summary="Get test run")
    def test_run(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Return a single test run by id."""
        return require_scoped_record("test_runs", run_id, user, "Test run not found")

    @router.get("/test-runs/{run_id}/diagnostics", tags=["Test Runs"], summary="Get run diagnostics")
    def run_diagnostics(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Return lifecycle events, runtime lane, latest metrics, and operator hints."""
        run = require_scoped_record("test_runs", run_id, user, "Test run not found")
        snapshots = repo.run_snapshots(run_id)
        latest_snapshot = snapshots[-1] if snapshots else None
        errors = repo.latest_errors(run_id)
        lane = repo.get_lane_by_run(run_id)
        report = repo.get_report(run_id)
        recommendations = []
        if not lane and run["status"] in {"PROVISIONING", "RUNNING"}:
            recommendations.append("No runtime lane is recorded; check Kubernetes namespace and service account creation.")
        if errors:
            recommendations.append("Failures are present; inspect the Failures and Logs tabs before accepting the result.")
        if run["status"] == "COMPLETED" and not report:
            recommendations.append("Run completed without an archived report; retry stop/archive or inspect artifact storage.")
        if not recommendations:
            recommendations.append("Run telemetry is available; continue watching charts or archive the report when finished.")
        return {
            "run": run,
            "lane": lane,
            "latest_snapshot": latest_snapshot,
            "latest_errors": errors,
            "workers": repo.latest_workers(run_id),
            "report": report,
            "events": repo.run_events(run_id),
            "recommendations": recommendations,
        }

    @router.post("/test-runs/{run_id}/rerun", tags=["Test Runs"], summary="Rerun test run")
    def rerun(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Create a fresh run from the same test plan as an existing run."""
        run = require_scoped_record("test_runs", run_id, user, "Test run not found")
        return repo.create_run_from_plan(
            {
                "tenant_id": run["tenant_id"],
                "project_id": run["project_id"],
                "test_plan_id": run["test_plan_id"],
                "source": "manual",
            }
        )

    @router.post("/test-runs/{run_id}/start", tags=["Test Runs"], summary="Start test run")
    def start_run(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Validate admission, create the runtime lane, and begin collecting metrics."""
        require_scoped_record("test_runs", run_id, user, "Test run not found")
        try:
            return runner.start(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @router.post("/test-runs/{run_id}/collect", tags=["Metrics"], summary="Collect one metrics sample")
    def collect_run(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Collect one sample from the configured metrics backend for a running test."""
        require_scoped_record("test_runs", run_id, user, "Test run not found")
        return {"samples": runner.collect(run_id, samples=1)}

    @router.post("/test-runs/{run_id}/stop", tags=["Test Runs"], summary="Stop test run and archive report")
    def stop_run(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Collect final metrics, archive reports, destroy the lane, and mark the run completed."""
        require_scoped_record("test_runs", run_id, user, "Test run not found")
        try:
            return runner.stop(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @router.get("/test-runs/{run_id}/locust/stats", tags=["Metrics"], summary="Get Locust UI compatible stats")
    def locust_stats(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Return the latest stats using Locust UI field names for frontend reuse."""
        require_scoped_record("test_runs", run_id, user, "Test run not found")
        snapshots = repo.run_snapshots(run_id)
        stats = repo.latest_request_stats(run_id)
        errors = repo.latest_errors(run_id)
        workers = repo.latest_workers(run_id)
        latest = snapshots[-1] if snapshots else None
        return metrics.format_locust_stats(latest, stats, workers, errors=errors, snapshots=snapshots)

    @router.get("/test-runs/{run_id}/locust/workers", tags=["Metrics"], summary="Get latest worker states")
    def locust_workers(run_id: str, user: dict = Depends(current_user)) -> list[dict]:
        """Return the latest worker status rows collected for the run."""
        require_scoped_record("test_runs", run_id, user, "Test run not found")
        return repo.latest_workers(run_id)

    @router.get("/test-runs/{run_id}/lane", tags=["Runtime Lanes"], summary="Get runtime lane")
    def lane(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Return the stored namespace, service account, and manifest for a run lane."""
        require_scoped_record("test_runs", run_id, user, "Test run not found")
        lane = repo.get_lane_by_run(run_id)
        if not lane:
            raise HTTPException(status_code=404, detail="Lane not found")
        return lane

    @router.get("/test-runs/{run_id}/report", tags=["Reports"], summary="Get archived report summary")
    def report(run_id: str, user: dict = Depends(current_user)) -> dict:
        """Return the report summary and artifact ids after a run has been archived."""
        require_scoped_record("test_runs", run_id, user, "Test run not found")
        report = repo.get_report(run_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not archived")
        return enrich_report(report)

    @router.get("/artifacts/{artifact_id}/download", tags=["Reports"], summary="Download archived artifact")
    def download_artifact(artifact_id: str, user: dict = Depends(current_user)):
        """Download a report, CSV, or log artifact after enforcing tenant scope."""
        artifact = repo.get_artifact(artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        ensure_tenant_access(artifact["tenant_id"], user)
        filename = artifact["object_key"].rstrip("/").split("/")[-1] or artifact["id"]
        if hasattr(artifacts, "path_for"):
            path = artifacts.path_for(artifact["object_key"])
            if not path.exists():
                raise HTTPException(status_code=404, detail="Artifact content not found")
            return FileResponse(path, media_type=artifact["content_type"], filename=filename)
        return RedirectResponse(artifacts.generate_download_url(artifact["object_key"]))

    @router.get("/target-whitelists", tags=["Governance"], summary="List target whitelist entries")
    def targets(user: dict = Depends(current_user)) -> list[dict]:
        """List approved and pending load test targets."""
        return scoped_rows("target_whitelists", user)

    @router.post("/target-whitelists", tags=["Governance"], summary="Create target whitelist request")
    def create_target(payload: TargetWhitelistCreate, user: dict = Depends(current_user)) -> dict:
        """Create a pending target whitelist entry that must be approved before use."""
        ensure_tenant_access(payload.tenant_id, user)
        return repo.insert_target(payload.model_dump())

    @router.post("/target-whitelists/{target_id}/approve", tags=["Governance"], summary="Approve target whitelist entry")
    def approve_target(target_id: str, user: dict = Depends(current_user)) -> dict:
        """Approve a target so test plans for the project can run against it."""
        ensure_admin(user)
        target = repo.approve_target(target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        return target

    @router.get("/approval-requests", tags=["Governance"], summary="List approval requests")
    def approval_requests(user: dict = Depends(current_user)) -> list[dict]:
        """List pending and resolved approval requests for target and quota governance."""
        return scoped_rows("approval_requests", user)

    @router.post("/approval-requests/{approval_id}/resolve", tags=["Governance"], summary="Resolve approval request")
    def resolve_approval_request(approval_id: str, payload: ApprovalResolve, user: dict = Depends(current_user)) -> dict:
        """Approve or reject a governance request and update its linked resource."""
        ensure_admin(user)
        approval = repo.resolve_approval_request(approval_id, payload.status, payload.actor)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")
        return approval

    @router.get("/dns-resolution-snapshots", tags=["Governance"], summary="List DNS/IP admission snapshots")
    def dns_resolution_snapshots(user: dict = Depends(current_user)) -> list[dict]:
        """List DNS resolution and IP risk decisions captured during admission."""
        return scoped_rows("dns_resolution_snapshots", user)

    @router.get("/quota-usage-snapshots", tags=["Governance"], summary="List quota usage snapshots")
    def quota_usage_snapshots(user: dict = Depends(current_user)) -> list[dict]:
        """List resource and traffic quota decisions captured during admission."""
        return scoped_rows("quota_usage_snapshots", user)

    @router.get("/tenant-quotas", tags=["Governance"], summary="List tenant quotas")
    def quotas(user: dict = Depends(current_user)) -> list[dict]:
        """List resource and traffic quotas used by admission control."""
        return scoped_rows("tenant_quotas", user)

    @router.put("/tenant-quotas/{tenant_id}", tags=["Governance"], summary="Update tenant quota")
    def update_quota(tenant_id: str, payload: QuotaUpdate, user: dict = Depends(current_user)) -> dict:
        """Update admission limits for one tenant."""
        ensure_tenant_access(tenant_id, user)
        return repo.update_quota(tenant_id, payload.model_dump())

    @router.post("/ci/performance-runs", tags=["CI Baselines"], summary="Create CI performance baseline run")
    def create_ci_run(payload: BaselineRunCreate, user: dict = Depends(current_user)) -> dict:
        """Create and start a CI-triggered performance run, then evaluate request thresholds."""
        ensure_tenant_access(payload.tenant_id, user)
        run = repo.create_run_from_plan(
            {
                "tenant_id": payload.tenant_id,
                "project_id": payload.project_id,
                "test_plan_id": payload.test_plan_id,
                "source": "ci",
            }
        )
        started = runner.start(run["id"])
        if started["status"] == "RUNNING":
            # CI baselines need enough samples to evaluate non-instant metrics
            # such as fail ratio, while manual runs can keep the faster start.
            runner.collect(run["id"], samples=2)
        violations = []
        stats = repo.run_snapshots(run["id"])
        latest = stats[-1] if stats else {}
        p95 = latest.get("current_p95", 0)
        fail_ratio = latest.get("fail_ratio", 0)
        total_rps = latest.get("total_rps", 0)
        if p95 > payload.max_p95_ms:
            violations.append({"metric": "p95", "operator": "<=", "expected": payload.max_p95_ms, "actual": p95})
        if fail_ratio > payload.max_fail_ratio:
            violations.append({"metric": "fail_ratio", "operator": "<=", "expected": payload.max_fail_ratio, "actual": fail_ratio})
        if payload.min_total_rps is not None and total_rps < payload.min_total_rps:
            violations.append({"metric": "total_rps", "operator": ">=", "expected": payload.min_total_rps, "actual": total_rps})
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

    @router.get("/ci/performance-runs/{test_run_id}/result", tags=["CI Baselines"], summary="Get CI performance baseline result")
    def ci_run_result(test_run_id: str, user: dict = Depends(current_user)) -> dict:
        """Return persisted CI baseline conclusion and threshold violations for a test run."""
        run = require_scoped_record("test_runs", test_run_id, user, "Test run not found")
        baseline = repo.get_baseline_by_run(test_run_id)
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline result not found")
        return {
            "test_run_id": run["id"],
            "baseline_run_id": baseline["id"],
            "status": baseline["status"],
            "conclusion": baseline["conclusion"],
            "violations": baseline.get("violations", []),
            "ci_provider": baseline["ci_provider"],
            "pipeline_id": baseline["pipeline_id"],
            "job_id": baseline["job_id"],
            "commit_sha": baseline["commit_sha"],
            "branch": baseline["branch"],
            "created_at": baseline["created_at"],
        }

    return router
