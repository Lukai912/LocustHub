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
for (const api of ['listTestRuns', 'startRun', 'collectRun', 'stopRun', 'getLocustStats', 'listApprovalRequests', 'listDnsSnapshots', 'listQuotaUsageSnapshots', 'validateLocustfile', 'createScriptVersion', 'createTestPlan', 'cloneTestPlan', 'getRunDiagnostics', 'rerunTestRun', 'listUsers', 'createUser', 'listApiTokens', 'createApiToken', 'revokeApiToken', 'listReports', 'compareReports', 'listBaselineProfiles', 'createBaselineProfile']) {
  assert.match(client, new RegExp(`export async function ${api}`), `${api} must be exported`);
}

const types = readFileSync(join(root, 'src/types.ts'), 'utf8');
assert.match(types, /export interface LocustStatsResponse/);
assert.match(types, /export interface TestRun/);
assert.match(types, /export interface ApprovalRequest/);
assert.match(types, /export interface DnsResolutionSnapshot/);
assert.match(types, /export interface QuotaUsageSnapshot/);

const app = readFileSync(join(root, 'src/App.vue'), 'utf8');
for (const label of ['仪表盘', '租户', '访问控制', '项目', '脚本', '压测计划', '压测任务', '治理', '报告', 'CI 基线']) {
  assert.match(app, new RegExp(label), `${label} navigation label must exist`);
}
for (const label of ['审批请求', '准入快照']) {
  assert.match(app, new RegExp(label), `${label} governance label must exist`);
}
for (const tab of ['统计', '图表', '失败', 'Worker', '日志', '下载数据']) {
  assert.match(app, new RegExp(tab), `${tab} Locust tab must exist`);
}
for (const label of ['RPS', '失败/秒', '响应时间', '用户数', 'Master 日志', 'HTML 报告', '请求 CSV', '失败 CSV', '异常 CSV', '历史 CSV']) {
  assert.match(app, new RegExp(label), `${label} Locust WebUI detail label must exist`);
}
for (const label of ['校验 Locustfile', '创建脚本版本', '创建压测计划', '复制计划']) {
  assert.match(app, new RegExp(label), `${label} script and plan management label must exist`);
}
for (const label of ['诊断', '重跑', '建议', '生命周期事件']) {
  assert.match(app, new RegExp(label), `${label} run diagnostics label must exist`);
}
for (const label of ['访问控制', '创建用户', '创建 API Token', '撤销 Token']) {
  assert.match(app, new RegExp(label), `${label} access management label must exist`);
}
for (const label of ['报告历史', '报告对比', 'P95 变化', '失败率变化']) {
  assert.match(app, new RegExp(label), `${label} report comparison label must exist`);
}
for (const label of ['基线 Profile', '创建基线 Profile', '最大 P95', '最小 RPS']) {
  assert.match(app, new RegExp(label), `${label} CI baseline label must exist`);
}
