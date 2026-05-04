"""Typed export contracts for the frozen Phase 5 card boundary."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.source_profiles import get_source_profile

FREQUENCY_EXPORT_CARD_FIELD_NAMES = (
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
MANUAL_EXPORT_CARD_FIELD_NAMES = FREQUENCY_EXPORT_CARD_FIELD_NAMES
EXPORT_CARD_FIELD_NAMES = FREQUENCY_EXPORT_CARD_FIELD_NAMES
HIGHLIGHT_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "Word",
    "IPA",
    "word_audio",
    "Example Sentence",
    "sentence_audio",
    "Definition",
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
    translation: str = Field(default="", alias="Translation")
    word_audio: str = Field(default="", alias="word_audio")
    sentence_audio: str = Field(default="", alias="sentence_audio")
    image: str = Field(default="", alias="Image")

    @model_validator(mode="after")
    def populate_stable_fields(self) -> "ExportCardRow":
        if self.sort_index is None:
            object.__setattr__(self, "sort_index", self.identity.sort_index)
        elif self.sort_index != self.identity.sort_index:
            raise ValueError("SortIndex must match identity.sort_index")
        if self.note_guid is None:
            object.__setattr__(self, "note_guid", build_export_note_guid(self.identity))
        if self.image != "":
            raise ValueError("Image must default to an empty string for export rows")
        return self

    @classmethod
    def field_names(cls, *, source_type: str = "frequency") -> tuple[str, ...]:
        return export_field_names_for_source_type(source_type)

    def ordered_field_mapping(self, *, field_names: tuple[str, ...] | None = None) -> dict[str, object]:
        resolved_field_names = field_names or export_field_names_for_source_type(self.identity.source_type)
        values = self.model_dump(by_alias=True, exclude={"identity", "note_guid"})
        values["Word"] = values["word"]
        values["Definition"] = values["Definitions"]
        return {field_name: values[field_name] for field_name in resolved_field_names}


def export_field_names_for_source_type(source_type: str) -> tuple[str, ...]:
    profile = get_source_profile(source_type)
    if not profile.exports_translation_field:
        return HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    if profile.source_type == "word-list":
        return MANUAL_EXPORT_CARD_FIELD_NAMES
    return FREQUENCY_EXPORT_CARD_FIELD_NAMES


def export_field_names_for_rows(rows: list[ExportCardRow]) -> tuple[str, ...]:
    source_types = {row.identity.source_type for row in rows}
    if len(source_types) > 1:
        raise ValueError("cannot resolve export field names for mixed source types")
    source_type = next(iter(source_types), "frequency")
    return export_field_names_for_source_type(source_type)


class ExportDeckArtifact(BaseModel):
    job_id: str = Field(min_length=1)
    export_format: ExportArtifactFormat
    deck_name: str = Field(min_length=1)
    output_path: str = Field(min_length=1)
    card_count: int = Field(ge=0)
    status: ExportArtifactStatus


__all__ = [
    "EXPORT_CARD_FIELD_NAMES",
    "FREQUENCY_EXPORT_CARD_FIELD_NAMES",
    "HIGHLIGHT_EXPORT_CARD_FIELD_NAMES",
    "MANUAL_EXPORT_CARD_FIELD_NAMES",
    "ExportArtifactFormat",
    "ExportArtifactStatus",
    "ExportCardIdentity",
    "ExportCardRow",
    "ExportDeckArtifact",
    "build_export_note_guid",
    "export_field_names_for_rows",
    "export_field_names_for_source_type",
]
