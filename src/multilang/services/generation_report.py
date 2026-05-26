"""Final generation report writer derived from persisted job/export state."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from multilang.domain.exporting import ExportQualityGateResult
from multilang.domain.text_quality import ReviewStatus, ValidationStatus


@dataclass(frozen=True)
class GenerationReportResult:
    json_path: Path
    markdown_path: Path


def write_generation_report(
    *,
    job: object,
    export_artifact: object,
    rows: list[object],
    text_records: list[object],
    audio_assets: list[object],
    gate_result: ExportQualityGateResult,
    output_dir: Path,
) -> GenerationReportResult:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = _payload(
        job=job,
        export_artifact=export_artifact,
        rows=rows,
        text_records=text_records,
        audio_assets=audio_assets,
        gate_result=gate_result,
    )
    json_path = target_dir / "generation-report.json"
    markdown_path = target_dir / "generation-report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(payload), encoding="utf-8")
    return GenerationReportResult(json_path=json_path, markdown_path=markdown_path)


def _payload(
    *,
    job: object,
    export_artifact: object,
    rows: list[object],
    text_records: list[object],
    audio_assets: list[object],
    gate_result: ExportQualityGateResult,
) -> dict[str, Any]:
    review_counts = Counter(getattr(record, "review_status", "") for record in text_records)
    validation_counts = Counter(getattr(record, "validation_status", "") for record in text_records)
    sentence_providers = Counter(_provider(getattr(record, "sentence_provenance", None)) for record in text_records)
    translation_providers = Counter(_provider(getattr(record, "translation_provenance", None)) for record in text_records)
    audio_providers = Counter(getattr(getattr(asset, "provenance", None), "provider", "") for asset in audio_assets)
    output_path = Path(str(getattr(export_artifact, "output_path", "")))
    return {
        "job_id": getattr(job, "id", ""),
        "language": getattr(job, "language", ""),
        "source_type": getattr(job, "source_type", ""),
        "job_status": getattr(job, "status", ""),
        "total_items": getattr(job, "total_items", 0),
        "completed_items": getattr(job, "completed_items", 0),
        "failed_items": getattr(job, "failed_items", 0),
        "text_counts": {
            "total": len(text_records),
            "accepted": review_counts.get(ReviewStatus.ACCEPTED, review_counts.get(ReviewStatus.ACCEPTED.value, 0)),
            "review_required": review_counts.get(ReviewStatus.REVIEW_REQUIRED, review_counts.get(ReviewStatus.REVIEW_REQUIRED.value, 0)),
            "failed": validation_counts.get(ValidationStatus.FAILED, validation_counts.get(ValidationStatus.FAILED.value, 0)),
        },
        "level_counts": {str(level): count for level, count in sorted(gate_result.level_counts.items())},
        "export": {
            "format": getattr(getattr(export_artifact, "export_format", ""), "value", getattr(export_artifact, "export_format", "")),
            "status": getattr(getattr(export_artifact, "status", ""), "value", getattr(export_artifact, "status", "")),
            "path": str(output_path),
            "card_count": getattr(export_artifact, "card_count", len(rows)),
            "sha256": _sha256_file(output_path) if output_path.is_file() else "",
        },
        "providers": {
            "sentence": _string_counter(sentence_providers),
            "translation": _string_counter(translation_providers),
            "audio": _string_counter(audio_providers),
        },
        "blocking_issues": [issue.message for issue in gate_result.issues],
        "warnings": [warning.message for warning in gate_result.warnings],
    }


def _provider(provenance: object) -> str:
    if provenance is None:
        return "unknown"
    data = getattr(provenance, "metadata", None) or provenance
    if isinstance(data, dict):
        return str(data.get("provider") or data.get("source") or "unknown")
    provider = getattr(data, "provider", "unknown")
    return str(getattr(provider, "value", provider))


def _string_counter(counter: Counter[object]) -> dict[str, int]:
    return {str(getattr(key, "value", key)): count for key, count in counter.items() if str(key)}


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Report",
        "",
        f"job_id={payload['job_id']}",
        f"language={payload['language']}",
        f"source_type={payload['source_type']}",
        f"job_status={payload['job_status']}",
        f"card_count={payload['export']['card_count']}",
        f"export_status={payload['export']['status']}",
        f"export_path={payload['export']['path']}",
        f"export_sha256={payload['export']['sha256']}",
        "",
        "## Counts",
        "",
        f"text_total={payload['text_counts']['total']}",
        f"accepted={payload['text_counts']['accepted']}",
        f"review_required={payload['text_counts']['review_required']}",
        f"failed={payload['text_counts']['failed']}",
        f"level_counts={payload['level_counts']}",
        "",
        "## Gate",
        "",
        f"blocking_issues={payload['blocking_issues']}",
        f"warnings={payload['warnings']}",
        "",
    ]
    return "\n".join(lines)


__all__ = ["GenerationReportResult", "write_generation_report"]
