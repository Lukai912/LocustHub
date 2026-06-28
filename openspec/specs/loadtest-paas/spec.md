# Load Test PaaS Capability Spec

This is the accepted baseline capability spec for LocustHub. The detailed architecture document is archived at `docs/loadtest-paas-spec.md`.

## Requirement: Multi-tenant load test lanes

The system MUST support multiple tenants and projects. Each running TestRun MUST create an isolated temporary load test lane.

### Scenario: Start an approved load test

- GIVEN a tenant has sufficient quota
- AND the target is approved in the whitelist
- WHEN a user starts a TestRun
- THEN the system creates one Locust master and N Locust workers
- AND the system applies ServiceAccount, NetworkPolicy, and resource limits
- AND the TestRun status becomes RUNNING

## Requirement: Locust UI-compatible real-time metrics

The system MUST collect real-time metrics from each TestRun's Locust master.

### Scenario: View a running TestRun

- GIVEN a TestRun is RUNNING
- WHEN a user opens the run detail page
- THEN the user can view Statistics, Charts, Failures, Exceptions, Workers, Logs, and Download sections
- AND the fields are compatible with Locust UI semantics

## Requirement: Report archiving

The system MUST archive reports and artifacts before destroying runtime lane resources.

### Scenario: Complete a TestRun

- GIVEN a TestRun has finished
- WHEN the system enters ARCHIVING
- THEN HTML report, CSV files, logs, raw snapshots, and summary data are persisted
- AND runtime resources are destroyed only after successful archival

## Requirement: Security admission

The system MUST validate target whitelist, approval status, DNS/IP constraints, resource quota, traffic quota, and NetworkPolicy before creating a lane.

### Scenario: Target is not approved

- GIVEN a user starts a TestRun with an unapproved target
- WHEN Run Admission Controller validates the request
- THEN the TestRun does not create runtime resources
- AND the TestRun enters APPROVAL_PENDING or REJECTED

## Requirement: Extensible artifact storage

The system MUST use an ArtifactRepository abstraction for scripts, reports, CSV files, logs, and raw snapshots.

### Scenario: Default Aliyun OSS implementation

- GIVEN ArtifactRepository is configured with provider `aliyun_oss`
- WHEN a report is archived
- THEN artifacts are uploaded to Aliyun OSS
- AND MySQL stores provider, bucket, object key, file metadata, checksum, and archive status

## Requirement: CI performance baseline

The system SHOULD support CI-triggered performance baseline execution through the same TestRun engine.

### Scenario: CI creates a baseline run

- GIVEN a CI token has permission to create performance runs
- WHEN CI calls the baseline run API
- THEN the system creates a TestRun with source `ci`
- AND the final result includes pass, failed, or warning conclusion
