export type RunStatus =
  | 'CREATED'
  | 'VALIDATING'
  | 'APPROVAL_PENDING'
  | 'APPROVED'
  | 'LANE_CREATING'
  | 'PROVISIONING'
  | 'RUNNING'
  | 'COLLECTING'
  | 'ARCHIVING'
  | 'DESTROYING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELING'
  | 'CANCELED';

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  status: string;
}

export interface Project {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  status: string;
}

export interface ScriptVersion {
  id: string;
  tenant_id: string;
  project_id: string;
  name: string;
  locustfile: string;
  requirements: string;
}

export interface TestPlan {
  id: string;
  tenant_id: string;
  project_id: string;
  script_version_id: string;
  name: string;
  target_host: string;
  users: number;
  spawn_rate: number;
  run_time_seconds: number;
  worker_count: number;
  status: string;
}

export interface TestRun {
  id: string;
  tenant_id: string;
  project_id: string;
  test_plan_id: string;
  source: string;
  status: RunStatus;
  target_host: string;
  users: number;
  spawn_rate: number;
  run_time_seconds: number;
  worker_count: number;
  failure_reason?: string | null;
}

export interface TargetWhitelist {
  id: string;
  tenant_id: string;
  project_id: string;
  target_type: string;
  value: string;
  status: string;
  environment: string;
}

export interface TenantQuota {
  tenant_id: string;
  max_concurrent_runs: number;
  max_workers_per_run: number;
  max_total_workers: number;
  max_users: number;
  max_spawn_rate: number;
  max_run_duration_seconds: number;
}

export interface ReportSummary {
  id: string;
  tenant_id: string;
  project_id: string;
  run_id: string;
  report_status: string;
  total_requests: number;
  total_failures: number;
  avg_response_time: number;
  p95_response_time: number;
  p99_response_time: number;
  total_rps: number;
  fail_ratio: number;
}

export interface LocustStatRow {
  method: string;
  name: string;
  num_requests: number;
  num_failures: number;
  current_rps: number;
  current_fail_per_sec: number;
  avg_response_time: number;
  median_response_time: number;
  min_response_time: number;
  max_response_time: number;
  'response_time_percentile_0.95': number;
  'response_time_percentile_0.99': number;
  avg_content_length: number;
}

export interface LocustWorker {
  id: string;
  state: string;
  user_count: number;
  cpu_usage: number;
  memory_usage: number;
}

export interface LocustStatsResponse {
  stats: LocustStatRow[];
  errors: Array<Record<string, unknown>>;
  total_rps: number;
  total_fail_per_sec: number;
  fail_ratio: number;
  current_response_time_percentiles?: {
    'response_time_percentile_0.5'?: number;
    'response_time_percentile_0.95'?: number;
  };
  state: string;
  user_count: number;
  worker_count: number;
  workers: LocustWorker[];
}
