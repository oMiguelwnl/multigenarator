"""Prepare and validate a small Mandarin audio pilot from frozen session reviews."""

from __future__ import annotations

from dataclasses import asdict
from html import unescape
from pathlib import Path

from multilang.domain.audio import AudioAssetRecord
from multilang.domain.exporting import ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.domain.text_quality import TextQualityRecord
from multilang.services.audio.media_validation import inspect_local_mp3
from multilang.services.audio_synthesis import AudioSynthesisService
from multilang.services.mandarin_pronunciation_store import load_pronunciation_store
from multilang.services.qualification_machine_runner import (
    _locked,
    json_bytes,
    persist_artifact,
    read_json,
    verify_artifact,
)
from multilang.services.vocabulary_review import _plain_path
from multilang.settings import Settings

VOICE = "zh-CN-XiaoxiaoNeural"


class _OfflineVoiceInventory:
    def available_voice_ids(self):
        return {VOICE}


def prepare_pilot(*, rows: list[ExportCardRow], bundle_path: Path, bundle_sha256: str, output: Path) -> dict:
    if not 1 <= len(rows) <= 40 or len({r.note_guid for r in rows}) != len(rows):
        raise ValueError("pilot requires 1–40 distinct notes")
    root = _plain_path(output)
    store = load_pronunciation_store(bundle_path, bundle_sha256)
    service = AudioSynthesisService(adapter=_OfflineVoiceInventory(),
        settings=Settings(_env_file=None, audio_storage_dir=root / "audio-cache"), mandarin_review_service=store)
    requests = []
    for row in rows:
        if row.identity.language is not SupportedLanguage.ZH or row.image or row.word_audio or row.sentence_audio:
            raise ValueError("pilot requires Mandarin rows with empty image and audio")
        reviewed = store.derive(word=row.word, sentence=row.example_sentence)
        expected = {
            "word_pinyin": row.mandarin_word_pinyin, "word_traditional": row.mandarin_word_traditional,
            "sentence_pinyin": row.mandarin_sentence_pinyin, "sentence_traditional": row.mandarin_sentence_traditional,
        }
        if any(asdict(reviewed)[key] != unescape(value) for key, value in expected.items()):
            raise ValueError("card reading differs from its frozen pronunciation review")
        text = TextQualityRecord(job_id=row.identity.job_id, item_key=row.identity.item_key,
            lexical_candidate_id=row.identity.lemma_key, example_sentence=row.example_sentence,
            translation_text=row.translation, generation_status="generated", validation_status="passed",
            review_status="accepted", confidence_label="medium", review_reason="source-reviewed session pilot",
            sentence_provenance={"source": "session-review", "provider": "current-session"},
            translation_provenance={"source": "session-review", "provider": "current-session"})
        assets = service.prepare_item_assets(language=SupportedLanguage.ZH, display_word=row.word, text_record=text)
        for asset in (assets.word_asset, assets.sentence_asset):
            payload = asset.model_dump(mode="json")
            identifier = canonical_sha256(payload)
            requests.append({"id": identifier, "note_guid": row.note_guid,
                             "kind": asset.asset_kind.value, "asset": payload})
    summary = {"note_count": len(rows), "audio_request_count": len(requests),
        "spoken_characters": sum(len(r["asset"]["display_text"]) for r in requests),
        "provider_calls_executed": 0, "voice": VOICE, "bundle_sha256": bundle_sha256,
        "production_eligible": False, "independent_human_review": False}
    payload = {"summary": summary, "requests": requests, "rows": [r.model_dump(mode="json") for r in rows]}
    persist_artifact(root / "input", kind="mandarin-audio-pilot-input", binding=canonical_sha256(payload),
                     files={"pilot.json": json_bytes(payload)})
    return summary


def _input(root: Path) -> dict:
    manifest = verify_artifact(root / "input", kind="mandarin-audio-pilot-input")
    data = read_json(root / "input/pilot.json")
    if canonical_sha256(data) != manifest["binding_sha256"] or not 1 <= len(data["requests"]) <= 80:
        raise ValueError("pilot input binding drift")
    requests = data["requests"]
    if any(canonical_sha256(item["asset"]) != item["id"] for item in requests):
        raise ValueError("pilot audio request binding drift")
    rows = [ExportCardRow.model_validate(row) for row in data["rows"]]
    expected = {(row.note_guid, kind) for row in rows for kind in ("word", "sentence")}
    actual = {(item["note_guid"], item["kind"]) for item in requests}
    if (not 1 <= len(rows) <= 40 or len({r.note_guid for r in rows}) != len(rows)
            or actual != expected or len(requests) != len(expected)
            or data["summary"]["audio_request_count"] != len(requests)
            or data["summary"]["note_count"] != len(rows)):
        raise ValueError("pilot requests must match each note's word and sentence")
    characters = sum(len(item["asset"]["display_text"]) for item in requests)
    if not 1 <= characters <= 12000 or data["summary"]["spoken_characters"] != characters:
        raise ValueError("pilot exceeds speech character limit")
    return data


def synthesize_pilot(*, root: Path, settings: Settings) -> dict:
    """Explicit paid boundary: Azure only, one attempt per persisted request."""
    from multilang.services.azure_speech_adapter import AzureSpeechAdapter

    root = _plain_path(root)
    data = _input(root)
    adapter = AzureSpeechAdapter(settings)
    voices = adapter.fetch_voice_inventory_for_locale("zh-CN")
    selected = [v for v in voices if v.get("ShortName") == VOICE and v.get("Locale") == "zh-CN"]
    if len(selected) != 1:
        raise ValueError("reviewed Mandarin voice is unavailable")
    persist_artifact(root / "voice", kind="mandarin-azure-voice", binding=canonical_sha256(selected),
                     files={"voice.json": json_bytes(selected)})
    calls, reused = 0, 0
    with _locked(root / "audio-run"):
        for request in data["requests"]:
            identifier = request["id"]
            if canonical_sha256(request["asset"]) != identifier:
                raise ValueError("audio request drift")
            call_root = root / "calls" / identifier
            response_root = root / "results" / identifier
            if response_root.exists():
                _verified_media(root, request)
                reused += 1
                continue
            if call_root.exists():
                raise ValueError("previous audio call has no verified result; inspect before retry")
            asset = AudioAssetRecord.model_validate(request["asset"])
            target = _plain_path(root / "media" / f"{identifier}.mp3")
            if target.exists():
                raise ValueError("audio exists without a receipt; inspect before retry")
            persist_artifact(call_root, kind="mandarin-azure-request", binding=identifier,
                             files={"request.json": json_bytes(request)})
            response = adapter.synthesize(ssml_text=asset.normalized_input.ssml_text,
                voice_id=VOICE, locale="zh-CN", output_path=target,
                audio_format=asset.provenance.format.value, timeout_seconds=60)
            calls += 1
            media = inspect_local_mp3(str(target), expected_byte_size=response.byte_size)
            if media is None or not 150 <= media.duration_ms <= 30000:
                raise ValueError("Azure returned invalid pilot audio")
            receipt = {"request_id": identifier, "filename": target.name,
                "sha256": media.artifact_sha256, "byte_size": media.byte_size,
                "duration_ms": media.duration_ms, "provider": "azure", "voice": VOICE,
                "locale": "zh-CN", "acoustic_pronunciation_review": "pending"}
            persist_artifact(response_root, kind="mandarin-azure-result", binding=identifier,
                             files={"audio.json": json_bytes(receipt)})
            print(f"Azure audio: {calls} generated; {reused} verified/reused", flush=True)
    return {"generated_assets": calls, "reused_assets": reused, "audio_provider": "azure"}


def _verified_media(root: Path, request: dict) -> Path:
    identifier = request["id"]
    try:
        manifest = verify_artifact(root / "results" / identifier, kind="mandarin-azure-result")
        receipt = read_json(root / "results" / identifier / "audio.json")
    except (ValueError, OSError):
        raise ValueError("pilot audio has no verified result") from None
    if (manifest["binding_sha256"] != identifier or receipt["request_id"] != identifier
            or receipt["filename"] != f"{identifier}.mp3"):
        raise ValueError("pilot audio binding drift")
    path = _plain_path(root / "media" / receipt["filename"])
    info = inspect_local_mp3(str(path), expected_byte_size=receipt["byte_size"])
    if info is None or info.artifact_sha256 != receipt["sha256"] or info.duration_ms != receipt["duration_ms"]:
        raise ValueError("pilot audio content drift")
    return path


def verified_pilot_rows(root: Path) -> tuple[list[ExportCardRow], dict[str, Path]]:
    root = _plain_path(root)
    data = _input(root)
    mapping, media = {}, {}
    for request in data["requests"]:
        path = _verified_media(root, request)
        sound = f"[sound:{path.name}]"
        mapping[(request["note_guid"], request["kind"])] = sound
        media[sound] = path
    rows = []
    for payload in data["rows"]:
        row = ExportCardRow.model_validate(payload)
        rows.append(row.model_copy(update={"word_audio": mapping[(row.note_guid, "word")],
                                          "sentence_audio": mapping[(row.note_guid, "sentence")]}))
    return rows, media
