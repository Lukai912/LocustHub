import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const root = fileURLToPath(new URL('..', import.meta.url));

for (const file of [
  'package.json',
  'index.html',
  'src/main.ts',
  'src/App.vue',
  'src/styles.css',
  'src/api/client.ts',
  'src/types.ts',
]) {
  assert.equal(existsSync(join(root, file)), true, `${file} must exist`);
}

const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
assert.equal(pkg.scripts.dev, 'vite --host 127.0.0.1');
assert.equal(pkg.scripts.build, 'vue-tsc --noEmit --pretty false && node scripts/build.mjs');

const client = readFileSync(join(root, 'src/api/client.ts'), 'utf8');
for (const api of ['listTestRuns', 'startRun', 'collectRun', 'stopRun', 'getLocustStats', 'listApprovalRequests', 'listDnsSnapshots', 'listQuotaUsageSnapshots']) {
  assert.match(client, new RegExp(`export async function ${api}`), `${api} must be exported`);
}

const types = readFileSync(join(root, 'src/types.ts'), 'utf8');
assert.match(types, /export interface LocustStatsResponse/);
assert.match(types, /export interface TestRun/);
assert.match(types, /export interface ApprovalRequest/);
assert.match(types, /export interface DnsResolutionSnapshot/);
assert.match(types, /export interface QuotaUsageSnapshot/);

const app = readFileSync(join(root, 'src/App.vue'), 'utf8');
for (const label of ['Dashboard', 'Tenants', 'Projects', 'Scripts', 'Test Plans', 'Test Runs', 'Governance', 'Reports']) {
  assert.match(app, new RegExp(label), `${label} navigation label must exist`);
}
for (const label of ['Approval Requests', 'Admission Snapshots']) {
  assert.match(app, new RegExp(label), `${label} governance label must exist`);
}
for (const tab of ['Statistics', 'Failures', 'Workers', 'Download']) {
  assert.match(app, new RegExp(tab), `${tab} Locust tab must exist`);
}
