"""Bounded decode checks for untrusted provider media and local cached files."""

import os
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest
from support.audio import SILENT_MP3


def test_audio_decode_returns_measured_metadata(tmp_path: Path) -> None:
    from multilang.services.audio.media_validation import inspect_local_mp3

    path = tmp_path / "speech.mp3"
    path.write_bytes(SILENT_MP3)
    media = inspect_local_mp3(path, expected_byte_size=len(SILENT_MP3))
    assert media is not None
    assert media.duration_ms == 313
    assert media.num_frames == 13824


def test_audio_decode_preserves_korean_artifact_hash_namespace(tmp_path: Path) -> None:
    from multilang.services.audio.media_validation import inspect_local_mp3

    path = tmp_path / "speech.mp3"
    path.write_bytes(SILENT_MP3)
    media = inspect_local_mp3(path, artifact_hash_prefix=b"artifact:")

    assert media is not None
    assert media.artifact_sha256 == sha256(b"artifact:" + SILENT_MP3).hexdigest()


@pytest.mark.parametrize("kind", ["missing", "directory", "symlink", "fifo", "url"])
def test_audio_decode_accepts_only_regular_local_files(tmp_path: Path, kind: str) -> None:
    from multilang.services.audio.media_validation import inspect_local_mp3

    path: Path | str = tmp_path / "speech.mp3"
    if kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        source = tmp_path / "target.mp3"
        source.write_bytes(SILENT_MP3)
        path.symlink_to(source)
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "url":
        path = "https://example.invalid/speech.mp3"

    assert inspect_local_mp3(path) is None


@pytest.mark.parametrize("limit", ["MAX_AUDIO_BYTES", "MAX_AUDIO_DURATION_SECONDS"])
def test_audio_decode_enforces_resource_bounds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str) -> None:
    from multilang.services.audio import media_validation

    path = tmp_path / "speech.mp3"
    path.write_bytes(SILENT_MP3)
    monkeypatch.setattr(media_validation, limit, 1 if limit == "MAX_AUDIO_BYTES" else 0.1)

    assert media_validation.inspect_local_mp3(path) is None


@pytest.mark.parametrize("duration", [0, float("nan"), float("inf")])
def test_audio_decode_rejects_invalid_duration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, duration: float) -> None:
    from multilang.services.audio import media_validation

    path = tmp_path / "speech.mp3"
    path.write_bytes(SILENT_MP3)
    monkeypatch.setattr(media_validation.miniaudio, "mp3_get_info", lambda _: SimpleNamespace(
        duration=duration, num_frames=13824, nchannels=1, sample_rate=44100,
    ))

    assert media_validation.inspect_local_mp3(path) is None
