"""CLI coverage for Korean source-review batch commands."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from multilang.cli import create_app


runner = CliRunner()


def _load_module(path: Path, name: str) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixtures(tmp_path: Path) -> tuple[Path, Path, object]:
    root = Path(__file__).resolve().parents[2]
    service_tests = _load_module(
        root / "tests" / "services" / "test_korean_source_review.py",
        "test_korean_source_review",
    )
    bundle_dir, result_file = service_tests._build_tree(tmp_path)
    return bundle_dir, result_file, service_tests


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def test_import_cli_emits_safe_output_without_private_paths(tmp_path: Path) -> None:
    bundle_dir, result_file, helpers = _fixtures(tmp_path)
    batch_file = _write_json(
        tmp_path / "batch-0001.json",
        helpers._batch_payload(
            batch_id="batch-0001",
            ranks=range(1, 101),
            bundle_dir=bundle_dir,
            result_file=result_file,
        ),
    )
    receipt_dir = tmp_path / "receipts"

    result = runner.invoke(
        create_app(),
        [
            "import-korean-bundle-review-batch",
            "--batch-file",
            str(batch_file),
            "--build-result-file",
            str(result_file),
            "--bundle-dir",
            str(bundle_dir),
            "--receipt-dir",
            str(receipt_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[:3] == [
        "review_batch_status=imported",
        "batch_id=batch-0001",
        "decision_count=100",
    ]
    assert any(line.startswith("receipt_sha256=") for line in result.output.splitlines())
    assert str(tmp_path) not in result.output


def test_aggregate_cli_emits_complete_safe_output(tmp_path: Path) -> None:
    from multilang.services.korean_source_review import import_korean_bundle_review_batch

    bundle_dir, result_file, helpers = _fixtures(tmp_path)
    receipt_dir = tmp_path / "receipts"
    for start in range(1, 5966, 100):
        stop = min(start + 100, 5966)
        import_korean_bundle_review_batch(
            _write_json(
                tmp_path / f"batch-{start:04d}.json",
                helpers._batch_payload(
                    batch_id=f"batch-{start:04d}",
                    ranks=range(start, stop),
                    bundle_dir=bundle_dir,
                    result_file=result_file,
                ),
            ),
            build_result_file=result_file,
            bundle_dir=bundle_dir,
            receipt_dir=receipt_dir,
        )

    result = runner.invoke(
        create_app(),
        [
            "validate-korean-bundle-review-batches",
            "--receipt-dir",
            str(receipt_dir),
            "--build-result-file",
            str(result_file),
            "--bundle-dir",
            str(bundle_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[:4] == [
        "review_batches_status=complete",
        "total_dispositions=5965",
        "accepted_count=3000",
        "rejected_count=2965",
    ]
    assert str(tmp_path) not in result.output


def test_review_cli_failures_are_privacy_safe(tmp_path: Path) -> None:
    result = runner.invoke(
        create_app(),
        [
            "import-korean-bundle-review-batch",
            "--batch-file",
            str(tmp_path / "secret-batch.json"),
            "--build-result-file",
            str(tmp_path / "secret-build.json"),
            "--bundle-dir",
            str(tmp_path / "secret-bundle"),
            "--receipt-dir",
            str(tmp_path / "receipts"),
        ],
    )

    assert result.exit_code == 1
    assert result.output == "korean_source_review_error=operation_failed\n"
    assert str(tmp_path) not in result.output
