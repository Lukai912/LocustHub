CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL,
    created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    username VARCHAR(128) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(64) NOT NULL,
    password_hash VARCHAR(128),
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_users_tenant (tenant_id)
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    scopes_json JSON NOT NULL,
    revoked_at VARCHAR(64),
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_api_tokens_tenant (tenant_id, created_at)
);

CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_projects_tenant (tenant_id)
);

CREATE TABLE IF NOT EXISTS script_versions (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    locustfile MEDIUMTEXT NOT NULL,
    requirements TEXT NOT NULL,
    artifact_key VARCHAR(1024),
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_script_versions_project (tenant_id, project_id)
);

CREATE TABLE IF NOT EXISTS test_plans (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    script_version_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    target_host VARCHAR(1024) NOT NULL,
    users INT NOT NULL,
    spawn_rate INT NOT NULL,
    run_time_seconds INT NOT NULL,
    worker_count INT NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_test_plans_project (tenant_id, project_id)
);

CREATE TABLE IF NOT EXISTS target_whitelists (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    target_type VARCHAR(32) NOT NULL,
    value VARCHAR(512) NOT NULL,
    ports_json JSON NOT NULL,
    environment VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    reason TEXT,
    approved_by VARCHAR(128),
    approved_at VARCHAR(64),
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_targets_project (tenant_id, project_id, status)
);

CREATE TABLE IF NOT EXISTS approval_requests (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    request_type VARCHAR(32) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    reason TEXT,
    requested_by VARCHAR(128) NOT NULL,
    reviewed_by VARCHAR(128),
    reviewed_at VARCHAR(64),
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_approval_requests_project (tenant_id, project_id, status),
    INDEX idx_approval_requests_resource (resource_type, resource_id)
);

CREATE TABLE IF NOT EXISTS dns_resolution_snapshots (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    test_run_id VARCHAR(64) NOT NULL,
    hostname VARCHAR(512) NOT NULL,
    resolved_ips_json JSON NOT NULL,
    risk_level VARCHAR(32) NOT NULL,
    risk_reason TEXT NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_dns_snapshots_run (test_run_id, created_at),
    INDEX idx_dns_snapshots_project (tenant_id, project_id, created_at)
);

CREATE TABLE IF NOT EXISTS tenant_quotas (
    tenant_id VARCHAR(64) PRIMARY KEY,
    max_concurrent_runs INT NOT NULL,
    max_workers_per_run INT NOT NULL,
    max_total_workers INT NOT NULL,
    max_users INT NOT NULL,
    max_spawn_rate INT NOT NULL,
    max_run_duration_seconds INT NOT NULL,
    updated_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS quota_usage_snapshots (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    test_run_id VARCHAR(64) NOT NULL,
    requested_workers INT NOT NULL,
    running_workers INT NOT NULL,
    max_workers INT NOT NULL,
    requested_users INT NOT NULL,
    max_users INT NOT NULL,
    requested_spawn_rate INT NOT NULL,
    max_spawn_rate INT NOT NULL,
    decision VARCHAR(32) NOT NULL,
    reason TEXT,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_quota_usage_run (test_run_id, created_at),
    INDEX idx_quota_usage_project (tenant_id, project_id, created_at)
);

CREATE TABLE IF NOT EXISTS test_runs (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    test_plan_id VARCHAR(64) NOT NULL,
    source VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    target_host VARCHAR(1024) NOT NULL,
    users INT NOT NULL,
    spawn_rate INT NOT NULL,
    run_time_seconds INT NOT NULL,
    worker_count INT NOT NULL,
    failure_reason TEXT,
    created_at VARCHAR(64) NOT NULL,
    started_at VARCHAR(64),
    ended_at VARCHAR(64),
    INDEX idx_test_runs_project (tenant_id, project_id),
    INDEX idx_test_runs_status (tenant_id, status)
);

CREATE TABLE IF NOT EXISTS test_run_lanes (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    test_run_id VARCHAR(64) NOT NULL,
    namespace VARCHAR(128) NOT NULL,
    master_name VARCHAR(128) NOT NULL,
    worker_name VARCHAR(128) NOT NULL,
    service_account_name VARCHAR(128) NOT NULL,
    network_policy_name VARCHAR(128) NOT NULL,
    manifest_json JSON NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    destroyed_at VARCHAR(64),
    INDEX idx_lanes_run (test_run_id)
);

CREATE TABLE IF NOT EXISTS test_run_events (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    test_run_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    message TEXT NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_run_events_run (test_run_id, created_at)
);

CREATE TABLE IF NOT EXISTS locust_run_snapshots (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    run_id VARCHAR(64) NOT NULL,
    sample_time VARCHAR(64) NOT NULL,
    state VARCHAR(32) NOT NULL,
    user_count INT NOT NULL,
    worker_count INT NOT NULL,
    total_rps DOUBLE NOT NULL,
    total_fail_per_sec DOUBLE NOT NULL,
    fail_ratio DOUBLE NOT NULL,
    current_p50 DOUBLE NOT NULL,
    current_p95 DOUBLE NOT NULL,
    avg_response_time DOUBLE NOT NULL,
    INDEX idx_run_snapshots (run_id, sample_time),
    INDEX idx_tenant_run_snapshots (tenant_id, run_id, sample_time)
);

CREATE TABLE IF NOT EXISTS locust_request_stat_samples (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    run_id VARCHAR(64) NOT NULL,
    sample_time VARCHAR(64) NOT NULL,
    method VARCHAR(16) NOT NULL,
    name VARCHAR(1024) NOT NULL,
    num_requests INT NOT NULL,
    num_failures INT NOT NULL,
    current_rps DOUBLE NOT NULL,
    current_fail_per_sec DOUBLE NOT NULL,
    avg_response_time DOUBLE NOT NULL,
    median_response_time DOUBLE NOT NULL,
    min_response_time DOUBLE NOT NULL,
    max_response_time DOUBLE NOT NULL,
    p95 DOUBLE NOT NULL,
    p99 DOUBLE NOT NULL,
    avg_content_length DOUBLE NOT NULL,
    INDEX idx_request_samples (run_id, sample_time),
    INDEX idx_request_samples_name (run_id, method, name(255), sample_time)
);

CREATE TABLE IF NOT EXISTS locust_errors (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    run_id VARCHAR(64) NOT NULL,
    sample_time VARCHAR(64) NOT NULL,
    method VARCHAR(16) NOT NULL,
    name VARCHAR(1024) NOT NULL,
    error TEXT NOT NULL,
    occurrences INT NOT NULL,
    INDEX idx_locust_errors_run (run_id, sample_time)
);

CREATE TABLE IF NOT EXISTS locust_workers (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    run_id VARCHAR(64) NOT NULL,
    sample_time VARCHAR(64) NOT NULL,
    worker_id VARCHAR(128) NOT NULL,
    state VARCHAR(32) NOT NULL,
    user_count INT NOT NULL,
    cpu_usage DOUBLE NOT NULL,
    memory_usage DOUBLE NOT NULL,
    INDEX idx_locust_workers_run (run_id, sample_time)
);

CREATE TABLE IF NOT EXISTS artifact_objects (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    run_id VARCHAR(64),
    provider VARCHAR(64) NOT NULL,
    bucket VARCHAR(255) NOT NULL,
    object_key VARCHAR(1024) NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    checksum VARCHAR(128) NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_artifacts_run (run_id),
    INDEX idx_artifacts_project (tenant_id, project_id)
);

CREATE TABLE IF NOT EXISTS locust_report_summaries (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    run_id VARCHAR(64) NOT NULL UNIQUE,
    report_status VARCHAR(32) NOT NULL,
    html_artifact_id VARCHAR(64),
    requests_csv_artifact_id VARCHAR(64),
    failures_csv_artifact_id VARCHAR(64),
    exceptions_csv_artifact_id VARCHAR(64),
    history_csv_artifact_id VARCHAR(64),
    logs_artifact_id VARCHAR(64),
    total_requests INT NOT NULL,
    total_failures INT NOT NULL,
    avg_response_time DOUBLE NOT NULL,
    p95_response_time DOUBLE NOT NULL,
    p99_response_time DOUBLE NOT NULL,
    total_rps DOUBLE NOT NULL,
    fail_ratio DOUBLE NOT NULL,
    archived_at VARCHAR(64) NOT NULL,
    INDEX idx_reports_project (tenant_id, project_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    actor VARCHAR(128) NOT NULL,
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    detail_json JSON NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_audit_tenant_time (tenant_id, created_at)
);

CREATE TABLE IF NOT EXISTS baseline_runs (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64) NOT NULL,
    test_run_id VARCHAR(64) NOT NULL,
    ci_provider VARCHAR(64) NOT NULL,
    pipeline_id VARCHAR(128) NOT NULL,
    job_id VARCHAR(128) NOT NULL,
    commit_sha VARCHAR(128) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL,
    conclusion VARCHAR(32) NOT NULL,
    violations_json JSON NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    INDEX idx_baseline_project (tenant_id, project_id),
    INDEX idx_baseline_run (test_run_id)
);
