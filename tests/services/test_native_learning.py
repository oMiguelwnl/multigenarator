import sqlite3
import zipfile
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.native_models import UserStateRecord
from multilang.domain.learning import HistoryAlias
from multilang.domain.lexical_identity import LexicalIdentity
from multilang.repositories.native_repository import NativeRepository
from multilang.services.native_evidence import EvidenceStore, SignedEvidence


@pytest.fixture
def setup(tmp_path):
    from multilang.services.native_learning import NativeLearningService
    from multilang.services.semantic_anki import project_cards

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = NativeRepository(session)
        identity = LexicalIdentity(
            language="en",
            normalized_lemma="be",
            part_of_speech="VERB",
            sense_id="exist",
            profile_version="1",
            normalizer_version="1",
            analyzer_version="1",
            source_id="fixture",
            source_version="1",
            source_sha256="a" * 64,
        )
        repository.put_identity(identity, actor="test", reason="fixture")
        cards = project_cards(
            identities=(identity,), ranks={identity.lexical_identity_id: 1}, deck_edition_id="en-1"
        )
        root = tmp_path / "evidence"
        root.mkdir()
        store = EvidenceStore(root, key=b"k" * 32)
        service = NativeLearningService(repository, evidence_store=store)
        yield session, repository, service, cards, root
    engine.dispose()


def history_package(tmp_path):
    database = tmp_path / "history.db"
    with sqlite3.connect(database) as connection:
        connection.executescript("""
        CREATE TABLE notes(id INTEGER PRIMARY KEY,guid TEXT,mid INTEGER);
        CREATE TABLE cards(id INTEGER PRIMARY KEY,nid INTEGER,ord INTEGER,reps INTEGER,lapses INTEGER,ivl INTEGER);
        CREATE TABLE revlog(id INTEGER PRIMARY KEY,cid INTEGER);
        INSERT INTO notes VALUES (1,'legacy-guid',123);
        INSERT INTO cards VALUES (1,1,0,5,2,10);
        INSERT INTO revlog VALUES (1000,1);
        """)
    path = tmp_path / "history.apkg"
    with zipfile.ZipFile(path, "w") as archive:
        archive.write(database, "collection.anki2")
    return path


def approve_identity_alias(service, cards, root):
    from multilang.services.legacy_identity_adapter import (
        LegacyAliasCandidate,
        LegacyIdentityAdapter,
    )

    candidate = LegacyAliasCandidate(
        legacy_guid="legacy-guid", identity_ids=(cards[0].parent_lexical_identity_id,)
    )
    receipt = SignedEvidence.sign(
        candidate.model_dump(mode="json", exclude={"evidence_sha256"}),
        key=b"k" * 32,
        signer="reviewer",
        purpose="legacy-identity-alias",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    (root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    candidate = candidate.model_copy(update={"evidence_sha256": receipt.receipt_id})
    adapter = LegacyIdentityAdapter(
        service.session,
        evidence_verifier=lambda item: service.evidence_store.verify(
            item.evidence_sha256,
            item.model_dump(mode="json", exclude={"evidence_sha256"}),
            purpose="legacy-identity-alias",
        ),
    )
    preview = adapter.preview((candidate,))
    assert preview.ready
    adapter.apply(preview, confirmation_sha256=preview.confirmation_sha256, actor="reviewer")
    return adapter, candidate


def approve_alias(service, cards, root, *, identity_alias=False):
    alias = HistoryAlias(
        note_guid="legacy-guid",
        template_ordinal=0,
        model_id=123,
        semantic_card_id=cards[0].card_id,
        parent_lexical_identity_id=cards[0].parent_lexical_identity_id,
        evidence_sha256="a" * 64,
    )
    payload = {"aliases": [alias.model_dump(exclude={"evidence_sha256"})], "reviewer": "reviewer"}
    receipt = SignedEvidence.sign(
        payload,
        key=b"k" * 32,
        signer="reviewer",
        purpose="anki-history-alias",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    (root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    alias = alias.model_copy(update={"evidence_sha256": receipt.receipt_id})
    if identity_alias:
        approve_identity_alias(service, cards, root)
    assert (
        service.register_aliases(
            aliases=(alias,), receipt_sha256=receipt.receipt_id, actor="reviewer"
        )
        == 1
    )
    return alias


@pytest.mark.parametrize("identity_first", [True, False])
def test_history_alias_composes_with_approved_identity_alias_payload(setup, identity_first):
    from multilang.db.native_models import LegacyIdentityAlias

    session, _, service, cards, root = setup
    if identity_first:
        adapter, candidate = approve_identity_alias(service, cards, root)
    alias = approve_alias(service, cards, root)
    if not identity_first:
        adapter, candidate = approve_identity_alias(service, cards, root)
    row = session.get(LegacyIdentityAlias, "legacy-guid")
    assert row.payload["identity_alias"] == candidate.model_dump(mode="json")
    assert row.evidence_sha256 == alias.evidence_sha256 != candidate.evidence_sha256
    assert len(row.payload["history_aliases"]) == 1
    replay = adapter.preview((candidate,))
    assert replay.ready
    adapter.apply(replay, confirmation_sha256=replay.confirmation_sha256, actor="reviewer")
    assert (
        service.register_aliases(
            aliases=(alias,), receipt_sha256=alias.evidence_sha256, actor="reviewer"
        )
        == 1
    )


def test_history_alias_rejects_tampered_identity_proof_before_extending(setup):
    from multilang.db.native_models import LegacyIdentityAlias

    session, _, service, cards, root = setup
    _, candidate = approve_identity_alias(service, cards, root)
    proof = root / f"{candidate.evidence_sha256}.json"
    proof.write_text("{}")
    with pytest.raises(ValueError, match="identity.*evidence"):
        approve_alias(service, cards, root)
    row = session.get(LegacyIdentityAlias, "legacy-guid")
    assert "history_aliases" not in row.payload
    assert row.evidence_sha256 == candidate.evidence_sha256


def test_history_alias_refreshes_existing_mapping_before_composition(setup):
    from sqlalchemy import update

    from multilang.db.native_models import LegacyIdentityAlias

    session, _, service, cards, root = setup
    approve_identity_alias(service, cards, root)
    row = session.get(LegacyIdentityAlias, "legacy-guid")
    session.expire_on_commit = False
    session.commit()
    with Session(session.bind) as concurrent:
        concurrent.execute(
            update(LegacyIdentityAlias)
            .where(LegacyIdentityAlias.legacy_guid == "legacy-guid")
            .values(evidence_sha256="d" * 64)
        )
        concurrent.commit()
    with pytest.raises(ValueError, match="identity.*evidence"):
        approve_alias(service, cards, root)
    session.refresh(row)
    assert "history_aliases" not in row.payload
    assert row.evidence_sha256 == "d" * 64


def test_durable_history_queue_revocation_reset_and_delete_are_isolated(setup, tmp_path):
    session, repository, service, cards, root = setup
    approve_alias(service, cards, root)
    package = history_package(tmp_path)
    original = sha256(package.read_bytes()).hexdigest()
    imported = service.import_history(owner_id="alice", path=package, expected_revision=0)
    session.commit()
    assert len(imported.states) == 1
    assert service.get_state(owner_id="alice").revision == 1
    assert (
        service.import_history(owner_id="alice", path=package, expected_revision=1).import_id
        == imported.import_id
    )
    assert service.get_state(owner_id="alice").revision == 1
    assert "legacy-guid" not in repr(
        repository.get_user_state(owner_id="alice", key="native-learning")
    )
    assert sha256(package.read_bytes()).hexdigest() == original
    queue = service.queue(owner_id="alice", cards=cards)
    assert queue == service.queue(owner_id="alice", cards=tuple(reversed(cards)))
    state = service.override(
        owner_id="alice", card_id=cards[0].card_id, priority=50, expected_revision=1
    )
    assert state.overrides[cards[0].card_id] == 50
    state = service.reset(owner_id="alice", expected_revision=2)
    assert state.overrides == {} and state.history == (imported,)
    state = service.revoke_history(
        owner_id="alice", import_id=imported.import_id, expected_revision=3
    )
    assert state.history == ()
    service.set_known(owner_id="bob", card_ids=(cards[0].card_id,), expected_revision=0)
    service.delete(owner_id="alice", expected_revision=4)
    assert repository.get_user_state(owner_id="alice", key="native-learning") is None
    assert service.get_state(owner_id="bob").known_card_ids == (cards[0].card_id,)
    assert repository.get_identity(cards[0].parent_lexical_identity_id) is not None


def test_stale_revisions_and_rollback_cannot_overwrite_learner_state(setup):
    session, repository, service, cards, _ = setup
    session.commit()
    service.set_known(owner_id="alice", card_ids=(cards[0].card_id,), expected_revision=0)
    session.commit()
    with pytest.raises(ValueError, match="revision"):
        service.set_reading(owner_id="alice", card_ids=(), expected_revision=0)
    assert service.get_state(owner_id="alice").known_card_ids
    service.set_expansion(owner_id="alice", enabled=True, expected_revision=1)
    session.rollback()
    assert service.get_state(owner_id="alice").expansion_enabled is False
    assert service.get_state(owner_id="alice").revision == 1


def test_unproven_aliases_fail_without_persisting_private_data(setup, tmp_path):
    session, _, service, cards, _ = setup
    alias = HistoryAlias(
        note_guid="legacy-guid",
        template_ordinal=0,
        model_id=123,
        semantic_card_id=cards[0].card_id,
        parent_lexical_identity_id=cards[0].parent_lexical_identity_id,
        evidence_sha256="a" * 64,
    )
    with pytest.raises(ValueError, match="evidence"):
        service.register_aliases(aliases=(alias,), receipt_sha256="a" * 64, actor="reviewer")
    imported = service.import_history(
        owner_id="alice", path=history_package(tmp_path), expected_revision=0
    )
    assert imported.states == () and imported.quarantined_count == 1
    assert session.scalar(select(func.count()).select_from(UserStateRecord)) == 1


def test_import_rejects_unbounded_or_foreign_owner_before_parsing(setup, tmp_path):
    _, _, service, _, _ = setup
    for owner in ("", "alice:other", "a" * 129):
        with pytest.raises(ValueError, match="owner"):
            service.import_history(
                owner_id=owner, path=tmp_path / "missing.apkg", expected_revision=0
            )
