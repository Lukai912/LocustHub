from __future__ import annotations

from app.repositories.sqlite_repo import SQLiteRepository
from app.services.admission import AdmissionError, RunAdmissionController
from app.services.lane import LaneController
from app.services.metrics import LocustMetricsSimulator
from app.services.reports import ReportArchiver


class TestRunService:
    def __init__(
        self,
        repo: SQLiteRepository,
        admission: RunAdmissionController,
        lanes: LaneController,
        metrics: LocustMetricsSimulator,
        reports: ReportArchiver,
    ):
        self.repo = repo
        self.admission = admission
        self.lanes = lanes
        self.metrics = metrics
        self.reports = reports

    def start(self, run_id: str) -> dict:
        run = self.repo.get_by_id("test_runs", run_id)
        if not run:
            raise ValueError("Test run not found")

        self.repo.update_run_status(run_id, "VALIDATING")
        try:
            admission_policy = self.admission.validate(run)
        except AdmissionError as exc:
            return self.repo.update_run_status(run_id, "APPROVAL_PENDING", str(exc))

        self.repo.update_run_status(run_id, "LANE_CREATING")
        lane_run = {
            **run,
            "allowed_egress_ips": admission_policy.get("resolved_ips", []),
            "allowed_egress_ports": admission_policy.get("allowed_ports", []),
        }
        manifest = self.lanes.build_manifest(lane_run)
        self.repo.insert_lane(run, manifest)
        self.repo.update_run_status(run_id, "PROVISIONING")
        running = self.repo.update_run_status(run_id, "RUNNING")
        self.collect(run_id, samples=3)
        self.repo.audit(run["tenant_id"], "admin", "test_run.start", "test_run", run_id, {"manifest": manifest})
        return running

    def collect(self, run_id: str, samples: int = 1) -> list[dict]:
        run = self.repo.get_by_id("test_runs", run_id)
        if not run:
            raise ValueError("Test run not found")
        collected = []
        existing = len(self.repo.run_snapshots(run_id))
        lane = self.repo.get_lane_by_run(run_id)
        # The Locust API collector needs the concrete lane namespace because
        # deployments can be isolated per tenant or per run.
        sample_run = {**run, "lane_namespace": lane["namespace"]} if lane else run
        for index in range(samples):
            snapshot, stats, errors, workers = self.metrics.build_sample(sample_run, existing + index + 1)
            self.repo.insert_snapshot(snapshot, stats, errors, workers)
            collected.append(snapshot)
        return collected

    def stop(self, run_id: str) -> dict:
        run = self.repo.get_by_id("test_runs", run_id)
        if not run:
            raise ValueError("Test run not found")
        self.repo.update_run_status(run_id, "COLLECTING")
        self.collect(run_id, samples=1)
        self.repo.update_run_status(run_id, "ARCHIVING")
        summary = self.reports.archive(run)
        self.repo.update_run_status(run_id, "DESTROYING")
        lane = self.repo.get_lane_by_run(run_id)
        if lane:
            self.lanes.destroy(run_id, lane["namespace"])
        self.repo.destroy_lane(run_id)
        completed = self.repo.update_run_status(run_id, "COMPLETED")
        self.repo.audit(run["tenant_id"], "admin", "test_run.stop", "test_run", run_id, {"report": summary["id"]})
        return completed
