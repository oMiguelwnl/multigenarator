"""The preview entry point follows the same output root as deck exports."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("explicit", [False, True])
def test_mandarin_preview_writes_only_to_selected_output_root(tmp_path, explicit) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts/preview_mandarin_card.py"
    environment = {
        **os.environ,
        "MULTILANG_FORBID_NETWORK": "1",
        "MULTILANG_FORBID_PROVIDERS": "1",
        "MULTILANG_OUTPUT_DIR": str(tmp_path / "generated"),
    }
    command = [sys.executable, str(script)]
    destination = tmp_path / "generated/previews/mandarin"
    if explicit:
        destination = tmp_path / "custom-preview"
        command.append(str(destination))

    result = subprocess.run(
        command, cwd=tmp_path, env=environment, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, result.stderr
    front = destination / "front.html"
    back = destination / "back.html"
    assert front.is_file() and back.is_file(), result.stdout
    assert '<ruby class="mandarin-ruby' in front.read_text(encoding="utf-8")
    assert 'href="back.html"' in front.read_text(encoding="utf-8")
    assert 'href="front.html"' in back.read_text(encoding="utf-8")
    assert not (tmp_path / ".multilang").exists()
