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

export interface ScriptValidationResult {
  valid: boolean;
  user_class_found: boolean;
  task_count: number;
  errors: string[];
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

export interface RunEvent {
  id: string;
  test_run_id: string;
  status: string;
  message: string;
  created_at: string;
}

export interface RunDiagnostics {
  run: TestRun;
  lane?: Record<string, unknown> | null;
  latest_snapshot?: Record<string, unknown> | null;
  latest_errors: Array<Record<string, unknown>>;
  workers: LocustWorker[];
  report?: ReportSummary | null;
  events: RunEvent[];
  recommendations: string[];
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

export interface ApprovalRequest {
  id: string;
  tenant_id: string;
  project_id: string;
  request_type: string;
  resource_type: string;
  resource_id: string;
  status: string;
  reason?: string | null;
}

export interface DnsResolutionSnapshot {
  id: string;
  test_run_id: string;
  hostname: string;
  resolved_ips_json: string;
  risk_level: string;
  risk_reason: string;
}

export interface QuotaUsageSnapshot {
  id: string;
  test_run_id: string;
  requested_workers: number;
  running_workers: number;
  max_workers: number;
  requested_users: number;
  max_users: number;
  decision: string;
  reason?: string | null;
}

export interface ReportSummary {
  id: string;
  tenant_id: string;
  project_id: string;
  run_id: string;
  report_status: string;
  artifacts?: ReportArtifact[];
  log_preview?: string;
  total_requests: number;
  total_failures: number;
  avg_response_time: number;
  p95_response_time: number;
  p99_response_time: number;
  total_rps: number;
  fail_ratio: number;
}

export interface ReportArtifact {
  id: string;
  name: string;
  kind: string;
  content_type: string;
  size_bytes: number;
  checksum: string;
  download_url: string;
}

export interface LocustHistoryPoint {
  sample_time: string;
  user_count: number;
  total_rps: number;
  total_fail_per_sec: number;
  p50: number;
  p95: number;
  avg_response_time: number;
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
  history: LocustHistoryPoint[];
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
