"""Tests for Latin MVP audio metadata and integrity contracts."""

from __future__ import annotations

from hashlib import sha256

import pytest
from pydantic import ValidationError

from multilang.services.latin_audio import (
    LatinAudioArtifact,
    LatinAudioManifest,
    LatinAudioPair,
    assert_latin_audio_manifest_export_ready,
    summarize_latin_audio_manifest,
)
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


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


AudioOverrideKey = tuple[str, str]


def make_manifest(overrides: dict[AudioOverrideKey, dict[str, object]] | None = None) -> LatinAudioManifest:
    overrides = overrides or {}
    source_pack = load_latin_mvp_source_pack()
    pairs: list[LatinAudioPair] = []
    for entry in source_pack.entries:
        word_overrides = dict(overrides.get((entry.item_key, "word"), {}))
        sentence_overrides = dict(overrides.get((entry.item_key, "sentence"), {}))
        word_text = str(word_overrides.get("generated_text", entry.target_form))
        sentence_text = str(sentence_overrides.get("generated_text", entry.latin_sentence))
        word_overrides.pop("generated_text", None)
        word_overrides.pop("text_hash", None)
        sentence_overrides.pop("generated_text", None)
        sentence_overrides.pop("text_hash", None)
        pairs.append(
            LatinAudioPair(
                item_key=entry.item_key,
                word=make_artifact(
                    audio_kind="word",
                    generated_text=word_text,
                    text_hash=expected_hash(word_text),
                    storage_path=f"audio/latin/word/{entry.item_key}.mp3",
                    **word_overrides,
                ),
                sentence=make_artifact(
                    audio_kind="sentence",
                    generated_text=sentence_text,
                    text_hash=expected_hash(sentence_text),
                    storage_path=f"audio/latin/sentence/{entry.item_key}.mp3",
                    **sentence_overrides,
                ),
            )
        )
    return LatinAudioManifest(source_pack_version=source_pack.source_pack_version, artifacts=pairs)


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


def test_manifest_with_approved_word_and_sentence_audio_for_every_source_entry_is_export_ready() -> None:
    manifest = make_manifest()

    assert_latin_audio_manifest_export_ready(manifest)

    summary = summarize_latin_audio_manifest(manifest)
    assert summary.total_items == 50
    assert summary.approved_items == 50
    assert summary.blocked_items == 0
    assert summary.status_counts["word"]["approved"] == 50
    assert summary.status_counts["sentence"]["approved"] == 50


@pytest.mark.parametrize(
    ("manifest", "expected_kind", "expected_field"),
    [
        (
            LatinAudioManifest(
                artifacts=[pair.model_copy(update={"word": None}) for pair in make_manifest().artifacts]
            ),
            "word",
            "missing",
        ),
        (
            make_manifest({("latin-mvp-0001", "word"): {"playback_review_status": "needs_playback_review"}}),
            "word",
            "playback_review_status",
        ),
        (
            make_manifest({("latin-mvp-0001", "sentence"): {"playback_review_status": "rejected"}}),
            "sentence",
            "playback_review_status",
        ),
        (
            make_manifest(
                {
                    ("latin-mvp-0001", "sentence"): {
                        "playback_review_status": "blocked",
                        "fallback_reason": "eSpeak NG sample unavailable.",
                    }
                }
            ),
            "sentence",
            "playback_review_status",
        ),
    ],
)
def test_missing_or_unapproved_audio_fails_with_public_item_and_kind_diagnostics(
    manifest: LatinAudioManifest,
    expected_kind: str,
    expected_field: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        assert_latin_audio_manifest_export_ready(manifest)

    message = str(exc_info.value)
    assert "latin-mvp-0001" in message
    assert f"audio_kind={expected_kind}" in message
    assert expected_field in message
    assert "C:\\" not in message
    assert "/Users/" not in message


def test_word_and_sentence_generated_text_must_match_source_pack_export_text() -> None:
    source_pack = load_latin_mvp_source_pack()
    first = source_pack.entries[0]
    word_mismatch = make_manifest({(first.item_key, "word"): {"generated_text": f"{first.target_form} stale"}})
    sentence_mismatch = make_manifest(
        {(first.item_key, "sentence"): {"generated_text": f"{first.latin_sentence} stale"}}
    )
    whitespace_equivalent = make_manifest(
        {(first.item_key, "sentence"): {"generated_text": "  ".join(first.latin_sentence.split())}}
    )

    with pytest.raises(ValueError) as word_exc:
        assert_latin_audio_manifest_export_ready(word_mismatch)
    assert "latin-mvp-0001" in str(word_exc.value)
    assert "audio_kind=word" in str(word_exc.value)
    assert "generated_text" in str(word_exc.value)

    with pytest.raises(ValueError) as sentence_exc:
        assert_latin_audio_manifest_export_ready(sentence_mismatch)
    assert "latin-mvp-0001" in str(sentence_exc.value)
    assert "audio_kind=sentence" in str(sentence_exc.value)
    assert "generated_text" in str(sentence_exc.value)

    assert_latin_audio_manifest_export_ready(whitespace_equivalent)
