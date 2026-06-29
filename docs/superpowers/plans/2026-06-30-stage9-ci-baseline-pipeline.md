# Stage9 CI Baseline Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CI-friendly baseline execution, threshold evaluation, result query, and CLI exit codes.

**Architecture:** Keep the existing CI baseline API as the single entrypoint. Add threshold fields, a persisted result lookup, and a small standard-library client script.

**Tech Stack:** FastAPI, pytest TestClient, Python urllib CLI.

---

### Task 1: CI Baseline Contract Tests

**Files:**
- Create: `backend/tests/test_stage9_ci_baseline_pipeline.py`

- [ ] **Step 1: Write failing tests**

Test strict threshold failure, result endpoint lookup, tenant scoping, CLI success, and CLI failure exit code.

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage9_ci_baseline_pipeline.py -q`

Expected: FAIL because threshold fields, result endpoint, and CLI script are missing.

### Task 2: API Implementation

**Files:**
- Modify: `backend/app/models/schemas.py`
- Modify: `backend/app/api/routes.py`
- Modify: `backend/app/repositories/sqlite_repo.py`

- [ ] **Step 1: Add threshold fields**

Add `max_p95_ms`, `max_fail_ratio`, and optional `min_total_rps`.

- [ ] **Step 2: Evaluate thresholds**

Compare latest Locust snapshot values and persist violations.

- [ ] **Step 3: Add result endpoint**

Return baseline run plus violations for a test run id.

### Task 3: CLI Script and Docs

**Files:**
- Create: `scripts/run_ci_baseline.py`
- Create: `docs/stage9-ci-baseline-pipeline.md`
- Modify: `README.md`
- Modify: `docs/reports/acceptance-test-report.md`

- [ ] **Step 1: Add CLI**

Use environment variables and arguments, write JSON output, exit non-zero on failed baseline.

- [ ] **Step 2: Document usage**

Show local and CI examples.

- [ ] **Step 3: Run full verification**

Run target tests, full backend tests, frontend build, compileall, deployment verifier, and diff check.

