"""Tests for Latin MVP audio metadata and integrity contracts."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Callable

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
        "provider": "elevenlabs-italian",
        "provider_version": "eleven_multilingual_v2",
        "voice": "it-IT",
        "pronunciation_policy": "italian_multilingual_approx",
        "generated_text": text,
        "text_hash": expected_hash(text),
        "playback_review_status": "approved",
        "storage_path": "audio/latin/word/latin-mvp-0001.mp3",
        "fallback_reason": "ElevenLabs Italian reserve requires playback review for Latin.",
    }
    payload.update(overrides)
    return LatinAudioArtifact.model_validate(payload)


AudioOverrideKey = tuple[str, str]


def make_manifest(
    overrides: dict[AudioOverrideKey, dict[str, object]] | None = None,
    *,
    storage_path_factory: Callable[[str, str], str] | None = None,
) -> LatinAudioManifest:
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
        word_storage_path = str(
            word_overrides.pop(
                "storage_path",
                storage_path_factory(entry.item_key, "word")
                if storage_path_factory is not None
                else f"data/latin_mvp/audio/latin-mvp-50-v1/{entry.item_key}-word.wav",
            )
        )
        sentence_storage_path = str(
            sentence_overrides.pop(
                "storage_path",
                storage_path_factory(entry.item_key, "sentence")
                if storage_path_factory is not None
                else f"data/latin_mvp/audio/latin-mvp-50-v1/{entry.item_key}-sentence.wav",
            )
        )
        pairs.append(
            LatinAudioPair(
                item_key=entry.item_key,
                word=make_artifact(
                    audio_kind="word",
                    generated_text=word_text,
                    text_hash=expected_hash(word_text),
                    storage_path=word_storage_path,
                    **word_overrides,
                ),
                sentence=make_artifact(
                    audio_kind="sentence",
                    generated_text=sentence_text,
                    text_hash=expected_hash(sentence_text),
                    storage_path=sentence_storage_path,
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
    assert artifact.provider == "elevenlabs-italian"
    assert artifact.provider_version == "eleven_multilingual_v2"
    assert artifact.voice == "it-IT"
    assert artifact.pronunciation_policy == "italian_multilingual_approx"
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


def test_fallback_reason_required_for_reserve_or_blocked_provider_records() -> None:
    no_fallback = make_artifact(provider="espeak-ng", playback_review_status="approved", fallback_reason=None)
    assert no_fallback.fallback_reason is None

    fallback = make_artifact(
        provider="finevoice",
        playback_review_status="needs_playback_review",
        fallback_reason="FineVoice Latin sample requires manual approval.",
    )
    assert fallback.fallback_reason == "FineVoice Latin sample requires manual approval."

    blocked = make_artifact(playback_review_status="blocked", fallback_reason="reserve provider unavailable on runner.")
    assert blocked.fallback_reason == "reserve provider unavailable on runner."

    with pytest.raises(ValidationError, match="fallback_reason"):
        make_artifact(provider="elevenlabs-italian", fallback_reason=None)
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


def write_manifest_media_files(repo_root: Path) -> Callable[[str, str], str]:
    def storage_path_for(item_key: str, audio_kind: str) -> str:
        relative_path = Path("audio") / "latin" / audio_kind / f"{item_key}.wav"
        media_path = repo_root / relative_path
        media_path.parent.mkdir(parents=True, exist_ok=True)
        media_path.write_bytes(b"RIFFfake-wave")
        return relative_path.as_posix()

    return storage_path_for


def test_approved_audio_with_unsafe_or_missing_storage_path_blocks_export_readiness(tmp_path: Path) -> None:
    storage_path_for = write_manifest_media_files(tmp_path)
    (tmp_path / "audio" / "empty.wav").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "audio" / "empty.wav").write_bytes(b"")
    (tmp_path / "audio" / "not-media.wav").write_text("not really audio", encoding="utf-8")

    bad_paths = [
        "C:/private/latin-mvp-0001-word.wav",
        "../outside.wav",
        "audio/missing.wav",
        "audio/empty.wav",
        "audio/not-media.wav",
    ]

    for bad_path in bad_paths:
        manifest = make_manifest(
            {("latin-mvp-0001", "word"): {"storage_path": bad_path}},
            storage_path_factory=storage_path_for,
        )

        with pytest.raises(ValueError) as exc_info:
            assert_latin_audio_manifest_export_ready(manifest, repo_root=tmp_path)

        message = str(exc_info.value)
        assert "latin-mvp-0001" in message
        assert "audio_kind=word" in message
        assert "field=storage_path" in message
        assert bad_path not in message
        assert str(tmp_path) not in message
        assert "C:\\" not in message
        assert "/Users/" not in message


def test_approved_audio_with_existing_riff_storage_path_passes_export_readiness(tmp_path: Path) -> None:
    manifest = make_manifest(storage_path_factory=write_manifest_media_files(tmp_path))

    assert_latin_audio_manifest_export_ready(manifest, repo_root=tmp_path)


def test_approved_audio_with_existing_id3_storage_path_passes_export_readiness(tmp_path: Path) -> None:
    def storage_path_for(item_key: str, audio_kind: str) -> str:
        relative_path = Path("audio") / "latin" / audio_kind / f"{item_key}.mp3"
        media_path = tmp_path / relative_path
        media_path.parent.mkdir(parents=True, exist_ok=True)
        media_path.write_bytes(b"ID3fake-mp3")
        return relative_path.as_posix()

    manifest = make_manifest(storage_path_factory=storage_path_for)

    assert_latin_audio_manifest_export_ready(manifest, repo_root=tmp_path)


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
                        "fallback_reason": "reserve sample unavailable.",
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
