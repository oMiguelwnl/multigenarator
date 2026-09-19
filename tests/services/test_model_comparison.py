import hashlib
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import (
    ContextualAnalysis,
    ContextualToken,
    sentence_hash,
)
from multilang.services.vocabulary_evaluation import (
    evaluate_corpus,
    evaluate_development_corpus,
)


def corpus(tmp_path):
    path = tmp_path / "sample.conllu"
    path.write_text(
        "# sent_id = one\n# text = I went home.\n"
        "1\tI\tI\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
        "2\twent\tgo\tVERB\t_\tTense=Past\t0\troot\t_\t_\n"
        "3\thome\thome\tADV\t_\t_\t2\tadvmod\t_\tSpaceAfter=No\n"
        "4\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n"
    )
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class Analyzer:
    def __init__(self, *, wrong=False):
        self.wrong = wrong

    def analyze(self, language, text):
        fingerprint = "a" * 64
        tokens = tuple(
            ContextualToken(
                text=word,
                lemma=lemma,
                pos=pos,
                start=start,
                end=end,
                sentence_sha256=sentence_hash(text),
                model_fingerprint=fingerprint,
                features=features,
            )
            for word, lemma, pos, start, end, features in [
                ("I", "I", "PRON", 0, 1, ()),
                ("went", "went" if self.wrong else "go", "VERB", 2, 6, (("Tense", "Past"),)),
                ("home", "home", "ADV", 7, 11, ()),
                (".", ".", "PUNCT", 11, 12, ()),
            ]
        )
        return ContextualAnalysis(
            language=language,
            status="complete",
            tokens=tokens,
            sentence_sha256=sentence_hash(text),
            model_fingerprint=fingerprint,
            reason="morphology_only",
        )


def _request(tmp_path: Path, *, split: str = "dev", profiles=("fast", "balanced")):
    from multilang.services.model_comparison import ModelComparisonRequest

    path, digest = corpus(tmp_path)
    model_root = tmp_path / "models"
    model_root.mkdir()
    return ModelComparisonRequest(
        model_root=model_root,
        datasets=[
            {
                "language": "en",
                "corpus": path,
                "corpus_sha256": digest,
                "split": split,
            }
        ],
        profiles=profiles,
        max_sentences=2,
        timeout_seconds=10,
        threads=1,
    )


class _ProfileAnalyzer(Analyzer):
    def __init__(
        self,
        fingerprint: str,
        *,
        wrong=False,
        unavailable=False,
        omit_token=False,
        tense=None,
    ):
        super().__init__(wrong=wrong)
        self.fingerprint = fingerprint
        self.unavailable = unavailable
        self.omit_token = omit_token
        self.tense = tense

    def analyze(self, language, text):
        if self.unavailable:
            return ContextualAnalysis(
                language=language,
                status="unavailable",
                sentence_sha256=sentence_hash(text),
                model_fingerprint=self.fingerprint,
                reason="model_missing_or_drifted",
            )
        result = super().analyze(language, text)
        tokens = list(result.tokens)
        if self.omit_token:
            tokens.pop(2)
        if self.tense is not None:
            tokens[1] = tokens[1].model_copy(update={"features": self.tense})
        tokens = [token.model_copy(update={"model_fingerprint": self.fingerprint}) for token in tokens]
        return result.model_copy(
            update={"model_fingerprint": self.fingerprint, "tokens": tuple(tokens)}
        )


def _completed_worker(
    *,
    wrong_profiles=(),
    unavailable_profiles=(),
    omit_profiles=(),
    equivalent=False,
    equivalent_to_by_profile=None,
    tense_by_profile=None,
):
    equivalent_to_by_profile = equivalent_to_by_profile or {}
    tense_by_profile = tense_by_profile or {}

    def invoke(payload, *, timeout_seconds):
        assert timeout_seconds == 10
        profile = payload["profile"]
        manifest = "same" if equivalent else profile
        status = {
            "language": payload["dataset"]["language"],
            "backend": "stanza",
            "available": True,
            "profile": profile,
            "manifest_sha256": hashlib.sha256(manifest.encode()).hexdigest(),
            "qualified": False,
        }
        fingerprint = canonical_sha256(
            {"policy": "contextual-morphology-4", **status}
        )
        analyzer = _ProfileAnalyzer(
            fingerprint,
            wrong=profile in wrong_profiles,
            unavailable=profile in unavailable_profiles,
            omit_token=profile in omit_profiles,
            tense=tense_by_profile.get(profile),
        )
        evaluator = (
            evaluate_development_corpus
            if payload["dataset"]["split"] == "dev"
            else evaluate_corpus
        )
        evaluator(
            language=payload["dataset"]["language"],
            corpus=Path(payload["dataset"]["corpus"]),
            corpus_sha256=payload["dataset"]["corpus_sha256"],
            output=Path(payload["output"]),
            analyzer=analyzer,
            max_sentences=payload["max_sentences"],
        )
        return {
            "schema_version": 1,
            "status": "completed",
            "reason": None,
            "profile": profile,
            "elapsed_seconds": 0.2 if profile == "balanced" else 0.1,
            "peak_rss_bytes": 2_000 if profile == "balanced" else 1_000,
            "peak_rss_reason": None,
            "model_status": status,
            "model_fingerprint": fingerprint,
            "equivalent_to": equivalent_to_by_profile.get(profile),
            "worker_exit_code": 0,
            "worker_stdout_bytes": 100,
            "worker_stderr_bytes": 0,
        }

    return invoke


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"profiles": ["balanced"]}, "fast"),
        ({"profiles": ["fast", "fast"]}, "unique"),
        ({"threads": 9}, "less than or equal to 8"),
        ({"max_sentences": 0}, "greater than or equal to 1"),
        ({"timeout_seconds": 3601}, "less than or equal to 3600"),
    ],
)
def test_request_is_closed_and_bounded(tmp_path, overrides, match):
    values = _request(tmp_path).model_dump(mode="python")
    values.update(overrides)
    from multilang.services.model_comparison import ModelComparisonRequest

    with pytest.raises(ValidationError, match=match):
        ModelComparisonRequest.model_validate(values)


def test_dev_comparison_uses_identical_samples_and_recommends_non_regressing_gain(
    tmp_path, monkeypatch
):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    monkeypatch.setattr(
        comparison, "_invoke_worker", _completed_worker(wrong_profiles={"fast"})
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    dataset = result["datasets"][0]
    baseline, candidate = dataset["runs"]

    assert baseline["sample_sha256"] == candidate["sample_sha256"]
    assert baseline["sample_sentence_count"] == candidate["sample_sentence_count"] == 1
    assert candidate["deltas"]["metrics"]["lemma_accuracy"] == 0.25
    assert candidate["decision"] == "recommended"
    assert dataset["recommendation"] == "balanced"
    assert result["qualification"] is False
    assert result["activation"] is False


def test_test_data_never_recommends_or_selects_a_model(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path, split="test")
    monkeypatch.setattr(
        comparison, "_invoke_worker", _completed_worker(wrong_profiles={"fast"})
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    dataset = result["datasets"][0]

    assert dataset["recommendation"] is None
    assert dataset["recommendation_reason"] == "test_data_cannot_select_models"
    assert all(run["decision"] != "recommended" for run in dataset["runs"])
    assert dataset["runs"][1]["deltas"]["metrics"]["lemma_accuracy"] == 0.25


def test_candidate_with_lower_coverage_is_not_recommended(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    monkeypatch.setattr(
        comparison,
        "_invoke_worker",
        _completed_worker(wrong_profiles={"fast"}, omit_profiles={"balanced"}),
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    candidate = result["datasets"][0]["runs"][1]

    assert candidate["deltas"]["metrics"]["exact_span_recall"] < 0
    assert candidate["decision"] == "not_recommended"
    assert result["datasets"][0]["recommendation"] is None


def test_native_null_metrics_never_select_from_raw_annotation_scores(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    native_dataset = type(request.datasets[0]).model_validate(
        {**request.datasets[0].model_dump(mode="python"), "language": "ja"}
    )
    request = request.model_copy(update={"datasets": (native_dataset,)})
    monkeypatch.setattr(
        comparison, "_invoke_worker", _completed_worker(wrong_profiles={"fast"})
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    baseline, candidate = result["datasets"][0]["runs"]

    assert baseline["metrics"]["lemma_accuracy"] is None
    assert candidate["metrics"]["lemma_accuracy"] is None
    assert candidate["deltas"]["metrics"]["lemma_accuracy"] is None
    assert candidate["decision"] == "not_recommended"
    assert result["datasets"][0]["recommendation"] is None


def test_equivalent_profile_is_explicit_and_ties_retain_fast(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    monkeypatch.setattr(comparison, "_invoke_worker", _completed_worker(equivalent=True))
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    candidate = result["datasets"][0]["runs"][1]

    assert candidate["status"] == "equivalent"
    assert candidate["decision"] == "equivalent_to_fast"
    assert result["datasets"][0]["recommendation"] is None


def test_equivalence_to_an_earlier_candidate_is_explicit(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path, profiles=("fast", "balanced", "accurate"))
    monkeypatch.setattr(
        comparison,
        "_invoke_worker",
        _completed_worker(
            wrong_profiles={"fast"},
            equivalent_to_by_profile={"accurate": "balanced"},
        ),
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    balanced, accurate = result["datasets"][0]["runs"][1:]

    assert balanced["decision"] == "recommended"
    assert accurate["status"] == "equivalent"
    assert accurate["decision"] == "equivalent_to_balanced"
    assert result["datasets"][0]["recommendation"] == "balanced"


def test_feature_diagnostics_distinguish_missing_fields_from_different_values(
    tmp_path, monkeypatch
):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    monkeypatch.setattr(
        comparison,
        "_invoke_worker",
        _completed_worker(
            tense_by_profile={"fast": (), "balanced": (("Tense", "Pres"),)}
        ),
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    baseline, candidate = result["datasets"][0]["runs"]

    assert baseline["feature_diagnostics"]["missing_fields"] == {"Tense": 1}
    assert baseline["feature_diagnostics"]["different_values"] == {}
    assert candidate["feature_diagnostics"]["missing_fields"] == {}
    assert candidate["feature_diagnostics"]["different_values"] == {"Tense": 1}


def test_hash_mismatch_fails_before_launch_and_publishes_nothing(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    valid_request = _request(tmp_path)
    request = valid_request.model_copy(
        update={
            "datasets": (
                valid_request.datasets[0].model_copy(update={"corpus_sha256": "0" * 64}),
            )
        }
    )
    invoked = False

    def invoke(*args, **kwargs):
        nonlocal invoked
        invoked = True

    monkeypatch.setattr(comparison, "_invoke_worker", invoke)
    with pytest.raises(ValueError, match="checksum mismatch"):
        comparison.compare_models(request, output=tmp_path / "comparison")

    assert invoked is False
    assert not (tmp_path / "comparison").exists()


def test_fifo_corpus_is_rejected_without_blocking_before_worker_timeout(tmp_path):
    import multilang.services.model_comparison as comparison

    fifo = tmp_path / "corpus.conllu"
    os.mkfifo(fifo)
    previous = signal.signal(
        signal.SIGALRM,
        lambda *_: (_ for _ in ()).throw(TimeoutError("corpus validation blocked")),
    )
    signal.alarm(1)
    try:
        with pytest.raises(ValueError, match="regular file"):
            comparison._validate_corpus(fifo, "a" * 64)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def test_all_unavailable_baseline_is_explicit_and_cannot_recommend_candidate(
    tmp_path, monkeypatch
):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    monkeypatch.setattr(
        comparison,
        "_invoke_worker",
        _completed_worker(unavailable_profiles={"fast"}),
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")
    baseline, candidate = result["datasets"][0]["runs"]

    assert baseline["status"] == "unavailable"
    assert baseline["reason"] == "analyzer_unavailable_during_evaluation"
    assert baseline["analysis_statuses"] == {"unavailable": 1}
    assert baseline["metrics"]["lemma_accuracy"] == 0
    assert baseline["counts"]["lemma_eligible_tokens"] == 4
    assert baseline["artifact_path"] is not None
    assert candidate["status"] == "completed"
    assert candidate["decision"] != "recommended"
    assert result["datasets"][0]["recommendation"] is None
    assert result["datasets"][0]["recommendation_reason"] == "fast_baseline_not_available"


def test_mixed_unavailable_or_inconclusive_evidence_remains_a_completed_run():
    import multilang.services.model_comparison as comparison

    assert comparison._analysis_outcome({"complete": 1, "unavailable": 1}, 2) == (
        "completed",
        None,
    )
    assert comparison._analysis_outcome({"inconclusive": 2}, 2) == ("completed", None)
    assert comparison._analysis_outcome({"unsupported": 2}, 2) == (
        "unsupported",
        "analyzer_unsupported_during_evaluation",
    )


def test_existing_output_is_immutable(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    output = tmp_path / "comparison"
    output.mkdir()
    marker = output / "marker"
    marker.write_text("preserve")
    monkeypatch.setattr(comparison, "_invoke_worker", _completed_worker())

    with pytest.raises(ValueError, match="exists"):
        comparison.compare_models(request, output=output)
    assert marker.read_text() == "preserve"


def test_worker_invocation_uses_a_fixed_offline_module_without_a_shell(monkeypatch):
    import multilang.services.model_comparison as comparison

    captured = {}

    class Process:
        pid = 10
        returncode = 0

    def popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return Process()

    monkeypatch.setattr(comparison.subprocess, "Popen", popen)
    monkeypatch.setattr(
        comparison,
        "_read_bounded_worker_output",
        lambda process, encoded, timeout_seconds: (
            b'{"schema_version":1,"status":"unavailable","reason":"model_missing"}',
            b"",
        ),
    )
    result = comparison._invoke_worker({"schema_version": 1}, timeout_seconds=7)

    assert captured["command"] == [
        sys.executable,
        "-m",
        "multilang.services.model_comparison_worker",
    ]
    assert captured["kwargs"]["shell"] is False
    assert captured["kwargs"]["start_new_session"] is True
    assert captured["kwargs"]["env"]["HF_HUB_OFFLINE"] == "1"
    assert captured["kwargs"]["env"]["TRANSFORMERS_OFFLINE"] == "1"
    assert result["status"] == "unavailable"


def test_worker_timeout_terminates_only_its_process_group(monkeypatch):
    import multilang.services.model_comparison as comparison

    signals = []

    class Process:
        pid = 123
        returncode = None

        def wait(self, timeout):
            self.returncode = -signal.SIGTERM

    monkeypatch.setattr(comparison.subprocess, "Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr(
        comparison,
        "_read_bounded_worker_output",
        lambda process, encoded, timeout_seconds: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("worker", timeout_seconds)
        ),
    )
    monkeypatch.setattr(comparison.os, "killpg", lambda pid, sig: signals.append((pid, sig)))
    result = comparison._invoke_worker({"schema_version": 1}, timeout_seconds=1)

    assert signals == [(123, signal.SIGTERM)]
    assert result["status"] == "timeout"
    assert result["peak_rss_bytes"] is None
    assert result["peak_rss_reason"] == "worker_timeout_before_measurement"


@pytest.mark.parametrize("failure", [KeyboardInterrupt(), RuntimeError("reader failed")])
def test_worker_reader_interruption_cleans_owned_process_and_pipes(monkeypatch, failure):
    import multilang.services.model_comparison as comparison

    signals = []

    class Pipe:
        closed = False

        def close(self):
            self.closed = True

    class Process:
        pid = 321
        returncode = None
        stdin = Pipe()
        stdout = Pipe()
        stderr = Pipe()

        def poll(self):
            return self.returncode

        def wait(self, timeout):
            self.returncode = -signal.SIGTERM

    process = Process()
    monkeypatch.setattr(comparison.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(
        comparison,
        "_read_bounded_worker_output",
        lambda *args, **kwargs: (_ for _ in ()).throw(failure),
    )
    monkeypatch.setattr(comparison.os, "killpg", lambda pid, sig: signals.append((pid, sig)))

    with pytest.raises(type(failure), match=str(failure) or None):
        comparison._invoke_worker({"schema_version": 1}, timeout_seconds=1)

    assert signals == [(321, signal.SIGTERM)]
    assert process.returncode == -signal.SIGTERM
    assert all(stream.closed for stream in (process.stdin, process.stdout, process.stderr))


def test_worker_output_reader_stops_at_the_hard_byte_cap():
    import multilang.services.model_comparison as comparison

    process = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 1024)"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=True,
    )
    with pytest.raises(comparison._WorkerOutputLimit):
        comparison._read_bounded_worker_output(
            process,
            b"",
            5,
            max_stdout_bytes=32,
            max_stderr_bytes=32,
        )
    if process.poll() is None:
        comparison._terminate_worker(process)


def test_worker_input_write_is_covered_by_the_same_deadline():
    import multilang.services.model_comparison as comparison

    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=True,
    )
    previous = signal.signal(
        signal.SIGALRM,
        lambda *_: (_ for _ in ()).throw(TimeoutError("stdin write blocked")),
    )
    started = time.monotonic()
    signal.alarm(3)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            comparison._read_bounded_worker_output(process, b"x" * (128 * 1024), 1)
        assert time.monotonic() - started < 2.5
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        if process.poll() is None:
            comparison._terminate_worker(process)


def test_malformed_worker_output_is_a_bounded_explicit_failure(tmp_path, monkeypatch):
    import multilang.services.model_comparison as comparison

    request = _request(tmp_path)
    monkeypatch.setattr(
        comparison,
        "_invoke_worker",
        lambda *args, **kwargs: {
            "schema_version": 1,
            "status": "malformed_output",
            "reason": "worker_output_not_valid_json",
            "elapsed_seconds": 0.01,
            "peak_rss_bytes": None,
            "peak_rss_reason": "worker_failed_before_measurement",
        },
    )
    result = comparison.compare_models(request, output=tmp_path / "comparison")

    assert [run["status"] for run in result["datasets"][0]["runs"]] == [
        "malformed_output",
        "malformed_output",
    ]
    assert result["datasets"][0]["recommendation"] is None
    assert (tmp_path / "comparison" / "manifest.json").is_file()


def test_fixed_worker_passes_profile_and_cpu_bounds_to_local_analyzer(tmp_path, monkeypatch):
    from multilang.services import contextual_morphology, language_models, model_comparison_worker

    request = _request(tmp_path)
    calls = []
    status = {
        "language": "en",
        "backend": "stanza",
        "available": True,
        "package_version": "fixture",
        "manifest_sha256": "b" * 64,
        "qualified": False,
    }
    monkeypatch.setattr(language_models, "model_status", lambda *args, **kwargs: status)
    monkeypatch.setattr(
        language_models,
        "available_model_profiles",
        lambda *args, **kwargs: {
            "language": "en",
            "backend": "stanza",
            "profiles": {"fast": {"supported": True, "available": True}},
        },
    )
    monkeypatch.setattr(
        contextual_morphology,
        "LocalContextualMorphologyService",
        lambda **kwargs: calls.append(("analyzer", kwargs)) or object(),
    )

    def evaluate(**kwargs):
        calls.append(("evaluate", kwargs))
        return {"analysis_statuses": {"complete": 1}, "sample_sentence_count": 1}

    monkeypatch.setattr(
        sys.modules["multilang.services.vocabulary_evaluation"],
        "evaluate_development_corpus",
        evaluate,
    )
    payload = model_comparison_worker._WorkerRequest(
        schema_version=1,
        model_root=request.model_root,
        dataset=request.datasets[0],
        profile="fast",
        max_sentences=2,
        threads=1,
        output=tmp_path / "worker-output",
    )

    result = model_comparison_worker._execute(payload)

    assert calls[0] == (
        "analyzer",
        {"model_root": request.model_root, "model_profiles": {"en": "fast"}, "threads": 1},
    )
    assert calls[1][0] == "evaluate"
    assert result["status"] == "completed"
    assert result["model_fingerprint"] == canonical_sha256(
        {"policy": "contextual-morphology-4", **status}
    )


def test_fixed_worker_carries_registry_equivalence_into_result(tmp_path, monkeypatch):
    from multilang.services import contextual_morphology, language_models, model_comparison_worker

    request = _request(tmp_path)
    status = {
        "language": "en",
        "backend": "stanza",
        "available": True,
        "profile": "balanced",
        "package_version": "fixture",
        "manifest_sha256": "b" * 64,
        "qualified": False,
    }
    monkeypatch.setattr(language_models, "model_status", lambda *args, **kwargs: status)
    monkeypatch.setattr(
        language_models,
        "available_model_profiles",
        lambda *args, **kwargs: {
            "language": "en",
            "backend": "stanza",
            "profiles": {
                "balanced": {
                    "supported": True,
                    "available": True,
                    "equivalent_to": "fast",
                }
            },
        },
    )
    monkeypatch.setattr(
        contextual_morphology, "LocalContextualMorphologyService", lambda **kwargs: object()
    )
    monkeypatch.setattr(
        sys.modules["multilang.services.vocabulary_evaluation"],
        "evaluate_development_corpus",
        lambda **kwargs: {
            "analysis_statuses": {"complete": 1},
            "sample_sentence_count": 1,
        },
    )
    payload = model_comparison_worker._WorkerRequest(
        schema_version=1,
        model_root=request.model_root,
        dataset=request.datasets[0],
        profile="balanced",
        max_sentences=2,
        threads=1,
        output=tmp_path / "worker-output",
    )

    result = model_comparison_worker._execute(payload)

    assert result["equivalent_to"] == "fast"


def test_fixed_worker_marks_total_analysis_unavailability_but_retains_artifact(
    tmp_path, monkeypatch
):
    from multilang.services import contextual_morphology, language_models, model_comparison_worker

    request = _request(tmp_path)
    status = {
        "language": "en",
        "backend": "stanza",
        "available": True,
        "package_version": "fixture",
        "manifest_sha256": "b" * 64,
        "qualified": False,
    }
    monkeypatch.setattr(language_models, "model_status", lambda *args, **kwargs: status)
    monkeypatch.setattr(
        language_models,
        "available_model_profiles",
        lambda *args, **kwargs: {"profiles": {"fast": {"available": True}}},
    )
    monkeypatch.setattr(
        contextual_morphology, "LocalContextualMorphologyService", lambda **kwargs: object()
    )
    monkeypatch.setattr(
        sys.modules["multilang.services.vocabulary_evaluation"],
        "evaluate_development_corpus",
        lambda **kwargs: {
            "analysis_statuses": {"unavailable": 1},
            "sample_sentence_count": 1,
        },
    )
    payload = model_comparison_worker._WorkerRequest(
        schema_version=1,
        model_root=request.model_root,
        dataset=request.datasets[0],
        profile="fast",
        max_sentences=2,
        threads=1,
        output=tmp_path / "worker-output",
    )

    result = model_comparison_worker._execute(payload)

    assert result["status"] == "unavailable"
    assert result["reason"] == "analyzer_unavailable_during_evaluation"
    assert result["artifact_complete"] is True


def test_fixed_worker_reports_native_alternative_as_unsupported(tmp_path, monkeypatch):
    from multilang.services import language_models, model_comparison_worker

    request = _request(tmp_path)
    monkeypatch.setattr(
        language_models,
        "model_status",
        lambda *args, **kwargs: {
            "language": "ja",
            "backend": "fugashi",
            "profile": "balanced",
            "available": False,
            "reason": "unsupported_profile",
        },
    )
    dataset = type(request.datasets[0]).model_validate(
        {**request.datasets[0].model_dump(mode="python"), "language": "ja"}
    )
    payload = model_comparison_worker._WorkerRequest(
        schema_version=1,
        model_root=request.model_root,
        dataset=dataset,
        profile="balanced",
        max_sentences=2,
        threads=1,
        output=tmp_path / "worker-output",
    )

    result = model_comparison_worker._execute(payload)

    assert result["status"] == "unsupported"
    assert result["reason"] == "unsupported_profile"


def test_fixed_worker_audit_hook_rejects_network_connections():
    from multilang.services.model_comparison_worker import _deny_network

    with pytest.raises(RuntimeError, match="network_disabled"):
        _deny_network("socket.connect", ())
