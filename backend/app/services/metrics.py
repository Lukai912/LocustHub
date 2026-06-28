from __future__ import annotations

from datetime import datetime, timezone


class LocustMetricsSimulator:
    def build_sample(self, run: dict, sequence: int) -> tuple[dict, list[dict], list[dict], list[dict]]:
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
