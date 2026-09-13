"""Source-bound observations; measurements are proposals, never sense authority."""

from __future__ import annotations

import unicodedata
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import Field, computed_field, field_validator, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import UnitDecimal, canonical_sha256

EvidenceSplit = Literal["pilot", "calibration", "evaluation"]
LEXICAL_UPOS = frozenset(
    "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN SCONJ VERB".split()
)
NativeFeatureValue = Annotated[str, Field(min_length=1, max_length=64000)]


class EvidenceDocument(NativeContract):
    source_sha256: Sha256
    document_id: Identifier
    text_sha256: Sha256
    token_count: int = Field(ge=1, le=10**9)


class CorpusEvidenceContext(NativeContract):
    language: SupportedLanguage
    split: EvidenceSplit
    source_sha256s: tuple[Sha256, ...] = Field(min_length=1, max_length=1000)
    token_count: int = Field(ge=1, le=10**12)
    documents: tuple[EvidenceDocument, ...] = Field(default=(), max_length=100000)
    sampling_description: str = Field(
        default="Declared sample; general representativeness unverified", max_length=4000
    )

    @model_validator(mode="after")
    def consistent_documents(self) -> Self:
        keys = [(d.source_sha256, d.document_id) for d in self.documents]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate document identity")
        if any(d.source_sha256 not in self.source_sha256s for d in self.documents):
            raise ValueError("document source not declared")
        if self.documents and sum(d.token_count for d in self.documents) != self.token_count:
            raise ValueError("document token denominators do not match corpus")
        counts: dict[str, int] = {}
        for doc in self.documents:
            if doc.text_sha256 in counts and counts[doc.text_sha256] != doc.token_count:
                raise ValueError("duplicate document has conflicting token count")
            counts[doc.text_sha256] = doc.token_count
        return self


class EvidenceOccurrence(NativeContract):
    language: SupportedLanguage
    split: EvidenceSplit
    source_sha256: Sha256
    document_id: Identifier | None = None
    sentence_id: Identifier
    sentence: str = Field(min_length=1, max_length=64000)
    start: int = Field(ge=0, le=64000)
    end: int = Field(ge=1, le=64000)
    text: str = Field(min_length=1, max_length=512)
    lemma: str = Field(min_length=1, max_length=512)
    pos: Identifier
    features: dict[Identifier, NativeFeatureValue] = Field(default_factory=dict, max_length=64)
    sense_id: Identifier | None = None

    @field_validator("pos")
    @classmethod
    def universal_pos(cls, value: str) -> str:
        if value not in LEXICAL_UPOS | {"X", "PUNCT", "SYM"}:
            raise ValueError("unsupported universal POS")
        return value

    @field_validator("sense_id")
    @classmethod
    def resolved_sense(cls, value: str | None) -> str | None:
        if value is not None and value.casefold() in {
            "unknown",
            "unresolved",
            "none",
            "null",
            "?",
            "unk",
            "x",
        }:
            raise ValueError("reserved unresolved sense identifier")
        return value

    @field_validator("sentence", "text", "lemma")
    @classmethod
    def exact_nfc(cls, value: str) -> str:
        if value != unicodedata.normalize("NFC", value):
            raise ValueError("occurrence source must already be NFC; offsets cannot be normalized")
        return value

    @model_validator(mode="after")
    def exact_span(self) -> Self:
        if self.end <= self.start or self.sentence[self.start : self.end] != self.text:
            raise ValueError("occurrence must match exact source span")
        return self

    @computed_field
    @property
    def group_sha256(self) -> str:
        return canonical_sha256(
            {
                k: self.model_dump(mode="json", exclude_computed_fields=True)[k]
                for k in ("language", "lemma", "pos", "text", "features", "sense_id")
            }
        )


class FormEvidenceMeasurement(NativeContract):
    group_sha256: Sha256
    language: SupportedLanguage
    lemma: str
    pos: Identifier
    text: str
    features: dict[Identifier, NativeFeatureValue]
    sense_id: Identifier | None
    observed_count: int = Field(ge=1)
    document_count: int | None = Field(default=None, ge=1)
    frequency_per_million: Decimal = Field(ge=0, allow_inf_nan=False)
    dispersion: UnitDecimal | None = None
    dispersion_missing_reason: str | None = None
    evidence_values: dict[str, UnitDecimal]
    missing_reasons: dict[str, str]
    occurrence_sha256s: tuple[Sha256, ...]
    population_sha256: Sha256
    method: Literal["sample-midrank-cdf-1"] = "sample-midrank-cdf-1"
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def measurement_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class FormEvidenceReport(NativeContract):
    context_sha256: Sha256
    population_sha256: Sha256
    effective_token_count: int
    effective_document_count: int | None
    duplicate_occurrences: int
    ambiguous_occurrences: int
    ineligible_occurrences: int
    measurements: tuple[FormEvidenceMeasurement, ...]
    production_eligible: Literal[False] = False
