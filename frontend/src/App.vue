<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  collectRun,
  createRunFromPlan,
  createScriptVersion,
  createTestPlan,
  cloneTestPlan,
  getRunDiagnostics,
  getLocustStats,
  getReport,
  listApprovalRequests,
  listDnsSnapshots,
  listProjects,
  listQuotas,
  listQuotaUsageSnapshots,
  listScripts,
  listTargets,
  listTenants,
  listTestPlans,
  listTestRuns,
  startRun,
  stopRun,
  rerunTestRun,
  validateLocustfile,
} from './api/client';
import type {
  ApprovalRequest,
  DnsResolutionSnapshot,
  LocustStatsResponse,
  Project,
  QuotaUsageSnapshot,
  ReportSummary,
  RunDiagnostics,
  ScriptValidationResult,
  ScriptVersion,
  TargetWhitelist,
  Tenant,
  TenantQuota,
  TestPlan,
  TestRun,
} from './types';

type ViewKey = 'dashboard' | 'tenants' | 'projects' | 'scripts' | 'plans' | 'runs' | 'governance' | 'reports';
type LocustTab = 'Statistics' | 'Charts' | 'Failures' | 'Workers' | 'Logs' | 'Diagnostics' | 'Download Data';

const navigation: Array<{ key: ViewKey; label: string; cn: string }> = [
  { key: 'dashboard', label: 'Dashboard', cn: '仪表盘' },
  { key: 'tenants', label: 'Tenants', cn: '租户' },
  { key: 'projects', label: 'Projects', cn: '项目' },
  { key: 'scripts', label: 'Scripts', cn: '脚本' },
  { key: 'plans', label: 'Test Plans', cn: '压测计划' },
  { key: 'runs', label: 'Test Runs', cn: '压测任务' },
  { key: 'governance', label: 'Governance', cn: '治理' },
  { key: 'reports', label: 'Reports', cn: '报告' },
];
const locustTabs: LocustTab[] = ['Statistics', 'Charts', 'Failures', 'Workers', 'Logs', 'Diagnostics', 'Download Data'];
const expectedReportArtifacts = ['HTML Report', 'Requests CSV', 'Failures CSV', 'Exceptions CSV', 'History CSV', 'Master Log'];

const activeView = ref<ViewKey>('dashboard');
const activeTab = ref<LocustTab>('Statistics');
const selectedRunId = ref('');
const loading = ref(false);
const error = ref('');

const tenants = ref<Tenant[]>([]);
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
const diagnostics = ref<RunDiagnostics | null>(null);
const validation = ref<ScriptValidationResult | null>(null);
const defaultLocustfile = "from locust import HttpUser, task\n\nclass DemoUser(HttpUser):\n    @task\n    def index(self):\n        self.client.get('/todos/1')\n";
const scriptForm = ref({
  tenant_id: 'tenant-demo',
  project_id: 'project-demo',
  name: 'New Locust script',
  locustfile: defaultLocustfile,
  requirements: '',
});
const planForm = ref({
  tenant_id: 'tenant-demo',
  project_id: 'project-demo',
  script_version_id: 'script-demo',
  name: 'New Test Plan',
  target_host: 'https://jsonplaceholder.typicode.com',
  users: 5,
  spawn_rate: 1,
  run_time_seconds: 60,
  worker_count: 1,
});

const activeRun = computed(() => runs.value.find((run) => run.id === selectedRunId.value) ?? runs.value[0]);
const runningCount = computed(() => runs.value.filter((run) => run.status === 'RUNNING').length);
const completedCount = computed(() => runs.value.filter((run) => run.status === 'COMPLETED').length);
const pendingTargets = computed(() => targets.value.filter((target) => target.status !== 'approved').length);

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
    const [tenantRows, projectRows, scriptRows, planRows, runRows, targetRows, quotaRows, approvalRows, dnsRows, quotaUsageRows] = await Promise.all([
      listTenants(),
      listProjects(),
      listScripts(),
      listTestPlans(),
      listTestRuns(),
      listTargets(),
      listQuotas(),
      listApprovalRequests(),
      listDnsSnapshots(),
      listQuotaUsageSnapshots(),
    ]);
    tenants.value = tenantRows;
    projects.value = projectRows;
    scripts.value = scriptRows;
    plans.value = planRows;
    runs.value = runRows;
    targets.value = targetRows;
    quotas.value = quotaRows;
    approvals.value = approvalRows;
    dnsSnapshots.value = dnsRows;
    quotaUsageSnapshots.value = quotaUsageRows;
    if (!selectedRunId.value && runRows[0]) selectedRunId.value = runRows[0].id;
    if (selectedRunId.value) await refreshRunDetail(selectedRunId.value);
  });
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
    if (!plan) throw new Error('No test plan is available');
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
    const cloned = await cloneTestPlan(plan.id, `${plan.name} Copy`);
    plans.value = await listTestPlans();
    planForm.value = { ...planForm.value, ...cloned, name: `${cloned.name} Variant` };
  });
}

function p95Value() {
  return stats.value?.current_response_time_percentiles?.['response_time_percentile_0.95'] ?? 0;
}

function chartValues(key: 'total_rps' | 'total_fail_per_sec' | 'p50' | 'p95' | 'user_count') {
  return (stats.value?.history ?? []).map((point) => Number(point[key] ?? 0));
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
  { title: 'Failures/s', points: sparklinePoints(chartValues('total_fail_per_sec')), latest: stats.value?.total_fail_per_sec ?? 0 },
  { title: 'Response Times', points: sparklinePoints(chartValues('p95')), latest: p95Value() },
  { title: 'User Count', points: sparklinePoints(chartValues('user_count')), latest: stats.value?.user_count ?? 0 },
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
          <h1>LocustHub Admin</h1>
          <p>{{ activeRun ? `${activeRun.status} · ${activeRun.id}` : 'No active test run' }}</p>
        </div>
        <div class="topbar-actions">
          <button type="button" @click="refreshAll">Refresh</button>
          <button class="primary" type="button" @click="createAndStartDemo">Create Demo Run</button>
        </div>
      </header>

      <div v-if="error" class="alert">{{ error }}</div>

      <section v-if="activeView === 'dashboard'" class="content">
        <div class="metric-grid">
          <article class="metric-card">
            <span>Tenants</span>
            <strong>{{ tenants.length }}</strong>
          </article>
          <article class="metric-card">
            <span>Running</span>
            <strong>{{ runningCount }}</strong>
          </article>
          <article class="metric-card">
            <span>Completed</span>
            <strong>{{ completedCount }}</strong>
          </article>
          <article class="metric-card">
            <span>Pending Targets</span>
            <strong>{{ pendingTargets }}</strong>
          </article>
        </div>
        <div class="split-layout">
          <section class="surface">
            <div class="surface-title">
              <h2>Realtime Run</h2>
              <span class="status-tag">{{ activeRun?.status ?? 'MISSING' }}</span>
            </div>
            <div class="runtime-strip">
              <div><span>Users</span><strong>{{ stats?.user_count ?? 0 }}</strong></div>
              <div><span>RPS</span><strong>{{ stats?.total_rps ?? 0 }}</strong></div>
              <div><span>Failures/s</span><strong>{{ stats?.total_fail_per_sec ?? 0 }}</strong></div>
              <div><span>P95</span><strong>{{ p95Value() }}</strong></div>
            </div>
          </section>
          <section class="surface">
            <div class="surface-title">
              <h2>Governance</h2>
              <span>{{ quotas.length }} quota records</span>
            </div>
            <table>
              <thead><tr><th>Tenant</th><th>Users</th><th>Workers</th><th>Duration</th></tr></thead>
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
        <div class="surface-title"><h2>Tenants</h2><span>{{ tenants.length }} records</span></div>
        <table>
          <thead><tr><th>Name</th><th>Slug</th><th>Status</th><th>ID</th></tr></thead>
          <tbody><tr v-for="tenant in tenants" :key="tenant.id"><td>{{ tenant.name }}</td><td>{{ tenant.slug }}</td><td>{{ tenant.status }}</td><td>{{ tenant.id }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'projects'" class="content surface">
        <div class="surface-title"><h2>Projects</h2><span>{{ projects.length }} records</span></div>
        <table>
          <thead><tr><th>Name</th><th>Slug</th><th>Tenant</th><th>Status</th></tr></thead>
          <tbody><tr v-for="project in projects" :key="project.id"><td>{{ project.name }}</td><td>{{ project.slug }}</td><td>{{ project.tenant_id }}</td><td>{{ project.status }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'scripts'" class="content surface">
        <div class="surface-title"><h2>Scripts</h2><span>{{ scripts.length }} versions</span></div>
        <div class="form-grid">
          <label><span>Name</span><input v-model="scriptForm.name" /></label>
          <label><span>Tenant</span><input v-model="scriptForm.tenant_id" /></label>
          <label><span>Project</span><input v-model="scriptForm.project_id" /></label>
          <label><span>Requirements</span><input v-model="scriptForm.requirements" placeholder="locust plugins or libs" /></label>
          <label class="wide"><span>Locustfile</span><textarea v-model="scriptForm.locustfile" rows="9" /></label>
          <div class="form-actions wide">
            <button type="button" @click="validateScriptForm">Validate Locustfile</button>
            <button class="primary" type="button" @click="createScriptFromForm">Create Script Version</button>
            <span v-if="validation" class="validation-pill" :class="{ ok: validation.valid }">
              {{ validation.valid ? 'valid' : 'invalid' }} · {{ validation.task_count }} tasks
            </span>
          </div>
          <ul v-if="validation?.errors.length" class="validation-list wide">
            <li v-for="item in validation.errors" :key="item">{{ item }}</li>
          </ul>
        </div>
        <table>
          <thead><tr><th>Name</th><th>Project</th><th>Requirements</th><th>ID</th></tr></thead>
          <tbody><tr v-for="script in scripts" :key="script.id"><td>{{ script.name }}</td><td>{{ script.project_id }}</td><td>{{ script.requirements || '-' }}</td><td>{{ script.id }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'plans'" class="content surface">
        <div class="surface-title"><h2>Test Plans</h2><span>{{ plans.length }} plans</span></div>
        <div class="form-grid compact">
          <label><span>Name</span><input v-model="planForm.name" /></label>
          <label><span>Script</span><input v-model="planForm.script_version_id" /></label>
          <label><span>Target</span><input v-model="planForm.target_host" /></label>
          <label><span>Users</span><input v-model.number="planForm.users" type="number" min="1" /></label>
          <label><span>Spawn Rate</span><input v-model.number="planForm.spawn_rate" type="number" min="1" /></label>
          <label><span>Duration</span><input v-model.number="planForm.run_time_seconds" type="number" min="1" /></label>
          <label><span>Workers</span><input v-model.number="planForm.worker_count" type="number" min="1" /></label>
          <div class="form-actions"><button class="primary" type="button" @click="createPlanFromForm">Create Test Plan</button></div>
        </div>
        <table>
          <thead><tr><th>Name</th><th>Target</th><th>Users</th><th>Spawn</th><th>Workers</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            <tr v-for="plan in plans" :key="plan.id">
              <td>{{ plan.name }}</td><td>{{ plan.target_host }}</td><td>{{ plan.users }}</td><td>{{ plan.spawn_rate }}</td><td>{{ plan.worker_count }}</td><td>{{ plan.status }}</td>
              <td><button type="button" @click="cloneSelectedPlan(plan)">Clone Plan</button></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="activeView === 'runs'" class="content run-layout">
        <section class="surface">
          <div class="surface-title">
            <h2>Test Runs</h2>
            <div class="button-row">
              <button type="button" :disabled="!activeRun || loading" @click="collectActiveRun">Collect</button>
              <button type="button" :disabled="!activeRun || loading" @click="stopActiveRun">Stop</button>
              <button type="button" :disabled="!activeRun || loading" @click="rerunActiveRun">Rerun</button>
            </div>
          </div>
          <table>
            <thead><tr><th>Status</th><th>Source</th><th>Target</th><th>Users</th><th>Workers</th></tr></thead>
            <tbody>
              <tr v-for="run in runs" :key="run.id" :class="{ selected: run.id === activeRun?.id }" @click="selectRun(run)">
                <td><span class="status-tag">{{ run.status }}</span></td>
                <td>{{ run.source }}</td>
                <td>{{ run.target_host }}</td>
                <td>{{ run.users }}</td>
                <td>{{ run.worker_count }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="surface">
          <div class="surface-title">
            <h2>Locust Detail</h2>
            <span>{{ activeRun?.id ?? '-' }}</span>
          </div>
          <div class="tab-list">
            <button v-for="tab in locustTabs" :key="tab" :class="{ active: activeTab === tab }" type="button" @click="activeTab = tab">{{ tab }}</button>
          </div>
          <table v-if="activeTab === 'Statistics'">
            <thead><tr><th>Type</th><th>Name</th><th>Requests</th><th>Fails</th><th>Median</th><th>Average</th><th>Min</th><th>Max</th><th>Current RPS</th><th>95%</th><th>99%</th></tr></thead>
            <tbody>
              <tr v-for="row in stats?.stats ?? []" :key="`${row.method}-${row.name}`">
                <td>{{ row.method }}</td><td>{{ row.name }}</td><td>{{ row.num_requests }}</td><td>{{ row.num_failures }}</td><td>{{ row.median_response_time }}</td><td>{{ row.avg_response_time }}</td><td>{{ row.min_response_time }}</td><td>{{ row.max_response_time }}</td><td>{{ row.current_rps }}</td><td>{{ row['response_time_percentile_0.95'] }}</td><td>{{ row['response_time_percentile_0.99'] }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="activeTab === 'Charts'" class="chart-grid">
            <article v-for="card in chartCards" :key="card.title" class="chart-card">
              <div class="chart-title"><span>{{ card.title }}</span><strong>{{ card.latest }}</strong></div>
              <svg viewBox="0 0 320 90" role="img" :aria-label="`${card.title} trend chart`">
                <polyline v-if="card.points" :points="card.points" />
              </svg>
            </article>
          </div>
          <table v-if="activeTab === 'Failures'">
            <thead><tr><th>Name</th><th>Error</th><th>Occurrences</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in stats?.errors ?? []" :key="index"><td>{{ item.name ?? '-' }}</td><td>{{ item.error ?? '-' }}</td><td>{{ item.occurrences ?? 0 }}</td></tr>
              <tr v-if="!(stats?.errors ?? []).length"><td colspan="3">No failures captured for this sample</td></tr>
            </tbody>
          </table>
          <table v-if="activeTab === 'Workers'">
            <thead><tr><th>ID</th><th>State</th><th>Users</th><th>CPU</th><th>Memory</th></tr></thead>
            <tbody><tr v-for="worker in stats?.workers ?? []" :key="worker.id"><td>{{ worker.id }}</td><td>{{ worker.state }}</td><td>{{ worker.user_count }}</td><td>{{ worker.cpu_usage }}</td><td>{{ worker.memory_usage }}</td></tr></tbody>
          </table>
          <div v-if="activeTab === 'Logs'" class="logs-panel">
            <div>
              <h3>Exceptions</h3>
              <table>
                <thead><tr><th>Name</th><th>Error</th><th>Occurrences</th></tr></thead>
                <tbody>
                  <tr v-for="(item, index) in stats?.errors ?? []" :key="index"><td>{{ item.name ?? '-' }}</td><td>{{ item.error ?? '-' }}</td><td>{{ item.occurrences ?? 0 }}</td></tr>
                  <tr v-if="!(stats?.errors ?? []).length"><td colspan="3">No exceptions captured</td></tr>
                </tbody>
              </table>
            </div>
            <div>
              <h3>Master Log</h3>
              <pre>{{ report?.log_preview || 'Report logs are available after archival.' }}</pre>
            </div>
          </div>
          <div v-if="activeTab === 'Diagnostics'" class="diagnostics-panel">
            <section>
              <h3>Recommendations</h3>
              <ul>
                <li v-for="item in diagnostics?.recommendations ?? []" :key="item">{{ item }}</li>
              </ul>
            </section>
            <section>
              <h3>Lifecycle Events</h3>
              <table>
                <thead><tr><th>Status</th><th>Message</th><th>Time</th></tr></thead>
                <tbody>
                  <tr v-for="event in diagnostics?.events ?? []" :key="event.id"><td>{{ event.status }}</td><td>{{ event.message }}</td><td>{{ event.created_at }}</td></tr>
                </tbody>
              </table>
            </section>
          </div>
          <div v-if="activeTab === 'Download Data'" class="download-panel">
            <span>Report Status</span>
            <strong>{{ report?.report_status ?? 'not archived' }}</strong>
            <span>Total Requests</span>
            <strong>{{ report?.total_requests ?? 0 }}</strong>
            <div v-if="!(report?.artifacts ?? []).length" class="artifact-hint">
              <span v-for="name in expectedReportArtifacts" :key="name">{{ name }}</span>
            </div>
            <a v-for="artifact in report?.artifacts ?? []" :key="artifact.id" :href="artifact.download_url" target="_blank" rel="noreferrer">
              <span>{{ artifact.name }}</span>
              <strong>{{ artifact.size_bytes }} bytes</strong>
            </a>
          </div>
        </section>
      </section>

      <section v-if="activeView === 'governance'" class="content surface">
        <div class="surface-title"><h2>Governance</h2><span>{{ targets.length }} targets · {{ approvals.length }} approvals</span></div>
        <table>
          <thead><tr><th>Target</th><th>Type</th><th>Project</th><th>Environment</th><th>Status</th></tr></thead>
          <tbody><tr v-for="target in targets" :key="target.id"><td>{{ target.value }}</td><td>{{ target.target_type }}</td><td>{{ target.project_id }}</td><td>{{ target.environment }}</td><td>{{ target.status }}</td></tr></tbody>
        </table>
        <div class="surface-title nested"><h2>Approval Requests</h2><span>{{ approvals.length }} records</span></div>
        <table>
          <thead><tr><th>Type</th><th>Resource</th><th>Status</th><th>Reason</th></tr></thead>
          <tbody><tr v-for="approval in approvals" :key="approval.id"><td>{{ approval.request_type }}</td><td>{{ approval.resource_id }}</td><td>{{ approval.status }}</td><td>{{ approval.reason ?? '-' }}</td></tr></tbody>
        </table>
        <div class="surface-title nested"><h2>Admission Snapshots</h2><span>{{ dnsSnapshots.length }} DNS · {{ quotaUsageSnapshots.length }} quota</span></div>
        <table>
          <thead><tr><th>Run</th><th>Hostname</th><th>Risk</th><th>Reason</th></tr></thead>
          <tbody><tr v-for="snapshot in dnsSnapshots" :key="snapshot.id"><td>{{ snapshot.test_run_id }}</td><td>{{ snapshot.hostname }}</td><td>{{ snapshot.risk_level }}</td><td>{{ snapshot.risk_reason }}</td></tr></tbody>
        </table>
        <table>
          <thead><tr><th>Run</th><th>Decision</th><th>Workers</th><th>Users</th><th>Reason</th></tr></thead>
          <tbody><tr v-for="snapshot in quotaUsageSnapshots" :key="snapshot.id"><td>{{ snapshot.test_run_id }}</td><td>{{ snapshot.decision }}</td><td>{{ snapshot.requested_workers }} / {{ snapshot.max_workers }}</td><td>{{ snapshot.requested_users }} / {{ snapshot.max_users }}</td><td>{{ snapshot.reason ?? '-' }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'reports'" class="content surface">
        <div class="surface-title"><h2>Reports</h2><span>{{ report?.report_status ?? 'no active report' }}</span></div>
        <div class="report-grid">
          <div><span>Total Requests</span><strong>{{ report?.total_requests ?? 0 }}</strong></div>
          <div><span>Total Failures</span><strong>{{ report?.total_failures ?? 0 }}</strong></div>
          <div><span>Average</span><strong>{{ report?.avg_response_time ?? 0 }}</strong></div>
          <div><span>P95</span><strong>{{ report?.p95_response_time ?? 0 }}</strong></div>
        </div>
      </section>
    </main>
  </div>
</template>
