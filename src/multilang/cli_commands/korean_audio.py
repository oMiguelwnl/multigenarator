"""Korean audio command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer
from sqlalchemy.orm import Session

from multilang.db.provisioning import ensure_database_schema
from multilang.domain.audio import AudioAssetRecord
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
from multilang.services.korean_audio import build_korean_voice_profile_from_authority
from multilang.services.korean_audio_pilot_evidence import validate_korean_audio_pilot_result
from multilang.services.korean_audio_review import (
    KoreanAudioReviewAggregate,
    KoreanAudioReviewApplicationAuthority,
    KoreanAudioReviewApplicationService,
    KoreanAudioReviewBatch,
    KoreanAudioReviewImportLedger,
)
from multilang.settings import Settings


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    settings_factory: Callable[..., Settings]

    AzureSpeechAdapter: Callable[..., Any]
    _build_korean_audio_authority_from_cli: Callable[..., Any]
    _build_korean_audio_pilot_authority_from_cli: Callable[..., Any]
    _build_korean_frequency_job_authority: Callable[..., Any]
    _default_azure_catalog_endpoint: Callable[..., Any]
    _ensure_korean_voice_profile_outputs_distinct: Callable[..., Any]
    _fail_korean_frequency_text_operation: Callable[..., Any]
    _read_json_mapping: Callable[..., Any]
    _read_korean_provider_policy: Callable[..., Any]
    _read_markdown_json_mapping: Callable[..., Any]
    _runtime_authority_from_cli: Callable[..., Any]
    _sha256_file: Callable[..., Any]
    _validate_foundation_sha256: Callable[[str], str]
    _validate_optional_sha256: Callable[[str | None], str | None]
    _with_job_repository: Callable[..., Any]
    _write_json_atomic: Callable[..., Any]
    capture_korean_azure_catalog_pilot: Callable[..., Any]
    create_engine: Callable[..., Any]
    synthesize_korean_frequency_audio: Callable[..., Any]
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    @cli.command("capture-korean-azure-catalog")
    def capture_korean_azure_catalog_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        binding_receipt_sha256: Annotated[str, typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=True, dir_okay=False, readable=True)],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=False, dir_okay=False)],
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
        endpoint_url: Annotated[str | None, typer.Option("--endpoint-url")] = None,
    ) -> None:
        try:
            if frequency_bundle_root.is_file() or catalog_result_file.is_dir():
                raise ValueError("Korean Azure catalog authority drift")
            authority = dependencies._build_korean_frequency_job_authority(
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
            dependencies._runtime_authority_from_cli(
                database_url=database_url,
                job_id=job_id,
                frequency_bundle_root=frequency_bundle_root,
                binding_receipt_sha256=binding_receipt_sha256,
                authority=authority,
            )
            settings_obj = dependencies.settings_factory(_env_file=None, database_url=database_url)
            resolved_endpoint = endpoint_url or dependencies._default_azure_catalog_endpoint(settings_obj)
            engine = dependencies.create_engine(database_url)
            ensure_database_schema(engine, database_url)
            session = Session(engine)
            try:
                payload = dependencies.capture_korean_azure_catalog_pilot(
                    job_id=job_id,
                    authority=authority,
                    provider_policy=dependencies._read_korean_provider_policy(provider_policy_file),
                    endpoint_url=resolved_endpoint,
                    provider_call_logger=ProviderCallLogRepository(session),
                    phase31_verifier=dependencies.verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
                    catalog_fetcher=dependencies.AzureSpeechAdapter(settings_obj).fetch_voice_inventory,
                )
            finally:
                session.close()
                engine.dispose()
            dependencies._write_json_atomic(catalog_result_file, payload)
        except (RuntimeError, ValueError) as exc:
            if not isinstance(exc, ValueError):
                exc = ValueError(str(exc))
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_azure_catalog_status=captured")
        typer.echo(f"job_id={job_id}")
        typer.echo(f"catalog_voice_count={payload['voice_count']}")

    @cli.command("bind-korean-azure-voice-profile")
    def bind_korean_azure_voice_profile_command(
        job_id: Annotated[str, typer.Option("--job-id")],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=True, dir_okay=False, readable=True)],
        profile_authority_file: Annotated[Path, typer.Option("--profile-authority-file", exists=True, dir_okay=False, readable=True)],
        voice_profile_file: Annotated[Path, typer.Option("--voice-profile-file", exists=False, dir_okay=False, writable=True)],
        evidence_file: Annotated[Path, typer.Option("--evidence-file", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            protected_inputs = {
                "catalog_result": catalog_result_file,
                "profile_authority": profile_authority_file,
            }
            dependencies._ensure_korean_voice_profile_outputs_distinct(
                outputs=(voice_profile_file, evidence_file),
                protected_inputs=protected_inputs,
            )
            before_hashes = {label: dependencies._sha256_file(path) for label, path in protected_inputs.items()}
            catalog_result = dependencies._read_json_mapping(catalog_result_file)
            profile_authority = dependencies._read_markdown_json_mapping(profile_authority_file)
            profile, evidence = build_korean_voice_profile_from_authority(
                catalog_result=catalog_result,
                profile_authority=profile_authority,
                job_id=job_id,
                provider_policy_sha256=provider_policy_sha256,
                pilot_authority_sha256=pilot_authority_sha256,
                catalog_locator_sha256=catalog_locator_sha256,
                catalog_content_sha256=catalog_content_sha256,
                catalog_result_file_sha256=before_hashes["catalog_result"],
                profile_authority_sha256=before_hashes["profile_authority"],
            )
            after_hashes = {label: dependencies._sha256_file(path) for label, path in protected_inputs.items()}
            if after_hashes != before_hashes:
                raise ValueError("Korean voice profile protected input drift")
            dependencies._write_json_atomic(voice_profile_file, profile.model_dump(mode="json"))
            dependencies._write_json_atomic(evidence_file, evidence.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_voice_profile_status=bound")
        typer.echo(f"profile_sha256={profile.profile_sha256}")
        typer.echo(f"evidence_sha256={evidence.evidence_sha256}")

    @cli.command("synthesize-korean-frequency-audio")
    def synthesize_korean_frequency_audio_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        binding_receipt_sha256: Annotated[str, typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=dependencies._validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_result_file: Annotated[Path, typer.Option("--catalog-result-file", exists=False, dir_okay=False)],
        voice_profile_file: Annotated[Path, typer.Option("--voice-profile-file", exists=False, dir_okay=False)],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=False, dir_okay=False)],
        max_items: Annotated[int | None, typer.Option("--max-items", min=1)] = None,
        missing_only: Annotated[bool, typer.Option("--missing-only")] = False,
    ) -> None:
        try:
            authority = dependencies._build_korean_audio_authority_from_cli(
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
            job_authority = dependencies._build_korean_frequency_job_authority(
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
            result = dependencies.synthesize_korean_frequency_audio(
                database_url=database_url,
                authority=authority,
                catalog_result_file=catalog_result_file,
                voice_profile_file=voice_profile_file,
                provider_policy_file=provider_policy_file,
                frequency_bundle_root=frequency_bundle_root,
                job_authority=job_authority,
                max_items=max_items,
                missing_only=missing_only,
            )
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        status = "failed" if result.failed_items else "synthesized_pending_review"
        typer.echo(f"korean_frequency_audio_status={status}")
        typer.echo(f"audio_processed_items={result.processed_items}")
        typer.echo(f"audio_reused_items={result.reused_items}")
        typer.echo(f"fallback_audio_items={result.fallback_items}")
        typer.echo(f"failed_audio_items={result.failed_items}")

    @cli.command("validate-korean-audio-pilot-result")
    def validate_korean_audio_pilot_result_command(
        database_url: Annotated[str, typer.Option("--database-url")],
        job_id: Annotated[str, typer.Option("--job-id")],
        phase31_active_pointer_sha256: Annotated[str, typer.Option("--phase31-active-pointer-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_active_pointer_content_sha256: Annotated[str, typer.Option("--phase31-active-pointer-content-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_validation_receipt_sha256: Annotated[str, typer.Option("--phase31-validation-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_snapshot_manifest_sha256: Annotated[str, typer.Option("--phase31-snapshot-manifest-sha256", callback=dependencies._validate_foundation_sha256)],
        phase31_snapshot_root_sha256: Annotated[str, typer.Option("--phase31-snapshot-root-sha256", callback=dependencies._validate_foundation_sha256)],
        frequency_bundle_root: Annotated[Path, typer.Option("--frequency-bundle-root", exists=False, file_okay=False)],
        frequency_bundle_manifest_sha256: Annotated[str, typer.Option("--frequency-bundle-manifest-sha256", callback=dependencies._validate_foundation_sha256)],
        frequency_bundle_content_sha256: Annotated[str, typer.Option("--frequency-bundle-content-sha256", callback=dependencies._validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        pilot_authority_sha256: Annotated[str, typer.Option("--pilot-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        binding_receipt_sha256: Annotated[str, typer.Option("--binding-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=dependencies._validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        pilot_result_file: Annotated[Path, typer.Option("--pilot-result-file", exists=True, dir_okay=False, readable=True)],
        evidence_file: Annotated[Path, typer.Option("--evidence-file", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            payload = json.loads(pilot_result_file.read_text(encoding="utf-8"))
            assets = tuple(AudioAssetRecord.model_validate(item) for item in payload.get("assets", ()))
            evidence = validate_korean_audio_pilot_result(
                authority=dependencies._build_korean_audio_pilot_authority_from_cli(
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
            dependencies._fail_korean_frequency_text_operation(exc)
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
            dependencies._fail_korean_frequency_text_operation(exc)
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

            result = dependencies._with_job_repository(database_url, action)
        except ValueError as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_audio_review_application_status=applied")
        typer.echo(f"mode={result.mode}")
        typer.echo(f"mutated_count={result.mutated_count}")
