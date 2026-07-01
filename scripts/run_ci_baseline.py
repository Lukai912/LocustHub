#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a LocustHub CI performance baseline and exit non-zero on failure.")
    parser.add_argument("--api-base-url", required=True, help="LocustHub API base URL, for example https://host/api/v1.")
    parser.add_argument("--token", required=True, help="Bearer token for the CI user.")
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--test-plan-id", required=True)
    parser.add_argument("--baseline-profile-id", help="Optional LocustHub baseline profile id.")
    parser.add_argument("--ci-provider", default="local")
    parser.add_argument("--pipeline-id", default="local")
    parser.add_argument("--job-id", default="perf-baseline")
    parser.add_argument("--commit-sha", default="local")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--max-p95-ms", type=float, default=500)
    parser.add_argument("--max-fail-ratio", type=float, default=0.05)
    parser.add_argument("--min-total-rps", type=float)
    parser.add_argument("--output", default="ci-baseline-result.json", help="Path for the JSON result artifact.")
    parser.add_argument("--mock-response-json", help="Test-only JSON response that bypasses the HTTP call.")
    parser.add_argument("--capture-payload", help="Test-only path that records the JSON request payload.")
    return parser.parse_args()


def post_json(api_base_url: str, token: str, payload: dict) -> dict:
    url = f"{api_base_url.rstrip('/')}/ci/performance-runs"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    args = parse_args()
    payload = {
        "tenant_id": args.tenant_id,
        "project_id": args.project_id,
        "test_plan_id": args.test_plan_id,
        "ci_provider": args.ci_provider,
        "pipeline_id": args.pipeline_id,
        "job_id": args.job_id,
        "commit_sha": args.commit_sha,
        "branch": args.branch,
        "max_p95_ms": args.max_p95_ms,
        "max_fail_ratio": args.max_fail_ratio,
    }
    if args.baseline_profile_id:
        payload["baseline_profile_id"] = args.baseline_profile_id
    if args.min_total_rps is not None:
        payload["min_total_rps"] = args.min_total_rps
    if args.capture_payload:
        capture_path = Path(args.capture_payload)
        capture_path.parent.mkdir(parents=True, exist_ok=True)
        capture_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if args.mock_response_json:
        result = json.loads(args.mock_response_json)
    else:
        result = post_json(args.api_base_url, args.token, payload)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    conclusion = result.get("conclusion")
    print(f"LocustHub CI baseline {conclusion}: {output}")
    for violation in result.get("violations", []):
        print(
            f"- {violation['metric']} {violation['operator']} {violation['expected']} "
            f"(actual {violation['actual']})"
        )
    return 1 if conclusion == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
