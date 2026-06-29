<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  collectRun,
  createRunFromPlan,
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
} from './api/client';
import type {
  ApprovalRequest,
  DnsResolutionSnapshot,
  LocustStatsResponse,
  Project,
  QuotaUsageSnapshot,
  ReportSummary,
  ScriptVersion,
  TargetWhitelist,
  Tenant,
  TenantQuota,
  TestPlan,
  TestRun,
} from './types';

type ViewKey = 'dashboard' | 'tenants' | 'projects' | 'scripts' | 'plans' | 'runs' | 'governance' | 'reports';
type LocustTab = 'Statistics' | 'Failures' | 'Workers' | 'Download';

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
const locustTabs: LocustTab[] = ['Statistics', 'Failures', 'Workers', 'Download'];

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

async function selectRun(run: TestRun) {
  selectedRunId.value = run.id;
  await withLoading(async () => refreshRunDetail(run.id));
}

function p95Value() {
  return stats.value?.current_response_time_percentiles?.['response_time_percentile_0.95'] ?? 0;
}

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
        <table>
          <thead><tr><th>Name</th><th>Project</th><th>Requirements</th><th>ID</th></tr></thead>
          <tbody><tr v-for="script in scripts" :key="script.id"><td>{{ script.name }}</td><td>{{ script.project_id }}</td><td>{{ script.requirements || '-' }}</td><td>{{ script.id }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'plans'" class="content surface">
        <div class="surface-title"><h2>Test Plans</h2><span>{{ plans.length }} plans</span></div>
        <table>
          <thead><tr><th>Name</th><th>Target</th><th>Users</th><th>Spawn</th><th>Workers</th><th>Status</th></tr></thead>
          <tbody><tr v-for="plan in plans" :key="plan.id"><td>{{ plan.name }}</td><td>{{ plan.target_host }}</td><td>{{ plan.users }}</td><td>{{ plan.spawn_rate }}</td><td>{{ plan.worker_count }}</td><td>{{ plan.status }}</td></tr></tbody>
        </table>
      </section>

      <section v-if="activeView === 'runs'" class="content run-layout">
        <section class="surface">
          <div class="surface-title">
            <h2>Test Runs</h2>
            <div class="button-row">
              <button type="button" :disabled="!activeRun || loading" @click="collectActiveRun">Collect</button>
              <button type="button" :disabled="!activeRun || loading" @click="stopActiveRun">Stop</button>
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
          <table v-if="activeTab === 'Failures'">
            <thead><tr><th>Name</th><th>Error</th><th>Occurrences</th></tr></thead>
            <tbody><tr v-for="(item, index) in stats?.errors ?? []" :key="index"><td>{{ item.name ?? '-' }}</td><td>{{ item.error ?? '-' }}</td><td>{{ item.occurrences ?? 0 }}</td></tr></tbody>
          </table>
          <table v-if="activeTab === 'Workers'">
            <thead><tr><th>ID</th><th>State</th><th>Users</th><th>CPU</th><th>Memory</th></tr></thead>
            <tbody><tr v-for="worker in stats?.workers ?? []" :key="worker.id"><td>{{ worker.id }}</td><td>{{ worker.state }}</td><td>{{ worker.user_count }}</td><td>{{ worker.cpu_usage }}</td><td>{{ worker.memory_usage }}</td></tr></tbody>
          </table>
          <div v-if="activeTab === 'Download'" class="download-panel">
            <span>Report Status</span>
            <strong>{{ report?.report_status ?? 'not archived' }}</strong>
            <span>Total Requests</span>
            <strong>{{ report?.total_requests ?? 0 }}</strong>
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
