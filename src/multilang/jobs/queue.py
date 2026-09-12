"""Durable at-least-once tasks with compare-and-swap leases and fencing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from time import time
from uuid import uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from multilang.db.task_models import NativeTask

TASK_KINDS = frozenset({"audio", "ranking", "import", "anki", "content"})


def payload_hash(value: object) -> str:
    return sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


@dataclass(frozen=True)
class TaskLease:
    id: str
    kind: str
    owner_id: str
    payload: dict
    attempts: int
    worker_id: str
    lease_token: str


class TaskQueue:
    """Each mutation owns and commits its short queue transaction."""

    def __init__(self, session: Session):
        self.session = session

    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        owner_id: str,
        idempotency_key: str,
        max_attempts: int = 3,
        now: float | None = None,
    ) -> NativeTask:
        now = time() if now is None else now
        if kind not in TASK_KINDS or not 1 <= max_attempts <= 10:
            raise ValueError("invalid task kind or retry policy")
        if not owner_id or len(owner_id) > 128 or not idempotency_key or len(idempotency_key) > 128:
            raise ValueError("invalid task owner or idempotency key")
        digest = payload_hash(payload)
        lookup = select(NativeTask).where(
            NativeTask.owner_id == owner_id, NativeTask.idempotency_key == idempotency_key
        )
        existing = self.session.scalar(lookup)
        if existing is None:
            task = NativeTask(
                id=str(uuid4()),
                owner_id=owner_id,
                idempotency_key=idempotency_key,
                kind=kind,
                payload=payload,
                payload_sha256=digest,
                status="pending",
                attempts=0,
                max_attempts=max_attempts,
                available_at=now,
                created_at=now,
                updated_at=now,
            )
            self.session.add(task)
            try:
                self.session.commit()
                self.session.refresh(task)
                return task
            except IntegrityError:
                self.session.rollback()
                existing = self.session.scalar(lookup)
                if existing is None:
                    raise
        if existing.kind != kind or existing.payload_sha256 != digest:
            raise ValueError("idempotency key conflicts with an existing task")
        return existing

    def get(self, task_id: str, *, owner_id: str | None) -> NativeTask | None:
        statement = select(NativeTask).where(NativeTask.id == task_id)
        if owner_id is not None:
            statement = statement.where(NativeTask.owner_id == owner_id)
        return self.session.scalar(statement.execution_options(populate_existing=True))

    def claim(
        self, worker_id: str, *, now: float | None = None, lease_seconds: float = 120
    ) -> TaskLease | None:
        now = time() if now is None else now
        if not worker_id or len(worker_id) > 128 or lease_seconds <= 0:
            raise ValueError("invalid worker lease")
        self.session.execute(
            update(NativeTask)
            .where(
                NativeTask.status == "running",
                NativeTask.lease_expires_at <= now,
                NativeTask.attempts >= NativeTask.max_attempts,
            )
            .values(status="failed", error_code="LeaseExhausted", updated_at=now)
        )
        self.session.commit()
        eligible = and_(
            NativeTask.attempts < NativeTask.max_attempts,
            or_(
                and_(NativeTask.status == "pending", NativeTask.available_at <= now),
                and_(NativeTask.status == "running", NativeTask.lease_expires_at <= now),
            ),
        )
        for _ in range(16):
            candidate = self.session.scalar(
                select(NativeTask.id)
                .where(eligible)
                .order_by(NativeTask.available_at, NativeTask.id)
                .limit(1)
            )
            if candidate is None:
                self.session.rollback()
                return None
            token = str(uuid4())
            changed = self.session.execute(
                update(NativeTask)
                .where(NativeTask.id == candidate, eligible)
                .values(
                    status="running",
                    worker_id=worker_id,
                    lease_token=token,
                    lease_expires_at=now + lease_seconds,
                    attempts=NativeTask.attempts + 1,
                    updated_at=now,
                )
            ).rowcount
            self.session.commit()
            if changed:
                row = self.get(candidate, owner_id=None)
                return TaskLease(
                    row.id,
                    row.kind,
                    row.owner_id,
                    dict(row.payload),
                    row.attempts,
                    worker_id,
                    token,
                )
        return None

    def _lease_update(self, lease: TaskLease, *, now: float, values: dict) -> None:
        changed = self.session.execute(
            update(NativeTask)
            .where(
                NativeTask.id == lease.id,
                NativeTask.status == "running",
                NativeTask.worker_id == lease.worker_id,
                NativeTask.lease_token == lease.lease_token,
                NativeTask.lease_expires_at > now,
            )
            .values(**values, updated_at=now)
        ).rowcount
        self.session.commit()
        if not changed:
            raise ValueError("task lease is no longer owned")

    def heartbeat(
        self, lease: TaskLease, *, now: float | None = None, lease_seconds: float = 120
    ) -> None:
        now = time() if now is None else now
        if lease_seconds <= 0:
            raise ValueError("invalid lease duration")
        self._lease_update(lease, now=now, values={"lease_expires_at": now + lease_seconds})

    def complete(self, lease: TaskLease, result: dict, *, now: float | None = None) -> None:
        self._lease_update(
            lease,
            now=time() if now is None else now,
            values={
                "status": "completed",
                "result_sha256": payload_hash(result),
                "lease_expires_at": None,
                "lease_token": None,
                "error_code": None,
            },
        )

    def fail(
        self,
        lease: TaskLease,
        error: Exception,
        *,
        now: float | None = None,
        retry_delay: float = 5,
    ) -> None:
        now = time() if now is None else now
        row = self.get(lease.id, owner_id=None)
        if row is None:
            raise ValueError("task lease is no longer owned")
        self._lease_update(
            lease,
            now=now,
            values={
                "status": "pending" if lease.attempts < row.max_attempts else "failed",
                "available_at": now + max(0, retry_delay),
                "error_code": type(error).__name__[:64],
                "lease_token": None,
                "lease_expires_at": None,
            },
        )

    def cancel(self, task_id: str, *, owner_id: str | None) -> bool:
        # Running tasks may have provider side effects; only queued work is cancellable.
        statement = update(NativeTask).where(
            NativeTask.id == task_id, NativeTask.status == "pending"
        )
        if owner_id is not None:
            statement = statement.where(NativeTask.owner_id == owner_id)
        changed = self.session.execute(
            statement.values(status="cancelled", updated_at=time())
        ).rowcount
        self.session.commit()
        return bool(changed)
