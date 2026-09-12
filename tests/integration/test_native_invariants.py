"""Independent regression checks for shared/private and immutable-edition boundaries."""

from copy import deepcopy

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.native_models import AuditLog, SurfaceFormRecord
from multilang.domain.datasets import DatasetManifest, DatasetMember
from multilang.domain.language_profiles import (
    POLICY_GROUPS,
    CapabilityEvidence,
    LanguageProfile,
)
from multilang.domain.lexical_identity import (
    LexicalIdentity,
    MorphologicalAnalysis,
    SurfaceForm,
)
from multilang.native_runtime import NativeFacade
from multilang.repositories.native_repository import NativeRepository
from multilang.settings import Settings


@pytest.fixture
def native_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


def lexical(lemma="run"):
    return LexicalIdentity(
        language="en",
        normalized_lemma=lemma,
        part_of_speech="VERB",
        sense_id="motion",
        profile_version="1",
        normalizer_version="nfc-preserve-1",
        analyzer_version="1",
        source_id="fixture",
        source_version="1",
        source_sha256="a" * 64,
    )


def manifest(identity, **changes):
    return DatasetManifest(
        **{
            "language": "en",
            "kind": "lexical",
            "namespace": "core",
            "version": "1",
            "source_id": "fixture",
            "source_sha256": "a" * 64,
            "policy_version": "1",
            "members": (
                DatasetMember(identity_id=identity.lexical_identity_id, rank=1),
            ),
            **changes,
        }
    )


def qualified_profile():
    enabled = CapabilityEvidence(state="enabled", evidence_sha256="a" * 64)
    return LanguageProfile(
        language="en",
        name="English",
        explanation_language="pt",
        analyzer_id="source-evidence",
        analyzer_version="1",
        tokenizer_id="source-evidence",
        tokenizer_version="1",
        tagset="UD",
        tagset_version="1",
        source_ids=("fixture",),
        capabilities={"core": enabled},
        policies={key: enabled for key in POLICY_GROUPS},
    )


def ranking_request(identity):
    return {
        "language": "en",
        "profile_version": "1",
        "version": "rank-1",
        "corpora": [
            {
                "corpus_id": "c",
                "sha256": "a" * 64,
                "language": "en",
                "version": "1",
                "token_count": 100,
                "document_count": 1,
                "weight": "1",
                "source_id": "fixture",
                "license_id": "test-only",
                "domain": "fixture",
                "period": "fixture",
                "variant": "fixture",
            }
        ],
        "observations": [
            {
                "corpus_id": "c",
                "document_id": "d",
                "occurrence_id": "o",
                "token_start": 0,
                "token_end": 1,
                "surface": "run",
                "allocations": [
                    {
                        "lexical_identity_id": identity.lexical_identity_id,
                        "share": "1",
                        "confidence": "1",
                    }
                ],
            }
        ],
        "policy": {
            "version": "1",
            "normalizer_version": "nfc-preserve-1",
            "analyzer_version": "1",
            "tokenizer_version": "1",
            "tagset_version": "1",
            "allocation_policy_version": "1",
            "mwe_policy_version": "1",
            "confidence_threshold": "1",
        },
    }


@pytest.mark.parametrize(
    "mutation", ["analyzer_version", "normalizer_version", "private_corpus"]
)
def test_facade_rejects_unqualified_ranking_versions_and_private_core(
    native_session, mutation
):
    repo = NativeRepository(native_session)
    identity = lexical()
    repo.put_identity(identity, actor="linguist", reason="review")
    repo.put_profile(qualified_profile())
    request = deepcopy(ranking_request(identity))
    if mutation == "private_corpus":
        request["corpora"][0]["privacy_class"] = "private"
    else:
        request["policy"][mutation] = "unqualified-version"
    facade = NativeFacade(
        native_session, Settings(_env_file=None, roadmap_4_enabled=True)
    )
    with pytest.raises(ValueError):
        facade.calculate_ranking(request, actor="linguist")


def test_surface_storage_cannot_override_the_contract_parent(native_session):
    repo = NativeRepository(native_session)
    first, second = lexical(), lexical("walk")
    for identity in (first, second):
        repo.put_identity(identity, actor="linguist", reason="review")
    analysis = MorphologicalAnalysis(
        lexical_identity_id=first.lexical_identity_id,
        analyzer_id="fixture",
        analyzer_version="1",
        features={"tense": "past"},
        confidence="1",
        evidence_sha256="a" * 64,
    )
    form = SurfaceForm(
        lexical_identity_id=first.lexical_identity_id,
        text="ran",
        analysis=analysis,
        source_id="fixture",
        source_sha256="a" * 64,
        attestation=10,
    )
    with pytest.raises(ValueError):
        repo.put_form(
            form,
            identity_id=second.lexical_identity_id,
            analysis_id=analysis.morphological_analysis_id,
            text="ran",
        )
    assert (
        native_session.scalar(select(func.count()).select_from(SurfaceFormRecord)) == 0
    )


def test_dataset_metadata_is_immutable():
    frozen = manifest(lexical(), metadata={"policy": "reviewed"})
    original = frozen.dataset_id
    with pytest.raises(TypeError):
        frozen.metadata["policy"] = "changed"
    assert frozen.dataset_id == original


def test_old_edition_projects_the_immutable_identity_revision(
    native_session, monkeypatch, tmp_path
):
    from multilang.services import semantic_anki

    repo = NativeRepository(native_session)
    original = lexical()
    repo.put_identity(original, actor="linguist", reason="review")
    edition = manifest(original)
    repo.save_dataset(edition, actor="linguist", reason="freeze")
    repo.put_identity(
        original.model_copy(update={"source_version": "2"}),
        actor="linguist",
        reason="source_refresh",
        expected_revision=1,
    )
    observed_versions = []
    project = semantic_anki.project_cards

    def record_projection(*, identities, **kwargs):
        identities = tuple(identities)
        observed_versions.extend(identity.source_version for identity in identities)
        return project(identities=identities, **kwargs)

    monkeypatch.setattr(semantic_anki, "project_cards", record_projection)
    facade = NativeFacade(
        native_session,
        Settings(_env_file=None, roadmap_4_enabled=True, export_output_dir=tmp_path),
    )
    facade.export_anki(
        {"dataset_id": edition.dataset_id, "model": "B", "prototype": True},
        actor="linguist",
    )
    assert observed_versions == ["1"]


def test_private_active_dataset_cannot_satisfy_another_users_rank_filter(
    native_session,
):
    repo = NativeRepository(native_session)
    identity = lexical()
    repo.put_identity(identity, actor="linguist", reason="review")
    private = manifest(identity, namespace="custom", owner_id="alice")
    repo.save_dataset(private, actor="alice", reason="private_import")
    repo.activate_dataset(
        private.dataset_id,
        actor="alice",
        reason="preview",
        production=False,
        owner_id="alice",
    )
    assert repo.search("run", owner_id="bob", min_rank=1, max_rank=1) == []
    assert repo.search("run", min_rank=1, max_rank=1) == []


def test_delete_after_recreation_records_a_second_audit_event(native_session):
    repo = NativeRepository(native_session)
    for content in ("first", "second"):
        repo.save_user_state(
            owner_id="alice", key="preferences", payload={"fixture": content}
        )
        repo.delete_user_data(owner_id="alice", actor="alice")
    assert (
        native_session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == "UserDataDeleted")
        )
        == 2
    )
