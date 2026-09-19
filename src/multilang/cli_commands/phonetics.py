"""Phonetics command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.services.japanese_frequency_deck import (
    DEFAULT_JAPANESE_DECK_NAME,
    JAPANESE_FREQUENCY_CARDS,
    export_japanese_frequency_deck,
)
from multilang.services.japanese_kana_deck import DEFAULT_KANA_DECK_NAME, export_kana_deck
from multilang.services.japanese_kana_generated_deck import export_generated_kana_deck
from multilang.services.russian_phoneme_deck import (
    DEFAULT_GREEK_PHONEME_DECK_NAME,
    DEFAULT_POLISH_PHONEME_DECK_NAME,
    DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
    GREEK_PHONEME_CARDS,
    POLISH_PHONEME_CARDS,
    RUSSIAN_PHONEME_CARDS,
    export_greek_phoneme_deck,
    export_polish_phoneme_deck,
    export_russian_phoneme_deck,
)
from multilang.settings import Settings


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    settings_factory: Callable[..., Settings]

    _require_clean_anki_id_registry_for_export: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    @cli.command("export-russian-phonemes")
    def export_russian_phonemes(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Russian introductory phoneme .apkg deck.",
            ),
        ] = dependencies.settings_factory().export_output_dir / "russian-phonemes.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Russian phoneme package."),
        ] = DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Russian phoneme cards."),
        ] = None,
    ) -> None:
        cards = RUSSIAN_PHONEME_CARDS[:limit] if limit is not None else RUSSIAN_PHONEME_CARDS
        settings = dependencies.settings_factory()
        try:
            dependencies._require_clean_anki_id_registry_for_export()
            result = export_russian_phoneme_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-polish-phonemes")
    def export_polish_phonemes(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Polish introductory phoneme .apkg deck.",
            ),
        ] = dependencies.settings_factory().export_output_dir / "polish-phonemes.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Polish phoneme package."),
        ] = DEFAULT_POLISH_PHONEME_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Polish phoneme cards."),
        ] = None,
    ) -> None:
        cards = POLISH_PHONEME_CARDS[:limit] if limit is not None else POLISH_PHONEME_CARDS
        settings = dependencies.settings_factory()
        try:
            dependencies._require_clean_anki_id_registry_for_export()
            result = export_polish_phoneme_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-greek-phonemes")
    def export_greek_phonemes(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Greek introductory phoneme .apkg deck.",
            ),
        ] = dependencies.settings_factory().export_output_dir / "greek-phonemes.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Greek phoneme package."),
        ] = DEFAULT_GREEK_PHONEME_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Greek phoneme cards."),
        ] = None,
    ) -> None:
        cards = GREEK_PHONEME_CARDS[:limit] if limit is not None else GREEK_PHONEME_CARDS
        settings = dependencies.settings_factory()
        try:
            dependencies._require_clean_anki_id_registry_for_export()
            result = export_greek_phoneme_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-japanese")
    def export_japanese(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Japanese frequency .apkg deck.",
            ),
        ] = dependencies.settings_factory().export_output_dir / "japanese-frequency.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Japanese frequency package."),
        ] = DEFAULT_JAPANESE_DECK_NAME,
        limit: Annotated[
            int | None,
            typer.Option("--limit", min=1, help="Export only the first N Japanese frequency cards."),
        ] = None,
    ) -> None:
        cards = JAPANESE_FREQUENCY_CARDS[:limit] if limit is not None else JAPANESE_FREQUENCY_CARDS
        settings = dependencies.settings_factory()
        try:
            dependencies._require_clean_anki_id_registry_for_export()
            result = export_japanese_frequency_deck(output_path=output_path, deck_name=deck_name, cards=cards, settings=settings)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-kana")
    def export_kana(
        source_apkg: Annotated[
            Path | None,
            typer.Option(
                "--from",
                dir_okay=False,
                readable=True,
                help=(
                    "Optional source kana .apkg to import glyphs, mnemonics, stroke art, "
                    "and audio from. Omit for the fully self-generated deck (project "
                    "content + Azure ja-JP audio)."
                ),
            ),
        ] = None,
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the project-native kana .apkg deck.",
            ),
        ] = dependencies.settings_factory().export_output_dir / "japanese-kana.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Top-level deck name for the kana package."),
        ] = DEFAULT_KANA_DECK_NAME,
    ) -> None:
        try:
            dependencies._require_clean_anki_id_registry_for_export()
            if source_apkg is not None:
                if not source_apkg.is_file():
                    typer.echo(f"error: source package not found: {source_apkg}")
                    raise typer.Exit(code=1)
                result = export_kana_deck(
                    source_apkg=source_apkg, output_path=output_path, deck_name=deck_name
                )
                typer.echo("mode=import")
            else:
                result = export_generated_kana_deck(output_path=output_path, deck_name=deck_name)
                typer.echo("mode=generated")
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")
        typer.echo(f"hiragana_count={result.hiragana_count}")
        typer.echo(f"katakana_count={result.katakana_count}")
