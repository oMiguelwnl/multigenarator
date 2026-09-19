"""Local evidence import for personal Korean text; registration opens no resources."""

import json
import os
import stat
from pathlib import Path
from typing import Annotated

import typer

_MAX_EVIDENCE_BYTES = 1_000_000


def _read_evidence(path):
    # Open once, without following the final link; inspect and read that same file.
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_EVIDENCE_BYTES:
            raise ValueError("invalid_evidence_file")
        payload = source.read(_MAX_EVIDENCE_BYTES + 1)
        if len(payload) > _MAX_EVIDENCE_BYTES:
            raise ValueError("invalid_evidence_file")
    return json.loads(payload)


def register_commands(review_cli, resolve_learning_runtime):
    """Attach hash-only preparation and provider-free evidence application commands."""
    from multilang.services.korean_personal_text_review import (
        PersonalTextReviewError,
        apply_personal_text_evidence,
        prepare_personal_text_evidence,
    )

    def operate(operation, *, evidence_file=None, output=None, **kwargs):
        runtime = None
        try:
            if evidence_file is not None:
                kwargs["evidence"] = _read_evidence(evidence_file)
            runtime = resolve_learning_runtime()
            result = operation(runtime, **kwargs)
            rendered = json.dumps(result, ensure_ascii=False) + "\n"
            if output is not None:
                # An explicit new artifact cannot overwrite an earlier review subject.
                with output.open("x", encoding="utf-8") as destination:
                    destination.write(rendered)
            else:
                typer.echo(rendered, nl=False)
        except Exception as error:
            code = str(error) if isinstance(error, PersonalTextReviewError) else "text_review_operation_failed"
            typer.echo(f"korean_error={code}")
            raise typer.Exit(1) from None
        finally:
            if runtime is not None and getattr(runtime, "owned_session", False):
                runtime.session.close()

    @review_cli.command("prepare-text-evidence")
    def prepare(
        job_id: Annotated[str, typer.Option("--job-id")],
        item_id: Annotated[str, typer.Option("--item-id")],
        output: Annotated[Path | None, typer.Option("--output")] = None,
    ):
        """Prepare hashes and revision IDs for three independent AI review passes."""
        operate(prepare_personal_text_evidence, job_id=job_id, item_id=item_id, output=output)

    @review_cli.command("apply-text-evidence")
    def apply(
        job_id: Annotated[str, typer.Option("--job-id")],
        item_id: Annotated[str, typer.Option("--item-id")],
        evidence_file: Annotated[Path, typer.Option("--evidence-file")],
        actor_id: Annotated[str, typer.Option("--actor-id")],
        request_id: Annotated[str, typer.Option("--request-id")],
    ):
        """Apply existing AI evidence locally; this command never calls a provider."""
        operate(apply_personal_text_evidence, job_id=job_id, item_id=item_id,
            evidence_file=evidence_file, actor_id=actor_id, request_id=request_id)
