"""v1.2 regression boundary for existing generation modes and privacy gates."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
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
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_test_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_frequency_e2e = _load_integration_module("test_frequency_e2e_export_flow")
_custom_e2e = _load_integration_module("test_custom_word_list_e2e_export_flow")
_highlight_flow = _load_integration_module("test_highlight_generation_audio_flow")


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


def test_custom_word_list_existing_mode_generates_audio_exports_with_highlight_template_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _custom_e2e.test_custom_word_list_generates_audio_and_exports_all_formats(tmp_path, monkeypatch)

    assert MANUAL_NOTE_TYPE_NAME == "Multilang::Manual Card"
    assert "Translation" not in MANUAL_EXPORT_CARD_FIELD_NAMES
    assert MANUAL_EXPORT_CARD_FIELD_NAMES == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert HIGHLIGHT_NOTE_TYPE_NAME != MANUAL_NOTE_TYPE_NAME


def test_cli_accepts_public_highlights_but_rejects_internal_kindle_highlights() -> None:
    app = create_app(generate_executor=lambda request: None)

    internal_result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "kindle-highlights"],
    )
    public_result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "highlights", "--input-file", "local-export.txt"],
    )

    assert internal_result.exit_code != 0
    assert "--source must be one of: frequency, word-list, highlights" in internal_result.output
    assert public_result.exit_code == 0


def test_highlight_generation_audio_qa_evidence_is_source_aware_and_private_safe(tmp_path: Path) -> None:
    _highlight_flow.test_highlight_generation_audio_and_card_flow()

    text_review_tests = _load_test_module(Path(__file__).parents[1] / "services" / "test_text_review.py", "test_text_review_helpers")

    private_sentence = "Book: Secret Novel\nReaders wash every cup. Location: 123 https://reader.example/dav/private"
    service, _ = text_review_tests.build_service(
        text_review_tests.make_record(item_key="highlight:abc:wash", example_sentence=private_sentence, translation_text="user=private-token"),
        source_metadata={"highlight:abc:wash": {"source_type": "kindle-highlights"}},
    )

    report = service.build_review_report(job_id="job-123", output_path=tmp_path / "highlight-review.json")
    payload = report.report_path.read_text(encoding="utf-8")

    assert report.items[0].source_type == "kindle-highlights"
    assert report.items[0].translation_required is False
    assert "Secret Novel" not in payload
    assert "Location: 123" not in payload
    assert "dav/private" not in payload
    assert "private-token" not in payload
