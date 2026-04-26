"""Runtime bootstrap for the shipped CLI path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

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
from multilang.services.regenerate_text_item import RegenerateTextItemService
from multilang.services.tatoeba_sentence_source import (
    StaticTatoebaCandidateProvider,
    TatoebaApiCandidateProvider,
    TatoebaSentenceSource,
)
from multilang.services.text_generation import (
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceTranslationRequest,
    SentenceTranslationResult,
    TextGenerationService,
)
from multilang.services.text_review import ReviewReport, TextReviewService
from multilang.services.text_validation import TextValidationService
from multilang.settings import Settings
from multilang.domain.jobs import SupportedLanguage

_DEFINITION_RE = re.compile(r"<[^>]+>")

_SENSE_ALIASES = {
    "lavar": "wash",
    "lavarse": "wash",
    "se laver": "wash",
    "use": "use",
    "usar": "use",
    "wash": "wash",
}

_SENSE_TRANSLATIONS = {
    "use": {
        "de": "benutzen",
        "en": "use",
        "es": "usar",
        "fr": "utiliser",
        "nl": "gebruiken",
        "pt": "usar",
        "ru": "использовать",
    },
    "wash": {
        "de": "waschen",
        "en": "wash",
        "es": "lavarse",
        "fr": "se laver",
        "nl": "wassen",
        "pt": "lavar",
        "ru": "мыться",
    },
}

_VERB_TEMPLATES = {
    "de": "Es ist gut, jeden Tag {term} zu können.",
    "en": "It is good to {term} every day.",
    "es": "Es bueno {term} cada día.",
    "fr": "Il est bon de {term} chaque jour.",
    "nl": "Het is goed om elke dag {term} te kunnen.",
    "pt": "É bom {term} todos os dias.",
    "ru": "Полезно {term} каждый день.",
}

_TERM_TEMPLATES = {
    "de": "Das Wort {term} ist im Alltag nützlich.",
    "en": "The word {term} is useful in daily life.",
    "es": "La palabra {term} es útil en la vida diaria.",
    "fr": "Le mot {term} est utile au quotidien.",
    "nl": "Het woord {term} is nuttig in het dagelijks leven.",
    "pt": "A palavra {term} é útil no dia a dia.",
    "ru": "Слово {term} полезно в повседневной жизни.",
}
class _TemplateSentenceAdapter:
    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        sense_key = _infer_sense_key(request.definitions_html, request.display_form)
        sense_hint = _sense_hint(request.definitions_html, request.display_form)
        if request.target_language not in _VERB_TEMPLATES:
            raise ValueError(f"unsupported runtime template language: {request.target_language}")

        if "flag" in request.display_form.casefold():
            sentence = f"placeholder {request.display_form} placeholder"
            template_kind = "flagged"
            uncertainty_notes = ["local runtime inserted a placeholder review case"]
        else:
            template_kind = "verb" if sense_key is not None else "term"
            templates = _VERB_TEMPLATES if template_kind == "verb" else _TERM_TEMPLATES
            sentence = templates[request.target_language].format(term=request.display_form)
            uncertainty_notes = []
            if template_kind == "term":
                uncertainty_notes.append("local runtime used a generic term template")

        return SentenceGenerationResult(
            sentence=sentence,
            intended_sense=sense_key or sense_hint,
            uncertainty_notes=uncertainty_notes,
            provenance={
                "source": "runtime-template-generator",
                "provider": "local",
                "template_kind": template_kind,
                "sense_key": sense_key,
            },
        )


class _TemplateTranslationAdapter:
    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        if "placeholder" in request.sentence.casefold():
            translation = request.sentence
        else:
            term = _localized_sense(
                request.intended_sense,
                language=request.translation_target_language,
            )
            template_kind = request.template_kind or "term"
            templates = _VERB_TEMPLATES if template_kind == "verb" else _TERM_TEMPLATES
            template = templates.get(request.translation_target_language)
            translation = template.format(term=term) if template is not None else request.sentence
        return SentenceTranslationResult(
            translation=translation,
            provenance={"source": "runtime-template-translator", "provider": "local"},
        )


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

        resolved_deck_name = _sanitize_deck_name(deck_name or f"Multilang {job.language.upper()} {job_id[:8]}")
        output_path = output_dir / f"{job_id}.{export_format.value}"
        if export_format is ExportArtifactFormat.APKG:
            package_result = export_anki_package(
                rows=rows,
                media_index=self._build_media_index(rows),
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
            media_index[row.word_audio] = Path(word_asset.provenance.storage_path)
            media_index[row.sentence_audio] = Path(sentence_asset.provenance.storage_path)
        return media_index


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
        sentence_adapter=_TemplateSentenceAdapter(),
        translation_adapter=_TemplateTranslationAdapter(),
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


def _sense_hint(definitions_html: str | None, display_form: str) -> str:
    first_gloss = _first_gloss(definitions_html)
    if not first_gloss:
        return display_form

    if first_gloss.startswith("definition for "):
        candidate = first_gloss.removeprefix("definition for ").strip()
        return candidate or display_form

    if first_gloss.startswith("to "):
        candidate = first_gloss.removeprefix("to ").strip()
        return candidate or display_form

    return first_gloss


def _infer_sense_key(definitions_html: str | None, display_form: str) -> str | None:
    candidates = [display_form.casefold(), _sense_hint(definitions_html, display_form).casefold()]
    for candidate in candidates:
        if candidate in _SENSE_ALIASES:
            return _SENSE_ALIASES[candidate]
    return None


def _localized_sense(sense_hint: str | None, *, language: str) -> str:
    if not sense_hint:
        return "this"

    sense_key = _SENSE_ALIASES.get(sense_hint.casefold(), sense_hint.casefold())
    return _SENSE_TRANSLATIONS.get(sense_key, {}).get(language, sense_hint)


def _first_gloss(definitions_html: str | None) -> str:
    if not definitions_html:
        return ""

    first_segment = definitions_html.split("<br>", 1)[0]
    stripped = _DEFINITION_RE.sub(" ", first_segment)
    return " ".join(stripped.casefold().split())


def _sanitize_deck_name(deck_name: str) -> str:
    return " ".join(deck_name.replace("::", " - ").split())
