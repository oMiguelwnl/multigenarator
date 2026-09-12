"""Native writes must be atomic, versioned and isolated from learner data."""

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.native_models import AuditLog, DomainEventRecord, LexicalIdentityRecord
from multilang.domain.datasets import DatasetManifest, DatasetMember
from multilang.repositories.native_repository import NativeRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def identity(lemma="run", sense="move", **changes):
    from multilang.domain.lexical_identity import LexicalIdentity

    return LexicalIdentity(
        language="en",
        normalized_lemma=lemma,
        part_of_speech="VERB",
        sense_id=sense,
        profile_version="1",
        normalizer_version="nfc-1",
        analyzer_version="reviewed-1",
        source_id="fixture",
        source_version="1",
        source_sha256="a" * 64,
        **changes,
    )


def test_identity_history_audit_and_event_are_one_transaction(session):
    repo = NativeRepository(session)
    lexical = identity()
    repo.put_identity(lexical, actor="linguist:fixture", reason="source_review")
    assert session.scalar(select(func.count()).select_from(AuditLog)) == 1
    assert session.scalar(select(func.count()).select_from(DomainEventRecord)) == 1
    session.rollback()
    assert session.scalar(select(func.count()).select_from(LexicalIdentityRecord)) == 0
    assert session.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_rerun_is_idempotent_and_stale_revision_rejected(session):
    repo = NativeRepository(session)
    lexical = identity()
    first = repo.put_identity(lexical, actor="linguist", reason="review")
    session.commit()
    second = repo.put_identity(lexical, actor="linguist", reason="review")
    assert second["revision"] == first["revision"] == 1
    updated = lexical.model_copy(update={"source_version": "2"})
    result = repo.put_identity(
        updated, actor="linguist", reason="source_refresh", expected_revision=1
    )
    assert result["revision"] == 2
    session.commit()
    with pytest.raises(ValueError, match="revision"):
        repo.put_identity(lexical, actor="linguist", reason="stale", expected_revision=1)
    assert len(repo.identity_history(lexical.lexical_identity_id)) == 2


def test_dataset_versions_diff_activation_and_rollback(session):
    repo = NativeRepository(session)
    one, two = identity(), identity("walk")
    for lexical in (one, two):
        repo.put_identity(lexical, actor="fixture", reason="review")
    common = dict(
        language="en",
        kind="lexical",
        namespace="core",
        source_sha256="a" * 64,
        policy_version="1",
        source_id="fixture",
        redistribution_approved=False,
    )
    first = DatasetManifest(
        version="1", members=(DatasetMember(identity_id=one.lexical_identity_id, rank=1),), **common
    )
    second = DatasetManifest(
        version="2", members=(DatasetMember(identity_id=two.lexical_identity_id, rank=1),), **common
    )
    for manifest in (first, second):
        repo.save_dataset(manifest, actor="fixture", reason="import")
    repo.activate_dataset(first.dataset_id, actor="admin", reason="preview", production=False)
    repo.activate_dataset(second.dataset_id, actor="admin", reason="preview", production=False)
    assert repo.compare_datasets(first.dataset_id, second.dataset_id)["added"] == [
        two.lexical_identity_id
    ]
    repo.activate_dataset(first.dataset_id, actor="admin", reason="rollback", production=False)
    assert (
        repo.active_dataset(language="en", kind="lexical", namespace="core")["dataset_id"]
        == first.dataset_id
    )
    with pytest.raises(ValueError, match="3000|redistribution"):
        repo.activate_dataset(first.dataset_id, actor="admin", reason="release", production=True)


def test_private_state_never_overwrites_core_and_audit_has_no_payload(session):
    repo = NativeRepository(session)
    lexical = identity()
    repo.put_identity(lexical, actor="linguist", reason="review")
    session.commit()
    before = repo.get_identity(lexical.lexical_identity_id)
    repo.save_user_state(
        owner_id="alice", key="preferences", payload={"private_text": "secret highlight"}
    )
    repo.save_user_state(owner_id="bob", key="preferences", payload={"known": []})
    assert (
        repo.get_user_state(owner_id="alice", key="preferences")["private_text"]
        == "secret highlight"
    )
    assert repo.get_user_state(owner_id="bob", key="preferences") == {"known": []}
    assert repo.get_identity(lexical.lexical_identity_id) == before
    logs = [row.__dict__ for row in session.scalars(select(AuditLog))]
    assert "secret highlight" not in repr(logs)
    repo.delete_user_data(owner_id="alice", actor="alice")
    assert repo.get_user_state(owner_id="alice", key="preferences") is None
    assert repo.get_identity(lexical.lexical_identity_id) == before


def test_parameterized_search_distinguishes_senses_and_literal_wildcards(session):
    repo = NativeRepository(session)
    for lexical in (identity(), identity(sense="operate"), identity("100%")):
        repo.put_identity(lexical, actor="fixture", reason="review")
    assert len(repo.search("run", language="en")) == 2
    assert repo.search("' OR 1=1 --") == []
    assert len(repo.search("%")) == 1
    assert repo.search("run", language="ko") == []
    with pytest.raises(ValueError):
        repo.search("run", limit=100000)
