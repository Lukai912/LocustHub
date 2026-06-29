from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LaneRuntimeConfig:
    backend: str = "local"
    namespace_strategy: str = "tenant"
    kubernetes_apply_enabled: bool = False
    locust_image: str = "locustio/locust:latest"
    master_web_port: int = 8089
    master_bind_port: int = 5557
    master_bind_port_plus_one: int = 5558


class KubernetesManifestBuilder:
    def __init__(self, config: LaneRuntimeConfig):
        self.config = config

    def namespace_for(self, run: dict) -> str:
        # Tenant namespaces match the "lane" model and allow multiple runs to
        # share quota and policy boundaries; run namespaces are easier to delete
        # wholesale in isolated test environments.
        if self.config.namespace_strategy == "run":
            return f"lt-{run['tenant_id']}-{run['id']}"
        return f"lt-{run['tenant_id']}"

    def build_manifest(self, run: dict) -> dict:
        namespace = self.namespace_for(run)
        labels = {
            "app": "locusthub",
            "tenant-id": run["tenant_id"],
            "project-id": run["project_id"],
            "test-run-id": run["id"],
        }
        return {
            "namespace": namespace,
            "serviceAccount": {"name": f"{run['id']}-sa", "labels": labels},
            "master": {
                "name": f"{run['id']}-master",
                "image": self.config.locust_image,
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
                "webPort": self.config.master_web_port,
                "bindPorts": [self.config.master_bind_port, self.config.master_bind_port_plus_one],
                "labels": labels | {"component": "master"},
            },
            "workers": {
                "name": f"{run['id']}-worker",
                "replicas": run["worker_count"],
                "image": self.config.locust_image,
                "command": ["locust", "--worker", "--master-host", f"{run['id']}-master"],
                "labels": labels | {"component": "worker"},
            },
            "networkPolicy": {
                "name": f"{run['id']}-default-deny",
                "defaultDeny": True,
                "allowDns": True,
                "allowedTarget": run["target_host"],
            },
        }

    def build_kubernetes_resources(self, run: dict) -> list[dict]:
        manifest = self.build_manifest(run)
        namespace = manifest["namespace"]
        labels = {
            "app": "locusthub",
            "tenant-id": run["tenant_id"],
            "project-id": run["project_id"],
            "test-run-id": run["id"],
        }
        service_account_name = manifest["serviceAccount"]["name"]
        master_name = manifest["master"]["name"]
        worker_name = manifest["workers"]["name"]
        # Keep this as plain Kubernetes dictionaries instead of YAML strings so
        # tests can assert resource semantics and the runtime can apply/delete
        # the same object model later.
        return [
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": namespace, "labels": {"locusthub.io/tenant-id": run["tenant_id"]}},
            },
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {"name": service_account_name, "namespace": namespace, "labels": labels},
            },
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": f"{run['id']}-config", "namespace": namespace, "labels": labels},
                "data": {"LOCUST_HOST": run["target_host"]},
            },
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": master_name, "namespace": namespace, "labels": labels | {"component": "master"}},
                "spec": {
                    "replicas": 1,
                    "selector": {"matchLabels": labels | {"component": "master"}},
                    "template": {
                        "metadata": {"labels": labels | {"component": "master"}},
                        "spec": {
                            "serviceAccountName": service_account_name,
                            "containers": [
                                {
                                    "name": "locust-master",
                                    "image": manifest["master"]["image"],
                                    "args": manifest["master"]["command"][1:],
                                    "ports": [
                                        {"containerPort": self.config.master_web_port, "name": "web"},
                                        {"containerPort": self.config.master_bind_port, "name": "master"},
                                        {"containerPort": self.config.master_bind_port_plus_one, "name": "master-plus"},
                                    ],
                                }
                            ],
                        },
                    },
                },
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": master_name, "namespace": namespace, "labels": labels | {"component": "master"}},
                "spec": {
                    "selector": labels | {"component": "master"},
                    "ports": [
                        {"name": "web", "port": self.config.master_web_port, "targetPort": "web"},
                        {"name": "master", "port": self.config.master_bind_port, "targetPort": "master"},
                        {"name": "master-plus", "port": self.config.master_bind_port_plus_one, "targetPort": "master-plus"},
                    ],
                },
            },
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": worker_name, "namespace": namespace, "labels": labels | {"component": "worker"}},
                "spec": {
                    "replicas": run["worker_count"],
                    "selector": {"matchLabels": labels | {"component": "worker"}},
                    "template": {
                        "metadata": {"labels": labels | {"component": "worker"}},
                        "spec": {
                            "serviceAccountName": service_account_name,
                            "containers": [
                                {
                                    "name": "locust-worker",
                                    "image": manifest["workers"]["image"],
                                    "args": manifest["workers"]["command"][1:],
                                }
                            ],
                        },
                    },
                },
            },
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {"name": manifest["networkPolicy"]["name"], "namespace": namespace, "labels": labels},
                "spec": {
                    "podSelector": {"matchLabels": {"test-run-id": run["id"]}},
                    "policyTypes": ["Egress", "Ingress"],
                    "ingress": [
                        {
                            "from": [{"podSelector": {"matchLabels": {"test-run-id": run["id"]}}}],
                        }
                    ],
                    "egress": [
                        {
                            "to": [{"podSelector": {"matchLabels": {"test-run-id": run["id"]}}}],
                        },
                        {
                            # DNS is required before stricter FQDN/IP egress
                            # controls are added in the governance phase.
                            "ports": [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}],
                        },
                    ],
                },
            },
        ]


class KubernetesLaneRuntime:
    def __init__(self, builder: KubernetesManifestBuilder):
        self.builder = builder

    def apply(self, run: dict) -> dict:
        resources = self.builder.build_kubernetes_resources(run)
        # The same code path supports dry-run style manifest inspection and
        # real cluster application; local tests keep apply disabled.
        if self.builder.config.kubernetes_apply_enabled:
            self._apply_to_cluster(resources)
        return {"backend": "kubernetes", "resources": resources}

    def delete(self, run_id: str, namespace: str) -> dict:
        # Tenant namespaces may contain several active runs, so only task-owned
        # resources are removed. Run namespaces are safe to delete wholesale.
        namespace_deleted = self.builder.config.namespace_strategy == "run"
        if self.builder.config.kubernetes_apply_enabled:
            self._delete_from_cluster(run_id, namespace, delete_namespace=namespace_deleted)
        return {
            "backend": "kubernetes",
            "deleted": True,
            "run_id": run_id,
            "namespace": namespace,
            "namespace_deleted": namespace_deleted,
        }

    def _apply_to_cluster(self, resources: list[dict]) -> None:
        # Lazy import keeps the local MVP usable without Kubernetes packages
        # unless the operator explicitly enables cluster apply.
        try:
            from kubernetes import client, config, utils
        except ImportError as exc:
            raise RuntimeError("kubernetes package is required when KUBERNETES_APPLY_ENABLED=true") from exc

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        api_client = client.ApiClient()
        for resource in resources:
            utils.create_from_dict(api_client, resource, verbose=False)

    def _delete_from_cluster(self, run_id: str, namespace: str, delete_namespace: bool) -> None:
        # Delete operations are idempotent because stop/report archival may be
        # retried after partial failures.
        try:
            from kubernetes import client, config
            from kubernetes.client.exceptions import ApiException
        except ImportError as exc:
            raise RuntimeError("kubernetes package is required when KUBERNETES_APPLY_ENABLED=true") from exc

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        apps = client.AppsV1Api()
        core = client.CoreV1Api()
        networking = client.NetworkingV1Api()
        body = client.V1DeleteOptions()

        def ignore_missing(action):
            try:
                action()
            except ApiException as exc:
                if exc.status != 404:
                    raise

        ignore_missing(lambda: apps.delete_namespaced_deployment(f"{run_id}-master", namespace, body=body))
        ignore_missing(lambda: apps.delete_namespaced_deployment(f"{run_id}-worker", namespace, body=body))
        ignore_missing(lambda: core.delete_namespaced_service(f"{run_id}-master", namespace, body=body))
        ignore_missing(lambda: core.delete_namespaced_config_map(f"{run_id}-config", namespace, body=body))
        ignore_missing(lambda: core.delete_namespaced_service_account(f"{run_id}-sa", namespace, body=body))
        ignore_missing(lambda: networking.delete_namespaced_network_policy(f"{run_id}-default-deny", namespace, body=body))
        if delete_namespace:
            ignore_missing(lambda: core.delete_namespace(namespace, body=body))


class LaneController:
    def __init__(self, config: LaneRuntimeConfig | None = None):
        self.config = config or LaneRuntimeConfig()
        self.builder = KubernetesManifestBuilder(self.config)
        self.runtime = KubernetesLaneRuntime(self.builder)

    def build_manifest(self, run: dict) -> dict:
        manifest = self.builder.build_manifest(run)
        if self.config.backend == "kubernetes":
            manifest["kubernetes"] = self.runtime.apply(run)
        return manifest

    def destroy(self, run_id: str, namespace: str) -> dict:
        if self.config.backend == "kubernetes":
            return self.runtime.delete(run_id, namespace)
        return {"backend": "local", "deleted": True, "run_id": run_id, "namespace": namespace}
