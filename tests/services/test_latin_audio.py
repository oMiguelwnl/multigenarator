"""Tests for Latin MVP audio metadata and integrity contracts."""

from __future__ import annotations

from hashlib import sha256

import pytest
from pydantic import ValidationError

from multilang.services.latin_audio import LatinAudioArtifact


def expected_hash(text: str) -> str:
    return sha256(" ".join(text.split()).encode("utf-8")).hexdigest()


def make_artifact(**overrides: object) -> LatinAudioArtifact:
    text = str(overrides.get("generated_text", "arma"))
    payload: dict[str, object] = {
        "audio_kind": "word",
        "provider": "espeak-ng",
        "provider_version": "1.52.0",
        "voice": "la",
        "pronunciation_policy": "classical-restored-v1",
        "generated_text": text,
        "text_hash": expected_hash(text),
        "playback_review_status": "approved",
        "storage_path": "audio/latin/word/latin-mvp-0001.mp3",
        "fallback_reason": None,
    }
    payload.update(overrides)
    return LatinAudioArtifact.model_validate(payload)


def test_word_artifact_requires_auditable_metadata_and_matching_hash() -> None:
    artifact = make_artifact(audio_kind="word", generated_text="  arma  ")

    assert artifact.audio_kind == "word"
    assert artifact.generated_text == "arma"
    assert artifact.text_hash == expected_hash("arma")
    assert artifact.provider == "espeak-ng"
    assert artifact.provider_version == "1.52.0"
    assert artifact.voice == "la"
    assert artifact.pronunciation_policy == "classical-restored-v1"
    assert artifact.playback_review_status == "approved"
    assert artifact.storage_path == "audio/latin/word/latin-mvp-0001.mp3"

    with pytest.raises(ValidationError, match="generated_text"):
        make_artifact(generated_text="   ", text_hash=expected_hash(""))
    with pytest.raises(ValidationError, match="text_hash"):
        make_artifact(text_hash="stale-hash")
    with pytest.raises(ValidationError, match="provider"):
        make_artifact(provider="unapproved-provider")
    with pytest.raises(ValidationError, match="audio_kind"):
        make_artifact(audio_kind="phrase")


def test_sentence_artifact_requires_same_metadata_contract() -> None:
    sentence = "Gallia est omnis divisa in partes tres."
    artifact = make_artifact(
        audio_kind="sentence",
        generated_text=sentence,
        storage_path="audio/latin/sentence/latin-mvp-0001.mp3",
    )

    assert artifact.audio_kind == "sentence"
    assert artifact.generated_text == sentence
    assert artifact.text_hash == expected_hash(sentence)
    assert artifact.storage_path == "audio/latin/sentence/latin-mvp-0001.mp3"

    for field_name in ("provider_version", "voice", "pronunciation_policy", "storage_path"):
        with pytest.raises(ValidationError, match=field_name):
            make_artifact(audio_kind="sentence", **{field_name: "   "})

    with pytest.raises(ValidationError, match="playback_review_status"):
        make_artifact(audio_kind="sentence", playback_review_status="queued")


def test_fallback_reason_required_for_fallback_or_blocked_provider_records() -> None:
    no_fallback = make_artifact(provider="espeak-ng", playback_review_status="approved", fallback_reason=None)
    assert no_fallback.fallback_reason is None

    fallback = make_artifact(
        provider="azure-multilingual-experimental",
        playback_review_status="needs_playback_review",
        fallback_reason="Azure multilingual Latin sample requires manual approval.",
    )
    assert fallback.fallback_reason == "Azure multilingual Latin sample requires manual approval."

    blocked = make_artifact(playback_review_status="blocked", fallback_reason="eSpeak NG unavailable on runner.")
    assert blocked.fallback_reason == "eSpeak NG unavailable on runner."

    with pytest.raises(ValidationError, match="fallback_reason"):
        make_artifact(provider="azure-multilingual-experimental", fallback_reason=None)
    with pytest.raises(ValidationError, match="fallback_reason"):
        make_artifact(playback_review_status="blocked", fallback_reason="   ")
