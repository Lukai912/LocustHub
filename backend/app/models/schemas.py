from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


RunStatus = Literal[
    "CREATED",
    "VALIDATING",
    "APPROVAL_PENDING",
    "APPROVED",
    "LANE_CREATING",
    "PROVISIONING",
    "RUNNING",
    "COLLECTING",
    "ARCHIVING",
    "DESTROYING",
    "COMPLETED",
    "FAILED",
    "CANCELING",
    "CANCELED",
]


class LoginRequest(BaseModel):
    username: str = Field(default="admin", description="Login username for the MVP demo user.")
    password: str = Field(default="admin", description="Login password placeholder; token auth is used in the MVP.")


class TenantCreate(BaseModel):
    name: str = Field(description="Tenant display name.")
    slug: str = Field(description="Unique tenant slug used by operators and future URLs.")


class UserCreate(BaseModel):
    tenant_id: str = Field(description="Tenant id for the new user.")
    username: str = Field(description="Unique login username.")
    password: str = Field(description="Initial login password.")
    role: Literal["admin", "project_member", "viewer"] = Field(default="viewer", description="RBAC role assigned to the user.")


class ApiTokenCreate(BaseModel):
    name: str = Field(description="Human-readable token name.")
    scopes: list[str] = Field(default_factory=list, description="Token scopes reserved for CI and API clients.")


class ProjectCreate(BaseModel):
    tenant_id: str = Field(description="Owner tenant id.")
    name: str = Field(description="Project display name.")
    slug: str = Field(description="Unique project slug within the tenant.")


class ScriptVersionCreate(BaseModel):
    tenant_id: str = Field(description="Owner tenant id.")
    project_id: str = Field(description="Project id that owns this script version.")
    name: str = Field(description="Human-readable script version name.")
    locustfile: str = Field(default="from locust import HttpUser, task\n", description="Locustfile source code stored for this version.")
    requirements: str = Field(default="", description="Optional Python requirements needed by the Locust script.")


class ScriptValidationRequest(BaseModel):
    locustfile: str = Field(description="Locustfile source code to validate without executing it.")


class TestPlanCreate(BaseModel):
    tenant_id: str = Field(description="Owner tenant id.")
    project_id: str = Field(description="Project id for the load test plan.")
    script_version_id: str = Field(description="Script version used when the plan starts a run.")
    name: str = Field(description="Load test plan display name.")
    target_host: str = Field(default="https://example.com", description="Base URL that Locust will attack after whitelist approval.")
    users: int = Field(default=10, ge=1, description="Total virtual users requested for the run.")
    spawn_rate: int = Field(default=2, ge=1, description="Virtual users spawned per second.")
    run_time_seconds: int = Field(default=60, ge=1, description="Run duration in seconds.")
    worker_count: int = Field(default=1, ge=1, description="Locust worker replica count.")


class TestPlanClone(BaseModel):
    name: str | None = Field(default=None, description="Optional display name for the copied plan.")


class TestRunCreate(BaseModel):
    tenant_id: str = Field(description="Owner tenant id.")
    project_id: str = Field(description="Project id for the run.")
    test_plan_id: str = Field(description="Plan id copied into the new run.")
    source: Literal["manual", "api", "ci", "schedule"] = Field(default="manual", description="Run trigger source.")


class TargetWhitelistCreate(BaseModel):
    tenant_id: str = Field(description="Owner tenant id.")
    project_id: str = Field(description="Project id allowed to use this target.")
    target_type: Literal["domain", "ip", "cidr"] = Field(default="domain", description="Whitelist target kind.")
    value: str = Field(description="Approved domain, IP, or CIDR value.")
    ports: list[int] = Field(default_factory=lambda: [443], description="Allowed destination ports.")
    environment: str = Field(default="test", description="Environment label such as test, staging, or prod.")
    reason: str = Field(default="", description="Business reason for requesting this target.")


class ApprovalResolve(BaseModel):
    status: Literal["approved", "rejected"] = Field(description="Approval decision.")
    actor: str = Field(default="admin", description="Reviewer username.")


class QuotaUpdate(BaseModel):
    max_concurrent_runs: int = Field(default=5, description="Maximum concurrent running test runs for a tenant.")
    max_workers_per_run: int = Field(default=5, description="Maximum worker replicas for one run.")
    max_total_workers: int = Field(default=10, description="Reserved quota field for total worker accounting.")
    max_users: int = Field(default=1000, description="Maximum virtual users for one run.")
    max_spawn_rate: int = Field(default=200, description="Maximum virtual user spawn rate per second.")
    max_run_duration_seconds: int = Field(default=3600, description="Maximum run duration in seconds.")


class BaselineRunCreate(BaseModel):
    tenant_id: str = Field(description="Owner tenant id.")
    project_id: str = Field(description="Project id for the CI performance run.")
    baseline_profile_id: str | None = Field(default=None, description="Optional future baseline profile id.")
    test_plan_id: str = Field(description="Plan id executed by CI.")
    ci_provider: str = Field(default="manual", description="CI provider name, for example github-actions or gitlab.")
    pipeline_id: str = Field(default="local", description="External pipeline id.")
    job_id: str = Field(default="perf-test", description="External CI job id.")
    commit_sha: str = Field(default="local", description="Commit SHA under test.")
    branch: str = Field(default="main", description="Source branch under test.")
    max_p95_ms: float = Field(default=500, ge=0, description="Maximum allowed p95 response time in milliseconds.")
    max_fail_ratio: float = Field(default=0.05, ge=0, description="Maximum allowed failure ratio, from 0 to 1.")
    min_total_rps: float | None = Field(default=None, ge=0, description="Optional minimum required total requests per second.")
    variables: dict[str, Any] = Field(default_factory=dict, description="Additional CI variables captured for audit.")
