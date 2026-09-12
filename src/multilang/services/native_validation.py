"""Small validation adapters around the shared native domain contracts."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ValidationError

from multilang.domain.content import ContentVersion, GeneratedContent
from multilang.domain.datasets import DatasetManifest
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import LanguageProfile
from multilang.domain.lexical_identity import LexicalIdentity
from multilang.domain.validation import (
    EVALUATION_DIMENSIONS,
    DimensionEvaluation,
    LanguageEvaluation,
    MigrationValidationEvidence,
    ValidationFinding,
    ValidationReport,
)
from multilang.services.native_content import validate_plain_content


def _payload(value: Any) -> Any:
    return (
        value.model_dump(mode="json", round_trip=True)
        if isinstance(value, BaseModel)
        else value
    )


def _finding(code: str, subject_id: str = "") -> ValidationFinding:
    return ValidationFinding(code=code, subject_id=subject_id)


class LexicalValidator:
    def validate(
        self, value: object, *, profile: LanguageProfile | None = None
    ) -> ValidationReport:
        findings = []
        try:
            identity = LexicalIdentity.model_validate(_payload(value))
            if profile:
                if (
                    identity.language != profile.language
                    or identity.profile_version != profile.version
                ):
                    findings.append(_finding("lexical_profile_drift"))
                if identity.source_id not in profile.source_ids:
                    findings.append(_finding("lexical_source_unauthorized"))
                if identity.analyzer_version != profile.analyzer_version:
                    findings.append(_finding("lexical_analyzer_drift"))
        except (ValueError, TypeError, AttributeError):
            findings.append(_finding("invalid_lexical_identity"))
        return ValidationReport(validator="lexical", findings=tuple(findings))


class DatasetValidator:
    def validate(self, value: object, *, production: bool = False) -> ValidationReport:
        findings = []
        count = 1
        try:
            dataset = DatasetManifest.model_validate(_payload(value))
            count = max(1, len(dataset.members))
            if production:
                dataset.require_production()
        except (ValueError, TypeError, AttributeError):
            findings.append(
                _finding(
                    "dataset_production_gate_failed"
                    if production
                    else "invalid_dataset"
                )
            )
        return ValidationReport(
            validator="dataset", findings=tuple(findings), checked_count=count
        )


class ContentValidator:
    def validate(
        self, value: object, *, require_review: bool = False
    ) -> ValidationReport:
        findings = []
        try:
            payload = _payload(value)
            version = (
                ContentVersion.model_validate(payload)
                if isinstance(payload, dict) and "request" in payload
                else None
            )
            content = (
                version.content if version else GeneratedContent.model_validate(payload)
            )
            for field in (
                content.definition,
                content.example_sentence,
                content.translation,
                content.explanation,
                *content.exercises,
            ):
                validate_plain_content(field)
            if require_review and (
                version is None or version.review_status != "approved"
            ):
                findings.append(_finding("content_independent_review_required"))
            if version:
                request, evidence = version.request, version.target_evidence
                if (
                    not evidence.matched
                    or request.lexical_identity_id != evidence.lexical_identity_id
                    or request.sense_id != evidence.sense_id
                    or request.morphological_analysis_id
                    != evidence.morphological_analysis_id
                    or request.target_concept_id != evidence.target_concept_id
                    or request.target_concept_id not in evidence.observed_concept_ids
                ):
                    findings.append(_finding("content_target_match_failed"))
                known = set(request.canonical_known_concept_ids) | set(
                    request.known_concept_ids
                )
                if request.i_plus_one_mode == "strict" and set(
                    evidence.observed_concept_ids
                ) - known != {request.target_concept_id}:
                    findings.append(_finding("content_i_plus_one_failed"))
        except (ValueError, TypeError, AttributeError):
            findings.append(_finding("invalid_or_unsafe_content"))
        return ValidationReport(validator="content", findings=tuple(findings))


class MigrationValidator:
    """Validate hashes only; the migration service owns snapshot I/O and application."""

    def validate(self, value: object) -> ValidationReport:
        findings = []
        try:
            evidence = MigrationValidationEvidence.model_validate(_payload(value))
            if evidence.backup_sha256 != evidence.restored_sha256:
                findings.append(_finding("backup_restore_mismatch"))
            if evidence.confirmation_sha256 != evidence.expected_confirmation_sha256:
                findings.append(_finding("migration_confirmation_drift"))
            if (
                evidence.expected_source_sha256
                and evidence.source_sha256 != evidence.expected_source_sha256
            ):
                findings.append(_finding("migration_source_drift"))
        except (ValueError, TypeError, AttributeError):
            findings.append(_finding("invalid_migration_evidence"))
        return ValidationReport(validator="migration", findings=tuple(findings))

    def validate_evidence(self, **values: object) -> ValidationReport:
        return self.validate(values)


class EvaluationValidator:
    def validate_dimension(self, value: DimensionEvaluation) -> ValidationReport:
        try:
            evaluation = DimensionEvaluation.model_validate(_payload(value))
        except (ValueError, TypeError, AttributeError):
            return ValidationReport(
                validator="evaluation-dimension",
                findings=(_finding("invalid_evaluation"),),
            )
        findings = []
        subject = f"{evaluation.dimension}:{evaluation.dataset.stratum}"
        rate = evaluation.pass_rate
        if rate is None:
            findings.append(_finding("evaluation_no_eligible_cases", subject))
        elif rate < evaluation.threshold.minimum_pass_rate:
            findings.append(_finding("evaluation_threshold_failed", subject))
        if evaluation.critical_failures:
            findings.append(_finding("critical_failure", subject))
        delta = evaluation.regression_delta
        if delta is not None and delta < -evaluation.threshold.regression_tolerance:
            findings.append(_finding("evaluation_regression", subject))
        if evaluation.dataset.sha256 != evaluation.threshold.baseline_dataset_sha256:
            findings.append(_finding("evaluation_dataset_drift", subject))
        if (
            evaluation.dimension
            in {"anki_safety", "ambiguity", "target_sense_match", "form_analysis"}
            and rate != 1
        ):
            findings.append(_finding("evaluation_deterministic_gate_failed", subject))
        if (
            evaluation.dimension == "resolution"
            and rate is not None
            and rate < Decimal("0.98")
        ):
            findings.append(
                _finding("evaluation_resolution_below_required_minimum", subject)
            )
        return ValidationReport(
            validator="evaluation-dimension",
            findings=tuple(findings),
            checked_count=evaluation.eligible_cases,
        )

    def validate(
        self, value: object, *, require_complete: bool = True
    ) -> ValidationReport:
        try:
            evaluation = LanguageEvaluation.model_validate(_payload(value))
        except (ValidationError, TypeError, AttributeError):
            return ValidationReport(
                validator="evaluation-language",
                findings=(_finding("invalid_evaluation"),),
            )
        findings = [
            finding
            for row in evaluation.evaluations
            for finding in self.validate_dimension(row).findings
        ]
        if require_complete and set(EVALUATION_DIMENSIONS) - {
            row.dimension for row in evaluation.evaluations
        }:
            findings.append(_finding("evaluation_dimensions_missing"))
        review = evaluation.review
        if review.reviewer_kind == "llm" or review.reviewer_id == review.producer_id:
            findings.append(_finding("independent_review_required"))
        if evaluation.qualification:
            golden_cases: dict[str, int] = {}
            for row in evaluation.evaluations:
                if row.dataset.golden:
                    golden_cases[row.dataset.sha256] = max(
                        golden_cases.get(row.dataset.sha256, 0), row.eligible_cases
                    )
            minimum = (
                200
                if evaluation.language
                in {
                    SupportedLanguage.JA,
                    SupportedLanguage.ZH,
                    SupportedLanguage.KO,
                    SupportedLanguage.TR,
                    SupportedLanguage.FI,
                    SupportedLanguage.HU,
                }
                else 120
            )
            if sum(golden_cases.values()) < minimum:
                findings.append(_finding("language_goldens_insufficient"))
        return ValidationReport(
            validator="evaluation-language",
            findings=tuple(findings),
            checked_count=len(evaluation.evaluations),
        )
