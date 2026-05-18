"""Runtime bootstrap for the shipped CLI path."""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.export_repository import ExportRepository
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.text_repository import TextRepository
from multilang.domain.audio import AudioAssetKind
from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportArtifactStatus,
    ExportDeckArtifact,
    export_field_names_for_source_type,
)
from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.audio_synthesis import (
    AudioSynthesisAdapter,
    AudioSynthesisService,
)
from multilang.services.assemble_export_cards import AssembleExportCardsService
from multilang.services.audio_integrity import assert_word_audio_matches_word
from multilang.services.export_anki_package import MANUAL_NOTE_TYPE_NAME, NOTE_TYPE_NAME, export_anki_package
from multilang.services.export_tabular_bundle import ExportTabularBundleResult, write_export_tabular_bundle
from multilang.services.generate_job import GenerateJobService
from multilang.services.generate_audio_items import GenerateAudioItemsService
from multilang.services.generate_text_items import GenerateTextItemsService
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.lexical_lookup import LexicalLookup
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.local_text_adapter import LocalSentenceAdapter, LocalTranslationAdapter
from multilang.services.provider_text_adapters import (
    DeepLTranslationAdapter,
    FallbackTranslationAdapter,
    GoogleTranslateAdapter,
    LiteLLMSentenceAdapter,
    can_use_deepl,
    can_use_google_translate,
    can_use_litellm,
)
from multilang.services.provider_pronunciation_adapters import LiteLLMPronunciationAdapter
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
from multilang.domain.source_profiles import get_source_profile

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
                note_type_name=_note_type_name_for_rows(rows),
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
        asset_index = self._preload_audio_assets(rows)
        for row in rows:
            field_names = export_field_names_for_source_type(row.identity.source_type)
            if "word_audio" in field_names:
                word_asset = self._get_audio_asset(
                    asset_index=asset_index,
                    job_id=row.identity.job_id,
                    item_key=row.identity.item_key,
                    asset_kind=AudioAssetKind.WORD,
                )
                if word_asset is None:
                    raise ValueError(f"missing required word audio for item {row.identity.item_key}")
                assert_word_audio_matches_word(
                    word_asset,
                    unescape(row.word),
                    item_key=row.identity.item_key,
                )
                word_path = Path(word_asset.provenance.storage_path)
                _validate_media_reference(sound_tag=row.word_audio, media_path=word_path)
                _add_media_reference(media_index, sound_tag=row.word_audio, media_path=word_path)
            if "sentence_audio" in field_names:
                sentence_asset = self._get_audio_asset(
                    asset_index=asset_index,
                    job_id=row.identity.job_id,
                    item_key=row.identity.item_key,
                    asset_kind=AudioAssetKind.SENTENCE,
                )
                if sentence_asset is None:
                    raise ValueError(f"missing required sentence audio for item {row.identity.item_key}")
                sentence_path = Path(sentence_asset.provenance.storage_path)
                _validate_media_reference(sound_tag=row.sentence_audio, media_path=sentence_path)
                _add_media_reference(media_index, sound_tag=row.sentence_audio, media_path=sentence_path)
        return media_index

    def _preload_audio_assets(self, rows: list[object]) -> dict[tuple[str, str], object] | None:
        job_ids = {row.identity.job_id for row in rows}
        if len(job_ids) != 1 or not hasattr(self.audio_repository, "list_assets_for_job"):
            return None

        job_id = next(iter(job_ids))
        session = getattr(self.audio_repository, "session", None)
        expire_all = getattr(session, "expire_all", None)
        if callable(expire_all):
            expire_all()
        return {
            (asset.item_key, asset.asset_kind.value): asset
            for asset in self.audio_repository.list_assets_for_job(job_id)
        }

    def _get_audio_asset(
        self,
        *,
        asset_index: dict[tuple[str, str], object] | None,
        job_id: str,
        item_key: str,
        asset_kind: AudioAssetKind,
    ) -> object | None:
        if asset_index is not None:
            return asset_index.get((item_key, asset_kind.value))
        return self.audio_repository.get_asset(job_id, item_key, asset_kind)


def _validate_media_reference(*, sound_tag: str, media_path: Path) -> None:
    expected_sound_tag = f"[sound:{media_path.name}]"
    if sound_tag != expected_sound_tag:
        raise ValueError(f"media basename mismatch for {media_path.name}")
    if not media_path.exists():
        raise ValueError(f"missing media file for {media_path.name}")


def _add_media_reference(media_index: dict[str, Path], *, sound_tag: str, media_path: Path) -> None:
    existing_path = media_index.get(sound_tag)
    if existing_path is not None and existing_path != media_path:
        raise ValueError(f"conflicting media file for {sound_tag}")
    media_index[sound_tag] = media_path


def _build_translation_adapter(runtime_settings: Settings) -> object:
    if runtime_settings.translation_provider == "local":
        return LocalTranslationAdapter()
    if can_use_deepl(runtime_settings):
        return FallbackTranslationAdapter(
            primary=DeepLTranslationAdapter(runtime_settings),
            fallback=GoogleTranslateAdapter(),
        )
    if can_use_google_translate(runtime_settings):
        return GoogleTranslateAdapter()
    if runtime_settings.translation_provider == "deepl":
        raise ValueError("DeepL translation requires MULTILANG_DEEPL_API_KEY or DEEPL_API_KEY")
    raise ValueError(f"unsupported translation provider: {runtime_settings.translation_provider}")


def _build_sentence_adapter(runtime_settings: Settings) -> object:
    if runtime_settings.text_generation_provider == "local":
        return LocalSentenceAdapter()
    if can_use_litellm(runtime_settings):
        return LiteLLMSentenceAdapter(runtime_settings)
    if runtime_settings.text_generation_provider == "litellm":
        raise ValueError(
            "LiteLLM sentence generation requires MULTILANG_LITELLM_API_KEY, "
            "MULTILANG_OPENAI_API_KEY, or MULTILANG_OPENROUTER_API_KEY"
        )
    raise ValueError(f"unsupported text generation provider: {runtime_settings.text_generation_provider}")


def _build_pronunciation_adapter(runtime_settings: Settings) -> object | None:
    if can_use_litellm(runtime_settings):
        return LiteLLMPronunciationAdapter(runtime_settings)
    return None


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
    highlight_import_repository = HighlightImportRepository(session)
    generate_job_service = GenerateJobService(job_repository)
    translation_adapter = _build_translation_adapter(runtime_settings)
    sentence_adapter = _build_sentence_adapter(runtime_settings)
    text_generation_service = TextGenerationService(
        sentence_adapter=sentence_adapter,
        translation_adapter=translation_adapter,
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
        highlight_import_repo=highlight_import_repository,
        settings=runtime_settings,
        grounding_service=LexicalGroundingService(
            lookup=LexicalLookup(data_dir=runtime_settings.lexicon_data_dir),
            pronunciation_generator=_build_pronunciation_adapter(runtime_settings),
            definition_generator=sentence_adapter,
            allow_frequency_seed_fallback=True,
        ),
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
            highlight_import_repository=highlight_import_repository,
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


def _note_type_name_for_rows(rows: list[object]) -> str:
    source_types = {row.identity.source_type for row in rows}
    if len(source_types) > 1:
        raise ValueError("cannot export mixed source types in one note model")
    source_type = next(iter(source_types), "frequency")
    return get_source_profile(source_type).note_type_name
