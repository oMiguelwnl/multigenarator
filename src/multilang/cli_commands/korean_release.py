"""Korean release command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.services.korean_release_delivery import KoreanReleaseDeliveryActionResult
from multilang.services.korean_release_safety import (
    KoreanReleaseAuthorization,
    KoreanReleaseBuildResult,
    KoreanReleaseSafetyReport,
    build_korean_release_safety,
    promote_korean_release_bundle,
    validate_korean_release_authorization,
)


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    _fail_korean_release_safety_operation: Callable[..., Any]
    _parse_korean_release_authority_values: Callable[..., Any]
    _read_korean_production_json_mapping: Callable[..., Any]
    _validate_foundation_sha256: Callable[[str], str]
    _validate_optional_sha256: Callable[[str | None], str | None]
    _write_korean_production_json_atomic: Callable[..., Any]
    execute_korean_release_delivery: Callable[..., Any]
    validate_korean_release_delivery: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    @cli.command("build-korean-release-safety")
    def build_korean_release_safety_command(
        staging_root: Annotated[Path, typer.Option("--staging-root", exists=True, file_okay=False, readable=True)],
        member_controls: Annotated[Path, typer.Option("--member-controls", exists=True, dir_okay=False, readable=True)],
        authority_sha256: Annotated[list[str] | None, typer.Option("--authority-sha256")] = None,
    ) -> None:
        try:
            controls = dependencies._read_korean_production_json_mapping(member_controls)
            safety, build_result = build_korean_release_safety(
                staging_root=staging_root,
                member_controls=controls,
                authority_sha256s=dependencies._parse_korean_release_authority_values(authority_sha256),
            )
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_release_safety_operation(exc)
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
        authorization_sha256: Annotated[str, typer.Option("--authorization-sha256", callback=dependencies._validate_foundation_sha256)],
        safety_report: Annotated[Path, typer.Option("--safety-report", exists=True, dir_okay=False, readable=True)],
        build_result: Annotated[Path, typer.Option("--build-result", exists=True, dir_okay=False, readable=True)],
    ) -> None:
        try:
            result = promote_korean_release_bundle(
                staging_root=staging_root,
                release_parent=release_parent,
                current_pointer=current_pointer,
                authorization_sha256=authorization_sha256,
                safety_report=KoreanReleaseSafetyReport(**dependencies._read_korean_production_json_mapping(safety_report)),
                build_result=KoreanReleaseBuildResult(**dependencies._read_korean_production_json_mapping(build_result)),
            )
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_release_safety_operation(exc)
        typer.echo(f"korean_release_promotion_status={result.status}")
        typer.echo(f"target_name={result.target_name}")
        typer.echo(f"target_root_sha256={result.target_root_sha256}")

    @cli.command("validate-korean-release-authorization")
    def validate_korean_release_authorization_command(
        release_dir: Annotated[Path, typer.Option("--release-dir", exists=True, file_okay=False, readable=True)],
        current_pointer: Annotated[Path, typer.Option("--current-pointer", exists=True, dir_okay=False, readable=True)],
        authorization_sha256: Annotated[str, typer.Option("--authorization-sha256", callback=dependencies._validate_foundation_sha256)],
        safety_report: Annotated[Path, typer.Option("--safety-report", exists=True, dir_okay=False, readable=True)],
        build_result: Annotated[Path, typer.Option("--build-result", exists=True, dir_okay=False, readable=True)],
        authorization_output: Annotated[Path, typer.Option("--authorization-output", exists=False, dir_okay=False, writable=True)],
        commit_member: Annotated[list[str] | None, typer.Option("--commit-member")] = None,
        publication_member: Annotated[list[str] | None, typer.Option("--publication-member")] = None,
        commit_token_sha256: Annotated[str | None, typer.Option("--commit-token-sha256", callback=dependencies._validate_optional_sha256)] = None,
        publication_token_sha256: Annotated[str | None, typer.Option("--publication-token-sha256", callback=dependencies._validate_optional_sha256)] = None,
    ) -> None:
        try:
            authorization = validate_korean_release_authorization(
                release_dir=release_dir,
                current_pointer=current_pointer,
                authorization_sha256=authorization_sha256,
                safety_report=KoreanReleaseSafetyReport(**dependencies._read_korean_production_json_mapping(safety_report)),
                build_result=KoreanReleaseBuildResult(**dependencies._read_korean_production_json_mapping(build_result)),
                commit_members=commit_member or (),
                publication_members=publication_member or (),
                commit_token_sha256=commit_token_sha256,
                publication_token_sha256=publication_token_sha256,
            )
            dependencies._write_korean_production_json_atomic(authorization_output, authorization.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_release_safety_operation(exc)
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
            result = dependencies.execute_korean_release_delivery(
                authorization=KoreanReleaseAuthorization(**dependencies._read_korean_production_json_mapping(authorization)),
                release_dir=release_dir,
                git_worktree=git_worktree,
            )
            dependencies._write_korean_production_json_atomic(action_result, result.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_release_safety_operation(exc)
        typer.echo(f"korean_release_delivery_status={result.status}")
        typer.echo(f"action_sha256={result.action_sha256}")

    @cli.command("validate-korean-release-delivery")
    def validate_korean_release_delivery_command(
        authorization: Annotated[Path, typer.Option("--authorization", exists=True, dir_okay=False, readable=True)],
        action_result: Annotated[Path, typer.Option("--action-result", exists=True, dir_okay=False, readable=True)],
        validation_result: Annotated[Path, typer.Option("--validation-result", exists=False, dir_okay=False, writable=True)],
    ) -> None:
        try:
            validation = dependencies.validate_korean_release_delivery(
                authorization=KoreanReleaseAuthorization(**dependencies._read_korean_production_json_mapping(authorization)),
                action_result=KoreanReleaseDeliveryActionResult(**dependencies._read_korean_production_json_mapping(action_result)),
            )
            dependencies._write_korean_production_json_atomic(validation_result, validation.model_dump(mode="json"))
        except (ValueError, TypeError) as exc:
            dependencies._fail_korean_release_safety_operation(exc)
        typer.echo(f"korean_release_delivery_validation_status={validation.status}")
        typer.echo(f"validation_sha256={validation.validation_sha256}")
