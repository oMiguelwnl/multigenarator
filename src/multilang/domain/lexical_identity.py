"""Source-backed semantic identities, morphology and important-form policies."""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from hashlib import sha256
from typing import Annotated, Literal, Protocol, Self

from pydantic import Field, computed_field, field_validator, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256

UnitDecimal = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]
_UNKNOWN = {"unknown", "unresolved", "none", "null", "?", "unk", "x"}
_FEATURES = {
    "tense",
    "mood",
    "person",
    "number",
    "case",
    "gender",
    "aspect",
    "register",
    "voice",
    "degree",
    "animacy",
    "definiteness",
    "polarity",
    "possessive",
}
_FORM_REASONS = {
    "irregularity",
    "frequency",
    "unpredictability",
    "ambiguity",
    "unexpected_pronunciation",
    "prerequisite",
    "learning_difficulty",
}


def canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def normalize_identity_text(value: str) -> str:
    """Preserve case, script and diacritics; normalization never infers a lemma."""
    text = " ".join(unicodedata.normalize("NFC", value).split())
    if (
        not text
        or len(text) > 512
        or any(unicodedata.category(c).startswith("C") for c in text)
    ):
        raise ValueError(
            "lexical text must be nonempty bounded NFC text without control characters"
        )
    return text


class LexicalIdentity(NativeContract):
    language: SupportedLanguage
    normalized_lemma: str = Field(min_length=1, max_length=512)
    part_of_speech: Identifier
    sense_id: Identifier
    profile_version: Identifier
    normalizer_version: Identifier
    analyzer_version: Identifier
    source_id: Identifier
    source_version: Identifier
    source_sha256: Sha256
    namespace_version: Annotated[str, Field(pattern=r"^[a-zA-Z0-9._-]{1,16}$")] = "1"
    revision: int = Field(default=1, ge=1)
    aliases: tuple[Identifier, ...] = ()

    @field_validator("normalized_lemma")
    @classmethod
    def canonical_lemma(cls, value: str) -> str:
        return normalize_identity_text(value)

    @field_validator("part_of_speech", "sense_id")
    @classmethod
    def resolved_identifier(cls, value: str) -> str:
        value = unicodedata.normalize("NFC", value)
        if value.casefold() in _UNKNOWN:
            raise ValueError("lexical identity requires resolved POS and sense")
        return value

    @computed_field
    @property
    def lexical_identity_id(self) -> str:
        payload = {
            "language": self.language.value,
            "lemma": self.normalized_lemma,
            "part_of_speech": self.part_of_speech,
            "sense_id": self.sense_id,
            "namespace_version": self.namespace_version,
        }
        return f"lex:{self.namespace_version}:{canonical_sha256(payload)}"

    @property
    def lemma(self) -> str:
        return self.normalized_lemma


class LexicalIdentityContract(Protocol):
    def get_identity(self, lexical_identity_id: str) -> LexicalIdentity | None: ...


class MorphologicalAnalysis(NativeContract):
    lexical_identity_id: Identifier
    analyzer_id: Identifier
    analyzer_version: Identifier
    features: dict[str, Identifier] = Field(default_factory=dict)
    confidence: UnitDecimal
    evidence_sha256: Sha256
    sense_context: str | None = Field(default=None, max_length=2000)

    @field_validator("features")
    @classmethod
    def canonical_features(cls, value: dict[str, str]) -> dict[str, str]:
        if set(value) - _FEATURES:
            raise ValueError("unknown morphological feature")
        if any(item.casefold() in _UNKNOWN for item in value.values()):
            raise ValueError("unresolved morphological feature")
        return {key: unicodedata.normalize("NFC", value[key]) for key in sorted(value)}

    @computed_field
    @property
    def morphological_analysis_id(self) -> str:
        return "analysis:" + canonical_sha256(
            {
                "parent": self.lexical_identity_id,
                "features": self.features,
                "context": self.sense_context,
            }
        )


class SurfaceForm(NativeContract):
    lexical_identity_id: Identifier
    text: str = Field(min_length=1, max_length=512)
    analysis: MorphologicalAnalysis
    source_id: Identifier
    source_sha256: Sha256
    attestation: int = Field(ge=0)
    context: str | None = Field(default=None, max_length=2000)
    evidence_values: dict[str, UnitDecimal] = Field(default_factory=dict)
    prerequisite_depth: int = Field(default=1, ge=1, le=100)

    @field_validator("text")
    @classmethod
    def canonical_surface(cls, value: str) -> str:
        return normalize_identity_text(value)

    @model_validator(mode="after")
    def parent_and_evidence_match(self) -> Self:
        if self.analysis.lexical_identity_id != self.lexical_identity_id:
            raise ValueError(
                "surface analysis must belong to the same lexical identity"
            )
        if set(self.evidence_values) - _FORM_REASONS:
            raise ValueError("unsupported important-form reason")
        return self

    @computed_field
    @property
    def surface_form_id(self) -> str:
        return "form:" + canonical_sha256(
            {
                "parent": self.lexical_identity_id,
                "surface": self.text,
                "analysis": self.analysis.morphological_analysis_id,
            }
        )


class ImportantFormSelection(NativeContract):
    form: SurfaceForm
    score: UnitDecimal
    policy_sha256: Sha256


class ImportantFormCriteria(NativeContract):
    """Scoring proposal; production uses ImportantFormPolicy with an approval receipt."""
    policy_id: Identifier
    version: Identifier
    weights: dict[str, UnitDecimal]
    minimum_score: UnitDecimal
    attestation_threshold: int = Field(ge=1)
    analysis_confidence_threshold: UnitDecimal
    score_precision: int = Field(default=8, ge=0, le=18)
    intermediate_precision: int = Field(default=50, ge=28, le=100)
    missing_evidence: Literal["zero", "reject"] = "zero"

    @model_validator(mode="after")
    def complete_policy(self) -> Self:
        if not self.weights or set(self.weights) - _FORM_REASONS:
            raise ValueError("policy requires supported evidence kinds")
        if sum(self.weights.values(), Decimal(0)) != Decimal(1):
            raise ValueError("important-form evidence weights must sum exactly to 1")
        return self

    @computed_field
    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(
            self.model_dump(mode="json", exclude_computed_fields=True)
        )

    def select(
        self, forms: Iterable[SurfaceForm]
    ) -> tuple[ImportantFormSelection, ...]:
        """Return every approved form; quotas, budgets and top-N cannot remove forms."""
        candidates: dict[str, ImportantFormSelection] = {}
        with localcontext() as context:
            context.prec = self.intermediate_precision
            context.rounding = ROUND_HALF_EVEN
            for form in forms:
                score = self.score_evidence(
                    form.evidence_values, form.attestation, form.analysis.confidence
                )
                if score is None:
                    continue
                selected = ImportantFormSelection(
                    form=form, score=score, policy_sha256=self.policy_sha256
                )
                existing = candidates.get(form.surface_form_id)
                if existing is not None and existing != selected:
                    raise ValueError("conflicting evidence for the same important form")
                candidates[form.surface_form_id] = selected
        return tuple(
            sorted(
                candidates.values(),
                key=lambda item: (
                    item.form.prerequisite_depth,
                    -item.score,
                    item.form.text,
                    item.form.analysis.morphological_analysis_id,
                ),
            )
        )

    def score_evidence(
        self, values: dict[str, Decimal], attestation: int,
        analysis_confidence: Decimal | None,
    ) -> Decimal | None:
        """Use the same arithmetic in selection and calibration; unknown stays closed."""
        if analysis_confidence is None:
            return None
        if not analysis_confidence.is_finite() or not 0 <= analysis_confidence <= 1:
            raise ValueError("invalid analysis confidence")
        if attestation < 0 or any(not v.is_finite() or not 0 <= v <= 1 for v in values.values()):
            raise ValueError("invalid form evidence")
        if self.missing_evidence == "reject" and set(self.weights) - set(values):
            return None
        with localcontext() as arithmetic:
            arithmetic.prec = self.intermediate_precision
            arithmetic.rounding = ROUND_HALF_EVEN
            score = sum((weight * values.get(reason, Decimal(0))
                         for reason, weight in sorted(self.weights.items())), Decimal(0))
            score = score.quantize(Decimal(1).scaleb(-self.score_precision))
        if (score < self.minimum_score or attestation < self.attestation_threshold
                or analysis_confidence < self.analysis_confidence_threshold):
            return None
        return score


class ImportantFormPolicy(ImportantFormCriteria):
    approval_sha256: Sha256


class MultiWordExpression(NativeContract):
    identity: LexicalIdentity
    segments: tuple[Identifier, ...] = Field(min_length=2)
    variants: tuple[str, ...] = ()
    segmentation_version: Identifier = "1"

    @model_validator(mode="after")
    def segmentation_must_match(self) -> Self:
        joined = " ".join(self.segments)
        if normalize_identity_text(joined) != self.identity.normalized_lemma:
            raise ValueError("explicit MWE segments must reconstruct the lexical lemma")
        return self
