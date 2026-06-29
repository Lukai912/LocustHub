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
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';
// The MVP backend still uses a demo bearer token; centralizing the fallback
// keeps the later auth replacement localized to this client.
const DEMO_TOKEN = import.meta.env.VITE_DEMO_TOKEN ?? 'dev-token';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${DEMO_TOKEN}`,
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function listTenants(): Promise<Tenant[]> {
  return request<Tenant[]>('/tenants');
}

export async function listProjects(): Promise<Project[]> {
  return request<Project[]>('/projects');
}

export async function listScripts(): Promise<ScriptVersion[]> {
  return request<ScriptVersion[]>('/scripts/script-demo/versions');
}

export async function listTestPlans(): Promise<TestPlan[]> {
  return request<TestPlan[]>('/test-plans');
}

export async function listTestRuns(): Promise<TestRun[]> {
  return request<TestRun[]>('/test-runs');
}

export async function createRunFromPlan(plan: TestPlan): Promise<TestRun> {
  return request<TestRun>('/test-runs', {
    method: 'POST',
    body: JSON.stringify({
      tenant_id: plan.tenant_id,
      project_id: plan.project_id,
      test_plan_id: plan.id,
      source: 'manual',
    }),
  });
}

export async function startRun(runId: string): Promise<TestRun> {
  return request<TestRun>(`/test-runs/${runId}/start`, { method: 'POST' });
}

export async function collectRun(runId: string): Promise<{ samples: unknown[] }> {
  return request<{ samples: unknown[] }>(`/test-runs/${runId}/collect`, { method: 'POST' });
}

export async function stopRun(runId: string): Promise<TestRun> {
  return request<TestRun>(`/test-runs/${runId}/stop`, { method: 'POST' });
}

export async function getLocustStats(runId: string): Promise<LocustStatsResponse> {
  return request<LocustStatsResponse>(`/test-runs/${runId}/locust/stats`);
}

export async function getReport(runId: string): Promise<ReportSummary> {
  return request<ReportSummary>(`/test-runs/${runId}/report`);
}

export async function listTargets(): Promise<TargetWhitelist[]> {
  return request<TargetWhitelist[]>('/target-whitelists');
}

export async function listQuotas(): Promise<TenantQuota[]> {
  return request<TenantQuota[]>('/tenant-quotas');
}

export async function listApprovalRequests(): Promise<ApprovalRequest[]> {
  return request<ApprovalRequest[]>('/approval-requests');
}

export async function listDnsSnapshots(): Promise<DnsResolutionSnapshot[]> {
  return request<DnsResolutionSnapshot[]>('/dns-resolution-snapshots');
}

export async function listQuotaUsageSnapshots(): Promise<QuotaUsageSnapshot[]> {
  return request<QuotaUsageSnapshot[]>('/quota-usage-snapshots');
}
