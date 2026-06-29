# Stage 4 Vben Admin Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the one-file debug UI with a Vben-style Vue 3 admin console that can operate the LocustHub MVP lifecycle.

**Architecture:** Build a focused Vue 3 + Vite + TypeScript app under `frontend/` with a Vben-inspired shell, route-like module switching, API client, and Locust UI compatible run detail page. Keep dependencies small so the MVP can install and build without pulling the full upstream Vben monorepo into this repository.

**Tech Stack:** Vue 3, Vite, TypeScript, native Fetch API, FastAPI `/api/v1`, Swagger/OpenAPI already exposed by the backend.

---

### Task 1: Frontend Project Scaffold

**Files:**
- Replace: `frontend/index.html`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/styles.css`
- Create: `frontend/README.md`

- [ ] **Step 1: Write the failing structure check**

Create `frontend/tests/structure.test.mjs` that reads project files and asserts:

```js
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import assert from 'node:assert/strict';

const root = new URL('..', import.meta.url).pathname;
const required = ['package.json', 'index.html', 'src/main.ts', 'src/App.vue', 'src/styles.css'];
for (const file of required) assert.equal(existsSync(join(root, file)), true, `${file} must exist`);
const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
assert.equal(pkg.scripts.dev, 'vite --host 127.0.0.1');
assert.equal(pkg.scripts.build, 'vue-tsc --noEmit && vite build');
```

- [ ] **Step 2: Verify RED**

Run: `node frontend/tests/structure.test.mjs`
Expected: FAIL because `frontend/package.json` and `frontend/src/*` do not exist.

- [ ] **Step 3: Implement scaffold**

Create the Vue/Vite files listed above. `index.html` should load `/src/main.ts`; `package.json` should expose `dev`, `build`, and `test:structure` scripts.

- [ ] **Step 4: Verify GREEN**

Run: `node frontend/tests/structure.test.mjs`
Expected: PASS.

### Task 2: API Client And Admin Data Model

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/types.ts`
- Update: `frontend/tests/structure.test.mjs`

- [ ] **Step 1: Extend the failing structure check**

Assert that `src/api/client.ts` exports `listTestRuns`, `startRun`, `collectRun`, `stopRun`, and that `src/types.ts` contains `LocustStatsResponse`.

- [ ] **Step 2: Verify RED**

Run: `node frontend/tests/structure.test.mjs`
Expected: FAIL until files and exports exist.

- [ ] **Step 3: Implement API client**

Use `VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'` and `VITE_DEMO_TOKEN || 'dev-token'`. Add a short comment explaining the MVP token fallback.

- [ ] **Step 4: Verify GREEN**

Run: `node frontend/tests/structure.test.mjs`
Expected: PASS.

### Task 3: Vben-Style Admin Views

**Files:**
- Update: `frontend/src/App.vue`
- Update: `frontend/src/styles.css`
- Update: `frontend/tests/structure.test.mjs`

- [ ] **Step 1: Extend the failing structure check**

Assert `App.vue` contains labels for Dashboard, Tenants, Projects, Scripts, Test Plans, Test Runs, Governance, Reports, and a Locust tabs list containing Statistics, Failures, Workers, Download.

- [ ] **Step 2: Verify RED**

Run: `node frontend/tests/structure.test.mjs`
Expected: FAIL until the view contains required labels.

- [ ] **Step 3: Implement views**

Implement a Vben-style shell: dark sidebar, top header, dense table surfaces, status tags, toolbar buttons with icon text, realtime run detail area compatible with Locust UI fields.

- [ ] **Step 4: Verify GREEN**

Run: `node frontend/tests/structure.test.mjs`
Expected: PASS.

### Task 4: Documentation And Acceptance

**Files:**
- Update: `README.md`
- Update: `docs/reports/acceptance-test-report.md`
- Create: `docs/stage4-vben-admin-console.md`

- [ ] **Step 1: Document local usage**

Add commands for `cd frontend && npm install && npm run dev`, and note that package installation requires network access.

- [ ] **Step 2: Update acceptance evidence**

Record frontend structure test, backend pytest, compileall, and whether npm build was executed.

- [ ] **Step 3: Final verification**

Run:

```bash
node frontend/tests/structure.test.mjs
cd backend && rm -rf data artifacts && PYTHONPATH=. ../.venv/bin/pytest -q
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py
git diff --check
```

Expected: all pass. If `npm install` cannot run because network is restricted, document it as not executed.
