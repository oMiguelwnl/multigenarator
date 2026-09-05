"""Deterministic, fail-closed exports for Korean foundation decks."""

from __future__ import annotations

import csv
from dataclasses import replace
from hashlib import sha256
from importlib import import_module, util
import io
import inspect
import json
from pathlib import Path
import re
import sqlite3
import struct
from types import ModuleType
import unicodedata
import wave
import zipfile
import zlib

import pytest

from multilang.services.anki_id_registry import (
    ANKI_ID_REGISTRY,
    AnkiIdKind,
    registry_id,
    validate_anki_id_registry,
)
from multilang.services.phoneme_deck import PHONEME_FIELD_NAMES


EXPECTED_HANGUL_FIELD_NAMES = (
    "SortIndex",
    "Category",
    "JamoOrBlock",
    "ReadingOrName",
    "Sound",
    "Mnemonic",
    "Picture",
    "Strokes",
    "Gif",
    "Audio",
    "TargetConceptId",
    "PrerequisiteConceptIds",
    "ObservedConceptIds",
    "UnknownConceptIds",
    "IPlusOnePolicy",
)


def _export() -> ModuleType:
    assert util.find_spec("multilang.services.korean_foundation_export") is not None, (
        "the dedicated Korean foundation export service must exist"
    )
    return import_module("multilang.services.korean_foundation_export")


def _canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _text_sha256(value: str) -> str:
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


def _reseal_source_model(api: ModuleType, model_type: type, payload: dict[str, object]) -> object:
    payload.pop("content_hash", None)
    payload["content_hash"] = api.korean_canonical_json_sha256(payload)
    return model_type.model_validate(payload)


def _approved_source_packs() -> tuple[object, object, object]:
    api = import_module("multilang.services.korean_curriculum")
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pronunciation = api.load_korean_pronunciation_source_pack()

    hangul_entries = []
    for entry in hangul.entries:
        payload = entry.model_dump(mode="json")
        payload.update(
            {
                "reading_or_name": f"nome de teste {entry.sequence}",
                "sound": f"som de teste {entry.sequence}",
                "mnemonic": f"mnemônico de teste {entry.sequence}",
            }
        )
        hangul_entries.append(
            _reseal_source_model(api, api.KoreanHangulSourceEntry, payload)
        )
    hangul_payload = hangul.model_dump(mode="json")
    hangul_payload["entries"] = [
        entry.model_dump(mode="json") for entry in hangul_entries
    ]
    hangul = _reseal_source_model(api, api.KoreanHangulSourcePack, hangul_payload)

    pronunciation_entries = []
    for entry in pronunciation.entries:
        payload = entry.model_dump(mode="json")
        payload.update(
            {
                "spellings": "가",
                "sound": "[가]",
                "example_word": "가",
                "word_translation": f"palavra de teste {entry.sequence}",
                "example_sentence": "가요.",
                "sentence_translation": f"frase de teste {entry.sequence}",
            }
        )
        evidence = dict(payload["pronunciation_evidence"])
        evidence.update(
            {
                "canonical_spelling": "가",
                "normative_pronunciation": "가",
                "surface_pronunciation": "가",
            }
        )
        payload["pronunciation_evidence"] = evidence
        pronunciation_entries.append(
            _reseal_source_model(api, api.KoreanPronunciationSourceEntry, payload)
        )
    pronunciation_payload = pronunciation.model_dump(mode="json")
    pronunciation_payload["entries"] = [
        entry.model_dump(mode="json") for entry in pronunciation_entries
    ]
    pronunciation = _reseal_source_model(
        api,
        api.KoreanPronunciationSourcePack,
        pronunciation_payload,
    )
    return registry, hangul, pronunciation


def _approved_curation(
    registry: object,
    hangul: object,
    pronunciation: object,
    *,
    evidence_sha256: str,
) -> object:
    api = import_module("multilang.services.korean_foundation_review")
    pending = api._build_pending_korean_foundation_curation(
        registry=registry,
        hangul_pack=hangul,
        pronunciation_pack=pronunciation,
    )
    records = []
    for record in pending.records:
        gates = []
        for gate in record.gates:
            payload = gate.model_dump(mode="json")
            payload.update(
                {
                    "status": "approved",
                    "reason_code": None,
                    "reviewer_id": f"test-reviewer-{gate.gate_name}",
                    "reviewer_role": api.KOREAN_FOUNDATION_GATE_REVIEWER_ROLES[
                        gate.gate_name
                    ],
                    "reviewed_at": "2026-08-05T00:00:00Z",
                    "source_pack_version": record.source_pack_version,
                    "source_content_sha256": record.source_content_sha256,
                    "reviewed_evidence_sha256": evidence_sha256,
                }
            )
            gates.append(api.KoreanFoundationReviewGate.model_validate(payload))
        record_payload = record.model_dump(mode="json")
        record_payload["gates"] = [gate.model_dump(mode="json") for gate in gates]
        records.append(api.KoreanFoundationCurationRecord.model_validate(record_payload))
    manifest_payload = pending.model_dump(mode="json")
    manifest_payload["candidate_only"] = False
    manifest_payload["records"] = [record.model_dump(mode="json") for record in records]
    manifest_payload.pop("content_hash", None)
    manifest_payload["content_hash"] = _canonical_sha256(manifest_payload)
    return api.KoreanFoundationCurationManifest.model_validate(manifest_payload)


def _display_text(slot: object, entry: object) -> str:
    if slot.family == "hangul":
        mapping = entry.pedagogical_jamo_mapping
        return mapping.display_glyph if mapping is not None else entry.canonical_jamo_or_block
    if slot.media_kind == "letter_audio":
        return entry.spellings
    if slot.media_kind == "word_audio":
        return entry.example_word
    return entry.example_sentence


def _approved_media(
    registry: object,
    hangul: object,
    pronunciation: object,
) -> tuple[object, dict[str, bytes]]:
    api = import_module("multilang.services.korean_foundation_media")
    pending = api._build_pending_korean_foundation_media_manifest(
        registry=registry,
        hangul_pack=hangul,
        pronunciation_pack=pronunciation,
    )
    entries = {
        entry.item_key: entry
        for entry in (*hangul.entries, *pronunciation.entries)
    }
    media_bytes: dict[str, bytes] = {}
    slots = []
    audio_kinds = {"audio", "letter_audio", "word_audio", "sentence_audio"}
    for slot in pending.slots:
        if not slot.required:
            slots.append(slot)
            continue
        entry = entries[slot.item_key]
        content = _pcm_wav_bytes() if slot.media_kind in audio_kinds else _png_bytes()
        display_text = _display_text(slot, entry)
        spoken_text = (
            "테스트 전용 한글 음성"
            if slot.media_kind == "audio"
            else "테스트 전용 발음 문맥"
            if slot.media_kind == "letter_audio"
            else display_text
        )
        text_nfc = unicodedata.normalize("NFC", spoken_text or display_text)
        artifact_hash = sha256(content).hexdigest()
        payload = slot.model_dump(mode="json")
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
                "spoken_text": spoken_text if slot.media_kind in audio_kinds else None,
                "text_nfc": text_nfc,
                "display_text_sha256": _text_sha256(display_text),
                "spoken_text_sha256": (
                    _text_sha256(spoken_text)
                    if slot.media_kind in audio_kinds
                    else None
                ),
                "text_nfc_sha256": _text_sha256(text_nfc),
                "provider": "test-fixture-local" if slot.media_kind in audio_kinds else None,
                "provider_version": "test-fixture-v1" if slot.media_kind in audio_kinds else None,
                "voice_id": "test-voice-not-for-production" if slot.media_kind in audio_kinds else None,
                "locale": "ko-KR" if slot.media_kind in audio_kinds else None,
                "ssml_sha256": _text_sha256("test-ssml") if slot.media_kind in audio_kinds else None,
                "prosody_sha256": _text_sha256("test-prosody") if slot.media_kind in audio_kinds else None,
                "duration_ms": 100 if slot.media_kind in audio_kinds else None,
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
        roles = ["media-rights-reviewer", "media-integrity-reviewer"]
        if slot.media_kind in audio_kinds:
            roles.extend(
                [
                    "audio-playback-reviewer",
                    "korean-phonetics-specialist",
                    "independent-native-speaker",
                ]
            )
        payload["review_receipts"] = [
            {
                "reviewer_id": f"test-reviewer-{role}",
                "reviewer_role": role,
                "reviewed_at": "2026-08-05T00:00:00Z",
                "artifact_sha256": artifact_hash,
                "metadata_sha256": metadata_hash,
            }
            for role in roles
        ]
        slots.append(api.KoreanFoundationMediaSlot.model_validate(payload))
        media_bytes[slot.storage_relpath] = content
    manifest_payload = pending.model_dump(mode="json")
    manifest_payload["candidate_only"] = False
    manifest_payload["slots"] = [slot.model_dump(mode="json") for slot in slots]
    manifest_payload.pop("content_hash", None)
    manifest_payload["content_hash"] = api.korean_foundation_media_manifest_sha256(
        manifest_payload
    )
    return api.KoreanFoundationMediaManifest.model_validate(manifest_payload), media_bytes


def _json_bytes(model: object) -> bytes:
    return (
        json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


@pytest.fixture(scope="module")
def approved_snapshot(tmp_path_factory: pytest.TempPathFactory) -> object:
    snapshot_api = import_module("multilang.services.korean_foundation_snapshot")
    registry, hangul, pronunciation = _approved_source_packs()
    review_evidence = b'{"fixture":"TEST ONLY - NOT PRODUCTION EVIDENCE"}\n'
    review_hash = sha256(review_evidence).hexdigest()
    curation = _approved_curation(
        registry,
        hangul,
        pronunciation,
        evidence_sha256=review_hash,
    )
    media_manifest, media_bytes = _approved_media(registry, hangul, pronunciation)
    files_by_role: dict[str, tuple[str, bytes]] = {
        "content/registry.json": ("concept_registry", _json_bytes(registry)),
        "content/hangul.json": ("hangul_source_pack", _json_bytes(hangul)),
        "content/pronunciation.json": (
            "pronunciation_source_pack",
            _json_bytes(pronunciation),
        ),
        "content/curation.json": ("curation_manifest", _json_bytes(curation)),
        "content/media.json": ("media_manifest", _json_bytes(media_manifest)),
        "review/test-evidence.json": ("review_evidence", review_evidence),
    }
    files_by_role.update(
        {relpath: ("media", content) for relpath, content in media_bytes.items()}
    )
    member_payloads = [
        {
            "role": role,
            "relpath": relpath,
            "size_bytes": len(content),
            "sha256": sha256(content).hexdigest(),
        }
        for relpath, (role, content) in files_by_role.items()
    ]
    manifest_payload: dict[str, object] = {
        "schema_version": 1,
        "source_root": "content",
        "review_evidence_root": "review",
        "media_root": "media",
        "members": member_payloads,
    }
    manifest_payload["bundle_sha256"] = _canonical_sha256(manifest_payload)
    manifest = snapshot_api.KoreanFoundationSnapshotManifest.model_validate(
        manifest_payload
    )
    root = tmp_path_factory.mktemp("approved-korean-foundations") / manifest.bundle_sha256
    resolved_members = []
    for member in manifest.members:
        content = files_by_role[member.relpath][1]
        path = root.joinpath(*member.relpath.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        resolved_members.append(
            snapshot_api.ResolvedKoreanFoundationSnapshotMember(
                role=member.role,
                relpath=member.relpath,
                path=path,
                size_bytes=member.size_bytes,
                sha256=member.sha256,
                content=content,
            )
        )
    manifest_bytes = _json_bytes(manifest)
    (root / "snapshot-manifest.json").write_bytes(manifest_bytes)
    members = tuple(resolved_members)
    return snapshot_api.ResolvedKoreanFoundationSnapshot(
        bundle_sha256=manifest.bundle_sha256,
        snapshot_manifest_sha256=sha256(manifest_bytes).hexdigest(),
        snapshot_root=root,
        source_root=root / "content",
        review_evidence_root=root / "review",
        media_root=root / "media",
        manifest=manifest,
        members=members,
        review_evidence_members=tuple(
            member for member in members if member.role == "review_evidence"
        ),
        media_members=tuple(member for member in members if member.role == "media"),
        concept_registry=registry,
        hangul_source_pack=hangul,
        pronunciation_source_pack=pronunciation,
        curation_manifest=curation,
        media_manifest_bytes=_json_bytes(media_manifest),
    )


def _hangul_row(api: ModuleType) -> object:
    return api.HangulExportRow(
        sort_index=1,
        item_key="ko-hangul-0001",
        source_pack_version="hangul-v1",
        stage_id="H0",
        category="jamo-unit",
        jamo_or_block="ᄀ",
        reading_or_name="기역 & nome",
        sound="som de teste",
        mnemonic="mnemônico de teste",
        picture="<img src=\"picture.png\">",
        strokes="<img src=\"strokes.png\">",
        gif="",
        audio="[sound:audio.wav]",
        target_concept_id="orthography.jamo.unit",
        prerequisite_concept_ids=(),
        observed_concept_ids=("orthography.jamo.unit",),
        unknown_concept_ids=("orthography.jamo.unit",),
        i_plus_one_policy="strict",
    )


def _pronunciation_row(api: ModuleType) -> object:
    return api.KoreanPronunciationExportRow(
        sort_index=1,
        item_key="ko-pron-0001",
        source_pack_version="pronunciation-i-plus-1-v1",
        stage_id="P0",
        spellings="ㄱ & ㅋ",
        sound="대조",
        letter_audio="[sound:letter.wav]",
        example_word="가",
        word_audio="[sound:word.wav]",
        word_translation="palavra de teste",
        example_sentence="가요.",
        sentence_audio="[sound:sentence.wav]",
        sentence_translation="Frase de teste.",
    )


def test_korean_foundation_ids_are_registry_backed_without_local_numeric_declarations() -> None:
    api = _export()
    source = Path("src/multilang/services/korean_foundation_export.py").read_text(encoding="utf-8")

    assert api.KOREAN_HANGUL_MODEL_ID == registry_id(
        family="korean_foundation", role="hangul_model", kind=AnkiIdKind.MODEL
    )
    assert api.KOREAN_HANGUL_DECK_ID == registry_id(
        family="korean_foundation", role="hangul_deck", kind=AnkiIdKind.DECK
    )
    assert api.KOREAN_PRONUNCIATION_MODEL_ID == registry_id(
        family="korean_foundation", role="pronunciation_model", kind=AnkiIdKind.MODEL
    )
    assert api.KOREAN_PRONUNCIATION_DECK_ID == registry_id(
        family="korean_foundation", role="pronunciation_deck", kind=AnkiIdKind.DECK
    )
    assert api.KOREAN_HANGUL_MODEL_ID != registry_id(
        family="korean_frequency", role="model", kind=AnkiIdKind.MODEL
    )
    assert api.KOREAN_HANGUL_DECK_ID != registry_id(
        family="korean_frequency", role="parent_deck", kind=AnkiIdKind.DECK
    )
    assert "1_762_801_001" not in source
    assert "1_762_801_002" not in source
    assert "1_762_801_003" not in source
    assert "1_762_801_004" not in source


def test_fixed_ids_names_and_row_schemas_are_exact() -> None:
    api = _export()

    assert api.KOREAN_HANGUL_MODEL_ID == 1_762_801_001
    assert api.KOREAN_HANGUL_DECK_ID == 1_762_801_002
    assert api.KOREAN_PRONUNCIATION_MODEL_ID == 1_762_801_003
    assert api.KOREAN_PRONUNCIATION_DECK_ID == 1_762_801_004
    assert api.KOREAN_HANGUL_DECK_NAME == "Multilang Korean::Foundations::Hangul"
    assert (
        api.KOREAN_PRONUNCIATION_DECK_NAME
        == "Multilang Korean::Foundations::Pronunciation i+1"
    )
    assert api.KOREAN_HANGUL_NOTE_TYPE_NAME == "Multilang::Korean Hangul Foundation"
    assert (
        api.KOREAN_PRONUNCIATION_NOTE_TYPE_NAME
        == "Multilang::Korean Pronunciation i+1"
    )
    assert api.HANGUL_FIELD_NAMES == EXPECTED_HANGUL_FIELD_NAMES
    assert api.KOREAN_PRONUNCIATION_FIELD_NAMES == PHONEME_FIELD_NAMES
    assert len(api.HANGUL_FIELD_NAMES) == 15
    assert len(api.KOREAN_PRONUNCIATION_FIELD_NAMES) == 9


def test_stable_guid_uses_only_family_version_and_item_identity() -> None:
    api = _export()
    expected = sha256(
        b"hangul|hangul-v1|ko-hangul-0001"
    ).hexdigest()[:32]

    guid = api.stable_korean_foundation_guid(
        family=api.KoreanFoundationFamily.HANGUL,
        source_pack_version="hangul-v1",
        item_key="ko-hangul-0001",
    )

    assert guid == expected
    assert len(guid) == 32
    assert set(guid) <= set("0123456789abcdef")
    assert guid != api.stable_korean_foundation_guid(
        family=api.KoreanFoundationFamily.PRONUNCIATION,
        source_pack_version="hangul-v1",
        item_key="ko-hangul-0001",
    )
    assert guid != api.stable_korean_foundation_guid(
        family=api.KoreanFoundationFamily.HANGUL,
        source_pack_version="hangul-v1",
        item_key="ko-hangul-0002",
    )


def test_hangul_model_and_note_keep_exact_fields_hidden_evidence_and_safe_tags() -> None:
    api = _export()
    row = _hangul_row(api)

    model = api.build_korean_hangul_model()
    note = api.build_korean_hangul_note(row, model=model)

    assert model.model_id == api.KOREAN_HANGUL_MODEL_ID
    assert model.name == api.KOREAN_HANGUL_NOTE_TYPE_NAME
    assert tuple(field["name"] for field in model.fields) == EXPECTED_HANGUL_FIELD_NAMES
    assert len(model.templates) == 1
    assert "{{TargetConceptId}}" not in model.templates[0]["qfmt"]
    assert "{{TargetConceptId}}" not in model.templates[0]["afmt"]
    assert note.guid == api.stable_korean_foundation_guid(
        family=api.KoreanFoundationFamily.HANGUL,
        source_pack_version=row.source_pack_version,
        item_key=row.item_key,
    )
    assert note.fields == [
        "1",
        "jamo-unit",
        "ᄀ",
        "기역 &amp; nome",
        "som de teste",
        "mnemônico de teste",
        '<img src="picture.png">',
        '<img src="strokes.png">',
        "",
        "[sound:audio.wav]",
        "orthography.jamo.unit",
        "[]",
        '["orthography.jamo.unit"]',
        '["orthography.jamo.unit"]',
        "strict",
    ]
    assert note.tags == [
        "multilang",
        "ko",
        "korean_foundation",
        "family_hangul",
        "stage_H0",
        "item_ko_hangul_0001",
    ]


def test_pronunciation_model_and_note_reuse_exact_shared_mechanics() -> None:
    api = _export()
    row = _pronunciation_row(api)

    model = api.build_korean_pronunciation_model()
    note = api.build_korean_pronunciation_note(row, model=model)

    assert model.model_id == api.KOREAN_PRONUNCIATION_MODEL_ID
    assert model.name == api.KOREAN_PRONUNCIATION_NOTE_TYPE_NAME
    assert tuple(field["name"] for field in model.fields) == PHONEME_FIELD_NAMES
    assert "Noto Sans KR" in model.css
    assert note.guid == api.stable_korean_foundation_guid(
        family=api.KoreanFoundationFamily.PRONUNCIATION,
        source_pack_version=row.source_pack_version,
        item_key=row.item_key,
    )
    assert note.fields == [
        "ㄱ &amp; ㅋ",
        "대조",
        "[sound:letter.wav]",
        "가",
        "[sound:word.wav]",
        "palavra de teste",
        "가요.",
        "[sound:sentence.wav]",
        "Frase de teste.",
    ]
    assert note.tags == [
        "multilang",
        "ko",
        "korean_foundation",
        "family_pronunciation",
        "stage_P0",
        "item_ko_pron_0001",
    ]


def test_join_uses_one_typed_immutable_snapshot_for_exact_separate_rows(
    approved_snapshot: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    calls = 0

    def resolver() -> object:
        nonlocal calls
        calls += 1
        return approved_snapshot

    monkeypatch.setattr(api, "resolve_active_korean_foundation_snapshot", resolver)
    hangul = api.build_korean_foundation_export_bundle(
        family=api.KoreanFoundationFamily.HANGUL
    )
    assert calls == 1
    pronunciation = api.build_korean_foundation_export_bundle(
        family=api.KoreanFoundationFamily.PRONUNCIATION
    )
    assert calls == 2

    assert hangul.snapshot_bundle_sha256 == approved_snapshot.bundle_sha256
    assert pronunciation.snapshot_bundle_sha256 == approved_snapshot.bundle_sha256
    assert len(hangul.rows) == 92
    assert len(pronunciation.rows) == 47
    assert len(hangul.media) == 184
    assert len(pronunciation.media) == 141
    assert all(isinstance(row, api.HangulExportRow) for row in hangul.rows)
    assert all(
        isinstance(row, api.KoreanPronunciationExportRow)
        for row in pronunciation.rows
    )
    assert tuple(row.sort_index for row in hangul.rows) == tuple(range(1, 93))
    assert tuple(row.sort_index for row in pronunciation.rows) == tuple(range(1, 48))
    assert hangul.rows[0].ordered_fields()[:6] == [
        "1",
        "jamo-unit",
        "ᄀ",
        "nome de teste 1",
        "som de teste 1",
        "mnemônico de teste 1",
    ]
    assert hangul.rows[0].picture == ""
    assert hangul.rows[0].gif == ""
    assert hangul.rows[0].strokes.startswith('<img src="hangul-strokes-0001')
    assert hangul.rows[0].audio.startswith("[sound:hangul-audio-0001")
    assert pronunciation.rows[0].ordered_fields() == [
        "가",
        "[가]",
        "[sound:pron-letter-audio-0001.wav]",
        "가",
        "[sound:pron-word-audio-0001.wav]",
        "palavra de teste 1",
        "가요.",
        "[sound:pron-sentence-audio-0001.wav]",
        "frase de teste 1",
    ]
    assert all(media.path.is_file() for media in (*hangul.media, *pronunciation.media))
    assert all(
        sha256(media.content).hexdigest() == media.sha256
        for media in (*hangul.media, *pronunciation.media)
    )


def test_hangul_row_allows_blank_optional_sound_but_requires_core_copy(
    tmp_path: Path,
    approved_snapshot: object,
) -> None:
    api = _export()
    source_entry = approved_snapshot.hangul_source_pack.entries[0]
    entry = source_entry.model_copy(update={"sound": None})
    strokes_content = _png_bytes()
    audio_content = _pcm_wav_bytes()
    media_by_slot = {
        (entry.item_key, "strokes"): api.KoreanFoundationExportMedia(
            item_key=entry.item_key,
            media_kind="strokes",
            basename="strokes.png",
            path=tmp_path / "strokes.png",
            sha256=sha256(strokes_content).hexdigest(),
            content=strokes_content,
        ),
        (entry.item_key, "audio"): api.KoreanFoundationExportMedia(
            item_key=entry.item_key,
            media_kind="audio",
            basename="audio.wav",
            path=tmp_path / "audio.wav",
            sha256=sha256(audio_content).hexdigest(),
            content=audio_content,
        ),
    }

    row = api._hangul_row_from_source(entry, media_by_slot)

    assert row.sound == ""
    assert row.ordered_fields()[4] == ""
    for required_field in ("reading_or_name", "mnemonic"):
        missing = source_entry.model_copy(update={required_field: None})
        with pytest.raises(ValueError, match="learner_copy_missing"):
            api._hangul_row_from_source(missing, media_by_slot)


def test_guid_ignores_mutable_copy_template_and_media_filename_changes() -> None:
    api = _export()
    hangul = _hangul_row(api)
    pronunciation = _pronunciation_row(api)
    hangul_guid = api.build_korean_hangul_note(hangul).guid
    pronunciation_guid = api.build_korean_pronunciation_note(pronunciation).guid

    assert api.build_korean_hangul_note(
        replace(
            hangul,
            reading_or_name="outro nome",
            mnemonic="outro mnemônico",
            picture='<img src="different.png">',
            audio="[sound:different.wav]",
        )
    ).guid == hangul_guid
    assert api.build_korean_pronunciation_note(
        replace(
            pronunciation,
            word_translation="outra tradução",
            sentence_translation="outra frase",
            letter_audio="[sound:different.wav]",
        )
    ).guid == pronunciation_guid


def test_production_builder_has_no_source_override_and_missing_pointer_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    snapshot_api = import_module("multilang.services.korean_foundation_snapshot")

    def missing_active_snapshot() -> object:
        raise snapshot_api.KoreanFoundationSnapshotError(
            snapshot_api.KoreanFoundationSnapshotReasonCode.PRODUCTION_NOT_ACTIVE
        )

    monkeypatch.setattr(
        api,
        "resolve_active_korean_foundation_snapshot",
        missing_active_snapshot,
    )

    assert tuple(
        inspect.signature(api.build_korean_foundation_export_bundle).parameters
    ) == ("family",)
    assert tuple(
        inspect.signature(api._build_korean_foundation_export_bundle_from_snapshot).parameters
    ) == ("snapshot", "family")
    for forbidden in ("path", "root", "url", "archive", "manifest", "pointer"):
        assert forbidden not in inspect.signature(
            api.build_korean_foundation_export_bundle
        ).parameters

    for family in api.KoreanFoundationFamily:
        with pytest.raises(snapshot_api.KoreanFoundationSnapshotError) as exc_info:
            api.build_korean_foundation_export_bundle(family=family)
        assert exc_info.value.reason_code.value == "production_not_active"


def test_pending_or_false_i_plus_one_snapshot_fails_before_row_construction(
    approved_snapshot: object,
) -> None:
    api = _export()
    review_api = import_module("multilang.services.korean_foundation_review")
    pending = review_api._build_pending_korean_foundation_curation(
        registry=approved_snapshot.concept_registry,
        hangul_pack=approved_snapshot.hangul_source_pack,
        pronunciation_pack=approved_snapshot.pronunciation_source_pack,
    )
    pending_snapshot = approved_snapshot.model_copy(
        update={"curation_manifest": pending}
    )
    with pytest.raises(ValueError, match="snapshot typed member mismatch"):
        api._build_korean_foundation_export_bundle_from_snapshot(
            pending_snapshot,
            family=api.KoreanFoundationFamily.HANGUL,
        )

    first = approved_snapshot.hangul_source_pack.entries[0]
    forged_evidence = first.evidence.model_copy(
        update={"unknown_concept_ids": ("orthography.block.unit",)}
    )
    forged_entry = first.model_copy(update={"evidence": forged_evidence})
    forged_pack = approved_snapshot.hangul_source_pack.model_copy(
        update={
            "entries": (
                forged_entry,
                *approved_snapshot.hangul_source_pack.entries[1:],
            )
        }
    )
    false_i_plus_one = approved_snapshot.model_copy(
        update={"hangul_source_pack": forged_pack}
    )
    with pytest.raises(ValueError, match="snapshot typed member mismatch"):
        api._build_korean_foundation_export_bundle_from_snapshot(
            false_i_plus_one,
            family=api.KoreanFoundationFamily.HANGUL,
        )


def test_fixed_model_and_deck_ids_are_globally_unique() -> None:
    api = _export()

    proposed = {
        api.KOREAN_HANGUL_MODEL_ID,
        api.KOREAN_HANGUL_DECK_ID,
        api.KOREAN_PRONUNCIATION_MODEL_ID,
        api.KOREAN_PRONUNCIATION_DECK_ID,
        registry_id(family="korean_frequency", role="model", kind=AnkiIdKind.MODEL),
        registry_id(family="korean_frequency", role="parent_deck", kind=AnkiIdKind.DECK),
        registry_id(family="korean_frequency", role="level_1_deck", kind=AnkiIdKind.DECK),
        registry_id(family="korean_frequency", role="level_2_deck", kind=AnkiIdKind.DECK),
        registry_id(family="korean_frequency", role="level_3_deck", kind=AnkiIdKind.DECK),
    }
    assert len(proposed) == 9
    validate_anki_id_registry(ANKI_ID_REGISTRY)


def _expected_family_contract(api: ModuleType, family: object) -> tuple[object, ...]:
    if family is api.KoreanFoundationFamily.HANGUL:
        return (
            api.KOREAN_HANGUL_MODEL_ID,
            api.KOREAN_HANGUL_DECK_ID,
            api.KOREAN_HANGUL_NOTE_TYPE_NAME,
            api.KOREAN_HANGUL_DECK_NAME,
            api.HANGUL_FIELD_NAMES,
            92,
            184,
        )
    return (
        api.KOREAN_PRONUNCIATION_MODEL_ID,
        api.KOREAN_PRONUNCIATION_DECK_ID,
        api.KOREAN_PRONUNCIATION_NOTE_TYPE_NAME,
        api.KOREAN_PRONUNCIATION_DECK_NAME,
        api.KOREAN_PRONUNCIATION_FIELD_NAMES,
        47,
        141,
    )


@pytest.mark.parametrize("family_name", ["hangul", "pronunciation"])
def test_apkg_export_is_inspected_with_exact_sqlite_identity_notes_and_media(
    family_name: str,
    approved_snapshot: object,
    tmp_path: Path,
) -> None:
    api = _export()
    family = api.KoreanFoundationFamily(family_name)
    (
        model_id,
        deck_id,
        note_type_name,
        deck_name,
        field_names,
        card_count,
        media_count,
    ) = _expected_family_contract(api, family)
    output_path = tmp_path / f"{family.value}.apkg"

    result = api._export_korean_foundation_from_snapshot(
        approved_snapshot,
        family=family,
        export_format=api.ExportArtifactFormat.APKG,
        output_destination=output_path,
    )

    assert result.output_path == output_path
    assert result.bundle_path is None
    assert result.card_count == card_count
    assert result.media_count == media_count
    assert result.model_id == model_id
    assert result.deck_id == deck_id
    assert result.note_type_name == note_type_name
    assert result.deck_name == deck_name
    assert result.snapshot_bundle_sha256 == approved_snapshot.bundle_sha256
    assert result.export_status == "completed"

    with zipfile.ZipFile(output_path) as archive:
        infos = archive.infolist()
        assert len({info.filename for info in infos}) == len(infos)
        assert {info.date_time for info in infos} == {(1980, 1, 1, 0, 0, 0)}
        names = {info.filename for info in infos}
        assert {"collection.anki2", "media"} <= names
        media_map = json.loads(archive.read("media").decode("utf-8"))
        assert len(media_map) == media_count
        assert set(media_map) == {str(index) for index in range(media_count)}
        expected_media = {
            media.basename: media.content
            for media in api._build_korean_foundation_export_bundle_from_snapshot(
                approved_snapshot,
                family=family,
            ).media
        }
        assert set(media_map.values()) == set(expected_media)
        for member_name, basename in media_map.items():
            assert archive.read(member_name) == expected_media[basename]
        collection_path = tmp_path / f"{family.value}-collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))

    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        decks = json.loads(connection.execute("select decks from col").fetchone()[0])
        notes = connection.execute(
            "select guid, flds, tags from notes order by id"
        ).fetchall()
        cards = connection.execute("select did from cards order by id").fetchall()

    assert set(models) == {str(model_id)}
    assert models[str(model_id)]["name"] == note_type_name
    assert [field["name"] for field in models[str(model_id)]["flds"]] == list(
        field_names
    )
    assert set(decks) == {"1", str(deck_id)}
    assert decks[str(deck_id)]["name"] == deck_name
    assert len(notes) == card_count
    assert len(cards) == card_count
    assert {did for (did,) in cards} == {deck_id}
    source_pack = (
        approved_snapshot.hangul_source_pack
        if family is api.KoreanFoundationFamily.HANGUL
        else approved_snapshot.pronunciation_source_pack
    )
    for note, entry in zip(notes, source_pack.entries, strict=True):
        guid, raw_fields, raw_tags = note
        assert guid == api.stable_korean_foundation_guid(
            family=family,
            source_pack_version=source_pack.source_pack_version,
            item_key=entry.item_key,
        )
        assert len(raw_fields.split("\x1f")) == len(field_names)
        assert {"multilang", "ko", "korean_foundation"} <= set(raw_tags.split())


@pytest.mark.parametrize("family_name", ["hangul", "pronunciation"])
@pytest.mark.parametrize("format_name", ["csv", "tsv"])
def test_tabular_export_has_exact_headers_rows_metadata_checksums_and_media(
    family_name: str,
    format_name: str,
    approved_snapshot: object,
    tmp_path: Path,
) -> None:
    api = _export()
    family = api.KoreanFoundationFamily(family_name)
    export_format = api.ExportArtifactFormat(format_name)
    (
        model_id,
        deck_id,
        note_type_name,
        deck_name,
        field_names,
        card_count,
        media_count,
    ) = _expected_family_contract(api, family)
    destination = tmp_path / f"{family.value}-{format_name}"

    result = api._export_korean_foundation_from_snapshot(
        approved_snapshot,
        family=family,
        export_format=export_format,
        output_destination=destination,
    )

    assert result.bundle_path == destination
    assert result.output_path.parent == destination
    assert result.output_path.suffix == f".{format_name}"
    assert result.card_count == card_count
    assert result.media_count == media_count
    assert result.model_id == model_id
    assert result.deck_id == deck_id
    content = result.output_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    delimiter = "," if export_format is api.ExportArtifactFormat.CSV else "\t"
    separator_name = "Comma" if delimiter == "," else "Tab"
    assert lines[:5] == [
        f"#separator:{separator_name}",
        "#html:true",
        f"#notetype:{note_type_name}",
        f"#deck:{deck_name}",
        f"#columns:{delimiter.join(field_names)}",
    ]
    rows = list(csv.reader(lines[5:], delimiter=delimiter))
    assert len(rows) == card_count
    assert all(len(row) == len(field_names) for row in rows)

    metadata = json.loads((destination / "notes-metadata.json").read_text("utf-8"))
    assert metadata["family"] == family.value
    assert metadata["model_id"] == model_id
    assert metadata["deck_id"] == deck_id
    assert len(metadata["notes"]) == card_count
    assert all(len(note["guid"]) == 32 for note in metadata["notes"])
    assert all("ko" in note["tags"] for note in metadata["notes"])

    checksums = json.loads((destination / "media-checksums.json").read_text("utf-8"))
    assert checksums["family"] == family.value
    assert len(checksums["files"]) == media_count
    media_root = destination / "media"
    copied = {path.name: path for path in media_root.iterdir() if path.is_file()}
    assert set(copied) == {item["basename"] for item in checksums["files"]}
    for item in checksums["files"]:
        payload = copied[item["basename"]].read_bytes()
        assert len(payload) == item["size_bytes"]
        assert sha256(payload).hexdigest() == item["sha256"]

    references = {
        match.group(1) or match.group(2)
        for row in rows
        for field in row
        for match in [
            re.search(
                r"\[sound:([^\]]+)\]|<img src=\"([^\"]+)\">",
                field,
            )
        ]
        if match is not None
    }
    assert references == set(copied)


@pytest.mark.parametrize("family_name", ["hangul", "pronunciation"])
@pytest.mark.parametrize("format_name", ["apkg", "csv", "tsv"])
def test_repeated_exports_are_byte_deterministic(
    family_name: str,
    format_name: str,
    approved_snapshot: object,
    tmp_path: Path,
) -> None:
    api = _export()
    family = api.KoreanFoundationFamily(family_name)
    export_format = api.ExportArtifactFormat(format_name)
    first = tmp_path / "first" / (
        f"{family.value}.apkg" if format_name == "apkg" else family.value
    )
    second = tmp_path / "second" / (
        f"{family.value}.apkg" if format_name == "apkg" else family.value
    )

    first_result = api._export_korean_foundation_from_snapshot(
        approved_snapshot,
        family=family,
        export_format=export_format,
        output_destination=first,
    )
    second_result = api._export_korean_foundation_from_snapshot(
        approved_snapshot,
        family=family,
        export_format=export_format,
        output_destination=second,
    )

    if export_format is api.ExportArtifactFormat.APKG:
        assert first_result.output_path.read_bytes() == second_result.output_path.read_bytes()
    else:
        first_files = {
            path.relative_to(first).as_posix(): path.read_bytes()
            for path in first.rglob("*")
            if path.is_file()
        }
        second_files = {
            path.relative_to(second).as_posix(): path.read_bytes()
            for path in second.rglob("*")
            if path.is_file()
        }
        assert first_files == second_files


@pytest.mark.parametrize("family_name", ["hangul", "pronunciation"])
@pytest.mark.parametrize("format_name", ["apkg", "csv", "tsv"])
def test_missing_active_production_pointer_refuses_all_six_without_output(
    family_name: str,
    format_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    snapshot_api = import_module("multilang.services.korean_foundation_snapshot")

    def missing_active_snapshot() -> object:
        raise snapshot_api.KoreanFoundationSnapshotError(
            snapshot_api.KoreanFoundationSnapshotReasonCode.PRODUCTION_NOT_ACTIVE
        )

    monkeypatch.setattr(
        api,
        "resolve_active_korean_foundation_snapshot",
        missing_active_snapshot,
    )
    destination = tmp_path / (
        f"{family_name}.apkg" if format_name == "apkg" else family_name
    )

    with pytest.raises(snapshot_api.KoreanFoundationSnapshotError) as exc_info:
        api.export_korean_foundation(
            family=api.KoreanFoundationFamily(family_name),
            export_format=api.ExportArtifactFormat(format_name),
            output_destination=destination,
        )

    assert exc_info.value.reason_code.value == "production_not_active"
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("format_name", ["apkg", "csv", "tsv"])
def test_failed_staged_inspection_leaves_no_partial_output(
    format_name: str,
    approved_snapshot: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    export_format = api.ExportArtifactFormat(format_name)
    destination = tmp_path / ("hangul.apkg" if format_name == "apkg" else "hangul")
    inspector = (
        "_inspect_staged_apkg"
        if export_format is api.ExportArtifactFormat.APKG
        else "_inspect_staged_tabular_bundle"
    )

    def fail_inspection(*args: object, **kwargs: object) -> None:
        raise ValueError("fixture inspection failure")

    monkeypatch.setattr(api, inspector, fail_inspection)
    with pytest.raises(ValueError, match="fixture inspection failure"):
        api._export_korean_foundation_from_snapshot(
            approved_snapshot,
            family=api.KoreanFoundationFamily.HANGUL,
            export_format=export_format,
            output_destination=destination,
        )

    assert not destination.exists()
    assert not list(tmp_path.glob(".korean-foundation-*"))


@pytest.mark.parametrize(
    ("mutation", "expected_message"),
    [
        ("source_version", "source-pack identity"),
        ("item_key", "row identity"),
        ("media_reference", "media references"),
    ],
)
def test_version_item_and_reference_drift_fail_before_any_output(
    mutation: str,
    expected_message: str,
    approved_snapshot: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    bundle = api._build_korean_foundation_export_bundle_from_snapshot(
        approved_snapshot,
        family=api.KoreanFoundationFamily.HANGUL,
    )
    first = bundle.rows[0]
    if mutation == "source_version":
        changed = replace(first, source_pack_version="hangul-v1")
    elif mutation == "item_key":
        changed = replace(first, item_key="ko-hangul-9999")
    else:
        changed = replace(first, audio="[sound:dangling.wav]")
    forged = replace(bundle, rows=(changed, *bundle.rows[1:]))
    monkeypatch.setattr(
        api,
        "_build_korean_foundation_export_bundle_from_snapshot",
        lambda snapshot, *, family: forged,
    )
    destination = tmp_path / f"{mutation}.apkg"

    with pytest.raises(ValueError, match=expected_message):
        api._export_korean_foundation_from_snapshot(
            approved_snapshot,
            family=api.KoreanFoundationFamily.HANGUL,
            export_format=api.ExportArtifactFormat.APKG,
            output_destination=destination,
        )

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("format_name", ["apkg", "csv", "tsv"])
def test_unsafe_parent_traversal_is_rejected_before_directory_creation(
    format_name: str,
    approved_snapshot: object,
    tmp_path: Path,
) -> None:
    api = _export()
    destination = tmp_path / "created-by-bug" / ".." / (
        "escape.apkg" if format_name == "apkg" else "escape"
    )

    with pytest.raises(ValueError, match="unsafe output destination"):
        api._export_korean_foundation_from_snapshot(
            approved_snapshot,
            family=api.KoreanFoundationFamily.HANGUL,
            export_format=api.ExportArtifactFormat(format_name),
            output_destination=destination,
        )

    assert not (tmp_path / "created-by-bug").exists()
    assert not (tmp_path / ("escape.apkg" if format_name == "apkg" else "escape")).exists()


def test_public_export_resolves_active_pointer_once_and_has_no_candidate_fallback(
    approved_snapshot: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    calls = 0

    def resolver() -> object:
        nonlocal calls
        calls += 1
        return approved_snapshot

    monkeypatch.setattr(api, "resolve_active_korean_foundation_snapshot", resolver)
    result = api.export_korean_foundation(
        family=api.KoreanFoundationFamily.PRONUNCIATION,
        export_format=api.ExportArtifactFormat.CSV,
        output_destination=tmp_path / "pronunciation",
    )

    assert calls == 1
    assert result.output_path.is_file()
    assert tuple(inspect.signature(api.export_korean_foundation).parameters) == (
        "family",
        "export_format",
        "output_destination",
    )
    source = inspect.getsource(api.export_korean_foundation)
    assert source.count("resolve_active_korean_foundation_snapshot()") == 1
    assert "load_pending" not in source
    assert "candidate" not in source


def test_media_byte_race_after_validation_leaves_no_partial_output(
    approved_snapshot: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    original_validate = api._validate_export_bundle
    changed_path: Path | None = None
    original_bytes = b""

    def validate_then_change(bundle: object) -> None:
        nonlocal changed_path, original_bytes
        original_validate(bundle)
        changed_path = bundle.media[0].path
        original_bytes = changed_path.read_bytes()
        changed_path.write_bytes(original_bytes + b"tampered-after-validation")

    monkeypatch.setattr(api, "_validate_export_bundle", validate_then_change)
    destination = tmp_path / "race.apkg"
    try:
        with pytest.raises(ValueError, match="media_byte_mismatch"):
            api._export_korean_foundation_from_snapshot(
                approved_snapshot,
                family=api.KoreanFoundationFamily.HANGUL,
                export_format=api.ExportArtifactFormat.APKG,
                output_destination=destination,
            )
    finally:
        if changed_path is not None:
            changed_path.write_bytes(original_bytes)

    assert not destination.exists()
    assert not list(tmp_path.glob(".korean-foundation-*"))


@pytest.mark.parametrize(
    "row",
    [
        lambda api: replace(_hangul_row(api), audio='<img src="wrong.png">'),
        lambda api: replace(_hangul_row(api), strokes="[sound:wrong.wav]"),
        lambda api: replace(_hangul_row(api), gif='<img src="wrong.png">'),
        lambda api: replace(
            _pronunciation_row(api),
            letter_audio='<img src="wrong.png">',
        ),
    ],
)
def test_row_media_fields_reject_cross_kind_or_wrong_format_tags(row: object) -> None:
    api = _export()

    with pytest.raises(ValueError, match="media field"):
        row(api).ordered_fields()


@pytest.mark.parametrize("format_name", ["apkg", "csv", "tsv"])
def test_output_cannot_be_published_inside_the_immutable_snapshot(
    format_name: str,
    approved_snapshot: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _export()
    destination = approved_snapshot.snapshot_root / "forbidden-output" / (
        "hangul.apkg" if format_name == "apkg" else "hangul"
    )

    def forbidden_writer(*args: object, **kwargs: object) -> object:
        raise AssertionError("writer must not run inside the immutable snapshot")

    monkeypatch.setattr(api, "_write_apkg", forbidden_writer)
    monkeypatch.setattr(api, "_write_tabular_bundle", forbidden_writer)
    with pytest.raises(ValueError, match="unsafe output destination"):
        api._export_korean_foundation_from_snapshot(
            approved_snapshot,
            family=api.KoreanFoundationFamily.HANGUL,
            export_format=api.ExportArtifactFormat(format_name),
            output_destination=destination,
        )

    assert not (approved_snapshot.snapshot_root / "forbidden-output").exists()
