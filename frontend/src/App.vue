<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  collectRun,
  compareReports,
  createBaselineProfile,
  createRunFromPlan,
  createScriptVersion,
  createTestPlan,
  cloneTestPlan,
  createApiToken,
  getRunDiagnostics,
  getLocustStats,
  getReport,
  createUser,
  listReports,
  listApprovalRequests,
  listApiTokens,
  listBaselineProfiles,
  listDnsSnapshots,
  listProjects,
  listQuotas,
  listQuotaUsageSnapshots,
  listScripts,
  listTargets,
  listTenants,
  listTestPlans,
  listTestRuns,
  listUsers,
  revokeApiToken,
  startRun,
  stopRun,
  rerunTestRun,
  validateLocustfile,
} from './api/client';
import type {
  ApprovalRequest,
  ApiToken,
  BaselineProfile,
  DnsResolutionSnapshot,
  LocustStatsResponse,
  Project,
  QuotaUsageSnapshot,
  ReportCollection,
  ReportComparison,
  ReportSummary,
  RunDiagnostics,
  ScriptValidationResult,
  ScriptVersion,
  TargetWhitelist,
  Tenant,
  TenantQuota,
  TestPlan,
  TestRun,
  UserAccount,
} from './types';

type ViewKey = 'dashboard' | 'tenants' | 'access' | 'projects' | 'scripts' | 'plans' | 'runs' | 'governance' | 'reports' | 'ci';
type LocustTab = '统计' | '图表' | '失败' | 'Worker' | '日志' | '诊断' | '下载数据';

const navigation: Array<{ key: ViewKey; label: string; cn: string }> = [
  { key: 'dashboard', label: '仪表盘', cn: '总览' },
  { key: 'tenants', label: '租户', cn: '隔离域' },
  { key: 'access', label: '访问控制', cn: '用户与 Token' },
  { key: 'projects', label: '项目', cn: '业务域' },
  { key: 'scripts', label: '脚本', cn: 'Locustfile' },
  { key: 'plans', label: '压测计划', cn: '模板' },
  { key: 'runs', label: '压测任务', cn: '实时数据' },
  { key: 'governance', label: '治理', cn: '白名单与配额' },
  { key: 'reports', label: '报告', cn: '归档与对比' },
  { key: 'ci', label: 'CI 基线', cn: '性能门禁' },
];
const locustTabs: LocustTab[] = ['统计', '图表', '失败', 'Worker', '日志', '诊断', '下载数据'];
const expectedReportArtifacts = ['HTML 报告', '请求 CSV', '失败 CSV', '异常 CSV', '历史 CSV', 'Master 日志'];
const artifactNameMap: Record<string, string> = {
  'HTML Report': 'HTML 报告',
  'Requests CSV': '请求 CSV',
  'Failures CSV': '失败 CSV',
  'Exceptions CSV': '异常 CSV',
  'History CSV': '历史 CSV',
  'Master Log': 'Master 日志',
};

const activeView = ref<ViewKey>('dashboard');
const activeTab = ref<LocustTab>('统计');
const selectedRunId = ref('');
const loading = ref(false);
const error = ref('');

const tenants = ref<Tenant[]>([]);
const users = ref<UserAccount[]>([]);
const apiTokens = ref<ApiToken[]>([]);
const baselineProfiles = ref<BaselineProfile[]>([]);
const projects = ref<Project[]>([]);
const scripts = ref<ScriptVersion[]>([]);
const plans = ref<TestPlan[]>([]);
const runs = ref<TestRun[]>([]);
const targets = ref<TargetWhitelist[]>([]);
const quotas = ref<TenantQuota[]>([]);
const approvals = ref<ApprovalRequest[]>([]);
const dnsSnapshots = ref<DnsResolutionSnapshot[]>([]);
const quotaUsageSnapshots = ref<QuotaUsageSnapshot[]>([]);
const stats = ref<LocustStatsResponse | null>(null);
const report = ref<ReportSummary | null>(null);
const reportArchive = ref<ReportCollection>({ items: [], trend: [] });
const reportComparison = ref<ReportComparison | null>(null);
const diagnostics = ref<RunDiagnostics | null>(null);
const validation = ref<ScriptValidationResult | null>(null);
const defaultLocustfile = "from locust import HttpUser, task\n\nclass DemoUser(HttpUser):\n    @task\n    def index(self):\n        self.client.get('/todos/1')\n";
const scriptForm = ref({
  tenant_id: 'tenant-demo',
  project_id: 'project-demo',
  name: '新建 Locust 脚本',
  locustfile: defaultLocustfile,
  requirements: '',
});
const planForm = ref({
  tenant_id: 'tenant-demo',
  project_id: 'project-demo',
  script_version_id: 'script-demo',
  name: '新建压测计划',
  target_host: 'https://jsonplaceholder.typicode.com',
  users: 5,
  spawn_rate: 1,
  run_time_seconds: 60,
  worker_count: 1,
});
const userForm = ref({ tenant_id: 'tenant-demo', username: '性能用户', password: 'secret', role: 'project_member' });
const apiTokenForm = ref({ name: 'CI Token', scopes: 'ci:run,reports:read' });
const baselineProfileForm = ref({
  tenant_id: 'tenant-demo',
  project_id: 'project-demo',
  name: '主干分支基线',
  max_p95_ms: 500,
  max_fail_ratio: 0.05,
  min_total_rps: 1,
});
const createdTokenSecret = ref('');

const activeRun = computed(() => runs.value.find((run) => run.id === selectedRunId.value) ?? runs.value[0]);
const runningCount = computed(() => runs.value.filter((run) => run.status === 'RUNNING').length);
const completedCount = computed(() => runs.value.filter((run) => run.status === 'COMPLETED').length);
const pendingTargets = computed(() => targets.value.filter((target) => target.status !== 'approved').length);

function statusText(status?: string) {
  const map: Record<string, string> = {
    CREATED: '已创建',
    VALIDATING: '校验中',
    APPROVAL_PENDING: '等待审批',
    LANE_CREATING: '创建泳道',
    PROVISIONING: '准备资源',
    RUNNING: '运行中',
    COLLECTING: '采集中',
    ARCHIVING: '归档中',
    DESTROYING: '销毁中',
    COMPLETED: '已完成',
    FAILED: '失败',
    CANCELED: '已取消',
    active: '启用',
    pending: '待审批',
    approved: '已批准',
    rejected: '已拒绝',
    archived: '已归档',
  };
  return status ? map[status] ?? status : '未选择';
}

function sourceText(source?: string) {
  const map: Record<string, string> = { manual: '手动', api: 'API', ci: 'CI', schedule: '定时' };
  return source ? map[source] ?? source : '-';
}

function artifactDisplayName(name: string) {
  return artifactNameMap[name] ?? name;
}

async function withLoading(task: () => Promise<void>) {
  loading.value = true;
  error.value = '';
  try {
    await task();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function refreshAll() {
  await withLoading(async () => {
    const [tenantRows, userRows, tokenRows, profileRows, projectRows, scriptRows, planRows, runRows, targetRows, quotaRows, approvalRows, dnsRows, quotaUsageRows, reportRows] = await Promise.all([
      listTenants(),
      listUsers(),
      listApiTokens(),
      listBaselineProfiles(),
      listProjects(),
      listScripts(),
      listTestPlans(),
      listTestRuns(),
      listTargets(),
      listQuotas(),
      listApprovalRequests(),
      listDnsSnapshots(),
      listQuotaUsageSnapshots(),
      listReports(),
    ]);
    tenants.value = tenantRows;
    users.value = userRows;
    apiTokens.value = tokenRows;
    baselineProfiles.value = profileRows;
    projects.value = projectRows;
    scripts.value = scriptRows;
    plans.value = planRows;
    runs.value = runRows;
    targets.value = targetRows;
    quotas.value = quotaRows;
    approvals.value = approvalRows;
    dnsSnapshots.value = dnsRows;
    quotaUsageSnapshots.value = quotaUsageRows;
    reportArchive.value = reportRows;
    await refreshReportComparison(reportRows.items);
    if (!selectedRunId.value && runRows[0]) selectedRunId.value = runRows[0].id;
    if (selectedRunId.value) await refreshRunDetail(selectedRunId.value);
  });
}

async function refreshReportComparison(items = reportArchive.value.items) {
  if (items.length < 2) {
    reportComparison.value = null;
    return;
  }
  // Compare the newest archived report against the previous one, matching the
  // common operator workflow of checking whether the latest run regressed.
  reportComparison.value = await compareReports(items[1].run_id, items[0].run_id);
}

async function refreshRunDetail(runId: string) {
  stats.value = await getLocustStats(runId);
  try {
    report.value = await getReport(runId);
  } catch {
    report.value = null;
  }
  try {
    diagnostics.value = await getRunDiagnostics(runId);
  } catch {
    diagnostics.value = null;
  }
}

async function createAndStartDemo() {
  await withLoading(async () => {
    const plan = plans.value[0] ?? (await listTestPlans())[0];
    if (!plan) throw new Error('没有可用的压测计划');
    const run = await createRunFromPlan(plan);
    const started = await startRun(run.id);
    selectedRunId.value = started.id;
    runs.value = await listTestRuns();
    await refreshRunDetail(started.id);
    activeView.value = 'runs';
  });
}

async function collectActiveRun() {
  if (!activeRun.value) return;
  await withLoading(async () => {
    await collectRun(activeRun.value.id);
    await refreshRunDetail(activeRun.value.id);
  });
}

async function stopActiveRun() {
  if (!activeRun.value) return;
  await withLoading(async () => {
    const stopped = await stopRun(activeRun.value.id);
    runs.value = await listTestRuns();
    selectedRunId.value = stopped.id;
    await refreshRunDetail(stopped.id);
    reportArchive.value = await listReports();
    await refreshReportComparison();
  });
}

async function rerunActiveRun() {
  if (!activeRun.value) return;
  await withLoading(async () => {
    const created = await rerunTestRun(activeRun.value.id);
    runs.value = await listTestRuns();
    selectedRunId.value = created.id;
    await refreshRunDetail(created.id);
  });
}

async function createUserFromForm() {
  await withLoading(async () => {
    await createUser(userForm.value);
    users.value = await listUsers();
  });
}

async function createTokenFromForm() {
  await withLoading(async () => {
    const token = await createApiToken({ name: apiTokenForm.value.name, scopes: apiTokenForm.value.scopes.split(',').map((scope) => scope.trim()).filter(Boolean) });
    createdTokenSecret.value = token.token ?? '';
    apiTokens.value = await listApiTokens();
  });
}

async function revokeToken(token: ApiToken) {
  await withLoading(async () => {
    await revokeApiToken(token.id);
    apiTokens.value = await listApiTokens();
  });
}

async function createBaselineProfileFromForm() {
  await withLoading(async () => {
    await createBaselineProfile(baselineProfileForm.value);
    baselineProfiles.value = await listBaselineProfiles();
  });
}

async function selectRun(run: TestRun) {
  selectedRunId.value = run.id;
  await withLoading(async () => refreshRunDetail(run.id));
}

async function validateScriptForm() {
  await withLoading(async () => {
    validation.value = await validateLocustfile(scriptForm.value.locustfile);
  });
}

async function createScriptFromForm() {
  await withLoading(async () => {
    const created = await createScriptVersion(scriptForm.value);
    scripts.value = await listScripts();
    planForm.value.script_version_id = created.id;
    validation.value = await validateLocustfile(created.locustfile);
  });
}

async function createPlanFromForm() {
  await withLoading(async () => {
    await createTestPlan(planForm.value);
    plans.value = await listTestPlans();
  });
}

async function cloneSelectedPlan(plan: TestPlan) {
  await withLoading(async () => {
    const cloned = await cloneTestPlan(plan.id, `${plan.name} 副本`);
    plans.value = await listTestPlans();
    planForm.value = { ...planForm.value, ...cloned, name: `${cloned.name} 变体` };
  });
}

function p95Value() {
  return stats.value?.current_response_time_percentiles?.['response_time_percentile_0.95'] ?? 0;
}

function chartValues(key: 'total_rps' | 'total_fail_per_sec' | 'p50' | 'p95' | 'user_count') {
  return (stats.value?.history ?? []).map((point) => Number(point[key] ?? 0));
}

function reportTrendValues(key: 'p95_response_time' | 'total_rps' | 'fail_ratio') {
  return reportArchive.value.trend.map((point) => Number(point[key] ?? 0));
}

function latestReportTrendValue(key: 'p95_response_time' | 'total_rps' | 'fail_ratio') {
  const last = reportArchive.value.trend[reportArchive.value.trend.length - 1];
  return last ? Number(last[key] ?? 0) : 0;
}

function sparklinePoints(values: number[], width = 320, height = 90) {
  if (!values.length) return '';
  const max = Math.max(...values, 1);
  const step = values.length > 1 ? width / (values.length - 1) : width;
  // SVG coordinates grow downward, so each value is inverted against the chart
  // height while preserving the raw Locust metric scale.
  return values
    .map((value, index) => {
      const x = Math.round(index * step);
      const y = Math.round(height - (value / max) * height);
      return `${x},${y}`;
    })
    .join(' ');
}

const chartCards = computed(() => [
  { title: 'RPS', points: sparklinePoints(chartValues('total_rps')), latest: stats.value?.total_rps ?? 0 },
  { title: '失败/秒', points: sparklinePoints(chartValues('total_fail_per_sec')), latest: stats.value?.total_fail_per_sec ?? 0 },
  { title: '响应时间', points: sparklinePoints(chartValues('p95')), latest: p95Value() },
  { title: '用户数', points: sparklinePoints(chartValues('user_count')), latest: stats.value?.user_count ?? 0 },
]);

const reportTrendCards = computed(() => [
  { title: 'P95 趋势', points: sparklinePoints(reportTrendValues('p95_response_time')), latest: latestReportTrendValue('p95_response_time') },
  { title: 'RPS 趋势', points: sparklinePoints(reportTrendValues('total_rps')), latest: latestReportTrendValue('total_rps') },
  { title: '失败率趋势', points: sparklinePoints(reportTrendValues('fail_ratio')), latest: latestReportTrendValue('fail_ratio') },
]);

onMounted(refreshAll);
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">LH</span>
        <span>LocustHub</span>
      </div>
      <nav class="nav-list" aria-label="LocustHub modules">
        <button
          v-for="item in navigation"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeView === item.key }"
          type="button"
          @click="activeView = item.key"
        >
          <span>{{ item.label }}</span>
          <small>{{ item.cn }}</small>
        </button>
      </nav>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <h1>LocustHub 管理后台</h1>
          <p>{{ activeRun ? `${statusText(activeRun.status)} · ${activeRun.id}` : '暂无活跃压测任务' }}</p>
        </div>
        <div class="topbar-actions">
          <button type="button" @click="refreshAll">刷新</button>
          <button class="primary" type="button" @click="createAndStartDemo">创建演示任务</button>
        </div>
      </header>

      <div v-if="error" class="alert">{{ error }}</div>

      <section v-if="activeView === 'dashboard'" class="content">
        <div class="metric-grid">
          <article class="metric-card">
            <span>租户</span>
            <strong>{{ tenants.length }}</strong>
          </article>
          <article class="metric-card">
            <span>运行中</span>
            <strong>{{ runningCount }}</strong>
          </article>
          <article class="metric-card">
            <span>已完成</span>
            <strong>{{ completedCount }}</strong>
          </article>
          <article class="metric-card">
            <span>待审批目标</span>
            <strong>{{ pendingTargets }}</strong>
          </article>
        </div>
        <div class="split-layout">
          <section class="surface">
            <div class="surface-title">
              <h2>实时任务</h2>
              <span class="status-tag">{{ statusText(activeRun?.status) }}</span>
            </div>
            <div class="runtime-strip">
              <div><span>用户数</span><strong>{{ stats?.user_count ?? 0 }}</strong></div>
              <div><span>RPS</span><strong>{{ stats?.total_rps ?? 0 }}</strong></div>
              <div><span>失败/秒</span><strong>{{ stats?.total_fail_per_sec ?? 0 }}</strong></div>
              <div><span>P95</span><strong>{{ p95Value() }}</strong></div>
            </div>
          </section>
          <section class="surface">
            <div class="surface-title">
              <h2>治理</h2>
              <span>{{ quotas.length }} 条配额</span>
            </div>
            <table>
              <thead><tr><th>租户</th><th>用户数</th><th>Worker</th><th>时长</th></tr></thead>
              <tbody>
                <tr v-for="quota in quotas" :key="quota.tenant_id">
                  <td>{{ quota.tenant_id }}</td>
                  <td>{{ quota.max_users }}</td>
                  <td>{{ quota.max_workers_per_run }}</td>
                  <td>{{ quota.max_run_duration_seconds }}s</td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </section>

      <section v-if="activeView === 'tenants'" class="content surface">
        <div class="surface-title"><h2>租户</h2><span>{{ tenants.length }} 条记录</span></div>
        <table>
          <thead><tr><th>名称</th><th>标识</th><th>状态</th><th>ID</th></tr></thead>
          <tbody><tr v-for="tenant in tenants" :key="tenant.id"><td>{{ tenant.name }}</td><td>{{ tenant.slug }}</td><td>{{ statusText(tenant.status) }}</td><td>{{ tenant.id }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'access'" class="content surface">
        <div class="surface-title"><h2>访问控制</h2><span>{{ users.length }} 个用户 · {{ apiTokens.length }} 个 Token</span></div>
        <div class="split-layout flush">
          <section>
            <h3>创建用户</h3>
            <div class="form-grid compact">
              <label><span>租户</span><input v-model="userForm.tenant_id" /></label>
              <label><span>用户名</span><input v-model="userForm.username" /></label>
              <label><span>密码</span><input v-model="userForm.password" type="password" /></label>
              <label><span>角色</span><input v-model="userForm.role" /></label>
              <div class="form-actions"><button class="primary" type="button" @click="createUserFromForm">创建用户</button></div>
            </div>
            <table>
              <thead><tr><th>用户名</th><th>租户</th><th>角色</th></tr></thead>
              <tbody><tr v-for="item in users" :key="item.id"><td>{{ item.username }}</td><td>{{ item.tenant_id }}</td><td>{{ item.role }}</td></tr></tbody>
            </table>
          </section>
          <section>
            <h3>创建 API Token</h3>
            <div class="form-grid compact">
              <label><span>名称</span><input v-model="apiTokenForm.name" /></label>
              <label><span>权限范围</span><input v-model="apiTokenForm.scopes" /></label>
              <div class="form-actions"><button class="primary" type="button" @click="createTokenFromForm">创建 API Token</button></div>
              <p v-if="createdTokenSecret" class="token-secret">Token: {{ createdTokenSecret }}</p>
            </div>
            <table>
              <thead><tr><th>名称</th><th>权限范围</th><th>撤销时间</th><th>操作</th></tr></thead>
              <tbody>
                <tr v-for="token in apiTokens" :key="token.id">
                  <td>{{ token.name }}</td><td>{{ token.scopes.join(', ') }}</td><td>{{ token.revoked_at ?? '-' }}</td>
                  <td><button type="button" :disabled="Boolean(token.revoked_at)" @click="revokeToken(token)">撤销 Token</button></td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </section>

      <section v-if="activeView === 'projects'" class="content surface">
        <div class="surface-title"><h2>项目</h2><span>{{ projects.length }} 条记录</span></div>
        <table>
          <thead><tr><th>名称</th><th>标识</th><th>租户</th><th>状态</th></tr></thead>
          <tbody><tr v-for="project in projects" :key="project.id"><td>{{ project.name }}</td><td>{{ project.slug }}</td><td>{{ project.tenant_id }}</td><td>{{ statusText(project.status) }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'scripts'" class="content surface">
        <div class="surface-title"><h2>脚本</h2><span>{{ scripts.length }} 个版本</span></div>
        <div class="form-grid">
          <label><span>名称</span><input v-model="scriptForm.name" /></label>
          <label><span>租户</span><input v-model="scriptForm.tenant_id" /></label>
          <label><span>项目</span><input v-model="scriptForm.project_id" /></label>
          <label><span>依赖</span><input v-model="scriptForm.requirements" placeholder="locust 插件或依赖库" /></label>
          <label class="wide"><span>Locustfile</span><textarea v-model="scriptForm.locustfile" rows="9" /></label>
          <div class="form-actions wide">
            <button type="button" @click="validateScriptForm">校验 Locustfile</button>
            <button class="primary" type="button" @click="createScriptFromForm">创建脚本版本</button>
            <span v-if="validation" class="validation-pill" :class="{ ok: validation.valid }">
              {{ validation.valid ? '有效' : '无效' }} · {{ validation.task_count }} 个任务
            </span>
          </div>
          <ul v-if="validation?.errors.length" class="validation-list wide">
            <li v-for="item in validation.errors" :key="item">{{ item }}</li>
          </ul>
        </div>
        <table>
          <thead><tr><th>名称</th><th>项目</th><th>依赖</th><th>ID</th></tr></thead>
          <tbody><tr v-for="script in scripts" :key="script.id"><td>{{ script.name }}</td><td>{{ script.project_id }}</td><td>{{ script.requirements || '-' }}</td><td>{{ script.id }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'plans'" class="content surface">
        <div class="surface-title"><h2>压测计划</h2><span>{{ plans.length }} 个计划</span></div>
        <div class="form-grid compact">
          <label><span>名称</span><input v-model="planForm.name" /></label>
          <label><span>脚本</span><input v-model="planForm.script_version_id" /></label>
          <label><span>目标</span><input v-model="planForm.target_host" /></label>
          <label><span>用户数</span><input v-model.number="planForm.users" type="number" min="1" /></label>
          <label><span>生成速率</span><input v-model.number="planForm.spawn_rate" type="number" min="1" /></label>
          <label><span>时长</span><input v-model.number="planForm.run_time_seconds" type="number" min="1" /></label>
          <label><span>Workers</span><input v-model.number="planForm.worker_count" type="number" min="1" /></label>
          <div class="form-actions"><button class="primary" type="button" @click="createPlanFromForm">创建压测计划</button></div>
        </div>
        <table>
          <thead><tr><th>名称</th><th>目标</th><th>用户数</th><th>生成速率</th><th>Worker</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="plan in plans" :key="plan.id">
              <td>{{ plan.name }}</td><td>{{ plan.target_host }}</td><td>{{ plan.users }}</td><td>{{ plan.spawn_rate }}</td><td>{{ plan.worker_count }}</td><td>{{ statusText(plan.status) }}</td>
              <td><button type="button" @click="cloneSelectedPlan(plan)">复制计划</button></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="activeView === 'runs'" class="content run-layout">
        <section class="surface">
          <div class="surface-title">
            <h2>压测任务</h2>
            <div class="button-row">
              <button type="button" :disabled="!activeRun || loading" @click="collectActiveRun">采集</button>
              <button type="button" :disabled="!activeRun || loading" @click="stopActiveRun">停止</button>
              <button type="button" :disabled="!activeRun || loading" @click="rerunActiveRun">重跑</button>
            </div>
          </div>
          <table>
            <thead><tr><th>状态</th><th>来源</th><th>目标</th><th>用户数</th><th>Worker</th></tr></thead>
            <tbody>
              <tr v-for="run in runs" :key="run.id" :class="{ selected: run.id === activeRun?.id }" @click="selectRun(run)">
                <td><span class="status-tag">{{ statusText(run.status) }}</span></td>
                <td>{{ sourceText(run.source) }}</td>
                <td>{{ run.target_host }}</td>
                <td>{{ run.users }}</td>
                <td>{{ run.worker_count }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="surface">
          <div class="surface-title">
            <h2>Locust 详情</h2>
            <span>{{ activeRun?.id ?? '-' }}</span>
          </div>
          <div class="tab-list">
            <button v-for="tab in locustTabs" :key="tab" :class="{ active: activeTab === tab }" type="button" @click="activeTab = tab">{{ tab }}</button>
          </div>
          <table v-if="activeTab === '统计'">
            <thead><tr><th>类型</th><th>名称</th><th>请求数</th><th>失败数</th><th>中位数</th><th>平均</th><th>最小</th><th>最大</th><th>当前 RPS</th><th>95%</th><th>99%</th></tr></thead>
            <tbody>
              <tr v-for="row in stats?.stats ?? []" :key="`${row.method}-${row.name}`">
                <td>{{ row.method }}</td><td>{{ row.name }}</td><td>{{ row.num_requests }}</td><td>{{ row.num_failures }}</td><td>{{ row.median_response_time }}</td><td>{{ row.avg_response_time }}</td><td>{{ row.min_response_time }}</td><td>{{ row.max_response_time }}</td><td>{{ row.current_rps }}</td><td>{{ row['response_time_percentile_0.95'] }}</td><td>{{ row['response_time_percentile_0.99'] }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="activeTab === '图表'" class="chart-grid">
            <article v-for="card in chartCards" :key="card.title" class="chart-card">
              <div class="chart-title"><span>{{ card.title }}</span><strong>{{ card.latest }}</strong></div>
              <svg viewBox="0 0 320 90" role="img" :aria-label="`${card.title} trend chart`">
                <polyline v-if="card.points" :points="card.points" />
              </svg>
            </article>
          </div>
          <table v-if="activeTab === '失败'">
            <thead><tr><th>名称</th><th>错误</th><th>次数</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in stats?.errors ?? []" :key="index"><td>{{ item.name ?? '-' }}</td><td>{{ item.error ?? '-' }}</td><td>{{ item.occurrences ?? 0 }}</td></tr>
              <tr v-if="!(stats?.errors ?? []).length"><td colspan="3">当前采样未发现失败</td></tr>
            </tbody>
          </table>
          <table v-if="activeTab === 'Worker'">
            <thead><tr><th>ID</th><th>状态</th><th>用户数</th><th>CPU</th><th>内存</th></tr></thead>
            <tbody><tr v-for="worker in stats?.workers ?? []" :key="worker.id"><td>{{ worker.id }}</td><td>{{ statusText(worker.state) }}</td><td>{{ worker.user_count }}</td><td>{{ worker.cpu_usage }}</td><td>{{ worker.memory_usage }}</td></tr></tbody>
          </table>
          <div v-if="activeTab === '日志'" class="logs-panel">
            <div>
              <h3>异常</h3>
              <table>
                <thead><tr><th>名称</th><th>错误</th><th>次数</th></tr></thead>
                <tbody>
                  <tr v-for="(item, index) in stats?.errors ?? []" :key="index"><td>{{ item.name ?? '-' }}</td><td>{{ item.error ?? '-' }}</td><td>{{ item.occurrences ?? 0 }}</td></tr>
                  <tr v-if="!(stats?.errors ?? []).length"><td colspan="3">未发现异常</td></tr>
                </tbody>
              </table>
            </div>
            <div>
              <h3>Master 日志</h3>
              <pre>{{ report?.log_preview || '归档后可查看报告日志。' }}</pre>
            </div>
          </div>
          <div v-if="activeTab === '诊断'" class="diagnostics-panel">
            <section>
              <h3>建议</h3>
              <ul>
                <li v-for="item in diagnostics?.recommendations ?? []" :key="item">{{ item }}</li>
              </ul>
            </section>
            <section>
              <h3>生命周期事件</h3>
              <table>
                <thead><tr><th>状态</th><th>消息</th><th>时间</th></tr></thead>
                <tbody>
                  <tr v-for="event in diagnostics?.events ?? []" :key="event.id"><td>{{ statusText(event.status) }}</td><td>{{ event.message }}</td><td>{{ event.created_at }}</td></tr>
                </tbody>
              </table>
            </section>
          </div>
          <div v-if="activeTab === '下载数据'" class="download-panel">
            <span>报告状态</span>
            <strong>{{ statusText(report?.report_status) }}</strong>
            <span>总请求数</span>
            <strong>{{ report?.total_requests ?? 0 }}</strong>
            <div v-if="!(report?.artifacts ?? []).length" class="artifact-hint">
              <span v-for="name in expectedReportArtifacts" :key="name">{{ name }}</span>
            </div>
            <a v-for="artifact in report?.artifacts ?? []" :key="artifact.id" :href="artifact.download_url" target="_blank" rel="noreferrer">
              <span>{{ artifactDisplayName(artifact.name) }}</span>
              <strong>{{ artifact.size_bytes }} bytes</strong>
            </a>
          </div>
        </section>
      </section>

      <section v-if="activeView === 'governance'" class="content surface">
        <div class="surface-title"><h2>治理</h2><span>{{ targets.length }} 个目标 · {{ approvals.length }} 条审批</span></div>
        <table>
          <thead><tr><th>目标</th><th>类型</th><th>项目</th><th>环境</th><th>状态</th></tr></thead>
          <tbody><tr v-for="target in targets" :key="target.id"><td>{{ target.value }}</td><td>{{ target.target_type }}</td><td>{{ target.project_id }}</td><td>{{ target.environment }}</td><td>{{ statusText(target.status) }}</td></tr></tbody>
        </table>
        <div class="surface-title nested"><h2>审批请求</h2><span>{{ approvals.length }} 条记录</span></div>
        <table>
          <thead><tr><th>类型</th><th>资源</th><th>状态</th><th>原因</th></tr></thead>
          <tbody><tr v-for="approval in approvals" :key="approval.id"><td>{{ approval.request_type }}</td><td>{{ approval.resource_id }}</td><td>{{ statusText(approval.status) }}</td><td>{{ approval.reason ?? '-' }}</td></tr></tbody>
        </table>
        <div class="surface-title nested"><h2>准入快照</h2><span>{{ dnsSnapshots.length }} 条 DNS · {{ quotaUsageSnapshots.length }} 条配额</span></div>
        <table>
          <thead><tr><th>任务</th><th>主机名</th><th>风险</th><th>原因</th></tr></thead>
          <tbody><tr v-for="snapshot in dnsSnapshots" :key="snapshot.id"><td>{{ snapshot.test_run_id }}</td><td>{{ snapshot.hostname }}</td><td>{{ snapshot.risk_level }}</td><td>{{ snapshot.risk_reason }}</td></tr></tbody>
        </table>
        <table>
          <thead><tr><th>任务</th><th>决策</th><th>Worker</th><th>用户数</th><th>原因</th></tr></thead>
          <tbody><tr v-for="snapshot in quotaUsageSnapshots" :key="snapshot.id"><td>{{ snapshot.test_run_id }}</td><td>{{ statusText(snapshot.decision) }}</td><td>{{ snapshot.requested_workers }} / {{ snapshot.max_workers }}</td><td>{{ snapshot.requested_users }} / {{ snapshot.max_users }}</td><td>{{ snapshot.reason ?? '-' }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'reports'" class="content surface">
        <div class="surface-title"><h2>报告</h2><span>{{ reportArchive.items.length }} 份归档报告</span></div>
        <div class="report-grid">
          <div><span>总请求数</span><strong>{{ report?.total_requests ?? 0 }}</strong></div>
          <div><span>总失败数</span><strong>{{ report?.total_failures ?? 0 }}</strong></div>
          <div><span>平均响应</span><strong>{{ report?.avg_response_time ?? 0 }}</strong></div>
          <div><span>P95</span><strong>{{ report?.p95_response_time ?? 0 }}</strong></div>
        </div>
        <div class="surface-title compact-title"><h3>报告历史</h3><span>{{ reportArchive.trend.length }} 个趋势点</span></div>
        <div class="chart-grid compact-charts">
          <article v-for="card in reportTrendCards" :key="card.title" class="chart-card">
            <div class="chart-title"><span>{{ card.title }}</span><strong>{{ card.latest }}</strong></div>
            <svg viewBox="0 0 320 90" role="img" :aria-label="`${card.title} report trend chart`">
              <polyline :points="card.points" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
            </svg>
          </article>
        </div>
        <table>
          <thead><tr><th>任务</th><th>归档时间</th><th>总请求数</th><th>P95</th><th>总 RPS</th><th>下载项</th></tr></thead>
          <tbody>
            <tr v-for="item in reportArchive.items" :key="item.id">
              <td>{{ item.run_id }}</td>
              <td>{{ item.archived_at ?? '-' }}</td>
              <td>{{ item.total_requests }}</td>
              <td>{{ item.p95_response_time }}</td>
              <td>{{ item.total_rps }}</td>
              <td>{{ item.artifacts?.length ?? 0 }}</td>
            </tr>
          </tbody>
        </table>
        <div class="surface-title compact-title"><h3>报告对比</h3><span>最新 vs 上一次</span></div>
        <div class="compare-grid">
          <div>
            <span>基准任务</span>
            <strong>{{ reportComparison?.base.run_id ?? '-' }}</strong>
          </div>
          <div>
            <span>候选任务</span>
            <strong>{{ reportComparison?.candidate.run_id ?? '-' }}</strong>
          </div>
          <div>
            <span>P95 变化</span>
            <strong>{{ reportComparison?.deltas.p95_response_time?.delta ?? 0 }}</strong>
          </div>
          <div>
            <span>失败率变化</span>
            <strong>{{ reportComparison?.deltas.fail_ratio?.delta ?? 0 }}</strong>
          </div>
        </div>
      </section>

      <section v-if="activeView === 'ci'" class="content surface">
        <div class="surface-title"><h2>CI 基线</h2><span>{{ baselineProfiles.length }} 个 Profile</span></div>
        <div class="surface-title compact-title"><h3>基线 Profile</h3><span>可复用阈值</span></div>
        <div class="form-grid compact">
          <label><span>名称</span><input v-model="baselineProfileForm.name" /></label>
          <label><span>租户</span><input v-model="baselineProfileForm.tenant_id" /></label>
          <label><span>项目</span><input v-model="baselineProfileForm.project_id" /></label>
          <label><span>最大 P95</span><input v-model.number="baselineProfileForm.max_p95_ms" type="number" /></label>
          <label><span>最大失败率</span><input v-model.number="baselineProfileForm.max_fail_ratio" type="number" step="0.001" /></label>
          <label><span>最小 RPS</span><input v-model.number="baselineProfileForm.min_total_rps" type="number" /></label>
          <div class="form-actions"><button class="primary" type="button" @click="createBaselineProfileFromForm">创建基线 Profile</button></div>
        </div>
        <table>
          <thead><tr><th>名称</th><th>项目</th><th>最大 P95</th><th>最大失败率</th><th>最小 RPS</th><th>ID</th></tr></thead>
          <tbody>
            <tr v-for="profile in baselineProfiles" :key="profile.id">
              <td>{{ profile.name }}</td>
              <td>{{ profile.project_id }}</td>
              <td>{{ profile.max_p95_ms }}</td>
              <td>{{ profile.max_fail_ratio }}</td>
              <td>{{ profile.min_total_rps ?? '-' }}</td>
              <td>{{ profile.id }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  </div>
</template>
