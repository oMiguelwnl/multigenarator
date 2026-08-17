"""Domain contracts for local Kindle highlight normalization."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from multilang.domain.korean import KoreanLexicalIdentity


class HighlightProvenance(BaseModel):
    """Traceable source metadata for one normalized highlight."""

    source_path: str = Field(min_length=1)
    source_format: Literal["html", "text"]
    source_index: int = Field(ge=0)
    raw_location: str | None = None
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256_hex(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("content_hash must be lowercase SHA-256 hex")
        return value


class NormalizedHighlight(BaseModel):
    """A privacy-preserving highlight ready for downstream extraction."""

    highlight_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    provenance: HighlightProvenance


class RejectedHighlight(BaseModel):
    """A rejected source record with safe diagnostics."""

    source_index: int = Field(ge=0)
    reason_code: Literal["empty", "malformed", "unsafe", "unsupported_format"]
    detail: str = Field(min_length=1)


class KindleParseResult(BaseModel):
    """Result of parsing a local Kindle export."""

    highlights: list[NormalizedHighlight] = Field(default_factory=list)
    rejected: list[RejectedHighlight] = Field(default_factory=list)


class HighlightCandidate(BaseModel):
    """A reviewable vocabulary candidate extracted from normalized highlights."""

    item_key: str = Field(min_length=1)
    source_content_hash: str = Field(min_length=64, max_length=64)
    display_form: str = Field(min_length=1)
    lemma_key: str = Field(min_length=1)
    first_highlight_id: str = Field(min_length=1)
    first_source_index: int = Field(ge=0)
    occurrence_count: int = Field(ge=1)
    korean_identity: KoreanLexicalIdentity | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @field_validator("source_content_hash")
    @classmethod
    def source_content_hash_must_be_sha256_hex(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("source_content_hash must be lowercase SHA-256 hex")
        return value

    @model_validator(mode="after")
    def korean_identity_must_match_safe_candidate(self) -> Self:
        if self.korean_identity is None:
            return self
        if self.display_form != self.korean_identity.lemma:
            raise ValueError("Korean highlight display must use the source lemma")
        if self.lemma_key != self.korean_identity.lexical_key:
            raise ValueError("Korean highlight key must use the complete source identity")
        return self


class HighlightExtractionError(BaseModel):
    """Content-free extraction failure tied only to an allowed source index."""

    source_index: int = Field(ge=0)
    reason_code: Literal[
        "korean_resolver_required",
        "korean_resolution_failed",
        "korean_resolution_unavailable",
    ]


class HighlightImportManifest(BaseModel):
    """Safe count/hash-only manifest for one highlight import."""

    import_content_hash: str = Field(min_length=64, max_length=64)
    candidate_keys: list[str] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)

    @field_validator("import_content_hash")
    @classmethod
    def import_content_hash_must_be_sha256_hex(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("import_content_hash must be lowercase SHA-256 hex")
        return value


class HighlightCandidateExtractionResult(BaseModel):
    """Candidate extraction output with deterministic filtering counters."""

    candidates: list[HighlightCandidate] = Field(default_factory=list)
    duplicate_count: int = Field(ge=0)
    rejected_token_count: int = Field(ge=0)
    errors: list[HighlightExtractionError] = Field(
        default_factory=list,
        exclude_if=lambda value: not value,
    )


class HighlightImportPreview(BaseModel):
    """Count-only preview of a local Kindle import before generation."""

    imported_highlights: int = Field(ge=0)
    extracted_candidates: int = Field(ge=0)
    rejected_highlights: int = Field(ge=0)
    duplicate_candidates: int = Field(ge=0)
    planned_cards: int = Field(ge=0)


__all__ = [
    "HighlightCandidate",
    "HighlightCandidateExtractionResult",
    "HighlightExtractionError",
    "HighlightImportManifest",
    "HighlightImportPreview",
    "HighlightProvenance",
    "KindleParseResult",
    "NormalizedHighlight",
    "RejectedHighlight",
]
