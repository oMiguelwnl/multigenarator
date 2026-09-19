"""Korean foundations command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.korean_curriculum import KoreanFoundationFamily


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    _fail_korean_foundation_operation: Callable[..., Any]
    _foundation_receipt_sha256: Callable[..., Any]
    _inspect_fixed_korean_foundation_exports: Callable[..., Any]
    _print_korean_foundation_prepared_hashes: Callable[..., Any]
    _require_clean_anki_id_registry_for_export: Callable[..., Any]
    _validate_foundation_sha256: Callable[[str], str]
    activate_prepared_korean_foundation_snapshot_from_receipt: Callable[..., Any]
    build_korean_foundation_export_bundle: Callable[..., Any]
    check_korean_foundation_validation_receipt_continuity: Callable[..., Any]
    export_korean_foundation: Callable[..., Any]
    inspect_fixed_korean_foundation_evidence_inbox: Callable[..., Any]
    prepare_korean_foundation_snapshot_from_receipt: Callable[..., Any]
    validate_and_write_fixed_korean_foundation_validation_receipt: Callable[..., Any]
    verify_active_korean_foundation_snapshot_provenance: Callable[..., Any]
    verify_prepared_korean_foundation_snapshot: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    korean_foundations = typer.Typer(
        help="Operate the fixed Korean foundation evidence and export workflow."
    )
    cli.add_typer(korean_foundations, name="korean-foundations")

    @korean_foundations.command("inspect-inbox")
    def inspect_korean_foundation_inbox() -> None:
        try:
            inventory = dependencies.inspect_fixed_korean_foundation_evidence_inbox()
            if not inventory.complete:
                typer.echo("korean_foundations_error=inbox_incomplete")
                raise typer.Exit(code=1)
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
        typer.echo("inbox_status=complete_unvalidated")
        typer.echo(f"evidence_index_sha256={inventory.index_sha256}")
        typer.echo(f"declared_member_count={inventory.evidence_member_count}")

    @korean_foundations.command("validate-and-write-receipt")
    def validate_and_write_korean_foundation_receipt(
        confirmed_index_sha256: Annotated[
            str,
            typer.Option(
                "--confirmed-index-sha256",
                callback=dependencies._validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            receipt = dependencies.validate_and_write_fixed_korean_foundation_validation_receipt(
                confirmed_index_sha256=confirmed_index_sha256
            )
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
        status = getattr(receipt, "_receipt_write_status", "written")
        typer.echo(f"receipt_write_status={status}")
        typer.echo(f"receipt_sha256={dependencies._foundation_receipt_sha256(receipt)}")
        typer.echo(f"bundle_sha256={receipt.evidence_bundle_sha256}")

    @korean_foundations.command("check-receipt")
    def check_korean_foundation_receipt(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=dependencies._validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            report = dependencies.check_korean_foundation_validation_receipt_continuity(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
        typer.echo("receipt_status=continuous")
        typer.echo(f"receipt_sha256={report.receipt_sha256}")
        typer.echo(f"bundle_sha256={report.evidence_bundle_sha256}")

    @korean_foundations.command("prepare-snapshot")
    def prepare_korean_foundation_snapshot(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=dependencies._validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            prepared = dependencies.prepare_korean_foundation_snapshot_from_receipt(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
        dependencies._print_korean_foundation_prepared_hashes(prepared)
        typer.echo("snapshot_status=prepared_inactive")

    @korean_foundations.command("verify-prepared")
    def verify_prepared_korean_foundation(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=dependencies._validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            prepared = dependencies.verify_prepared_korean_foundation_snapshot(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
        dependencies._print_korean_foundation_prepared_hashes(prepared)
        typer.echo("prepared_status=verified")

    @korean_foundations.command("activate")
    def activate_korean_foundation_snapshot(
        expected_receipt_sha256: Annotated[
            str,
            typer.Option(
                "--expected-receipt-sha256",
                callback=dependencies._validate_foundation_sha256,
            ),
        ],
        authorization_sha256: Annotated[
            str,
            typer.Option(
                "--authorization-sha256",
                callback=dependencies._validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            result = dependencies.activate_prepared_korean_foundation_snapshot_from_receipt(
                expected_receipt_sha256=expected_receipt_sha256,
                authorization_sha256=authorization_sha256,
            )
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
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
                callback=dependencies._validate_foundation_sha256,
            ),
        ],
    ) -> None:
        try:
            report = dependencies.verify_active_korean_foundation_snapshot_provenance(
                expected_receipt_sha256=expected_receipt_sha256
            )
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
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
            bundle = dependencies.build_korean_foundation_export_bundle(family=family)
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
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
            dependencies._require_clean_anki_id_registry_for_export()
            result = dependencies.export_korean_foundation(
                family=family,
                export_format=format,
                output_destination=output,
            )
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
        typer.echo(f"family={family.value}")
        typer.echo(f"format={format.value}")
        typer.echo("export_status=written")
        typer.echo(f"card_count={result.card_count}")
        typer.echo(f"media_count={result.media_count}")

    @korean_foundations.command("inspect-exports")
    def inspect_korean_foundation_exports() -> None:
        try:
            report = dependencies._inspect_fixed_korean_foundation_exports()
        except ValueError as exc:
            dependencies._fail_korean_foundation_operation(exc)
        typer.echo("export_set_status=verified")
        typer.echo(f"artifact_count={report.artifact_count}")
        typer.echo(f"receipt_sha256={report.receipt_sha256}")
        typer.echo(f"bundle_sha256={report.bundle_sha256}")
        typer.echo(f"snapshot_root_sha256={report.snapshot_root_sha256}")
