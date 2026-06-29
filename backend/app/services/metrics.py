from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx


class LocustMetricsSimulator:
    def build_sample(self, run: dict, sequence: int) -> tuple[dict, list[dict], list[dict], list[dict]]:
        # The simulator emits the same storage shape as the real Locust API
        # collector so local development and frontend work do not need a cluster.
        user_count = min(run["users"], max(1, sequence * run["spawn_rate"]))
        rps = round(user_count * 1.8, 2)
        failures = 0 if sequence < 5 else round(user_count * 0.01, 2)
        p50 = 80 + sequence * 2
        p95 = p50 + 160
        snapshot = {
            "tenant_id": run["tenant_id"],
            "project_id": run["project_id"],
            "run_id": run["id"],
            "sample_time": datetime.now(timezone.utc).isoformat(),
            "state": "running",
            "user_count": user_count,
            "worker_count": run["worker_count"],
            "total_rps": rps,
            "total_fail_per_sec": failures,
            "fail_ratio": round(failures / rps, 4) if rps else 0,
            "current_p50": p50,
            "current_p95": p95,
            "avg_response_time": p50 + 30,
        }
        stats = [
            {
                "method": "GET",
                "name": "/",
                "num_requests": sequence * max(1, user_count),
                "num_failures": int(failures * sequence),
                "current_rps": rps,
                "current_fail_per_sec": failures,
                "avg_response_time": p50 + 30,
                "median_response_time": p50,
                "min_response_time": 8,
                "max_response_time": p95 + 220,
                "response_time_percentile_0.95": p95,
                "response_time_percentile_0.99": p95 + 180,
                "avg_content_length": 1024,
            },
            {
                "method": "POST",
                "name": "/api/orders",
                "num_requests": sequence * max(1, user_count // 2),
                "num_failures": int(failures),
                "current_rps": round(rps * 0.35, 2),
                "current_fail_per_sec": round(failures * 0.5, 2),
                "avg_response_time": p50 + 60,
                "median_response_time": p50 + 20,
                "min_response_time": 12,
                "max_response_time": p95 + 320,
                "response_time_percentile_0.95": p95 + 70,
                "response_time_percentile_0.99": p95 + 260,
                "avg_content_length": 2048,
            },
        ]
        errors = []
        if failures:
            errors.append(
                {
                    "method": "POST",
                    "name": "/api/orders",
                    "error": "Simulated 500 response",
                    "occurrences": int(failures),
                }
            )
        workers = [
            {
                "id": f"worker-{index + 1}",
                "state": "running",
                "user_count": user_count // run["worker_count"],
                "cpu_usage": min(95, 25 + sequence * 3 + index),
                "memory_usage": 256 + sequence * 5 + index * 10,
            }
            for index in range(run["worker_count"])
        ]
        return snapshot, stats, errors, workers

    def format_locust_stats(self, snapshot: dict | None, stats: list[dict], workers: list[dict]) -> dict:
        if snapshot is None:
            return {
                "stats": [],
                "errors": [],
                "total_rps": 0,
                "total_fail_per_sec": 0,
                "fail_ratio": 0,
                "user_count": 0,
                "worker_count": 0,
                "state": "missing",
            }
        converted = []
        for stat in stats:
            item = dict(stat)
            # Persisted columns use compact p95/p99 names, but the management UI
            # expects Locust's original response_time_percentile_* fields.
            item["response_time_percentile_0.95"] = item.pop("p95", item.get("response_time_percentile_0.95", 0))
            item["response_time_percentile_0.99"] = item.pop("p99", item.get("response_time_percentile_0.99", 0))
            converted.append(item)
        return {
            "stats": converted,
            "errors": [],
            "total_rps": snapshot["total_rps"],
            "total_fail_per_sec": snapshot["total_fail_per_sec"],
            "fail_ratio": snapshot["fail_ratio"],
            "current_response_time_percentiles": {
                "response_time_percentile_0.5": snapshot["current_p50"],
                "response_time_percentile_0.95": snapshot["current_p95"],
            },
            "state": snapshot["state"],
            "user_count": snapshot["user_count"],
            "worker_count": snapshot["worker_count"],
            "workers": workers,
        }


class LocustMasterApiClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds

    def get_stats(self) -> dict:
        response = httpx.get(urljoin(self.base_url, "stats/requests"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def get_report_html(self) -> str:
        response = httpx.get(urljoin(self.base_url, "stats/report"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text

    def get_requests_csv(self) -> str:
        response = httpx.get(urljoin(self.base_url, "stats/requests/csv"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text

    def get_failures_csv(self) -> str:
        response = httpx.get(urljoin(self.base_url, "stats/failures/csv"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text

    def get_history_csv(self) -> str:
        response = httpx.get(urljoin(self.base_url, "stats/requests_full_history/csv"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text


class LocustReportFetcher:
    def __init__(self, base_url_template: str, timeout_seconds: float = 5.0):
        self.base_url_template = base_url_template
        self.timeout_seconds = timeout_seconds

    def fetch(self, run: dict, namespace: str) -> dict[str, str]:
        # The namespace is read from the stored lane so tenant and run namespace
        # strategies both resolve to the correct in-cluster master Service.
        base_url = self.base_url_template.format(run_id=run["id"], tenant_id=run["tenant_id"], project_id=run["project_id"], namespace=namespace)
        client = LocustMasterApiClient(base_url, self.timeout_seconds)
        return {
            "html": client.get_report_html(),
            "requests_csv": client.get_requests_csv(),
            "failures_csv": client.get_failures_csv(),
            "history_csv": client.get_history_csv(),
        }


class LocustApiMetricsCollector(LocustMetricsSimulator):
    def __init__(self, base_url_template: str, timeout_seconds: float = 5.0):
        self.base_url_template = base_url_template
        self.timeout_seconds = timeout_seconds

    def build_sample(self, run: dict, sequence: int) -> tuple[dict, list[dict], list[dict], list[dict]]:
        # Prefer the persisted lane namespace so both tenant and run namespace
        # strategies resolve to the actual in-cluster Locust master Service.
        namespace = run.get("lane_namespace") or f"lt-{run['tenant_id']}"
        base_url = self.base_url_template.format(run_id=run["id"], tenant_id=run["tenant_id"], project_id=run["project_id"], namespace=namespace)
        payload = LocustMasterApiClient(base_url, self.timeout_seconds).get_stats()
        return self.from_locust_payload(run, payload)

    def from_locust_payload(self, run: dict, payload: dict) -> tuple[dict, list[dict], list[dict], list[dict]]:
        # Locust includes an "Aggregated" row for totals. Store endpoint rows
        # separately while using the aggregate row to populate run-level gauges.
        total_row = next((item for item in payload.get("stats", []) if item.get("name") == "Aggregated"), None)
        stat_rows = [item for item in payload.get("stats", []) if item.get("name") != "Aggregated"]
        if total_row is None and stat_rows:
            total_row = stat_rows[-1]
        total_row = total_row or {}
        percentiles = payload.get("current_response_time_percentiles", {})
        snapshot = {
            "tenant_id": run["tenant_id"],
            "project_id": run["project_id"],
            "run_id": run["id"],
            "sample_time": datetime.now(timezone.utc).isoformat(),
            "state": payload.get("state", "running"),
            "user_count": int(payload.get("user_count") or 0),
            "worker_count": int(payload.get("worker_count") or len(payload.get("workers", [])) or run["worker_count"]),
            "total_rps": float(payload.get("total_rps") or total_row.get("current_rps") or 0),
            "total_fail_per_sec": float(payload.get("total_fail_per_sec") or total_row.get("current_fail_per_sec") or 0),
            "fail_ratio": float(payload.get("fail_ratio") or 0),
            "current_p50": float(percentiles.get("response_time_percentile_0.5") or total_row.get("median_response_time") or 0),
            "current_p95": float(percentiles.get("response_time_percentile_0.95") or total_row.get("response_time_percentile_0.95") or 0),
            "avg_response_time": float(total_row.get("avg_response_time") or 0),
        }
        stats = [self._stat_from_locust(row) for row in stat_rows]
        errors = [
            {
                "method": error.get("method") or "",
                "name": error.get("name") or "",
                "error": error.get("error") or error.get("key") or "",
                "occurrences": int(error.get("occurrences") or 0),
            }
            for error in payload.get("errors", [])
        ]
        workers = [
            {
                "id": worker.get("id") or worker.get("client_id") or "worker",
                "state": worker.get("state") or "running",
                "user_count": int(worker.get("user_count") or 0),
                "cpu_usage": float(worker.get("cpu_usage") or 0),
                "memory_usage": float(worker.get("memory_usage") or 0),
            }
            for worker in payload.get("workers", [])
        ]
        return snapshot, stats, errors, workers

    def _stat_from_locust(self, row: dict) -> dict:
        return {
            "method": row.get("method") or "",
            "name": row.get("name") or "",
            "num_requests": int(row.get("num_requests") or 0),
            "num_failures": int(row.get("num_failures") or 0),
            "current_rps": float(row.get("current_rps") or 0),
            "current_fail_per_sec": float(row.get("current_fail_per_sec") or 0),
            "avg_response_time": float(row.get("avg_response_time") or 0),
            "median_response_time": float(row.get("median_response_time") or 0),
            "min_response_time": float(row.get("min_response_time") or 0),
            "max_response_time": float(row.get("max_response_time") or 0),
            "response_time_percentile_0.95": float(row.get("response_time_percentile_0.95") or 0),
            "response_time_percentile_0.99": float(row.get("response_time_percentile_0.99") or 0),
            "avg_content_length": float(row.get("avg_content_length") or 0),
        }
