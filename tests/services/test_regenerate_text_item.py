"""Tests for targeted Phase 3 text regeneration."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanMatchResult,
    KoreanMatchStatus,
    KoreanReasonCode,
    KoreanSignatureItem,
)
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
from multilang.services.korean_text_generation import KOREAN_TEXT_GENERATION_SELECTOR_VERSION
from multilang.services.language_identifier import LanguageDetectionResult
from multilang.services.text_generation import GeneratedSentence, GeneratedTextBundle, GeneratedTranslation
from multilang.services.text_validation import TextValidationResult, TextValidationService


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
            source="manual",
            definition=DefinitionRecord(source="manual", value=f"to {lemma}"),
            notes=[item_key],
        ),
    )


def make_bundle(
    *,
    sentence: str,
    translation: str,
    sentence_language: str = "en",
    translation_language: str = "pt",
) -> GeneratedTextBundle:
    return GeneratedTextBundle(
        sentence=GeneratedSentence(
            text=sentence,
            target_language=sentence_language,
            intended_sense="habit",
            uncertainty_notes=[],
            provenance=TextProvenance(source="generator", provider="fake-gen"),
        ),
        translation=GeneratedTranslation(
            text=translation,
            target_language=translation_language,
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
    request_metadata: list[dict[str, object]] = field(default_factory=list)

    def generate_bundle(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None = None,
        highlight_context: str | None = None,
        rate_limiter: object | None = None,
        job_id: str | None = None,
        korean_selector_attempt: object | None = None,
    ) -> GeneratedTextBundle:
        self.calls.append((candidate, deck_language))
        self.request_metadata.append(
            {
                "source_type": source_type,
                "highlight_context": highlight_context,
                "job_id": job_id,
                "korean_selector_attempt": korean_selector_attempt,
            }
        )
        return self.bundles.pop(0)


@dataclass
class FakeValidationService:
    results: list[TextValidationResult]
    calls: list[dict[str, object]] = field(default_factory=list)

    def validate(self, **kwargs: object) -> TextValidationResult:
        self.calls.append(kwargs)
        return self.results.pop(0)


@dataclass
class RecordingValidationService:
    delegate: TextValidationService
    calls: list[dict[str, object]] = field(default_factory=list)

    def validate(self, **kwargs: object) -> TextValidationResult:
        self.calls.append(kwargs)
        return self.delegate.validate(**kwargs)


class ExpectedLanguageIdentifier:
    def detect(self, value: str, *, expected_language: str | None = None) -> LanguageDetectionResult:
        return LanguageDetectionResult(
            detected_language=expected_language,
            confidence=1.0,
            reliable=True,
            provider="deterministic-test-identifier",
            detail="expected language",
        )


@dataclass
class FakeKoreanMatcher:
    fingerprint: KoreanAnalyzerFingerprint
    status: KoreanMatchStatus
    calls: list[tuple[str, KoreanLexicalIdentity]] = field(default_factory=list)

    def match_target(
        self,
        sentence_text: str,
        target: KoreanLexicalIdentity,
    ) -> KoreanMatchResult:
        self.calls.append((sentence_text, target))
        reasons = {
            KoreanMatchStatus.MATCHED: KoreanReasonCode.CONSENSUS_MATCH,
            KoreanMatchStatus.AMBIGUOUS: KoreanReasonCode.ANALYSIS_DISAGREEMENT,
            KoreanMatchStatus.UNAVAILABLE: KoreanReasonCode.ANALYZER_RUNTIME_ERROR,
        }
        alternatives = {
            KoreanMatchStatus.MATCHED: (True, True),
            KoreanMatchStatus.AMBIGUOUS: (True, False),
        }.get(self.status, ())
        return KoreanMatchResult(
            status=self.status,
            reason_code=reasons[self.status],
            analyzer_fingerprint=self.fingerprint,
            alternative_matches=alternatives,
        )


def make_korean_fingerprint(
    *, analyzer_package_version: str = "0.23.2"
) -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version=analyzer_package_version,
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
    )


def make_korean_identity(
    *, fingerprint: KoreanAnalyzerFingerprint,
) -> KoreanLexicalIdentity:
    return KoreanLexicalIdentity(
        submitted_form="먹다",
        canonical_nfc="먹다",
        lemma="먹다",
        part_of_speech="VV",
        sense_id="reviewed:eat:1",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="먹", pos="VV"),),
        analyzer_fingerprint=fingerprint,
        status="resolved",
    )


def make_persisted_korean_candidate(
    identity: KoreanLexicalIdentity,
) -> SimpleNamespace:
    return SimpleNamespace(
        id="lex-ko-1",
        item_key="ko:eat:1",
        source_type="word-list",
        submitted_form="먹다",
        display_form="먹다",
        lemma=identity.lemma,
        lemma_key=identity.lexical_key,
        frequency_rank=None,
        frequency_level=None,
        definitions_html="comer",
        definition_language="pt",
        ipa=None,
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED.value,
        warning_code=None,
        warning_detail=None,
        provenance={"source": "reviewed_test_fixture", "notes": []},
        korean_identity=identity.model_dump(mode="json"),
    )


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


@pytest.mark.parametrize("failure_kind", ["unavailable", "ambiguous", "drift"])
def test_korean_regeneration_passes_persisted_identity_on_both_attempts_and_stays_review_required(
    failure_kind: str,
) -> None:
    active_fingerprint = make_korean_fingerprint()
    persisted_fingerprint = (
        make_korean_fingerprint(analyzer_package_version="0.23.1")
        if failure_kind == "drift"
        else active_fingerprint
    )
    persisted_identity = make_korean_identity(fingerprint=persisted_fingerprint)
    persisted_candidate = make_persisted_korean_candidate(persisted_identity)
    existing_record = make_record(item_key=persisted_candidate.item_key)
    lexical_repository = FakeLexicalRepository(
        candidates={
            ("job-1", persisted_candidate.item_key): persisted_candidate,
        }
    )
    text_repository = FakeTextRepository(
        records={("job-1", persisted_candidate.item_key): existing_record}
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(
                sentence="저는 오늘 집에서 맛있는 밥을 먹었어요.",
                translation="Eu comi uma refeição deliciosa em casa hoje.",
                sentence_language="ko",
            ),
            make_bundle(
                sentence="오늘 저는 집에서 따뜻한 밥을 먹었어요.",
                translation="Hoje eu comi uma refeição quente em casa.",
                sentence_language="ko",
            ),
            make_bundle(
                sentence="오늘 집에서 밥을 천천히 먹었어요.",
                translation="Hoje eu comi arroz devagar em casa.",
                sentence_language="ko",
            ),
        ]
    )
    matcher = FakeKoreanMatcher(
        fingerprint=active_fingerprint,
        status={
            "unavailable": KoreanMatchStatus.UNAVAILABLE,
            "ambiguous": KoreanMatchStatus.AMBIGUOUS,
            "drift": KoreanMatchStatus.MATCHED,
        }[failure_kind],
    )
    validation = RecordingValidationService(
        TextValidationService(
            language_identifier=ExpectedLanguageIdentifier(),
            korean_matcher=matcher,
        )
    )
    job_repository = FakeJobRepository()
    service = RegenerateTextItemService(
        job_repository=job_repository,
        lexical_repository=lexical_repository,
        text_repository=text_repository,
        text_generation_service=generation,
        text_validation_service=validation,
    )

    regenerated = service.execute(
        job_id="job-1",
        item_key=persisted_candidate.item_key,
        deck_language=SupportedLanguage.KO,
    )

    assert len(generation.calls) == 3
    restored_candidate = generation.calls[0][0]
    restored_identity = restored_candidate.korean_identity
    assert isinstance(restored_identity, KoreanLexicalIdentity)
    assert restored_identity == persisted_identity
    assert restored_identity.model_dump(mode="json") == persisted_candidate.korean_identity
    assert all(call[0] is restored_candidate for call in generation.calls)
    assert [call[0].korean_identity for call in generation.calls] == [
        restored_identity,
        restored_identity,
        restored_identity,
    ]
    assert len(validation.calls) == 3
    assert all(call["korean_identity"] is restored_identity for call in validation.calls)
    if failure_kind == "drift":
        assert matcher.calls == []
    else:
        assert [target for _sentence, target in matcher.calls] == [
            restored_identity,
            restored_identity,
            restored_identity,
        ]

    assert regenerated.job_id == existing_record.job_id
    assert regenerated.item_key == existing_record.item_key
    assert regenerated.lexical_candidate_id == existing_record.lexical_candidate_id
    assert regenerated.generation_status is TextGenerationStatus.REPAIRED
    assert regenerated.review_status is ReviewStatus.REVIEW_REQUIRED
    assert regenerated.validation_status is ValidationStatus.FAILED
    assert regenerated.repair_attempt_count == 1
    assert regenerated.review_reason == ValidationFlagCode.MORPHOLOGY_MISMATCH.value
    morphology_flags = [
        flag
        for flag in regenerated.validation_flags
        if flag.code is ValidationFlagCode.MORPHOLOGY_MISMATCH
    ]
    assert len(morphology_flags) == 1
    expected_status = "fingerprint-mismatch" if failure_kind == "drift" else failure_kind
    assert expected_status in morphology_flags[0].detail
    assert persisted_identity.lemma not in morphology_flags[0].detail
    assert persisted_identity.sense_id not in morphology_flags[0].detail
    assert regenerated.example_sentence not in morphology_flags[0].detail
    assert len(text_repository.upserted) == 1
    assert job_repository.successes == [
        ("job-1", persisted_candidate.item_key, JobStage.GENERATE_TEXT)
    ]


def test_korean_regeneration_consumes_only_unused_repair_from_persisted_selector_history() -> None:
    fingerprint = make_korean_fingerprint()
    persisted_identity = make_korean_identity(fingerprint=fingerprint)
    persisted_candidate = make_persisted_korean_candidate(persisted_identity)
    initial_history = {
        "selector_version": KOREAN_TEXT_GENERATION_SELECTOR_VERSION,
        "initial_candidate_count": 2,
        "repair_attempt_count": 0,
        "attempts": [
            {
                "stage": "initial",
                "ordinal": 1,
                "candidate_sha256": "a" * 64,
                "validation_status": "failed",
                "rejection_codes": ["banned_pattern"],
            },
            {
                "stage": "initial",
                "ordinal": 2,
                "candidate_sha256": "b" * 64,
                "validation_status": "failed",
                "rejection_codes": ["translation_mismatch"],
            },
        ],
    }
    existing_record = make_record(item_key=persisted_candidate.item_key).model_copy(
        update={
            "repair_attempt_count": 0,
            "sentence_provenance": TextProvenance(
                source="generator",
                provider="fake-gen",
                metadata={"korean_selector_history": initial_history},
            ),
        }
    )
    lexical_repository = FakeLexicalRepository(
        candidates={("job-1", persisted_candidate.item_key): persisted_candidate}
    )
    text_repository = FakeTextRepository(
        records={("job-1", persisted_candidate.item_key): existing_record}
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(
                sentence="오늘 집에서 밥을 먹어요.",
                translation="Hoje eu como arroz em casa.",
                sentence_language="ko",
            )
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.94)
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
        item_key=persisted_candidate.item_key,
        deck_language=SupportedLanguage.KO,
    )

    assert len(generation.calls) == 1
    attempt = generation.request_metadata[0]["korean_selector_attempt"]
    assert attempt.stage == "repair"
    assert attempt.ordinal == 3
    assert attempt.rejected_candidate_sha256s == ("a" * 64, "b" * 64)
    assert attempt.rejection_codes == ("banned_pattern", "translation_mismatch")
    history = regenerated.sentence_provenance.metadata["korean_selector_history"]
    assert history["initial_candidate_count"] == 2
    assert history["repair_attempt_count"] == 1
    assert [entry["stage"] for entry in history["attempts"]] == ["initial", "initial", "repair"]
    assert regenerated.repair_attempt_count == 1
