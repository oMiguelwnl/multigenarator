"""Explicit operator inputs for personal Korean audio; registration has no side effects."""

import json
from pathlib import Path
from typing import Annotated

import typer


def register_personal_audio_commands(review_cli, operate):
    @review_cli.command("bind-audio-profile")
    def bind_profile(
        authority_file: Annotated[Path, typer.Option("--authority-file", exists=True, dir_okay=False)],
        catalog_file: Annotated[Path, typer.Option("--catalog-file", exists=True, dir_okay=False)],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=True, dir_okay=False)],
        output_file: Annotated[Path, typer.Option("--output-file", dir_okay=False)],
    ):
        from multilang.services.korean_personal_audio import (
            bind_personal_voice_profile,
            read_contract_file,
        )
        try:
            catalog, catalog_hash = read_contract_file(catalog_file)
            binding = bind_personal_voice_profile(authority=read_contract_file(authority_file)[0], catalog=catalog,
                catalog_file_sha256=catalog_hash, provider_policy=read_contract_file(provider_policy_file)[0])
            # A fresh explicit artifact cannot overwrite a previously approved binding.
            with output_file.open("x", encoding="utf-8") as target:
                target.write(binding.model_dump_json(indent=2) + "\n")
            typer.echo(json.dumps({"binding_sha256": binding.binding_sha256}))
        except Exception:
            typer.echo("korean_error=personal_audio_binding_failed")
            raise typer.Exit(1) from None

    @review_cli.command("regenerate-audio")
    def regenerate(
        authority_file: Annotated[Path, typer.Option("--authority-file", exists=True, dir_okay=False)],
        profile_file: Annotated[Path, typer.Option("--profile-file", exists=True, dir_okay=False)],
        catalog_file: Annotated[Path, typer.Option("--catalog-file", exists=True, dir_okay=False)],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=True, dir_okay=False)],
    ):
        typer.echo(json.dumps(operate("review_regenerate_audio", authority_file=authority_file,
            profile_file=profile_file, catalog_file=catalog_file, provider_policy_file=provider_policy_file)))

    @review_cli.command("apply-audio-review")
    def apply_review(
        authority_file: Annotated[Path, typer.Option("--authority-file", exists=True, dir_okay=False)],
        evidence_file: Annotated[Path, typer.Option("--evidence-file", exists=True, dir_okay=False)],
    ):
        typer.echo(json.dumps(operate("review_apply_audio_evidence", authority_file=authority_file, evidence_file=evidence_file)))

    @review_cli.command("reject-audio")
    def reject(
        job_id: Annotated[str, typer.Option("--job-id")],
        item_id: Annotated[str, typer.Option("--item-id")],
        field: Annotated[str, typer.Option("--field")],
        revision_id: Annotated[str, typer.Option("--revision-id")],
        expected_pointer_version: Annotated[int, typer.Option("--expected-pointer-version", min=1)],
        actor_id: Annotated[str, typer.Option("--actor-id")],
        request_id: Annotated[str, typer.Option("--request-id")],
    ):
        typer.echo(json.dumps(operate("review_decide", job_id=job_id, item_id=item_id, field=field,
            revision_id=revision_id, expected_pointer_version=expected_pointer_version,
            actor_id=actor_id, request_id=request_id, decision="rejected")))

    @review_cli.command("recover-audio")
    def recover(
        authority_file: Annotated[Path, typer.Option("--authority-file", exists=True, dir_okay=False)],
    ):
        typer.echo(json.dumps(operate("review_recover_audio", authority_file=authority_file)))
