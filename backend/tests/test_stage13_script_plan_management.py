from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


AUTH = {"Authorization": "Bearer dev-token"}


def make_client(monkeypatch, tmp_path) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "locusthub.db"))
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    client = TestClient(create_app())
    get_settings.cache_clear()
    return client


def test_locustfile_validation_reports_user_class_and_tasks(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    locustfile = """
from locust import HttpUser, task

class DemoUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")
"""

    response = client.post("/api/v1/scripts/validate", headers=AUTH, json={"locustfile": locustfile})

    assert response.status_code == 200
    assert response.json() == {"valid": True, "user_class_found": True, "task_count": 1, "errors": []}


def test_locustfile_validation_rejects_missing_http_user(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.post("/api/v1/scripts/validate", headers=AUTH, json={"locustfile": "print('hello')"})

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert "HttpUser" in body["errors"][0]


def test_test_plan_clone_creates_reusable_plan(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    cloned = client.post("/api/v1/test-plans/plan-demo/clone", headers=AUTH, json={"name": "Demo Plan Copy"})

    assert cloned.status_code == 200
    plan = cloned.json()
    assert plan["id"] != "plan-demo"
    assert plan["name"] == "Demo Plan Copy"
    assert plan["target_host"] == "https://jsonplaceholder.typicode.com"

    run = client.post(
        "/api/v1/test-runs",
        headers=AUTH,
        json={"tenant_id": plan["tenant_id"], "project_id": plan["project_id"], "test_plan_id": plan["id"], "source": "manual"},
    )
    assert run.status_code == 200
    assert run.json()["test_plan_id"] == plan["id"]


def test_created_script_version_appears_in_script_list(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    payload = {
        "tenant_id": "tenant-demo",
        "project_id": "project-demo",
        "name": "Checkout flow",
        "locustfile": "from locust import HttpUser, task\nclass U(HttpUser):\n    @task\n    def t(self): pass\n",
        "requirements": "",
    }

    created = client.post("/api/v1/scripts", headers=AUTH, json=payload)
    listed = client.get("/api/v1/scripts", headers=AUTH)

    assert created.status_code == 200
    assert listed.status_code == 200
    assert any(item["id"] == created.json()["id"] for item in listed.json())
