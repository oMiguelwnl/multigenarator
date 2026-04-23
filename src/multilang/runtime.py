"""Runtime bootstrap for the shipped CLI path."""

from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.text_repository import TextRepository
from multilang.services.generate_job import GenerateJobService
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


class RuntimeGenerateService(IngestLexicalItemsService):
    """Repository-backed shipped runtime that composes lexical and Phase 3 text work."""

    def __init__(
        self,
        *,
        text_repository: TextRepository,
        generate_text_items_service: GenerateTextItemsService,
        regenerate_text_item_service: RegenerateTextItemService,
        text_review_service: TextReviewService,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.text_repository = text_repository
        self.generate_text_items_service = generate_text_items_service
        self.regenerate_text_item_service = regenerate_text_item_service
        self.text_review_service = text_review_service

    def generate_text(self, *, job_id: str, deck_language: object) -> RuntimeTextResult:
        result = self.generate_text_items_service.execute(job_id=job_id, deck_language=deck_language)
        return RuntimeTextResult(
            processed_items=result.processed_items,
            accepted_items=result.accepted_items,
            review_required_items=result.review_required_items,
        )

    def regenerate_text_item(self, *, job_id: str, item_key: str, deck_language: object) -> RuntimeTextResult:
        record = self.regenerate_text_item_service.execute(
            job_id=job_id,
            item_key=item_key,
            deck_language=deck_language,
        )
        return RuntimeTextResult(
            processed_items=1,
            accepted_items=1 if record.review_status.value == "accepted" else 0,
            review_required_items=1 if record.review_status.value == "review_required" else 0,
        )

    def build_review_report(self, *, job_id: str, output_path: object) -> ReviewReport:
        return self.text_review_service.build_review_report(job_id=job_id, output_path=output_path)


def build_runtime_service(settings: Settings | None = None) -> IngestLexicalItemsService:
    """Construct the repository-backed orchestration service from runtime settings."""

    runtime_settings = settings or Settings()
    engine = create_engine(runtime_settings.database_url)
    Base.metadata.create_all(engine)
    session = Session(engine)
    job_repository = JobRepository(session)
    lexical_repository = LexicalRepository(session)
    text_repository = TextRepository(session)
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
    return RuntimeGenerateService(
        job_service=generate_job_service,
        lexical_repo=lexical_repository,
        settings=runtime_settings,
        text_repository=text_repository,
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
