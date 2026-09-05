"""Fixed, pathless Korean foundation evidence and receipt contracts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from importlib import import_module, util
import inspect
import io
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import stat
import struct
import time
from types import ModuleType
from typing import Any, Callable
import unicodedata
import wave
import zlib

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_ROOT = (
    PROJECT_ROOT
    / ".planning"
    / "phases"
    / "31-hangul-and-pronunciation-i-plus-1"
)
CANONICAL_INBOX = PHASE_ROOT / "evidence-inbox"
CURRENT_BUNDLE_SHA256 = (
    "e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357"
)
CURRENT_BUNDLE_RELPATH = f"candidate-bundles/{CURRENT_BUNDLE_SHA256}"
REGISTRY_FILENAME = "korean-concepts-v1.json"
CANDIDATE_FILENAMES = (
    "current-candidate.json",
    "bundle-manifest.json",
    "hangul-v2.json",
    "pronunciation-i-plus-1-v2.json",
    "korean-foundations-v2-curation.json",
    "korean-foundations-v2-media.json",
)
CANDIDATE_MEMBER_FILENAMES = CANDIDATE_FILENAMES[2:]
REQUEST_FILENAMES = (
    "31-CURRICULUM-REVIEW.md",
    "31-AUDIO-PLAYBACK-REVIEW.md",
)
FIXED_EVIDENCE_RELPATHS = (
    "proposed-curation.json",
    "proposed-media.json",
    "curriculum-review.json",
    "audio-playback-review.json",
    "rights.json",
    "reviewers/korean-orthography.json",
    "reviewers/korean-phonetics.json",
    "reviewers/portuguese.json",
    "reviewers/independent-native-speaker.json",
)
REVIEWED_AT = "2026-08-05T00:00:00Z"
CURRENT_AI_AGGREGATE_ROOT = (
    "9abb3d6b950e34c010ea0ed380e995cf39d653e875f43c3a2bfdc78363993922"
)
CURRENT_ACOUSTIC_AGGREGATE_ROOT = (
    "1618b67d251d13a29a1c9d27ce736c5f14a23be2fd8c679ae45739fae57a4c4d"
)
CURRENT_MEDIA_RIGHTS_SHA256 = (
    "c00cc1d5b297bf15499a49318fcc31ab373e595167b01f7f72b47d0a6290a8c6"
)
CURRENT_MEDIA_AUTHORITY_SHA256 = (
    "a9eb33b67ed869297b603cbe37a0faa689b2087b22d2b1bdf86dba23aaf1f2f5"
)
CURRICULUM_GATES = {
    "hangul": (
        "source_content",
        "curriculum_atomicity",
        "korean_orthography",
        "portuguese",
    ),
    "pronunciation": (
        "source_content",
        "curriculum_atomicity",
        "korean_phonetics",
        "portuguese",
    ),
}
REVIEWER_FILE_PAYLOADS = {
    "reviewers/korean-orthography.json": {
        "reviewer_id": "fixture-only-orthography-reviewer",
        "primary_role": "korean-orthography-reviewer",
        "qualified_roles": [
            "korean-foundation-content-reviewer",
            "korean-curriculum-reviewer",
            "korean-orthography-reviewer",
            "media-rights-reviewer",
            "media-integrity-reviewer",
        ],
    },
    "reviewers/korean-phonetics.json": {
        "reviewer_id": "fixture-only-phonetics-reviewer",
        "primary_role": "korean-phonetics-specialist",
        "qualified_roles": ["korean-phonetics-specialist"],
    },
    "reviewers/portuguese.json": {
        "reviewer_id": "fixture-only-portuguese-reviewer",
        "primary_role": "portuguese-reviewer",
        "qualified_roles": ["portuguese-reviewer"],
    },
    "reviewers/independent-native-speaker.json": {
        "reviewer_id": "fixture-only-independent-native-reviewer",
        "primary_role": "independent-native-speaker",
        "qualified_roles": [
            "audio-playback-reviewer",
            "independent-native-speaker",
        ],
    },
}
REVIEWER_BY_ROLE = {
    role: payload["reviewer_id"]
    for payload in REVIEWER_FILE_PAYLOADS.values()
    for role in payload["qualified_roles"]
}
AUDIO_KINDS = frozenset(
    {"audio", "letter_audio", "word_audio", "sentence_audio"}
)
EXPECTED_CANDIDATE_SHA256 = {
    "current-candidate.json": (
        "225ff85c19346866640400765a3b33ac9d13e2e9a13ee67c6edb11455a6179e5"
    ),
    "bundle-manifest.json": (
        "6852f7cc6eeedf2ec88f33ab8f027e76a72981a4179015b8aa40a0f3eb40a3ab"
    ),
    "hangul-v2.json": (
        "da12a49c5f42483eeeb6da4f251ea2eba3295afa7cf07c2c621e4dddfa5ff038"
    ),
    "pronunciation-i-plus-1-v2.json": (
        "889acedc9de497cfa25d8699ac4d2434bd102653c31276874a8b4336fd15448e"
    ),
    "korean-foundations-v2-curation.json": (
        "695346c70e34e163e459e3f2e1c8156b39ed4f126c4803e98258d229a8164caf"
    ),
    "korean-foundations-v2-media.json": (
        "545bd060992e9a17d7a95a3397d774678c3cb3e3cddbe593e93c949f9b12326d"
    ),
}
EXPECTED_REGISTRY_SHA256 = {
    "file_sha256": "79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625",
    "canonical_content_sha256": (
        "89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d"
    ),
}
EXPECTED_REQUEST_SHA256 = {
    "31-CURRICULUM-REVIEW.md": (
        "df52d78f2bcd3a89e9589ea68d645df02841a2f9017394d14c833cb7580b36cc"
    ),
    "31-AUDIO-PLAYBACK-REVIEW.md": (
        "4e28149921c9602c78f1e15633923b55eaf572993fce506651d6d474acf73035"
    ),
}


def _evidence() -> ModuleType:
    assert util.find_spec("multilang.services.korean_foundation_evidence") is not None, (
        "the fixed Korean foundation evidence service must exist"
    )
    return import_module("multilang.services.korean_foundation_evidence")


def _media_api() -> ModuleType:
    return import_module("multilang.services.korean_foundation_media")


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _json_file_bytes(payload: object) -> bytes:
    return _canonical_bytes(payload) + b"\n"


def _canonical_sha256(payload: object) -> str:
    return sha256(_canonical_bytes(payload)).hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _text_sha256(value: str) -> str:
    return _sha256_bytes(unicodedata.normalize("NFC", value).encode("utf-8"))


def _write_json(path: Path, payload: object) -> bytes:
    raw = _json_file_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def _png_chunk(name: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(name + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + name + payload + struct.pack(">I", checksum)


def _png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + _png_chunk(b"IEND", b"")
    )


def _gif_bytes() -> bytes:
    return (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
        b"\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00"
        b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )


def _pcm_wav_bytes(sequence: int, *, duration_ms: int = 100) -> bytes:
    frame_rate = 16_000
    frame_count = frame_rate * duration_ms // 1_000
    sample = struct.pack("<h", (sequence % 101) + 1)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(frame_rate)
        wav_file.writeframes(sample * frame_count)
    return buffer.getvalue()


def _media_bytes(slot: dict[str, Any]) -> bytes:
    if slot["media_kind"] in AUDIO_KINDS:
        return _pcm_wav_bytes(int(slot["sequence"]))
    if slot["output_format"] == "gif":
        return _gif_bytes()
    return _png_bytes()


def _expected_display_text(
    slot: dict[str, Any],
    entry: dict[str, Any],
) -> str:
    if slot["family"] == "hangul":
        mapping = entry.get("pedagogical_jamo_mapping")
        return (
            str(mapping["display_glyph"])
            if isinstance(mapping, dict)
            else str(entry["canonical_jamo_or_block"])
        )
    if slot["media_kind"] == "letter_audio":
        return str(entry["spellings"])
    if slot["media_kind"] == "word_audio":
        return str(entry["example_word"])
    return str(entry["example_sentence"])


def _spoken_text(slot: dict[str, Any], display_text: str) -> str | None:
    if slot["media_kind"] not in AUDIO_KINDS:
        return None
    if slot["family"] == "hangul":
        return "테스트 전용 한글 음성"
    if slot["media_kind"] == "letter_audio":
        return "테스트 전용 발음 문맥"
    if display_text == "needs_review":
        return "테스트 전용 검토 문장"
    return display_text


def _gate_digest(
    *,
    record: dict[str, Any],
    gate: dict[str, Any],
) -> str:
    return _canonical_sha256(
        {
            "item_key": record["item_key"],
            "gate_name": gate["gate_name"],
            "scope_ids": gate["scope_ids"],
            "source_pack_version": record["source_pack_version"],
            "source_content_sha256": record["source_content_sha256"],
        }
    )


def _reseal_payload(payload: dict[str, Any], hash_field: str) -> None:
    payload.pop(hash_field, None)
    payload[hash_field] = _canonical_sha256(payload)


def _candidate_version(filename: str, payload: dict[str, Any]) -> str:
    field = {
        "hangul-v2.json": "source_pack_version",
        "pronunciation-i-plus-1-v2.json": "source_pack_version",
        "korean-foundations-v2-curation.json": "manifest_version",
        "korean-foundations-v2-media.json": "manifest_version",
    }[filename]
    return str(payload[field])


def _canonical_candidate_path(filename: str) -> Path:
    root = PROJECT_ROOT / "data" / "korean_foundations"
    if filename in {REGISTRY_FILENAME, "current-candidate.json"}:
        return root / filename
    return root / CURRENT_BUNDLE_RELPATH / filename


def _fixture_candidate_path(candidate_root: Path, filename: str) -> Path:
    if filename in {REGISTRY_FILENAME, "current-candidate.json"}:
        return candidate_root / filename
    return candidate_root / CURRENT_BUNDLE_RELPATH / filename


def _candidate_binding(
    filename: str,
    payload: dict[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    if filename == "current-candidate.json":
        return {
            "filename": filename,
            "bundle_sha256": payload["bundle_sha256"],
            "bundle_relpath": payload["bundle_relpath"],
            "bundle_manifest_sha256": payload["bundle_manifest_sha256"],
            "file_sha256": _sha256_bytes(raw),
        }
    if filename == "bundle-manifest.json":
        return {
            "filename": filename,
            "bundle_sha256": payload["bundle_sha256"],
            "selected_draft_manifest_sha256": payload[
                "selected_draft_manifest_sha256"
            ],
            "draft_validation_sha256": payload["draft_validation_sha256"],
            "file_sha256": _sha256_bytes(raw),
            "total_record_count": 139,
            "media_slot_count": 509,
        }

    binding: dict[str, Any] = {
        "filename": filename,
        "version": _candidate_version(filename, payload),
        "file_sha256": _sha256_bytes(raw),
        "canonical_content_sha256": payload["content_hash"],
    }
    if filename == "hangul-v2.json":
        binding["item_count"] = 92
    elif filename == "pronunciation-i-plus-1-v2.json":
        binding["item_count"] = 47
    elif filename == "korean-foundations-v2-curation.json":
        binding["record_count"] = 139
        binding["gate_count"] = sum(
            len(record["gates"]) for record in payload["records"]
        )
    else:
        binding["asset_count"] = 509
        binding["required_asset_count"] = sum(
            1 for slot in payload["slots"] if slot["required"]
        )
    return binding


def _reviewer_records() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for relpath, identity in REVIEWER_FILE_PAYLOADS.items():
        qualification_payload = {
            "reviewer_id": identity["reviewer_id"],
            "primary_role": identity["primary_role"],
            "qualified_roles": identity["qualified_roles"],
            "qualification_status": "approved",
            "reviewed_at": REVIEWED_AT,
        }
        records[relpath] = {
            "schema_version": 1,
            "record_version": "fixture-only-reviewer-record-v1",
            **qualification_payload,
            "qualification_evidence_sha256": _canonical_sha256(
                qualification_payload
            ),
        }
    return records


def _approved_curation(
    candidate: dict[str, Any],
    entries_by_key: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    proposed = deepcopy(candidate)
    proposed["candidate_only"] = False
    for record in proposed["records"]:
        entry = entries_by_key[str(record["item_key"])]
        assert record["source_content_sha256"] == entry["content_hash"]
        for gate in record["gates"]:
            reviewer_role = {
                "source_content": "korean-foundation-content-reviewer",
                "curriculum_atomicity": "korean-curriculum-reviewer",
                "korean_orthography": "korean-orthography-reviewer",
                "korean_phonetics": "korean-phonetics-specialist",
                "portuguese": "portuguese-reviewer",
                "media_license": "media-rights-reviewer",
                "media_integrity": "media-integrity-reviewer",
                "audio_playback": "audio-playback-reviewer",
            }[str(gate["gate_name"])]
            gate.update(
                {
                    "status": "approved",
                    "reason_code": None,
                    "reviewer_id": REVIEWER_BY_ROLE[reviewer_role],
                    "reviewer_role": reviewer_role,
                    "reviewed_at": REVIEWED_AT,
                    "source_pack_version": record["source_pack_version"],
                    "source_content_sha256": record["source_content_sha256"],
                    "reviewed_evidence_sha256": _gate_digest(
                        record=record,
                        gate=gate,
                    ),
                }
            )
    _reseal_payload(proposed, "content_hash")
    return proposed


def _curriculum_review(
    *,
    proposed: dict[str, Any],
    proposed_raw: bytes,
    curriculum_request_raw: bytes,
) -> dict[str, Any]:
    item_reviews = []
    for record in proposed["records"]:
        gate_reviews = []
        for gate in record["gates"]:
            if gate["gate_name"] not in CURRICULUM_GATES[record["family"]]:
                continue
            gate_reviews.append(
                {
                    "gate_name": gate["gate_name"],
                    "scope_ids": gate["scope_ids"],
                    "reviewer_id": gate["reviewer_id"],
                    "reviewer_role": gate["reviewer_role"],
                    "reviewed_at": gate["reviewed_at"],
                    "source_content_sha256": record["source_content_sha256"],
                    "reviewed_evidence_sha256": gate[
                        "reviewed_evidence_sha256"
                    ],
                }
            )
        item_reviews.append(
            {
                "family": record["family"],
                "item_key": record["item_key"],
                "source_pack_version": record["source_pack_version"],
                "source_content_sha256": record["source_content_sha256"],
                "gate_reviews": gate_reviews,
            }
        )
    specialist_reviews = []
    records_by_key = {record["item_key"]: record for record in proposed["records"]}
    for sequence in range(42, 48):
        item_key = f"ko-pron-{sequence:04d}"
        record = records_by_key[item_key]
        specialist_reviews.append(
            {
                "item_key": item_key,
                "stage_id": "P11" if sequence == 42 else "P12" if sequence < 47 else "P13",
                "scope_ids": [
                    "P11-P13-atomization",
                    "active-rule-analysis",
                    "rule-ordering",
                ],
                "reviewer_id": REVIEWER_BY_ROLE["korean-phonetics-specialist"],
                "reviewer_role": "korean-phonetics-specialist",
                "reviewed_at": REVIEWED_AT,
                "source_content_sha256": record["source_content_sha256"],
                "reviewed_evidence_sha256": _canonical_sha256(
                    {
                        "item_key": item_key,
                        "source_content_sha256": record[
                            "source_content_sha256"
                        ],
                        "scope_ids": [
                            "P11-P13-atomization",
                            "active-rule-analysis",
                            "rule-ordering",
                        ],
                    }
                ),
            }
        )
    policy_binding = {
        "canonical_language_code": "pt",
        "regional_editorial_policy": "fixture-only-pt-policy",
        "reviewer_id": REVIEWER_BY_ROLE["portuguese-reviewer"],
        "reviewer_role": "portuguese-reviewer",
        "reviewed_at": REVIEWED_AT,
    }
    return {
        "schema_version": 1,
        "review_version": "fixture-only-curriculum-review-v1",
        "curriculum_request_sha256": _sha256_bytes(curriculum_request_raw),
        "proposed_curation_sha256": _sha256_bytes(proposed_raw),
        "item_reviews": item_reviews,
        "specialist_atomization_reviews": specialist_reviews,
        "portuguese_policy": {
            **policy_binding,
            "reviewed_evidence_sha256": _canonical_sha256(policy_binding),
        },
    }


def _approved_media(
    *,
    candidate: dict[str, Any],
    entries_by_key: dict[str, dict[str, Any]],
    media_root: Path,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    media_api = _media_api()
    proposed = deepcopy(candidate)
    proposed["candidate_only"] = False
    media_members: dict[str, bytes] = {}
    for slot in proposed["slots"]:
        entry = entries_by_key[str(slot["item_key"])]
        content = _media_bytes(slot)
        display_text = _expected_display_text(slot, entry)
        spoken_text = _spoken_text(slot, display_text)
        text_nfc = unicodedata.normalize("NFC", spoken_text or display_text)
        is_audio = slot["media_kind"] in AUDIO_KINDS
        artifact_hash = _sha256_bytes(content)
        slot.update(
            {
                "status": "approved",
                "reason_code": None,
                "source_id": "fixture-only-media-source",
                "source_version": "fixture-only-media-source-v1",
                "attribution": "FIXTURE ONLY - NOT PRODUCTION EVIDENCE",
                "license_id": "fixture-only-license",
                "redistribution_disposition": "approved",
                "display_text": display_text,
                "spoken_text": spoken_text,
                "text_nfc": text_nfc,
                "display_text_sha256": _text_sha256(display_text),
                "spoken_text_sha256": (
                    _text_sha256(spoken_text) if spoken_text is not None else None
                ),
                "text_nfc_sha256": _text_sha256(text_nfc),
                "provider": "fixture-only-local-provider" if is_audio else None,
                "provider_version": "fixture-only-provider-v1" if is_audio else None,
                "voice_id": "fixture-only-voice" if is_audio else None,
                "locale": "ko-KR" if is_audio else None,
                "ssml_sha256": _text_sha256("fixture-only-ssml")
                if is_audio
                else None,
                "prosody_sha256": _text_sha256("fixture-only-prosody")
                if is_audio
                else None,
                "duration_ms": 100 if is_audio else None,
                "artifact_sha256": artifact_hash,
                "reviewed_artifact_sha256": artifact_hash,
                "metadata_sha256": "0" * 64,
                "reviewed_metadata_sha256": "0" * 64,
                "review_receipts": [],
            }
        )
        metadata_hash = media_api.korean_foundation_media_metadata_sha256(slot)
        slot["metadata_sha256"] = metadata_hash
        slot["reviewed_metadata_sha256"] = metadata_hash
        roles = ["media-rights-reviewer", "media-integrity-reviewer"]
        if is_audio:
            roles.extend(
                [
                    "audio-playback-reviewer",
                    "korean-phonetics-specialist",
                    "independent-native-speaker",
                ]
            )
        slot["review_receipts"] = [
            {
                "reviewer_id": REVIEWER_BY_ROLE[role],
                "reviewer_role": role,
                "reviewed_at": REVIEWED_AT,
                "artifact_sha256": artifact_hash,
                "metadata_sha256": metadata_hash,
            }
            for role in roles
        ]
        media_api.KoreanFoundationMediaSlot.model_validate(slot)
        destination = media_root / str(slot["basename"])
        destination.write_bytes(content)
        media_members[str(slot["basename"])] = content
    proposed.pop("content_hash", None)
    proposed["content_hash"] = media_api.korean_foundation_media_manifest_sha256(
        proposed
    )
    media_api.KoreanFoundationMediaManifest.model_validate(proposed)
    return proposed, media_members


def _rights_payload(proposed_media: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "rights_version": "fixture-only-rights-v1",
        "records": [
            {
                "slot_id": slot["slot_id"],
                "media_kind": slot["media_kind"],
                "source_id": slot["source_id"],
                "source_version": slot["source_version"],
                "attribution": slot["attribution"],
                "license_id": slot["license_id"],
                "reuse_disposition": "approved",
                "redistribution_disposition": slot[
                    "redistribution_disposition"
                ],
                "artifact_sha256": slot["artifact_sha256"],
                "reviewed_metadata_sha256": slot[
                    "reviewed_metadata_sha256"
                ],
                "reviewer_id": REVIEWER_BY_ROLE["media-rights-reviewer"],
                "reviewer_role": "media-rights-reviewer",
                "reviewed_at": REVIEWED_AT,
            }
            for slot in proposed_media["slots"]
        ],
    }


def _playback_payload(
    proposed_media: dict[str, Any],
    audio_request_raw: bytes,
) -> dict[str, Any]:
    records = []
    for slot in proposed_media["slots"]:
        if slot["media_kind"] not in AUDIO_KINDS:
            continue
        roles = (
            "audio-playback-reviewer",
            "korean-phonetics-specialist",
            "independent-native-speaker",
        )
        records.append(
            {
                "slot_id": slot["slot_id"],
                "media_kind": slot["media_kind"],
                "exact_media_version": "fixture-only-media-v1",
                "display_text_sha256": slot["display_text_sha256"],
                "spoken_text_sha256": slot["spoken_text_sha256"],
                "text_nfc_sha256": slot["text_nfc_sha256"],
                "artifact_sha256": slot["artifact_sha256"],
                "metadata_sha256": slot["metadata_sha256"],
                "heard_playback_result": "approved",
                "reviews": [
                    {
                        "reviewer_id": REVIEWER_BY_ROLE[role],
                        "reviewer_role": role,
                        "reviewed_at": REVIEWED_AT,
                    }
                    for role in roles
                ],
            }
        )
    return {
        "schema_version": 1,
        "playback_version": "fixture-only-playback-v1",
        "audio_request_sha256": _sha256_bytes(audio_request_raw),
        "records": records,
    }


@dataclass(frozen=True)
class EvidenceFixture:
    project_root: Path
    inbox: Path
    index_path: Path
    receipt_path: Path
    active_pointer: Path
    index_sha256: str
    proposed_media: dict[str, Any]


@dataclass(frozen=True)
class CurrentAIMediaEvidenceFixture:
    project_root: Path
    inbox: Path
    index_path: Path
    receipt_path: Path
    active_pointer: Path


def _export_ready_candidates(
    candidates: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return candidates


def _build_complete_fixture(
    tmp_path: Path,
    *,
    export_ready: bool = False,
) -> EvidenceFixture:
    project_root = tmp_path / "fixture-only-korean-foundation-evidence"
    assert "fixture-only" in project_root.as_posix()
    candidate_root = project_root / "data" / "korean_foundations"
    phase_root = (
        project_root
        / ".planning"
        / "phases"
        / "31-hangul-and-pronunciation-i-plus-1"
    )
    inbox = phase_root / "evidence-inbox"
    media_root = inbox / "media"
    (inbox / "reviewers").mkdir(parents=True)
    media_root.mkdir()
    candidate_root.mkdir(parents=True)
    (inbox / "README.md").write_text(
        "FIXTURE ONLY - no production evidence.\n",
        encoding="utf-8",
    )

    registry_raw = _canonical_candidate_path(REGISTRY_FILENAME).read_bytes()
    assert _sha256_bytes(registry_raw) == EXPECTED_REGISTRY_SHA256["file_sha256"]
    (candidate_root / REGISTRY_FILENAME).write_bytes(registry_raw)

    candidates: dict[str, dict[str, Any]] = {}
    for filename in CANDIDATE_FILENAMES:
        raw = _canonical_candidate_path(filename).read_bytes()
        assert _sha256_bytes(raw) == EXPECTED_CANDIDATE_SHA256[filename]
        destination = _fixture_candidate_path(candidate_root, filename)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        candidates[filename] = json.loads(raw.decode("utf-8"))
    if export_ready:
        candidates = _export_ready_candidates(candidates)
        for filename in CANDIDATE_FILENAMES:
            _write_json(
                _fixture_candidate_path(candidate_root, filename),
                candidates[filename],
            )
    requests: dict[str, bytes] = {}
    for filename in REQUEST_FILENAMES:
        raw = (PHASE_ROOT / filename).read_bytes()
        assert _sha256_bytes(raw) == EXPECTED_REQUEST_SHA256[filename]
        (phase_root / filename).write_bytes(raw)
        requests[filename] = raw

    source_entries = [
        *candidates["hangul-v2.json"]["entries"],
        *candidates["pronunciation-i-plus-1-v2.json"]["entries"],
    ]
    entries_by_key = {str(entry["item_key"]): entry for entry in source_entries}

    reviewer_raw: dict[str, bytes] = {}
    for relpath, payload in _reviewer_records().items():
        reviewer_raw[relpath] = _write_json(inbox / relpath, payload)

    proposed_curation = _approved_curation(
        candidates["korean-foundations-v2-curation.json"],
        entries_by_key,
    )
    proposed_curation_raw = _write_json(
        inbox / "proposed-curation.json",
        proposed_curation,
    )
    curriculum_review = _curriculum_review(
        proposed=proposed_curation,
        proposed_raw=proposed_curation_raw,
        curriculum_request_raw=requests["31-CURRICULUM-REVIEW.md"],
    )
    curriculum_review_raw = _write_json(
        inbox / "curriculum-review.json",
        curriculum_review,
    )

    proposed_media, media_members = _approved_media(
        candidate=candidates["korean-foundations-v2-media.json"],
        entries_by_key=entries_by_key,
        media_root=media_root,
    )
    proposed_media_raw = _write_json(inbox / "proposed-media.json", proposed_media)
    rights_raw = _write_json(inbox / "rights.json", _rights_payload(proposed_media))
    playback_raw = _write_json(
        inbox / "audio-playback-review.json",
        _playback_payload(
            proposed_media,
            requests["31-AUDIO-PLAYBACK-REVIEW.md"],
        ),
    )

    evidence_raw = {
        "proposed-curation.json": proposed_curation_raw,
        "proposed-media.json": proposed_media_raw,
        "curriculum-review.json": curriculum_review_raw,
        "audio-playback-review.json": playback_raw,
        "rights.json": rights_raw,
        **reviewer_raw,
        **{
            f"media/{basename}": content
            for basename, content in media_members.items()
        },
    }
    role_by_relpath = {
        "proposed-curation.json": "proposed_curation",
        "proposed-media.json": "proposed_media",
        "curriculum-review.json": "curriculum_review",
        "audio-playback-review.json": "audio_playback_review",
        "rights.json": "rights",
    }
    member_rows = []
    for relpath in FIXED_EVIDENCE_RELPATHS:
        raw = evidence_raw[relpath]
        member_rows.append(
            {
                "relpath": relpath,
                "role": role_by_relpath.get(relpath, "reviewer"),
                "size_bytes": len(raw),
                "sha256": _sha256_bytes(raw),
            }
        )
    for slot in proposed_media["slots"]:
        relpath = f"media/{slot['basename']}"
        raw = evidence_raw[relpath]
        member_rows.append(
            {
                "relpath": relpath,
                "role": "media",
                "size_bytes": len(raw),
                "sha256": _sha256_bytes(raw),
            }
        )

    candidate_bindings = []
    for filename in CANDIDATE_FILENAMES:
        raw = _fixture_candidate_path(candidate_root, filename).read_bytes()
        payload = candidates[filename]
        candidate_bindings.append(_candidate_binding(filename, payload, raw))
    request_bindings = [
        {
            "filename": filename,
            "file_sha256": _sha256_bytes(requests[filename]),
        }
        for filename in REQUEST_FILENAMES
    ]
    index: dict[str, Any] = {
        "schema_version": 1,
        "index_version": "phase31-korean-foundation-evidence-index-v1",
        "layout_version": "phase31-korean-foundation-evidence-layout-v1",
        "policy_version": "phase31-korean-foundation-evidence-policy-v1",
        "candidate_bindings": candidate_bindings,
        "request_bindings": request_bindings,
        "members": member_rows,
        "declared_members_sha256": _canonical_sha256(member_rows),
    }
    index["index_payload_sha256"] = _canonical_sha256(index)
    index_path = inbox / "evidence-index.json"
    index_raw = _write_json(index_path, index)
    return EvidenceFixture(
        project_root=project_root,
        inbox=inbox,
        index_path=index_path,
        receipt_path=inbox / "validation-receipt.json",
        active_pointer=candidate_root / "active-foundations.json",
        index_sha256=_sha256_bytes(index_raw),
        proposed_media=proposed_media,
    )


def _build_current_ai_media_fixture(tmp_path: Path) -> CurrentAIMediaEvidenceFixture:
    project_root = tmp_path / "fixture-only-current-ai-media-evidence"
    candidate_root = project_root / "data" / "korean_foundations"
    phase_root = (
        project_root
        / ".planning"
        / "phases"
        / "31-hangul-and-pronunciation-i-plus-1"
    )
    inbox = phase_root / "evidence-inbox"
    shutil.copytree(PROJECT_ROOT / "data" / "korean_foundations", candidate_root)
    shutil.copytree(CANONICAL_INBOX, inbox)
    (inbox / "validation-receipt.json").unlink(missing_ok=True)
    handoff_root = phase_root / "execution-handoffs"
    handoff_root.mkdir(parents=True)
    shutil.copy2(
        PHASE_ROOT / "execution-handoffs" / "media-authority.json",
        handoff_root / "media-authority.json",
    )
    for filename in REQUEST_FILENAMES:
        shutil.copy2(PHASE_ROOT / filename, phase_root / filename)
    return CurrentAIMediaEvidenceFixture(
        project_root=project_root,
        inbox=inbox,
        index_path=inbox / "evidence-index.json",
        receipt_path=inbox / "validation-receipt.json",
        active_pointer=candidate_root / "active-foundations.json",
    )


def _install_fixture_paths(
    api: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    fixture: EvidenceFixture,
) -> None:
    monkeypatch.setattr(
        api,
        "_FIXED_PATHS",
        api._KoreanFoundationEvidencePaths.from_project_root(fixture.project_root),
    )


def _reason(exc_info: pytest.ExceptionInfo[BaseException]) -> str:
    reason_code = getattr(exc_info.value, "reason_code")
    return getattr(reason_code, "value", reason_code)


def _tree_bytes(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


def _receipt_file_sha256(fixture: EvidenceFixture) -> str:
    return _sha256_bytes(fixture.receipt_path.read_bytes())


def _reseal_index(fixture: EvidenceFixture, mutator: Callable[[dict[str, Any]], None]) -> str:
    payload = json.loads(fixture.index_path.read_text(encoding="utf-8"))
    mutator(payload)
    payload.pop("index_payload_sha256", None)
    payload["index_payload_sha256"] = _canonical_sha256(payload)
    return _sha256_bytes(_write_json(fixture.index_path, payload))


def _rewrite_index_member_hash(fixture: EvidenceFixture, relpath: str) -> str:
    target = fixture.inbox / Path(relpath)

    def update(payload: dict[str, Any]) -> None:
        for member in payload["members"]:
            if member["relpath"] == relpath:
                raw = target.read_bytes()
                member["size_bytes"] = len(raw)
                member["sha256"] = _sha256_bytes(raw)
                break
        payload["declared_members_sha256"] = _canonical_sha256(payload["members"])

    return _reseal_index(fixture, update)


def _lock_worker(
    lock_root: str,
    started: Any,
    acquired: Any,
    release: Any,
) -> None:
    lock_api = import_module("multilang.services._korean_foundation_state_lock")
    started.set()
    with lock_api._korean_foundation_state_lock(Path(lock_root)):
        acquired.set()
        release.wait(10)


def test_layout_module_and_readme_are_required_before_implementation() -> None:
    assert util.find_spec("multilang.services.korean_foundation_evidence") is not None
    assert CANONICAL_INBOX.joinpath("README.md").is_file()


def test_layout_constants_and_canonical_inbox_have_only_technical_readme() -> None:
    api = _evidence()
    expected_inbox = Path(
        ".planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox"
    )
    assert api.PHASE31_EVIDENCE_INBOX == expected_inbox
    assert api.PHASE31_EVIDENCE_INDEX == expected_inbox / "evidence-index.json"
    assert api.PHASE31_VALIDATION_RECEIPT == expected_inbox / "validation-receipt.json"
    assert api.KOREAN_FOUNDATION_EVIDENCE_LAYOUT_VERSION == (
        "phase31-korean-foundation-evidence-layout-v1"
    )
    assert api.KOREAN_FOUNDATION_EVIDENCE_POLICY_VERSION == (
        "phase31-korean-foundation-evidence-policy-v1"
    )
    assert {path.name for path in CANONICAL_INBOX.iterdir()} == {
        "README.md",
        "acoustic-review.json",
        "ai-review",
        "media",
        "media-rights.json",
        "validation-receipt.json",
    }
    readme = CANONICAL_INBOX.joinpath("README.md").read_text(encoding="utf-8")
    for relpath in (
        "evidence-index.json",
        *FIXED_EVIDENCE_RELPATHS,
        "media/<exact basenames declared by proposed-media.json>",
        "validation-receipt.json",
    ):
        assert relpath in readme
    for forbidden in (
        "importer",
        "upload",
        "URL",
        "archive",
        "APKG",
        "source-root",
    ):
        assert forbidden.casefold() in readme.casefold()


def test_no_public_path_surface_and_exactly_one_receipt_writer() -> None:
    api = _evidence()
    expected_signatures = {
        "inspect_fixed_korean_foundation_evidence_inbox": (),
        "validate_and_write_fixed_korean_foundation_validation_receipt": (
            "confirmed_index_sha256",
        ),
        "check_korean_foundation_validation_receipt_continuity": (
            "expected_receipt_sha256",
        ),
    }
    for name, expected in expected_signatures.items():
        assert tuple(inspect.signature(getattr(api, name)).parameters) == expected
    forbidden_fragments = (
        "path",
        "root",
        "url",
        "archive",
        "apkg",
        "import",
        "copy",
        "upload",
        "validated",
        "payload",
        "receipt",
        "bypass",
    )
    for name in api.__all__:
        value = getattr(api, name)
        if not inspect.isfunction(value):
            continue
        parameters = inspect.signature(value).parameters
        if name == "validate_and_write_fixed_korean_foundation_validation_receipt":
            assert tuple(parameters) == ("confirmed_index_sha256",)
            continue
        if name == "check_korean_foundation_validation_receipt_continuity":
            assert tuple(parameters) == ("expected_receipt_sha256",)
            continue
        assert not any(
            fragment in parameter.casefold()
            for parameter in parameters
            for fragment in forbidden_fragments
        )
    public_writers = [
        name
        for name in api.__all__
        if inspect.isfunction(getattr(api, name))
        and any(token in name for token in ("write", "create", "mint", "repair"))
    ]
    assert public_writers == [
        "validate_and_write_fixed_korean_foundation_validation_receipt"
    ]
    with pytest.raises(TypeError):
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256="0" * 64,
            validated=object(),
        )
    with pytest.raises(TypeError):
        api.check_korean_foundation_validation_receipt_continuity(
            expected_receipt_sha256="0" * 64,
            receipt=object(),
        )


def test_assembler_exact_layout_and_canonical_hashes_are_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    first = _build_complete_fixture(tmp_path / "first")
    _install_fixture_paths(api, monkeypatch, first)
    inventory = api.inspect_fixed_korean_foundation_evidence_inbox()
    assert inventory.complete is True
    assert inventory.evidence_member_count == 519
    assert inventory.declared_media_count == 509
    assert inventory.missing_members == ()
    assert inventory.unexpected_members == ()
    assert inventory.index_sha256 == first.index_sha256

    second = _build_complete_fixture(tmp_path / "second")
    _install_fixture_paths(api, monkeypatch, second)
    second_inventory = api.inspect_fixed_korean_foundation_evidence_inbox()
    assert second_inventory.model_dump() == inventory.model_dump()


def test_evidence_contract_binds_exact_v2_candidate_and_request_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    assert api._CANDIDATE_FILENAMES == CANDIDATE_FILENAMES

    fixture = _build_complete_fixture(tmp_path / "valid")
    index = json.loads(fixture.index_path.read_text(encoding="utf-8"))
    candidate_bindings = {
        binding["filename"]: binding for binding in index["candidate_bindings"]
    }
    request_bindings = {
        binding["filename"]: binding for binding in index["request_bindings"]
    }
    assert tuple(candidate_bindings) == CANDIDATE_FILENAMES
    assert {
        filename: binding["file_sha256"]
        for filename, binding in candidate_bindings.items()
    } == EXPECTED_CANDIDATE_SHA256
    assert {
        filename: binding["file_sha256"]
        for filename, binding in request_bindings.items()
    } == EXPECTED_REQUEST_SHA256
    assert candidate_bindings["current-candidate.json"] == {
        "filename": "current-candidate.json",
        "bundle_sha256": CURRENT_BUNDLE_SHA256,
        "bundle_relpath": CURRENT_BUNDLE_RELPATH,
        "bundle_manifest_sha256": EXPECTED_CANDIDATE_SHA256["bundle-manifest.json"],
        "file_sha256": EXPECTED_CANDIDATE_SHA256["current-candidate.json"],
    }
    assert candidate_bindings["bundle-manifest.json"] == {
        "filename": "bundle-manifest.json",
        "bundle_sha256": CURRENT_BUNDLE_SHA256,
        "selected_draft_manifest_sha256": (
            "2cbab1150d862511a66c22a902737df1d65601a9f38351b0a97aecad852f7cf2"
        ),
        "draft_validation_sha256": (
            "a300a5376119d3e2fb4a734390d61e2cf0c5f8db794f758c95ad4de64aa2fb78"
        ),
        "file_sha256": EXPECTED_CANDIDATE_SHA256["bundle-manifest.json"],
        "total_record_count": 139,
        "media_slot_count": 509,
    }
    serialized_index = json.dumps(index, sort_keys=True)
    assert "hangul-v1.json" not in serialized_index
    assert "pronunciation-i-plus-1-v1.json" not in serialized_index
    _install_fixture_paths(api, monkeypatch, fixture)
    receipt = api.validate_and_write_fixed_korean_foundation_validation_receipt(
        confirmed_index_sha256=fixture.index_sha256
    )
    assert receipt.confirmed_index_sha256 == fixture.index_sha256
    assert fixture.receipt_path.is_file()

    def stale_v1_binding(stale_fixture: EvidenceFixture) -> str:
        def mutate(payload: dict[str, Any]) -> None:
            payload["candidate_bindings"][2] = {
                "filename": "hangul-v1.json",
                "version": "hangul-v1",
                "file_sha256": "0" * 64,
                "canonical_content_sha256": "1" * 64,
            }

        return _reseal_index(stale_fixture, mutate)

    def draft_binding(stale_fixture: EvidenceFixture) -> str:
        def mutate(payload: dict[str, Any]) -> None:
            payload["candidate_bindings"][2]["filename"] = "hangul-v2-draft.json"

        return _reseal_index(stale_fixture, mutate)

    def stale_request_binding(stale_fixture: EvidenceFixture) -> str:
        def mutate(payload: dict[str, Any]) -> None:
            payload["request_bindings"][0]["file_sha256"] = (
                "788aea87abb9d710617b86d8e05878151184d9ec92e4d3f0e013747c3655ae57"
            )

        return _reseal_index(stale_fixture, mutate)

    def mixed_v1_manifest_binding(stale_fixture: EvidenceFixture) -> str:
        def mutate(payload: dict[str, Any]) -> None:
            payload["candidate_bindings"][4] = {
                "filename": "korean-foundations-v1-curation.json",
                "version": "korean-foundations-v1-curation",
                "file_sha256": "2" * 64,
                "canonical_content_sha256": "3" * 64,
            }

        return _reseal_index(stale_fixture, mutate)

    def incomplete_member(stale_fixture: EvidenceFixture) -> str:
        candidate_root = stale_fixture.project_root / "data" / "korean_foundations"
        _fixture_candidate_path(
            candidate_root,
            "korean-foundations-v2-media.json",
        ).unlink()
        return stale_fixture.index_sha256

    cases: tuple[tuple[str, Callable[[EvidenceFixture], str], str], ...] = (
        ("v1-binding", stale_v1_binding, "index_invalid"),
        ("draft-binding", draft_binding, "index_invalid"),
        ("stale-request", stale_request_binding, "source_binding_mismatch"),
        ("mixed-v1-manifest", mixed_v1_manifest_binding, "index_invalid"),
        ("incomplete-member", incomplete_member, "source_binding_mismatch"),
    )
    for case_name, mutate, expected_reason in cases:
        case_fixture = _build_complete_fixture(tmp_path / case_name)
        _install_fixture_paths(api, monkeypatch, case_fixture)
        confirmed = mutate(case_fixture)
        before = _tree_bytes(case_fixture.project_root)
        with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
            api.validate_and_write_fixed_korean_foundation_validation_receipt(
                confirmed_index_sha256=confirmed
            )
        assert _reason(exc_info) == expected_reason
        assert case_fixture.receipt_path.exists() is False
        assert not tuple(case_fixture.inbox.glob(".validation-receipt.*.tmp"))
        assert _tree_bytes(case_fixture.project_root) == before


def test_current_ai_media_inbox_derives_ai_passed_manifests_and_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_current_ai_media_fixture(tmp_path)
    assert fixture.index_path.exists() is False
    _install_fixture_paths(api, monkeypatch, fixture)  # type: ignore[arg-type]

    inventory = api.inspect_fixed_korean_foundation_evidence_inbox()

    assert inventory.complete is True
    assert inventory.declared_media_count == 325
    assert inventory.missing_members == ()
    assert inventory.unexpected_members == ()
    assert inventory.index_sha256 is not None

    receipt = api.validate_and_write_fixed_korean_foundation_validation_receipt(
        confirmed_index_sha256=inventory.index_sha256
    )

    assert fixture.receipt_path.is_file()
    assert fixture.index_path.exists() is False
    assert receipt.reviewer_evidence_sha256 == CURRENT_AI_AGGREGATE_ROOT
    assert receipt.rights_evidence_sha256 == CURRENT_MEDIA_RIGHTS_SHA256
    assert receipt.media_evidence_sha256 == CURRENT_ACOUSTIC_AGGREGATE_ROOT

    validated = api._validate_fixed_evidence(
        api._FIXED_PATHS,
        confirmed_index_sha256=inventory.index_sha256,
    )
    curation = api.KoreanFoundationCurationManifest.model_validate_json(
        validated.layout.members["proposed-curation.json"]
    )
    media = api.KoreanFoundationMediaManifest.model_validate_json(
        validated.layout.members["proposed-media.json"]
    )
    member_hashes = {
        member.relpath: member.sha256 for member in validated.layout.index.members
    }

    assert curation.candidate_only is False
    assert {
        gate.status
        for record in curation.records
        for gate in record.gates
    } == {"ai_review_passed"}
    assert all(
        gate.reviewer_id is None and gate.reviewer_role is None
        for record in curation.records
        for gate in record.gates
    )
    assert media.candidate_only is False
    assert sum(slot.required and slot.status == "approved" for slot in media.slots) == 325
    assert sum((not slot.required) and slot.status == "needs_review" for slot in media.slots) == 184
    assert all(
        slot.review_receipts == ()
        for slot in media.slots
        if slot.required and slot.status == "approved"
    )
    assert member_hashes["ai-review/aggregate.json"] == (
        "3acfd8c27b05d6f4415d294617d251f985a84243faeee96c7d61dbc03e559a69"
    )
    assert member_hashes["media-rights.json"] == CURRENT_MEDIA_RIGHTS_SHA256
    assert member_hashes["media/artifacts.json"] == (
        "825e361707e56b77c2c1e26441751afcaa9b9573c3b1decb5eeb5601819a3254"
    )
    assert member_hashes["execution-handoffs/media-authority.json"] == (
        CURRENT_MEDIA_AUTHORITY_SHA256
    )


def test_current_ai_media_artifact_metadata_corruption_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from multilang.services.ai_acoustic_review import ai_acoustic_review_sha256

    api = _evidence()
    fixture = _build_current_ai_media_fixture(tmp_path)
    artifacts_path = fixture.inbox / "media" / "artifacts.json"
    artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
    artifacts["artifacts"][0].pop("provider_id")
    artifacts["content_hash"] = api._canonical_sha256(artifacts["artifacts"])
    artifacts_path.write_bytes(api._json_file_bytes(artifacts))

    acoustic_path = fixture.inbox / "acoustic-review.json"
    acoustic = json.loads(acoustic_path.read_text(encoding="utf-8"))
    acoustic["media_artifacts_sha256"] = artifacts["content_hash"]
    acoustic["aggregate_root"] = ai_acoustic_review_sha256(acoustic)
    acoustic_path.write_bytes(api._json_file_bytes(acoustic))
    _install_fixture_paths(api, monkeypatch, fixture)  # type: ignore[arg-type]

    inventory = api.inspect_fixed_korean_foundation_evidence_inbox()
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=inventory.index_sha256
        )

    assert exc_info.value.reason_code is api.KoreanFoundationEvidenceReasonCode.MEDIA_INVALID


@pytest.mark.parametrize(
    "unsafe_relpath",
    [
        "../escape.json",
        "/absolute.json",
        "C:/drive.json",
        "reviewers\\escape.json",
        "https://example.invalid/evidence.json",
        "media/fixture.apkg",
        "media/fixture.zip",
    ],
)
def test_assembler_rejects_traversal_drives_urls_archives_and_backslashes(
    unsafe_relpath: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_complete_fixture(tmp_path)
    _install_fixture_paths(api, monkeypatch, fixture)

    def mutate(payload: dict[str, Any]) -> None:
        payload["members"][0]["relpath"] = unsafe_relpath
        payload["declared_members_sha256"] = _canonical_sha256(payload["members"])

    confirmed = _reseal_index(fixture, mutate)
    before = _tree_bytes(fixture.project_root)
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=confirmed
        )
    assert _reason(exc_info) in {"index_invalid", "unsafe_member"}
    assert _tree_bytes(fixture.project_root) == before
    assert str(fixture.project_root) not in str(exc_info.value)


def test_assembler_rejects_extra_missing_archive_magic_and_unbounded_members(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    cases: list[tuple[str, Callable[[EvidenceFixture], None], str]] = [
        (
            "extra",
            lambda fixture: (fixture.inbox / "unexpected.json").write_text(
                "{}\n", encoding="utf-8"
            ),
            "unexpected_member",
        ),
        (
            "missing",
            lambda fixture: (fixture.inbox / "rights.json").unlink(),
            "member_missing",
        ),
        (
            "archive-magic",
            lambda fixture: (fixture.inbox / "media" / "hangul-audio-0001.wav").write_bytes(
                b"PK\x03\x04FIXTURE-ARCHIVE"
            ),
            "archive_member",
        ),
        (
            "oversized-index",
            lambda fixture: fixture.index_path.write_bytes(b"{" + b" " * 5_000_000),
            "member_oversized",
        ),
    ]
    for case_name, mutate, expected_reason in cases:
        case_root = tmp_path / case_name
        case_root.mkdir()
        fixture = _build_complete_fixture(case_root)
        _install_fixture_paths(api, monkeypatch, fixture)
        mutate(fixture)
        confirmed = _sha256_bytes(fixture.index_path.read_bytes())
        before = _tree_bytes(fixture.project_root)
        with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
            api.validate_and_write_fixed_korean_foundation_validation_receipt(
                confirmed_index_sha256=confirmed
            )
        assert _reason(exc_info) == expected_reason
        assert _tree_bytes(fixture.project_root) == before


def test_assembler_rejects_symlink_and_simulated_windows_reparse_content_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_complete_fixture(tmp_path)
    _install_fixture_paths(api, monkeypatch, fixture)
    rights_path = fixture.inbox / "rights.json"
    original_lstat = Path.lstat

    def reparse_lstat(path: Path) -> os.stat_result:
        result = original_lstat(path)
        if path == rights_path:
            values = list(result)
            replacement = os.stat_result(values)
            object.__setattr__(replacement, "st_file_attributes", 0x400)
            return replacement
        return result

    if os.name == "nt":
        monkeypatch.setattr(api, "_stat_is_link_or_reparse", lambda value: (
            getattr(value, "st_ino", None) == rights_path.stat().st_ino
            or stat.S_ISLNK(value.st_mode)
        ))
    else:
        target = fixture.project_root / "fixture-only-outside.json"
        target.write_text("{}\n", encoding="utf-8")
        rights_path.unlink()
        rights_path.symlink_to(target)
    before = _tree_bytes(fixture.project_root)
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=fixture.index_sha256
        )
    assert _reason(exc_info) == "unsafe_filesystem_component"
    assert fixture.receipt_path.exists() is False
    assert not tuple(fixture.inbox.glob(".validation-receipt.*.tmp"))
    assert _tree_bytes(fixture.project_root) == before
    assert str(rights_path) not in str(exc_info.value)


def test_combined_validate_and_write_success_is_atomic_and_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_complete_fixture(tmp_path)
    _install_fixture_paths(api, monkeypatch, fixture)
    before = _tree_bytes(fixture.project_root)
    receipt = api.validate_and_write_fixed_korean_foundation_validation_receipt(
        confirmed_index_sha256=fixture.index_sha256
    )
    assert fixture.receipt_path.is_file()
    assert not tuple(fixture.inbox.glob(".validation-receipt.*.tmp"))
    after = _tree_bytes(fixture.project_root)
    changed = set(after) ^ set(before)
    assert changed == {".planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/validation-receipt.json"}
    payload = json.loads(fixture.receipt_path.read_text(encoding="utf-8"))
    unsigned = deepcopy(payload)
    payload_sha256 = unsigned.pop("payload_sha256")
    assert payload_sha256 == _canonical_sha256(unsigned)
    assert receipt.payload_sha256 == payload_sha256
    assert receipt.confirmed_index_sha256 == fixture.index_sha256
    assert receipt.active_prestate_marker == "absent"
    assert receipt.evidence_bundle_sha256
    assert receipt.source_evidence_sha256
    assert receipt.reviewer_evidence_sha256
    assert receipt.rights_evidence_sha256
    assert receipt.media_evidence_sha256

    receipt_bytes = fixture.receipt_path.read_bytes()
    receipt_mtime = fixture.receipt_path.stat().st_mtime_ns
    retry = api.validate_and_write_fixed_korean_foundation_validation_receipt(
        confirmed_index_sha256=fixture.index_sha256
    )
    assert retry == receipt
    assert fixture.receipt_path.read_bytes() == receipt_bytes
    assert fixture.receipt_path.stat().st_mtime_ns == receipt_mtime


@pytest.mark.parametrize(
    ("case_name", "mutator", "expected_reason"),
    [
        (
            "reviewer-role-collapse",
            lambda fixture: _mutate_reviewer_identity_collapse(fixture),
            "reviewer_qualification_invalid",
        ),
        (
            "rights-reuse",
            lambda fixture: _mutate_rights_reuse(fixture),
            "rights_invalid",
        ),
        (
            "spoken-text",
            lambda fixture: _mutate_playback_text_hash(fixture),
            "playback_invalid",
        ),
        (
            "media-hash",
            lambda fixture: _mutate_media_byte(fixture),
            "media_hash_mismatch",
        ),
        (
            "source-byte",
            lambda fixture: _mutate_candidate_source(fixture),
            "source_binding_mismatch",
        ),
    ],
)
def test_qualification_distinct_role_rights_media_text_and_hash_fail_zero_write(
    case_name: str,
    mutator: Callable[[EvidenceFixture], str],
    expected_reason: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    case_root = tmp_path / case_name
    case_root.mkdir()
    fixture = _build_complete_fixture(case_root)
    _install_fixture_paths(api, monkeypatch, fixture)
    confirmed = mutator(fixture)
    before = _tree_bytes(fixture.project_root)
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=confirmed
        )
    assert _reason(exc_info) == expected_reason
    assert _tree_bytes(fixture.project_root) == before
    assert fixture.receipt_path.exists() is False
    assert not tuple(fixture.inbox.glob(".validation-receipt.*.tmp"))


def _mutate_reviewer_identity_collapse(fixture: EvidenceFixture) -> str:
    path = fixture.inbox / "reviewers" / "independent-native-speaker.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["reviewer_id"] = REVIEWER_BY_ROLE["korean-phonetics-specialist"]
    qualification = {
        key: payload[key]
        for key in (
            "reviewer_id",
            "primary_role",
            "qualified_roles",
            "qualification_status",
            "reviewed_at",
        )
    }
    payload["qualification_evidence_sha256"] = _canonical_sha256(qualification)
    _write_json(path, payload)
    return _rewrite_index_member_hash(
        fixture, "reviewers/independent-native-speaker.json"
    )


def _mutate_rights_reuse(fixture: EvidenceFixture) -> str:
    path = fixture.inbox / "rights.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["records"][0]["reuse_disposition"] = "rejected"
    _write_json(path, payload)
    return _rewrite_index_member_hash(fixture, "rights.json")


def _mutate_playback_text_hash(fixture: EvidenceFixture) -> str:
    path = fixture.inbox / "audio-playback-review.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["records"][0]["spoken_text_sha256"] = "f" * 64
    _write_json(path, payload)
    return _rewrite_index_member_hash(fixture, "audio-playback-review.json")


def _mutate_media_byte(fixture: EvidenceFixture) -> str:
    path = fixture.inbox / "media" / "hangul-audio-0001.wav"
    raw = bytearray(path.read_bytes())
    raw[-1] ^= 0x01
    path.write_bytes(bytes(raw))
    return fixture.index_sha256


def _mutate_candidate_source(fixture: EvidenceFixture) -> str:
    candidate_root = fixture.project_root / "data" / "korean_foundations"
    path = _fixture_candidate_path(candidate_root, "hangul-v2.json")
    raw = bytearray(path.read_bytes())
    raw[-2] = ord(" ")
    path.write_bytes(bytes(raw))
    return fixture.index_sha256


def test_stale_or_conflicting_receipt_is_never_overwritten_or_repaired(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_complete_fixture(tmp_path)
    _install_fixture_paths(api, monkeypatch, fixture)
    api.validate_and_write_fixed_korean_foundation_validation_receipt(
        confirmed_index_sha256=fixture.index_sha256
    )
    payload = json.loads(fixture.receipt_path.read_text(encoding="utf-8"))
    payload["continuity_token"] = "f" * 64
    stale = _json_file_bytes(payload)
    fixture.receipt_path.write_bytes(stale)
    before = _tree_bytes(fixture.project_root)
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=fixture.index_sha256
        )
    assert _reason(exc_info) == "stale_receipt"
    assert fixture.receipt_path.read_bytes() == stale
    assert _tree_bytes(fixture.project_root) == before
    assert not tuple(fixture.inbox.glob(".validation-receipt.*.tmp"))


@pytest.mark.parametrize(
    "stage",
    ["after_validation", "after_payload_derivation", "before_write"],
)
def test_between_stage_evidence_drift_is_detected_before_any_receipt_write(
    stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_complete_fixture(tmp_path)
    _install_fixture_paths(api, monkeypatch, fixture)
    rights_path = fixture.inbox / "rights.json"
    original = rights_path.read_bytes()

    def hook(current_stage: str, _paths: object) -> None:
        if current_stage == stage:
            rights_path.write_bytes(original + b" ")

    monkeypatch.setattr(api, "_PRIVATE_STAGE_HOOK", hook)
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=fixture.index_sha256
        )
    assert _reason(exc_info) == "between_stage_drift"
    assert rights_path.read_bytes() == original + b" "
    assert fixture.receipt_path.exists() is False
    assert not tuple(fixture.inbox.glob(".validation-receipt.*.tmp"))


@pytest.mark.parametrize(
    "stage",
    ["after_validation", "after_payload_derivation", "before_write"],
)
def test_between_stage_active_prestate_drift_is_detected_without_stale_refresh(
    stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_complete_fixture(tmp_path)
    _install_fixture_paths(api, monkeypatch, fixture)
    pointer_bytes = _json_file_bytes(
        {
            "schema_version": 1,
            "bundle_sha256": "1" * 64,
            "snapshot_relpath": f"snapshots/{'1' * 64}",
            "snapshot_manifest_sha256": "2" * 64,
        }
    )

    def hook(current_stage: str, _paths: object) -> None:
        if current_stage == stage:
            fixture.active_pointer.write_bytes(pointer_bytes)

    monkeypatch.setattr(api, "_PRIVATE_STAGE_HOOK", hook)
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=fixture.index_sha256
        )
    assert _reason(exc_info) == "between_stage_drift"
    assert fixture.active_pointer.read_bytes() == pointer_bytes
    assert fixture.receipt_path.exists() is False
    assert not tuple(fixture.inbox.glob(".validation-receipt.*.tmp"))


def test_read_only_continuity_accepts_exact_state_and_uses_no_write_primitive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    fixture = _build_complete_fixture(tmp_path)
    _install_fixture_paths(api, monkeypatch, fixture)
    receipt = api.validate_and_write_fixed_korean_foundation_validation_receipt(
        confirmed_index_sha256=fixture.index_sha256
    )
    expected_hash = _receipt_file_sha256(fixture)
    before = _tree_bytes(fixture.project_root)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("continuity attempted a write")

    monkeypatch.setattr(api.tempfile, "mkstemp", forbidden)
    monkeypatch.setattr(api.os, "replace", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    report = api.check_korean_foundation_validation_receipt_continuity(
        expected_receipt_sha256=expected_hash
    )
    assert report.continuous is True
    assert report.receipt_sha256 == expected_hash
    assert report.payload_sha256 == receipt.payload_sha256
    assert _tree_bytes(fixture.project_root) == before


@pytest.mark.parametrize(
    ("case_name", "mutator", "expected_reason"),
    [
        (
            "receipt-hash-first",
            lambda fixture: fixture.receipt_path.write_bytes(
                fixture.receipt_path.read_bytes() + b" "
            ),
            "receipt_hash_mismatch",
        ),
        (
            "index",
            lambda fixture: fixture.index_path.write_bytes(
                fixture.index_path.read_bytes() + b" "
            ),
            "continuity_drift",
        ),
        (
            "reviewer",
            lambda fixture: (fixture.inbox / "reviewers" / "portuguese.json").write_bytes(
                (fixture.inbox / "reviewers" / "portuguese.json").read_bytes()
                + b" "
            ),
            "continuity_drift",
        ),
        (
            "rights",
            lambda fixture: (fixture.inbox / "rights.json").write_bytes(
                (fixture.inbox / "rights.json").read_bytes() + b" "
            ),
            "continuity_drift",
        ),
        (
            "media",
            lambda fixture: (fixture.inbox / "media" / "hangul-audio-0001.wav").write_bytes(
                (fixture.inbox / "media" / "hangul-audio-0001.wav").read_bytes()
                + b" "
            ),
            "continuity_drift",
        ),
        (
            "source",
            lambda fixture: (
                fixture.project_root
                / "data"
                / "korean_foundations"
                / CURRENT_BUNDLE_RELPATH
                / "hangul-v2.json"
            ).write_bytes(
                (
                    fixture.project_root
                    / "data"
                    / "korean_foundations"
                    / CURRENT_BUNDLE_RELPATH
                    / "hangul-v2.json"
                ).read_bytes()
                + b" "
            ),
            "continuity_drift",
        ),
        (
            "prestate",
            lambda fixture: fixture.active_pointer.write_bytes(
                _json_file_bytes(
                    {
                        "schema_version": 1,
                        "bundle_sha256": "3" * 64,
                        "snapshot_relpath": f"snapshots/{'3' * 64}",
                        "snapshot_manifest_sha256": "4" * 64,
                    }
                )
            ),
            "continuity_drift",
        ),
    ],
)
def test_read_only_continuity_rejects_each_drift_without_repair(
    case_name: str,
    mutator: Callable[[EvidenceFixture], object],
    expected_reason: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _evidence()
    case_root = tmp_path / case_name
    case_root.mkdir()
    fixture = _build_complete_fixture(case_root)
    _install_fixture_paths(api, monkeypatch, fixture)
    api.validate_and_write_fixed_korean_foundation_validation_receipt(
        confirmed_index_sha256=fixture.index_sha256
    )
    expected_hash = _receipt_file_sha256(fixture)
    mutator(fixture)
    before = _tree_bytes(fixture.project_root)
    receipt_before = fixture.receipt_path.read_bytes()
    with pytest.raises(api.KoreanFoundationEvidenceError) as exc_info:
        api.check_korean_foundation_validation_receipt_continuity(
            expected_receipt_sha256=expected_hash
        )
    assert _reason(exc_info) == expected_reason
    assert fixture.receipt_path.read_bytes() == receipt_before
    assert _tree_bytes(fixture.project_root) == before
    assert not tuple(fixture.inbox.glob(".validation-receipt.*.tmp"))


def test_shared_private_state_lock_serializes_across_processes(tmp_path: Path) -> None:
    lock_api = import_module("multilang.services._korean_foundation_state_lock")
    lock_root = tmp_path / "fixture-only-shared-state-lock"
    lock_root.mkdir()
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    acquired = context.Event()
    release = context.Event()
    process = context.Process(
        target=_lock_worker,
        args=(str(lock_root), started, acquired, release),
    )
    with lock_api._korean_foundation_state_lock(lock_root):
        process.start()
        assert started.wait(5)
        assert acquired.wait(0.4) is False
    assert acquired.wait(5)
    release.set()
    process.join(10)
    assert process.exitcode == 0
    assert tuple(lock_root.iterdir()) == ()
    assert lock_api.KOREAN_FOUNDATION_STATE_LOCK_VERSION == (
        "phase31-korean-foundation-state-lock-v1"
    )


def test_public_source_has_no_importer_provider_network_or_forged_writer_surface() -> None:
    api = _evidence()
    source = inspect.getsource(api).casefold()
    for forbidden in (
        "azurespeechadapter",
        "requests.",
        "httpx.",
        "urllib.request",
        "tatoeba",
        "openai",
        "allow_unapproved",
        "source_root:",
        "inbox_root:",
        "receipt_payload:",
        "validated_evidence:",
    ):
        assert forbidden not in source
    assert source.count(
        "def validate_and_write_fixed_korean_foundation_validation_receipt("
    ) == 1
    assert source.count("from multilang.services._korean_foundation_state_lock import") == 1


def test_canonical_candidates_requests_and_production_roots_remain_untouched() -> None:
    for filename, expected_hash in EXPECTED_CANDIDATE_SHA256.items():
        path = _canonical_candidate_path(filename)
        assert _sha256_bytes(path.read_bytes()) == expected_hash
    registry_path = _canonical_candidate_path(REGISTRY_FILENAME)
    assert _sha256_bytes(registry_path.read_bytes()) == (
        EXPECTED_REGISTRY_SHA256["file_sha256"]
    )
    for filename, expected_hash in EXPECTED_REQUEST_SHA256.items():
        path = PHASE_ROOT / filename
        assert _sha256_bytes(path.read_bytes()) == expected_hash
    assert {path.name for path in CANONICAL_INBOX.iterdir()} == {
        "README.md",
        "acoustic-review.json",
        "ai-review",
        "media",
        "media-rights.json",
        "validation-receipt.json",
    }
    receipt_path = CANONICAL_INBOX / "validation-receipt.json"
    assert receipt_path.is_file()
    active_path = PROJECT_ROOT / "data/korean_foundations/active-foundations.json"
    assert active_path.is_file()
    active_pointer = json.loads(active_path.read_text(encoding="utf-8"))
    assert active_pointer["receipt_sha256"] == _sha256_bytes(receipt_path.read_bytes())
    snapshot_root = PROJECT_ROOT / "data/korean_foundations" / active_pointer["snapshot_relpath"]
    snapshot_manifest = snapshot_root / "snapshot-manifest.json"
    assert snapshot_manifest.is_file()
    assert active_pointer["snapshot_manifest_sha256"] == _sha256_bytes(
        snapshot_manifest.read_bytes()
    )
    assert not (PROJECT_ROOT / "exports/korean_foundations").exists()
