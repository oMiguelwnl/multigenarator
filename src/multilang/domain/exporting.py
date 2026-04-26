"""Typed export contracts for the frozen Phase 5 card boundary."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import SupportedLanguage

EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "word",
    "Front of Card",
    "IPA",
    "Definitions",
    "Example Sentence",
    "Translation",
    "word_audio",
    "sentence_audio",
    "Image",
)


class ExportArtifactFormat(str, Enum):
    APKG = "apkg"
    CSV = "csv"
    TSV = "tsv"


class ExportArtifactStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportCardIdentity(BaseModel):
    language: SupportedLanguage
    source_type: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    item_key: str = Field(min_length=1)
    lemma_key: str = Field(min_length=1)
    sort_index: int = Field(ge=0)

    def stable_guid_input(self) -> str:
        return "|".join(
            (
                self.language.value,
                self.source_type,
                self.job_id,
                self.item_key,
                self.lemma_key,
                str(self.sort_index),
            )
        )


def build_export_note_guid(identity: ExportCardIdentity) -> str:
    return sha256(identity.stable_guid_input().encode("utf-8")).hexdigest()[:32]


class ExportCardRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, frozen=True)

    identity: ExportCardIdentity
    note_guid: str | None = None
    sort_index: int | None = Field(default=None, alias="SortIndex")
    word: str = Field(min_length=1, alias="word")
    front_of_card: str = Field(min_length=1, alias="Front of Card")
    ipa: str | None = Field(default=None, alias="IPA")
    definitions: str = Field(min_length=1, alias="Definitions")
    example_sentence: str = Field(min_length=1, alias="Example Sentence")
    translation: str = Field(min_length=1, alias="Translation")
    word_audio: str = Field(default="", alias="word_audio")
    sentence_audio: str = Field(default="", alias="sentence_audio")
    image: str = Field(default="", alias="Image")

    @model_validator(mode="after")
    def populate_stable_fields(self) -> "ExportCardRow":
        if self.sort_index is None:
            object.__setattr__(self, "sort_index", self.identity.sort_index)
        if self.note_guid is None:
            object.__setattr__(self, "note_guid", build_export_note_guid(self.identity))
        if self.image != "":
            raise ValueError("Image must default to an empty string for export rows")
        return self

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return EXPORT_CARD_FIELD_NAMES

    def ordered_field_mapping(self) -> dict[str, object]:
        values = self.model_dump(by_alias=True, exclude={"identity", "note_guid"})
        return {field_name: values[field_name] for field_name in EXPORT_CARD_FIELD_NAMES}


__all__ = [
    "EXPORT_CARD_FIELD_NAMES",
    "ExportArtifactFormat",
    "ExportArtifactStatus",
    "ExportCardIdentity",
    "ExportCardRow",
    "build_export_note_guid",
]
