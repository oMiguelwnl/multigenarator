"""Representative Latin audio provider policy manifest generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


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
DEEPL_PRIMARY_TRANSLATION_REASON = "DeepL is the primary configured translation provider for generated text."
GOOGLE_TRANSLATE_CANDIDATE_REASON = "Google Translate is retained as a candidate translation provider."
GOOGLE_TRANSLATE_TTS_REASON = (
    "Google Translate TTS is retained as a reserve Latin audio candidate and requires playback review before export approval."
)
ELEVENLABS_ITALIAN_RESERVE_REASON = (
    "ElevenLabs multilingual TTS is the preferred Latin replacement candidate using an Italian locale/voice; "
    "playback review is required before export approval."
)
FINEVOICE_RESERVE_REASON = (
    "FineVoice is research-only for future evaluation; no live FineVoice adapter is implemented yet."
)


class LatinAudioSampleManifest(BaseModel):
    """Provider candidate policy for Latin audio playback review."""

    manifest_version: str = "latin-audio-samples-v1"
    provider_candidates: dict[str, dict[str, str]]
    representative_words: list[str] = Field(default_factory=list)
    representative_sentences: list[str] = Field(default_factory=list)


def _write_manifest_file(manifest: LatinAudioSampleManifest, output_dir: Path) -> None:
    payload: dict[str, Any] = manifest.model_dump(mode="json")
    (output_dir / "latin-audio-samples.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def generate_latin_audio_sample_manifest(
    *,
    output_dir: Path = DEFAULT_LATIN_AUDIO_SAMPLE_DIR,
) -> LatinAudioSampleManifest:
    """Write deterministic Latin audio provider candidate metadata."""

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = LatinAudioSampleManifest(
        provider_candidates={
            "deepl": {
                "status": "primary_translation",
                "target_language": "pt",
                "reason": DEEPL_PRIMARY_TRANSLATION_REASON,
            },
            "google-translate": {
                "status": "translation_candidate",
                "target_language": "pt",
                "reason": GOOGLE_TRANSLATE_CANDIDATE_REASON,
            },
            "google-translate-tts": {
                "status": "reserve_audio_candidate",
                "voice": "la",
                "pronunciation_policy": "google_translate_latin_tts",
                "reason": GOOGLE_TRANSLATE_TTS_REASON,
            },
            "elevenlabs-italian": {
                "status": "primary_audio_candidate",
                "voice": "it-IT",
                "pronunciation_policy": "italian_multilingual_approx",
                "reason": ELEVENLABS_ITALIAN_RESERVE_REASON,
            },
            "finevoice": {
                "status": "research_candidate",
                "voice": "manual-selection-required",
                "pronunciation_policy": "manual_evaluation_required",
                "reason": FINEVOICE_RESERVE_REASON,
            },
            "azure-multilingual-experimental": {
                "status": "blocked",
                "voice": "multilingual-experimental",
                "pronunciation_policy": "experimental_unverified",
                "fallback_reason": AZURE_LATIN_FALLBACK_REASON,
            },
        },
        representative_words=list(REPRESENTATIVE_LATIN_SAMPLE_WORDS),
        representative_sentences=list(REPRESENTATIVE_LATIN_SAMPLE_SENTENCES),
    )
    _write_manifest_file(manifest, output_dir)
    return manifest


__all__ = [
    "AZURE_LATIN_FALLBACK_REASON",
    "DEFAULT_LATIN_AUDIO_SAMPLE_DIR",
    "DEEPL_PRIMARY_TRANSLATION_REASON",
    "ELEVENLABS_ITALIAN_RESERVE_REASON",
    "FINEVOICE_RESERVE_REASON",
    "GOOGLE_TRANSLATE_CANDIDATE_REASON",
    "GOOGLE_TRANSLATE_TTS_REASON",
    "LatinAudioSampleManifest",
    "REPRESENTATIVE_LATIN_SAMPLE_SENTENCES",
    "REPRESENTATIVE_LATIN_SAMPLE_WORDS",
    "generate_latin_audio_sample_manifest",
]
