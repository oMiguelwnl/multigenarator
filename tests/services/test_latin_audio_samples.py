"""Tests for representative Latin audio provider policy generation."""

from __future__ import annotations

from pathlib import Path

from multilang.services.latin_audio_samples import (
    DEEPL_PRIMARY_TRANSLATION_REASON,
    ELEVENLABS_ITALIAN_RESERVE_REASON,
    FINEVOICE_RESERVE_REASON,
    GOOGLE_TRANSLATE_CANDIDATE_REASON,
    GOOGLE_TRANSLATE_TTS_REASON,
    REPRESENTATIVE_LATIN_SAMPLE_SENTENCES,
    REPRESENTATIVE_LATIN_SAMPLE_WORDS,
    generate_latin_audio_sample_manifest,
)


def test_policy_keeps_representative_latin_review_texts(tmp_path: Path) -> None:
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path)

    assert REPRESENTATIVE_LATIN_SAMPLE_WORDS == (
        "virum",
        "puella",
        "caesar",
        "cicero",
        "veni",
        "quae",
        "cum",
        "Romae",
    )
    assert REPRESENTATIVE_LATIN_SAMPLE_SENTENCES == ("Arma virumque cano.",)
    assert manifest.representative_words == list(REPRESENTATIVE_LATIN_SAMPLE_WORDS)
    assert manifest.representative_sentences == list(REPRESENTATIVE_LATIN_SAMPLE_SENTENCES)


def test_policy_records_deepl_primary_and_google_translation_candidate(tmp_path: Path) -> None:
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path)

    deepl = manifest.provider_candidates["deepl"]
    assert deepl["status"] == "primary_translation"
    assert deepl["target_language"] == "pt"
    assert deepl["reason"] == DEEPL_PRIMARY_TRANSLATION_REASON

    google = manifest.provider_candidates["google-translate"]
    assert google["status"] == "translation_candidate"
    assert google["target_language"] == "pt"
    assert google["reason"] == GOOGLE_TRANSLATE_CANDIDATE_REASON


def test_policy_records_google_final_elevenlabs_deferred_and_finevoice_research_only(tmp_path: Path) -> None:
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path)

    google_tts = manifest.provider_candidates["google-translate-tts"]
    assert google_tts["status"] == "final_audio_provider"
    assert google_tts["voice"] == "la"
    assert google_tts["pronunciation_policy"] == "google_translate_latin"
    assert google_tts["reason"] == GOOGLE_TRANSLATE_TTS_REASON

    elevenlabs = manifest.provider_candidates["elevenlabs-italian"]
    assert elevenlabs["status"] == "deferred_billing_blocked"
    assert elevenlabs["voice"] == "it-IT"
    assert elevenlabs["pronunciation_policy"] == "italian_multilingual_approx"
    assert elevenlabs["blocking_reason"] == "HTTP 402 Payment Required for key1, key2, and key3."
    assert elevenlabs["reason"] == ELEVENLABS_ITALIAN_RESERVE_REASON

    finevoice = manifest.provider_candidates["finevoice"]
    assert finevoice["status"] == "research_candidate"
    assert finevoice["voice"] == "manual-selection-required"
    assert finevoice["reason"] == FINEVOICE_RESERVE_REASON


def test_policy_no_longer_generates_espeak_samples(tmp_path: Path) -> None:
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path)

    assert "espeak-ng" not in manifest.provider_candidates
    assert not list(tmp_path.glob("*.wav"))
    assert (tmp_path / "latin-audio-samples.json").exists()


def test_azure_multilingual_candidate_remains_blocked_with_public_reason(tmp_path: Path) -> None:
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path)

    azure = manifest.provider_candidates["azure-multilingual-experimental"]
    assert azure["status"] == "blocked"
    assert "no verified native Classical Latin/`la` Azure TTS locale" in azure["fallback_reason"]
