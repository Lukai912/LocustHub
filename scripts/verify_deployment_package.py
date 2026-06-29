#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DeploymentPackageError(RuntimeError):
    pass


def read(path: str) -> str:
    file_path = REPO_ROOT / path
    if not file_path.exists():
        raise DeploymentPackageError(f"missing required file: {path}")
    return file_path.read_text(encoding="utf-8")


def require_contains(path: str, required: list[str]) -> None:
    content = read(path)
    missing = [item for item in required if item not in content]
    if missing:
        joined = ", ".join(missing)
        raise DeploymentPackageError(f"{path} missing required content: {joined}")


def verify_compose() -> None:
    require_contains(
        "docker-compose.yml",
        [
            "mysql:",
            "api:",
            "admin:",
            "frontend/Dockerfile",
            "healthcheck:",
            "depends_on:",
            "VITE_API_BASE_URL",
            "8000:8000",
            "8080:80",
        ],
    )


def verify_frontend_container() -> None:
    require_contains("frontend/Dockerfile", ["npm ci", "npm run build", "nginx"])
    require_contains(
        "frontend/nginx.conf",
        [
            "try_files $uri $uri/ /index.html",
            "proxy_pass http://api:8000",
            "location /api/",
        ],
    )


def verify_env_example() -> None:
    require_contains(
        ".env.example",
        [
            "PUBLIC_API_BASE_URL=",
            "PUBLIC_ADMIN_BASE_URL=",
            "DATABASE_BACKEND=",
            "MYSQL_HOST=",
            "ARTIFACT_STORAGE_PROVIDER=",
            "ALIYUN_OSS_BUCKET=",
            "LANE_RUNTIME_BACKEND=",
            "KUBERNETES_APPLY_ENABLED=",
            "LOCUST_METRICS_BACKEND=",
            "DEMO_TOKEN=",
        ],
    )


def verify_helm() -> None:
    require_contains(
        "deploy/helm/locusthub/values.yaml",
        [
            "api:",
            "admin:",
            "repository: locusthub-api",
            "repository: locusthub-admin",
            "ALIYUN_OSS_BUCKET",
            "LOCUST_METRICS_BACKEND",
        ],
    )
    require_contains(
        "deploy/helm/locusthub/templates/deployment.yaml",
        ["readinessProbe:", "livenessProbe:", ".Values.api.image.repository"],
    )
    require_contains(
        "deploy/helm/locusthub/templates/admin-deployment.yaml",
        ["locusthub-admin", "containerPort: 80", ".Values.admin.image.repository"],
    )
    require_contains("deploy/helm/locusthub/templates/admin-service.yaml", ["targetPort: 80", "locusthub-admin"])


def main() -> int:
    checks = [
        verify_compose,
        verify_frontend_container,
        verify_env_example,
        verify_helm,
    ]
    for check in checks:
        check()

    print("LocustHub deployment package ready")
    print("- docker-compose.yml includes mysql, api, and admin services")
    print("- frontend/Dockerfile builds and serves the Vben-style admin console")
    print("- deploy/helm/locusthub includes API and admin workloads")
    print("- .env.example documents required local, OSS, and Kubernetes runtime keys")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeploymentPackageError as exc:
        print(f"deployment package check failed: {exc}")
        raise SystemExit(1)

