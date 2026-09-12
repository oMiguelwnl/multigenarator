"""Validation cannot replace independent evidence with averages or labels."""

import pytest


def evaluation(**changes):
    from multilang.domain.validation import (
        DimensionEvaluation,
        EvaluationDataset,
        MetricThreshold,
    )

    dataset = EvaluationDataset(
        dataset_id="fixture-eval",
        version="1",
        language="en",
        sha256="a" * 64,
        source_id="fixture",
        source_sha256="b" * 64,
        source_version="1",
        stratum="homographs",
        case_count=120,
        golden=True,
    )
    threshold = MetricThreshold(
        minimum_pass_rate="0.95",
        regression_tolerance="0.01",
        baseline_pass_rate="0.98",
        baseline_dataset_sha256="a" * 64,
        evidence_sha256="c" * 64,
        signed_baseline_sha256="d" * 64,
    )
    return DimensionEvaluation(
        **{
            "dimension": "definition",
            "dataset": dataset,
            "eligible_cases": 100,
            "excluded_cases": 20,
            "passed_cases": 99,
            "critical_failures": 0,
            "threshold": threshold,
            **changes,
        }
    )


def test_evaluation_reports_rates_and_blocks_critical_failure_despite_high_average():
    from multilang.services.native_validation import EvaluationValidator

    good = EvaluationValidator().validate_dimension(evaluation())
    assert good.valid
    assert evaluation().pass_rate.as_tuple().digits == (9, 9)
    bad = EvaluationValidator().validate_dimension(evaluation(critical_failures=1))
    assert not bad.valid
    assert "critical_failure" in {item.code for item in bad.findings}


def test_evaluation_decimal_metrics_roundtrip_and_complete_independent_review_passes():
    from multilang.domain.validation import (
        EVALUATION_DIMENSIONS,
        DimensionEvaluation,
        IndependentEvaluationReview,
        LanguageEvaluation,
    )
    from multilang.services.native_validation import EvaluationValidator

    assert (
        DimensionEvaluation.model_validate(evaluation().model_dump(mode="json"))
        == evaluation()
    )
    rows = tuple(
        evaluation(
            dimension=dimension, eligible_cases=120, excluded_cases=0, passed_cases=120
        )
        for dimension in EVALUATION_DIMENSIONS
    )
    complete = LanguageEvaluation(
        language="en",
        profile_version="1",
        analyzer_version="1",
        evaluations=rows,
        qualification=True,
        review=IndependentEvaluationReview(
            producer_id="author",
            reviewer_id="independent",
            reviewer_kind="expert",
            receipt_sha256="a" * 64,
        ),
    )
    assert EvaluationValidator().validate(complete).valid


def test_evidence_threshold_regression_and_empty_denominator_fail_closed():
    from multilang.domain.validation import MetricThreshold
    from multilang.services.native_validation import EvaluationValidator

    with pytest.raises(ValueError):
        MetricThreshold(
            minimum_pass_rate="0.9",
            regression_tolerance="0.1",
            baseline_pass_rate="0.9",
        )
    result = EvaluationValidator().validate_dimension(evaluation(passed_cases=96))
    assert not result.valid
    assert "evaluation_regression" in {item.code for item in result.findings}
    assert (
        not EvaluationValidator()
        .validate_dimension(evaluation(eligible_cases=0, passed_cases=0))
        .valid
    )


def test_language_evaluation_requires_independent_review_and_complete_dimensions():
    from multilang.domain.validation import (
        IndependentEvaluationReview,
        LanguageEvaluation,
    )
    from multilang.services.native_validation import EvaluationValidator

    review = IndependentEvaluationReview(
        producer_id="generator",
        reviewer_id="judge",
        reviewer_kind="llm",
        receipt_sha256="e" * 64,
    )
    result = EvaluationValidator().validate(
        LanguageEvaluation(
            language="en",
            profile_version="1",
            analyzer_version="1",
            evaluations=(evaluation(),),
            review=review,
        )
    )
    codes = {item.code for item in result.findings}
    assert "independent_review_required" in codes
    assert "evaluation_dimensions_missing" in codes


def test_dataset_validator_reuses_manifest_core_count_and_license_rules():
    from multilang.domain.datasets import DatasetManifest, DatasetMember
    from multilang.services.native_validation import DatasetValidator

    manifest = DatasetManifest(
        language="en",
        kind="lexical",
        namespace="core",
        version="1",
        source_id="fixture",
        source_sha256="a" * 64,
        policy_version="1",
        members=(DatasetMember(identity_id="lex:1:a", rank=1),),
    )
    assert DatasetValidator().validate(manifest).valid
    assert not DatasetValidator().validate(manifest, production=True).valid


def test_migration_hash_validation_rejects_snapshot_or_confirmation_drift():
    from multilang.services.native_validation import MigrationValidator

    valid = {
        "source_sha256": "a" * 64,
        "target_sha256": "b" * 64,
        "backup_sha256": "c" * 64,
        "restored_sha256": "c" * 64,
        "confirmation_sha256": "d" * 64,
        "expected_confirmation_sha256": "d" * 64,
    }
    assert MigrationValidator().validate_evidence(**valid).valid
    valid["restored_sha256"] = "e" * 64
    result = MigrationValidator().validate_evidence(**valid)
    assert not result.valid
    assert "backup_restore_mismatch" in {finding.code for finding in result.findings}
    with pytest.raises(ValueError):
        result.require_valid()


def test_lexical_validator_rechecks_forged_constructed_identity():
    from multilang.domain.jobs import SupportedLanguage
    from multilang.domain.lexical_identity import LexicalIdentity
    from multilang.services.native_validation import LexicalValidator

    forged = LexicalIdentity.model_construct(
        language=SupportedLanguage.EN,
        normalized_lemma="run",
        part_of_speech="unknown",
        sense_id="motion",
        profile_version="1",
        normalizer_version="1",
        analyzer_version="1",
        source_id="fixture",
        source_version="1",
        source_sha256="a" * 64,
    )
    assert not LexicalValidator().validate(forged).valid


def test_content_validator_rejects_active_fields_before_persistence():
    from multilang.domain.content import GeneratedContent
    from multilang.services.native_validation import ContentValidator

    good = GeneratedContent(
        definition="Move quickly.",
        example_sentence="They run home.",
        translation="Eles correm.",
    )
    assert ContentValidator().validate(good).valid
    assert not ContentValidator().validate(good, require_review=True).valid
    hostile = good.model_copy(update={"definition": "<script>alert(1)</script>"})
    assert not ContentValidator().validate(hostile).valid
