"""Tests for targeted Phase 3 text regeneration."""

from __future__ import annotations

from dataclasses import dataclass, field

from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.lexicon import DefinitionRecord, GroundingStatus, LexicalCardCandidate, LexicalProvenance
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
from multilang.services.regenerate_text_item import RegenerateTextItemService
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


def make_record(*, item_key: str, status: ValidationStatus = ValidationStatus.FAILED) -> TextQualityRecord:
    return TextQualityRecord(
        job_id="job-1",
        item_key=item_key,
        lexical_candidate_id=f"lex-{item_key}",
        example_sentence=f"old sentence for {item_key}",
        translation_text=f"old translation for {item_key}",
        generation_status=TextGenerationStatus.REPAIRED,
        validation_status=status,
        review_status=(ReviewStatus.ACCEPTED if status is ValidationStatus.PASSED else ReviewStatus.REVIEW_REQUIRED),
        repair_attempt_count=1,
        confidence_score=0.25,
        confidence_label=ConfidenceLabel.LOW,
        validation_flags=[
            ValidationFlag(code=ValidationFlagCode.LOW_CONFIDENCE, detail="old flagged state")
        ],
        review_reason="low_confidence",
        sentence_provenance=TextProvenance(source="generator"),
        translation_provenance=TextProvenance(source="translator"),
    )


@dataclass
class PersistedCandidate:
    id: str
    item_key: str
    candidate: LexicalCardCandidate


@dataclass
class FakeLexicalRepository:
    candidates: dict[tuple[str, str], PersistedCandidate]
    calls: list[tuple[str, str]] = field(default_factory=list)

    def get_candidate_for_item(self, job_id: str, item_key: str) -> PersistedCandidate | None:
        self.calls.append((job_id, item_key))
        return self.candidates.get((job_id, item_key))


@dataclass
class FakeTextRepository:
    records: dict[tuple[str, str], TextQualityRecord]
    upserted: list[TextQualityRecord] = field(default_factory=list)

    def get_text_record(self, job_id: str, item_key: str) -> TextQualityRecord | None:
        return self.records.get((job_id, item_key))

    def list_example_sentences_for_job(
        self,
        job_id: str,
        *,
        exclude_item_key: str | None = None,
    ) -> list[str]:
        return [
            record.example_sentence
            for (record_job_id, record_item_key), record in self.records.items()
            if record_job_id == job_id and record.example_sentence and record_item_key != exclude_item_key
        ]

    def upsert_text_record(self, record: TextQualityRecord) -> TextQualityRecord:
        self.upserted.append(record)
        self.records[(record.job_id, record.item_key)] = record
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


def test_regenerate_text_item_updates_only_requested_row() -> None:
    lexical_repository = FakeLexicalRepository(
        candidates={
            ("job-1", "line-1"): PersistedCandidate(
                id="lex-line-1", item_key="line-1", candidate=make_candidate(item_key="line-1")
            )
        }
    )
    text_repository = FakeTextRepository(
        records={
            ("job-1", "line-1"): make_record(item_key="line-1"),
            ("job-1", "line-2"): make_record(item_key="line-2", status=ValidationStatus.PASSED),
        }
    )
    generation = FakeGenerationService(
        bundles=[make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa.")]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(
                status=ValidationStatus.PASSED,
                label=ConfidenceLabel.HIGH,
                score=0.93,
            )
        ]
    )

    service = RegenerateTextItemService(
        job_repository=FakeJobRepository(),
        lexical_repository=lexical_repository,
        text_repository=text_repository,
        text_generation_service=generation,
        text_validation_service=validation,
    )

    regenerated = service.execute(
        job_id="job-1",
        item_key="line-1",
        deck_language=SupportedLanguage.EN,
    )

    assert regenerated.item_key == "line-1"
    assert regenerated.example_sentence == "I wash the cup at home."
    assert regenerated.review_status is ReviewStatus.ACCEPTED
    assert text_repository.records[("job-1", "line-2")].example_sentence == "old sentence for line-2"
    assert len(text_repository.records) == 2
    assert len(text_repository.upserted) == 1


def test_regenerate_text_item_reuses_grounded_lexical_candidate() -> None:
    candidate = make_candidate(lemma="wash", item_key="line-1")
    lexical_repository = FakeLexicalRepository(
        candidates={
            ("job-1", "line-1"): PersistedCandidate(id="lex-line-1", item_key="line-1", candidate=candidate)
        }
    )
    text_repository = FakeTextRepository(records={("job-1", "line-1"): make_record(item_key="line-1")})
    generation = FakeGenerationService(
        bundles=[make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa.")]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(
                status=ValidationStatus.PASSED,
                label=ConfidenceLabel.HIGH,
                score=0.91,
            )
        ]
    )

    service = RegenerateTextItemService(
        job_repository=FakeJobRepository(),
        lexical_repository=lexical_repository,
        text_repository=text_repository,
        text_generation_service=generation,
        text_validation_service=validation,
    )

    service.execute(job_id="job-1", item_key="line-1", deck_language=SupportedLanguage.EN)

    assert lexical_repository.calls == [("job-1", "line-1")]
    assert generation.calls == [(candidate, SupportedLanguage.EN)]
    assert validation.calls[0]["display_form"] == "wash"
    assert validation.calls[0]["lemma"] == "wash"


def test_regenerate_text_item_keeps_failed_item_flagged_in_place() -> None:
    lexical_repository = FakeLexicalRepository(
        candidates={
            ("job-1", "line-1"): PersistedCandidate(
                id="lex-line-1", item_key="line-1", candidate=make_candidate(item_key="line-1")
            )
        }
    )
    text_repository = FakeTextRepository(records={("job-1", "line-1"): make_record(item_key="line-1")})
    failed = make_validation_result(
        status=ValidationStatus.FAILED,
        label=ConfidenceLabel.LOW,
        score=0.18,
        flags=[
            ValidationFlag(
                code=ValidationFlagCode.TRANSLATION_MISMATCH,
                detail="translation copied from definition",
            )
        ],
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="I wash every day.", translation="to wash"),
            make_bundle(sentence="Wash every day.", translation="to wash"),
        ]
    )
    validation = FakeValidationService(results=[failed, failed])

    service = RegenerateTextItemService(
        job_repository=FakeJobRepository(),
        lexical_repository=lexical_repository,
        text_repository=text_repository,
        text_generation_service=generation,
        text_validation_service=validation,
    )

    regenerated = service.execute(
        job_id="job-1",
        item_key="line-1",
        deck_language=SupportedLanguage.EN,
    )

    assert regenerated.review_status is ReviewStatus.REVIEW_REQUIRED
    assert regenerated.validation_status is ValidationStatus.FAILED
    assert regenerated.repair_attempt_count == 1
    assert regenerated.review_reason == "translation_mismatch"
    assert len(text_repository.records) == 1
    assert len(text_repository.upserted) == 1


def test_regenerate_text_item_flags_duplicate_sentence_against_other_cards() -> None:
    lexical_repository = FakeLexicalRepository(
        candidates={
            ("job-1", "line-1"): PersistedCandidate(
                id="lex-line-1", item_key="line-1", candidate=make_candidate(item_key="line-1")
            )
        }
    )
    text_repository = FakeTextRepository(
        records={
            ("job-1", "line-1"): make_record(item_key="line-1"),
            ("job-1", "line-2"): make_record(item_key="line-2", status=ValidationStatus.PASSED).model_copy(
                update={"example_sentence": "I wash the cup at home."}
            ),
        }
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
            make_bundle(sentence="I wash the cup tonight.", translation="Eu lavo a xícara esta noite."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(
                status=ValidationStatus.FAILED,
                label=ConfidenceLabel.LOW,
                score=0.42,
                flags=[
                    ValidationFlag(
                        code=ValidationFlagCode.DUPLICATE_SENTENCE,
                        detail="sentence must be unique across cards in the same deck generation job",
                    )
                ],
            ),
            make_validation_result(
                status=ValidationStatus.PASSED,
                label=ConfidenceLabel.HIGH,
                score=0.9,
            ),
        ]
    )

    service = RegenerateTextItemService(
        job_repository=FakeJobRepository(),
        lexical_repository=lexical_repository,
        text_repository=text_repository,
        text_generation_service=generation,
        text_validation_service=validation,
    )

    regenerated = service.execute(job_id="job-1", item_key="line-1", deck_language=SupportedLanguage.EN)

    assert regenerated.example_sentence == "I wash the cup tonight."
    assert regenerated.review_status is ReviewStatus.ACCEPTED
    assert validation.calls[0]["disallowed_sentence_texts"] == {"i wash the cup at home"}
    assert validation.calls[1]["disallowed_sentence_texts"] == {"i wash the cup at home"}
