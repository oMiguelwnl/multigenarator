"""Validated source-pack contract for the frozen Classical Latin MVP manifest."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from multilang.domain.latin import DEFAULT_LATIN_SOURCE_PACK_VERSION, LATIN_LANGUAGE_CODE, LATIN_MVP_CARD_COUNT, LatinVariant


LatinSourceType = Literal["original_classical", "adapted_didactic", "reference_example"]
LatinLicenseGate = Literal["approved", "blocked"]
LatinInclusionStatus = Literal["included", "deferred", "replacement"]
LatinTargetMatchMode = Literal["exact", "orthographic_normalization", "enclitic_normalization"]
LatinCaseLabel = Literal["Nominativus", "Vocativus", "Accusativus", "Genitivus", "Dativus", "Ablativus"]
LatinPartOfSpeech = Literal["subst", "adj", "v", "pron", "prep", "conj", "adv"]
LatinGrammarNumber = Literal["sg", "pl"]
LatinSyntacticFunction = Literal["Suj", "OD", "OI", "Pred", "Circ", "Conj", "Mod", "V"]
LatinGrammarReviewStatus = Literal["approved", "unresolved", "ambiguous"]

DEFAULT_LATIN_MVP_SOURCE_PACK_PATH = Path("data") / "latin_mvp" / "latin-mvp-50-v1.json"
APPROVED_LATIN_CASE_LABELS: tuple[str, ...] = (
    "Nominativus",
    "Vocativus",
    "Accusativus",
    "Genitivus",
    "Dativus",
    "Ablativus",
)
APPROVED_LATIN_GRAMATICA_TOKENS: frozenset[str] = frozenset(
    {
        *APPROVED_LATIN_CASE_LABELS,
        "subst",
        "adj",
        "v",
        "pron",
        "prep",
        "conj",
        "adv",
        "sg",
        "pl",
        "Suj",
        "OD",
        "OI",
        "Pred",
        "Circ",
        "Conj",
        "Mod",
        "V",
        "pres",
        "imperf",
        "fut",
        "perf",
        "plup",
        "ind",
        "subj",
        "imp",
        "inf",
        "act",
        "pass",
        "1sg",
        "2sg",
        "3sg",
        "1pl",
        "2pl",
        "3pl",
    }
)
_GRAMATICA_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_GRAMATICA_ALLOWED_RE = re.compile(r"^[A-Za-z0-9 ,;:/()+.-]+$")
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_MACRON_MAP = str.maketrans(
    {
        "ā": "a",
        "ē": "e",
        "ī": "i",
        "ō": "o",
        "ū": "u",
        "ȳ": "y",
        "Ā": "a",
        "Ē": "e",
        "Ī": "i",
        "Ō": "o",
        "Ū": "u",
        "Ȳ": "y",
    }
)
_ENCLITICS = ("que", "ve", "ne")


def _not_blank(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("required text field must not be blank")
    return stripped


def _strip_macrons(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.translate(_MACRON_MAP))
    return "".join(character for character in normalized if not unicodedata.combining(character)).casefold()


def _tokens(value: str) -> list[str]:
    return [match.group(0).casefold() for match in _TOKEN_RE.finditer(value)]


def validate_latin_target_presence(target_form: str, latin_sentence: str, match_mode: LatinTargetMatchMode) -> bool:
    """Return whether the displayed target form occurs as a whole Latin token."""

    target = target_form.strip().casefold()
    if not target or not latin_sentence.strip():
        return False
    sentence_tokens = _tokens(latin_sentence)
    if match_mode == "exact":
        return target in sentence_tokens

    normalized_target = _strip_macrons(target)
    normalized_tokens = [_strip_macrons(token) for token in sentence_tokens]
    if match_mode == "orthographic_normalization":
        return normalized_target in normalized_tokens

    if normalized_target in normalized_tokens:
        return True
    return any(
        token == f"{normalized_target}{enclitic}"
        for token in normalized_tokens
        for enclitic in _ENCLITICS
    )


def validate_latin_gramatica(value: str) -> str:
    """Validate and normalize the learner-facing concise Latin grammar note."""

    gramatica = _not_blank(value)
    if not _GRAMATICA_ALLOWED_RE.fullmatch(gramatica):
        raise ValueError("gramatica contains unapproved punctuation or characters")
    tokens = _GRAMATICA_TOKEN_RE.findall(gramatica)
    if not tokens:
        raise ValueError("gramatica must include approved grammar tokens")
    unknown = [token for token in tokens if token not in APPROVED_LATIN_GRAMATICA_TOKENS]
    if unknown:
        raise ValueError(f"gramatica contains unapproved grammar token: {unknown[0]}")
    return gramatica


class LatinMorphologyEvidence(BaseModel):
    """Reviewed morphology evidence for the target form in one Latin MVP sentence."""

    lemma: str = Field(min_length=1)
    part_of_speech: LatinPartOfSpeech
    case_label: LatinCaseLabel | None = None
    number: LatinGrammarNumber | None = None
    verbal_analysis: str | None = None
    syntactic_function: LatinSyntacticFunction
    evidence_note: str = Field(min_length=1)
    grammar_review_status: LatinGrammarReviewStatus = "approved"

    _strip_text = field_validator("lemma", "syntactic_function", "evidence_note")(_not_blank)

    @field_validator("verbal_analysis")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _not_blank(value)

    @model_validator(mode="after")
    def enforce_resolved_morphology(self) -> "LatinMorphologyEvidence":
        if self.grammar_review_status != "approved":
            raise ValueError("grammar_review_status must be approved")
        if self.part_of_speech in {"subst", "adj", "pron"}:
            if self.case_label is None:
                raise ValueError("nominal morphology requires case_label")
            if self.number is None:
                raise ValueError("nominal morphology requires number")
        if self.part_of_speech == "v" and self.verbal_analysis is None:
            raise ValueError("verbal morphology requires verbal_analysis")
        return self


class LatinSourceProvenance(BaseModel):
    """Auditable origin and license metadata for a source-pack entry."""

    source_type: LatinSourceType
    citation: str = Field(min_length=1)
    work_reference: str = Field(min_length=1)
    source_url_or_id: str = Field(min_length=1)
    license_note: str = Field(min_length=1)
    license_gate: LatinLicenseGate = "approved"
    original_citation_claim: bool = False

    _strip_text = field_validator("citation", "work_reference", "source_url_or_id", "license_note")(_not_blank)

    @model_validator(mode="after")
    def enforce_license_and_source_truthfulness(self) -> "LatinSourceProvenance":
        if self.license_gate != "approved":
            raise ValueError("license_gate must be approved for the frozen Latin MVP source pack")
        if self.source_type == "adapted_didactic" and self.original_citation_claim:
            raise ValueError("adapted didactic entries cannot claim an original citation")
        return self


class LatinDidacticRationale(BaseModel):
    """Frequency and sequencing rationale for a source-pack entry."""

    inclusion_status: LatinInclusionStatus = "included"
    inclusion_rationale: str = Field(min_length=1)
    didactic_order_rationale: str = Field(min_length=1)

    _strip_text = field_validator("inclusion_rationale", "didactic_order_rationale")(_not_blank)


class LatinMvpSourcePackEntry(LatinSourceProvenance, LatinDidacticRationale):
    """One validated card seed in the frozen 50-card Classical Latin MVP manifest."""

    item_key: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    lemma: str = Field(min_length=1)
    target_form: str = Field(min_length=1)
    latin_sentence: str = Field(min_length=1)
    frequency_rank: int = Field(ge=1)
    frequency_source: str = Field(min_length=1)
    frequency_source_url: HttpUrl
    source_pack_version: Literal["latin-mvp-50-v1"] = DEFAULT_LATIN_SOURCE_PACK_VERSION
    target_match_mode: LatinTargetMatchMode = "exact"
    morphology_evidence: LatinMorphologyEvidence
    gramatica: str = Field(min_length=1)

    _strip_text = field_validator(
        "item_key",
        "lemma",
        "target_form",
        "latin_sentence",
        "frequency_source",
        "inclusion_rationale",
        "didactic_order_rationale",
        "citation",
        "work_reference",
        "source_url_or_id",
        "license_note",
        "gramatica",
    )(_not_blank)

    @field_validator("gramatica")
    @classmethod
    def validate_gramatica_field(cls, value: str) -> str:
        return validate_latin_gramatica(value)

    @model_validator(mode="after")
    def validate_entry_contract(self) -> "LatinMvpSourcePackEntry":
        expected_key = f"latin-mvp-{self.sequence:04d}"
        if self.item_key != expected_key:
            raise ValueError(f"item_key must be {expected_key} for sequence {self.sequence}")
        if not validate_latin_target_presence(self.target_form, self.latin_sentence, self.target_match_mode):
            raise ValueError("target_form must appear in latin_sentence using target_match_mode")
        if self.morphology_evidence.lemma != self.lemma:
            raise ValueError("morphology_evidence lemma must match entry lemma")
        return self


class LatinMvpSourcePack(BaseModel):
    """Validated frozen Classical Latin MVP source-pack manifest."""

    language_code: Literal["la"] = LATIN_LANGUAGE_CODE
    variant: LatinVariant = LatinVariant.CLASSICAL
    source_pack_version: Literal["latin-mvp-50-v1"] = DEFAULT_LATIN_SOURCE_PACK_VERSION
    card_count: Literal[50] = LATIN_MVP_CARD_COUNT
    frequency_attribution: str = Field(min_length=1)
    license_attribution: str = Field(min_length=1)
    entries: list[LatinMvpSourcePackEntry]

    _strip_text = field_validator("frequency_attribution", "license_attribution")(_not_blank)

    @model_validator(mode="after")
    def validate_pack_invariants(self) -> "LatinMvpSourcePack":
        if len(self.entries) != LATIN_MVP_CARD_COUNT:
            raise ValueError("Latin MVP source pack must contain exactly 50 entries")
        expected_keys = [f"latin-mvp-{index:04d}" for index in range(1, LATIN_MVP_CARD_COUNT + 1)]
        actual_keys = [entry.item_key for entry in self.entries]
        if actual_keys != expected_keys:
            raise ValueError("entries must be ordered by item_key latin-mvp-0001 through latin-mvp-0050")
        actual_sequences = [entry.sequence for entry in self.entries]
        if actual_sequences != list(range(1, LATIN_MVP_CARD_COUNT + 1)):
            raise ValueError("entries must have sequence numbers 1 through 50")
        if any(entry.source_pack_version != self.source_pack_version for entry in self.entries):
            raise ValueError("every entry source_pack_version must match the pack version")
        included_lemmas = [entry.lemma.casefold() for entry in self.entries if entry.inclusion_status == "included"]
        duplicates = [lemma for lemma, count in Counter(included_lemmas).items() if count > 1]
        if duplicates:
            raise ValueError("included lemmas must be unique")
        return self


def load_latin_mvp_source_pack(path: Path | None = None) -> LatinMvpSourcePack:
    """Load and validate the frozen Latin MVP source pack from committed JSON."""

    manifest_path = path or DEFAULT_LATIN_MVP_SOURCE_PACK_PATH
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return LatinMvpSourcePack.model_validate(payload)
    except FileNotFoundError as exc:
        raise ValueError("Latin MVP source pack is missing for latin-mvp-50-v1") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Latin MVP source pack JSON is malformed for latin-mvp-50-v1") from exc
    except Exception as exc:
        if exc.__class__.__module__.startswith("pydantic"):
            raise ValueError(f"Latin MVP source pack failed validation for {DEFAULT_LATIN_SOURCE_PACK_VERSION}: {exc}") from exc
        raise


__all__ = [
    "APPROVED_LATIN_CASE_LABELS",
    "APPROVED_LATIN_GRAMATICA_TOKENS",
    "DEFAULT_LATIN_MVP_SOURCE_PACK_PATH",
    "LatinDidacticRationale",
    "LatinGrammarReviewStatus",
    "LatinMorphologyEvidence",
    "LatinMvpSourcePack",
    "LatinMvpSourcePackEntry",
    "LatinSourceProvenance",
    "load_latin_mvp_source_pack",
    "validate_latin_gramatica",
    "validate_latin_target_presence",
]
