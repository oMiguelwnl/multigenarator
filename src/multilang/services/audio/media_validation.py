"""Bounded, local-only MP3 validation using actual streaming PCM decoding."""

from __future__ import annotations

import math
import os
import stat
from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import miniaudio

# A vocabulary word or learner sentence should be far below these limits.
MAX_AUDIO_BYTES = 16 * 1024 * 1024
MAX_AUDIO_DURATION_SECONDS = 300
_DECODE_CHUNK_FRAMES = 4096


@dataclass(frozen=True, slots=True)
class AudioMediaInfo:
    byte_size: int
    duration_ms: int
    num_frames: int
    artifact_sha256: str


def inspect_local_mp3(
    storage_path: str | Path,
    *,
    expected_byte_size: int | None = None,
    artifact_hash_prefix: bytes = b"",
) -> AudioMediaInfo | None:
    """Return measured metadata only for a bounded, fully decodable local MP3.

    Open regular files without following a final symlink or blocking on FIFOs.
    The decoder receives a size-limited byte snapshot, never a path or URL, and
    yields fixed-size PCM chunks instead of allocating the full decoded audio.
    """

    path = str(storage_path)
    if "://" in path or "\x00" in path:
        return None
    try:
        if Path(path).is_symlink():
            return None
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as source:
            file_info = os.fstat(source.fileno())
            if not stat.S_ISREG(file_info.st_mode) or not 0 < file_info.st_size <= MAX_AUDIO_BYTES:
                return None
            if expected_byte_size is not None and expected_byte_size != file_info.st_size:
                return None
            data = source.read(MAX_AUDIO_BYTES + 1)
            if len(data) != file_info.st_size or len(data) > MAX_AUDIO_BYTES:
                return None

        info = miniaudio.mp3_get_info(data)
        if (
            not math.isfinite(info.duration)
            or not 0 < info.duration <= MAX_AUDIO_DURATION_SECONDS
            or info.num_frames <= 0
            or info.nchannels not in (1, 2)
            or not 0 < info.sample_rate <= 192000
        ):
            return None
        max_frames = int(MAX_AUDIO_DURATION_SECONDS * info.sample_rate)
        decoded_frames = 0
        with closing(miniaudio.stream_memory(
            data, output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=info.nchannels, sample_rate=info.sample_rate,
            frames_to_read=_DECODE_CHUNK_FRAMES,
        )) as stream:
            for samples in stream:
                if not samples or len(samples) % info.nchannels:
                    return None
                decoded_frames += len(samples) // info.nchannels
                if decoded_frames > max_frames:
                    return None
        if decoded_frames <= 0 or decoded_frames != info.num_frames:
            return None
        duration_ms = round(decoded_frames * 1000 / info.sample_rate)
        if duration_ms <= 0:
            return None
        return AudioMediaInfo(
            byte_size=len(data), duration_ms=duration_ms, num_frames=decoded_frames,
            artifact_sha256=sha256(artifact_hash_prefix + data).hexdigest(),
        )
    except (OSError, ValueError, OverflowError, miniaudio.DecodeError):
        return None


__all__ = ["AudioMediaInfo", "inspect_local_mp3"]
