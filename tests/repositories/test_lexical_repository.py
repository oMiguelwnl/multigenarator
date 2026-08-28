"""Repository tests for lexical candidate persistence."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
    raw_bytes_sha256,
)
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
    KoreanFrequencyLexicalEvidence,
    PronunciationRecord,
)
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository


def build_repositories() -> tuple[LexicalRepository, JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return LexicalRepository(session), JobRepository(session), session


def make_request(
    source_type: str = "word-list",
    *,
    language: SupportedLanguage = SupportedLanguage.EN,
) -> GenerationRequest:
    return GenerationRequest(language=language, source_type=source_type, input_file=None)


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def make_candidate(
    *, status: GroundingStatus, ipa: str | None, warning_code: str | None, spoken_form: str | None = None
) -> LexicalCardCandidate:
    return LexicalCardCandidate(
        submitted_form="running",
        display_form="running",
        lemma="run",
        lemma_key="en:run",
        frequency_rank=17 if status is GroundingStatus.GROUNDED else None,
        frequency_level=1 if status is GroundingStatus.GROUNDED else None,
        definitions_html="to move swiftly on foot" if status is GroundingStatus.GROUNDED else None,
        definition_language="en",
        ipa=ipa,
        spoken_form=spoken_form,
        translation_target_language="pt",
        grounding_status=status,
        warning_code=warning_code,
        warning_detail="Need lexical review" if warning_code else None,
        provenance=LexicalProvenance(
            source="manual" if status is GroundingStatus.GROUNDED else "user-input",
            definition=DefinitionRecord(
                source="manual" if status is GroundingStatus.GROUNDED else "fallback",
                value="to move swiftly on foot",
                fallback_used=status is not GroundingStatus.GROUNDED,
            ),
            pronunciation=PronunciationRecord(
                source="provider-pronunciation-generator" if ipa else "missing",
                value=ipa,
                authoritative=ipa is not None,
            ),
        ),
    )


def make_korean_candidate(*, include_frequency_evidence: bool = False) -> LexicalCardCandidate:
    identity = KoreanLexicalIdentity(
        submitted_form="학교",
        canonical_nfc="학교",
        lemma="학교",
        part_of_speech="NNG",
        sense_id="fixture-school-1",
        register="neutral",
        morpheme_signature=(KoreanSignatureItem(form="학교", pos="NNG"),),
        analyzer_fingerprint=KoreanAnalyzerFingerprint(
            analyzer_name="kiwi",
            analyzer_package_version="0.23.2",
            model_package_version="0.23.0",
            model_type="cong",
            enabled_dialects="standard",
            num_workers=1,
            integrate_allomorph=True,
            top_n=2,
            split_complex=False,
            compatible_jamo=False,
            normalize_coda=False,
            z_coda=False,
            typos=None,
            oov_handling="chr",
            policy_version="kiwi-top2-consensus-v1",
        ),
        status="resolved",
    )
    evidence = KoreanFrequencyLexicalEvidence(
        source_id="nikl-korean-learners-vocabulary",
        source_version="fixture-v1",
        source_rank=23,
        final_rank=17,
        level=1,
        part_of_speech=identity.part_of_speech,
        sense_id=identity.sense_id,
        grounding_confidence="reviewed-source-backed",
        license_decision="approved-local-use",
        curation_decision="accepted",
        bundle_sha256=_hash("bundle"),
        source_sha256=_hash("source"),
        source_review_receipt_sha256=_hash("source-review-receipt"),
        source_review_aggregate_sha256=_hash("source-review-aggregate"),
        analyzer_fingerprint=identity.analyzer_fingerprint,
    )
    return LexicalCardCandidate(
        submitted_form="학교",
        display_form="학교",
        lemma=identity.lemma,
        lemma_key=identity.lexical_key,
        frequency_rank=17,
        frequency_level=1,
        definitions_html="escola",
        definition_language="pt",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="reviewed-fixture"),
        korean_identity=identity,
        korean_frequency_evidence=evidence if include_frequency_evidence else None,
    )


def test_upsert_candidate_updates_existing_row() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-en-custom",
        source_fingerprint="list-a",
        total_items=1,
    )

    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        source_type="word-list",
        normalized_source="running",
        candidate=make_candidate(status=GroundingStatus.PENDING, ipa=None, warning_code="needs-grounding"),
    )
    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        source_type="word-list",
        normalized_source="running",
        candidate=make_candidate(status=GroundingStatus.GROUNDED, ipa="/ɹʌn/", spoken_form="RYT", warning_code=None),
    )

    assert session.execute(
        text("SELECT COUNT(*) FROM lexical_candidates WHERE job_id = :job_id AND item_key = :item_key"),
        {"job_id": job.id, "item_key": "line-1"},
    ).scalar_one() == 1

    stored = repository.list_candidates(job.id)
    assert len(stored) == 1
    assert stored[0].grounding_status is GroundingStatus.GROUNDED
    assert stored[0].ipa == "/ɹʌn/"
    assert stored[0].spoken_form == "RYT"
    assert stored[0].frequency_rank == 17


def test_list_candidates_preserves_pending_warnings_and_grounded_fields() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-en-custom",
        source_fingerprint="list-b",
        total_items=2,
    )

    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        source_type="word-list",
        normalized_source="running",
        candidate=make_candidate(status=GroundingStatus.PENDING, ipa=None, warning_code="needs-grounding"),
    )
    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-2",
        source_type="word-list",
        normalized_source="run",
        candidate=make_candidate(status=GroundingStatus.GROUNDED, ipa="/ɹʌn/", spoken_form="RYT", warning_code=None),
    )

    pending, grounded = repository.list_candidates(job.id)

    assert pending.grounding_status is GroundingStatus.PENDING
    assert pending.warning_code == "needs-grounding"
    assert pending.provenance.source == "user-input"
    assert grounded.grounding_status is GroundingStatus.GROUNDED
    assert grounded.definitions_html == "to move swiftly on foot"
    assert grounded.ipa == "/ɹʌn/"
    assert grounded.spoken_form == "RYT"


def test_count_pending_candidates_only_counts_pending_and_insufficient_rows() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-en-custom",
        source_fingerprint="list-c",
        total_items=3,
    )

    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        source_type="word-list",
        normalized_source="running",
        candidate=make_candidate(status=GroundingStatus.PENDING, ipa=None, warning_code="needs-grounding"),
    )
    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-2",
        source_type="word-list",
        normalized_source="run",
        candidate=make_candidate(status=GroundingStatus.INSUFFICIENT, ipa=None, warning_code="missing-definition"),
    )
    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-3",
        source_type="word-list",
        normalized_source="runner",
        candidate=make_candidate(status=GroundingStatus.GROUNDED, ipa="/ɹʌn/", spoken_form="RYT", warning_code=None),
    )

    assert repository.count_pending_candidates(job.id) == 2


def test_frequency_upsert_candidates_rejects_duplicates_before_persistence() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(source_type="frequency"),
        run_key="run-en-frequency",
        source_fingerprint="freq-a",
        total_items=2,
    )
    first = make_candidate(status=GroundingStatus.GROUNDED, ipa="/rʌn/", warning_code=None)
    duplicate = first.model_copy(update={"submitted_form": "ran", "display_form": "ran"})

    try:
        repository.upsert_candidates(
            job_id=job.id,
            run_key=job.run_key,
            source_type="frequency",
            candidates=[
                ("level-1-rank-0001", "run", first),
                ("level-2-rank-1001", "ran", duplicate),
            ],
        )
    except ValueError as exc:
        assert "duplicate frequency lemma_key" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("expected duplicate frequency candidate validation failure")


def test_frequency_upsert_candidate_rejects_existing_duplicate_across_levels() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(source_type="frequency"),
        run_key="run-en-frequency-existing",
        source_fingerprint="freq-b",
        total_items=2,
    )
    first = make_candidate(status=GroundingStatus.GROUNDED, ipa="/rʌn/", warning_code=None)
    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="level-1-rank-0001",
        source_type="frequency",
        normalized_source="run",
        candidate=first,
    )

    try:
        repository.upsert_candidate(
            job_id=job.id,
            run_key=job.run_key,
            item_key="level-2-rank-1001",
            source_type="frequency",
            normalized_source="run",
            candidate=first,
        )
    except ValueError as exc:
        assert "duplicate frequency lexical candidate" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("expected duplicate frequency candidate validation failure")


def test_korean_identity_survives_commit_expire_reload_and_typed_restoration() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(language=SupportedLanguage.KO),
        run_key="run-ko-word-list-fixture",
        source_fingerprint="fixture-korean-list",
        total_items=1,
    )
    candidate = make_korean_candidate()

    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="학교",
        source_type="word-list",
        normalized_source="학교",
        candidate=candidate,
    )
    session.commit()
    session.expire_all()

    row = repository.get_candidate_for_item(job.id, "학교")
    assert row is not None
    assert row.korean_identity == candidate.korean_identity.model_dump(mode="json")

    restored = repository.list_candidates(job.id)[0]
    assert restored.korean_identity == candidate.korean_identity
    assert restored.korean_identity is not None
    assert restored.korean_identity.morpheme_signature == candidate.korean_identity.morpheme_signature
    assert restored.korean_identity.analyzer_fingerprint == (
        candidate.korean_identity.analyzer_fingerprint
    )


def test_non_korean_candidate_expire_reload_preserves_null_korean_identity() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-en-null-korean-identity",
        source_fingerprint="fixture-legacy-list",
        total_items=1,
    )

    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        source_type="word-list",
        normalized_source="running",
        candidate=make_candidate(
            status=GroundingStatus.GROUNDED,
            ipa="/ɹʌn/",
            warning_code=None,
        ),
    )
    session.commit()
    session.expire_all()

    row = repository.get_candidate_for_item(job.id, "line-1")
    assert row is not None
    assert row.korean_identity is None
    restored = repository.list_candidates(job.id)[0]
    assert restored.korean_identity is None
    assert restored.korean_frequency_evidence is None


def test_korean_frequency_provenance_survives_commit_expire_reload() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(source_type="frequency", language=SupportedLanguage.KO),
        run_key="run-ko-frequency-evidence",
        source_fingerprint="fixture-frequency",
        total_items=1,
    )
    candidate = make_korean_candidate(include_frequency_evidence=True)
    assert candidate.korean_frequency_evidence is not None

    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="level-1-rank-0017",
        source_type="frequency",
        normalized_source="학교",
        candidate=candidate,
    )
    session.commit()
    session.expire_all()

    row = repository.get_candidate_for_item(job.id, "level-1-rank-0017")
    assert row is not None
    assert row.frequency_bundle_sha256 == candidate.korean_frequency_evidence.bundle_sha256
    assert row.frequency_source_sha256 == candidate.korean_frequency_evidence.source_sha256
    assert row.source_review_receipt_sha256 == candidate.korean_frequency_evidence.source_review_receipt_sha256
    assert row.source_review_aggregate_sha256 == candidate.korean_frequency_evidence.source_review_aggregate_sha256
    assert "private_path" not in row.lexical_evidence

    restored = repository.list_candidates(job.id)[0]
    assert restored.korean_identity == candidate.korean_identity
    assert restored.korean_frequency_evidence == candidate.korean_frequency_evidence


def test_korean_frequency_provenance_rejects_identity_and_storage_drift() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(source_type="frequency", language=SupportedLanguage.KO),
        run_key="run-ko-frequency-drift",
        source_fingerprint="fixture-frequency",
        total_items=1,
    )
    candidate = make_korean_candidate(include_frequency_evidence=True)
    assert candidate.korean_frequency_evidence is not None

    bad_identity = candidate.korean_frequency_evidence.model_copy(update={"part_of_speech": "VA"})
    with pytest.raises(ValueError):
        LexicalCardCandidate.model_validate(
            candidate.model_dump(mode="json")
            | {"korean_frequency_evidence": bad_identity.model_dump(mode="json")}
        )

    repository.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="level-1-rank-0017",
        source_type="frequency",
        normalized_source="학교",
        candidate=candidate,
    )
    row = repository.get_candidate_for_item(job.id, "level-1-rank-0017")
    assert row is not None
    row.frequency_bundle_sha256 = _hash("different-bundle")
    session.add(row)
    session.commit()
    session.expire_all()

    with pytest.raises(ValueError):
        repository.list_candidates(job.id)
