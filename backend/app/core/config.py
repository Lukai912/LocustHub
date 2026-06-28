import os
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "LocustHub"
    database_backend: str = "sqlite"
    database_path: Path = Path("data/locusthub.db")
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "locusthub"
    mysql_password: str = "locusthub"
    mysql_database: str = "locusthub"
    artifact_root: Path = Path("artifacts")
    artifact_storage_provider: str = "local"
    aliyun_oss_endpoint: str = ""
    aliyun_oss_bucket: str = ""
    aliyun_oss_access_key_id: str = ""
    aliyun_oss_access_key_secret: str = ""
    aliyun_oss_signed_url_expire_seconds: int = 900
    api_prefix: str = "/api/v1"
    demo_token: str = "dev-token"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "LocustHub"),
        database_backend=os.getenv("DATABASE_BACKEND", "sqlite"),
        database_path=Path(os.getenv("DATABASE_PATH", "data/locusthub.db")),
        mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", "locusthub"),
        mysql_password=os.getenv("MYSQL_PASSWORD", "locusthub"),
        mysql_database=os.getenv("MYSQL_DATABASE", "locusthub"),
        artifact_root=Path(os.getenv("ARTIFACT_ROOT", "artifacts")),
        artifact_storage_provider=os.getenv("ARTIFACT_STORAGE_PROVIDER", "local"),
        aliyun_oss_endpoint=os.getenv("ALIYUN_OSS_ENDPOINT", ""),
        aliyun_oss_bucket=os.getenv("ALIYUN_OSS_BUCKET", ""),
        aliyun_oss_access_key_id=os.getenv("ALIYUN_OSS_ACCESS_KEY_ID", ""),
        aliyun_oss_access_key_secret=os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET", ""),
        aliyun_oss_signed_url_expire_seconds=int(os.getenv("ALIYUN_OSS_SIGNED_URL_EXPIRE_SECONDS", "900")),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        demo_token=os.getenv("DEMO_TOKEN", "dev-token"),
    )
