"""Bounded Korean foundation manifests and strict curriculum validation."""

from __future__ import annotations

from enum import Enum
from graphlib import CycleError, TopologicalSorter
from hashlib import sha256
import json
from pathlib import Path
from typing import Final, Literal, Self, TypeVar
import unicodedata

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from multilang.domain.korean import (
    KOREAN_LANGUAGE_CODE,
    KoreanConcept,
    KoreanCurriculumEvidence,
    KoreanPedagogicalJamoMapping,
    KoreanPronunciationEvidence,
    KoreanReviewStatus,
)


KOREAN_FOUNDATION_DATA_ROOT: Final = Path("data") / "korean_foundations"
DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH: Path = (
    KOREAN_FOUNDATION_DATA_ROOT / "korean-concepts-v1.json"
)
DEFAULT_KOREAN_HANGUL_SOURCE_PACK_PATH: Path = (
    KOREAN_FOUNDATION_DATA_ROOT / "hangul-v1.json"
)
DEFAULT_KOREAN_PRONUNCIATION_SOURCE_PACK_PATH: Path = (
    KOREAN_FOUNDATION_DATA_ROOT / "pronunciation-i-plus-1-v1.json"
)

KOREAN_MANIFEST_MAX_BYTES: Final = 1_048_576
_MAX_IDENTIFIER_LENGTH: Final = 128
_MAX_TEXT_LENGTH: Final = 2_048
_MAX_CONCEPTS: Final = 4_096
_MAX_ENTRIES: Final = 4_096
_MAX_PROVENANCE: Final = 16
_MAX_REVIEWS: Final = 16
_MAX_MEDIA_SLOTS: Final = 32
_MAX_STAGE_COVERAGE: Final = 14
_MAX_CATEGORY_IDS: Final = 128
_MAX_IDS: Final = 128
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_UNKNOWN_IDENTIFIERS: Final = frozenset(
    {"unknown", "unresolved", "unspecified", "none", "null", "n/a", "na"}
)
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

_HANGUL_STAGE_CATEGORIES: Final[dict[str, tuple[str, ...]]] = {
    "H0": (
        "jamo-unit",
        "syllable-block-unit",
        "onset-slot",
        "nucleus-slot",
        "optional-coda-slot",
        "vertical-vowel-layout",
        "horizontal-vowel-layout",
    ),
    "H1": (
        "vowel-a",
        "vowel-eo",
        "vowel-o",
        "vowel-u",
        "vowel-eu",
        "vowel-i",
    ),
    "H2": (
        "null-onset-ieung",
        "vertical-block-composition",
        "horizontal-block-composition",
    ),
    "H3": (
        "basic-onset-nieun",
        "basic-onset-mieum",
        "basic-onset-rieul",
        "basic-onset-kiyeok",
        "basic-onset-tikeut",
        "basic-onset-pieup",
        "basic-onset-cieuc",
        "basic-onset-sios",
        "basic-onset-hieuh",
    ),
    "H4": (
        "vowel-ya",
        "vowel-yeo",
        "vowel-yo",
        "vowel-yu",
        "vowel-ae",
        "vowel-e",
        "vowel-yae",
        "vowel-ye",
    ),
    "H5": (
        "aspirated-onset-khieukh",
        "aspirated-onset-thieuth",
        "aspirated-onset-phieuph",
        "aspirated-onset-chieuch",
        "tense-onset-ssangkiyeok",
        "tense-onset-ssangtikeut",
        "tense-onset-ssangpieup",
        "tense-onset-ssangsios",
        "tense-onset-ssangcieuc",
    ),
    "H6": (
        "vowel-wa",
        "vowel-wo",
        "vowel-wae",
        "vowel-we",
        "vowel-oe",
        "vowel-wi",
        "vowel-ui",
    ),
    "H7": (
        "batchim-position",
        "coda-output-kiyeok",
        "coda-output-nieun",
        "coda-output-tikeut",
        "coda-output-rieul",
        "coda-output-mieum",
        "coda-output-pieup",
        "coda-output-ieung",
    ),
    "H8": (
        "final-kiyeok",
        "final-ssangkiyeok",
        "final-kiyeok-sios",
        "final-nieun",
        "final-nieun-cieuc",
        "final-nieun-hieuh",
        "final-tikeut",
        "final-rieul",
        "final-rieul-kiyeok",
        "final-rieul-mieum",
        "final-rieul-pieup",
        "final-rieul-sios",
        "final-rieul-thieuth",
        "final-rieul-phieuph",
        "final-rieul-hieuh",
        "final-mieum",
        "final-pieup",
        "final-pieup-sios",
        "final-sios",
        "final-ssangsios",
        "final-ieung",
        "final-cieuc",
        "final-chieuch",
        "final-khieukh",
        "final-thieuth",
        "final-phieuph",
        "final-hieuh",
    ),
    "H9": (
        "morpheme-preserving-spelling",
        "basic-word-spacing",
        "attached-particle-spacing",
    ),
    "H10": (
        "nfc-nfd-equivalence",
        "keyboard-orientation",
        "punctuation",
        "numerals",
        "bounded-mixed-script",
    ),
}

_PRONUNCIATION_STAGE_CATEGORIES: Final[dict[str, tuple[str, ...]]] = {
    "P0": (
        "syllable-timing",
        "vowel-quality",
        "null-onset",
        "sonorant-nieun",
        "sonorant-mieum",
        "sonorant-ieung",
        "rieul-intervocalic",
        "rieul-coda",
    ),
    "P1": (
        "onset-contrast-pieup",
        "onset-contrast-tikeut",
        "onset-contrast-kiyeok",
        "onset-contrast-cieuc",
        "onset-contrast-sios",
        "onset-hieuh",
    ),
    "P2": (
        "unreleased-coda",
        "coda-neutralization-kiyeok",
        "coda-neutralization-nieun",
        "coda-neutralization-tikeut",
        "coda-neutralization-rieul",
        "coda-neutralization-mieum",
        "coda-neutralization-pieup",
        "coda-neutralization-ieung",
    ),
    "P3": ("liaison-vowel-initial-morpheme",),
    "P4": ("post-obstruent-tensification",),
    "P5": (
        "nasalization-velar",
        "nasalization-coronal",
        "nasalization-labial",
    ),
    "P6": (
        "h-aspiration-coda-to-onset",
        "h-aspiration-onset-from-coda",
    ),
    "P7": ("palatalization-tikeut", "palatalization-thieuth"),
    "P8": ("liquid-assimilation", "rieul-related-process", "n-insertion"),
    "P9": (
        "complex-coda-before-consonant",
        "complex-coda-before-vowel",
        "complex-coda-rule-interaction",
    ),
    "P10": (
        "contraction-boa-bwa",
        "contraction-jueo-jwo",
        "contraction-doeeo-dwae",
        "contraction-hayeo-hae",
    ),
    "P11": ("optional-reduction-register-context",),
    "P12": (
        "phrase-accent",
        "focus",
        "boundary-intonation",
        "rate-conditioned-effects",
    ),
    "P13": ("rule-ordering-relation",),
}

_HANGUL_LEARNER_FIELD_ORDER: Final = (
    "SortIndex",
    "Category",
    "JamoOrBlock",
    "ReadingOrName",
    "Sound",
    "Mnemonic",
    "Picture",
    "Strokes",
    "Gif",
    "Audio",
    "TargetConceptId",
    "PrerequisiteConceptIds",
    "ObservedConceptIds",
    "UnknownConceptIds",
    "IPlusOnePolicy",
)

_PRONUNCIATION_LEARNER_FIELD_ORDER: Final = (
    "Spellings",
    "Sound",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Example Sentence",
    "sentence_audio",
    "Sentence Translation",
)

_HANGUL_MEDIA_SLOT_SCHEMA: Final = (
    ("picture", False),
    ("strokes", True),
    ("gif", False),
    ("audio", True),
)

_PRONUNCIATION_MEDIA_SLOT_SCHEMA: Final = (
    ("letter_audio", True),
    ("word_audio", True),
    ("sentence_audio", True),
)


class KoreanFoundationFamily(str, Enum):
    """The two isolated Korean foundation source-pack families."""

    HANGUL = "hangul"
    PRONUNCIATION = "pronunciation"


class KoreanCurriculumReasonCode(str, Enum):
    """Content-free failure reasons for manifest and strict graph boundaries."""

    MANIFEST_MISSING = "manifest_missing"
    MANIFEST_MALFORMED = "manifest_malformed"
    MANIFEST_OVERSIZED = "manifest_oversized"
    MANIFEST_INVALID = "manifest_invalid"
    REGISTRY_MISMATCH = "registry_mismatch"
    COVERAGE_MISMATCH = "coverage_mismatch"
    BOOTSTRAP_MISMATCH = "bootstrap_mismatch"
    INHERITED_CONCEPTS_MISMATCH = "inherited_concepts_mismatch"
    UNKNOWN_CONCEPT = "unknown_concept"
    UNSUPPORTED_DOMAIN = "unsupported_domain"
    STRICT_POLICY_REQUIRED = "strict_policy_required"
    TARGET_NOT_OBSERVED = "target_not_observed"
    REPEATED_TARGET = "repeated_target"
    UNKNOWN_PREREQUISITE = "unknown_prerequisite"
    ACTIVE_RULE_NOT_PREREQUISITE = "active_rule_not_prerequisite"
    RECOMPUTED_UNKNOWN_MISMATCH = "recomputed_unknown_mismatch"
    SERIALIZED_UNKNOWN_MISMATCH = "serialized_unknown_mismatch"


class KoreanCurriculumError(ValueError):
    """A controlled curriculum failure that never includes submitted content."""

    def __init__(self, reason_code: KoreanCurriculumReasonCode) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code.value)


class _FrozenManifest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


def korean_canonical_json_sha256(value: object) -> str:
    """Hash deterministic UTF-8 canonical JSON without ASCII escaping."""

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


def _manifest_content_hash(model: BaseModel) -> str:
    payload = model.model_dump(mode="json", by_alias=True)
    payload.pop("content_hash", None)
    return korean_canonical_json_sha256(payload)


def _identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _MAX_IDENTIFIER_LENGTH
        or normalized.casefold() in _UNKNOWN_IDENTIFIERS
        or not normalized[0].isalnum()
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _identifiers(
    values: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(_identifier(value, field_name=field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must contain unique identifiers")
    return normalized


def _sha256_text(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _safe_text(value: str, *, field_name: str) -> str:
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
        or any(
            0x3130 <= ord(character) < 0x3190
            or 0xFFA0 <= ord(character) < 0xFFDD
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be bounded safe text")
    return normalized


def _optional_safe_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _safe_text(value, field_name=field_name)


def _korean_pronunciation_candidate_text(
    value: str,
    *,
    field_name: str,
) -> str:
    """Keep Korean candidate claims out of unrelated alphabetic scripts."""

    normalized = _safe_text(value, field_name=field_name)
    if normalized == "needs_review":
        return normalized
    alphabetic = tuple(character for character in normalized if character.isalpha())
    if not alphabetic or any(
        not (
            0x1100 <= ord(character) <= 0x11FF
            or 0xAC00 <= ord(character) <= 0xD7A3
        )
        for character in alphabetic
    ):
        raise ValueError(f"{field_name} must use bounded Korean candidate text")
    return normalized


def _stage_number(stage_id: str, family: KoreanFoundationFamily) -> int:
    prefix = "H" if family is KoreanFoundationFamily.HANGUL else "P"
    maximum = 10 if family is KoreanFoundationFamily.HANGUL else 13
    if (
        len(stage_id) < 2
        or not stage_id.startswith(prefix)
        or not stage_id[1:].isdigit()
    ):
        raise ValueError("stage id does not match its foundation family")
    number = int(stage_id[1:])
    if not 0 <= number <= maximum or stage_id != f"{prefix}{number}":
        raise ValueError("stage id does not match its foundation family")
    return number


class KoreanSourceProvenance(_FrozenManifest):
    """Bounded source identity retained without an executable source location."""

    source_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    source_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    citation: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    source_reference: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    source_hash: str = Field(min_length=64, max_length=64)

    @field_validator("source_id", "source_version")
    @classmethod
    def source_identifiers_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "source identifier"),
        )

    @field_validator("citation", "source_reference")
    @classmethod
    def source_text_must_be_safe(cls, value: str, info: object) -> str:
        return _safe_text(
            value,
            field_name=getattr(info, "field_name", "source text"),
        )

    @field_validator("source_hash")
    @classmethod
    def source_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="source hash")


class KoreanPendingReview(_FrozenManifest):
    """One actionable review requirement that cannot self-approve."""

    status: Literal["needs_review"] = "needs_review"
    reason_code: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    required_reviewer_role: str = Field(
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )

    @field_validator("reason_code", "required_reviewer_role")
    @classmethod
    def review_identifiers_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "review identifier"),
        )


class KoreanMediaSlotReference(_FrozenManifest):
    """A required media identity with no source path, URL, or media bytes."""

    slot_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    media_kind: Literal[
        "picture",
        "strokes",
        "gif",
        "audio",
        "letter_audio",
        "word_audio",
        "sentence_audio",
    ]
    required: bool
    review_status: Literal["needs_review"] = "needs_review"
    reason_code: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)

    @field_validator("slot_id", "reason_code")
    @classmethod
    def media_identifiers_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "media identifier"),
        )


class KoreanMediaSlotSchema(_FrozenManifest):
    """One family-level media requirement that cannot imply available bytes."""

    media_kind: Literal[
        "picture",
        "strokes",
        "gif",
        "audio",
        "letter_audio",
        "word_audio",
        "sentence_audio",
    ]
    required: bool
    review_status: Literal["needs_review"] = "needs_review"
    reason_code: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)

    @field_validator("reason_code")
    @classmethod
    def reason_code_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="media schema reason code")


class KoreanStageCoverage(_FrozenManifest):
    """Source-declared stage and atomic category coverage."""

    family: KoreanFoundationFamily
    stage_id: str = Field(min_length=2, max_length=4)
    required_category_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=_MAX_CATEGORY_IDS,
    )

    @field_validator("required_category_ids")
    @classmethod
    def categories_must_be_unique(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        return _identifiers(value, field_name="required category ids")

    @model_validator(mode="after")
    def stage_must_match_family(self) -> Self:
        _stage_number(self.stage_id, self.family)
        return self


class KoreanConceptRegistry(_FrozenManifest):
    """The bounded shared prerequisite registry for both foundation families."""

    language_code: Literal["ko"] = KOREAN_LANGUAGE_CODE
    registry_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    provenance: tuple[KoreanSourceProvenance, ...] = Field(
        min_length=1,
        max_length=_MAX_PROVENANCE,
    )
    concepts: tuple[KoreanConcept, ...] = Field(
        min_length=1,
        max_length=_MAX_CONCEPTS,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("registry_version")
    @classmethod
    def registry_version_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="registry version")

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="registry content hash")

    @model_validator(mode="after")
    def registry_graph_must_be_closed_and_deterministic(self) -> Self:
        concept_ids = tuple(concept.id for concept in self.concepts)
        sequences = tuple(concept.sequence for concept in self.concepts)
        if len(concept_ids) != len(set(concept_ids)):
            raise ValueError("concept registry ids must be unique")
        if len(sequences) != len(set(sequences)):
            raise ValueError("concept registry sequences must be unique")
        if sequences != tuple(range(1, len(self.concepts) + 1)):
            raise ValueError("concept registry order must be deterministic")

        concept_by_id = {concept.id: concept for concept in self.concepts}
        if any(
            predecessor not in concept_by_id
            for concept in self.concepts
            for predecessor in concept.prerequisite_ids
        ):
            raise ValueError("concept registry predecessor is missing")
        if any(
            concept.domain not in {"orthography", "phonology"}
            for concept in self.concepts
        ):
            raise ValueError("concept registry domain is unsupported")
        allowed_predecessor_domains = {
            "orthography": {"orthography"},
            "phonology": {"orthography", "phonology"},
        }
        if any(
            concept_by_id[predecessor].domain
            not in allowed_predecessor_domains[concept.domain]
            for concept in self.concepts
            for predecessor in concept.prerequisite_ids
        ):
            raise ValueError("concept registry domain dependency is unsupported")

        graph = {
            concept.id: set(concept.prerequisite_ids) for concept in self.concepts
        }
        try:
            tuple(TopologicalSorter(graph).static_order())
        except CycleError as exc:
            raise ValueError("concept registry contains a cycle") from exc

        if any(
            concept_by_id[predecessor].sequence >= concept.sequence
            for concept in self.concepts
            for predecessor in concept.prerequisite_ids
        ):
            raise ValueError("concept registry contains a forward dependency")

        ancestor_cache: dict[str, set[str]] = {}

        def ancestors(concept_id: str) -> set[str]:
            if concept_id in ancestor_cache:
                return ancestor_cache[concept_id]
            result: set[str] = set()
            for predecessor in graph[concept_id]:
                result.add(predecessor)
                result.update(ancestors(predecessor))
            ancestor_cache[concept_id] = result
            return result

        if any(
            set(concept.prerequisite_ids) != ancestors(concept.id)
            for concept in self.concepts
        ):
            raise ValueError("concept registry predecessor closure is incomplete")
        if self.content_hash != _manifest_content_hash(self):
            raise ValueError("concept registry content hash does not match")
        return self


class KoreanFoundationEntry(_FrozenManifest):
    """Common strict source evidence shared by both foundation entry schemas."""

    item_key: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    family: KoreanFoundationFamily
    stage_id: str = Field(min_length=2, max_length=4)
    category_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    sequence: int = Field(ge=1, le=_MAX_ENTRIES)
    source_pack_version: str = Field(
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    evidence: KoreanCurriculumEvidence
    active_rule_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=_MAX_IDS,
    )
    inherited_orthographic_concept_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_MAX_IDS,
    )
    provenance: tuple[KoreanSourceProvenance, ...] = Field(
        min_length=1,
        max_length=_MAX_PROVENANCE,
    )
    pending_reviews: tuple[KoreanPendingReview, ...] = Field(
        min_length=1,
        max_length=_MAX_REVIEWS,
    )
    media_slots: tuple[KoreanMediaSlotReference, ...] = Field(
        min_length=1,
        max_length=_MAX_MEDIA_SLOTS,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("item_key", "category_id", "source_pack_version")
    @classmethod
    def entry_identifiers_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "entry identifier"),
        )

    @field_validator("active_rule_ids", "inherited_orthographic_concept_ids")
    @classmethod
    def entry_id_sets_must_be_unique(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        return _identifiers(
            value,
            field_name=getattr(info, "field_name", "entry ids"),
        )

    @field_validator("content_hash")
    @classmethod
    def entry_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="entry content hash")

    @model_validator(mode="after")
    def common_entry_contract_must_be_deterministic(self) -> Self:
        _stage_number(self.stage_id, self.family)
        prefix = (
            "ko-hangul"
            if self.family is KoreanFoundationFamily.HANGUL
            else "ko-pron"
        )
        if self.item_key != f"{prefix}-{self.sequence:04d}":
            raise ValueError("entry item key does not match family and sequence")
        if (
            self.family is KoreanFoundationFamily.HANGUL
            and self.inherited_orthographic_concept_ids
        ):
            raise ValueError("Hangul entries cannot inherit external concepts")
        media_ids = tuple(slot.slot_id for slot in self.media_slots)
        if len(media_ids) != len(set(media_ids)):
            raise ValueError("entry media slot ids must be unique")
        if self.content_hash != _manifest_content_hash(self):
            raise ValueError("entry content hash does not match")
        return self


class KoreanHangulSourceEntry(KoreanFoundationEntry):
    """One Hangul source record with canonical identity and pending learner copy."""

    sort_index: int = Field(ge=1, le=_MAX_ENTRIES)
    category: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    canonical_jamo_or_block: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    reading_or_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=_MAX_TEXT_LENGTH,
    )
    sound: str | None = Field(
        default=None,
        min_length=1,
        max_length=_MAX_TEXT_LENGTH,
    )
    mnemonic: str | None = Field(
        default=None,
        min_length=1,
        max_length=_MAX_TEXT_LENGTH,
    )
    pedagogical_jamo_mapping: KoreanPedagogicalJamoMapping | None = None

    @field_validator("category", "canonical_jamo_or_block")
    @classmethod
    def required_hangul_text_must_be_safe(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _safe_text(
            value,
            field_name=getattr(info, "field_name", "Hangul entry text"),
        )

    @field_validator("reading_or_name", "sound", "mnemonic")
    @classmethod
    def optional_hangul_text_must_be_safe(
        cls,
        value: str | None,
        info: object,
    ) -> str | None:
        return _optional_safe_text(
            value,
            field_name=getattr(info, "field_name", "Hangul entry text"),
        )

    @model_validator(mode="after")
    def hangul_entry_must_match_family(self) -> Self:
        if self.family is not KoreanFoundationFamily.HANGUL:
            raise ValueError("Hangul entry family is invalid")
        if self.sort_index != self.sequence or self.category != self.category_id:
            raise ValueError("Hangul entry order or category is inconsistent")
        if (
            self.pedagogical_jamo_mapping is not None
            and self.pedagogical_jamo_mapping.canonical_jamo
            != self.canonical_jamo_or_block
        ):
            raise ValueError("pedagogical mapping does not match canonical Jamo")
        return self


class KoreanPronunciationSourceEntry(KoreanFoundationEntry):
    """One rich pronunciation source record behind the exact nine learner fields."""

    spellings: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    sound: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    example_word: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    word_translation: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    example_sentence: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    sentence_translation: str = Field(min_length=1, max_length=_MAX_TEXT_LENGTH)
    register_context: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    pronunciation_evidence: KoreanPronunciationEvidence

    @field_validator("spellings", "sound", "example_word", "example_sentence")
    @classmethod
    def pronunciation_korean_text_must_be_safe(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _korean_pronunciation_candidate_text(
            value,
            field_name=getattr(info, "field_name", "pronunciation Korean text"),
        )

    @field_validator("word_translation", "sentence_translation")
    @classmethod
    def pronunciation_translation_text_must_be_safe(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _safe_text(
            value,
            field_name=getattr(info, "field_name", "pronunciation translation"),
        )

    @field_validator("register_context")
    @classmethod
    def register_context_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="register context")

    @model_validator(mode="after")
    def pronunciation_entry_must_match_family(self) -> Self:
        if self.family is not KoreanFoundationFamily.PRONUNCIATION:
            raise ValueError("pronunciation entry family is invalid")
        media_kinds = {slot.media_kind for slot in self.media_slots if slot.required}
        if media_kinds != {"letter_audio", "word_audio", "sentence_audio"}:
            raise ValueError("pronunciation entry requires all three audio slots")
        if self.pronunciation_evidence.canonical_spelling != self.example_word:
            raise ValueError("pronunciation evidence must match the example word")
        if tuple(self.pronunciation_evidence.phonological_rule_ids) != tuple(
            self.active_rule_ids
        ):
            raise ValueError("pronunciation rule evidence must match active rules")
        for field_name, value in (
            (
                "canonical spelling",
                self.pronunciation_evidence.canonical_spelling,
            ),
            (
                "normative pronunciation",
                self.pronunciation_evidence.normative_pronunciation,
            ),
            (
                "surface pronunciation",
                self.pronunciation_evidence.surface_pronunciation,
            ),
        ):
            _korean_pronunciation_candidate_text(value, field_name=field_name)
        if (
            self.pronunciation_evidence.review_status
            is not KoreanReviewStatus.NEEDS_REVIEW
        ):
            raise ValueError("pronunciation source candidates cannot self-approve")
        return self


class _KoreanFoundationSourcePack(_FrozenManifest):
    language_code: Literal["ko"] = KOREAN_LANGUAGE_CODE
    family: KoreanFoundationFamily
    source_pack_version: str = Field(
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    registry_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    registry_content_hash: str = Field(min_length=64, max_length=64)
    item_key_pattern: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    sequence_policy: Literal["contiguous-from-1"] = "contiguous-from-1"
    inventory_status: Literal["skeleton", "complete"] = "skeleton"
    review_status: Literal["needs_review"] = "needs_review"
    learner_field_order: tuple[str, ...] = Field(min_length=1, max_length=32)
    media_slot_schema: tuple[KoreanMediaSlotSchema, ...] = Field(
        min_length=1,
        max_length=_MAX_MEDIA_SLOTS,
    )
    strict_start_sequence: int = Field(ge=1, le=_MAX_ENTRIES)
    bootstrap_concept_ids: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)
    inherited_orthographic_concept_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_MAX_IDS,
    )
    stage_coverage: tuple[KoreanStageCoverage, ...] = Field(
        min_length=1,
        max_length=_MAX_STAGE_COVERAGE,
    )
    provenance: tuple[KoreanSourceProvenance, ...] = Field(
        min_length=1,
        max_length=_MAX_PROVENANCE,
    )
    entries: tuple[KoreanFoundationEntry, ...] = Field(
        default=(),
        max_length=_MAX_ENTRIES,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("source_pack_version", "registry_version")
    @classmethod
    def pack_versions_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "pack version"),
        )

    @field_validator("registry_content_hash", "content_hash")
    @classmethod
    def pack_hashes_must_be_sha256(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "pack hash"),
        )

    @field_validator(
        "bootstrap_concept_ids",
        "inherited_orthographic_concept_ids",
    )
    @classmethod
    def pack_id_sets_must_be_unique(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        return _identifiers(
            value,
            field_name=getattr(info, "field_name", "pack ids"),
        )

    @model_validator(mode="after")
    def source_pack_must_be_deterministic(self) -> Self:
        expected_item_key_pattern = (
            "ko-hangul-{sequence:04d}"
            if self.family is KoreanFoundationFamily.HANGUL
            else "ko-pron-{sequence:04d}"
        )
        expected_field_order = (
            _HANGUL_LEARNER_FIELD_ORDER
            if self.family is KoreanFoundationFamily.HANGUL
            else _PRONUNCIATION_LEARNER_FIELD_ORDER
        )
        expected_media_schema = (
            _HANGUL_MEDIA_SLOT_SCHEMA
            if self.family is KoreanFoundationFamily.HANGUL
            else _PRONUNCIATION_MEDIA_SLOT_SCHEMA
        )
        actual_media_schema = tuple(
            (slot.media_kind, slot.required) for slot in self.media_slot_schema
        )
        if self.item_key_pattern != expected_item_key_pattern:
            raise ValueError("source pack item-key policy is inconsistent")
        if tuple(self.learner_field_order) != expected_field_order:
            raise ValueError("source pack learner field order is inconsistent")
        if actual_media_schema != expected_media_schema:
            raise ValueError("source pack media-slot schema is inconsistent")

        stages = tuple(coverage.stage_id for coverage in self.stage_coverage)
        if len(stages) != len(set(stages)):
            raise ValueError("source pack stage coverage must be unique")
        if any(coverage.family is not self.family for coverage in self.stage_coverage):
            raise ValueError("source pack stage family is inconsistent")
        stage_numbers = tuple(
            _stage_number(coverage.stage_id, self.family)
            for coverage in self.stage_coverage
        )
        if stage_numbers != tuple(sorted(stage_numbers)):
            raise ValueError("source pack stage order must be deterministic")
        expected_coverage = (
            _HANGUL_STAGE_CATEGORIES
            if self.family is KoreanFoundationFamily.HANGUL
            else _PRONUNCIATION_STAGE_CATEGORIES
        )
        actual_coverage = {
            coverage.stage_id: tuple(coverage.required_category_ids)
            for coverage in self.stage_coverage
        }
        if actual_coverage != expected_coverage:
            raise ValueError("source pack stage/category coverage is incomplete")

        sequences = tuple(entry.sequence for entry in self.entries)
        item_keys = tuple(entry.item_key for entry in self.entries)
        if sequences != tuple(range(1, len(self.entries) + 1)):
            raise ValueError("source pack entry sequence must be contiguous")
        if len(item_keys) != len(set(item_keys)):
            raise ValueError("source pack item keys must be unique")
        if any(
            entry.family is not self.family
            or entry.source_pack_version != self.source_pack_version
            for entry in self.entries
        ):
            raise ValueError("source pack entry identity is inconsistent")

        declared_categories = {
            coverage.stage_id: set(coverage.required_category_ids)
            for coverage in self.stage_coverage
        }
        if any(
            entry.stage_id not in declared_categories
            or entry.category_id not in declared_categories[entry.stage_id]
            for entry in self.entries
        ):
            raise ValueError("source pack entry coverage is undeclared")
        if any(
            tuple((slot.media_kind, slot.required) for slot in entry.media_slots)
            != expected_media_schema
            for entry in self.entries
        ):
            raise ValueError("source pack entry media slots are inconsistent")
        if self.inventory_status == "complete":
            actual_entry_coverage = {
                stage_id: tuple(
                    entry.category_id
                    for entry in self.entries
                    if entry.stage_id == stage_id
                )
                for stage_id in expected_coverage
            }
            if actual_entry_coverage != expected_coverage:
                raise ValueError("source pack complete entry coverage is inconsistent")
        if self.content_hash != _manifest_content_hash(self):
            raise ValueError("source pack content hash does not match")
        return self


class KoreanHangulSourcePack(_KoreanFoundationSourcePack):
    """Bounded Hangul source pack with explicit H0 bootstrap."""

    entries: tuple[KoreanHangulSourceEntry, ...] = Field(
        default=(),
        max_length=_MAX_ENTRIES,
    )

    @model_validator(mode="after")
    def hangul_pack_must_not_inherit_external_concepts(self) -> Self:
        if self.family is not KoreanFoundationFamily.HANGUL:
            raise ValueError("Hangul source pack family is invalid")
        if self.inherited_orthographic_concept_ids:
            raise ValueError("Hangul source pack cannot inherit external concepts")
        return self


class KoreanPronunciationSourcePack(_KoreanFoundationSourcePack):
    """Bounded pronunciation pack with declared inherited orthography only."""

    entries: tuple[KoreanPronunciationSourceEntry, ...] = Field(
        default=(),
        max_length=_MAX_ENTRIES,
    )

    @model_validator(mode="after")
    def pronunciation_pack_must_not_define_bootstrap(self) -> Self:
        if self.family is not KoreanFoundationFamily.PRONUNCIATION:
            raise ValueError("pronunciation source pack family is invalid")
        if self.bootstrap_concept_ids:
            raise ValueError("pronunciation source pack cannot define H0 bootstrap")
        return self


class KoreanCurriculumValidation(_FrozenManifest):
    """Recomputed admission result returned only after every strict entry passes."""

    family: KoreanFoundationFamily
    validated_entry_count: int = Field(ge=0, le=_MAX_ENTRIES)
    bootstrap_concept_ids: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)
    inherited_known_concept_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_MAX_IDS,
    )
    admitted_target_concept_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_MAX_ENTRIES,
    )
    known_concept_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_MAX_ENTRIES + _MAX_IDS,
    )


_ManifestT = TypeVar("_ManifestT", bound=BaseModel)


def _load_fixed_manifest(path: Path, model_type: type[_ManifestT]) -> _ManifestT:
    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise KoreanCurriculumError(
            KoreanCurriculumReasonCode.MANIFEST_MISSING
        ) from exc
    except OSError as exc:
        raise KoreanCurriculumError(
            KoreanCurriculumReasonCode.MANIFEST_MALFORMED
        ) from exc
    if size > KOREAN_MANIFEST_MAX_BYTES:
        raise KoreanCurriculumError(KoreanCurriculumReasonCode.MANIFEST_OVERSIZED)

    try:
        raw = path.read_bytes()
        if len(raw) > KOREAN_MANIFEST_MAX_BYTES:
            raise KoreanCurriculumError(
                KoreanCurriculumReasonCode.MANIFEST_OVERSIZED
            )
        payload = json.loads(raw.decode("utf-8"))
    except KoreanCurriculumError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanCurriculumError(
            KoreanCurriculumReasonCode.MANIFEST_MALFORMED
        ) from exc
    try:
        return model_type.model_validate(payload)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanCurriculumError(
            KoreanCurriculumReasonCode.MANIFEST_INVALID
        ) from exc


def load_korean_concept_registry() -> KoreanConceptRegistry:
    """Load the only supported concept registry from its fixed project path."""

    return _load_fixed_manifest(
        DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH,
        KoreanConceptRegistry,
    )


def load_korean_hangul_source_pack() -> KoreanHangulSourcePack:
    """Load the only supported Hangul source pack from its fixed project path."""

    return _load_fixed_manifest(
        DEFAULT_KOREAN_HANGUL_SOURCE_PACK_PATH,
        KoreanHangulSourcePack,
    )


def load_korean_pronunciation_source_pack() -> KoreanPronunciationSourcePack:
    """Load the only supported pronunciation pack from its fixed project path."""

    return _load_fixed_manifest(
        DEFAULT_KOREAN_PRONUNCIATION_SOURCE_PACK_PATH,
        KoreanPronunciationSourcePack,
    )


def _raise(reason_code: KoreanCurriculumReasonCode) -> None:
    raise KoreanCurriculumError(reason_code)


def validate_korean_foundation_pack(
    *,
    registry: KoreanConceptRegistry,
    pack: KoreanHangulSourcePack | KoreanPronunciationSourcePack,
    inherited_known_ids: tuple[str, ...] = (),
) -> KoreanCurriculumValidation:
    """Recompute graph, bootstrap, active-rule, and strict one-unknown evidence."""

    if (
        pack.registry_version != registry.registry_version
        or pack.registry_content_hash != registry.content_hash
    ):
        _raise(KoreanCurriculumReasonCode.REGISTRY_MISMATCH)

    if pack.inventory_status == "complete":
        expected_coverage = (
            _HANGUL_STAGE_CATEGORIES
            if pack.family is KoreanFoundationFamily.HANGUL
            else _PRONUNCIATION_STAGE_CATEGORIES
        )
        actual_coverage = {
            stage_id: tuple(
                entry.category_id
                for entry in pack.entries
                if entry.stage_id == stage_id
            )
            for stage_id in expected_coverage
        }
        if actual_coverage != expected_coverage:
            _raise(KoreanCurriculumReasonCode.COVERAGE_MISMATCH)

    concept_by_id = {concept.id: concept for concept in registry.concepts}
    inherited = tuple(inherited_known_ids)
    if inherited != tuple(pack.inherited_orthographic_concept_ids):
        _raise(KoreanCurriculumReasonCode.INHERITED_CONCEPTS_MISMATCH)
    if len(inherited) != len(set(inherited)) or any(
        concept_id not in concept_by_id for concept_id in inherited
    ):
        _raise(KoreanCurriculumReasonCode.INHERITED_CONCEPTS_MISMATCH)
    if any(concept_by_id[concept_id].domain != "orthography" for concept_id in inherited):
        _raise(KoreanCurriculumReasonCode.UNSUPPORTED_DOMAIN)

    if pack.family is KoreanFoundationFamily.HANGUL:
        h0_targets = tuple(
            entry.evidence.target_concept_id
            for entry in pack.entries
            if entry.stage_id == "H0"
        )
        if h0_targets != tuple(pack.bootstrap_concept_ids):
            _raise(KoreanCurriculumReasonCode.BOOTSTRAP_MISMATCH)
    elif pack.bootstrap_concept_ids:
        _raise(KoreanCurriculumReasonCode.BOOTSTRAP_MISMATCH)

    known_order = list(inherited)
    known = set(inherited)
    admitted: list[str] = []
    all_registry_ids = set(concept_by_id)

    for entry in pack.entries:
        evidence = entry.evidence
        target_id = evidence.target_concept_id
        referenced_ids = {
            target_id,
            *evidence.prerequisite_concept_ids,
            *evidence.observed_concept_ids,
            *evidence.unknown_concept_ids,
            *entry.active_rule_ids,
            *entry.inherited_orthographic_concept_ids,
        }
        if not referenced_ids <= all_registry_ids:
            _raise(KoreanCurriculumReasonCode.UNKNOWN_CONCEPT)
        if evidence.policy != "strict":
            _raise(KoreanCurriculumReasonCode.STRICT_POLICY_REQUIRED)

        target = concept_by_id[target_id]
        observed = tuple(evidence.observed_concept_ids)
        prerequisites = set(evidence.prerequisite_concept_ids)
        if target_id not in observed:
            _raise(KoreanCurriculumReasonCode.TARGET_NOT_OBSERVED)
        if target_id in known:
            _raise(KoreanCurriculumReasonCode.REPEATED_TARGET)

        if pack.family is KoreanFoundationFamily.HANGUL:
            if target.domain != "orthography" or any(
                concept_by_id[concept_id].domain != "orthography"
                for concept_id in referenced_ids
            ):
                _raise(KoreanCurriculumReasonCode.UNSUPPORTED_DOMAIN)
        else:
            if target.domain != "phonology" or any(
                concept_by_id[concept_id].domain not in {"orthography", "phonology"}
                for concept_id in referenced_ids
            ):
                _raise(KoreanCurriculumReasonCode.UNSUPPORTED_DOMAIN)
            if tuple(entry.inherited_orthographic_concept_ids) != inherited:
                _raise(KoreanCurriculumReasonCode.INHERITED_CONCEPTS_MISMATCH)
            if any(
                concept_by_id[concept_id].domain == "orthography"
                and concept_id not in inherited
                for concept_id in prerequisites
            ):
                _raise(KoreanCurriculumReasonCode.INHERITED_CONCEPTS_MISMATCH)

        if not prerequisites <= known or not set(target.prerequisite_ids) <= prerequisites:
            _raise(KoreanCurriculumReasonCode.UNKNOWN_PREREQUISITE)

        active_non_target = set(entry.active_rule_ids) - {target_id}
        if (
            not active_non_target <= prerequisites
            or not active_non_target <= known
            or not active_non_target <= set(observed)
        ):
            _raise(KoreanCurriculumReasonCode.ACTIVE_RULE_NOT_PREREQUISITE)

        recomputed_unknown = tuple(
            concept_id for concept_id in observed if concept_id not in known
        )
        if recomputed_unknown != (target_id,):
            _raise(KoreanCurriculumReasonCode.RECOMPUTED_UNKNOWN_MISMATCH)
        if tuple(evidence.unknown_concept_ids) != recomputed_unknown:
            _raise(KoreanCurriculumReasonCode.SERIALIZED_UNKNOWN_MISMATCH)

        known.add(target_id)
        known_order.append(target_id)
        admitted.append(target_id)

    return KoreanCurriculumValidation(
        family=pack.family,
        validated_entry_count=len(pack.entries),
        bootstrap_concept_ids=pack.bootstrap_concept_ids,
        inherited_known_concept_ids=inherited,
        admitted_target_concept_ids=tuple(admitted),
        known_concept_ids=tuple(known_order),
    )


__all__ = [
    "DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH",
    "DEFAULT_KOREAN_HANGUL_SOURCE_PACK_PATH",
    "DEFAULT_KOREAN_PRONUNCIATION_SOURCE_PACK_PATH",
    "KOREAN_FOUNDATION_DATA_ROOT",
    "KOREAN_MANIFEST_MAX_BYTES",
    "KoreanConceptRegistry",
    "KoreanCurriculumError",
    "KoreanCurriculumReasonCode",
    "KoreanCurriculumValidation",
    "KoreanFoundationEntry",
    "KoreanFoundationFamily",
    "KoreanHangulSourceEntry",
    "KoreanHangulSourcePack",
    "KoreanMediaSlotReference",
    "KoreanMediaSlotSchema",
    "KoreanPendingReview",
    "KoreanPronunciationSourceEntry",
    "KoreanPronunciationSourcePack",
    "KoreanSourceProvenance",
    "KoreanStageCoverage",
    "korean_canonical_json_sha256",
    "load_korean_concept_registry",
    "load_korean_hangul_source_pack",
    "load_korean_pronunciation_source_pack",
    "validate_korean_foundation_pack",
]
