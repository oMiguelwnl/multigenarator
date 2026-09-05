"""Immutable Korean grammar bundle and readiness contracts."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Final, Literal, Self
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.korean import (
    KOREAN_LANGUAGE_CODE,
    KoreanConcept,
    KoreanCurriculumEvidence,
    canonicalize_korean,
)


KOREAN_GRAMMAR_REVIEW_POLICY_ID: Final = "multilang-ai-linguistic-review-v1"
KOREAN_GRAMMAR_SOURCE_KIND: Final = "active-approved-snapshot"
KOREAN_GRAMMAR_READY_STATES: Final = ("blocked", "needs_review", "learner_ready")
KOREAN_GRAMMAR_CATEGORIES: Final = tuple(f"G{index}" for index in range(14))
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_MAX_IDENTIFIER_LENGTH: Final = 128
_MAX_TEXT_LENGTH: Final = 2_048
_MAX_IDS: Final = 256
_UNSAFE_TEXT_MARKERS: Final = (
    "<",
    ">",
    "\x00",
    "[sound:",
    "[anki:play:",
    "javascript:",
    "data:text/html",
    "file://",
)


class _FrozenGrammarModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


def korean_grammar_canonical_json_sha256(value: object) -> str:
    """Hash deterministic UTF-8 canonical JSON for grammar evidence."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", by_alias=True)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def grammar_content_hash(value: BaseModel) -> str:
    payload = value.model_dump(mode="json", by_alias=True)
    payload.pop("content_hash", None)
    return korean_grammar_canonical_json_sha256(payload)


def _sha256_text(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _MAX_IDENTIFIER_LENGTH
        or not normalized[0].isascii()
        or not normalized[0].isalnum()
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _identifiers(values: tuple[str, ...], *, field_name: str) -> tuple[str, ...]:
    normalized = tuple(_identifier(value, field_name=field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must contain unique identifiers")
    return normalized


def _safe_text(value: str, *, field_name: str, require_hangul: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be bounded safe text")
    normalized = value.strip()
    folded = normalized.casefold()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _MAX_TEXT_LENGTH
        or unicodedata.normalize("NFC", normalized) != normalized
        or any(marker in folded for marker in _UNSAFE_TEXT_MARKERS)
    ):
        raise ValueError(f"{field_name} must be bounded safe text")
    if require_hangul:
        canonicalize_korean(normalized)
        if not any(
            0x1100 <= ord(character) <= 0x11FF
            or 0xAC00 <= ord(character) <= 0xD7A3
            for character in normalized
        ):
            raise ValueError(f"{field_name} must contain Korean text")
    return normalized


class Phase31GrammarRootBinding(_FrozenGrammarModel):
    """Exact active Phase 31 root imported as grammar known-state authority."""

    source_kind: Literal["active-approved-snapshot"] = KOREAN_GRAMMAR_SOURCE_KIND
    bundle_sha256: str = Field(min_length=64, max_length=64)
    receipt_sha256: str = Field(min_length=64, max_length=64)
    snapshot_manifest_sha256: str = Field(min_length=64, max_length=64)
    snapshot_root_sha256: str = Field(min_length=64, max_length=64)
    concept_registry_member_sha256: str = Field(min_length=64, max_length=64)
    imported_concept_ids: tuple[str, ...] = Field(min_length=1, max_length=_MAX_IDS)
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "bundle_sha256",
        "receipt_sha256",
        "snapshot_manifest_sha256",
        "snapshot_root_sha256",
        "concept_registry_member_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("imported_concept_ids")
    @classmethod
    def imported_ids_must_be_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _identifiers(value, field_name="imported concept ids")


class KoreanGrammarSourceBinding(_FrozenGrammarModel):
    """Source, license, and lexical authority for one grammar-owned record."""

    source_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    source_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    license_decision: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    entry_sha256: str = Field(min_length=64, max_length=64)
    bundle_sha256: str = Field(min_length=64, max_length=64)
    source_backed: bool
    synthetic: bool
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("source_id", "source_version", "license_decision")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("entry_sha256", "bundle_sha256", "content_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))


class KoreanGrammarAIEvidenceBinding(_FrozenGrammarModel):
    """AI linguistic review evidence under the global review policy."""

    policy_id: Literal["multilang-ai-linguistic-review-v1"]
    policy_sha256: str = Field(min_length=64, max_length=64)
    actor_type: Literal["ai_model"]
    is_human: Literal[False]
    provider: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    model_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    route_sha256: str = Field(min_length=64, max_length=64)
    prompt_sha256: str = Field(min_length=64, max_length=64)
    output_schema_sha256: str = Field(min_length=64, max_length=64)
    source_sha256: str = Field(min_length=64, max_length=64)
    candidate_sha256: str = Field(min_length=64, max_length=64)
    analyzer_sha256: str = Field(min_length=64, max_length=64)
    curriculum_sha256: str = Field(min_length=64, max_length=64)
    media_sha256: str = Field(min_length=64, max_length=64)
    deterministic_validator_ids: tuple[str, ...] = Field(min_length=1, max_length=32)
    deterministic_validator_result: Literal["passed", "failed", "stale"]
    fresh_context_pass_ids: tuple[str, ...] = Field(min_length=1, max_length=3)
    required_pass_count: int = Field(ge=2, le=3)
    consensus_status: Literal[
        "ai_review_passed",
        "ai_review_failed",
        "blocked_uncertainty",
        "blocked_disagreement",
        "stale",
    ]
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "policy_sha256",
        "route_sha256",
        "prompt_sha256",
        "output_schema_sha256",
        "source_sha256",
        "candidate_sha256",
        "analyzer_sha256",
        "curriculum_sha256",
        "media_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("provider", "model_id")
    @classmethod
    def provider_fields_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("deterministic_validator_ids", "fresh_context_pass_ids")
    @classmethod
    def ids_must_be_unique(cls, value: tuple[str, ...], info: object) -> tuple[str, ...]:
        return _identifiers(value, field_name=getattr(info, "field_name", "ids"))

    @model_validator(mode="after")
    def review_evidence_must_match_policy(self) -> Self:
        if len(self.fresh_context_pass_ids) != self.required_pass_count:
            raise ValueError("AI review pass count must match required pass count")
        if (
            self.consensus_status == "ai_review_passed"
            and self.deterministic_validator_result != "passed"
        ):
            raise ValueError("AI review cannot pass a deterministic validator failure")
        return self


class KoreanGrammarMediaBinding(_FrozenGrammarModel):
    """Exact text, request, artifact, profile, and acoustic evidence."""

    text_sha256: str = Field(min_length=64, max_length=64)
    request_sha256: str = Field(min_length=64, max_length=64)
    artifact_sha256: str = Field(min_length=64, max_length=64)
    voice_profile_sha256: str = Field(min_length=64, max_length=64)
    integrity_status: Literal["passed", "failed", "stale", "missing"]
    acoustic_review_status: Literal[
        "ai_acoustic_review_passed",
        "automated_integrity_passed",
        "failed",
        "stale",
        "missing",
    ]
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "text_sha256",
        "request_sha256",
        "artifact_sha256",
        "voice_profile_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))


class KoreanGrammarBootstrapEntry(_FrozenGrammarModel):
    """One ordered learner-visible lexical prerequisite owned by grammar."""

    entry_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    sequence: int = Field(ge=1, le=10_000)
    target_concept_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    lexical_identity_sha256: str = Field(min_length=64, max_length=64)
    submitted_form: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    canonical_nfc: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    source_binding: KoreanGrammarSourceBinding
    observed_concept_ids: tuple[str, ...] = Field(min_length=1, max_length=_MAX_IDS)
    prerequisite_concept_ids: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)
    learner_visible: Literal[True]
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("entry_id", "target_concept_id")
    @classmethod
    def ids_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("lexical_identity_sha256", "content_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("observed_concept_ids", "prerequisite_concept_ids")
    @classmethod
    def concept_ids_must_be_unique(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        return _identifiers(value, field_name=getattr(info, "field_name", "concept ids"))

    @field_validator("submitted_form", "canonical_nfc")
    @classmethod
    def korean_values_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_text(
            value,
            field_name=getattr(info, "field_name", "Korean text"),
            require_hangul=True,
        )

    @model_validator(mode="after")
    def bootstrap_contract_must_be_visible_and_source_backed(self) -> Self:
        if not self.target_concept_id.startswith("lexicon:"):
            raise ValueError("bootstrap target must be a lexicon concept")
        if self.target_concept_id not in self.observed_concept_ids:
            raise ValueError("bootstrap target concept must be observed")
        if self.target_concept_id in self.prerequisite_concept_ids:
            raise ValueError("bootstrap target cannot be pre-known")
        if canonicalize_korean(self.submitted_form) != self.canonical_nfc:
            raise ValueError("submitted form must normalize to canonical_nfc")
        if not self.source_binding.source_backed:
            raise ValueError("bootstrap identity must be source backed")
        return self


class KoreanGrammarEntry(_FrozenGrammarModel):
    """One atomic form-function-register grammar construction."""

    entry_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    sequence: int = Field(ge=1, le=100_000)
    category_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    target_concept_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    construction_label: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    form: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    function: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    attachment_rule: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    usage_register: str = Field(
        alias="register",
        serialization_alias="register",
        min_length=1,
        max_length=_MAX_TEXT_LENGTH,
    )
    example_sentence: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    portuguese_translation: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    pronunciation_sample: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    spoken_sample: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    source_binding: KoreanGrammarSourceBinding
    evidence: KoreanCurriculumEvidence
    review_binding: KoreanGrammarAIEvidenceBinding
    word_media_binding: KoreanGrammarMediaBinding
    sentence_media_binding: KoreanGrammarMediaBinding
    ready_state: Literal["blocked", "needs_review", "learner_ready"]
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("entry_id", "category_id", "target_concept_id", "construction_label")
    @classmethod
    def ids_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="content hash")

    @field_validator(
        "form",
        "usage_register",
        "example_sentence",
        "pronunciation_sample",
        "spoken_sample",
    )
    @classmethod
    def korean_text_must_be_canonical(cls, value: str, info: object) -> str:
        return _safe_text(
            value,
            field_name=getattr(info, "field_name", "Korean text"),
            require_hangul=True,
        )

    @field_validator("function", "attachment_rule", "portuguese_translation")
    @classmethod
    def learner_text_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_text(value, field_name=getattr(info, "field_name", "learner text"))

    @model_validator(mode="after")
    def grammar_entry_must_be_hash_bound_and_gate_ready_state(self) -> Self:
        if not self.target_concept_id.startswith("grammar:"):
            raise ValueError("grammar target must be a grammar concept")
        if self.evidence.target_concept_id != self.target_concept_id:
            raise ValueError("grammar target must match curriculum evidence")
        if not self.source_binding.source_backed:
            raise ValueError("grammar source must be source backed")
        if self.ready_state == "learner_ready":
            media_ready = (
                self.word_media_binding.integrity_status == "passed"
                and self.sentence_media_binding.integrity_status == "passed"
                and self.word_media_binding.acoustic_review_status
                in {"ai_acoustic_review_passed", "automated_integrity_passed"}
                and self.sentence_media_binding.acoustic_review_status
                in {"ai_acoustic_review_passed", "automated_integrity_passed"}
            )
            if (
                self.source_binding.synthetic
                or not self.source_binding.license_decision.startswith("approved")
                or self.review_binding.consensus_status != "ai_review_passed"
                or self.review_binding.deterministic_validator_result != "passed"
                or not media_ready
            ):
                raise ValueError("learner-ready grammar requires source, review, and media gates")
        if self.content_hash != grammar_content_hash(self):
            raise ValueError("grammar entry content hash does not match")
        return self

    @property
    def register(self) -> str:
        return self.usage_register


class KoreanGrammarBundle(_FrozenGrammarModel):
    """One immutable grammar bundle over an imported Phase 31 root."""

    schema_version: Literal["korean-grammar-bundle-v1"] = "korean-grammar-bundle-v1"
    language: Literal["ko"] = KOREAN_LANGUAGE_CODE
    phase31_binding: Phase31GrammarRootBinding
    imported_concepts: tuple[KoreanConcept, ...] = Field(min_length=1, max_length=_MAX_IDS)
    overlay_concepts: tuple[KoreanConcept, ...] = Field(default=(), max_length=_MAX_IDS)
    lexical_bootstrap: tuple[KoreanGrammarBootstrapEntry, ...] = Field(
        default=(),
        max_length=_MAX_IDS,
    )
    grammar_entries: tuple[KoreanGrammarEntry, ...] = Field(default=(), max_length=_MAX_IDS)
    member_hashes: dict[str, str]
    bundle_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("member_hashes")
    @classmethod
    def member_hashes_must_be_sha256(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("grammar bundle must declare member hashes")
        for name, digest in value.items():
            _identifier(name, field_name="member name")
            _sha256_text(digest, field_name="member hash")
        return value

    @field_validator("bundle_sha256")
    @classmethod
    def bundle_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="bundle hash")

    @model_validator(mode="after")
    def imported_ids_must_match_binding(self) -> Self:
        imported_ids = tuple(concept.id for concept in self.imported_concepts)
        if imported_ids != self.phase31_binding.imported_concept_ids:
            raise ValueError("imported concepts must match Phase 31 binding")
        overlay_ids = tuple(concept.id for concept in self.overlay_concepts)
        if len(overlay_ids) != len(set(overlay_ids)):
            raise ValueError("overlay concepts must be unique")
        if set(imported_ids) & set(overlay_ids):
            raise ValueError("overlay concepts cannot collide with imported concepts")
        return self


def build_member_hashes(
    *,
    phase31_binding: Phase31GrammarRootBinding,
    imported_concepts: tuple[KoreanConcept, ...],
    overlay_concepts: tuple[KoreanConcept, ...],
    lexical_bootstrap: tuple[KoreanGrammarBootstrapEntry, ...],
    grammar_entries: tuple[KoreanGrammarEntry, ...],
) -> dict[str, str]:
    """Return stable member hashes for the independently versioned bundle parts."""

    return {
        "phase31_binding": korean_grammar_canonical_json_sha256(phase31_binding),
        "imported_concepts": korean_grammar_canonical_json_sha256(
            [concept.model_dump(mode="json") for concept in imported_concepts]
        ),
        "overlay_concepts": korean_grammar_canonical_json_sha256(
            [concept.model_dump(mode="json") for concept in overlay_concepts]
        ),
        "lexical_bootstrap": korean_grammar_canonical_json_sha256(
            [entry.model_dump(mode="json", by_alias=True) for entry in lexical_bootstrap]
        ),
        "grammar_entries": korean_grammar_canonical_json_sha256(
            [entry.model_dump(mode="json", by_alias=True) for entry in grammar_entries]
        ),
    }


def build_bundle_sha256(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("bundle_sha256", None)
    return korean_grammar_canonical_json_sha256(unsigned)


__all__ = [
    "KOREAN_GRAMMAR_CATEGORIES",
    "KOREAN_GRAMMAR_READY_STATES",
    "KOREAN_GRAMMAR_REVIEW_POLICY_ID",
    "KOREAN_GRAMMAR_SOURCE_KIND",
    "KoreanGrammarAIEvidenceBinding",
    "KoreanGrammarBootstrapEntry",
    "KoreanGrammarBundle",
    "KoreanGrammarEntry",
    "KoreanGrammarMediaBinding",
    "KoreanGrammarSourceBinding",
    "Phase31GrammarRootBinding",
    "build_bundle_sha256",
    "build_member_hashes",
    "grammar_content_hash",
    "korean_grammar_canonical_json_sha256",
]
