"""Fixed Phase 31 execution handoff helper."""

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


_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
_PHASE_RELPATH: Final = Path(
    ".planning/phases/31-hangul-and-pronunciation-i-plus-1"
)
_HANDOFF_ROOT: Path = _PROJECT_ROOT / _PHASE_RELPATH / "execution-handoffs"
_DRAFT_MANIFEST_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "curation-drafts" / "draft-manifest.json"
)
_EVIDENCE_INDEX_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "evidence-inbox" / "evidence-index.json"
)
_RECEIPT_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "evidence-inbox" / "validation-receipt.json"
)
_MEDIA_RIGHTS_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "evidence-inbox" / "media-rights.json"
)
_MEDIA_AUTHORITY_PATH: Path = (
    _PROJECT_ROOT / _PHASE_RELPATH / "execution-handoffs" / "media-authority.json"
)
_HANDOFF_VERSION: Final = "phase31-handoff-v1"
_MAX_JSON_BYTES: Final = 1_048_576


class Phase31HandoffReasonCode(str, Enum):
    HASH_INVALID = "hash_invalid"
    ARTIFACT_MISSING = "artifact_missing"
    ARTIFACT_INVALID = "artifact_invalid"
    HASH_MISMATCH = "hash_mismatch"
    HANDOFF_MISSING = "handoff_missing"
    HANDOFF_INVALID = "handoff_invalid"
    HANDOFF_CONFLICT = "handoff_conflict"
    UNSAFE_PATH = "unsafe_path"
    ATOMIC_WRITE_FAILED = "atomic_write_failed"


class Phase31HandoffError(ValueError):
    """Scanner-safe handoff failure that never includes paths or content."""

    def __init__(self, reason_code: Phase31HandoffReasonCode) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code.value)


def _raise(reason_code: Phase31HandoffReasonCode) -> None:
    raise Phase31HandoffError(reason_code)


def _sha256_text(value: str, *, field_name: str = "sha256") -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _checked_sha256(value: str) -> str:
    try:
        return _sha256_text(value)
    except ValueError as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.HASH_INVALID) from exc


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_hash(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_hash", None)
    return sha256(_canonical_bytes(unsigned)).hexdigest()


def _json_file_bytes(payload: dict[str, object]) -> bytes:
    return _canonical_bytes(payload) + b"\n"


def _utc_timestamp(value: str) -> str:
    if not isinstance(value, str) or len(value) != 20:
        raise ValueError("timestamp must be UTC")
    from datetime import datetime

    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("timestamp must be UTC") from exc
    return value


def _is_link_or_reparse(value: os.stat_result) -> bool:
    if stat.S_ISLNK(value.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(value, "st_file_attributes", 0) & reparse_flag)


def _assert_existing_path_safe(path: Path, *, missing_ok: bool) -> os.stat_result | None:
    try:
        parts = path.relative_to(_PROJECT_ROOT).parts
    except ValueError:
        _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
    current = _PROJECT_ROOT
    try:
        current_stat = current.lstat()
    except OSError as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.UNSAFE_PATH) from exc
    if _is_link_or_reparse(current_stat):
        _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
    for index, part in enumerate(parts):
        current = current / part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            if missing_ok:
                return None
            _raise(Phase31HandoffReasonCode.ARTIFACT_MISSING)
        except OSError as exc:
            raise Phase31HandoffError(Phase31HandoffReasonCode.UNSAFE_PATH) from exc
        if _is_link_or_reparse(current_stat):
            _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
        if index < len(parts) - 1 and not stat.S_ISDIR(current_stat.st_mode):
            _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
    return current_stat


def _ensure_handoff_root() -> None:
    try:
        parts = _HANDOFF_ROOT.relative_to(_PROJECT_ROOT).parts
    except ValueError:
        _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
    current = _PROJECT_ROOT
    _assert_existing_path_safe(current, missing_ok=False)
    for part in parts:
        current = current / part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o700)
                current_stat = current.lstat()
            except OSError as exc:
                raise Phase31HandoffError(
                    Phase31HandoffReasonCode.ATOMIC_WRITE_FAILED
                ) from exc
        except OSError as exc:
            raise Phase31HandoffError(Phase31HandoffReasonCode.UNSAFE_PATH) from exc
        if _is_link_or_reparse(current_stat) or not stat.S_ISDIR(current_stat.st_mode):
            _raise(Phase31HandoffReasonCode.UNSAFE_PATH)


def _read_regular_bytes(
    path: Path,
    *,
    missing_reason: Phase31HandoffReasonCode,
) -> bytes:
    before = _assert_existing_path_safe(path, missing_ok=False)
    assert before is not None
    if not stat.S_ISREG(before.st_mode):
        _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
    if before.st_size > _MAX_JSON_BYTES:
        _raise(Phase31HandoffReasonCode.ARTIFACT_INVALID)
    try:
        raw = path.read_bytes()
        after = path.lstat()
    except FileNotFoundError as exc:
        raise Phase31HandoffError(missing_reason) from exc
    except OSError as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.ARTIFACT_INVALID) from exc
    if (
        _is_link_or_reparse(after)
        or not stat.S_ISREG(after.st_mode)
        or before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_mtime_ns != after.st_mtime_ns
        or before.st_size != after.st_size
    ):
        _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
    return raw


def _read_json(path: Path, *, missing_reason: Phase31HandoffReasonCode) -> dict[str, object]:
    raw = _read_regular_bytes(path, missing_reason=missing_reason)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.ARTIFACT_INVALID) from exc
    if not isinstance(payload, dict):
        _raise(Phase31HandoffReasonCode.ARTIFACT_INVALID)
    return payload


def _current_draft_manifest_sha256() -> str:
    payload = _read_json(
        _DRAFT_MANIFEST_PATH,
        missing_reason=Phase31HandoffReasonCode.ARTIFACT_MISSING,
    )
    try:
        return _sha256_text(str(payload["content_hash"]), field_name="content_hash")
    except (KeyError, ValueError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.ARTIFACT_INVALID) from exc


def _file_sha256(path: Path, *, missing_reason: Phase31HandoffReasonCode) -> str:
    return sha256(_read_regular_bytes(path, missing_reason=missing_reason)).hexdigest()


def _validate_handoff(payload: dict[str, object], *, kind: str) -> None:
    if payload.get("schema_version") != 1:
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    if payload.get("handoff_version") != _HANDOFF_VERSION:
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    if payload.get("kind") != kind:
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    try:
        _sha256_text(str(payload["content_hash"]), field_name="content_hash")
    except (KeyError, ValueError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.HANDOFF_INVALID) from exc
    if payload["content_hash"] != _canonical_hash(payload):
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)


def _handoff_path(filename: str) -> Path:
    if filename not in {
        "curation-selection.json",
        "evidence-confirmation.json",
        "activation.json",
        "media-authority.json",
    }:
        _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
    return _HANDOFF_ROOT / filename


def _atomic_write_handoff(path: Path, raw: bytes) -> None:
    _ensure_handoff_root()
    current_stat = _assert_existing_path_safe(path, missing_ok=True)
    if current_stat is not None:
        if not stat.S_ISREG(current_stat.st_mode):
            _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
        existing = _read_regular_bytes(
            path,
            missing_reason=Phase31HandoffReasonCode.HANDOFF_MISSING,
        )
        if existing == raw:
            return
        _raise(Phase31HandoffReasonCode.HANDOFF_CONFLICT)
    descriptor = -1
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        try:
            os.fchmod(descriptor, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        current_stat = _assert_existing_path_safe(path, missing_ok=True)
        if current_stat is not None and not stat.S_ISREG(current_stat.st_mode):
            _raise(Phase31HandoffReasonCode.UNSAFE_PATH)
        os.replace(temporary_name, path)
        temporary_name = None
    except Phase31HandoffError:
        raise
    except OSError as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.ATOMIC_WRITE_FAILED) from exc
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _write_handoff(filename: str, payload: dict[str, object]) -> dict[str, object]:
    payload = dict(payload)
    payload["schema_version"] = 1
    payload["handoff_version"] = _HANDOFF_VERSION
    payload["content_hash"] = _canonical_hash(payload)
    _validate_handoff(payload, kind=str(payload["kind"]))
    _atomic_write_handoff(_handoff_path(filename), _json_file_bytes(payload))
    return payload


def _read_handoff(filename: str, *, kind: str) -> dict[str, object]:
    try:
        payload = _read_json(
            _handoff_path(filename),
            missing_reason=Phase31HandoffReasonCode.HANDOFF_MISSING,
        )
    except Phase31HandoffError as exc:
        if exc.reason_code is Phase31HandoffReasonCode.ARTIFACT_MISSING:
            raise Phase31HandoffError(Phase31HandoffReasonCode.HANDOFF_MISSING) from exc
        raise
    _validate_handoff(payload, kind=kind)
    return payload


def record_selection(sha256_value: str) -> dict[str, object]:
    selected = _checked_sha256(sha256_value)
    current = _current_draft_manifest_sha256()
    if selected != current:
        _raise(Phase31HandoffReasonCode.HASH_MISMATCH)
    return _write_handoff(
        "curation-selection.json",
        {
            "kind": "curation-selection",
            "selected_sha256": selected,
            "current_draft_manifest_sha256": current,
        },
    )


def get_selection() -> str:
    payload = _read_handoff("curation-selection.json", kind="curation-selection")
    try:
        return _sha256_text(str(payload["selected_sha256"]))
    except (KeyError, ValueError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.HANDOFF_INVALID) from exc


def record_evidence(sha256_value: str) -> dict[str, object]:
    confirmed = _checked_sha256(sha256_value)
    current = _file_sha256(
        _EVIDENCE_INDEX_PATH,
        missing_reason=Phase31HandoffReasonCode.ARTIFACT_MISSING,
    )
    if confirmed != current:
        _raise(Phase31HandoffReasonCode.HASH_MISMATCH)
    return _write_handoff(
        "evidence-confirmation.json",
        {
            "kind": "evidence-confirmation",
            "confirmed_index_sha256": confirmed,
            "current_evidence_index_sha256": current,
        },
    )


def get_evidence() -> str:
    payload = _read_handoff("evidence-confirmation.json", kind="evidence-confirmation")
    try:
        return _sha256_text(str(payload["confirmed_index_sha256"]))
    except (KeyError, ValueError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.HANDOFF_INVALID) from exc


def get_receipt() -> str:
    return _file_sha256(
        _RECEIPT_PATH,
        missing_reason=Phase31HandoffReasonCode.ARTIFACT_MISSING,
    )


def record_authorization(
    sha256_value: str,
    *,
    expected_receipt_sha256: str,
) -> dict[str, object]:
    authorization = _checked_sha256(sha256_value)
    expected_receipt = _checked_sha256(expected_receipt_sha256)
    current_receipt = get_receipt()
    if expected_receipt != current_receipt:
        _raise(Phase31HandoffReasonCode.HASH_MISMATCH)
    return _write_handoff(
        "activation.json",
        {
            "kind": "activation-authorization",
            "authorization_sha256": authorization,
            "expected_receipt_sha256": expected_receipt,
            "current_receipt_sha256": current_receipt,
        },
    )


def get_authorization() -> str:
    payload = _read_handoff("activation.json", kind="activation-authorization")
    try:
        return _sha256_text(str(payload["authorization_sha256"]))
    except (KeyError, ValueError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.HANDOFF_INVALID) from exc


def _read_media_rights() -> tuple[dict[str, object], str]:
    raw = _read_regular_bytes(
        _MEDIA_RIGHTS_PATH,
        missing_reason=Phase31HandoffReasonCode.ARTIFACT_MISSING,
    )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.ARTIFACT_INVALID) from exc
    if not isinstance(payload, dict):
        _raise(Phase31HandoffReasonCode.ARTIFACT_INVALID)
    return payload, sha256(raw).hexdigest()


def _media_scope(payload: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    provider = payload.get("provider_scope")
    item_set = payload.get("item_set")
    if not isinstance(provider, dict) or not isinstance(item_set, dict):
        _raise(Phase31HandoffReasonCode.ARTIFACT_INVALID)
    required_provider = {
        "route",
        "voice_profile_id",
        "voice_profile_version",
        "provider_attempt_ceiling",
        "budget_ceiling_amount",
        "budget_ceiling_currency",
        "credential_boundary",
    }
    required_items = {"item_set_sha256", "required_slots"}
    if not required_provider <= set(provider) or not required_items <= set(item_set):
        _raise(Phase31HandoffReasonCode.ARTIFACT_INVALID)
    return provider, item_set


def _validate_media_authority_payload(payload: dict[str, object]) -> None:
    required = {
        "schema_version",
        "handoff_version",
        "kind",
        "actor_type",
        "agent_authored",
        "confirmation_method",
        "exact_supplied_response",
        "supplied_response_sha256",
        "orchestration_timestamp",
        "rights_document_sha256",
        "route",
        "item_set_sha256",
        "item_count",
        "voice_profile_id",
        "voice_profile_version",
        "provider_attempt_ceiling",
        "budget_ceiling_amount",
        "budget_ceiling_currency",
        "credential_boundary",
        "single_use_operation_id",
        "consumed",
        "replay_constraints",
        "content_hash",
    }
    if set(payload) != required:
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    if (
        payload.get("schema_version") != 1
        or payload.get("handoff_version") != _HANDOFF_VERSION
        or payload.get("kind") != "media-authority"
        or payload.get("actor_type") != "project_owner"
        or payload.get("agent_authored") is not False
        or payload.get("consumed") is not False
    ):
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    for field in ("rights_document_sha256", "item_set_sha256", "content_hash"):
        try:
            _sha256_text(str(payload[field]), field_name=field)
        except (KeyError, ValueError) as exc:
            raise Phase31HandoffError(Phase31HandoffReasonCode.HANDOFF_INVALID) from exc
    if payload["content_hash"] != _canonical_hash(payload):
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)


def record_media_authority(
    response: str,
    *,
    confirmation_method: str,
    orchestration_timestamp: str,
) -> dict[str, object]:
    if not isinstance(response, str) or response.startswith("decline:"):
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    prefix = "authorize-media "
    if not response.startswith(prefix):
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    supplied_hash = _checked_sha256(response.removeprefix(prefix))
    rights, rights_sha256 = _read_media_rights()
    if supplied_hash != rights_sha256:
        _raise(Phase31HandoffReasonCode.HASH_MISMATCH)
    provider, item_set = _media_scope(rights)
    try:
        timestamp = _utc_timestamp(orchestration_timestamp)
        item_set_hash = _sha256_text(str(item_set["item_set_sha256"]))
        item_count = int(item_set["required_slots"])
        attempt_ceiling = int(provider["provider_attempt_ceiling"])
    except (KeyError, TypeError, ValueError) as exc:
        raise Phase31HandoffError(Phase31HandoffReasonCode.ARTIFACT_INVALID) from exc
    if item_count <= 0 or attempt_ceiling <= 0:
        _raise(Phase31HandoffReasonCode.ARTIFACT_INVALID)
    payload: dict[str, object] = {
        "schema_version": 1,
        "handoff_version": _HANDOFF_VERSION,
        "kind": "media-authority",
        "actor_type": "project_owner",
        "agent_authored": False,
        "confirmation_method": confirmation_method,
        "exact_supplied_response": response,
        "supplied_response_sha256": sha256(response.encode("utf-8")).hexdigest(),
        "orchestration_timestamp": timestamp,
        "rights_document_sha256": rights_sha256,
        "route": str(provider["route"]),
        "item_set_sha256": item_set_hash,
        "item_count": item_count,
        "voice_profile_id": str(provider["voice_profile_id"]),
        "voice_profile_version": str(provider["voice_profile_version"]),
        "provider_attempt_ceiling": attempt_ceiling,
        "budget_ceiling_amount": str(provider["budget_ceiling_amount"]),
        "budget_ceiling_currency": str(provider["budget_ceiling_currency"]),
        "credential_boundary": str(provider["credential_boundary"]),
        "single_use_operation_id": str(rights.get("single_use_operation_id", "")),
        "consumed": False,
        "replay_constraints": rights.get("replay_constraints", {}),
    }
    payload["content_hash"] = _canonical_hash(payload)
    _validate_media_authority_payload(payload)
    _atomic_write_handoff(_MEDIA_AUTHORITY_PATH, _json_file_bytes(payload))
    return payload


def _read_media_authority() -> dict[str, object]:
    payload = _read_json(
        _MEDIA_AUTHORITY_PATH,
        missing_reason=Phase31HandoffReasonCode.HANDOFF_MISSING,
    )
    _validate_media_authority_payload(payload)
    return payload


def get_media_authority() -> str:
    payload = _read_media_authority()
    return _sha256_text(str(payload["rights_document_sha256"]))


def verify_media_authority(
    *,
    require_project_owner: bool = False,
    require_unconsumed: bool = False,
    require_voice_profile: bool = False,
    require_provider_attempt_ceiling: bool = False,
) -> dict[str, object]:
    payload = _read_media_authority()
    _, rights_sha256 = _read_media_rights()
    if payload["rights_document_sha256"] != rights_sha256:
        _raise(Phase31HandoffReasonCode.HASH_MISMATCH)
    if require_project_owner and (
        payload["actor_type"] != "project_owner" or payload["agent_authored"] is not False
    ):
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    if require_unconsumed and payload["consumed"] is not False:
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    if require_voice_profile and not payload["voice_profile_id"]:
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    if require_provider_attempt_ceiling and int(payload["provider_attempt_ceiling"]) <= 0:
        _raise(Phase31HandoffReasonCode.HANDOFF_INVALID)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record or read fixed Phase 31 hash-only handoffs."
    )
    commands = parser.add_subparsers(dest="operation", required=True)
    selection = commands.add_parser("record-selection")
    selection.add_argument("--sha256", required=True)
    commands.add_parser("get-selection")
    evidence = commands.add_parser("record-evidence")
    evidence.add_argument("--sha256", required=True)
    commands.add_parser("get-evidence")
    commands.add_parser("get-receipt")
    authorization = commands.add_parser("record-authorization")
    authorization.add_argument("--sha256", required=True)
    authorization.add_argument("--expected-receipt-sha256", required=True)
    commands.add_parser("get-authorization")
    media = commands.add_parser("record-media-authority")
    media.add_argument("--response", required=True)
    media.add_argument("--confirmation-method", required=True)
    media.add_argument("--orchestration-timestamp", required=True)
    verify_media = commands.add_parser("verify-media-authority")
    verify_media.add_argument("--require-project-owner", action="store_true")
    verify_media.add_argument("--require-unconsumed", action="store_true")
    verify_media.add_argument("--require-voice-profile", action="store_true")
    verify_media.add_argument("--require-provider-attempt-ceiling", action="store_true")
    commands.add_parser("get-media-authority")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.operation == "record-selection":
            print(record_selection(args.sha256)["content_hash"])
        elif args.operation == "get-selection":
            print(get_selection())
        elif args.operation == "record-evidence":
            print(record_evidence(args.sha256)["content_hash"])
        elif args.operation == "get-evidence":
            print(get_evidence())
        elif args.operation == "get-receipt":
            print(get_receipt())
        elif args.operation == "record-authorization":
            print(
                record_authorization(
                    args.sha256,
                    expected_receipt_sha256=args.expected_receipt_sha256,
                )["content_hash"]
            )
        elif args.operation == "record-media-authority":
            print(
                record_media_authority(
                    args.response,
                    confirmation_method=args.confirmation_method,
                    orchestration_timestamp=args.orchestration_timestamp,
                )["content_hash"]
            )
        elif args.operation == "verify-media-authority":
            verify_media_authority(
                require_project_owner=args.require_project_owner,
                require_unconsumed=args.require_unconsumed,
                require_voice_profile=args.require_voice_profile,
                require_provider_attempt_ceiling=args.require_provider_attempt_ceiling,
            )
            print("media_authority_status=verified")
        elif args.operation == "get-media-authority":
            print(get_media_authority())
        else:
            print(get_authorization())
    except Phase31HandoffError as exc:
        print(exc.reason_code.value, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
