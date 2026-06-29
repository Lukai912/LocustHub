from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from app.repositories.sqlite_repo import SQLiteRepository


class AdmissionError(Exception):
    pass


@dataclass
class DnsIpPolicy:
    resolver: object | None = None

    def resolve(self, host: str) -> list[str]:
        if self.resolver:
            return list(self.resolver(host))
        try:
            # getaddrinfo is used only at admission time to snapshot the target
            # boundary before Kubernetes resources are created.
            return sorted({item[4][0] for item in socket.getaddrinfo(host, None)})
        except socket.gaierror:
            return []

    def assess(self, host: str, allow_unresolved: bool = False) -> tuple[list[str], str, str]:
        resolved_ips = self.resolve(host)
        if not resolved_ips:
            if allow_unresolved:
                return [], "warning", "System-approved target DNS did not resolve in the local environment"
            return [], "blocked", "Target DNS did not resolve"
        for value in resolved_ips:
            ip = ipaddress.ip_address(value)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return resolved_ips, "blocked", f"Target resolves to private or reserved IP {value}"
        return resolved_ips, "allowed", "Target DNS/IP policy passed"


class RunAdmissionController:
    def __init__(self, repo: SQLiteRepository, dns_policy: DnsIpPolicy | None = None):
        self.repo = repo
        self.dns_policy = dns_policy or DnsIpPolicy()

    def validate(self, run: dict) -> None:
        quota = self.repo.get_quota(run["tenant_id"])
        if quota is None:
            raise AdmissionError("Tenant quota is not configured")

        running = self.repo.count_running_runs(run["tenant_id"])
        running_workers = running * quota["max_workers_per_run"]
        if running >= quota["max_concurrent_runs"]:
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", "Tenant concurrent run quota exceeded")
            raise AdmissionError("Tenant concurrent run quota exceeded")

        if run["worker_count"] > quota["max_workers_per_run"]:
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", "Worker count exceeds tenant quota")
            raise AdmissionError("Worker count exceeds tenant quota")
        if running_workers + run["worker_count"] > quota["max_total_workers"]:
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", "Total worker quota exceeded")
            raise AdmissionError("Total worker quota exceeded")
        if run["users"] > quota["max_users"]:
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", "Users exceeds tenant traffic quota")
            raise AdmissionError("Users exceeds tenant traffic quota")
        if run["spawn_rate"] > quota["max_spawn_rate"]:
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", "Spawn rate exceeds tenant traffic quota")
            raise AdmissionError("Spawn rate exceeds tenant traffic quota")
        if run["run_time_seconds"] > quota["max_run_duration_seconds"]:
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", "Run duration exceeds tenant quota")
            raise AdmissionError("Run duration exceeds tenant quota")

        host = self._host(run["target_host"])
        targets = self.repo.approved_targets(run["tenant_id"], run["project_id"])
        approved_target = next((target for target in targets if target["value"] == host), None)
        if not approved_target:
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", f"Target {host} is not approved")
            raise AdmissionError(f"Target {host} is not approved")

        # System-seeded demo targets must keep the local MVP usable even when
        # the developer machine cannot resolve public DNS. Explicit private or
        # reserved IPs are still blocked below.
        resolved_ips, risk_level, risk_reason = self.dns_policy.assess(host, allow_unresolved=approved_target.get("approved_by") == "system")
        self.repo.insert_dns_snapshot(run, host, resolved_ips, risk_level, risk_reason)
        if risk_level == "blocked":
            self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "rejected", risk_reason)
            raise AdmissionError(risk_reason)
        self.repo.insert_quota_usage_snapshot(run, quota, running_workers, "approved")

    def _host(self, target_host: str) -> str:
        parsed = urlparse(target_host)
        if parsed.hostname:
            return parsed.hostname
        return target_host.split("/")[0].split(":")[0]
