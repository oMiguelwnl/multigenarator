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


def test_draft_roundtrip_completes_without_provider_and_revalidates_identity(tmp_path):
    from multilang.domain.content import ContentDraft, ContentRequest, TargetMatchEvidence
    from multilang.services.native_content import NativeContentService

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    calls = []

    def matcher(request, sentence):
        return TargetMatchEvidence(
            lexical_identity_id=request.lexical_identity_id,
            sense_id=request.sense_id,
            target_concept_id=request.target_concept_id,
            matched=True,
            observed_concept_ids=(request.target_concept_id,),
            analyzer_version="fixture",
            evidence_sha256="b" * 64,
            target_span=(2, 5),
        )

    def generate(request):
        calls.append("provider")
        return {
            "definition": "Move fast.",
            "example_sentence": "I run.",
            "translation": "Eu corro.",
        }

    try:
        with Session(engine) as session:
            settings = Settings(
                _env_file=None,
                roadmap_4_enabled=True,
                native_content_drafts_dir=tmp_path / "drafts",
            )
            facade = build_native_facade(session, settings)
            facade.repository.put_profile(qualified_profile())
            imported = facade.import_dataset(import_payload(), actor="fixture")
            identity = next(
                i
                for i in facade.repository.dataset_identities(imported["dataset_id"])
                if i.normalized_lemma == "run"
            )
            _, digest = facade._identity(identity.lexical_identity_id)
            request = ContentRequest(
                lexical_identity_id=identity.lexical_identity_id,
                card_id="fixture-card",
                language="en",
                language_profile_version="1",
                lemma="run",
                display_text="run",
                sense_id=identity.sense_id,
                context_cue="move fast",
                namespace="core",
                deck_edition_id="fixture-edition",
                grounding_sha256=digest,
                target_concept_id="run:move",
                explanation_language="pt",
            )
            facade.content_service = NativeContentService(
                generator=generate, matcher=matcher, provider="fixture", model_version="1"
            )
            draft = facade.draft_content(request.model_dump(mode="json"), actor="fixture")
            session.commit()
            assert calls == ["provider"]
        with Session(engine) as session:
            facade = build_native_facade(session, settings)
            facade.plugins.register(
                kind="analyzer", name="source-evidence-target", version="1", plugin=matcher
            )
            result = facade.complete_content_draft(draft, actor="fixture")
            assert result["review_status"] == "pending"
            assert calls == ["provider"]
            changed = ContentDraft.model_validate(draft).model_copy(
                update={"request": request.model_copy(update={"grounding_sha256": "0" * 64})}
            )
            with pytest.raises(ValueError, match="grounding"):
                facade.complete_content_draft(changed.model_dump(mode="json"), actor="fixture")
            with pytest.raises(ValueError):
                facade.complete_content_draft({**draft, "target_evidence": {}}, actor="fixture")
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
