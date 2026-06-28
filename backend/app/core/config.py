from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "LocustHub"
    database_path: Path = Path("data/locusthub.db")
    artifact_root: Path = Path("artifacts")
    api_prefix: str = "/api/v1"
    demo_token: str = "dev-token"


@lru_cache
def get_settings() -> Settings:
    return Settings()
