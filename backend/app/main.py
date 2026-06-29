from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import create_router
from app.core.config import get_settings
from app.core.database import Database, MySQLDatabase
from app.repositories.mysql_repo import MySQLRepository
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.admission import RunAdmissionController
from app.services.artifacts import AliyunOssArtifactRepository, LocalArtifactRepository
from app.services.lane import LaneController, LaneRuntimeConfig
from app.services.metrics import LocustApiMetricsCollector, LocustMetricsSimulator, LocustReportFetcher
from app.services.reports import ReportArchiver
from app.services.runner import TestRunService


OPENAPI_TAGS = [
    {"name": "Auth", "description": "Demo authentication and current user context."},
    {"name": "Tenants", "description": "Tenant records and default quota bootstrap."},
    {"name": "Projects", "description": "Tenant-owned project management."},
    {"name": "Scripts", "description": "Locust script version management."},
    {"name": "Test Plans", "description": "Reusable load test plans with target and traffic settings."},
    {"name": "Test Runs", "description": "Load test run lifecycle operations."},
    {"name": "Metrics", "description": "Locust UI compatible realtime metrics endpoints."},
    {"name": "Runtime Lanes", "description": "Kubernetes namespace, service account, and lane manifest inspection."},
    {"name": "Reports", "description": "Archived report and artifact metadata."},
    {"name": "Governance", "description": "Target whitelist, approval, and tenant quota APIs."},
    {"name": "CI Baselines", "description": "CI-triggered performance baseline execution."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.database_backend == "mysql":
        database = MySQLDatabase(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
        )
        repo = MySQLRepository(database)
    else:
        database = Database(settings.database_path)
        repo = SQLiteRepository(database)
    repo.init_schema()
    repo.seed_demo(settings.demo_token)

    if settings.artifact_storage_provider == "aliyun_oss":
        artifacts = AliyunOssArtifactRepository(
            endpoint=settings.aliyun_oss_endpoint,
            bucket=settings.aliyun_oss_bucket,
            access_key_id=settings.aliyun_oss_access_key_id,
            access_key_secret=settings.aliyun_oss_access_key_secret,
            signed_url_expire_seconds=settings.aliyun_oss_signed_url_expire_seconds,
        )
    else:
        artifacts = LocalArtifactRepository(settings.artifact_root)
    if settings.locust_metrics_backend == "locust_api":
        metrics = LocustApiMetricsCollector(settings.locust_master_base_url_template, settings.locust_api_timeout_seconds)
    else:
        metrics = LocustMetricsSimulator()
    runner = TestRunService(
        repo=repo,
        admission=RunAdmissionController(repo),
        lanes=LaneController(
            LaneRuntimeConfig(
                backend=settings.lane_runtime_backend,
                namespace_strategy=settings.lane_namespace_strategy,
                kubernetes_apply_enabled=settings.kubernetes_apply_enabled,
                locust_image=settings.locust_image,
                master_web_port=settings.locust_master_web_port,
                master_bind_port=settings.locust_master_bind_port,
                master_bind_port_plus_one=settings.locust_master_bind_port_plus_one,
            )
        ),
        metrics=metrics,
        reports=ReportArchiver(
            repo,
            artifacts,
            LocustReportFetcher(settings.locust_master_base_url_template, settings.locust_api_timeout_seconds)
            if settings.locust_metrics_backend == "locust_api"
            else None,
        ),
    )

    app = FastAPI(
        title=settings.app_name,
        description="LocustHub control plane API. Swagger UI is available at /docs and OpenAPI JSON at /openapi.json.",
        version="0.3.0",
        openapi_tags=OPENAPI_TAGS,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_router({"repo": repo, "runner": runner, "metrics": metrics, "settings": settings}), prefix=settings.api_prefix)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
