from __future__ import annotations

import csv
import io

from app.repositories.sqlite_repo import SQLiteRepository
from app.services.artifacts import ArtifactRepository


class ReportArchiver:
    def __init__(self, repo: SQLiteRepository, artifacts: ArtifactRepository, locust_report_fetcher=None):
        self.repo = repo
        self.artifacts = artifacts
        self.locust_report_fetcher = locust_report_fetcher

    def archive(self, run: dict) -> dict:
        snapshots = self.repo.run_snapshots(run["id"])
        stats = self.repo.latest_request_stats(run["id"])
        latest = snapshots[-1] if snapshots else None
        total_requests = sum(int(row["num_requests"]) for row in stats)
        total_failures = sum(int(row["num_failures"]) for row in stats)
        avg_response_time = latest["avg_response_time"] if latest else 0
        p95 = latest["current_p95"] if latest else 0
        p99 = p95 + 180 if latest else 0
        total_rps = latest["total_rps"] if latest else 0
        fail_ratio = latest["fail_ratio"] if latest else 0

        # Keep report object keys tenant/project/run scoped so OSS lifecycle
        # policies and future per-tenant export jobs can operate by prefix.
        base = f"loadtest-artifacts/tenants/{run['tenant_id']}/projects/{run['project_id']}/runs/{run['id']}"
        real_reports = self._fetch_real_reports(run)
        html_artifact = self._save(run, f"{base}/reports/report.html", real_reports.get("html") or self._html(run, latest, stats), "text/html")
        requests_artifact = self._save(run, f"{base}/reports/requests.csv", real_reports.get("requests_csv") or self._csv(stats), "text/csv")
        failures_artifact = self._save(run, f"{base}/reports/failures.csv", real_reports.get("failures_csv") or "method,name,error,occurrences\n", "text/csv")
        history_artifact = self._save(run, f"{base}/reports/history.csv", real_reports.get("history_csv") or self._csv(snapshots), "text/csv")
        logs_artifact = self._save(run, f"{base}/logs/master.log", f"Run {run['id']} archived\n", "text/plain")

        summary = self.repo.insert_report_summary(
            {
                "tenant_id": run["tenant_id"],
                "project_id": run["project_id"],
                "run_id": run["id"],
                "report_status": "archived",
                "html_artifact_id": html_artifact["id"],
                "requests_csv_artifact_id": requests_artifact["id"],
                "failures_csv_artifact_id": failures_artifact["id"],
                "history_csv_artifact_id": history_artifact["id"],
                "logs_artifact_id": logs_artifact["id"],
                "total_requests": total_requests,
                "total_failures": total_failures,
                "avg_response_time": avg_response_time,
                "p95_response_time": p95,
                "p99_response_time": p99,
                "total_rps": total_rps,
                "fail_ratio": fail_ratio,
            }
        )
        return summary

    def _fetch_real_reports(self, run: dict) -> dict[str, str]:
        if not self.locust_report_fetcher:
            return {}
        lane = self.repo.get_lane_by_run(run["id"])
        if not lane:
            return {}
        try:
            return self.locust_report_fetcher.fetch(run, lane["namespace"])
        except Exception:
            # Report archiving must not fail the stop flow just because the
            # master Service disappeared first; fall back to platform summaries.
            return {}

    def _save(self, run: dict, object_key: str, content: str, content_type: str) -> dict:
        artifact = self.artifacts.upload_text(object_key, content, content_type)
        artifact.update({"tenant_id": run["tenant_id"], "project_id": run["project_id"], "run_id": run["id"]})
        return self.repo.insert_artifact(artifact)

    def _csv(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def _html(self, run: dict, latest: dict | None, stats: list[dict]) -> str:
        rows = "".join(
            f"<tr><td>{row['method']}</td><td>{row['name']}</td><td>{row['num_requests']}</td><td>{row['num_failures']}</td><td>{row['avg_response_time']}</td></tr>"
            for row in stats
        )
        rps = latest["total_rps"] if latest else 0
        return f"""
<!doctype html>
<html>
<head><meta charset="utf-8"><title>LocustHub Report {run['id']}</title></head>
<body>
<h1>LocustHub Report</h1>
<p>Run: {run['id']}</p>
<p>Total RPS: {rps}</p>
<table border="1">
<thead><tr><th>Type</th><th>Name</th><th>Requests</th><th>Fails</th><th>Average</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body>
</html>
"""
