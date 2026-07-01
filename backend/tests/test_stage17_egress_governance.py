from app.core.database import Database
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.admission import AdmissionError, DnsIpPolicy, RunAdmissionController
from app.services.lane import KubernetesManifestBuilder, LaneRuntimeConfig


def make_repo(tmp_path) -> SQLiteRepository:
    repo = SQLiteRepository(Database(tmp_path / "locusthub.db"))
    repo.init_schema()
    repo.seed_demo("dev-token")
    return repo


def test_admission_rejects_unapproved_target_port(tmp_path):
    repo = make_repo(tmp_path)
    run = {
        "id": "run-port",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "target_host": "http://jsonplaceholder.typicode.com",
        "worker_count": 1,
        "users": 5,
        "spawn_rate": 1,
        "run_time_seconds": 60,
    }

    try:
        RunAdmissionController(repo, DnsIpPolicy(resolver=lambda host: ["104.21.1.1"])).validate(run)
    except AdmissionError as exc:
        assert "port 80 is not approved" in str(exc)
    else:
        raise AssertionError("unapproved target port should be rejected")

    usage = repo.list_table("quota_usage_snapshots")[0]
    assert usage["decision"] == "rejected"
    assert "port 80 is not approved" in usage["reason"]


def test_admission_result_carries_resolved_egress_policy(tmp_path):
    repo = make_repo(tmp_path)
    run = {
        "id": "run-egress",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "target_host": "https://jsonplaceholder.typicode.com",
        "worker_count": 1,
        "users": 5,
        "spawn_rate": 1,
        "run_time_seconds": 60,
    }

    result = RunAdmissionController(repo, DnsIpPolicy(resolver=lambda host: ["104.21.1.1"])).validate(run)

    assert result["target_host"] == "jsonplaceholder.typicode.com"
    assert result["target_port"] == 443
    assert result["resolved_ips"] == ["104.21.1.1"]
    assert result["allowed_ports"] == [443]


def test_network_policy_uses_resolved_ip_blocks_and_target_ports():
    run = {
        "id": "run-policy",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "target_host": "https://jsonplaceholder.typicode.com",
        "worker_count": 1,
        "users": 5,
        "spawn_rate": 1,
        "run_time_seconds": 60,
        "allowed_egress_ips": ["104.21.1.1"],
        "allowed_egress_ports": [443],
    }

    resources = KubernetesManifestBuilder(LaneRuntimeConfig()).build_kubernetes_resources(run)
    policy = next(item for item in resources if item["kind"] == "NetworkPolicy")
    egress = policy["spec"]["egress"]

    assert {"ipBlock": {"cidr": "104.21.1.1/32"}} in egress[-1]["to"]
    assert egress[-1]["ports"] == [{"protocol": "TCP", "port": 443}]
