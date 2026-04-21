"""Typed boundaries for Phase 3 sentence generation and translation."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate


class SentenceGenerationRequest(BaseModel):
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions_html: str | None = None
    target_language: str = Field(min_length=2)
    translation_target_language: str = Field(min_length=2)

    @classmethod
    def from_candidate(
        cls,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
    ) -> "SentenceGenerationRequest":
        if candidate.grounding_status is not GroundingStatus.GROUNDED:
            raise ValueError("sentence generation requires a grounded lexical candidate")
        return cls(
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions_html=candidate.definitions_html,
            target_language=deck_language.value,
            translation_target_language=candidate.translation_target_language,
        )


class SentenceGenerationResult(BaseModel):
    sentence: str = Field(min_length=1)
    intended_sense: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class SentenceTranslationRequest(BaseModel):
    sentence: str = Field(min_length=1)
    translation_target_language: str = Field(min_length=2)

    @classmethod
    def from_sentence(
        cls,
        *,
        sentence_result: SentenceGenerationResult,
        translation_target_language: str,
    ) -> "SentenceTranslationRequest":
        return cls(
            sentence=sentence_result.sentence,
            translation_target_language=translation_target_language,
        )


class SentenceTranslationResult(BaseModel):
    translation: str = Field(min_length=1)
    provenance: dict[str, Any] = Field(default_factory=dict)


class SentenceGenerationAdapter(Protocol):
    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult: ...


class SentenceTranslationAdapter(Protocol):
    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult: ...


__all__ = [
    "SentenceGenerationAdapter",
    "SentenceGenerationRequest",
    "SentenceGenerationResult",
    "SentenceTranslationAdapter",
    "SentenceTranslationRequest",
    "SentenceTranslationResult",
]
