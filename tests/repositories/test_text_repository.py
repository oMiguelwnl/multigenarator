"""Repository tests for persisted text-quality rows."""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import LexicalCandidate
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
    PronunciationRecord,
)
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.text_repository import TextRepository


def build_repositories() -> tuple[TextRepository, LexicalRepository, JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return TextRepository(session), LexicalRepository(session), JobRepository(session), session


def make_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.EN, source_type="word-list", input_file=None)


def make_candidate(*, lemma: str, translation_target_language: str = "pt") -> LexicalCardCandidate:
    return LexicalCardCandidate(
        submitted_form=lemma,
        display_form=lemma,
        lemma=lemma,
        lemma_key=f"en:{lemma}",
        frequency_rank=12,
        frequency_level=1,
        definitions_html=f"definition for {lemma}",
        definition_language="en",
        ipa=f"/{lemma}/",
        translation_target_language=translation_target_language,
        grounding_status=GroundingStatus.GROUNDED,
        warning_code=None,
        warning_detail=None,
        provenance=LexicalProvenance(
            source="kaikki",
            definition=DefinitionRecord(source="kaikki", value=f"definition for {lemma}"),
            pronunciation=PronunciationRecord(source="kaikki", value=f"/{lemma}/"),
        ),
    )


def make_record(*, lexical_candidate_id: str, job_id: str, item_key: str, **overrides: object) -> TextQualityRecord:
    payload: dict[str, object] = {
        "job_id": job_id,
        "item_key": item_key,
        "lexical_candidate_id": lexical_candidate_id,
        "example_sentence": f"I can {item_key} today.",
        "translation_text": f"Eu consigo {item_key} hoje.",
        "generation_status": TextGenerationStatus.GENERATED,
        "validation_status": ValidationStatus.PASSED,
        "review_status": ReviewStatus.ACCEPTED,
        "repair_attempt_count": 0,
        "confidence_score": 0.82,
        "confidence_label": ConfidenceLabel.MEDIUM,
        "validation_flags": [],
        "review_reason": None,
        "sentence_provenance": TextProvenance(
            source="generator",
            provider="openai",
            model="gpt-4.1-mini",
            metadata={"prompt_version": "sentence-v1"},
        ),
        "translation_provenance": TextProvenance(
            source="translator",
            provider="deepl",
            model="api",
            metadata={"glossary": "disabled"},
        ),
    }
    payload.update(overrides)
    return TextQualityRecord(**payload)


def seed_lexical_candidate(
    lexical_repository: LexicalRepository,
    session: Session,
    *,
    job_id: str,
    run_key: str,
    item_key: str,
    lemma: str,
) -> LexicalCandidate:
    lexical_repository.upsert_candidate(
        job_id=job_id,
        run_key=run_key,
        item_key=item_key,
        source_type="word-list",
        normalized_source=lemma,
        candidate=make_candidate(lemma=lemma),
    )
    return session.query(LexicalCandidate).filter_by(job_id=job_id, item_key=item_key).one()


def test_upsert_text_record_updates_existing_row() -> None:
    repository, lexical_repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-en-text",
        source_fingerprint="list-a",
        total_items=1,
    )
    lexical = seed_lexical_candidate(
        lexical_repository,
        session,
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        lemma="run",
    )

    repository.upsert_text_record(
        make_record(
            lexical_candidate_id=lexical.id,
            job_id=job.id,
            item_key="line-1",
            generation_status=TextGenerationStatus.GENERATED,
            validation_status=ValidationStatus.FAILED,
            review_status=ReviewStatus.NOT_REVIEWED,
            confidence_score=0.44,
            confidence_label=ConfidenceLabel.LOW,
            validation_flags=[
                ValidationFlag(
                    code=ValidationFlagCode.LOW_CONFIDENCE,
                    detail="judge requested review",
                )
            ],
        )
    )
    updated = repository.upsert_text_record(
        make_record(
            lexical_candidate_id=lexical.id,
            job_id=job.id,
            item_key="line-1",
            example_sentence="I run outside every morning.",
            translation_text="Eu corro lá fora todas as manhãs.",
            confidence_score=0.91,
            confidence_label=ConfidenceLabel.HIGH,
        )
    )

    assert session.execute(
        text("SELECT COUNT(*) FROM text_quality_records WHERE job_id = :job_id AND item_key = :item_key"),
        {"job_id": job.id, "item_key": "line-1"},
    ).scalar_one() == 1
    assert updated.example_sentence == "I run outside every morning."
    assert updated.confidence_label is ConfidenceLabel.HIGH
    assert updated.validation_flags == []


def test_repository_queries_return_flagged_and_accepted_records() -> None:
    repository, lexical_repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-en-text",
        source_fingerprint="list-b",
        total_items=2,
    )
    accepted = seed_lexical_candidate(
        lexical_repository,
        _,
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        lemma="read",
    )
    flagged = seed_lexical_candidate(
        lexical_repository,
        _,
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-2",
        lemma="write",
    )

    repository.upsert_text_record(
        make_record(lexical_candidate_id=accepted.id, job_id=job.id, item_key="line-1")
    )
    repository.upsert_text_record(
        make_record(
            lexical_candidate_id=flagged.id,
            job_id=job.id,
            item_key="line-2",
            validation_status=ValidationStatus.FAILED,
            review_status=ReviewStatus.REVIEW_REQUIRED,
            review_reason="translation mismatch after repair",
            repair_attempt_count=1,
            validation_flags=[
                ValidationFlag(
                    code=ValidationFlagCode.TRANSLATION_MISMATCH,
                    detail="translation omits the subject",
                )
            ],
        )
    )

    records = repository.list_records_for_job(job.id)
    flagged_records = repository.list_flagged_records(job.id)

    assert [record.item_key for record in records if record.review_status is ReviewStatus.ACCEPTED] == ["line-1"]
    assert [record.item_key for record in flagged_records] == ["line-2"]
    assert flagged_records[0].review_reason == "translation mismatch after repair"


def test_list_generation_candidates_and_round_trip_structured_fields() -> None:
    repository, lexical_repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-en-text",
        source_fingerprint="list-c",
        total_items=3,
    )
    pending = seed_lexical_candidate(
        lexical_repository,
        _,
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-1",
        lemma="sing",
    )
    review = seed_lexical_candidate(
        lexical_repository,
        _,
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-2",
        lemma="dance",
    )
    accepted = seed_lexical_candidate(
        lexical_repository,
        _,
        job_id=job.id,
        run_key=job.run_key,
        item_key="line-3",
        lemma="cook",
    )

    repository.upsert_text_record(
        make_record(
            lexical_candidate_id=review.id,
            job_id=job.id,
            item_key="line-2",
            generation_status=TextGenerationStatus.REPAIRED,
            validation_status=ValidationStatus.FAILED,
            review_status=ReviewStatus.REVIEW_REQUIRED,
            repair_attempt_count=1,
            confidence_score=0.35,
            confidence_label=ConfidenceLabel.LOW,
            validation_flags=[
                ValidationFlag(code=ValidationFlagCode.LOW_CONFIDENCE, detail="score below threshold")
            ],
            sentence_provenance=TextProvenance(
                source="generator",
                provider="openai",
                model="gpt-4.1-mini",
                metadata={"repair": True},
            ),
            translation_provenance=TextProvenance(
                source="translator",
                provider="deepl",
                model="api",
                metadata={"repair": True},
            ),
        )
    )
    repository.upsert_text_record(
        make_record(lexical_candidate_id=accepted.id, job_id=job.id, item_key="line-3")
    )

    stored = repository.get_text_record(job.id, "line-2")
    candidates = repository.list_generation_candidates(job.id)

    assert stored is not None
    assert stored.validation_flags[0].code is ValidationFlagCode.LOW_CONFIDENCE
    assert stored.sentence_provenance.metadata["repair"] is True
    assert stored.translation_provenance.metadata["repair"] is True
    assert [candidate.item_key for candidate in candidates] == ["line-1", "line-2"]
    assert candidates[0].lemma == pending.lemma
