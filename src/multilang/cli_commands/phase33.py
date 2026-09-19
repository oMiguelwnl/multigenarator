"""Phase33 command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.korean_grammar import KoreanGrammarBundle
from multilang.services.korean_learning_runtime import build_korean_learning_runtime
from multilang.services.phase33_authority import (
    Phase33AuthorityError,
    build_phase33_authority_preflight,
    validate_phase33_authority,
)


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    _validate_foundation_sha256: Callable[[str], str]
    resolve_learning_runtime: Callable[[], Any] = build_korean_learning_runtime


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    phase33 = typer.Typer(help="Import, process, export and review Korean learning material.")
    phase33_review = typer.Typer(help="Review persisted Korean card fields.")
    phase33.add_typer(phase33_review, name="review")
    cli.add_typer(phase33, name="phase33")
    cli.add_typer(phase33, name="korean")

    def _operate(method: str, **kwargs):
        runtime = None
        try:
            runtime = dependencies.resolve_learning_runtime()
            return getattr(runtime, method)(**kwargs)
        except Exception as exc:
            from multilang.services.korean_learning_runtime import KoreanLearningRuntimeError
            code = str(exc) if isinstance(exc, KoreanLearningRuntimeError) else "operation_failed"
            _phase33_error(f"korean_error={code}")
        finally:
            if runtime is not None and getattr(runtime, "owned_session", False):
                runtime.session.close()

    def _write_phase33_json(payload: dict[str, Any], output: Path | None = None) -> None:
        rendered = json.dumps(payload, ensure_ascii=False) + "\n"
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
            return
        typer.echo(rendered, nl=False)

    def _phase33_error(message: str) -> None:
        typer.echo(message)
        raise typer.Exit(code=1)

    def _parse_phase33_path_pairs(values: list[str]) -> dict[str, Path]:
        pairs: dict[str, Path] = {}
        for value in values:
            if "=" not in value:
                raise ValueError("phase33 path pair must use name=path")
            name, raw_path = value.split("=", 1)
            if not name or not raw_path or name in pairs:
                raise ValueError("phase33 path pair must be unique and nonempty")
            pairs[name] = Path(raw_path)
        return pairs

    @phase33.command("status")
    def phase33_status(
        job_id: Annotated[str, typer.Option("--job-id")],
        output_format: Annotated[str, typer.Option("--format")] = "json",
        require_exact_authority: Annotated[bool, typer.Option("--require-exact-authority")] = False,
        no_private_values: Annotated[bool, typer.Option("--no-private-values")] = False,
        output: Annotated[Path | None, typer.Option("--output", exists=False, dir_okay=False)] = None,
    ) -> None:
        if output_format != "json":
            _phase33_error("phase33_status_error=json_required")
        payload = _operate("status", job_id=job_id)
        _write_phase33_json(payload, output)

    @phase33.command("process")
    def phase33_process(
        job_id: Annotated[str, typer.Option("--job-id")],
        source: Annotated[str, typer.Option("--source")],
        mode: Annotated[str, typer.Option("--mode")],
        max_items: Annotated[int | None, typer.Option("--max-items")] = None,
    ) -> None:
        if source not in {"grammar", "custom", "highlight"}:
            _phase33_error("phase33_process_error=invalid_source")
        if mode not in {"start", "resume"}:
            _phase33_error("phase33_process_error=invalid_mode")
        if max_items is not None and max_items < 1:
            _phase33_error("phase33_process_error=invalid_max_items")
        payload = _operate("process", job_id=job_id, source=source, mode=mode, max_items=max_items)
        _write_phase33_json(payload)
        if payload["failed"]:
            raise typer.Exit(code=1)

    @phase33.command("import-grammar")
    def import_grammar(
        bundle_path: Annotated[Path, typer.Option("--bundle", exists=True, dir_okay=False)],
        job_id: Annotated[str | None, typer.Option("--job-id")] = None,
    ) -> None:
        try:
            if bundle_path.stat().st_size > 8_000_000:
                raise ValueError("oversize")
            bundle = KoreanGrammarBundle.model_validate_json(bundle_path.read_bytes())
        except Exception:
            _phase33_error("korean_error=invalid_grammar_bundle")
        _write_phase33_json(_operate("import_grammar_bundle", bundle=bundle, job_id=job_id))

    @phase33.command("import-highlights")
    def import_highlights(
        input_file: Annotated[Path, typer.Option("--input-file", exists=True, dir_okay=False)],
    ) -> None:
        _write_phase33_json(_operate("import_highlights", input_file=input_file))

    @phase33.command("import-custom")
    def import_custom(
        input_file: Annotated[Path, typer.Option("--input-file", exists=True, dir_okay=False)],
        prerequisites_file: Annotated[Path | None, typer.Option("--prerequisites-file", exists=True, dir_okay=False)] = None,
    ) -> None:
        evidence = None
        if prerequisites_file is not None:
            try:
                if prerequisites_file.stat().st_size > 1_000_000:
                    raise ValueError("oversize")
                evidence = json.loads(prerequisites_file.read_text(encoding="utf-8"))
            except Exception:
                _phase33_error("korean_error=invalid_prerequisite_file")
        _write_phase33_json(_operate("import_custom", input_file=input_file, prerequisite_evidence=evidence))

    @phase33.command("bind-provider-policy")
    def bind_provider_policy(
        job_id: Annotated[str, typer.Option("--job-id")],
        provider_policy_file: Annotated[Path, typer.Option("--provider-policy-file", exists=True, dir_okay=False)],
    ) -> None:
        from multilang.domain.korean_provider import KoreanProviderPolicy
        try:
            if provider_policy_file.is_symlink() or provider_policy_file.stat().st_size > 1_000_000:
                raise ValueError("invalid policy file")
            policy = KoreanProviderPolicy.model_validate_json(provider_policy_file.read_bytes())
        except Exception:
            _phase33_error("korean_error=invalid_provider_policy")
        _write_phase33_json(_operate("bind_provider_policy", job_id=job_id, provider_policy=policy))

    @phase33.command("decide-prerequisites")
    def decide_prerequisites(
        job_id: Annotated[str, typer.Option("--job-id")],
        row_id: Annotated[str, typer.Option("--row-id")],
        command_file: Annotated[Path, typer.Option("--command-file", exists=True, dir_okay=False)],
    ) -> None:
        try:
            if command_file.stat().st_size > 32_000:
                raise ValueError("oversize")
            command = json.loads(command_file.read_text(encoding="utf-8"))
        except Exception:
            _phase33_error("korean_error=invalid_decision_file")
        _write_phase33_json(_operate("decide_prerequisites", job_id=job_id, row_id=row_id, command=command))

    @phase33.command("export-grammar")
    def export_grammar(
        job_id: Annotated[str, typer.Option("--job-id")],
        media_dir: Annotated[Path, typer.Option("--media-dir", exists=True, file_okay=False)],
        output_dir: Annotated[Path, typer.Option("--output-dir", file_okay=False)],
        export_format: Annotated[str, typer.Option("--format")] = "apkg",
        bootstrap_cards_file: Annotated[Path | None, typer.Option("--bootstrap-cards", exists=True, dir_okay=False,
            help="Reviewed lexical prerequisite cards, required when the bundle has lexical bootstrap entries.")] = None,
    ) -> None:
        _write_phase33_json(_operate("export_grammar", job_id=job_id, media_dir=media_dir,
            output_dir=output_dir, export_format=export_format, bootstrap_cards_file=bootstrap_cards_file))

    @phase33_review.command("validate")
    def review_validate(
        job_id: Annotated[str, typer.Option("--job-id")],
        item_id: Annotated[str, typer.Option("--item-id")],
    ) -> None:
        result = _operate("review_validate", job_id=job_id, item_id=item_id)
        _write_phase33_json(result)
        if result["validation_status"] != "passed":
            raise typer.Exit(code=1)

    @phase33.command("authority-preflight")
    def phase33_authority_preflight(
        job_id: Annotated[str, typer.Option("--job-id")],
        policy_sha256: Annotated[str, typer.Option("--policy-sha256", callback=dependencies._validate_foundation_sha256)],
        curriculum_sha256: Annotated[str, typer.Option("--curriculum-sha256", callback=dependencies._validate_foundation_sha256)],
        profile_sha256: Annotated[str, typer.Option("--profile-sha256", callback=dependencies._validate_foundation_sha256)],
        source_sha256: Annotated[str, typer.Option("--source-sha256", callback=dependencies._validate_foundation_sha256)],
        target_sha256: Annotated[str, typer.Option("--target-sha256", callback=dependencies._validate_foundation_sha256)],
        output_pairs: Annotated[list[str], typer.Option("--output-pair")],
        audio_roots: Annotated[list[str], typer.Option("--audio-root")],
        custom_safe_ids: Annotated[list[str], typer.Option("--custom-safe-id")],
        highlight_safe_ids: Annotated[list[str], typer.Option("--highlight-safe-id")],
        migration_revision: Annotated[str, typer.Option("--migration-revision")],
        output: Annotated[Path, typer.Option("--output", exists=False, dir_okay=False)],
    ) -> None:
        try:
            audio_root_map = _parse_phase33_path_pairs(audio_roots)
            result = build_phase33_authority_preflight(
                job_id=job_id,
                policy_sha256=policy_sha256,
                curriculum_sha256=curriculum_sha256,
                profile_sha256=profile_sha256,
                source_sha256=source_sha256,
                target_sha256=target_sha256,
                output_pairs=tuple(output_pairs),
                audio_roots=audio_root_map,
                custom_safe_ids=tuple(custom_safe_ids),
                highlight_safe_ids=tuple(highlight_safe_ids),
                migration_revision=migration_revision,
                private_capability="phase33-private-token-v1",
                max_private_tokens=24,
            )
        except (Phase33AuthorityError, ValueError) as exc:
            typer.echo("phase33_authority_error=preflight_failed")
            raise typer.Exit(code=1) from exc
        _write_phase33_json(result.model_dump(mode="json"), output)
        typer.echo("phase33_authority_preflight_status=ready")

    @phase33.command("validate-authority")
    def phase33_validate_authority(
        authority_file: Annotated[Path, typer.Option("--authority-file", exists=True, dir_okay=False, readable=True)],
        expected_kind: Annotated[str, typer.Option("--expected-kind")],
    ) -> None:
        try:
            result = validate_phase33_authority(authority_file, expected_kind=expected_kind)
        except (Phase33AuthorityError, ValueError) as exc:
            typer.echo("phase33_authority_error=validation_failed")
            raise typer.Exit(code=1) from exc
        typer.echo("phase33_authority_status=valid")
        typer.echo(f"authority_kind={result.kind}")
        typer.echo(f"authority_sha256={result.authority_sha256}")

    @phase33_review.command("list")
    def phase33_review_list(
        job_id: Annotated[str, typer.Option("--job-id")],
        actor_id: Annotated[str, typer.Option("--actor-id")],
        request_id: Annotated[str, typer.Option("--request-id")],
        status: Annotated[str, typer.Option("--status")] = "needs_review",
        field: Annotated[str, typer.Option("--field")] = "all",
        source: Annotated[str, typer.Option("--source")] = "all",
        output_format: Annotated[str, typer.Option("--format")] = "json",
    ) -> None:
        if output_format != "json":
            _phase33_error("phase33_review_error=json_required")
        _write_phase33_json(_operate("review_list", job_id=job_id, actor_id=actor_id,
            request_id=request_id, status=status, field=field, source=source))

    @phase33_review.command("edit")
    def review_edit(
        job_id: Annotated[str, typer.Option("--job-id")],
        item_id: Annotated[str, typer.Option("--item-id")],
        field: Annotated[str, typer.Option("--field")],
        value_file: Annotated[Path, typer.Option("--value-file", exists=True, dir_okay=False)],
        actor_id: Annotated[str, typer.Option("--actor-id")],
        request_id: Annotated[str, typer.Option("--request-id")],
        expected_pointer_version: Annotated[int, typer.Option("--expected-pointer-version", min=1)],
    ) -> None:
        try:
            if value_file.stat().st_size > 32_000:
                raise ValueError("oversize")
            value = value_file.read_text(encoding="utf-8").strip()
        except Exception:
            _phase33_error("korean_error=invalid_field_file")
        _write_phase33_json(_operate("review_edit", job_id=job_id, item_id=item_id, field=field,
            value=value, actor_id=actor_id, request_id=request_id, expected_pointer_version=expected_pointer_version))

    def _review_decision_command(decision):
        def command(
            job_id: Annotated[str, typer.Option("--job-id")],
            item_id: Annotated[str, typer.Option("--item-id")],
            field: Annotated[str, typer.Option("--field")],
            revision_id: Annotated[str, typer.Option("--revision-id")],
            actor_id: Annotated[str, typer.Option("--actor-id")],
            request_id: Annotated[str, typer.Option("--request-id")],
            expected_pointer_version: Annotated[int, typer.Option("--expected-pointer-version", min=1)],
        ) -> None:
            _write_phase33_json(_operate("review_decide", job_id=job_id, item_id=item_id, field=field,
                revision_id=revision_id, actor_id=actor_id, request_id=request_id,
                expected_pointer_version=expected_pointer_version, decision=decision))
        return command

    @phase33_review.command("regenerate")
    def review_regenerate(
        job_id: Annotated[str, typer.Option("--job-id")],
        item_id: Annotated[str, typer.Option("--item-id")],
        field: Annotated[str, typer.Option("--field")],
        actor_id: Annotated[str, typer.Option("--actor-id")],
        request_id: Annotated[str, typer.Option("--request-id")],
        expected_pointer_version: Annotated[int, typer.Option("--expected-pointer-version", min=1)],
    ) -> None:
        _write_phase33_json(_operate("review_regenerate", job_id=job_id, item_id=item_id,
            field=field, actor_id=actor_id, request_id=request_id,
            expected_pointer_version=expected_pointer_version))

    phase33_review.command("approve")(_review_decision_command("approved"))
    phase33_review.command("reject")(_review_decision_command("rejected"))
    from multilang.cli_commands.korean_personal_audio import register_personal_audio_commands
    from multilang.cli_commands.korean_personal_text_review import (
        register_commands as register_personal_text_review_commands,
    )
    register_personal_audio_commands(phase33_review, _operate)
    register_personal_text_review_commands(phase33_review, dependencies.resolve_learning_runtime)
