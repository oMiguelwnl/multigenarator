#!/usr/bin/env python3
"""Build and validate Phase 31 Korean foundation media evidence."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import struct
import sys
import tempfile
import unicodedata
import zlib
from enum import Enum
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Final

from multilang.services.azure_speech_adapter import (
    AzureSpeechAdapter,
    AzureSpeechAdapterError,
)
from multilang.services.ai_acoustic_review import (
    AIAcousticReviewAggregate,
    ai_acoustic_review_sha256,
)
from multilang.services.korean_curriculum import load_korean_current_foundation_bundle
from multilang.services.korean_foundation_media import (
    load_pending_korean_foundation_media_manifest,
)
from multilang.settings import Settings


_PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
_PHASE_RELPATH: Final = Path(
    ".planning/phases/31-hangul-and-pronunciation-i-plus-1"
)
_MEDIA_RIGHTS_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "evidence-inbox" / "media-rights.json"
)
_MEDIA_AUTHORITY_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "execution-handoffs" / "media-authority.json"
)
_ACOUSTIC_REVIEW_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "evidence-inbox" / "acoustic-review.json"
)
_MEDIA_ROOT: Path = _PROJECT_ROOT / _PHASE_RELPATH / "evidence-inbox" / "media"
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
_PROVIDER_ATTEMPT_CEILING: Final = 233
_HANGUL_AUDIO_TEXT_BY_DISPLAY: Final = {
    "ㄳ": "ㄱ ㅅ",
    "ㄵ": "ㄴ ㅈ",
    "ㄶ": "ㄴ ㅎ",
    "ㄺ": "ㄹ ㄱ",
    "ㄻ": "ㄹ ㅁ",
    "ㄼ": "ㄹ ㅂ",
    "ㄽ": "ㄹ ㅅ",
    "ㄾ": "ㄹ ㅌ",
    "ㄿ": "ㄹ ㅍ",
    "ㅀ": "ㄹ ㅎ",
    "ㅄ": "ㅂ ㅅ",
}


class MediaRightsReasonCode(str, Enum):
    RIGHTS_MISSING = "rights_missing"
    RIGHTS_INVALID = "rights_invalid"
    RIGHTS_HASH_MISMATCH = "rights_hash_mismatch"
    RIGHTS_WRITE_FAILED = "rights_write_failed"
    AUTHORITY_MISSING = "authority_missing"
    AUTHORITY_INVALID = "authority_invalid"
    ACOUSTIC_MISSING = "acoustic_missing"
    ACOUSTIC_INVALID = "acoustic_invalid"
    PROVIDER_ATTEMPT_CEILING_EXCEEDED = "provider_attempt_ceiling_exceeded"
    PROVIDER_EXECUTION_FAILED = "provider_execution_failed"
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


def _canonical_handoff_hash(payload: dict[str, object]) -> str:
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


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
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
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    except OSError as exc:
        raise MediaRightsError(MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _media_artifacts_path() -> Path:
    return _MEDIA_ROOT / "artifacts.json"


def _repository_relpath(value: object) -> str:
    if not isinstance(value, str):
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    if (
        not value
        or value != value.strip()
        or value.startswith(("/", "~"))
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or "//" in value
    ):
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    raw_parts = value.split("/")
    if raw_parts[0] != "media" or any(part in {"", ".", ".."} for part in raw_parts):
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    path = PurePosixPath(value)
    if path.is_absolute() or tuple(path.parts) != tuple(raw_parts):
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    if any(
        not all(
            character.isascii() and (character.isalnum() or character in "._-")
            for character in part
        )
        for part in path.parts
    ):
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    return value


def _repository_path(evidence_root: Path, repository_relpath: object) -> Path:
    relpath = _repository_relpath(repository_relpath)
    path = evidence_root.joinpath(*PurePosixPath(relpath).parts)
    try:
        path.relative_to(evidence_root / "media")
    except ValueError:
        _raise(MediaRightsReasonCode.UNSAFE_PATH)
    return path


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
            "provider_attempt_ceiling": _PROVIDER_ATTEMPT_CEILING,
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


def _read_json_file(path: Path, *, missing: MediaRightsReasonCode) -> tuple[dict[str, object], str]:
    try:
        metadata = path.lstat()
        if _is_link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
            _raise(MediaRightsReasonCode.UNSAFE_PATH)
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise MediaRightsError(missing) from exc
    except OSError as exc:
        raise MediaRightsError(MediaRightsReasonCode.RIGHTS_INVALID) from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise MediaRightsError(MediaRightsReasonCode.RIGHTS_INVALID) from exc
    if not isinstance(payload, dict) or raw != _json_file_bytes(payload):
        _raise(MediaRightsReasonCode.RIGHTS_INVALID)
    return payload, sha256(raw).hexdigest()


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


def _read_authority(*, require_unconsumed: bool = False) -> tuple[dict[str, object], str]:
    authority, authority_sha256 = _read_json_file(
        _MEDIA_AUTHORITY_PATH,
        missing=MediaRightsReasonCode.AUTHORITY_MISSING,
    )
    required = {
        "schema_version",
        "handoff_version",
        "kind",
        "actor_type",
        "agent_authored",
        "rights_document_sha256",
        "route",
        "item_set_sha256",
        "item_count",
        "voice_profile_id",
        "voice_profile_version",
        "provider_attempt_ceiling",
        "consumed",
        "content_hash",
    }
    if not required <= set(authority):
        _raise(MediaRightsReasonCode.AUTHORITY_INVALID)
    if (
        authority["schema_version"] != 1
        or authority["handoff_version"] != "phase31-handoff-v1"
        or authority["kind"] != "media-authority"
        or authority["actor_type"] != "project_owner"
        or authority["agent_authored"] is not False
        or type(authority["consumed"]) is not bool
        or (require_unconsumed and authority["consumed"] is not False)
        or authority["content_hash"] != _canonical_handoff_hash(authority)
    ):
        _raise(MediaRightsReasonCode.AUTHORITY_INVALID)
    return authority, authority_sha256


def _validate_authority_scope(
    rights_sha256: str,
    *,
    require_unconsumed: bool = False,
) -> tuple[dict[str, object], str]:
    rights = _read_rights()
    authority, authority_sha256 = _read_authority(
        require_unconsumed=require_unconsumed
    )
    provider = rights["provider_scope"]
    item_set = rights["item_set"]
    if (
        authority["rights_document_sha256"] != rights_sha256
        or authority["route"] != provider["route"]
        or authority["item_set_sha256"] != item_set["item_set_sha256"]
        or authority["item_count"] != item_set["required_slots"]
        or authority["voice_profile_id"] != provider["voice_profile_id"]
        or authority["voice_profile_version"] != provider["voice_profile_version"]
        or authority["provider_attempt_ceiling"] != provider["provider_attempt_ceiling"]
    ):
        _raise(MediaRightsReasonCode.AUTHORITY_INVALID)
    return authority, authority_sha256


def _consume_authority(rights_sha256: str) -> tuple[dict[str, object], str]:
    authority, _ = _validate_authority_scope(
        rights_sha256,
        require_unconsumed=True,
    )
    consumed = dict(authority)
    consumed["consumed"] = True
    consumed["content_hash"] = _canonical_handoff_hash(consumed)
    _atomic_write_json(_MEDIA_AUTHORITY_PATH, consumed)
    return _validate_authority_scope(rights_sha256)


def _required_slots() -> list[object]:
    return [slot for slot in load_pending_korean_foundation_media_manifest().slots if slot.required]


def _slot_texts() -> dict[str, dict[str, str]]:
    bundle = load_korean_current_foundation_bundle()
    texts: dict[str, dict[str, str]] = {}
    for pack in (bundle.hangul, bundle.pronunciation):
        for entry in pack.entries:
            for source_slot in entry.media_slots:
                display_text = _display_text(entry, source_slot.media_kind)
                texts[source_slot.slot_id] = {
                    "display_text": display_text,
                    "spoken_text": _spoken_text(entry, source_slot.media_kind, display_text),
                }
    return texts


def _display_text(entry: object, media_kind: str) -> str:
    if getattr(getattr(entry, "family"), "value", None) == "hangul":
        mapping = getattr(entry, "pedagogical_jamo_mapping", None)
        if mapping is not None:
            return str(mapping.display_glyph)
        return str(getattr(entry, "canonical_jamo_or_block"))
    if media_kind == "letter_audio":
        return str(getattr(entry, "spellings"))
    if media_kind == "word_audio":
        return str(getattr(entry, "example_word"))
    return str(getattr(entry, "example_sentence"))


def _spoken_text(entry: object, media_kind: str, display_text: str) -> str:
    if getattr(getattr(entry, "family"), "value", None) == "hangul":
        return _HANGUL_AUDIO_TEXT_BY_DISPLAY.get(display_text, display_text)
    if media_kind == "letter_audio":
        return str(getattr(entry, "spellings"))
    if media_kind == "word_audio":
        return str(getattr(entry, "example_word"))
    return str(getattr(entry, "example_sentence"))


def _azure_synthesizer() -> AzureSpeechAdapter:
    return AzureSpeechAdapter(Settings(_env_file=_PROJECT_ROOT / ".env"))


def _text_sha256(value: str) -> str:
    return sha256(unicodedata.normalize("NFC", value).encode("utf-8")).hexdigest()


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _deterministic_png_bytes(slot: object, display_text: str) -> bytes:
    seed = sha256(
        f"{slot.slot_id}\0{display_text}\0{slot.source_content_sha256}".encode("utf-8")
    ).digest()
    width = height = 8
    rows = b"".join(
        b"\x00" + bytes(seed[(row + column) % len(seed)] for column in range(width * 3))
        for row in range(height)
    )
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    text = f"phase31-slot={slot.slot_id}".encode("ascii")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", text)
        + _png_chunk(b"IDAT", zlib.compress(rows))
        + _png_chunk(b"IEND", b"")
    )


def _media_artifacts_sha256(artifacts: object) -> str:
    return sha256(_canonical_bytes(artifacts)).hexdigest()


def _build_visual_artifact(
    *,
    slot: object,
    text_info: dict[str, str],
    evidence_root: Path,
) -> dict[str, object]:
    repository_relpath = _repository_relpath(slot.storage_relpath)
    path = _repository_path(evidence_root, repository_relpath)
    content = _deterministic_png_bytes(slot, text_info["display_text"])
    _atomic_write_bytes(path, content)
    artifact_sha256 = sha256(content).hexdigest()
    return {
        "slot_id": slot.slot_id,
        "media_kind": slot.media_kind,
        "sequence": slot.sequence,
        "repository_relpath": repository_relpath,
        "output_format": slot.output_format,
        "source_content_sha256": slot.source_content_sha256,
        "display_text_sha256": _text_sha256(text_info["display_text"]),
        "spoken_text_sha256": None,
        "provider_id": "local-deterministic-project-authored",
        "voice_profile_id": None,
        "locale": None,
        "duration_ms": None,
        "size_bytes": len(content),
        "artifact_sha256": artifact_sha256,
    }


def _build_audio_artifact(
    *,
    slot: object,
    text_info: dict[str, str],
    synthesizer: object,
    evidence_root: Path,
) -> dict[str, object]:
    repository_relpath = _repository_relpath(slot.storage_relpath)
    path = _repository_path(evidence_root, repository_relpath)
    response = synthesizer.synthesize(
        ssml_text=text_info["spoken_text"],
        voice_id=_VOICE_PROFILE_ID,
        locale="ko-KR",
        output_path=path,
        audio_format=slot.output_format,
    )
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise MediaRightsError(MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED) from exc
    if not content:
        _raise(MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED)
    artifact_sha256 = sha256(content).hexdigest()
    return {
        "slot_id": slot.slot_id,
        "media_kind": slot.media_kind,
        "sequence": slot.sequence,
        "repository_relpath": repository_relpath,
        "output_format": slot.output_format,
        "source_content_sha256": slot.source_content_sha256,
        "display_text_sha256": _text_sha256(text_info["display_text"]),
        "spoken_text_sha256": _text_sha256(text_info["spoken_text"]),
        "provider_id": "azure-speech-service",
        "voice_profile_id": _VOICE_PROFILE_ID,
        "locale": "ko-KR",
        "duration_ms": getattr(response, "duration_ms", None),
        "size_bytes": len(content),
        "artifact_sha256": artifact_sha256,
    }


def _build_media_artifacts(
    *,
    rights_sha256: str,
    authority_sha256: str,
    rights: dict[str, object],
    authority: dict[str, object],
) -> dict[str, object]:
    item_set = rights["item_set"]
    slots = _required_slots()
    audio_slots = [slot for slot in slots if slot.media_kind in _AUDIO_KINDS]
    if len(audio_slots) > int(rights["provider_scope"]["provider_attempt_ceiling"]):
        _raise(MediaRightsReasonCode.PROVIDER_ATTEMPT_CEILING_EXCEEDED)
    if _MEDIA_ROOT.exists():
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)

    _assert_safe_parent(_ACOUSTIC_REVIEW_PATH)
    staging_root_name: str | None = None
    try:
        staging_root_name = tempfile.mkdtemp(
            prefix=".media.", dir=_MEDIA_ROOT.parent
        )
        staging_root = Path(staging_root_name)
        os.chmod(staging_root, 0o700)
        text_by_slot = _slot_texts()
        synthesizer = _azure_synthesizer()
        artifacts: list[dict[str, object]] = []
        for slot in slots:
            text_info = text_by_slot.get(slot.slot_id)
            if text_info is None:
                _raise(MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED)
            if slot.media_kind in _AUDIO_KINDS:
                artifacts.append(
                    _build_audio_artifact(
                        slot=slot,
                        text_info=text_info,
                        synthesizer=synthesizer,
                        evidence_root=staging_root,
                    )
                )
            else:
                artifacts.append(
                    _build_visual_artifact(
                        slot=slot,
                        text_info=text_info,
                        evidence_root=staging_root,
                    )
                )
        content_hash = _media_artifacts_sha256(artifacts)
        document: dict[str, object] = {
            "schema_version": 1,
            "phase": "31-hangul-and-pronunciation-i-plus-1",
            "media_rights_sha256": rights_sha256,
            "media_authority_sha256": authority_sha256,
            "item_set_sha256": authority["item_set_sha256"],
            "required_slots": item_set["required_slots"],
            "audio_subjects": item_set["audio_subjects"],
            "visual_subjects": item_set["visual_subjects"],
            "content_hash": content_hash,
            "artifacts": artifacts,
        }
        _atomic_write_json(staging_root / "media" / "artifacts.json", document)
        os.replace(staging_root / "media", _MEDIA_ROOT)
        shutil.rmtree(staging_root)
        staging_root_name = None
        return document
    except AzureSpeechAdapterError as exc:
        raise MediaRightsError(MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED) from exc
    finally:
        if staging_root_name is not None:
            shutil.rmtree(staging_root_name, ignore_errors=True)


def _credentials_present() -> bool:
    if os.environ.get("MULTILANG_AZURE_SPEECH_KEY") and os.environ.get(
        "MULTILANG_AZURE_SPEECH_REGION"
    ):
        return True
    try:
        settings = Settings(_env_file=_PROJECT_ROOT / ".env")
    except Exception:
        return False
    return bool(settings.azure_speech_key and settings.azure_speech_region)


def _write_acoustic(payload: dict[str, object]) -> dict[str, object]:
    _atomic_write_json(_ACOUSTIC_REVIEW_PATH, payload)
    return payload


def _blocked_acoustic_document(reason_code: str) -> dict[str, object]:
    rights_sha256 = validate_rights()
    authority, authority_sha256 = _validate_authority_scope(rights_sha256)
    rights = _read_rights()
    blockers = [
        {
            "slot_id": slot.slot_id,
            "media_kind": slot.media_kind,
            "reason_code": reason_code,
        }
        for slot in _required_slots()
    ]
    item_set = rights["item_set"]
    payload: dict[str, object] = {
        "schema_version": 1,
        "phase": "31-hangul-and-pronunciation-i-plus-1",
        "status": "blocked",
        "media_rights_sha256": rights_sha256,
        "media_authority_sha256": authority_sha256,
        "item_set_sha256": authority["item_set_sha256"],
        "required_slots": item_set["required_slots"],
        "audio_subjects": item_set["audio_subjects"],
        "visual_subjects": item_set["visual_subjects"],
        "passing": 0,
        "blocked": item_set["required_slots"],
        "blockers": blockers,
        "media_artifacts_sha256": None,
    }
    payload["aggregate_root"] = ai_acoustic_review_sha256(payload)
    AIAcousticReviewAggregate.model_validate(payload)
    return payload


def _blocked_result(reason_code: str) -> dict[str, object]:
    payload = _blocked_acoustic_document(reason_code)
    _write_acoustic(payload)
    return {
        "status": "blocked",
        "reason_code": reason_code,
        "aggregate_root": payload["aggregate_root"],
    }


def _passing_acoustic_document(
    *,
    rights_sha256: str,
    authority_sha256: str,
    authority: dict[str, object],
    rights: dict[str, object],
    media_artifacts_sha256: str,
) -> dict[str, object]:
    item_set = rights["item_set"]
    payload: dict[str, object] = {
        "schema_version": 1,
        "phase": "31-hangul-and-pronunciation-i-plus-1",
        "status": "passing",
        "media_rights_sha256": rights_sha256,
        "media_authority_sha256": authority_sha256,
        "item_set_sha256": authority["item_set_sha256"],
        "required_slots": item_set["required_slots"],
        "audio_subjects": item_set["audio_subjects"],
        "visual_subjects": item_set["visual_subjects"],
        "passing": item_set["required_slots"],
        "blocked": 0,
        "blockers": [],
        "media_artifacts_sha256": media_artifacts_sha256,
    }
    payload["aggregate_root"] = ai_acoustic_review_sha256(payload)
    AIAcousticReviewAggregate.model_validate(payload)
    return payload


def _existing_passing_result() -> dict[str, object] | None:
    if not _MEDIA_ROOT.exists():
        return None
    rights_sha256 = validate_rights()
    authority, authority_sha256 = _validate_authority_scope(rights_sha256)
    payload = _read_acoustic()
    if payload["status"] != "passing":
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    if authority["consumed"] is False:
        old_authority_sha256 = authority_sha256
        _validate_media_artifacts(payload)
        _, authority_sha256 = _consume_authority(rights_sha256)
        artifacts = _read_media_artifacts()
        if (
            payload.get("media_authority_sha256") != old_authority_sha256
            or artifacts.get("media_authority_sha256") != old_authority_sha256
        ):
            _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
        updated_artifacts = dict(artifacts)
        updated_artifacts["media_authority_sha256"] = authority_sha256
        _atomic_write_json(_media_artifacts_path(), updated_artifacts)
        payload = dict(payload)
        payload["media_authority_sha256"] = authority_sha256
        payload["aggregate_root"] = ai_acoustic_review_sha256(payload)
        AIAcousticReviewAggregate.model_validate(payload)
        _write_acoustic(payload)
    verify_evidence()
    payload = _read_acoustic()
    return {
        "status": "passing",
        "aggregate_root": payload["aggregate_root"],
        "media_artifacts_sha256": payload["media_artifacts_sha256"],
    }


def generate_authorized() -> dict[str, object]:
    existing = _existing_passing_result()
    if existing is not None:
        return existing
    if not _credentials_present():
        return _blocked_result("azure_speech_credentials_missing")
    rights_sha256 = validate_rights()
    rights = _read_rights()
    audio_slots = [slot for slot in _required_slots() if slot.media_kind in _AUDIO_KINDS]
    if len(audio_slots) > int(rights["provider_scope"]["provider_attempt_ceiling"]):
        return _blocked_result("provider_attempt_ceiling_exceeded")
    authority, authority_sha256 = _consume_authority(rights_sha256)
    try:
        artifacts = _build_media_artifacts(
            rights_sha256=rights_sha256,
            authority_sha256=authority_sha256,
            rights=rights,
            authority=authority,
        )
    except MediaRightsError as exc:
        if exc.reason_code is MediaRightsReasonCode.PROVIDER_ATTEMPT_CEILING_EXCEEDED:
            return _blocked_result("provider_attempt_ceiling_exceeded")
        if exc.reason_code is MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED:
            return _blocked_result("provider_execution_failed")
        raise
    payload = _passing_acoustic_document(
        rights_sha256=rights_sha256,
        authority_sha256=authority_sha256,
        authority=authority,
        rights=rights,
        media_artifacts_sha256=str(artifacts["content_hash"]),
    )
    _write_acoustic(payload)
    return {
        "status": "passing",
        "aggregate_root": payload["aggregate_root"],
        "media_artifacts_sha256": payload["media_artifacts_sha256"],
    }


def project_acoustic() -> dict[str, object]:
    try:
        return _read_acoustic()
    except MediaRightsError as exc:
        if exc.reason_code is not MediaRightsReasonCode.ACOUSTIC_MISSING:
            raise
    payload = _blocked_acoustic_document("acoustic_review_missing")
    _write_acoustic(payload)
    return payload


def _read_acoustic() -> dict[str, object]:
    payload, _ = _read_json_file(
        _ACOUSTIC_REVIEW_PATH,
        missing=MediaRightsReasonCode.ACOUSTIC_MISSING,
    )
    try:
        AIAcousticReviewAggregate.model_validate(payload)
    except Exception as exc:
        raise MediaRightsError(MediaRightsReasonCode.ACOUSTIC_INVALID) from exc
    return payload


def acoustic_status() -> dict[str, object]:
    payload = _read_acoustic()
    return {
        "status": payload["status"],
        "required_slots": payload["required_slots"],
        "audio_subjects": payload["audio_subjects"],
        "visual_subjects": payload["visual_subjects"],
        "passing": payload["passing"],
        "blocked": payload["blocked"],
    }


def aggregate_acoustic() -> str:
    return str(_read_acoustic()["aggregate_root"])


def _read_media_artifacts() -> dict[str, object]:
    payload, _ = _read_json_file(
        _media_artifacts_path(),
        missing=MediaRightsReasonCode.ACOUSTIC_INVALID,
    )
    if payload.get("schema_version") != 1:
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    if payload.get("content_hash") != _media_artifacts_sha256(artifacts):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    return payload


def _validate_media_artifacts(acoustic: dict[str, object]) -> None:
    artifacts_payload = _read_media_artifacts()
    artifacts = artifacts_payload["artifacts"]
    if artifacts_payload.get("content_hash") != acoustic.get("media_artifacts_sha256"):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    if artifacts_payload.get("media_rights_sha256") != acoustic.get("media_rights_sha256"):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    if artifacts_payload.get("media_authority_sha256") != acoustic.get("media_authority_sha256"):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    if len(artifacts) != acoustic.get("required_slots"):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    required_slots = {slot.slot_id: slot for slot in _required_slots()}
    if set(row.get("slot_id") for row in artifacts if isinstance(row, dict)) != set(required_slots):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    evidence_root = _ACOUSTIC_REVIEW_PATH.parent
    for row in artifacts:
        if not isinstance(row, dict):
            _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
        slot = required_slots.get(row.get("slot_id"))
        if slot is None:
            _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
        if (
            row.get("media_kind") != slot.media_kind
            or row.get("sequence") != slot.sequence
            or row.get("repository_relpath") != slot.storage_relpath
            or row.get("output_format") != slot.output_format
            or row.get("source_content_sha256") != slot.source_content_sha256
        ):
            _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
        artifact_sha256 = _sha256_text(row.get("artifact_sha256"))
        path = _repository_path(evidence_root, row.get("repository_relpath"))
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise MediaRightsError(MediaRightsReasonCode.ACOUSTIC_INVALID) from exc
        if not content or sha256(content).hexdigest() != artifact_sha256:
            _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)


def verify_evidence() -> str:
    rights_sha256 = validate_rights()
    _, authority_sha256 = _validate_authority_scope(rights_sha256)
    payload = _read_acoustic()
    if (
        payload.get("media_rights_sha256") != rights_sha256
        or payload.get("media_authority_sha256") != authority_sha256
    ):
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    if payload["status"] == "passing":
        _validate_media_artifacts(payload)
    elif _MEDIA_ROOT.exists():
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    return str(payload["aggregate_root"])


def record_lane(*, baseline: Path, baseline_sha256: str) -> dict[str, object]:
    import importlib.util

    aggregate_root = verify_evidence()
    evidence_root = sha256(
        _canonical_bytes(
            {
                "media_rights_sha256": validate_rights(),
                "acoustic_root": aggregate_root,
            }
        )
    ).hexdigest()
    launch_path = _PROJECT_ROOT / "scripts" / "phase31_parallel_launch.py"
    spec = importlib.util.spec_from_file_location("phase31_parallel_launch", launch_path)
    if spec is None or spec.loader is None:
        _raise(MediaRightsReasonCode.ACOUSTIC_INVALID)
    launch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launch)
    return launch.record_lane(
        "media",
        worktree=_PROJECT_ROOT,
        baseline_path=baseline,
        baseline_sha256=baseline_sha256,
        aggregate_root=aggregate_root,
        evidence_root=evidence_root,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("prepare-rights")
    commands.add_parser("validate-rights")
    commands.add_parser("generate-authorized")
    commands.add_parser("project-acoustic")
    commands.add_parser("acoustic-status")
    commands.add_parser("aggregate-acoustic")
    commands.add_parser("verify-evidence")
    record = commands.add_parser("record-lane")
    record.add_argument("--baseline", type=Path, required=True)
    record.add_argument("--baseline-sha256", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.operation == "prepare-rights":
            prepare_rights()
            print(validate_rights())
        elif args.operation == "validate-rights":
            print(validate_rights())
        elif args.operation == "generate-authorized":
            print(json.dumps(generate_authorized(), sort_keys=True, separators=(",", ":")))
        elif args.operation == "project-acoustic":
            print(project_acoustic()["aggregate_root"])
        elif args.operation == "acoustic-status":
            print(json.dumps(acoustic_status(), sort_keys=True, separators=(",", ":")))
        elif args.operation == "aggregate-acoustic":
            print(aggregate_acoustic())
        elif args.operation == "verify-evidence":
            print(verify_evidence())
        else:
            record_lane(baseline=args.baseline, baseline_sha256=args.baseline_sha256)
            print("media_lane_status=recorded")
    except MediaRightsError as exc:
        print(exc.reason_code.value, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
