"""Tests for accepted-text audio orchestration and reuse."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioFormat, AudioProvenance, AudioProvider, AudioSynthesisStatus, NormalizedTtsInput
from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.lexicon import DefinitionRecord, GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import ConfidenceLabel, ReviewStatus, TextGenerationStatus, TextProvenance, TextQualityRecord, ValidationStatus
from multilang.services.audio_synthesis import AudioSynthesisBundle
from multilang.services.generate_audio_items import GenerateAudioItemsService


def make_text_record(*, item_key: str, review_status: ReviewStatus) -> TextQualityRecord:
    return TextQualityRecord(
        job_id="job-1",
        item_key=item_key,
        lexical_candidate_id=f"lex-{item_key}",
        example_sentence=f"I use {item_key} every day.",
        translation_text="Eu uso isto todos os dias.",
        generation_status=TextGenerationStatus.GENERATED,
        validation_status=ValidationStatus.PASSED,
        review_status=review_status,
        repair_attempt_count=0,
        confidence_score=0.95,
        confidence_label=ConfidenceLabel.HIGH,
        validation_flags=[],
        review_reason=None,
        sentence_provenance=TextProvenance(source="generator", provider="local"),
        translation_provenance=TextProvenance(source="translator", provider="local"),
    )


def make_candidate(*, item_key: str, source_type: str = "frequency") -> object:
    candidate = LexicalCardCandidate(
        submitted_form=item_key,
        display_form=item_key,
        lemma=item_key,
        lemma_key=f"en:{item_key}",
        frequency_rank=1 if source_type == "frequency" else None,
        frequency_level=1 if source_type == "frequency" else None,
        definitions_html=f"definition for {item_key}",
        definition_language="en",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="manual", definition=DefinitionRecord(source="manual", value=f"definition for {item_key}")),
    )
    if source_type == "frequency":
        return candidate
    return SimpleNamespace(**candidate.model_dump(), source_type=source_type)


def make_asset(*, item_key: str, asset_kind: AudioAssetKind, status: AudioSynthesisStatus, fallback_used: bool = False) -> AudioAssetRecord:
    normalized = NormalizedTtsInput(
        display_text=item_key if asset_kind is AudioAssetKind.WORD else f"I use {item_key} every day.",
        tts_text=item_key if asset_kind is AudioAssetKind.WORD else f"I use {item_key} every day.",
        ssml_text=f"<speak version=\"1.0\">{item_key}</speak>",
    )
    return AudioAssetRecord(
        job_id="job-1",
        item_key=item_key,
        asset_kind=asset_kind,
        display_text=normalized.display_text,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="en-US-JennyNeural",
            locale="en-US",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path=f"audio/{asset_kind.value}/{item_key}.mp3",
            byte_size=4096 if status is AudioSynthesisStatus.SYNTHESIZED else 0,
            duration_ms=800 if status is AudioSynthesisStatus.SYNTHESIZED else None,
            status=status,
            fallback_used=fallback_used,
        ),
    )


@dataclass
class FakeTextRepository:
    accepted_records: list[TextQualityRecord]

    def list_accepted_records(self, job_id: str) -> list[TextQualityRecord]:
        return [record for record in self.accepted_records if record.job_id == job_id]


@dataclass
class FakeLexicalRepository:
    candidates: dict[str, object]

    def get_candidate_for_item(self, job_id: str, item_key: str) -> object | None:
        return self.candidates.get(item_key)


@dataclass
class FakeAudioRepository:
    reusable_assets: dict[tuple[str, str, str, str, str], AudioAssetRecord] = field(default_factory=dict)
    saved_assets: list[AudioAssetRecord] = field(default_factory=list)

    def get_reusable_asset(self, *, asset_kind: AudioAssetKind, text_hash: str, ssml_hash: str, voice_id: str, format: AudioFormat) -> AudioAssetRecord | None:
        return self.reusable_assets.get((asset_kind.value, text_hash, ssml_hash, voice_id, format.value))

    def upsert_audio_asset(self, record: AudioAssetRecord) -> AudioAssetRecord:
        self.saved_assets.append(record)
        return record


@dataclass
class FakeJobRepository:
    successes: list[tuple[str, str, JobStage]] = field(default_factory=list)

    def record_item_success(self, job_id: str, *, item_key: str, completed_stage: JobStage) -> None:
        self.successes.append((job_id, item_key, completed_stage))


@dataclass
class FakeAudioSynthesisService:
    prepared: dict[str, AudioSynthesisBundle]
    synthesized: list[AudioAssetRecord] = field(default_factory=list)

    def prepare_item_assets(self, *, language: SupportedLanguage, display_word: str, text_record: TextQualityRecord) -> AudioSynthesisBundle:
        return self.prepared[text_record.item_key]

    def synthesize_prepared_asset(self, prepared_asset: AudioAssetRecord) -> AudioAssetRecord:
        synthesized = prepared_asset.model_copy(
            update={
                "provenance": prepared_asset.provenance.model_copy(
                    update={
                        "status": AudioSynthesisStatus.SYNTHESIZED,
                        "byte_size": 4096,
                        "duration_ms": 900,
                    }
                )
            }
        )
        self.synthesized.append(synthesized)
        return synthesized


def test_generate_audio_items_service_reuses_existing_assets() -> None:
    existing_word = make_asset(
        item_key="alpha",
        asset_kind=AudioAssetKind.WORD,
        status=AudioSynthesisStatus.SYNTHESIZED,
    ).model_copy(update={"job_id": "old-job", "item_key": "old-item"})
    prepared_word = make_asset(item_key="alpha", asset_kind=AudioAssetKind.WORD, status=AudioSynthesisStatus.PENDING)
    prepared_sentence = make_asset(item_key="alpha", asset_kind=AudioAssetKind.SENTENCE, status=AudioSynthesisStatus.PENDING)
    audio_repository = FakeAudioRepository(
        reusable_assets={
            (
                AudioAssetKind.WORD.value,
                prepared_word.normalized_input.text_hash or "",
                prepared_word.normalized_input.ssml_hash or "",
                prepared_word.provenance.voice_id,
                prepared_word.provenance.format.value,
            ): existing_word
        }
    )
    synthesis = FakeAudioSynthesisService(
        prepared={"alpha": AudioSynthesisBundle(word_asset=prepared_word, sentence_asset=prepared_sentence)}
    )

    service = GenerateAudioItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=FakeLexicalRepository(candidates={"alpha": make_candidate(item_key="alpha")}),
        text_repository=FakeTextRepository(accepted_records=[make_text_record(item_key="alpha", review_status=ReviewStatus.ACCEPTED)]),
        audio_repository=audio_repository,
        audio_synthesis_service=synthesis,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 2
    assert result.reused_items == 1
    assert result.failed_items == 0
    assert len(audio_repository.saved_assets) == 2
    assert audio_repository.saved_assets[0].job_id == "job-1"
    assert audio_repository.saved_assets[0].item_key == "alpha"
    assert audio_repository.saved_assets[0].provenance.storage_path == existing_word.provenance.storage_path
    assert synthesis.synthesized[0].asset_kind is AudioAssetKind.SENTENCE


def test_generate_audio_items_service_skips_review_required_text_rows() -> None:
    service = GenerateAudioItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=FakeLexicalRepository(candidates={"alpha": make_candidate(item_key="alpha")}),
        text_repository=FakeTextRepository(accepted_records=[]),
        audio_repository=FakeAudioRepository(),
        audio_synthesis_service=FakeAudioSynthesisService(prepared={}),
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 0
    assert result.reused_items == 0
    assert result.fallback_items == 0
    assert result.failed_items == 0


def test_generate_audio_items_service_tracks_fallback_and_failure_counters() -> None:
    prepared_word = make_asset(item_key="alpha", asset_kind=AudioAssetKind.WORD, status=AudioSynthesisStatus.PENDING, fallback_used=True)
    prepared_sentence = make_asset(item_key="alpha", asset_kind=AudioAssetKind.SENTENCE, status=AudioSynthesisStatus.FAILED)
    synthesis = FakeAudioSynthesisService(
        prepared={"alpha": AudioSynthesisBundle(word_asset=prepared_word, sentence_asset=prepared_sentence)}
    )
    service = GenerateAudioItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=FakeLexicalRepository(candidates={"alpha": make_candidate(item_key="alpha")}),
        text_repository=FakeTextRepository(accepted_records=[make_text_record(item_key="alpha", review_status=ReviewStatus.ACCEPTED)]),
        audio_repository=FakeAudioRepository(),
        audio_synthesis_service=synthesis,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 2
    assert result.fallback_items == 1
    assert result.failed_items == 1


def test_generate_audio_items_service_creates_only_sentence_audio_for_highlights() -> None:
    item_key = "highlight:abc:wash"
    prepared_word = make_asset(item_key=item_key, asset_kind=AudioAssetKind.WORD, status=AudioSynthesisStatus.PENDING)
    prepared_sentence = make_asset(item_key=item_key, asset_kind=AudioAssetKind.SENTENCE, status=AudioSynthesisStatus.PENDING)
    synthesis = FakeAudioSynthesisService(
        prepared={item_key: AudioSynthesisBundle(word_asset=prepared_word, sentence_asset=prepared_sentence)}
    )
    audio_repository = FakeAudioRepository()
    job_repository = FakeJobRepository()
    service = GenerateAudioItemsService(
        job_repository=job_repository,
        lexical_repository=FakeLexicalRepository(candidates={item_key: make_candidate(item_key=item_key, source_type="kindle-highlights")}),
        text_repository=FakeTextRepository(accepted_records=[make_text_record(item_key=item_key, review_status=ReviewStatus.ACCEPTED)]),
        audio_repository=audio_repository,
        audio_synthesis_service=synthesis,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 1
    assert {asset.asset_kind for asset in audio_repository.saved_assets} == {AudioAssetKind.SENTENCE}
    assert len(synthesis.synthesized) == 1
    assert synthesis.synthesized[0].asset_kind is AudioAssetKind.SENTENCE
    assert job_repository.successes == [("job-1", item_key, JobStage.SYNTHESIZE_AUDIO)]


def test_generate_audio_items_service_skips_review_required_highlight_rows() -> None:
    item_key = "highlight:abc:wash"
    service = GenerateAudioItemsService(
        job_repository=FakeJobRepository(),
        lexical_repository=FakeLexicalRepository(candidates={item_key: make_candidate(item_key=item_key)}),
        text_repository=FakeTextRepository(accepted_records=[]),
        audio_repository=FakeAudioRepository(),
        audio_synthesis_service=FakeAudioSynthesisService(prepared={}),
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.processed_items == 0
