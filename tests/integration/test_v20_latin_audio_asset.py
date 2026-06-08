"""Integration evidence for the full Latin MVP audio asset."""

from __future__ import annotations

from pathlib import Path

import pytest

from multilang.services.latin_audio import (
    LatinAudioArtifact,
    LatinAudioManifest,
    LatinAudioPair,
    assert_latin_audio_manifest_export_ready,
    latin_audio_text_hash,
    load_latin_audio_manifest,
)
from multilang.services.latin_review import load_latin_curated_records
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


PHASE_27_REQUIREMENTS = ("AUD-01", "AUD-02", "AUD-03", "AUD-04")

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYBACK_REVIEW_PATH = REPO_ROOT / ".planning/phases/27-latin-audio-policy-and-integrity/27-AUDIO-PLAYBACK-REVIEW.md"


def _playback_review_field(name: str) -> str:
    for line in PLAYBACK_REVIEW_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"missing playback review field: {name}")


def _assert_repository_relative_media_path(storage_path: str) -> Path:
    media_path = Path(storage_path)
    assert not media_path.is_absolute()
    assert "\\" not in storage_path
    assert not storage_path.startswith(("/", "~"))
    assert ":" not in storage_path
    assert "data/latin_mvp/audio/latin-mvp-50-v1/" in storage_path
    absolute_media_path = REPO_ROOT / media_path
    assert absolute_media_path.exists()
    assert absolute_media_path.stat().st_size > 0
    assert absolute_media_path.read_bytes().startswith(b"RIFF")
    return absolute_media_path


def _replace_pair_artifact(
    manifest: LatinAudioManifest,
    *,
    item_key: str,
    audio_kind: str,
    artifact: LatinAudioArtifact | None,
) -> LatinAudioManifest:
    updated_pairs: list[LatinAudioPair] = []
    for pair in manifest.artifacts:
        if pair.item_key != item_key:
            updated_pairs.append(pair)
        elif audio_kind == "word":
            updated_pairs.append(pair.model_copy(update={"word": artifact}))
        else:
            updated_pairs.append(pair.model_copy(update={"sentence": artifact}))
    return manifest.model_copy(update={"artifacts": updated_pairs})


def test_phase_27_requirements_are_scanner_readable() -> None:
    assert PHASE_27_REQUIREMENTS == ("AUD-01", "AUD-02", "AUD-03", "AUD-04")


def test_full_manifest_has_approved_source_aligned_word_and_sentence_audio() -> None:
    source_pack = load_latin_mvp_source_pack()
    manifest = load_latin_audio_manifest()

    assert manifest.source_pack_version == source_pack.source_pack_version
    assert [pair.item_key for pair in manifest.artifacts] == [entry.item_key for entry in source_pack.entries]
    assert len(manifest.artifacts) == 50
    assert sum(pair.word is not None for pair in manifest.artifacts) == 50
    assert sum(pair.sentence is not None for pair in manifest.artifacts) == 50

    for entry, pair in zip(source_pack.entries, manifest.artifacts, strict=True):
        assert pair.word is not None
        assert pair.sentence is not None
        for artifact, expected_kind, expected_text in (
            (pair.word, "word", entry.target_form),
            (pair.sentence, "sentence", entry.latin_sentence),
        ):
            assert artifact.audio_kind == expected_kind
            assert artifact.provider == "espeak-ng"
            assert artifact.provider_version
            assert artifact.voice == "la"
            assert artifact.pronunciation_policy == "classical_approx"
            assert artifact.generated_text == expected_text
            assert artifact.text_hash == latin_audio_text_hash(expected_text)
            assert artifact.playback_review_status == "approved"
            assert artifact.fallback_reason is None
            _assert_repository_relative_media_path(artifact.storage_path)

    assert_latin_audio_manifest_export_ready(manifest)


@pytest.mark.parametrize(
    ("audio_kind", "mutation", "expected_field"),
    [
        ("word", "missing", "missing"),
        ("sentence", "unapproved", "playback_review_status"),
        ("word", "stale_hash", "text_hash"),
        ("word", "text_mismatch", "generated_text"),
        ("sentence", "text_mismatch", "generated_text"),
    ],
)
def test_manifest_readiness_fails_for_missing_unapproved_stale_or_mismatched_audio(
    audio_kind: str,
    mutation: str,
    expected_field: str,
) -> None:
    manifest = load_latin_audio_manifest()
    first_pair = manifest.artifacts[0]
    artifact = getattr(first_pair, audio_kind)
    assert artifact is not None

    if mutation == "missing":
        mutated_artifact = None
    elif mutation == "unapproved":
        mutated_artifact = artifact.model_copy(update={"playback_review_status": "needs_playback_review"})
    elif mutation == "stale_hash":
        mutated_artifact = artifact.model_copy(update={"text_hash": "0" * 64})
    else:
        mutated_artifact = artifact.model_copy(update={"generated_text": f"{artifact.generated_text} stale"})

    mutated_manifest = _replace_pair_artifact(
        manifest,
        item_key=first_pair.item_key,
        audio_kind=audio_kind,
        artifact=mutated_artifact,
    )

    with pytest.raises(ValueError) as exc_info:
        assert_latin_audio_manifest_export_ready(mutated_manifest)

    message = str(exc_info.value)
    assert "latin-mvp-0001" in message
    assert f"audio_kind={audio_kind}" in message
    assert expected_field in message
    assert "C:\\" not in message
    assert "/Users/" not in message


def test_audio_gate_approval_matches_playback_review_without_changing_other_gates() -> None:
    review_status = _playback_review_field("playback_review_status")
    reviewer = _playback_review_field("reviewer")
    reviewed_at = _playback_review_field("reviewed_at")
    selected_provider = _playback_review_field("selected_provider")
    selected_voice = _playback_review_field("selected_voice")
    pronunciation_policy = _playback_review_field("pronunciation_policy")
    records = load_latin_curated_records()

    assert review_status == "approved"
    assert selected_provider == "espeak-ng"
    assert selected_voice == "la"
    assert pronunciation_policy == "classical_approx"
    assert len(records) == 50

    for record in records:
        assert record.audio_gate.status == "approved"
        assert record.audio_gate.reason == "playback_review_approved: espeak-ng/la/classical_approx"
        assert record.audio_gate.reviewed_by == reviewer
        assert record.audio_gate.reviewed_at == reviewed_at
        assert record.source_gate.status == "approved"
        assert record.grammar_gate.status == "approved"
        assert record.translation_gate.status == "needs_review"
        assert record.translation_gate.reason == "translation_pending_phase_26"
