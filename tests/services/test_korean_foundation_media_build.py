from __future__ import annotations

import importlib.util
import io
import json
from hashlib import sha256
from pathlib import Path
from types import ModuleType, SimpleNamespace
import wave

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


def _pcm_wav_bytes(*, duration_ms: int = 120) -> bytes:
    frame_rate = 16_000
    frame_count = frame_rate * duration_ms // 1_000
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(frame_rate)
        wav_file.writeframes(b"\x00\x01" * frame_count)
    return buffer.getvalue()


def _fake_required_slots() -> list[SimpleNamespace]:
    slots: list[SimpleNamespace] = []
    for sequence in range(1, 93):
        slots.append(
            SimpleNamespace(
                family=SimpleNamespace(value="hangul"),
                item_key=f"ko-hangul-{sequence:04d}",
                sequence=sequence,
                slot_id=f"hangul.strokes.{sequence:04d}",
                media_kind="strokes",
                required=True,
                output_format="png",
                storage_relpath=f"media/hangul/hangul-strokes-{sequence:04d}.png",
                source_content_sha256="1" * 64,
            )
        )
    for sequence in range(1, 234):
        slots.append(
            SimpleNamespace(
                family=SimpleNamespace(value="pronunciation"),
                item_key=f"ko-pron-{sequence:04d}",
                sequence=sequence + 92,
                slot_id=f"pron.word-audio.{sequence:04d}",
                media_kind="word_audio",
                required=True,
                output_format="pcm_s16le_wav",
                storage_relpath=f"media/pronunciation/pron-word-audio-{sequence:04d}.wav",
                source_content_sha256="2" * 64,
            )
        )
    return slots


def _fake_item_set() -> dict[str, object]:
    return {
        "manifest_version": "korean-foundations-v2-media",
        "manifest_content_sha256": "3" * 64,
        "item_set_sha256": "4" * 64,
        "all_slots": 509,
        "required_slots": 325,
        "audio_subjects": 233,
        "visual_subjects": 92,
    }


class _FakeAzureSynthesizer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> SimpleNamespace:
        content = _pcm_wav_bytes()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)
        self.calls.append(
            {
                "ssml_text": ssml_text,
                "voice_id": voice_id,
                "locale": locale,
                "output_path": output_path,
                "audio_format": audio_format,
            }
        )
        return SimpleNamespace(
            storage_path=output_path,
            byte_size=len(content),
            duration_ms=120,
        )


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
    assert stored["provider_scope"]["provider_attempt_ceiling"] == 233
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


def test_generate_authorized_reads_azure_credentials_from_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)
    monkeypatch.setattr(
        api,
        "_item_set",
        lambda: {
            "item_set_sha256": "9" * 64,
            "all_slots": 509,
            "required_slots": 325,
            "audio_subjects": 233,
            "visual_subjects": 92,
        },
    )
    monkeypatch.setattr(
        api,
        "_required_slots",
        lambda: [
            SimpleNamespace(
                family=SimpleNamespace(value="hangul"),
                item_key="ko-hangul-0001",
                sequence=1,
                slot_id="hangul.audio.0001",
                media_kind="audio",
                required=True,
                output_format="pcm_s16le_wav",
                storage_relpath="media/hangul/hangul-audio-0001.wav",
                source_content_sha256="1" * 64,
            )
        ],
    )
    monkeypatch.setattr(
        api,
        "_slot_texts",
        lambda: {
            "hangul.audio.0001": {
                "display_text": "ㄱ",
                "spoken_text": "ㄱ",
            }
        },
    )

    def failing_synthesizer() -> object:
        class _Failing:
            def synthesize(self, **_: object) -> object:
                raise api.MediaRightsError(api.MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED)

        return _Failing()

    monkeypatch.setattr(api, "_azure_synthesizer", failing_synthesizer)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MULTILANG_AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("MULTILANG_AZURE_SPEECH_REGION", raising=False)
    (tmp_path / ".env").write_text(
        "MULTILANG_AZURE_SPEECH_KEY=test-key\n"
        "MULTILANG_AZURE_SPEECH_REGION=westeurope\n",
        encoding="utf-8",
    )
    api.prepare_rights()
    rights_sha256 = api.validate_rights()
    _write_media_authority(api, tmp_path, rights_sha256)

    result = api.generate_authorized()
    projected = api.project_acoustic()

    assert result["status"] != "blocked" or result["reason_code"] != "azure_speech_credentials_missing"


def test_hangul_audio_uses_synthesizable_display_glyph_when_mapped() -> None:
    api = _builder()
    mapping = SimpleNamespace(display_glyph="ㄱ")
    entry = SimpleNamespace(
        family=SimpleNamespace(value="hangul"),
        canonical_jamo_or_block="ᄀ",
        pedagogical_jamo_mapping=mapping,
    )

    assert api._spoken_text(entry, "audio", "ㄱ") == "ㄱ"


def test_hangul_audio_decomposes_compound_compatibility_jamo_for_azure() -> None:
    api = _builder()
    entry = SimpleNamespace(
        family=SimpleNamespace(value="hangul"),
        canonical_jamo_or_block="ᆪ",
        pedagogical_jamo_mapping=SimpleNamespace(display_glyph="ㄳ"),
    )

    assert api._spoken_text(entry, "audio", "ㄳ") == "ㄱ ㅅ"


def test_generate_authorized_writes_media_and_passing_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)
    fake_slots = _fake_required_slots()
    fake_synthesizer = _FakeAzureSynthesizer()
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_REGION", "westeurope")
    monkeypatch.setattr(api, "_required_slots", lambda: fake_slots)
    monkeypatch.setattr(api, "_item_set", _fake_item_set)
    monkeypatch.setattr(
        api,
        "_slot_texts",
        lambda: {
            slot.slot_id: {
                "display_text": f"표시 {slot.sequence}",
                "spoken_text": f"소리 {slot.sequence}",
            }
            for slot in fake_slots
        },
    )
    monkeypatch.setattr(api, "_azure_synthesizer", lambda: fake_synthesizer)
    api.prepare_rights()
    rights_sha256 = api.validate_rights()
    _write_media_authority(api, tmp_path, rights_sha256)

    result = api.generate_authorized()
    aggregate_root = api.verify_evidence()
    status = api.acoustic_status()
    artifacts_path = tmp_path / PHASE_RELPATH / "evidence-inbox" / "media" / "artifacts.json"
    artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
    acoustic = json.loads(
        (tmp_path / PHASE_RELPATH / "evidence-inbox" / "acoustic-review.json").read_text(
            encoding="utf-8"
        )
    )
    authority_path = tmp_path / PHASE_RELPATH / "execution-handoffs" / "media-authority.json"
    authority = json.loads(
        authority_path.read_text(encoding="utf-8")
    )
    authority_sha256 = sha256(authority_path.read_bytes()).hexdigest()

    assert result["status"] == "passing"
    assert aggregate_root == result["aggregate_root"]
    assert status == {
        "status": "passing",
        "required_slots": 325,
        "audio_subjects": 233,
        "visual_subjects": 92,
        "passing": 325,
        "blocked": 0,
    }
    assert len(fake_synthesizer.calls) == 233
    assert len(artifacts["artifacts"]) == 325
    assert artifacts["content_hash"] == api._media_artifacts_sha256(artifacts["artifacts"])
    assert authority["consumed"] is True
    assert authority["content_hash"] == api._canonical_handoff_hash(authority)
    assert artifacts["media_authority_sha256"] == authority_sha256
    assert acoustic["media_authority_sha256"] == authority_sha256
    assert "test-key" not in artifacts_path.read_text(encoding="utf-8")
    for row in artifacts["artifacts"]:
        path = tmp_path / PHASE_RELPATH / "evidence-inbox" / row["repository_relpath"]
        assert path.is_file()
        assert sha256(path.read_bytes()).hexdigest() == row["artifact_sha256"]


def test_generate_authorized_reuses_existing_passing_media_without_provider_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)
    fake_slots = _fake_required_slots()
    fake_synthesizer = _FakeAzureSynthesizer()
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_REGION", "westeurope")
    monkeypatch.setattr(api, "_required_slots", lambda: fake_slots)
    monkeypatch.setattr(api, "_item_set", _fake_item_set)
    monkeypatch.setattr(
        api,
        "_slot_texts",
        lambda: {
            slot.slot_id: {
                "display_text": f"표시 {slot.sequence}",
                "spoken_text": f"소리 {slot.sequence}",
            }
            for slot in fake_slots
        },
    )
    monkeypatch.setattr(api, "_azure_synthesizer", lambda: fake_synthesizer)
    api.prepare_rights()
    rights_sha256 = api.validate_rights()
    _write_media_authority(api, tmp_path, rights_sha256)
    first = api.generate_authorized()

    def unexpected_synthesizer() -> object:
        raise AssertionError("existing passing media must not replay Azure synthesis")

    monkeypatch.setattr(api, "_azure_synthesizer", unexpected_synthesizer)

    replay = api.generate_authorized()

    assert replay == first
    assert len(fake_synthesizer.calls) == 233


def test_verify_evidence_rejects_stale_current_authority_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)
    fake_slots = _fake_required_slots()
    fake_synthesizer = _FakeAzureSynthesizer()
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_REGION", "westeurope")
    monkeypatch.setattr(api, "_required_slots", lambda: fake_slots)
    monkeypatch.setattr(api, "_item_set", _fake_item_set)
    monkeypatch.setattr(
        api,
        "_slot_texts",
        lambda: {
            slot.slot_id: {
                "display_text": f"표시 {slot.sequence}",
                "spoken_text": f"소리 {slot.sequence}",
            }
            for slot in fake_slots
        },
    )
    monkeypatch.setattr(api, "_azure_synthesizer", lambda: fake_synthesizer)
    api.prepare_rights()
    rights_sha256 = api.validate_rights()
    _write_media_authority(api, tmp_path, rights_sha256)
    api.generate_authorized()
    authority_path = tmp_path / PHASE_RELPATH / "execution-handoffs" / "media-authority.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["confirmation_method"] = "opencode-question-selection"
    authority["content_hash"] = api._canonical_handoff_hash(authority)
    authority_path.write_text(
        json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(api.MediaRightsError) as exc:
        api.verify_evidence()

    assert exc.value.reason_code is api.MediaRightsReasonCode.ACOUSTIC_INVALID


def test_generate_authorized_blocks_without_partial_media_on_provider_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _builder()
    _install_root(api, monkeypatch, tmp_path)
    fake_slots = _fake_required_slots()
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setenv("MULTILANG_AZURE_SPEECH_REGION", "westeurope")
    monkeypatch.setattr(api, "_required_slots", lambda: fake_slots)
    monkeypatch.setattr(api, "_item_set", _fake_item_set)
    monkeypatch.setattr(
        api,
        "_slot_texts",
        lambda: {
            slot.slot_id: {
                "display_text": f"표시 {slot.sequence}",
                "spoken_text": f"소리 {slot.sequence}",
            }
            for slot in fake_slots
        },
    )

    def failing_synthesizer() -> object:
        class _Failing:
            def synthesize(self, **_: object) -> object:
                raise api.MediaRightsError(api.MediaRightsReasonCode.PROVIDER_EXECUTION_FAILED)

        return _Failing()

    monkeypatch.setattr(api, "_azure_synthesizer", failing_synthesizer)
    api.prepare_rights()
    rights_sha256 = api.validate_rights()
    _write_media_authority(api, tmp_path, rights_sha256)

    result = api.generate_authorized()
    authority = json.loads(
        (tmp_path / PHASE_RELPATH / "execution-handoffs" / "media-authority.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "provider_execution_failed"
    assert authority["consumed"] is True
    assert authority["content_hash"] == api._canonical_handoff_hash(authority)
    assert not (tmp_path / PHASE_RELPATH / "evidence-inbox" / "media").exists()
