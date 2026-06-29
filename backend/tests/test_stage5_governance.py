from app.core.database import Database
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.admission import AdmissionError, DnsIpPolicy, RunAdmissionController


def make_repo(tmp_path) -> SQLiteRepository:
    db = Database(tmp_path / "locusthub.db")
    repo = SQLiteRepository(db)
    repo.init_schema()
    repo.seed_demo("dev-token")
    return repo


def test_target_whitelist_request_creates_approval_record(tmp_path):
    repo = make_repo(tmp_path)

    target = repo.insert_target(
        {
            "tenant_id": "tenant-demo",
            "project_id": "project-demo",
            "target_type": "domain",
            "value": "api.example.com",
            "ports": [443],
            "environment": "test",
            "reason": "stage5 approval",
        }
    )

    approvals = repo.list_table("approval_requests")
    assert target["status"] == "pending"
    assert approvals[0]["resource_id"] == target["id"]
    assert approvals[0]["request_type"] == "target"
    assert approvals[0]["status"] == "pending"


def test_approval_request_approve_and_reject_update_target_status(tmp_path):
    repo = make_repo(tmp_path)
    target = repo.insert_target(
        {
            "tenant_id": "tenant-demo",
            "project_id": "project-demo",
            "target_type": "domain",
            "value": "api.example.com",
            "ports": [443],
            "environment": "test",
            "reason": "stage5 approval",
        }
    )
    approval = repo.list_table("approval_requests")[0]

    approved = repo.resolve_approval_request(approval["id"], "approved", actor="reviewer")

    assert approved["status"] == "approved"
    assert repo.get_by_id("target_whitelists", target["id"])["status"] == "approved"

    second = repo.insert_target(
        {
            "tenant_id": "tenant-demo",
            "project_id": "project-demo",
            "target_type": "domain",
            "value": "blocked.example.com",
            "ports": [443],
            "environment": "test",
            "reason": "stage5 rejection",
        }
    )
    rejected = repo.resolve_approval_request(repo.list_table("approval_requests")[-1]["id"], "rejected", actor="reviewer")

    assert rejected["status"] == "rejected"
    assert repo.get_by_id("target_whitelists", second["id"])["status"] == "rejected"


def test_admission_rejects_private_ip_targets_and_records_dns_snapshot(tmp_path):
    repo = make_repo(tmp_path)
    run = {
        "id": "run-private",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "target_host": "http://10.0.0.1",
        "worker_count": 1,
        "users": 5,
        "spawn_rate": 1,
        "run_time_seconds": 60,
    }
    repo.insert_target(
        {
            "tenant_id": "tenant-demo",
            "project_id": "project-demo",
            "target_type": "ip",
            "value": "10.0.0.1",
            "ports": [80],
            "environment": "test",
            "reason": "private ip should still be blocked",
        }
    )
    repo.approve_target(repo.list_table("target_whitelists")[-1]["id"])

    try:
        RunAdmissionController(repo, DnsIpPolicy(resolver=lambda host: ["10.0.0.1"])).validate(run)
    except AdmissionError as exc:
        assert "private or reserved" in str(exc)
    else:
        raise AssertionError("private IP target should be rejected")

    snapshots = repo.list_table("dns_resolution_snapshots")
    assert snapshots[0]["hostname"] == "10.0.0.1"
    assert "10.0.0.1" in snapshots[0]["resolved_ips_json"]
    assert snapshots[0]["risk_level"] == "blocked"


def test_admission_records_quota_usage_snapshot_for_approved_run(tmp_path):
    repo = make_repo(tmp_path)
    run = {
        "id": "run-approved",
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "target_host": "https://jsonplaceholder.typicode.com",
        "worker_count": 2,
        "users": 10,
        "spawn_rate": 2,
        "run_time_seconds": 60,
    }

    RunAdmissionController(repo, DnsIpPolicy(resolver=lambda host: ["104.21.1.1"])).validate(run)

    usage = repo.list_table("quota_usage_snapshots")[0]
    assert usage["test_run_id"] == "run-approved"
    assert usage["requested_workers"] == 2
    assert usage["requested_users"] == 10
    assert usage["decision"] == "approved"
