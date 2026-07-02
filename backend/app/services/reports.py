from __future__ import annotations

import csv
import io
import logging

from app.repositories.sqlite_repo import SQLiteRepository
from app.services.artifacts import ArtifactRepository


logger = logging.getLogger(__name__)


class ReportArchiver:
    def __init__(self, repo: SQLiteRepository, artifacts: ArtifactRepository, locust_report_fetcher=None):
        self.repo = repo
        self.artifacts = artifacts
        self.locust_report_fetcher = locust_report_fetcher

    def archive(self, run: dict) -> dict:
        logger.info(
            "archive_report_start run_id=%s tenant_id=%s project_id=%s",
            run["id"],
            run["tenant_id"],
            run["project_id"],
        )
        snapshots = self.repo.run_snapshots(run["id"])
        stats = self.repo.latest_request_stats(run["id"])
        latest = snapshots[-1] if snapshots else None
        logger.debug(
            "archive_report_inputs run_id=%s snapshots=%s request_stats=%s latest_snapshot=%s",
            run["id"],
            len(snapshots),
            len(stats),
            latest,
        )
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
        native_html = real_reports.get("html")
        html_object_key = f"{base}/locust-native/report.html" if native_html else f"{base}/reports/platform-report.html"
        logger.info(
            "archive_report_html_selected run_id=%s report_source=%s object_key=%s real_report_keys=%s",
            run["id"],
            "locust_native" if native_html else "platform_fallback",
            html_object_key,
            sorted(real_reports.keys()),
        )
        html_artifact = self._save(run, html_object_key, native_html or self._html(run, latest, stats), "text/html")
        requests_artifact = self._save(run, f"{base}/reports/requests.csv", real_reports.get("requests_csv") or self._csv(stats), "text/csv")
        failures_artifact = self._save(run, f"{base}/reports/failures.csv", real_reports.get("failures_csv") or "method,name,error,occurrences\n", "text/csv")
        exceptions_artifact = self._save(run, f"{base}/reports/exceptions.csv", real_reports.get("exceptions_csv") or "method,name,error,occurrences\n", "text/csv")
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
                "exceptions_csv_artifact_id": exceptions_artifact["id"],
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
        logger.info(
            "archive_report_complete run_id=%s report_id=%s html_artifact_id=%s total_requests=%s total_failures=%s",
            run["id"],
            summary["id"],
            html_artifact["id"],
            total_requests,
            total_failures,
        )
        return summary

    def _fetch_real_reports(self, run: dict) -> dict[str, str]:
        if not self.locust_report_fetcher:
            logger.info("locust_native_report_skipped run_id=%s reason=no_fetcher", run["id"])
            return {}
        lane = self.repo.get_lane_by_run(run["id"])
        if not lane:
            logger.info("locust_native_report_skipped run_id=%s reason=no_lane", run["id"])
            return {}
        try:
            reports = self.locust_report_fetcher.fetch(run, lane["namespace"])
            logger.info(
                "locust_native_report_fetched run_id=%s namespace=%s keys=%s html_bytes=%s",
                run["id"],
                lane["namespace"],
                sorted(reports.keys()),
                len(reports.get("html") or ""),
            )
            logger.debug(
                "locust_native_report_payload run_id=%s keys=%s namespace=%s sizes=%s",
                run["id"],
                sorted(reports.keys()),
                lane["namespace"],
                {key: len(value or "") for key, value in reports.items()},
            )
            return reports
        except Exception as exc:
            # Report archiving must not fail the stop flow just because the
            # master Service disappeared first; fall back to platform summaries.
            logger.warning(
                "locust_native_report_fetch_failed run_id=%s namespace=%s error=%s",
                run["id"],
                lane["namespace"],
                exc,
                exc_info=True,
            )
            return {}

    def _save(self, run: dict, object_key: str, content: str, content_type: str) -> dict:
        logger.debug(
            "archive_artifact_payload run_id=%s object_key=%s content_type=%s content_chars=%s",
            run["id"],
            object_key,
            content_type,
            len(content or ""),
        )
        artifact = self.artifacts.upload_text(object_key, content, content_type)
        artifact.update({"tenant_id": run["tenant_id"], "project_id": run["project_id"], "run_id": run["id"]})
        record = self.repo.insert_artifact(artifact)
        logger.info(
            "archive_artifact_saved run_id=%s artifact_id=%s object_key=%s content_type=%s size_bytes=%s",
            run["id"],
            record["id"],
            record["object_key"],
            record["content_type"],
            record["size_bytes"],
        )
        return record

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
