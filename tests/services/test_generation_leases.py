"""Exclusive generation ownership and durable interruption boundaries."""

import importlib
from multiprocessing import get_context

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from multilang.db.base import Base


def lease_api():
    name = "multilang.services.generation_leases"
    assert importlib.util.find_spec(name) is not None, "generation leases are missing"
    return importlib.import_module(name)


@pytest.fixture
def engine(tmp_path):
    lease_api()
    database = create_engine(f"sqlite:///{tmp_path / 'leases.db'}")
    Base.metadata.create_all(database)
    yield database
    database.dispose()


def test_sqlite_allows_only_one_generation_job_at_a_time(engine):
    api = lease_api()
    manager = api.GenerationLeaseManager(engine, now=lambda: 100)
    first = manager.claim("job-a")
    with pytest.raises(api.GenerationLeaseError):
        manager.claim("job-a")
    with pytest.raises(api.GenerationLeaseError):
        manager.claim("job-b")
    manager.release(first)
    second = manager.claim("job-b")
    manager.release(second)


def test_expired_lease_can_be_reclaimed_and_old_content_writer_is_fenced(engine):
    api = lease_api()
    clock = [100.0]
    manager = api.GenerationLeaseManager(engine, lease_seconds=10, now=lambda: clock[0])
    first = manager.claim("job-a")
    clock[0] = 111
    second = manager.claim("job-a")
    with Session(engine) as session, pytest.raises(api.GenerationLeaseError):
        first.fence(session)
    manager.release(first)
    with Session(engine) as session:
        second.fence(session)
        session.commit()
    manager.release(second)


def test_inflight_marker_blocks_unknown_provider_replay_but_not_other_jobs(engine):
    api = lease_api()
    clock = [100.0]
    manager = api.GenerationLeaseManager(engine, lease_seconds=10, now=lambda: clock[0])
    first = manager.claim("job-a")
    first.begin_item("private input key")
    manager.release(first)
    clock[0] = 111
    with pytest.raises(api.GenerationLeaseError, match="recovery"):
        manager.claim("job-a")
    other = manager.claim("job-b")
    manager.release(other)
    with Session(engine) as session:
        rows = session.scalars(select(api.GenerationLeaseRecord)).all()
        assert "private input" not in repr([row.__dict__ for row in rows])


def test_item_commit_clears_marker_and_allows_idempotent_resume(engine):
    api = lease_api()
    manager = api.GenerationLeaseManager(engine, now=lambda: 100)
    first = manager.claim("job-a")
    first.begin_item("one")
    with Session(engine) as session, session.begin():
        first.fence(session)
        first.finish_item(session)
    manager.release(first)
    resumed = manager.claim("job-a")
    manager.release(resumed)


def test_content_transaction_rollback_preserves_interruption_marker(engine):
    api = lease_api()
    manager = api.GenerationLeaseManager(engine, now=lambda: 100)
    first = manager.claim("job-a")
    first.begin_item("one")
    with Session(engine) as session, pytest.raises(RuntimeError):
        with session.begin():
            first.fence(session)
            first.finish_item(session)
            raise RuntimeError("content failed")
    manager.release(first)
    with pytest.raises(api.GenerationLeaseError, match="recovery"):
        manager.claim("job-a")


def _process_claim(database_url, ready, release, output):
    api = lease_api()
    engine = create_engine(database_url)
    manager = api.GenerationLeaseManager(engine)
    ready.wait(10)
    try:
        lease = manager.claim("same-job")
    except api.GenerationLeaseError:
        output.put("blocked")
    else:
        output.put("claimed")
        release.wait(10)
        manager.release(lease)
    finally:
        engine.dispose()


def test_claims_are_exclusive_across_sqlite_processes(engine):
    context = get_context("fork")
    ready, release, output = context.Event(), context.Event(), context.Queue()
    processes = [context.Process(target=_process_claim, args=(str(engine.url), ready, release, output)) for _ in range(2)]
    for process in processes:
        process.start()
    try:
        ready.set()
        assert sorted(output.get(timeout=15) for _ in processes) == ["blocked", "claimed"]
    finally:
        release.set()
        for process in processes:
            process.join(15)
            if process.is_alive():
                process.terminate()
                process.join()
    assert all(process.exitcode == 0 for process in processes)


def test_claim_sql_is_atomic_on_postgresql():
    api = lease_api()
    from sqlalchemy.dialects import postgresql

    statement = api.claim_statement("postgresql", scope_key="job:a", job_id="a", token="t", now=1, lease_seconds=120)
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT" in sql
    assert "DO UPDATE" in sql
    assert "expires_at <=" in sql
    assert "inflight_item_sha256 IS NULL" in sql


def test_shared_service_holds_lease_before_candidate_reads(engine):
    api = lease_api()
    from multilang.domain.jobs import SupportedLanguage
    from multilang.repositories.text_repository import TextRepository
    from multilang.services.generate_text_items import GenerateTextItemsService

    observations = []

    class ObservedRepository(TextRepository):
        def list_example_sentences_for_job(self, job_id, **kwargs):
            with pytest.raises(api.GenerationLeaseError):
                api.GenerationLeaseManager(engine).claim(job_id)
            observations.append("exclusive")
            return []

        def list_generation_candidates(self, job_id, **kwargs):
            return []

    with Session(engine) as session:
        service = GenerateTextItemsService(
            job_repository=None, lexical_repository=None,
            text_repository=ObservedRepository(session), text_generation_service=None,
            text_validation_service=None, tatoeba_sentence_source=None,
        )
        assert service.execute(job_id="job-a", deck_language=SupportedLanguage.EN).processed_items == 0
    assert observations == ["exclusive"]
    lease = api.GenerationLeaseManager(engine).claim("job-a")
    lease.manager.release(lease)


def test_provider_history_survives_item_transaction_failure(engine):
    api = lease_api()
    from multilang.db.models import ProviderCallLogModel
    from multilang.repositories.provider_call_log_repository import (
        ProviderCallLogCreate,
        ProviderCallLogRepository,
    )
    from multilang.repositories.text_repository import TextRepository

    with Session(engine) as session:
        repository = TextRepository(session)
        assert callable(getattr(repository, "generation_lease", None)), "shared lease context is missing"
        with pytest.raises(RuntimeError):
            with repository.generation_lease("job-a"):
                repository.begin_generation_item("job-a", "one")
                ProviderCallLogRepository(session).insert(ProviderCallLogCreate(
                    operation="sentence", provider="fixture", status="success",
                ))
                with repository.generation_item_transaction("job-a"):
                    raise RuntimeError("content rejected")
    with Session(engine) as session:
        assert len(session.scalars(select(ProviderCallLogModel)).all()) == 1
    with pytest.raises(api.GenerationLeaseError, match="recovery"):
        api.GenerationLeaseManager(engine).claim("job-a")


def test_recovery_requires_expired_ownership_exact_hash_and_acknowledgement(engine):
    api = lease_api()
    from hashlib import sha256

    manager = api.GenerationLeaseManager(engine, now=lambda: 100)
    lease = manager.claim("job-a")
    lease.begin_item("one")
    digest = sha256(b"one").hexdigest()
    assert callable(getattr(manager, "recover", None)), "explicit recovery is missing"
    with pytest.raises(api.GenerationLeaseError):
        manager.recover("job-a", expected_item_sha256=digest, acknowledge_unknown_outcome=True)
    manager.release(lease)
    with pytest.raises(api.GenerationLeaseError):
        manager.recover("job-a", expected_item_sha256=digest, acknowledge_unknown_outcome=False)
    with pytest.raises(api.GenerationLeaseError):
        manager.recover("job-a", expected_item_sha256="b" * 64, acknowledge_unknown_outcome=True)
    result = manager.recover("job-a", expected_item_sha256=digest, acknowledge_unknown_outcome=True)
    assert result["paid_replay_authorized"] is False
    with pytest.raises(api.GenerationLeaseError):
        manager.recover("job-a", expected_item_sha256=digest, acknowledge_unknown_outcome=True)
    resumed = manager.claim("job-a")
    manager.release(resumed)


@pytest.fixture
def postgres_engine():
    import os
    from uuid import uuid4

    from sqlalchemy.schema import CreateSchema, DropSchema

    url = os.environ.get("MULTILANG_TEST_GENERATION_LEASE_POSTGRES_URL")
    if not url:
        pytest.skip("requires disposable PostgreSQL test server")
    database = create_engine(url)
    schema = "generation_lease_test_" + uuid4().hex
    with database.begin() as connection:
        connection.execute(CreateSchema(schema))
    isolated = database.execution_options(schema_translate_map={None: schema})
    lease_api().GenerationLeaseRecord.__table__.create(isolated)
    try:
        yield isolated
    finally:
        with database.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        database.dispose()


def test_postgresql_claims_are_exclusive_while_different_jobs_can_run(postgres_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    api = lease_api()
    manager = api.GenerationLeaseManager(postgres_engine)
    barrier = Barrier(2)

    def claim():
        barrier.wait(timeout=10)
        try:
            return manager.claim("job-a")
        except api.GenerationLeaseError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        leases = list(executor.map(lambda _: claim(), range(2)))
    winners = [lease for lease in leases if lease is not None]
    assert len(winners) == 1
    independent = manager.claim("job-b")
    manager.release(independent)
    manager.release(winners[0])


def test_postgresql_expiration_fences_stale_writer(postgres_engine):
    test_expired_lease_can_be_reclaimed_and_old_content_writer_is_fenced(postgres_engine)


def test_latin_batch_reserves_unknown_outcome_before_provider_and_never_silently_falls_back(engine):
    from types import SimpleNamespace

    from multilang.domain.jobs import SupportedLanguage
    from multilang.repositories.text_repository import TextRepository
    from multilang.services.generate_text_items import GenerateTextItemsService

    api = lease_api()
    calls = []

    class Repository(TextRepository):
        def list_example_sentences_for_job(self, job_id, **kwargs):
            return []

        def list_generation_candidates(self, job_id, **kwargs):
            return [SimpleNamespace(id="one", item_key="vir", lemma="vir", display_form="vir", part_of_speech="noun")]

    def latin_generate(seeds):
        calls.append("latin")
        status = api.GenerationLeaseManager(engine).status("job-a")
        assert status["inflight_item_sha256"] is not None
        raise TimeoutError("unknown provider outcome")

    def fallback(**kwargs):
        calls.append("fallback")
        raise AssertionError("provider fallback is not permitted after unknown outcome")

    with Session(engine) as session:
        service = GenerateTextItemsService(
            job_repository=None, lexical_repository=None, text_repository=Repository(session),
            text_generation_service=SimpleNamespace(generate_bundle=fallback),
            text_validation_service=None, tatoeba_sentence_source=None,
            latin_card_service=SimpleNamespace(generate=latin_generate),
        )
        with pytest.raises(TimeoutError):
            service.execute(job_id="job-a", deck_language=SupportedLanguage.LA)
    assert calls == ["latin"]
    assert api.GenerationLeaseManager(engine).status("job-a")["state"] == "recovery_required"
