"""Latin to Portuguese translation generation and repair contracts."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from multilang.services.latin_source_pack import LatinMvpSourcePackEntry
from multilang.services.latin_translation_quality import LatinPortugueseTranslationEntry, LatinPortugueseTranslationQaService


class LatinPortugueseDraftTranslation(BaseModel):
    """Draft translation produced by Google Translate before OpenRouter QA/repair."""

    short_translation_pt: str = Field(min_length=1)
    sentence_translation_pt: str = Field(min_length=1)
    translation_notes: str = Field(min_length=1)


LatinPortugueseTranslator = Callable[[LatinMvpSourcePackEntry], LatinPortugueseDraftTranslation | dict[str, object]]
LatinPortugueseRepairer = Callable[[LatinPortugueseTranslationEntry], LatinPortugueseTranslationEntry | dict[str, object]]


class LatinTranslationGenerationService:
    """Generate Portuguese translations with Google-first and optional OpenRouter repair."""

    def __init__(
        self,
        translator: LatinPortugueseTranslator,
        repairer: LatinPortugueseRepairer | None = None,
        qa_service: LatinPortugueseTranslationQaService | None = None,
    ) -> None:
        self.translator = translator
        self.repairer = repairer
        self.qa_service = qa_service or LatinPortugueseTranslationQaService()

    def translate_entry(self, source_entry: LatinMvpSourcePackEntry) -> LatinPortugueseTranslationEntry:
        draft = LatinPortugueseDraftTranslation.model_validate(self.translator(source_entry))
        entry = LatinPortugueseTranslationEntry(
            item_key=source_entry.item_key,
            source_pack_version=source_entry.source_pack_version,
            lemma=source_entry.lemma,
            target_form=source_entry.target_form,
            latin_sentence=source_entry.latin_sentence,
            short_translation_pt=draft.short_translation_pt,
            sentence_translation_pt=draft.sentence_translation_pt,
            translation_notes=draft.translation_notes,
            review_status="approved",
        )
        if self.qa_service.validate_entry(entry).issues and self.repairer is not None:
            entry = LatinPortugueseTranslationEntry.model_validate(self.repairer(entry))
        result = self.qa_service.validate_entry(entry)
        if result.issues:
            raise ValueError("Latin Portuguese translation failed QA")
        return entry


__all__ = [
    "LatinPortugueseDraftTranslation",
    "LatinTranslationGenerationService",
]
