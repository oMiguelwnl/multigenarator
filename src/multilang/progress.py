"""Progress rendering helpers for job execution."""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

from multilang.domain.jobs import JobProgressSnapshot, JobStage


class ProgressRenderer:
    """Render concise stage-level counters for the default CLI UX."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render_line(
        self,
        *,
        stage: JobStage,
        completed_items: int,
        total_items: int,
        retrying_items: int,
        failed_items: int,
        skipped_duplicates: int,
    ) -> str:
        text = Text.assemble(
            (f"stage={self._format_stage_label(stage)}", "bold cyan"),
            " ",
            (f"completed={completed_items}/{total_items}", "bold"),
            " ",
            (f"retrying={retrying_items}", "yellow"),
            " ",
            (f"failed={failed_items}", "red"),
            " ",
            (f"skipped_duplicates={skipped_duplicates}", "magenta"),
        )
        return text.plain

    def render_snapshot(self, snapshot: JobProgressSnapshot, *, total_items: int) -> str:
        return self.render_line(
            stage=snapshot.stage,
            completed_items=snapshot.completed_items,
            total_items=total_items,
            retrying_items=snapshot.retrying_items,
            failed_items=snapshot.failed_items,
            skipped_duplicates=snapshot.skipped_duplicates,
        )

    def print_snapshot(self, snapshot: JobProgressSnapshot, *, total_items: int) -> str:
        line = self.render_snapshot(snapshot, total_items=total_items)
        self.console.print(Text(line))
        return line

    def _format_stage_label(self, stage: JobStage) -> str:
        return stage.value.replace("_", " ")
