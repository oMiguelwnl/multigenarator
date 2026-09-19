"""Latin command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.exporting import ExportArtifactFormat
from multilang.domain.latin import LatinGenerationRequest
from multilang.services.latin_export import LATIN_DECK_NAME
from multilang.services.latin_review import (
    DEFAULT_LATIN_MVP_CURATION_PATH,
    load_latin_curated_records,
    summarize_latin_review_records,
    update_latin_review_gate,
    write_latin_curated_records,
)


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    _require_clean_anki_id_registry_for_export: Callable[..., Any]
    export_latin_mvp_bundle: Callable[..., Any]
    resolve_latin_mvp_service: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

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
            latin_service = dependencies.resolve_latin_mvp_service()
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
            dependencies._require_clean_anki_id_registry_for_export()
            result = dependencies.export_latin_mvp_bundle(
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
