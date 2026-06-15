"""Tests for the Latin ElevenLabs audio refresh service."""

from __future__ import annotations

from pathlib import Path

from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.latin_audio import CURRENT_LATIN_AUDIO_PROVIDER, LatinAudioManifest
from multilang.services.latin_audio_refresh import (
    LATIN_ELEVENLABS_PRONUNCIATION_POLICY,
    generate_latin_elevenlabs_full_manifest,
    generate_latin_elevenlabs_samples,
    main,
)
from multilang.services.latin_audio_samples import (
    REPRESENTATIVE_LATIN_SAMPLE_SENTENCES,
    REPRESENTATIVE_LATIN_SAMPLE_WORDS,
)
from multilang.settings import Settings


class FakeSourceEntry:
    def __init__(self, item_key: str, target_form: str, latin_sentence: str) -> None:
        self.item_key = item_key
        self.target_form = target_form
        self.latin_sentence = latin_sentence


class FakeSourcePack:
    source_pack_version = "latin-mvp-50-v1"
    entries = [
        FakeSourceEntry(f"latin-mvp-{index:04d}", "et" if index == 1 else f"verbum{index}", f"Sententia {index}.")
        for index in range(1, 51)
    ]


def fake_source_pack() -> FakeSourcePack:
    return FakeSourcePack()


class FakeLatinSynthesizer:
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
    ) -> AudioSynthesisResponse:
        self.calls.append(
            {
                "ssml_text": ssml_text,
                "voice_id": voice_id,
                "locale": locale,
                "output_path": output_path,
                "audio_format": audio_format,
            }
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"ID3-fake-latin-audio")
        return AudioSynthesisResponse(storage_path=output_path, byte_size=output_path.stat().st_size, duration_ms=None)


def test_generate_latin_elevenlabs_samples_writes_manifest_and_mp3_metadata(tmp_path: Path) -> None:
    fake = FakeLatinSynthesizer()
    settings = Settings(_env_file=None, elevenlabs_voice_id="voice-123", elevenlabs_model_id="eleven_multilingual_v2")
    result = generate_latin_elevenlabs_samples(
        output_dir=Path("samples"),
        synthesizer=fake,
        settings=settings,
        repo_root=tmp_path,
    )

    assert result.provider == CURRENT_LATIN_AUDIO_PROVIDER
    assert result.provider_version == "eleven_multilingual_v2"
    assert result.pronunciation_policy == LATIN_ELEVENLABS_PRONUNCIATION_POLICY
    assert result.sample_manifest_path == "samples/latin-audio-samples.json"
    assert len(result.artifacts) == len(REPRESENTATIVE_LATIN_SAMPLE_WORDS) + len(REPRESENTATIVE_LATIN_SAMPLE_SENTENCES)
    assert len(fake.calls) == 9
    assert (tmp_path / "samples" / "latin-audio-samples.json").exists()
    assert len(list((tmp_path / "samples").glob("*.mp3"))) == 9

    first = result.artifacts[0].artifact
    assert first.provider == CURRENT_LATIN_AUDIO_PROVIDER
    assert first.playback_review_status == "needs_playback_review"
    assert first.storage_path == "samples/word-01-virum.mp3"
    assert first.fallback_reason is None


def test_generate_latin_elevenlabs_full_manifest_uses_source_pack_text_and_mp3_paths(tmp_path: Path) -> None:
    fake = FakeLatinSynthesizer()
    manifest = generate_latin_elevenlabs_full_manifest(
        output_dir=Path("audio"),
        synthesizer=fake,
        settings=Settings(_env_file=None, elevenlabs_voice_id="voice-123"),
        repo_root=tmp_path,
        source_pack_loader=fake_source_pack,
    )

    assert isinstance(manifest, LatinAudioManifest)
    assert len(manifest.artifacts) == 50
    assert len(fake.calls) == 100
    first = manifest.artifacts[0]
    assert first.item_key == "latin-mvp-0001"
    assert first.word is not None
    assert first.sentence is not None
    assert first.word.provider == CURRENT_LATIN_AUDIO_PROVIDER
    assert first.word.generated_text == "et"
    assert first.word.storage_path == "audio/latin-mvp-0001-word.mp3"
    assert first.sentence.storage_path == "audio/latin-mvp-0001-sentence.mp3"


def test_module_cli_generates_samples_and_review_stub_with_fake_adapter(tmp_path: Path, monkeypatch) -> None:
    fake = FakeLatinSynthesizer()

    class FakeAdapterFactory:
        def __init__(self, settings: Settings) -> None:
            self.settings = settings

        def synthesize(self, **kwargs):
            return fake.synthesize(**kwargs)

    monkeypatch.setattr("multilang.services.latin_audio_refresh.ElevenLabsSpeechAdapter", FakeAdapterFactory)
    review_path = tmp_path / "review.md"

    main([
        "generate-samples",
        "--output-dir",
        str(tmp_path / "samples"),
        "--review-path",
        str(review_path),
        "--provider",
        "elevenlabs-italian",
    ])

    assert review_path.exists()
    assert "selected_provider: elevenlabs-italian" in review_path.read_text(encoding="utf-8")
    assert (tmp_path / "samples" / "latin-audio-refresh-samples.json").exists()
    assert len(list((tmp_path / "samples").glob("*.mp3"))) == 9
