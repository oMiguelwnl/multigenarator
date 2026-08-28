"""CLI coverage for Korean frequency build validation commands."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app


runner = CliRunner()


def _build_tree(tmp_path: Path) -> tuple[Path, Path]:
    fixture_path = Path(__file__).resolve().parents[1] / "scripts" / "test_build_frequency_assets.py"
    fixture_spec = importlib.util.spec_from_file_location("test_build_frequency_assets", fixture_path)
    assert fixture_spec is not None and fixture_spec.loader is not None
    fixture_module = importlib.util.module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture_module)
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "build_frequency_assets.py"
    spec = importlib.util.spec_from_file_location("build_frequency_assets", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build_korean_frequency_assets = module.build_korean_frequency_assets

    target_root = tmp_path / "bundles"
    inputs = fixture_module._fixture_inputs(tmp_path)
    build_korean_frequency_assets(**inputs, target_root=target_root)
    bundle_dir = target_root / "fixture-v1"
    return bundle_dir, bundle_dir / "build-result.json"


def test_build_result_cli_emits_safe_output_without_private_paths(tmp_path: Path) -> None:
    bundle_dir, result_file = _build_tree(tmp_path)

    result = runner.invoke(
        create_app(),
        [
            "validate-korean-source-build-result",
            "--result-file",
            str(result_file),
            "--bundle-dir",
            str(bundle_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[:3] == [
        "build_result_status=valid",
        "accepted_count=3000",
        "rejection_count=2965",
    ]
    assert any(line.startswith("bundle_sha256=") for line in lines)
    assert str(tmp_path) not in result.output


def test_build_result_cli_failure_is_privacy_safe(tmp_path: Path) -> None:
    result_file = tmp_path / "missing-private-source-build-result.json"

    result = runner.invoke(
        create_app(),
        [
            "validate-korean-source-build-result",
            "--result-file",
            str(result_file),
        ],
    )

    assert result.exit_code == 1
    assert result.output == "korean_frequency_source_error=operation_failed\n"
    assert str(tmp_path) not in result.output
