"""Diagnostics explain disagreements without redefining evaluation scores."""

import hashlib
import json
import os
from pathlib import Path

import pytest

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import ContextualAnalysis, sentence_hash
from multilang.services.vocabulary_sources import CorpusSentence


def observation(*, omit=False, lemma="go", pos="VERB", features=None, status="complete"):
    text = "cats went home"
    reference = CorpusSentence.model_validate(
        {
            "language": "en",
            "document_id": "doc",
            "sentence_id": "one",
            "text": text,
            "source_sha256": "b" * 64,
            "tokens": [
                {
                    "index": 1,
                    "text": "cats",
                    "lemma": "cat",
                    "pos": "NOUN",
                    "start": 0,
                    "end": 4,
                    "features": {"Number": "Plur"},
                },
                {
                    "index": 2,
                    "text": "went",
                    "lemma": "go",
                    "pos": "VERB",
                    "start": 5,
                    "end": 9,
                    "features": {"Tense": "Past", "VerbForm": "Fin"},
                },
                {"index": 3, "text": "home", "lemma": "home", "pos": "ADV", "start": 10, "end": 14},
            ],
        }
    )
    tokens = []
    for token in reference.tokens:
        if omit and token.index == 2:
            continue
        tokens.append(
            {
                "text": token.text,
                "lemma": lemma if token.index == 2 else token.lemma,
                "pos": pos if token.index == 2 else token.pos,
                "start": token.start,
                "end": token.end,
                "features": list(
                    (
                        features if features is not None and token.index == 2 else token.features
                    ).items()
                ),
                "sentence_sha256": sentence_hash(text),
                "model_fingerprint": "a" * 64,
            }
        )
    analysis = ContextualAnalysis.model_validate(
        {
            "language": "en",
            "status": status,
            "reason": "morphology_only",
            "sentence_sha256": sentence_hash(text),
            "model_fingerprint": "a" * 64,
            "tokens": tokens if status != "unavailable" else [],
        }
    )
    return reference, analysis


def diagnose(**kwargs):
    from multilang.services.vocabulary.diagnostics import diagnose_observation

    return diagnose_observation(*observation(**kwargs))


def test_missing_token_is_alignment_failure_without_missing_feature_inflation():
    result = diagnose(omit=True)
    assert [case["category"] for case in result["cases"]] == ["token_unmatched"]
    assert result["feature_diagnostics"]["missing_fields"] == {}
    assert result["feature_diagnostics"]["unaligned_tokens"] == 1
    checks = [item for item in result["checks"] if item["metric"] == "annotated_features_accuracy"]
    assert len(checks) == 2  # Missing predictions remain eligible in the original metric.
    assert sum(item["correct"] for item in checks) == 1


def test_aligned_missing_and_different_features_have_separate_evidence():
    result = diagnose(lemma="went", pos="NOUN", features={"Tense": "Pres"})
    cases = result["cases"]
    assert {item["category"] for item in cases} == {
        "lemma_different",
        "pos_different",
        "feature_missing",
        "feature_different",
    }
    tense = next(item for item in cases if item["field"] == "Tense")
    assert (tense["expected"], tense["actual"], tense["word"]) == ("Past", "Pres", "went")
    assert tense["reference_pos"] == "VERB"
    assert tense["cause_status"] == "unreviewed"
    assert result["feature_diagnostics"]["missing_fields"] == {"VerbForm": 1}
    assert result["feature_diagnostics"]["different_values"] == {"Tense": 1}


def test_unavailable_analysis_preserves_eligibility_and_records_reason():
    result = diagnose(status="unavailable")
    assert result["cases"][0]["category"] == "analysis_unavailable"
    assert result["cases"][0]["actual"] == "morphology_only"
    assert result["feature_diagnostics"]["missing_fields"] == {}
    assert len([c for c in result["checks"] if c["metric"] == "lemma_accuracy"]) == 3


def test_incompatible_annotations_are_not_classified_as_linguistic_errors():
    from multilang.services.vocabulary.diagnostics import diagnose_observation

    compatibility = {
        name: {"comparable": False, "reason": "different_inventory"}
        for name in ("lemma_accuracy", "pos_accuracy", "annotated_features_accuracy")
    }
    result = diagnose_observation(
        *observation(lemma="went", features={}), compatibility=compatibility
    )
    assert result["cases"] == []
    assert all(c["correct"] is None for c in result["checks"] if c["metric"] != "exact_span_recall")


def test_reference_without_span_and_extra_predicted_token_are_explicit():
    from multilang.services.vocabulary.diagnostics import diagnose_observation

    reference, analysis = observation()
    token = reference.tokens[0].model_copy(update={"start": None, "end": None})
    reference = reference.model_copy(update={"tokens": (token, *reference.tokens[1:])})
    result = diagnose_observation(reference, analysis)
    assert {c["category"] for c in result["cases"]} == {
        "reference_span_missing",
        "predicted_token_unmatched",
    }
    assert len([c for c in result["checks"] if c["metric"] == "lemma_accuracy"]) == 2
    extra = next(c for c in result["cases"] if c["category"] == "predicted_token_unmatched")
    assert extra["reference_pos"] is None
    assert extra["predicted_pos"] == "NOUN"


def test_pairing_exposes_gains_regressions_and_persistent_disagreements():
    from multilang.services.vocabulary.diagnostics import pair_checks

    fast = diagnose(lemma="went", pos="NOUN")
    balanced = diagnose(pos="NOUN", features={"Tense": "Pres", "VerbForm": "Fin"})
    pair = pair_checks(fast["checks"], balanced["checks"])
    assert pair["metrics"]["lemma_accuracy"]["resolved"] == 1
    assert pair["metrics"]["lemma_accuracy"]["introduced"] == 0
    assert pair["metrics"]["pos_accuracy"]["persistent"] == 1
    assert pair["metrics"]["annotated_features_accuracy"]["introduced"] == 1
    assert pair["metrics"]["annotated_features_accuracy"]["eligible"] == 2
    assert {c["transition"] for c in pair["cases"]} == {"resolved", "introduced", "persistent"}


def test_pairing_rejects_different_reference_or_sample():
    from multilang.services.vocabulary.diagnostics import pair_checks

    fast = diagnose()["checks"]
    with pytest.raises(ValueError, match="sample"):
        pair_checks(fast, fast[:-1])


def test_case_identity_is_stable_and_includes_reference_identity():
    result = diagnose(lemma="went")
    assert result == diagnose(lemma="went")
    assert len(result["cases"][0]["occurrence_id"]) == 64


@pytest.mark.parametrize("change", ["wrong_text", "duplicate_index"])
def test_invalid_observation_identity_is_rejected(change):
    from multilang.services.vocabulary.diagnostics import diagnose_observation

    reference, analysis = observation()
    if change == "wrong_text":
        reference = reference.model_copy(update={"text": "dogs went home"})
    else:
        token = reference.tokens[0].model_copy(update={"index": 2})
        reference = reference.model_copy(update={"tokens": (token, *reference.tokens[1:])})
    with pytest.raises(ValueError):
        diagnose_observation(reference, analysis)


def evaluation(tmp_path, *, language="en", wrong=False):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    corpus = tmp_path / "input.conllu"
    corpus.write_text(
        "# sent_id = one\n# text = cats went home\n"
        "1\tcats\tcat\tNOUN\t_\tNumber=Plur\t2\tnsubj\t_\t_\n"
        "2\twent\tgo\tVERB\t_\tTense=Past|VerbForm=Fin\t0\troot\t_\t_\n"
        "3\thome\thome\tADV\t_\t_\t2\tadvmod\t_\t_\n\n",
        encoding="utf-8",
    )

    class Analyzer:
        def analyze(self, code, text):
            return observation(lemma="went" if wrong else "go")[1].model_copy(
                update={"language": code},
            )

    root = tmp_path / "evaluation"
    manifest = evaluate_corpus(
        language=language,
        corpus=corpus,
        corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
        output=root,
        analyzer=Analyzer(),
    )
    return root, manifest


def comparison(tmp_path, monkeypatch, *, unavailable_profile=None, failure_status="unavailable"):
    from multilang.services import model_comparison
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    evaluation(tmp_path)
    corpus = tmp_path / "input.conllu"
    models = tmp_path / "models"
    models.mkdir()

    def worker(payload, *, timeout_seconds):
        status = {
            "language": "en",
            "available": True,
            "profile": payload["profile"],
            "backend": "stanza",
        }
        fingerprint = canonical_sha256({"policy": "contextual-morphology-4", **status})

        class Analyzer:
            def analyze(self, language, text):
                result = observation(lemma="went" if payload["profile"] == "fast" else "go")[1]
                if payload["profile"] == unavailable_profile:
                    result = result.model_copy(update={"tokens": (), "status": failure_status})
                return result.model_copy(
                    update={
                        "model_fingerprint": fingerprint,
                        "tokens": tuple(
                            t.model_copy(update={"model_fingerprint": fingerprint})
                            for t in result.tokens
                        ),
                    }
                )

        evaluate_corpus(
            language="en",
            corpus=corpus,
            corpus_sha256=payload["dataset"]["corpus_sha256"],
            output=Path(payload["output"]),
            analyzer=Analyzer(),
        )
        return {
            "schema_version": 1,
            "status": "completed",
            "profile": payload["profile"],
            "model_status": status,
            "model_fingerprint": fingerprint,
        }

    monkeypatch.setattr(model_comparison, "_invoke_worker", worker)
    request = model_comparison.ModelComparisonRequest(
        model_root=models,
        profiles=["fast", "balanced"],
        max_sentences=2,
        timeout_seconds=10,
        threads=1,
        datasets=[
            {
                "language": "en",
                "corpus": corpus,
                "corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
                "split": "test",
            }
        ],
    )
    root = tmp_path / "comparison"
    return root, model_comparison.compare_models(request, output=root)


def generate(root, output, **kwargs):
    from multilang.services.vocabulary.diagnostic_reports import diagnose_report

    digest = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
    return diagnose_report(root, manifest_sha256=digest, output=output, **kwargs)


def test_standalone_report_is_deterministic_preserves_metrics_and_has_evidence(tmp_path):
    root, original = evaluation(tmp_path, wrong=True)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    first = generate(root, tmp_path / "first")
    second = generate(root, tmp_path / "second")
    assert first == second
    assert first["runs"][0]["metrics"] == original["metrics"]
    assert first["runs"][0]["counts"] == original["counts"]
    assert first["activation"] is False
    assert first["recommendation"] is None
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}
    cases = [json.loads(line) for line in (tmp_path / "first/cases.jsonl").read_text().splitlines()]
    assert cases[0]["category"] == "lemma_different"
    assert cases[0]["evidence"]["line"] == 1
    assert cases[0]["evidence"]["observations_sha256"] == original["observations_sha256"]
    assert cases[0]["model_fingerprint"] == "a" * 64
    group = next(g for g in first["runs"][0]["groups"] if g["category"] == "lemma_different")
    assert (group["count"], group["eligible"], group["rate"]) == (1, 1, 1.0)
    assert "went" in (tmp_path / "first/report.md").read_text()
    for name, digest in first["files"].items():
        assert hashlib.sha256((tmp_path / "first" / name).read_bytes()).hexdigest() == digest


def test_comparison_report_pairs_exact_cases_and_exposes_resolved_lemmata(tmp_path, monkeypatch):
    root, original = comparison(tmp_path, monkeypatch)
    result = generate(root, tmp_path / "diagnostics")
    pair = result["pairs"][0]
    assert pair["status"] == "paired"
    assert pair["metrics"]["lemma_accuracy"]["resolved"] == 1
    assert pair["metrics"]["lemma_accuracy"]["eligible"] == 3
    assert result["runs"][0]["sample_sha256"] == original["datasets"][0]["sample_sha256"]


@pytest.mark.parametrize("language", ["ko", "ja"])
def test_native_reports_keep_null_metrics_and_explain_incompatibility(tmp_path, language):
    root, original = evaluation(tmp_path, language=language, wrong=True)
    result = generate(root, tmp_path / "diagnostics")
    run = result["runs"][0]
    assert run["metrics"]["lemma_accuracy"] is None
    assert len(run["incompatible_metrics"]) == 3
    assert not any(g["category"] == "lemma_different" for g in run["groups"])
    assert run["counts"] == original["counts"]


@pytest.mark.parametrize("target", ["manifest", "observations"])
def test_tampered_evidence_is_rejected_without_publishing(tmp_path, target):
    from multilang.services.vocabulary.diagnostic_reports import diagnose_report

    root, _ = evaluation(tmp_path)
    digest = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
    path = root / ("manifest.json" if target == "manifest" else "observations.jsonl")
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum"):
        diagnose_report(root, manifest_sha256=digest, output=tmp_path / "diagnostics")
    assert not (tmp_path / "diagnostics").exists()


def test_manifest_cannot_reference_artifacts_outside_report(tmp_path, monkeypatch):
    root, manifest = comparison(tmp_path, monkeypatch)
    manifest["datasets"][0]["runs"][0]["artifact_path"] = "../evaluation"
    manifest.pop("comparison_sha256")
    manifest["comparison_sha256"] = canonical_sha256(manifest)
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="path"):
        generate(root, tmp_path / "diagnostics")


def test_report_does_not_overwrite_existing_output(tmp_path):
    root, _ = evaluation(tmp_path)
    output = tmp_path / "diagnostics"
    output.mkdir()
    marker = output / "keep"
    marker.write_text("important")
    with pytest.raises(ValueError, match="exists"):
        generate(root, output)
    assert marker.read_text() == "important"


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_special_input_files_are_rejected_before_opening(tmp_path, kind):
    root, _ = evaluation(tmp_path)
    path = root / "observations.jsonl"
    path.unlink()
    if kind == "fifo":
        os.mkfifo(path)
    else:
        path.symlink_to(root / "manifest.json")
    with pytest.raises(ValueError):
        generate(root, tmp_path / "diagnostics")


def test_report_limits_fail_atomically(tmp_path, monkeypatch):
    from multilang.services.vocabulary import diagnostic_reports

    root, _ = evaluation(tmp_path, wrong=True)
    monkeypatch.setattr(diagnostic_reports, "MAX_OUTPUT_BYTES", 20)
    with pytest.raises(ValueError, match="limit"):
        generate(root, tmp_path / "diagnostics")
    assert not (tmp_path / "diagnostics").exists()


def test_diagnose_cli_publishes_a_real_offline_report(tmp_path):
    from typer.testing import CliRunner

    from multilang.settings import Settings
    from multilang.vocabulary_cli import create_vocabulary_app

    root, _ = evaluation(tmp_path, wrong=True)
    digest = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
    result = CliRunner().invoke(
        create_vocabulary_app(settings=Settings(_env_file=None)),
        ["diagnose", str(root), digest, str(tmp_path / "diagnostics")],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["case_count"] == 1
    assert (tmp_path / "diagnostics/report.md").is_file()


def test_existing_comparator_uses_alignment_aware_feature_counts(tmp_path):
    from multilang.services.model_comparison import ModelComparisonDataset, _observation_evidence

    reference, analysis = observation(omit=True)
    path = tmp_path / "observations.jsonl"
    path.write_text(
        json.dumps(
            {
                "reference": reference.model_dump(mode="json"),
                "analysis": analysis.model_dump(mode="json"),
            }
        )
        + "\n"
    )
    dataset = ModelComparisonDataset(
        language="en",
        corpus=tmp_path / "unused",
        corpus_sha256=reference.source_sha256,
        split="test",
    )
    _, _, diagnostics = _observation_evidence(path, dataset=dataset, fingerprint="a" * 64)
    assert diagnostics["missing_fields"] == {}
    assert diagnostics["unaligned_tokens"] == 1
    assert diagnostics["schema_version"] == 2


def test_report_rejects_metric_denominators_that_do_not_match_observations(tmp_path):
    root, manifest = evaluation(tmp_path)
    manifest["counts"]["lemma_eligible_tokens"] += 1
    manifest.pop("evaluation_sha256")
    manifest["evaluation_sha256"] = canonical_sha256(manifest)
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="metric|count"):
        generate(root, tmp_path / "diagnostics")


def test_comparison_rejects_displayed_metrics_that_differ_from_artifacts(tmp_path, monkeypatch):
    root, manifest = comparison(tmp_path, monkeypatch)
    manifest["datasets"][0]["runs"][0]["metrics"]["lemma_accuracy"] = 1.0
    manifest.pop("comparison_sha256")
    manifest["comparison_sha256"] = canonical_sha256(manifest)
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="metadata"):
        generate(root, tmp_path / "diagnostics")


def test_native_incompatibility_cannot_publish_nonnull_accuracy(tmp_path):
    root, manifest = evaluation(tmp_path, language="ko")
    manifest["metrics"]["lemma_accuracy"] = 1.0
    manifest.pop("evaluation_sha256")
    manifest["evaluation_sha256"] = canonical_sha256(manifest)
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="metric|compatibility"):
        generate(root, tmp_path / "diagnostics")


def test_markdown_examples_escape_corpus_html_and_links(tmp_path):
    from multilang.services.vocabulary.diagnostic_reports import _text

    rendered = _text("<script>alert(1)</script> [open](https://invalid.example) `code`")
    assert "<script>" not in rendered
    assert "[open](" not in rendered
    assert "`code`" not in rendered


def test_checks_limit_stops_before_publishing(tmp_path, monkeypatch):
    from multilang.services.vocabulary import diagnostic_reports

    root, _ = evaluation(tmp_path)
    monkeypatch.setattr(diagnostic_reports, "MAX_CHECKS", 2)
    with pytest.raises(ValueError, match="limit"):
        generate(root, tmp_path / "diagnostics")


@pytest.mark.parametrize("profile", ["fast", "balanced"])
@pytest.mark.parametrize("status", ["unavailable", "unsupported"])
def test_unavailable_analyzer_artifact_is_preserved_but_never_paired(
    tmp_path,
    monkeypatch,
    profile,
    status,
):
    root, manifest = comparison(
        tmp_path, monkeypatch, unavailable_profile=profile, failure_status=status
    )
    source_run = next(r for r in manifest["datasets"][0]["runs"] if r["profile"] == profile)
    assert source_run["status"] == status
    assert source_run["artifact_path"] is not None
    result = generate(root, tmp_path / "diagnostics")
    assert result["pairs"][0]["status"] == "unavailable"
    run = next(r for r in result["runs"] if r["profile"] == profile)
    assert run["metrics"] == source_run["metrics"]
    assert run["counts"] == source_run["counts"]
    assert run["source_status"] == status
    cases = [
        json.loads(line) for line in (tmp_path / "diagnostics/cases.jsonl").read_text().splitlines()
    ]
    assert not any(c["kind"] == "transition" for c in cases)


def test_markdown_keeps_apostrophes_in_readable_examples():
    from markdown import markdown

    from multilang.services.vocabulary.diagnostic_reports import _text

    assert markdown(_text("l'homme & <tag>")) == "<p>l'homme &amp; &lt;tag&gt;</p>"
