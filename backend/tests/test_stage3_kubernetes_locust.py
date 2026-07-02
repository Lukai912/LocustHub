import logging

from app.core.database import Database
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.artifacts import LocalArtifactRepository
import app.services.metrics as metrics_module
from app.services.lane import KubernetesLaneRuntime, KubernetesManifestBuilder, LaneRuntimeConfig
from app.services.metrics import LocustApiMetricsCollector
from app.services.reports import ReportArchiver


def test_kubernetes_manifest_builder_creates_locust_resources():
    run = {
        "id": "run-stage3",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "target_host": "https://jsonplaceholder.typicode.com",
        "users": 5,
        "spawn_rate": 1,
        "run_time_seconds": 60,
        "worker_count": 2,
    }
    builder = KubernetesManifestBuilder(LaneRuntimeConfig(backend="kubernetes", namespace_strategy="tenant"))

    resources = builder.build_kubernetes_resources(run)
    kinds = [resource["kind"] for resource in resources]

    assert "Namespace" in kinds
    assert "ServiceAccount" in kinds
    assert kinds.count("Deployment") == 2
    assert "Service" in kinds
    assert "NetworkPolicy" in kinds
    master = next(resource for resource in resources if resource["kind"] == "Deployment" and resource["metadata"]["name"] == "run-stage3-master")
    assert "--master" in master["spec"]["template"]["spec"]["containers"][0]["args"]
    workers = next(resource for resource in resources if resource["kind"] == "Deployment" and resource["metadata"]["name"] == "run-stage3-worker")
    assert workers["spec"]["replicas"] == 2


def test_lane_repository_persists_manifest_namespace_for_run_strategy(tmp_path):
    db = Database(tmp_path / "locusthub.db")
    repo = SQLiteRepository(db)
    repo.init_schema()
    run = {
        "id": "run-stage3",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "target_host": "https://jsonplaceholder.typicode.com",
        "users": 5,
        "spawn_rate": 1,
        "run_time_seconds": 60,
        "worker_count": 2,
    }
    manifest = KubernetesManifestBuilder(LaneRuntimeConfig(backend="kubernetes", namespace_strategy="run")).build_manifest(run)

    lane = repo.insert_lane(run, manifest)

    assert lane["namespace"] == "lt-tenant-demo-run-stage3"
    assert lane["network_policy_name"] == "run-stage3-default-deny"


class RecordingKubernetesLaneRuntime(KubernetesLaneRuntime):
    def __init__(self, builder: KubernetesManifestBuilder):
        super().__init__(builder)
        self.deleted = None

    def _delete_from_cluster(self, run_id: str, namespace: str, delete_namespace: bool) -> None:
        self.deleted = {"run_id": run_id, "namespace": namespace, "delete_namespace": delete_namespace}


def test_kubernetes_lane_runtime_deletes_cluster_resources_when_apply_enabled():
    builder = KubernetesManifestBuilder(
        LaneRuntimeConfig(backend="kubernetes", namespace_strategy="run", kubernetes_apply_enabled=True)
    )
    runtime = RecordingKubernetesLaneRuntime(builder)

    result = runtime.delete("run-stage3", "lt-tenant-demo-run-stage3")

    assert result["deleted"] is True
    assert result["namespace_deleted"] is True
    assert runtime.deleted == {
        "run_id": "run-stage3",
        "namespace": "lt-tenant-demo-run-stage3",
        "delete_namespace": True,
    }


def test_locust_payload_is_converted_to_platform_samples():
    run = {"id": "run-1", "tenant_id": "tenant-demo", "project_id": "project-demo", "worker_count": 1}
    payload = {
        "state": "running",
        "user_count": 5,
        "worker_count": 1,
        "total_rps": 12.5,
        "total_fail_per_sec": 0.1,
        "fail_ratio": 0.008,
        "current_response_time_percentiles": {
            "response_time_percentile_0.5": 80,
            "response_time_percentile_0.95": 220,
        },
        "stats": [
            {
                "method": "GET",
                "name": "/todos/1",
                "num_requests": 100,
                "num_failures": 1,
                "current_rps": 12.5,
                "current_fail_per_sec": 0.1,
                "avg_response_time": 95,
                "median_response_time": 80,
                "min_response_time": 20,
                "max_response_time": 330,
                "response_time_percentile_0.95": 220,
                "response_time_percentile_0.99": 300,
                "avg_content_length": 128,
            },
            {"name": "Aggregated", "avg_response_time": 95, "current_rps": 12.5},
        ],
        "workers": [{"id": "worker-1", "state": "running", "user_count": 5, "cpu_usage": 20, "memory_usage": 128}],
        "errors": [{"method": "GET", "name": "/todos/1", "error": "boom", "occurrences": 1}],
    }

    snapshot, stats, errors, workers = LocustApiMetricsCollector("http://locust").from_locust_payload(run, payload)

    assert snapshot["total_rps"] == 12.5
    assert snapshot["current_p95"] == 220
    assert stats[0]["name"] == "/todos/1"
    assert stats[0]["response_time_percentile_0.99"] == 300
    assert errors[0]["occurrences"] == 1
    assert workers[0]["id"] == "worker-1"


def test_locust_api_collector_uses_persisted_lane_namespace(monkeypatch):
    captured = {}

    class FakeLocustMasterApiClient:
        def __init__(self, base_url: str, timeout_seconds: float):
            captured["base_url"] = base_url
            captured["timeout_seconds"] = timeout_seconds

        def get_stats(self) -> dict:
            return {
                "stats": [{"name": "Aggregated", "current_rps": 1, "avg_response_time": 10}],
                "workers": [],
            }

    monkeypatch.setattr(metrics_module, "LocustMasterApiClient", FakeLocustMasterApiClient)
    run = {
        "id": "run-1",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "worker_count": 1,
        "lane_namespace": "lt-tenant-demo-run-1",
    }
    collector = LocustApiMetricsCollector("http://{run_id}-master.{namespace}.svc.cluster.local:8089", timeout_seconds=2)

    collector.build_sample(run, sequence=1)

    assert captured == {
        "base_url": "http://run-1-master.lt-tenant-demo-run-1.svc.cluster.local:8089",
        "timeout_seconds": 2,
    }


class FakeReportFetcher:
    def fetch(self, run: dict, namespace: str) -> dict[str, str]:
        assert namespace == "lt-tenant-demo"
        return {
            "html": "<html>real locust report</html>",
            "requests_csv": "method,name\nGET,/todos/1\n",
            "failures_csv": "method,name,error\n",
            "history_csv": "timestamp,rps\n",
        }


def test_report_archiver_prefers_real_locust_reports(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    db = Database(tmp_path / "locusthub.db")
    repo = SQLiteRepository(db)
    repo.init_schema()
    run = {
        "id": "run-report",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "test_plan_id": "plan-demo",
        "source": "manual",
        "status": "RUNNING",
        "target_host": "https://jsonplaceholder.typicode.com",
        "users": 5,
        "spawn_rate": 1,
        "run_time_seconds": 60,
        "worker_count": 1,
        "failure_reason": None,
        "created_at": "now",
        "started_at": "now",
        "ended_at": None,
    }
    repo.insert_lane(run, {"namespace": "lt-tenant-demo"})

    archiver = ReportArchiver(repo, LocalArtifactRepository(tmp_path / "artifacts"), FakeReportFetcher())
    summary = archiver.archive(run)

    assert summary["report_status"] == "archived"
    artifacts = repo.list_table("artifact_objects")
    html = next(item for item in artifacts if item["object_key"].endswith("locust-native/report.html"))
    assert summary["html_artifact_id"] == html["id"]
    report_file = tmp_path / "artifacts" / html["object_key"]
    assert "real locust report" in report_file.read_text(encoding="utf-8")
    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "locust_native_report_fetched run_id=run-report" in messages
    assert "archive_report_html_selected run_id=run-report report_source=locust_native" in messages
    assert "archive_artifact_saved run_id=run-report" in messages
    assert "archive_report_inputs run_id=run-report snapshots=0 request_stats=0" in messages
    assert "locust_native_report_payload run_id=run-report keys=" in messages
    assert "archive_artifact_payload run_id=run-report" in messages
