"""Persisted lexical and morphological prerequisites, independent of card level."""

from __future__ import annotations

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.jobs import SupportedLanguage

UPOS = "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN SCONJ VERB".split()


class CurriculumLexeme(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    lemma: str = Field(min_length=1, max_length=256)
    pos: str

    @field_validator("lemma")
    @classmethod
    def normalized_lemma(cls, value: str) -> str:
        if value != value.strip() or not unicodedata.is_normalized("NFC", value):
            raise ValueError("curriculum lemma must be trimmed NFC")
        if any(unicodedata.category(c).startswith("C") for c in value):
            raise ValueError("curriculum lemma contains unsupported characters")
        return value

    @field_validator("pos")
    @classmethod
    def resolved_pos(cls, value: str) -> str:
        if value not in UPOS:
            raise ValueError("curriculum requires a resolved universal POS")
        return value

    @property
    def key(self) -> tuple[str, str]:
        return self.lemma, self.pos


class SentenceCurriculum(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    version: Literal["lexical-sentence-curriculum-1"] = "lexical-sentence-curriculum-1"
    language: SupportedLanguage
    inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    analyzer_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    target: CurriculumLexeme
    introduced: tuple[CurriculumLexeme, ...] = Field(default=(), max_length=256)
    allowed_features: tuple[tuple[str, str], ...] = Field(default=(), max_length=256)
    min_units: int = Field(default=4, ge=1, le=32, strict=True)
    max_units: int = Field(default=12, ge=1, le=48, strict=True)
    knowledge_basis: Literal["previously_introduced_not_observed_mastery"] = (
        "previously_introduced_not_observed_mastery"
    )
    length_unit: Literal["analyzer_lexical_tokens"] = "analyzer_lexical_tokens"

    @model_validator(mode="after")
    def consistent_prerequisites(self):
        if self.min_units > self.max_units:
            raise ValueError("curriculum length interval is reversed")
        if len({item.key for item in self.introduced}) != len(self.introduced):
            raise ValueError("duplicate curriculum prerequisite")
        if len(set(self.allowed_features)) != len(self.allowed_features):
            raise ValueError("duplicate grammar prerequisite")
        for pair in self.allowed_features:
            if any(not 0 < len(x) <= 128 or not x.isascii() or not all(
                c.isalnum() or c in "-_,=" for c in x
            ) for x in pair):
                raise ValueError("invalid grammar prerequisite")
        return self
