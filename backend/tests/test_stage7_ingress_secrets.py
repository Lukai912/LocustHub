from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read_repo_file(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_helm_values_expose_ingress_tls_and_secret_configuration():
    values = read_repo_file("deploy/helm/locusthub/values.yaml")

    for expected in [
        "ingress:",
        "enabled: true",
        "className:",
        "host: locusthub.example.com",
        "tls:",
        "secretName: locusthub-tls",
        "secret:",
        "existingSecret:",
        "MYSQL_PASSWORD:",
        "ALIYUN_OSS_ACCESS_KEY_SECRET:",
        "DEMO_TOKEN:",
    ]:
        assert expected in values


def test_api_deployment_reads_sensitive_settings_from_secret_refs():
    deployment = read_repo_file("deploy/helm/locusthub/templates/deployment.yaml")

    for key in ["MYSQL_PASSWORD", "ALIYUN_OSS_ACCESS_KEY_ID", "ALIYUN_OSS_ACCESS_KEY_SECRET", "DEMO_TOKEN"]:
        assert f"name: {key}" in deployment
    assert "secretKeyRef:" in deployment
    assert ".Values.secret.existingSecret" in deployment
    assert ".Values.secret.name" in deployment


def test_secret_template_can_create_demo_secret_or_use_existing_secret():
    secret = read_repo_file("deploy/helm/locusthub/templates/secret.yaml")

    assert "kind: Secret" in secret
    assert "stringData:" in secret
    assert "MYSQL_PASSWORD:" in secret
    assert "ALIYUN_OSS_ACCESS_KEY_SECRET:" in secret
    assert "DEMO_TOKEN:" in secret
    assert "not .Values.secret.existingSecret" in secret


def test_ingress_template_routes_api_and_integrated_admin_with_tls():
    ingress = read_repo_file("deploy/helm/locusthub/templates/ingress.yaml")

    assert "apiVersion: networking.k8s.io/v1" in ingress
    assert "kind: Ingress" in ingress
    assert "secretName:" in ingress
    assert "locusthub-api" in ingress
    assert "locusthub-admin" in ingress
    assert ".Values.admin.enabled" in ingress
    assert "path: /api" in ingress
    assert "path: /" in ingress
