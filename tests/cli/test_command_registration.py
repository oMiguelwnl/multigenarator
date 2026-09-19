"""Characterization of the public CLI surface during command extraction."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import click
from typer.main import get_command
from typer.testing import CliRunner

import multilang.cli as cli_module


def _command_contract(command: click.Command) -> dict[str, object]:
    result = {
        "name": command.name,
        "help": command.help,
        "params": [
            {
                "name": parameter.name,
                "opts": parameter.opts,
                "secondary_opts": parameter.secondary_opts,
                "required": parameter.required,
                "default": str(parameter.default),
                "help": getattr(parameter, "help", None),
                "type": "path" if isinstance(parameter.type, click.Path) else str(parameter.type),
                "nargs": parameter.nargs,
                "multiple": parameter.multiple,
                "is_flag": getattr(parameter, "is_flag", False),
            }
            for parameter in command.params
        ],
    }
    if isinstance(command, click.Group):
        result["commands"] = {
            name: _command_contract(child)
            for name, child in command.commands.items()
            # Concurrent native/qualification work has its own CLI coverage.
            if name != "native"
        }
    return result


def test_legacy_command_names_options_defaults_and_help_are_preserved() -> None:
    expected = json.loads(
        Path(__file__).with_name("command_contract.json").read_text(encoding="utf-8")
    )
    assert _command_contract(get_command(cli_module.create_app())) == expected


def test_command_families_are_owned_by_focused_registrars() -> None:
    commands = get_command(cli_module.create_app()).commands
    expected = {
        "generate": "generation",
        "export": "generation",
        "generate-latin-mvp": "latin",
        "retrieve-korean-frequency-source": "korean_frequency",
        "validate-korean-production-evidence": "korean_evidence",
        "build-korean-release-safety": "korean_release",
        "preview-kindle-highlights": "personal_sources",
        "export-russian-phonemes": "phonetics",
    }
    for name, module in expected.items():
        assert commands[name].callback.__module__ == f"multilang.cli_commands.{module}"


def test_create_app_and_help_do_not_construct_runtime(monkeypatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("help must not construct runtime collaborators")

    for name in ("build_runtime_service", "create_engine", "KiwiKoreanMorphologyService"):
        monkeypatch.setattr(cli_module, name, forbidden)
    app = cli_module.create_app()
    result = CliRunner().invoke(app, ["generate", "--help"])
    assert result.exit_code == 0, result.output


def test_injected_export_service_and_late_legacy_patch_are_preserved(monkeypatch, tmp_path) -> None:
    class Service:
        def export_job(self, **kwargs: object) -> None:
            raise AssertionError("registry rejection must precede export")

    calls = []
    app = cli_module.create_app(service=Service())

    def blocked_registry(**kwargs: object) -> None:
        calls.append(kwargs)
        raise ValueError("synthetic registry rejection")

    monkeypatch.setattr(cli_module, "assert_anki_id_registry_clean", blocked_registry)
    result = CliRunner().invoke(
        app, ["export", "--job-id", "injected-job", "--format", "apkg", "--output-dir", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "synthetic registry rejection" in result.output
    assert calls == [{"production_roots": True}]


def test_export_uses_settings_patched_after_app_creation(monkeypatch, tmp_path) -> None:
    destinations = []

    class Service:
        def export_job(self, **kwargs):
            destinations.append(kwargs["output_dir"])
            return SimpleNamespace(output_path=tmp_path / "fixture.tsv", card_count=1)

    app = cli_module.create_app(service=Service())
    monkeypatch.setattr(cli_module, "Settings", lambda **kwargs: SimpleNamespace(export_output_dir=tmp_path))
    monkeypatch.setattr(cli_module, "_require_clean_anki_id_registry_for_export", lambda: None)

    result = CliRunner().invoke(app, ["export", "--job-id", "fixture", "--format", "tsv"])

    assert result.exit_code == 0, result.output
    assert destinations == [tmp_path]


def test_phonetics_defaults_use_legacy_settings_factory(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli_module, "Settings", lambda **kwargs: SimpleNamespace(export_output_dir=tmp_path))

    command = get_command(cli_module.create_app()).commands["export-russian-phonemes"]

    output = next(parameter for parameter in command.params if parameter.name == "output_path")
    assert output.default == tmp_path / "russian-phonemes.apkg"


def test_generated_local_smoke_index_is_usable_as_english_evidence(tmp_path) -> None:
    from multilang.domain.jobs import SupportedLanguage
    from multilang.domain.lexicon import GroundingStatus
    from multilang.services.lexical_grounding import LexicalGroundingService
    from multilang.services.lexical_lookup import LexicalLookup
    from multilang.services.word_list_parser import ParsedWordListItem

    cli_module._write_local_smoke_assets(tmp_path)
    service = LexicalGroundingService(LexicalLookup(tmp_path / "lexicon"))
    candidate = service.ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(line_number=1, submitted_form="harbor", display_form="harbor", item_key="harbor"),
    )

    assert candidate.grounding_status == GroundingStatus.GROUNDED
    assert candidate.definition_language == "en"
