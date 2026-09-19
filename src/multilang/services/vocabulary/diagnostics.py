"""Pure, source-bound explanations of morphology evaluation disagreements.

Metric checks keep the evaluator's denominators. Explanations only attribute a
missing feature to an aligned token; an absent prediction is an alignment case.
None of these disagreements establishes a linguistic root cause.
"""

from collections import Counter

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import (
    ContextualAnalysis,
    ContextualToken,
    sentence_hash,
)
from multilang.services.vocabulary_sources import CorpusSentence, CorpusToken

PAIRED_METRICS = (
    "exact_span_recall",
    "lemma_accuracy",
    "pos_accuracy",
    "annotated_features_accuracy",
)


def diagnose_observation(
    reference: CorpusSentence,
    analysis: ContextualAnalysis,
    *,
    compatibility: dict | None = None,
) -> dict:
    """Explain one observation; omitted compatibility means raw UD comparison."""
    reference = CorpusSentence.model_validate(reference)
    analysis = ContextualAnalysis.model_validate(analysis)
    if analysis.language != reference.language.value or (
        analysis.sentence_sha256 != sentence_hash(reference.text)
    ):
        raise ValueError("observation identity mismatch")
    indexes = [token.index for token in reference.tokens]
    if len(indexes) != len(set(indexes)):
        raise ValueError("duplicate reference token index")
    for token in (*analysis.tokens, *analysis.blocked_spans):
        if reference.text[token.start : token.end] != token.text:
            raise ValueError("predicted token text does not match source span")
    spans = [
        (t.start, t.end) for t in reference.tokens if t.start is not None and t.end is not None
    ]
    gold_spans = set(spans)
    if len(spans) != len(gold_spans):
        raise ValueError("duplicate reference span")
    for token in reference.tokens:
        if (
            token.start is not None
            and token.end is not None
            and (token.start >= token.end or reference.text[token.start : token.end] != token.text)
        ):
            raise ValueError("reference token text does not match source span")
    reference_hash = canonical_sha256(reference.model_dump(mode="json"))
    context = {
        "language": reference.language.value,
        "source_sha256": reference.source_sha256,
        "document_id": reference.document_id,
        "sentence_id": reference.sentence_id,
        "sentence_sha256": analysis.sentence_sha256,
        "sentence": reference.text,
        "reference_sha256": reference_hash,
    }
    cases, checks, feature_checks = [], [], []
    missing, different = Counter(), Counter()
    unaligned = unaligned_reference = 0
    predicted = {(token.start, token.end): token for token in analysis.tokens}

    def comparable(metric):
        return compatibility is None or compatibility.get(metric, {}).get("comparable") is True

    def evidence(token=None):
        values = {
            "token_index": getattr(token, "index", None),
            "start": getattr(token, "start", None),
            "end": getattr(token, "end", None),
            "word": getattr(token, "text", None),
            "reference_pos": token.pos if isinstance(token, CorpusToken) else None,
            "predicted_pos": token.pos if isinstance(token, ContextualToken) else None,
        }
        return {
            **context,
            **values,
            "occurrence_id": canonical_sha256(
                {
                    "reference": reference_hash,
                    **values,
                }
            ),
        }

    def case(base, category, field, expected, actual):
        cases.append(
            {
                **base,
                "category": category,
                "field": field,
                "expected": expected,
                "actual": actual,
                "cause_status": "unreviewed",
            }
        )

    def check(base, metric, expected, actual, correct):
        checks.append(
            {
                **base,
                "metric": metric,
                "expected": expected,
                "actual": actual,
                "correct": bool(correct) if comparable(metric) else None,
            }
        )

    if analysis.status != "complete":
        case(evidence(), f"analysis_{analysis.status}", "status", "complete", analysis.reason)
    for blocker in analysis.blocked_spans:
        case(evidence(blocker), "blocked_span", "alignment", None, blocker.reason)
    for token in reference.tokens:
        base = evidence(token)
        if token.start is None or token.end is None:
            unaligned_reference += 1
            case(base, "reference_span_missing", "alignment", token.text, None)
            continue
        prediction = predicted.get((token.start, token.end))
        check(
            base,
            "exact_span_recall",
            token.text,
            prediction.text if prediction else None,
            prediction is not None,
        )
        if prediction is None:
            unaligned += 1
            case(base, "token_unmatched", "alignment", token.text, None)
        for field, metric in (("lemma", "lemma_accuracy"), ("pos", "pos_accuracy")):
            expected = getattr(token, field)
            if expected is None:
                continue
            actual = getattr(prediction, field) if prediction else None
            check(base, metric, expected, actual, prediction is not None and expected == actual)
            if prediction and comparable(metric) and expected != actual:
                case(base, f"{field}_different", field, expected, actual)
        features = dict(prediction.features) if prediction else {}
        if token.features:
            check(
                base,
                "annotated_features_accuracy",
                token.features,
                features if prediction else None,
                prediction is not None
                and all(features.get(k) == v for k, v in token.features.items()),
            )
        if prediction is None:
            continue
        for name, value in sorted(token.features.items()):
            actual = features.get(name)
            feature_checks.append(
                {
                    **base,
                    "field": name,
                    "expected": value,
                    "actual": actual,
                    "correct": value == actual
                    if comparable("annotated_features_accuracy")
                    else None,
                }
            )
            if name not in features:
                missing[name] += 1
                category = "feature_missing"
            elif value != actual:
                different[name] += 1
                category = "feature_different"
            else:
                continue
            if comparable("annotated_features_accuracy"):
                case(base, category, name, value, actual)
    for span, token in predicted.items():
        if span not in gold_spans:
            case(evidence(token), "predicted_token_unmatched", "alignment", None, token.text)
    return {
        "cases": cases,
        "checks": checks,
        "feature_checks": feature_checks,
        "feature_diagnostics": {
            "schema_version": 2,
            "missing_fields": dict(sorted(missing.items())),
            "different_values": dict(sorted(different.items())),
            "unaligned_tokens": unaligned,
            "unaligned_reference_tokens": unaligned_reference,
        },
    }


def pair_checks(baseline: list[dict], candidate: list[dict]) -> dict:
    """Pair exact source occurrences, exposing gross gains and regressions."""

    def index(rows):
        result = {(row["occurrence_id"], row["metric"]): row for row in rows}
        if len(result) != len(rows):
            raise ValueError("duplicate sample occurrence")
        return result

    left, right = index(baseline), index(candidate)
    if left.keys() != right.keys():
        raise ValueError("incompatible sample occurrences")
    metrics = {
        name: dict.fromkeys(
            (
                "eligible",
                "resolved",
                "introduced",
                "persistent",
                "unchanged_correct",
                "not_comparable",
            ),
            0,
        )
        for name in PAIRED_METRICS
    }
    cases = []
    for key in sorted(left):
        first, second = left[key], right[key]
        if first["expected"] != second["expected"]:
            raise ValueError("incompatible sample reference")
        metric = metrics[first["metric"]]
        if first["correct"] is None or second["correct"] is None:
            metric["not_comparable"] += 1
            continue
        metric["eligible"] += 1
        transition = (
            "unchanged_correct"
            if first["correct"] and second["correct"]
            else "resolved"
            if second["correct"]
            else "introduced"
            if first["correct"]
            else "persistent"
        )
        metric[transition] += 1
        if transition != "unchanged_correct":
            cases.append(
                {
                    **{k: v for k, v in first.items() if k not in {"actual", "correct"}},
                    "transition": transition,
                    "baseline_actual": first["actual"],
                    "candidate_actual": second["actual"],
                    "cause_status": "unreviewed",
                }
            )
    return {"metrics": metrics, "cases": cases}
