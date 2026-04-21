"""Tests for the bounded generate/validate/repair text pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.lexicon import DefinitionRecord, GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.generate_text_items import GenerateTextItemsService
from multilang.services.text_generation import GeneratedSentence, GeneratedTextBundle, GeneratedTranslation
from multilang.services.text_validation import TextValidationResult


def make_candidate(*, lemma: str = "wash", item_key: str = "line-1") -> LexicalCardCandidate:
    return LexicalCardCandidate(
        submitted_form=lemma,
        display_form=lemma,
        lemma=lemma,
        lemma_key=f"en:{lemma}",
        definitions_html=f"to {lemma}",
        definition_language="en",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(
            source="kaikki",
            definition=DefinitionRecord(source="kaikki", value=f"to {lemma}"),
            notes=[item_key],
        ),
    )


def make_bundle(*, sentence: str, translation: str) -> GeneratedTextBundle:
    return GeneratedTextBundle(
        sentence=GeneratedSentence(
            text=sentence,
            target_language="en",
            intended_sense="habit",
            uncertainty_notes=[],
            provenance=TextProvenance(source="generator", provider="fake-gen"),
        ),
        translation=GeneratedTranslation(
            text=translation,
            target_language="pt",
            provenance=TextProvenance(source="translator", provider="fake-translate"),
        ),
    )


def make_validation_result(
    *,
    status: ValidationStatus,
    label: ConfidenceLabel,
    score: float,
    flags: list[ValidationFlag] | None = None,
) -> TextValidationResult:
    return TextValidationResult(
        validation_status=status,
        confidence_label=label,
        confidence_score=score,
        validation_flags=flags or [],
    )


@dataclass
class FakeTextRepository:
    candidates: list[object]
    saved_records: list[object] = field(default_factory=list)

    def list_generation_candidates(self, job_id: str) -> list[object]:
        return list(self.candidates)

    def upsert_text_record(self, record: object) -> object:
        self.saved_records.append(record)
        return record


@dataclass
class FakeJobRepository:
    successes: list[tuple[str, str, JobStage]] = field(default_factory=list)

    def record_item_success(self, job_id: str, *, item_key: str, completed_stage: JobStage) -> None:
        self.successes.append((job_id, item_key, completed_stage))


@dataclass
class FakeGenerationService:
    bundles: list[GeneratedTextBundle]
    calls: list[tuple[LexicalCardCandidate, SupportedLanguage]] = field(default_factory=list)

    def generate_bundle(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
    ) -> GeneratedTextBundle:
        self.calls.append((candidate, deck_language))
        return self.bundles.pop(0)


@dataclass
class FakeValidationService:
    results: list[TextValidationResult]
    calls: list[dict[str, object]] = field(default_factory=list)

    def validate(self, **kwargs: object) -> TextValidationResult:
        self.calls.append(kwargs)
        return self.results.pop(0)


@dataclass
class PersistedCandidate:
    id: str
    item_key: str
    candidate: LexicalCardCandidate


def test_generate_text_items_repairs_once_then_accepts() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate())]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="They practice every morning.", translation="Eles praticam todas as manhãs."),
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(
                status=ValidationStatus.FAILED,
                label=ConfidenceLabel.LOW,
                score=0.31,
                flags=[
                    ValidationFlag(
                        code=ValidationFlagCode.MISSING_TARGET_LEMMA,
                        detail="missing target form",
                    )
                ],
            ),
            make_validation_result(
                status=ValidationStatus.PASSED,
                label=ConfidenceLabel.HIGH,
                score=0.92,
            ),
        ]
    )
    job_repository = FakeJobRepository()

    service = GenerateTextItemsService(
        job_repository=job_repository,
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 1
    assert result.accepted_items == 1
    assert result.review_required_items == 0
    assert len(repository.saved_records) == 1
    assert repository.saved_records[0].generation_status is TextGenerationStatus.REPAIRED
    assert repository.saved_records[0].review_status is ReviewStatus.ACCEPTED
    assert repository.saved_records[0].repair_attempt_count == 1
    assert job_repository.successes == [("job-1", "line-1", JobStage.GENERATE_TEXT)]


def test_generate_text_items_flags_review_after_one_failed_repair() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate())]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="They practice every morning.", translation="Eles praticam todas as manhãs."),
            make_bundle(sentence="Practice every morning.", translation="to wash"),
        ]
    )
    failed_result = make_validation_result(
        status=ValidationStatus.FAILED,
        label=ConfidenceLabel.LOW,
        score=0.22,
        flags=[
            ValidationFlag(
                code=ValidationFlagCode.TRANSLATION_MISMATCH,
                detail="translation copied from definition",
            )
        ],
    )
    validation = FakeValidationService(results=[failed_result, failed_result])
    job_repository = FakeJobRepository()

    service = GenerateTextItemsService(
        job_repository=job_repository,
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 1
    assert result.accepted_items == 0
    assert result.review_required_items == 1
    assert len(repository.saved_records) == 1
    saved = repository.saved_records[0]
    assert saved.review_status is ReviewStatus.REVIEW_REQUIRED
    assert saved.validation_status is ValidationStatus.FAILED
    assert saved.repair_attempt_count == 1
    assert saved.review_reason == "translation_mismatch"
    assert saved.validation_flags[0].code is ValidationFlagCode.TRANSLATION_MISMATCH
    assert job_repository.successes == [("job-1", "line-1", JobStage.GENERATE_TEXT)]
