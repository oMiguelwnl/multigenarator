"""Bounded Korean frequency source-review receipt tests."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from multilang.domain.korean import canonical_json_sha256, raw_bytes_sha256


def _load_module(path: Path, name: str) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_tree(tmp_path: Path) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[2]
    fixture_module = _load_module(
        root / "tests" / "scripts" / "test_build_frequency_assets.py",
        "test_build_frequency_assets",
    )
    build_module = _load_module(
        root / "scripts" / "build_frequency_assets.py",
        "build_frequency_assets",
    )
    target_root = tmp_path / "bundles"
    inputs = fixture_module._fixture_inputs(tmp_path)
    build_module.build_korean_frequency_assets(**inputs, target_root=target_root)
    bundle_dir = target_root / "fixture-v1"
    return bundle_dir, bundle_dir / "build-result.json"


def _subjects(bundle_dir: Path) -> dict[int, dict[str, str]]:
    subjects: dict[int, dict[str, str]] = {}
    for line in (bundle_dir / "curated-inventory.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        subjects[int(row["source_rank"])] = {
            "disposition": "accepted",
            "subject_sha256": canonical_json_sha256(row["lexical_identity"]),
        }
    for line in (bundle_dir / "rejections.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        subjects[int(row["source_rank"])] = {
            "disposition": "rejected",
            "subject_sha256": row["source_form_sha256"],
        }
    return subjects


def _batch_payload(
    *,
    batch_id: str,
    ranks: range,
    bundle_dir: Path,
    result_file: Path,
) -> dict[str, Any]:
    subjects = _subjects(bundle_dir)
    return {
        "schema_version": "korean-source-review-batch-v1",
        "batch_id": batch_id,
        "reviewer_class": "ai_policy_source_review",
        "reviewer_role": "source-curation",
        "policy_id": "multilang-ai-linguistic-review-v1",
        "build_result_sha256": raw_bytes_sha256(result_file.read_bytes()),
        "bundle_sha256": json.loads(result_file.read_text(encoding="utf-8"))["bundle_sha256"],
        "decisions": [
            {
                "source_rank": rank,
                "disposition": subjects[rank]["disposition"],
                "subject_sha256": subjects[rank]["subject_sha256"],
                "risk_codes": ["modernity_review_required"],
            }
            for rank in ranks
        ],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def test_batch_import_writes_bounded_content_free_receipt_and_replay_is_no_write(
    tmp_path: Path,
) -> None:
    from multilang.services.korean_source_review import import_korean_bundle_review_batch

    bundle_dir, result_file = _build_tree(tmp_path)
    batch_file = _write_json(
        tmp_path / "batch-0001.json",
        _batch_payload(
            batch_id="batch-0001",
            ranks=range(1, 101),
            bundle_dir=bundle_dir,
            result_file=result_file,
        ),
    )
    receipt_dir = tmp_path / "receipts"

    receipt = import_korean_bundle_review_batch(
        batch_file,
        build_result_file=result_file,
        bundle_dir=bundle_dir,
        receipt_dir=receipt_dir,
    )
    receipt_path = receipt_dir / "batch-0001.json"
    before = receipt_path.stat().st_mtime_ns
    replay = import_korean_bundle_review_batch(
        batch_file,
        build_result_file=result_file,
        bundle_dir=bundle_dir,
        receipt_dir=receipt_dir,
    )

    assert replay == receipt
    assert receipt.decision_count == 100
    assert receipt.accepted_count == 100
    assert receipt.rejected_count == 0
    assert before == receipt_path.stat().st_mtime_ns
    receipt_text = receipt_path.read_text(encoding="utf-8")
    assert "어휘" not in receipt_text
    assert str(tmp_path) not in receipt_text


def test_batch_import_rejects_oversize_overlap_bad_role_stale_identity_and_privacy(
    tmp_path: Path,
) -> None:
    from multilang.services.korean_source_review import import_korean_bundle_review_batch

    bundle_dir, result_file = _build_tree(tmp_path)
    valid = _batch_payload(
        batch_id="batch-0001",
        ranks=range(1, 101),
        bundle_dir=bundle_dir,
        result_file=result_file,
    )
    invalid_payloads = [
        valid | {"batch_id": "batch-oversize", "decisions": valid["decisions"] + [valid["decisions"][0]]},
        valid | {"batch_id": "batch-overlap", "decisions": [valid["decisions"][0], valid["decisions"][0]]},
        valid | {"batch_id": "batch-role", "reviewer_role": "legal-approval"},
        valid | {"batch_id": "batch-stale", "build_result_sha256": "0" * 64},
        valid | {"batch_id": "batch-identity", "decisions": [dict(valid["decisions"][0]) | {"subject_sha256": "1" * 64}]},
        valid | {"batch_id": "batch-private", "private_path": str(tmp_path / "secret.txt")},
    ]

    for index, payload in enumerate(invalid_payloads, start=1):
        with pytest.raises(ValueError):
            import_korean_bundle_review_batch(
                _write_json(tmp_path / f"invalid-{index}.json", payload),
                build_result_file=result_file,
                bundle_dir=bundle_dir,
                receipt_dir=tmp_path / "receipts",
            )


def test_aggregate_requires_disjoint_complete_coverage_and_role_counts(
    tmp_path: Path,
) -> None:
    from multilang.services.korean_source_review import (
        import_korean_bundle_review_batch,
        validate_korean_bundle_review_batches,
    )

    bundle_dir, result_file = _build_tree(tmp_path)
    receipt_dir = tmp_path / "receipts"
    for start in range(1, 5966, 100):
        stop = min(start + 100, 5966)
        import_korean_bundle_review_batch(
            _write_json(
                tmp_path / f"batch-{start:04d}.json",
                _batch_payload(
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

    aggregate = validate_korean_bundle_review_batches(
        receipt_dir,
        build_result_file=result_file,
        bundle_dir=bundle_dir,
    )

    assert aggregate.status == "complete"
    assert aggregate.total_dispositions == 5965
    assert aggregate.accepted_count == 3000
    assert aggregate.rejected_count == 2965
    assert aggregate.max_batch_size <= 100

    (receipt_dir / "batch-0001-copy.json").write_bytes((receipt_dir / "batch-0001.json").read_bytes())
    with pytest.raises(ValueError):
        validate_korean_bundle_review_batches(
            receipt_dir,
            build_result_file=result_file,
            bundle_dir=bundle_dir,
        )
