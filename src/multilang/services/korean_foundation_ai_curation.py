"""Nonauthoritative Korean foundation assisted-curation contracts."""

import json
import os
import shutil
import stat
import tempfile
import unicodedata
from collections import Counter
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Self, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from multilang.services.korean_curriculum import (
    KoreanFoundationEntry,
    KoreanFoundationFamily,
    KoreanHangulSourcePack,
    KoreanPronunciationSourcePack,
    korean_canonical_json_sha256,
)


_LOWERCASE_HEX = frozenset("0123456789abcdef")
_PLACEHOLDERS = frozenset(
    {"needs_review", "needs review", "tbd", "todo", "unknown", "n/a", "null"}
)
_MAX_TEXT_LENGTH = 1_000
_MAX_GROUNDING_REFERENCES = 8
KOREAN_FOUNDATION_PROJECTION_MAX_BYTES = 120 * 1024
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_PATHS = {
    KoreanFoundationFamily.HANGUL: (
        _PROJECT_ROOT / "data/korean_foundations/hangul-v1.json"
    ),
    KoreanFoundationFamily.PRONUNCIATION: (
        _PROJECT_ROOT / "data/korean_foundations/pronunciation-i-plus-1-v1.json"
    ),
}
KOREAN_FOUNDATION_CURATION_DRAFT_ROOT = (
    _PROJECT_ROOT
    / ".planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts"
)
KOREAN_FOUNDATION_CURATION_INPUT_ROOT = (
    KOREAN_FOUNDATION_CURATION_DRAFT_ROOT / "inputs"
)

KoreanFoundationBatchId: TypeAlias = Literal[
    "hangul-h0-h3",
    "hangul-h4-h7",
    "hangul-h8-h10",
    "pronunciation-p0-p4",
    "pronunciation-p5-p9",
    "pronunciation-p10-p13",
]

_BATCH_STAGES: dict[str, tuple[str, ...]] = {
    "hangul-h0-h3": ("H0", "H1", "H2", "H3"),
    "hangul-h4-h7": ("H4", "H5", "H6", "H7"),
    "hangul-h8-h10": ("H8", "H9", "H10"),
    "pronunciation-p0-p4": ("P0", "P1", "P2", "P3", "P4"),
    "pronunciation-p5-p9": ("P5", "P6", "P7", "P8", "P9"),
    "pronunciation-p10-p13": ("P10", "P11", "P12", "P13"),
}
_BATCH_FAMILIES = {
    batch_id: (
        KoreanFoundationFamily.HANGUL
        if batch_id.startswith("hangul-")
        else KoreanFoundationFamily.PRONUNCIATION
    )
    for batch_id in _BATCH_STAGES
}
_PROJECTION_PATHS = {
    batch_id: KOREAN_FOUNDATION_CURATION_INPUT_ROOT / f"{batch_id}.json"
    for batch_id in _BATCH_STAGES
}
_BATCH_DRAFT_PATHS = {
    batch_id: KOREAN_FOUNDATION_CURATION_DRAFT_ROOT / f"{batch_id}.json"
    for batch_id in _BATCH_STAGES
}
_FAMILY_DRAFT_PATHS = {
    KoreanFoundationFamily.HANGUL: (
        KOREAN_FOUNDATION_CURATION_DRAFT_ROOT / "hangul-v2-draft.json"
    ),
    KoreanFoundationFamily.PRONUNCIATION: (
        KOREAN_FOUNDATION_CURATION_DRAFT_ROOT
        / "pronunciation-i-plus-1-v2-draft.json"
    ),
}
_DRAFT_MANIFEST_PATH = KOREAN_FOUNDATION_CURATION_DRAFT_ROOT / "draft-manifest.json"
KOREAN_FOUNDATION_EXECUTION_HANDOFF_ROOT = (
    _PROJECT_ROOT
    / ".planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs"
)
_CURATION_SELECTION_HANDOFF_PATH = (
    KOREAN_FOUNDATION_EXECUTION_HANDOFF_ROOT / "curation-selection.json"
)
KOREAN_FOUNDATION_CANDIDATE_ROOT = _PROJECT_ROOT / "data/korean_foundations"
KOREAN_FOUNDATION_CANDIDATE_BUNDLE_ROOT = (
    KOREAN_FOUNDATION_CANDIDATE_ROOT / "candidate-bundles"
)
_CURRENT_CANDIDATE_POINTER_PATH = (
    KOREAN_FOUNDATION_CANDIDATE_ROOT / "current-candidate.json"
)
_FOUNDATION_V1_CURATION_PATH = (
    KOREAN_FOUNDATION_CANDIDATE_ROOT / "korean-foundations-v1-curation.json"
)
_FOUNDATION_V1_MEDIA_PATH = (
    KOREAN_FOUNDATION_CANDIDATE_ROOT / "korean-foundations-v1-media.json"
)
_CURRICULUM_REVIEW_REQUEST_PATH = (
    KOREAN_FOUNDATION_EXECUTION_HANDOFF_ROOT.parent / "31-CURRICULUM-REVIEW.md"
)
_AUDIO_PLAYBACK_REVIEW_REQUEST_PATH = (
    KOREAN_FOUNDATION_EXECUTION_HANDOFF_ROOT.parent / "31-AUDIO-PLAYBACK-REVIEW.md"
)
_CANDIDATE_MEMBER_NAMES = (
    "hangul-v2.json",
    "pronunciation-i-plus-1-v2.json",
    "korean-foundations-v2-curation.json",
    "korean-foundations-v2-media.json",
)
_FAMILY_FIELDS = {
    KoreanFoundationFamily.HANGUL: frozenset(
        {"reading_or_name", "sound", "mnemonic"}
    ),
    KoreanFoundationFamily.PRONUNCIATION: frozenset(
        {
            "spellings",
            "sound",
            "example_word",
            "word_translation",
            "example_sentence",
            "sentence_translation",
            "normative_pronunciation",
            "surface_pronunciation",
            "ipa",
        }
    ),
}

KoreanFoundationDraftFieldName: TypeAlias = Literal[
    "reading_or_name",
    "sound",
    "mnemonic",
    "spellings",
    "example_word",
    "word_translation",
    "example_sentence",
    "sentence_translation",
    "normative_pronunciation",
    "surface_pronunciation",
    "ipa",
]


def _sha256_text(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _LOWERCASE_HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > 128
        or not normalized[0].isalnum()
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _plain_nfc_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be bounded plain text")
    normalized = value.strip()
    folded = normalized.casefold()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _MAX_TEXT_LENGTH
        or unicodedata.normalize("NFC", normalized) != normalized
        or folded in _PLACEHOLDERS
        or any(character in normalized for character in "<>`{}")
        or "![" in normalized
        or "](" in normalized
        or any(
            unicodedata.category(character) in {"Cc", "Cf"}
            for character in normalized
        )
        or any(
            0x3130 <= ord(character) < 0x3190
            or 0xFFA0 <= ord(character) < 0xFFDD
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be bounded plain NFC text")
    return normalized


def _json_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def korean_draft_content_hash(value: BaseModel | dict[str, object]) -> str:
    """Hash one draft object without its self-referential content hash."""

    payload = _json_value(value)
    if not isinstance(payload, dict):
        raise TypeError("draft hash payload must be an object")
    payload.pop("content_hash", None)
    return korean_canonical_json_sha256(payload)


def _load_fixed_source_pack(
    family: KoreanFoundationFamily,
) -> tuple[Path, KoreanHangulSourcePack | KoreanPronunciationSourcePack]:
    path = _SOURCE_PATHS[family]
    raw = path.read_bytes()
    model_type = (
        KoreanHangulSourcePack
        if family is KoreanFoundationFamily.HANGUL
        else KoreanPronunciationSourcePack
    )
    return path, model_type.model_validate_json(raw)


class _FrozenDraftModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class KoreanFoundationDraftSourceReference(_FrozenDraftModel):
    family: KoreanFoundationFamily
    source_file_name: Literal[
        "hangul-v1.json",
        "pronunciation-i-plus-1-v1.json",
    ]
    source_file_sha256: str = Field(min_length=64, max_length=64)
    source_pack_version: Literal["hangul-v1", "pronunciation-i-plus-1-v1"]
    source_pack_content_hash: str = Field(min_length=64, max_length=64)
    registry_version: Literal["korean-concepts-v1"]
    registry_content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "source_file_sha256",
        "source_pack_content_hash",
        "registry_content_hash",
    )
    @classmethod
    def hashes_must_be_lowercase_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "source hash"),
        )

    @model_validator(mode="after")
    def source_identity_must_match_family(self) -> Self:
        expected = {
            KoreanFoundationFamily.HANGUL: ("hangul-v1.json", "hangul-v1"),
            KoreanFoundationFamily.PRONUNCIATION: (
                "pronunciation-i-plus-1-v1.json",
                "pronunciation-i-plus-1-v1",
            ),
        }[self.family]
        if (self.source_file_name, self.source_pack_version) != expected:
            raise ValueError("source identity does not match foundation family")
        return self


class KoreanFoundationProjectionValue(_FrozenDraftModel):
    field_name: str = Field(min_length=1, max_length=128)
    value: str | None = Field(default=None, max_length=2_048)

    @field_validator("field_name")
    @classmethod
    def field_name_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="projection field name")


class KoreanFoundationProjectionGrounding(_FrozenDraftModel):
    source_id: str = Field(min_length=1, max_length=128)
    source_reference: str = Field(min_length=1, max_length=1_000)
    source_hash: str = Field(min_length=64, max_length=64)

    @field_validator("source_id")
    @classmethod
    def source_id_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="projection source id")

    @field_validator("source_hash")
    @classmethod
    def source_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="projection source hash")


class KoreanFoundationProjectionRecord(_FrozenDraftModel):
    item_key: str = Field(min_length=1, max_length=128)
    sequence: int = Field(ge=1, le=4_096)
    stage_id: str = Field(min_length=2, max_length=4)
    category_id: str = Field(min_length=1, max_length=128)
    target_concept_id: str = Field(min_length=1, max_length=128)
    prerequisite_concept_ids: tuple[str, ...] = Field(default=(), max_length=128)
    active_rule_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    source_entry_content_hash: str = Field(min_length=64, max_length=64)
    structure_hash: str = Field(min_length=64, max_length=64)
    current_values: tuple[KoreanFoundationProjectionValue, ...] = Field(
        min_length=1,
        max_length=16,
    )
    grounding: tuple[KoreanFoundationProjectionGrounding, ...] = Field(
        min_length=1,
        max_length=16,
    )

    @field_validator("item_key", "stage_id", "category_id", "target_concept_id")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "projection identifier"),
        )

    @field_validator("prerequisite_concept_ids", "active_rule_ids")
    @classmethod
    def concept_ids_must_be_unique(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        normalized = tuple(
            _identifier(
                item,
                field_name=getattr(info, "field_name", "projection concept id"),
            )
            for item in value
        )
        if len(normalized) != len(set(normalized)):
            raise ValueError("projection concept ids must be unique")
        return normalized

    @field_validator("source_entry_content_hash", "structure_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "projection hash"),
        )


class KoreanFoundationBatchProjection(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    batch_id: KoreanFoundationBatchId
    draft_only: Literal[True] = True
    review_status: Literal["needs_review"] = "needs_review"
    promotion_authority: Literal[False] = False
    source: KoreanFoundationDraftSourceReference
    stages: tuple[str, ...] = Field(min_length=1, max_length=5)
    records: tuple[KoreanFoundationProjectionRecord, ...] = Field(
        min_length=1,
        max_length=128,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="projection content hash")

    @model_validator(mode="after")
    def projection_must_be_exact_bounded_batch(self) -> Self:
        if self.source.family is not _BATCH_FAMILIES[self.batch_id]:
            raise ValueError("projection family does not match batch")
        if self.stages != _BATCH_STAGES[self.batch_id]:
            raise ValueError("projection stages do not match batch")
        if any(record.stage_id not in self.stages for record in self.records):
            raise ValueError("projection contains an unrelated stage")
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("projection content hash does not match")
        if len(self.model_dump_json().encode("utf-8")) > (
            KOREAN_FOUNDATION_PROJECTION_MAX_BYTES
        ):
            raise ValueError("projection exceeds the fixed size limit")
        return self


def _source_reference_payload(
    family: KoreanFoundationFamily,
    path: Path,
    pack: KoreanHangulSourcePack | KoreanPronunciationSourcePack,
) -> dict[str, object]:
    return {
        "family": family,
        "source_file_name": path.name,
        "source_file_sha256": sha256(path.read_bytes()).hexdigest(),
        "source_pack_version": pack.source_pack_version,
        "source_pack_content_hash": pack.content_hash,
        "registry_version": pack.registry_version,
        "registry_content_hash": pack.registry_content_hash,
    }


def _projection_current_values(entry: KoreanFoundationEntry) -> dict[str, str | None]:
    if entry.family is KoreanFoundationFamily.HANGUL:
        values = {
            "canonical_jamo_or_block": getattr(entry, "canonical_jamo_or_block"),
            "reading_or_name": getattr(entry, "reading_or_name"),
            "sound": getattr(entry, "sound"),
            "mnemonic": getattr(entry, "mnemonic"),
        }
        mapping = getattr(entry, "pedagogical_jamo_mapping")
        if mapping is not None:
            values["display_glyph"] = mapping.display_glyph
        return values
    evidence = getattr(entry, "pronunciation_evidence")
    return {
        "spellings": getattr(entry, "spellings"),
        "sound": getattr(entry, "sound"),
        "example_word": getattr(entry, "example_word"),
        "word_translation": getattr(entry, "word_translation"),
        "example_sentence": getattr(entry, "example_sentence"),
        "sentence_translation": getattr(entry, "sentence_translation"),
        "register_context": getattr(entry, "register_context"),
        "normative_pronunciation": evidence.normative_pronunciation,
        "surface_pronunciation": evidence.surface_pronunciation,
        "ipa": evidence.ipa,
    }


def build_korean_foundation_batch_projection(
    batch_id: KoreanFoundationBatchId,
) -> KoreanFoundationBatchProjection:
    """Build one bounded projection from the fixed immutable source pack."""

    if batch_id not in _BATCH_STAGES:
        raise ValueError("unsupported Korean foundation curation batch")
    family = _BATCH_FAMILIES[batch_id]
    stages = _BATCH_STAGES[batch_id]
    path, pack = _load_fixed_source_pack(family)
    records = []
    for entry in pack.entries:
        if entry.stage_id not in stages:
            continue
        structure = {
            "item_key": entry.item_key,
            "sequence": entry.sequence,
            "stage_id": entry.stage_id,
            "category_id": entry.category_id,
            "target_concept_id": entry.evidence.target_concept_id,
            "prerequisite_concept_ids": list(
                entry.evidence.prerequisite_concept_ids
            ),
            "active_rule_ids": list(entry.active_rule_ids),
        }
        records.append(
            {
                **structure,
                "source_entry_content_hash": entry.content_hash,
                "structure_hash": korean_canonical_json_sha256(structure),
                "current_values": [
                    {"field_name": field_name, "value": value}
                    for field_name, value in _projection_current_values(entry).items()
                ],
                "grounding": [
                    {
                        "source_id": provenance.source_id,
                        "source_reference": provenance.source_reference,
                        "source_hash": provenance.source_hash,
                    }
                    for provenance in entry.provenance
                ],
            }
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "batch_id": batch_id,
        "draft_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "source": _source_reference_payload(family, path, pack),
        "stages": stages,
        "records": records,
    }
    payload["content_hash"] = korean_draft_content_hash(payload)
    return KoreanFoundationBatchProjection.model_validate(payload)


class KoreanFoundationFieldProposal(_FrozenDraftModel):
    field_name: KoreanFoundationDraftFieldName
    value: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    authorship: Literal["ai-proposed"] = "ai-proposed"
    grounding_reference_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=_MAX_GROUNDING_REFERENCES,
    )

    @field_validator("value")
    @classmethod
    def value_must_be_plain_nfc_text(cls, value: str) -> str:
        return _plain_nfc_text(value, field_name="proposal value")

    @field_validator("grounding_reference_ids")
    @classmethod
    def grounding_references_must_be_unique(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized = tuple(
            _identifier(item, field_name="grounding reference") for item in value
        )
        if len(normalized) != len(set(normalized)):
            raise ValueError("grounding references must be unique")
        return normalized


class KoreanFoundationDraftUncertainty(_FrozenDraftModel):
    field_name: KoreanFoundationDraftFieldName
    code: str = Field(min_length=1, max_length=128)
    grounding_reference_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=_MAX_GROUNDING_REFERENCES,
    )

    @field_validator("code")
    @classmethod
    def code_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="uncertainty code")

    @field_validator("grounding_reference_ids")
    @classmethod
    def grounding_references_must_be_unique(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        return KoreanFoundationFieldProposal.grounding_references_must_be_unique(value)


class KoreanFoundationDraftDisagreement(KoreanFoundationDraftUncertainty):
    """A bounded challenge-pass disagreement with no adjudication authority."""


class KoreanFoundationDraftRecord(_FrozenDraftModel):
    item_key: str = Field(min_length=1, max_length=128)
    sequence: int = Field(ge=1, le=4_096)
    stage_id: str = Field(min_length=2, max_length=4)
    source_entry_content_hash: str = Field(min_length=64, max_length=64)
    proposals: tuple[KoreanFoundationFieldProposal, ...] = Field(
        default=(),
        max_length=16,
    )
    uncertainties: tuple[KoreanFoundationDraftUncertainty, ...] = Field(
        default=(),
        max_length=16,
    )
    disagreements: tuple[KoreanFoundationDraftDisagreement, ...] = Field(
        default=(),
        max_length=16,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("item_key", "stage_id")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "record identifier"),
        )

    @field_validator("source_entry_content_hash", "content_hash")
    @classmethod
    def hashes_must_be_lowercase_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "record hash"),
        )

    @model_validator(mode="after")
    def record_must_have_unique_dispositions_and_valid_hash(self) -> Self:
        proposal_fields = tuple(item.field_name for item in self.proposals)
        uncertainty_fields = tuple(item.field_name for item in self.uncertainties)
        dispositions = proposal_fields + uncertainty_fields
        if len(dispositions) != len(set(dispositions)):
            raise ValueError("draft field dispositions must be unique")
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("draft record content hash does not match")
        return self


class KoreanFoundationBatchDraft(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    batch_id: KoreanFoundationBatchId
    draft_only: Literal[True] = True
    review_status: Literal["needs_review"] = "needs_review"
    promotion_authority: Literal[False] = False
    source: KoreanFoundationDraftSourceReference
    stages: tuple[str, ...] = Field(min_length=1, max_length=5)
    records: tuple[KoreanFoundationDraftRecord, ...] = Field(
        min_length=1,
        max_length=128,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="batch content hash")

    @model_validator(mode="after")
    def batch_must_match_exact_immutable_source(self) -> Self:
        family = _BATCH_FAMILIES[self.batch_id]
        expected_stages = _BATCH_STAGES[self.batch_id]
        if self.source.family is not family or tuple(self.stages) != expected_stages:
            raise ValueError("draft batch identity or stages do not match")

        path, pack = _load_fixed_source_pack(family)
        expected_source = {
            "family": family,
            "source_file_name": path.name,
            "source_file_sha256": sha256(path.read_bytes()).hexdigest(),
            "source_pack_version": pack.source_pack_version,
            "source_pack_content_hash": pack.content_hash,
            "registry_version": pack.registry_version,
            "registry_content_hash": pack.registry_content_hash,
        }
        if self.source.model_dump(mode="json") != expected_source:
            raise ValueError("draft source binding is stale")

        expected_entries = tuple(
            entry for entry in pack.entries if entry.stage_id in expected_stages
        )
        expected_identity = tuple(
            (
                entry.item_key,
                entry.sequence,
                entry.stage_id,
                entry.content_hash,
            )
            for entry in expected_entries
        )
        actual_identity = tuple(
            (
                record.item_key,
                record.sequence,
                record.stage_id,
                record.source_entry_content_hash,
            )
            for record in self.records
        )
        if actual_identity != expected_identity:
            raise ValueError("draft batch item coverage or source hashes do not match")

        allowed_fields = _FAMILY_FIELDS[family]
        for record, entry in zip(self.records, expected_entries, strict=True):
            disposition_fields = {
                item.field_name for item in (*record.proposals, *record.uncertainties)
            }
            if disposition_fields != allowed_fields:
                raise ValueError("draft record learner-field coverage does not match")
            source_ids = {item.source_id for item in entry.provenance}
            grounding_ids = {
                grounding_id
                for item in (*record.proposals, *record.uncertainties)
                for grounding_id in item.grounding_reference_ids
            }
            if not grounding_ids <= source_ids:
                raise ValueError("draft grounding reference is not source-bound")

        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("draft batch content hash does not match")
        return self


class KoreanFoundationDraftArtifactBinding(_FrozenDraftModel):
    artifact_id: str = Field(min_length=1, max_length=128)
    content_hash: str = Field(min_length=64, max_length=64)
    record_count: int = Field(ge=1, le=139)
    stages: tuple[str, ...] = Field(min_length=1, max_length=14)
    proposal_count: int = Field(ge=0, le=1_251)
    uncertainty_count: int = Field(ge=0, le=1_251)
    disagreement_count: int = Field(ge=0, le=1_251)

    @field_validator("artifact_id")
    @classmethod
    def artifact_id_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="artifact id")

    @field_validator("stages")
    @classmethod
    def stages_must_be_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_identifier(item, field_name="stage id") for item in value)
        if len(normalized) != len(set(normalized)):
            raise ValueError("artifact stages must be unique")
        return normalized

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="artifact content hash")


class KoreanFoundationFamilyDraft(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    family: KoreanFoundationFamily
    draft_only: Literal[True] = True
    review_status: Literal["needs_review"] = "needs_review"
    promotion_authority: Literal[False] = False
    source: KoreanFoundationDraftSourceReference
    batch_bindings: tuple[KoreanFoundationDraftArtifactBinding, ...] = Field(
        min_length=3,
        max_length=3,
    )
    records: tuple[KoreanFoundationDraftRecord, ...] = Field(
        min_length=1,
        max_length=139,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="family draft content hash")

    @model_validator(mode="after")
    def family_draft_must_have_exact_source_and_coverage(self) -> Self:
        expected_batch_ids = tuple(
            batch_id
            for batch_id, family in _BATCH_FAMILIES.items()
            if family is self.family
        )
        if self.source.family is not self.family or tuple(
            binding.artifact_id for binding in self.batch_bindings
        ) != expected_batch_ids:
            raise ValueError("family draft batch identity does not match")

        path, pack = _load_fixed_source_pack(self.family)
        expected_source = {
            "family": self.family,
            "source_file_name": path.name,
            "source_file_sha256": sha256(path.read_bytes()).hexdigest(),
            "source_pack_version": pack.source_pack_version,
            "source_pack_content_hash": pack.content_hash,
            "registry_version": pack.registry_version,
            "registry_content_hash": pack.registry_content_hash,
        }
        if self.source.model_dump(mode="json") != expected_source:
            raise ValueError("family draft source binding is stale")

        actual_identity = tuple(
            (
                record.item_key,
                record.sequence,
                record.stage_id,
                record.source_entry_content_hash,
            )
            for record in self.records
        )
        expected_identity = tuple(
            (entry.item_key, entry.sequence, entry.stage_id, entry.content_hash)
            for entry in pack.entries
        )
        if actual_identity != expected_identity:
            raise ValueError("family draft item coverage or source hashes do not match")

        allowed_fields = _FAMILY_FIELDS[self.family]
        for record, entry in zip(self.records, pack.entries, strict=True):
            disposition_fields = {
                item.field_name for item in (*record.proposals, *record.uncertainties)
            }
            if disposition_fields != allowed_fields:
                raise ValueError("family draft learner-field coverage does not match")
            source_ids = {item.source_id for item in entry.provenance}
            references = {
                reference
                for item in (
                    *record.proposals,
                    *record.uncertainties,
                    *record.disagreements,
                )
                for reference in item.grounding_reference_ids
            }
            if not references <= source_ids:
                raise ValueError("family draft grounding is not source-bound")

        records_by_stage = {
            stage: tuple(record for record in self.records if record.stage_id == stage)
            for stage in tuple(
                stage for stages in _BATCH_STAGES.values() for stage in stages
            )
        }
        for binding in self.batch_bindings:
            expected_stages = _BATCH_STAGES[binding.artifact_id]
            records = tuple(
                record
                for stage in expected_stages
                for record in records_by_stage.get(stage, ())
            )
            if (
                binding.stages != expected_stages
                or binding.record_count != len(records)
                or binding.proposal_count
                != sum(len(record.proposals) for record in records)
                or binding.uncertainty_count
                != sum(len(record.uncertainties) for record in records)
                or binding.disagreement_count
                != sum(len(record.disagreements) for record in records)
            ):
                raise ValueError("family draft batch counts do not match")

        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("family draft content hash does not match")
        return self


class KoreanFoundationDraftManifest(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    manifest_version: Literal["korean-foundations-v2-draft"]
    draft_only: Literal[True] = True
    review_status: Literal["needs_review"] = "needs_review"
    promotion_authority: Literal[False] = False
    family_bindings: tuple[KoreanFoundationDraftArtifactBinding, ...] = Field(
        min_length=2,
        max_length=2,
    )
    batch_bindings: tuple[KoreanFoundationDraftArtifactBinding, ...] = Field(
        min_length=6,
        max_length=6,
    )
    total_record_count: Literal[139]
    proposal_count: int = Field(ge=0, le=1_251)
    uncertainty_count: int = Field(ge=0, le=1_251)
    disagreement_count: int = Field(ge=0, le=1_251)
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="draft manifest content hash")

    @model_validator(mode="after")
    def manifest_must_bind_exact_two_family_inventory(self) -> Self:
        expected_family_ids = (
            "hangul-v2-draft",
            "pronunciation-i-plus-1-v2-draft",
        )
        if tuple(binding.artifact_id for binding in self.family_bindings) != (
            expected_family_ids
        ):
            raise ValueError("draft manifest family bindings do not match")
        if tuple(binding.record_count for binding in self.family_bindings) != (92, 47):
            raise ValueError("draft manifest family counts do not match")
        expected_family_stages = (
            tuple(f"H{number}" for number in range(11)),
            tuple(f"P{number}" for number in range(14)),
        )
        if tuple(binding.stages for binding in self.family_bindings) != (
            expected_family_stages
        ):
            raise ValueError("draft manifest family stages do not match")
        if tuple(binding.artifact_id for binding in self.batch_bindings) != tuple(
            _BATCH_STAGES
        ):
            raise ValueError("draft manifest batch bindings do not match")
        if any(
            binding.stages != _BATCH_STAGES[binding.artifact_id]
            for binding in self.batch_bindings
        ):
            raise ValueError("draft manifest batch stages do not match")
        if sum(binding.record_count for binding in self.batch_bindings) != 139:
            raise ValueError("draft manifest batch record counts do not match")
        for field_name in (
            "proposal_count",
            "uncertainty_count",
            "disagreement_count",
        ):
            family_total = sum(
                getattr(binding, field_name) for binding in self.family_bindings
            )
            batch_total = sum(
                getattr(binding, field_name) for binding in self.batch_bindings
            )
            if getattr(self, field_name) != family_total or family_total != batch_total:
                raise ValueError("draft manifest aggregate counts do not match")
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("draft manifest content hash does not match")
        return self


class KoreanFoundationDraftValidationReport(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    status: Literal["valid"] = "valid"
    draft_only: Literal[True] = True
    review_status: Literal["needs_review"] = "needs_review"
    promotion_authority: Literal[False] = False
    validated_batch_count: Literal[6] = 6
    validated_family_count: Literal[2] = 2
    validated_record_count: Literal[139] = 139
    draft_manifest_hash: str = Field(min_length=64, max_length=64)
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("draft_manifest_hash", "content_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "validation hash"),
        )

    @model_validator(mode="after")
    def report_hash_must_match(self) -> Self:
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("draft validation report content hash does not match")
        return self


class KoreanFoundationCurationSelectionHandoff(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    handoff_version: Literal["phase31-handoff-v1"]
    kind: Literal["curation-selection"]
    selected_sha256: str = Field(min_length=64, max_length=64)
    current_draft_manifest_sha256: str = Field(min_length=64, max_length=64)
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "selected_sha256",
        "current_draft_manifest_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "selection hash"),
        )

    @model_validator(mode="after")
    def selected_hash_must_be_current_and_self_hashed(self) -> Self:
        if self.selected_sha256 != self.current_draft_manifest_sha256:
            raise ValueError("selection handoff hash does not match current manifest")
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("selection handoff content hash does not match")
        return self


class KoreanFoundationCandidateBundlePlan(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    bundle_contract_version: Literal[
        "korean-foundations-v2-candidate-bundle-plan-v1"
    ]
    selected_draft_manifest_sha256: str = Field(min_length=64, max_length=64)
    validation_report_sha256: str = Field(min_length=64, max_length=64)
    hangul_family_sha256: str = Field(min_length=64, max_length=64)
    pronunciation_family_sha256: str = Field(min_length=64, max_length=64)
    member_names: tuple[
        Literal[
            "hangul-v2.json",
            "pronunciation-i-plus-1-v2.json",
            "korean-foundations-v2-curation.json",
            "korean-foundations-v2-media.json",
        ],
        ...,
    ] = Field(min_length=4, max_length=4)
    bundle_sha256: str = Field(min_length=64, max_length=64)
    bundle_relpath: str = Field(min_length=1, max_length=256)
    pointer_relpath: Literal["current-candidate.json"] = "current-candidate.json"
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "selected_draft_manifest_sha256",
        "validation_report_sha256",
        "hangul_family_sha256",
        "pronunciation_family_sha256",
        "bundle_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "candidate hash"),
        )

    @model_validator(mode="after")
    def bundle_plan_must_be_exact_and_self_hashed(self) -> Self:
        if self.member_names != _CANDIDATE_MEMBER_NAMES:
            raise ValueError("candidate bundle member names do not match")
        if self.bundle_relpath != f"candidate-bundles/{self.bundle_sha256}":
            raise ValueError("candidate bundle relpath does not match hash")
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("candidate bundle plan content hash does not match")
        return self


class KoreanFoundationCandidateBundleMember(_FrozenDraftModel):
    name: Literal[
        "hangul-v2.json",
        "pronunciation-i-plus-1-v2.json",
        "korean-foundations-v2-curation.json",
        "korean-foundations-v2-media.json",
    ]
    sha256: str = Field(min_length=64, max_length=64)

    @field_validator("sha256")
    @classmethod
    def sha256_must_be_hash(cls, value: str) -> str:
        return _sha256_text(value, field_name="candidate member hash")


class KoreanFoundationCandidateBundleManifest(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    bundle_version: Literal["korean-foundations-v2-candidate-bundle-v1"]
    selected_draft_manifest_sha256: str = Field(min_length=64, max_length=64)
    draft_validation_sha256: str = Field(min_length=64, max_length=64)
    candidate_only: Literal[True] = True
    review_status: Literal["needs_review"] = "needs_review"
    promotion_authority: Literal[False] = False
    total_record_count: Literal[139]
    hangul_record_count: Literal[92]
    pronunciation_record_count: Literal[47]
    media_slot_count: Literal[509]
    members: tuple[KoreanFoundationCandidateBundleMember, ...] = Field(
        min_length=4,
        max_length=4,
    )
    bundle_sha256: str = Field(min_length=64, max_length=64)

    @field_validator(
        "selected_draft_manifest_sha256",
        "draft_validation_sha256",
        "bundle_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "candidate bundle hash"),
        )

    @model_validator(mode="after")
    def manifest_must_bind_exact_members(self) -> Self:
        if tuple(member.name for member in self.members) != _CANDIDATE_MEMBER_NAMES:
            raise ValueError("candidate bundle members do not match")
        payload = self.model_dump(mode="json")
        payload.pop("bundle_sha256", None)
        if self.bundle_sha256 != korean_canonical_json_sha256(payload):
            raise ValueError("candidate bundle hash does not match")
        return self


class KoreanFoundationCandidatePointer(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    bundle_sha256: str = Field(min_length=64, max_length=64)
    bundle_relpath: str = Field(min_length=1, max_length=256)
    bundle_manifest_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("bundle_sha256", "bundle_manifest_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "candidate pointer hash"),
        )

    @model_validator(mode="after")
    def relpath_must_match_bundle(self) -> Self:
        if self.bundle_relpath != f"candidate-bundles/{self.bundle_sha256}":
            raise ValueError("candidate pointer relpath does not match bundle")
        return self


class KoreanFoundationCandidatePublication(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    status: Literal["candidate_published"] = "candidate_published"
    selected_draft_manifest_sha256: str = Field(min_length=64, max_length=64)
    bundle_sha256: str = Field(min_length=64, max_length=64)
    bundle_relpath: str = Field(min_length=1, max_length=256)
    bundle_manifest_sha256: str = Field(min_length=64, max_length=64)
    member_names: tuple[
        Literal[
            "hangul-v2.json",
            "pronunciation-i-plus-1-v2.json",
            "korean-foundations-v2-curation.json",
            "korean-foundations-v2-media.json",
        ],
        ...,
    ] = Field(min_length=4, max_length=4)
    total_record_count: Literal[139]
    media_slot_count: Literal[509]
    candidate_only: Literal[True] = True
    review_status: Literal["needs_review"] = "needs_review"
    promotion_authority: Literal[False] = False
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "selected_draft_manifest_sha256",
        "bundle_sha256",
        "bundle_manifest_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "candidate publication hash"),
        )

    @model_validator(mode="after")
    def publication_must_match_fixed_contract(self) -> Self:
        if self.member_names != _CANDIDATE_MEMBER_NAMES:
            raise ValueError("candidate publication member names do not match")
        if self.bundle_relpath != f"candidate-bundles/{self.bundle_sha256}":
            raise ValueError("candidate publication relpath does not match")
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("candidate publication content hash does not match")
        return self


class KoreanFoundationReviewRequestsResult(_FrozenDraftModel):
    schema_version: Literal[1] = 1
    status: Literal["review_requests_ready"] = "review_requests_ready"
    candidate_bundle_sha256: str = Field(min_length=64, max_length=64)
    candidate_bundle_manifest_sha256: str = Field(min_length=64, max_length=64)
    curriculum_request_sha256: str = Field(min_length=64, max_length=64)
    audio_playback_request_sha256: str = Field(min_length=64, max_length=64)
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "candidate_bundle_sha256",
        "candidate_bundle_manifest_sha256",
        "curriculum_request_sha256",
        "audio_playback_request_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "review request hash"),
        )

    @model_validator(mode="after")
    def result_must_be_self_hashed(self) -> Self:
        if self.content_hash != korean_draft_content_hash(self):
            raise ValueError("review requests result content hash does not match")
        return self


class KoreanFoundationAICurationReasonCode(str, Enum):
    ARTIFACT_MISSING = "artifact_missing"
    ARTIFACT_OVERSIZED = "artifact_oversized"
    ARTIFACT_MALFORMED = "artifact_malformed"
    ARTIFACT_INVALID = "artifact_invalid"
    ARTIFACT_BINDING_MISMATCH = "artifact_binding_mismatch"
    SELECTION_MISSING = "selection_missing"
    SELECTION_INVALID = "selection_invalid"
    SELECTION_MISMATCH = "selection_mismatch"
    STRUCTURAL_DIFF = "structural_diff"
    CANDIDATE_BUNDLE_CONFLICT = "candidate_bundle_conflict"
    CANDIDATE_POINTER_CONFLICT = "candidate_pointer_conflict"
    CANDIDATE_POINTER_MISSING = "candidate_pointer_missing"
    CANDIDATE_POINTER_INVALID = "candidate_pointer_invalid"
    REVIEW_REQUEST_MISMATCH = "review_request_mismatch"
    REVIEW_REQUEST_UNSAFE_PATH = "review_request_unsafe_path"
    ATOMIC_WRITE_FAILED = "atomic_write_failed"


class KoreanFoundationAICurationError(ValueError):
    """A controlled failure that does not include draft learner content."""

    def __init__(
        self,
        reason_code: KoreanFoundationAICurationReasonCode,
        *,
        failures: tuple[str, ...] = (),
    ) -> None:
        self.reason_code = reason_code
        self.failures = failures
        super().__init__(reason_code.value)


def _coerce_family(family: KoreanFoundationFamily | str) -> KoreanFoundationFamily:
    try:
        return KoreanFoundationFamily(family)
    except ValueError as exc:
        raise ValueError("unsupported Korean foundation family") from exc


def _artifact_binding(
    *,
    artifact_id: str,
    content_hash: str,
    stages: tuple[str, ...],
    records: tuple[KoreanFoundationDraftRecord, ...],
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "content_hash": content_hash,
        "record_count": len(records),
        "stages": stages,
        "proposal_count": sum(len(record.proposals) for record in records),
        "uncertainty_count": sum(len(record.uncertainties) for record in records),
        "disagreement_count": sum(len(record.disagreements) for record in records),
    }


def assemble_korean_foundation_family_draft(
    family: KoreanFoundationFamily | str,
    batches: tuple[KoreanFoundationBatchDraft, ...],
) -> KoreanFoundationFamilyDraft:
    """Assemble one complete family from exactly three validated batch drafts."""

    normalized_family = _coerce_family(family)
    expected_batch_ids = tuple(
        batch_id
        for batch_id, batch_family in _BATCH_FAMILIES.items()
        if batch_family is normalized_family
    )
    if tuple(batch.batch_id for batch in batches) != expected_batch_ids:
        raise ValueError("family assembly batch identity does not match")
    if any(batch.source.family is not normalized_family for batch in batches):
        raise ValueError("family assembly source does not match")
    source = batches[0].source
    if any(batch.source != source for batch in batches[1:]):
        raise ValueError("family assembly source bindings differ")
    records = tuple(record for batch in batches for record in batch.records)
    payload: dict[str, object] = {
        "schema_version": 1,
        "family": normalized_family,
        "draft_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "source": source,
        "batch_bindings": [
            _artifact_binding(
                artifact_id=batch.batch_id,
                content_hash=batch.content_hash,
                stages=batch.stages,
                records=batch.records,
            )
            for batch in batches
        ],
        "records": records,
    }
    payload["content_hash"] = korean_draft_content_hash(payload)
    return KoreanFoundationFamilyDraft.model_validate(payload)


def assemble_korean_foundation_draft_manifest(
    families: tuple[KoreanFoundationFamilyDraft, ...],
    batches: tuple[KoreanFoundationBatchDraft, ...],
) -> KoreanFoundationDraftManifest:
    """Bind the exact two family drafts and six batch drafts without authority."""

    if tuple(family.family for family in families) != (
        KoreanFoundationFamily.HANGUL,
        KoreanFoundationFamily.PRONUNCIATION,
    ):
        raise ValueError("draft manifest family order does not match")
    if tuple(batch.batch_id for batch in batches) != tuple(_BATCH_STAGES):
        raise ValueError("draft manifest batch order does not match")
    family_ids = {
        KoreanFoundationFamily.HANGUL: "hangul-v2-draft",
        KoreanFoundationFamily.PRONUNCIATION: "pronunciation-i-plus-1-v2-draft",
    }
    family_bindings = [
        _artifact_binding(
            artifact_id=family_ids[family.family],
            content_hash=family.content_hash,
            stages=tuple(dict.fromkeys(record.stage_id for record in family.records)),
            records=family.records,
        )
        for family in families
    ]
    batch_bindings = [
        _artifact_binding(
            artifact_id=batch.batch_id,
            content_hash=batch.content_hash,
            stages=batch.stages,
            records=batch.records,
        )
        for batch in batches
    ]
    payload: dict[str, object] = {
        "schema_version": 1,
        "manifest_version": "korean-foundations-v2-draft",
        "draft_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "family_bindings": family_bindings,
        "batch_bindings": batch_bindings,
        "total_record_count": 139,
        "proposal_count": sum(
            int(binding["proposal_count"]) for binding in family_bindings
        ),
        "uncertainty_count": sum(
            int(binding["uncertainty_count"]) for binding in family_bindings
        ),
        "disagreement_count": sum(
            int(binding["disagreement_count"]) for binding in family_bindings
        ),
    }
    payload["content_hash"] = korean_draft_content_hash(payload)
    return KoreanFoundationDraftManifest.model_validate(payload)


def _json_bytes(model: BaseModel) -> bytes:
    return (
        json.dumps(
            model.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


_ALLOWED_WRITE_PATHS = frozenset(
    {
        *_PROJECTION_PATHS.values(),
        *_FAMILY_DRAFT_PATHS.values(),
        _DRAFT_MANIFEST_PATH,
    }
)


def _atomic_write_json(path: Path, model: BaseModel) -> None:
    if path not in _ALLOWED_WRITE_PATHS:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        )
    raw = _json_bytes(model)
    if (
        isinstance(model, KoreanFoundationBatchProjection)
        and len(raw) > KOREAN_FOUNDATION_PROJECTION_MAX_BYTES
    ):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_OVERSIZED
        )
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = -1
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


_ModelT = type[BaseModel]


def _read_fixed_model(path: Path, model_type: _ModelT) -> BaseModel:
    try:
        size = path.stat().st_size
        if size > 1_048_576:
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.ARTIFACT_OVERSIZED
            )
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except KoreanFoundationAICurationError:
        raise
    except FileNotFoundError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_MISSING
        ) from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_MALFORMED
        ) from exc
    try:
        return model_type.model_validate(payload)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_INVALID
        ) from exc


def _load_fixed_batch_draft(batch_id: str) -> KoreanFoundationBatchDraft:
    if batch_id not in _BATCH_DRAFT_PATHS:
        raise ValueError("unsupported Korean foundation curation batch")
    return KoreanFoundationBatchDraft.model_validate(
        _read_fixed_model(_BATCH_DRAFT_PATHS[batch_id], KoreanFoundationBatchDraft)
    )


def _load_fixed_family_draft(
    family: KoreanFoundationFamily | str,
) -> KoreanFoundationFamilyDraft:
    normalized_family = _coerce_family(family)
    return KoreanFoundationFamilyDraft.model_validate(
        _read_fixed_model(
            _FAMILY_DRAFT_PATHS[normalized_family],
            KoreanFoundationFamilyDraft,
        )
    )


def _load_fixed_draft_manifest() -> KoreanFoundationDraftManifest:
    return KoreanFoundationDraftManifest.model_validate(
        _read_fixed_model(_DRAFT_MANIFEST_PATH, KoreanFoundationDraftManifest)
    )


def write_korean_foundation_batch_projection(
    batch_id: KoreanFoundationBatchId,
) -> KoreanFoundationBatchProjection:
    projection = build_korean_foundation_batch_projection(batch_id)
    _atomic_write_json(_PROJECTION_PATHS[batch_id], projection)
    return projection


def validate_korean_foundation_batch_draft(
    batch_id: KoreanFoundationBatchId,
) -> KoreanFoundationBatchDraft:
    """Validate one exact fixed batch draft without writing."""

    return _load_fixed_batch_draft(batch_id)


def write_korean_foundation_family_draft(
    family: KoreanFoundationFamily | str,
) -> KoreanFoundationFamilyDraft:
    normalized_family = _coerce_family(family)
    batches = tuple(
        _load_fixed_batch_draft(batch_id)
        for batch_id, batch_family in _BATCH_FAMILIES.items()
        if batch_family is normalized_family
    )
    draft = assemble_korean_foundation_family_draft(normalized_family, batches)
    _atomic_write_json(_FAMILY_DRAFT_PATHS[normalized_family], draft)
    return draft


def write_korean_foundation_draft_manifest() -> KoreanFoundationDraftManifest:
    batches = tuple(_load_fixed_batch_draft(batch_id) for batch_id in _BATCH_STAGES)
    families = tuple(
        _load_fixed_family_draft(family)
        for family in (
            KoreanFoundationFamily.HANGUL,
            KoreanFoundationFamily.PRONUNCIATION,
        )
    )
    manifest = assemble_korean_foundation_draft_manifest(families, batches)
    _atomic_write_json(_DRAFT_MANIFEST_PATH, manifest)
    return manifest


def validate_korean_foundation_drafts() -> KoreanFoundationDraftValidationReport:
    """Validate all fixed drafts and cross-bindings without any write operation."""

    failures: list[str] = []
    loaded_batches: list[KoreanFoundationBatchDraft] = []
    for batch_id in _BATCH_STAGES:
        try:
            loaded_batches.append(_load_fixed_batch_draft(batch_id))
        except KoreanFoundationAICurationError as exc:
            failures.append(f"batch:{batch_id}:{exc.reason_code.value}")

    loaded_families: list[KoreanFoundationFamilyDraft] = []
    for family in (
        KoreanFoundationFamily.HANGUL,
        KoreanFoundationFamily.PRONUNCIATION,
    ):
        try:
            loaded_families.append(_load_fixed_family_draft(family))
        except KoreanFoundationAICurationError as exc:
            failures.append(f"family:{family.value}:{exc.reason_code.value}")

    manifest: KoreanFoundationDraftManifest | None = None
    try:
        manifest = _load_fixed_draft_manifest()
    except KoreanFoundationAICurationError as exc:
        failures.append(f"manifest:{exc.reason_code.value}")
    if failures:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_INVALID,
            failures=tuple(failures),
        )

    batches = tuple(loaded_batches)
    families = tuple(loaded_families)
    assert manifest is not None
    expected_families = tuple(
        assemble_korean_foundation_family_draft(
            family,
            tuple(
                batch
                for batch in batches
                if _BATCH_FAMILIES[batch.batch_id] is family
            ),
        )
        for family in (
            KoreanFoundationFamily.HANGUL,
            KoreanFoundationFamily.PRONUNCIATION,
        )
    )
    expected_manifest = assemble_korean_foundation_draft_manifest(
        expected_families,
        batches,
    )
    if families != expected_families or manifest != expected_manifest:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "valid",
        "draft_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "validated_batch_count": 6,
        "validated_family_count": 2,
        "validated_record_count": 139,
        "draft_manifest_hash": manifest.content_hash,
    }
    payload["content_hash"] = korean_draft_content_hash(payload)
    return KoreanFoundationDraftValidationReport.model_validate(payload)


def _load_selected_draft_manifest_sha256() -> str:
    try:
        handoff = KoreanFoundationCurationSelectionHandoff.model_validate(
            _read_fixed_model(
                _CURATION_SELECTION_HANDOFF_PATH,
                KoreanFoundationCurationSelectionHandoff,
            )
        )
    except KoreanFoundationAICurationError as exc:
        reason = (
            KoreanFoundationAICurationReasonCode.SELECTION_MISSING
            if exc.reason_code is KoreanFoundationAICurationReasonCode.ARTIFACT_MISSING
            else KoreanFoundationAICurationReasonCode.SELECTION_INVALID
        )
        raise KoreanFoundationAICurationError(reason) from exc
    return handoff.selected_sha256


def _candidate_bundle_sha256(payload: dict[str, object]) -> str:
    return korean_canonical_json_sha256(payload)


def check_korean_foundation_curation_selection(
    *,
    expected_draft_manifest_sha256: str | None = None,
) -> KoreanFoundationCandidateBundlePlan:
    """Validate the selected draft hash and derive a no-write candidate plan."""

    expected_hash = (
        _sha256_text(
            expected_draft_manifest_sha256,
            field_name="expected draft manifest hash",
        )
        if expected_draft_manifest_sha256 is not None
        else None
    )
    selected_hash = _load_selected_draft_manifest_sha256()
    if expected_hash is not None and selected_hash != expected_hash:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.SELECTION_MISMATCH
        )

    validation = validate_korean_foundation_drafts()
    if selected_hash != validation.draft_manifest_hash:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.SELECTION_MISMATCH
        )
    manifest = _load_fixed_draft_manifest()
    if manifest.content_hash != selected_hash:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.SELECTION_MISMATCH
        )
    hangul = _load_fixed_family_draft(KoreanFoundationFamily.HANGUL)
    pronunciation = _load_fixed_family_draft(KoreanFoundationFamily.PRONUNCIATION)
    if (len(hangul.records), len(pronunciation.records)) != (92, 47):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.STRUCTURAL_DIFF
        )
    if any(binding.record_count <= 0 for binding in manifest.batch_bindings):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.STRUCTURAL_DIFF
        )

    bundle_seed: dict[str, object] = {
        "bundle_contract_version": "korean-foundations-v2-candidate-bundle-plan-v1",
        "selected_draft_manifest_sha256": selected_hash,
        "validation_report_sha256": validation.content_hash,
        "hangul_family_sha256": hangul.content_hash,
        "pronunciation_family_sha256": pronunciation.content_hash,
        "member_names": list(_CANDIDATE_MEMBER_NAMES),
        "pointer_relpath": "current-candidate.json",
    }
    bundle_sha256 = _candidate_bundle_sha256(bundle_seed)
    payload: dict[str, object] = {
        "schema_version": 1,
        **bundle_seed,
        "member_names": _CANDIDATE_MEMBER_NAMES,
        "bundle_sha256": bundle_sha256,
        "bundle_relpath": f"candidate-bundles/{bundle_sha256}",
    }
    payload["content_hash"] = korean_draft_content_hash(payload)
    return KoreanFoundationCandidateBundlePlan.model_validate(payload)


def _plain_json_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _rehashed_payload(payload: dict[str, Any], *, hash_field: str = "content_hash") -> dict[str, Any]:
    payload = dict(payload)
    payload.pop(hash_field, None)
    payload[hash_field] = korean_canonical_json_sha256(payload)
    return payload


def _proposal_values(record: KoreanFoundationDraftRecord) -> dict[str, str]:
    return {proposal.field_name: proposal.value for proposal in record.proposals}


def _apply_family_draft_to_source_pack(
    family: KoreanFoundationFamily,
    draft: KoreanFoundationFamilyDraft,
) -> KoreanHangulSourcePack | KoreanPronunciationSourcePack:
    _, source_pack = _load_fixed_source_pack(family)
    pack_payload = source_pack.model_dump(mode="json")
    version = "hangul-v2" if family is KoreanFoundationFamily.HANGUL else "pronunciation-i-plus-1-v2"
    pack_payload["source_pack_version"] = version
    entries: list[dict[str, Any]] = []
    for source_entry, draft_record in zip(source_pack.entries, draft.records, strict=True):
        if (
            source_entry.item_key != draft_record.item_key
            or source_entry.sequence != draft_record.sequence
            or source_entry.stage_id != draft_record.stage_id
            or source_entry.content_hash != draft_record.source_entry_content_hash
        ):
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.STRUCTURAL_DIFF
            )
        entry_payload = source_entry.model_dump(mode="json")
        entry_payload["source_pack_version"] = version
        proposals = _proposal_values(draft_record)
        if family is KoreanFoundationFamily.HANGUL:
            for field_name in ("reading_or_name", "sound", "mnemonic"):
                if field_name in proposals:
                    entry_payload[field_name] = proposals[field_name]
        else:
            for field_name in (
                "spellings",
                "sound",
                "example_word",
                "word_translation",
                "example_sentence",
                "sentence_translation",
            ):
                if field_name in proposals:
                    entry_payload[field_name] = proposals[field_name]
            evidence = dict(entry_payload["pronunciation_evidence"])
            if "example_word" in proposals:
                evidence["canonical_spelling"] = proposals["example_word"]
            if "normative_pronunciation" in proposals:
                evidence["normative_pronunciation"] = proposals["normative_pronunciation"]
            if "surface_pronunciation" in proposals:
                evidence["surface_pronunciation"] = proposals["surface_pronunciation"]
            if "ipa" in proposals:
                evidence["ipa"] = proposals["ipa"]
            entry_payload["pronunciation_evidence"] = evidence
        entries.append(_rehashed_payload(entry_payload))
    pack_payload["entries"] = entries
    pack_payload = _rehashed_payload(pack_payload)
    model_type = (
        KoreanHangulSourcePack
        if family is KoreanFoundationFamily.HANGUL
        else KoreanPronunciationSourcePack
    )
    return model_type.model_validate(pack_payload)


def _load_json_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_INVALID
        ) from exc
    if not isinstance(payload, dict):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_INVALID
        )
    return payload


def _entry_hash_by_key(
    pack: KoreanHangulSourcePack | KoreanPronunciationSourcePack,
) -> dict[str, str]:
    return {entry.item_key: entry.content_hash for entry in pack.entries}


def _v2_curation_payload(
    *,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
) -> dict[str, Any]:
    payload = _load_json_payload(_FOUNDATION_V1_CURATION_PATH)
    entry_hashes = {**_entry_hash_by_key(hangul), **_entry_hash_by_key(pronunciation)}
    payload["manifest_version"] = "korean-foundations-v2-curation"
    payload["candidate_only"] = True
    payload["hangul_source_pack_version"] = hangul.source_pack_version
    payload["hangul_source_pack_sha256"] = hangul.content_hash
    payload["pronunciation_source_pack_version"] = pronunciation.source_pack_version
    payload["pronunciation_source_pack_sha256"] = pronunciation.content_hash
    records = []
    for record in payload["records"]:
        updated = dict(record)
        family = KoreanFoundationFamily(updated["family"])
        updated["source_pack_version"] = (
            hangul.source_pack_version
            if family is KoreanFoundationFamily.HANGUL
            else pronunciation.source_pack_version
        )
        updated["source_content_sha256"] = entry_hashes[updated["item_key"]]
        records.append(updated)
    payload["records"] = records
    return _rehashed_payload(payload)


def _v2_media_payload(
    *,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
) -> dict[str, Any]:
    payload = _load_json_payload(_FOUNDATION_V1_MEDIA_PATH)
    entry_hashes = {**_entry_hash_by_key(hangul), **_entry_hash_by_key(pronunciation)}
    payload["manifest_version"] = "korean-foundations-v2-media"
    payload["candidate_only"] = True
    payload["hangul_source_pack_version"] = hangul.source_pack_version
    payload["hangul_source_pack_sha256"] = hangul.content_hash
    payload["pronunciation_source_pack_version"] = pronunciation.source_pack_version
    payload["pronunciation_source_pack_sha256"] = pronunciation.content_hash
    slots = []
    for slot in payload["slots"]:
        updated = dict(slot)
        family = KoreanFoundationFamily(updated["family"])
        updated["source_pack_version"] = (
            hangul.source_pack_version
            if family is KoreanFoundationFamily.HANGUL
            else pronunciation.source_pack_version
        )
        updated["source_content_sha256"] = entry_hashes[updated["item_key"]]
        slots.append(updated)
    payload["slots"] = slots
    return _rehashed_payload(payload)


def _build_candidate_bundle_payloads() -> tuple[
    KoreanFoundationCandidateBundleManifest,
    dict[str, bytes],
    bytes,
]:
    plan = check_korean_foundation_curation_selection()
    hangul_draft = _load_fixed_family_draft(KoreanFoundationFamily.HANGUL)
    pronunciation_draft = _load_fixed_family_draft(KoreanFoundationFamily.PRONUNCIATION)
    hangul = _apply_family_draft_to_source_pack(
        KoreanFoundationFamily.HANGUL,
        hangul_draft,
    )
    pronunciation = _apply_family_draft_to_source_pack(
        KoreanFoundationFamily.PRONUNCIATION,
        pronunciation_draft,
    )
    member_payloads = {
        "hangul-v2.json": hangul.model_dump(mode="json"),
        "pronunciation-i-plus-1-v2.json": pronunciation.model_dump(mode="json"),
        "korean-foundations-v2-curation.json": _v2_curation_payload(
            hangul=hangul,
            pronunciation=pronunciation,
        ),
        "korean-foundations-v2-media.json": _v2_media_payload(
            hangul=hangul,
            pronunciation=pronunciation,
        ),
    }
    member_bytes = {
        name: _plain_json_bytes(member_payloads[name]) for name in _CANDIDATE_MEMBER_NAMES
    }
    members = tuple(
        KoreanFoundationCandidateBundleMember(
            name=name,
            sha256=sha256(member_bytes[name]).hexdigest(),
        )
        for name in _CANDIDATE_MEMBER_NAMES
    )
    manifest_payload: dict[str, object] = {
        "schema_version": 1,
        "bundle_version": "korean-foundations-v2-candidate-bundle-v1",
        "selected_draft_manifest_sha256": plan.selected_draft_manifest_sha256,
        "draft_validation_sha256": plan.validation_report_sha256,
        "candidate_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "total_record_count": 139,
        "hangul_record_count": 92,
        "pronunciation_record_count": 47,
        "media_slot_count": len(member_payloads["korean-foundations-v2-media.json"]["slots"]),
        "members": [member.model_dump(mode="json") for member in members],
    }
    manifest_payload["bundle_sha256"] = korean_canonical_json_sha256(manifest_payload)
    manifest = KoreanFoundationCandidateBundleManifest.model_validate(manifest_payload)
    return manifest, member_bytes, _plain_json_bytes(manifest.model_dump(mode="json"))


def _candidate_publication(
    *,
    manifest: KoreanFoundationCandidateBundleManifest,
    manifest_bytes: bytes,
) -> KoreanFoundationCandidatePublication:
    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "candidate_published",
        "selected_draft_manifest_sha256": manifest.selected_draft_manifest_sha256,
        "bundle_sha256": manifest.bundle_sha256,
        "bundle_relpath": f"candidate-bundles/{manifest.bundle_sha256}",
        "bundle_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "member_names": _CANDIDATE_MEMBER_NAMES,
        "total_record_count": 139,
        "media_slot_count": manifest.media_slot_count,
        "candidate_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
    }
    payload["content_hash"] = korean_draft_content_hash(payload)
    return KoreanFoundationCandidatePublication.model_validate(payload)


def _path_is_link_or_reparse(value: os.stat_result) -> bool:
    if stat.S_ISLNK(value.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(value, "st_file_attributes", 0) & reparse_flag)


def _ensure_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        value = path.lstat()
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        ) from exc
    if _path_is_link_or_reparse(value) or not stat.S_ISDIR(value.st_mode):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        )


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _write_file(path: Path, raw: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _bundle_matches(
    path: Path,
    *,
    manifest: KoreanFoundationCandidateBundleManifest,
    member_bytes: dict[str, bytes],
    manifest_bytes: bytes,
) -> bool:
    try:
        path_stat = path.lstat()
    except OSError:
        return False
    if _path_is_link_or_reparse(path_stat) or not stat.S_ISDIR(path_stat.st_mode):
        return False
    expected_names = {"bundle-manifest.json", *_CANDIDATE_MEMBER_NAMES}
    actual_names = {child.name for child in path.iterdir()}
    if actual_names != expected_names:
        return False
    if (path / "bundle-manifest.json").read_bytes() != manifest_bytes:
        return False
    return all((path / name).read_bytes() == member_bytes[name] for name in _CANDIDATE_MEMBER_NAMES)


def _write_candidate_bundle(
    *,
    manifest: KoreanFoundationCandidateBundleManifest,
    member_bytes: dict[str, bytes],
    manifest_bytes: bytes,
) -> Path:
    _ensure_directory(KOREAN_FOUNDATION_CANDIDATE_ROOT)
    _ensure_directory(KOREAN_FOUNDATION_CANDIDATE_BUNDLE_ROOT)
    target = KOREAN_FOUNDATION_CANDIDATE_BUNDLE_ROOT / manifest.bundle_sha256
    if target.exists():
        if _bundle_matches(
            target,
            manifest=manifest,
            member_bytes=member_bytes,
            manifest_bytes=manifest_bytes,
        ):
            return target
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_BUNDLE_CONFLICT
        )
    stage_name = tempfile.mkdtemp(
        prefix=f".{manifest.bundle_sha256}.",
        suffix=".tmp",
        dir=KOREAN_FOUNDATION_CANDIDATE_BUNDLE_ROOT,
    )
    stage = Path(stage_name)
    try:
        for name in _CANDIDATE_MEMBER_NAMES:
            _write_file(stage / name, member_bytes[name])
        _write_file(stage / "bundle-manifest.json", manifest_bytes)
        _fsync_directory(stage)
        os.replace(stage, target)
        _fsync_directory(KOREAN_FOUNDATION_CANDIDATE_BUNDLE_ROOT)
    except KoreanFoundationAICurationError:
        raise
    except OSError as exc:
        if target.exists() and _bundle_matches(
            target,
            manifest=manifest,
            member_bytes=member_bytes,
            manifest_bytes=manifest_bytes,
        ):
            shutil.rmtree(stage, ignore_errors=True)
            return target
        if target.exists():
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.CANDIDATE_BUNDLE_CONFLICT
            ) from exc
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        ) from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    return target


def _pointer_bytes(publication: KoreanFoundationCandidatePublication) -> bytes:
    pointer = KoreanFoundationCandidatePointer(
        schema_version=1,
        bundle_sha256=publication.bundle_sha256,
        bundle_relpath=publication.bundle_relpath,
        bundle_manifest_sha256=publication.bundle_manifest_sha256,
    )
    return _plain_json_bytes(pointer.model_dump(mode="json"))


def _atomic_replace_candidate_pointer(raw: bytes) -> None:
    _ensure_directory(KOREAN_FOUNDATION_CANDIDATE_ROOT)
    pointer_path = _CURRENT_CANDIDATE_POINTER_PATH
    try:
        pointer_stat = pointer_path.lstat()
    except FileNotFoundError:
        pointer_stat = None
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
        ) from exc
    if pointer_stat is not None:
        if _path_is_link_or_reparse(pointer_stat) or not stat.S_ISREG(
            pointer_stat.st_mode
        ):
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
            )
        try:
            existing = pointer_path.read_bytes()
        except OSError as exc:
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
            ) from exc
        if existing == raw:
            return
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_CONFLICT
        )
    descriptor = -1
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".current-candidate.",
            suffix=".tmp",
            dir=KOREAN_FOUNDATION_CANDIDATE_ROOT,
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_name, pointer_path)
        except FileExistsError as exc:
            try:
                pointer_stat = pointer_path.lstat()
                if _path_is_link_or_reparse(pointer_stat) or not stat.S_ISREG(
                    pointer_stat.st_mode
                ):
                    raise KoreanFoundationAICurationError(
                        KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
                    ) from exc
                existing = pointer_path.read_bytes()
            except KoreanFoundationAICurationError:
                raise
            except OSError as read_exc:
                raise KoreanFoundationAICurationError(
                    KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
                ) from read_exc
            if existing == raw:
                return
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_CONFLICT
            ) from exc
        os.unlink(temporary_name)
        temporary_name = None
        _fsync_directory(KOREAN_FOUNDATION_CANDIDATE_ROOT)
    except KoreanFoundationAICurationError:
        raise
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def promote_korean_foundation_curation_selection(
    *,
    expected_draft_manifest_sha256: str,
) -> KoreanFoundationCandidatePublication:
    expected = _sha256_text(
        expected_draft_manifest_sha256,
        field_name="expected draft manifest hash",
    )
    manifest, member_bytes, manifest_bytes = _build_candidate_bundle_payloads()
    if manifest.selected_draft_manifest_sha256 != expected:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.SELECTION_MISMATCH
        )
    publication = _candidate_publication(
        manifest=manifest,
        manifest_bytes=manifest_bytes,
    )
    pointer_raw = _pointer_bytes(publication)
    if _CURRENT_CANDIDATE_POINTER_PATH.exists() and (
        _CURRENT_CANDIDATE_POINTER_PATH.read_bytes() != pointer_raw
    ):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_CONFLICT
        )
    _write_candidate_bundle(
        manifest=manifest,
        member_bytes=member_bytes,
        manifest_bytes=manifest_bytes,
    )
    _atomic_replace_candidate_pointer(pointer_raw)
    return verify_promoted_korean_foundation_candidate(
        expected_draft_manifest_sha256=expected,
    )


def _read_candidate_pointer() -> KoreanFoundationCandidatePointer:
    try:
        pointer_stat = _CURRENT_CANDIDATE_POINTER_PATH.lstat()
    except FileNotFoundError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_MISSING
        ) from exc
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
        ) from exc
    if _path_is_link_or_reparse(pointer_stat) or not stat.S_ISREG(pointer_stat.st_mode):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
        )
    try:
        payload = json.loads(_CURRENT_CANDIDATE_POINTER_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
        ) from exc
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "bundle_sha256",
        "bundle_relpath",
        "bundle_manifest_sha256",
    }:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
        )
    try:
        return KoreanFoundationCandidatePointer.model_validate(payload)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
        ) from exc


def read_current_korean_foundation_candidate() -> KoreanFoundationCandidatePublication:
    pointer = _read_candidate_pointer()
    bundle_root = KOREAN_FOUNDATION_CANDIDATE_ROOT / pointer.bundle_relpath
    try:
        manifest_bytes = (bundle_root / "bundle-manifest.json").read_bytes()
        manifest_payload = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_INVALID
        ) from exc
    if sha256(manifest_bytes).hexdigest() != pointer.bundle_manifest_sha256:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    manifest = KoreanFoundationCandidateBundleManifest.model_validate(manifest_payload)
    if manifest.bundle_sha256 != pointer.bundle_sha256:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    for member in manifest.members:
        try:
            content = (bundle_root / member.name).read_bytes()
        except OSError as exc:
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.ARTIFACT_MISSING
            ) from exc
        if sha256(content).hexdigest() != member.sha256:
            raise KoreanFoundationAICurationError(
                KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
            )
    names = {child.name for child in bundle_root.iterdir()}
    if names != {"bundle-manifest.json", *_CANDIDATE_MEMBER_NAMES}:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    return _candidate_publication(manifest=manifest, manifest_bytes=manifest_bytes)


def verify_promoted_korean_foundation_candidate(
    *,
    expected_draft_manifest_sha256: str,
) -> KoreanFoundationCandidatePublication:
    expected = _sha256_text(
        expected_draft_manifest_sha256,
        field_name="expected draft manifest hash",
    )
    current = read_current_korean_foundation_candidate()
    if current.selected_draft_manifest_sha256 != expected:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.SELECTION_MISMATCH
        )
    return current


def _current_candidate_bundle_payloads() -> tuple[
    KoreanFoundationCandidatePublication,
    Path,
    dict[str, Any],
    dict[str, dict[str, Any]],
]:
    publication = read_current_korean_foundation_candidate()
    bundle_root = KOREAN_FOUNDATION_CANDIDATE_ROOT / publication.bundle_relpath
    manifest = _load_json_payload(bundle_root / "bundle-manifest.json")
    members = {name: _load_json_payload(bundle_root / name) for name in _CANDIDATE_MEMBER_NAMES}
    _validate_current_candidate_projection(publication, manifest, members)
    return publication, bundle_root, manifest, members


def _validate_current_candidate_projection(
    publication: KoreanFoundationCandidatePublication,
    manifest: dict[str, Any],
    members: dict[str, dict[str, Any]],
) -> None:
    if publication.member_names != _CANDIDATE_MEMBER_NAMES:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    if manifest.get("candidate_only") is not True or manifest.get("review_status") != "needs_review":
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    hangul = members["hangul-v2.json"]
    pronunciation = members["pronunciation-i-plus-1-v2.json"]
    curation = members["korean-foundations-v2-curation.json"]
    media = members["korean-foundations-v2-media.json"]
    if (
        hangul.get("source_pack_version") != "hangul-v2"
        or pronunciation.get("source_pack_version") != "pronunciation-i-plus-1-v2"
        or len(hangul.get("entries", ())) != 92
        or len(pronunciation.get("entries", ())) != 47
        or curation.get("manifest_version") != "korean-foundations-v2-curation"
        or curation.get("candidate_only") is not True
        or len(curation.get("records", ())) != 139
        or media.get("manifest_version") != "korean-foundations-v2-media"
        or media.get("candidate_only") is not True
        or len(media.get("slots", ())) != 509
    ):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    if any(
        gate.get("status") != "needs_review"
        or gate.get("reviewer_id") is not None
        or gate.get("reviewed_at") is not None
        or gate.get("reviewed_evidence_sha256") is not None
        for record in curation["records"]
        for gate in record["gates"]
    ):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )
    if any(
        slot.get("status") != "needs_review"
        or slot.get("artifact_sha256") is not None
        or slot.get("source_id") is not None
        or slot.get("review_receipts") != []
        for slot in media["slots"]
    ):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH
        )


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _candidate_request_bindings(
    *,
    publication: KoreanFoundationCandidatePublication,
    bundle_root: Path,
    manifest: dict[str, Any],
    members: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    media_slots = members["korean-foundations-v2-media.json"]["slots"]
    curation_records = members["korean-foundations-v2-curation.json"]["records"]
    bindings: dict[str, Any] = {
        "current-candidate.json": {
            "filename": "current-candidate.json",
            "bundle_sha256": publication.bundle_sha256,
            "bundle_relpath": publication.bundle_relpath,
            "bundle_manifest_sha256": publication.bundle_manifest_sha256,
            "file_sha256": _file_sha256(_CURRENT_CANDIDATE_POINTER_PATH),
        },
        "bundle-manifest.json": {
            "filename": "bundle-manifest.json",
            "bundle_sha256": manifest["bundle_sha256"],
            "selected_draft_manifest_sha256": manifest[
                "selected_draft_manifest_sha256"
            ],
            "draft_validation_sha256": manifest["draft_validation_sha256"],
            "file_sha256": _file_sha256(bundle_root / "bundle-manifest.json"),
            "total_record_count": 139,
            "media_slot_count": 509,
        },
    }
    for name in _CANDIDATE_MEMBER_NAMES:
        payload = members[name]
        version_field = "source_pack_version" if "entries" in payload else "manifest_version"
        binding: dict[str, Any] = {
            "filename": name,
            "version": payload[version_field],
            "canonical_content_sha256": payload["content_hash"],
            "file_sha256": _file_sha256(bundle_root / name),
        }
        if name == "hangul-v2.json":
            binding["item_count"] = 92
        elif name == "pronunciation-i-plus-1-v2.json":
            binding["item_count"] = 47
        elif name == "korean-foundations-v2-curation.json":
            binding["record_count"] = 139
            binding["gate_count"] = sum(
                len(record["gates"]) for record in curation_records
            )
        else:
            binding["asset_count"] = 509
            binding["required_asset_count"] = sum(
                1 for slot in media_slots if slot["required"]
            )
        bindings[name] = binding
    return bindings


def _item_identity_rows(members: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "family": entry["family"],
            "item_key": entry["item_key"],
            "sequence": entry["sequence"],
            "stage_id": entry["stage_id"],
            "category_id": entry["category_id"],
            "source_pack_version": entry["source_pack_version"],
            "source_content_sha256": entry["content_hash"],
            "target_concept_id": entry["evidence"]["target_concept_id"],
            "active_rule_ids": entry["active_rule_ids"],
        }
        for entry in (
            *members["hangul-v2.json"]["entries"],
            *members["pronunciation-i-plus-1-v2.json"]["entries"],
        )
    ]


def _asset_identity_rows(members: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "family",
        "item_key",
        "sequence",
        "slot_id",
        "media_kind",
        "required",
        "source_pack_version",
        "source_content_sha256",
        "basename",
        "storage_relpath",
        "output_format",
    )
    return [
        {field: slot[field] for field in fields}
        for slot in members["korean-foundations-v2-media.json"]["slots"]
    ]


def _source_entry_lookup(
    members: dict[str, dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (entry["family"], entry["item_key"]): entry
        for entry in (
            *members["hangul-v2.json"]["entries"],
            *members["pronunciation-i-plus-1-v2.json"]["entries"],
        )
    }


def _slot_display_text(slot: dict[str, Any], entry: dict[str, Any]) -> str:
    if slot["family"] == "hangul":
        mapping = entry.get("pedagogical_jamo_mapping")
        if mapping is not None:
            return str(mapping["display_glyph"])
        return str(entry["canonical_jamo_or_block"])
    if slot["media_kind"] == "letter_audio":
        return str(entry["spellings"])
    if slot["media_kind"] == "word_audio":
        return str(entry["example_word"])
    return str(entry["example_sentence"])


def _text_binding_rows(members: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    entries = _source_entry_lookup(members)
    rows = []
    for slot in members["korean-foundations-v2-media.json"]["slots"]:
        display_text = _slot_display_text(slot, entries[(slot["family"], slot["item_key"])])
        rows.append(
            {
                "slot_id": slot["slot_id"],
                "display_text": display_text,
                "display_text_sha256": sha256(display_text.encode("utf-8")).hexdigest(),
                "text_nfc": unicodedata.normalize("NFC", display_text),
            }
        )
    return rows


def _curriculum_gate_role_matrix() -> dict[str, list[dict[str, Any]]]:
    return {
        "hangul": [
            {
                "gate_name": "source_content",
                "required_role": "korean-foundation-content-reviewer",
                "scope_ids": [
                    "mapping",
                    "name-or-reading",
                    "block-or-example",
                    "stroke-order",
                    "mnemonic",
                ],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "curriculum_atomicity",
                "required_role": "korean-curriculum-reviewer",
                "scope_ids": [
                    "target-concept",
                    "prerequisites",
                    "observed-concepts",
                    "one-target-unknown",
                ],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "korean_orthography",
                "required_role": "korean-orthography-reviewer",
                "scope_ids": [
                    "canonical-jamo-or-block",
                    "pedagogical-jamo-mapping",
                    "orthographic-example",
                ],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "portuguese",
                "required_role": "portuguese-reviewer",
                "scope_ids": ["learner-facing-portuguese"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
        ],
        "pronunciation": [
            {
                "gate_name": "source_content",
                "required_role": "korean-foundation-content-reviewer",
                "scope_ids": [
                    "spelling",
                    "example-word",
                    "example-sentence",
                    "register-context",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "curriculum_atomicity",
                "required_role": "korean-curriculum-reviewer",
                "scope_ids": [
                    "target-concept",
                    "prerequisites",
                    "active-rules",
                    "one-target-unknown",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "korean_phonetics",
                "required_role": "korean-phonetics-specialist",
                "scope_ids": [
                    "normative-pronunciation",
                    "surface-pronunciation",
                    "optional-ipa",
                    "phonological-rules",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "portuguese",
                "required_role": "portuguese-reviewer",
                "scope_ids": [
                    "word-translation",
                    "sentence-translation",
                    "register-alignment",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
        ],
    }


def _audio_item_gate_role_matrix() -> dict[str, list[dict[str, Any]]]:
    return {
        "hangul": [
            {
                "gate_name": "media_license",
                "required_role": "media-rights-reviewer",
                "scope_ids": ["all-declared-media-rights"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "media_integrity",
                "required_role": "media-integrity-reviewer",
                "scope_ids": ["all-required-media-slots"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "audio_playback",
                "required_role": "audio-playback-reviewer",
                "scope_ids": ["exact-audio-bytes", "heard-playback"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
        ],
        "pronunciation": [
            {
                "gate_name": "media_license",
                "required_role": "media-rights-reviewer",
                "scope_ids": ["all-declared-audio-rights"],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "media_integrity",
                "required_role": "media-integrity-reviewer",
                "scope_ids": ["letter-word-sentence-audio"],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "audio_playback",
                "required_role": "audio-playback-reviewer",
                "scope_ids": ["exact-audio-bytes", "heard-playback"],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
        ],
    }


def _build_curriculum_request_payload(
    bindings: dict[str, Any],
    members: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rows = _item_identity_rows(members)
    hangul_rows = [row for row in rows if row["family"] == "hangul"]
    pronunciation_rows = [row for row in rows if row["family"] == "pronunciation"]
    matrix = _curriculum_gate_role_matrix()
    return {
        "artifact_type": "korean_foundation_curriculum_review_request",
        "schema_version": 1,
        "request_status": "needs_review",
        "request_only": True,
        "evidence_supplied": False,
        "human_checkpoint_count": 0,
        "candidate_bindings": bindings,
        "coverage": {
            "item_count": 139,
            "hangul_item_count": 92,
            "pronunciation_item_count": 47,
            "item_key_selectors": [
                {
                    "family": "hangul",
                    "prefix": "ko-hangul-",
                    "first_sequence": 1,
                    "last_sequence": 92,
                    "zero_pad_width": 4,
                    "count": 92,
                },
                {
                    "family": "pronunciation",
                    "prefix": "ko-pron-",
                    "first_sequence": 1,
                    "last_sequence": 47,
                    "zero_pad_width": 4,
                    "count": 47,
                },
            ],
            "stage_counts": dict(Counter(row["stage_id"] for row in rows)),
            "item_identity_projection": {
                "source_array": "entries",
                "selection": "all",
                "fields": [
                    "family",
                    "item_key",
                    "sequence",
                    "stage_id",
                    "category_id",
                    "source_pack_version",
                    "source_content_sha256",
                    "target_concept_id",
                    "active_rule_ids",
                ],
                "order": "hangul-then-pronunciation-source-order",
                "hash_algorithm": "sha256-utf8-canonical-json",
            },
            "item_key_set_sha256": korean_canonical_json_sha256(
                [[row["family"], row["item_key"]] for row in rows]
            ),
            "item_identity_set_sha256": korean_canonical_json_sha256(rows),
            "hangul_item_identity_sha256": korean_canonical_json_sha256(hangul_rows),
            "pronunciation_item_identity_sha256": korean_canonical_json_sha256(
                pronunciation_rows
            ),
        },
        "gate_role_matrix": matrix,
        "global_decisions": [
            {
                "decision_name": "portuguese_editorial_policy",
                "canonical_language_code": "pt",
                "required_role": "portuguese-reviewer",
                "required_output_field": "regional_editorial_policy",
                "decision_count": 1,
                "status": "needs_review",
            }
        ],
        "additional_role_requirements": [
            {
                "requirement_name": "specialist_atomization",
                "gate_name": "curriculum_atomicity",
                "required_role": "korean-phonetics-specialist",
                "selector": {
                    "family": "pronunciation",
                    "item_keys": [f"ko-pron-{sequence:04d}" for sequence in range(42, 48)],
                    "stages": ["P11", "P12", "P13"],
                    "source_reason_code": "specialist-atomization-review-required",
                },
                "scope_ids": [
                    "P11-P13-atomization",
                    "active-rule-analysis",
                    "rule-ordering",
                ],
                "role_assignment_count": 6,
                "status": "needs_review",
            }
        ],
        "decision_counts": {
            "item_gate_decisions": 556,
            "global_policy_decisions": 1,
            "total_decisions": 557,
            "total_role_assignments": 563,
            "by_required_role": {
                "korean-foundation-content-reviewer": 139,
                "korean-curriculum-reviewer": 139,
                "korean-orthography-reviewer": 92,
                "korean-phonetics-specialist": 53,
                "portuguese-reviewer": 140,
            },
        },
        "future_fixed_evidence_filenames": [
            "proposed-curation.json",
            "curriculum-review.json",
            "reviewers/korean-orthography.json",
            "reviewers/korean-phonetics.json",
            "reviewers/portuguese.json",
        ],
        "high_leverage_traces": [rows[0], rows[-1]],
    }


def _build_audio_request_payload(
    bindings: dict[str, Any],
    members: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    assets = _asset_identity_rows(members)
    slots = members["korean-foundations-v2-media.json"]["slots"]
    text_rows = _text_binding_rows(members)
    audio_kinds = {"audio", "letter_audio", "word_audio", "sentence_audio"}
    decision_matrix = [
        {
            "decision_name": "source_identity",
            "gate_name": "media_license",
            "selector": "all-assets",
            "decision_count": 509,
            "required_role": "media-rights-reviewer",
            "required_evidence_fields": ["source_id", "source_version"],
            "status": "needs_review",
        },
        {
            "decision_name": "attribution",
            "gate_name": "media_license",
            "selector": "all-assets",
            "decision_count": 509,
            "required_role": "media-rights-reviewer",
            "required_evidence_fields": ["attribution"],
            "status": "needs_review",
        },
        {
            "decision_name": "license",
            "gate_name": "media_license",
            "selector": "all-assets",
            "decision_count": 509,
            "required_role": "media-rights-reviewer",
            "required_evidence_fields": ["license_id"],
            "status": "needs_review",
        },
        {
            "decision_name": "reuse",
            "gate_name": "media_license",
            "selector": "all-assets",
            "decision_count": 509,
            "required_role": "media-rights-reviewer",
            "required_evidence_fields": ["reuse_disposition"],
            "status": "needs_review",
        },
        {
            "decision_name": "redistribution",
            "gate_name": "media_license",
            "selector": "all-assets",
            "decision_count": 509,
            "required_role": "media-rights-reviewer",
            "required_evidence_fields": ["redistribution_disposition"],
            "status": "needs_review",
        },
        {
            "decision_name": "exact_byte_integrity",
            "gate_name": "media_integrity",
            "selector": "all-assets",
            "decision_count": 509,
            "required_role": "media-integrity-reviewer",
            "required_evidence_fields": [
                "artifact_sha256",
                "reviewed_artifact_sha256",
                "metadata_sha256",
                "reviewed_metadata_sha256",
                "output_format",
                "duration_ms",
            ],
            "status": "needs_review",
        },
        {
            "decision_name": "exact_spoken_text",
            "gate_name": "audio_playback",
            "selector": "all-audio-assets",
            "decision_count": 233,
            "required_role": "korean-phonetics-specialist",
            "required_evidence_fields": [
                "display_text",
                "display_text_sha256",
                "spoken_text",
                "spoken_text_sha256",
                "text_nfc",
                "text_nfc_sha256",
            ],
            "status": "needs_review",
        },
        {
            "decision_name": "specialist_playback",
            "gate_name": "audio_playback",
            "selector": "all-audio-assets",
            "decision_count": 233,
            "required_role": "korean-phonetics-specialist",
            "required_evidence_fields": [
                "exact_media_version",
                "exact_text_hashes",
                "exact_byte_hash",
                "heard_playback_result",
            ],
            "status": "needs_review",
        },
        {
            "decision_name": "independent_native_playback",
            "gate_name": "audio_playback",
            "selector": "all-audio-assets",
            "decision_count": 233,
            "required_role": "independent-native-speaker",
            "required_evidence_fields": [
                "exact_media_version",
                "exact_text_hashes",
                "exact_byte_hash",
                "heard_playback_result",
            ],
            "status": "needs_review",
        },
        {
            "decision_name": "heard_playback",
            "gate_name": "audio_playback",
            "selector": "all-audio-assets",
            "decision_count": 233,
            "required_role": "audio-playback-reviewer",
            "required_evidence_fields": [
                "exact_media_version",
                "exact_text_hashes",
                "exact_byte_hash",
                "heard_playback_result",
            ],
            "status": "needs_review",
        },
    ]
    return {
        "artifact_type": "korean_foundation_audio_playback_review_request",
        "schema_version": 1,
        "request_status": "needs_review",
        "request_only": True,
        "evidence_supplied": False,
        "human_checkpoint_count": 0,
        "candidate_bindings": bindings,
        "coverage": {
            "asset_count": 509,
            "required_asset_count": 325,
            "optional_asset_count": 184,
            "hangul_asset_count": 368,
            "pronunciation_asset_count": 141,
            "hangul_required_asset_count": 184,
            "pronunciation_required_asset_count": 141,
            "audio_asset_count": 233,
            "non_audio_asset_count": 276,
            "asset_kind_counts": dict(Counter(slot["media_kind"] for slot in slots)),
            "asset_id_selectors": [
                {
                    "family": "hangul",
                    "media_kind": kind,
                    "prefix": f"hangul.{kind}.",
                    "first_sequence": 1,
                    "last_sequence": 92,
                    "zero_pad_width": 4,
                    "count": 92,
                }
                for kind in ("picture", "strokes", "gif", "audio")
            ]
            + [
                {
                    "family": "pronunciation",
                    "media_kind": kind,
                    "prefix": f"pron.{kind.replace('_', '-')}.",
                    "first_sequence": 1,
                    "last_sequence": 47,
                    "zero_pad_width": 4,
                    "count": 47,
                }
                for kind in ("letter_audio", "word_audio", "sentence_audio")
            ],
            "asset_identity_projection": {
                "source_array": "slots",
                "selection": "all",
                "fields": [
                    "family",
                    "item_key",
                    "sequence",
                    "slot_id",
                    "media_kind",
                    "required",
                    "source_pack_version",
                    "source_content_sha256",
                    "basename",
                    "storage_relpath",
                    "output_format",
                ],
                "order": "media-manifest-source-order",
                "hash_algorithm": "sha256-utf8-canonical-json",
            },
            "asset_id_set_sha256": korean_canonical_json_sha256(
                [asset["slot_id"] for asset in assets]
            ),
            "asset_identity_set_sha256": korean_canonical_json_sha256(assets),
            "hangul_asset_identity_sha256": korean_canonical_json_sha256(
                [asset for asset in assets if asset["family"] == "hangul"]
            ),
            "pronunciation_asset_identity_sha256": korean_canonical_json_sha256(
                [asset for asset in assets if asset["family"] == "pronunciation"]
            ),
            "required_asset_identity_sha256": korean_canonical_json_sha256(
                [asset for asset, slot in zip(assets, slots, strict=True) if slot["required"]]
            ),
            "audio_asset_identity_sha256": korean_canonical_json_sha256(
                [
                    asset
                    for asset, slot in zip(assets, slots, strict=True)
                    if slot["media_kind"] in audio_kinds
                ]
            ),
            "text_binding_projection": {
                "hangul": (
                    "pedagogical_jamo_mapping.display_glyph-if-present-else-"
                    "canonical_jamo_or_block"
                ),
                "pronunciation_letter_audio": "spellings",
                "pronunciation_word_audio": "example_word",
                "pronunciation_sentence_audio": "example_sentence",
                "selection": "all-assets",
                "fields": [
                    "slot_id",
                    "display_text",
                    "display_text_sha256",
                    "text_nfc",
                ],
                "hash_algorithm": "sha256-utf8-canonical-json",
            },
            "text_binding_set_sha256": korean_canonical_json_sha256(text_rows),
            "hangul_text_binding_sha256": korean_canonical_json_sha256(text_rows[:368]),
            "pronunciation_text_binding_sha256": korean_canonical_json_sha256(
                text_rows[368:]
            ),
        },
        "item_gate_role_matrix": _audio_item_gate_role_matrix(),
        "asset_role_matrix": {
            "non_audio_assets": {
                "media_kinds": ["picture", "strokes", "gif"],
                "selector": "all-non-audio-assets",
                "asset_count": 276,
                "required_roles": [
                    "media-rights-reviewer",
                    "media-integrity-reviewer",
                ],
            },
            "audio_assets": {
                "media_kinds": [
                    "audio",
                    "letter_audio",
                    "word_audio",
                    "sentence_audio",
                ],
                "selector": "all-audio-assets",
                "asset_count": 233,
                "required_roles": [
                    "media-rights-reviewer",
                    "media-integrity-reviewer",
                    "audio-playback-reviewer",
                    "korean-phonetics-specialist",
                    "independent-native-speaker",
                ],
                "distinct_role_constraints": [
                    [
                        "korean-phonetics-specialist",
                        "independent-native-speaker",
                    ]
                ],
            },
        },
        "decision_matrix": decision_matrix,
        "decision_counts": {
            "item_gate_decisions": 417,
            "asset_decisions": 3986,
            "total_decisions": 4403,
            "unique_item_and_asset_role_bindings": 2134,
            "by_required_role": {
                "media-rights-reviewer": 2684,
                "media-integrity-reviewer": 648,
                "audio-playback-reviewer": 372,
                "korean-phonetics-specialist": 466,
                "independent-native-speaker": 233,
            },
        },
        "future_fixed_evidence_filenames": [
            "proposed-media.json",
            "audio-playback-review.json",
            "rights.json",
            "reviewers/korean-phonetics.json",
            "reviewers/independent-native-speaker.json",
        ],
        "high_leverage_traces": {
            "hangul_first_audio": {
                "asset": assets[3],
                "text_binding": text_rows[3],
            },
            "pronunciation_p13_audio": [
                {"asset": asset, "text_binding": text}
                for asset, text in zip(assets[-3:], text_rows[-3:], strict=True)
            ],
        },
    }


def _review_request_bytes(title: str, intro: str, payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return (
        f"# {title}\n\n"
        f"{intro}\n\n"
        "This is a request contract only. It supplies no human, legal, media, "
        "playback, activation, or export evidence. Every selector applies to "
        "the exact current-candidate bundle and remains scanner-detectable.\n\n"
        "Place future evidence only at the fixed filenames listed in the JSON "
        "contract. There is no source-location importer or alternate filename.\n\n"
        "`review_status=needs_review`\n"
        "`human_checkpoint_count=0`\n\n"
        "```json\n"
        f"{body}"
        "```\n\n"
        "This request selects no approval, regional policy, rights disposition, "
        "spoken-text result, media byte, activation, export, or production state.\n"
    ).encode("utf-8")


def _build_review_request_files() -> tuple[bytes, bytes, KoreanFoundationReviewRequestsResult]:
    publication, bundle_root, manifest, members = _current_candidate_bundle_payloads()
    bindings = _candidate_request_bindings(
        publication=publication,
        bundle_root=bundle_root,
        manifest=manifest,
        members=members,
    )
    curriculum_payload = _build_curriculum_request_payload(bindings, members)
    audio_payload = _build_audio_request_payload(bindings, members)
    curriculum_raw = _review_request_bytes(
        "Korean Foundation Curriculum Review Request",
        "Review the exact v2 Hangul and pronunciation candidate identities, "
        "curriculum atomicity, Korean orthography/phonetics, and Portuguese policy.",
        curriculum_payload,
    )
    audio_raw = _review_request_bytes(
        "Korean Foundation Audio, Media Rights, and Playback Review Request",
        "Review the exact v2 media slots, rights selectors, text bindings, "
        "specialist playback, independent native playback, and heard playback.",
        audio_payload,
    )
    _parse_review_request_payload(curriculum_raw)
    _parse_review_request_payload(audio_raw)
    result_payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "review_requests_ready",
        "candidate_bundle_sha256": publication.bundle_sha256,
        "candidate_bundle_manifest_sha256": publication.bundle_manifest_sha256,
        "curriculum_request_sha256": sha256(curriculum_raw).hexdigest(),
        "audio_playback_request_sha256": sha256(audio_raw).hexdigest(),
    }
    result_payload["content_hash"] = korean_draft_content_hash(result_payload)
    return (
        curriculum_raw,
        audio_raw,
        KoreanFoundationReviewRequestsResult.model_validate(result_payload),
    )


def _parse_review_request_payload(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
        if text.count("```json\n") != 1:
            raise ValueError("request does not contain exactly one JSON block")
        payload_text = text.split("```json\n", maxsplit=1)[1].split(
            "\n```",
            maxsplit=1,
        )[0]
        payload = json.loads(payload_text)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.REVIEW_REQUEST_MISMATCH
        ) from exc
    if not isinstance(payload, dict):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.REVIEW_REQUEST_MISMATCH
        )
    return payload


def _assert_safe_review_request_target(path: Path) -> None:
    if path not in {_CURRICULUM_REVIEW_REQUEST_PATH, _AUDIO_PLAYBACK_REVIEW_REQUEST_PATH}:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.REVIEW_REQUEST_UNSAFE_PATH
        )
    _ensure_directory(path.parent)
    try:
        target_stat = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.REVIEW_REQUEST_UNSAFE_PATH
        ) from exc
    if _path_is_link_or_reparse(target_stat) or not stat.S_ISREG(target_stat.st_mode):
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.REVIEW_REQUEST_UNSAFE_PATH
        )


def _write_review_request_file(path: Path, raw: bytes) -> None:
    _assert_safe_review_request_target(path)
    descriptor = -1
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
        _fsync_directory(path.parent)
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _write_review_request_pair(curriculum_raw: bytes, audio_raw: bytes) -> None:
    _parse_review_request_payload(curriculum_raw)
    _parse_review_request_payload(audio_raw)
    _assert_safe_review_request_target(_CURRICULUM_REVIEW_REQUEST_PATH)
    _assert_safe_review_request_target(_AUDIO_PLAYBACK_REVIEW_REQUEST_PATH)
    _write_review_request_file(_CURRICULUM_REVIEW_REQUEST_PATH, curriculum_raw)
    _write_review_request_file(_AUDIO_PLAYBACK_REVIEW_REQUEST_PATH, audio_raw)


def regenerate_korean_foundation_review_requests() -> KoreanFoundationReviewRequestsResult:
    curriculum_raw, audio_raw, result = _build_review_request_files()
    _write_review_request_pair(curriculum_raw, audio_raw)
    return verify_korean_foundation_review_requests()


def verify_korean_foundation_review_requests() -> KoreanFoundationReviewRequestsResult:
    expected_curriculum, expected_audio, expected = _build_review_request_files()
    try:
        actual_curriculum = _CURRICULUM_REVIEW_REQUEST_PATH.read_bytes()
        actual_audio = _AUDIO_PLAYBACK_REVIEW_REQUEST_PATH.read_bytes()
    except OSError as exc:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.ARTIFACT_MISSING
        ) from exc
    if actual_curriculum != expected_curriculum or actual_audio != expected_audio:
        raise KoreanFoundationAICurationError(
            KoreanFoundationAICurationReasonCode.REVIEW_REQUEST_MISMATCH
        )
    return expected


__all__ = [
    "KOREAN_FOUNDATION_CURATION_DRAFT_ROOT",
    "KOREAN_FOUNDATION_CURATION_INPUT_ROOT",
    "KOREAN_FOUNDATION_CANDIDATE_BUNDLE_ROOT",
    "KOREAN_FOUNDATION_CANDIDATE_ROOT",
    "KOREAN_FOUNDATION_EXECUTION_HANDOFF_ROOT",
    "KOREAN_FOUNDATION_PROJECTION_MAX_BYTES",
    "KoreanFoundationAICurationError",
    "KoreanFoundationAICurationReasonCode",
    "KoreanFoundationBatchDraft",
    "KoreanFoundationBatchProjection",
    "KoreanFoundationCandidateBundleManifest",
    "KoreanFoundationCandidateBundleMember",
    "KoreanFoundationCandidateBundlePlan",
    "KoreanFoundationCandidatePointer",
    "KoreanFoundationCandidatePublication",
    "KoreanFoundationCurationSelectionHandoff",
    "KoreanFoundationDraftArtifactBinding",
    "KoreanFoundationDraftDisagreement",
    "KoreanFoundationDraftManifest",
    "KoreanFoundationDraftRecord",
    "KoreanFoundationDraftSourceReference",
    "KoreanFoundationDraftUncertainty",
    "KoreanFoundationDraftValidationReport",
    "KoreanFoundationFamilyDraft",
    "KoreanFoundationFieldProposal",
    "KoreanFoundationReviewRequestsResult",
    "assemble_korean_foundation_draft_manifest",
    "assemble_korean_foundation_family_draft",
    "build_korean_foundation_batch_projection",
    "check_korean_foundation_curation_selection",
    "korean_draft_content_hash",
    "promote_korean_foundation_curation_selection",
    "read_current_korean_foundation_candidate",
    "regenerate_korean_foundation_review_requests",
    "validate_korean_foundation_batch_draft",
    "validate_korean_foundation_drafts",
    "verify_promoted_korean_foundation_candidate",
    "verify_korean_foundation_review_requests",
    "write_korean_foundation_batch_projection",
    "write_korean_foundation_draft_manifest",
    "write_korean_foundation_family_draft",
]
