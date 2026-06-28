from pathlib import Path

import pytest

from app.core.config import get_settings
from app.services.artifacts import AliyunOssArtifactRepository, LocalArtifactRepository


def test_settings_can_select_mysql_and_oss(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_BACKEND", "mysql")
    monkeypatch.setenv("MYSQL_HOST", "mysql")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("ARTIFACT_STORAGE_PROVIDER", "aliyun_oss")
    monkeypatch.setenv("ALIYUN_OSS_BUCKET", "locusthub-artifacts")

    settings = get_settings()

    assert settings.database_backend == "mysql"
    assert settings.mysql_host == "mysql"
    assert settings.mysql_port == 3307
    assert settings.artifact_storage_provider == "aliyun_oss"
    assert settings.aliyun_oss_bucket == "locusthub-artifacts"
    get_settings.cache_clear()


def test_mysql_schema_contains_required_tables():
    schema = (Path(__file__).resolve().parents[1] / "app" / "db" / "mysql_schema.sql").read_text(encoding="utf-8")

    for table in [
        "tenants",
        "test_runs",
        "locust_run_snapshots",
        "artifact_objects",
        "locust_report_summaries",
        "baseline_runs",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema


def test_local_artifact_repository_uploads_text(tmp_path):
    repo = LocalArtifactRepository(tmp_path)
    result = repo.upload_text("reports/report.html", "<html></html>", "text/html")

    assert result["provider"] == "local_fs"
    assert result["bucket"] == "locusthub-local"
    assert result["object_key"] == "reports/report.html"
    assert (tmp_path / "reports" / "report.html").read_text(encoding="utf-8") == "<html></html>"


def test_aliyun_oss_repository_requires_configuration():
    with pytest.raises(ValueError):
        AliyunOssArtifactRepository(endpoint="", bucket="", access_key_id="", access_key_secret="")
