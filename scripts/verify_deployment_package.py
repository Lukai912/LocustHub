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
            "backend/Dockerfile",
            "FRONTEND_DIST_DIR",
            "healthcheck:",
            "depends_on:",
            "VITE_API_BASE_URL",
            "8000:8000",
        ],
    )


def verify_integrated_container() -> None:
    require_contains(
        "backend/Dockerfile",
        [
            "FROM node:20-alpine AS frontend-build",
            "npm ci",
            "npm run build",
            "FRONTEND_DIST_DIR=/app/frontend_dist",
            "COPY --from=frontend-build /app/dist /app/frontend_dist",
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
            "ingress:",
            "secret:",
            "repository: locusthub-api",
            "enabled: false",
            "FRONTEND_DIST_DIR: /app/frontend_dist",
            "ALIYUN_OSS_BUCKET",
            "LOCUST_METRICS_BACKEND",
        ],
    )
    require_contains(
        "deploy/helm/locusthub/templates/deployment.yaml",
        ["readinessProbe:", "livenessProbe:", ".Values.api.image.repository", "secretKeyRef:"],
    )
    require_contains(
        "deploy/helm/locusthub/templates/admin-deployment.yaml",
        ["{{- if .Values.admin.enabled }}", "locusthub-admin", "containerPort: 80", ".Values.admin.image.repository"],
    )
    require_contains(
        "deploy/helm/locusthub/templates/admin-service.yaml",
        ["{{- if .Values.admin.enabled }}", "targetPort: 80", "locusthub-admin"],
    )
    require_contains("deploy/helm/locusthub/templates/secret.yaml", ["kind: Secret", "stringData:", "DEMO_TOKEN:"])
    require_contains(
        "deploy/helm/locusthub/templates/ingress.yaml",
        ["kind: Ingress", "locusthub-api", "locusthub-admin", ".Values.admin.enabled", "secretName:"],
    )


def main() -> int:
    checks = [
        verify_compose,
        verify_integrated_container,
        verify_env_example,
        verify_helm,
    ]
    for check in checks:
        check()

    print("LocustHub deployment package ready")
    print("- docker-compose.yml includes mysql and one api service that serves the admin console")
    print("- backend/Dockerfile builds the Vue admin console and copies it into the FastAPI image")
    print("- deploy/helm/locusthub defaults to integrated admin serving with optional split admin workloads")
    print("- deploy/helm/locusthub includes ingress, TLS, and Secret-backed settings")
    print("- .env.example documents required local, OSS, and Kubernetes runtime keys")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeploymentPackageError as exc:
        print(f"deployment package check failed: {exc}")
        raise SystemExit(1)
