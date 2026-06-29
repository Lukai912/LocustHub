# Stage10 E2E Acceptance and Runbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable end-to-end acceptance script and final deployment/use runbook.

**Architecture:** Reuse FastAPI TestClient for deterministic local behavior and call the existing deployment package verifier for artifact checks.

**Tech Stack:** Python standard library, FastAPI TestClient, pytest, existing LocustHub API.

---

### Task 1: Acceptance Contract Test

**Files:**
- Create: `backend/tests/test_stage10_e2e_acceptance.py`

- [ ] **Step 1: Write failing tests**

Assert the acceptance script exists, emits required JSON sections, and exits 0.

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage10_e2e_acceptance.py -q`

Expected: FAIL because the script and runbook are missing.

### Task 2: Acceptance Script

**Files:**
- Create: `scripts/run_acceptance_smoke.py`

- [ ] **Step 1: Implement deterministic workflow**

Use TestClient to run health, auth, load test lifecycle, report archive, CI baseline, and result lookup.

- [ ] **Step 2: Write JSON report**

Write `docs/reports/final-acceptance-smoke.json` or a user-provided output path.

### Task 3: Final Runbook and Report

**Files:**
- Create: `docs/full-deployment-runbook.md`
- Modify: `README.md`
- Modify: `docs/reports/acceptance-test-report.md`

- [ ] **Step 1: Document local, Compose, Helm, OSS, and CI paths**

Provide exact commands and known limits.

- [ ] **Step 2: Run full verification**

Run target tests, full backend tests, frontend build, acceptance script, deployment verifier, compileall, and diff check.

