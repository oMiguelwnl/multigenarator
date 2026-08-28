from __future__ import annotations

import importlib.util
import json
from hashlib import sha256
from pathlib import Path
from types import ModuleType

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HANDOFF_SCRIPT = PROJECT_ROOT / "scripts" / "phase31_handoff.py"
PHASE_RELPATH = Path(".planning/phases/31-hangul-and-pronunciation-i-plus-1")


def _handoff() -> ModuleType:
    assert HANDOFF_SCRIPT.is_file(), "phase31 handoff script must exist"
    spec = importlib.util.spec_from_file_location("phase31_handoff", HANDOFF_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_hash(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_hash", None)
    return sha256(
        json.dumps(
            unsigned,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _write_manifest(project_root: Path, digest: str) -> None:
    path = project_root / PHASE_RELPATH / "curation-drafts" / "draft-manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "manifest_version": "korean-foundations-v2-draft",
                "draft_only": True,
                "review_status": "needs_review",
                "promotion_authority": False,
                "content_hash": digest,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_evidence_index(project_root: Path, payload: bytes = b"index\n") -> str:
    path = project_root / PHASE_RELPATH / "evidence-inbox" / "evidence-index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256(payload).hexdigest()


def _write_receipt(project_root: Path, payload: bytes = b"receipt\n") -> str:
    path = project_root / PHASE_RELPATH / "evidence-inbox" / "validation-receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256(payload).hexdigest()


def _install_root(api: ModuleType, monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(api, "_PROJECT_ROOT", root)
    monkeypatch.setattr(api, "_HANDOFF_ROOT", root / PHASE_RELPATH / "execution-handoffs")
    monkeypatch.setattr(
        api,
        "_DRAFT_MANIFEST_PATH",
        root / PHASE_RELPATH / "curation-drafts" / "draft-manifest.json",
    )
    monkeypatch.setattr(
        api,
        "_EVIDENCE_INDEX_PATH",
        root / PHASE_RELPATH / "evidence-inbox" / "evidence-index.json",
    )
    monkeypatch.setattr(
        api,
        "_RECEIPT_PATH",
        root / PHASE_RELPATH / "evidence-inbox" / "validation-receipt.json",
    )
    monkeypatch.setattr(
        api,
        "_MEDIA_RIGHTS_PATH",
        root / PHASE_RELPATH / "evidence-inbox" / "media-rights.json",
    )
    monkeypatch.setattr(
        api,
        "_MEDIA_AUTHORITY_PATH",
        root / PHASE_RELPATH / "execution-handoffs" / "media-authority.json",
    )


def _write_media_rights(project_root: Path) -> tuple[str, dict[str, object]]:
    rights = {
        "schema_version": 1,
        "document_type": "phase31-media-rights-request",
        "status": "awaiting_project_owner_authorization",
        "provider_scope": {
            "route": "azure-speech-tts",
            "locale": "ko-KR",
            "voice_profile_id": "ko-KR-SunHiNeural",
            "voice_profile_version": "azure-docs-2026-08-13-ebc37366082bd4d002282e679e4fc07099083d5b",
            "provider_attempt_ceiling": 72,
            "budget_ceiling_amount": "5.00",
            "budget_ceiling_currency": "USD",
            "credential_boundary": "existing-environment-only-no-secrets-recorded",
        },
        "item_set": {
            "item_set_sha256": "7" * 64,
            "required_slots": 325,
            "audio_subjects": 233,
            "visual_subjects": 92,
        },
        "single_use_operation_id": "phase31-media-authority-v1",
        "content_hash": "6" * 64,
    }
    path = project_root / PHASE_RELPATH / "evidence-inbox" / "media-rights.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(
        rights,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    path.write_bytes(raw)
    return sha256(raw).hexdigest(), rights


def test_fixed_handoff_contract_is_not_implemented(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _handoff()
    selected_hash = "8" * 64
    _install_root(api, monkeypatch, tmp_path)
    _write_manifest(tmp_path, selected_hash)

    handoff = api.record_selection(selected_hash)
    stored = json.loads(
        (tmp_path / PHASE_RELPATH / "execution-handoffs" / "curation-selection.json").read_text(
            encoding="utf-8"
        )
    )

    assert handoff["kind"] == "curation-selection"
    assert stored["schema_version"] == 1
    assert stored["selected_sha256"] == selected_hash
    assert stored["current_draft_manifest_sha256"] == selected_hash
    assert stored["content_hash"] == _canonical_hash(stored)
    assert api.get_selection() == selected_hash


def test_handoff_records_evidence_receipt_and_authorization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _handoff()
    _install_root(api, monkeypatch, tmp_path)
    index_sha256 = _write_evidence_index(tmp_path)
    receipt_sha256 = _write_receipt(tmp_path)
    authorization_sha256 = "2" * 64

    assert api.record_evidence(index_sha256)["confirmed_index_sha256"] == index_sha256
    assert api.get_evidence() == index_sha256
    assert api.get_receipt() == receipt_sha256
    assert (
        api.record_authorization(
            authorization_sha256,
            expected_receipt_sha256=receipt_sha256,
        )["authorization_sha256"]
        == authorization_sha256
    )
    assert api.get_authorization() == authorization_sha256


def test_handoff_records_project_owner_media_authority_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _handoff()
    _install_root(api, monkeypatch, tmp_path)
    rights_sha256, rights = _write_media_rights(tmp_path)
    response = f"authorize-media {rights_sha256}"

    authority = api.record_media_authority(
        response,
        confirmation_method="opencode-user-message",
        orchestration_timestamp="2026-08-28T00:00:00Z",
    )

    assert authority["actor_type"] == "project_owner"
    assert authority["agent_authored"] is False
    assert authority["rights_document_sha256"] == rights_sha256
    assert authority["route"] == rights["provider_scope"]["route"]
    assert authority["item_set_sha256"] == rights["item_set"]["item_set_sha256"]
    assert authority["item_count"] == rights["item_set"]["required_slots"]
    assert authority["voice_profile_id"] == "ko-KR-SunHiNeural"
    assert authority["provider_attempt_ceiling"] == 72
    assert authority["consumed"] is False
    assert api.get_media_authority() == rights_sha256
    api.verify_media_authority(
        require_project_owner=True,
        require_unconsumed=True,
        require_voice_profile=True,
        require_provider_attempt_ceiling=True,
    )


def test_media_authority_rejects_decline_stale_hash_and_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _handoff()
    _install_root(api, monkeypatch, tmp_path)
    rights_sha256, _ = _write_media_rights(tmp_path)

    with pytest.raises(api.Phase31HandoffError):
        api.record_media_authority(
            "decline: no budget",
            confirmation_method="opencode-user-message",
            orchestration_timestamp="2026-08-28T00:00:00Z",
        )
    with pytest.raises(api.Phase31HandoffError):
        api.record_media_authority(
            f"authorize-media {'0' * 64}",
            confirmation_method="opencode-user-message",
            orchestration_timestamp="2026-08-28T00:00:00Z",
        )

    api.record_media_authority(
        f"authorize-media {rights_sha256}",
        confirmation_method="opencode-user-message",
        orchestration_timestamp="2026-08-28T00:00:00Z",
    )
    with pytest.raises(api.Phase31HandoffError):
        api.record_media_authority(
            f"authorize-media {rights_sha256}",
            confirmation_method="opencode-user-message",
            orchestration_timestamp="2026-08-28T00:00:01Z",
        )


def test_handoff_rejects_malformed_hash_and_nonidentical_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _handoff()
    _install_root(api, monkeypatch, tmp_path)
    first_hash = "3" * 64
    second_hash = "4" * 64
    _write_manifest(tmp_path, first_hash)

    with pytest.raises(api.Phase31HandoffError):
        api.record_selection("not-a-sha")

    api.record_selection(first_hash)
    api.record_selection(first_hash)
    _write_manifest(tmp_path, second_hash)

    with pytest.raises(api.Phase31HandoffError):
        api.record_selection(second_hash)
    assert api.get_selection() == first_hash


def test_handoff_refuses_symlink_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _handoff()
    selected_hash = "5" * 64
    _install_root(api, monkeypatch, tmp_path)
    _write_manifest(tmp_path, selected_hash)
    handoff_root = tmp_path / PHASE_RELPATH / "execution-handoffs"
    handoff_root.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    target = handoff_root / "curation-selection.json"
    target.symlink_to(outside)

    with pytest.raises(api.Phase31HandoffError):
        api.record_selection(selected_hash)
    assert not outside.exists()


def test_handoff_cli_exposes_only_fixed_operations() -> None:
    api = _handoff()
    help_text = api.build_parser().format_help()

    for operation in (
        "record-selection",
        "get-selection",
        "record-evidence",
        "get-evidence",
        "get-receipt",
        "record-authorization",
        "get-authorization",
        "record-media-authority",
        "verify-media-authority",
        "get-media-authority",
    ):
        assert operation in help_text
    for forbidden_option in ("--root", "--path", "--output", "--force", "--repair"):
        assert forbidden_option not in help_text
