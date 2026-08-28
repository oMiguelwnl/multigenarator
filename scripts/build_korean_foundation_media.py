#!/usr/bin/env python3
"""Build and validate Phase 31 Korean foundation media evidence."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Final

from multilang.services.korean_foundation_media import (
    load_pending_korean_foundation_media_manifest,
)


_PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
_PHASE_RELPATH: Final = Path(
    ".planning/phases/31-hangul-and-pronunciation-i-plus-1"
)
_MEDIA_RIGHTS_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "evidence-inbox" / "media-rights.json"
)
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_AUDIO_KINDS: Final = frozenset(
    {"audio", "letter_audio", "word_audio", "sentence_audio"}
)
_AZURE_DOC_URL: Final = (
    "https://learn.microsoft.com/en-us/azure/ai-services/"
    "speech-service/language-support?tabs=tts"
)
_AZURE_DOC_COMMIT: Final = "ebc37366082bd4d002282e679e4fc07099083d5b"
_VOICE_PROFILE_ID: Final = "ko-KR-SunHiNeural"
_VOICE_PROFILE_VERSION: Final = (
    "azure-docs-2026-08-13-ebc37366082bd4d002282e679e4fc07099083d5b"
)


class MediaRightsReasonCode(str, Enum):
    RIGHTS_MISSING = "rights_missing"
    RIGHTS_INVALID = "rights_invalid"
    RIGHTS_HASH_MISMATCH = "rights_hash_mismatch"
    RIGHTS_WRITE_FAILED = "rights_write_failed"
    UNSAFE_PATH = "unsafe_path"


class MediaRightsError(ValueError):
    def __init__(self, reason_code: MediaRightsReasonCode) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code.value)


def _raise(reason_code: MediaRightsReasonCode) -> None:
    raise MediaRightsError(reason_code)


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _json_file_bytes(payload: dict[str, object]) -> bytes:
    return _canonical_bytes(payload) + b"\n"


def _rights_content_hash(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_hash", None)
    return sha256(_canonical_bytes(unsigned)).hexdigest()


def _file_sha256(payload: dict[str, object]) -> str:
    return sha256(_json_file_bytes(payload)).hexdigest()


def _sha256_text(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        _raise(MediaRightsReasonCode.RIGHTS_INVALID)
    return value


def _is_link_or_reparse(value: os.stat_result) -> bool:
    if stat.S_ISLNK(value.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(value, "st_file_attributes", 0) & reparse_flag)


def _assert_safe_parent(path: Path) -> None:
    try:
        parts = path.parent.relative_to(_PROJECT_ROOT).parts
    except ValueError:
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    current = _PROJECT_ROOT
    for part in parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            current.mkdir(mode=0o700)
            metadata = current.lstat()
        except OSError as exc:
            raise MediaRightsError(MediaRightsReasonCode.UNSAFE_PATH) from exc
        if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
            _raise(MediaRightsReasonCode.UNSAFE_PATH)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    _assert_safe_parent(path)
    if path.is_symlink():
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    descriptor = -1
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(_json_file_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    except OSError as exc:
        raise MediaRightsError(MediaRightsReasonCode.RIGHTS_WRITE_FAILED) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _item_set() -> dict[str, object]:
    manifest = load_pending_korean_foundation_media_manifest()
    required_slots = [slot for slot in manifest.slots if slot.required]
    audio_slots = [slot for slot in required_slots if slot.media_kind in _AUDIO_KINDS]
    visual_slots = [slot for slot in required_slots if slot.media_kind not in _AUDIO_KINDS]
    slot_rows = [
        {
            "family": slot.family.value,
            "item_key": slot.item_key,
            "media_kind": slot.media_kind,
            "sequence": slot.sequence,
            "slot_id": slot.slot_id,
            "source_content_sha256": slot.source_content_sha256,
            "storage_relpath": slot.storage_relpath,
        }
        for slot in required_slots
    ]
    return {
        "manifest_version": manifest.manifest_version,
        "manifest_content_sha256": manifest.content_hash,
        "item_set_sha256": sha256(_canonical_bytes(slot_rows)).hexdigest(),
        "all_slots": len(manifest.slots),
        "required_slots": len(required_slots),
        "audio_subjects": len(audio_slots),
        "visual_subjects": len(visual_slots),
    }


def _rights_document() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "document_type": "phase31-media-rights-request",
        "phase": "31-hangul-and-pronunciation-i-plus-1",
        "status": "awaiting_project_owner_authorization",
        "rights_scope": {
            "visual_source": "local-deterministic-project-authored",
            "audio_source": "azure-speech-service-text-to-speech",
            "third_party_media_reuse": False,
            "redistribution_disposition": "requires_project_owner_authorization",
            "human_listening_claim": False,
        },
        "provider_scope": {
            "route": "azure-speech-tts",
            "provider_id": "azure-speech-service",
            "provider_api": "text-to-speech",
            "provider_doc_url": _AZURE_DOC_URL,
            "provider_doc_git_commit_id": _AZURE_DOC_COMMIT,
            "locale": "ko-KR",
            "voice_profile_id": _VOICE_PROFILE_ID,
            "voice_profile_version": _VOICE_PROFILE_VERSION,
            "output_format": "pcm_s16le_wav",
            "provider_attempt_ceiling": 72,
            "budget_ceiling_amount": "5.00",
            "budget_ceiling_currency": "USD",
            "credential_boundary": "existing-environment-only-no-secrets-recorded",
        },
        "item_set": _item_set(),
        "single_use_operation_id": "phase31-media-authority-v1",
        "replay_constraints": {
            "single_use": True,
            "authority_hash_must_match_file_sha256": True,
            "stale_or_replayed_authority_fails": True,
        },
        "blockers_until_authorized": [
            "no-project-owner-media-authority-recorded",
        ],
        "authority_prompt": "authorize-media {media-rights-file-sha256}",
        "decline_prompt": "decline: {reason}",
    }
    payload["content_hash"] = _rights_content_hash(payload)
    return payload


def prepare_rights() -> dict[str, object]:
    document = _rights_document()
    _atomic_write_json(_MEDIA_RIGHTS_PATH, document)
    return document


def _read_rights() -> dict[str, object]:
    try:
        metadata = _MEDIA_RIGHTS_PATH.lstat()
        if _is_link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
            _raise(MediaRightsReasonCode.UNSAFE_PATH)
        raw = _MEDIA_RIGHTS_PATH.read_bytes()
    except FileNotFoundError as exc:
        raise MediaRightsError(MediaRightsReasonCode.RIGHTS_MISSING) from exc
    except OSError as exc:
        raise MediaRightsError(MediaRightsReasonCode.RIGHTS_INVALID) from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise MediaRightsError(MediaRightsReasonCode.RIGHTS_INVALID) from exc
    if not isinstance(payload, dict) or raw != _json_file_bytes(payload):
        _raise(MediaRightsReasonCode.RIGHTS_INVALID)
    return payload


def validate_rights() -> str:
    document = _read_rights()
    expected = _rights_document()
    for key in (
        "schema_version",
        "document_type",
        "phase",
        "status",
        "rights_scope",
        "provider_scope",
        "item_set",
        "single_use_operation_id",
        "replay_constraints",
        "blockers_until_authorized",
        "decline_prompt",
    ):
        if document.get(key) != expected[key]:
            _raise(MediaRightsReasonCode.RIGHTS_INVALID)
    content_hash = _sha256_text(document.get("content_hash"))
    if content_hash != _rights_content_hash(document):
        _raise(MediaRightsReasonCode.RIGHTS_HASH_MISMATCH)
    if document.get("authority_prompt") != "authorize-media {media-rights-file-sha256}":
        _raise(MediaRightsReasonCode.RIGHTS_INVALID)
    return _file_sha256(document)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("prepare-rights")
    commands.add_parser("validate-rights")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.operation == "prepare-rights":
            prepare_rights()
            print(validate_rights())
        else:
            print(validate_rights())
    except MediaRightsError as exc:
        print(exc.reason_code.value, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
