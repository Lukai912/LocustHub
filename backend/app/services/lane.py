from __future__ import annotations


class LaneController:
    def build_manifest(self, run: dict) -> dict:
        labels = {
            "app": "locusthub",
            "tenant-id": run["tenant_id"],
            "project-id": run["project_id"],
            "test-run-id": run["id"],
        }
        return {
            "namespace": f"lt-{run['tenant_id']}",
            "serviceAccount": {"name": f"{run['id']}-sa", "labels": labels},
            "master": {
                "name": f"{run['id']}-master",
                "image": "locustio/locust:latest",
                "command": [
                    "locust",
                    "--master",
                    "--headless",
                    "--expect-workers",
                    str(run["worker_count"]),
                    "--users",
                    str(run["users"]),
                    "--spawn-rate",
                    str(run["spawn_rate"]),
                    "--run-time",
                    f"{run['run_time_seconds']}s",
                    "--host",
                    run["target_host"],
                ],
                "labels": labels | {"component": "master"},
            },
            "workers": {
                "name": f"{run['id']}-worker",
                "replicas": run["worker_count"],
                "image": "locustio/locust:latest",
                "command": ["locust", "--worker", "--master-host", f"{run['id']}-master"],
                "labels": labels | {"component": "worker"},
            },
            "networkPolicy": {
                "name": f"{run['id']}-egress",
                "defaultDeny": True,
                "allowDns": True,
                "allowedTarget": run["target_host"],
            },
        }
