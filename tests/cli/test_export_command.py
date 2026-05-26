"""CLI tests for the export command."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.exporting import ExportArtifactFormat

runner = CliRunner()


@dataclass
class FakeExportResult:
    output_path: Path
    card_count: int


@dataclass
class FakeRuntimeService:
    response: FakeExportResult | None = None
    error: Exception | None = None
    calls: list[tuple[str, ExportArtifactFormat, Path, str | None, bool, bool]] = field(default_factory=list)

    def export_job(
        self,
        *,
        job_id: str,
        export_format: ExportArtifactFormat,
        output_dir: Path,
        deck_name: str | None,
        refresh_snapshots: bool = False,
        allow_partial: bool = False,
    ) -> FakeExportResult:
        self.calls.append((job_id, export_format, output_dir, deck_name, refresh_snapshots, allow_partial))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def test_export_command_writes_requested_artifact_and_prints_path(tmp_path: Path) -> None:
    artifact_path = tmp_path / "exports" / "job-1.csv"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("csv", encoding="utf-8")
    service = FakeRuntimeService(response=FakeExportResult(output_path=artifact_path, card_count=3))

    result = runner.invoke(
        create_app(service=service),
        [
            "export",
            "--job-id",
            "job-1",
            "--format",
            "csv",
            "--output-dir",
            str(tmp_path / "exports"),
        ],
    )

    assert result.exit_code == 0
    assert f"artifact_path={artifact_path}" in result.output
    assert "card_count=3" in result.output
    assert service.calls == [("job-1", ExportArtifactFormat.CSV, tmp_path / "exports", None, False, False)]


def test_export_command_forwards_refresh_snapshots(tmp_path: Path) -> None:
    artifact_path = tmp_path / "exports" / "job-1.tsv"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("tsv", encoding="utf-8")
    service = FakeRuntimeService(response=FakeExportResult(output_path=artifact_path, card_count=1))

    result = runner.invoke(
        create_app(service=service),
        ["export", "--job-id", "job-1", "--format", "tsv", "--output-dir", str(tmp_path / "exports"), "--refresh-snapshots"],
    )

    assert result.exit_code == 0
    assert service.calls == [("job-1", ExportArtifactFormat.TSV, tmp_path / "exports", None, True, False)]


def test_export_command_forwards_allow_partial(tmp_path: Path) -> None:
    artifact_path = tmp_path / "exports" / "job-1.apkg"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("apkg", encoding="utf-8")
    service = FakeRuntimeService(response=FakeExportResult(output_path=artifact_path, card_count=2740))

    result = runner.invoke(
        create_app(service=service),
        ["export", "--job-id", "job-1", "--format", "apkg", "--output-dir", str(tmp_path / "exports"), "--allow-partial"],
    )

    assert result.exit_code == 0
    assert service.calls == [("job-1", ExportArtifactFormat.APKG, tmp_path / "exports", None, False, True)]


def test_export_command_exits_non_zero_with_explicit_diagnostics(tmp_path: Path) -> None:
    service = FakeRuntimeService(error=ValueError("missing required sentence audio for item line-1"))

    result = runner.invoke(
        create_app(service=service),
        [
            "export",
            "--job-id",
            "job-1",
            "--format",
            "apkg",
            "--output-dir",
            str(tmp_path / "exports"),
        ],
    )

    assert result.exit_code == 1
    assert "missing required sentence audio for item line-1" in result.output
