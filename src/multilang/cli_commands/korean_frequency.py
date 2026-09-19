"""Korean frequency command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.jobs import SupportedLanguage
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.text_repository import TextRepository
from multilang.services.korean_checkpoint_authority import validate_korean_checkpoint_authority
from multilang.services.korean_frequency import (
    validate_korean_source_build_result,
    validate_korean_source_retrieval_result,
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
from multilang.settings import Settings


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    settings_factory: Callable[..., Settings]

    KoreanFrequencySourceRetriever: Callable[..., Any]
    _bind_korean_frequency_authority: Callable[..., Any]
    _build_korean_frequency_job_authority: Callable[..., Any]
    _check_korean_frequency_authority: Callable[..., Any]
    _fail_korean_checkpoint_authority_operation: Callable[..., Any]
    _fail_korean_frequency_export_operation: Callable[..., Any]
    _fail_korean_frequency_source_operation: Callable[..., Any]
    _fail_korean_frequency_text_operation: Callable[..., Any]
    _fail_korean_source_review_operation: Callable[..., Any]
    _korean_frequency_text_result_payload: Callable[..., Any]
    _print_generate_text_progress: Callable[..., Any]
    _read_korean_provider_policy: Callable[..., Any]
    _require_clean_anki_id_registry_for_export: Callable[..., Any]
    _runtime_authority_from_cli: Callable[..., Any]
    _sha256_file: Callable[..., Any]
    _validate_foundation_sha256: Callable[[str], str]
    _validate_korean_frequency_authority_stage: Callable[[str], str]
    _validate_optional_sha256: Callable[[str | None], str | None]
    _verify_korean_frequency_phase31_authority: Callable[..., Any]
    _with_job_repository: Callable[..., Any]
    _write_json_atomic: Callable[..., Any]
    build_korean_frequency_text_runtime_service: Callable[..., Any]
    build_runtime_service: Callable[..., Any]
    setup_korean_frequency_live_pilot_candidates: Callable[..., Any]
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

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
            result, result_path = dependencies.KoreanFrequencySourceRetriever().retrieve_to_directory(output_dir)
        except ValueError as exc:
            dependencies._fail_korean_frequency_source_operation(exc)
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
        output: Annotated[
            Path | None,
            typer.Option("--output", dir_okay=False, writable=True),
        ] = None,
    ) -> None:
        try:
            result = validate_korean_source_retrieval_result(result_file, source_file=source_file)
            if output is not None:
                source_file_sha256 = dependencies._sha256_file(source_file) if source_file is not None else None
                dependencies._write_json_atomic(
                    output,
                    {
                        "schema_version": "korean-source-retrieval-validation-v1",
                        "status": "valid",
                        "source_id": result.source_id,
                        "accepted_filename": result.accepted_filename,
                        "landing_locator_sha256": sha256(result.landing_url.encode("utf-8")).hexdigest(),
                        "attachment_locator_sha256": sha256(result.attachment_url.encode("utf-8")).hexdigest(),
                        "retrieval_result_sha256": dependencies._sha256_file(result_file),
                        "source_file_sha256": source_file_sha256,
                        "source_bytes_sha256": result.source_bytes_sha256,
                        "attachment_sha256": result.attachment_sha256,
                        "source_byte_count": result.source_byte_count,
                        "text_encoding": result.text_encoding,
                        "grants_transform_power": result.grants_transform_power,
                        "production_asset_path_present": Path("assets/frequency/ko").exists(),
                        "active_frequency_pointer_present": any(
                            path.exists()
                            for path in (
                                Path("assets/frequency/ko/active-frequency.json"),
                                Path("data/korean_frequency/active-frequency.json"),
                            )
                        ),
                    },
                )
        except ValueError as exc:
            dependencies._fail_korean_frequency_source_operation(exc)
        typer.echo("retrieval_result_status=valid")
        typer.echo(f"source_id={result.source_id}")
        typer.echo(f"accepted_filename={result.accepted_filename}")
        typer.echo(f"source_byte_count={result.source_byte_count}")
        if output is not None:
            typer.echo("validation_result_written=true")

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
        output: Annotated[
            Path | None,
            typer.Option("--output", dir_okay=False, writable=True),
        ] = None,
    ) -> None:
        try:
            result = validate_korean_source_build_result(
                result_file,
                bundle_dir=bundle_dir,
            )
            if output is not None:
                dependencies._write_json_atomic(
                    output,
                    {
                        "schema_version": "korean-source-build-validation-v1",
                        "status": "valid",
                        "accepted_count": result.accepted_count,
                        "rejection_count": result.rejection_count,
                        "level_counts": {str(key): value for key, value in result.level_counts.items()},
                        "inventory_sha256": result.inventory_sha256,
                        "rejection_sha256": result.rejection_sha256,
                        "report_sha256": result.report_sha256,
                        "bundle_sha256": result.bundle_sha256,
                        "source_bytes_sha256": result.source_bytes_sha256,
                        "retrieval_sha256": result.retrieval_sha256,
                        "active": result.active,
                        "grants_runtime_activation": result.grants_runtime_activation,
                        "production_asset_path_present": Path("assets/frequency/ko").exists(),
                        "active_frequency_pointer_present": any(
                            path.exists()
                            for path in (
                                Path("assets/frequency/ko/active-frequency.json"),
                                Path("data/korean_frequency/active-frequency.json"),
                            )
                        ),
                    },
                )
        except ValueError as exc:
            dependencies._fail_korean_frequency_source_operation(exc)
        typer.echo("build_result_status=valid")
        typer.echo(f"accepted_count={result.accepted_count}")
        typer.echo(f"rejection_count={result.rejection_count}")
        typer.echo(f"bundle_sha256={result.bundle_sha256}")
        if output is not None:
            typer.echo("build_validation_written=true")

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
            dependencies._fail_korean_source_review_operation(exc)
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
            dependencies._fail_korean_source_review_operation(exc)
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
        output: Annotated[
            Path | None,
            typer.Option("--output", dir_okay=False, writable=True),
        ] = None,
    ) -> None:
        try:
            result = validate_korean_checkpoint_authority(authority_file, expected_kind=expected_kind)
            if output is not None:
                dependencies._write_json_atomic(
                    output,
                    {
                        "authority_kind": result.kind,
                        "authority_sha256": result.authority_sha256,
                        "binding_count": result.binding_count,
                        "power_count": len(result.powers),
                        "status": "valid",
                    },
                )
        except ValueError as exc:
            dependencies._fail_korean_checkpoint_authority_operation(exc)
        typer.echo("authority_status=valid")
        typer.echo(f"authority_kind={result.kind}")
        typer.echo(f"power_count={len(result.powers)}")
        typer.echo(f"binding_count={result.binding_count}")
        typer.echo(f"authority_sha256={result.authority_sha256}")
        if output is not None:
            typer.echo("authority_validation_written=true")

    @cli.command("prepare-korean-frequency-job")
    def prepare_korean_frequency_job(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        authority_stage: Annotated[
            str,
            typer.Option("--authority-stage", callback=dependencies._validate_korean_frequency_authority_stage),
        ] = "pilot_base",
    ) -> None:
        try:
            if authority_stage != "pilot_base":
                raise ValueError("Korean frequency job preparation is limited to pilot_base authority")
            authority = dependencies._build_korean_frequency_job_authority(
                stage=authority_stage,
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
            dependencies._runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            dependencies._verify_korean_frequency_phase31_authority(authority)
            bound = dependencies._bind_korean_frequency_authority(
                database_url=database_url,
                job_id=job_id,
                authority=authority,
            )
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_frequency_job_status=prepared")
        typer.echo(f"job_id={job_id}")
        typer.echo(f"authority_stage={bound.stage}")
        typer.echo(f"binding_receipt_sha256={binding_receipt_sha256}")

    @cli.command("setup-korean-frequency-live-pilot-candidates")
    def setup_korean_frequency_live_pilot_candidates_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        provider_policy_file: Annotated[
            Path,
            typer.Option("--provider-policy-file", exists=True, dir_okay=False, readable=True),
        ],
        authority_stage: Annotated[
            str,
            typer.Option("--authority-stage", callback=dependencies._validate_korean_frequency_authority_stage),
        ] = "pilot_base",
        max_items: Annotated[int, typer.Option("--max-items", min=1)] = 10,
        setup_result_file: Annotated[
            Path,
            typer.Option("--setup-result-file", exists=False, dir_okay=False, writable=True),
        ] = Path("korean-live-pilot-candidate-setup.json"),
    ) -> None:
        try:
            authority = dependencies._build_korean_frequency_job_authority(
                stage=authority_stage,
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
            payload = dependencies.setup_korean_frequency_live_pilot_candidates(
                database_url=database_url,
                job_id=job_id,
                authority=authority,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                provider_policy=dependencies._read_korean_provider_policy(provider_policy_file),
                max_items=max_items,
            )
            dependencies._write_json_atomic(setup_result_file, payload)
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_live_pilot_candidate_setup_status=prepared")
        typer.echo(f"job_id={job_id}")
        typer.echo(f"candidate_count={payload['candidate_count']}")
        typer.echo("setup_result_written=true")

    @cli.command("bind-korean-frequency-audio-authority")
    def bind_korean_frequency_audio_authority(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        catalog_locator_sha256: Annotated[
            str,
            typer.Option("--catalog-locator-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        catalog_content_sha256: Annotated[
            str,
            typer.Option("--catalog-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        profile_sample_authority_sha256: Annotated[
            str,
            typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        provider_review_authority_sha256: Annotated[
            str,
            typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        heard_review_authority_sha256: Annotated[
            str,
            typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
    ) -> None:
        try:
            authority = dependencies._build_korean_frequency_job_authority(
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
            dependencies._runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            dependencies._verify_korean_frequency_phase31_authority(authority)
            bound = dependencies._bind_korean_frequency_authority(
                database_url=database_url,
                job_id=job_id,
                authority=authority,
            )
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
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
            typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        catalog_locator_sha256: Annotated[
            str | None,
            typer.Option("--catalog-locator-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        catalog_content_sha256: Annotated[
            str | None,
            typer.Option("--catalog-content-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        profile_sample_authority_sha256: Annotated[
            str | None,
            typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        provider_review_authority_sha256: Annotated[
            str | None,
            typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        heard_review_authority_sha256: Annotated[
            str | None,
            typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        authority_stage: Annotated[
            str,
            typer.Option("--authority-stage", callback=dependencies._validate_korean_frequency_authority_stage),
        ] = "full",
    ) -> None:
        try:
            authority = dependencies._build_korean_frequency_job_authority(
                stage=authority_stage,
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
            dependencies._runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            dependencies._verify_korean_frequency_phase31_authority(authority)
            bound = dependencies._check_korean_frequency_authority(
                database_url=database_url,
                job_id=job_id,
                authority=authority,
            )
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
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
            typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_active_pointer_content_sha256: Annotated[
            str,
            typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_validation_receipt_sha256: Annotated[
            str,
            typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_manifest_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        phase31_snapshot_root_sha256: Annotated[
            str,
            typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_root: Annotated[
            Path,
            typer.Option("--frequency-bundle-root", exists=False, file_okay=False),
        ],
        frequency_bundle_manifest_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        frequency_bundle_content_sha256: Annotated[
            str,
            typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_retrieval_sha256: Annotated[
            str,
            typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_build_result_sha256: Annotated[
            str,
            typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        source_review_aggregate_sha256: Annotated[
            str,
            typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        provider_policy_sha256: Annotated[
            str,
            typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        pilot_authority_sha256: Annotated[
            str,
            typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        binding_receipt_sha256: Annotated[
            str,
            typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256),
        ],
        catalog_locator_sha256: Annotated[
            str | None,
            typer.Option("--catalog-locator-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        catalog_content_sha256: Annotated[
            str | None,
            typer.Option("--catalog-content-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        profile_sample_authority_sha256: Annotated[
            str | None,
            typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        provider_review_authority_sha256: Annotated[
            str | None,
            typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        heard_review_authority_sha256: Annotated[
            str | None,
            typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        authority_stage: Annotated[
            str,
            typer.Option("--authority-stage", callback=dependencies._validate_korean_frequency_authority_stage),
        ] = "full",
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
        text_result_file: Annotated[
            Path | None,
            typer.Option("--text-result-file", exists=False, dir_okay=False, writable=True),
        ] = None,
        provider_policy_file: Annotated[
            Path | None,
            typer.Option("--provider-policy-file", exists=True, dir_okay=False, readable=True),
        ] = None,
    ) -> None:
        try:
            if authority_stage == "pilot_base" and synthesize_audio:
                raise ValueError("Korean pilot_base text generation cannot synthesize audio")
            authority = dependencies._build_korean_frequency_job_authority(
                stage=authority_stage,
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
            runtime_authority = dependencies._runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            provider_policy = dependencies._read_korean_provider_policy(provider_policy_file) if provider_policy_file is not None else None
            runtime_service = dependencies.build_korean_frequency_text_runtime_service(
                settings=dependencies.settings_factory(_env_file=None, database_url=database_url),
                runtime_authority=runtime_authority,
                phase31_provenance_verifier=(
                    dependencies.verify_active_korean_foundation_snapshot_provenance_with_approved_fallback
                ),
                korean_provider_policy=provider_policy,
            )
            text_result = runtime_service.generate_text(
                job_id=job_id,
                deck_language=SupportedLanguage.KO,
                missing_only=missing_only,
                max_items=max_items,
                progress_callback=dependencies._print_generate_text_progress,
                synthesize_audio=synthesize_audio,
            )
            if text_result_file is not None:
                dependencies._write_json_atomic(
                    text_result_file,
                    dependencies._korean_frequency_text_result_payload(
                        job_id=job_id,
                        authority=authority,
                        binding_receipt_sha256=binding_receipt_sha256,
                        synthesize_audio=synthesize_audio,
                        text_result=text_result,
                        max_items=max_items,
                        korean_provider_policy=provider_policy,
                    ),
                )
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_frequency_text_status=generated")
        typer.echo(f"text_processed_items={text_result.processed_items}")
        typer.echo(f"accepted_text_items={text_result.accepted_items}")
        typer.echo(f"review_required_text_items={text_result.review_required_items}")
        typer.echo(f"audio_processed_items={text_result.audio_processed_items}")
        typer.echo(f"audio_reused_items={text_result.audio_reused_items}")
        typer.echo(f"fallback_audio_items={text_result.fallback_audio_items}")
        typer.echo(f"failed_audio_items={text_result.failed_audio_items}")
        if text_result_file is not None:
            typer.echo("text_result_written=true")

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
            dependencies._fail_korean_frequency_text_operation(exc)
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

            result = dependencies._with_job_repository(database_url, action)
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_text_review_application_status=applied")
        typer.echo(f"mode={result.mode}")
        typer.echo(f"mutated_count={result.mutated_count}")

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
            dependencies._require_clean_anki_id_registry_for_export()
            runtime_service = dependencies.build_runtime_service(
                settings=dependencies.settings_factory(
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
            dependencies._fail_korean_frequency_export_operation(exc)

        typer.echo("korean_frequency_export_status=completed")
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")
        typer.echo(f"generation_report_json={result.report_json_path}")
        typer.echo(f"generation_report_md={result.report_markdown_path}")
