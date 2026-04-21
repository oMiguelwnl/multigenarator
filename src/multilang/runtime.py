"""Runtime bootstrap for the shipped CLI path."""

from __future__ import annotations

from dataclasses import dataclass

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


class _TemplateSentenceAdapter:
    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        if "flag" in request.display_form.casefold():
            sentence = f"placeholder {request.display_form} placeholder"
        else:
            sentence = f"I use {request.display_form} every day."
        return SentenceGenerationResult(
            sentence=sentence,
            intended_sense=request.definitions_html,
            provenance={"source": "runtime-template-generator", "provider": "local"},
        )


class _TemplateTranslationAdapter:
    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        if "placeholder" in request.sentence.casefold():
            translation = request.sentence
        else:
            catalog = {
                "de": "Ich benutze das jeden Tag.",
                "en": "I use this every day.",
                "es": "Yo uso esto todos los días.",
                "fr": "J'utilise cela tous les jours.",
                "nl": "Ik gebruik dit elke dag.",
                "pt": "Eu uso isso todos os dias.",
                "ru": "Я использую это каждый день.",
            }
            translation = catalog.get(request.translation_target_language, request.sentence)
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
