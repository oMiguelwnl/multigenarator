"""Exercise actual native composition across imports, ranking and persistence."""

import json
from hashlib import sha256

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.language_profiles import POLICY_GROUPS, CapabilityEvidence, LanguageProfile
from multilang.native_runtime import build_native_facade
from multilang.repositories.native_repository import NativeRepository
from multilang.settings import Settings


def qualified_profile():
    approved = CapabilityEvidence(state="enabled", version="1", evidence_sha256="a" * 64)
    return LanguageProfile(
        language="en",
        name="English",
        explanation_language="pt",
        analyzer_id="source-evidence",
        analyzer_version="1",
        tokenizer_id="reviewed",
        tokenizer_version="1",
        tagset="UD",
        tagset_version="1",
        source_ids=("fixture",),
        capabilities={"core": approved},
        policies={name: approved for name in POLICY_GROUPS},
    )


def import_payload():
    data = json.dumps(
        [
            {"lemma": "run", "pos": "VERB", "sense": "move"},
            {"lemma": "walk", "pos": "VERB", "sense": "move"},
        ]
    )
    return {
        "format": "dictionary",
        "data": data,
        "version": "fixture-1",
        "namespace": "core",
        "source": {
            "source_id": "fixture",
            "version": "1",
            "sha256": sha256(data.encode()).hexdigest(),
            "language": "en",
            "profile_version": "1",
            "normalizer_version": "nfc-preserve-1",
            "analyzer_version": "1",
            "license_id": "synthetic-fixture",
            "attribution": "Test author",
        },
    }


def test_real_facade_import_search_and_transactional_replay():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            facade = build_native_facade(session, Settings(_env_file=None, roadmap_4_enabled=True))
            with pytest.raises(ValueError, match="capability"):
                facade.import_dataset(import_payload(), actor="linguist")
            NativeRepository(session).put_profile(qualified_profile())
            imported = facade.import_dataset(import_payload(), actor="linguist")
            session.commit()
            assert imported["identity_count"] == 2
            assert len(facade.search("run", language="en")) == 1
            assert (
                facade.import_dataset(import_payload(), actor="linguist")["dataset_id"]
                == imported["dataset_id"]
            )
            assert facade.list_datasets()[0]["member_count"] == 2
    finally:
        engine.dispose()


def test_disabled_native_facade_rejects_writes_before_database_access():
    engine = create_engine("sqlite://")
    try:
        with Session(engine) as session:
            facade = build_native_facade(session, Settings(_env_file=None, roadmap_4_enabled=False))
            with pytest.raises(ValueError, match="ROADMAP_4_ENABLED"):
                facade.import_dataset(import_payload(), actor="linguist")
    finally:
        engine.dispose()


def test_facade_adaptive_state_is_owned_and_does_not_modify_core():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            repo = NativeRepository(session)
            repo.put_profile(qualified_profile())
            facade = build_native_facade(session, Settings(_env_file=None, roadmap_4_enabled=True))
            imported = facade.import_dataset(import_payload(), actor="linguist")
            payload = {"dataset_ids": [imported["dataset_id"]]}
            original = repo.get_dataset(imported["dataset_id"])
            before = facade.adaptive_queue(payload, actor="alice")
            assert len(before["eligible"]) == 2
            card_id = before["eligible"][0]["card_id"]
            updated = facade.update_learner_state(
                {"action": "known", "card_ids": [card_id], "expected_revision": 0}, "alice"
            )
            assert updated["revision"] == 1
            after = facade.adaptive_queue(payload, actor="alice")
            assert len(after["eligible"]) == 1
            assert after["deferred"][0]["reason"] == "known"
            assert len(facade.adaptive_queue(payload, actor="bob")["eligible"]) == 2
            assert repo.get_dataset(imported["dataset_id"]) == original
            with pytest.raises(ValueError, match="revision"):
                facade.update_learner_state({"action": "reset", "expected_revision": 0}, "alice")
            facade.update_learner_state({"action": "delete", "expected_revision": 1}, "alice")
            assert len(facade.adaptive_queue(payload, actor="alice")["eligible"]) == 2
    finally:
        engine.dispose()
