"""Versioned HTTP adapters with bounded input and server-owned authorization."""

from __future__ import annotations

import unicodedata
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from threading import Lock
from time import monotonic
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from multilang.db.models import GenerationJob, LexicalCandidate
from multilang.db.task_models import NativeTask
from multilang.domain.jobs import SupportedLanguage
from multilang.jobs.queue import TaskQueue
from multilang.observability import configure_logging, operation
from multilang.security.access import AccessPolicy, Principal, Role
from multilang.settings import Settings


class TaskSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    kind: Literal["audio", "ranking", "import", "anki", "content"]
    payload: dict = Field(default_factory=dict)


class RequestWindow:
    """Bounded per-credential, per-process request limiter (use gateway limits across replicas)."""

    def __init__(self, limit: int):
        self.limit = limit
        self.requests = defaultdict(deque)
        self.lock = Lock()

    def allow(self, subject: str) -> bool:
        now = monotonic()
        with self.lock:
            window = self.requests[subject]
            while window and window[0] <= now - 60:
                window.popleft()
            if len(window) >= self.limit:
                return False
            window.append(now)
            return True


class RequestBoundary:
    """Bound the bytes received before JSON parsing; fail closed when native mode is off."""

    def __init__(self, app, *, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if scope.get("path", "").startswith("/api/v2") and not self.settings.roadmap_4_enabled:
            return await JSONResponse({"detail": "not found"}, status_code=404)(
                scope, receive, send
            )
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "invalid content length"}, status_code=400)(
                scope, receive, send
            )
        if length < 0:
            return await JSONResponse({"detail": "invalid content length"}, status_code=400)(
                scope, receive, send
            )
        if length > self.settings.native_api_max_body_bytes:
            return await JSONResponse({"detail": "request too large"}, status_code=413)(
                scope, receive, send
            )
        messages = deque()
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.settings.native_api_max_body_bytes:
                return await JSONResponse({"detail": "request too large"}, status_code=413)(
                    scope, receive, send
                )
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def buffered_receive():
            if messages:
                return messages.popleft()
            return await receive()

        with operation(
            "http.request", task_kind="http", enabled=self.settings.native_telemetry_enabled
        ):
            await self.app(scope, buffered_receive, send)


_FORBIDDEN_INPUT_KEYS = frozenset(
    {
        "actor",
        "role",
        "permissions",
        "owner_id",
        "user_id",
        "subject",
        "token",
        "secret",
        "password",
        "api_key",
        "authorization",
        "input_file",
        "output_file",
        "file_path",
        "output_path",
        "input_path",
        "path",
        "database_url",
        "endpoint",
        "provider_url",
        "url",
        "callback_url",
    }
)


def validate_http_payload(value: object, depth: int = 0) -> None:
    if depth > 12:
        raise ValueError("input nesting exceeds limit")
    if isinstance(value, dict):
        if len(value) > 1000:
            raise ValueError("input object exceeds limit")
        for key, item in value.items():
            if str(key).casefold() in _FORBIDDEN_INPUT_KEYS:
                raise ValueError("input contains a server-owned field")
            validate_http_payload(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > 3000:
            raise ValueError("input list exceeds limit")
        for item in value:
            validate_http_payload(item, depth + 1)
    elif isinstance(value, str) and len(value) > 16384:
        raise ValueError("input text exceeds limit")


def task_projection(task: NativeTask) -> dict:
    return {
        name: getattr(task, name)
        for name in (
            "id",
            "kind",
            "status",
            "attempts",
            "max_attempts",
            "created_at",
            "updated_at",
            "error_code",
            "result_sha256",
        )
    }


def create_app(
    *, settings: Settings | None = None, engine: Engine | None = None, facade_factory=None
) -> FastAPI:
    runtime_settings = settings or Settings()
    owned_engine = engine is None
    database = (
        engine
        if engine is not None
        else create_engine(runtime_settings.database_url, pool_pre_ping=True)
    )
    sessions = sessionmaker(database, expire_on_commit=False)
    policy = AccessPolicy(runtime_settings.native_api_credentials)
    limiter = RequestWindow(runtime_settings.native_api_requests_per_minute)
    bearer = HTTPBearer(auto_error=False)

    @asynccontextmanager
    async def lifespan(app):
        if runtime_settings.native_telemetry_enabled:
            configure_logging()
        yield
        if owned_engine:
            database.dispose()

    app = FastAPI(title="Multilang API", version="2.0", lifespan=lifespan)
    app.add_middleware(RequestBoundary, settings=runtime_settings)

    def session_dependency():
        with sessions() as session:
            yield session

    def principal_dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> Principal:
        principal = None if credentials is None else policy.authenticate(credentials.credentials)
        if principal is None:
            raise HTTPException(
                401, "authentication required", headers={"WWW-Authenticate": "Bearer"}
            )
        if not limiter.allow(principal.subject):
            raise HTTPException(429, "request rate exceeded", headers={"Retry-After": "60"})
        return principal

    def require(action):
        def dependency(principal: Principal = Depends(principal_dependency)):
            if not policy.permits(principal, action):
                raise HTTPException(403, "permission denied")
            return principal

        return dependency

    def facade(session):
        if facade_factory is not None:
            return facade_factory(session, runtime_settings)
        from multilang.native_runtime import build_native_facade

        return build_native_facade(session, runtime_settings)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error):
        return JSONResponse({"detail": "invalid request"}, status_code=422)

    @app.exception_handler(ValueError)
    async def invalid_operation(request: Request, error):
        return JSONResponse({"detail": "invalid operation or unmet prerequisites"}, status_code=422)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, error):
        return JSONResponse(
            {"detail": "database unavailable or schema requires explicit migration"},
            status_code=503,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error):
        return JSONResponse({"detail": "operation failed"}, status_code=500)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/v1/languages")
    def legacy_languages(principal: Principal = Depends(require("read"))):
        return [{"code": language.value} for language in SupportedLanguage]

    @app.get("/api/v1/search")
    def legacy_search(
        q: str = Query(min_length=1, max_length=256),
        language: SupportedLanguage | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        principal: Principal = Depends(require("read")),
        session: Session = Depends(session_dependency),
    ):
        normalized = unicodedata.normalize("NFC", q).strip()
        statement = (
            select(LexicalCandidate)
            .join(GenerationJob, GenerationJob.id == LexicalCandidate.job_id)
            .where(
                LexicalCandidate.source_type == "frequency",
                LexicalCandidate.lemma == normalized,
            )
            .order_by(LexicalCandidate.id)
            .limit(limit)
        )
        if language is not None:
            statement = statement.where(GenerationJob.language == language.value)
        return [
            {"lemma": row.lemma, "lemma_key": row.lemma_key, "display_form": row.display_form}
            for row in session.scalars(statement)
        ]

    @app.get("/api/v1/jobs/{job_id}")
    def legacy_job(
        job_id: str,
        principal: Principal = Depends(require("admin")),
        session: Session = Depends(session_dependency),
    ):
        row = session.get(GenerationJob, job_id)
        if row is None:
            raise HTTPException(404, "not found")
        return {
            name: getattr(row, name)
            for name in (
                "id",
                "language",
                "source_type",
                "status",
                "current_stage",
                "total_items",
                "completed_items",
                "failed_items",
            )
        }

    @app.get("/api/v2/search")
    def search(
        q: str = Query(min_length=1, max_length=256),
        language: SupportedLanguage | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        principal: Principal = Depends(require("read")),
        min_rank: int | None = Query(default=None, ge=1),
        max_rank: int | None = Query(default=None, ge=1),
        session: Session = Depends(session_dependency),
    ):
        if min_rank is not None and max_rank is not None and min_rank > max_rank:
            raise ValueError("minimum rank exceeds maximum rank")
        return facade(session).search(
            q,
            language=language.value if language else None,
            limit=limit,
            owner_id=principal.subject,
            min_rank=min_rank,
            max_rank=max_rank,
        )

    @app.get("/api/v2/datasets")
    def datasets(
        principal: Principal = Depends(require("read")),
        session: Session = Depends(session_dependency),
    ):
        return facade(session).list_datasets()

    @app.post("/api/v2/jobs", status_code=202)
    def enqueue(
        submission: TaskSubmission,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
        principal: Principal = Depends(principal_dependency),
        session: Session = Depends(session_dependency),
    ):
        if not policy.permits(principal, submission.kind):
            raise HTTPException(403, "permission denied")
        validate_http_payload(submission.payload)
        return task_projection(
            TaskQueue(session).enqueue(
                submission.kind,
                submission.payload,
                owner_id=principal.subject,
                idempotency_key=idempotency_key,
                max_attempts=runtime_settings.native_task_max_attempts,
            )
        )

    @app.post("/api/v2/datasets/import", status_code=202)
    def import_dataset(
        payload: dict,
        principal: Principal = Depends(require("import")),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
        session: Session = Depends(session_dependency),
    ):
        if not idempotency_key:
            raise HTTPException(422, "Idempotency-Key required")
        validate_http_payload(payload)
        return task_projection(
            TaskQueue(session).enqueue(
                "import",
                payload,
                owner_id=principal.subject,
                idempotency_key=idempotency_key,
                max_attempts=runtime_settings.native_task_max_attempts,
            )
        )

    @app.get("/api/v2/jobs/{task_id}")
    def task_status(
        task_id: str,
        principal: Principal = Depends(require("read")),
        session: Session = Depends(session_dependency),
    ):
        task = TaskQueue(session).get(
            task_id, owner_id=None if principal.role == Role.ADMIN else principal.subject
        )
        if task is None:
            raise HTTPException(404, "not found")
        return task_projection(task)

    @app.post("/api/v2/jobs/{task_id}/cancel")
    def cancel(
        task_id: str,
        principal: Principal = Depends(require("cancel")),
        session: Session = Depends(session_dependency),
    ):
        if not TaskQueue(session).cancel(
            task_id, owner_id=None if principal.role == Role.ADMIN else principal.subject
        ):
            raise HTTPException(409, "task not queued or not accessible")
        return {"id": task_id, "status": "cancelled"}

    return app
