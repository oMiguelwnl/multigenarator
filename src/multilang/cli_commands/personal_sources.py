"""Personal sources command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.highlights import HighlightInputMode
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.webdav import (
    WebDAVError,
    WebDAVFailureCode,
    WebDAVFetchResult,
    WebDAVRemoteCandidate,
)


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    _build_cli_highlight_preview: Callable[..., Any]
    _print_highlight_preview_counts: Callable[..., Any]
    _print_webdav_error: Callable[..., Any]
    resolve_korean_preview_resolver: Callable[..., Any]
    resolve_webdav_service: Callable[..., Any]


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    @cli.command("preview-kindle-highlights")
    def preview_kindle_highlights(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language for candidate filtering."),
        ],
        input_file: Annotated[
            Path,
            typer.Option("--input-file", exists=False, dir_okay=False, help="Path to a local Kindle export."),
        ],
        planned_card_limit: Annotated[
            int | None,
            typer.Option("--planned-card-limit", min=0, help="Optional cap for planned preview cards."),
        ] = None,
        highlight_input: Annotated[
            HighlightInputMode,
            typer.Option("--highlight-input", help="Kindle input: text extracts words; vocabulary keeps each highlight as one word or expression."),
        ] = HighlightInputMode.TEXT,
    ) -> None:
        if language is SupportedLanguage.KO and highlight_input is HighlightInputMode.VOCABULARY:
            raise typer.BadParameter("Korean highlights require --highlight-input text")
        try:
            preview = dependencies._build_cli_highlight_preview(
                input_file,
                language=language,
                planned_card_limit=planned_card_limit,
                input_mode=highlight_input,
                korean_resolver=(
                    dependencies.resolve_korean_preview_resolver()
                    if language is SupportedLanguage.KO
                    else None
                ),
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"imported_highlights={preview.imported_highlights}")
        typer.echo(f"extracted_candidates={preview.extracted_candidates}")
        typer.echo(f"rejected_highlights={preview.rejected_highlights}")
        typer.echo(f"duplicate_candidates={preview.duplicate_candidates}")
        typer.echo(f"planned_cards={preview.planned_cards}")

    @cli.command("list-webdav-highlights")
    def list_webdav_highlights() -> None:
        try:
            candidates: list[WebDAVRemoteCandidate] = dependencies.resolve_webdav_service().list_exports()
        except WebDAVError as exc:
            dependencies._print_webdav_error(exc)
            raise typer.Exit(code=1) from exc

        for candidate in candidates:
            size = "" if candidate.size_bytes is None else str(candidate.size_bytes)
            modified = "" if candidate.modified_at is None else candidate.modified_at
            typer.echo(
                f"candidate={candidate.safe_name} suffix={candidate.suffix} "
                f"size_bytes={size} modified_at={modified}"
            )

    @cli.command("fetch-webdav-highlights")
    def fetch_webdav_highlights(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language for candidate filtering."),
        ],
        remote_path: Annotated[
            str,
            typer.Option("--remote-path", help="Explicit WebDAV remote Kindle export path."),
        ],
        planned_card_limit: Annotated[
            int | None,
            typer.Option("--planned-card-limit", min=0, help="Optional cap for planned preview cards."),
        ] = None,
        highlight_input: Annotated[
            HighlightInputMode,
            typer.Option("--highlight-input", help="Kindle input: text extracts words; vocabulary keeps each highlight as one word or expression."),
        ] = HighlightInputMode.TEXT,
    ) -> None:
        if language is SupportedLanguage.KO and highlight_input is HighlightInputMode.VOCABULARY:
            raise typer.BadParameter("Korean highlights require --highlight-input text")
        try:
            fetch_result: WebDAVFetchResult = dependencies.resolve_webdav_service().fetch_export(remote_path)
            if language is not SupportedLanguage.KO:
                typer.echo(f"webdav_content_hash={fetch_result.content_hash}")
                typer.echo(f"webdav_cached_file={fetch_result.cached_path}")
                typer.echo(f"webdav_size_bytes={fetch_result.size_bytes}")
            dependencies._print_highlight_preview_counts(
                fetch_result.cached_path,
                language=language,
                planned_card_limit=planned_card_limit,
                input_mode=highlight_input,
                korean_resolver=(
                    dependencies.resolve_korean_preview_resolver()
                    if language is SupportedLanguage.KO
                    else None
                ),
            )
        except WebDAVError as exc:
            dependencies._print_webdav_error(exc)
            raise typer.Exit(code=1) from exc
        except ValueError as exc:
            message = str(exc)
            code = "empty_source" if "empty" in message.lower() else "malformed_response"
            dependencies._print_webdav_error(WebDAVError(WebDAVFailureCode(code), message))
            raise typer.Exit(code=1) from exc
