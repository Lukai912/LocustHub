# Stage8 Auth and Tenant Scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make API authentication repository-backed and tenant-aware.

**Architecture:** Keep FastAPI dependencies local to `routes.py`, add small password helpers in `security.py`, and extend repository user lookups. Avoid adding a full user management surface in this stage.

**Tech Stack:** FastAPI dependencies, SQLite/MySQL schema, pytest TestClient.

---

### Task 1: Auth Contract Tests

**Files:**
- Create: `backend/tests/test_stage8_auth_tenant_scope.py`

- [ ] **Step 1: Write failing tests**

Assert invalid bearer tokens fail, bad login password fails, `/me` returns stored user context, non-admin users only see their tenant, and cross-tenant create returns `403`.

- [ ] **Step 2: Verify RED**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_stage8_auth_tenant_scope.py -q`

Expected: FAIL because tokens are not repository-validated and tenant scoping is not enforced.

### Task 2: Repository and Security Helpers

**Files:**
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/repositories/sqlite_repo.py`
- Modify: `backend/app/db/mysql_schema.sql`

- [ ] **Step 1: Add password hashing helpers**

Use standard-library hashing and isolate the helper for later replacement.

- [ ] **Step 2: Add user lookup methods**

Implement `get_user_by_token` and `get_user_by_username`.

- [ ] **Step 3: Seed demo admin and viewer users**

Keep `admin/admin` working and add a tenant viewer for scoping tests.

### Task 3: FastAPI Tenant Scope

**Files:**
- Modify: `backend/app/api/routes.py`

- [ ] **Step 1: Add `current_user` dependency**

Resolve bearer token to a user record or return `401`.

- [ ] **Step 2: Scope list endpoints**

Admin sees all rows; non-admin users only see rows matching their tenant.

- [ ] **Step 3: Guard create/update endpoints**

Non-admin users cannot create or update resources for another tenant.

### Task 4: Docs and Verification

**Files:**
- Create: `docs/stage8-auth-tenant-scope.md`
- Modify: `README.md`
- Modify: `docs/reports/acceptance-test-report.md`

- [ ] **Step 1: Document auth behavior**

Describe demo credentials, token validation, tenant scoping, and known limits.

- [ ] **Step 2: Run full verification**

Run backend tests, frontend build, compileall, deployment verifier, and diff check.

