"""Final generation report writer derived from persisted job/export state."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from multilang.domain.audio import AudioAssetKind, AudioReviewStatus, AudioSynthesisStatus
from multilang.domain.exporting import ExportQualityGateResult, validate_korean_frequency_export_rows
from multilang.domain.text_quality import ReviewStatus, ValidationStatus
from multilang.services.anki_id_registry import AnkiIdKind, registry_id
from multilang.repositories.provider_call_log_repository import summarize_provider_call_records


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
    provider_call_records: list[object] | None = None,
    provider_call_summary: list[dict[str, object]] | None = None,
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
        provider_call_records=provider_call_records or [],
        provider_call_summary=provider_call_summary,
    )
    json_path = target_dir / "generation-report.json"
    markdown_path = target_dir / "generation-report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(payload), encoding="utf-8")
    return GenerationReportResult(json_path=json_path, markdown_path=markdown_path)


def build_korean_frequency_export_evidence(
    *,
    job: object,
    rows: list[object],
    text_records: list[object],
    audio_assets: list[object],
    provider_call_records: list[object],
    apkg_sha256: str,
    binding_receipt_sha256: str,
    manifest_sha256: str,
    cards_per_level: int,
    expected_items: int,
    expected_word_assets: int,
    expected_sentence_assets: int,
) -> dict[str, Any]:
    gate = validate_korean_frequency_export_rows(
        rows,  # type: ignore[arg-type]
        cards_per_level=cards_per_level,
        expected_items=expected_items,
    )
    if not gate.passed:
        raise ValueError(f"Korean frequency export gate failed: {gate.message()}")
    bundles = {getattr(row, "frequency_bundle_sha256", None) for row in rows}
    bundle_sha256 = next(iter(bundles - {None}), "")
    text_counts = _korean_text_counts(text_records)
    audio_counts = _korean_audio_counts(
        audio_assets,
        expected_word_assets=expected_word_assets,
        expected_sentence_assets=expected_sentence_assets,
    )
    provider_calls = summarize_provider_call_records(provider_call_records)
    return {
        "report_schema": "korean-frequency-export-report-v1",
        "job": {
            "id": str(getattr(job, "id", "")),
            "language": str(getattr(job, "language", "")),
            "source_type": str(getattr(job, "source_type", "")),
            "status": str(getattr(job, "status", "")),
            "total_items": int(getattr(job, "total_items", expected_items) or 0),
            "failed_items": int(getattr(job, "failed_items", 0) or 0),
        },
        "frequency_bundle": {
            "content_sha256": bundle_sha256,
            "manifest_sha256": manifest_sha256,
            "binding_receipt_sha256": binding_receipt_sha256,
        },
        "anki_ids": {
            "model": registry_id(family="korean_frequency", role="model", kind=AnkiIdKind.MODEL),
            "parent_deck": registry_id(family="korean_frequency", role="parent_deck", kind=AnkiIdKind.DECK),
            "level_1_deck": registry_id(family="korean_frequency", role="level_1_deck", kind=AnkiIdKind.DECK),
            "level_2_deck": registry_id(family="korean_frequency", role="level_2_deck", kind=AnkiIdKind.DECK),
            "level_3_deck": registry_id(family="korean_frequency", role="level_3_deck", kind=AnkiIdKind.DECK),
        },
        "export": {
            "format": "apkg",
            "apkg_sha256": apkg_sha256,
            "card_count": len(rows),
            "expected_items": expected_items,
            "cards_per_level": cards_per_level,
        },
        "level_counts": {str(level): count for level, count in sorted(gate.level_counts.items())},
        "lexical": {
            "row_count": len(rows),
            "expected_items": expected_items,
            "duplicate_lemma_keys": _duplicate_count(rows, "lemma_key"),
            "rejection_count": int(getattr(job, "failed_items", 0) or 0),
        },
        "text": text_counts,
        "adaptive_i_plus_one": _korean_adaptive_counts(text_records),
        "audio": audio_counts,
        "provider_calls": provider_calls,
        "denominators": _provider_denominators(provider_call_records),
        "privacy": {
            "excluded": [
                "learner_text",
                "prompts",
                "provider_payloads",
                "credentials",
                "review_notes",
                "private_paths",
            ]
        },
    }


def write_korean_frequency_generation_report(
    evidence: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
) -> GenerationReportResult:
    if json_path == markdown_path:
        raise ValueError("generation report output paths must be distinct")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_korean_markdown(evidence), encoding="utf-8")
    return GenerationReportResult(json_path=json_path, markdown_path=markdown_path)


def _payload(
    *,
    job: object,
    export_artifact: object,
    rows: list[object],
    text_records: list[object],
    audio_assets: list[object],
    gate_result: ExportQualityGateResult,
    provider_call_records: list[object],
    provider_call_summary: list[dict[str, object]] | None,
) -> dict[str, Any]:
    review_counts = Counter(getattr(record, "review_status", "") for record in text_records)
    validation_counts = Counter(getattr(record, "validation_status", "") for record in text_records)
    sentence_providers = Counter(_provider(getattr(record, "sentence_provenance", None)) for record in text_records)
    translation_providers = Counter(_provider(getattr(record, "translation_provenance", None)) for record in text_records)
    audio_providers = Counter(getattr(getattr(asset, "provenance", None), "provider", "") for asset in audio_assets)
    fallback_audio_count = sum(1 for asset in audio_assets if getattr(getattr(asset, "provenance", None), "fallback_used", False))
    invalid_translation_count = sum(1 for record in text_records if _looks_like_invalid_translation(getattr(record, "translation_text", "") or ""))
    output_path = Path(str(getattr(export_artifact, "output_path", "")))
    telemetry = provider_call_summary if provider_call_summary is not None else summarize_provider_call_records(provider_call_records)
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
        "quality_counts": {
            "duplicate_lemma_keys": _duplicate_count(rows, "lemma_key"),
            "duplicate_words": _duplicate_count(rows, "word"),
            "invalid_translations": invalid_translation_count,
            "audio_fallback_count": fallback_audio_count,
        },
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
        "provider_calls": telemetry,
        "gates": {
            "passed": gate_result.passed,
            "partial": gate_result.partial,
            "failed": [issue.code for issue in gate_result.issues],
            "warnings": [warning.code for warning in gate_result.warnings],
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


def _duplicate_count(rows: list[object], field_name: str) -> int:
    values = [str(getattr(getattr(row, "identity", row), field_name, getattr(row, field_name, ""))).casefold() for row in rows]
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _looks_like_invalid_translation(value: str) -> bool:
    from multilang.services.text_validation import looks_like_invalid_translation

    return looks_like_invalid_translation(value)


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _korean_text_counts(text_records: list[object]) -> dict[str, int]:
    review_counts = Counter(_enum_value(getattr(record, "review_status", "")) for record in text_records)
    validation_counts = Counter(_enum_value(getattr(record, "validation_status", "")) for record in text_records)
    return {
        "total": len(text_records),
        "accepted": review_counts.get(ReviewStatus.ACCEPTED.value, 0),
        "review_required": review_counts.get(ReviewStatus.REVIEW_REQUIRED.value, 0),
        "validation_failed": validation_counts.get(ValidationStatus.FAILED.value, 0),
        "review_receipt_count": sum(1 for record in text_records if getattr(record, "text_review_receipt_sha256", None)),
    }


def _korean_adaptive_counts(text_records: list[object]) -> dict[str, object]:
    known_counts = Counter()
    history_2_plus_1_count = 0
    adaptive_count = 0
    for record in text_records:
        evidence = getattr(record, "adaptive_i_plus_one_evidence", None)
        if evidence is not None:
            adaptive_count += 1
            known_counts[str(int(getattr(evidence, "known_concept_count", 0) or 0))] += 1
        selection = getattr(record, "candidate_selection_evidence", None)
        if (
            selection is not None
            and getattr(selection, "initial_candidate_count", None) == 2
            and getattr(selection, "repair_attempt_count", None) == 1
        ):
            history_2_plus_1_count += 1
    return {
        "record_count": len(text_records),
        "adaptive_history_count": adaptive_count,
        "history_2_plus_1_count": history_2_plus_1_count,
        "known_concept_count_distribution": dict(sorted(known_counts.items())),
    }


def _korean_audio_counts(
    audio_assets: list[object],
    *,
    expected_word_assets: int,
    expected_sentence_assets: int,
) -> dict[str, object]:
    counts = {
        AudioAssetKind.WORD.value: {"expected": expected_word_assets, "total": 0, "approved": 0, "missing": 0},
        AudioAssetKind.SENTENCE.value: {"expected": expected_sentence_assets, "total": 0, "approved": 0, "missing": 0},
    }
    fallback_count = 0
    artifact_hash_count = 0
    for asset in audio_assets:
        kind = _enum_value(getattr(asset, "asset_kind", ""))
        if kind not in counts:
            continue
        bucket = counts[kind]
        bucket["total"] = int(bucket["total"]) + 1
        provenance = getattr(asset, "provenance", None)
        if getattr(provenance, "fallback_used", False):
            fallback_count += 1
        if getattr(provenance, "artifact_sha256", None):
            artifact_hash_count += 1
        if (
            _enum_value(getattr(provenance, "status", "")) == AudioSynthesisStatus.SYNTHESIZED.value
            and _enum_value(getattr(provenance, "audio_review_status", "")) == AudioReviewStatus.APPROVED.value
            and not getattr(provenance, "fallback_used", False)
            and getattr(provenance, "artifact_sha256", None)
        ):
            bucket["approved"] = int(bucket["approved"]) + 1
    for bucket in counts.values():
        bucket["missing"] = max(0, int(bucket["expected"]) - int(bucket["total"]))
    return {
        "word": counts[AudioAssetKind.WORD.value],
        "sentence": counts[AudioAssetKind.SENTENCE.value],
        "fallback_count": fallback_count,
        "artifact_hash_count": artifact_hash_count,
    }


def _provider_denominators(provider_call_records: list[object]) -> dict[str, int]:
    return {
        "provider_call_records": len(provider_call_records),
        "latency_ms_values": sum(1 for record in provider_call_records if getattr(record, "latency_ms", None) is not None),
        "token_values": sum(
            1
            for record in provider_call_records
            if any(getattr(record, field, None) is not None for field in ("input_tokens", "output_tokens", "total_tokens"))
        ),
        "cost_values": sum(1 for record in provider_call_records if getattr(record, "estimated_cost", None) is not None),
        "route_policy_sha256_values": sum(1 for record in provider_call_records if getattr(record, "route_policy_sha256", None)),
        "retry_values": sum(1 for record in provider_call_records if getattr(record, "attempt", None) is not None),
        "cache_key_sha256_values": sum(1 for record in provider_call_records if getattr(record, "cache_key_sha256", None)),
    }


def _korean_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Korean Frequency Generation Report",
        "",
        f"job_id={payload['job']['id']}",
        f"language={payload['job']['language']}",
        f"source_type={payload['job']['source_type']}",
        f"card_count={payload['export']['card_count']}",
        f"exact_apkg_sha256={payload['export']['apkg_sha256']}",
        f"frequency_bundle_sha256={payload['frequency_bundle']['content_sha256']}",
        f"frequency_manifest_sha256={payload['frequency_bundle']['manifest_sha256']}",
        f"binding_receipt_sha256={payload['frequency_bundle']['binding_receipt_sha256']}",
        f"level_counts={payload['level_counts']}",
        "",
        "## Evidence Counts",
        "",
        f"text={payload['text']}",
        f"adaptive_i_plus_one={payload['adaptive_i_plus_one']}",
        f"audio={payload['audio']}",
        f"denominators={payload['denominators']}",
        "",
        "## Provider Calls",
        "",
    ]
    for row in payload.get("provider_calls", []):
        lines.append(
            "provider_call="
            f"provider:{row.get('provider')} operation:{row.get('operation')} status:{row.get('status')} "
            f"calls:{row.get('calls')} retries:{row.get('retry_attempts')} "
            f"latency_ms_total:{row.get('latency_ms_total')} tokens:{row.get('total_tokens')} "
            f"cost:{row.get('estimated_cost')} fallbacks:{row.get('fallback_count')}"
        )
    lines.append("")
    return "\n".join(lines)


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
        f"duplicate_lemma_keys={payload['quality_counts']['duplicate_lemma_keys']}",
        f"duplicate_words={payload['quality_counts']['duplicate_words']}",
        f"invalid_translations={payload['quality_counts']['invalid_translations']}",
        f"audio_fallback_count={payload['quality_counts']['audio_fallback_count']}",
        "",
        "## Gate",
        "",
        f"gate_passed={payload['gates']['passed']}",
        f"gate_partial={payload['gates']['partial']}",
        f"failed_gates={payload['gates']['failed']}",
        f"warning_gates={payload['gates']['warnings']}",
        f"blocking_issues={payload['blocking_issues']}",
        f"warnings={payload['warnings']}",
        "",
        "## Provider Calls",
        "",
    ]
    for row in payload.get("provider_calls", []):
        lines.append(
            "provider_call="
            f"provider:{row.get('provider')} operation:{row.get('operation')} status:{row.get('status')} "
            f"calls:{row.get('calls')} retries:{row.get('retry_attempts')} "
            f"latency_ms_total:{row.get('latency_ms_total')} avg:{row.get('latency_ms_avg')} p95:{row.get('latency_ms_p95')} "
            f"tokens:{row.get('total_tokens')} cost:{row.get('estimated_cost')} "
            f"fallbacks:{row.get('fallback_count')} circuit_blocks:{row.get('circuit_open_blocks')}"
        )
    lines.extend([""])
    return "\n".join(lines)


__all__ = [
    "GenerationReportResult",
    "build_korean_frequency_export_evidence",
    "write_generation_report",
    "write_korean_frequency_generation_report",
]
