# Stage7 Ingress and Secrets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production-ready Helm ingress, TLS, and Secret-backed sensitive settings.

**Architecture:** Keep Docker Compose unchanged and enhance only the Helm production entrypoint. Route browser traffic through one Ingress and feed sensitive API settings through Kubernetes Secret references.

**Tech Stack:** Helm templates, Kubernetes Ingress v1, Kubernetes Secret, pytest text contract tests.

---

### Task 1: Helm Production Entrypoint Test

**Files:**
- Create: `backend/tests/test_stage7_ingress_secrets.py`

- [ ] **Step 1: Write failing tests**

Assert that values and templates include ingress, TLS, Secret settings, and `secretKeyRef` environment variables.

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage7_ingress_secrets.py -q`

Expected: FAIL because ingress and secret templates do not exist yet.

### Task 2: Helm Templates

**Files:**
- Modify: `deploy/helm/locusthub/values.yaml`
- Modify: `deploy/helm/locusthub/templates/deployment.yaml`
- Create: `deploy/helm/locusthub/templates/secret.yaml`
- Create: `deploy/helm/locusthub/templates/ingress.yaml`

- [ ] **Step 1: Add values**

Add `secret` and `ingress` sections with demo-safe defaults and production override hooks.

- [ ] **Step 2: Wire Deployment to Secret**

Use `secretKeyRef` for MySQL password, OSS keys, and demo token. Keep non-sensitive env values in the existing `env` loop.

- [ ] **Step 3: Add Ingress**

Route `/api` to `locusthub-api` and `/` to `locusthub-admin`. Include optional TLS.

- [ ] **Step 4: Verify GREEN**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage7_ingress_secrets.py -q`

Expected: PASS.

### Task 3: Verification and Docs

**Files:**
- Modify: `scripts/verify_deployment_package.py`
- Create: `docs/stage7-ingress-secrets.md`
- Modify: `README.md`
- Modify: `docs/reports/acceptance-test-report.md`

- [ ] **Step 1: Extend verifier**

Check ingress and secret templates.

- [ ] **Step 2: Document production values**

Explain TLS, host routing, and existing Secret usage.

- [ ] **Step 3: Run full verification**

Run backend tests, frontend build, deployment verifier, compileall, and diff check.

