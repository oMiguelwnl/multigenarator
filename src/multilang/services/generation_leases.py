"""Generation leases with per-item fencing and unknown-outcome recovery gates.

Provider telemetry/cache writes remain independently durable. Only the short
content/status transaction is fenced; an interrupted provider item retains its
hash and requires recovery instead of silently consuming another paid attempt.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from threading import Event, Thread
from time import time
from uuid import uuid4

from sqlalchemy import delete, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from multilang.db.generation_lease_models import GenerationLeaseRecord


class GenerationLeaseError(ValueError):
    """Generation ownership is unavailable or an interrupted item needs recovery."""


def claim_statement(dialect: str, *, scope_key: str, job_id: str, token: str,
                    now: float, lease_seconds: float):
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise GenerationLeaseError("generation leases require PostgreSQL or SQLite")
    return insert(GenerationLeaseRecord).values(
        scope_key=scope_key, job_id=job_id, token=token, expires_at=now + lease_seconds,
    ).on_conflict_do_update(
        index_elements=[GenerationLeaseRecord.scope_key],
        set_={"job_id": job_id, "token": token, "expires_at": now + lease_seconds},
        where=(GenerationLeaseRecord.expires_at <= now)
        & GenerationLeaseRecord.inflight_item_sha256.is_(None),
    )


@dataclass
class GenerationLease:
    manager: "GenerationLeaseManager"
    job_id: str
    scope_keys: tuple[str, ...]
    job_scope: str
    token: str
    lost: Event
    current_item_sha256: str | None = None

    def fence(self, session: Session) -> None:
        """Lock and verify lease rows in the SAME transaction as content writes."""
        if self.lost.is_set():
            raise GenerationLeaseError("generation lease was lost")
        now = self.manager.now()
        changed = session.scalars(
            update(GenerationLeaseRecord).where(
                GenerationLeaseRecord.scope_key.in_(self.scope_keys),
                GenerationLeaseRecord.token == self.token,
                GenerationLeaseRecord.expires_at > now,
            ).values(expires_at=now + self.manager.lease_seconds)
            .returning(GenerationLeaseRecord.scope_key)
        ).all()
        if len(changed) != len(self.scope_keys):
            raise GenerationLeaseError("generation lease was lost")

    def begin_item(self, item_key: str) -> None:
        digest = sha256(item_key.encode("utf-8")).hexdigest()
        with Session(self.manager.engine) as session, session.begin():
            self.fence(session)
            changed = session.scalar(
                update(GenerationLeaseRecord).where(
                    GenerationLeaseRecord.scope_key == self.job_scope,
                    GenerationLeaseRecord.token == self.token,
                    GenerationLeaseRecord.inflight_item_sha256.is_(None),
                ).values(inflight_item_sha256=digest)
                .returning(GenerationLeaseRecord.scope_key)
            )
            if changed is None:
                raise GenerationLeaseError("interrupted text item requires recovery")
        self.current_item_sha256 = digest

    def finish_item(self, session: Session) -> None:
        if self.current_item_sha256 is None:
            raise GenerationLeaseError("generation item was not reserved")
        changed = session.scalar(
            update(GenerationLeaseRecord).where(
                GenerationLeaseRecord.scope_key == self.job_scope,
                GenerationLeaseRecord.token == self.token,
                GenerationLeaseRecord.inflight_item_sha256 == self.current_item_sha256,
            ).values(inflight_item_sha256=None)
            .returning(GenerationLeaseRecord.scope_key)
        )
        if changed is None:
            raise GenerationLeaseError("generation item ownership was lost")
        # The caller clears the in-memory marker only after its transaction
        # commits. A failed commit must still represent unfinished provider work.


class GenerationLeaseManager:
    def __init__(self, engine: Engine, *, lease_seconds: float = 120,
                 now: Callable[[], float] = time):
        if lease_seconds <= 0:
            raise ValueError("lease duration must be positive")
        self.engine = engine
        self.lease_seconds = lease_seconds
        self.now = now

    def claim(self, job_id: str) -> GenerationLease:
        job_scope = "job:" + sha256(job_id.encode("utf-8")).hexdigest()
        scopes = (("sqlite:global",) if self.engine.dialect.name == "sqlite" else ()) + (job_scope,)
        token = str(uuid4())
        now = self.now()
        with Session(self.engine) as session, session.begin():
            for scope in scopes:
                changed = session.scalar(claim_statement(
                    self.engine.dialect.name, scope_key=scope, job_id=job_id,
                    token=token, now=now, lease_seconds=self.lease_seconds,
                ).returning(GenerationLeaseRecord.scope_key))
                if changed is None:
                    existing = session.get(GenerationLeaseRecord, scope)
                    if existing is not None and existing.expires_at <= now and existing.inflight_item_sha256:
                        raise GenerationLeaseError("interrupted text item requires recovery")
                    raise GenerationLeaseError("generation is already running")
        return GenerationLease(self, job_id, scopes, job_scope, token, Event())

    def release(self, lease: GenerationLease) -> None:
        with Session(self.engine) as session, session.begin():
            owned = (
                GenerationLeaseRecord.scope_key.in_(lease.scope_keys),
                GenerationLeaseRecord.token == lease.token,
            )
            session.execute(delete(GenerationLeaseRecord).where(
                *owned, GenerationLeaseRecord.inflight_item_sha256.is_(None),
            ))
            # Preserve unknown provider outcomes while freeing the unrelated
            # SQLite/global lane. Never release a replacement worker's token.
            session.execute(update(GenerationLeaseRecord).where(*owned).values(expires_at=0))

    def status(self, job_id: str) -> dict[str, object]:
        scope = "job:" + sha256(job_id.encode("utf-8")).hexdigest()
        with Session(self.engine) as session:
            row = session.get(GenerationLeaseRecord, scope)
            if row is None:
                return {"job_id": job_id, "state": "idle", "inflight_item_sha256": None}
            active = row.expires_at > self.now()
            return {
                "job_id": job_id,
                "state": "active" if active else "recovery_required" if row.inflight_item_sha256 else "expired",
                "inflight_item_sha256": row.inflight_item_sha256,
            }

    def recover(self, job_id: str, *, expected_item_sha256: str,
                acknowledge_unknown_outcome: bool = False) -> dict[str, object]:
        if not acknowledge_unknown_outcome:
            raise GenerationLeaseError("unknown provider outcome must be acknowledged")
        if len(expected_item_sha256) != 64 or any(char not in "0123456789abcdef" for char in expected_item_sha256):
            raise GenerationLeaseError("expected item SHA256 is invalid")
        scope = "job:" + sha256(job_id.encode("utf-8")).hexdigest()
        with Session(self.engine) as session, session.begin():
            changed = session.scalar(update(GenerationLeaseRecord).where(
                GenerationLeaseRecord.scope_key == scope,
                GenerationLeaseRecord.job_id == job_id,
                GenerationLeaseRecord.expires_at <= self.now(),
                GenerationLeaseRecord.inflight_item_sha256 == expected_item_sha256,
            ).values(inflight_item_sha256=None, token=str(uuid4()))
                .returning(GenerationLeaseRecord.scope_key))
            if changed is None:
                raise GenerationLeaseError("recovery requires an expired lease and matching item hash")
        return {
            "job_id": job_id, "item_sha256": expected_item_sha256,
            "state": "recovered", "paid_replay_authorized": False,
        }

    @contextmanager
    def hold(self, job_id: str) -> Iterator[GenerationLease]:
        lease = self.claim(job_id)
        stop = Event()

        def renew() -> None:
            while not stop.wait(self.lease_seconds / 3):
                try:
                    with Session(self.engine) as session, session.begin():
                        lease.fence(session)
                except Exception:
                    lease.lost.set()
                    return

        in_memory = self.engine.dialect.name == "sqlite" and self.engine.url.database in (None, "", ":memory:")
        heartbeat = None if in_memory else Thread(target=renew, daemon=True, name="generation-lease-heartbeat")
        if heartbeat is not None:
            heartbeat.start()
        try:
            yield lease
        finally:
            stop.set()
            if heartbeat is not None:
                heartbeat.join(timeout=1)
            self.release(lease)
