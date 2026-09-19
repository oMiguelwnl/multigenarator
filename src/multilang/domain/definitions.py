"""Bounded source meanings and advisory definition/example assessments."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DefinitionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class SourceDefinitionSense(DefinitionModel):
    sense_id: str = Field(min_length=1, max_length=255)
    meaning: str = Field(min_length=1, max_length=2000)
    language: str = Field(min_length=2, max_length=16)

    @field_validator("sense_id", "meaning", "language")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source meaning fields must not be blank")
        return value


class DefinitionEvidence(SourceDefinitionSense):
    lemma: str = Field(min_length=1, max_length=512)
    source_language: str = Field(min_length=2, max_length=16)
    part_of_speech: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1, max_length=256)
    source_version: str = Field(min_length=1, max_length=128)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lexical_record_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DefinitionConsistencyRequest(DefinitionModel):
    lemma: str = Field(min_length=1, max_length=512)
    display_form: str = Field(min_length=1, max_length=512)
    source_language: str = Field(min_length=2, max_length=16)
    definition_language: str = Field(min_length=2, max_length=16)
    definition: str = Field(min_length=1, max_length=4096)
    sentence: str = Field(min_length=1, max_length=4000)
    source_meaning: str | None = Field(
        default=None, max_length=2000, exclude_if=lambda value: value is None
    )
    source_meaning_language: str | None = Field(
        default=None, min_length=2, max_length=16, exclude_if=lambda value: value is None
    )


class DefinitionConsistencyVerdict(DefinitionModel):
    decision: Literal["consistent", "mismatch", "uncertain"]
