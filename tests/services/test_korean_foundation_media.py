"""Licensed exact-byte media gates for Korean foundation snapshots."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
import inspect
import io
import json
import os
from pathlib import Path
import stat
import struct
from types import ModuleType, SimpleNamespace
import unicodedata
import wave
import zlib

import pytest
from pydantic import ValidationError


def _media() -> ModuleType:
    assert util.find_spec("multilang.services.korean_foundation_media") is not None, (
        "the Korean foundation media service must exist"
    )
    return import_module("multilang.services.korean_foundation_media")


def _curriculum() -> ModuleType:
    return import_module("multilang.services.korean_curriculum")


def _snapshot_module() -> ModuleType:
    return import_module("multilang.services.korean_foundation_snapshot")


def _reason(exc_info: pytest.ExceptionInfo[BaseException]) -> str:
    reason_code = getattr(exc_info.value, "reason_code")
    return getattr(reason_code, "value", reason_code)


def _text_hash(value: str) -> str:
    return sha256(unicodedata.normalize("NFC", value).encode("utf-8")).hexdigest()


def _pcm_wav_bytes(*, duration_ms: int = 100) -> bytes:
    frame_rate = 16_000
    frame_count = frame_rate * duration_ms // 1_000
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(frame_rate)
        wav_file.writeframes(b"\x00\x01" * frame_count)
    return buffer.getvalue()


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


def _source_entries() -> tuple[dict[str, object], dict[str, object], object, object]:
    curriculum = _curriculum()
    hangul = curriculum.load_korean_hangul_source_pack()
    pronunciation = curriculum.load_korean_pronunciation_source_pack()
    by_item = {
        entry.item_key: entry for entry in (*hangul.entries, *pronunciation.entries)
    }
    by_slot = {
        slot.slot_id: entry
        for entry in (*hangul.entries, *pronunciation.entries)
        for slot in entry.media_slots
    }
    return by_item, by_slot, hangul, pronunciation


def _display_text(slot: object, entry: object) -> str:
    media_kind = getattr(slot, "media_kind")
    if getattr(slot, "family") == "hangul":
        mapping = getattr(entry, "pedagogical_jamo_mapping")
        return (
            mapping.display_glyph
            if mapping is not None
            else getattr(entry, "canonical_jamo_or_block")
        )
    if media_kind == "letter_audio":
        return getattr(entry, "spellings")
    if media_kind == "word_audio":
        return getattr(entry, "example_word")
    return getattr(entry, "example_sentence")


def _spoken_text(slot: object, entry: object, display_text: str) -> str | None:
    media_kind = getattr(slot, "media_kind")
    if media_kind in {"picture", "strokes", "gif"}:
        return None
    if getattr(slot, "family") == "hangul":
        return "테스트 전용 한글 음성"
    if media_kind == "letter_audio":
        return "테스트 전용 발음 문맥"
    return display_text


def _review_receipts(
    api: ModuleType,
    *,
    media_kind: str,
    artifact_hash: str,
    metadata_hash: str,
) -> list[dict[str, object]]:
    roles = ["media-rights-reviewer", "media-integrity-reviewer"]
    if media_kind in {"audio", "letter_audio", "word_audio", "sentence_audio"}:
        roles.extend(
            [
                "audio-playback-reviewer",
                "korean-phonetics-specialist",
                "independent-native-speaker",
            ]
        )
    return [
        {
            "reviewer_id": f"test-reviewer-{role}",
            "reviewer_role": role,
            "reviewed_at": "2026-08-05T00:00:00Z",
            "artifact_sha256": artifact_hash,
            "metadata_sha256": metadata_hash,
        }
        for role in roles
    ]


def _approved_slot(
    api: ModuleType,
    pending: object,
    entry: object,
    content: bytes,
) -> object:
    display_text = _display_text(pending, entry)
    spoken_text = _spoken_text(pending, entry, display_text)
    text_nfc = unicodedata.normalize("NFC", spoken_text or display_text)
    is_audio = getattr(pending, "media_kind") in {
        "audio",
        "letter_audio",
        "word_audio",
        "sentence_audio",
    }
    artifact_hash = sha256(content).hexdigest()
    payload = pending.model_dump(mode="json")
    payload.update(
        {
            "status": "approved",
            "reason_code": None,
            "source_id": "test-media-source",
            "source_version": "test-media-source-v1",
            "attribution": "TEST FIXTURE ONLY - NOT PRODUCTION EVIDENCE",
            "license_id": "test-fixture-license",
            "redistribution_disposition": "approved",
            "display_text": display_text,
            "spoken_text": spoken_text,
            "text_nfc": text_nfc,
            "display_text_sha256": _text_hash(display_text),
            "spoken_text_sha256": (
                _text_hash(spoken_text) if spoken_text is not None else None
            ),
            "text_nfc_sha256": _text_hash(text_nfc),
            "provider": "test-fixture-local" if is_audio else None,
            "provider_version": "test-fixture-v1" if is_audio else None,
            "voice_id": "test-voice-not-for-production" if is_audio else None,
            "locale": "ko-KR" if is_audio else None,
            "ssml_sha256": _text_hash("test-ssml") if is_audio else None,
            "prosody_sha256": _text_hash("test-prosody") if is_audio else None,
            "duration_ms": 100 if is_audio else None,
            "artifact_sha256": artifact_hash,
            "reviewed_artifact_sha256": artifact_hash,
            "metadata_sha256": "0" * 64,
            "reviewed_metadata_sha256": "0" * 64,
            "review_receipts": [],
        }
    )
    metadata_hash = api.korean_foundation_media_metadata_sha256(payload)
    payload["metadata_sha256"] = metadata_hash
    payload["reviewed_metadata_sha256"] = metadata_hash
    payload["review_receipts"] = _review_receipts(
        api,
        media_kind=getattr(pending, "media_kind"),
        artifact_hash=artifact_hash,
        metadata_hash=metadata_hash,
    )
    return api.KoreanFoundationMediaSlot.model_validate(payload)


def _reseal_manifest(api: ModuleType, manifest: object, slots: list[object]) -> object:
    payload = manifest.model_dump(mode="json")
    payload["candidate_only"] = False
    payload["slots"] = [slot.model_dump(mode="json") for slot in slots]
    payload.pop("content_hash", None)
    payload["content_hash"] = api.korean_foundation_media_manifest_sha256(payload)
    return api.KoreanFoundationMediaManifest.model_validate(payload)


def _snapshot_with_manifest(
    api: ModuleType,
    tmp_path: Path,
    manifest: object,
    *,
    write_files: bool = True,
) -> object:
    snapshot_api = _snapshot_module()
    _, by_slot, hangul, pronunciation = _source_entries()
    media_members = []
    for slot in manifest.slots:
        if slot.status != "approved":
            continue
        content = (
            _pcm_wav_bytes()
            if slot.media_kind
            in {"audio", "letter_audio", "word_audio", "sentence_audio"}
            else _png_bytes()
        )
        assert slot.slot_id in by_slot
        path = tmp_path.joinpath(*slot.storage_relpath.split("/"))
        if write_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        media_members.append(
            snapshot_api.ResolvedKoreanFoundationSnapshotMember(
                role="media",
                relpath=slot.storage_relpath,
                path=path,
                size_bytes=len(content),
                sha256=sha256(content).hexdigest(),
                content=content,
            )
        )
    return SimpleNamespace(
        concept_registry=_curriculum().load_korean_concept_registry(),
        hangul_source_pack=hangul,
        pronunciation_source_pack=pronunciation,
        snapshot_root=tmp_path,
        media_root=tmp_path / "media",
        media_manifest_bytes=(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False) + "\n"
        ).encode("utf-8"),
        media_members=tuple(media_members),
    )


def _approved_fixture(
    tmp_path: Path,
) -> tuple[ModuleType, object, object]:
    api = _media()
    pending = api.load_pending_korean_foundation_media_manifest()
    _, by_slot, _, _ = _source_entries()
    slots = []
    for slot in pending.slots:
        if not slot.required:
            slots.append(slot)
            continue
        content = (
            _pcm_wav_bytes()
            if slot.media_kind
            in {"audio", "letter_audio", "word_audio", "sentence_audio"}
            else _png_bytes()
        )
        slots.append(_approved_slot(api, slot, by_slot[slot.slot_id], content))
    manifest = _reseal_manifest(api, pending, slots)
    snapshot = _snapshot_with_manifest(api, tmp_path, manifest)
    return api, manifest, snapshot


def _replace_slot(manifest: object, replacement: object) -> object:
    return manifest.model_copy(
        update={
            "slots": tuple(
                replacement if slot.slot_id == replacement.slot_id else slot
                for slot in manifest.slots
            )
        }
    )


def test_media_public_contract_has_no_path_or_url_production_inputs() -> None:
    api = _media()

    assert tuple(
        inspect.signature(api.load_pending_korean_foundation_media_manifest).parameters
    ) == ()
    assert tuple(
        inspect.signature(api.load_korean_v1_foundation_media_manifest).parameters
    ) == ()
    assert tuple(inspect.signature(api.assert_korean_foundation_media_ready).parameters) == (
        "snapshot",
    )
    assert tuple(inspect.signature(api.resolve_korean_foundation_media).parameters) == (
        "snapshot",
    )
    assert tuple(
        inspect.signature(api.assert_active_korean_foundation_media_ready).parameters
    ) == ()
    assert tuple(
        inspect.signature(api.resolve_active_korean_foundation_media).parameters
    ) == ()
    source = inspect.getsource(api).casefold()
    for forbidden in (
        "azurespeechadapter",
        "requests.",
        "httpx.",
        "urllib.request",
        "tatoeba",
        "openai",
    ):
        assert forbidden not in source


def test_committed_media_candidate_has_every_slot_pending_inactive_and_byte_free() -> None:
    api = _media()
    curriculum = _curriculum()
    manifest = api.load_pending_korean_foundation_media_manifest()
    hangul = curriculum.load_korean_hangul_source_pack()
    pronunciation = curriculum.load_korean_pronunciation_source_pack()

    assert api.DEFAULT_KOREAN_FOUNDATION_MEDIA_MANIFEST_PATH == (
        curriculum.CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH
    )
    assert manifest.manifest_version == "korean-foundations-v2-media"
    assert manifest.hangul_source_pack_version == "hangul-v2"
    assert manifest.pronunciation_source_pack_version == "pronunciation-i-plus-1-v2"
    history = api.load_korean_v1_foundation_media_manifest()
    assert history.manifest_version == "korean-foundations-v1-media"
    assert history.hangul_source_pack_version == "hangul-v1"
    assert history.pronunciation_source_pack_version == "pronunciation-i-plus-1-v1"
    assert manifest.candidate_only is True
    assert len(manifest.slots) == 509
    assert sum(slot.required for slot in manifest.slots) == 325
    assert sum(slot.family == "hangul" for slot in manifest.slots) == 368
    assert sum(slot.family == "pronunciation" for slot in manifest.slots) == 141
    assert {slot.status for slot in manifest.slots} == {"needs_review"}
    assert len({slot.basename for slot in manifest.slots}) == 509
    assert len({slot.storage_relpath for slot in manifest.slots}) == 509
    expected_slot_ids = tuple(
        slot.slot_id
        for entry in (*hangul.entries, *pronunciation.entries)
        for slot in entry.media_slots
    )
    assert tuple(slot.slot_id for slot in manifest.slots) == expected_slot_ids
    for slot in manifest.slots:
        assert slot.reason_code == "media-evidence-required"
        assert slot.artifact_sha256 is None
        assert slot.reviewed_artifact_sha256 is None
        assert slot.review_receipts == ()
        assert not Path(slot.storage_relpath).is_absolute()
        assert "\\" not in slot.storage_relpath
        assert ".." not in slot.storage_relpath.split("/")

    media_root = Path("data/korean_foundations/media")
    assert not media_root.exists()
    assert not Path("data/korean_foundations/active-foundations.json").exists()


def test_pending_candidate_is_readable_but_can_never_satisfy_readiness(
    tmp_path: Path,
) -> None:
    api = _media()
    manifest = api.load_pending_korean_foundation_media_manifest()
    snapshot = _snapshot_with_manifest(api, tmp_path, manifest, write_files=False)

    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.assert_korean_foundation_media_ready(snapshot)
    assert _reason(exc_info) == "candidate_manifest_not_active"


def test_approved_media_requires_rights_text_metadata_hashes_and_role_receipts() -> None:
    api = _media()
    pending = api.load_pending_korean_foundation_media_manifest()
    _, by_slot, _, _ = _source_entries()
    target = next(slot for slot in pending.slots if slot.required and slot.media_kind == "audio")
    approved = _approved_slot(api, target, by_slot[target.slot_id], _pcm_wav_bytes())
    assert approved.status == "approved"

    required_fields = (
        "source_id",
        "source_version",
        "attribution",
        "license_id",
        "redistribution_disposition",
        "display_text",
        "spoken_text",
        "text_nfc",
        "display_text_sha256",
        "spoken_text_sha256",
        "text_nfc_sha256",
        "provider",
        "provider_version",
        "voice_id",
        "locale",
        "artifact_sha256",
        "reviewed_artifact_sha256",
        "metadata_sha256",
        "reviewed_metadata_sha256",
    )
    for field_name in required_fields:
        payload = approved.model_dump(mode="json")
        payload[field_name] = None
        with pytest.raises(ValidationError):
            api.KoreanFoundationMediaSlot.model_validate(payload)


def test_complete_transient_pcm_and_png_snapshot_satisfies_exact_media_contract(
    tmp_path: Path,
) -> None:
    api, manifest, snapshot = _approved_fixture(tmp_path)

    api.assert_korean_foundation_media_ready(snapshot)
    resolved = api.resolve_korean_foundation_media(snapshot)
    assert len(resolved) == 325
    assert len({path.name for path in resolved}) == 325
    assert all(path.is_file() and path.stat().st_size > 0 for path in resolved)
    assert sum(path.suffix == ".wav" for path in resolved) == 233
    assert sum(path.suffix == ".png" for path in resolved) == 92
    assert sum(slot.status == "approved" for slot in manifest.slots) == 325
    assert sum(slot.status == "needs_review" for slot in manifest.slots) == 184


def test_raw_glyph_audio_and_collapsed_specialist_native_roles_are_denied() -> None:
    api = _media()
    pending = api.load_pending_korean_foundation_media_manifest()
    _, by_slot, _, _ = _source_entries()
    target = next(slot for slot in pending.slots if slot.media_kind == "audio")
    approved = _approved_slot(api, target, by_slot[target.slot_id], _pcm_wav_bytes())

    raw_payload = approved.model_dump(mode="json")
    raw_payload["spoken_text"] = raw_payload["display_text"]
    raw_payload["spoken_text_sha256"] = raw_payload["display_text_sha256"]
    raw_payload["text_nfc"] = raw_payload["display_text"]
    raw_payload["text_nfc_sha256"] = raw_payload["display_text_sha256"]
    raw_payload["metadata_sha256"] = api.korean_foundation_media_metadata_sha256(
        raw_payload
    )
    raw_payload["reviewed_metadata_sha256"] = raw_payload["metadata_sha256"]
    for receipt in raw_payload["review_receipts"]:
        receipt["metadata_sha256"] = raw_payload["metadata_sha256"]
    with pytest.raises(ValidationError):
        api.KoreanFoundationMediaSlot.model_validate(raw_payload)

    collapsed_payload = approved.model_dump(mode="json")
    specialist = next(
        receipt
        for receipt in collapsed_payload["review_receipts"]
        if receipt["reviewer_role"] == "korean-phonetics-specialist"
    )
    native = next(
        receipt
        for receipt in collapsed_payload["review_receipts"]
        if receipt["reviewer_role"] == "independent-native-speaker"
    )
    native["reviewer_id"] = specialist["reviewer_id"]
    with pytest.raises(ValidationError):
        api.KoreanFoundationMediaSlot.model_validate(collapsed_payload)


def test_role_and_license_failures_block_even_when_bytes_and_hashes_match() -> None:
    api = _media()
    pending = api.load_pending_korean_foundation_media_manifest()
    _, by_slot, _, _ = _source_entries()
    target = next(slot for slot in pending.slots if slot.media_kind == "letter_audio")
    approved = _approved_slot(api, target, by_slot[target.slot_id], _pcm_wav_bytes())

    for field_name, invalid_value in (
        ("license_id", "unknown"),
        ("redistribution_disposition", "needs_review"),
        ("attribution", ""),
    ):
        payload = approved.model_dump(mode="json")
        payload[field_name] = invalid_value
        with pytest.raises(ValidationError):
            api.KoreanFoundationMediaSlot.model_validate(payload)

    payload = approved.model_dump(mode="json")
    payload["review_receipts"] = [
        receipt
        for receipt in payload["review_receipts"]
        if receipt["reviewer_role"] != "independent-native-speaker"
    ]
    with pytest.raises(ValidationError):
        api.KoreanFoundationMediaSlot.model_validate(payload)


def test_paths_urls_traversal_backslashes_drives_and_duplicate_basenames_fail_closed(
    tmp_path: Path,
) -> None:
    api, manifest, snapshot = _approved_fixture(tmp_path)
    target = next(slot for slot in manifest.slots if slot.status == "approved")
    for unsafe_path in (
        "/absolute.wav",
        "C:/absolute.wav",
        "C:\\absolute.wav",
        "media/../escape.wav",
        "media\\escape.wav",
        "https://example.invalid/audio.wav",
        "file://audio.wav",
    ):
        forged = target.model_copy(update={"storage_relpath": unsafe_path})
        forged_manifest = _replace_slot(manifest, forged)
        with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
            api.validate_korean_foundation_media_manifest(
                forged_manifest,
                snapshot=snapshot,
            )
        assert _reason(exc_info) == "unsafe_media_path"
        assert unsafe_path not in str(exc_info.value)
        assert str(tmp_path) not in str(exc_info.value)

    other = next(
        slot
        for slot in manifest.slots
        if slot.status == "approved" and slot.slot_id != target.slot_id
    )
    duplicate = other.model_copy(
        update={
            "basename": target.basename,
            "storage_relpath": f"media/{other.family}/{target.basename}",
        }
    )
    duplicate_manifest = _replace_slot(manifest, duplicate)
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.validate_korean_foundation_media_manifest(
            duplicate_manifest,
            snapshot=snapshot,
        )
    assert _reason(exc_info) == "duplicate_media_basename"


def test_symlink_and_simulated_reparse_media_components_are_denied_content_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api, manifest, snapshot = _approved_fixture(tmp_path)
    target = next(slot for slot in manifest.slots if slot.status == "approved")
    path = tmp_path.joinpath(*target.storage_relpath.split("/"))
    outside = tmp_path / "outside-media.bin"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    try:
        path.symlink_to(outside)
    except OSError:
        original_lstat = Path.lstat

        def simulated_symlink_lstat(candidate: Path) -> os.stat_result:
            if candidate == path:
                return SimpleNamespace(
                    st_mode=stat.S_IFLNK,
                    st_file_attributes=0,
                    st_size=outside.stat().st_size,
                )
            return original_lstat(candidate)

        monkeypatch.setattr(Path, "lstat", simulated_symlink_lstat)
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.assert_korean_foundation_media_ready(snapshot)
    assert _reason(exc_info) == "unsafe_filesystem_component"
    assert str(outside) not in str(exc_info.value)

    reparse_root = tmp_path / "reparse"
    reparse_root.mkdir()
    api, _, snapshot = _approved_fixture(reparse_root)
    original = api._stat_is_link_or_reparse
    calls = 0

    def simulated_reparse(stat_result: os.stat_result) -> bool:
        nonlocal calls
        calls += 1
        return calls == 3 or original(stat_result)

    monkeypatch.setattr(api, "_stat_is_link_or_reparse", simulated_reparse)
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.assert_korean_foundation_media_ready(snapshot)
    assert _reason(exc_info) == "unsafe_filesystem_component"


def test_hash_text_provider_voice_ssml_prosody_format_and_version_drift_block(
    tmp_path: Path,
) -> None:
    api, manifest, snapshot = _approved_fixture(tmp_path)
    target = next(
        slot
        for slot in manifest.slots
        if slot.status == "approved" and slot.media_kind == "letter_audio"
    )
    mutations = {
        "source_pack_version": "pronunciation-i-plus-1-v1",
        "source_content_sha256": "f" * 64,
        "display_text": "다른 글자",
        "spoken_text": "다른 발음",
        "text_nfc": "다른 문맥",
        "display_text_sha256": "f" * 64,
        "provider": "changed-provider",
        "provider_version": "changed-version",
        "voice_id": "changed-voice",
        "ssml_sha256": "f" * 64,
        "prosody_sha256": "e" * 64,
        "output_format": "png",
        "reviewed_artifact_sha256": "d" * 64,
        "reviewed_metadata_sha256": "c" * 64,
    }
    for field_name, changed_value in mutations.items():
        forged = target.model_copy(update={field_name: changed_value})
        forged_manifest = _replace_slot(manifest, forged)
        with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
            api.validate_korean_foundation_media_manifest(
                forged_manifest,
                snapshot=snapshot,
            )
        assert _reason(exc_info) in {
            "source_identity_mismatch",
            "text_binding_mismatch",
            "metadata_binding_mismatch",
            "artifact_hash_mismatch",
            "media_format_mismatch",
        }

    path = tmp_path.joinpath(*target.storage_relpath.split("/"))
    path.write_bytes(path.read_bytes() + b"replacement")
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.assert_korean_foundation_media_ready(snapshot)
    assert _reason(exc_info) == "artifact_hash_mismatch"


def test_missing_empty_wrong_header_duration_and_unmanifested_member_block(
    tmp_path: Path,
) -> None:
    api, manifest, snapshot = _approved_fixture(tmp_path)
    target = next(
        slot
        for slot in manifest.slots
        if slot.status == "approved" and slot.media_kind == "letter_audio"
    )
    path = tmp_path.joinpath(*target.storage_relpath.split("/"))
    path.unlink()
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.assert_korean_foundation_media_ready(snapshot)
    assert _reason(exc_info) == "media_file_missing"

    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    api, manifest, snapshot = _approved_fixture(empty_root)
    target = next(slot for slot in manifest.slots if slot.status == "approved")
    empty_root.joinpath(*target.storage_relpath.split("/")).write_bytes(b"")
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.assert_korean_foundation_media_ready(snapshot)
    assert _reason(exc_info) == "media_file_empty"

    header_root = tmp_path / "header"
    header_root.mkdir()
    api, manifest, snapshot = _approved_fixture(header_root)
    target = next(
        slot
        for slot in manifest.slots
        if slot.status == "approved" and slot.media_kind == "letter_audio"
    )
    bad = b"NOT-A-WAV-BUT-NONEMPTY"
    replaced = _approved_slot(
        api,
        target.model_copy(update={"status": "needs_review", "reason_code": "media-evidence-required"}),
        _source_entries()[1][target.slot_id],
        bad,
    )
    replaced_manifest = _replace_slot(manifest, replaced)
    replaced_snapshot = _snapshot_with_manifest(api, header_root, replaced_manifest)
    header_root.joinpath(*target.storage_relpath.split("/")).write_bytes(bad)
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.validate_korean_foundation_media_manifest(
            replaced_manifest,
            snapshot=replaced_snapshot,
        )
    assert _reason(exc_info) == "media_header_invalid"

    duration_root = tmp_path / "duration"
    duration_root.mkdir()
    api, manifest, snapshot = _approved_fixture(duration_root)
    target = next(
        slot
        for slot in manifest.slots
        if slot.status == "approved" and slot.media_kind == "letter_audio"
    )
    changed = target.model_copy(update={"duration_ms": 999})
    changed_manifest = _replace_slot(manifest, changed)
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.validate_korean_foundation_media_manifest(
            changed_manifest,
            snapshot=snapshot,
        )
    assert _reason(exc_info) in {"metadata_binding_mismatch", "media_duration_mismatch"}

    extra_member = SimpleNamespace(
        role="media",
        relpath="media/hangul/unmanifested.png",
        path=duration_root / "media" / "hangul" / "unmanifested.png",
        size_bytes=len(_png_bytes()),
        sha256=sha256(_png_bytes()).hexdigest(),
        content=_png_bytes(),
    )
    snapshot.media_members = (*snapshot.media_members, extra_member)
    with pytest.raises(api.KoreanFoundationMediaError) as exc_info:
        api.assert_korean_foundation_media_ready(snapshot)
    assert _reason(exc_info) == "unmanifested_media_member"


def test_fixture_validation_does_not_mutate_candidates_pointer_or_call_resolver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _media()
    candidate_path = api.DEFAULT_KOREAN_FOUNDATION_MEDIA_MANIFEST_PATH
    history_path = Path("data/korean_foundations/korean-foundations-v1-media.json")
    curation_path = Path(
        "data/korean_foundations/korean-foundations-v1-curation.json"
    )
    before_candidate = candidate_path.read_bytes()
    before_history = history_path.read_bytes()
    before_curation = curation_path.read_bytes()
    pointer = Path("data/korean_foundations/active-foundations.json")
    assert not pointer.exists()
    calls = 0

    def forbidden_resolver() -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("injected snapshot validation must not resolve production")

    monkeypatch.setattr(api, "resolve_active_korean_foundation_snapshot", forbidden_resolver)
    _, _, snapshot = _approved_fixture(tmp_path)
    api.assert_korean_foundation_media_ready(snapshot)

    assert calls == 0
    assert candidate_path.read_bytes() == before_candidate
    assert history_path.read_bytes() == before_history
    assert curation_path.read_bytes() == before_curation
    assert not pointer.exists()


def test_active_media_entrypoints_resolve_exactly_once_each(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api, _, snapshot = _approved_fixture(tmp_path)
    calls = 0

    def resolver() -> object:
        nonlocal calls
        calls += 1
        return snapshot

    monkeypatch.setattr(api, "resolve_active_korean_foundation_snapshot", resolver)
    api.assert_active_korean_foundation_media_ready()
    assert calls == 1
    paths = api.resolve_active_korean_foundation_media()
    assert calls == 2
    assert len(paths) == 325
