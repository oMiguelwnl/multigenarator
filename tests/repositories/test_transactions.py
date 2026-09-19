"""Repository writes respect the transaction explicitly owned by an application."""

import importlib
from contextlib import contextmanager, nullcontext

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import GenerationJob, ProviderCallLogModel
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.provider_call_log_repository import (
    ProviderCallLogCreate,
    ProviderCallLogRepository,
)


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'transactions.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def write_job_and_log(session):
    job = JobRepository(session).create_job(
        request=GenerationRequest(language=SupportedLanguage.EN, source_type="word-list"),
        run_key="transaction-test",
        source_fingerprint="source",
        total_items=1,
    )
    ProviderCallLogRepository(session).insert(
        ProviderCallLogCreate(
            job_id=job.id, operation="definition", provider="fixture", status="success"
        )
    )


def counts(engine):
    with Session(engine) as observer:
        return tuple(
            observer.scalar(select(func.count()).select_from(model))
            for model in (GenerationJob, ProviderCallLogModel)
        )


@contextmanager
def managed(session):
    name = "multilang.repositories.transactions"
    assert importlib.util.find_spec(name) is not None, "explicit transaction scope is missing"
    with importlib.import_module(name).repository_transaction(session):
        yield


def test_standalone_repositories_still_commit(engine):
    with Session(engine) as session:
        write_job_and_log(session)
    assert counts(engine) == (1, 1)


def test_job_state_lock_refreshes_a_stale_session_before_merging(engine):
    from multilang.repositories.transactions import lock_job_for_update, repository_transaction

    with Session(engine) as writer, Session(engine) as stale:
        write_job_and_log(writer)
        job_id = writer.scalar(select(GenerationJob.id))
        cached = stale.get(GenerationJob, job_id)
        assert cached.resume_state == {}
        with repository_transaction(writer):
            current = lock_job_for_update(writer, job_id)
            current.resume_state = {"review_history": ["first"]}
        with repository_transaction(stale):
            current = lock_job_for_update(stale, job_id)
            current.resume_state = {**current.resume_state, "export": "receipt"}
    with Session(engine) as observer:
        assert observer.get(GenerationJob, job_id).resume_state == {"review_history": ["first"], "export": "receipt"}


def test_explicit_sqlalchemy_transaction_rolls_back_both_repositories(engine):
    with Session(engine) as session:
        with pytest.raises(ValueError, match="abort"):
            with session.begin():
                write_job_and_log(session)
                raise ValueError("abort")
    assert counts(engine) == (0, 0)


def test_managed_scope_commits_once_and_is_not_visible_early(engine):
    with Session(engine) as session:
        with managed(session):
            write_job_and_log(session)
            assert counts(engine) == (0, 0)
    assert counts(engine) == (1, 1)


def test_managed_scope_rolls_back_all_writes_on_failure(engine):
    with Session(engine) as session:
        with pytest.raises(ValueError, match="abort"):
            with managed(session):
                write_job_and_log(session)
                raise ValueError("abort")
    assert counts(engine) == (0, 0)


def test_nested_scope_failure_cannot_be_swallowed_and_committed(engine):
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="transaction"):
            with managed(session):
                write_job_and_log(session)
                try:
                    with managed(session):
                        raise ValueError("nested abort")
                except ValueError:
                    pass
    assert counts(engine) == (0, 0)


def test_scope_joins_explicit_outer_transaction_without_committing_it(engine):
    with Session(engine) as session:
        with pytest.raises(ValueError, match="outer abort"):
            with session.begin():
                with managed(session):
                    write_job_and_log(session)
                assert counts(engine) == (0, 0)
                raise ValueError("outer abort")
    assert counts(engine) == (0, 0)


def test_scope_can_own_autobegun_read_transaction(engine):
    with Session(engine) as session:
        session.scalar(select(func.count()).select_from(GenerationJob))
        with managed(session):
            write_job_and_log(session)
    assert counts(engine) == (1, 1)


def test_explicit_rollback_inside_scope_cannot_report_success(engine):
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="transaction"):
            with managed(session):
                write_job_and_log(session)
                session.rollback()
    assert counts(engine) == (0, 0)


@pytest.mark.parametrize("managed_scope", [False, True])
def test_repository_does_not_commit_outer_transaction_from_savepoint(engine, managed_scope):
    with Session(engine) as session:
        session.scalar(select(func.count()).select_from(GenerationJob))
        with pytest.raises(ValueError, match="savepoint abort"):
            with session.begin_nested():
                with managed(session) if managed_scope else nullcontext():
                    write_job_and_log(session)
                raise ValueError("savepoint abort")
        session.commit()
    assert counts(engine) == (0, 0)
