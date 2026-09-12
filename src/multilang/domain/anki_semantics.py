"""Topology-neutral semantic cards and explicit external-client evidence gates."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.audio import AudioAssetKind
from multilang.domain.audio_version import AudioVersion
from multilang.domain.content import ContentVersion, canonical_content_hash
from multilang.domain.jobs import SupportedLanguage


class SemanticCard(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    parent_lexical_identity_id: str = Field(min_length=1, max_length=255)
    language: SupportedLanguage
    parent_lemma: str = Field(min_length=1, max_length=255)
    sense_id: str = Field(min_length=1, max_length=255)
    role: Literal["headword", "important_form", "reverse", "listening", "cloze"]
    display_text: str = Field(min_length=1, max_length=1000)
    context_cue: str = Field(min_length=1, max_length=4000)
    surface_form_id: str | None = None
    morphological_analysis_id: str | None = None
    inventory: Literal["core", "expansion", "custom", "highlight", "foundation"]
    rank: int | None = Field(default=None, ge=1)
    deck_edition_id: str = Field(min_length=1, max_length=255)
    namespace: str = "core"
    prerequisite_card_id: str | None = None
    content: ContentVersion | None = None
    word_audio: AudioVersion | None = None
    sentence_audio: AudioVersion | None = None
    rendering_policy_version: str = "plain-text-1"

    @model_validator(mode="after")
    def validate_card(self) -> SemanticCard:
        if self.namespace != "core" and (
            not self.namespace.startswith("user:") or len(self.namespace) <= 5
        ):
            raise ValueError("semantic cards require core or an explicit user namespace")
        if self.inventory == "core" and (
            self.rank is None or self.rank > 3000 or self.namespace != "core"
        ):
            raise ValueError("Core requires canonical rank 1..3000 and shared namespace")
        if self.inventory in {"custom", "highlight"} and not self.namespace.startswith("user:"):
            raise ValueError("personal inventories require a private namespace")
        if self.role == "important_form" and (
            not self.surface_form_id
            or not self.morphological_analysis_id
            or not self.prerequisite_card_id
        ):
            raise ValueError(
                "important form requires parent prerequisite, surface and analysis IDs"
            )
        if (
            self.role == "important_form"
            and self.context_cue.strip().casefold() == self.display_text.strip().casefold()
        ):
            raise ValueError("important form requires a distinguishing context cue")
        if self.role == "headword" and (self.surface_form_id or self.morphological_analysis_id):
            raise ValueError("headword cannot masquerade as a form")
        if self.content is not None:
            req = self.content.request
            if (
                req.card_id != self.card_id
                or req.lexical_identity_id != self.parent_lexical_identity_id
                or req.sense_id != self.sense_id
                or req.display_text != self.display_text
                or req.morphological_analysis_id != self.morphological_analysis_id
                or req.deck_edition_id != self.deck_edition_id
                or req.namespace != self.namespace
                or req.language != self.language.value
                or req.lemma != self.parent_lemma
                or req.context_cue != self.context_cue
                or req.render_policy_version != self.rendering_policy_version
            ):
                raise ValueError("content does not belong to semantic card/edition/namespace")
        if self.word_audio is not None:
            signature = self.word_audio.signature
            if (
                signature.display_text != self.display_text
                or signature.sense_id != self.sense_id
                or signature.morphological_analysis_id != self.morphological_analysis_id
                or signature.language != self.language.value
                or signature.asset_kind != AudioAssetKind.WORD
                or signature.context != self.context_cue
                or self.word_audio.namespace != self.namespace
            ):
                raise ValueError("word audio does not match exact form pronunciation")
        if self.sentence_audio is not None and (
            self.content is None
            or self.sentence_audio.signature.display_text != self.content.content.example_sentence
            or self.sentence_audio.signature.language != self.language.value
            or self.sentence_audio.signature.asset_kind != AudioAssetKind.SENTENCE
            or self.sentence_audio.signature.sense_id != self.sense_id
            or self.sentence_audio.signature.context != self.context_cue
            or self.sentence_audio.signature.morphological_analysis_id
            != self.morphological_analysis_id
            or self.sentence_audio.namespace != self.namespace
        ):
            raise ValueError("sentence audio does not match exact approved sentence")
        if self.content is not None:
            for audio in (self.word_audio, self.sentence_audio):
                if (
                    audio
                    and audio.signature.language_profile_version
                    != self.content.request.language_profile_version
                ):
                    raise ValueError("audio and content language profile versions differ")
        return self

    @property
    def card_id(self) -> str:
        return "card:1:" + canonical_content_hash(
            {
                "identity": self.parent_lexical_identity_id,
                "role": self.role,
                "analysis": self.morphological_analysis_id,
                "form": self.surface_form_id if self.morphological_analysis_id else None,
                "namespace": self.namespace,
            }
        )

    @property
    def note_guid(self) -> str:
        """Separate-note prototype GUID; family prototype uses its family GUID."""
        return canonical_content_hash({"semantic_card": self.card_id})[:32]

    @property
    def level(self) -> int | None:
        return (self.rank - 1) // 1000 + 1 if self.inventory == "core" and self.rank else None

    @property
    def destination(self) -> str:
        labels = {
            "expansion": "Expansion",
            "custom": "Custom",
            "highlight": "Highlight",
            "foundation": "Grammar",
        }
        if self.inventory == "core":
            return f"{self.language.value}::Frequency::Level {self.level}"
        return f"{self.language.value}::{labels[self.inventory]}"


ANKI_CLIENTS = (
    "desktop_current",
    "desktop_previous",
    "ankidroid_current",
    "ankimobile_current",
)
ANKI_SCENARIOS = (
    "identity",
    "import",
    "reimport",
    "update",
    "alias",
    "scheduling",
    "prerequisite",
    "nonconcurrent_exposure",
    "dynamic_add",
    "dynamic_remove",
    "collision",
    "round_trip",
)


class TopologyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model: Literal["A", "B"]
    client: Literal[
        "desktop_current", "desktop_previous", "ankidroid_current", "ankimobile_current"
    ]
    client_version: str = Field(min_length=1)
    scenario: str
    positive_passed: bool
    negative_passed: bool
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class TopologyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    selected_model: Literal["A", "B"]
    topology_version: Literal["1"]
    evidence: tuple[TopologyEvidence, ...]
    signer: str = Field(min_length=1)
    decision_receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    nonconcurrent_mechanism: str = Field(min_length=1)

    def require_verified(self, verifier: Callable[[TopologyDecision], bool] | None) -> None:
        expected = {
            (model, client, scenario)
            for model in ("A", "B")
            for client in ANKI_CLIENTS
            for scenario in ANKI_SCENARIOS
        }
        actual = {(row.model, row.client, row.scenario) for row in self.evidence}
        if (
            actual != expected
            or len(actual) != len(self.evidence)
            or not all(row.positive_passed and row.negative_passed for row in self.evidence)
            or len({row.fixture_sha256 for row in self.evidence}) != 1
        ):
            raise ValueError(
                "ANKI-01 requires complete positive/negative A/B evidence in all four clients"
            )
        if self.selected_model == "B" and "sibling" in self.nonconcurrent_mechanism.casefold():
            raise ValueError("separate notes cannot claim native sibling burying")
        if verifier is None or not verifier(self):
            raise ValueError("ANKI-01 requires an externally verified signed client decision")


class SemanticManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    card_id: str
    note_guid: str
    template_ordinal: int
    model_id: int
    deck_id: int
    destination: str
    parent_lexical_identity_id: str
    role: str
    surface_form_id: str | None
    morphological_analysis_id: str | None
    sense_id: str
    context_cue: str
    prerequisite_card_id: str | None
    inventory: str
    deck_edition_id: str
    content_version_id: str | None = None
    word_audio_version_id: str | None = None
    sentence_audio_version_id: str | None = None


class SemanticExportResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    output_path: str
    model: Literal["A", "B"]
    prototype: bool
    native_sibling_structure: bool
    client_acceptance_proven: bool = False
    field_contract_compatible: bool = False
    manifest: tuple[SemanticManifestEntry, ...]
    artifact_sha256: str
    composition_sha256: str
