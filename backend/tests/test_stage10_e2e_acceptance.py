import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_acceptance_smoke_script_generates_final_report(tmp_path):
    output = tmp_path / "acceptance.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_acceptance_smoke.py",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["checks"]["health"]["status"] == "ok"
    assert report["checks"]["auth"]["username"] == "admin"
    assert report["checks"]["load_test"]["run_status"] == "COMPLETED"
    assert report["checks"]["load_test"]["total_rps"] > 0
    assert report["checks"]["report"]["report_status"] == "archived"
    assert report["checks"]["ci_baseline"]["conclusion"] in {"passed", "failed"}
    assert report["checks"]["deployment_package"]["ready"] is True


def test_final_runbook_links_operational_paths():
    runbook = (REPO_ROOT / "docs" / "full-deployment-runbook.md").read_text(encoding="utf-8")

    for expected in [
        "scripts/run_acceptance_smoke.py",
        "scripts/run_local.sh",
        "docker compose up --build",
        "helm upgrade --install",
        "ALIYUN_OSS_BUCKET",
        "scripts/run_ci_baseline.py",
    ]:
        assert expected in runbook

