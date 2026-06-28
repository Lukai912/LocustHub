from __future__ import annotations

from pathlib import Path

from app.repositories.sqlite_repo import SQLiteRepository, new_id, now_iso


class MySQLRepository(SQLiteRepository):
    def init_schema(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "db" / "mysql_schema.sql"
        statements = [statement.strip() for statement in schema_path.read_text(encoding="utf-8").split(";") if statement.strip()]
        with self.db.connect() as conn:
            for statement in statements:
                conn.execute(statement)

    def update_quota(self, tenant_id: str, data: dict) -> dict:
        now = now_iso()
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO tenant_quotas (
                    tenant_id,
                    max_concurrent_runs,
                    max_workers_per_run,
                    max_total_workers,
                    max_users,
                    max_spawn_rate,
                    max_run_duration_seconds,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                    max_concurrent_runs = VALUES(max_concurrent_runs),
                    max_workers_per_run = VALUES(max_workers_per_run),
                    max_total_workers = VALUES(max_total_workers),
                    max_users = VALUES(max_users),
                    max_spawn_rate = VALUES(max_spawn_rate),
                    max_run_duration_seconds = VALUES(max_run_duration_seconds),
                    updated_at = VALUES(updated_at)
                """,
                (
                    tenant_id,
                    data["max_concurrent_runs"],
                    data["max_workers_per_run"],
                    data["max_total_workers"],
                    data["max_users"],
                    data["max_spawn_rate"],
                    data["max_run_duration_seconds"],
                    now,
                ),
            )
            return conn.execute("SELECT * FROM tenant_quotas WHERE tenant_id = ?", (tenant_id,)).fetchone()

    def insert_report_summary(self, item: dict) -> dict:
        record = {"id": new_id("report"), "archived_at": now_iso(), **item}
        values = (
            record["id"],
            record["tenant_id"],
            record["project_id"],
            record["run_id"],
            record["report_status"],
            record.get("html_artifact_id"),
            record.get("requests_csv_artifact_id"),
            record.get("failures_csv_artifact_id"),
            record.get("history_csv_artifact_id"),
            record.get("logs_artifact_id"),
            record["total_requests"],
            record["total_failures"],
            record["avg_response_time"],
            record["p95_response_time"],
            record["p99_response_time"],
            record["total_rps"],
            record["fail_ratio"],
            record["archived_at"],
        )
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO locust_report_summaries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                    id = VALUES(id),
                    tenant_id = VALUES(tenant_id),
                    project_id = VALUES(project_id),
                    report_status = VALUES(report_status),
                    html_artifact_id = VALUES(html_artifact_id),
                    requests_csv_artifact_id = VALUES(requests_csv_artifact_id),
                    failures_csv_artifact_id = VALUES(failures_csv_artifact_id),
                    history_csv_artifact_id = VALUES(history_csv_artifact_id),
                    logs_artifact_id = VALUES(logs_artifact_id),
                    total_requests = VALUES(total_requests),
                    total_failures = VALUES(total_failures),
                    avg_response_time = VALUES(avg_response_time),
                    p95_response_time = VALUES(p95_response_time),
                    p99_response_time = VALUES(p99_response_time),
                    total_rps = VALUES(total_rps),
                    fail_ratio = VALUES(fail_ratio),
                    archived_at = VALUES(archived_at)
                """,
                values,
            )
        return record
