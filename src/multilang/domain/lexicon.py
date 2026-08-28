"""Typed lexical candidate contracts for Phase 2 ingestion."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import (
    KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT,
    KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT,
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
)

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


_HEX = frozenset("0123456789abcdef")


def _sha256(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


class KoreanFrequencyLexicalEvidence(BaseModel):
    """Source-backed lexical authority for one Korean final frequency candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    source_id: Literal["nikl-korean-learners-vocabulary"]
    source_version: str = Field(min_length=1, max_length=128)
    source_rank: int = Field(ge=1, le=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT)
    final_rank: int = Field(ge=1, le=KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT)
    level: int = Field(ge=1, le=3)
    part_of_speech: str = Field(min_length=1, max_length=32)
    sense_id: str = Field(min_length=1, max_length=128)
    grounding_confidence: Literal["source-backed", "reviewed-source-backed"]
    license_decision: str = Field(min_length=1, max_length=128)
    curation_decision: Literal["accepted"]
    bundle_sha256: str = Field(min_length=64, max_length=64)
    source_sha256: str = Field(min_length=64, max_length=64)
    source_review_receipt_sha256: str = Field(min_length=64, max_length=64)
    source_review_aggregate_sha256: str = Field(min_length=64, max_length=64)
    analyzer_fingerprint: KoreanAnalyzerFingerprint

    @field_validator(
        "bundle_sha256",
        "source_sha256",
        "source_review_receipt_sha256",
        "source_review_aggregate_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def level_must_match_final_rank(self) -> Self:
        expected_level = ((self.final_rank - 1) // 1000) + 1
        if self.level != expected_level:
            raise ValueError("Korean frequency lexical evidence level drift")
        return self


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
    korean_frequency_evidence: KoreanFrequencyLexicalEvidence | None = None

    @model_validator(mode="after")
    def korean_identity_must_match_candidate(self) -> Self:
        identity = self.korean_identity
        if identity is None:
            return self
        if self.lemma != identity.lemma:
            raise ValueError("Korean identity lemma must match candidate lemma")
        if self.lemma_key != identity.lexical_key:
            raise ValueError("Korean identity key must match candidate lemma_key")
        evidence = self.korean_frequency_evidence
        if evidence is None:
            return self
        if self.frequency_rank != evidence.final_rank:
            raise ValueError("Korean frequency evidence rank must match candidate rank")
        if self.frequency_level != evidence.level:
            raise ValueError("Korean frequency evidence level must match candidate level")
        if evidence.part_of_speech != identity.part_of_speech:
            raise ValueError("Korean frequency evidence POS must match identity")
        if evidence.sense_id != identity.sense_id:
            raise ValueError("Korean frequency evidence sense must match identity")
        if evidence.analyzer_fingerprint != identity.analyzer_fingerprint:
            raise ValueError("Korean frequency evidence analyzer fingerprint drift")
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
    "KoreanFrequencyLexicalEvidence",
    "LexicalCardCandidate",
    "LexicalProvenance",
    "PronunciationRecord",
    "WordListLineResult",
    "policy_for_language",
]
