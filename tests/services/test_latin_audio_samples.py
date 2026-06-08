"""Tests for representative Latin audio sample manifest generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from multilang.services.latin_audio import latin_audio_text_hash
from multilang.services.latin_audio_samples import (
    REPRESENTATIVE_LATIN_SAMPLE_SENTENCES,
    REPRESENTATIVE_LATIN_SAMPLE_WORDS,
    generate_latin_audio_sample_manifest,
)
from tests.services.test_espeak_ng_speech_adapter import FakeRunner
from multilang.services.espeak_ng_speech_adapter import EspeakNgSpeechAdapter


@dataclass(frozen=True)
class FakeCompletedProcess:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


def test_sample_set_includes_representative_words_and_sentence(tmp_path: Path) -> None:
    adapter = EspeakNgSpeechAdapter(runner=FakeRunner())
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path, adapter=adapter)

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
    assert [sample.generated_text for sample in manifest.espeak_samples if sample.audio_kind == "word"] == list(
        REPRESENTATIVE_LATIN_SAMPLE_WORDS
    )
    assert any(sample.generated_text == "Arma virumque cano." for sample in manifest.espeak_samples)


def test_espeak_sample_metadata_records_paths_hashes_and_review_status(tmp_path: Path) -> None:
    adapter = EspeakNgSpeechAdapter(runner=FakeRunner())
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path, adapter=adapter)

    assert manifest.provider_candidates["espeak-ng"]["status"] == "needs_playback_review"
    assert len(manifest.espeak_samples) == 9
    for sample in manifest.espeak_samples:
        assert sample.provider == "espeak-ng"
        assert sample.provider_version == "1.52.0"
        assert sample.voice == "la"
        assert sample.pronunciation_policy == "classical_approx"
        assert sample.playback_review_status == "needs_playback_review"
        assert sample.text_hash == latin_audio_text_hash(sample.generated_text)
        assert sample.storage_path.startswith(".multilang/latin-audio-samples/")
        assert (tmp_path / Path(sample.storage_path).name).exists()


def test_azure_multilingual_candidate_is_blocked_with_public_reason(tmp_path: Path) -> None:
    adapter = EspeakNgSpeechAdapter(runner=FakeRunner())
    manifest = generate_latin_audio_sample_manifest(output_dir=tmp_path, adapter=adapter)

    azure = manifest.provider_candidates["azure-multilingual-experimental"]
    assert azure["status"] == "blocked"
    assert "no verified native Classical Latin/`la` Azure TTS locale" in azure["fallback_reason"]
    assert not manifest.azure_samples
