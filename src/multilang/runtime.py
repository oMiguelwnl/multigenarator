"""Runtime bootstrap for the shipped CLI path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.export_repository import ExportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.text_repository import TextRepository
from multilang.domain.audio import AudioAssetKind
from multilang.domain.exporting import ExportArtifactFormat, ExportArtifactStatus, ExportDeckArtifact
from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.audio_synthesis import (
    AudioSynthesisAdapter,
    AudioSynthesisService,
)
from multilang.services.assemble_export_cards import AssembleExportCardsService
from multilang.services.export_anki_package import NOTE_TYPE_NAME, export_anki_package
from multilang.services.export_tabular_bundle import ExportTabularBundleResult, write_export_tabular_bundle
from multilang.services.generate_job import GenerateJobService
from multilang.services.generate_audio_items import GenerateAudioItemsService
from multilang.services.generate_text_items import GenerateTextItemsService
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.local_text_adapter import LocalSentenceAdapter, LocalTranslationAdapter
from multilang.services.regenerate_text_item import RegenerateTextItemService
from multilang.services.tatoeba_sentence_source import (
    StaticTatoebaCandidateProvider,
    TatoebaApiCandidateProvider,
    TatoebaSentenceSource,
)
from multilang.services.text_generation import TextGenerationService
from multilang.services.text_review import ReviewReport, TextReviewService
from multilang.services.text_validation import TextValidationService
from multilang.settings import Settings
from multilang.domain.jobs import SupportedLanguage

_LANGUAGE_NAMES = {
    SupportedLanguage.PT: "Portuguese",
    SupportedLanguage.ES: "Spanish",
    SupportedLanguage.EN: "English",
    SupportedLanguage.FR: "French",
    SupportedLanguage.DE: "German",
    SupportedLanguage.IT: "Italian",
    SupportedLanguage.PL: "Polish",
    SupportedLanguage.TR: "Turkish",
    SupportedLanguage.RO: "Romanian",
    SupportedLanguage.RU: "Russian",
    SupportedLanguage.NL: "Dutch",
}


@dataclass(slots=True)
class RuntimeTextResult:
    processed_items: int
    accepted_items: int
    review_required_items: int
    audio_processed_items: int = 0
    audio_reused_items: int = 0
    fallback_audio_items: int = 0
    failed_audio_items: int = 0


@dataclass(slots=True)
class RuntimeExportResult:
    output_path: Path
    card_count: int


class RuntimeGenerateService(IngestLexicalItemsService):
    """Repository-backed shipped runtime that composes lexical and Phase 3 text work."""

    def __init__(
        self,
        *,
        text_repository: TextRepository,
        audio_repository: AudioRepository,
        export_repository: ExportRepository,
        generate_text_items_service: GenerateTextItemsService,
        regenerate_text_item_service: RegenerateTextItemService,
        text_review_service: TextReviewService,
        generate_audio_items_service: GenerateAudioItemsService,
        assemble_export_cards_service: AssembleExportCardsService,
        runtime_settings: Settings,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.text_repository = text_repository
        self.audio_repository = audio_repository
        self.export_repository = export_repository
        self.generate_text_items_service = generate_text_items_service
        self.regenerate_text_item_service = regenerate_text_item_service
        self.text_review_service = text_review_service
        self.generate_audio_items_service = generate_audio_items_service
        self.assemble_export_cards_service = assemble_export_cards_service
        self.settings = runtime_settings

    def generate_text(self, *, job_id: str, deck_language: object) -> RuntimeTextResult:
        result = self.generate_text_items_service.execute(job_id=job_id, deck_language=deck_language)
        audio_result = self.generate_audio_items_service.execute(
            job_id=job_id,
            deck_language=deck_language,
        )
        return RuntimeTextResult(
            processed_items=result.processed_items,
            accepted_items=result.accepted_items,
            review_required_items=result.review_required_items,
            audio_processed_items=audio_result.processed_items,
            audio_reused_items=audio_result.reused_items,
            fallback_audio_items=audio_result.fallback_items,
            failed_audio_items=audio_result.failed_items,
        )

    def regenerate_text_item(self, *, job_id: str, item_key: str, deck_language: object) -> RuntimeTextResult:
        record = self.regenerate_text_item_service.execute(
            job_id=job_id,
            item_key=item_key,
            deck_language=deck_language,
        )
        audio_result = self.generate_audio_items_service.execute(
            job_id=job_id,
            deck_language=deck_language,
            item_keys={item_key},
        )
        return RuntimeTextResult(
            processed_items=1,
            accepted_items=1 if record.review_status.value == "accepted" else 0,
            review_required_items=1 if record.review_status.value == "review_required" else 0,
            audio_processed_items=audio_result.processed_items,
            audio_reused_items=audio_result.reused_items,
            fallback_audio_items=audio_result.fallback_items,
            failed_audio_items=audio_result.failed_items,
        )

    def build_review_report(self, *, job_id: str, output_path: object) -> ReviewReport:
        return self.text_review_service.build_review_report(job_id=job_id, output_path=output_path)

    def export_job(
        self,
        *,
        job_id: str,
        export_format: ExportArtifactFormat,
        output_dir: Path,
        deck_name: str | None = None,
    ) -> RuntimeExportResult:
        job = self.job_service.repository.get_job(job_id)
        if job is None:
            raise ValueError(f"unknown job_id: {job_id}")

        rows = self.export_repository.list_card_snapshots(job_id)
        if not rows:
            rows = self.assemble_export_cards_service.execute(
                job_id=job_id,
                deck_language=SupportedLanguage(job.language),
            ).cards

        resolved_deck_name = _sanitize_deck_name(deck_name or _default_deck_name(SupportedLanguage(job.language)))
        output_path = output_dir / f"{job_id}.{export_format.value}"
        media_index = self._build_media_index(rows)
        if export_format is ExportArtifactFormat.APKG:
            package_result = export_anki_package(
                rows=rows,
                media_index=media_index,
                output_path=output_path,
                deck_name=resolved_deck_name,
            )
            card_count = package_result.card_count
        else:
            tabular_result = write_export_tabular_bundle(
                rows=rows,
                export_format=export_format,
                output_dir=output_dir,
                deck_name=resolved_deck_name,
                note_type_name=NOTE_TYPE_NAME,
            )
            if tabular_result.output_path != output_path:
                tabular_result.output_path.replace(output_path)
            card_count = tabular_result.card_count

        self.export_repository.upsert_deck_export(
            ExportDeckArtifact(
                job_id=job_id,
                export_format=export_format,
                deck_name=resolved_deck_name,
                output_path=str(output_path),
                card_count=card_count,
                status=ExportArtifactStatus.COMPLETED,
            )
        )
        return RuntimeExportResult(output_path=output_path, card_count=card_count)

    def _build_media_index(self, rows: list[object]) -> dict[str, Path]:
        media_index: dict[str, Path] = {}
        for row in rows:
            word_asset = self.audio_repository.get_asset(row.identity.job_id, row.identity.item_key, AudioAssetKind.WORD)
            sentence_asset = self.audio_repository.get_asset(row.identity.job_id, row.identity.item_key, AudioAssetKind.SENTENCE)
            if word_asset is None or sentence_asset is None:
                raise ValueError(f"missing required audio for item {row.identity.item_key}")
            word_path = Path(word_asset.provenance.storage_path)
            sentence_path = Path(sentence_asset.provenance.storage_path)
            _validate_media_reference(sound_tag=row.word_audio, media_path=word_path)
            _validate_media_reference(sound_tag=row.sentence_audio, media_path=sentence_path)
            media_index[row.word_audio] = word_path
            media_index[row.sentence_audio] = sentence_path
        return media_index


def _validate_media_reference(*, sound_tag: str, media_path: Path) -> None:
    expected_sound_tag = f"[sound:{media_path.name}]"
    if sound_tag != expected_sound_tag:
        raise ValueError(f"media basename mismatch for {media_path.name}")
    if not media_path.exists():
        raise ValueError(f"missing media file for {media_path.name}")


def build_runtime_service(
    settings: Settings | None = None,
    *,
    audio_adapter: AudioSynthesisAdapter | None = None,
) -> IngestLexicalItemsService:
    """Construct the repository-backed orchestration service from runtime settings."""

    runtime_settings = settings or Settings()
    engine = create_engine(runtime_settings.database_url)
    Base.metadata.create_all(engine)
    session = Session(engine)
    job_repository = JobRepository(session)
    lexical_repository = LexicalRepository(session)
    text_repository = TextRepository(session)
    audio_repository = AudioRepository(session)
    export_repository = ExportRepository(session)
    generate_job_service = GenerateJobService(job_repository)
    text_generation_service = TextGenerationService(
        sentence_adapter=LocalSentenceAdapter(),
        translation_adapter=LocalTranslationAdapter(),
    )
    text_validation_service = TextValidationService()
    tatoeba_sentence_source = TatoebaSentenceSource(
        candidate_provider=(
            TatoebaApiCandidateProvider()
            if runtime_settings.tatoeba_enabled
            else StaticTatoebaCandidateProvider()
        )
    )
    audio_synthesis_service = AudioSynthesisService(
        adapter=audio_adapter or AzureSpeechAdapter(runtime_settings),
        settings=runtime_settings,
    )
    return RuntimeGenerateService(
        job_service=generate_job_service,
        lexical_repo=lexical_repository,
        settings=runtime_settings,
        text_repository=text_repository,
        audio_repository=audio_repository,
        export_repository=export_repository,
        generate_text_items_service=GenerateTextItemsService(
            job_repository=job_repository,
            lexical_repository=lexical_repository,
            text_repository=text_repository,
            text_generation_service=text_generation_service,
            text_validation_service=text_validation_service,
            tatoeba_sentence_source=tatoeba_sentence_source,
        ),
        regenerate_text_item_service=RegenerateTextItemService(
            job_repository=job_repository,
            lexical_repository=lexical_repository,
            text_repository=text_repository,
            text_generation_service=text_generation_service,
            text_validation_service=text_validation_service,
        ),
        text_review_service=TextReviewService(text_repository=text_repository),
        generate_audio_items_service=GenerateAudioItemsService(
            job_repository=job_repository,
            lexical_repository=lexical_repository,
            text_repository=text_repository,
            audio_repository=audio_repository,
            audio_synthesis_service=audio_synthesis_service,
        ),
        assemble_export_cards_service=AssembleExportCardsService(
            text_repository=text_repository,
            lexical_repository=lexical_repository,
            audio_repository=audio_repository,
            export_repository=export_repository,
        ),
        runtime_settings=runtime_settings,
    )


def _sanitize_deck_name(deck_name: str) -> str:
    return " ".join(deck_name.replace("::", " - ").split())


def _default_deck_name(language: SupportedLanguage) -> str:
    return f"Multilang {_LANGUAGE_NAMES[language]}"
