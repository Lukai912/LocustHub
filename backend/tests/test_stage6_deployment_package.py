import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read_repo_file(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_compose_package_runs_api_admin_and_mysql():
    compose = read_repo_file("docker-compose.yml")

    for service in ["mysql:", "api:", "admin:"]:
        assert service in compose
    assert "frontend/Dockerfile" in compose
    assert "healthcheck:" in compose
    assert "depends_on:" in compose
    assert "VITE_API_BASE_URL" in compose
    assert "8000:8000" in compose
    assert "8080:80" in compose


def test_frontend_container_serves_admin_and_proxies_api():
    dockerfile = read_repo_file("frontend/Dockerfile")
    nginx = read_repo_file("frontend/nginx.conf")

    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert "nginx" in dockerfile
    assert "try_files $uri $uri/ /index.html" in nginx
    assert "proxy_pass http://api:8000" in nginx


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


def test_helm_package_contains_api_and_admin_workloads():
    values = read_repo_file("deploy/helm/locusthub/values.yaml")
    api_deployment = read_repo_file("deploy/helm/locusthub/templates/deployment.yaml")
    admin_deployment = read_repo_file("deploy/helm/locusthub/templates/admin-deployment.yaml")
    admin_service = read_repo_file("deploy/helm/locusthub/templates/admin-service.yaml")

    assert "api:" in values
    assert "admin:" in values
    assert "repository: locusthub-api" in values
    assert "repository: locusthub-admin" in values
    assert "readinessProbe:" in api_deployment
    assert "livenessProbe:" in api_deployment
    assert "locusthub-admin" in admin_deployment
    assert "containerPort: 80" in admin_deployment
    assert "targetPort: 80" in admin_service


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

    assert "npm run dev" in run_local
    assert "uvicorn app.main:app" in run_local
    assert "trap" in run_local
    assert "frontend/tests/structure.test.mjs" in test_local
    assert "npm run build" in test_local
    assert "scripts/verify_deployment_package.py" in test_local
