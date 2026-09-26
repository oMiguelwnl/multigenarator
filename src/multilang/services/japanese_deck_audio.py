"""Validated audio and atomic artifacts for the standalone Japanese exporters."""

from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.services.audio.media_validation import inspect_local_mp3
from multilang.services.vocabulary_acquisition import _plain_path

AUDIO_FORMAT = "audio-24khz-48kbitrate-mono-mp3"


def synthesize_cached_japanese(*, text: str, synthesizer, audio_dir: Path,
                              voice_id: str, locale: str = "ja-JP") -> Path:
    if not text.strip() or len(text) > 4096:
        raise ValueError("invalid Japanese audio text")
    audio_dir = _plain_path(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    identity = json.dumps(["azure-japanese-v1", text, voice_id, locale, AUDIO_FORMAT], ensure_ascii=False)
    target = audio_dir / f"ja-{sha256(identity.encode()).hexdigest()}.mp3"
    if inspect_local_mp3(target) is not None:
        return target
    if target.is_symlink():
        raise ValueError("unsafe Japanese audio cache path")
    try:
        with TemporaryDirectory(prefix=".synthesize-", dir=audio_dir) as temporary:
            staged = Path(temporary) / target.name
            response = synthesizer.synthesize(ssml_text=text, voice_id=voice_id, locale=locale,
                output_path=staged, audio_format=AUDIO_FORMAT)
            if response.storage_path != staged or inspect_local_mp3(staged) is None:
                raise ValueError("provider returned invalid audio")
            os.replace(staged, target)
    except Exception as exc:
        # Provider errors may contain credentials or private source text.
        raise ValueError("Japanese audio synthesis failed or returned invalid audio") from exc
    return target


def write_japanese_package(*, package, output_path: Path, manifest: dict) -> None:
    output_path = _plain_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = _plain_path(output_path.with_suffix(".manifest.json"))
    with TemporaryDirectory(prefix=".japanese-export-", dir=output_path.parent) as temporary:
        staged = Path(temporary) / "deck.apkg"
        package.write_to_file(str(staged))
        manifest = {**manifest, "artifact_sha256": sha256(staged.read_bytes()).hexdigest()}
        staged_manifest = Path(temporary) / "manifest.json"
        staged_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(staged_manifest, manifest_path)
        os.replace(staged, output_path)
