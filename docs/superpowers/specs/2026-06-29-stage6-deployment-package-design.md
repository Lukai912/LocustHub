# Stage6 Deployment Package Design

## Goal

Stage6 turns the MVP from a locally runnable API/frontend pair into a deployable package that can be checked before use. The delivery must preserve the current MySQL, Aliyun OSS, Kubernetes Locust runtime, and Vben-style admin console choices while keeping local debugging simple.

## Recommended Approach

Use the existing Docker Compose and Helm chart as the source of truth, then add missing deployment surfaces around them:

- A frontend container image that serves the built Vue admin console.
- A Docker Compose stack containing MySQL, API, and admin UI with health checks.
- Helm values/templates for API and admin UI plus explicit runtime configuration.
- A deployment verification script that checks required files, environment keys, compose services, Helm values, and runnable local scripts without requiring Docker or Helm to be installed.
- Documentation and acceptance evidence for repeatable local and production-like deployment.

This is smaller and safer than introducing a new deployment framework, and it keeps Stage6 aligned with the current repository structure.

## Components

- `scripts/verify_deployment_package.py` validates deployment package completeness.
- `backend/tests/test_stage6_deployment_package.py` locks the deployment package contract.
- `frontend/Dockerfile` and `frontend/nginx.conf` package the admin console.
- `docker-compose.yml` runs MySQL, API, and admin UI together.
- `deploy/helm/locusthub/*` exposes API/admin image and runtime values.
- `docs/stage6-deployment-package.md` and the acceptance report record commands, evidence, and limits.

## Acceptance

Stage6 is accepted when automated tests prove the deployment package contract, the frontend build still passes, the backend test suite still passes, and PR content is merged to `main`.

