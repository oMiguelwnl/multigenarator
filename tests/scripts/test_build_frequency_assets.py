"""Durable Korean frequency bundle builder tests."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from typing import Any

import pytest

from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanFrequencyBuildPolicy,
    KoreanFrequencyEntry,
    KoreanFrequencyRetrievalResult,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
    raw_bytes_sha256,
)


_LANDING_HASH = "a" * 64
_ATTACHMENT_HASH = "b" * 64
_BUNDLE_VERSION = "fixture-v1"


def _fingerprint() -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version="0.23.2",
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def _entry(rank: int, source_hash: str) -> dict[str, Any]:
    lemma = f"어휘{rank}"
    identity = KoreanLexicalIdentity(
        submitted_form=lemma,
        canonical_nfc=lemma,
        lemma=lemma,
        part_of_speech="NNG",
        sense_id=f"nikl:{rank}",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form=lemma, pos="NNG"),),
        analyzer_fingerprint=_fingerprint(),
        status="resolved",
    )
    return KoreanFrequencyEntry(
        language="ko",
        version=_BUNDLE_VERSION,
        level=((rank - 1) // 1000) + 1,
        final_rank=rank,
        source_rank=rank,
        source_provenance="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        license_decision="approved-local-use",
        storage_disposition="private-local-only",
        curation_decision="accepted",
        curation_flags=("source_rank_preserved", "modernity_review_required"),
        grounding_confidence="source-backed",
        bundle_sha256=source_hash,
        retrieval_sha256=source_hash,
        analyzer_fingerprint=_fingerprint(),
        lexical_identity=identity,
    ).model_dump(mode="json")


def _fixture_inputs(tmp_path: Path) -> dict[str, Any]:
    source_text = "".join(
        f"{rank}\t어휘{rank}\tNNG\tfixture gloss\n"
        for rank in range(1, 5966)
    )
    source_bytes = source_text.encode("utf-8")
    source_file = tmp_path / "source.txt"
    source_file.write_bytes(source_bytes)
    source_hash = raw_bytes_sha256(source_bytes)
    retrieval = KoreanFrequencyRetrievalResult(
        source_id="nikl-korean-learners-vocabulary",
        landing_url="https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70",
        accepted_filename="한국어 학습용 어휘 목록.txt",
        landing_sha256=_LANDING_HASH,
        attachment_url="https://www.korean.go.kr/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1",
        attachment_sha256=_ATTACHMENT_HASH,
        source_bytes_sha256=source_hash,
        source_byte_count=len(source_bytes),
        retrieved_at="2026-08-28T00:00:00Z",
        text_encoding="utf-8",
        schema_version="nikl-frequency-retrieval-v1",
    )
    retrieval_file = tmp_path / "retrieval-result.json"
    retrieval_file.write_text(retrieval.model_dump_json(), encoding="utf-8")
    policy = KoreanFrequencyBuildPolicy(
        source_id="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        allowed_use="local-generation",
        redistribution="not-approved",
        attribution_required=True,
        storage_disposition="private-local-only",
        retrieval_sha256=source_hash,
        source_bytes_sha256=source_hash,
        analyzer_fingerprint=_fingerprint(),
    )
    policy_file = tmp_path / "policy.json"
    policy_file.write_text(policy.model_dump_json(), encoding="utf-8")
    return {
        "retrieval_result_file": retrieval_file,
        "source_file": source_file,
        "policy_file": policy_file,
        "inventory_rows": [_entry(rank, source_hash) for rank in range(1, 3001)],
        "rejection_rows": [
            {
                "source_rank": rank,
                "source_form_sha256": raw_bytes_sha256(f"어휘{rank}".encode("utf-8")),
                "reason_code": "modernity_review_required",
            }
            for rank in range(3001, 5966)
        ],
        "attribution_text": "Synthetic local-use fixture attributed to NIKL test data.",
        "curation_report": {
            "accepted_count": 3000,
            "rejection_count": 2965,
            "level_counts": {"1": 1000, "2": 1000, "3": 1000},
        },
        "version": _BUNDLE_VERSION,
    }


def _build(tmp_path: Path, **overrides: Any):
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "build_frequency_assets.py"
    spec = importlib.util.spec_from_file_location("build_frequency_assets", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build_korean_frequency_assets = module.build_korean_frequency_assets

    kwargs = _fixture_inputs(tmp_path)
    kwargs.update(overrides)
    return build_korean_frequency_assets(**kwargs)


def test_staging_fsync_atomic_rename_creates_inactive_bundle(tmp_path: Path) -> None:
    target_root = tmp_path / "bundles"
    fsync_calls: list[int] = []

    result = _build(
        tmp_path,
        target_root=target_root,
        fsync=lambda descriptor: fsync_calls.append(descriptor),
    )

    bundle_dir = target_root / _BUNDLE_VERSION
    assert result.active is False
    assert result.accepted_count == 3000
    assert result.rejection_count == 2965
    assert (bundle_dir / "manifest.json").is_file()
    assert (bundle_dir / "build-result.json").is_file()
    assert (bundle_dir / "curated-inventory.jsonl").is_file()
    assert not list(target_root.glob(".staging-*"))
    assert fsync_calls


def test_interruption_rolls_back_owned_staging_and_preserves_neighbors(
    tmp_path: Path,
) -> None:
    target_root = tmp_path / "bundles"
    target_root.mkdir()
    neighbor = target_root / "keep.txt"
    neighbor.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError):
        _build(
            tmp_path,
            target_root=target_root,
            failure_injector=lambda boundary, _path: boundary == "after-member:curated-inventory",
        )

    assert neighbor.read_text(encoding="utf-8") == "keep"
    assert sorted(path.name for path in target_root.iterdir()) == ["keep.txt"]


def test_collision_rejects_partial_existing_target_without_overwrite(
    tmp_path: Path,
) -> None:
    target_root = tmp_path / "bundles"
    target = target_root / _BUNDLE_VERSION
    target.mkdir(parents=True)
    marker = target / "build-result.json"
    marker.write_text("partial", encoding="utf-8")

    with pytest.raises(ValueError):
        _build(tmp_path, target_root=target_root)

    assert marker.read_text(encoding="utf-8") == "partial"


def test_idempotent_exact_existing_target_returns_without_timestamp_drift(
    tmp_path: Path,
) -> None:
    target_root = tmp_path / "bundles"

    first = _build(tmp_path, target_root=target_root)
    before = {
        path.relative_to(target_root).as_posix(): path.stat().st_mtime_ns
        for path in (target_root / _BUNDLE_VERSION).iterdir()
    }
    second = _build(tmp_path, target_root=target_root)

    assert second == first
    assert before == {
        path.relative_to(target_root).as_posix(): path.stat().st_mtime_ns
        for path in (target_root / _BUNDLE_VERSION).iterdir()
    }
