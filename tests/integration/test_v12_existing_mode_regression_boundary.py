"""v1.2 regression boundary for existing generation modes and privacy gates."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
)
from multilang.services.export_anki_package import HIGHLIGHT_NOTE_TYPE_NAME, MANUAL_NOTE_TYPE_NAME, NOTE_TYPE_NAME


runner = CliRunner()


def _load_integration_module(name: str) -> ModuleType:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_frequency_e2e = _load_integration_module("test_frequency_e2e_export_flow")
_custom_e2e = _load_integration_module("test_custom_word_list_e2e_export_flow")


def test_frequency_existing_mode_still_generates_audio_exports_and_uses_default_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _frequency_e2e.test_frequency_sample_generates_audio_and_exports_all_formats(tmp_path, monkeypatch)
    _frequency_e2e.test_frequency_production_contract_remains_three_levels_of_one_thousand()

    assert NOTE_TYPE_NAME == "Multilang::Card"
    assert "Translation" in FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert "Word" not in FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert HIGHLIGHT_NOTE_TYPE_NAME != NOTE_TYPE_NAME


def test_custom_word_list_existing_mode_still_generates_audio_exports_without_highlight_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _custom_e2e.test_custom_word_list_generates_audio_and_exports_all_formats(tmp_path, monkeypatch)

    assert MANUAL_NOTE_TYPE_NAME == "Multilang::Manual Card"
    assert "Translation" in MANUAL_EXPORT_CARD_FIELD_NAMES
    assert MANUAL_EXPORT_CARD_FIELD_NAMES != HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert HIGHLIGHT_NOTE_TYPE_NAME != MANUAL_NOTE_TYPE_NAME


def test_cli_rejects_kindle_highlights_until_user_facing_mode_is_wired() -> None:
    app = create_app(generate_executor=lambda request: None)

    result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "kindle-highlights"],
    )

    assert result.exit_code != 0
    assert "--source must be one of: frequency, word-list" in result.output
