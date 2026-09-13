"""Reproducible morphology diagnostics against declared held-out source labels.

This produces review material, not independent linguistic qualification. UD
annotations do not evaluate lexical sense, strict-i+1, audio or Anki clients.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import os
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import (
    ContextualAnalysis,
    ContextualAnalyzer,
    sentence_hash,
)
from multilang.services.language_models import model_spec
from multilang.services.vocabulary_preparation import source_catalog
from multilang.services.vocabulary_sources import SourceLimits, read_conllu


def evaluate_corpus(
    *,
    language: str,
    corpus: Path,
    corpus_sha256: str,
    output: Path,
    analyzer: ContextualAnalyzer,
    split: str = "test",
    max_sentences: int = 200,
    limits: SourceLimits | None = None,
) -> dict:
    limits = limits or SourceLimits()
    catalog = source_catalog(language)
    if split != "test":
        raise ValueError("held-out diagnostics require the declared test split")
    if not 1 <= max_sentences <= 5000:
        raise ValueError("evaluation sentence count is outside bounds")
    output = Path(output).absolute()
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("evaluation output cannot traverse symlinks")
    if output.exists():
        raise ValueError("evaluation output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Sample across the entire file, with a stable hash order rather than its
    # opening sentences. nsmallest keeps only bounded selected sentences in RAM.
    source_count = 0

    def references():
        nonlocal source_count
        for reference in read_conllu(
            corpus, language=language, expected_sha256=corpus_sha256, limits=limits
        ):
            source_count += 1
            yield reference

    selected = heapq.nsmallest(
        max_sentences,
        references(),
        key=lambda row: canonical_sha256(
            {
                "source": row.source_sha256,
                "document": row.document_id,
                "sentence": row.sentence_id,
                "text": row.text,
            }
        ),
    )
    if not selected:
        raise ValueError("evaluation corpus has no source sentences")
    statuses: Counter = Counter()
    counts: Counter = Counter()
    fingerprints = set()
    output_bytes = 0
    with TemporaryDirectory(prefix=".evaluation-", dir=output.parent) as temporary:
        staging = Path(temporary) / "result"
        staging.mkdir()
        with (staging / "observations.jsonl").open("w", encoding="utf-8") as observations:
            for reference in selected:
                analysis = ContextualAnalysis.model_validate(
                    analyzer.analyze(language, reference.text).model_dump(mode="json")
                )
                if analysis.language != language or analysis.sentence_sha256 != sentence_hash(
                    reference.text
                ):
                    raise ValueError("analyzer result does not match evaluation source")
                for token in analysis.tokens:
                    if reference.text[token.start : token.end] != token.text:
                        raise ValueError("analyzer offsets do not match evaluation source")
                for blocked in analysis.blocked_spans:
                    if reference.text[blocked.start : blocked.end] != blocked.text:
                        raise ValueError("analyzer blocker does not match evaluation source")
                statuses[analysis.status] += 1
                counts["blocked_source_spans"] += len(analysis.blocked_spans)
                fingerprints.add(analysis.model_fingerprint)
                predicted = {(token.start, token.end): token for token in analysis.tokens}
                gold = {
                    (token.start, token.end): token
                    for token in reference.tokens
                    if token.start is not None and token.end is not None
                }
                counts["gold_tokens"] += len(reference.tokens)
                counts["unaligned_gold_tokens"] += len(reference.tokens) - len(gold)
                counts["aligned_gold_tokens"] += len(gold)
                counts["predicted_tokens"] += len(predicted)
                counts["exact_span_matches"] += len(gold.keys() & predicted.keys())
                sentence_errors = len(reference.tokens) - len(gold)
                for span, token in gold.items():
                    predicted_token = predicted.get(span)
                    if token.lemma is not None:
                        counts["lemma_eligible_tokens"] += 1
                        counts["lemma_correct"] += bool(
                            predicted_token and predicted_token.lemma == token.lemma
                        )
                    if token.pos is not None:
                        counts["pos_eligible_tokens"] += 1
                        counts["pos_correct"] += bool(
                            predicted_token and predicted_token.pos == token.pos
                        )
                    if token.features:
                        counts["features_eligible_tokens"] += 1
                        counts["features_correct"] += bool(
                            predicted_token
                            and all(
                                dict(predicted_token.features).get(key) == value
                                for key, value in token.features.items()
                            )
                        )
                    if (
                        predicted_token is None
                        or (token.lemma is not None and token.lemma != predicted_token.lemma)
                        or (token.pos is not None and token.pos != predicted_token.pos)
                        or any(
                            dict(predicted_token.features).get(key) != value
                            for key, value in token.features.items()
                        )
                    ):
                        sentence_errors += 1
                if analysis.status == "complete" and sentence_errors:
                    counts["false_complete_sentences"] += 1
                payload = (
                    json.dumps(
                        {
                            "reference": reference.model_dump(mode="json"),
                            "analysis": analysis.model_dump(mode="json"),
                            "token_analysis_ids": [token.analysis_id for token in analysis.tokens],
                            "sense_review_status": "pending",
                            "canonical_ranking_input": False,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                output_bytes += len(payload.encode("utf-8"))
                if output_bytes > limits.max_output_bytes:
                    raise ValueError("evaluation output byte limit exceeded")
                observations.write(payload)

        def ratio(numerator: str, denominator: str):
            return counts[numerator] / counts[denominator] if counts[denominator] else None

        raw_metrics = {
            "exact_span_precision": ratio("exact_span_matches", "predicted_tokens"),
            "exact_span_recall": ratio("exact_span_matches", "aligned_gold_tokens"),
            "lemma_accuracy": ratio("lemma_correct", "lemma_eligible_tokens"),
            "pos_accuracy": ratio("pos_correct", "pos_eligible_tokens"),
            "annotated_features_accuracy": ratio("features_correct", "features_eligible_tokens"),
        }
        backend = model_spec(language).backend
        native_annotations = backend in {"kiwi", "fugashi"}
        reasons = {
            "kiwi": {
                "lemma_accuracy": "ud_korean_morpheme_sequence_is_not_kiwi_citation_lemma",
                "pos_accuracy": "ud_eojeol_pos_is_not_projected_kiwi_lexical_pos",
                "annotated_features_accuracy": "ud_features_are_not_sejong_morpheme_features",
            },
            "fugashi": {
                "lemma_accuracy": "ud_and_unidic_lemma_inventory_not_qualified_equivalent",
                "pos_accuracy": "unidic_lexicon_pos_needs_contextual_ud_conversion",
                "annotated_features_accuracy": "ud_features_are_not_unidic_native_features",
            },
        }
        compatibility = {
            name: {
                "comparable": not (native_annotations and name in reasons[backend]),
                "reason": (
                    reasons[backend][name]
                    if native_annotations and name in reasons[backend]
                    else "exact_source_surface_spans"
                    if name.startswith("exact_span")
                    else "stanza_ud_annotation_inventory"
                ),
            }
            for name in raw_metrics
        }
        metrics = {
            name: value if compatibility[name]["comparable"] else None
            for name, value in raw_metrics.items()
        }
        result = {
            "schema_version": 1,
            "evaluator_version": "3",
            "language": language,
            "corpus_sha256": corpus_sha256,
            "corpus_split": split,
            "source_catalog_sha256": canonical_sha256(catalog),
            "source_sentence_count": source_count,
            "sample_sentence_count": len(selected),
            "sample_policy": "smallest-source-bound-sentence-sha256-v1",
            "model_fingerprints": sorted(fingerprints),
            "analysis_statuses": dict(statuses),
            "counts": dict(counts),
            "metrics": metrics,
            "raw_annotation_metrics": raw_metrics,
            "metric_compatibility": compatibility,
            "annotation_backend": backend,
            "false_complete_sentence_count": (
                None if native_annotations else counts["false_complete_sentences"]
            ),
            "raw_annotation_disagreement_sentence_count": counts["false_complete_sentences"],
            "target_false_accept_rate": None,
            "qualification": False,
            "independent_review": None,
            "canonical_ranking_input": False,
            "limitations": [
                "source_annotations_not_fully_human_verified",
                "model_pretraining_overlap_not_established",
                "sense_matching_not_evaluated",
                "grammar_strict_i_plus_one_not_evaluated",
                "audio_and_clients_not_evaluated",
            ],
        }
        with (staging / "observations.jsonl").open("rb") as handle:
            result["observations_sha256"] = hashlib.file_digest(handle, "sha256").hexdigest()
        result["evaluation_sha256"] = canonical_sha256(result)
        manifest_payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if output_bytes + len(manifest_payload.encode("utf-8")) > limits.max_output_bytes:
            raise ValueError("evaluation output byte limit exceeded")
        (staging / "manifest.json").write_text(manifest_payload, encoding="utf-8")
        if output.exists():
            raise ValueError("evaluation output created concurrently")
        os.rename(staging, output)
    return result
