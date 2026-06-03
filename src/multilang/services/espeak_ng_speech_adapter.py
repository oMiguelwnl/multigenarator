"""Local eSpeak NG adapter for Classical Latin sample synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Protocol

from multilang.services.audio_synthesis import AudioSynthesisResponse


class EspeakNgRunner(Protocol):
    def __call__(self, command: list[str], *, input_text: str | None = None) -> object: ...


def _default_runner(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - binary/args are controlled by adapter configuration.
        command,
        input=input_text,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        text=True,
    )


def _returncode(result: object) -> int:
    return int(getattr(result, "returncode", 1))


def _stdout(result: object) -> str:
    return str(getattr(result, "stdout", "") or "")


def _stderr(result: object) -> str:
    return str(getattr(result, "stderr", "") or "")


def _sanitize_error(value: str) -> str:
    sanitized = re.sub(r"[A-Za-z_][A-Za-z0-9_]*=[^\s]+", "[redacted]", value)
    sanitized = re.sub(r"[A-Za-z]:\\[^\s]+", "[path]", sanitized)
    sanitized = re.sub(r"/(Users|home)/[^\s]+", "/[path]", sanitized)
    return sanitized.strip() or "native tool failed"


def _parse_version(output: str) -> str:
    match = re.search(r"(\d+(?:\.\d+)+)", output)
    if not match:
        raise ValueError("Unable to determine eSpeak NG version")
    return match.group(1)


def _voice_ids(output: str) -> set[str]:
    voices: set[str] = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].isalpha():
            voices.add(parts[1])
    return voices


@dataclass(frozen=True, slots=True)
class EspeakNgSpeechAdapter:
    """Small, subprocess-injectable adapter for eSpeak NG's Latin voice."""

    runner: EspeakNgRunner = _default_runner
    binary: str = "espeak-ng"
    default_voice: str = "la"
    default_speed: int = 135
    pronunciation_policy: str = "classical_approx"

    def provider_version(self) -> str:
        result = self._run([self.binary, "--version"], operation="version")
        return _parse_version(_stdout(result))

    def available_voice_ids(self) -> set[str] | None:
        result = self._run([self.binary, "--voices"], operation="voices")
        voices = _voice_ids(_stdout(result))
        return {self.default_voice} if self.default_voice in voices else set()

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        if voice_id != self.default_voice or locale != "la":
            raise ValueError("eSpeak NG Latin synthesis requires voice_id=la and locale=la")
        if audio_format.lower() != "wav":
            raise ValueError("eSpeak NG Latin synthesis supports wav output only")
        if self.default_voice not in (self.available_voice_ids() or set()):
            raise ValueError("eSpeak NG Latin voice la is not available")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self.binary,
            "-v",
            voice_id,
            "-s",
            str(self.default_speed),
            "-w",
            str(output_path),
            ssml_text,
        ]
        self._run(command, operation="synthesis")
        if not output_path.exists() or output_path.stat().st_size <= 0:
            raise ValueError("eSpeak NG synthesis produced missing or empty output")
        return AudioSynthesisResponse(
            storage_path=output_path,
            byte_size=output_path.stat().st_size,
            duration_ms=None,
            voice_id=voice_id,
            locale=locale,
        )

    def _run(self, command: list[str], *, operation: str) -> object:
        try:
            result = self.runner(command, input_text=None)
        except FileNotFoundError as exc:
            raise ValueError("eSpeak NG binary is not available") from exc
        if _returncode(result) != 0:
            detail = _sanitize_error(_stderr(result) or _stdout(result))
            raise ValueError(f"eSpeak NG {operation} failed: {detail}")
        return result


__all__ = ["EspeakNgSpeechAdapter"]
