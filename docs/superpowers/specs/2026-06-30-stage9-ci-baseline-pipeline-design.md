# Stage9 CI Baseline Pipeline Design

## Goal

Stage9 makes LocustHub usable from CI by adding configurable performance thresholds, a baseline result query endpoint, and a command-line client that exits with CI-friendly status codes.

## Approach

Extend the existing `/ci/performance-runs` endpoint instead of introducing a second CI workflow. The request carries threshold values; the API stores violations with the baseline run and exposes the result through a GET endpoint. A standard-library Python script calls the API, writes a JSON result file, and exits `1` when the baseline conclusion is `failed`.

## Components

- `BaselineRunCreate` threshold fields.
- `POST /api/v1/ci/performance-runs` threshold evaluation for p95, fail ratio, and optional minimum RPS.
- `GET /api/v1/ci/performance-runs/{test_run_id}/result` for polling or report collection.
- `scripts/run_ci_baseline.py` for GitHub Actions, GitLab CI, Jenkins, or local CI jobs.
- Stage9 documentation and acceptance evidence.

## Acceptance

Stage9 is accepted when API tests prove configurable pass/fail behavior, the result endpoint returns persisted violations, the CLI exits with correct codes, and the PR is merged to `main`.

