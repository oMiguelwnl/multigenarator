"""Classical Latin MVP domain contracts isolated from modern-language modes."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

LATIN_LANGUAGE_CODE = "la"
LATIN_MVP_CARD_COUNT = 50
DEFAULT_LATIN_SOURCE_PACK_VERSION = "latin-mvp-50-v1"
LATIN_MVP_SOURCE_TYPE: Literal["latin-mvp"] = "latin-mvp"


class LatinVariant(str, Enum):
    """Supported Latin variant for the v2.0 MVP."""

    CLASSICAL = "classical"


class LatinDeckMetadata(BaseModel):
    """Metadata contract for the fixed Classical Latin MVP deck."""

    language_code: Literal["la"] = LATIN_LANGUAGE_CODE
    variant: LatinVariant = LatinVariant.CLASSICAL
    source_pack_version: str = Field(default=DEFAULT_LATIN_SOURCE_PACK_VERSION, min_length=1)
    card_count: int = LATIN_MVP_CARD_COUNT

    @field_validator("source_pack_version")
    @classmethod
    def source_pack_version_must_not_be_blank(cls, value: str) -> str:
        version = value.strip()
        if not version:
            raise ValueError("source_pack_version must not be blank")
        return version

    @model_validator(mode="after")
    def card_count_must_match_latin_mvp_scope(self) -> "LatinDeckMetadata":
        if self.card_count != LATIN_MVP_CARD_COUNT:
            raise ValueError("Latin MVP card_count must be exactly 50")
        return self


class LatinGenerationRequest(BaseModel):
    """Start request for the isolated Classical Latin MVP generation path."""

    language_code: Literal["la"] = LATIN_LANGUAGE_CODE
    variant: LatinVariant = LatinVariant.CLASSICAL
    source_type: Literal["latin-mvp"] = LATIN_MVP_SOURCE_TYPE
    source_pack_version: str = Field(default=DEFAULT_LATIN_SOURCE_PACK_VERSION, min_length=1)
    card_count: int = LATIN_MVP_CARD_COUNT

    @field_validator("source_pack_version")
    @classmethod
    def source_pack_version_must_not_be_blank(cls, value: str) -> str:
        version = value.strip()
        if not version:
            raise ValueError("source_pack_version must not be blank")
        return version

    @model_validator(mode="after")
    def card_count_must_match_latin_mvp_scope(self) -> "LatinGenerationRequest":
        if self.card_count != LATIN_MVP_CARD_COUNT:
            raise ValueError("Latin MVP card_count must be exactly 50")
        return self

    def metadata(self) -> LatinDeckMetadata:
        """Return the deck metadata encoded by this request."""

        return LatinDeckMetadata(
            language_code=self.language_code,
            variant=self.variant,
            source_pack_version=self.source_pack_version,
            card_count=self.card_count,
        )


__all__ = [
    "DEFAULT_LATIN_SOURCE_PACK_VERSION",
    "LATIN_LANGUAGE_CODE",
    "LATIN_MVP_CARD_COUNT",
    "LATIN_MVP_SOURCE_TYPE",
    "LatinDeckMetadata",
    "LatinGenerationRequest",
    "LatinVariant",
]
