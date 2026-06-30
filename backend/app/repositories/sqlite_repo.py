from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.security import hash_password
from app.core.database import Database, row_to_dict, rows_to_dicts


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class SQLiteRepository:
    def __init__(self, db: Database):
        self.db = db

    def init_schema(self) -> None:
        schema = [
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                username TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                password_hash TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS script_versions (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                locustfile TEXT NOT NULL,
                requirements TEXT NOT NULL,
                artifact_key TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS test_plans (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                script_version_id TEXT NOT NULL,
                name TEXT NOT NULL,
                target_host TEXT NOT NULL,
                users INTEGER NOT NULL,
                spawn_rate INTEGER NOT NULL,
                run_time_seconds INTEGER NOT NULL,
                worker_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS target_whitelists (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                value TEXT NOT NULL,
                ports_json TEXT NOT NULL,
                environment TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT,
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS approval_requests (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                request_type TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT,
                requested_by TEXT NOT NULL,
                reviewed_by TEXT,
                reviewed_at TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS dns_resolution_snapshots (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                test_run_id TEXT NOT NULL,
                hostname TEXT NOT NULL,
                resolved_ips_json TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                risk_reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tenant_quotas (
                tenant_id TEXT PRIMARY KEY,
                max_concurrent_runs INTEGER NOT NULL,
                max_workers_per_run INTEGER NOT NULL,
                max_total_workers INTEGER NOT NULL,
                max_users INTEGER NOT NULL,
                max_spawn_rate INTEGER NOT NULL,
                max_run_duration_seconds INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS quota_usage_snapshots (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                test_run_id TEXT NOT NULL,
                requested_workers INTEGER NOT NULL,
                running_workers INTEGER NOT NULL,
                max_workers INTEGER NOT NULL,
                requested_users INTEGER NOT NULL,
                max_users INTEGER NOT NULL,
                requested_spawn_rate INTEGER NOT NULL,
                max_spawn_rate INTEGER NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS test_runs (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                test_plan_id TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                target_host TEXT NOT NULL,
                users INTEGER NOT NULL,
                spawn_rate INTEGER NOT NULL,
                run_time_seconds INTEGER NOT NULL,
                worker_count INTEGER NOT NULL,
                failure_reason TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS test_run_lanes (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                test_run_id TEXT NOT NULL,
                namespace TEXT NOT NULL,
                master_name TEXT NOT NULL,
                worker_name TEXT NOT NULL,
                service_account_name TEXT NOT NULL,
                network_policy_name TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                destroyed_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS locust_run_snapshots (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                sample_time TEXT NOT NULL,
                state TEXT NOT NULL,
                user_count INTEGER NOT NULL,
                worker_count INTEGER NOT NULL,
                total_rps REAL NOT NULL,
                total_fail_per_sec REAL NOT NULL,
                fail_ratio REAL NOT NULL,
                current_p50 REAL NOT NULL,
                current_p95 REAL NOT NULL,
                avg_response_time REAL NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS locust_request_stat_samples (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                sample_time TEXT NOT NULL,
                method TEXT NOT NULL,
                name TEXT NOT NULL,
                num_requests INTEGER NOT NULL,
                num_failures INTEGER NOT NULL,
                current_rps REAL NOT NULL,
                current_fail_per_sec REAL NOT NULL,
                avg_response_time REAL NOT NULL,
                median_response_time REAL NOT NULL,
                min_response_time REAL NOT NULL,
                max_response_time REAL NOT NULL,
                p95 REAL NOT NULL,
                p99 REAL NOT NULL,
                avg_content_length REAL NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS locust_errors (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                sample_time TEXT NOT NULL,
                method TEXT NOT NULL,
                name TEXT NOT NULL,
                error TEXT NOT NULL,
                occurrences INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS locust_workers (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                sample_time TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                state TEXT NOT NULL,
                user_count INTEGER NOT NULL,
                cpu_usage REAL NOT NULL,
                memory_usage REAL NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS artifact_objects (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                run_id TEXT,
                provider TEXT NOT NULL,
                bucket TEXT NOT NULL,
                object_key TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS locust_report_summaries (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                run_id TEXT NOT NULL UNIQUE,
                report_status TEXT NOT NULL,
                html_artifact_id TEXT,
                requests_csv_artifact_id TEXT,
                failures_csv_artifact_id TEXT,
                exceptions_csv_artifact_id TEXT,
                history_csv_artifact_id TEXT,
                logs_artifact_id TEXT,
                total_requests INTEGER NOT NULL,
                total_failures INTEGER NOT NULL,
                avg_response_time REAL NOT NULL,
                p95_response_time REAL NOT NULL,
                p99_response_time REAL NOT NULL,
                total_rps REAL NOT NULL,
                fail_ratio REAL NOT NULL,
                archived_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                detail_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS baseline_runs (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                test_run_id TEXT NOT NULL,
                ci_provider TEXT NOT NULL,
                pipeline_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                branch TEXT NOT NULL,
                status TEXT NOT NULL,
                conclusion TEXT NOT NULL,
                violations_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        ]
        with self.db.connect() as conn:
            for statement in schema:
                conn.execute(statement)
            columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
            if "password_hash" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            report_columns = [row[1] for row in conn.execute("PRAGMA table_info(locust_report_summaries)").fetchall()]
            if "exceptions_csv_artifact_id" not in report_columns:
                conn.execute("ALTER TABLE locust_report_summaries ADD COLUMN exceptions_csv_artifact_id TEXT")

    def seed_demo(self, token: str) -> None:
        with self.db.connect() as conn:
            exists = conn.execute("SELECT id FROM tenants LIMIT 1").fetchone()
            now = now_iso()
            tenant_id = "tenant-demo"
            admin_hash = hash_password("admin", "admin")
            viewer_hash = hash_password("viewer", "viewer")
            if exists:
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE username = 'admin' AND (password_hash IS NULL OR password_hash = '')",
                    (admin_hash,),
                )
                viewer = conn.execute("SELECT id FROM users WHERE id = ?", ("user-viewer",)).fetchone()
                if not viewer:
                    conn.execute(
                        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                        ("user-viewer", tenant_id, "viewer", f"{token}-viewer", "viewer", viewer_hash, now),
                    )
                return
            project_id = "project-demo"
            script_id = "script-demo"
            plan_id = "plan-demo"
            conn.execute(
                "INSERT INTO tenants VALUES (?, ?, ?, ?, ?)",
                (tenant_id, "Demo Tenant", "demo", "active", now),
            )
            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("user-admin", tenant_id, "admin", token, "admin", admin_hash, now),
            )
            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("user-viewer", tenant_id, "viewer", f"{token}-viewer", "viewer", viewer_hash, now),
            )
            conn.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)",
                (project_id, tenant_id, "Demo Project", "demo-project", "active", now),
            )
            conn.execute(
                "INSERT INTO script_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    script_id,
                    tenant_id,
                    project_id,
                    "JSONPlaceholder demo locustfile",
                    "from locust import HttpUser, task\n\nclass DemoUser(HttpUser):\n    @task\n    def todo(self):\n        self.client.get('/todos/1')\n",
                    "",
                    None,
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO test_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (plan_id, tenant_id, project_id, script_id, "JSONPlaceholder Demo Plan", "https://jsonplaceholder.typicode.com", 5, 1, 60, 1, "active", now),
            )
            conn.execute(
                "INSERT INTO target_whitelists VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("target-demo", tenant_id, project_id, "domain", "jsonplaceholder.typicode.com", json.dumps([443]), "test", "approved", "public fake API for low-rate MVP validation", "system", now, now),
            )
            conn.execute(
                "INSERT INTO tenant_quotas VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tenant_id, 5, 5, 10, 1000, 200, 3600, now),
            )

    def list_table(self, table: str) -> list[dict]:
        with self.db.connect() as conn:
            return rows_to_dicts(conn.execute(f"SELECT * FROM {table}").fetchall())

    def get_user_by_token(self, token: str) -> dict | None:
        with self.db.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone())

    def get_user_by_username(self, username: str) -> dict | None:
        with self.db.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone())

    def get_by_id(self, table: str, item_id: str) -> dict | None:
        with self.db.connect() as conn:
            return row_to_dict(conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone())

    def insert_tenant(self, data: dict) -> dict:
        item = {"id": new_id("tenant"), "status": "active", "created_at": now_iso(), **data}
        with self.db.connect() as conn:
            conn.execute("INSERT INTO tenants VALUES (?, ?, ?, ?, ?)", (item["id"], item["name"], item["slug"], item["status"], item["created_at"]))
            conn.execute("INSERT INTO tenant_quotas VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (item["id"], 5, 5, 10, 1000, 200, 3600, item["created_at"]))
        return item

    def insert_project(self, data: dict) -> dict:
        item = {"id": new_id("project"), "status": "active", "created_at": now_iso(), **data}
        with self.db.connect() as conn:
            conn.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", (item["id"], item["tenant_id"], item["name"], item["slug"], item["status"], item["created_at"]))
        return item

    def insert_script_version(self, data: dict, artifact_key: str | None = None) -> dict:
        item = {"id": new_id("script"), "artifact_key": artifact_key, "created_at": now_iso(), **data}
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO script_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (item["id"], item["tenant_id"], item["project_id"], item["name"], item["locustfile"], item["requirements"], item["artifact_key"], item["created_at"]),
            )
        return item

    def insert_test_plan(self, data: dict) -> dict:
        item = {"id": new_id("plan"), "status": "active", "created_at": now_iso(), **data}
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO test_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["tenant_id"],
                    item["project_id"],
                    item["script_version_id"],
                    item["name"],
                    item["target_host"],
                    item["users"],
                    item["spawn_rate"],
                    item["run_time_seconds"],
                    item["worker_count"],
                    item["status"],
                    item["created_at"],
                ),
            )
        return item

    def insert_target(self, data: dict) -> dict:
        item = {"id": new_id("target"), "status": "pending", "created_at": now_iso(), "approved_by": None, "approved_at": None, **data}
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO target_whitelists VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["tenant_id"],
                    item["project_id"],
                    item["target_type"],
                    item["value"],
                    json.dumps(item["ports"]),
                    item["environment"],
                    item["status"],
                    item["reason"],
                    item["approved_by"],
                    item["approved_at"],
                    item["created_at"],
                ),
            )
            approval = {
                "id": new_id("approval"),
                "tenant_id": item["tenant_id"],
                "project_id": item["project_id"],
                "request_type": "target",
                "resource_type": "target_whitelist",
                "resource_id": item["id"],
                "status": "pending",
                "reason": item["reason"],
                "requested_by": "admin",
                "reviewed_by": None,
                "reviewed_at": None,
                "created_at": item["created_at"],
            }
            conn.execute(
                "INSERT INTO approval_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    approval["id"],
                    approval["tenant_id"],
                    approval["project_id"],
                    approval["request_type"],
                    approval["resource_type"],
                    approval["resource_id"],
                    approval["status"],
                    approval["reason"],
                    approval["requested_by"],
                    approval["reviewed_by"],
                    approval["reviewed_at"],
                    approval["created_at"],
                ),
            )
        return item

    def approve_target(self, target_id: str, actor: str = "admin") -> dict | None:
        now = now_iso()
        with self.db.connect() as conn:
            conn.execute("UPDATE target_whitelists SET status = 'approved', approved_by = ?, approved_at = ? WHERE id = ?", (actor, now, target_id))
            conn.execute(
                "UPDATE approval_requests SET status = 'approved', reviewed_by = ?, reviewed_at = ? WHERE resource_type = 'target_whitelist' AND resource_id = ?",
                (actor, now, target_id),
            )
            return row_to_dict(conn.execute("SELECT * FROM target_whitelists WHERE id = ?", (target_id,)).fetchone())

    def resolve_approval_request(self, approval_id: str, status: str, actor: str = "admin") -> dict | None:
        if status not in {"approved", "rejected"}:
            raise ValueError("Approval status must be approved or rejected")
        now = now_iso()
        with self.db.connect() as conn:
            approval = row_to_dict(conn.execute("SELECT * FROM approval_requests WHERE id = ?", (approval_id,)).fetchone())
            if not approval:
                return None
            conn.execute("UPDATE approval_requests SET status = ?, reviewed_by = ?, reviewed_at = ? WHERE id = ?", (status, actor, now, approval_id))
            if approval["resource_type"] == "target_whitelist":
                if status == "approved":
                    conn.execute("UPDATE target_whitelists SET status = 'approved', approved_by = ?, approved_at = ? WHERE id = ?", (actor, now, approval["resource_id"]))
                else:
                    conn.execute("UPDATE target_whitelists SET status = 'rejected', approved_by = ?, approved_at = ? WHERE id = ?", (actor, now, approval["resource_id"]))
            return row_to_dict(conn.execute("SELECT * FROM approval_requests WHERE id = ?", (approval_id,)).fetchone())

    def update_quota(self, tenant_id: str, data: dict) -> dict:
        now = now_iso()
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO tenant_quotas VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id) DO UPDATE SET
                    max_concurrent_runs = excluded.max_concurrent_runs,
                    max_workers_per_run = excluded.max_workers_per_run,
                    max_total_workers = excluded.max_total_workers,
                    max_users = excluded.max_users,
                    max_spawn_rate = excluded.max_spawn_rate,
                    max_run_duration_seconds = excluded.max_run_duration_seconds,
                    updated_at = excluded.updated_at
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
            return row_to_dict(conn.execute("SELECT * FROM tenant_quotas WHERE tenant_id = ?", (tenant_id,)).fetchone())

    def create_run_from_plan(self, data: dict) -> dict:
        plan = self.get_by_id("test_plans", data["test_plan_id"])
        if not plan:
            raise ValueError("Test plan not found")
        item = {
            "id": new_id("run"),
            "tenant_id": data["tenant_id"],
            "project_id": data["project_id"],
            "test_plan_id": data["test_plan_id"],
            "source": data["source"],
            "status": "CREATED",
            "target_host": plan["target_host"],
            "users": plan["users"],
            "spawn_rate": plan["spawn_rate"],
            "run_time_seconds": plan["run_time_seconds"],
            "worker_count": plan["worker_count"],
            "failure_reason": None,
            "created_at": now_iso(),
            "started_at": None,
            "ended_at": None,
        }
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO test_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["tenant_id"],
                    item["project_id"],
                    item["test_plan_id"],
                    item["source"],
                    item["status"],
                    item["target_host"],
                    item["users"],
                    item["spawn_rate"],
                    item["run_time_seconds"],
                    item["worker_count"],
                    item["failure_reason"],
                    item["created_at"],
                    item["started_at"],
                    item["ended_at"],
                ),
            )
        return item

    def update_run_status(self, run_id: str, status: str, failure_reason: str | None = None) -> dict | None:
        now = now_iso()
        started_at = now if status == "RUNNING" else None
        ended_at = now if status in {"COMPLETED", "FAILED", "CANCELED"} else None
        with self.db.connect() as conn:
            if started_at:
                conn.execute("UPDATE test_runs SET status = ?, started_at = ?, failure_reason = ? WHERE id = ?", (status, started_at, failure_reason, run_id))
            elif ended_at:
                conn.execute("UPDATE test_runs SET status = ?, ended_at = ?, failure_reason = ? WHERE id = ?", (status, ended_at, failure_reason, run_id))
            else:
                conn.execute("UPDATE test_runs SET status = ?, failure_reason = COALESCE(?, failure_reason) WHERE id = ?", (status, failure_reason, run_id))
            return row_to_dict(conn.execute("SELECT * FROM test_runs WHERE id = ?", (run_id,)).fetchone())

    def count_running_runs(self, tenant_id: str) -> int:
        with self.db.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM test_runs WHERE tenant_id = ? AND status = 'RUNNING'", (tenant_id,)).fetchone()
            return int(row["c"])

    def get_quota(self, tenant_id: str) -> dict | None:
        with self.db.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM tenant_quotas WHERE tenant_id = ?", (tenant_id,)).fetchone())

    def approved_targets(self, tenant_id: str, project_id: str) -> list[dict]:
        with self.db.connect() as conn:
            return rows_to_dicts(
                conn.execute(
                    "SELECT * FROM target_whitelists WHERE tenant_id = ? AND project_id = ? AND status = 'approved'",
                    (tenant_id, project_id),
                ).fetchall()
            )

    def insert_dns_snapshot(self, run: dict, hostname: str, resolved_ips: list[str], risk_level: str, risk_reason: str) -> dict:
        item = {
            "id": new_id("dns"),
            "tenant_id": run["tenant_id"],
            "project_id": run["project_id"],
            "test_run_id": run["id"],
            "hostname": hostname,
            "resolved_ips_json": json.dumps(resolved_ips),
            "risk_level": risk_level,
            "risk_reason": risk_reason,
            "created_at": now_iso(),
        }
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO dns_resolution_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["tenant_id"],
                    item["project_id"],
                    item["test_run_id"],
                    item["hostname"],
                    item["resolved_ips_json"],
                    item["risk_level"],
                    item["risk_reason"],
                    item["created_at"],
                ),
            )
        return item

    def insert_quota_usage_snapshot(self, run: dict, quota: dict, running_workers: int, decision: str, reason: str | None = None) -> dict:
        item = {
            "id": new_id("quota-usage"),
            "tenant_id": run["tenant_id"],
            "project_id": run["project_id"],
            "test_run_id": run["id"],
            "requested_workers": run["worker_count"],
            "running_workers": running_workers,
            "max_workers": quota["max_total_workers"],
            "requested_users": run["users"],
            "max_users": quota["max_users"],
            "requested_spawn_rate": run["spawn_rate"],
            "max_spawn_rate": quota["max_spawn_rate"],
            "decision": decision,
            "reason": reason,
            "created_at": now_iso(),
        }
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO quota_usage_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["tenant_id"],
                    item["project_id"],
                    item["test_run_id"],
                    item["requested_workers"],
                    item["running_workers"],
                    item["max_workers"],
                    item["requested_users"],
                    item["max_users"],
                    item["requested_spawn_rate"],
                    item["max_spawn_rate"],
                    item["decision"],
                    item["reason"],
                    item["created_at"],
                ),
            )
        return item

    def insert_lane(self, run: dict, manifest: dict) -> dict:
        namespace = manifest.get("namespace", f"lt-{run['tenant_id']}")
        master = manifest.get("master", {})
        workers = manifest.get("workers", {})
        service_account = manifest.get("serviceAccount", {})
        network_policy = manifest.get("networkPolicy", {})
        item = {
            "id": new_id("lane"),
            "tenant_id": run["tenant_id"],
            "project_id": run["project_id"],
            "test_run_id": run["id"],
            "namespace": namespace,
            "master_name": master.get("name", f"{run['id']}-master"),
            "worker_name": workers.get("name", f"{run['id']}-worker"),
            "service_account_name": service_account.get("name", f"{run['id']}-sa"),
            "network_policy_name": network_policy.get("name", f"{run['id']}-default-deny"),
            "manifest_json": json.dumps(manifest),
            "status": "active",
            "created_at": now_iso(),
            "destroyed_at": None,
        }
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO test_run_lanes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["tenant_id"],
                    item["project_id"],
                    item["test_run_id"],
                    item["namespace"],
                    item["master_name"],
                    item["worker_name"],
                    item["service_account_name"],
                    item["network_policy_name"],
                    item["manifest_json"],
                    item["status"],
                    item["created_at"],
                    item["destroyed_at"],
                ),
            )
        return item

    def destroy_lane(self, run_id: str) -> None:
        with self.db.connect() as conn:
            conn.execute("UPDATE test_run_lanes SET status = 'destroyed', destroyed_at = ? WHERE test_run_id = ?", (now_iso(), run_id))

    def get_lane_by_run(self, run_id: str) -> dict | None:
        with self.db.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM test_run_lanes WHERE test_run_id = ? ORDER BY created_at DESC LIMIT 1", (run_id,)).fetchone())

    def insert_snapshot(self, snapshot: dict, stats: list[dict], errors: list[dict], workers: list[dict]) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO locust_run_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_id("snap"),
                    snapshot["tenant_id"],
                    snapshot["project_id"],
                    snapshot["run_id"],
                    snapshot["sample_time"],
                    snapshot["state"],
                    snapshot["user_count"],
                    snapshot["worker_count"],
                    snapshot["total_rps"],
                    snapshot["total_fail_per_sec"],
                    snapshot["fail_ratio"],
                    snapshot["current_p50"],
                    snapshot["current_p95"],
                    snapshot["avg_response_time"],
                ),
            )
            for stat in stats:
                conn.execute(
                    "INSERT INTO locust_request_stat_samples VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        new_id("req"),
                        snapshot["tenant_id"],
                        snapshot["project_id"],
                        snapshot["run_id"],
                        snapshot["sample_time"],
                        stat["method"],
                        stat["name"],
                        stat["num_requests"],
                        stat["num_failures"],
                        stat["current_rps"],
                        stat["current_fail_per_sec"],
                        stat["avg_response_time"],
                        stat["median_response_time"],
                        stat["min_response_time"],
                        stat["max_response_time"],
                        stat["response_time_percentile_0.95"],
                        stat["response_time_percentile_0.99"],
                        stat["avg_content_length"],
                    ),
                )
            for error in errors:
                conn.execute(
                    "INSERT INTO locust_errors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (new_id("err"), snapshot["tenant_id"], snapshot["project_id"], snapshot["run_id"], snapshot["sample_time"], error["method"], error["name"], error["error"], error["occurrences"]),
                )
            for worker in workers:
                conn.execute(
                    "INSERT INTO locust_workers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (new_id("wrk"), snapshot["tenant_id"], snapshot["project_id"], snapshot["run_id"], snapshot["sample_time"], worker["id"], worker["state"], worker["user_count"], worker["cpu_usage"], worker["memory_usage"]),
                )

    def run_snapshots(self, run_id: str) -> list[dict]:
        with self.db.connect() as conn:
            return rows_to_dicts(conn.execute("SELECT * FROM locust_run_snapshots WHERE run_id = ? ORDER BY sample_time", (run_id,)).fetchall())

    def latest_request_stats(self, run_id: str) -> list[dict]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT MAX(sample_time) AS sample_time FROM locust_request_stat_samples WHERE run_id = ?", (run_id,)).fetchone()
            if not row or not row["sample_time"]:
                return []
            return rows_to_dicts(conn.execute("SELECT * FROM locust_request_stat_samples WHERE run_id = ? AND sample_time = ?", (run_id, row["sample_time"])).fetchall())

    def latest_workers(self, run_id: str) -> list[dict]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT MAX(sample_time) AS sample_time FROM locust_workers WHERE run_id = ?", (run_id,)).fetchone()
            if not row or not row["sample_time"]:
                return []
            return rows_to_dicts(conn.execute("SELECT * FROM locust_workers WHERE run_id = ? AND sample_time = ?", (run_id, row["sample_time"])).fetchall())

    def latest_errors(self, run_id: str) -> list[dict]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT MAX(sample_time) AS sample_time FROM locust_errors WHERE run_id = ?", (run_id,)).fetchone()
            if not row or not row["sample_time"]:
                return []
            return rows_to_dicts(conn.execute("SELECT * FROM locust_errors WHERE run_id = ? AND sample_time = ?", (run_id, row["sample_time"])).fetchall())

    def insert_artifact(self, item: dict) -> dict:
        record = {"id": new_id("artifact"), "created_at": now_iso(), **item}
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO artifact_objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["id"],
                    record["tenant_id"],
                    record["project_id"],
                    record.get("run_id"),
                    record["provider"],
                    record["bucket"],
                    record["object_key"],
                    record["content_type"],
                    record["size_bytes"],
                    record["checksum"],
                    record["created_at"],
                ),
            )
        return record

    def get_artifact(self, artifact_id: str) -> dict | None:
        with self.db.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM artifact_objects WHERE id = ?", (artifact_id,)).fetchone())

    def insert_report_summary(self, item: dict) -> dict:
        record = {"id": new_id("report"), "archived_at": now_iso(), **item}
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO locust_report_summaries (
                    id,
                    tenant_id,
                    project_id,
                    run_id,
                    report_status,
                    html_artifact_id,
                    requests_csv_artifact_id,
                    failures_csv_artifact_id,
                    exceptions_csv_artifact_id,
                    history_csv_artifact_id,
                    logs_artifact_id,
                    total_requests,
                    total_failures,
                    avg_response_time,
                    p95_response_time,
                    p99_response_time,
                    total_rps,
                    fail_ratio,
                    archived_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["tenant_id"],
                    record["project_id"],
                    record["run_id"],
                    record["report_status"],
                    record.get("html_artifact_id"),
                    record.get("requests_csv_artifact_id"),
                    record.get("failures_csv_artifact_id"),
                    record.get("exceptions_csv_artifact_id"),
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
                ),
            )
        return record

    def get_report(self, run_id: str) -> dict | None:
        with self.db.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM locust_report_summaries WHERE run_id = ?", (run_id,)).fetchone())

    def insert_baseline_run(self, item: dict) -> dict:
        record = {"id": new_id("baseline"), "created_at": now_iso(), **item}
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO baseline_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["id"],
                    record["tenant_id"],
                    record["project_id"],
                    record["test_run_id"],
                    record["ci_provider"],
                    record["pipeline_id"],
                    record["job_id"],
                    record["commit_sha"],
                    record["branch"],
                    record["status"],
                    record["conclusion"],
                    json.dumps(record["violations"]),
                    record["created_at"],
                ),
            )
        return record

    def get_baseline_by_run(self, test_run_id: str) -> dict | None:
        with self.db.connect() as conn:
            record = row_to_dict(conn.execute("SELECT * FROM baseline_runs WHERE test_run_id = ?", (test_run_id,)).fetchone())
        if record and isinstance(record.get("violations_json"), str):
            record["violations"] = json.loads(record["violations_json"])
        return record

    def audit(self, tenant_id: str, actor: str, action: str, resource_type: str, resource_id: str, detail: dict) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id("audit"), tenant_id, actor, action, resource_type, resource_id, json.dumps(detail), now_iso()),
            )
