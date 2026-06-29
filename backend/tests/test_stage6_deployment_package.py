import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read_repo_file(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_compose_package_runs_api_and_mysql_with_integrated_admin():
    compose = read_repo_file("docker-compose.yml")

    for service in ["mysql:", "api:"]:
        assert service in compose
    assert "admin:" not in compose
    assert "backend/Dockerfile" in compose
    assert "FRONTEND_DIST_DIR" in compose
    assert "healthcheck:" in compose
    assert "depends_on:" in compose
    assert "VITE_API_BASE_URL" in compose
    assert "8000:8000" in compose


def test_backend_container_builds_and_serves_admin_console():
    dockerfile = read_repo_file("backend/Dockerfile")

    assert "FROM node:20-alpine AS frontend-build" in dockerfile
    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert "FRONTEND_DIST_DIR=/app/frontend_dist" in dockerfile
    assert "COPY --from=frontend-build /app/dist /app/frontend_dist" in dockerfile


def test_env_example_contains_deployment_runtime_keys():
    env_example = read_repo_file(".env.example")

    for key in [
        "PUBLIC_API_BASE_URL",
        "PUBLIC_ADMIN_BASE_URL",
        "DATABASE_BACKEND",
        "MYSQL_HOST",
        "ARTIFACT_STORAGE_PROVIDER",
        "ALIYUN_OSS_BUCKET",
        "LANE_RUNTIME_BACKEND",
        "KUBERNETES_APPLY_ENABLED",
        "LOCUST_METRICS_BACKEND",
        "DEMO_TOKEN",
    ]:
        assert f"{key}=" in env_example


def test_helm_package_defaults_to_integrated_admin_with_optional_split_admin():
    values = read_repo_file("deploy/helm/locusthub/values.yaml")
    api_deployment = read_repo_file("deploy/helm/locusthub/templates/deployment.yaml")
    admin_deployment = read_repo_file("deploy/helm/locusthub/templates/admin-deployment.yaml")
    admin_service = read_repo_file("deploy/helm/locusthub/templates/admin-service.yaml")
    ingress = read_repo_file("deploy/helm/locusthub/templates/ingress.yaml")

    assert "api:" in values
    assert "admin:" in values
    assert "enabled: false" in values
    assert "repository: locusthub-api" in values
    assert "FRONTEND_DIST_DIR: /app/frontend_dist" in values
    assert "readinessProbe:" in api_deployment
    assert "livenessProbe:" in api_deployment
    assert "{{- if .Values.admin.enabled }}" in admin_deployment
    assert "locusthub-admin" in admin_deployment
    assert "containerPort: 80" in admin_deployment
    assert "{{- if .Values.admin.enabled }}" in admin_service
    assert "targetPort: 80" in admin_service
    assert "name: locusthub-api" in ingress
    assert ".Values.admin.enabled" in ingress


def test_deployment_verifier_reports_ready_package():
    result = subprocess.run(
        [sys.executable, "scripts/verify_deployment_package.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "LocustHub deployment package ready" in result.stdout
    assert "docker-compose.yml" in result.stdout
    assert "deploy/helm/locusthub" in result.stdout


def test_local_scripts_cover_admin_and_deployment_checks():
    run_local = read_repo_file("scripts/run_local.sh")
    test_local = read_repo_file("scripts/test_local.sh")

    assert "npm run build" in run_local
    assert "uvicorn app.main:app" in run_local
    assert "FRONTEND_DIST_DIR" in run_local
    assert "http://127.0.0.1:8000/" in run_local
    assert "frontend/tests/structure.test.mjs" in test_local
    assert "npm run build" in test_local
    assert "scripts/verify_deployment_package.py" in test_local
