"""Nonauthoritative Korean foundation assisted-curation contracts."""

import json
import os
import tempfile
import unicodedata
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Literal, Self, TypeAlias

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


class KoreanFoundationAICurationReasonCode(str, Enum):
    ARTIFACT_MISSING = "artifact_missing"
    ARTIFACT_OVERSIZED = "artifact_oversized"
    ARTIFACT_MALFORMED = "artifact_malformed"
    ARTIFACT_INVALID = "artifact_invalid"
    ARTIFACT_BINDING_MISMATCH = "artifact_binding_mismatch"
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


__all__ = [
    "KOREAN_FOUNDATION_CURATION_DRAFT_ROOT",
    "KOREAN_FOUNDATION_CURATION_INPUT_ROOT",
    "KOREAN_FOUNDATION_PROJECTION_MAX_BYTES",
    "KoreanFoundationAICurationError",
    "KoreanFoundationAICurationReasonCode",
    "KoreanFoundationBatchDraft",
    "KoreanFoundationBatchProjection",
    "KoreanFoundationDraftArtifactBinding",
    "KoreanFoundationDraftDisagreement",
    "KoreanFoundationDraftManifest",
    "KoreanFoundationDraftRecord",
    "KoreanFoundationDraftSourceReference",
    "KoreanFoundationDraftUncertainty",
    "KoreanFoundationDraftValidationReport",
    "KoreanFoundationFamilyDraft",
    "KoreanFoundationFieldProposal",
    "assemble_korean_foundation_draft_manifest",
    "assemble_korean_foundation_family_draft",
    "build_korean_foundation_batch_projection",
    "korean_draft_content_hash",
    "validate_korean_foundation_batch_draft",
    "validate_korean_foundation_drafts",
    "write_korean_foundation_batch_projection",
    "write_korean_foundation_draft_manifest",
    "write_korean_foundation_family_draft",
]
