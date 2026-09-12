"""Validation and EVAL-01 evidence contracts, independent of provider judgments."""

from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Literal, Protocol, Self

from pydantic import Field, computed_field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import UnitDecimal, canonical_sha256


class ValidationFinding(NativeContract):
    code: Identifier
    subject_id: str = Field(default="", max_length=256)
    severity: Literal["error", "warning"] = "error"


class ValidationReport(NativeContract):
    validator: Identifier
    findings: tuple[ValidationFinding, ...] = ()
    checked_count: int = Field(default=1, ge=0)

    @computed_field
    @property
    def valid(self) -> bool:
        return self.checked_count > 0 and not any(
            item.severity == "error" for item in self.findings
        )

    def require_valid(self) -> None:
        if not self.valid:
            raise ValueError(
                "validation failed: " + ", ".join(item.code for item in self.findings)
            )


class ValidationContract(Protocol):
    def validate(self, value: object) -> ValidationReport: ...


EVALUATION_DIMENSIONS = (
    "definition",
    "form_analysis",
    "naturalness",
    "target_sense_match",
    "translation",
    "i_plus_one",
    "pronunciation_audio",
    "anki_safety",
    "ambiguity",
    "resolution",
)


class EvaluationDataset(NativeContract):
    dataset_id: Identifier
    version: Identifier
    language: SupportedLanguage
    sha256: Sha256
    source_id: Identifier
    source_version: Identifier
    source_sha256: Sha256
    stratum: Identifier
    case_count: int = Field(ge=1)
    source_type: Literal["core", "custom", "highlight", "held_out"] = "held_out"
    golden: bool = False


class MetricThreshold(NativeContract):
    """Thresholds must be supplied with evidence; this module does not invent them."""

    minimum_pass_rate: UnitDecimal
    regression_tolerance: UnitDecimal
    baseline_pass_rate: UnitDecimal
    baseline_dataset_sha256: Sha256
    evidence_sha256: Sha256
    signed_baseline_sha256: Sha256


class DimensionEvaluation(NativeContract):
    dimension: Identifier
    dataset: EvaluationDataset
    eligible_cases: int = Field(ge=0)
    excluded_cases: int = Field(default=0, ge=0)
    passed_cases: int = Field(ge=0)
    critical_failures: int = Field(ge=0)
    threshold: MetricThreshold
    rubric_version: Literal["0-wrong-1-major-2-correction-3-minor-4-release"] = (
        "0-wrong-1-major-2-correction-3-minor-4-release"
    )

    @model_validator(mode="after")
    def accounting_matches_dataset(self) -> Self:
        if self.dimension not in EVALUATION_DIMENSIONS:
            raise ValueError("unknown evaluation dimension")
        if (
            self.passed_cases > self.eligible_cases
            or self.critical_failures > self.eligible_cases
        ):
            raise ValueError("evaluation outcome counts exceed eligible cases")
        if self.eligible_cases + self.excluded_cases > self.dataset.case_count:
            raise ValueError("evaluation sample exceeds the checksummed dataset")
        return self

    @computed_field
    @property
    def pass_rate(self) -> Decimal | None:
        with localcontext() as context:
            context.prec = 50
            return (
                Decimal(self.passed_cases) / Decimal(self.eligible_cases)
                if self.eligible_cases
                else None
            )

    @computed_field
    @property
    def critical_failure_rate(self) -> Decimal | None:
        with localcontext() as context:
            context.prec = 50
            return (
                Decimal(self.critical_failures) / Decimal(self.eligible_cases)
                if self.eligible_cases
                else None
            )

    @computed_field
    @property
    def regression_delta(self) -> Decimal | None:
        with localcontext() as context:
            context.prec = 50
            rate = self.pass_rate
            return (
                rate - self.threshold.baseline_pass_rate if rate is not None else None
            )


class IndependentEvaluationReview(NativeContract):
    producer_id: Identifier
    reviewer_id: Identifier
    reviewer_kind: Literal["human", "expert", "llm"]
    receipt_sha256: Sha256


class LanguageEvaluation(NativeContract):
    language: SupportedLanguage
    profile_version: Identifier
    analyzer_version: Identifier
    evaluations: tuple[DimensionEvaluation, ...] = Field(min_length=1, max_length=10000)
    review: IndependentEvaluationReview
    qualification: bool = False

    @model_validator(mode="after")
    def language_and_strata_match(self) -> Self:
        if any(row.dataset.language != self.language for row in self.evaluations):
            raise ValueError("evaluation dataset language drift")
        keys = [
            (row.dimension, row.dataset.dataset_id, row.dataset.stratum)
            for row in self.evaluations
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate dimension/source/stratum evaluation")
        return self

    @computed_field
    @property
    def manifest_sha256(self) -> str:
        return canonical_sha256(
            self.model_dump(mode="json", exclude_computed_fields=True)
        )


class MigrationValidationEvidence(NativeContract):
    source_sha256: Sha256
    target_sha256: Sha256
    backup_sha256: Sha256
    restored_sha256: Sha256
    confirmation_sha256: Sha256
    expected_confirmation_sha256: Sha256
    expected_source_sha256: Sha256 | None = None
