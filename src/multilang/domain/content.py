"""Immutable enrichment contracts; generated text never owns lexical identity."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)


class FrozenContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def canonical_content_hash(value: object) -> str:
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


class ContentRequest(FrozenContentModel):
    lexical_identity_id: str = Field(min_length=1, max_length=255)
    card_id: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=2, max_length=8)
    language_profile_version: str = Field(min_length=1, max_length=128)
    lemma: str = Field(min_length=1, max_length=255)
    display_text: str = Field(min_length=1, max_length=1000)
    sense_id: str = Field(min_length=1, max_length=255)
    morphological_analysis_id: str | None = Field(
        default=None, min_length=1, max_length=255
    )
    context_cue: str = Field(min_length=1, max_length=4000)
    namespace: str = Field(min_length=1, max_length=255)
    deck_edition_id: str = Field(min_length=1, max_length=255)
    grounding_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_concept_id: str = Field(min_length=1, max_length=255)
    canonical_known_concept_ids: tuple[str, ...] = Field(default=(), max_length=10000)
    known_concept_ids: tuple[str, ...] = Field(default=(), max_length=10000)
    private_context: str | None = Field(default=None, max_length=4000)
    private_context_authorized: bool = False
    i_plus_one_mode: Literal["strict", "adaptive", "contextual"] = "contextual"
    render_policy_version: str = "plain-text-1"
    content_policy_version: str = "1"
    explanation_language: str = Field(default="en", min_length=2, max_length=8)

    @model_validator(mode="after")
    def namespace_policy(self) -> ContentRequest:
        if self.namespace == "core":
            if (
                self.known_concept_ids
                or self.private_context
                or self.private_context_authorized
            ):
                raise ValueError(
                    "Core content cannot use personal knowledge or context"
                )
        elif not self.namespace.startswith("user:") or len(self.namespace) <= 5:
            raise ValueError(
                "content namespace must be core or an explicit user namespace"
            )
        if self.private_context and not self.private_context_authorized:
            raise ValueError("private context requires explicit authorization")
        return self


class GeneratedContent(FrozenContentModel):
    definition: str = Field(min_length=1, max_length=2000)
    example_sentence: str = Field(min_length=1, max_length=4000)
    translation: str = Field(min_length=1, max_length=4000)
    explanation: str = Field(default="", max_length=4000)
    exercises: tuple[str, ...] = Field(default=(), max_length=10)


class TargetMatchEvidence(FrozenContentModel):
    lexical_identity_id: str
    sense_id: str
    morphological_analysis_id: str | None = None
    target_concept_id: str
    matched: bool
    observed_concept_ids: tuple[str, ...]
    analyzer_version: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    # Matcher-verified Unicode character offsets into the exact example sentence;
    # the end is exclusive. No tokenizer or substring heuristic may infer them.
    target_span: tuple[
        Annotated[int, Field(ge=0, strict=True)],
        Annotated[int, Field(gt=0, strict=True)],
    ] | None = None

    @model_serializer(mode="wrap")
    def serialize_verified_span(self, handler: SerializerFunctionWrapHandler) -> dict:
        payload = handler(self)
        if self.target_span is None:
            # Existing versions without a span must retain their content hashes.
            payload.pop("target_span", None)
        return payload


class ContentLimits(FrozenContentModel):
    max_request_bytes: int = Field(default=64000, ge=1, le=1000000)
    max_request_characters: int = Field(default=32000, ge=1, le=1000000)
    max_estimated_tokens: int = Field(default=16000, ge=1, le=1000000)
    max_response_bytes: int = Field(default=32000, ge=1, le=1000000)


class ContentVersion(FrozenContentModel):
    request: ContentRequest
    content: GeneratedContent
    target_evidence: TargetMatchEvidence
    provider: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    incidental_concept_ids: tuple[str, ...] = ()
    review_status: Literal["pending", "approved", "rejected"] = "pending"
    review_receipt_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    independent_reviewer: str | None = None

    @model_validator(mode="after")
    def independent_review(self) -> ContentVersion:
        if self.review_status == "approved" and (
            not self.review_receipt_sha256 or not self.independent_reviewer
        ):
            raise ValueError("approved content requires independent review evidence")
        return self

    @property
    def version_id(self) -> str:
        return "content:1:" + canonical_content_hash(self.model_dump(mode="json"))

    @property
    def namespace(self) -> str:
        return self.request.namespace


ContentContract = ContentVersion


class CanonicalContentEdition(FrozenContentModel):
    deck_edition_id: str = Field(min_length=1)
    content_versions: tuple[ContentVersion, ...] = Field(min_length=1)
    approval_receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def canonical_shared_bundle(self) -> CanonicalContentEdition:
        ids: set[str] = set()
        for version in self.content_versions:
            if (
                version.namespace != "core"
                or version.request.deck_edition_id != self.deck_edition_id
            ):
                raise ValueError("canonical edition requires same-edition Core content")
            if version.review_status != "approved":
                raise ValueError(
                    "canonical edition requires independent approved content"
                )
            if version.request.card_id in ids:
                raise ValueError("duplicate card content in canonical edition")
            ids.add(version.request.card_id)
        return self

    @property
    def bundle_sha256(self) -> str:
        return canonical_content_hash(
            {
                "edition": self.deck_edition_id,
                "versions": sorted(
                    version.version_id for version in self.content_versions
                ),
                "approval": self.approval_receipt_sha256,
            }
        )

    def diff(
        self, other: CanonicalContentEdition
    ) -> dict[str, tuple[str | None, str | None]]:
        old = {v.request.card_id: v.version_id for v in self.content_versions}
        new = {v.request.card_id: v.version_id for v in other.content_versions}
        return {
            key: (old.get(key), new.get(key))
            for key in sorted(old.keys() | new.keys())
            if old.get(key) != new.get(key)
        }
