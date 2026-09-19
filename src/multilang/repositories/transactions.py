"""Explicit application ownership around otherwise standalone repositories.

Standalone repository calls retain commit-as-you-go semantics. An explicit
``session.begin()`` or ``repository_transaction(session)`` owns the commit when
combining writes. The latter can also adopt an autobegun read transaction.
Session objects and their transaction scopes must never be shared across threads.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session, SessionTransaction, SessionTransactionOrigin

_SCOPE_KEY = "multilang.repository_transaction"


class RepositoryTransactionError(RuntimeError):
    """A composed transaction was aborted and cannot be reported as successful."""


@dataclass
class _Scope:
    transaction: SessionTransaction
    rollback_only: bool = False


def lock_job_for_update(session: Session, job_id: str):
    """Lock and refresh a job before merging its JSON state, on SQLite or PG.

    Call first inside an owned transaction. A no-op update acquires the SQLite
    write lock and PostgreSQL row lock without relying on JSON equality. Reading
    with populate_existing then replaces stale identity-map state.
    """
    from multilang.db.models import GenerationJob

    transaction = session.get_transaction()
    if not isinstance(session.info.get(_SCOPE_KEY), _Scope) and (
        transaction is None or transaction.origin is SessionTransactionOrigin.AUTOBEGIN
    ):
        raise RepositoryTransactionError("job state lock requires an owned transaction")
    if any(isinstance(row, GenerationJob) and session.is_modified(row, include_collections=False)
           for row in session.dirty):
        raise RepositoryTransactionError("job state must be locked before editing")
    with session.no_autoflush:
        found = session.execute(update(GenerationJob).where(GenerationJob.id == job_id).values(
            id=GenerationJob.id, updated_at=GenerationJob.updated_at,
        ).returning(GenerationJob.id).execution_options(synchronize_session=False)).scalar_one_or_none()
        if found is None:
            raise RepositoryTransactionError("unknown job")
        return session.scalar(select(GenerationJob).where(GenerationJob.id == job_id)
            .execution_options(populate_existing=True))


def commit_repository_changes(session: Session) -> None:
    """Flush under an application transaction, commit for standalone callers."""
    scope = session.info.get(_SCOPE_KEY)
    transaction = session.get_transaction()
    if isinstance(scope, _Scope):
        if scope.rollback_only or transaction is not scope.transaction:
            raise RepositoryTransactionError("repository transaction was aborted")
        session.flush()
    elif session.in_nested_transaction() or (
        transaction is not None and transaction.origin is not SessionTransactionOrigin.AUTOBEGIN
    ):
        session.flush()
    else:
        session.commit()


@contextmanager
def repository_transaction(session: Session) -> Iterator[Session]:
    """Compose writes atomically, joining an explicit outer transaction if present.

    With no outer ``session.begin()``, this scope owns the current implicit
    transaction, including any writes already made in it. Nested scopes join the
    same unit; a caught inner failure still makes the complete unit rollback-only.
    A repository's internal rollback invalidates the unit instead of silently
    discarding earlier writes and allowing a partial commit.
    """
    existing = session.info.get(_SCOPE_KEY)
    if isinstance(existing, _Scope):
        try:
            yield session
        except BaseException:
            existing.rollback_only = True
            raise
        return

    transaction = session.get_transaction()
    owns_transaction = not session.in_nested_transaction() and (
        transaction is None or transaction.origin is SessionTransactionOrigin.AUTOBEGIN
    )
    if transaction is None:
        transaction = session.begin()
    scope = _Scope(transaction)
    session.info[_SCOPE_KEY] = scope
    try:
        yield session
        if (
            scope.rollback_only
            or session.get_transaction() is not transaction
            or not transaction.is_active
        ):
            raise RepositoryTransactionError("repository transaction was aborted")
        session.flush()
        if owns_transaction:
            transaction.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.info.pop(_SCOPE_KEY, None)


__all__ = [
    "RepositoryTransactionError",
    "commit_repository_changes",
    "lock_job_for_update",
    "repository_transaction",
]
