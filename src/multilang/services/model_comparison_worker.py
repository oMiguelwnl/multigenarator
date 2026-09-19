"""Fixed subprocess worker for one offline morphology evaluation."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from multilang.services.model_comparison import ModelComparisonDataset, _analysis_outcome

_REASON = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class _WorkerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    model_root: Path
    dataset: ModelComparisonDataset
    profile: Literal["fast", "balanced", "accurate"]
    max_sentences: int = Field(ge=1, le=5000)
    threads: int = Field(ge=1, le=8)
    output: Path


def _peak_rss() -> tuple[int | None, str | None]:
    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return (int(value) if sys.platform == "darwin" else int(value) * 1024), None
    except (ImportError, OSError, ValueError):  # pragma: no cover - platform dependent
        return None, "platform_not_supported"


def _controlled_reason(value: object, fallback: str) -> str:
    return value if isinstance(value, str) and _REASON.fullmatch(value) else fallback


def _deny_network(event: str, args: tuple[object, ...]) -> None:
    if event == "socket.connect":
        raise RuntimeError("network_disabled")


def _execute(request: _WorkerRequest) -> dict:
    from multilang.services.contextual_morphology import (
        LocalContextualMorphologyService,
        contextual_model_fingerprint,
    )
    from multilang.services.language_models import available_model_profiles, model_status
    from multilang.services.vocabulary_evaluation import (
        evaluate_corpus,
        evaluate_development_corpus,
    )

    started = time.monotonic()
    try:
        status = model_status(
            request.dataset.language.value,
            request.model_root,
            profile=request.profile,
        )
    except (OSError, ValueError):
        peak, peak_reason = _peak_rss()
        return {
            "schema_version": 1,
            "status": "unsupported",
            "reason": "profile_unsupported",
            "profile": request.profile,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "peak_rss_bytes": peak,
            "peak_rss_reason": peak_reason,
        }
    if not status.get("available"):
        peak, peak_reason = _peak_rss()
        reason = _controlled_reason(status.get("reason"), "model_unavailable")
        supported = status.get("supported", reason != "unsupported_profile")
        return {
            "schema_version": 1,
            "status": "unavailable" if supported else "unsupported",
            "reason": reason,
            "profile": request.profile,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "peak_rss_bytes": peak,
            "peak_rss_reason": peak_reason,
            "model_status": status,
        }
    try:
        inventory = available_model_profiles(request.dataset.language.value, request.model_root)
        option = inventory.get("profiles", {}).get(request.profile, {})
        equivalent_to = option.get("equivalent_to")
    except (OSError, ValueError):
        equivalent_to = None
    fingerprint = contextual_model_fingerprint(status)
    analyzer = LocalContextualMorphologyService(
        model_root=request.model_root,
        model_profiles={request.dataset.language.value: request.profile},
        threads=request.threads,
    )
    evaluator = evaluate_development_corpus if request.dataset.split == "dev" else evaluate_corpus
    evaluation = evaluator(
        language=request.dataset.language.value,
        corpus=request.dataset.corpus,
        corpus_sha256=request.dataset.corpus_sha256,
        output=request.output,
        analyzer=analyzer,
        max_sentences=request.max_sentences,
    )
    run_status, run_reason = _analysis_outcome(
        evaluation.get("analysis_statuses"), evaluation.get("sample_sentence_count")
    )
    peak, peak_reason = _peak_rss()
    return {
        "schema_version": 1,
        "status": run_status,
        "reason": run_reason,
        "artifact_complete": True,
        "profile": request.profile,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "peak_rss_bytes": peak,
        "peak_rss_reason": peak_reason,
        "model_status": status,
        "model_fingerprint": fingerprint,
        "equivalent_to": equivalent_to,
    }


def main() -> int:
    os.environ.update(
        {
            "HF_DATASETS_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HUB_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "TRANSFORMERS_OFFLINE": "1",
            "WANDB_DISABLED": "true",
        }
    )
    sys.addaudithook(_deny_network)
    try:
        raw = sys.stdin.buffer.read(1024**2 + 1)
        if len(raw) > 1024**2:
            raise ValueError("worker request exceeds byte limit")
        request = _WorkerRequest.model_validate_json(raw)
        result = _execute(request)
    except Exception:
        result = {
            "schema_version": 1,
            "status": "failed",
            "reason": "worker_evaluation_failed",
            "elapsed_seconds": None,
            "peak_rss_bytes": None,
            "peak_rss_reason": "worker_failed_before_measurement",
        }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - fixed module entry point
    raise SystemExit(main())
