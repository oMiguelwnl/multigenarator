"""Typer CLI for Multilang job orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Annotated, Any

import typer
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from multilang.db.models import GenerationJob
from multilang.db.provisioning import ensure_database_schema
from multilang.domain.audio import AudioAssetRecord
from multilang.domain.korean import KoreanFrequencyJobAuthority
from multilang.domain.jobs import (
    GenerationRequest,
    JobProgressSnapshot,
    JobStage,
    JobStatus,
    SupportedLanguage,
)
from multilang.domain.latin import LatinGenerationRequest
from multilang.domain.exporting import ExportArtifactFormat
from multilang.domain.deck_audit import audit_deck_package
from multilang.domain.webdav import WebDAVError, WebDAVFailureCode, WebDAVFetchResult, WebDAVRemoteCandidate
from multilang.progress import ProgressRenderer
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
from multilang.repositories.text_repository import TextRepository
from multilang.runtime import (
    KoreanFrequencyTextRuntimeAuthority,
    build_korean_frequency_text_runtime_service,
    build_runtime_service,
)
from multilang.repositories.job_repository import JobRepository
from multilang.services.execution_report import JobExecutionReport
from multilang.services.generate_job import GenerateJobResult, GenerateJobService
from multilang.services.generate_text_items import GenerateTextProgress
from multilang.services.highlight_import_preview import build_highlight_import_preview
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.rate_limit import SimpleRateLimiter
from multilang.services.deck_audit_reader import read_apkg_cards
from multilang.services.deck_audit_reports import write_deck_audit_reports
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.lexical_lookup import LexicalLookup, normalize_lexical_key
from multilang.services.job_summary import JobLifecycleSummary, JobSummaryBuilder
from multilang.services.latin_mvp import LatinMvpGenerationService
from multilang.services.latin_export import LATIN_DECK_NAME, export_latin_mvp_bundle
from multilang.services.latin_review import (
    DEFAULT_LATIN_MVP_CURATION_PATH,
    load_latin_curated_records,
    summarize_latin_review_records,
    update_latin_review_gate,
    write_latin_curated_records,
)
from multilang.services.russian_phoneme_deck import (
    DEFAULT_GREEK_PHONEME_DECK_NAME,
    DEFAULT_POLISH_PHONEME_DECK_NAME,
    DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
    GREEK_PHONEME_CARDS,
    POLISH_PHONEME_CARDS,
    RUSSIAN_PHONEME_CARDS,
    export_greek_phoneme_deck,
    export_polish_phoneme_deck,
    export_russian_phoneme_deck,
)
from multilang.services.japanese_frequency_deck import (
    DEFAULT_JAPANESE_DECK_NAME,
    JAPANESE_FREQUENCY_CARDS,
    export_japanese_frequency_deck,
)
from multilang.services.japanese_kana_deck import (
    DEFAULT_KANA_DECK_NAME,
    export_kana_deck,
)
from multilang.services.japanese_kana_generated_deck import export_generated_kana_deck
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
from multilang.services.korean_checkpoint_authority import validate_korean_checkpoint_authority
from multilang.services.korean_frequency import (
    KoreanFrequencySourceRetriever,
    validate_korean_source_build_result,
    validate_korean_source_retrieval_result,
)
from multilang.services.korean_audio import (
    KoreanAudioAuthority,
    synthesize_korean_frequency_audio,
)
from multilang.services.korean_audio_pilot_evidence import (
    KoreanAudioPilotAuthority,
    validate_korean_audio_pilot_result,
)
from multilang.services.korean_provider_pilot_evidence import (
    KoreanProviderCatalogPilotAuthority,
    validate_korean_provider_catalog_pilot_result,
)
from multilang.services.korean_production_evidence import (
    KoreanProductionEvidenceAuthority,
    build_korean_production_audit_payload,
    validate_korean_production_review_batches,
    load_korean_production_evidence_rows,
    render_korean_production_audit_markdown,
    validate_korean_production_final_evidence,
    validate_korean_production_run_result,
)
from multilang.services.korean_release_safety import (
    KoreanReleaseBuildResult,
    KoreanReleaseAuthorization,
    KoreanReleaseSafetyReport,
    build_korean_release_safety,
    promote_korean_release_bundle,
    validate_korean_release_authorization,
)
from multilang.services.korean_release_delivery import (
    KoreanReleaseDeliveryActionResult,
    execute_korean_release_delivery,
    validate_korean_release_delivery,
)
from multilang.services.korean_audio_review import (
    KoreanAudioReviewAggregate,
    KoreanAudioReviewApplicationAuthority,
    KoreanAudioReviewApplicationService,
    KoreanAudioReviewBatch,
    KoreanAudioReviewImportLedger,
)
from multilang.services.korean_source_review import (
    import_korean_bundle_review_batch,
    validate_korean_bundle_review_batches,
)
from multilang.services.korean_text_review import (
    KoreanTextReviewAggregate,
    KoreanTextReviewApplicationAuthority,
    KoreanTextReviewApplicationService,
    KoreanTextReviewBatch,
    KoreanTextReviewImportLedger,
)
from multilang.services.text_review import ReviewReport, TextReviewService
from multilang.services.webdav_highlight_fetch import WebDAVHighlightFetchService
from multilang.services.anki_id_registry import assert_anki_id_registry_clean
from multilang.settings import Settings

app = typer.Typer(help="Multilang operator CLI.")

TEST_MODE_CARDS_PER_LEVEL = 3
LOCAL_SMOKE_LANGUAGE = SupportedLanguage.EN
LOCAL_SMOKE_FIXTURE_DIR = Path(".multilang/live-smoke-azure")
LOCAL_SMOKE_WORDS = ("harbor", "lantern", "meadow")
_KOREAN_FOUNDATION_EXPORT_ROOT = Path(".multilang/exports/korean-foundations")

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
    report = verify_active_korean_foundation_snapshot_provenance(
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
    return Path(".multilang") / "review-reports" / f"{job_id}.json"


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
) -> None:
    preview = _build_cli_highlight_preview(
        input_file,
        language=language,
        planned_card_limit=planned_card_limit,
        korean_resolver=korean_resolver,
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
) -> typer.Typer:
    """Build the CLI application with injectable collaborators for tests."""

    cli = typer.Typer(help="Multilang operator CLI.")
    korean_foundations = typer.Typer(
        help="Operate the fixed Korean foundation evidence and export workflow."
    )
    cli.add_typer(korean_foundations, name="korean-foundations")
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

    @cli.command("check-anki-id-registry")
    def check_anki_id_registry(
        production_roots: Annotated[
            bool,
            typer.Option("--production-roots", help="Scan production roots for non-registry Anki IDs."),
        ] = False,
    ) -> None:
        if not production_roots:
            typer.echo("check_anki_id_registry_error=production_roots_required")
            raise typer.Exit(code=1)
        try:
            result = assert_anki_id_registry_clean(production_roots=True)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo("anki_id_registry_status=clean")
        typer.echo(f"scanned_files={result.scanned_files}")
        typer.echo(f"issue_count={len(result.issues)}")

    @korean_foundations.command("inspect-inbox")
    def inspect_korean_foundation_inbox() -> None:
        try:
            inventory = inspect_fixed_korean_foundation_evidence_inbox()
            if not inventory.complete:
                typer.echo("korean_foundations_error=inbox_incomplete")
                raise typer.Exit(code=1)
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        typer.echo("inbox_status=complete_unvalidated")
        typer.echo(f"evidence_index_sha256={inventory.index_sha256}")
        typer.echo(f"declared_member_count={inventory.evidence_member_count}")

    @korean_foundations.command("validate-and-write-receipt")
    def validate_and_write_korean_foundation_receipt(
        confirmed_index_sha256: Annotated[
            str,
            typer.Option(
                "--confirmed-index-sha256",
                callback=_validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            receipt = validate_and_write_fixed_korean_foundation_validation_receipt(
                confirmed_index_sha256=confirmed_index_sha256
            )
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        status = getattr(receipt, "_receipt_write_status", "written")
        typer.echo(f"receipt_write_status={status}")
        typer.echo(f"receipt_sha256={_foundation_receipt_sha256(receipt)}")
        typer.echo(f"bundle_sha256={receipt.evidence_bundle_sha256}")

    @korean_foundations.command("check-receipt")
    def check_korean_foundation_receipt(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=_validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            report = check_korean_foundation_validation_receipt_continuity(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        typer.echo("receipt_status=continuous")
        typer.echo(f"receipt_sha256={report.receipt_sha256}")
        typer.echo(f"bundle_sha256={report.evidence_bundle_sha256}")

    @korean_foundations.command("prepare-snapshot")
    def prepare_korean_foundation_snapshot(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=_validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            prepared = prepare_korean_foundation_snapshot_from_receipt(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        _print_korean_foundation_prepared_hashes(prepared)
        typer.echo("snapshot_status=prepared_inactive")

    @korean_foundations.command("verify-prepared")
    def verify_prepared_korean_foundation(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=_validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            prepared = verify_prepared_korean_foundation_snapshot(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        _print_korean_foundation_prepared_hashes(prepared)
        typer.echo("prepared_status=verified")

    @korean_foundations.command("activate")
    def activate_korean_foundation_snapshot(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=_validate_foundation_sha256,
            ),
        ],
        authorization_sha256: Annotated[
            str,
            typer.Option(
                "--authorization-sha256",
                callback=_validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            result = activate_prepared_korean_foundation_snapshot_from_receipt(
                expected_receipt_sha256=expected_receipt_sha256,
                authorization_sha256=authorization_sha256,
            )
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        status = "already_active" if result.already_active else "activated"
        typer.echo(f"activation_status={status}")
        typer.echo(f"receipt_sha256={result.receipt_sha256}")
        typer.echo(f"bundle_sha256={result.bundle_sha256}")

    @korean_foundations.command("verify-active")
    def verify_active_korean_foundation(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=_validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            report = verify_active_korean_foundation_snapshot_provenance(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        typer.echo("active_status=verified")
        typer.echo(f"receipt_sha256={report.receipt_sha256}")
        typer.echo(f"bundle_sha256={report.bundle_sha256}")
        typer.echo(f"snapshot_root_sha256={report.snapshot_root_sha256}")

    @korean_foundations.command("check")
    def check_korean_foundation(
        family: Annotated[
            KoreanFoundationFamily,
            typer.Option("--family"),
        ],
    ) -> None:
        try:
            bundle = build_korean_foundation_export_bundle(family=family)
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        typer.echo(f"family={family.value}")
        typer.echo("readiness_status=ready")
        typer.echo(f"card_count={len(bundle.rows)}")
        typer.echo(f"media_count={len(bundle.media)}")

    @korean_foundations.command("export")
    def export_korean_foundation_command(
        family: Annotated[
            KoreanFoundationFamily,
            typer.Option("--family"),
        ],
        format: Annotated[
            ExportArtifactFormat,
            typer.Option("--format"),
        ],
        output: Annotated[
            Path,
            typer.Option("--output", exists=False),
        ],
    ) -> None:
        try:
            _require_clean_anki_id_registry_for_export()
            result = export_korean_foundation(
                family=family,
                export_format=format,
                output_destination=output,
            )
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        typer.echo(f"family={family.value}")
        typer.echo(f"format={format.value}")
        typer.echo("export_status=written")
        typer.echo(f"card_count={result.card_count}")
        typer.echo(f"media_count={result.media_count}")

    @korean_foundations.command("inspect-exports")
    def inspect_korean_foundation_exports() -> None:
        try:
            report = _inspect_fixed_korean_foundation_exports()
        except ValueError as exc:
            _fail_korean_foundation_operation(exc)
        typer.echo("export_set_status=verified")
        typer.echo(f"artifact_count={report.artifact_count}")
        typer.echo(f"receipt_sha256={report.receipt_sha256}")
        typer.echo(f"bundle_sha256={report.bundle_sha256}")
        typer.echo(f"snapshot_root_sha256={report.snapshot_root_sha256}")

    @cli.command("prepare-local-smoke")
    def prepare_local_smoke(
        output_dir: Annotated[
            Path,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                writable=True,
                help="Directory where the local English smoke assets will be written.",
            ),
        ] = LOCAL_SMOKE_FIXTURE_DIR,
    ) -> None:
        words_path, index_path = _write_local_smoke_assets(output_dir)
        typer.echo(f"words={words_path}")
        typer.echo(f"index={index_path}")
        typer.echo(
            "smoke_command="
            f"MULTILANG_DATABASE_URL=sqlite+pysqlite:///{output_dir / 'smoke.db'} "
            f"MULTILANG_LEXICON_DATA_DIR={output_dir / 'lexicon'} "
            f"MULTILANG_AUDIO_STORAGE_DIR={output_dir / 'audio'} "
            "uv run python -m multilang.cli generate --language en --source word-list "
            f"--input-file {words_path}"
        )

    @cli.command("retrieve-korean-frequency-source")
    def retrieve_korean_frequency_source(
        output_dir: Annotated[
            Path,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                writable=True,
                help="Directory for the quarantined Korean frequency source and retrieval result.",
            ),
        ],
    ) -> None:
        try:
            result, result_path = KoreanFrequencySourceRetriever().retrieve_to_directory(output_dir)
        except ValueError as exc:
            _fail_korean_frequency_source_operation(exc)
        typer.echo("retrieval_status=validated")
        typer.echo(f"source_id={result.source_id}")
        typer.echo(f"accepted_filename={result.accepted_filename}")
        typer.echo(f"source_bytes_sha256={result.source_bytes_sha256}")
        typer.echo(f"source_byte_count={result.source_byte_count}")
        typer.echo(f"retrieval_result={result_path}")

    @cli.command("validate-korean-source-retrieval-result")
    def validate_korean_source_retrieval_result_command(
        result_file: Annotated[
            Path,
            typer.Option("--result-file", exists=True, dir_okay=False, readable=True),
        ],
        source_file: Annotated[
            Path | None,
            typer.Option("--source-file", exists=True, dir_okay=False, readable=True),
        ] = None,
    ) -> None:
        try:
            result = validate_korean_source_retrieval_result(result_file, source_file=source_file)
        except ValueError as exc:
            _fail_korean_frequency_source_operation(exc)
        typer.echo("retrieval_result_status=valid")
        typer.echo(f"source_id={result.source_id}")
        typer.echo(f"accepted_filename={result.accepted_filename}")
        typer.echo(f"source_byte_count={result.source_byte_count}")

    @cli.command("validate-korean-source-build-result")
    def validate_korean_source_build_result_command(
        result_file: Annotated[
            Path,
            typer.Option("--result-file", exists=False, dir_okay=False, readable=True),
        ],
        bundle_dir: Annotated[
            Path | None,
            typer.Option("--bundle-dir", exists=False, file_okay=False, readable=True),
        ] = None,
    ) -> None:
        try:
            result = validate_korean_source_build_result(
                result_file,
                bundle_dir=bundle_dir,
            )
        except ValueError as exc:
            _fail_korean_frequency_source_operation(exc)
        typer.echo("build_result_status=valid")
        typer.echo(f"accepted_count={result.accepted_count}")
        typer.echo(f"rejection_count={result.rejection_count}")
        typer.echo(f"bundle_sha256={result.bundle_sha256}")

    @cli.command("import-korean-bundle-review-batch")
    def import_korean_bundle_review_batch_command(
        batch_file: Annotated[
            Path,
            typer.Option("--batch-file", exists=False, dir_okay=False, readable=True),
        ],
        build_result_file: Annotated[
            Path,
            typer.Option("--build-result-file", exists=False, dir_okay=False, readable=True),
        ],
        bundle_dir: Annotated[
            Path,
            typer.Option("--bundle-dir", exists=False, file_okay=False, readable=True),
        ],
        receipt_dir: Annotated[
            Path,
            typer.Option("--receipt-dir", exists=False, file_okay=False, writable=True),
        ],
    ) -> None:
        try:
            receipt = import_korean_bundle_review_batch(
                batch_file,
                build_result_file=build_result_file,
                bundle_dir=bundle_dir,
                receipt_dir=receipt_dir,
            )
        except ValueError as exc:
            _fail_korean_source_review_operation(exc)
        typer.echo("review_batch_status=imported")
        typer.echo(f"batch_id={receipt.batch_id}")
        typer.echo(f"decision_count={receipt.decision_count}")
        typer.echo(f"accepted_count={receipt.accepted_count}")
        typer.echo(f"rejected_count={receipt.rejected_count}")
        typer.echo(f"receipt_sha256={receipt.receipt_sha256}")

    @cli.command("validate-korean-bundle-review-batches")
    def validate_korean_bundle_review_batches_command(
        receipt_dir: Annotated[
            Path,
            typer.Option("--receipt-dir", exists=False, file_okay=False, readable=True),
        ],
        build_result_file: Annotated[
            Path,
            typer.Option("--build-result-file", exists=False, dir_okay=False, readable=True),
        ],
        bundle_dir: Annotated[
            Path,
            typer.Option("--bundle-dir", exists=False, file_okay=False, readable=True),
        ],
    ) -> None:
        try:
            aggregate = validate_korean_bundle_review_batches(
                receipt_dir,
                build_result_file=build_result_file,
                bundle_dir=bundle_dir,
            )
        except ValueError as exc:
            _fail_korean_source_review_operation(exc)
        typer.echo(f"review_batches_status={aggregate.status}")
        typer.echo(f"total_dispositions={aggregate.total_dispositions}")
        typer.echo(f"accepted_count={aggregate.accepted_count}")
        typer.echo(f"rejected_count={aggregate.rejected_count}")
        typer.echo(f"receipt_count={aggregate.receipt_count}")
        typer.echo(f"aggregate_sha256={aggregate.aggregate_sha256}")

    @cli.command("validate-korean-checkpoint-authority")
    def validate_korean_checkpoint_authority_command(
        authority_file: Annotated[
            Path,
            typer.Option("--authority-file", exists=True, dir_okay=False, readable=True),
        ],
        expected_kind: Annotated[
            str,
            typer.Option("--expected-kind", help="Expected fixed authority kind."),
        ],
    ) -> None:
        try:
            result = validate_korean_checkpoint_authority(authority_file, expected_kind=expected_kind)
        except ValueError as exc:
            _fail_korean_checkpoint_authority_operation(exc)
        typer.echo("authority_status=valid")
        typer.echo(f"authority_kind={result.kind}")
        typer.echo(f"power_count={len(result.powers)}")
        typer.echo(f"binding_count={result.binding_count}")
        typer.echo(f"authority_sha256={result.authority_sha256}")

    @cli.command("prepare-korean-frequency-job")
    def prepare_korean_frequency_job(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256),
        ],
    ) -> None:
        try:
            authority = _build_korean_frequency_job_authority(
                stage="pilot_base",
                phase31_active_pointer_sha256=phase31_active_pointer_sha256,
                phase31_active_pointer_content_sha256=phase31_active_pointer_content_sha256,
                phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
                phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
                phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
                frequency_bundle_manifest_sha256=frequency_bundle_manifest_sha256,
                frequency_bundle_content_sha256=frequency_bundle_content_sha256,
                source_retrieval_sha256=source_retrieval_sha256,
                source_build_result_sha256=source_build_result_sha256,
                source_review_aggregate_sha256=source_review_aggregate_sha256,
                provider_policy_sha256=provider_policy_sha256,
                pilot_authority_sha256=pilot_authority_sha256,
            )
            _runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            _verify_korean_frequency_phase31_authority(authority)
            bound = _bind_korean_frequency_authority(
                database_url=database_url,
                job_id=job_id,
                authority=authority,
            )
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_frequency_job_status=prepared")
        typer.echo(f"job_id={job_id}")
        typer.echo(f"authority_stage={bound.stage}")
        typer.echo(f"binding_receipt_sha256={binding_receipt_sha256}")

    @cli.command("bind-korean-frequency-audio-authority")
    def bind_korean_frequency_audio_authority(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256),
        ],
        catalog_locator_sha256: Annotated[
            str,
            typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256),
        ],
        catalog_content_sha256: Annotated[
            str,
            typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256),
        ],
        profile_sample_authority_sha256: Annotated[
            str,
            typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256),
        ],
        provider_review_authority_sha256: Annotated[
            str,
            typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256),
        ],
        heard_review_authority_sha256: Annotated[
            str,
            typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256),
        ],
    ) -> None:
        try:
            authority = _build_korean_frequency_job_authority(
                stage="full",
                phase31_active_pointer_sha256=phase31_active_pointer_sha256,
                phase31_active_pointer_content_sha256=phase31_active_pointer_content_sha256,
                phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
                phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
                phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
                frequency_bundle_manifest_sha256=frequency_bundle_manifest_sha256,
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
            _runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            _verify_korean_frequency_phase31_authority(authority)
            bound = _bind_korean_frequency_authority(
                database_url=database_url,
                job_id=job_id,
                authority=authority,
            )
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_frequency_audio_authority_status=bound")
        typer.echo(f"job_id={job_id}")
        typer.echo(f"authority_stage={bound.stage}")
        typer.echo(f"binding_receipt_sha256={binding_receipt_sha256}")

    @cli.command("check-korean-frequency-job-binding")
    def check_korean_frequency_job_binding(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256),
        ],
        catalog_locator_sha256: Annotated[
            str,
            typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256),
        ],
        catalog_content_sha256: Annotated[
            str,
            typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256),
        ],
        profile_sample_authority_sha256: Annotated[
            str,
            typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256),
        ],
        provider_review_authority_sha256: Annotated[
            str,
            typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256),
        ],
        heard_review_authority_sha256: Annotated[
            str,
            typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256),
        ],
    ) -> None:
        try:
            authority = _build_korean_frequency_job_authority(
                stage="full",
                phase31_active_pointer_sha256=phase31_active_pointer_sha256,
                phase31_active_pointer_content_sha256=phase31_active_pointer_content_sha256,
                phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
                phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
                phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
                frequency_bundle_manifest_sha256=frequency_bundle_manifest_sha256,
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
            _runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            _verify_korean_frequency_phase31_authority(authority)
            bound = _check_korean_frequency_authority(
                database_url=database_url,
                job_id=job_id,
                authority=authority,
            )
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_frequency_job_binding_status=verified")
        typer.echo(f"job_id={job_id}")
        typer.echo(f"authority_stage={bound.stage}")
        typer.echo(f"binding_receipt_sha256={binding_receipt_sha256}")

    @cli.command("generate-korean-frequency-text")
    def generate_korean_frequency_text(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256),
        ],
        catalog_locator_sha256: Annotated[
            str,
            typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256),
        ],
        catalog_content_sha256: Annotated[
            str,
            typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256),
        ],
        profile_sample_authority_sha256: Annotated[
            str,
            typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256),
        ],
        provider_review_authority_sha256: Annotated[
            str,
            typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256),
        ],
        heard_review_authority_sha256: Annotated[
            str,
            typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256),
        ],
        max_items: Annotated[
            int | None,
            typer.Option("--max-items", min=1),
        ] = None,
        missing_only: Annotated[
            bool,
            typer.Option("--missing-only"),
        ] = False,
        synthesize_audio: Annotated[
            bool,
            typer.Option("--synthesize-audio/--no-synthesize-audio"),
        ] = True,
    ) -> None:
        try:
            authority = _build_korean_frequency_job_authority(
                stage="full",
                phase31_active_pointer_sha256=phase31_active_pointer_sha256,
                phase31_active_pointer_content_sha256=phase31_active_pointer_content_sha256,
                phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
                phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
                phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
                frequency_bundle_manifest_sha256=frequency_bundle_manifest_sha256,
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
            runtime_authority = _runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            runtime_service = build_korean_frequency_text_runtime_service(
                settings=Settings(_env_file=None, database_url=database_url),
                runtime_authority=runtime_authority,
            )
            text_result = runtime_service.generate_text(
                job_id=job_id,
                deck_language=SupportedLanguage.KO,
                missing_only=missing_only,
                max_items=max_items,
                progress_callback=_print_generate_text_progress,
                synthesize_audio=synthesize_audio,
            )
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_frequency_text_status=generated")
        typer.echo(f"text_processed_items={text_result.processed_items}")
        typer.echo(f"accepted_text_items={text_result.accepted_items}")
        typer.echo(f"review_required_text_items={text_result.review_required_items}")
        typer.echo(f"audio_processed_items={text_result.audio_processed_items}")
        typer.echo(f"audio_reused_items={text_result.audio_reused_items}")
        typer.echo(f"fallback_audio_items={text_result.fallback_audio_items}")
        typer.echo(f"failed_audio_items={text_result.failed_audio_items}")

    @cli.command("import-korean-production-text-review-batch")
    def import_korean_production_text_review_batch_command(
        batch_file: Annotated[
            Path,
            typer.Option("--batch-file", exists=True, dir_okay=False, readable=True),
        ],
        receipt_file: Annotated[
            Path,
            typer.Option("--receipt-file", exists=False, dir_okay=False, writable=True),
        ],
    ) -> None:
        try:
            batch = KoreanTextReviewBatch.model_validate_json(batch_file.read_text(encoding="utf-8"))
            result = KoreanTextReviewImportLedger().import_batch(batch)
            receipt_file.parent.mkdir(parents=True, exist_ok=True)
            receipt_file.write_text(
                json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_text_review_batch_status=imported")
        typer.echo(f"receipt_sha256={result.receipt_sha256}")
        typer.echo(f"decision_count={result.decision_count}")

    @cli.command("apply-korean-frequency-text-review")
    def apply_korean_frequency_text_review_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        aggregate_file: Annotated[
            Path,
            typer.Option("--aggregate-file", exists=True, dir_okay=False, readable=True),
        ],
        authority_file: Annotated[
            Path,
            typer.Option("--authority-file", exists=True, dir_okay=False, readable=True),
        ],
        mode: Annotated[str, typer.Option("--mode")],
    ) -> None:
        try:
            aggregate = KoreanTextReviewAggregate.model_validate_json(aggregate_file.read_text(encoding="utf-8"))
            authority = KoreanTextReviewApplicationAuthority.model_validate_json(authority_file.read_text(encoding="utf-8"))
            if aggregate.job_id != job_id or authority.mode != mode:
                raise ValueError("Korean text-review authority drift")

            def action(_: JobRepository) -> object:
                session = _.session
                return KoreanTextReviewApplicationService(TextRepository(session)).apply(aggregate, authority)

            result = _with_job_repository(database_url, action)
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_text_review_application_status=applied")
        typer.echo(f"mode={result.mode}")
        typer.echo(f"mutated_count={result.mutated_count}")

    @cli.command("capture-korean-azure-catalog")
    def capture_korean_azure_catalog_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256)],
        binding_receipt_sha256: Annotated[str, typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256)],
        endpoint_url: Annotated[str, typer.Option("--endpoint-url")],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=False, dir_okay=False)],
    ) -> None:
        try:
            _build_korean_audio_authority_from_cli(
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
            if not database_url or not endpoint_url or catalog_result_file.is_dir():
                raise ValueError("Korean Azure catalog authority drift")
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_azure_catalog_status=ready_for_authorized_capture")
        typer.echo(f"job_id={job_id}")
        typer.echo(f"catalog_result_file={catalog_result_file}")

    @cli.command("validate-korean-provider-catalog-pilot-result")
    def validate_korean_provider_catalog_pilot_result_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256)],
        binding_receipt_sha256: Annotated[str, typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256)],
        final_authority_sha256: Annotated[str, typer.Option("--final-authority-sha256", callback=_validate_foundation_sha256)],
        binding_receipt_file: Annotated[Path, typer.Option("--binding-receipt-file", exists=True, dir_okay=False, readable=True)],
        frequency_bundle_manifest_file: Annotated[Path, typer.Option("--frequency-bundle-manifest-file", exists=True, dir_okay=False, readable=True)],
        source_retrieval_authority_file: Annotated[Path, typer.Option("--source-retrieval-authority-file", exists=True, dir_okay=False, readable=True)],
        source_build_authority_file: Annotated[Path, typer.Option("--source-build-authority-file", exists=True, dir_okay=False, readable=True)],
        source_review_aggregate_file: Annotated[Path, typer.Option("--source-review-aggregate-file", exists=True, dir_okay=False, readable=True)],
        final_authority_file: Annotated[Path, typer.Option("--final-authority-file", exists=True, dir_okay=False, readable=True)],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=True, dir_okay=False, readable=True)],
        pilot_authority_file: Annotated[Path, typer.Option("--pilot-authority-file", exists=True, dir_okay=False, readable=True)],
        text_result_file: Annotated[Path, typer.Option("--text-result-file", exists=True, dir_okay=False, readable=True)],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=True, dir_okay=False, readable=True)],
        expected_item_count: Annotated[int, typer.Option("--expected-item-count", min=1)],
        evidence_file: Annotated[Path, typer.Option("--evidence-file", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            if frequency_bundle_root.is_file() or not profile_sample_authority_sha256:
                raise ValueError("Korean provider/catalog pilot bundle authority drift")
            if not provider_review_authority_sha256 or not heard_review_authority_sha256:
                raise ValueError("Korean provider/catalog pilot review authority drift")
            protected_inputs = {
                "binding_receipt": binding_receipt_file,
                "frequency_bundle_manifest": frequency_bundle_manifest_file,
                "source_retrieval_authority": source_retrieval_authority_file,
                "source_build_authority": source_build_authority_file,
                "source_review_aggregate": source_review_aggregate_file,
                "final_authority": final_authority_file,
                "provider_policy": provider_policy_file,
                "pilot_authority": pilot_authority_file,
                "text_result": text_result_file,
                "catalog_result": catalog_result_file,
            }
            if evidence_file.resolve() in {path.resolve() for path in protected_inputs.values()}:
                raise ValueError("Korean provider/catalog pilot evidence output must be distinct from inputs")
            before_hashes = {label: _sha256_file(path) for label, path in protected_inputs.items()}
            authority = KoreanProviderCatalogPilotAuthority(
                job_id=job_id,
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
                binding_receipt_sha256=binding_receipt_sha256,
                catalog_locator_sha256=catalog_locator_sha256,
                catalog_content_sha256=catalog_content_sha256,
                final_authority_sha256=final_authority_sha256,
            )
            text_result = _read_json_mapping(text_result_file)
            catalog_result = _read_json_mapping(catalog_result_file)
            provider_call_rows = _list_provider_call_rows_read_only(database_url=database_url, job_id=job_id)
            after_hashes = {label: _sha256_file(path) for label, path in protected_inputs.items()}
            evidence = validate_korean_provider_catalog_pilot_result(
                authority=authority,
                provider_call_records=provider_call_rows,
                text_result=text_result,
                catalog_result=catalog_result,
                expected_item_count=expected_item_count,
                protected_hashes={label: (before_hashes[label], after_hashes[label]) for label in protected_inputs},
                phase31_verifier=verify_active_korean_foundation_snapshot_provenance,
            )
            _write_korean_production_json_atomic(evidence_file, evidence.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_provider_catalog_pilot_evidence_status=validated")
        typer.echo(f"evidence_sha256={evidence.evidence_sha256}")
        typer.echo(f"provider_call_count={evidence.provider_call_count}")
        typer.echo(f"synthesis_attempt_count={evidence.synthesis_attempt_count}")

    @cli.command("validate-korean-production-run-result")
    def validate_korean_production_run_result_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256)],
        source_access_authority_sha256: Annotated[str, typer.Option("--source-access-authority-sha256", callback=_validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256)],
        source_transformation_sha256: Annotated[str, typer.Option("--source-transformation-sha256", callback=_validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        final_bundle_authority_sha256: Annotated[str, typer.Option("--final-bundle-authority-sha256", callback=_validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256)],
        budget_authority_sha256: Annotated[str, typer.Option("--budget-authority-sha256", callback=_validate_foundation_sha256)],
        retry_policy_sha256: Annotated[str, typer.Option("--retry-policy-sha256", callback=_validate_foundation_sha256)],
        full_run_authority_sha256: Annotated[str, typer.Option("--full-run-authority-sha256", callback=_validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256)],
        full_binding_receipt_sha256: Annotated[str, typer.Option("--full-binding-receipt-sha256", callback=_validate_foundation_sha256)],
        binding_receipt_file: Annotated[Path, typer.Option("--binding-receipt-file", exists=True, dir_okay=False, readable=True)],
        frequency_bundle_manifest_file: Annotated[Path, typer.Option("--frequency-bundle-manifest-file", exists=True, dir_okay=False, readable=True)],
        source_access_authority_file: Annotated[Path, typer.Option("--source-access-authority-file", exists=True, dir_okay=False, readable=True)],
        source_retrieval_authority_file: Annotated[Path, typer.Option("--source-retrieval-authority-file", exists=True, dir_okay=False, readable=True)],
        source_transformation_authority_file: Annotated[Path, typer.Option("--source-transformation-authority-file", exists=True, dir_okay=False, readable=True)],
        source_build_authority_file: Annotated[Path, typer.Option("--source-build-authority-file", exists=True, dir_okay=False, readable=True)],
        source_review_aggregate_file: Annotated[Path, typer.Option("--source-review-aggregate-file", exists=True, dir_okay=False, readable=True)],
        final_bundle_authority_file: Annotated[Path, typer.Option("--final-bundle-authority-file", exists=True, dir_okay=False, readable=True)],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=True, dir_okay=False, readable=True)],
        provider_review_authority_file: Annotated[Path, typer.Option("--provider-review-authority-file", exists=True, dir_okay=False, readable=True)],
        budget_authority_file: Annotated[Path, typer.Option("--budget-authority-file", exists=True, dir_okay=False, readable=True)],
        retry_policy_file: Annotated[Path, typer.Option("--retry-policy-file", exists=True, dir_okay=False, readable=True)],
        full_run_authority_file: Annotated[Path, typer.Option("--full-run-authority-file", exists=True, dir_okay=False, readable=True)],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=True, dir_okay=False, readable=True)],
        voice_profile_file: Annotated[Path, typer.Option("--voice-profile-file", exists=True, dir_okay=False, readable=True)],
        heard_review_authority_file: Annotated[Path, typer.Option("--heard-review-authority-file", exists=True, dir_okay=False, readable=True)],
        full_binding_receipt_file: Annotated[Path, typer.Option("--full-binding-receipt-file", exists=True, dir_okay=False, readable=True)],
        text_result_file: Annotated[Path, typer.Option("--text-result-file", exists=True, dir_okay=False, readable=True)],
        audio_result_file: Annotated[Path, typer.Option("--audio-result-file", exists=True, dir_okay=False, readable=True)],
        expected_item_count: Annotated[int, typer.Option("--expected-item-count", min=1)],
        evidence_file: Annotated[Path, typer.Option("--evidence-file", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            if frequency_bundle_root.is_file():
                raise ValueError("Korean production evidence bundle authority drift")
            protected_inputs = {
                "binding_receipt": binding_receipt_file,
                "frequency_bundle_manifest": frequency_bundle_manifest_file,
                "source_access_authority": source_access_authority_file,
                "source_retrieval_authority": source_retrieval_authority_file,
                "source_transformation_authority": source_transformation_authority_file,
                "source_build_authority": source_build_authority_file,
                "source_review_aggregate": source_review_aggregate_file,
                "final_bundle_authority": final_bundle_authority_file,
                "provider_policy": provider_policy_file,
                "provider_review_authority": provider_review_authority_file,
                "budget_authority": budget_authority_file,
                "retry_policy": retry_policy_file,
                "full_run_authority": full_run_authority_file,
                "catalog_result": catalog_result_file,
                "voice_profile": voice_profile_file,
                "heard_review_authority": heard_review_authority_file,
                "full_binding_receipt": full_binding_receipt_file,
                "text_result": text_result_file,
                "audio_result": audio_result_file,
            }
            _ensure_korean_production_outputs_distinct(outputs=(evidence_file,), protected_inputs=protected_inputs)
            before_hashes = _hash_korean_production_inputs(protected_inputs)
            _read_korean_production_required_json_inputs(protected_inputs, final=False)
            authority = _build_korean_production_evidence_authority_from_cli(
                job_id=job_id,
                phase31_active_pointer_sha256=phase31_active_pointer_sha256,
                phase31_active_pointer_content_sha256=phase31_active_pointer_content_sha256,
                phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
                phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
                phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
                frequency_bundle_manifest_sha256=frequency_bundle_manifest_sha256,
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
            rows = load_korean_production_evidence_rows(database_url=database_url, job_id=job_id)
            after_hashes = _hash_korean_production_inputs(protected_inputs)
            evidence = validate_korean_production_run_result(
                authority=authority,
                rows=rows,
                expected_item_count=expected_item_count,
                protected_hashes={label: (before_hashes[label], after_hashes[label]) for label in protected_inputs},
                phase31_verifier=verify_active_korean_foundation_snapshot_provenance,
            )
            _write_json_atomic(evidence_file, evidence.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            _fail_korean_production_evidence_operation(exc)
        typer.echo("korean_production_run_evidence_status=validated")
        typer.echo(f"evidence_sha256={evidence.evidence_sha256}")
        typer.echo(f"provider_call_count={evidence.provider_call_count}")

    @cli.command("validate-korean-production-evidence")
    def validate_korean_production_evidence_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256)],
        source_access_authority_sha256: Annotated[str, typer.Option("--source-access-authority-sha256", callback=_validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256)],
        source_transformation_sha256: Annotated[str, typer.Option("--source-transformation-sha256", callback=_validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        final_bundle_authority_sha256: Annotated[str, typer.Option("--final-bundle-authority-sha256", callback=_validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256)],
        budget_authority_sha256: Annotated[str, typer.Option("--budget-authority-sha256", callback=_validate_foundation_sha256)],
        retry_policy_sha256: Annotated[str, typer.Option("--retry-policy-sha256", callback=_validate_foundation_sha256)],
        full_run_authority_sha256: Annotated[str, typer.Option("--full-run-authority-sha256", callback=_validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256)],
        full_binding_receipt_sha256: Annotated[str, typer.Option("--full-binding-receipt-sha256", callback=_validate_foundation_sha256)],
        binding_receipt_file: Annotated[Path, typer.Option("--binding-receipt-file", exists=True, dir_okay=False, readable=True)],
        frequency_bundle_manifest_file: Annotated[Path, typer.Option("--frequency-bundle-manifest-file", exists=True, dir_okay=False, readable=True)],
        source_access_authority_file: Annotated[Path, typer.Option("--source-access-authority-file", exists=True, dir_okay=False, readable=True)],
        source_retrieval_authority_file: Annotated[Path, typer.Option("--source-retrieval-authority-file", exists=True, dir_okay=False, readable=True)],
        source_transformation_authority_file: Annotated[Path, typer.Option("--source-transformation-authority-file", exists=True, dir_okay=False, readable=True)],
        source_build_authority_file: Annotated[Path, typer.Option("--source-build-authority-file", exists=True, dir_okay=False, readable=True)],
        source_review_aggregate_file: Annotated[Path, typer.Option("--source-review-aggregate-file", exists=True, dir_okay=False, readable=True)],
        final_bundle_authority_file: Annotated[Path, typer.Option("--final-bundle-authority-file", exists=True, dir_okay=False, readable=True)],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=True, dir_okay=False, readable=True)],
        provider_review_authority_file: Annotated[Path, typer.Option("--provider-review-authority-file", exists=True, dir_okay=False, readable=True)],
        budget_authority_file: Annotated[Path, typer.Option("--budget-authority-file", exists=True, dir_okay=False, readable=True)],
        retry_policy_file: Annotated[Path, typer.Option("--retry-policy-file", exists=True, dir_okay=False, readable=True)],
        full_run_authority_file: Annotated[Path, typer.Option("--full-run-authority-file", exists=True, dir_okay=False, readable=True)],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=True, dir_okay=False, readable=True)],
        voice_profile_file: Annotated[Path, typer.Option("--voice-profile-file", exists=True, dir_okay=False, readable=True)],
        heard_review_authority_file: Annotated[Path, typer.Option("--heard-review-authority-file", exists=True, dir_okay=False, readable=True)],
        full_binding_receipt_file: Annotated[Path, typer.Option("--full-binding-receipt-file", exists=True, dir_okay=False, readable=True)],
        text_result_file: Annotated[Path, typer.Option("--text-result-file", exists=True, dir_okay=False, readable=True)],
        audio_result_file: Annotated[Path, typer.Option("--audio-result-file", exists=True, dir_okay=False, readable=True)],
        expected_item_count: Annotated[int, typer.Option("--expected-item-count", min=1)],
        evidence_file: Annotated[Path, typer.Option("--evidence-file", exists=False, dir_okay=False, writable=True)],
        content_promotion_authority_sha256: Annotated[str, typer.Option("--content-promotion-authority-sha256", callback=_validate_foundation_sha256)],
        content_promotion_authority_file: Annotated[Path, typer.Option("--content-promotion-authority-file", exists=True, dir_okay=False, readable=True)],
        text_review_aggregate_sha256: Annotated[str, typer.Option("--text-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        text_review_aggregate_file: Annotated[Path, typer.Option("--text-review-aggregate-file", exists=True, dir_okay=False, readable=True)],
        text_review_application_sha256: Annotated[str, typer.Option("--text-review-application-sha256", callback=_validate_foundation_sha256)],
        text_review_application_receipt_file: Annotated[Path, typer.Option("--text-review-application-receipt-file", exists=True, dir_okay=False, readable=True)],
        audio_review_aggregate_sha256: Annotated[str, typer.Option("--audio-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        audio_review_aggregate_file: Annotated[Path, typer.Option("--audio-review-aggregate-file", exists=True, dir_okay=False, readable=True)],
        audio_review_application_sha256: Annotated[str, typer.Option("--audio-review-application-sha256", callback=_validate_foundation_sha256)],
        audio_review_application_receipt_file: Annotated[Path, typer.Option("--audio-review-application-receipt-file", exists=True, dir_okay=False, readable=True)],
        apkg_file: Annotated[Path, typer.Option("--apkg-file", exists=True, dir_okay=False, readable=True)],
        generation_report_json: Annotated[Path, typer.Option("--generation-report-json", exists=True, dir_okay=False, readable=True)],
        generation_report_markdown: Annotated[Path, typer.Option("--generation-report-markdown", exists=True, dir_okay=False, readable=True)],
        expected_word_assets: Annotated[int, typer.Option("--expected-word-assets", min=1)],
        expected_sentence_assets: Annotated[int, typer.Option("--expected-sentence-assets", min=1)],
        cards_per_level: Annotated[int, typer.Option("--cards-per-level", min=1)],
        audit_json: Annotated[Path, typer.Option("--audit-json", exists=False, dir_okay=False, writable=True)],
        audit_markdown: Annotated[Path, typer.Option("--audit-markdown", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            if frequency_bundle_root.is_file():
                raise ValueError("Korean production evidence bundle authority drift")
            protected_inputs = {
                "binding_receipt": binding_receipt_file,
                "frequency_bundle_manifest": frequency_bundle_manifest_file,
                "source_access_authority": source_access_authority_file,
                "source_retrieval_authority": source_retrieval_authority_file,
                "source_transformation_authority": source_transformation_authority_file,
                "source_build_authority": source_build_authority_file,
                "source_review_aggregate": source_review_aggregate_file,
                "final_bundle_authority": final_bundle_authority_file,
                "provider_policy": provider_policy_file,
                "provider_review_authority": provider_review_authority_file,
                "budget_authority": budget_authority_file,
                "retry_policy": retry_policy_file,
                "full_run_authority": full_run_authority_file,
                "catalog_result": catalog_result_file,
                "voice_profile": voice_profile_file,
                "heard_review_authority": heard_review_authority_file,
                "full_binding_receipt": full_binding_receipt_file,
                "text_result": text_result_file,
                "audio_result": audio_result_file,
                "content_promotion_authority": content_promotion_authority_file,
                "text_review_aggregate": text_review_aggregate_file,
                "text_review_application_receipt": text_review_application_receipt_file,
                "audio_review_aggregate": audio_review_aggregate_file,
                "audio_review_application_receipt": audio_review_application_receipt_file,
                "apkg": apkg_file,
                "generation_report_json": generation_report_json,
                "generation_report_markdown": generation_report_markdown,
            }
            _ensure_korean_production_outputs_distinct(
                outputs=(evidence_file, audit_json, audit_markdown),
                protected_inputs=protected_inputs,
            )
            before_hashes = _hash_korean_production_inputs(protected_inputs)
            _read_korean_production_required_json_inputs(protected_inputs, final=True)
            authority = _build_korean_production_evidence_authority_from_cli(
                job_id=job_id,
                phase31_active_pointer_sha256=phase31_active_pointer_sha256,
                phase31_active_pointer_content_sha256=phase31_active_pointer_content_sha256,
                phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
                phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
                phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
                frequency_bundle_manifest_sha256=frequency_bundle_manifest_sha256,
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
            rows = load_korean_production_evidence_rows(database_url=database_url, job_id=job_id)
            after_hashes = _hash_korean_production_inputs(protected_inputs)
            evidence = validate_korean_production_final_evidence(
                authority=authority,
                rows=rows,
                expected_item_count=expected_item_count,
                expected_word_assets=expected_word_assets,
                expected_sentence_assets=expected_sentence_assets,
                cards_per_level=cards_per_level,
                content_promotion_authority_sha256=content_promotion_authority_sha256,
                text_review_aggregate_sha256=text_review_aggregate_sha256,
                text_review_application_sha256=text_review_application_sha256,
                audio_review_aggregate_sha256=audio_review_aggregate_sha256,
                audio_review_application_sha256=audio_review_application_sha256,
                apkg_file=apkg_file,
                generation_report_json=generation_report_json,
                generation_report_markdown=generation_report_markdown,
                protected_hashes={label: (before_hashes[label], after_hashes[label]) for label in protected_inputs},
                phase31_verifier=verify_active_korean_foundation_snapshot_provenance,
            )
            audit_payload = build_korean_production_audit_payload(evidence)
            _write_korean_production_json_atomic(evidence_file, evidence.model_dump(mode="json"))
            _write_korean_production_json_atomic(audit_json, audit_payload)
            _write_korean_production_text_atomic(audit_markdown, render_korean_production_audit_markdown(audit_payload))
        except (ValueError, TypeError) as exc:
            _fail_korean_production_evidence_operation(exc)
        typer.echo("korean_production_final_evidence_status=validated")
        typer.echo(f"evidence_sha256={evidence.evidence_sha256}")
        typer.echo(f"provider_call_count={evidence.provider_call_count}")

    @cli.command("validate-korean-production-review-batches")
    def validate_korean_production_review_batches_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        authority_file: Annotated[Path, typer.Option("--authority-file", exists=True, dir_okay=False, readable=True)],
        receipt_dir: Annotated[list[Path], typer.Option("--receipt-dir", exists=True, file_okay=False, readable=True)],
        expected_item_count: Annotated[int, typer.Option("--expected-item-count", min=1)],
        aggregate_file: Annotated[Path, typer.Option("--aggregate-file", exists=False, dir_okay=False, writable=True)],
        expected_heard_sample_count: Annotated[int, typer.Option("--expected-heard-sample-count", min=0)] = 300,
    ) -> None:
        try:
            authority = KoreanProductionEvidenceAuthority(**_read_korean_production_json_mapping(authority_file))
            receipt_files: list[Path] = []
            for directory in receipt_dir:
                receipt_files.extend(sorted(path for path in directory.iterdir() if path.suffix == ".json" and path.is_file()))
            if not receipt_files:
                raise ValueError("Korean production review aggregate receipt directory is empty")
            rows = load_korean_production_evidence_rows(database_url=database_url, job_id=job_id)
            aggregate = validate_korean_production_review_batches(
                authority=authority,
                rows=rows,
                receipt_files=receipt_files,
                expected_item_count=expected_item_count,
                expected_heard_sample_count=expected_heard_sample_count,
            )
            _write_korean_production_json_atomic(aggregate_file, aggregate.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            _fail_korean_production_evidence_operation(exc)
        typer.echo("korean_production_review_aggregate_status=validated")
        typer.echo(f"aggregate_sha256={aggregate.aggregate_sha256}")
        typer.echo(f"receipt_file_count={aggregate.receipt_file_count}")

    @cli.command("build-korean-release-safety")
    def build_korean_release_safety_command(
        staging_root: Annotated[Path, typer.Option("--staging-root", exists=True, file_okay=False, readable=True)],
        member_controls: Annotated[Path, typer.Option("--member-controls", exists=True, dir_okay=False, readable=True)],
        authority_sha256: Annotated[list[str] | None, typer.Option("--authority-sha256")] = None,
    ) -> None:
        try:
            controls = _read_korean_production_json_mapping(member_controls)
            safety, build_result = build_korean_release_safety(
                staging_root=staging_root,
                member_controls=controls,
                authority_sha256s=_parse_korean_release_authority_values(authority_sha256),
            )
        except (ValueError, TypeError) as exc:
            _fail_korean_release_safety_operation(exc)
        typer.echo("korean_release_safety_status=validated")
        typer.echo(f"report_sha256={safety.report_sha256}")
        typer.echo(f"build_result_sha256={build_result.build_result_sha256}")
        typer.echo(f"safe_for_local_release={str(safety.safe_for_local_release).lower()}")
        typer.echo(f"safe_to_publish={str(safety.safe_to_publish).lower()}")

    @cli.command("promote-korean-release-bundle")
    def promote_korean_release_bundle_command(
        staging_root: Annotated[Path, typer.Option("--staging-root", exists=True, file_okay=False, readable=True)],
        release_parent: Annotated[Path, typer.Option("--release-parent", exists=False, file_okay=False)],
        current_pointer: Annotated[Path, typer.Option("--current-pointer", exists=False, dir_okay=False, writable=True)],
        authorization_sha256: Annotated[str, typer.Option("--authorization-sha256", callback=_validate_foundation_sha256)],
        safety_report: Annotated[Path, typer.Option("--safety-report", exists=True, dir_okay=False, readable=True)],
        build_result: Annotated[Path, typer.Option("--build-result", exists=True, dir_okay=False, readable=True)],
    ) -> None:
        try:
            result = promote_korean_release_bundle(
                staging_root=staging_root,
                release_parent=release_parent,
                current_pointer=current_pointer,
                authorization_sha256=authorization_sha256,
                safety_report=KoreanReleaseSafetyReport(**_read_korean_production_json_mapping(safety_report)),
                build_result=KoreanReleaseBuildResult(**_read_korean_production_json_mapping(build_result)),
            )
        except (ValueError, TypeError) as exc:
            _fail_korean_release_safety_operation(exc)
        typer.echo(f"korean_release_promotion_status={result.status}")
        typer.echo(f"target_name={result.target_name}")
        typer.echo(f"target_root_sha256={result.target_root_sha256}")

    @cli.command("validate-korean-release-authorization")
    def validate_korean_release_authorization_command(
        release_dir: Annotated[Path, typer.Option("--release-dir", exists=True, file_okay=False, readable=True)],
        current_pointer: Annotated[Path, typer.Option("--current-pointer", exists=True, dir_okay=False, readable=True)],
        authorization_sha256: Annotated[str, typer.Option("--authorization-sha256", callback=_validate_foundation_sha256)],
        safety_report: Annotated[Path, typer.Option("--safety-report", exists=True, dir_okay=False, readable=True)],
        build_result: Annotated[Path, typer.Option("--build-result", exists=True, dir_okay=False, readable=True)],
        authorization_output: Annotated[Path, typer.Option("--authorization-output", exists=False, dir_okay=False, writable=True)],
        commit_member: Annotated[list[str] | None, typer.Option("--commit-member")] = None,
        publication_member: Annotated[list[str] | None, typer.Option("--publication-member")] = None,
        commit_token_sha256: Annotated[str | None, typer.Option("--commit-token-sha256", callback=_validate_optional_sha256)] = None,
        publication_token_sha256: Annotated[str | None, typer.Option("--publication-token-sha256", callback=_validate_optional_sha256)] = None,
    ) -> None:
        try:
            authorization = validate_korean_release_authorization(
                release_dir=release_dir,
                current_pointer=current_pointer,
                authorization_sha256=authorization_sha256,
                safety_report=KoreanReleaseSafetyReport(**_read_korean_production_json_mapping(safety_report)),
                build_result=KoreanReleaseBuildResult(**_read_korean_production_json_mapping(build_result)),
                commit_members=commit_member or (),
                publication_members=publication_member or (),
                commit_token_sha256=commit_token_sha256,
                publication_token_sha256=publication_token_sha256,
            )
            _write_korean_production_json_atomic(authorization_output, authorization.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            _fail_korean_release_safety_operation(exc)
        typer.echo("korean_release_authorization_status=validated")
        typer.echo(f"authorization_sha256={authorization.authorization_sha256}")

    @cli.command("execute-korean-release-delivery")
    def execute_korean_release_delivery_command(
        authorization: Annotated[Path, typer.Option("--authorization", exists=True, dir_okay=False, readable=True)],
        release_dir: Annotated[Path, typer.Option("--release-dir", exists=True, file_okay=False, readable=True)],
        git_worktree: Annotated[Path, typer.Option("--git-worktree", exists=False, file_okay=False)],
        action_result: Annotated[Path, typer.Option("--action-result", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            result = execute_korean_release_delivery(
                authorization=KoreanReleaseAuthorization(**_read_korean_production_json_mapping(authorization)),
                release_dir=release_dir,
                git_worktree=git_worktree,
            )
            _write_korean_production_json_atomic(action_result, result.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            _fail_korean_release_safety_operation(exc)
        typer.echo(f"korean_release_delivery_status={result.status}")
        typer.echo(f"action_sha256={result.action_sha256}")

    @cli.command("validate-korean-release-delivery")
    def validate_korean_release_delivery_command(
        authorization: Annotated[Path, typer.Option("--authorization", exists=True, dir_okay=False, readable=True)],
        action_result: Annotated[Path, typer.Option("--action-result", exists=True, dir_okay=False, readable=True)],
        validation_result: Annotated[Path, typer.Option("--validation-result", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            validation = validate_korean_release_delivery(
                authorization=KoreanReleaseAuthorization(**_read_korean_production_json_mapping(authorization)),
                action_result=KoreanReleaseDeliveryActionResult(**_read_korean_production_json_mapping(action_result)),
            )
            _write_korean_production_json_atomic(validation_result, validation.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            _fail_korean_release_safety_operation(exc)
        typer.echo(f"korean_release_delivery_validation_status={validation.status}")
        typer.echo(f"validation_sha256={validation.validation_sha256}")

    @cli.command("synthesize-korean-frequency-audio")
    def synthesize_korean_frequency_audio_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256)],
        binding_receipt_sha256: Annotated[str, typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256)],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=False, dir_okay=False)],
        voice_profile_file: Annotated[Path, typer.Option("--voice-profile-file", exists=False, dir_okay=False)],
        max_items: Annotated[int | None, typer.Option("--max-items", min=1)] = None,
        missing_only: Annotated[bool, typer.Option("--missing-only")] = False,
    ) -> None:
        try:
            authority = _build_korean_audio_authority_from_cli(
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
            result = synthesize_korean_frequency_audio(
                database_url=database_url,
                authority=authority,
                catalog_result_file=catalog_result_file,
                voice_profile_file=voice_profile_file,
                max_items=max_items,
                missing_only=missing_only,
            )
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_frequency_audio_status=synthesized")
        typer.echo(f"audio_processed_items={result.processed_items}")
        typer.echo(f"audio_reused_items={result.reused_items}")
        typer.echo(f"fallback_audio_items={result.fallback_items}")
        typer.echo(f"failed_audio_items={result.failed_items}")

    @cli.command("validate-korean-audio-pilot-result")
    def validate_korean_audio_pilot_result_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=_validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=_validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=_validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=_validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=_validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=_validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=_validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=_validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=_validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=_validate_foundation_sha256)],
        binding_receipt_sha256: Annotated[str, typer.Option("--binding-receipt-sha256", callback=_validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=_validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=_validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=_validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=_validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=_validate_foundation_sha256)],
        pilot_result_file: Annotated[Path, typer.Option("--pilot-result-file", exists=True, dir_okay=False, readable=True)],
        evidence_file: Annotated[Path, typer.Option("--evidence-file", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            payload = json.loads(pilot_result_file.read_text(encoding="utf-8"))
            assets = tuple(AudioAssetRecord.model_validate(item) for item in payload.get("assets", ()))
            evidence = validate_korean_audio_pilot_result(
                authority=_build_korean_audio_pilot_authority_from_cli(
                    job_id=job_id,
                    phase31_validation_receipt_sha256=phase31_validation_receipt_sha256,
                    phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
                    phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
                    binding_receipt_sha256=binding_receipt_sha256,
                    catalog_content_sha256=catalog_content_sha256,
                    profile_sample_authority_sha256=profile_sample_authority_sha256,
                ),
                assets=assets,
                expected_item_count=int(payload.get("expected_item_count", 0)),
                protected_pre_sha256=str(payload.get("protected_pre_sha256", binding_receipt_sha256)),
                protected_post_sha256=str(payload.get("protected_post_sha256", binding_receipt_sha256)),
            )
            evidence_file.parent.mkdir(parents=True, exist_ok=True)
            evidence_file.write_text(evidence.model_dump_json(indent=2) + "\n", encoding="utf-8")
        except (ValueError, TypeError) as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_audio_pilot_evidence_status=validated")
        typer.echo(f"evidence_sha256={evidence.evidence_sha256}")

    @cli.command("import-korean-production-audio-review-batch")
    def import_korean_production_audio_review_batch_command(
        batch_file: Annotated[Path, typer.Option("--batch-file", exists=True, dir_okay=False, readable=True)],
        receipt_file: Annotated[Path, typer.Option("--receipt-file", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            batch = KoreanAudioReviewBatch.model_validate_json(batch_file.read_text(encoding="utf-8"))
            result = KoreanAudioReviewImportLedger().import_batch(batch)
            receipt_file.parent.mkdir(parents=True, exist_ok=True)
            receipt_file.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_audio_review_batch_status=imported")
        typer.echo(f"receipt_sha256={result.receipt_sha256}")
        typer.echo(f"decision_count={result.decision_count}")

    @cli.command("apply-korean-frequency-audio-review")
    def apply_korean_frequency_audio_review_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        aggregate_file: Annotated[Path, typer.Option("--aggregate-file", exists=True, dir_okay=False, readable=True)],
        authority_file: Annotated[Path, typer.Option("--authority-file", exists=True, dir_okay=False, readable=True)],
        mode: Annotated[str, typer.Option("--mode")],
    ) -> None:
        try:
            aggregate = KoreanAudioReviewAggregate.model_validate_json(aggregate_file.read_text(encoding="utf-8"))
            authority = KoreanAudioReviewApplicationAuthority.model_validate_json(authority_file.read_text(encoding="utf-8"))
            if aggregate.job_id != job_id or authority.mode != mode:
                raise ValueError("Korean audio-review authority drift")

            def action(repository: JobRepository) -> object:
                return KoreanAudioReviewApplicationService(AudioRepository(repository.session)).apply(aggregate, authority)

            result = _with_job_repository(database_url, action)
        except ValueError as exc:
            _fail_korean_frequency_text_operation(exc)
        typer.echo("korean_audio_review_application_status=applied")
        typer.echo(f"mode={result.mode}")
        typer.echo(f"mutated_count={result.mutated_count}")

    @cli.command("preview-kindle-highlights")
    def preview_kindle_highlights(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language for candidate filtering."),
        ],
        input_file: Annotated[
            Path,
            typer.Option("--input-file", exists=False, dir_okay=False, help="Path to a local Kindle export."),
        ],
        planned_card_limit: Annotated[
            int | None,
            typer.Option("--planned-card-limit", min=0, help="Optional cap for planned preview cards."),
        ] = None,
    ) -> None:
        try:
            preview = _build_cli_highlight_preview(
                input_file,
                language=language,
                planned_card_limit=planned_card_limit,
                korean_resolver=(
                    resolve_korean_preview_resolver()
                    if language is SupportedLanguage.KO
                    else None
                ),
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"imported_highlights={preview.imported_highlights}")
        typer.echo(f"extracted_candidates={preview.extracted_candidates}")
        typer.echo(f"rejected_highlights={preview.rejected_highlights}")
        typer.echo(f"duplicate_candidates={preview.duplicate_candidates}")
        typer.echo(f"planned_cards={preview.planned_cards}")

    @cli.command("list-webdav-highlights")
    def list_webdav_highlights() -> None:
        try:
            candidates: list[WebDAVRemoteCandidate] = resolve_webdav_service().list_exports()
        except WebDAVError as exc:
            _print_webdav_error(exc)
            raise typer.Exit(code=1) from exc

        for candidate in candidates:
            size = "" if candidate.size_bytes is None else str(candidate.size_bytes)
            modified = "" if candidate.modified_at is None else candidate.modified_at
            typer.echo(
                f"candidate={candidate.safe_name} suffix={candidate.suffix} "
                f"size_bytes={size} modified_at={modified}"
            )

    @cli.command("fetch-webdav-highlights")
    def fetch_webdav_highlights(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language for candidate filtering."),
        ],
        remote_path: Annotated[
            str,
            typer.Option("--remote-path", help="Explicit WebDAV remote Kindle export path."),
        ],
        planned_card_limit: Annotated[
            int | None,
            typer.Option("--planned-card-limit", min=0, help="Optional cap for planned preview cards."),
        ] = None,
    ) -> None:
        try:
            fetch_result: WebDAVFetchResult = resolve_webdav_service().fetch_export(remote_path)
            if language is not SupportedLanguage.KO:
                typer.echo(f"webdav_content_hash={fetch_result.content_hash}")
                typer.echo(f"webdav_cached_file={fetch_result.cached_path}")
                typer.echo(f"webdav_size_bytes={fetch_result.size_bytes}")
            _print_highlight_preview_counts(
                fetch_result.cached_path,
                language=language,
                planned_card_limit=planned_card_limit,
                korean_resolver=(
                    resolve_korean_preview_resolver()
                    if language is SupportedLanguage.KO
                    else None
                ),
            )
        except WebDAVError as exc:
            _print_webdav_error(exc)
            raise typer.Exit(code=1) from exc
        except ValueError as exc:
            message = str(exc)
            code = "empty_source" if "empty" in message.lower() else "malformed_response"
            _print_webdav_error(WebDAVError(WebDAVFailureCode(code), message))
            raise typer.Exit(code=1) from exc

    @cli.command("generate")
    def generate(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language."),
        ],
        source: Annotated[
            str,
            typer.Option("--source", help="Input mode: frequency, word-list, or highlights."),
        ],
        level: Annotated[
            int | None,
            typer.Option("--level", min=1, max=3, help="Frequency level 1-3."),
        ] = None,
        cards_per_level: Annotated[
            int | None,
            typer.Option("--cards-per-level", min=1, help="Cards to generate per frequency level."),
        ] = None,
        test_mode: Annotated[
            bool,
            typer.Option(
                "--test-mode",
                help=f"Shortcut for a small frequency run ({TEST_MODE_CARDS_PER_LEVEL} cards per level).",
            ),
        ] = False,
        input_file: Annotated[
            Path | None,
            typer.Option("--input-file", exists=False, dir_okay=False, help="Path to a word list."),
        ] = None,
        webdav_remote_path: Annotated[
            str | None,
            typer.Option(
                "--webdav-remote-path",
                help="Explicit WebDAV remote Kindle export path for --source highlights.",
            ),
        ] = None,
        resume: Annotated[
            str | None,
            typer.Option("--resume", help="Resume an existing job by id."),
        ] = None,
        overwrite: Annotated[
            bool,
            typer.Option("--overwrite", help="Allow reprocessing completed items."),
        ] = False,
        yes_overwrite: Annotated[
            bool,
            typer.Option(
                "--yes-overwrite",
                help="Confirm overwrite in non-interactive mode when conflicts exist.",
            ),
        ] = False,
        missing_only: Annotated[
            bool,
            typer.Option(
                "--missing-only",
                help="Generate text only for items without persisted text.",
            ),
        ] = False,
        max_items: Annotated[
            int | None,
            typer.Option(
                "--max-items",
                min=1,
                help="Maximum eligible text candidates to process in this run.",
            ),
        ] = None,
        rate_limit_per_minute: Annotated[
            int | None,
            typer.Option(
                "--rate-limit-per-minute",
                min=1,
                help="Maximum provider calls per minute during generation.",
            ),
        ] = None,
        concurrency: Annotated[
            int,
            typer.Option(
                "--concurrency",
                min=1,
                help="Generation workers to claim text items for; default 1. SQLite is conservative, Postgres is recommended for real concurrency.",
            ),
        ] = 1,
        review_report_file: Annotated[
            Path | None,
            typer.Option(
                "--review-report-file",
                dir_okay=False,
                exists=False,
                help="Optional output path for the flagged text review report.",
            ),
        ] = None,
        regenerate_item_key: Annotated[
            str | None,
            typer.Option(
                "--regenerate-item-key",
                help="Regenerate one persisted text item for the resumed job.",
            ),
        ] = None,
    ) -> None:
        if source not in {"frequency", "word-list", "highlights"}:
            raise typer.BadParameter("--source must be one of: frequency, word-list, highlights")
        if language == SupportedLanguage.LA and source == "frequency":
            raise typer.BadParameter("--source frequency is not supported for Latin (la); use --source word-list with a list of lemmas instead (frozen data path is legacy)")
        if webdav_remote_path is not None and source != "highlights":
            raise typer.BadParameter("--webdav-remote-path is only valid when --source highlights")
        if webdav_remote_path is not None and input_file is not None:
            raise typer.BadParameter("--input-file and --webdav-remote-path are mutually exclusive")

        resolved_cards_per_level = cards_per_level
        if source == "frequency" and test_mode and resolved_cards_per_level is None:
            resolved_cards_per_level = TEST_MODE_CARDS_PER_LEVEL
        internal_source = "kindle-highlights" if source == "highlights" else source
        if webdav_remote_path is not None:
            try:
                fetch_result = resolve_webdav_service().fetch_export(webdav_remote_path)
            except WebDAVError as exc:
                _print_webdav_error(exc)
                raise typer.Exit(code=1) from exc
            input_file = fetch_result.cached_path
            typer.echo(f"webdav_content_hash={fetch_result.content_hash}")
            typer.echo(f"webdav_size_bytes={fetch_result.size_bytes}")

        request = GenerationRequest(
            language=language,
            source_type=internal_source,
            level=level,
            cards_per_level=resolved_cards_per_level,
            input_file=input_file,
            resume_job_id=resume,
            overwrite=overwrite,
            yes_overwrite=yes_overwrite,
            missing_only=missing_only,
            max_items=max_items,
            rate_limit_per_minute=rate_limit_per_minute,
            concurrency=concurrency,
        )
        _validate_request(request, test_mode=test_mode)
        _validate_regeneration_flags(
            request=request,
            regenerate_item_key=regenerate_item_key,
        )
        _confirm_overwrite(request, conflict_checker)
        resolved_service = resolve_service()
        rate_limiter = (
            SimpleRateLimiter(request.rate_limit_per_minute)
            if request.rate_limit_per_minute is not None
            else None
        )

        if isinstance(resolved_service, IngestLexicalItemsService):
            if service is None:
                _prepare_lexical_data(request, settings=resolved_service.settings)
            lexical_result = resolved_service.execute(request, rate_limiter=rate_limiter)
            if lexical_result.report.orchestration.diagnostic is not None:
                _print_resume_diagnostic(lexical_result.report)
                raise typer.Exit(code=1)

            typer.echo(f"grounded_candidates={lexical_result.grounded_candidates}")
            typer.echo(f"pending_groundings={lexical_result.pending_groundings}")
            typer.echo(f"rejected_rows={lexical_result.rejected_rows}")
            typer.echo(f"level_1_candidates={lexical_result.level_counts.get(1, 0)}")
            typer.echo(f"level_2_candidates={lexical_result.level_counts.get(2, 0)}")
            typer.echo(f"level_3_candidates={lexical_result.level_counts.get(3, 0)}")
            typer.echo(f"backfilled_candidates={lexical_result.backfilled_candidates}")
            if request.source_type == "kindle-highlights":
                typer.echo(f"imported_highlights={lexical_result.imported_highlights}")
                typer.echo(f"rejected_highlights={lexical_result.rejected_highlights}")
                typer.echo(f"extracted_candidates={lexical_result.extracted_candidates}")
                typer.echo(f"duplicate_candidates={lexical_result.duplicate_candidates}")
                typer.echo(f"reused_existing_candidates={lexical_result.reused_existing_items}")
                typer.echo(f"newly_planned_candidates={lexical_result.newly_planned_candidates}")
                typer.echo(f"blocked_candidates={lexical_result.blocked_candidates}")
                typer.echo(f"planned_cards={lexical_result.planned_cards}")
            if hasattr(resolved_service, "generate_text"):
                if regenerate_item_key is not None:
                    text_result = resolved_service.regenerate_text_item(
                        job_id=lexical_result.report.job_id,
                        item_key=regenerate_item_key,
                        deck_language=language,
                    )
                else:
                    try:
                        text_result = resolved_service.generate_text(
                            job_id=lexical_result.report.job_id,
                            deck_language=language,
                            missing_only=request.missing_only,
                            max_items=request.max_items,
                            progress_callback=_print_generate_text_progress,
                            rate_limiter=rate_limiter,
                            concurrency=request.concurrency,
                        )
                    except TypeError as exc:
                        if "concurrency" not in str(exc):
                            raise
                        text_result = resolved_service.generate_text(
                            job_id=lexical_result.report.job_id,
                            deck_language=language,
                            missing_only=request.missing_only,
                            max_items=request.max_items,
                            progress_callback=_print_generate_text_progress,
                            rate_limiter=rate_limiter,
                        )
                typer.echo(f"text_processed_items={text_result.processed_items}")
                typer.echo(f"accepted_text_items={text_result.accepted_items}")
                typer.echo(f"review_required_text_items={text_result.review_required_items}")
                typer.echo(f"audio_processed_items={text_result.audio_processed_items}")
                typer.echo(f"audio_reused_items={text_result.audio_reused_items}")
                typer.echo(f"fallback_audio_items={text_result.fallback_audio_items}")
                typer.echo(f"failed_audio_items={text_result.failed_audio_items}")
                _print_review_report(
                    _build_review_report(
                        resolved_service,
                        job_id=lexical_result.report.job_id,
                        review_report_file=review_report_file,
                        review_report_builder=review_report_builder,
                    )
                )
            _print_summary(JobSummaryBuilder(resolved_service.repository).build(lexical_result.report))
            return

        result = resolve_executor(resolved_service)(request)

        if not isinstance(result, JobExecutionReport):
            return

        if result.orchestration.diagnostic is not None:
            _print_resume_diagnostic(result)
            raise typer.Exit(code=1)

        if resolved_service is None:
            return

        summary = JobSummaryBuilder(resolved_service.repository).build(result)
        _print_summary(summary)
        _print_review_report(
            _build_review_report(
                resolved_service,
                job_id=result.job_id,
                review_report_file=review_report_file,
                review_report_builder=review_report_builder,
            )
        )

    @cli.command("generate-latin-mvp")
    def generate_latin_mvp(
        source_pack_version: Annotated[
            str,
            typer.Option(
                "--source-pack-version",
                help="Classical Latin MVP source pack version.",
            ),
        ] = "latin-mvp-50-v1",
        manifest_json: Annotated[
            bool,
            typer.Option(
                "--manifest-json",
                help="Print a validated public JSON summary of the Latin MVP source pack.",
            ),
        ] = False,
        portuguese_json: Annotated[
            bool,
            typer.Option(
                "--portuguese-json",
                help="Print a validated public JSON summary with Portuguese translation QA counts.",
            ),
        ] = False,
        audio_json: Annotated[
            bool,
            typer.Option(
                "--audio-json",
                help="Print a validated public JSON summary with Latin audio readiness counts.",
            ),
        ] = False,
    ) -> None:
        # LEGACY FROZEN DATA:
        # These latin-mvp commands use the curated/frozen assets under data/latin_mvp/.
        # To stop using frozen data and generate Latin dynamically (with Definition field etc.):
        #   uv run multilang generate --language la --source word-list --input-file your-lemmas.txt
        request = LatinGenerationRequest(source_pack_version=source_pack_version)
        try:
            latin_service = resolve_latin_mvp_service()
            result = latin_service.start(
                request,
                include_portuguese_translation_summary=portuguese_json,
                include_audio_summary=audio_json,
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        if manifest_json or portuguese_json or audio_json:
            typer.echo(json.dumps(result.manifest_summary(), ensure_ascii=False, indent=2, sort_keys=True))
            return

        typer.echo(f"language_code={result.metadata.language_code}")
        typer.echo(f"variant={result.metadata.variant.value}")
        typer.echo(f"source_type={result.source_type}")
        typer.echo(f"source_pack_version={result.metadata.source_pack_version}")
        typer.echo(f"card_count={result.metadata.card_count}")
        typer.echo(f"item_count={len(result.item_keys)}")
        typer.echo(f"first_item_key={result.first_item_key}")
        typer.echo(f"last_item_key={result.last_item_key}")
        typer.echo(f"license_gate_status={result.license_gate_status}")
        typer.echo(f"source_type_counts={json.dumps(result.source_type_counts, sort_keys=True)}")
        typer.echo(f"frequency_source_count={result.frequency_source_count}")
        typer.echo(f"didactic_sequence_summary={result.didactic_sequence_summary}")
        typer.echo(f"grammar_gate_status={result.grammar_gate_status}")
        typer.echo(f"grammar_evidence_count={result.grammar_evidence_count}")
        typer.echo(f"gramatica_count={result.gramatica_count}")
        typer.echo(f"grammar_gate_status={result.grammar_gate_status}")
        typer.echo(f"grammar_evidence_count={result.grammar_evidence_count}")
        typer.echo(f"gramatica_count={result.gramatica_count}")

    @cli.command("review-latin-mvp")
    def review_latin_mvp(
        curation_file: Annotated[
            Path,
            typer.Option("--curation-file", exists=False, dir_okay=False, help="Path to the Latin curation JSON."),
        ] = DEFAULT_LATIN_MVP_CURATION_PATH,
        summary: Annotated[
            bool,
            typer.Option("--summary", help="Print Latin review gate counts."),
        ] = False,
        item_key: Annotated[
            str | None,
            typer.Option("--item-key", help="Curated record item key to update."),
        ] = None,
        gate: Annotated[
            str | None,
            typer.Option("--gate", help="Gate to update: source, translation, grammar, or audio."),
        ] = None,
        status: Annotated[
            str | None,
            typer.Option("--status", help="New status: needs_review, approved, or rejected."),
        ] = None,
        reason: Annotated[
            str | None,
            typer.Option("--reason", help="Review reason; required for blocking states."),
        ] = None,
        reviewed_by: Annotated[
            str | None,
            typer.Option("--reviewed-by", help="Optional reviewer identifier."),
        ] = None,
        reviewed_at: Annotated[
            str | None,
            typer.Option("--reviewed-at", help="Optional review timestamp."),
        ] = None,
        force: Annotated[
            bool,
            typer.Option("--force", help="Allow overwriting an approved gate."),
        ] = False,
    ) -> None:
        try:
            records = load_latin_curated_records(curation_file)
            if summary:
                review_summary = summarize_latin_review_records(records)
                typer.echo(f"total_records={review_summary.total_records}")
                typer.echo(f"learner_ready_records={review_summary.learner_ready_records}")
                typer.echo(f"blocked_records={review_summary.blocked_records}")
                typer.echo(f"gate_counts={json.dumps(review_summary.gate_counts, sort_keys=True)}")
                return

            missing = [name for name, value in (("item_key", item_key), ("gate", gate), ("status", status)) if value is None]
            if missing:
                raise ValueError("review-latin-mvp update requires --item-key, --gate, and --status")
            records = update_latin_review_gate(
                records,
                item_key=item_key or "",
                gate=gate or "",
                status=status or "",
                reason=reason,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                force=force,
            )
            write_latin_curated_records(records, curation_file)
            typer.echo(f"updated_item_key={item_key}")
            typer.echo(f"updated_gate={gate}")
            typer.echo(f"updated_status={status}")
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

    @cli.command("export-latin-mvp")
    def export_latin_mvp(
        format: Annotated[
            ExportArtifactFormat,
            typer.Option("--format", help="Latin export format: apkg, csv, or tsv. (LEGACY: frozen curated data; for dynamic non-frozen use 'generate --language la --source word-list')"),
        ],
        output_dir: Annotated[
            Path,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                writable=True,
                help="Directory where the Latin MVP export artifact will be written.",
            ),
        ],
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Optional Latin deck name override."),
        ] = LATIN_DECK_NAME,
    ) -> None:
        try:
            _require_clean_anki_id_registry_for_export()
            result = export_latin_mvp_bundle(
                export_format=format,
                output_dir=output_dir,
                deck_name=deck_name,
                repo_root=Path.cwd(),
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")
        typer.echo(f"media_count={result.media_count}")
        typer.echo(f"note_type={result.note_type_name}")
        typer.echo(f"export_status={result.export_status}")

    @cli.command("export")
    def export(
        job_id: Annotated[str, typer.Option("--job-id", help="Persisted job id to export.")],
        format: Annotated[
            ExportArtifactFormat,
            typer.Option("--format", help="Export format: apkg, csv, or tsv."),
        ],
        output_dir: Annotated[
            Path | None,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                writable=True,
                help="Directory where the export artifact will be written.",
            ),
        ] = None,
        deck_name: Annotated[
            str | None,
            typer.Option("--deck-name", help="Optional deck name override for exported artifacts."),
        ] = None,
        refresh_snapshots: Annotated[
            bool,
            typer.Option("--refresh-snapshots", help="Rebuild card_exports before writing the artifact."),
        ] = False,
        allow_partial: Annotated[
            bool,
            typer.Option("--allow-partial", help="Allow incomplete frequency exports with an explicit warning status."),
        ] = False,
    ) -> None:
        resolved_service = resolve_service()
        if resolved_service is None or not hasattr(resolved_service, "export_job"):
            raise typer.Exit(code=1)

        settings = getattr(resolved_service, "settings", Settings())
        target_output_dir = output_dir or settings.export_output_dir

        try:
            _require_clean_anki_id_registry_for_export()
            result = resolved_service.export_job(
                job_id=job_id,
                export_format=format,
                output_dir=target_output_dir,
                deck_name=deck_name,
                refresh_snapshots=refresh_snapshots,
                allow_partial=allow_partial,
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")
        if getattr(result, "partial", False):
            typer.echo("export_status=partial")
        if getattr(result, "report_json_path", None):
            typer.echo(f"generation_report_json={result.report_json_path}")
            typer.echo(f"generation_report_md={result.report_markdown_path}")

    @cli.command("export-korean-frequency-apkg")
    def export_korean_frequency_apkg_command(
        database: Annotated[str, typer.Option("--database", help="Explicit database URL for the Korean export job.")],
        job_id: Annotated[str, typer.Option("--job-id", help="Persisted Korean frequency job id to export.")],
        binding_receipt: Annotated[
            Path,
            typer.Option("--binding-receipt", exists=True, dir_okay=False, readable=True),
        ],
        bundle_root: Annotated[
            Path,
            typer.Option("--bundle-root", exists=True, file_okay=False, readable=True),
        ],
        manifest_file: Annotated[
            Path,
            typer.Option("--manifest-file", exists=True, dir_okay=False, readable=True),
        ],
        output: Annotated[
            Path,
            typer.Option("--output", exists=False, dir_okay=False, writable=True),
        ],
        generation_report_json: Annotated[
            Path,
            typer.Option("--generation-report-json", exists=False, dir_okay=False, writable=True),
        ],
        generation_report_markdown: Annotated[
            Path,
            typer.Option("--generation-report-markdown", exists=False, dir_okay=False, writable=True),
        ],
        cards_per_level: Annotated[int, typer.Option("--cards-per-level", min=1)],
        expected_items: Annotated[int, typer.Option("--expected-items", min=1)],
        expected_word_assets: Annotated[int, typer.Option("--expected-word-assets", min=1)],
        expected_sentence_assets: Annotated[int, typer.Option("--expected-sentence-assets", min=1)],
        no_partial: Annotated[
            bool,
            typer.Option("--no-partial", help="Required: fail closed instead of writing partial Korean frequency output."),
        ] = False,
    ) -> None:
        try:
            if not no_partial:
                raise ValueError("Korean frequency export requires --no-partial")
            _require_clean_anki_id_registry_for_export()
            runtime_service = build_runtime_service(
                settings=Settings(
                    _env_file=None,
                    database_url=database,
                    text_generation_provider="local",
                    translation_provider="local",
                )
            )
            if not hasattr(runtime_service, "export_korean_frequency_apkg"):
                raise ValueError("runtime does not support Korean frequency export")
            result = runtime_service.export_korean_frequency_apkg(
                job_id=job_id,
                binding_receipt_file=binding_receipt,
                bundle_root=bundle_root,
                manifest_file=manifest_file,
                output_path=output,
                generation_report_json_path=generation_report_json,
                generation_report_markdown_path=generation_report_markdown,
                cards_per_level=cards_per_level,
                expected_items=expected_items,
                expected_word_assets=expected_word_assets,
                expected_sentence_assets=expected_sentence_assets,
                no_partial=no_partial,
            )
        except ValueError as exc:
            _fail_korean_frequency_export_operation(exc)

        typer.echo("korean_frequency_export_status=completed")
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")
        typer.echo(f"generation_report_json={result.report_json_path}")
        typer.echo(f"generation_report_md={result.report_markdown_path}")

    @cli.command("repair-text")
    def repair_text(
        job_id: Annotated[str, typer.Option("--job-id", help="Persisted job id to repair.")],
        max_items: Annotated[int | None, typer.Option("--max-items", min=1, help="Maximum review rows to repair.")] = None,
    ) -> None:
        resolved_service = resolve_service()
        if resolved_service is None or not hasattr(resolved_service, "generate_text"):
            raise typer.Exit(code=1)
        job = resolved_service.repository.get_job(job_id)
        if job is None:
            typer.echo(f"unknown job_id: {job_id}")
            raise typer.Exit(code=1)
        result = resolved_service.generate_text(
            job_id=job_id,
            deck_language=SupportedLanguage(job.language),
            max_items=max_items,
            repair_only=True,
            synthesize_audio=False,
            progress_callback=_print_generate_text_progress,
        )
        typer.echo(f"text_processed_items={result.processed_items}")
        typer.echo(f"accepted_text_items={result.accepted_items}")
        typer.echo(f"review_required_text_items={result.review_required_items}")

    @cli.command("synthesize-audio")
    def synthesize_audio(
        job_id: Annotated[str, typer.Option("--job-id", help="Persisted job id to synthesize audio for.")],
        missing_only: Annotated[bool, typer.Option("--missing-only", help="Generate only missing audio assets.")] = False,
        fallback_only: Annotated[bool, typer.Option("--fallback-only", help="Regenerate only audio assets previously produced via fallback.")] = False,
        max_items: Annotated[int | None, typer.Option("--max-items", min=1, help="Maximum text rows to process.")] = None,
    ) -> None:
        resolved_service = resolve_service()
        if resolved_service is None or not hasattr(resolved_service, "synthesize_audio"):
            raise typer.Exit(code=1)
        job = resolved_service.repository.get_job(job_id)
        if job is None:
            typer.echo(f"unknown job_id: {job_id}")
            raise typer.Exit(code=1)
        result = resolved_service.synthesize_audio(
            job_id=job_id,
            deck_language=SupportedLanguage(job.language),
            missing_only=missing_only,
            fallback_only=fallback_only,
            max_items=max_items,
        )
        typer.echo(f"audio_processed_items={result.audio_processed_items}")
        typer.echo(f"audio_reused_items={result.audio_reused_items}")
        typer.echo(f"fallback_audio_items={result.fallback_audio_items}")
        typer.echo(f"failed_audio_items={result.failed_audio_items}")

    @cli.command("audit-deck")
    def audit_deck(
        input_apkg: Annotated[
            Path,
            typer.Option("--input-apkg", exists=False, dir_okay=False, help="Path to the APKG deck to audit."),
        ],
        output_dir: Annotated[
            Path,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                help="Directory where deck-audit.json and deck-audit.md will be written.",
            ),
        ] = Path(".multilang/audits"),
    ) -> None:
        try:
            read_result = read_apkg_cards(input_apkg)
            issues = audit_deck_package(read_result)
            report_result = write_deck_audit_reports(read_result, issues, output_dir)
        except (ValueError, OSError) as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"json_report={report_result.json_path}")
        typer.echo(f"markdown_report={report_result.markdown_path}")
        typer.echo(f"card_count={read_result.card_count}")
        typer.echo(f"issue_count={report_result.issue_count}")
        typer.echo(f"input_sha256={read_result.input_sha256}")
        if any(issue.severity == "error" for issue in issues):
            raise typer.Exit(code=1)

    @cli.command("export-russian-phonemes")
    def export_russian_phonemes(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Russian introductory phoneme .apkg deck.",
            ),
        ] = Settings().export_output_dir / "russian-phonemes.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Russian phoneme package."),
        ] = DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Russian phoneme cards."),
        ] = None,
    ) -> None:
        cards = RUSSIAN_PHONEME_CARDS[:limit] if limit is not None else RUSSIAN_PHONEME_CARDS
        settings = Settings()
        try:
            _require_clean_anki_id_registry_for_export()
            result = export_russian_phoneme_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-polish-phonemes")
    def export_polish_phonemes(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Polish introductory phoneme .apkg deck.",
            ),
        ] = Settings().export_output_dir / "polish-phonemes.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Polish phoneme package."),
        ] = DEFAULT_POLISH_PHONEME_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Polish phoneme cards."),
        ] = None,
    ) -> None:
        cards = POLISH_PHONEME_CARDS[:limit] if limit is not None else POLISH_PHONEME_CARDS
        settings = Settings()
        try:
            _require_clean_anki_id_registry_for_export()
            result = export_polish_phoneme_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-greek-phonemes")
    def export_greek_phonemes(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Greek introductory phoneme .apkg deck.",
            ),
        ] = Settings().export_output_dir / "greek-phonemes.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Greek phoneme package."),
        ] = DEFAULT_GREEK_PHONEME_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Greek phoneme cards."),
        ] = None,
    ) -> None:
        cards = GREEK_PHONEME_CARDS[:limit] if limit is not None else GREEK_PHONEME_CARDS
        settings = Settings()
        try:
            _require_clean_anki_id_registry_for_export()
            result = export_greek_phoneme_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-japanese")
    def export_japanese(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Japanese frequency .apkg deck.",
            ),
        ] = Settings().export_output_dir / "japanese-frequency.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Japanese frequency package."),
        ] = DEFAULT_JAPANESE_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Japanese frequency cards."),
        ] = None,
    ) -> None:
        cards = JAPANESE_FREQUENCY_CARDS[:limit] if limit is not None else JAPANESE_FREQUENCY_CARDS
        settings = Settings()
        try:
            _require_clean_anki_id_registry_for_export()
            result = export_japanese_frequency_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-kana")
    def export_kana(
        source_apkg: Annotated[
            Path | None,
            typer.Option(
                "--from",
                dir_okay=False,
                readable=True,
                help=(
                    "Optional source kana .apkg to import glyphs, mnemonics, stroke art, "
                    "and audio from. Omit for the fully self-generated deck (project "
                    "content + Azure ja-JP audio)."
                ),
            ),
        ] = None,
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the project-native kana .apkg deck.",
            ),
        ] = Settings().export_output_dir / "japanese-kana.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Top-level deck name for the kana package."),
        ] = DEFAULT_KANA_DECK_NAME,
    ) -> None:
        try:
            _require_clean_anki_id_registry_for_export()
            if source_apkg is not None:
                if not source_apkg.is_file():
                    typer.echo(f"error: source package not found: {source_apkg}")
                    raise typer.Exit(code=1)
                result = export_kana_deck(
                    source_apkg=source_apkg, output_path=output_path, deck_name=deck_name
                )
                typer.echo("mode=import")
            else:
                result = export_generated_kana_deck(output_path=output_path, deck_name=deck_name)
                typer.echo("mode=generated")
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")
        typer.echo(f"hiragana_count={result.hiragana_count}")
        typer.echo(f"katakana_count={result.katakana_count}")

    return cli


app = create_app()


if __name__ == "__main__":
    app()
