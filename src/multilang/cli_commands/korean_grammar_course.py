"""Offline preparation commands for the authored G0–G13 course."""

from pathlib import Path
from typing import Annotated

import typer


def register_commands(korean: typer.Typer) -> None:
    @korean.command("build-grammar-course")
    def build_grammar_course_command(
        evidence_file: Annotated[Path, typer.Option("--evidence", exists=True, dir_okay=False)],
        output: Annotated[Path, typer.Option("--output", dir_okay=False)],
        source_dir: Annotated[
            Path | None, typer.Option("--source-dir", exists=True, file_okay=False)
        ] = None,
    ) -> None:
        """Bind current course text to supplied review/media evidence for import-grammar."""
        import json

        from multilang.services.korean_grammar_course import (
            _read_bounded,
            build_grammar_course_bundle,
            load_grammar_course,
            load_grammar_course_support,
        )

        try:
            evidence = json.loads(_read_bounded(evidence_file))
            course = load_grammar_course(source_dir)
            bundle = build_grammar_course_bundle(
                course, evidence, support=load_grammar_course_support(course, source_dir),
            )
            with output.open("x", encoding="utf-8") as stream:
                stream.write(bundle.model_dump_json(indent=2, by_alias=True) + "\n")
        except (ValueError, OSError):
            typer.echo("korean_error=invalid_course_evidence_or_output")
            raise typer.Exit(code=1) from None
        typer.echo(json.dumps({"bundle_sha256": bundle.bundle_sha256,
                               "grammar_card_count": len(bundle.grammar_entries),
                               "orientation_card_count": len(bundle.orientation_entries)}))

    @korean.command("prepare-grammar-course")
    def prepare_grammar_course_command(
        output_dir: Annotated[Path, typer.Option("--output-dir", file_okay=False)],
        source_dir: Annotated[
            Path | None, typer.Option("--source-dir", exists=True, file_okay=False)
        ] = None,
        analyze: Annotated[
            bool, typer.Option("--analyze/--no-analyze", help="Run local Kiwi morphology.")
        ] = True,
        lexical_source_bundle: Annotated[
            Path | None, typer.Option("--lexical-source-bundle", exists=True, file_okay=False,
                                     help="Exact approved NIKL source bundle for lexical grounding.")
        ] = None,
    ) -> None:
        """Prepare the complete course, review preview and bounded audio work list."""
        import json

        from multilang.services.korean_grammar_course import (
            load_grammar_course,
            load_grammar_course_support,
            write_grammar_review_pack,
        )

        try:
            course = load_grammar_course(source_dir)
            report = write_grammar_review_pack(
                course, output_dir, analyze=analyze, lexical_source_bundle=lexical_source_bundle,
                support=load_grammar_course_support(
                    course, source_dir, source_bundle_dir=lexical_source_bundle,
                ),
            )
        except (ValueError, OSError):
            typer.echo("korean_error=invalid_course_or_output_directory")
            raise typer.Exit(code=1) from None
        typer.echo(json.dumps({
            "course_sha256": report["course_sha256"],
            "grammar_card_count": report["grammar_card_count"],
            "category_counts": report["category_counts"],
            "learner_ready": report["learner_ready"],
            "blockers": report["blockers"],
            "audio_requests": report["audio_plan"]["requests"],
            "audio_characters": report["audio_plan"]["characters"],
        }, ensure_ascii=False))
