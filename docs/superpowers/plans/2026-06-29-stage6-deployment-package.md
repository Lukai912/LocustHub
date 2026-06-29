# Stage6 Deployment Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a deployable LocustHub package for local debug and production-like rollout.

**Architecture:** Extend existing Docker Compose and Helm assets instead of adding a parallel deployment stack. Add a Python verification script with focused tests so deployment completeness can be checked without Docker or Helm installed.

**Tech Stack:** Python pytest, Docker Compose YAML, Helm chart templates, Vue/Vite static frontend, Nginx.

---

### Task 1: Deployment Contract Test

**Files:**
- Create: `backend/tests/test_stage6_deployment_package.py`
- Create: `scripts/verify_deployment_package.py`

- [ ] **Step 1: Write failing pytest coverage**

Create tests that assert:

- `docker-compose.yml` has `mysql`, `api`, and `admin` services.
- API/admin services expose health checks or dependency checks.
- `.env.example` contains MySQL, OSS, Kubernetes runtime, API/admin public URL, and demo token keys.
- Helm values include API and admin image blocks.
- `scripts/verify_deployment_package.py` reports success.

- [ ] **Step 2: Run targeted test and verify RED**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage6_deployment_package.py -q`

Expected before implementation: FAIL because the admin deployment assets are missing.

- [ ] **Step 3: Implement the verifier**

Add a small standard-library script that loads deployment text with conservative checks and prints a deployment readiness summary. Keep it free of PyYAML so it runs in the existing backend environment.

- [ ] **Step 4: Run targeted test and verify GREEN**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage6_deployment_package.py -q`

Expected after implementation: PASS.

### Task 2: Compose and Frontend Container

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `frontend/README.md`

- [ ] **Step 1: Add frontend container files**

Use a multi-stage Node build followed by Nginx static serving. Configure `/api/` to proxy to the API container so the admin console works in compose.

- [ ] **Step 2: Extend compose**

Add the `admin` service, health checks, env-file support, explicit API CORS/admin URL values, and named volumes. Preserve MySQL and API defaults.

- [ ] **Step 3: Update env docs**

Add environment keys required by compose, Helm, OSS, Kubernetes runtime, and admin UI base URL.

- [ ] **Step 4: Run deployment package test**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage6_deployment_package.py -q`

Expected: PASS.

### Task 3: Helm Deployment Package

**Files:**
- Modify: `deploy/helm/locusthub/values.yaml`
- Modify: `deploy/helm/locusthub/templates/deployment.yaml`
- Create: `deploy/helm/locusthub/templates/admin-deployment.yaml`
- Create: `deploy/helm/locusthub/templates/admin-service.yaml`
- Modify: `deploy/helm/locusthub/Chart.yaml`

- [ ] **Step 1: Split API/admin image values**

Keep API image settings under `api.image` and add `admin.image`.

- [ ] **Step 2: Add admin workload templates**

Create a Deployment and Service for the admin console. Keep labels stable and simple.

- [ ] **Step 3: Add health probes and env comments**

Add API readiness/liveness probes and document values requiring secret management in production.

- [ ] **Step 4: Run verifier**

Run: `python3 scripts/verify_deployment_package.py`

Expected: exit 0 with a readiness summary.

### Task 4: Documentation and Acceptance Evidence

**Files:**
- Create: `docs/stage6-deployment-package.md`
- Modify: `README.md`
- Modify: `docs/reports/acceptance-test-report.md`

- [ ] **Step 1: Write Stage6 docs**

Document local compose usage, production Helm values, OSS configuration, and known limits.

- [ ] **Step 2: Update acceptance report**

Record Stage6 scope and verification commands.

- [ ] **Step 3: Run full verification**

Run:

```bash
node frontend/tests/structure.test.mjs
cd frontend && npm run build
cd backend && DATABASE_PATH=/private/tmp/locusthub-stage6.db ARTIFACT_ROOT=/private/tmp/locusthub-stage6-artifacts PYTHONPATH=. ../.venv/bin/pytest -q
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py
python3 scripts/verify_deployment_package.py
git diff --check
```

Expected: all commands exit 0.

