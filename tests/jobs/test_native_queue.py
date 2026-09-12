"""Durable task ownership, retries and worker execution contracts."""

import importlib.util
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def queue_types():
    assert importlib.util.find_spec("multilang.jobs") is not None, "native durable queue missing"
    from multilang.db.task_models import NativeTask
    from multilang.jobs.queue import TaskQueue

    return NativeTask, TaskQueue


@pytest.fixture
def database(tmp_path):
    model, _ = queue_types()
    engine = create_engine(f"sqlite:///{tmp_path / 'queue.db'}")
    model.__table__.create(engine)
    yield engine
    engine.dispose()


def test_claim_is_exclusive_and_idempotency_is_owner_scoped(database):
    _, queue_type = queue_types()
    with Session(database) as session:
        queue = queue_type(session)
        task = queue.enqueue(
            "ranking", {"dataset_id": "one"}, owner_id="alice", idempotency_key="same", now=100
        )
        assert (
            queue.enqueue(
                "ranking", {"dataset_id": "one"}, owner_id="alice", idempotency_key="same"
            ).id
            == task.id
        )
        with pytest.raises(ValueError, match="idempotency"):
            queue.enqueue(
                "ranking", {"dataset_id": "two"}, owner_id="alice", idempotency_key="same"
            )

    def claim(worker):
        with Session(database) as session:
            return queue_type(session).claim(worker, now=100, lease_seconds=20)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, ["worker-a", "worker-b"]))
    claimed = [r for r in results if r is not None]
    assert len(claimed) == 1
    assert claimed[0].attempts == 1


def test_expired_lease_reclaims_and_fences_old_worker(database):
    _, queue_type = queue_types()
    with Session(database) as session:
        queue = queue_type(session)
        task = queue.enqueue(
            "audio", {"asset_id": "one"}, owner_id="alice", idempotency_key="one", now=100
        )
        first = queue.claim("worker-a", now=100, lease_seconds=10)
        assert first is not None
        assert queue.claim("worker-b", now=105) is None
        second = queue.claim("worker-b", now=111, lease_seconds=10)
        assert second.id == task.id
        assert second.lease_token != first.lease_token
        with pytest.raises(ValueError, match="lease"):
            queue.complete(first, {"status": "ok"}, now=112)
        queue.complete(second, {"status": "ok"}, now=112)
        assert queue.get(task.id, owner_id="alice").status == "completed"
        assert queue.get(task.id, owner_id="bob") is None


def test_failures_have_bounded_retry_and_safe_diagnostics(database):
    _, queue_type = queue_types()
    with Session(database) as session:
        queue = queue_type(session)
        task = queue.enqueue(
            "import",
            {"dataset_id": "one"},
            owner_id="alice",
            idempotency_key="one",
            max_attempts=2,
            now=100,
        )
        first = queue.claim("worker", now=100)
        queue.fail(first, RuntimeError("secret=private-user-payload"), now=101, retry_delay=5)
        assert queue.claim("worker", now=103) is None
        second = queue.claim("worker", now=107)
        queue.fail(second, RuntimeError("raw-private-data"), now=108)
        stored = queue.get(task.id, owner_id="alice")
        assert stored.status == "failed"
        assert stored.error_code == "RuntimeError"
        assert "private" not in str(stored.__dict__)
        assert queue.claim("worker", now=200) is None


def test_worker_calls_service_and_rolls_back_failure(database):
    _, queue_type = queue_types()
    from multilang.jobs.worker import Worker

    with Session(database) as session:
        task = queue_type(session).enqueue(
            "ranking", {"dataset_id": "one"}, owner_id="alice", idempotency_key="one"
        )
    calls = []

    def handler(payload, actor, session):
        calls.append((payload, actor))
        return {"dataset_id": "one", "count": 3}

    worker = Worker(sessionmaker(database), {"ranking": handler}, worker_id="test-worker")
    assert worker.run_once() is True
    assert calls == [({"dataset_id": "one"}, "alice")]
    with Session(database) as session:
        stored = queue_type(session).get(task.id, owner_id="alice")
        assert stored.status == "completed"
        assert len(stored.result_sha256) == 64
