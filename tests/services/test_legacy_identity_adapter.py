"""Identity migration preserves old GUIDs without inferring history mappings."""

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.native_models import LegacyIdentityAlias
from multilang.domain.lexical_identity import LexicalIdentity
from multilang.repositories.native_repository import NativeRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as value:
        yield value
    engine.dispose()


def lexical(session, lemma="run"):
    item = LexicalIdentity(
        language="en",
        normalized_lemma=lemma,
        part_of_speech="VERB",
        sense_id="move",
        profile_version="1",
        normalizer_version="nfc-1",
        analyzer_version="reviewed-1",
        source_id="fixture",
        source_version="1",
        source_sha256="a" * 64,
    )
    NativeRepository(session).put_identity(item, actor="fixture", reason="review")
    return item


def test_alias_migration_is_previewed_proven_one_to_one_and_idempotent(session):
    from multilang.services.legacy_identity_adapter import (
        LegacyAliasCandidate,
        LegacyIdentityAdapter,
    )

    item = lexical(session)
    candidate = LegacyAliasCandidate(
        legacy_guid="Old-GUID", identity_ids=(item.lexical_identity_id,), evidence_sha256="b" * 64
    )
    adapter = LegacyIdentityAdapter(session, evidence_verifier=lambda _: True)
    preview = adapter.preview((candidate,))
    assert preview.ready and preview.unresolved_count == 0
    assert session.scalar(select(func.count()).select_from(LegacyIdentityAlias)) == 0
    result = adapter.apply(
        preview, confirmation_sha256=preview.confirmation_sha256, actor="fixture"
    )
    assert result["preserved_guids"] == ["Old-GUID"]
    record = session.get(LegacyIdentityAlias, "Old-GUID")
    assert record.identity_id == item.lexical_identity_id
    assert "history_aliases" not in record.payload
    replay = adapter.preview((candidate,))
    assert (
        adapter.apply(replay, confirmation_sha256=replay.confirmation_sha256, actor="fixture")
        == result
    )


def test_unresolved_merges_and_missing_proof_fail_before_writes(session):
    from multilang.services.legacy_identity_adapter import (
        LegacyAliasCandidate,
        LegacyIdentityAdapter,
    )

    item, second = lexical(session), lexical(session, "walk")
    candidates = (
        LegacyAliasCandidate(
            legacy_guid="one", identity_ids=(item.lexical_identity_id,), evidence_sha256="b" * 64
        ),
        LegacyAliasCandidate(
            legacy_guid="two", identity_ids=(item.lexical_identity_id,), evidence_sha256="b" * 64
        ),
        LegacyAliasCandidate(
            legacy_guid="ambiguous",
            identity_ids=(item.lexical_identity_id, second.lexical_identity_id),
            evidence_sha256="b" * 64,
        ),
        LegacyAliasCandidate(legacy_guid="unknown", identity_ids=()),
    )
    adapter = LegacyIdentityAdapter(session, evidence_verifier=lambda _: True)
    preview = adapter.preview(candidates)
    assert {entry.classification for entry in preview.decisions} == {
        "merge_requires_resolution",
        "ambiguous",
        "unresolved",
    }
    with pytest.raises(ValueError, match="unresolved"):
        adapter.apply(preview, confirmation_sha256=preview.confirmation_sha256, actor="fixture")
    rejected = LegacyIdentityAdapter(session, evidence_verifier=lambda _: False).preview(
        (candidates[0],)
    )
    assert not rejected.ready
    assert session.scalar(select(func.count()).select_from(LegacyIdentityAlias)) == 0


def test_existing_history_payload_is_preserved_and_conflict_blocks(session):
    from multilang.services.legacy_identity_adapter import (
        LegacyAliasCandidate,
        LegacyIdentityAdapter,
    )

    item, second = lexical(session), lexical(session, "walk")
    history = [{"opaque": "preserve existing independently proven history"}]
    session.add(
        LegacyIdentityAlias(
            legacy_guid="original",
            identity_id=item.lexical_identity_id,
            evidence_sha256="b" * 64,
            payload={"history_aliases": history},
        )
    )
    session.flush()
    adapter = LegacyIdentityAdapter(session, evidence_verifier=lambda _: True)
    candidate = LegacyAliasCandidate(
        legacy_guid="original", identity_ids=(item.lexical_identity_id,), evidence_sha256="c" * 64
    )
    preview = adapter.preview((candidate,))
    with pytest.raises(ValueError, match="confirmation"):
        adapter.apply(preview, confirmation_sha256="0" * 64, actor="fixture")
    adapter.apply(preview, confirmation_sha256=preview.confirmation_sha256, actor="fixture")
    assert session.get(LegacyIdentityAlias, "original").payload["history_aliases"] == history
    assert session.get(LegacyIdentityAlias, "original").evidence_sha256 == "b" * 64
    changed_proof = candidate.model_copy(update={"evidence_sha256": "d" * 64})
    assert adapter.preview((changed_proof,)).decisions[0].classification == "existing_conflict"
    changed = candidate.model_copy(update={"identity_ids": (second.lexical_identity_id,)})
    assert adapter.preview((changed,)).decisions[0].classification == "existing_conflict"


def test_alias_preview_batches_database_reads(session):
    from sqlalchemy import event

    from multilang.services.legacy_identity_adapter import (
        LegacyAliasCandidate,
        LegacyIdentityAdapter,
    )

    candidates = tuple(
        LegacyAliasCandidate(
            legacy_guid=f"old-{index}",
            identity_ids=(lexical(session, f"term-{index}").lexical_identity_id,),
            evidence_sha256="b" * 64,
        )
        for index in range(25)
    )
    statements = []

    def capture(*args):
        statements.append(args[2])

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        assert (
            LegacyIdentityAdapter(session, evidence_verifier=lambda _: True)
            .preview(candidates)
            .ready
        )
        assert len(statements) <= 8
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
