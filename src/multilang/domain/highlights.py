"""Domain contracts for local Kindle highlight normalization."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


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


__all__ = [
    "HighlightProvenance",
    "KindleParseResult",
    "NormalizedHighlight",
    "RejectedHighlight",
]
