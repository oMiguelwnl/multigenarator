"""A bounded worker; services execute under caller-owned transactions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from threading import Event, Thread
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from multilang.jobs.queue import TaskQueue
from multilang.observability import operation

TaskHandler = Callable[[dict, str, Session], dict]


class Worker:
    def __init__(
        self,
        sessions: sessionmaker,
        handlers: Mapping[str, TaskHandler],
        *,
        worker_id: str | None = None,
        lease_seconds: float = 120,
        telemetry_enabled: bool = False,
    ):
        self.sessions = sessions
        self.handlers = dict(handlers)
        self.worker_id = worker_id or str(uuid4())
        self.lease_seconds = lease_seconds
        self.telemetry_enabled = telemetry_enabled

    def run_once(self) -> bool:
        with self.sessions() as session:
            lease = TaskQueue(session).claim(self.worker_id, lease_seconds=self.lease_seconds)
        if lease is None:
            return False
        stop = Event()
        lost = Event()

        def renew():
            while not stop.wait(self.lease_seconds / 3):
                try:
                    with self.sessions() as session:
                        TaskQueue(session).heartbeat(lease, lease_seconds=self.lease_seconds)
                except Exception:
                    lost.set()
                    return

        heartbeat = Thread(target=renew, daemon=True, name="multilang-task-heartbeat")
        heartbeat.start()
        try:
            with operation("task.execute", task_kind=lease.kind, enabled=self.telemetry_enabled):
                handler = self.handlers.get(lease.kind)
                if handler is None:
                    raise ValueError("no registered handler for task kind")
                with self.sessions() as session, session.begin():
                    result = handler(lease.payload, lease.owner_id, session)
                    if not isinstance(result, dict):
                        raise ValueError("task handler must return a result object")
                    if lost.is_set():
                        raise ValueError("task lease was lost during execution")
                with self.sessions() as session:
                    TaskQueue(session).complete(lease, result)
        except Exception as exc:
            try:
                with self.sessions() as session:
                    TaskQueue(session).fail(
                        lease, exc, retry_delay=min(300, 5 * 2 ** (lease.attempts - 1))
                    )
            except ValueError:
                pass  # A newer worker owns the task; fencing preserves its state.
        finally:
            stop.set()
            heartbeat.join(timeout=1)
        return True
