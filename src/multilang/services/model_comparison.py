"""Bounded, offline morphology-profile comparisons in isolated processes."""

from __future__ import annotations

import hashlib
import json
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import ContextualAnalysis, sentence_hash
from multilang.services.vocabulary_sources import CorpusSentence

ModelProfile = Literal["fast", "balanced", "accurate"]
_WORKER_MODULE = "multilang.services.model_comparison_worker"
_MAX_CORPUS_BYTES = 512 * 1024**2
_MAX_WORKER_STDOUT_BYTES = 1024**2
_MAX_WORKER_STDERR_BYTES = 64 * 1024
_MAX_MANIFEST_BYTES = 1024**2
_MAX_OBSERVATIONS_BYTES = 128 * 1024**2
_MAX_OBSERVATION_LINE_BYTES = 16 * 1024**2
_ACCURACY_METRICS = (
    "lemma_accuracy",
    "pos_accuracy",
    "annotated_features_accuracy",
)
_DENOMINATOR_COUNTS = (
    "gold_tokens",
    "unaligned_gold_tokens",
    "aligned_gold_tokens",
    "lemma_eligible_tokens",
    "pos_eligible_tokens",
    "features_eligible_tokens",
)
_REASON = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class _WorkerOutputLimit(Exception):
    def __init__(self, stdout: bytes, stderr: bytes) -> None:
        self.stdout = stdout
        self.stderr = stderr


class ModelComparisonDataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    language: SupportedLanguage
    corpus: Path
    corpus_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    split: Literal["dev", "test"]

    @model_validator(mode="after")
    def modern_language_only(self) -> "ModelComparisonDataset":
        if self.language is SupportedLanguage.LA:
            raise ValueError("Classical Latin uses its isolated morphology evaluation")
        return self


class ModelComparisonRequest(BaseModel):
    """Closed request contract for reproducible local profile comparisons."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_root: Path
    datasets: tuple[ModelComparisonDataset, ...] = Field(min_length=1, max_length=22)
    profiles: tuple[ModelProfile, ...] = Field(min_length=1, max_length=3)
    max_sentences: int = Field(ge=1, le=5000)
    timeout_seconds: int = Field(ge=1, le=3600)
    threads: int = Field(ge=1, le=8)

    @model_validator(mode="after")
    def comparison_is_unambiguous(self) -> "ModelComparisonRequest":
        if "fast" not in self.profiles:
            raise ValueError("profiles must include fast")
        if len(set(self.profiles)) != len(self.profiles):
            raise ValueError("profiles must be unique")
        identities = [
            (item.language.value, item.corpus_sha256, item.split) for item in self.datasets
        ]
        if len(set(identities)) != len(identities):
            raise ValueError("datasets must be unique")
        return self


def _plain_path(path: Path, *, label: str) -> Path:
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError(f"{label} cannot traverse symlinks")
    return path


def _validate_model_root(path: Path) -> Path:
    path = _plain_path(path, label="model root")
    if not path.is_dir():
        raise ValueError("model root must be an existing directory")
    return path


def _validate_corpus(path: Path, expected_sha256: str) -> Path:
    path = _plain_path(path, label="corpus")
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
    )
    with os.fdopen(descriptor, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("corpus must be a regular file")
        if before.st_size > _MAX_CORPUS_BYTES:
            raise ValueError("corpus byte limit exceeded")
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
        after = os.fstat(handle.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise ValueError("corpus changed during validation")
    if digest != expected_sha256:
        raise ValueError("corpus checksum mismatch")
    return path


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "HF_DATASETS_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HUB_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "TRANSFORMERS_OFFLINE": "1",
            "WANDB_DISABLED": "true",
        }
    )
    return environment


def _terminate_worker(process: subprocess.Popen) -> None:
    try:
        if hasattr(os, "killpg"):
            os.killpg(process.pid, signal.SIGTERM)
        else:  # pragma: no cover - exercised on Windows
            process.terminate()
        process.wait(timeout=1)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            if hasattr(os, "killpg"):
                os.killpg(process.pid, signal.SIGKILL)
            else:  # pragma: no cover - exercised on Windows
                process.kill()
            process.wait(timeout=1)


def _close_worker_pipes(process: subprocess.Popen) -> None:
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(process, name, None)
        if stream is not None:
            try:
                stream.close()
            except OSError:
                pass


def _read_bounded_worker_output(
    process: subprocess.Popen,
    encoded: bytes,
    timeout_seconds: int,
    *,
    max_stdout_bytes: int = _MAX_WORKER_STDOUT_BYTES,
    max_stderr_bytes: int = _MAX_WORKER_STDERR_BYTES,
) -> tuple[bytes, bytes]:
    """Drain child pipes incrementally and stop before either output can grow unbounded."""
    if len(encoded) > 1024**2:
        raise ValueError("worker request byte limit exceeded")
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise RuntimeError("worker pipes are unavailable")
    stdin_descriptor = process.stdin.fileno()
    stdout_descriptor = process.stdout.fileno()
    stderr_descriptor = process.stderr.fileno()
    for descriptor in (stdin_descriptor, stdout_descriptor, stderr_descriptor):
        os.set_blocking(descriptor, False)
    streams = {
        stdout_descriptor: (process.stdout, bytearray(), max_stdout_bytes),
        stderr_descriptor: (process.stderr, bytearray(), max_stderr_bytes),
    }
    selector = selectors.DefaultSelector()
    for descriptor, (stream, _, _) in streams.items():
        selector.register(stream, selectors.EVENT_READ, ("output", descriptor))
    deadline = time.monotonic() + timeout_seconds
    input_position = 0
    input_open = True
    if encoded:
        selector.register(process.stdin, selectors.EVENT_WRITE, ("input", stdin_descriptor))
    else:
        process.stdin.close()
        input_open = False
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(
                    _WORKER_MODULE,
                    timeout_seconds,
                    output=bytes(streams[stdout_descriptor][1]),
                    stderr=bytes(streams[stderr_descriptor][1]),
                )
            events = selector.select(remaining)
            if not events:
                raise subprocess.TimeoutExpired(
                    _WORKER_MODULE,
                    timeout_seconds,
                    output=bytes(streams[stdout_descriptor][1]),
                    stderr=bytes(streams[stderr_descriptor][1]),
                )
            for key, _ in events:
                kind, descriptor = key.data
                if kind == "input":
                    try:
                        written = os.write(descriptor, encoded[input_position : input_position + 65536])
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        written = 0
                        input_position = len(encoded)
                    else:
                        input_position += written
                    if input_position == len(encoded) or written == 0:
                        selector.unregister(process.stdin)
                        process.stdin.close()
                        input_open = False
                    continue
                stream, buffer, limit = streams[descriptor]
                chunk = os.read(descriptor, min(65536, limit - len(buffer) + 1))
                if not chunk:
                    selector.unregister(stream)
                    continue
                buffer.extend(chunk)
                if len(buffer) > limit:
                    raise _WorkerOutputLimit(
                        bytes(streams[stdout_descriptor][1]),
                        bytes(streams[stderr_descriptor][1]),
                    )
        process.wait(timeout=max(0.001, deadline - time.monotonic()))
    finally:
        selector.close()
        if input_open:
            process.stdin.close()
    return bytes(streams[stdout_descriptor][1]), bytes(streams[stderr_descriptor][1])


def _invoke_worker(payload: dict, *, timeout_seconds: int) -> dict:
    """Run only the fixed comparison worker module, without a command shell."""
    encoded = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    started = time.monotonic()
    process = subprocess.Popen(
        [sys.executable, "-m", _WORKER_MODULE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=True,
        env=_offline_environment(),
    )
    try:
        try:
            stdout, stderr = _read_bounded_worker_output(process, encoded, timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            _terminate_worker(process)
            stdout = exc.output or b""
            stderr = exc.stderr or b""
            return {
                "schema_version": 1,
                "status": "timeout",
                "reason": "worker_timeout",
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "peak_rss_bytes": None,
                "peak_rss_reason": "worker_timeout_before_measurement",
                "worker_exit_code": process.returncode,
                "worker_stdout_bytes": len(stdout),
                "worker_stderr_bytes": len(stderr),
            }
        except _WorkerOutputLimit as exc:
            _terminate_worker(process)
            return {
                "schema_version": 1,
                "status": "output_limit_exceeded",
                "reason": "worker_output_limit_exceeded",
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "peak_rss_bytes": None,
                "peak_rss_reason": "worker_failed_before_measurement",
                "worker_exit_code": process.returncode,
                "worker_stdout_bytes": len(exc.stdout),
                "worker_stderr_bytes": len(exc.stderr),
                "worker_stdout_sha256": hashlib.sha256(exc.stdout).hexdigest(),
                "worker_stderr_sha256": hashlib.sha256(exc.stderr).hexdigest(),
            }
        except BaseException:
            if process.poll() is None:
                _terminate_worker(process)
            raise
    finally:
        _close_worker_pipes(process)
    elapsed = round(time.monotonic() - started, 6)
    metadata = {
        "elapsed_seconds": elapsed,
        "worker_exit_code": process.returncode,
        "worker_stdout_bytes": len(stdout),
        "worker_stderr_bytes": len(stderr),
        "worker_stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "worker_stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }
    if len(stdout) > _MAX_WORKER_STDOUT_BYTES or len(stderr) > _MAX_WORKER_STDERR_BYTES:
        return {
            "schema_version": 1,
            "status": "output_limit_exceeded",
            "reason": "worker_output_limit_exceeded",
            "peak_rss_bytes": None,
            "peak_rss_reason": "worker_failed_before_measurement",
            **metadata,
        }
    try:
        result = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        result = None
    if process.returncode != 0 or not isinstance(result, dict):
        return {
            "schema_version": 1,
            "status": "malformed_output" if process.returncode == 0 else "failed",
            "reason": (
                "worker_output_not_valid_json"
                if process.returncode == 0
                else "worker_process_failed"
            ),
            "peak_rss_bytes": None,
            "peak_rss_reason": "worker_failed_before_measurement",
            **metadata,
        }
    result.update(metadata)
    return result


def _controlled_reason(value: object, fallback: str) -> str:
    return value if isinstance(value, str) and _REASON.fullmatch(value) else fallback


def _failure_run(profile: str, worker: dict) -> dict:
    return {
        "profile": profile,
        "status": str(worker.get("status", "failed")),
        "decision": "not_available",
        "reason": _controlled_reason(worker.get("reason"), "worker_failed"),
        "elapsed_seconds": worker.get("elapsed_seconds"),
        "peak_rss_bytes": worker.get("peak_rss_bytes"),
        "peak_rss_reason": worker.get("peak_rss_reason"),
        "worker_exit_code": worker.get("worker_exit_code"),
        "worker_stdout_bytes": worker.get("worker_stdout_bytes"),
        "worker_stderr_bytes": worker.get("worker_stderr_bytes"),
        "worker_stdout_sha256": worker.get("worker_stdout_sha256"),
        "worker_stderr_sha256": worker.get("worker_stderr_sha256"),
        "model_status": worker.get("model_status"),
        "equivalent_to": worker.get("equivalent_to"),
        "model_fingerprints": [],
        "analysis_statuses": None,
        "metrics": None,
        "metric_compatibility": None,
        "counts": None,
        "feature_diagnostics": None,
        "sample_sha256": None,
        "sample_sentence_count": None,
        "source_sentence_count": None,
        "deltas": None,
        "artifact_path": None,
        "artifact_manifest_sha256": None,
        "artifact_observations_sha256": None,
    }


def _observation_evidence(path: Path, *, dataset: ModelComparisonDataset, fingerprint: str):
    references = []
    missing_fields: Counter[str] = Counter()
    different_values: Counter[str] = Counter()
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, 1):
            if len(line) > _MAX_OBSERVATION_LINE_BYTES:
                raise ValueError("observation line byte limit exceeded")
            if line_number > 5000:
                raise ValueError("observation count exceeds bounds")
            payload = json.loads(line)
            reference = CorpusSentence.model_validate(payload.get("reference"))
            analysis = ContextualAnalysis.model_validate(payload.get("analysis"))
            if (
                reference.language.value != dataset.language.value
                or reference.source_sha256 != dataset.corpus_sha256
                or analysis.language != dataset.language.value
                or analysis.sentence_sha256 != sentence_hash(reference.text)
                or analysis.model_fingerprint != fingerprint
            ):
                raise ValueError("observation identity does not match comparison request")
            predicted = {(token.start, token.end): token for token in analysis.tokens}
            for token in reference.tokens:
                if token.start is None or token.end is None:
                    continue
                predicted_token = predicted.get((token.start, token.end))
                features = dict(predicted_token.features) if predicted_token is not None else {}
                for name, value in token.features.items():
                    if name not in features:
                        missing_fields[name] += 1
                    elif features[name] != value:
                        different_values[name] += 1
            references.append(reference.model_dump(mode="json"))
    if not references:
        raise ValueError("comparison observations are empty")
    return (
        canonical_sha256(references),
        len(references),
        {
            "missing_fields": dict(sorted(missing_fields.items())),
            "different_values": dict(sorted(different_values.items())),
        },
    )


def _completed_run(
    *,
    profile: str,
    worker: dict,
    artifact: Path,
    artifact_path: str,
    dataset: ModelComparisonDataset,
) -> dict:
    if worker.get("schema_version") != 1 or worker.get("profile") != profile:
        raise ValueError("worker result metadata mismatch")
    status = worker.get("model_status")
    fingerprint = worker.get("model_fingerprint")
    if (
        not isinstance(status, dict)
        or status.get("language") != dataset.language.value
        or status.get("available") is not True
        or not isinstance(fingerprint, str)
        or fingerprint != canonical_sha256({"policy": "contextual-morphology-2", **status})
    ):
        raise ValueError("worker model status or fingerprint mismatch")
    artifact = _plain_path(artifact, label="worker artifact")
    if not artifact.is_dir():
        raise ValueError("worker artifact is missing")
    children = sorted(item.name for item in artifact.iterdir())
    if children != ["manifest.json", "observations.jsonl"]:
        raise ValueError("worker artifact contains unexpected files")
    manifest_path = artifact / "manifest.json"
    observations_path = artifact / "observations.jsonl"
    for path in (manifest_path, observations_path):
        if path.is_symlink() or not path.is_file():
            raise ValueError("worker artifact file is invalid")
    if manifest_path.stat().st_size > _MAX_MANIFEST_BYTES:
        raise ValueError("worker manifest byte limit exceeded")
    if observations_path.stat().st_size > _MAX_OBSERVATIONS_BYTES:
        raise ValueError("worker observations byte limit exceeded")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict):
        raise ValueError("worker manifest is malformed")
    published_digest = manifest.get("evaluation_sha256")
    hashed = dict(manifest)
    hashed.pop("evaluation_sha256", None)
    if published_digest != canonical_sha256(hashed):
        raise ValueError("worker evaluation checksum mismatch")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("evaluator_version") != "3"
        or manifest.get("language") != dataset.language.value
        or manifest.get("corpus_sha256") != dataset.corpus_sha256
        or manifest.get("corpus_split") != dataset.split
        or manifest.get("model_fingerprints") != [fingerprint]
    ):
        raise ValueError("worker evaluation metadata mismatch")
    observations_sha256 = hashlib.sha256(observations_path.read_bytes()).hexdigest()
    if observations_sha256 != manifest.get("observations_sha256"):
        raise ValueError("worker observations checksum mismatch")
    sample_sha256, sample_count, diagnostics = _observation_evidence(
        observations_path, dataset=dataset, fingerprint=fingerprint
    )
    if sample_count != manifest.get("sample_sentence_count"):
        raise ValueError("worker observation count mismatch")
    analysis_statuses = manifest.get("analysis_statuses")
    run_status, run_reason = _analysis_outcome(
        analysis_statuses, manifest.get("sample_sentence_count")
    )
    return {
        "profile": profile,
        "status": run_status,
        "decision": (
            "baseline"
            if profile == "fast" and run_status == "completed"
            else "not_available"
            if run_status != "completed"
            else "not_recommended"
        ),
        "reason": run_reason,
        "elapsed_seconds": worker.get("elapsed_seconds"),
        "peak_rss_bytes": worker.get("peak_rss_bytes"),
        "peak_rss_reason": worker.get("peak_rss_reason"),
        "worker_exit_code": worker.get("worker_exit_code"),
        "worker_stdout_bytes": worker.get("worker_stdout_bytes"),
        "worker_stderr_bytes": worker.get("worker_stderr_bytes"),
        "worker_stdout_sha256": worker.get("worker_stdout_sha256"),
        "worker_stderr_sha256": worker.get("worker_stderr_sha256"),
        "model_status": status,
        "equivalent_to": worker.get("equivalent_to"),
        "model_fingerprints": manifest["model_fingerprints"],
        "analysis_statuses": analysis_statuses,
        "metrics": manifest.get("metrics"),
        "metric_compatibility": manifest.get("metric_compatibility"),
        "counts": manifest.get("counts"),
        "feature_diagnostics": diagnostics,
        "sample_sha256": sample_sha256,
        "sample_sentence_count": sample_count,
        "source_sentence_count": manifest.get("source_sentence_count"),
        "deltas": None,
        "artifact_path": artifact_path,
        "artifact_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "artifact_observations_sha256": observations_sha256,
    }


def _analysis_outcome(statuses: object, sample_count: object) -> tuple[str, str | None]:
    allowed = {"complete", "inconclusive", "invalid", "unavailable", "unsupported"}
    if (
        not isinstance(statuses, dict)
        or type(sample_count) is not int
        or not 1 <= sample_count <= 5000
        or any(
            key not in allowed or type(value) is not int or value < 1
            for key, value in statuses.items()
        )
        or sum(statuses.values()) != sample_count
    ):
        raise ValueError("worker analysis statuses are malformed")
    unavailable = statuses.get("unavailable", 0)
    unsupported = statuses.get("unsupported", 0)
    if unavailable + unsupported == sample_count:
        if unavailable:
            return "unavailable", "analyzer_unavailable_during_evaluation"
        return "unsupported", "analyzer_unsupported_during_evaluation"
    return "completed", None


def _metric_deltas(baseline: dict, candidate: dict) -> dict | None:
    if (
        candidate["sample_sha256"] != baseline["sample_sha256"]
        or candidate["sample_sentence_count"] != baseline["sample_sentence_count"]
        or candidate["source_sentence_count"] != baseline["source_sentence_count"]
        or any(
            candidate["counts"].get(name) != baseline["counts"].get(name)
            for name in _DENOMINATOR_COUNTS
        )
    ):
        return None
    deltas = {}
    for name, baseline_value in baseline["metrics"].items():
        candidate_value = candidate["metrics"].get(name)
        baseline_compatible = baseline["metric_compatibility"].get(name, {}).get("comparable")
        candidate_compatible = candidate["metric_compatibility"].get(name, {}).get("comparable")
        if (
            baseline_compatible
            and candidate_compatible
            and baseline_value is not None
            and candidate_value is not None
        ):
            deltas[name] = candidate_value - baseline_value
        else:
            deltas[name] = None
    elapsed_delta = (
        candidate["elapsed_seconds"] - baseline["elapsed_seconds"]
        if isinstance(candidate["elapsed_seconds"], (int, float))
        and isinstance(baseline["elapsed_seconds"], (int, float))
        else None
    )
    peak_delta = (
        candidate["peak_rss_bytes"] - baseline["peak_rss_bytes"]
        if isinstance(candidate["peak_rss_bytes"], int)
        and isinstance(baseline["peak_rss_bytes"], int)
        else None
    )
    return {
        "metrics": deltas,
        "elapsed_seconds": elapsed_delta,
        "peak_rss_bytes": peak_delta,
    }


def _equivalent_target(runs: list[dict], baseline: dict, candidate: dict) -> str | None:
    declared = candidate.get("equivalent_to")
    if isinstance(declared, str) and any(
        run is not candidate
        and run["profile"] == declared
        and run["status"] in {"completed", "equivalent"}
        for run in runs
    ):
        return declared
    baseline_status = baseline.get("model_status") or {}
    status = candidate.get("model_status") or {}
    for field in ("manifest_sha256", "model_artifact_sha256"):
        value = status.get(field)
        if value is not None and value == baseline_status.get(field):
            return "fast"
    if candidate["model_fingerprints"] == baseline["model_fingerprints"]:
        return "fast"
    return None


def _recommend(dataset: dict) -> None:
    runs = dataset["runs"]
    baseline = next((run for run in runs if run["profile"] == "fast"), None)
    if baseline is None or baseline["status"] != "completed":
        dataset["recommendation"] = None
        dataset["recommendation_reason"] = (
            "test_data_cannot_select_models"
            if dataset["corpus_split"] == "test"
            else "fast_baseline_not_available"
        )
        return
    for run in runs:
        if run is baseline or run["status"] != "completed":
            continue
        equivalent_target = _equivalent_target(runs, baseline, run)
        if equivalent_target is not None:
            run["status"] = "equivalent"
            run["decision"] = f"equivalent_to_{equivalent_target}"
            run["reason"] = "equivalent_model_fingerprint"
            continue
        run["deltas"] = _metric_deltas(baseline, run)
        if run["deltas"] is None:
            run["reason"] = "incompatible_sample_or_denominators"
    if dataset["corpus_split"] == "test":
        dataset["recommendation"] = None
        dataset["recommendation_reason"] = "test_data_cannot_select_models"
        for run in runs:
            if run["status"] == "completed":
                run["decision"] = "diagnostic_only"
        return
    eligible = []
    for run in runs:
        if run is baseline or run["status"] != "completed":
            continue
        if run["deltas"] is None:
            continue
        deltas = run["deltas"]["metrics"]
        comparable = [value for value in deltas.values() if value is not None]
        accuracy = [deltas.get(name) for name in _ACCURACY_METRICS]
        improves_accuracy = any(value is not None and value > 0 for value in accuracy)
        regresses = any(value < 0 for value in comparable)
        if improves_accuracy and not regresses:
            run["decision"] = "recommendation_candidate"
            eligible.append(run)
        else:
            run["reason"] = (
                "comparable_metric_regressed" if regresses else "no_comparable_accuracy_gain"
            )
    if len(eligible) == 1:
        eligible[0]["decision"] = "recommended"
        dataset["recommendation"] = eligible[0]["profile"]
        dataset["recommendation_reason"] = "dev_accuracy_gain_without_regression"
    elif eligible:
        dataset["recommendation"] = None
        dataset["recommendation_reason"] = "multiple_non_dominated_candidates"
    else:
        dataset["recommendation"] = None
        dataset["recommendation_reason"] = "fast_retained"


def compare_models(request: ModelComparisonRequest, *, output: Path) -> dict:
    """Compare local profiles sequentially and publish one immutable report."""
    request = ModelComparisonRequest.model_validate(request)
    model_root = _validate_model_root(request.model_root)
    datasets = [
        (dataset, _validate_corpus(dataset.corpus, dataset.corpus_sha256))
        for dataset in request.datasets
    ]
    output = _plain_path(output, label="comparison output")
    if output.exists():
        raise ValueError("comparison output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    _plain_path(output.parent, label="comparison output")
    with TemporaryDirectory(prefix=".model-comparison-", dir=output.parent) as temporary:
        staging = Path(temporary) / "result"
        staging.mkdir()
        reports = []
        for dataset_index, (dataset, corpus) in enumerate(datasets):
            dataset_report = {
                "language": dataset.language.value,
                "corpus_sha256": dataset.corpus_sha256,
                "corpus_split": dataset.split,
                "source_sentence_count": None,
                "sample_sentence_count": None,
                "sample_sha256": None,
                "runs": [],
                "recommendation": None,
                "recommendation_reason": None,
            }
            artifact_root = staging / "artifacts" / f"{dataset_index:02d}-{dataset.language.value}"
            artifact_root.mkdir(parents=True)
            for profile in request.profiles:
                artifact = artifact_root / profile
                relative_artifact = artifact.relative_to(staging).as_posix()
                payload = {
                    "schema_version": 1,
                    "model_root": str(model_root),
                    "dataset": {
                        "language": dataset.language.value,
                        "corpus": str(corpus),
                        "corpus_sha256": dataset.corpus_sha256,
                        "split": dataset.split,
                    },
                    "profile": profile,
                    "max_sentences": request.max_sentences,
                    "threads": request.threads,
                    "output": str(artifact),
                }
                worker = _invoke_worker(payload, timeout_seconds=request.timeout_seconds)
                artifact_complete = worker.get("artifact_complete") is True and worker.get(
                    "status"
                ) in {"completed", "unavailable", "unsupported"}
                if worker.get("status") != "completed" and not artifact_complete:
                    if artifact.exists():
                        shutil.rmtree(artifact)
                    run = _failure_run(profile, worker)
                else:
                    try:
                        run = _completed_run(
                            profile=profile,
                            worker=worker,
                            artifact=artifact,
                            artifact_path=relative_artifact,
                            dataset=dataset,
                        )
                    except (OSError, ValueError, TypeError, json.JSONDecodeError):
                        if artifact.exists():
                            shutil.rmtree(artifact)
                        run = _failure_run(
                            profile,
                            {
                                **worker,
                                "status": "artifact_mismatch",
                                "reason": "worker_artifact_validation_failed",
                            },
                        )
                dataset_report["runs"].append(run)
            _recommend(dataset_report)
            baseline = next(
                (run for run in dataset_report["runs"] if run["profile"] == "fast"), None
            )
            if baseline is not None and baseline["sample_sha256"] is not None:
                dataset_report["source_sentence_count"] = baseline["source_sentence_count"]
                dataset_report["sample_sentence_count"] = baseline["sample_sentence_count"]
                dataset_report["sample_sha256"] = baseline["sample_sha256"]
            reports.append(dataset_report)
        result = {
            "schema_version": 1,
            "evaluator_version": "3",
            "request_sha256": canonical_sha256(request.model_dump(mode="json")),
            "datasets": reports,
            "qualification": False,
            "activation": False,
        }
        result["comparison_sha256"] = canonical_sha256(result)
        manifest_payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if len(manifest_payload.encode("utf-8")) > 8 * 1024**2:
            raise ValueError("comparison manifest byte limit exceeded")
        (staging / "manifest.json").write_text(manifest_payload, encoding="utf-8")
        if output.exists():
            raise ValueError("comparison output created concurrently")
        os.rename(staging, output)
    return result
