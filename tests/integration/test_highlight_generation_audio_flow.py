"""Focused Phase 12 highlight generation/audio/card integration evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.services.assemble_export_cards import AssembleExportCardsService
from multilang.services.audio_synthesis import AudioSynthesisBundle
from multilang.services.generate_audio_items import GenerateAudioItemsService


ITEM_KEY = "highlight:abc:wash"


def make_text_record() -> TextQualityRecord:
    return TextQualityRecord(
        job_id="job-highlight",
        item_key=ITEM_KEY,
        lexical_candidate_id="lex-highlight",
        example_sentence="Readers wash every cup before the quiet chapter ends.",
        translation_text="translation omitted by highlight export",
        generation_status=TextGenerationStatus.GENERATED,
        validation_status=ValidationStatus.PASSED,
        review_status=ReviewStatus.ACCEPTED,
        repair_attempt_count=0,
        confidence_score=0.95,
        confidence_label=ConfidenceLabel.HIGH,
        validation_flags=[],
        review_reason=None,
        sentence_provenance=TextProvenance(source="runtime-local-generator", provider="local", metadata={"source_type": "kindle-highlights"}),
        translation_provenance=TextProvenance(source="runtime-local-translator", provider="local"),
    )


def make_candidate() -> SimpleNamespace:
    return SimpleNamespace(
        source_type="kindle-highlights",
        submitted_form="wash",
        display_form="wash",
        lemma="wash",
        lemma_key="en:wash",
        frequency_rank=None,
        frequency_level=None,
        definitions_html="verb: to clean with water",
        definition_language="en",
        ipa="/wɑʃ/",
        spoken_form="wash",
        translation_target_language="pt",
        grounding_status="grounded",
        warning_code=None,
        warning_detail=None,
    )


def make_asset(*, asset_kind: AudioAssetKind, status: AudioSynthesisStatus = AudioSynthesisStatus.PENDING) -> AudioAssetRecord:
    text = "wash" if asset_kind is AudioAssetKind.WORD else "Readers wash every cup before the quiet chapter ends."
    normalized = NormalizedTtsInput(display_text=text, tts_text=text, ssml_text=f"<speak>{text}</speak>")
    return AudioAssetRecord(
        job_id="job-highlight",
        item_key=ITEM_KEY,
        asset_kind=asset_kind,
        display_text=text,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="en-US-JennyNeural",
            locale="en-US",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path=f"audio/{asset_kind.value}/wash-{asset_kind.value}.mp3",
            byte_size=4096 if status is AudioSynthesisStatus.SYNTHESIZED else 0,
            duration_ms=900 if status is AudioSynthesisStatus.SYNTHESIZED else None,
            status=status,
        ),
    )


@dataclass
class TextRepo:
    record: TextQualityRecord

    def list_accepted_records(self, job_id: str) -> list[TextQualityRecord]:
        return [self.record] if job_id == self.record.job_id and self.record.review_status is ReviewStatus.ACCEPTED else []


@dataclass
class LexicalRepo:
    candidate: SimpleNamespace

    def get_candidate_for_item(self, job_id: str, item_key: str) -> SimpleNamespace | None:
        return self.candidate if item_key == ITEM_KEY else None


@dataclass
class AudioRepo:
    assets: dict[tuple[str, str], AudioAssetRecord] = field(default_factory=dict)

    def get_reusable_asset(self, **kwargs: object) -> None:
        return None

    def upsert_audio_asset(self, record: AudioAssetRecord) -> AudioAssetRecord:
        self.assets[(record.item_key, record.asset_kind.value)] = record
        return record

    def get_asset(self, job_id: str, item_key: str, asset_kind: AudioAssetKind) -> AudioAssetRecord | None:
        return self.assets.get((item_key, asset_kind.value))


@dataclass
class JobRepo:
    successes: list[tuple[str, str, JobStage]] = field(default_factory=list)

    def record_item_success(self, job_id: str, *, item_key: str, completed_stage: JobStage) -> None:
        self.successes.append((job_id, item_key, completed_stage))


@dataclass
class AudioSynthesis:
    synthesized: list[AudioAssetRecord] = field(default_factory=list)

    def prepare_item_assets(self, *, language: SupportedLanguage, display_word: str, text_record: TextQualityRecord) -> AudioSynthesisBundle:
        return AudioSynthesisBundle(
            word_asset=make_asset(asset_kind=AudioAssetKind.WORD),
            sentence_asset=make_asset(asset_kind=AudioAssetKind.SENTENCE),
        )

    def synthesize_prepared_asset(self, prepared_asset: AudioAssetRecord) -> AudioAssetRecord:
        synthesized = prepared_asset.model_copy(
            update={"provenance": prepared_asset.provenance.model_copy(update={"status": AudioSynthesisStatus.SYNTHESIZED, "byte_size": 4096})}
        )
        self.synthesized.append(synthesized)
        return synthesized


@dataclass
class ExportRepo:
    rows: list[object] = field(default_factory=list)

    def upsert_card_snapshot(self, record: object) -> object:
        self.rows.append(record)
        return record


def test_highlight_generation_audio_and_card_flow() -> None:
    text_record = make_text_record()
    candidate = make_candidate()
    text_repo = TextRepo(text_record)
    lexical_repo = LexicalRepo(candidate)
    audio_repo = AudioRepo()
    audio_service = AudioSynthesis()
    job_repo = JobRepo()

    audio_result = GenerateAudioItemsService(
        job_repository=job_repo,
        lexical_repository=lexical_repo,
        text_repository=text_repo,
        audio_repository=audio_repo,
        audio_synthesis_service=audio_service,
    ).execute(job_id="job-highlight", deck_language=SupportedLanguage.EN)

    export_repo = ExportRepo()
    card_result = AssembleExportCardsService(
        text_repository=text_repo,
        lexical_repository=lexical_repo,
        audio_repository=audio_repo,
        export_repository=export_repo,
    ).execute(job_id="job-highlight", deck_language=SupportedLanguage.EN)

    row = card_result.cards[0]
    mapping = row.ordered_field_mapping()
    assert audio_result.processed_items == 2
    assert {asset.asset_kind for asset in audio_repo.assets.values()} == {AudioAssetKind.WORD, AudioAssetKind.SENTENCE}
    assert row.identity.source_type == "kindle-highlights"
    assert row.word == "wash"
    assert row.translation == ""
    assert mapping["Image"] == ""
    assert "Translation" not in mapping
    assert mapping["word_audio"].startswith("[sound:")
    assert mapping["sentence_audio"].startswith("[sound:")
