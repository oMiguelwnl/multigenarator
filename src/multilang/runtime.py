"""Runtime bootstrap for the shipped CLI path."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.repositories.job_repository import JobRepository
from multilang.services.generate_job import GenerateJobService
from multilang.settings import Settings


def build_runtime_service(settings: Settings | None = None) -> GenerateJobService:
    """Construct the repository-backed orchestration service from runtime settings."""

    runtime_settings = settings or Settings()
    engine = create_engine(runtime_settings.database_url)
    Base.metadata.create_all(engine)
    session = Session(engine)
    repository = JobRepository(session)
    return GenerateJobService(repository)
