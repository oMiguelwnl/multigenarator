"""Canonical Korean text, analyzer evidence, and lexical identity contracts."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256
import json
from typing import Any, Final, Literal, Self
import unicodedata
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

KOREAN_LANGUAGE_CODE: Final = "ko"
KOREAN_PROVIDER_LOCALE: Final = "ko-KR"
KOREAN_LANGUAGE_VARIANT: Final = "modern-standard-seoul"
KOREAN_MORPHOLOGY_POLICY_VERSION: Final = "kiwi-top2-consensus-v1"
KOREAN_FOUNDATION_DEFAULT_SOURCE: Final = "current-candidate"
KOREAN_FOUNDATION_HISTORY_SOURCE: Final = "v1-history"
KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT: Final = 5965
KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT: Final = 3000
KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT: Final = 2965
KOREAN_FREQUENCY_EXPECTED_LEVEL_COUNT: Final = 1000
KOREAN_FREQUENCY_SOURCE_ID: Final = "nikl-korean-learners-vocabulary"
KOREAN_FREQUENCY_SCHEMA_VERSION: Final = "korean-frequency-bundle-v1"
KOREAN_FREQUENCY_RETRIEVAL_SCHEMA_VERSION: Final = "nikl-frequency-retrieval-v1"
KOREAN_FREQUENCY_EXPECTED_FILENAME: Final = "한국어 학습용 어휘 목록.txt"
KOREAN_FREQUENCY_LANDING_URL: Final = (
    "https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70"
)

KOREAN_LEXICAL_POS_TAGS: Final[frozenset[str]] = frozenset(
    {
        "NNG",
        "NNP",
        "NNB",
        "NR",
        "NP",
        "VV",
        "VA",
        "VX",
        "VCP",
        "VCN",
        "MM",
        "MAG",
        "MAJ",
        "IC",
        "XR",
        "XSV",
        "XSA",
    }
)

_UNKNOWN_IDENTIFIERS: Final = frozenset(
    {"unknown", "unresolved", "unspecified", "none", "null", "n/a", "na"}
)
_HANGUL_COMPATIBILITY_JAMO: Final = range(0x3130, 0x3190)
_HALFWIDTH_HANGUL: Final = range(0xFFA0, 0xFFDD)
_MODERN_HANGUL_INITIAL_JAMO: Final = range(0x1100, 0x1113)
_MODERN_HANGUL_MEDIAL_JAMO: Final = range(0x1161, 0x1176)
_MODERN_HANGUL_FINAL_JAMO: Final = range(0x11A8, 0x11C3)
_HANGUL_SYLLABLE_BASE: Final = 0xAC00
_HANGUL_INITIAL_BASE: Final = 0x1100
_HANGUL_MEDIAL_BASE: Final = 0x1161
_HANGUL_FINAL_BASE: Final = 0x11A7
_HANGUL_INITIAL_COUNT: Final = 19
_HANGUL_MEDIAL_COUNT: Final = 21
_HANGUL_FINAL_COUNT: Final = 28
_HANGUL_INITIAL_BLOCK_SIZE: Final = _HANGUL_MEDIAL_COUNT * _HANGUL_FINAL_COUNT
_HANGUL_SYLLABLE_COUNT: Final = (
    _HANGUL_INITIAL_COUNT * _HANGUL_INITIAL_BLOCK_SIZE
)
_FOUNDATION_IDENTIFIER_MAX_LENGTH: Final = 128
_FOUNDATION_TEXT_MAX_LENGTH: Final = 512
_FOUNDATION_ID_TUPLE_MAX_LENGTH: Final = 128
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")


class KoreanTextError(ValueError):
    """Raised without source content when Korean text is not canonicalizable."""


class KoreanMorphologyStatus(str, Enum):
    """Outcome of local Korean morphology analysis."""

    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    OOV = "oov"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"


class KoreanMatchStatus(str, Enum):
    """Fail-closed target matching outcome."""

    MATCHED = "matched"
    MISMATCH = "mismatch"
    AMBIGUOUS = "ambiguous"
    OOV = "oov"
    UNAVAILABLE = "unavailable"
    MISSING = "missing"
    FINGERPRINT_MISMATCH = "fingerprint-mismatch"
    INVALID = "invalid"


class KoreanReasonCode(str, Enum):
    """Controlled diagnostic codes that never contain learner or vendor text."""

    ANALYSIS_RESOLVED = "analysis_resolved"
    ANALYSIS_DISAGREEMENT = "analysis_disagreement"
    ANALYZER_IMPORT_ERROR = "analyzer_import_error"
    ANALYZER_CONSTRUCTION_ERROR = "analyzer_construction_error"
    ANALYZER_RUNTIME_ERROR = "analyzer_runtime_error"
    EMPTY_ANALYSIS = "empty_analysis"
    MALFORMED_ANALYSIS = "malformed_analysis"
    INVALID_TEXT = "invalid_text"
    OOV_TOKEN = "oov_token"
    CONSENSUS_MATCH = "consensus_match"
    NO_SIGNATURE_MATCH = "no_signature_match"
    MISSING_IDENTITY = "missing_identity"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    INVALID_SIGNATURE = "invalid_signature"


class KoreanReviewStatus(str, Enum):
    """Human review state shared by frozen Korean foundation evidence."""

    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class _FrozenContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


def canonical_json_sha256(payload: Any) -> str:
    """Hash canonical UTF-8 JSON for stable cross-process evidence."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def raw_bytes_sha256(payload: bytes) -> str:
    """Hash exact source or artifact bytes without decoding side effects."""

    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    return sha256(payload).hexdigest()


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    normalized = value.strip()
    if (
        normalized != value
        or len(normalized) != 64
        or any(character not in _LOWERCASE_HEX for character in normalized)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return normalized


def _safe_relative_path(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a safe relative path")
    normalized = value.strip().replace("\\", "/")
    parts = tuple(part for part in normalized.split("/") if part)
    if (
        not normalized
        or normalized != value
        or normalized.startswith("/")
        or normalized.startswith("~")
        or "//" in normalized
        or any(part in {".", ".."} for part in parts)
    ):
        raise ValueError(f"{field_name} must be a safe relative path")
    return normalized


def _require_official_korean_url(value: str, *, field_name: str, landing: bool) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must use the official Korean source host")
    normalized = value.strip()
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or parsed.netloc != "www.korean.go.kr":
        raise ValueError(f"{field_name} must use the official Korean source host")
    if landing and normalized != KOREAN_FREQUENCY_LANDING_URL:
        raise ValueError("landing URL must match the approved NIKL page")
    if not landing and not parsed.path.startswith("/front/etcData/"):
        raise ValueError("attachment URL must be derived from the approved NIKL response")
    return normalized


def canonicalize_korean(value: str) -> str:
    """Reject forbidden Hangul compatibility forms, then normalize with NFC."""

    if not isinstance(value, str) or not value.strip():
        raise KoreanTextError("Korean text must not be blank")
    if any(
        ord(character) in _HANGUL_COMPATIBILITY_JAMO
        or ord(character) in _HALFWIDTH_HANGUL
        for character in value
    ):
        raise KoreanTextError("Korean text contains forbidden compatibility Hangul")
    return unicodedata.normalize("NFC", value)


def _modern_jamo_index(
    value: str,
    *,
    allowed: range,
    base: int,
    reason: str,
) -> int:
    if not isinstance(value, str) or len(value) != 1 or ord(value) not in allowed:
        raise KoreanTextError(reason)
    return ord(value) - base


def compose_modern_hangul(
    initial: str,
    medial: str,
    final: str | None = None,
) -> str:
    """Compose one modern Hangul syllable from positional conjoining Jamo."""

    initial_index = _modern_jamo_index(
        initial,
        allowed=_MODERN_HANGUL_INITIAL_JAMO,
        base=_HANGUL_INITIAL_BASE,
        reason="Hangul initial must be one modern conjoining Jamo",
    )
    medial_index = _modern_jamo_index(
        medial,
        allowed=_MODERN_HANGUL_MEDIAL_JAMO,
        base=_HANGUL_MEDIAL_BASE,
        reason="Hangul medial must be one modern conjoining Jamo",
    )
    final_index = 0
    if final is not None:
        final_index = _modern_jamo_index(
            final,
            allowed=_MODERN_HANGUL_FINAL_JAMO,
            base=_HANGUL_FINAL_BASE,
            reason="Hangul final must be one modern conjoining Jamo",
        )
    syllable_offset = (
        initial_index * _HANGUL_INITIAL_BLOCK_SIZE
        + medial_index * _HANGUL_FINAL_COUNT
        + final_index
    )
    return chr(_HANGUL_SYLLABLE_BASE + syllable_offset)


def decompose_modern_hangul(syllable: str) -> tuple[str, str, str | None]:
    """Decompose exactly one precomposed modern Hangul syllable."""

    if not isinstance(syllable, str) or len(syllable) != 1:
        raise KoreanTextError(
            "value must be one precomposed modern Hangul syllable"
        )
    syllable_offset = ord(syllable) - _HANGUL_SYLLABLE_BASE
    if not 0 <= syllable_offset < _HANGUL_SYLLABLE_COUNT:
        raise KoreanTextError(
            "value must be one precomposed modern Hangul syllable"
        )

    initial_index, remainder = divmod(
        syllable_offset,
        _HANGUL_INITIAL_BLOCK_SIZE,
    )
    medial_index, final_index = divmod(remainder, _HANGUL_FINAL_COUNT)
    initial = chr(_HANGUL_INITIAL_BASE + initial_index)
    medial = chr(_HANGUL_MEDIAL_BASE + medial_index)
    final = None if final_index == 0 else chr(_HANGUL_FINAL_BASE + final_index)
    return initial, medial, final


def normalize_korean_pos(value: str) -> str:
    """Return a supported base lexical POS, removing Kiwi irregular suffixes."""

    if not isinstance(value, str):
        raise ValueError("Korean POS must be a supported lexical tag")
    normalized = value.strip().upper().partition("-")[0]
    if normalized not in KOREAN_LEXICAL_POS_TAGS:
        raise ValueError("Korean POS must be a supported lexical tag")
    return normalized


def _required_identifier(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized or normalized.casefold() in _UNKNOWN_IDENTIFIERS:
        raise ValueError(f"{field_name} must identify a resolved value")
    return unicodedata.normalize("NFC", normalized)


def _require_canonical_text(value: str, *, field_name: str) -> str:
    canonical = canonicalize_korean(value)
    if value != value.strip() or canonical != value:
        raise ValueError(f"{field_name} must already be canonical NFC")
    return value


def _foundation_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _FOUNDATION_IDENTIFIER_MAX_LENGTH
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


def _foundation_identifiers(
    values: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(
        _foundation_identifier(value, field_name=field_name) for value in values
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must contain unique identifiers")
    return normalized


def _foundation_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or len(value) > _FOUNDATION_TEXT_MAX_LENGTH:
        raise ValueError(f"{field_name} must be bounded canonical text")
    canonical = _require_canonical_text(value, field_name=field_name)
    if canonical.casefold() in _UNKNOWN_IDENTIFIERS:
        raise ValueError(f"{field_name} must be resolved")
    return canonical


class KoreanConcept(_FrozenContract):
    """One stable, atomic concept in the shared Korean curriculum graph."""

    id: str = Field(min_length=1, max_length=_FOUNDATION_IDENTIFIER_MAX_LENGTH)
    domain: Literal["orthography", "phonology", "grammar", "lexicon"]
    prerequisite_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_FOUNDATION_ID_TUPLE_MAX_LENGTH,
    )
    sequence: int = Field(ge=1, le=1_000_000)

    @field_validator("id")
    @classmethod
    def concept_id_must_be_resolved(cls, value: str) -> str:
        return _foundation_identifier(value, field_name="concept id")

    @field_validator("prerequisite_ids")
    @classmethod
    def prerequisites_must_be_unique(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        return _foundation_identifiers(value, field_name="prerequisite ids")

    @model_validator(mode="after")
    def concept_must_not_require_itself(self) -> Self:
        if self.id in self.prerequisite_ids:
            raise ValueError("concept cannot require itself")
        return self


class KoreanCurriculumEvidence(_FrozenContract):
    """Serialized curriculum evidence that a pack validator must recompute."""

    target_concept_id: str = Field(
        min_length=1,
        max_length=_FOUNDATION_IDENTIFIER_MAX_LENGTH,
    )
    prerequisite_concept_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_FOUNDATION_ID_TUPLE_MAX_LENGTH,
    )
    observed_concept_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=_FOUNDATION_ID_TUPLE_MAX_LENGTH,
    )
    unknown_concept_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=_FOUNDATION_ID_TUPLE_MAX_LENGTH,
    )
    policy: Literal["strict", "adaptive", "contextual"]

    @field_validator("target_concept_id")
    @classmethod
    def target_must_be_resolved(cls, value: str) -> str:
        return _foundation_identifier(value, field_name="target concept id")

    @field_validator(
        "prerequisite_concept_ids",
        "observed_concept_ids",
        "unknown_concept_ids",
    )
    @classmethod
    def evidence_ids_must_be_unique(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "curriculum ids")
        return _foundation_identifiers(value, field_name=field_name)

    @model_validator(mode="after")
    def evidence_must_be_locally_consistent(self) -> Self:
        observed = set(self.observed_concept_ids)
        if self.target_concept_id not in observed:
            raise ValueError("target concept must be observed")
        if not set(self.prerequisite_concept_ids) <= observed:
            raise ValueError("prerequisite concepts must be observed")
        if self.target_concept_id in self.prerequisite_concept_ids:
            raise ValueError("target concept cannot be a prerequisite")
        return self


class KoreanPronunciationEvidence(_FrozenContract):
    """Distinct frozen spelling, normative, surface, and optional IPA evidence."""

    canonical_spelling: str = Field(
        min_length=1,
        max_length=_FOUNDATION_TEXT_MAX_LENGTH,
    )
    normative_pronunciation: str = Field(
        min_length=1,
        max_length=_FOUNDATION_TEXT_MAX_LENGTH,
    )
    surface_pronunciation: str = Field(
        min_length=1,
        max_length=_FOUNDATION_TEXT_MAX_LENGTH,
    )
    ipa: str | None = Field(
        default=None,
        min_length=1,
        max_length=_FOUNDATION_TEXT_MAX_LENGTH,
    )
    phonological_rule_ids: tuple[str, ...] = Field(
        default=(),
        max_length=_FOUNDATION_ID_TUPLE_MAX_LENGTH,
    )
    review_status: KoreanReviewStatus

    @field_validator(
        "canonical_spelling",
        "normative_pronunciation",
        "surface_pronunciation",
    )
    @classmethod
    def pronunciation_text_must_be_canonical(
        cls,
        value: str,
        info: object,
    ) -> str:
        field_name = getattr(info, "field_name", "pronunciation text")
        return _foundation_text(value, field_name=field_name)

    @field_validator("ipa")
    @classmethod
    def ipa_must_be_canonical(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _foundation_text(value, field_name="ipa")

    @field_validator("phonological_rule_ids")
    @classmethod
    def rule_ids_must_be_unique(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        return _foundation_identifiers(value, field_name="phonological rule ids")


class KoreanPedagogicalJamoMapping(_FrozenContract):
    """Reviewed display glyph mapped explicitly to one positional modern Jamo."""

    display_glyph: str = Field(min_length=1, max_length=1)
    canonical_jamo: str = Field(min_length=1, max_length=1)
    jamo_position: Literal["initial", "medial", "final"]
    unicode_name: str = Field(min_length=1, max_length=128)
    source_version: str = Field(
        min_length=1,
        max_length=_FOUNDATION_IDENTIFIER_MAX_LENGTH,
    )
    source_hash: str = Field(min_length=64, max_length=64)
    review_status: KoreanReviewStatus

    @field_validator("display_glyph")
    @classmethod
    def display_must_be_one_compatibility_jamo(cls, value: str) -> str:
        if (
            len(value) != 1
            or ord(value) not in _HANGUL_COMPATIBILITY_JAMO
            or not unicodedata.name(value, "").startswith("HANGUL LETTER ")
        ):
            raise ValueError("display glyph must be one Compatibility Jamo letter")
        return value

    @field_validator("canonical_jamo")
    @classmethod
    def canonical_jamo_must_be_one_code_point(cls, value: str) -> str:
        if len(value) != 1:
            raise ValueError("canonical Jamo must be one code point")
        code_point = ord(value)
        if (
            code_point in _HANGUL_COMPATIBILITY_JAMO
            or code_point in _HALFWIDTH_HANGUL
        ):
            raise ValueError("canonical Jamo must be a modern conjoining Jamo")
        return value

    @field_validator("unicode_name")
    @classmethod
    def unicode_name_must_be_bounded(cls, value: str) -> str:
        if value != value.strip() or any(
            ord(character) in _HALFWIDTH_HANGUL for character in value
        ):
            raise ValueError("Unicode name must be bounded metadata")
        return value

    @field_validator("source_version")
    @classmethod
    def source_version_must_be_resolved(cls, value: str) -> str:
        return _foundation_identifier(value, field_name="source version")

    @field_validator("source_hash")
    @classmethod
    def source_hash_must_be_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(
            character not in _LOWERCASE_HEX for character in value
        ):
            raise ValueError("source hash must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def canonical_jamo_must_match_position_and_name(self) -> Self:
        allowed_ranges = {
            "initial": _MODERN_HANGUL_INITIAL_JAMO,
            "medial": _MODERN_HANGUL_MEDIAL_JAMO,
            "final": _MODERN_HANGUL_FINAL_JAMO,
        }
        if ord(self.canonical_jamo) not in allowed_ranges[self.jamo_position]:
            raise ValueError("canonical Jamo does not match its position")
        if self.unicode_name != unicodedata.name(self.canonical_jamo, ""):
            raise ValueError("Unicode name does not match canonical Jamo")
        return self


def korean_lexical_key(*, lemma: str, part_of_speech: str, sense_id: str) -> str:
    """Create a stable identity key from canonical lemma, POS, and source sense."""

    canonical_lemma = canonicalize_korean(lemma).strip()
    if not canonical_lemma:
        raise KoreanTextError("Korean text must not be blank")
    normalized_pos = normalize_korean_pos(part_of_speech)
    normalized_sense = _required_identifier(sense_id, field_name="sense_id")
    payload = json.dumps(
        {
            "language": KOREAN_LANGUAGE_CODE,
            "lemma": canonical_lemma,
            "part_of_speech": normalized_pos,
            "sense_id": normalized_sense,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{KOREAN_LANGUAGE_CODE}:{sha256(payload.encode('utf-8')).hexdigest()}"


class KoreanAnalyzerFingerprint(_FrozenContract):
    """Complete set of inputs that can affect pinned Kiwi analysis."""

    analyzer_name: Literal["kiwi"]
    analyzer_package_version: str = Field(min_length=1)
    model_package_version: str = Field(min_length=1)
    model_type: Literal["cong"]
    enabled_dialects: Literal["standard"]
    num_workers: Literal[1]
    integrate_allomorph: Literal[True]
    top_n: Literal[2]
    split_complex: Literal[False]
    compatible_jamo: Literal[False]
    normalize_coda: Literal[False]
    z_coda: Literal[False]
    typos: None
    oov_handling: Literal["chr"]
    policy_version: Literal["kiwi-top2-consensus-v1"]

    @field_validator("analyzer_package_version", "model_package_version")
    @classmethod
    def versions_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("analyzer versions must not be blank")
        return normalized


class KoreanSignatureItem(_FrozenContract):
    """One ordered, project-owned lexical morpheme signature item."""

    form: str = Field(min_length=1)
    pos: str = Field(min_length=1)

    @field_validator("form")
    @classmethod
    def form_must_be_canonical(cls, value: str) -> str:
        return _require_canonical_text(value, field_name="signature form")

    @field_validator("pos", mode="before")
    @classmethod
    def pos_must_be_lexical(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Korean POS must be a supported lexical tag")
        return normalize_korean_pos(value)


class KoreanMorphemeEvidence(_FrozenContract):
    """Safe projection of one Kiwi token without retaining a vendor object."""

    form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    pos: str = Field(min_length=1, max_length=32)
    raw_pos: str = Field(min_length=1, max_length=32)
    oov: bool

    @field_validator("form", "lemma")
    @classmethod
    def text_must_be_canonical(cls, value: str) -> str:
        return _require_canonical_text(value, field_name="morpheme text")

    @field_validator("pos", "raw_pos")
    @classmethod
    def pos_must_be_safe(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized or any(
            character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            for character in normalized
        ):
            raise ValueError("morpheme POS must be a safe analyzer tag")
        return normalized


class KoreanWordAnalysis(_FrozenContract):
    """Ordered morphology evidence and lexical signature for one eojeol."""

    surface_form: str = Field(min_length=1)
    word_position: int = Field(ge=0)
    morphemes: tuple[KoreanMorphemeEvidence, ...] = Field(min_length=1)
    lexical_signature: tuple[KoreanSignatureItem, ...] = Field(min_length=1)

    @field_validator("surface_form")
    @classmethod
    def surface_must_be_canonical(cls, value: str) -> str:
        return _require_canonical_text(value, field_name="surface form")

    @model_validator(mode="after")
    def signature_must_match_lexical_morphemes(self) -> Self:
        expected = tuple(
            KoreanSignatureItem(form=item.form, pos=item.pos)
            for item in self.morphemes
            if item.pos in KOREAN_LEXICAL_POS_TAGS
        )
        if expected != self.lexical_signature:
            raise ValueError("lexical signature must match ordered morpheme evidence")
        return self


class KoreanAnalysisAlternative(_FrozenContract):
    """One ranked Kiwi analysis projected into project-owned word groups."""

    rank: int = Field(ge=1, le=2)
    score: float = Field(allow_inf_nan=False)
    words: tuple[KoreanWordAnalysis, ...] = Field(min_length=1)
    has_oov: bool

    @model_validator(mode="after")
    def evidence_must_be_consistent(self) -> Self:
        positions = tuple(word.word_position for word in self.words)
        if positions != tuple(sorted(set(positions))):
            raise ValueError("word positions must be unique and ordered")
        observed_oov = any(
            morpheme.oov
            for word in self.words
            for morpheme in word.morphemes
        )
        if self.has_oov is not observed_oov:
            raise ValueError("has_oov must match projected morpheme evidence")
        return self


class KoreanMorphologyResult(_FrozenContract):
    """Typed analysis outcome; only resolved results can be considered passing."""

    status: KoreanMorphologyStatus
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    alternatives: tuple[KoreanAnalysisAlternative, ...] = Field(max_length=2)
    reason_code: KoreanReasonCode
    exception_class: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("exception_class")
    @classmethod
    def exception_class_must_be_a_class_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized or not normalized.replace("_", "").isalnum():
            raise ValueError("exception_class must contain a class name only")
        return normalized

    @model_validator(mode="after")
    def outcome_must_fail_closed(self) -> Self:
        has_oov = any(alternative.has_oov for alternative in self.alternatives)
        if self.status is KoreanMorphologyStatus.RESOLVED:
            if len(self.alternatives) != self.analyzer_fingerprint.top_n or has_oov:
                raise ValueError("resolved analysis requires two complete non-OOV alternatives")
            if self.reason_code is not KoreanReasonCode.ANALYSIS_RESOLVED:
                raise ValueError("resolved analysis requires its controlled reason code")
        elif self.status is KoreanMorphologyStatus.OOV:
            if not self.alternatives or not has_oov:
                raise ValueError("OOV analysis requires projected OOV evidence")
            if self.reason_code is not KoreanReasonCode.OOV_TOKEN:
                raise ValueError("OOV analysis requires its controlled reason code")
        elif self.status in {
            KoreanMorphologyStatus.UNAVAILABLE,
            KoreanMorphologyStatus.INVALID,
        } and self.alternatives:
            raise ValueError("unavailable or invalid analysis cannot carry alternatives")
        return self

    @property
    def passing(self) -> bool:
        return self.status is KoreanMorphologyStatus.RESOLVED


class KoreanLexicalIdentity(_FrozenContract):
    """Resolved source-backed Korean lemma/POS/sense identity."""

    submitted_form: str | None
    canonical_nfc: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    part_of_speech: str = Field(min_length=1)
    sense_id: str = Field(min_length=1)
    usage_register: str = Field(
        alias="register",
        serialization_alias="register",
        min_length=1,
    )
    morpheme_signature: tuple[KoreanSignatureItem, ...] = Field(min_length=1)
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    status: Literal["resolved"]

    @field_validator("submitted_form")
    @classmethod
    def submitted_form_must_be_acceptable(cls, value: str | None) -> str | None:
        if value is not None:
            canonicalize_korean(value)
        return value

    @field_validator("canonical_nfc", "lemma")
    @classmethod
    def canonical_values_must_be_nfc(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "Korean value")
        canonical = _require_canonical_text(value, field_name=field_name)
        if canonical.casefold() in _UNKNOWN_IDENTIFIERS:
            raise ValueError(f"{field_name} must identify a resolved value")
        return canonical

    @field_validator("part_of_speech", mode="before")
    @classmethod
    def part_of_speech_must_be_lexical(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Korean POS must be a supported lexical tag")
        return normalize_korean_pos(value)

    @field_validator("sense_id", "usage_register")
    @classmethod
    def identifiers_must_be_resolved(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "identity field")
        return _required_identifier(value, field_name=field_name)

    @model_validator(mode="after")
    def submitted_and_canonical_forms_must_agree(self) -> Self:
        if (
            self.submitted_form is not None
            and canonicalize_korean(self.submitted_form) != self.canonical_nfc
        ):
            raise ValueError("submitted form must normalize to canonical_nfc")
        return self

    @property
    def lexical_key(self) -> str:
        return korean_lexical_key(
            lemma=self.lemma,
            part_of_speech=self.part_of_speech,
            sense_id=self.sense_id,
        )

    @property
    def register(self) -> str:
        return self.usage_register


class KoreanMatchResult(_FrozenContract):
    """Explicit consensus outcome for a sentence and resolved target identity."""

    status: KoreanMatchStatus
    reason_code: KoreanReasonCode
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    alternative_matches: tuple[bool, ...] = Field(default=(), max_length=2)

    @model_validator(mode="after")
    def consensus_evidence_must_match_status(self) -> Self:
        if self.status is KoreanMatchStatus.MATCHED:
            if self.alternative_matches != (True, True):
                raise ValueError("matched status requires two matching analyses")
        elif self.status is KoreanMatchStatus.AMBIGUOUS:
            if (
                self.alternative_matches
                and sorted(self.alternative_matches) != [False, True]
            ):
                raise ValueError("ambiguous status requires one matching analysis")
        elif self.status is KoreanMatchStatus.MISMATCH:
            if self.alternative_matches != (False, False):
                raise ValueError("mismatch status requires two non-matching analyses")
        elif self.alternative_matches:
            raise ValueError("non-analysis match outcomes cannot carry match decisions")
        return self

    @property
    def matched(self) -> bool:
        return self.status is KoreanMatchStatus.MATCHED


class KoreanFrequencyRetrievalResult(_FrozenContract):
    """Read-only evidence for discovering and retrieving the exact NIKL TXT."""

    source_id: Literal["nikl-korean-learners-vocabulary"]
    landing_url: str = Field(min_length=1)
    accepted_filename: Literal["한국어 학습용 어휘 목록.txt"]
    landing_sha256: str = Field(min_length=64, max_length=64)
    attachment_url: str = Field(min_length=1)
    attachment_sha256: str = Field(min_length=64, max_length=64)
    source_bytes_sha256: str = Field(min_length=64, max_length=64)
    source_byte_count: int = Field(gt=0, le=20_000_000)
    retrieved_at: str = Field(min_length=1, max_length=64)
    text_encoding: Literal["utf-8"]
    schema_version: Literal["nikl-frequency-retrieval-v1"]

    @field_validator("landing_url")
    @classmethod
    def landing_url_must_be_fixed(cls, value: str) -> str:
        return _require_official_korean_url(value, field_name="landing URL", landing=True)

    @field_validator("attachment_url")
    @classmethod
    def attachment_url_must_be_official(cls, value: str) -> str:
        return _require_official_korean_url(value, field_name="attachment URL", landing=False)

    @field_validator("landing_sha256", "attachment_sha256", "source_bytes_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @property
    def grants_transform_power(self) -> bool:
        return False


class KoreanFrequencyBuildPolicy(_FrozenContract):
    """Exact source-use authority consumed by a transformation build."""

    source_id: Literal["nikl-korean-learners-vocabulary"]
    source_version: str = Field(min_length=1, max_length=128)
    allowed_use: Literal["local-generation", "test-fixture"]
    redistribution: Literal["not-approved", "approved-repository", "approved-publication"]
    attribution_required: bool
    storage_disposition: Literal["private-local-only", "repository-redistributable", "synthetic-test-only"]
    retrieval_sha256: str = Field(min_length=64, max_length=64)
    source_bytes_sha256: str = Field(min_length=64, max_length=64)
    analyzer_fingerprint: KoreanAnalyzerFingerprint

    @field_validator("source_version")
    @classmethod
    def source_version_must_be_resolved(cls, value: str) -> str:
        return _required_identifier(value, field_name="source_version")

    @field_validator("retrieval_sha256", "source_bytes_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def rights_and_storage_must_match(self) -> Self:
        if self.allowed_use == "test-fixture" and self.storage_disposition != "synthetic-test-only":
            raise ValueError("test fixture source policy requires synthetic storage")
        if self.redistribution == "not-approved" and self.storage_disposition == "repository-redistributable":
            raise ValueError("repository storage requires redistribution approval")
        return self


class KoreanFrequencyBuildResult(_FrozenContract):
    """Inactive transformation output bound to exact retrieval bytes and policy."""

    policy: KoreanFrequencyBuildPolicy
    retrieval_sha256: str = Field(min_length=64, max_length=64)
    source_bytes_sha256: str = Field(min_length=64, max_length=64)
    accepted_count: int = Field(ge=0, le=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT)
    rejection_count: int = Field(ge=0, le=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT)
    level_counts: dict[int, int]
    inventory_sha256: str = Field(min_length=64, max_length=64)
    rejection_sha256: str = Field(min_length=64, max_length=64)
    report_sha256: str = Field(min_length=64, max_length=64)
    bundle_sha256: str = Field(min_length=64, max_length=64)
    active: Literal[False]

    @field_validator(
        "retrieval_sha256",
        "source_bytes_sha256",
        "inventory_sha256",
        "rejection_sha256",
        "report_sha256",
        "bundle_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def output_must_match_policy_and_counts(self) -> Self:
        if self.retrieval_sha256 != self.policy.retrieval_sha256:
            raise ValueError("build result retrieval hash does not match policy")
        if self.source_bytes_sha256 != self.policy.source_bytes_sha256:
            raise ValueError("build result source hash does not match policy")
        if self.accepted_count != KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT:
            raise ValueError("Korean frequency build must contain exactly 3000 accepted entries")
        if self.rejection_count != KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT:
            raise ValueError("Korean frequency build must contain exactly 2965 rejections")
        if self.accepted_count + self.rejection_count != KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT:
            raise ValueError("Korean frequency source accounting must reconcile")
        if self.level_counts != {1: 1000, 2: 1000, 3: 1000}:
            raise ValueError("Korean frequency levels must be 1000/1000/1000")
        return self

    @property
    def total_source_dispositions(self) -> int:
        return self.accepted_count + self.rejection_count

    @property
    def grants_runtime_activation(self) -> bool:
        return False


class KoreanFrequencyTextAudioEvidence(_FrozenContract):
    """Hash-only Phase 32 authority tuple shared by DB-bound evidence rows."""

    phase31_pointer_locator_sha256: str | None = None
    phase31_pointer_content_sha256: str | None = None
    phase31_validation_receipt_sha256: str | None = None
    phase31_snapshot_manifest_sha256: str | None = None
    phase31_snapshot_root_sha256: str | None = None
    frequency_bundle_locator_sha256: str | None = None
    frequency_bundle_content_sha256: str | None = None
    provider_policy_sha256: str | None = None

    @field_validator(
        "phase31_pointer_locator_sha256",
        "phase31_pointer_content_sha256",
        "phase31_validation_receipt_sha256",
        "phase31_snapshot_manifest_sha256",
        "phase31_snapshot_root_sha256",
        "frequency_bundle_locator_sha256",
        "frequency_bundle_content_sha256",
        "provider_policy_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return value
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanFrequencyJobAuthority(_FrozenContract):
    """Hash-only staged authority for Korean frequency execution attempts."""

    stage: Literal["pilot_base", "pilot_audio", "full"]
    phase31_pointer_locator_sha256: str | None = None
    phase31_pointer_content_sha256: str | None = None
    phase31_validation_receipt_sha256: str | None = None
    phase31_snapshot_manifest_sha256: str | None = None
    phase31_snapshot_root_sha256: str | None = None
    frequency_bundle_locator_sha256: str | None = None
    frequency_bundle_content_sha256: str | None = None
    source_retrieval_sha256: str | None = None
    source_build_result_sha256: str | None = None
    source_review_aggregate_sha256: str | None = None
    provider_policy_sha256: str | None = None
    pilot_authority_sha256: str | None = None
    catalog_locator_sha256: str | None = None
    catalog_content_sha256: str | None = None
    profile_sample_authority_sha256: str | None = None
    provider_review_authority_sha256: str | None = None
    heard_review_authority_sha256: str | None = None

    @field_validator(
        "phase31_pointer_locator_sha256",
        "phase31_pointer_content_sha256",
        "phase31_validation_receipt_sha256",
        "phase31_snapshot_manifest_sha256",
        "phase31_snapshot_root_sha256",
        "frequency_bundle_locator_sha256",
        "frequency_bundle_content_sha256",
        "source_retrieval_sha256",
        "source_build_result_sha256",
        "source_review_aggregate_sha256",
        "provider_policy_sha256",
        "pilot_authority_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
        "profile_sample_authority_sha256",
        "provider_review_authority_sha256",
        "heard_review_authority_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return value
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def required_hashes_must_match_stage(self) -> Self:
        base_required = {
            "phase31_pointer_locator_sha256",
            "phase31_pointer_content_sha256",
            "phase31_validation_receipt_sha256",
            "phase31_snapshot_manifest_sha256",
            "phase31_snapshot_root_sha256",
            "frequency_bundle_locator_sha256",
            "frequency_bundle_content_sha256",
            "source_retrieval_sha256",
            "source_build_result_sha256",
            "source_review_aggregate_sha256",
            "provider_policy_sha256",
            "pilot_authority_sha256",
        }
        audio_required = {
            "catalog_locator_sha256",
            "catalog_content_sha256",
            "profile_sample_authority_sha256",
        }
        full_required = {
            "provider_review_authority_sha256",
            "heard_review_authority_sha256",
        }
        required = set(base_required)
        if self.stage in {"pilot_audio", "full"}:
            required |= audio_required
        if self.stage == "full":
            required |= full_required
        missing = [field for field in sorted(required) if getattr(self, field) is None]
        if missing:
            raise ValueError(f"Korean frequency authority is missing required hashes: {missing}")
        return self


class KoreanFrequencyEntry(_FrozenContract):
    """One final Korean frequency identity from the approved frozen bundle."""

    language: Literal["ko"]
    version: str = Field(min_length=1, max_length=128)
    level: int = Field(ge=1, le=3)
    final_rank: int = Field(ge=1, le=KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT)
    source_rank: int = Field(ge=1, le=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT)
    source_provenance: str = Field(min_length=1, max_length=128)
    source_version: str = Field(min_length=1, max_length=128)
    license_decision: str = Field(min_length=1, max_length=128)
    storage_disposition: Literal["private-local-only", "repository-redistributable", "synthetic-test-only"]
    curation_decision: Literal["accepted"]
    curation_flags: tuple[str, ...] = Field(min_length=1, max_length=16)
    grounding_confidence: Literal["source-backed", "reviewed-source-backed"]
    bundle_sha256: str = Field(min_length=64, max_length=64)
    retrieval_sha256: str = Field(min_length=64, max_length=64)
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    lexical_identity: KoreanLexicalIdentity

    @field_validator("version", "source_provenance", "source_version", "license_decision")
    @classmethod
    def identifiers_must_be_resolved(cls, value: str, info: object) -> str:
        return _required_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("curation_flags")
    @classmethod
    def curation_flags_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _foundation_identifiers(value, field_name="curation flags")

    @field_validator("bundle_sha256", "retrieval_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def identity_must_match_entry_authority(self) -> Self:
        expected_level = ((self.final_rank - 1) // KOREAN_FREQUENCY_EXPECTED_LEVEL_COUNT) + 1
        if self.level != expected_level:
            raise ValueError("Korean frequency level must match final rank window")
        if self.lexical_identity.analyzer_fingerprint != self.analyzer_fingerprint:
            raise ValueError("Korean frequency identity analyzer fingerprint drift")
        if self.lexical_identity.status != "resolved":
            raise ValueError("Korean frequency identity must be resolved")
        return self


class KoreanFrequencyBundleMember(_FrozenContract):
    """One hash-bound member of a Korean frequency bundle."""

    relative_path: str = Field(min_length=1, max_length=256)
    sha256: str = Field(min_length=64, max_length=64)
    byte_count: int = Field(gt=0, le=100_000_000)
    row_count: int = Field(ge=0, le=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT)
    kind: Literal["attribution", "curated-inventory", "rejections", "curation-report", "source-snapshot"]

    @field_validator("relative_path")
    @classmethod
    def relative_path_must_be_safe(cls, value: str) -> str:
        return _safe_relative_path(value, field_name="relative path")

    @field_validator("sha256")
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_identifier(value, field_name="member hash")


class KoreanFrequencyBundleManifest(_FrozenContract):
    """Root manifest binding Korean frequency source, members, and counts."""

    schema_version: Literal["korean-frequency-bundle-v1"]
    language: Literal["ko"]
    version: str = Field(min_length=1, max_length=128)
    source_id: Literal["nikl-korean-learners-vocabulary"]
    source_version: str = Field(min_length=1, max_length=128)
    license_decision: str = Field(min_length=1, max_length=128)
    storage_disposition: Literal["private-local-only", "repository-redistributable", "synthetic-test-only"]
    synthetic: bool
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    members: tuple[KoreanFrequencyBundleMember, ...] = Field(min_length=1, max_length=12)
    inventory_sha256: str = Field(min_length=64, max_length=64)
    rejection_sha256: str = Field(min_length=64, max_length=64)
    report_sha256: str = Field(min_length=64, max_length=64)
    bundle_sha256: str = Field(min_length=64, max_length=64)
    level_counts: dict[int, int]
    entry_count: int = Field(ge=0, le=KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT)
    rejection_count: int = Field(ge=0, le=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT)

    @field_validator("version", "source_version", "license_decision")
    @classmethod
    def identifiers_must_be_resolved(cls, value: str, info: object) -> str:
        return _required_identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("inventory_sha256", "rejection_sha256", "report_sha256", "bundle_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def manifest_must_be_count_and_authority_consistent(self) -> Self:
        if self.synthetic and self.storage_disposition != "synthetic-test-only":
            raise ValueError("synthetic Korean frequency bundles cannot be production storage")
        if self.entry_count != KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT:
            raise ValueError("Korean frequency manifest must contain exactly 3000 entries")
        if self.rejection_count != KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT:
            raise ValueError("Korean frequency manifest must contain exactly 2965 rejections")
        if self.level_counts != {1: 1000, 2: 1000, 3: 1000}:
            raise ValueError("Korean frequency manifest levels must be 1000/1000/1000")
        if self.entry_count + self.rejection_count != KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT:
            raise ValueError("Korean frequency manifest accounting must reconcile")
        member_hashes = {member.kind: member.sha256 for member in self.members}
        if member_hashes.get("curated-inventory") not in {None, self.inventory_sha256}:
            raise ValueError("inventory member hash drift")
        if member_hashes.get("rejections") not in {None, self.rejection_sha256}:
            raise ValueError("rejection member hash drift")
        if member_hashes.get("curation-report") not in {None, self.report_sha256}:
            raise ValueError("report member hash drift")
        return self

    @property
    def production_eligible(self) -> bool:
        return (
            not self.synthetic
            and self.storage_disposition == "repository-redistributable"
            and self.license_decision == "approved-redistribution"
        )


def validate_korean_frequency_accounting(
    entries: tuple[KoreanFrequencyEntry, ...],
    *,
    source_candidate_count: int,
    rejection_count: int,
) -> dict[int, int]:
    """Validate exact final Korean frequency counts and identity uniqueness."""

    if source_candidate_count != KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT:
        raise ValueError("Korean frequency source count must be 5965")
    if rejection_count != KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT:
        raise ValueError("Korean frequency rejection count must be 2965")
    if len(entries) != KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT:
        raise ValueError("Korean frequency inventory must contain exactly 3000 entries")
    if len(entries) + rejection_count != source_candidate_count:
        raise ValueError("Korean frequency accounting must reconcile")
    ranks = tuple(entry.final_rank for entry in entries)
    if ranks != tuple(range(1, KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT + 1)):
        raise ValueError("Korean frequency ranks must be contiguous")
    identity_keys = tuple(entry.lexical_identity.lexical_key for entry in entries)
    if len(identity_keys) != len(set(identity_keys)):
        raise ValueError("Korean frequency identities must be unique")
    level_counts = {level: sum(1 for entry in entries if entry.level == level) for level in (1, 2, 3)}
    if level_counts != {1: 1000, 2: 1000, 3: 1000}:
        raise ValueError("Korean frequency levels must be 1000/1000/1000")
    return level_counts


__all__ = [
    "KOREAN_LANGUAGE_CODE",
    "KOREAN_FOUNDATION_DEFAULT_SOURCE",
    "KOREAN_FOUNDATION_HISTORY_SOURCE",
    "KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT",
    "KOREAN_FREQUENCY_EXPECTED_FILENAME",
    "KOREAN_FREQUENCY_EXPECTED_LEVEL_COUNT",
    "KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT",
    "KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT",
    "KOREAN_FREQUENCY_LANDING_URL",
    "KOREAN_FREQUENCY_RETRIEVAL_SCHEMA_VERSION",
    "KOREAN_FREQUENCY_SCHEMA_VERSION",
    "KOREAN_FREQUENCY_SOURCE_ID",
    "KOREAN_LANGUAGE_VARIANT",
    "KOREAN_LEXICAL_POS_TAGS",
    "KOREAN_MORPHOLOGY_POLICY_VERSION",
    "KOREAN_PROVIDER_LOCALE",
    "KoreanAnalysisAlternative",
    "KoreanAnalyzerFingerprint",
    "KoreanConcept",
    "KoreanCurriculumEvidence",
    "KoreanFrequencyBuildPolicy",
    "KoreanFrequencyBuildResult",
    "KoreanFrequencyBundleManifest",
    "KoreanFrequencyBundleMember",
    "KoreanFrequencyEntry",
    "KoreanFrequencyJobAuthority",
    "KoreanFrequencyRetrievalResult",
    "KoreanFrequencyTextAudioEvidence",
    "KoreanLexicalIdentity",
    "KoreanMatchResult",
    "KoreanMatchStatus",
    "KoreanMorphemeEvidence",
    "KoreanMorphologyResult",
    "KoreanMorphologyStatus",
    "KoreanPedagogicalJamoMapping",
    "KoreanPronunciationEvidence",
    "KoreanReasonCode",
    "KoreanReviewStatus",
    "KoreanSignatureItem",
    "KoreanTextError",
    "KoreanWordAnalysis",
    "canonicalize_korean",
    "canonical_json_sha256",
    "compose_modern_hangul",
    "decompose_modern_hangul",
    "korean_lexical_key",
    "normalize_korean_pos",
    "raw_bytes_sha256",
    "validate_korean_frequency_accounting",
]
