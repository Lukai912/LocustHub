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
    username: str = "admin"
    password: str = "admin"


class TenantCreate(BaseModel):
    name: str
    slug: str


class ProjectCreate(BaseModel):
    tenant_id: str
    name: str
    slug: str


class ScriptVersionCreate(BaseModel):
    tenant_id: str
    project_id: str
    name: str
    locustfile: str = "from locust import HttpUser, task\n"
    requirements: str = ""


class TestPlanCreate(BaseModel):
    tenant_id: str
    project_id: str
    script_version_id: str
    name: str
    target_host: str = "https://example.com"
    users: int = Field(default=10, ge=1)
    spawn_rate: int = Field(default=2, ge=1)
    run_time_seconds: int = Field(default=60, ge=1)
    worker_count: int = Field(default=1, ge=1)


class TestRunCreate(BaseModel):
    tenant_id: str
    project_id: str
    test_plan_id: str
    source: Literal["manual", "api", "ci", "schedule"] = "manual"


class TargetWhitelistCreate(BaseModel):
    tenant_id: str
    project_id: str
    target_type: Literal["domain", "ip", "cidr"] = "domain"
    value: str
    ports: list[int] = Field(default_factory=lambda: [443])
    environment: str = "test"
    reason: str = ""


class QuotaUpdate(BaseModel):
    max_concurrent_runs: int = 5
    max_workers_per_run: int = 5
    max_total_workers: int = 10
    max_users: int = 1000
    max_spawn_rate: int = 200
    max_run_duration_seconds: int = 3600


class BaselineRunCreate(BaseModel):
    tenant_id: str
    project_id: str
    baseline_profile_id: str | None = None
    test_plan_id: str
    ci_provider: str = "manual"
    pipeline_id: str = "local"
    job_id: str = "perf-test"
    commit_sha: str = "local"
    branch: str = "main"
    variables: dict[str, Any] = Field(default_factory=dict)
