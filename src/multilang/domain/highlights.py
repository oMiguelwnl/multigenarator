"""Domain contracts for local Kindle highlight normalization."""

from __future__ import annotations

import unicodedata
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.korean import KoreanLexicalIdentity


_LOWERCASE_HEX = frozenset("0123456789abcdef")
_IDENTIFIER_MAX_LENGTH = 256
_TEXT_MAX_LENGTH = 10_000
_SOURCE_PATH_MAX_LENGTH = 512
_SOURCE_LOCATION_MAX_LENGTH = 256
_SAFE_MANIFEST_COUNT_KEYS = frozenset(
    {
        "imported_highlights",
        "rejected_highlights",
        "extracted_candidates",
        "duplicate_candidates",
        "planned_cards",
        "resolution_errors",
        "blocked_candidates",
        "reused_existing_items",
    }
)


class _HighlightContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


def _sha256_hex(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be lowercase SHA-256 hex")
    if len(value) != 64 or any(character not in _LOWERCASE_HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256 hex")
    return value


def _safe_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _IDENTIFIER_MAX_LENGTH
        or not all(
            character.isascii() and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _nfc_bounded_text(
    value: str | None,
    *,
    field_name: str,
    max_length: int,
    allow_none: bool = False,
) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be bounded NFC text")
    if not value or len(value) > max_length:
        raise ValueError(f"{field_name} must be bounded NFC text")
    return unicodedata.normalize("NFC", value)


class HighlightProvenance(_HighlightContract):
    """Traceable source metadata for one normalized highlight."""

    source_path: str = Field(min_length=1, max_length=_SOURCE_PATH_MAX_LENGTH)
    source_format: Literal["html", "text"]
    source_index: int = Field(ge=0)
    raw_location: str | None = Field(default=None, max_length=_SOURCE_LOCATION_MAX_LENGTH)
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("source_path")
    @classmethod
    def source_path_must_be_bounded(cls, value: str) -> str:
        normalized = _nfc_bounded_text(
            value,
            field_name="source_path",
            max_length=_SOURCE_PATH_MAX_LENGTH,
        )
        assert normalized is not None
        return normalized

    @field_validator("raw_location")
    @classmethod
    def raw_location_must_be_bounded(cls, value: str | None) -> str | None:
        return _nfc_bounded_text(
            value,
            field_name="raw_location",
            max_length=_SOURCE_LOCATION_MAX_LENGTH,
            allow_none=True,
        )

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256_hex(cls, value: str) -> str:
        return _sha256_hex(value, field_name="content_hash")


class NormalizedHighlight(_HighlightContract):
    """A privacy-preserving highlight ready for downstream extraction."""

    highlight_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    text: str = Field(min_length=1, max_length=_TEXT_MAX_LENGTH)
    provenance: HighlightProvenance

    @field_validator("highlight_id")
    @classmethod
    def highlight_id_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="highlight_id")

    @field_validator("text")
    @classmethod
    def text_must_be_nfc(cls, value: str) -> str:
        normalized = _nfc_bounded_text(value, field_name="text", max_length=_TEXT_MAX_LENGTH)
        assert normalized is not None
        return normalized


class RejectedHighlight(_HighlightContract):
    """A rejected source record with safe diagnostics."""

    source_index: int = Field(ge=0)
    reason_code: Literal["empty", "malformed", "unsafe", "unsupported_format"]
    detail: str = Field(min_length=1, max_length=256)

    @field_validator("detail")
    @classmethod
    def detail_must_be_bounded(cls, value: str) -> str:
        normalized = _nfc_bounded_text(value, field_name="detail", max_length=256)
        assert normalized is not None
        return normalized


class KindleParseResult(_HighlightContract):
    """Result of parsing a local Kindle export."""

    highlights: list[NormalizedHighlight] = Field(default_factory=list)
    rejected: list[RejectedHighlight] = Field(default_factory=list)


class SafeHighlightExcerptReference(_HighlightContract):
    """Content-free public reference to a private excerpt revision."""

    artifact_type: Literal["safe_excerpt_reference"] = "safe_excerpt_reference"
    excerpt_revision_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    highlight_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    import_content_hash: str = Field(min_length=64, max_length=64)
    source_content_hash: str = Field(min_length=64, max_length=64)
    source_index: int = Field(ge=0)
    occurrence_count: int = Field(ge=1, le=1_000_000)

    @field_validator("excerpt_revision_id", "highlight_id")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("import_content_hash", "source_content_hash")
    @classmethod
    def hashes_must_be_sha256_hex(cls, value: str, info: object) -> str:
        return _sha256_hex(value, field_name=getattr(info, "field_name", "hash"))


class HighlightPrivateExcerptRevision(_HighlightContract):
    """Local-only exact excerpt text and source linkage."""

    artifact_type: Literal["private_excerpt_revision"] = "private_excerpt_revision"
    excerpt_revision_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    highlight_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    import_content_hash: str = Field(min_length=64, max_length=64)
    source_content_hash: str = Field(min_length=64, max_length=64)
    source_index: int = Field(ge=0)
    source_path: str = Field(min_length=1, max_length=_SOURCE_PATH_MAX_LENGTH)
    source_format: Literal["html", "text"]
    raw_location: str | None = Field(default=None, max_length=_SOURCE_LOCATION_MAX_LENGTH)
    normalized_text: str = Field(min_length=1, max_length=_TEXT_MAX_LENGTH)
    revision_number: int = Field(ge=1, le=1_000_000)

    @field_validator("excerpt_revision_id", "highlight_id")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("import_content_hash", "source_content_hash")
    @classmethod
    def hashes_must_be_sha256_hex(cls, value: str, info: object) -> str:
        return _sha256_hex(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("source_path")
    @classmethod
    def private_source_path_must_be_bounded(cls, value: str) -> str:
        normalized = _nfc_bounded_text(
            value,
            field_name="source_path",
            max_length=_SOURCE_PATH_MAX_LENGTH,
        )
        assert normalized is not None
        return normalized

    @field_validator("raw_location")
    @classmethod
    def private_raw_location_must_be_bounded(cls, value: str | None) -> str | None:
        return _nfc_bounded_text(
            value,
            field_name="raw_location",
            max_length=_SOURCE_LOCATION_MAX_LENGTH,
            allow_none=True,
        )

    @field_validator("normalized_text")
    @classmethod
    def private_text_must_be_nfc(cls, value: str) -> str:
        normalized = _nfc_bounded_text(
            value,
            field_name="normalized_text",
            max_length=_TEXT_MAX_LENGTH,
        )
        assert normalized is not None
        return normalized

    def to_safe_reference(self, *, occurrence_count: int = 1) -> SafeHighlightExcerptReference:
        return SafeHighlightExcerptReference(
            excerpt_revision_id=self.excerpt_revision_id,
            highlight_id=self.highlight_id,
            import_content_hash=self.import_content_hash,
            source_content_hash=self.source_content_hash,
            source_index=self.source_index,
            occurrence_count=occurrence_count,
        )


class HighlightProviderContextMetadata(_HighlightContract):
    """Hash-only provider-context metadata; the context value is not exposed."""

    artifact_type: Literal["provider_context_metadata"] = "provider_context_metadata"
    context_revision_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    source_excerpt: SafeHighlightExcerptReference
    context_hash: str = Field(min_length=64, max_length=64)
    redaction_policy_version: str = Field(min_length=1, max_length=128)
    max_context_tokens: int = Field(ge=1, le=24)
    context_token_count: int = Field(ge=0, le=24)
    disclosure_status: Literal["not_disclosed"] = "not_disclosed"

    @field_validator("context_revision_id", "redaction_policy_version")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("context_hash")
    @classmethod
    def context_hash_must_be_sha256_hex(cls, value: str) -> str:
        return _sha256_hex(value, field_name="context_hash")

    @model_validator(mode="after")
    def token_count_must_fit_context_bound(self) -> Self:
        if self.context_token_count > self.max_context_tokens:
            raise ValueError("context token count must not exceed context bound")
        return self


class HighlightMicroexampleRevisionReference(_HighlightContract):
    """Hash-only reference to a generated learner microexample revision."""

    artifact_type: Literal["microexample_revision_reference"] = "microexample_revision_reference"
    microexample_revision_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    source_excerpt: SafeHighlightExcerptReference
    microexample_hash: str = Field(min_length=64, max_length=64)
    review_state: Literal["needs_review", "approved", "rejected"]
    evidence_policy: Literal["adaptive", "contextual"]

    @field_validator("microexample_revision_id")
    @classmethod
    def revision_id_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="microexample_revision_id")

    @field_validator("microexample_hash")
    @classmethod
    def microexample_hash_must_be_sha256_hex(cls, value: str) -> str:
        return _sha256_hex(value, field_name="microexample_hash")

    @property
    def export_eligible(self) -> bool:
        return self.review_state == "approved"


class HighlightCandidate(_HighlightContract):
    """A reviewable vocabulary candidate extracted from normalized highlights."""

    item_key: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    source_content_hash: str = Field(min_length=64, max_length=64)
    display_form: str = Field(min_length=1, max_length=256)
    lemma_key: str = Field(min_length=1, max_length=256)
    first_highlight_id: str = Field(min_length=1, max_length=_IDENTIFIER_MAX_LENGTH)
    first_source_index: int = Field(ge=0)
    occurrence_count: int = Field(ge=1, le=1_000_000)
    korean_identity: KoreanLexicalIdentity | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @field_validator("item_key", "first_highlight_id")
    @classmethod
    def identifiers_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("display_form", "lemma_key")
    @classmethod
    def candidate_text_must_be_nfc(cls, value: str, info: object) -> str:
        normalized = _nfc_bounded_text(
            value,
            field_name=getattr(info, "field_name", "candidate text"),
            max_length=256,
        )
        assert normalized is not None
        return normalized

    @field_validator("source_content_hash")
    @classmethod
    def source_content_hash_must_be_sha256_hex(cls, value: str) -> str:
        return _sha256_hex(value, field_name="source_content_hash")

    @model_validator(mode="after")
    def korean_identity_must_match_safe_candidate(self) -> Self:
        if self.korean_identity is None:
            return self
        if self.display_form != self.korean_identity.lemma:
            raise ValueError("Korean highlight display must use the source lemma")
        if self.lemma_key != self.korean_identity.lexical_key:
            raise ValueError("Korean highlight key must use the complete source identity")
        return self

    def to_safe_export_reference(
        self,
        *,
        microexample: HighlightMicroexampleRevisionReference | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "item_key": self.item_key,
            "source_content_hash": self.source_content_hash,
            "display_form": self.display_form,
            "lemma_key": self.lemma_key,
            "first_highlight_id": self.first_highlight_id,
            "first_source_index": self.first_source_index,
            "occurrence_count": self.occurrence_count,
            "source_evidence_policy": "contextual",
        }
        if microexample is not None:
            if not microexample.export_eligible:
                raise ValueError("microexample revision must be approved before export reference")
            if microexample.source_excerpt.source_content_hash != self.source_content_hash:
                raise ValueError("microexample source hash must match highlight candidate")
            payload.update(
                {
                    "microexample_revision_id": microexample.microexample_revision_id,
                    "microexample_hash": microexample.microexample_hash,
                    "microexample_evidence_policy": microexample.evidence_policy,
                }
            )
        return payload


class HighlightExtractionError(_HighlightContract):
    """Content-free extraction failure tied only to an allowed source index."""

    source_index: int = Field(ge=0)
    reason_code: Literal[
        "korean_resolver_required",
        "korean_resolution_failed",
        "korean_resolution_unavailable",
    ]


class HighlightImportManifest(_HighlightContract):
    """Safe count/hash-only manifest for one highlight import."""

    import_content_hash: str = Field(min_length=64, max_length=64)
    candidate_keys: list[str] = Field(default_factory=list, max_length=100_000)
    counts: dict[str, int] = Field(
        default_factory=dict,
        max_length=len(_SAFE_MANIFEST_COUNT_KEYS),
    )

    @field_validator("import_content_hash")
    @classmethod
    def import_content_hash_must_be_sha256_hex(cls, value: str) -> str:
        return _sha256_hex(value, field_name="import_content_hash")

    @field_validator("candidate_keys")
    @classmethod
    def candidate_keys_must_be_safe(cls, value: list[str]) -> list[str]:
        return [_safe_identifier(item, field_name="candidate key") for item in value]

    @field_validator("counts")
    @classmethod
    def counts_must_be_controlled(cls, value: dict[str, int]) -> dict[str, int]:
        controlled: dict[str, int] = {}
        for key, count in value.items():
            if key not in _SAFE_MANIFEST_COUNT_KEYS:
                raise ValueError("manifest counts must use controlled keys")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError("manifest counts must be non-negative integers")
            controlled[key] = count
        return controlled


class HighlightCandidateExtractionResult(_HighlightContract):
    """Candidate extraction output with deterministic filtering counters."""

    candidates: list[HighlightCandidate] = Field(default_factory=list)
    duplicate_count: int = Field(ge=0)
    rejected_token_count: int = Field(ge=0)
    errors: list[HighlightExtractionError] = Field(
        default_factory=list,
        exclude_if=lambda value: not value,
    )


class HighlightImportPreview(_HighlightContract):
    """Count-only preview of a local Kindle import before generation."""

    imported_highlights: int = Field(ge=0)
    extracted_candidates: int = Field(ge=0)
    rejected_highlights: int = Field(ge=0)
    duplicate_candidates: int = Field(ge=0)
    planned_cards: int = Field(ge=0)


__all__ = [
    "HighlightCandidate",
    "HighlightCandidateExtractionResult",
    "HighlightExtractionError",
    "HighlightImportManifest",
    "HighlightImportPreview",
    "HighlightMicroexampleRevisionReference",
    "HighlightPrivateExcerptRevision",
    "HighlightProvenance",
    "HighlightProviderContextMetadata",
    "KindleParseResult",
    "NormalizedHighlight",
    "RejectedHighlight",
    "SafeHighlightExcerptReference",
]
