"""Scanner-readable v2.1 Google TTS final Latin audio evidence."""

from __future__ import annotations

import json
from pathlib import Path

from multilang.services.latin_audio import assert_latin_audio_manifest_export_ready, load_latin_audio_manifest
from multilang.services.latin_audio_samples import generate_latin_audio_sample_manifest
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


PHASE_29_REQUIREMENTS = ("AUDR-01", "AUDR-02", "AUDR-03", "AUDR-04", "AUDR-05")
REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_PATH = REPO_ROOT / ".planning/phases/29-latin-elevenlabs-audio-refresh/29-GOOGLE-TTS-FINAL-REVIEW.md"
SECOND_PASS_REVIEW_PATH = REPO_ROOT / ".planning/phases/29-latin-elevenlabs-audio-refresh/29-SECOND-PASS-REVIEW.md"
STATE_PATH = REPO_ROOT / ".planning/STATE.md"
LATIN_STRUCTURE_PATH = REPO_ROOT / "LATIN-STRUCTURE.md"


def _review_field(name: str) -> str:
    for line in REVIEW_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"missing review field: {name}")


def _second_pass_field(name: str) -> str:
    for line in SECOND_PASS_REVIEW_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"missing second-pass field: {name}")


def test_phase_29_requirements_are_scanner_readable() -> None:
    assert PHASE_29_REQUIREMENTS == ("AUDR-01", "AUDR-02", "AUDR-03", "AUDR-04", "AUDR-05")


def test_google_tts_final_review_records_provider_and_deferred_candidates() -> None:
    assert REVIEW_PATH.exists()
    review_text = REVIEW_PATH.read_text(encoding="utf-8")

    assert _review_field("selected_provider") == "google-translate-tts"
    assert _review_field("selected_voice") == "la"
    assert _review_field("pronunciation_policy") == "google_translate_latin"
    assert _review_field("provider_version") == "google-translate-tts-la"
    assert _review_field("playback_review_status") == "approved"
    assert _review_field("elevenlabs_status") == "deferred_billing_blocked"
    assert _review_field("finevoice_status") == "research_only"
    assert _review_field("system_espeak_uninstall") == "not_requested"
    assert "HTTP 402 Payment Required" in review_text
    assert "api_key" not in review_text.lower()
    assert "secret" not in review_text.lower()


def test_second_pass_review_records_closing_provider_verdict() -> None:
    assert SECOND_PASS_REVIEW_PATH.exists()
    review_text = SECOND_PASS_REVIEW_PATH.read_text(encoding="utf-8")

    assert _second_pass_field("selected_provider") == "google-translate-tts"
    assert _second_pass_field("selected_voice") == "la"
    assert _second_pass_field("pronunciation_policy") == "google_translate_latin"
    assert _second_pass_field("review_status") == "passed"
    assert _second_pass_field("elevenlabs_status") == "deferred_billing_blocked"
    assert _second_pass_field("finevoice_status") == "research_only"
    assert "100 media" in review_text
    assert "50 cards" in review_text


def test_sample_policy_keeps_google_final_and_finevoice_research_only(tmp_path: Path) -> None:
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path)
    candidates = manifest.provider_candidates

    assert candidates["google-translate-tts"]["status"] == "final_audio_provider"
    assert candidates["google-translate-tts"]["voice"] == "la"
    assert candidates["google-translate-tts"]["pronunciation_policy"] == "google_translate_latin"
    assert candidates["elevenlabs-italian"]["status"] == "deferred_billing_blocked"
    assert candidates["finevoice"]["status"] == "research_candidate"
    assert "espeak-ng" not in candidates


def test_committed_manifest_uses_google_tts_for_all_source_aligned_audio() -> None:
    source_pack = load_latin_mvp_source_pack()
    manifest = load_latin_audio_manifest()

    assert [pair.item_key for pair in manifest.artifacts] == [entry.item_key for entry in source_pack.entries]
    assert len(manifest.artifacts) == 50
    assert_latin_audio_manifest_export_ready(manifest, repo_root=REPO_ROOT)

    provider_counts: dict[str, int] = {}
    for entry, pair in zip(source_pack.entries, manifest.artifacts, strict=True):
        assert pair.word is not None
        assert pair.sentence is not None
        for artifact, expected_text in ((pair.word, entry.target_form), (pair.sentence, entry.latin_sentence)):
            assert artifact.provider == "google-translate-tts"
            assert artifact.provider_version == "google-translate-tts-la"
            assert artifact.voice == "la"
            assert artifact.pronunciation_policy == "google_translate_latin"
            assert artifact.generated_text == expected_text
            assert artifact.playback_review_status == "approved"
            assert artifact.fallback_reason is None
            media_path = REPO_ROOT / artifact.storage_path
            assert media_path.exists()
            assert media_path.read_bytes().startswith(b"ID3")
            provider_counts[artifact.provider] = provider_counts.get(artifact.provider, 0) + 1

    assert provider_counts == {"google-translate-tts": 100}


def test_audio_assets_do_not_leak_provider_secrets_or_private_paths() -> None:
    payload = json.dumps(load_latin_audio_manifest().model_dump(mode="json"), ensure_ascii=False)
    payload += REVIEW_PATH.read_text(encoding="utf-8")
    payload += SECOND_PASS_REVIEW_PATH.read_text(encoding="utf-8")

    forbidden = ["api_key", "api key", "secret", "raw_response", "provider_response", "C:\\", "/Users/", "/home/"]
    for token in forbidden:
        assert token.casefold() not in payload.casefold()


def test_current_docs_do_not_require_live_elevenlabs_or_system_espeak_for_latin_export() -> None:
    state_text = STATE_PATH.read_text(encoding="utf-8")
    structure_text = LATIN_STRUCTURE_PATH.read_text(encoding="utf-8")
    current_text = state_text + "\n" + structure_text

    assert "google-translate-tts" in current_text
    assert "google_translate_latin" in current_text
    assert "ElevenLabs italiano permanece deferido" in structure_text
    assert "nao e requisito para exportar o MVP 50 atual" in structure_text
    assert "eSpeak NG lista suporte" not in structure_text
    assert "espeak-ng -v la" not in structure_text
