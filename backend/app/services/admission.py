from __future__ import annotations

from urllib.parse import urlparse

from app.repositories.sqlite_repo import SQLiteRepository


class AdmissionError(Exception):
    pass


class RunAdmissionController:
    def __init__(self, repo: SQLiteRepository):
        self.repo = repo

    def validate(self, run: dict) -> None:
        quota = self.repo.get_quota(run["tenant_id"])
        if quota is None:
            raise AdmissionError("Tenant quota is not configured")

        running = self.repo.count_running_runs(run["tenant_id"])
        if running >= quota["max_concurrent_runs"]:
            raise AdmissionError("Tenant concurrent run quota exceeded")

        if run["worker_count"] > quota["max_workers_per_run"]:
            raise AdmissionError("Worker count exceeds tenant quota")
        if run["users"] > quota["max_users"]:
            raise AdmissionError("Users exceeds tenant traffic quota")
        if run["spawn_rate"] > quota["max_spawn_rate"]:
            raise AdmissionError("Spawn rate exceeds tenant traffic quota")
        if run["run_time_seconds"] > quota["max_run_duration_seconds"]:
            raise AdmissionError("Run duration exceeds tenant quota")

        host = self._host(run["target_host"])
        targets = self.repo.approved_targets(run["tenant_id"], run["project_id"])
        if not any(target["value"] == host for target in targets):
            raise AdmissionError(f"Target {host} is not approved")

    def _host(self, target_host: str) -> str:
        parsed = urlparse(target_host)
        if parsed.hostname:
            return parsed.hostname
        return target_host.split("/")[0].split(":")[0]
