"""Tests for the local eSpeak NG Latin speech adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from multilang.services.espeak_ng_speech_adapter import EspeakNgSpeechAdapter


@dataclass(frozen=True)
class FakeCompletedProcess:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


class FakeRunner:
    def __init__(self, *, voices: str = " 5  la             --/M      Latin", fail_synthesis: bool = False) -> None:
        self.voices = voices
        self.fail_synthesis = fail_synthesis
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str], *, input_text: str | None = None) -> FakeCompletedProcess:
        self.commands.append(command)
        if command == ["espeak-ng", "--version"]:
            return FakeCompletedProcess(stdout="eSpeak NG text-to-speech: 1.52.0\n")
        if command == ["espeak-ng", "--voices"]:
            return FakeCompletedProcess(stdout=self.voices)
        if self.fail_synthesis:
            return FakeCompletedProcess(returncode=1, stderr="native synthesis failed with PATH=/secret/bin")
        if "-w" in command:
            output_path = Path(command[command.index("-w") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"RIFFfake-wave")
            return FakeCompletedProcess(stdout="")
        return FakeCompletedProcess(returncode=99, stderr="unexpected command")


def test_detects_version_and_latin_voice_without_native_process() -> None:
    runner = FakeRunner()
    adapter = EspeakNgSpeechAdapter(runner=runner)

    assert adapter.provider_version() == "1.52.0"
    assert adapter.available_voice_ids() == {"la"}

    assert ["espeak-ng", "--version"] in runner.commands
    assert ["espeak-ng", "--voices"] in runner.commands


def test_synthesizes_latin_wav_with_expected_command(tmp_path: Path) -> None:
    runner = FakeRunner()
    adapter = EspeakNgSpeechAdapter(runner=runner)
    output_path = tmp_path / "sample.wav"

    response = adapter.synthesize(
        ssml_text="Arma virumque cano.",
        voice_id="la",
        locale="la",
        output_path=output_path,
        audio_format="wav",
    )

    synth_command = runner.commands[-1]
    assert synth_command[:2] == ["espeak-ng", "-v"]
    assert "la" in synth_command
    assert "-s" in synth_command
    assert "135" in synth_command
    assert "-w" in synth_command
    assert str(output_path) in synth_command
    assert synth_command[-1] == "Arma virumque cano."
    assert response.storage_path == output_path
    assert response.byte_size > 0
    assert response.voice_id == "la"
    assert response.locale == "la"


@pytest.mark.parametrize(
    ("runner", "match"),
    [
        (FakeRunner(voices=" 5  en             --/M      English"), "Latin voice"),
        (FakeRunner(fail_synthesis=True), "eSpeak NG synthesis failed"),
    ],
)
def test_fail_closed_errors_are_deterministic_and_sanitized(
    tmp_path: Path,
    runner: FakeRunner,
    match: str,
) -> None:
    adapter = EspeakNgSpeechAdapter(runner=runner)

    with pytest.raises(ValueError, match=match) as exc_info:
        adapter.synthesize(
            ssml_text="virum",
            voice_id="la",
            locale="la",
            output_path=tmp_path / "virum.wav",
            audio_format="wav",
        )

    message = str(exc_info.value)
    assert "PATH=" not in message
    assert "C:\\" not in message
    assert "/Users/" not in message


def test_missing_or_empty_output_fails_closed(tmp_path: Path) -> None:
    class NoOutputRunner(FakeRunner):
        def __call__(self, command: list[str], *, input_text: str | None = None) -> FakeCompletedProcess:
            self.commands.append(command)
            if command == ["espeak-ng", "--version"]:
                return FakeCompletedProcess(stdout="eSpeak NG text-to-speech: 1.52.0\n")
            if command == ["espeak-ng", "--voices"]:
                return FakeCompletedProcess(stdout=self.voices)
            return FakeCompletedProcess(stdout="")

    adapter = EspeakNgSpeechAdapter(runner=NoOutputRunner())

    with pytest.raises(ValueError, match="missing or empty"):
        adapter.synthesize(
            ssml_text="virum",
            voice_id="la",
            locale="la",
            output_path=tmp_path / "virum.wav",
            audio_format="wav",
        )
