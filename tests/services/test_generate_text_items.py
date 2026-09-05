"""Tests for the bounded generate/validate/repair text pipeline."""

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
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.generate_text_items import GenerateTextItemsService
from multilang.services.language_identifier import LanguageDetectionResult
from multilang.services.text_generation import (
    DefinitionGenerationResult,
    GeneratedSentence,
    GeneratedTextBundle,
    GeneratedTranslation,
    SentenceGenerationFallback,
    SentenceGenerationResult,
    SentenceTranslationResult,
)
from multilang.services.text_validation import TextValidationResult, TextValidationService


def make_candidate(
    *,
    lemma: str = "wash",
    item_key: str = "line-1",
    frequency_rank: int | None = None,
    frequency_level: int | None = None,
    translation_target_language: str = "pt",
) -> LexicalCardCandidate:
    return LexicalCardCandidate(
        submitted_form=lemma,
        display_form=lemma,
        lemma=lemma,
        lemma_key=f"en:{lemma}",
        frequency_rank=frequency_rank,
        frequency_level=frequency_level,
        definitions_html=f"to {lemma}",
        definition_language="en",
        translation_target_language=translation_target_language,
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


def make_local_bundle(*, sentence: str, translation: str) -> GeneratedTextBundle:
    return GeneratedTextBundle(
        sentence=GeneratedSentence(
            text=sentence,
            target_language="en",
            intended_sense="habit",
            uncertainty_notes=[],
            provenance=TextProvenance(
                source="local",
                provider="local",
                metadata={"source": "runtime-local-generator", "template_kind": "term"},
            ),
        ),
        translation=GeneratedTranslation(
            text=translation,
            target_language="pt",
            provenance=TextProvenance(
                source="local",
                provider="local",
                metadata={"source": "runtime-local-translator"},
            ),
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
    existing_sentences: list[str] = field(default_factory=list)
    missing_only_calls: list[bool] = field(default_factory=list)
    claim_calls: list[dict[str, object]] = field(default_factory=list)
    records: dict[tuple[str, str], object] = field(default_factory=dict)

    def list_generation_candidates(self, job_id: str, *, missing_only: bool = False) -> list[object]:
        self.missing_only_calls.append(missing_only)
        return list(self.candidates)

    def list_repair_candidates(self, job_id: str, *, max_items: int | None = None) -> list[object]:
        return list(self.candidates[:max_items]) if max_items is not None else list(self.candidates)

    def claim_generation_candidates(self, job_id: str, *, missing_only: bool = False, limit: int | None = None) -> list[object]:
        self.claim_calls.append({"job_id": job_id, "missing_only": missing_only, "limit": limit})
        rows = list(self.candidates)
        return rows[:limit] if limit is not None else rows

    def list_example_sentences_for_job(
        self,
        job_id: str,
        *,
        exclude_item_key: str | None = None,
    ) -> list[str]:
        return list(self.existing_sentences)

    def get_text_record(self, job_id: str, item_key: str) -> object | None:
        return self.records.get((job_id, item_key))

    def upsert_text_record(self, record: object) -> object:
        self.saved_records.append(record)
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
    fallback_calls: list[tuple[LexicalCardCandidate, SupportedLanguage, SentenceGenerationFallback]] = field(
        default_factory=list
    )

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

    def generate_bundle_from_fallback(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        fallback: SentenceGenerationFallback,
        source_type: str | None = None,
        highlight_context: str | None = None,
        rate_limiter: object | None = None,
        job_id: str | None = None,
    ) -> GeneratedTextBundle:
        self.fallback_calls.append((candidate, deck_language, fallback))
        self.request_metadata.append({"source_type": source_type, "highlight_context": highlight_context})
        return self.bundles.pop(0)


@dataclass
class FakeHighlightRecord:
    highlight_id: str
    normalized_text: str


@dataclass
class FakeHighlightImportRepository:
    records: dict[tuple[str, str], FakeHighlightRecord]

    def get_private_record(self, job_id: str, highlight_id: str) -> FakeHighlightRecord | None:
        return self.records.get((job_id, highlight_id))


@dataclass
class FakeTatoebaSentenceSource:
    fallback: SentenceGenerationResult | None
    calls: list[dict[str, object]] = field(default_factory=list)

    def select_sentence(self, **kwargs: object) -> SentenceGenerationResult | None:
        self.calls.append(kwargs)
        return self.fallback


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
        reason_code = (
            KoreanReasonCode.ANALYSIS_DISAGREEMENT
            if self.status is KoreanMatchStatus.AMBIGUOUS
            else KoreanReasonCode.ANALYZER_RUNTIME_ERROR
        )
        return KoreanMatchResult(
            status=self.status,
            reason_code=reason_code,
            analyzer_fingerprint=self.fingerprint,
            alternative_matches=(True, False)
            if self.status is KoreanMatchStatus.AMBIGUOUS
            else (),
        )


def make_korean_fingerprint() -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
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


@dataclass
class PersistedCandidate:
    id: str
    item_key: str
    candidate: LexicalCardCandidate
    source_type: str = "word-list"


@dataclass
class RecordingFieldTextService:
    calls: list[tuple[str, object]] = field(default_factory=list)

    def generate_definition(self, request: object) -> DefinitionGenerationResult:
        self.calls.append(("definition", request))
        return DefinitionGenerationResult(
            definitions_html="to wash carefully",
            provenance={"provider": "field-text", "route": "definition"},
        )

    def generate_sentence(self, request: object) -> SentenceGenerationResult:
        self.calls.append(("sentence", request))
        return SentenceGenerationResult(
            sentence="I wash the cup at home.",
            intended_sense="habit",
            provenance={"provider": "field-text", "route": "sentence"},
        )


@dataclass
class RecordingTranslationAdapter:
    calls: list[object] = field(default_factory=list)

    def translate_sentence(self, request: object) -> SentenceTranslationResult:
        self.calls.append(request)
        return SentenceTranslationResult(
            translation="Eu lavo a xicara em casa.",
            provenance={"provider": "field-translation"},
        )


@dataclass
class RecordingAudioPort:
    label: str
    events: list[str]
    calls: list[object] = field(default_factory=list)

    def synthesize(self, request: object) -> object:
        self.events.append(f"{self.label}:call")
        self.calls.append(request)
        return SimpleNamespace(artifact_sha256="f" * 64, storage_path=getattr(request, "final_path"))


@dataclass
class RecordingFieldReviewRepository:
    events: list[str] = field(default_factory=list)
    candidate_revisions: list[dict[str, object]] = field(default_factory=list)
    audio_reservations: list[dict[str, object]] = field(default_factory=list)

    def create_candidate_revision(self, **kwargs: object) -> object:
        self.events.append(f"revision:{kwargs['field_name']}")
        self.candidate_revisions.append(kwargs)
        return SimpleNamespace(
            revision=SimpleNamespace(
                revision_id=f"rev-{kwargs['field_name']}-{len(self.candidate_revisions)}",
                value_sha256=kwargs["value_sha256"],
            ),
            pointer_version=int(kwargs["expected_pointer_version"]) + 1,
            pointer_status="needs_review",
            replayed=False,
        )

    def reserve_audio_publication(self, **kwargs: object) -> object:
        self.events.append(f"reserve:{kwargs['field_name']}")
        self.audio_reservations.append(kwargs)
        return SimpleNamespace(
            reservation_id=f"res-{kwargs['field_name']}-{len(self.audio_reservations)}",
            final_path=kwargs["final_path"],
            state="reserved",
            version=0,
        )


class PoisonPort:
    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"unexpected fallback call to {name}")


def build_field_dispatch_service(
    *,
    text_service: object | None = None,
    translation_adapter: object | None = None,
    word_audio_port: object | None = None,
    sentence_audio_port: object | None = None,
    review_repository: RecordingFieldReviewRepository | None = None,
) -> tuple[GenerateTextItemsService, RecordingFieldReviewRepository]:
    review_repository = review_repository or RecordingFieldReviewRepository()
    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=FakeTextRepository(candidates=[]),
        text_generation_service=text_service or RecordingFieldTextService(),
        text_validation_service=FakeValidationService(results=[]),
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
        review_repository=review_repository,
        translation_adapter=translation_adapter,
        word_audio_port=word_audio_port,
        sentence_audio_port=sentence_audio_port,
    )
    return service, review_repository


def test_definition_text_dispatch_sentence_microexample_text_dispatch_and_unknown_field_no_fallback() -> None:
    text_service = RecordingFieldTextService()
    service, review_repository = build_field_dispatch_service(
        text_service=text_service,
        translation_adapter=PoisonPort(),
        word_audio_port=PoisonPort(),
        sentence_audio_port=PoisonPort(),
    )
    candidate = make_candidate()

    definition = service.regenerate_field(
        job_id="job-1",
        item_id="item-1",
        field_name="definition",
        candidate=candidate,
        deck_language=SupportedLanguage.EN,
        request_id="def-1",
        expected_pointer_version=0,
    )
    sentence = service.regenerate_field(
        job_id="job-1",
        item_id="item-1",
        field_name="sentence",
        candidate=candidate,
        deck_language=SupportedLanguage.EN,
        request_id="sent-1",
        expected_pointer_version=0,
    )
    microexample = service.regenerate_field(
        job_id="job-1",
        item_id="item-1",
        field_name="microexample",
        candidate=candidate,
        deck_language=SupportedLanguage.EN,
        request_id="micro-1",
        expected_pointer_version=0,
    )

    assert [call[0] for call in text_service.calls] == ["definition", "sentence", "sentence"]
    assert [row["field_name"] for row in review_repository.candidate_revisions] == [
        "definition",
        "sentence",
        "microexample",
    ]
    assert definition.field_name == "definition"
    assert sentence.field_name == "sentence"
    assert microexample.field_name == "microexample"
    assert {result.pointer_status for result in (definition, sentence, microexample)} == {"needs_review"}

    before = list(text_service.calls)
    with pytest.raises(ValueError):
        service.regenerate_field(
            job_id="job-1",
            item_id="item-1",
            field_name="grammar",
            candidate=candidate,
            deck_language=SupportedLanguage.EN,
            request_id="unknown-1",
            expected_pointer_version=0,
        )
    assert text_service.calls == before
    assert len(review_repository.candidate_revisions) == 3


def test_translation_adapter_dispatch_uses_exact_translation_adapter_without_text_fallback() -> None:
    text_service = PoisonPort()
    translation_adapter = RecordingTranslationAdapter()
    service, review_repository = build_field_dispatch_service(
        text_service=text_service,
        translation_adapter=translation_adapter,
        word_audio_port=PoisonPort(),
        sentence_audio_port=PoisonPort(),
    )

    result = service.regenerate_field(
        job_id="job-1",
        item_id="item-1",
        field_name="translation",
        candidate=make_candidate(),
        deck_language=SupportedLanguage.EN,
        request_id="translation-1",
        expected_pointer_version=0,
        sentence_text="I wash the cup at home.",
        intended_sense="habit",
    )

    assert len(translation_adapter.calls) == 1
    assert getattr(translation_adapter.calls[0], "sentence") == "I wash the cup at home."
    assert getattr(translation_adapter.calls[0], "translation_target_language") == "pt"
    assert result.field_name == "translation"
    assert review_repository.candidate_revisions[0]["field_name"] == "translation"


def test_word_audio_port_dispatch_and_sentence_audio_port_dispatch_audio_reservation_before_call() -> None:
    events: list[str] = []
    word_audio = RecordingAudioPort(label="word", events=events)
    sentence_audio = RecordingAudioPort(label="sentence", events=events)
    review_repository = RecordingFieldReviewRepository(events=events)
    service, review_repository = build_field_dispatch_service(
        text_service=PoisonPort(),
        translation_adapter=PoisonPort(),
        word_audio_port=word_audio,
        sentence_audio_port=sentence_audio,
        review_repository=review_repository,
    )
    candidate = make_candidate()

    word_result = service.regenerate_field(
        job_id="job-1",
        item_id="item-1",
        field_name="word_audio",
        candidate=candidate,
        deck_language=SupportedLanguage.EN,
        request_id="word-audio-1",
        expected_pointer_version=2,
        field_revision_id="rev-word-audio-1",
        field_revision_value_sha256="a" * 64,
        authority_sha256="b" * 64,
        root_prestate_sha256="c" * 64,
    )
    sentence_result = service.regenerate_field(
        job_id="job-1",
        item_id="item-1",
        field_name="sentence_audio",
        candidate=candidate,
        deck_language=SupportedLanguage.EN,
        request_id="sentence-audio-1",
        expected_pointer_version=3,
        sentence_text="I wash the cup at home.",
        field_revision_id="rev-sentence-audio-1",
        field_revision_value_sha256="d" * 64,
        authority_sha256="b" * 64,
        root_prestate_sha256="c" * 64,
    )

    assert events == ["reserve:word_audio", "word:call", "reserve:sentence_audio", "sentence:call"]
    assert getattr(word_audio.calls[0], "text") == candidate.display_form
    assert getattr(sentence_audio.calls[0], "text") == "I wash the cup at home."
    assert [row["field_name"] for row in review_repository.audio_reservations] == [
        "word_audio",
        "sentence_audio",
    ]
    assert word_result.audio_reservation_id == "res-word_audio-1"
    assert sentence_result.audio_reservation_id == "res-sentence_audio-2"


def test_generate_text_items_limits_eligible_candidates_after_missing_only_selection() -> None:
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate(item_key="line-1")),
            PersistedCandidate(id="lex-2", item_key="line-2", candidate=make_candidate(lemma="cook", item_key="line-2")),
            PersistedCandidate(id="lex-3", item_key="line-3", candidate=make_candidate(lemma="draw", item_key="line-3")),
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="I wash the cup at home.", translation="I wash the cup at home."),
            make_bundle(sentence="I cook rice at home.", translation="I cook rice at home."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.93),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.91),
        ]
    )
    job_repository = FakeJobRepository()
    service = GenerateTextItemsService(
        job_repository=job_repository,
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    progress = []

    result = service.execute(
        job_id="job-1",
        deck_language=SupportedLanguage.EN,
        missing_only=True,
        max_items=2,
        progress_callback=progress.append,
    )

    assert repository.claim_calls == [{"job_id": "job-1", "missing_only": True, "limit": 2}]
    assert result.processed_items == 2
    assert result.processed_item_keys == ["line-1", "line-2"]
    assert [record.item_key for record in repository.saved_records] == ["line-1", "line-2"]
    assert job_repository.successes == [
        ("job-1", "line-1", JobStage.GENERATE_TEXT),
        ("job-1", "line-2", JobStage.GENERATE_TEXT),
    ]
    assert [snapshot.processed_this_run for snapshot in progress] == [1, 2]
    assert [snapshot.accepted_this_run for snapshot in progress] == [1, 2]
    assert [snapshot.review_this_run for snapshot in progress] == [0, 0]
    assert [snapshot.remaining_missing for snapshot in progress] == [1, 0]
    assert [snapshot.last_item_key for snapshot in progress] == ["line-1", "line-2"]
    assert all(snapshot.elapsed_seconds >= 0 for snapshot in progress)


def test_generate_text_items_uses_claim_boundary_for_concurrency_without_duplicates() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate(item_key="line-1"))]
    )
    generation = FakeGenerationService(bundles=[make_bundle(sentence="I wash the cup at home.", translation="I wash the cup at home.")])
    validation = FakeValidationService(results=[make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.93)])
    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN, concurrency=2, max_items=1)

    assert result.processed_item_keys == ["line-1"]
    assert repository.claim_calls == [{"job_id": "job-1", "missing_only": False, "limit": 1}]


def test_generate_text_items_repair_only_uses_review_selection_without_missing_only() -> None:
    repository = FakeTextRepository(candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate())])
    generation = FakeGenerationService(bundles=[make_bundle(sentence="I wash the cup at home.", translation="I wash the cup at home.")])
    validation = FakeValidationService(results=[make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.93)])
    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN, repair_only=True, max_items=1)

    assert result.processed_items == 1
    assert repository.missing_only_calls == []


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
        tatoeba_sentence_source=FakeTatoebaSentenceSource(
            fallback=SentenceGenerationResult(sentence="I wash the cup at home.", provenance={"source": "tatoeba"})
        ),
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
    validation = FakeValidationService(results=[failed_result, failed_result, failed_result])
    job_repository = FakeJobRepository()

    service = GenerateTextItemsService(
        job_repository=job_repository,
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(
            fallback=SentenceGenerationResult(sentence="Practice every morning.", provenance={"source": "tatoeba"})
        ),
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 1
    assert result.accepted_items == 0
    assert result.review_required_items == 1
    assert len(repository.saved_records) == 1
    saved = repository.saved_records[0]
    assert saved.review_status is ReviewStatus.REVIEW_REQUIRED
    assert saved.validation_status is ValidationStatus.FAILED
    assert saved.repair_attempt_count == 2
    assert saved.review_reason == "translation_mismatch"
    assert saved.validation_flags[0].code is ValidationFlagCode.TRANSLATION_MISMATCH
    assert job_repository.successes == [("job-1", "line-1", JobStage.GENERATE_TEXT)]


def test_generate_text_items_routes_isolated_word_translation_to_review() -> None:
    candidate = make_candidate(lemma="достичь", item_key="ru-1", translation_target_language="en").model_copy(
        update={"definitions_html": "verb: to achieve, to attain, to reach"}
    )
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-ru-1", item_key="ru-1", candidate=candidate)]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="Он хочет достичь цели завтра.", translation="to achieve", sentence_language="ru", translation_language="en"),
            make_bundle(sentence="Он хочет достичь цели завтра.", translation="to achieve", sentence_language="ru", translation_language="en"),
        ]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=TextValidationService(),
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    result = service.execute(job_id="job-ru", deck_language=SupportedLanguage.RU)

    assert result.accepted_items == 0
    assert result.review_required_items == 1
    saved = repository.saved_records[0]
    assert saved.review_status is ReviewStatus.REVIEW_REQUIRED
    assert saved.review_reason == "translation_mismatch"
    assert saved.validation_flags[0].code is ValidationFlagCode.TRANSLATION_MISMATCH


def test_generate_text_items_accepts_repaired_full_sentence_translation() -> None:
    candidate = make_candidate(lemma="достичь", item_key="ru-1", translation_target_language="en").model_copy(
        update={"definitions_html": "verb: to achieve, to attain, to reach"}
    )
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-ru-1", item_key="ru-1", candidate=candidate)]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="Он хочет достичь цели завтра.", translation="to achieve", sentence_language="ru", translation_language="en"),
            make_bundle(
                sentence="Он хочет достичь цели завтра.",
                translation="He wants to achieve the goal tomorrow.",
                sentence_language="ru",
                translation_language="en",
            ),
        ]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=TextValidationService(),
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    result = service.execute(job_id="job-ru", deck_language=SupportedLanguage.RU)

    assert result.accepted_items == 1
    assert result.review_required_items == 0
    saved = repository.saved_records[0]
    assert saved.review_status is ReviewStatus.ACCEPTED
    assert saved.generation_status is TextGenerationStatus.REPAIRED
    assert saved.translation_text == "He wants to achieve the goal tomorrow."


def test_generate_text_items_skips_tatoeba_when_first_pass_validation_succeeds() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate())]
    )
    generation = FakeGenerationService(
        bundles=[make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa.")]
    )
    validation = FakeValidationService(
        results=[make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95)]
    )
    tatoeba = FakeTatoebaSentenceSource(
        fallback=SentenceGenerationResult(sentence="I wash late at night.", provenance={"source": "tatoeba"})
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=tatoeba,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.accepted_items == 1
    assert generation.calls == [(repository.candidates[0].candidate, SupportedLanguage.EN)]
    assert generation.fallback_calls == []
    assert tatoeba.calls == []
    assert repository.saved_records[0].generation_status is TextGenerationStatus.GENERATED


def test_generate_text_items_routes_frequency_local_templates_to_review() -> None:
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(
                id="lex-1",
                item_key="level-1-rank-0001",
                candidate=make_candidate(item_key="level-1-rank-0001"),
                source_type="frequency",
            )
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_local_bundle(
                sentence="Friends discuss wash during lunch.",
                translation="Amigos comentam wash durante o almoço.",
            ),
            make_local_bundle(
                sentence="Friends discuss wash during lunch.",
                translation="Amigos comentam wash durante o almoço.",
            ),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
        ]
    )
    tatoeba = FakeTatoebaSentenceSource(fallback=None)

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=tatoeba,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.RU)

    assert result.accepted_items == 0
    assert result.review_required_items == 1
    assert tatoeba.calls
    saved = repository.saved_records[0]
    assert saved.review_status is ReviewStatus.REVIEW_REQUIRED
    assert saved.validation_status is ValidationStatus.FAILED
    assert saved.review_reason == "banned_pattern"
    assert saved.validation_flags[0].detail.startswith("non-English learner decks must not accept")


def test_generate_text_items_routes_non_english_word_list_local_templates_to_review() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-fr-1", item_key="remercia", candidate=make_candidate())]
    )
    generation = FakeGenerationService(
        bundles=[
            make_local_bundle(
                sentence="Des voisins discutent Remercia pendant le dîner.",
                translation="Des voisins discutent Remercia pendant le dîner.",
            ),
            make_local_bundle(
                sentence="Des voisins discutent Remercia pendant le dîner.",
                translation="Des voisins discutent Remercia pendant le dîner.",
            ),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
        ]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    result = service.execute(job_id="job-fr", deck_language=SupportedLanguage.FR)

    assert result.accepted_items == 0
    assert result.review_required_items == 1
    saved = repository.saved_records[0]
    assert saved.review_status is ReviewStatus.REVIEW_REQUIRED
    assert saved.validation_status is ValidationStatus.FAILED
    assert saved.review_reason == "banned_pattern"


def test_generate_text_items_retries_ai_then_uses_tatoeba_for_failed_first_pass() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate())]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="They practice every morning.", translation="Eles praticam todas as manhãs."),
            make_bundle(sentence="Practice every morning.", translation="Pratique todas as manhãs."),
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(
                status=ValidationStatus.FAILED,
                label=ConfidenceLabel.LOW,
                score=0.3,
                flags=[ValidationFlag(code=ValidationFlagCode.MISSING_TARGET_LEMMA, detail="missing target form")],
            ),
            make_validation_result(
                status=ValidationStatus.FAILED,
                label=ConfidenceLabel.LOW,
                score=0.31,
                flags=[ValidationFlag(code=ValidationFlagCode.MISSING_TARGET_LEMMA, detail="missing target form")],
            ),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.92),
        ]
    )
    fallback_sentence = SentenceGenerationResult(
        sentence="I wash the cup at home.",
        intended_sense="habit",
        provenance={"source": "tatoeba"},
    )
    tatoeba = FakeTatoebaSentenceSource(fallback=fallback_sentence)

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=tatoeba,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.accepted_items == 1
    assert len(tatoeba.calls) == 1
    assert len(generation.calls) == 2
    assert len(generation.fallback_calls) == 1
    assert generation.fallback_calls[0][2].sentence_result.sentence == "I wash the cup at home."
    assert repository.saved_records[0].generation_status is TextGenerationStatus.REPAIRED
    assert repository.saved_records[0].review_status is ReviewStatus.ACCEPTED


def test_generate_text_items_keeps_review_required_when_tatoeba_has_no_usable_candidate() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate())]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="They practice every morning.", translation="Eles praticam todas as manhãs."),
            make_bundle(sentence="Practice every morning.", translation="Pratique todas as manhãs."),
        ]
    )
    failed_result = make_validation_result(
        status=ValidationStatus.FAILED,
        label=ConfidenceLabel.LOW,
        score=0.22,
        flags=[ValidationFlag(code=ValidationFlagCode.MISSING_TARGET_LEMMA, detail="missing target form")],
    )
    validation = FakeValidationService(results=[failed_result, failed_result])

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.accepted_items == 0
    assert result.review_required_items == 1
    assert len(generation.calls) == 2
    assert generation.fallback_calls == []
    assert repository.saved_records[0].review_status is ReviewStatus.REVIEW_REQUIRED
    assert repository.saved_records[0].repair_attempt_count == 1


def test_generate_text_items_flags_duplicate_sentence_across_cards() -> None:
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate(item_key="line-1")),
            PersistedCandidate(id="lex-2", item_key="line-2", candidate=make_candidate(lemma="clean", item_key="line-2")),
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
            make_bundle(sentence="I wash the cup at home.", translation="Eu limpo a xícara em casa."),
            make_bundle(sentence="I clean the cup at home.", translation="Eu limpo a xícara em casa."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
            make_validation_result(
                status=ValidationStatus.FAILED,
                label=ConfidenceLabel.LOW,
                score=0.45,
                flags=[
                    ValidationFlag(
                        code=ValidationFlagCode.DUPLICATE_SENTENCE,
                        detail="sentence must be unique across cards in the same deck generation job",
                    )
                ],
            ),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.91),
        ]
    )
    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(
            fallback=SentenceGenerationResult(sentence="I clean the cup at home.", provenance={"source": "tatoeba"})
        ),
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 2
    assert result.accepted_items == 2
    assert result.review_required_items == 0
    assert len(validation.calls) == 3
    assert validation.calls[0]["disallowed_sentence_texts"] == set()
    assert validation.calls[1]["disallowed_sentence_texts"] == {"i wash the cup at home"}
    assert validation.calls[2]["disallowed_sentence_texts"] == {"i wash the cup at home"}
    assert repository.saved_records[1].generation_status is TextGenerationStatus.REPAIRED


def test_generate_text_items_uses_highlight_profile_validation_rules() -> None:
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(
                id="lex-highlight-1",
                item_key="highlight:abc123:wash",
                candidate=make_candidate(item_key="highlight:abc123:wash"),
                source_type="kindle-highlights",
            )
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(
                sentence="Readers wash the old cup carefully after the quiet chapter ends.",
                translation="translation omitted by highlight export",
            )
        ]
    )
    validation = FakeValidationService(
        results=[make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.94)]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    result = service.execute(job_id="job-highlight", deck_language=SupportedLanguage.EN)

    assert result.accepted_items == 1
    assert validation.calls[0]["require_translation"] is False
    assert validation.calls[0]["min_sentence_tokens"] == 6
    assert validation.calls[0]["max_sentence_tokens"] == 16


def test_generate_text_items_preserves_frequency_and_word_list_profile_validation_rules() -> None:
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(
                id="lex-frequency-1",
                item_key="level-1-rank-0001",
                candidate=make_candidate(
                    item_key="level-1-rank-0001",
                    frequency_rank=1,
                    frequency_level=1,
                ),
                source_type="frequency",
            ),
            PersistedCandidate(
                id="lex-word-list-1",
                item_key="line-1",
                candidate=make_candidate(item_key="line-1"),
                source_type="word-list",
            ),
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
        ]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    service.execute(job_id="job-existing", deck_language=SupportedLanguage.EN)

    assert [call["require_translation"] for call in validation.calls] == [True, True]
    assert [call["min_sentence_tokens"] for call in validation.calls] == [4, 4]
    assert [call["max_sentence_tokens"] for call in validation.calls] == [12, 12]


def test_generate_text_items_skips_same_language_translation_validation() -> None:
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(
                id="lex-frequency-1",
                item_key="level-1-rank-0001",
                candidate=make_candidate(
                    item_key="level-1-rank-0001",
                    frequency_rank=1,
                    frequency_level=1,
                    translation_target_language="en",
                ),
                source_type="frequency",
            ),
            PersistedCandidate(
                id="lex-word-list-1",
                item_key="line-1",
                candidate=make_candidate(item_key="line-1", translation_target_language="en"),
                source_type="word-list",
            ),
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="I wash the cup at home.", translation="I wash the cup at home."),
            make_bundle(sentence="I wash the cup at home.", translation="I wash the cup at home."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
        ]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    service.execute(job_id="job-same-language", deck_language=SupportedLanguage.EN)

    assert [call["require_translation"] for call in validation.calls] == [False, False]


def test_generate_text_items_infers_source_profile_when_source_type_is_absent() -> None:
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(
                id="lex-frequency-1",
                item_key="level-1-rank-0001",
                candidate=make_candidate(
                    item_key="level-1-rank-0001",
                    frequency_rank=1,
                    frequency_level=1,
                ),
                source_type=None,
            ),
            PersistedCandidate(
                id="lex-word-list-1",
                item_key="line-1",
                candidate=make_candidate(item_key="line-1"),
                source_type=None,
            ),
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
            make_bundle(sentence="I wash the cup at home.", translation="Eu lavo a xícara em casa."),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95),
        ]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
    )

    service.execute(job_id="job-inferred", deck_language=SupportedLanguage.EN)

    assert [call["require_translation"] for call in validation.calls] == [True, True]
    assert [call["min_sentence_tokens"] for call in validation.calls] == [4, 4]
    assert [call["max_sentence_tokens"] for call in validation.calls] == [12, 12]


def test_generate_text_items_sends_bounded_redacted_highlight_context() -> None:
    private_text = (
        "Book: Secret Novel\n"
        "The quiet room held a silver basin while readers wash every cup before dawn. "
        "This extra private paragraph must not be copied wholesale into provider prompts. "
        "Location: 123\n"
        "https://reader.example/dav/private-export"
    )
    candidate = make_candidate(item_key="highlight:abc:wash")
    candidate = candidate.model_copy(
        update={
            "provenance": candidate.provenance.model_copy(
                update={
                    "notes": [
                        "first_highlight_id=highlight-7",
                        f"source_content_hash={'a' * 64}",
                    ]
                }
            )
        }
    )
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(
                id="lex-highlight-1",
                item_key="highlight:abc:wash",
                candidate=candidate,
                source_type="kindle-highlights",
            )
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(
                sentence="Readers wash every cup before the quiet chapter ends.",
                translation="translation omitted by highlight export",
            )
        ]
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=FakeValidationService(
            results=[make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95)]
        ),
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
        highlight_import_repository=FakeHighlightImportRepository(
            records={("job-highlight", "highlight-7"): FakeHighlightRecord("highlight-7", private_text)}
        ),
    )

    service.execute(job_id="job-highlight", deck_language=SupportedLanguage.EN)

    metadata = generation.request_metadata[0]
    context = str(metadata["highlight_context"])
    assert metadata["source_type"] == "kindle-highlights"
    assert "readers wash every cup before dawn" in context.casefold()
    assert "Secret Novel" not in context
    assert "Location: 123" not in context
    assert "dav/private-export" not in context
    assert len(context.split()) <= 24


def test_generate_text_items_forwards_highlight_context_to_repair_attempts() -> None:
    candidate = make_candidate(item_key="highlight:abc:wash")
    candidate = candidate.model_copy(
        update={
            "provenance": candidate.provenance.model_copy(update={"notes": ["first_highlight_id=highlight-7"]})
        }
    )
    repository = FakeTextRepository(
        candidates=[
            PersistedCandidate(
                id="lex-highlight-1",
                item_key="highlight:abc:wash",
                candidate=candidate,
                source_type="kindle-highlights",
            )
        ]
    )
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence="Tiny wash clue.", translation="translation omitted by highlight export"),
            make_bundle(
                sentence="Readers wash every cup before the quiet chapter ends.",
                translation="translation omitted by highlight export",
            ),
        ]
    )
    failed = make_validation_result(
        status=ValidationStatus.FAILED,
        label=ConfidenceLabel.LOW,
        score=0.25,
        flags=[ValidationFlag(code=ValidationFlagCode.SENTENCE_TOO_SHORT, detail="too short")],
    )

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=FakeValidationService(
            results=[failed, make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.95)]
        ),
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
        highlight_import_repository=FakeHighlightImportRepository(
            records={
                ("job-highlight", "highlight-7"): FakeHighlightRecord(
                    "highlight-7", "Readers wash every cup before dawn in the quiet chapter."
                )
            }
        ),
    )

    service.execute(job_id="job-highlight", deck_language=SupportedLanguage.EN)

    assert len(generation.request_metadata) == 2
    assert generation.request_metadata[0] == generation.request_metadata[1]
    assert generation.request_metadata[0]["source_type"] == "kindle-highlights"
    assert "wash every cup" in str(generation.request_metadata[0]["highlight_context"])


@dataclass
class FakeLatinGenerationService:
    """Fake text-generation service exposing the dynamic-Latin translation hook."""

    bundles: list[GeneratedTextBundle]
    translate_calls: list[str] = field(default_factory=list)

    def generate_bundle(self, **kwargs: object) -> GeneratedTextBundle:
        return self.bundles.pop(0)

    def generate_bundle_from_fallback(self, **kwargs: object) -> GeneratedTextBundle:
        return self.bundles.pop(0)

    def translate_sentence_text(
        self,
        *,
        sentence: str,
        translation_target_language: str,
        deck_language: SupportedLanguage,
        intended_sense: str | None = None,
        rate_limiter: object | None = None,
        job_id: str | None = None,
        item_key: str | None = None,
    ) -> GeneratedTranslation:
        self.translate_calls.append(sentence)
        return GeneratedTranslation(
            text=f"[pt de] {sentence}",
            target_language=translation_target_language,
            provenance=TextProvenance(source="translator", provider="fake-retranslate"),
        )


class _FakeLatinCard:
    def __init__(self, latin_sentence: str, gramatica: str) -> None:
        self.latin_sentence = latin_sentence
        self.gramatica = gramatica


@dataclass
class FakeLatinCardService:
    cards: list[_FakeLatinCard]

    def generate(self, seeds: object) -> list[_FakeLatinCard]:
        return list(self.cards)


def test_dynamic_latin_override_regenerates_translation_for_new_sentence() -> None:
    repository = FakeTextRepository(
        candidates=[PersistedCandidate(id="lex-1", item_key="line-1", candidate=make_candidate(lemma="vir", item_key="line-1", translation_target_language="pt"))]
    )
    # The bundle translation here belongs to the ORIGINAL sentence and must not survive.
    generation = FakeLatinGenerationService(
        bundles=[make_bundle(sentence="Original sentence.", translation="Traducao da frase original.", sentence_language="la")]
    )
    validation = FakeValidationService(results=[make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.93)])
    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=FakeTatoebaSentenceSource(fallback=None),
        latin_card_service=FakeLatinCardService(cards=[_FakeLatinCard(latin_sentence="Vir bonus est.", gramatica="vir: subst masc, Nom sing, Suj.")]),
    )

    service.execute(job_id="job-1", deck_language=SupportedLanguage.LA, max_items=1)

    saved = repository.saved_records[0]
    # The structured Latin sentence replaced the original...
    assert saved.example_sentence == "Vir bonus est."
    # ...and the translation was regenerated for it, not left tied to the old sentence.
    assert generation.translate_calls == ["Vir bonus est."]
    assert saved.translation_text == "[pt de] Vir bonus est."
    assert saved.translation_text != "Traducao da frase original."
    # And the structured grammar rode along in provenance for export.
    assert saved.sentence_provenance.metadata.get("gramatica") == "vir: subst masc, Nom sing, Suj."


@pytest.mark.parametrize(
    "match_status",
    [KoreanMatchStatus.UNAVAILABLE, KoreanMatchStatus.AMBIGUOUS],
)
def test_korean_generation_restores_one_identity_for_retry_and_never_calls_tatoeba(
    match_status: KoreanMatchStatus,
) -> None:
    fingerprint = make_korean_fingerprint()
    persisted_identity = make_korean_identity(fingerprint=fingerprint)
    persisted_candidate = make_persisted_korean_candidate(persisted_identity)
    repository = FakeTextRepository(candidates=[persisted_candidate])
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
    matcher = FakeKoreanMatcher(fingerprint=fingerprint, status=match_status)
    validation = RecordingValidationService(
        TextValidationService(
            language_identifier=ExpectedLanguageIdentifier(),
            korean_matcher=matcher,
        )
    )
    tatoeba = FakeTatoebaSentenceSource(fallback=None)
    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=tatoeba,
    )

    result = service.execute(job_id="job-ko", deck_language=SupportedLanguage.KO)

    assert result.accepted_items == 0
    assert result.review_required_items == 1
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
    assert [target for _sentence, target in matcher.calls] == [
        restored_identity,
        restored_identity,
        restored_identity,
    ]
    assert tatoeba.calls == []

    saved = repository.saved_records[0]
    assert saved.review_status is ReviewStatus.REVIEW_REQUIRED
    assert saved.validation_status is ValidationStatus.FAILED
    assert saved.review_reason == ValidationFlagCode.MORPHOLOGY_MISMATCH.value
    assert saved.repair_attempt_count == 1
    morphology_flags = [
        flag
        for flag in saved.validation_flags
        if flag.code is ValidationFlagCode.MORPHOLOGY_MISMATCH
    ]
    assert len(morphology_flags) == 1
    assert match_status.value in morphology_flags[0].detail
    assert persisted_identity.lemma not in morphology_flags[0].detail
    assert persisted_identity.sense_id not in morphology_flags[0].detail
    assert saved.example_sentence not in morphology_flags[0].detail


def test_korean_generation_persists_hash_only_two_plus_one_selector_history() -> None:
    fingerprint = make_korean_fingerprint()
    persisted_identity = make_korean_identity(fingerprint=fingerprint)
    repository = FakeTextRepository(
        candidates=[make_persisted_korean_candidate(persisted_identity)]
    )
    bad_template = "먹다 예문입니다."
    bad_translation = "Hoje eu eat school."
    generation = FakeGenerationService(
        bundles=[
            make_bundle(sentence=bad_template, translation="comer", sentence_language="ko"),
            make_bundle(sentence="오늘 밥을 먹습니다.", translation=bad_translation, sentence_language="ko"),
            make_bundle(
                sentence="오늘 집에서 밥을 먹어요.",
                translation="Hoje eu como arroz em casa.",
                sentence_language="ko",
            ),
        ]
    )
    validation = FakeValidationService(
        results=[
            make_validation_result(
                status=ValidationStatus.FAILED,
                label=ConfidenceLabel.LOW,
                score=0.2,
                flags=[ValidationFlag(code=ValidationFlagCode.BANNED_PATTERN, detail="template")],
            ),
            make_validation_result(
                status=ValidationStatus.FAILED,
                label=ConfidenceLabel.LOW,
                score=0.3,
                flags=[ValidationFlag(code=ValidationFlagCode.TRANSLATION_MISMATCH, detail="translation")],
            ),
            make_validation_result(status=ValidationStatus.PASSED, label=ConfidenceLabel.HIGH, score=0.94),
        ]
    )
    tatoeba = FakeTatoebaSentenceSource(fallback=None)

    service = GenerateTextItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=None,
        text_repository=repository,
        text_generation_service=generation,
        text_validation_service=validation,
        tatoeba_sentence_source=tatoeba,
    )

    result = service.execute(job_id="job-ko", deck_language=SupportedLanguage.KO)

    assert result.processed_items == 1
    assert len(generation.calls) == 3
    assert [metadata["korean_selector_attempt"].stage for metadata in generation.request_metadata] == [
        "initial",
        "initial",
        "repair",
    ]
    saved = repository.saved_records[0]
    history = saved.sentence_provenance.metadata["korean_selector_history"]
    assert history["initial_candidate_count"] == 2
    assert history["repair_attempt_count"] == 1
    assert [attempt["stage"] for attempt in history["attempts"]] == ["initial", "initial", "repair"]
    assert history["attempts"][0]["rejection_codes"] == ["banned_pattern"]
    assert history["attempts"][1]["rejection_codes"] == ["translation_mismatch"]
    assert bad_template not in str(history)
    assert bad_translation not in str(history)
    assert saved.repair_attempt_count == 1
    assert tatoeba.calls == []
