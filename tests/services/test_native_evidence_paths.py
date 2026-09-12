from hashlib import sha256
from pathlib import Path

import pytest


def test_korean_runtime_defaults_are_native_not_planning():
    from multilang.services import korean_foundation_ai_curation as curation
    from multilang.services import korean_foundation_evidence as evidence
    from multilang.services import korean_foundation_snapshot as snapshot
    from multilang.services import korean_foundation_snapshot_fallback as fallback

    for path in (
        snapshot._FIXED_PATHS.phase_dir,
        evidence.PHASE31_EVIDENCE_INBOX,
        curation.KOREAN_FOUNDATION_CURATION_DRAFT_ROOT,
        curation.KOREAN_FOUNDATION_EXECUTION_HANDOFF_ROOT,
        fallback._PHASE31_SUMMARY_FILE,
        fallback._PHASE31_VERIFICATION_REPORT_FILE,
    ):
        assert ".planning" not in Path(path).parts
        assert "evidence" in Path(path).parts


def test_explicit_legacy_evidence_import_is_hash_bound_and_preserves_original(tmp_path):
    from multilang.services.native_evidence_paths import (
        import_legacy_evidence,
        native_korean_evidence_relpath,
    )

    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "receipt.json").write_bytes(b'{"approved":true}')
    content_hash = sha256((legacy / "receipt.json").read_bytes()).hexdigest()
    target = tmp_path / "project"
    target.mkdir()
    with pytest.raises(ValueError, match="hash"):
        import_legacy_evidence(
            legacy_root=legacy,
            project_root=target,
            expected_files={"receipt.json": "a" * 64},
        )
    assert not (target / native_korean_evidence_relpath()).exists()
    report = import_legacy_evidence(
        legacy_root=legacy,
        project_root=target,
        expected_files={"receipt.json": content_hash},
    )
    assert report["file_count"] == 1
    assert (
        target / native_korean_evidence_relpath() / "receipt.json"
    ).read_bytes() == (legacy / "receipt.json").read_bytes()
    assert (
        import_legacy_evidence(
            legacy_root=legacy,
            project_root=target,
            expected_files={"receipt.json": content_hash},
        )
        == report
    )


def test_evidence_configuration_rejects_planning_escape_and_symlinks(
    tmp_path, monkeypatch
):
    from multilang.services.native_evidence_paths import native_korean_evidence_relpath

    for bad in ("../escape", "/absolute", ".planning/evidence"):
        monkeypatch.setenv("MULTILANG_KOREAN_EVIDENCE_ROOT", bad)
        with pytest.raises(ValueError):
            native_korean_evidence_relpath()


def test_approved_korean_fallback_works_without_reading_planning(monkeypatch):
    from multilang.services.korean_foundation_snapshot_fallback import (
        APPROVED_KOREAN_FOUNDATION_PHASE31_FALLBACK,
        verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
    )

    original_open = Path.open

    def native_only_open(path, *args, **kwargs):
        assert ".planning" not in path.parts, "runtime attempted to read planning state"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", native_only_open)
    result = verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
        expected_receipt_sha256=APPROVED_KOREAN_FOUNDATION_PHASE31_FALLBACK.receipt_sha256
    )
    assert (
        result.receipt_sha256
        == APPROVED_KOREAN_FOUNDATION_PHASE31_FALLBACK.receipt_sha256
    )


def test_native_evidence_inventory_supports_clean_checkout_without_empty_directories():
    from multilang.services.korean_foundation_evidence import (
        inspect_fixed_korean_foundation_evidence_inbox,
    )

    inventory = inspect_fixed_korean_foundation_evidence_inbox()
    assert inventory.complete is True
    assert inventory.declared_media_count == 325
