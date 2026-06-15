"""ElevenLabs-first Latin MVP audio refresh helpers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Protocol, Sequence

from pydantic import BaseModel, Field

from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.elevenlabs_speech_adapter import ElevenLabsSpeechAdapter
from multilang.services.latin_audio import (
    CURRENT_LATIN_AUDIO_PROVIDER,
    LatinAudioArtifact,
    LatinAudioManifest,
    LatinAudioPair,
    latin_audio_text_hash,
    normalize_latin_audio_text,
)
from multilang.services.latin_audio_samples import (
    DEFAULT_LATIN_AUDIO_SAMPLE_DIR,
    REPRESENTATIVE_LATIN_SAMPLE_SENTENCES,
    REPRESENTATIVE_LATIN_SAMPLE_WORDS,
    generate_latin_audio_sample_manifest,
)
from multilang.services.latin_source_pack import load_latin_mvp_source_pack
from multilang.settings import Settings

LATIN_ELEVENLABS_VOICE = "it-IT"
LATIN_ELEVENLABS_LOCALE = "it-IT"
LATIN_ELEVENLABS_PRONUNCIATION_POLICY = "italian_multilingual_approx"
LATIN_ELEVENLABS_DEFAULT_VOICE_ID = "AZnzlk1XvdvUeBnXmlld"
LATIN_ELEVENLABS_FALLBACK_REASON = None


class LatinAudioSynthesizer(Protocol):
    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse: ...


class LatinAudioRefreshArtifact(BaseModel):
    """Generated Latin audio metadata plus its item key."""

    item_key: str = Field(min_length=1)
    artifact: LatinAudioArtifact


class LatinAudioRefreshSampleResult(BaseModel):
    """Result for representative Latin audio sample generation."""

    provider: str = CURRENT_LATIN_AUDIO_PROVIDER
    provider_version: str
    voice: str
    pronunciation_policy: str
    sample_manifest_path: str
    artifacts: list[LatinAudioRefreshArtifact]


def _safe_sample_name(text: str) -> str:
    safe = "".join(character.lower() if character.isalnum() else "-" for character in text.strip())
    return "-".join(part for part in safe.split("-") if part) or "sample"


def _public_storage_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.name


def _settings_voice_id(settings: Settings) -> str:
    return settings.elevenlabs_voice_id or LATIN_ELEVENLABS_DEFAULT_VOICE_ID


def _artifact_for_generated_audio(
    *,
    audio_kind: str,
    provider_version: str,
    voice: str,
    generated_text: str,
    storage_path: Path,
    repo_root: Path,
    playback_review_status: str,
) -> LatinAudioArtifact:
    normalized_text = normalize_latin_audio_text(generated_text)
    return LatinAudioArtifact.model_validate(
        {
            "audio_kind": audio_kind,
            "provider": CURRENT_LATIN_AUDIO_PROVIDER,
            "provider_version": provider_version,
            "voice": voice,
            "pronunciation_policy": LATIN_ELEVENLABS_PRONUNCIATION_POLICY,
            "generated_text": normalized_text,
            "text_hash": latin_audio_text_hash(normalized_text),
            "playback_review_status": playback_review_status,
            "storage_path": _public_storage_path(storage_path, repo_root=repo_root),
            "fallback_reason": LATIN_ELEVENLABS_FALLBACK_REASON,
        }
    )


def _synthesize_artifact(
    *,
    synthesizer: LatinAudioSynthesizer,
    settings: Settings,
    repo_root: Path,
    output_path: Path,
    audio_kind: str,
    text: str,
    playback_review_status: str,
) -> LatinAudioArtifact:
    response = synthesizer.synthesize(
        ssml_text=text,
        voice_id=_settings_voice_id(settings),
        locale=LATIN_ELEVENLABS_LOCALE,
        output_path=output_path,
        audio_format=settings.elevenlabs_output_format,
    )
    if response.byte_size <= 0 or not response.storage_path.exists():
        raise ValueError("Latin ElevenLabs synthesis returned missing or empty media")
    return _artifact_for_generated_audio(
        audio_kind=audio_kind,
        provider_version=settings.elevenlabs_model_id,
        voice=LATIN_ELEVENLABS_VOICE,
        generated_text=text,
        storage_path=response.storage_path,
        repo_root=repo_root,
        playback_review_status=playback_review_status,
    )


def generate_latin_elevenlabs_samples(
    *,
    output_dir: Path = DEFAULT_LATIN_AUDIO_SAMPLE_DIR,
    synthesizer: LatinAudioSynthesizer | None = None,
    settings: Settings | None = None,
    repo_root: Path | None = None,
) -> LatinAudioRefreshSampleResult:
    """Generate representative Latin MP3 samples and deterministic metadata."""

    runtime_settings = settings or Settings()
    runtime_repo_root = (repo_root or Path.cwd()).resolve()
    target_dir = output_dir if output_dir.is_absolute() else runtime_repo_root / output_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    sample_manifest = generate_latin_audio_sample_manifest(output_dir=target_dir)
    adapter = synthesizer or ElevenLabsSpeechAdapter(runtime_settings)
    artifacts: list[LatinAudioRefreshArtifact] = []

    for index, word in enumerate(REPRESENTATIVE_LATIN_SAMPLE_WORDS, start=1):
        output_path = target_dir / f"word-{index:02d}-{_safe_sample_name(word)}.mp3"
        artifacts.append(
            LatinAudioRefreshArtifact(
                item_key=f"sample-word-{index:02d}",
                artifact=_synthesize_artifact(
                    synthesizer=adapter,
                    settings=runtime_settings,
                    repo_root=runtime_repo_root,
                    output_path=output_path,
                    audio_kind="word",
                    text=word,
                    playback_review_status="needs_playback_review",
                ),
            )
        )

    for index, sentence in enumerate(REPRESENTATIVE_LATIN_SAMPLE_SENTENCES, start=1):
        output_path = target_dir / f"sentence-{index:02d}.mp3"
        artifacts.append(
            LatinAudioRefreshArtifact(
                item_key=f"sample-sentence-{index:02d}",
                artifact=_synthesize_artifact(
                    synthesizer=adapter,
                    settings=runtime_settings,
                    repo_root=runtime_repo_root,
                    output_path=output_path,
                    audio_kind="sentence",
                    text=sentence,
                    playback_review_status="needs_playback_review",
                ),
            )
        )

    return LatinAudioRefreshSampleResult(
        provider_version=runtime_settings.elevenlabs_model_id,
        voice=LATIN_ELEVENLABS_VOICE,
        pronunciation_policy=LATIN_ELEVENLABS_PRONUNCIATION_POLICY,
        sample_manifest_path=_public_storage_path(target_dir / "latin-audio-samples.json", repo_root=runtime_repo_root),
        artifacts=artifacts,
    )


def generate_latin_elevenlabs_full_manifest(
    *,
    output_dir: Path = Path("data") / "latin_mvp" / "audio" / "latin-mvp-50-v1",
    synthesizer: LatinAudioSynthesizer | None = None,
    settings: Settings | None = None,
    repo_root: Path | None = None,
    source_pack_loader: Callable[[], object] = load_latin_mvp_source_pack,
) -> LatinAudioManifest:
    """Generate approved-shape Latin MVP audio manifest records from the frozen source pack."""

    runtime_settings = settings or Settings()
    runtime_repo_root = (repo_root or Path.cwd()).resolve()
    target_dir = output_dir if output_dir.is_absolute() else runtime_repo_root / output_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    adapter = synthesizer or ElevenLabsSpeechAdapter(runtime_settings)
    source_pack = source_pack_loader()
    pairs: list[LatinAudioPair] = []

    for entry in source_pack.entries:
        word_path = target_dir / f"{entry.item_key}-word.mp3"
        sentence_path = target_dir / f"{entry.item_key}-sentence.mp3"
        pairs.append(
            LatinAudioPair(
                item_key=entry.item_key,
                word=_synthesize_artifact(
                    synthesizer=adapter,
                    settings=runtime_settings,
                    repo_root=runtime_repo_root,
                    output_path=word_path,
                    audio_kind="word",
                    text=entry.target_form,
                    playback_review_status="approved",
                ),
                sentence=_synthesize_artifact(
                    synthesizer=adapter,
                    settings=runtime_settings,
                    repo_root=runtime_repo_root,
                    output_path=sentence_path,
                    audio_kind="sentence",
                    text=entry.latin_sentence,
                    playback_review_status="approved",
                ),
            )
        )

    return LatinAudioManifest(source_pack_version=source_pack.source_pack_version, artifacts=pairs)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, BaseModel):
        data = payload.model_dump(mode="json")
    else:
        data = payload
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Latin MVP ElevenLabs audio refresh artifacts.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    samples = subcommands.add_parser("generate-samples")
    samples.add_argument("--output-dir", type=Path, default=DEFAULT_LATIN_AUDIO_SAMPLE_DIR)
    samples.add_argument("--review-path", type=Path, required=False)
    samples.add_argument("--provider", choices=[CURRENT_LATIN_AUDIO_PROVIDER], default=CURRENT_LATIN_AUDIO_PROVIDER)

    full_pack = subcommands.add_parser("generate-full-pack")
    full_pack.add_argument("--output-dir", type=Path, default=Path("data") / "latin_mvp" / "audio" / "latin-mvp-50-v1")
    full_pack.add_argument("--manifest", type=Path, default=Path("data") / "latin_mvp" / "latin-mvp-50-v1-audio.json")
    full_pack.add_argument("--provider", choices=[CURRENT_LATIN_AUDIO_PROVIDER], default=CURRENT_LATIN_AUDIO_PROVIDER)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    if args.command == "generate-samples":
        result = generate_latin_elevenlabs_samples(output_dir=args.output_dir)
        _write_json(args.output_dir / "latin-audio-refresh-samples.json", result)
        if args.review_path is not None:
            args.review_path.parent.mkdir(parents=True, exist_ok=True)
            args.review_path.write_text(
                "# Phase 29 Latin Audio Provider Review\n\n"
                f"selected_provider: {result.provider}\n"
                f"selected_voice: {result.voice}\n"
                f"provider_version: {result.provider_version}\n"
                f"pronunciation_policy: {result.pronunciation_policy}\n"
                "playback_review_status: needs_playback_review\n"
                "finevoice_status: research_only\n"
                "system_espeak_uninstall: not_requested\n",
                encoding="utf-8",
            )
        return

    manifest = generate_latin_elevenlabs_full_manifest(output_dir=args.output_dir)
    _write_json(args.manifest, manifest)


if __name__ == "__main__":
    main()


__all__ = [
    "LATIN_ELEVENLABS_DEFAULT_VOICE_ID",
    "LATIN_ELEVENLABS_LOCALE",
    "LATIN_ELEVENLABS_PRONUNCIATION_POLICY",
    "LATIN_ELEVENLABS_VOICE",
    "LatinAudioRefreshArtifact",
    "LatinAudioRefreshSampleResult",
    "generate_latin_elevenlabs_full_manifest",
    "generate_latin_elevenlabs_samples",
    "main",
]
