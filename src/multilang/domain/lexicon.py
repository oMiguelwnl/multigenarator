"""Typed lexical candidate contracts for Phase 2 ingestion."""

from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import KoreanLexicalIdentity

DEFAULT_DEFINITION_LANGUAGE = "en"


class GroundingStatus(str, Enum):
    PENDING = "pending"
    GROUNDED = "grounded"
    INSUFFICIENT = "insufficient"
    BACKFILL_REQUIRED = "backfill_required"


class DefinitionRecord(BaseModel):
    source: str = Field(min_length=1)
    value: str | None = None
    fallback_used: bool = False


class PronunciationRecord(BaseModel):
    source: str = Field(min_length=1)
    value: str | None = None
    authoritative: bool = True


class LexicalProvenance(BaseModel):
    source: str = Field(min_length=1)
    definition: DefinitionRecord | None = None
    pronunciation: PronunciationRecord | None = None
    notes: list[str] = Field(default_factory=list)


class DeckLanguagePolicy(BaseModel):
    deck_language: SupportedLanguage
    definition_language: str = DEFAULT_DEFINITION_LANGUAGE
    translation_target_language: str


class WordListLineResult(BaseModel):
    line_number: int = Field(ge=1)
    submitted_text: str = Field(min_length=1)
    item_key: str = Field(min_length=1)
    warning_code: str | None = None
    warning_detail: str | None = None


class LexicalCardCandidate(BaseModel):
    submitted_form: str = Field(min_length=1)
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    lemma_key: str = Field(min_length=1)
    frequency_rank: int | None = Field(default=None, ge=1)
    frequency_level: int | None = Field(default=None, ge=1, le=3)
    definitions_html: str | None = None
    definition_language: str = DEFAULT_DEFINITION_LANGUAGE
    ipa: str | None = None
    spoken_form: str | None = None
    translation_target_language: str = Field(min_length=2)
    grounding_status: GroundingStatus
    warning_code: str | None = None
    warning_detail: str | None = None
    provenance: LexicalProvenance
    korean_identity: KoreanLexicalIdentity | None = None

    @model_validator(mode="after")
    def korean_identity_must_match_candidate(self) -> Self:
        identity = self.korean_identity
        if identity is None:
            return self
        if self.lemma != identity.lemma:
            raise ValueError("Korean identity lemma must match candidate lemma")
        if self.lemma_key != identity.lexical_key:
            raise ValueError("Korean identity key must match candidate lemma_key")
        return self


def policy_for_language(language: SupportedLanguage) -> DeckLanguagePolicy:
    output_language = (
        "pt"
        if language in {SupportedLanguage.EN, SupportedLanguage.KO}
        else DEFAULT_DEFINITION_LANGUAGE
    )
    return DeckLanguagePolicy(
        deck_language=language,
        definition_language=output_language,
        translation_target_language=output_language,
    )


__all__ = [
    "DEFAULT_DEFINITION_LANGUAGE",
    "DeckLanguagePolicy",
    "DefinitionRecord",
    "GroundingStatus",
    "LexicalCardCandidate",
    "LexicalProvenance",
    "PronunciationRecord",
    "WordListLineResult",
    "policy_for_language",
]
