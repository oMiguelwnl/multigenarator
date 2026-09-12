"""Canonical edition bindings pin content and exact pronunciation versions."""

from typing import Literal

from pydantic import Field, model_validator

from multilang.domain.events import canonical_hash
from multilang.domain.language_profiles import NativeContract
from multilang.domain.lexical_identity import ImportantFormPolicy


class CardVersionBinding(NativeContract):
    card_id: str = Field(min_length=1, max_length=128)
    content_version_id: str = Field(min_length=1, max_length=128)
    word_audio_version_id: str = Field(min_length=1, max_length=128)
    sentence_audio_version_id: str = Field(min_length=1, max_length=128)


class DeckEdition(NativeContract):
    edition_id: str = Field(min_length=1, max_length=128)
    dataset_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    bindings: tuple[CardVersionBinding, ...] = Field(max_length=100000)
    important_form_policy: ImportantFormPolicy | None = None
    optional_roles: tuple[Literal["reverse", "listening", "cloze"], ...] = ()
    render_policy_version: Literal["plain-text-1"] = "plain-text-1"
    approval_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def unique_bindings(self):
        if len({binding.card_id for binding in self.bindings}) != len(self.bindings):
            raise ValueError("duplicate card binding in edition")
        if len(set(self.optional_roles)) != len(self.optional_roles):
            raise ValueError("duplicate optional role")
        return self

    @property
    def bundle_sha256(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))
