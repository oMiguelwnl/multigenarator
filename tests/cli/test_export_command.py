"""CLI tests for the export command."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app
from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.anki_id_registry import AnkiIdRegistryScanResult

runner = CliRunner()


@dataclass
class FakeExportResult:
    output_path: Path
    card_count: int
    report_json_path: Path | None = None
    report_markdown_path: Path | None = None
    partial: bool = False


@dataclass
class FakeRuntimeService:
    response: FakeExportResult | None = None
    error: Exception | None = None
    calls: list[tuple[str, ExportArtifactFormat, Path, str | None, bool, bool]] = field(default_factory=list)
    korean_frequency_calls: list[dict[str, object]] = field(default_factory=list)

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

    def export_korean_frequency_apkg(
        self,
        *,
        job_id: str,
        binding_receipt_file: Path,
        bundle_root: Path,
        manifest_file: Path,
        output_path: Path,
        generation_report_json_path: Path,
        generation_report_markdown_path: Path,
        cards_per_level: int,
        expected_items: int,
        expected_word_assets: int,
        expected_sentence_assets: int,
        no_partial: bool,
    ) -> FakeExportResult:
        self.korean_frequency_calls.append(
            {
                "job_id": job_id,
                "binding_receipt_file": binding_receipt_file,
                "bundle_root": bundle_root,
                "manifest_file": manifest_file,
                "output_path": output_path,
                "generation_report_json_path": generation_report_json_path,
                "generation_report_markdown_path": generation_report_markdown_path,
                "cards_per_level": cards_per_level,
                "expected_items": expected_items,
                "expected_word_assets": expected_word_assets,
                "expected_sentence_assets": expected_sentence_assets,
                "no_partial": no_partial,
            }
        )
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


def test_check_anki_id_registry_command_reports_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_module,
        "assert_anki_id_registry_clean",
        lambda *, production_roots=False, roots=None: AnkiIdRegistryScanResult(
            roots=(Path("src/multilang"),), scanned_files=7, issues=()
        ),
    )

    result = runner.invoke(create_app(), ["check-anki-id-registry", "--production-roots"])

    assert result.exit_code == 0
    assert "anki_id_registry_status=clean" in result.output
    assert "scanned_files=7" in result.output


def test_export_command_checks_registry_before_output_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_registry(*, production_roots: bool = False, roots: object = None) -> object:
        raise ValueError("Anki ID registry violations: injected collision")

    monkeypatch.setattr(cli_module, "assert_anki_id_registry_clean", fail_registry)
    artifact_path = tmp_path / "exports" / "job-1.csv"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text("sentinel", encoding="utf-8")
    service = FakeRuntimeService(response=FakeExportResult(output_path=artifact_path, card_count=3))

    result = runner.invoke(
        create_app(service=service),
        ["export", "--job-id", "job-1", "--format", "csv", "--output-dir", str(artifact_path.parent)],
    )

    assert result.exit_code == 1
    assert "Anki ID registry violations: injected collision" in result.output
    assert service.calls == []
    assert artifact_path.read_text(encoding="utf-8") == "sentinel"


def test_export_korean_frequency_apkg_uses_explicit_database_paths_and_generation_reports(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    receipt = tmp_path / "binding-receipt.json"
    manifest = tmp_path / "manifest.json"
    bundle_root = tmp_path / "bundle"
    output_path = tmp_path / "korean-frequency.apkg"
    report_json = tmp_path / "reports" / "generation-report.json"
    report_md = tmp_path / "reports" / "generation-report.md"
    receipt.write_text("{}", encoding="utf-8")
    manifest.write_text("{}", encoding="utf-8")
    bundle_root.mkdir()
    service = FakeRuntimeService(
        response=FakeExportResult(
            output_path=output_path,
            card_count=3,
            report_json_path=report_json,
            report_markdown_path=report_md,
        )
    )
    built_database_urls: list[str] = []

    def fake_build_runtime_service(settings: object) -> FakeRuntimeService:
        built_database_urls.append(str(getattr(settings, "database_url")))
        return service

    monkeypatch.setattr(cli_module, "build_runtime_service", fake_build_runtime_service)
    monkeypatch.setattr(cli_module, "assert_anki_id_registry_clean", lambda *, production_roots=False, roots=None: None)

    result = runner.invoke(
        create_app(),
        [
            "export-korean-frequency-apkg",
            "--database",
            f"sqlite:///{tmp_path / 'korean.sqlite'}",
            "--job-id",
            "job-ko",
            "--binding-receipt",
            str(receipt),
            "--bundle-root",
            str(bundle_root),
            "--manifest-file",
            str(manifest),
            "--output",
            str(output_path),
            "--generation-report-json",
            str(report_json),
            "--generation-report-markdown",
            str(report_md),
            "--cards-per-level",
            "1",
            "--expected-items",
            "3",
            "--expected-word-assets",
            "3",
            "--expected-sentence-assets",
            "3",
            "--no-partial",
        ],
    )

    assert result.exit_code == 0
    assert built_database_urls == [f"sqlite:///{tmp_path / 'korean.sqlite'}"]
    assert service.korean_frequency_calls == [
        {
            "job_id": "job-ko",
            "binding_receipt_file": receipt,
            "bundle_root": bundle_root,
            "manifest_file": manifest,
            "output_path": output_path,
            "generation_report_json_path": report_json,
            "generation_report_markdown_path": report_md,
            "cards_per_level": 1,
            "expected_items": 3,
            "expected_word_assets": 3,
            "expected_sentence_assets": 3,
            "no_partial": True,
        }
    ]
    assert f"artifact_path={output_path}" in result.output
    assert "card_count=3" in result.output
    assert f"generation_report_json={report_json}" in result.output
    assert f"generation_report_md={report_md}" in result.output


def test_export_korean_frequency_apkg_requires_no_partial_before_runtime_build(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    receipt = tmp_path / "binding-receipt.json"
    manifest = tmp_path / "manifest.json"
    bundle_root = tmp_path / "bundle"
    receipt.write_text("{}", encoding="utf-8")
    manifest.write_text("{}", encoding="utf-8")
    bundle_root.mkdir()

    def fail_build_runtime_service(settings: object) -> object:
        raise AssertionError("runtime should not be built without --no-partial")

    monkeypatch.setattr(cli_module, "build_runtime_service", fail_build_runtime_service)

    result = runner.invoke(
        create_app(),
        [
            "export-korean-frequency-apkg",
            "--database",
            f"sqlite:///{tmp_path / 'korean.sqlite'}",
            "--job-id",
            "job-ko",
            "--binding-receipt",
            str(receipt),
            "--bundle-root",
            str(bundle_root),
            "--manifest-file",
            str(manifest),
            "--output",
            str(tmp_path / "korean-frequency.apkg"),
            "--generation-report-json",
            str(tmp_path / "generation-report.json"),
            "--generation-report-markdown",
            str(tmp_path / "generation-report.md"),
            "--cards-per-level",
            "1",
            "--expected-items",
            "3",
            "--expected-word-assets",
            "3",
            "--expected-sentence-assets",
            "3",
        ],
    )

    assert result.exit_code == 1
    assert "korean_frequency_export_error=no_partial_required" in result.output
