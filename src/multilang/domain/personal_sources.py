"""Contracts for ordered personal-source inputs and decisions."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.korean import KoreanAnalyzerFingerprint, KoreanLexicalIdentity

PERSONAL_SOURCE_FORM_MAX_LENGTH = 256
PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH = 128
_LOWERCASE_HEX = frozenset("0123456789abcdef")

KoreanPersonalSourceReviewReason = Literal[
    "ambiguous_analysis",
    "analysis_unavailable",
    "duplicate_of_existing",
    "fingerprint_drift",
    "invalid_text",
    "malformed_identity",
    "non_consensus",
    "oov",
    "resolver_error",
]
PersonalSourceAdaptiveReason = Literal[
    "excessive_prerequisites",
    "unresolved_identity",
    "within_threshold",
]
PersonalSourceDecisionKind = Literal["bridge", "defer", "needs_review"]
PersonalSourceDecisionReason = Literal[
    "dependency_drift",
    "invalid_bridge",
    "no_decision_required",
    "operator_bridge",
    "operator_defer",
    "policy_drift",
    "unresolved_identity",
]
PersonalSourcePreparationStatus = Literal[
    "bridge_reference",
    "deferred",
    "duplicate",
    "needs_review",
    "ready",
]


class _FrozenPersonalSourceContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class PersonalSourceRow(_FrozenPersonalSourceContract):
    """One nonblank submitted row before lexical resolution."""

    input_position: int = Field(ge=1)
    line_number: int = Field(ge=1)
    submitted_form: str = Field(min_length=1, max_length=PERSONAL_SOURCE_FORM_MAX_LENGTH)
    display_form: str = Field(min_length=1, max_length=PERSONAL_SOURCE_FORM_MAX_LENGTH)
    normalized_duplicate_key: str = Field(
        min_length=1,
        max_length=PERSONAL_SOURCE_FORM_MAX_LENGTH,
    )
    duplicate_of_position: int | None = Field(default=None, ge=1)

    @field_validator("submitted_form", "display_form", "normalized_duplicate_key")
    @classmethod
    def text_must_be_bounded_nonblank(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "personal source text")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be bounded nonblank text")
        return value

    @model_validator(mode="after")
    def duplicate_must_reference_earlier_position(self) -> Self:
        if (
            self.duplicate_of_position is not None
            and self.duplicate_of_position >= self.input_position
        ):
            raise ValueError("duplicate_of must reference an earlier input position")
        return self

    @property
    def disposition(self) -> Literal["card_bearing", "duplicate"]:
        if self.duplicate_of_position is None:
            return "card_bearing"
        return "duplicate"

    @property
    def is_card_bearing(self) -> bool:
        return self.duplicate_of_position is None

    @property
    def stable_item_key(self) -> str:
        return self.normalized_duplicate_key


def _safe_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        normalized != value
        or not normalized
        or len(normalized) > PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH
        or not normalized[0].isalnum()
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _concept_identifiers(
    values: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(_safe_identifier(value, field_name=field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must contain unique identifiers")
    return normalized


class KoreanPersonalSourceIdentityEvidence(_FrozenPersonalSourceContract):
    """Exact source and analyzer evidence for one resolved Korean custom row."""

    language: Literal["ko"]
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    source_id: str = Field(min_length=1, max_length=PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH)
    source_version: str = Field(min_length=1, max_length=PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH)
    source_entry_hash: str = Field(min_length=64, max_length=64)
    source_selector_hash: str = Field(min_length=64, max_length=64)

    @field_validator("source_id", "source_version")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("source_entry_hash", "source_selector_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanPersonalSourceIdentitySelection(_FrozenPersonalSourceContract):
    """Injected resolver/source-selector success payload for Korean rows."""

    language: Literal["ko"]
    lexical_identity: KoreanLexicalIdentity
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    top_two_consensus: bool
    source_consensus: bool
    source_id: str = Field(min_length=1, max_length=PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH)
    source_version: str = Field(min_length=1, max_length=PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH)
    source_entry_hash: str = Field(min_length=64, max_length=64)
    source_selector_hash: str = Field(min_length=64, max_length=64)

    @field_validator("source_id", "source_version")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("source_entry_hash", "source_selector_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    def identity_evidence(self) -> KoreanPersonalSourceIdentityEvidence:
        return KoreanPersonalSourceIdentityEvidence(
            language=self.language,
            analyzer_fingerprint=self.analyzer_fingerprint,
            source_id=self.source_id,
            source_version=self.source_version,
            source_entry_hash=self.source_entry_hash,
            source_selector_hash=self.source_selector_hash,
        )


class KoreanPersonalSourceResolutionFailure(_FrozenPersonalSourceContract):
    """Content-free failure returned by an injected Korean resolver."""

    language: Literal["ko"] = "ko"
    status: Literal["ambiguous", "invalid", "oov", "unavailable"]
    reason_code: KoreanPersonalSourceReviewReason


class KoreanPersonalSourceResolutionOutcome(_FrozenPersonalSourceContract):
    """Visible resolution outcome for one ordered Korean personal-source row."""

    row: PersonalSourceRow
    resolution_status: Literal["resolved", "needs_review", "duplicate"]
    lexical_identity: KoreanLexicalIdentity | None = None
    identity_evidence: KoreanPersonalSourceIdentityEvidence | None = None
    review_reason_code: KoreanPersonalSourceReviewReason | None = None

    @model_validator(mode="after")
    def status_must_match_payload(self) -> Self:
        if self.resolution_status == "resolved":
            if self.lexical_identity is None or self.identity_evidence is None:
                raise ValueError("resolved outcome requires identity and evidence")
            if self.review_reason_code is not None:
                raise ValueError("resolved outcome cannot carry a review reason")
        else:
            if self.lexical_identity is not None or self.identity_evidence is not None:
                raise ValueError("unresolved outcome cannot carry resolved identity")
            if self.review_reason_code is None:
                raise ValueError("unresolved outcome requires a review reason")
        return self


class PersonalSourceAdaptiveEvidence(_FrozenPersonalSourceContract):
    """Versioned adaptive prerequisite evidence for a personal-source row."""

    policy: Literal["adaptive"] = "adaptive"
    observed_concept_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    prerequisite_concept_ids: tuple[str, ...] = Field(default=(), max_length=128)
    known_concept_ids: tuple[str, ...] = Field(default=(), max_length=128)
    unknown_prerequisite_concept_ids: tuple[str, ...] = Field(default=(), max_length=128)
    novelty_count: int = Field(ge=0, le=128)
    threshold: int = Field(ge=0, le=128)
    policy_version: str = Field(min_length=1, max_length=PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH)
    policy_hash: str = Field(min_length=64, max_length=64)
    reason_codes: tuple[PersonalSourceAdaptiveReason, ...] = Field(min_length=1, max_length=3)

    @field_validator(
        "observed_concept_ids",
        "prerequisite_concept_ids",
        "known_concept_ids",
        "unknown_prerequisite_concept_ids",
    )
    @classmethod
    def concepts_must_be_safe(cls, value: tuple[str, ...], info: object) -> tuple[str, ...]:
        return _concept_identifiers(
            value,
            field_name=getattr(info, "field_name", "concept ids"),
        )

    @field_validator("policy_version")
    @classmethod
    def policy_version_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="policy version")

    @field_validator("policy_hash")
    @classmethod
    def policy_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_identifier(value, field_name="policy hash")

    @model_validator(mode="after")
    def novelty_must_match_prerequisite_delta(self) -> Self:
        observed = set(self.observed_concept_ids)
        prerequisites = set(self.prerequisite_concept_ids)
        known = set(self.known_concept_ids)
        if not prerequisites <= observed:
            raise ValueError("prerequisite concepts must be observed")
        expected_unknown = tuple(
            concept_id
            for concept_id in self.prerequisite_concept_ids
            if concept_id not in known
        )
        if expected_unknown != self.unknown_prerequisite_concept_ids:
            raise ValueError("unknown prerequisites must match known evidence")
        if self.novelty_count != len(self.unknown_prerequisite_concept_ids):
            raise ValueError("novelty count must match unknown prerequisites")
        return self

    @property
    def requires_decision(self) -> bool:
        return "excessive_prerequisites" in self.reason_codes


class PersonalSourcePrerequisiteProposal(_FrozenPersonalSourceContract):
    """Stable proposal produced by adaptive prerequisite assessment."""

    proposal_id: str = Field(min_length=64, max_length=64)
    input_position: int = Field(ge=1)
    row_item_key: str = Field(min_length=1, max_length=PERSONAL_SOURCE_FORM_MAX_LENGTH)
    status: Literal["ready", "requires_decision", "needs_review"]
    evidence: PersonalSourceAdaptiveEvidence
    available_decisions: tuple[PersonalSourceDecisionKind, ...] = Field(max_length=3)

    @field_validator("proposal_id")
    @classmethod
    def proposal_id_must_be_sha256(cls, value: str) -> str:
        return _sha256_identifier(value, field_name="proposal id")

    @field_validator("available_decisions")
    @classmethod
    def decisions_must_be_unique(
        cls,
        value: tuple[PersonalSourceDecisionKind, ...],
    ) -> tuple[PersonalSourceDecisionKind, ...]:
        if len(value) != len(set(value)):
            raise ValueError("available decisions must be unique")
        return value

    @model_validator(mode="after")
    def status_must_match_decisions(self) -> Self:
        if self.status == "requires_decision" and self.available_decisions != (
            "bridge",
            "defer",
        ):
            raise ValueError("excessive prerequisites require bridge/defer choices")
        if self.status == "needs_review" and self.available_decisions != ("needs_review",):
            raise ValueError("review proposals expose only needs_review")
        if self.status == "ready" and self.available_decisions:
            raise ValueError("ready proposals do not require a decision")
        return self


class PersonalSourceDecisionCommand(_FrozenPersonalSourceContract):
    """Compare-and-set command for one explicit prerequisite decision."""

    input_position: int = Field(ge=1)
    row_item_key: str = Field(min_length=1, max_length=PERSONAL_SOURCE_FORM_MAX_LENGTH)
    expected_proposal_id: str = Field(min_length=64, max_length=64)
    expected_policy_hash: str = Field(min_length=64, max_length=64)
    expected_prerequisite_concept_ids: tuple[str, ...] = Field(default=(), max_length=128)
    decision: PersonalSourceDecisionKind
    reviewed_prerequisite_ids: tuple[str, ...] = Field(default=(), max_length=128)
    actor_id: str = Field(min_length=1, max_length=PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH)
    reason_code: Literal["operator_bridge", "operator_defer"]

    @field_validator("expected_proposal_id", "expected_policy_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("expected_prerequisite_concept_ids", "reviewed_prerequisite_ids")
    @classmethod
    def concept_ids_must_be_safe(cls, value: tuple[str, ...], info: object) -> tuple[str, ...]:
        return _concept_identifiers(
            value,
            field_name=getattr(info, "field_name", "concept ids"),
        )

    @field_validator("actor_id")
    @classmethod
    def actor_id_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="actor id")

    @model_validator(mode="after")
    def command_must_match_decision_shape(self) -> Self:
        if self.decision == "bridge":
            if not self.reviewed_prerequisite_ids:
                raise ValueError("bridge decision requires reviewed prerequisite ids")
            if self.reason_code != "operator_bridge":
                raise ValueError("bridge decision requires bridge reason")
        if self.decision == "defer":
            if self.reviewed_prerequisite_ids:
                raise ValueError("defer decision cannot carry bridge references")
            if self.reason_code != "operator_defer":
                raise ValueError("defer decision requires defer reason")
        if self.decision == "needs_review":
            raise ValueError("needs_review is derived from drift or unresolved evidence")
        return self


class PersonalSourcePrerequisiteDecision(_FrozenPersonalSourceContract):
    """Persistable bridge/defer/needs_review decision state."""

    decision_id: str = Field(min_length=64, max_length=64)
    input_position: int = Field(ge=1)
    row_item_key: str = Field(min_length=1, max_length=PERSONAL_SOURCE_FORM_MAX_LENGTH)
    proposal_id: str = Field(min_length=64, max_length=64)
    policy_hash: str = Field(min_length=64, max_length=64)
    prerequisite_concept_ids: tuple[str, ...] = Field(default=(), max_length=128)
    decision: PersonalSourceDecisionKind
    reviewed_prerequisite_ids: tuple[str, ...] = Field(default=(), max_length=128)
    reason_code: PersonalSourceDecisionReason
    blocks_current_preparation: bool

    @field_validator("decision_id", "proposal_id", "policy_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("prerequisite_concept_ids", "reviewed_prerequisite_ids")
    @classmethod
    def concept_ids_must_be_safe(cls, value: tuple[str, ...], info: object) -> tuple[str, ...]:
        return _concept_identifiers(
            value,
            field_name=getattr(info, "field_name", "concept ids"),
        )

    @model_validator(mode="after")
    def decision_must_match_effect(self) -> Self:
        if self.decision == "bridge":
            if not self.reviewed_prerequisite_ids:
                raise ValueError("bridge decision requires reviewed prerequisite ids")
            if not set(self.reviewed_prerequisite_ids) <= set(
                self.prerequisite_concept_ids
            ):
                raise ValueError("bridge references must be prerequisites")
            if self.blocks_current_preparation:
                raise ValueError("bridge references do not block current preparation")
        elif self.decision == "defer":
            if self.reviewed_prerequisite_ids:
                raise ValueError("defer decision cannot carry bridge references")
            if not self.blocks_current_preparation:
                raise ValueError("defer must block current preparation")
        elif self.decision == "needs_review":
            if self.reviewed_prerequisite_ids:
                raise ValueError("needs_review cannot carry bridge references")
            if not self.blocks_current_preparation:
                raise ValueError("needs_review must block current preparation")
        return self


class PersonalSourcePreparedItem(_FrozenPersonalSourceContract):
    """Projected preparation order entry without mutating source rows."""

    kind: Literal["bridge_reference", "user_row"]
    input_position: int = Field(ge=1)
    row_item_key: str = Field(min_length=1, max_length=PERSONAL_SOURCE_FORM_MAX_LENGTH)
    preparation_status: PersonalSourcePreparationStatus
    bridge_reference_id: str | None = Field(default=None, max_length=128)

    @field_validator("bridge_reference_id")
    @classmethod
    def bridge_reference_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _safe_identifier(value, field_name="bridge reference id")

    @model_validator(mode="after")
    def item_shape_must_match_kind(self) -> Self:
        if self.kind == "bridge_reference":
            if self.bridge_reference_id is None:
                raise ValueError("bridge reference item requires a reference id")
            if self.preparation_status != "bridge_reference":
                raise ValueError("bridge reference item requires bridge status")
        else:
            if self.bridge_reference_id is not None:
                raise ValueError("user row item cannot carry bridge reference id")
            if self.preparation_status == "bridge_reference":
                raise ValueError("user row item cannot use bridge status")
        return self


__all__ = [
    "KoreanPersonalSourceIdentityEvidence",
    "KoreanPersonalSourceIdentitySelection",
    "KoreanPersonalSourceResolutionFailure",
    "KoreanPersonalSourceResolutionOutcome",
    "KoreanPersonalSourceReviewReason",
    "PERSONAL_SOURCE_FORM_MAX_LENGTH",
    "PERSONAL_SOURCE_IDENTIFIER_MAX_LENGTH",
    "PersonalSourceAdaptiveEvidence",
    "PersonalSourceAdaptiveReason",
    "PersonalSourceDecisionCommand",
    "PersonalSourceDecisionKind",
    "PersonalSourceDecisionReason",
    "PersonalSourcePreparedItem",
    "PersonalSourcePreparationStatus",
    "PersonalSourcePrerequisiteDecision",
    "PersonalSourcePrerequisiteProposal",
    "PersonalSourceRow",
]
