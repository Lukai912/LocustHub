from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import create_router
from app.core.config import get_settings
from app.core.database import Database
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.admission import RunAdmissionController
from app.services.artifacts import LocalArtifactRepository
from app.services.lane import LaneController
from app.services.metrics import LocustMetricsSimulator
from app.services.reports import ReportArchiver
from app.services.runner import TestRunService


def create_app() -> FastAPI:
    settings = get_settings()
    database = Database(settings.database_path)
    repo = SQLiteRepository(database)
    repo.init_schema()
    repo.seed_demo(settings.demo_token)

    artifacts = LocalArtifactRepository(settings.artifact_root)
    metrics = LocustMetricsSimulator()
    runner = TestRunService(
        repo=repo,
        admission=RunAdmissionController(repo),
        lanes=LaneController(),
        metrics=metrics,
        reports=ReportArchiver(repo, artifacts),
    )

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_router({"repo": repo, "runner": runner, "metrics": metrics, "settings": settings}), prefix=settings.api_prefix)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
