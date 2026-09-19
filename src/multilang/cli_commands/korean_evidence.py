"""Korean evidence command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.services.korean_production_evidence import KoreanProductionEvidenceAuthority
from multilang.services.korean_provider_pilot_evidence import (
    KoreanProviderCatalogPilotAuthority,
    validate_korean_provider_catalog_pilot_result,
)


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    _build_korean_production_evidence_authority_from_cli: Callable[..., Any]
    _catalog_result_hash: Callable[..., Any]
    _ensure_korean_production_outputs_distinct: Callable[..., Any]
    _fail_korean_frequency_text_operation: Callable[..., Any]
    _fail_korean_production_evidence_operation: Callable[..., Any]
    _hash_korean_production_inputs: Callable[..., Any]
    _list_provider_call_rows_read_only: Callable[..., Any]
    _read_json_mapping: Callable[..., Any]
    _read_korean_production_json_mapping: Callable[..., Any]
    _read_korean_production_required_json_inputs: Callable[..., Any]
    _sha256_file: Callable[..., Any]
    _validate_foundation_sha256: Callable[[str], str]
    _validate_optional_sha256: Callable[[str | None], str | None]
    _write_json_atomic: Callable[..., Any]
    _write_korean_production_json_atomic: Callable[..., Any]
    _write_korean_production_text_atomic: Callable[..., Any]
    build_korean_production_audit_payload: Callable[..., Any]
    load_korean_production_evidence_rows: Callable[..., Any]
    render_korean_production_audit_markdown: Callable[..., Any]
    validate_korean_production_final_evidence: Callable[..., Any]
    validate_korean_production_review_batches: Callable[..., Any]
    validate_korean_production_run_result: Callable[..., Any]
    verify_active_korean_foundation_snapshot_provenance: Callable[..., Any]
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    @cli.command("validate-korean-provider-catalog-pilot-result")
    def validate_korean_provider_catalog_pilot_result_command(
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
        final_authority_sha256: Annotated[str, typer.Option("--final-authority-sha256", callback=dependencies._validate_foundation_sha256)],
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
        profile_sample_authority_sha256: Annotated[
            str | None,
            typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        catalog_locator_sha256: Annotated[
            str | None,
            typer.Option("--catalog-locator-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        catalog_content_sha256: Annotated[
            str | None,
            typer.Option("--catalog-content-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        provider_review_authority_sha256: Annotated[
            str | None,
            typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
        heard_review_authority_sha256: Annotated[
            str | None,
            typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_optional_sha256),
        ] = None,
    ) -> None:
        try:
            if frequency_bundle_root.is_file():
                raise ValueError("Korean provider/catalog pilot bundle authority drift")
            if not provider_review_authority_sha256:
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
            before_hashes = {label: dependencies._sha256_file(path) for label, path in protected_inputs.items()}
            text_result = dependencies._read_json_mapping(text_result_file)
            catalog_result = dependencies._read_json_mapping(catalog_result_file)
            derived_catalog_locator_sha256 = dependencies._catalog_result_hash(catalog_result, "catalog_locator_sha256")
            derived_catalog_content_sha256 = dependencies._catalog_result_hash(catalog_result, "catalog_content_sha256")
            if catalog_locator_sha256 is not None and catalog_locator_sha256 != derived_catalog_locator_sha256:
                raise ValueError("Korean provider/catalog pilot catalog locator drift")
            if catalog_content_sha256 is not None and catalog_content_sha256 != derived_catalog_content_sha256:
                raise ValueError("Korean provider/catalog pilot catalog content drift")
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
                catalog_locator_sha256=derived_catalog_locator_sha256,
                catalog_content_sha256=derived_catalog_content_sha256,
                final_authority_sha256=final_authority_sha256,
            )
            provider_call_rows = dependencies._list_provider_call_rows_read_only(database_url=database_url, job_id=job_id)
            after_hashes = {label: dependencies._sha256_file(path) for label, path in protected_inputs.items()}
            evidence = validate_korean_provider_catalog_pilot_result(
                authority=authority,
                provider_call_records=provider_call_rows,
                text_result=text_result,
                catalog_result=catalog_result,
                expected_item_count=expected_item_count,
                protected_hashes={label: (before_hashes[label], after_hashes[label]) for label in protected_inputs},
                phase31_verifier=dependencies.verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
            )
            dependencies._write_korean_production_json_atomic(evidence_file, evidence.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_frequency_text_operation(exc)
        typer.echo("korean_provider_catalog_pilot_evidence_status=validated")
        typer.echo(f"evidence_sha256={evidence.evidence_sha256}")
        typer.echo(f"provider_call_count={evidence.provider_call_count}")
        typer.echo(f"synthesis_attempt_count={evidence.synthesis_attempt_count}")

    @cli.command("validate-korean-production-run-result")
    def validate_korean_production_run_result_command(
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
        source_access_authority_sha256: Annotated[str, typer.Option("--source-access-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256)],
        source_transformation_sha256: Annotated[str, typer.Option("--source-transformation-sha256", callback=dependencies._validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256)],
        final_bundle_authority_sha256: Annotated[str, typer.Option("--final-bundle-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        budget_authority_sha256: Annotated[str, typer.Option("--budget-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        retry_policy_sha256: Annotated[str, typer.Option("--retry-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        full_run_authority_sha256: Annotated[str, typer.Option("--full-run-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=dependencies._validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        full_binding_receipt_sha256: Annotated[str, typer.Option("--full-binding-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
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
            dependencies._ensure_korean_production_outputs_distinct(outputs=(evidence_file,), protected_inputs=protected_inputs)
            before_hashes = dependencies._hash_korean_production_inputs(protected_inputs)
            dependencies._read_korean_production_required_json_inputs(protected_inputs, final=False)
            voice_profile = dependencies._read_korean_production_json_mapping(voice_profile_file)
            authority = dependencies._build_korean_production_evidence_authority_from_cli(
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
            rows = dependencies.load_korean_production_evidence_rows(database_url=database_url, job_id=job_id)
            after_hashes = dependencies._hash_korean_production_inputs(protected_inputs)
            evidence = dependencies.validate_korean_production_run_result(
                authority=authority,
                voice_profile=voice_profile,
                provider_policy=dependencies._read_korean_production_json_mapping(provider_policy_file),
                rows=rows,
                expected_item_count=expected_item_count,
                protected_hashes={label: (before_hashes[label], after_hashes[label]) for label in protected_inputs},
                phase31_verifier=dependencies.verify_active_korean_foundation_snapshot_provenance,
            )
            dependencies._write_json_atomic(evidence_file, evidence.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_production_evidence_operation(exc)
        typer.echo("korean_production_run_evidence_status=validated")
        typer.echo(f"evidence_sha256={evidence.evidence_sha256}")
        typer.echo(f"provider_call_count={evidence.provider_call_count}")

    @cli.command("validate-korean-production-evidence")
    def validate_korean_production_evidence_command(
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
        source_access_authority_sha256: Annotated[str, typer.Option("--source-access-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        source_retrieval_sha256: Annotated[str, typer.Option("--source-retrieval-sha256", callback=dependencies._validate_foundation_sha256)],
        source_transformation_sha256: Annotated[str, typer.Option("--source-transformation-sha256", callback=dependencies._validate_foundation_sha256)],
        source_build_result_sha256: Annotated[str, typer.Option("--source-build-result-sha256", callback=dependencies._validate_foundation_sha256)],
        source_review_aggregate_sha256: Annotated[str, typer.Option("--source-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256)],
        final_bundle_authority_sha256: Annotated[str, typer.Option("--final-bundle-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_policy_sha256: Annotated[str, typer.Option("--provider-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        provider_review_authority_sha256: Annotated[str, typer.Option("--provider-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        budget_authority_sha256: Annotated[str, typer.Option("--budget-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        retry_policy_sha256: Annotated[str, typer.Option("--retry-policy-sha256", callback=dependencies._validate_foundation_sha256)],
        full_run_authority_sha256: Annotated[str, typer.Option("--full-run-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_locator_sha256: Annotated[str, typer.Option("--catalog-locator-sha256", callback=dependencies._validate_foundation_sha256)],
        catalog_content_sha256: Annotated[str, typer.Option("--catalog-content-sha256", callback=dependencies._validate_foundation_sha256)],
        profile_sample_authority_sha256: Annotated[str, typer.Option("--profile-sample-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        heard_review_authority_sha256: Annotated[str, typer.Option("--heard-review-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        full_binding_receipt_sha256: Annotated[str, typer.Option("--full-binding-receipt-sha256", callback=dependencies._validate_foundation_sha256)],
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
        content_promotion_authority_sha256: Annotated[str, typer.Option("--content-promotion-authority-sha256", callback=dependencies._validate_foundation_sha256)],
        content_promotion_authority_file: Annotated[Path, typer.Option("--content-promotion-authority-file", exists=True, dir_okay=False, readable=True)],
        text_review_aggregate_sha256: Annotated[str, typer.Option("--text-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256)],
        text_review_aggregate_file: Annotated[Path, typer.Option("--text-review-aggregate-file", exists=True, dir_okay=False, readable=True)],
        text_review_application_sha256: Annotated[str, typer.Option("--text-review-application-sha256", callback=dependencies._validate_foundation_sha256)],
        text_review_application_receipt_file: Annotated[Path, typer.Option("--text-review-application-receipt-file", exists=True, dir_okay=False, readable=True)],
        audio_review_aggregate_sha256: Annotated[str, typer.Option("--audio-review-aggregate-sha256", callback=dependencies._validate_foundation_sha256)],
        audio_review_aggregate_file: Annotated[Path, typer.Option("--audio-review-aggregate-file", exists=True, dir_okay=False, readable=True)],
        audio_review_application_sha256: Annotated[str, typer.Option("--audio-review-application-sha256", callback=dependencies._validate_foundation_sha256)],
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
            dependencies._ensure_korean_production_outputs_distinct(
                outputs=(evidence_file, audit_json, audit_markdown),
                protected_inputs=protected_inputs,
            )
            before_hashes = dependencies._hash_korean_production_inputs(protected_inputs)
            dependencies._read_korean_production_required_json_inputs(protected_inputs, final=True)
            voice_profile = dependencies._read_korean_production_json_mapping(voice_profile_file)
            authority = dependencies._build_korean_production_evidence_authority_from_cli(
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
            rows = dependencies.load_korean_production_evidence_rows(database_url=database_url, job_id=job_id)
            after_hashes = dependencies._hash_korean_production_inputs(protected_inputs)
            evidence = dependencies.validate_korean_production_final_evidence(
                authority=authority,
                voice_profile=voice_profile,
                provider_policy=dependencies._read_korean_production_json_mapping(provider_policy_file),
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
                phase31_verifier=dependencies.verify_active_korean_foundation_snapshot_provenance,
            )
            audit_payload = dependencies.build_korean_production_audit_payload(evidence)
            dependencies._write_korean_production_json_atomic(evidence_file, evidence.model_dump(mode="json"))
            dependencies._write_korean_production_json_atomic(audit_json, audit_payload)
            dependencies._write_korean_production_text_atomic(audit_markdown, dependencies.render_korean_production_audit_markdown(audit_payload))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_production_evidence_operation(exc)
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
            authority = KoreanProductionEvidenceAuthority(**dependencies._read_korean_production_json_mapping(authority_file))
            receipt_files: list[Path] = []
            for directory in receipt_dir:
                receipt_files.extend(sorted(path for path in directory.iterdir() if path.suffix == ".json" and path.is_file()))
            if not receipt_files:
                raise ValueError("Korean production review aggregate receipt directory is empty")
            rows = dependencies.load_korean_production_evidence_rows(database_url=database_url, job_id=job_id)
            aggregate = dependencies.validate_korean_production_review_batches(
                authority=authority,
                rows=rows,
                receipt_files=receipt_files,
                expected_item_count=expected_item_count,
                expected_heard_sample_count=expected_heard_sample_count,
            )
            dependencies._write_korean_production_json_atomic(aggregate_file, aggregate.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_production_evidence_operation(exc)
        typer.echo("korean_production_review_aggregate_status=validated")
        typer.echo(f"aggregate_sha256={aggregate.aggregate_sha256}")
        typer.echo(f"receipt_file_count={aggregate.receipt_file_count}")
