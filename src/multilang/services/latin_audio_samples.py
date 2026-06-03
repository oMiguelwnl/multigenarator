"""Representative Latin audio sample manifest generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from multilang.services.espeak_ng_speech_adapter import EspeakNgSpeechAdapter
from multilang.services.latin_audio import LatinAudioArtifact, latin_audio_text_hash


REPRESENTATIVE_LATIN_SAMPLE_WORDS = (
    "virum",
    "puella",
    "caesar",
    "cicero",
    "veni",
    "quae",
    "cum",
    "Romae",
)
REPRESENTATIVE_LATIN_SAMPLE_SENTENCES = ("Arma virumque cano.",)
DEFAULT_LATIN_AUDIO_SAMPLE_DIR = Path(".multilang") / "latin-audio-samples"
AZURE_LATIN_FALLBACK_REASON = "no verified native Classical Latin/`la` Azure TTS locale"


class LatinAudioSampleManifest(BaseModel):
    """Provider comparison samples for the Phase 27 playback checkpoint."""

    manifest_version: str = "latin-audio-samples-v1"
    provider_candidates: dict[str, dict[str, str]]
    espeak_samples: list[LatinAudioArtifact] = Field(default_factory=list)
    azure_samples: list[LatinAudioArtifact] = Field(default_factory=list)


def _sample_storage_path(filename: str) -> str:
    return str(DEFAULT_LATIN_AUDIO_SAMPLE_DIR / filename).replace("\\", "/")


def _write_manifest_file(manifest: LatinAudioSampleManifest, output_dir: Path) -> None:
    payload: dict[str, Any] = manifest.model_dump(mode="json")
    (output_dir / "latin-audio-samples.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def generate_latin_audio_sample_manifest(
    *,
    output_dir: Path = DEFAULT_LATIN_AUDIO_SAMPLE_DIR,
    adapter: EspeakNgSpeechAdapter | None = None,
) -> LatinAudioSampleManifest:
    """Generate deterministic representative eSpeak samples and Azure comparison metadata."""

    output_dir.mkdir(parents=True, exist_ok=True)
    adapter = adapter or EspeakNgSpeechAdapter()
    provider_version = adapter.provider_version()
    samples: list[LatinAudioArtifact] = []

    for text in REPRESENTATIVE_LATIN_SAMPLE_WORDS:
        filename = f"word-{text}.wav"
        adapter.synthesize(
            ssml_text=text,
            voice_id="la",
            locale="la",
            output_path=output_dir / filename,
            audio_format="wav",
        )
        samples.append(
            LatinAudioArtifact(
                audio_kind="word",
                provider="espeak-ng",
                provider_version=provider_version,
                voice="la",
                pronunciation_policy="classical_approx",
                generated_text=text,
                text_hash=latin_audio_text_hash(text),
                playback_review_status="needs_playback_review",
                storage_path=_sample_storage_path(filename),
            )
        )

    for index, text in enumerate(REPRESENTATIVE_LATIN_SAMPLE_SENTENCES, start=1):
        filename = f"sentence-{index}.wav"
        adapter.synthesize(
            ssml_text=text,
            voice_id="la",
            locale="la",
            output_path=output_dir / filename,
            audio_format="wav",
        )
        samples.append(
            LatinAudioArtifact(
                audio_kind="sentence",
                provider="espeak-ng",
                provider_version=provider_version,
                voice="la",
                pronunciation_policy="classical_approx",
                generated_text=text,
                text_hash=latin_audio_text_hash(text),
                playback_review_status="needs_playback_review",
                storage_path=_sample_storage_path(filename),
            )
        )

    manifest = LatinAudioSampleManifest(
        provider_candidates={
            "espeak-ng": {
                "status": "needs_playback_review",
                "voice": "la",
                "pronunciation_policy": "classical_approx",
                "reason": "eSpeak NG advertises a Latin voice and generated local WAV samples for review.",
            },
            "azure-multilingual-experimental": {
                "status": "blocked",
                "voice": "multilingual-experimental",
                "pronunciation_policy": "experimental_unverified",
                "fallback_reason": AZURE_LATIN_FALLBACK_REASON,
            },
        },
        espeak_samples=samples,
        azure_samples=[],
    )
    _write_manifest_file(manifest, output_dir)
    return manifest


__all__ = [
    "AZURE_LATIN_FALLBACK_REASON",
    "DEFAULT_LATIN_AUDIO_SAMPLE_DIR",
    "LatinAudioSampleManifest",
    "REPRESENTATIVE_LATIN_SAMPLE_SENTENCES",
    "REPRESENTATIVE_LATIN_SAMPLE_WORDS",
    "generate_latin_audio_sample_manifest",
]
