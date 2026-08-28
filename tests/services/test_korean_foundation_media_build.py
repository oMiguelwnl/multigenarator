from __future__ import annotations

import importlib.util
import json
from hashlib import sha256
from pathlib import Path
from types import ModuleType

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = PROJECT_ROOT / "scripts" / "build_korean_foundation_media.py"
PHASE_RELPATH = Path(".planning/phases/31-hangul-and-pronunciation-i-plus-1")


def _builder() -> ModuleType:
    assert BUILD_SCRIPT.is_file(), "the Phase 31 media build script must exist"
    spec = importlib.util.spec_from_file_location(
        "build_korean_foundation_media", BUILD_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_root(api: ModuleType, monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(api, "_PROJECT_ROOT", root)
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
    monkeypatch.setattr(
        api,
        "_ACOUSTIC_REVIEW_PATH",
        root / PHASE_RELPATH / "evidence-inbox" / "acoustic-review.json",
    )
    monkeypatch.setattr(
        api,
        "_MEDIA_ROOT",
        root / PHASE_RELPATH / "evidence-inbox" / "media",
    )


def _canonical_file_hash(payload: dict[str, object]) -> str:
    return sha256(
        (
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()


def test_prepare_rights_writes_hash_bound_current_v2_media_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)

    document = api.prepare_rights()
    stored = json.loads(
        (tmp_path / PHASE_RELPATH / "evidence-inbox" / "media-rights.json").read_text(
            encoding="utf-8"
        )
    )

    assert document == stored
    assert stored["status"] == "awaiting_project_owner_authorization"
    assert stored["provider_scope"]["route"] == "azure-speech-tts"
    assert stored["provider_scope"]["locale"] == "ko-KR"
    assert stored["provider_scope"]["voice_profile_id"] == "ko-KR-SunHiNeural"
    assert stored["provider_scope"]["provider_attempt_ceiling"] == 72
    assert stored["item_set"]["all_slots"] == 509
    assert stored["item_set"]["required_slots"] == 325
    assert stored["item_set"]["audio_subjects"] == 233
    assert stored["item_set"]["visual_subjects"] == 92
    assert stored["authority_prompt"] == "authorize-media {media-rights-file-sha256}"
    assert api.validate_rights() == _canonical_file_hash(stored)


def test_validate_rights_rejects_stale_counts_and_hash_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)
    document = api.prepare_rights()
    path = tmp_path / PHASE_RELPATH / "evidence-inbox" / "media-rights.json"

    changed = dict(document)
    changed["item_set"] = dict(document["item_set"])
    changed["item_set"]["audio_subjects"] = 232
    path.write_text(json.dumps(changed, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(api.MediaRightsError):
        api.validate_rights()

    drifted = dict(document)
    drifted["content_hash"] = "0" * 64
    path.write_text(json.dumps(drifted, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(api.MediaRightsError):
        api.validate_rights()


def _write_media_authority(api: ModuleType, root: Path, rights_sha256: str) -> None:
    rights = json.loads(
        (root / PHASE_RELPATH / "evidence-inbox" / "media-rights.json").read_text(
            encoding="utf-8"
        )
    )
    payload = {
        "schema_version": 1,
        "handoff_version": "phase31-handoff-v1",
        "kind": "media-authority",
        "actor_type": "project_owner",
        "agent_authored": False,
        "confirmation_method": "opencode-user-message",
        "exact_supplied_response": f"authorize-media {rights_sha256}",
        "supplied_response_sha256": sha256(
            f"authorize-media {rights_sha256}".encode("utf-8")
        ).hexdigest(),
        "orchestration_timestamp": "2026-08-28T00:00:00Z",
        "rights_document_sha256": rights_sha256,
        "route": rights["provider_scope"]["route"],
        "item_set_sha256": rights["item_set"]["item_set_sha256"],
        "item_count": rights["item_set"]["required_slots"],
        "voice_profile_id": rights["provider_scope"]["voice_profile_id"],
        "voice_profile_version": rights["provider_scope"]["voice_profile_version"],
        "provider_attempt_ceiling": rights["provider_scope"]["provider_attempt_ceiling"],
        "budget_ceiling_amount": rights["provider_scope"]["budget_ceiling_amount"],
        "budget_ceiling_currency": rights["provider_scope"]["budget_ceiling_currency"],
        "credential_boundary": rights["provider_scope"]["credential_boundary"],
        "single_use_operation_id": rights["single_use_operation_id"],
        "consumed": False,
        "replay_constraints": rights["replay_constraints"],
    }
    payload["content_hash"] = api._canonical_handoff_hash(payload)
    path = root / PHASE_RELPATH / "execution-handoffs" / "media-authority.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def test_generate_authorized_records_missing_credentials_without_media_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)
    monkeypatch.delenv("MULTILANG_AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("MULTILANG_AZURE_SPEECH_REGION", raising=False)
    api.prepare_rights()
    rights_sha256 = api.validate_rights()
    _write_media_authority(api, tmp_path, rights_sha256)

    result = api.generate_authorized()
    aggregate_root = api.verify_evidence()
    status = api.acoustic_status()

    assert result["status"] == "blocked"
    assert result["reason_code"] == "azure_speech_credentials_missing"
    assert status["blocked"] == 325
    assert status["passing"] == 0
    assert aggregate_root == result["aggregate_root"]
    assert not (tmp_path / PHASE_RELPATH / "evidence-inbox" / "media").exists()

    projected = api.project_acoustic()
    assert projected["aggregate_root"] == result["aggregate_root"]
    assert {blocker["reason_code"] for blocker in projected["blockers"]} == {
        "azure_speech_credentials_missing"
    }
