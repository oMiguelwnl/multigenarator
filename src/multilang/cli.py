"""Typer CLI for Multilang job orchestration."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import typer
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from multilang.cli_commands import (
    generation,
    korean_audio,
    korean_evidence,
    korean_foundations,
    korean_frequency,
    korean_release,
    latin,
    personal_sources,
    phase33,
    phonetics,
)
from multilang.cli_commands.common import (
    LOCAL_SMOKE_FIXTURE_DIR as LOCAL_SMOKE_FIXTURE_DIR,
)
from multilang.cli_commands.common import (
    LOCAL_SMOKE_LANGUAGE as LOCAL_SMOKE_LANGUAGE,
)
from multilang.cli_commands.common import (
    LOCAL_SMOKE_WORDS as LOCAL_SMOKE_WORDS,
)
from multilang.cli_commands.common import (
    TEST_MODE_CARDS_PER_LEVEL as TEST_MODE_CARDS_PER_LEVEL,
)
from multilang.db.models import GenerationJob
from multilang.db.provisioning import ensure_database_schema
from multilang.domain.exporting import ExportArtifactFormat
from multilang.domain.jobs import (
    GenerationRequest,
    JobProgressSnapshot,
    JobStage,
    JobStatus,
    SupportedLanguage,
)
from multilang.domain.korean import KoreanFrequencyJobAuthority
from multilang.domain.korean_provider import KoreanProviderPolicy, KoreanProviderTask
from multilang.domain.webdav import (
    WebDAVError,
)
from multilang.output_paths import DEFAULT_OUTPUT_DIR
from multilang.progress import ProgressRenderer
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
from multilang.repositories.text_repository import TextRepository
from multilang.runtime import (
    KoreanFrequencyTextRuntimeAuthority,
    build_korean_frequency_text_runtime_service,
    build_runtime_service,
)
from multilang.services.anki_id_registry import assert_anki_id_registry_clean
from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.execution_report import JobExecutionReport
from multilang.services.frequency_decks import build_frequency_level
from multilang.services.generate_job import GenerateJobResult, GenerateJobService
from multilang.services.generate_text_items import GenerateTextProgress
from multilang.services.highlight_import_preview import build_highlight_import_preview
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.job_summary import JobLifecycleSummary
from multilang.services.korean_audio import (
    KoreanAudioAuthority,
    capture_korean_azure_catalog_pilot,
    synthesize_korean_frequency_audio,
)
from multilang.services.korean_audio_pilot_evidence import (
    KoreanAudioPilotAuthority,
)
from multilang.services.korean_curriculum import KoreanFoundationFamily
from multilang.services.korean_foundation_evidence import (
    check_korean_foundation_validation_receipt_continuity,
    inspect_fixed_korean_foundation_evidence_inbox,
    validate_and_write_fixed_korean_foundation_validation_receipt,
)
from multilang.services.korean_foundation_export import (
    _build_korean_foundation_export_bundle_from_snapshot,
    _inspect_staged_apkg,
    _inspect_staged_tabular_bundle,
    build_korean_foundation_export_bundle,
    export_korean_foundation,
)
from multilang.services.korean_foundation_snapshot import (
    activate_prepared_korean_foundation_snapshot_from_receipt,
    prepare_korean_foundation_snapshot_from_receipt,
    resolve_active_korean_foundation_snapshot,
    verify_active_korean_foundation_snapshot_provenance,
    verify_prepared_korean_foundation_snapshot,
)
from multilang.services.korean_foundation_snapshot_fallback import (
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
)
from multilang.services.korean_frequency import (
    KoreanFrequencySourceRetriever,
    load_korean_final_frequency_entries,
)
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.korean_production_evidence import (
    KoreanProductionEvidenceAuthority,
    build_korean_production_audit_payload,
    load_korean_production_evidence_rows,
    render_korean_production_audit_markdown,
    validate_korean_production_final_evidence,
    validate_korean_production_review_batches,
    validate_korean_production_run_result,
)
from multilang.services.korean_release_delivery import (
    execute_korean_release_delivery,
    validate_korean_release_delivery,
)
from multilang.services.latin_export import export_latin_mvp_bundle
from multilang.services.latin_mvp import LatinMvpGenerationService
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.lexical_lookup import LexicalLookup, normalize_lexical_key
from multilang.services.text_review import ReviewReport, TextReviewService
from multilang.services.webdav_highlight_fetch import WebDAVHighlightFetchService
from multilang.settings import Settings

_KOREAN_FOUNDATION_EXPORT_ROOT = DEFAULT_OUTPUT_DIR / "decks/korean-foundations"

_KOREAN_FOUNDATION_EXPORT_NAMES = (
    "hangul.apkg",
    "hangul-csv",
    "hangul-tsv",
    "pronunciation-i-plus-1.apkg",
    "pronunciation-i-plus-1-csv",
    "pronunciation-i-plus-1-tsv",
)

ConflictChecker = Callable[[GenerationRequest], bool]
GenerateExecutor = Callable[[GenerationRequest], Any]
RequestedItemKeysLoader = Callable[[GenerationRequest], list[str]]
ItemProcessor = Callable[[str], None]
ProgressSink = Callable[[str], None]
ReviewReportBuilder = Callable[..., ReviewReport]
WebDAVServiceFactory = Callable[[], Any]
_KOREAN_PREVIEW_ERROR = (
    "korean_highlight_preview_error=korean_resolution_unavailable"
)


@dataclass(frozen=True, slots=True)
class _KoreanFoundationExportInspection:
    artifact_count: int
    receipt_sha256: str
    bundle_sha256: str
    snapshot_root_sha256: str


def _validate_foundation_sha256(value: str) -> str:
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise typer.BadParameter("lowercase SHA-256")
    return value


def _validate_optional_sha256(value: str | None) -> str | None:
    if value is None:
        return None
    return _validate_foundation_sha256(value)


def _validate_korean_frequency_authority_stage(value: str) -> str:
    if value not in {"pilot_base", "pilot_audio", "full"}:
        raise typer.BadParameter("pilot_base, pilot_audio, or full")
    return value


def _foundation_receipt_sha256(receipt: object) -> str:
    payload = receipt.model_dump(mode="json")
    raw = (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    return sha256(raw).hexdigest()


def _foundation_failure_reason(exc: ValueError) -> str:
    reason = getattr(getattr(exc, "reason_code", None), "value", None)
    return reason if isinstance(reason, str) else "operation_failed"


def _fail_korean_foundation_operation(exc: ValueError) -> None:
    typer.echo(f"korean_foundations_error={_foundation_failure_reason(exc)}")
    raise typer.Exit(code=1) from exc


def _fail_korean_frequency_source_operation(exc: ValueError) -> None:
    typer.echo("korean_frequency_source_error=operation_failed")
    raise typer.Exit(code=1) from exc


def _fail_korean_checkpoint_authority_operation(exc: ValueError) -> None:
    typer.echo("korean_checkpoint_authority_error=operation_failed")
    raise typer.Exit(code=1) from exc


def _fail_korean_source_review_operation(exc: ValueError) -> None:
    typer.echo("korean_source_review_error=operation_failed")
    raise typer.Exit(code=1) from exc


def _fail_korean_frequency_text_operation(exc: ValueError) -> None:
    typer.echo("korean_frequency_text_error=operation_failed")
    raise typer.Exit(code=1) from exc


def _fail_korean_production_evidence_operation(exc: ValueError) -> None:
    typer.echo("korean_production_evidence_error=operation_failed")
    raise typer.Exit(code=1) from exc


def _fail_korean_release_safety_operation(exc: ValueError) -> None:
    typer.echo("korean_release_safety_error=operation_failed")
    raise typer.Exit(code=1) from exc


def _korean_production_sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_korean_production_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Korean production evidence input must be a JSON object")
    return payload


def _write_korean_production_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    if temp_path.exists():
        raise ValueError("Korean production evidence temporary output already exists")
    try:
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def _write_korean_production_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    if temp_path.exists():
        raise ValueError("Korean production evidence temporary output already exists")
    try:
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def _parse_korean_release_authority_values(values: list[str] | None) -> dict[str, str]:
    authorities: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError("Korean release authority must use label=sha256")
        label, digest = value.split("=", 1)
        if not label:
            raise ValueError("Korean release authority label is required")
        authorities[label] = _validate_foundation_sha256(digest)
    if not authorities:
        raise ValueError("Korean release authority is required")
    return authorities


def _fail_korean_frequency_export_operation(exc: ValueError) -> None:
    code = "no_partial_required" if "--no-partial" in str(exc) else "operation_failed"
    typer.echo(f"korean_frequency_export_error={code}")
    if code == "operation_failed":
        typer.echo(str(exc))
    raise typer.Exit(code=1) from exc


def _require_clean_anki_id_registry_for_export() -> None:
    assert_anki_id_registry_clean(production_roots=True)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Korean provider/catalog pilot input must be a JSON object")
    return payload


def _read_korean_provider_policy(path: Path) -> KoreanProviderPolicy:
    try:
        return KoreanProviderPolicy.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError("Korean provider policy file is invalid") from exc


def _catalog_result_hash(catalog_result: dict[str, object], field_name: str) -> str:
    value = catalog_result.get(field_name)
    if not isinstance(value, str):
        raise ValueError("Korean provider/catalog pilot catalog hash is missing")
    return _validate_foundation_sha256(value)


def _list_provider_call_rows_read_only(*, database_url: str, job_id: str) -> list[object]:
    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database not in {None, "", ":memory:"}:
        if not Path(str(url.database)).is_file():
            raise ValueError("Korean provider/catalog pilot database is unavailable")
    engine = create_engine(database_url)
    session = Session(engine)
    try:
        return ProviderCallLogRepository(session).list_for_job(job_id)
    except Exception as exc:
        raise ValueError("Korean provider/catalog pilot provider-call read failed") from exc
    finally:
        session.close()
        engine.dispose()


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    if temp_path.exists():
        raise ValueError("Korean provider/catalog pilot temporary output already exists")
    try:
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def _read_markdown_json_mapping(path: Path) -> dict[str, object]:
    body = path.read_text(encoding="utf-8")
    fence_start = body.find("```json")
    if fence_start < 0:
        raise ValueError("Korean voice profile authority JSON block is missing")
    json_start = body.find("\n", fence_start)
    if json_start < 0:
        raise ValueError("Korean voice profile authority JSON block is invalid")
    fence_end = body.find("```", json_start + 1)
    if fence_end < 0:
        raise ValueError("Korean voice profile authority JSON block is invalid")
    payload = json.loads(body[json_start:fence_end].strip())
    if not isinstance(payload, dict):
        raise ValueError("Korean voice profile authority must be a JSON object")
    return payload


def _ensure_korean_voice_profile_outputs_distinct(
    *,
    outputs: tuple[Path, ...],
    protected_inputs: dict[str, Path],
) -> None:
    input_paths = {path.resolve() for path in protected_inputs.values()}
    output_paths = tuple(path.resolve() for path in outputs)
    if len(set(output_paths)) != len(output_paths) or any(path in input_paths for path in output_paths):
        raise ValueError("Korean voice profile outputs must be distinct from inputs and each other")


def setup_korean_frequency_live_pilot_candidates(
    *,
    database_url: str,
    job_id: str,
    authority: KoreanFrequencyJobAuthority,
    frequency_bundle_root: Path,
    binding_receipt_sha256: str,
    provider_policy: KoreanProviderPolicy,
    max_items: int,
) -> dict[str, object]:
    """Prepare the local live Korean text/catalog pilot denominator."""

    if authority.stage != "pilot_base":
        raise ValueError("Korean live pilot candidate setup requires pilot_base authority")
    if max_items != 10:
        raise ValueError("Korean live pilot candidate setup requires exactly 10 items")
    if provider_policy.policy_sha256 != authority.provider_policy_sha256:
        raise ValueError("Korean live pilot provider policy drift")
    route = provider_policy.route_for(KoreanProviderTask.SENTENCE_GENERATION)
    route.assert_within_budget(
        input_tokens=0,
        output_tokens=0,
        estimated_cost_usd=0.0,
        latency_ms=0,
        batch_items=max_items,
        concurrency=1,
        timeout_seconds=route.budget.timeout_seconds,
    )
    if provider_policy.fallback_policy != "none":
        raise ValueError("Korean live pilot fallback policy drift")

    database_relative_path = _sqlite_database_relative_path(database_url)
    if _git_check_ignore(database_relative_path) != "passed":
        raise ValueError("Korean live pilot database must be gitignored")
    _verify_korean_frequency_phase31_authority(authority)
    runtime_authority = _runtime_authority_from_cli(
        database_url=database_url,
        job_id=job_id,
        frequency_bundle_root=frequency_bundle_root,
        binding_receipt_sha256=binding_receipt_sha256,
        authority=authority,
    )
    entries = load_korean_final_frequency_entries(
        job_id=job_id,
        bundle_root=frequency_bundle_root,
        binding_receipt_sha256=binding_receipt_sha256,
        authority=authority,
        repo_root=Path.cwd(),
    )
    candidates = build_frequency_level(
        SupportedLanguage.KO,
        level=1,
        required_count_per_level=1000,
        korean_final_entries=entries,
        source_review_receipt_sha256=runtime_authority.binding_receipt_sha256,
        source_review_aggregate_sha256=authority.source_review_aggregate_sha256,
    )[:max_items]
    if len(candidates) != max_items:
        raise ValueError("Korean live pilot candidate denominator mismatch")

    engine = create_engine(database_url)
    ensure_database_schema(engine, database_url)
    session = Session(engine)
    try:
        job_repository = JobRepository(session)
        lexical_repository = LexicalRepository(session)
        _ensure_korean_frequency_job(job_repository, job_id=job_id, authority=authority)
        job_repository.bind_execution_authority(job_id, authority)
        item_rows = []
        item_keys = []
        for position, candidate in enumerate(candidates, start=1):
            item_key = f"level-1-rank-{position:04d}"
            item_rows.append((item_key, candidate.lemma_key, candidate))
            item_keys.append(item_key)
        lexical_repository.upsert_candidates(
            job_id=job_id,
            run_key=f"ko-frequency-{job_id}",
            source_type="frequency",
            candidates=item_rows,
        )
        job_repository.record_item_successes(job_id, item_keys=item_keys, completed_stage=JobStage.INGEST)
        job_repository.advance_job_to_stage(job_id, JobStage.GENERATE_TEXT)
        ingested_item_count = len(lexical_repository.list_candidates(job_id))
        provider_attempt_count = job_repository.count_provider_attempts(job_id)
    finally:
        session.close()
        engine.dispose()

    return {
        "schema_version": "korean-live-pilot-candidate-setup-v1",
        "job_id": job_id,
        "database_kind": "local_ignored_sqlite",
        "database_relative_path": database_relative_path,
        "database_gitignore_check": "passed",
        "authority_stage": authority.stage,
        "candidate_count": len(candidates),
        "ingested_item_count": ingested_item_count,
        "provider_attempt_count": provider_attempt_count,
        "audio_synthesis_enabled": False,
        "max_items": max_items,
        "max_concurrency": route.budget.max_concurrency,
        "max_attempts": route.budget.max_attempts,
        "cost_ceiling_usd": f"{route.budget.max_estimated_cost_usd:.2f}",
        "fallback_policy": provider_policy.fallback_policy,
        "production_database_used": False,
        "provider_policy_sha256": authority.provider_policy_sha256,
        "pilot_authority_sha256": authority.pilot_authority_sha256,
        "final_frequency_bundle_sha256": authority.frequency_bundle_content_sha256,
    }


def _sqlite_database_relative_path(database_url: str) -> str:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or url.database in {None, "", ":memory:"}:
        raise ValueError("Korean live pilot requires a local SQLite database")
    database_path = Path(str(url.database))
    if database_path.is_absolute():
        try:
            database_path = database_path.resolve().relative_to(Path.cwd().resolve())
        except ValueError as exc:
            raise ValueError("Korean live pilot database must be inside the workspace") from exc
    if any(part in {"", ".", ".."} for part in database_path.parts):
        raise ValueError("Korean live pilot database path is invalid")
    return database_path.as_posix()


def _git_check_ignore(relative_path: str) -> str:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", relative_path],
        cwd=Path.cwd(),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return "passed" if result.returncode == 0 else "failed"


def _default_azure_catalog_endpoint(settings: Settings) -> str:
    region = (settings.azure_speech_region or "").strip()
    if not region:
        raise ValueError("Azure Speech region is required for Korean catalog capture")
    return f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"


def _build_korean_frequency_job_authority(
    *,
    stage: str,
    phase31_active_pointer_sha256: str,
    phase31_active_pointer_content_sha256: str,
    phase31_validation_receipt_sha256: str,
    phase31_snapshot_manifest_sha256: str,
    phase31_snapshot_root_sha256: str,
    frequency_bundle_manifest_sha256: str,
    frequency_bundle_content_sha256: str,
    source_retrieval_sha256: str,
    source_build_result_sha256: str,
    source_review_aggregate_sha256: str,
    provider_policy_sha256: str,
    pilot_authority_sha256: str,
    catalog_locator_sha256: str | None = None,
    catalog_content_sha256: str | None = None,
    profile_sample_authority_sha256: str | None = None,
    provider_review_authority_sha256: str | None = None,
    heard_review_authority_sha256: str | None = None,
) -> KoreanFrequencyJobAuthority:
    return KoreanFrequencyJobAuthority(
        stage=stage,
        phase31_pointer_locator_sha256=phase31_active_pointer_sha256,
        phase31_pointer_content_sha256=phase31_active_pointer_content_sha256,
        phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
        phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
        phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
        frequency_bundle_locator_sha256=frequency_bundle_manifest_sha256,
        frequency_bundle_content_sha256=frequency_bundle_content_sha256,
        source_retrieval_sha256=source_retrieval_sha256,
        source_build_result_sha256=source_build_result_sha256,
        source_review_aggregate_sha256=source_review_aggregate_sha256,
        provider_policy_sha256=provider_policy_sha256,
        pilot_authority_sha256=pilot_authority_sha256,
        catalog_locator_sha256=catalog_locator_sha256,
        catalog_content_sha256=catalog_content_sha256,
        profile_sample_authority_sha256=profile_sample_authority_sha256,
        provider_review_authority_sha256=provider_review_authority_sha256,
        heard_review_authority_sha256=heard_review_authority_sha256,
    )


def _build_korean_production_evidence_authority_from_cli(
    *,
    job_id: str,
    phase31_active_pointer_sha256: str,
    phase31_active_pointer_content_sha256: str,
    phase31_validation_receipt_sha256: str,
    phase31_snapshot_manifest_sha256: str,
    phase31_snapshot_root_sha256: str,
    frequency_bundle_manifest_sha256: str,
    frequency_bundle_content_sha256: str,
    source_access_authority_sha256: str,
    source_retrieval_sha256: str,
    source_transformation_sha256: str,
    source_build_result_sha256: str,
    source_review_aggregate_sha256: str,
    final_bundle_authority_sha256: str,
    provider_policy_sha256: str,
    provider_review_authority_sha256: str,
    budget_authority_sha256: str,
    retry_policy_sha256: str,
    full_run_authority_sha256: str,
    catalog_locator_sha256: str,
    catalog_content_sha256: str,
    profile_sample_authority_sha256: str,
    heard_review_authority_sha256: str,
    full_binding_receipt_sha256: str,
) -> KoreanProductionEvidenceAuthority:
    return KoreanProductionEvidenceAuthority(
        job_id=job_id,
        phase31_pointer_locator_sha256=phase31_active_pointer_sha256,
        phase31_pointer_content_sha256=phase31_active_pointer_content_sha256,
        phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
        phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
        phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
        frequency_bundle_locator_sha256=frequency_bundle_manifest_sha256,
        frequency_bundle_content_sha256=frequency_bundle_content_sha256,
        source_access_authority_sha256=source_access_authority_sha256,
        source_retrieval_sha256=source_retrieval_sha256,
        source_transformation_sha256=source_transformation_sha256,
        source_build_result_sha256=source_build_result_sha256,
        source_review_aggregate_sha256=source_review_aggregate_sha256,
        final_bundle_authority_sha256=final_bundle_authority_sha256,
        provider_policy_sha256=provider_policy_sha256,
        provider_review_authority_sha256=provider_review_authority_sha256,
        budget_authority_sha256=budget_authority_sha256,
        retry_policy_sha256=retry_policy_sha256,
        full_run_authority_sha256=full_run_authority_sha256,
        catalog_locator_sha256=catalog_locator_sha256,
        catalog_content_sha256=catalog_content_sha256,
        profile_sample_authority_sha256=profile_sample_authority_sha256,
        heard_review_authority_sha256=heard_review_authority_sha256,
        full_binding_receipt_sha256=full_binding_receipt_sha256,
    )


def _ensure_korean_production_outputs_distinct(
    *,
    outputs: tuple[Path, ...],
    protected_inputs: dict[str, Path],
) -> None:
    input_paths = {path.resolve() for path in protected_inputs.values()}
    output_paths = tuple(path.resolve() for path in outputs)
    if len(set(output_paths)) != len(output_paths) or any(path in input_paths for path in output_paths):
        raise ValueError("Korean production evidence outputs must be distinct from inputs and each other")


def _hash_korean_production_inputs(protected_inputs: dict[str, Path]) -> dict[str, str]:
    return {label: _korean_production_sha256_file(path) for label, path in protected_inputs.items()}


def _read_korean_production_required_json_inputs(
    protected_inputs: dict[str, Path],
    *,
    final: bool,
) -> None:
    for label in ("catalog_result", "voice_profile", "text_result", "audio_result"):
        _read_korean_production_json_mapping(protected_inputs[label])
    if final:
        _read_korean_production_json_mapping(protected_inputs["generation_report_json"])


def _write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    if temp_path.exists():
        raise ValueError("temporary output already exists")
    try:
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def _verify_korean_frequency_phase31_authority(authority: KoreanFrequencyJobAuthority) -> None:
    report = verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
        expected_receipt_sha256=authority.phase31_validation_receipt_sha256,
    )
    expected = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    for field, value in expected.items():
        if getattr(report, field, None) != value:
            raise ValueError("Phase 31 active authority drift")


def _with_job_repository(database_url: str, action: Any) -> Any:
    engine = create_engine(database_url)
    ensure_database_schema(engine, database_url)
    session = Session(engine)
    try:
        return action(JobRepository(session))
    finally:
        session.close()


def _ensure_korean_frequency_job(
    repository: JobRepository,
    *,
    job_id: str,
    authority: KoreanFrequencyJobAuthority,
) -> None:
    job = repository.get_job(job_id)
    if job is None:
        repository.session.add(
            GenerationJob(
                id=job_id,
                run_key=f"ko-frequency-{job_id}",
                language=SupportedLanguage.KO.value,
                source_type="frequency",
                source_fingerprint=authority.frequency_bundle_content_sha256 or "",
                status=JobStatus.PENDING.value,
                current_stage=JobStage.INGEST.value,
                total_items=3000,
                completed_items=0,
                failed_items=0,
                retrying_items=0,
                skipped_duplicates=0,
                resume_state={},
            )
        )
        repository.session.commit()
        return
    if job.language != SupportedLanguage.KO.value or job.source_type != "frequency":
        raise ValueError("job is not a Korean frequency job")


def _bind_korean_frequency_authority(
    *,
    database_url: str,
    job_id: str,
    authority: KoreanFrequencyJobAuthority,
) -> KoreanFrequencyJobAuthority:
    def action(repository: JobRepository) -> KoreanFrequencyJobAuthority:
        _ensure_korean_frequency_job(repository, job_id=job_id, authority=authority)
        if authority.stage in {"pilot_audio", "full"}:
            return repository.bind_audio_authority(job_id, authority)
        return repository.bind_execution_authority(job_id, authority)

    return _with_job_repository(database_url, action)


def _check_korean_frequency_authority(
    *,
    database_url: str,
    job_id: str,
    authority: KoreanFrequencyJobAuthority,
) -> KoreanFrequencyJobAuthority:
    def action(repository: JobRepository) -> KoreanFrequencyJobAuthority:
        existing = repository.load_korean_authority(job_id)
        if existing.model_dump(mode="json", exclude_none=True) != authority.model_dump(mode="json", exclude_none=True):
            raise ValueError("Korean frequency authority drift")
        return existing

    return _with_job_repository(database_url, action)


def _runtime_authority_from_cli(
    *,
    database_url: str,
    job_id: str,
    frequency_bundle_root: Path,
    binding_receipt_sha256: str,
    authority: KoreanFrequencyJobAuthority,
) -> KoreanFrequencyTextRuntimeAuthority:
    if database_url.strip() != database_url or not database_url.strip():
        raise ValueError("database URL is required")
    if binding_receipt_sha256 != authority.source_review_aggregate_sha256:
        raise ValueError("Korean frequency binding receipt drift")
    return KoreanFrequencyTextRuntimeAuthority(
        job_id=job_id,
        bundle_root=frequency_bundle_root,
        binding_receipt_sha256=binding_receipt_sha256,
        authority=authority,
    )


def _korean_frequency_text_result_payload(
    *,
    job_id: str,
    authority: KoreanFrequencyJobAuthority,
    binding_receipt_sha256: str,
    synthesize_audio: bool,
    text_result: Any,
    max_items: int | None = None,
    korean_provider_policy: KoreanProviderPolicy | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "korean-frequency-text-result-v1",
        "job_id": job_id,
        "authority_stage": authority.stage,
        "binding_receipt_sha256": binding_receipt_sha256,
        "provider_policy_sha256": authority.provider_policy_sha256,
        "pilot_authority_sha256": authority.pilot_authority_sha256,
        "processed_items": text_result.processed_items,
        "accepted_items": text_result.accepted_items,
        "review_required_items": text_result.review_required_items,
        "audio_synthesis_enabled": synthesize_audio,
        "fallback_audio_items": text_result.fallback_audio_items,
        "failed_audio_items": text_result.failed_audio_items,
    }
    if korean_provider_policy is not None:
        route = korean_provider_policy.route_for(KoreanProviderTask.SENTENCE_GENERATION)
        payload.update(
            {
                "max_items": max_items,
                "max_concurrency": route.budget.max_concurrency,
                "max_attempts": route.budget.max_attempts,
                "cost_ceiling_usd": f"{route.budget.max_estimated_cost_usd:.2f}",
                "fallback_policy": korean_provider_policy.fallback_policy,
                "production_database_used": False,
            }
        )
    return payload


def _build_korean_audio_authority_from_cli(
    *,
    job_id: str,
    phase31_validation_receipt_sha256: str,
    phase31_snapshot_manifest_sha256: str,
    phase31_snapshot_root_sha256: str,
    binding_receipt_sha256: str,
    provider_policy_sha256: str,
    pilot_authority_sha256: str,
    catalog_locator_sha256: str,
    catalog_content_sha256: str,
    profile_sample_authority_sha256: str,
) -> KoreanAudioAuthority:
    return KoreanAudioAuthority(
        job_id=job_id,
        phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
        phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
        phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
        binding_receipt_sha256=binding_receipt_sha256,
        provider_policy_sha256=provider_policy_sha256,
        pilot_authority_sha256=pilot_authority_sha256,
        catalog_locator_sha256=catalog_locator_sha256,
        catalog_content_sha256=catalog_content_sha256,
        profile_sample_authority_sha256=profile_sample_authority_sha256,
    )


def _build_korean_audio_pilot_authority_from_cli(
    *,
    job_id: str,
    phase31_validation_receipt_sha256: str,
    phase31_snapshot_manifest_sha256: str,
    phase31_snapshot_root_sha256: str,
    binding_receipt_sha256: str,
    catalog_content_sha256: str,
    profile_sample_authority_sha256: str,
) -> KoreanAudioPilotAuthority:
    return KoreanAudioPilotAuthority(
        job_id=job_id,
        phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
        phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
        phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
        binding_receipt_sha256=binding_receipt_sha256,
        catalog_receipt_sha256=catalog_content_sha256,
        profile_authority_sha256=profile_sample_authority_sha256,
        budget_sha256=binding_receipt_sha256,
        retry_policy_sha256=binding_receipt_sha256,
    )


def _inspect_fixed_korean_foundation_exports() -> _KoreanFoundationExportInspection:
    snapshot = resolve_active_korean_foundation_snapshot()
    root = _KOREAN_FOUNDATION_EXPORT_ROOT
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    if not root.is_dir() or root.is_symlink():
        raise ValueError("fixed export set is unavailable")
    children = tuple(root.iterdir())
    if {child.name for child in children} != set(_KOREAN_FOUNDATION_EXPORT_NAMES):
        raise ValueError("fixed export set does not match the allowlist")
    if any(child.is_symlink() for child in children):
        raise ValueError("fixed export set contains an unsafe member")

    for family, stem in (
        (KoreanFoundationFamily.HANGUL, "hangul"),
        (KoreanFoundationFamily.PRONUNCIATION, "pronunciation-i-plus-1"),
    ):
        bundle = _build_korean_foundation_export_bundle_from_snapshot(
            snapshot,
            family=family,
        )
        _inspect_staged_apkg(root / f"{stem}.apkg", bundle=bundle)
        for export_format in (ExportArtifactFormat.CSV, ExportArtifactFormat.TSV):
            _inspect_staged_tabular_bundle(
                root / f"{stem}-{export_format.value}",
                bundle=bundle,
                export_format=export_format,
            )

    if snapshot.receipt_sha256 is None or snapshot.snapshot_root_sha256 is None:
        raise ValueError("active snapshot provenance is incomplete")
    return _KoreanFoundationExportInspection(
        artifact_count=len(children),
        receipt_sha256=snapshot.receipt_sha256,
        bundle_sha256=snapshot.bundle_sha256,
        snapshot_root_sha256=snapshot.snapshot_root_sha256,
    )


class _FailClosedKoreanPreviewResolver:
    """Hide resolver failures while recording that preview must be rejected."""

    def __init__(self, resolver: object) -> None:
        self._resolver = resolver
        self.failed = False

    def resolve_korean_highlight_text(self, text: str) -> tuple[object, ...]:
        try:
            resolved = tuple(
                self._resolver.resolve_korean_highlight_text(text)
            )
        except Exception:
            self.failed = True
            return ()
        if not resolved:
            self.failed = True
        return resolved


def default_conflict_checker(_: GenerationRequest) -> bool:
    """Return whether the request would overwrite completed items."""

    return False


def default_item_processor(_: str) -> None:
    """Default stub processor until downstream phases add real work."""

    return None


def default_progress_sink(line: str) -> None:
    """Write progress lines to the terminal."""

    typer.echo(line)


def build_generate_executor(
    service: GenerateJobService,
    *,
    settings: Settings | None = None,
    item_processor: ItemProcessor = default_item_processor,
    progress_renderer: ProgressRenderer | None = None,
    progress_sink: ProgressSink = default_progress_sink,
) -> GenerateExecutor:
    """Create a CLI executor backed by the orchestration service."""

    runtime_settings = settings or Settings()
    renderer = progress_renderer or ProgressRenderer()

    def execute(request: GenerationRequest) -> JobExecutionReport:
        orchestration = service.orchestrate(
            request,
            requested_item_keys=load_requested_item_keys(request),
        )
        progress_updates, retried_item_keys, failed_item_keys = _execute_with_progress(
            service,
            orchestration,
            max_attempts=runtime_settings.default_retry_attempts,
            item_processor=item_processor,
            progress_renderer=renderer,
            progress_sink=progress_sink,
        )
        return JobExecutionReport(
            orchestration=orchestration,
            progress_updates=progress_updates,
            retried_item_keys=retried_item_keys,
            failed_item_keys=failed_item_keys,
        )

    return execute


def _build_snapshot(
    *,
    stage: Any,
    completed_items: int,
    failed_items: int,
    retrying_items: int,
    skipped_duplicates: int,
) -> JobProgressSnapshot:
    return JobProgressSnapshot(
        stage=stage,
        completed_items=completed_items,
        failed_items=failed_items,
        retrying_items=retrying_items,
        skipped_duplicates=skipped_duplicates,
    )


def _emit_progress(
    snapshot: JobProgressSnapshot,
    *,
    total_items: int,
    progress_renderer: ProgressRenderer,
    progress_sink: ProgressSink,
    progress_updates: list[str],
) -> None:
    line = progress_renderer.render_snapshot(snapshot, total_items=total_items)
    progress_sink(line)
    progress_updates.append(line)


def _execute_with_progress(
    service: GenerateJobService,
    orchestration: GenerateJobResult,
    *,
    max_attempts: int,
    item_processor: ItemProcessor,
    progress_renderer: ProgressRenderer,
    progress_sink: ProgressSink,
) -> tuple[list[str], list[str], list[str]]:
    total_items = len(orchestration.pending_item_keys) + len(orchestration.skipped_item_keys)
    completed_items = 0
    failed_items = 0
    skipped_duplicates = len(orchestration.skipped_item_keys)
    progress_updates: list[str] = []
    retried_item_keys: list[str] = []
    failed_item_keys: list[str] = []

    _emit_progress(
        _build_snapshot(
            stage=orchestration.resume_from_stage,
            completed_items=completed_items,
            failed_items=failed_items,
            retrying_items=0,
            skipped_duplicates=skipped_duplicates,
        ),
        total_items=total_items,
        progress_renderer=progress_renderer,
        progress_sink=progress_sink,
        progress_updates=progress_updates,
    )

    for item_key in orchestration.pending_item_keys:
        for attempt in range(1, max_attempts + 1):
            try:
                item_processor(item_key)
            except Exception as exc:
                if attempt < max_attempts:
                    if item_key not in retried_item_keys:
                        retried_item_keys.append(item_key)
                    _emit_progress(
                        _build_snapshot(
                            stage=orchestration.resume_from_stage,
                            completed_items=completed_items,
                            failed_items=failed_items,
                            retrying_items=1,
                            skipped_duplicates=skipped_duplicates,
                        ),
                        total_items=total_items,
                        progress_renderer=progress_renderer,
                        progress_sink=progress_sink,
                        progress_updates=progress_updates,
                    )
                    continue

                failed_items += 1
                failed_item_keys.append(item_key)
                service.repository.record_item_failure(
                    orchestration.job_id,
                    item_key=item_key,
                    failed_stage=orchestration.resume_from_stage,
                    error=str(exc),
                    retry_count=attempt,
                )
                _emit_progress(
                    _build_snapshot(
                        stage=orchestration.resume_from_stage,
                        completed_items=completed_items,
                        failed_items=failed_items,
                        retrying_items=0,
                        skipped_duplicates=skipped_duplicates,
                    ),
                    total_items=total_items,
                    progress_renderer=progress_renderer,
                    progress_sink=progress_sink,
                    progress_updates=progress_updates,
                )
                break

            completed_items += 1
            service.repository.record_item_success(
                orchestration.job_id,
                item_key=item_key,
                completed_stage=orchestration.resume_from_stage,
            )
            _emit_progress(
                _build_snapshot(
                    stage=orchestration.resume_from_stage,
                    completed_items=completed_items,
                    failed_items=failed_items,
                    retrying_items=0,
                    skipped_duplicates=skipped_duplicates,
                ),
                total_items=total_items,
                progress_renderer=progress_renderer,
                progress_sink=progress_sink,
                progress_updates=progress_updates,
            )
            break

    return progress_updates, retried_item_keys, failed_item_keys


def load_requested_item_keys(request: GenerationRequest) -> list[str]:
    """Resolve deterministic item keys for the current orchestration phase."""

    if request.source_type == "frequency":
        levels = [request.level] if request.level is not None else [1, 2, 3]
        cards_per_level = request.resolved_cards_per_level()
        return [
            f"level-{level}-rank-{index:04d}"
            for level in levels
            for index in range(1, cards_per_level + 1)
        ]

    if request.input_file is None:
        raise ValueError("word-list requests require an input file")

    return [
        line.strip()
        for line in request.input_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _validate_request(request: GenerationRequest, *, test_mode: bool = False) -> None:
    if request.source_type == "frequency" and request.level is None:
        # Allow None level for frequency - indicates full 3-level deck build
        pass
    if request.source_type in {"word-list", "kindle-highlights"} and request.input_file is None:
        source_name = "highlights" if request.source_type == "kindle-highlights" else "word-list"
        raise typer.BadParameter(f"--input-file is required when --source {source_name}")
    if request.source_type != "frequency" and request.level is not None:
        raise typer.BadParameter("--level is only valid when --source frequency")
    if request.source_type != "frequency" and test_mode:
        raise typer.BadParameter("--test-mode is only valid when --source frequency")
    if request.source_type != "frequency" and request.cards_per_level is not None:
        raise typer.BadParameter("--cards-per-level is only valid when --source frequency")
    if request.source_type not in {"word-list", "kindle-highlights"} and request.input_file is not None:
        raise typer.BadParameter("--input-file is only valid when --source word-list or highlights")
    if request.yes_overwrite and not request.overwrite:
        raise typer.BadParameter("--yes-overwrite requires --overwrite")


def _validate_regeneration_flags(
    *,
    request: GenerationRequest,
    regenerate_item_key: str | None,
) -> None:
    if regenerate_item_key is None:
        return
    if request.resume_job_id is None:
        raise typer.BadParameter("--regenerate-item-key requires --resume")
    if request.missing_only:
        raise typer.BadParameter("--missing-only cannot be combined with --regenerate-item-key")


def _confirm_overwrite(request: GenerationRequest, conflict_checker: ConflictChecker) -> None:
    if not request.overwrite:
        return

    has_conflicts = conflict_checker(request)
    if not has_conflicts:
        return

    if request.yes_overwrite:
        return

    confirmed = typer.confirm(
        "Completed items already exist for this run. Overwrite and reprocess them?",
        default=False,
    )
    if not confirmed:
        raise typer.Exit(code=1)


def _print_summary(summary: JobLifecycleSummary) -> None:
    typer.echo(f"completed_items={summary.completed_items}")
    typer.echo(f"retried_items={summary.retried_items}")
    typer.echo(f"failed_items={len(summary.failed_items)}")
    typer.echo(f"skipped_duplicates={summary.skipped_duplicates}")
    typer.echo(f"resumed_from_job={summary.resumed_from_job}")
    typer.echo(f"overwritten_items={summary.overwritten_items}")

    for failed_item in summary.failed_items:
        typer.echo(
            f"failed_item={failed_item.item_key} retry_count={failed_item.retry_count} error={failed_item.error}"
        )


def _print_generate_text_progress(progress: GenerateTextProgress) -> None:
    typer.echo(
        "stage=generate_text "
        f"processed_this_run={progress.processed_this_run} "
        f"accepted_this_run={progress.accepted_this_run} "
        f"review_this_run={progress.review_this_run} "
        f"remaining_missing={progress.remaining_missing} "
        f"last_item_key={progress.last_item_key} "
        f"elapsed_seconds={progress.elapsed_seconds:.2f}"
    )


def _print_resume_diagnostic(report: JobExecutionReport) -> None:
    diagnostic = report.orchestration.diagnostic
    if diagnostic is None:
        return

    typer.echo(diagnostic.reason)
    typer.echo(f"resume_diagnostic_details={diagnostic.details}")


def _default_review_report_path(job_id: str) -> Path:
    return Settings().report_output_dir / "reviews" / f"{job_id}.json"


def _build_review_report(
    service: GenerateJobService | IngestLexicalItemsService,
    *,
    job_id: str,
    review_report_file: Path | None,
    review_report_builder: ReviewReportBuilder | None,
) -> ReviewReport:
    if review_report_builder is not None:
        return review_report_builder(job_id=job_id, output_path=review_report_file)

    if hasattr(service, "build_review_report"):
        return service.build_review_report(
            job_id=job_id,
            output_path=review_report_file or _default_review_report_path(job_id),
        )

    text_repository = TextRepository(service.repository.session)
    return TextReviewService(text_repository=text_repository).build_review_report(
        job_id=job_id,
        output_path=review_report_file or _default_review_report_path(job_id),
    )


def _print_review_report(report: ReviewReport) -> None:
    typer.echo(f"flagged_cards={report.item_count}")
    if report.item_count > 0 and report.report_path is not None:
        typer.echo(f"review_report={report.report_path}")


def _print_webdav_error(exc: WebDAVError) -> None:
    typer.echo(f"webdav_error={exc.code.value}")
    detail = str(exc)
    if detail:
        typer.echo(f"webdav_error_detail={detail}")


def _build_cli_highlight_preview(
    input_file: Path,
    *,
    language: SupportedLanguage,
    planned_card_limit: int | None,
    korean_resolver: object | None,
    input_mode: str = "text",
) -> object:
    guarded_resolver = (
        _FailClosedKoreanPreviewResolver(korean_resolver)
        if language is SupportedLanguage.KO and korean_resolver is not None
        else None
    )
    preview = build_highlight_import_preview(
        input_file,
        language=language,
        planned_card_limit=planned_card_limit,
        korean_resolver=guarded_resolver,
        input_mode=input_mode,
    )
    if language is SupportedLanguage.KO and (
        guarded_resolver is None or guarded_resolver.failed
    ):
        raise ValueError(_KOREAN_PREVIEW_ERROR)
    return preview


def _print_korean_foundation_prepared_hashes(prepared: object) -> None:
    typer.echo(f"receipt_sha256={prepared.receipt_sha256}")
    typer.echo(f"bundle_sha256={prepared.bundle_sha256}")
    typer.echo(
        f"snapshot_manifest_sha256={prepared.snapshot_manifest_sha256}"
    )
    typer.echo(f"snapshot_root_sha256={prepared.snapshot_root_sha256}")
    typer.echo(f"active_prestate_sha256={prepared.active_prestate_sha256}")
    typer.echo(f"authorization_sha256={prepared.authorization_sha256}")


def _print_highlight_preview_counts(
    input_file: Path,
    *,
    language: SupportedLanguage,
    planned_card_limit: int | None,
    korean_resolver: object | None = None,
    input_mode: str = "text",
) -> None:
    preview = _build_cli_highlight_preview(
        input_file,
        language=language,
        planned_card_limit=planned_card_limit,
        korean_resolver=korean_resolver,
        input_mode=input_mode,
    )
    typer.echo(f"imported_highlights={preview.imported_highlights}")
    typer.echo(f"extracted_candidates={preview.extracted_candidates}")
    typer.echo(f"rejected_highlights={preview.rejected_highlights}")
    typer.echo(f"duplicate_candidates={preview.duplicate_candidates}")
    typer.echo(f"planned_cards={preview.planned_cards}")


def _prepare_lexical_data(request: GenerationRequest, *, settings: Settings) -> None:
    if request.source_type == "frequency":
        return

    lookup = LexicalLookup(data_dir=settings.lexicon_data_dir)
    if lookup.has_index(language_code=request.language.value):
        return

    index_path = lookup.index_path(language_code=request.language.value)
    typer.echo(
        "lexical data is missing for language "
        f"'{request.language.value}'. Create a lexical cache at {index_path} "
        "before running generation."
    )
    raise typer.Exit(code=1)


def _local_smoke_lexical_rows() -> dict[str, dict[str, object]]:
    rows = [
        ("harbor", "a sheltered place where boats can anchor safely", "/harbor/"),
        ("lantern", "a portable light protected by a transparent case", "/lantern/"),
        ("meadow", "a field of grass and wildflowers", "/meadow/"),
    ]
    return {
        normalize_lexical_key(term): {
            "term": term,
            "display_form": term,
            "lemma": term,
            "definitions": [definition],
            "definition_language": "en",
            "ipa": ipa,
            "source": "manual",
        }
        for term, definition, ipa in rows
    }


def _write_local_smoke_assets(output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    words_path = output_dir / "words.txt"
    words_path.write_text("\n".join(LOCAL_SMOKE_WORDS), encoding="utf-8")

    lookup = LexicalLookup(data_dir=output_dir / "lexicon")
    index_path = lookup.index_path(language_code=LOCAL_SMOKE_LANGUAGE.value)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(_local_smoke_lexical_rows(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return words_path, index_path


def create_app(
    *,
    conflict_checker: ConflictChecker = default_conflict_checker,
    generate_executor: GenerateExecutor | None = None,
    service: GenerateJobService | IngestLexicalItemsService | None = None,
    review_report_builder: ReviewReportBuilder | None = None,
    webdav_service_factory: WebDAVServiceFactory | None = None,
    latin_mvp_service: LatinMvpGenerationService | None = None,
    korean_learning_service: object | None = None,
) -> typer.Typer:
    """Build the CLI application with injectable collaborators for tests."""

    cli = typer.Typer(help="Multilang operator CLI.")
    korean_morphology: KiwiKoreanMorphologyService | None = None
    korean_preview_resolver: object | None = None

    def resolve_korean_morphology() -> KiwiKoreanMorphologyService:
        nonlocal korean_morphology
        if korean_morphology is None:
            korean_morphology = KiwiKoreanMorphologyService()
        return korean_morphology

    def resolve_korean_preview_resolver() -> object:
        nonlocal korean_preview_resolver
        injected_grounding = getattr(service, "grounding_service", None)
        if callable(
            getattr(injected_grounding, "resolve_korean_highlight_text", None)
        ):
            return injected_grounding
        if korean_preview_resolver is None:
            preview_settings = Settings()
            korean_preview_resolver = LexicalGroundingService(
                lookup=LexicalLookup(data_dir=preview_settings.lexicon_data_dir),
                korean_morphology=resolve_korean_morphology(),
            )
        return korean_preview_resolver

    def resolve_service() -> GenerateJobService | IngestLexicalItemsService | None:
        if service is not None:
            return service
        if generate_executor is not None:
            return None
        return build_runtime_service(
            korean_morphology_service=resolve_korean_morphology()
        )

    def resolve_executor(resolved_service: GenerateJobService | None) -> GenerateExecutor:
        if resolved_service is not None:
            return build_generate_executor(resolved_service)
        if generate_executor is not None:
            return generate_executor
        raise RuntimeError("unable to resolve generate executor")

    def resolve_webdav_service() -> Any:
        if webdav_service_factory is not None:
            return webdav_service_factory()
        return WebDAVHighlightFetchService.from_settings(Settings())

    def resolve_latin_mvp_service() -> LatinMvpGenerationService:
        return latin_mvp_service or LatinMvpGenerationService()

    @cli.callback()
    def main() -> None:
        """Root command group for Multilang."""

        return None

    # Resolve legacy callable seams at invocation time so existing operator
    # integrations can patch multilang.cli even after creating an application.
    # Validator adapters retain one named argument for Typer callback inspection.
    phase33.register_commands(
        cli,
        phase33.Dependencies(
            _validate_foundation_sha256=lambda value: _validate_foundation_sha256(value),
            resolve_learning_runtime=(
                (lambda: korean_learning_service) if korean_learning_service is not None
                else phase33.build_korean_learning_runtime
            ),
        ),
    )

    generation.register_commands(
        cli,
        generation.Dependencies(
            settings_factory=lambda **kwargs: Settings(**kwargs),
            _build_review_report=lambda *args, **kwargs: _build_review_report(*args, **kwargs),
            _confirm_overwrite=lambda *args, **kwargs: _confirm_overwrite(*args, **kwargs),
            _prepare_lexical_data=lambda *args, **kwargs: _prepare_lexical_data(*args, **kwargs),
            _print_generate_text_progress=lambda *args, **kwargs: _print_generate_text_progress(*args, **kwargs),
            _print_resume_diagnostic=lambda *args, **kwargs: _print_resume_diagnostic(*args, **kwargs),
            _print_review_report=lambda *args, **kwargs: _print_review_report(*args, **kwargs),
            _print_summary=lambda *args, **kwargs: _print_summary(*args, **kwargs),
            _print_webdav_error=lambda *args, **kwargs: _print_webdav_error(*args, **kwargs),
            _require_clean_anki_id_registry_for_export=lambda *args, **kwargs: _require_clean_anki_id_registry_for_export(*args, **kwargs),
            _validate_regeneration_flags=lambda *args, **kwargs: _validate_regeneration_flags(*args, **kwargs),
            _validate_request=lambda *args, **kwargs: _validate_request(*args, **kwargs),
            _write_local_smoke_assets=lambda *args, **kwargs: _write_local_smoke_assets(*args, **kwargs),
            assert_anki_id_registry_clean=lambda *args, **kwargs: assert_anki_id_registry_clean(*args, **kwargs),
            conflict_checker=conflict_checker,
            resolve_executor=resolve_executor,
            resolve_service=resolve_service,
            resolve_webdav_service=resolve_webdav_service,
            review_report_builder=review_report_builder,
            service=service,
        ),
    )

    korean_foundations.register_commands(
        cli,
        korean_foundations.Dependencies(
            _fail_korean_foundation_operation=lambda *args, **kwargs: _fail_korean_foundation_operation(*args, **kwargs),
            _foundation_receipt_sha256=lambda *args, **kwargs: _foundation_receipt_sha256(*args, **kwargs),
            _inspect_fixed_korean_foundation_exports=lambda *args, **kwargs: _inspect_fixed_korean_foundation_exports(*args, **kwargs),
            _print_korean_foundation_prepared_hashes=lambda *args, **kwargs: _print_korean_foundation_prepared_hashes(*args, **kwargs),
            _require_clean_anki_id_registry_for_export=lambda *args, **kwargs: _require_clean_anki_id_registry_for_export(*args, **kwargs),
            _validate_foundation_sha256=lambda value: _validate_foundation_sha256(value),
            activate_prepared_korean_foundation_snapshot_from_receipt=lambda *args, **kwargs: activate_prepared_korean_foundation_snapshot_from_receipt(*args, **kwargs),
            build_korean_foundation_export_bundle=lambda *args, **kwargs: build_korean_foundation_export_bundle(*args, **kwargs),
            check_korean_foundation_validation_receipt_continuity=lambda *args, **kwargs: check_korean_foundation_validation_receipt_continuity(*args, **kwargs),
            export_korean_foundation=lambda *args, **kwargs: export_korean_foundation(*args, **kwargs),
            inspect_fixed_korean_foundation_evidence_inbox=lambda *args, **kwargs: inspect_fixed_korean_foundation_evidence_inbox(*args, **kwargs),
            prepare_korean_foundation_snapshot_from_receipt=lambda *args, **kwargs: prepare_korean_foundation_snapshot_from_receipt(*args, **kwargs),
            validate_and_write_fixed_korean_foundation_validation_receipt=lambda *args, **kwargs: validate_and_write_fixed_korean_foundation_validation_receipt(*args, **kwargs),
            verify_active_korean_foundation_snapshot_provenance=lambda *args, **kwargs: verify_active_korean_foundation_snapshot_provenance(*args, **kwargs),
            verify_prepared_korean_foundation_snapshot=lambda *args, **kwargs: verify_prepared_korean_foundation_snapshot(*args, **kwargs),
        ),
    )

    korean_frequency.register_commands(
        cli,
        korean_frequency.Dependencies(
            settings_factory=lambda **kwargs: Settings(**kwargs),
            KoreanFrequencySourceRetriever=lambda *args, **kwargs: KoreanFrequencySourceRetriever(*args, **kwargs),
            _bind_korean_frequency_authority=lambda *args, **kwargs: _bind_korean_frequency_authority(*args, **kwargs),
            _build_korean_frequency_job_authority=lambda *args, **kwargs: _build_korean_frequency_job_authority(*args, **kwargs),
            _check_korean_frequency_authority=lambda *args, **kwargs: _check_korean_frequency_authority(*args, **kwargs),
            _fail_korean_checkpoint_authority_operation=lambda *args, **kwargs: _fail_korean_checkpoint_authority_operation(*args, **kwargs),
            _fail_korean_frequency_export_operation=lambda *args, **kwargs: _fail_korean_frequency_export_operation(*args, **kwargs),
            _fail_korean_frequency_source_operation=lambda *args, **kwargs: _fail_korean_frequency_source_operation(*args, **kwargs),
            _fail_korean_frequency_text_operation=lambda *args, **kwargs: _fail_korean_frequency_text_operation(*args, **kwargs),
            _fail_korean_source_review_operation=lambda *args, **kwargs: _fail_korean_source_review_operation(*args, **kwargs),
            _korean_frequency_text_result_payload=lambda *args, **kwargs: _korean_frequency_text_result_payload(*args, **kwargs),
            _print_generate_text_progress=lambda *args, **kwargs: _print_generate_text_progress(*args, **kwargs),
            _read_korean_provider_policy=lambda *args, **kwargs: _read_korean_provider_policy(*args, **kwargs),
            _require_clean_anki_id_registry_for_export=lambda *args, **kwargs: _require_clean_anki_id_registry_for_export(*args, **kwargs),
            _runtime_authority_from_cli=lambda *args, **kwargs: _runtime_authority_from_cli(*args, **kwargs),
            _sha256_file=lambda *args, **kwargs: _sha256_file(*args, **kwargs),
            _validate_foundation_sha256=lambda value: _validate_foundation_sha256(value),
            _validate_korean_frequency_authority_stage=lambda value: _validate_korean_frequency_authority_stage(value),
            _validate_optional_sha256=lambda value: _validate_optional_sha256(value),
            _verify_korean_frequency_phase31_authority=lambda *args, **kwargs: _verify_korean_frequency_phase31_authority(*args, **kwargs),
            _with_job_repository=lambda *args, **kwargs: _with_job_repository(*args, **kwargs),
            _write_json_atomic=lambda *args, **kwargs: _write_json_atomic(*args, **kwargs),
            build_korean_frequency_text_runtime_service=lambda *args, **kwargs: build_korean_frequency_text_runtime_service(*args, **kwargs),
            build_runtime_service=lambda *args, **kwargs: build_runtime_service(*args, **kwargs),
            setup_korean_frequency_live_pilot_candidates=lambda *args, **kwargs: setup_korean_frequency_live_pilot_candidates(*args, **kwargs),
            verify_active_korean_foundation_snapshot_provenance_with_approved_fallback=lambda *args, **kwargs: verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(*args, **kwargs),
        ),
    )

    korean_audio.register_commands(
        cli,
        korean_audio.Dependencies(
            settings_factory=lambda **kwargs: Settings(**kwargs),
            AzureSpeechAdapter=lambda *args, **kwargs: AzureSpeechAdapter(*args, **kwargs),
            _build_korean_audio_authority_from_cli=lambda *args, **kwargs: _build_korean_audio_authority_from_cli(*args, **kwargs),
            _build_korean_audio_pilot_authority_from_cli=lambda *args, **kwargs: _build_korean_audio_pilot_authority_from_cli(*args, **kwargs),
            _build_korean_frequency_job_authority=lambda *args, **kwargs: _build_korean_frequency_job_authority(*args, **kwargs),
            _default_azure_catalog_endpoint=lambda *args, **kwargs: _default_azure_catalog_endpoint(*args, **kwargs),
            _ensure_korean_voice_profile_outputs_distinct=lambda *args, **kwargs: _ensure_korean_voice_profile_outputs_distinct(*args, **kwargs),
            _fail_korean_frequency_text_operation=lambda *args, **kwargs: _fail_korean_frequency_text_operation(*args, **kwargs),
            _read_json_mapping=lambda *args, **kwargs: _read_json_mapping(*args, **kwargs),
            _read_korean_provider_policy=lambda *args, **kwargs: _read_korean_provider_policy(*args, **kwargs),
            _read_markdown_json_mapping=lambda *args, **kwargs: _read_markdown_json_mapping(*args, **kwargs),
            _runtime_authority_from_cli=lambda *args, **kwargs: _runtime_authority_from_cli(*args, **kwargs),
            _sha256_file=lambda *args, **kwargs: _sha256_file(*args, **kwargs),
            _validate_foundation_sha256=lambda value: _validate_foundation_sha256(value),
            _validate_optional_sha256=lambda value: _validate_optional_sha256(value),
            _with_job_repository=lambda *args, **kwargs: _with_job_repository(*args, **kwargs),
            _write_json_atomic=lambda *args, **kwargs: _write_json_atomic(*args, **kwargs),
            capture_korean_azure_catalog_pilot=lambda *args, **kwargs: capture_korean_azure_catalog_pilot(*args, **kwargs),
            create_engine=lambda *args, **kwargs: create_engine(*args, **kwargs),
            synthesize_korean_frequency_audio=lambda *args, **kwargs: synthesize_korean_frequency_audio(*args, **kwargs),
            verify_active_korean_foundation_snapshot_provenance_with_approved_fallback=lambda *args, **kwargs: verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(*args, **kwargs),
        ),
    )

    korean_evidence.register_commands(
        cli,
        korean_evidence.Dependencies(
            _build_korean_production_evidence_authority_from_cli=lambda *args, **kwargs: _build_korean_production_evidence_authority_from_cli(*args, **kwargs),
            _catalog_result_hash=lambda *args, **kwargs: _catalog_result_hash(*args, **kwargs),
            _ensure_korean_production_outputs_distinct=lambda *args, **kwargs: _ensure_korean_production_outputs_distinct(*args, **kwargs),
            _fail_korean_frequency_text_operation=lambda *args, **kwargs: _fail_korean_frequency_text_operation(*args, **kwargs),
            _fail_korean_production_evidence_operation=lambda *args, **kwargs: _fail_korean_production_evidence_operation(*args, **kwargs),
            _hash_korean_production_inputs=lambda *args, **kwargs: _hash_korean_production_inputs(*args, **kwargs),
            _list_provider_call_rows_read_only=lambda *args, **kwargs: _list_provider_call_rows_read_only(*args, **kwargs),
            _read_json_mapping=lambda *args, **kwargs: _read_json_mapping(*args, **kwargs),
            _read_korean_production_json_mapping=lambda *args, **kwargs: _read_korean_production_json_mapping(*args, **kwargs),
            _read_korean_production_required_json_inputs=lambda *args, **kwargs: _read_korean_production_required_json_inputs(*args, **kwargs),
            _sha256_file=lambda *args, **kwargs: _sha256_file(*args, **kwargs),
            _validate_foundation_sha256=lambda value: _validate_foundation_sha256(value),
            _validate_optional_sha256=lambda value: _validate_optional_sha256(value),
            _write_json_atomic=lambda *args, **kwargs: _write_json_atomic(*args, **kwargs),
            _write_korean_production_json_atomic=lambda *args, **kwargs: _write_korean_production_json_atomic(*args, **kwargs),
            _write_korean_production_text_atomic=lambda *args, **kwargs: _write_korean_production_text_atomic(*args, **kwargs),
            build_korean_production_audit_payload=lambda *args, **kwargs: build_korean_production_audit_payload(*args, **kwargs),
            load_korean_production_evidence_rows=lambda *args, **kwargs: load_korean_production_evidence_rows(*args, **kwargs),
            render_korean_production_audit_markdown=lambda *args, **kwargs: render_korean_production_audit_markdown(*args, **kwargs),
            validate_korean_production_final_evidence=lambda *args, **kwargs: validate_korean_production_final_evidence(*args, **kwargs),
            validate_korean_production_review_batches=lambda *args, **kwargs: validate_korean_production_review_batches(*args, **kwargs),
            validate_korean_production_run_result=lambda *args, **kwargs: validate_korean_production_run_result(*args, **kwargs),
            verify_active_korean_foundation_snapshot_provenance=lambda *args, **kwargs: verify_active_korean_foundation_snapshot_provenance(*args, **kwargs),
            verify_active_korean_foundation_snapshot_provenance_with_approved_fallback=lambda *args, **kwargs: verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(*args, **kwargs),
        ),
    )

    korean_release.register_commands(
        cli,
        korean_release.Dependencies(
            _fail_korean_release_safety_operation=lambda *args, **kwargs: _fail_korean_release_safety_operation(*args, **kwargs),
            _parse_korean_release_authority_values=lambda *args, **kwargs: _parse_korean_release_authority_values(*args, **kwargs),
            _read_korean_production_json_mapping=lambda *args, **kwargs: _read_korean_production_json_mapping(*args, **kwargs),
            _validate_foundation_sha256=lambda value: _validate_foundation_sha256(value),
            _validate_optional_sha256=lambda value: _validate_optional_sha256(value),
            _write_korean_production_json_atomic=lambda *args, **kwargs: _write_korean_production_json_atomic(*args, **kwargs),
            execute_korean_release_delivery=lambda *args, **kwargs: execute_korean_release_delivery(*args, **kwargs),
            validate_korean_release_delivery=lambda *args, **kwargs: validate_korean_release_delivery(*args, **kwargs),
        ),
    )

    personal_sources.register_commands(
        cli,
        personal_sources.Dependencies(
            _build_cli_highlight_preview=lambda *args, **kwargs: _build_cli_highlight_preview(*args, **kwargs),
            _print_highlight_preview_counts=lambda *args, **kwargs: _print_highlight_preview_counts(*args, **kwargs),
            _print_webdav_error=lambda *args, **kwargs: _print_webdav_error(*args, **kwargs),
            resolve_korean_preview_resolver=resolve_korean_preview_resolver,
            resolve_webdav_service=resolve_webdav_service,
        ),
    )

    latin.register_commands(
        cli,
        latin.Dependencies(
            _require_clean_anki_id_registry_for_export=lambda *args, **kwargs: _require_clean_anki_id_registry_for_export(*args, **kwargs),
            export_latin_mvp_bundle=lambda *args, **kwargs: export_latin_mvp_bundle(*args, **kwargs),
            resolve_latin_mvp_service=resolve_latin_mvp_service,
        ),
    )

    phonetics.register_commands(
        cli,
        phonetics.Dependencies(
            settings_factory=lambda **kwargs: Settings(**kwargs),
            _require_clean_anki_id_registry_for_export=lambda *args, **kwargs: _require_clean_anki_id_registry_for_export(*args, **kwargs),
        ),
    )

    from multilang.native_cli import create_native_app
    cli.add_typer(create_native_app(), name="native")
    return cli


app = create_app()


if __name__ == "__main__":
    app()
