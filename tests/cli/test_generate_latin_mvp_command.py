"""CLI tests for the isolated Classical Latin MVP command."""

from __future__ import annotations

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.latin import LatinGenerationRequest
from multilang.services.latin_mvp import LatinMvpGenerationService

runner = CliRunner()


def test_generate_latin_mvp_prints_required_metadata() -> None:
    result = runner.invoke(create_app(), ["generate-latin-mvp"])

    assert result.exit_code == 0
    assert "language_code=la" in result.output
    assert "variant=classical" in result.output
    assert "source_type=latin-mvp" in result.output
    assert "source_pack_version=latin-mvp-50-v1" in result.output
    assert "card_count=50" in result.output
    assert "item_count=50" in result.output
    assert "first_item_key=latin-mvp-0001" in result.output
    assert "last_item_key=latin-mvp-0050" in result.output
    assert "license_gate_status=approved" in result.output
    assert "source_type_counts=" in result.output


def test_generate_latin_mvp_rejects_source_pack_version_override_mismatch() -> None:
    result = runner.invoke(
        create_app(),
        ["generate-latin-mvp", "--source-pack-version", "custom-pack"],
    )

    assert result.exit_code == 1
    assert "source_pack_version" in result.output


def test_generate_latin_mvp_manifest_json_prints_public_summary() -> None:
    result = runner.invoke(create_app(), ["generate-latin-mvp", "--manifest-json"])

    assert result.exit_code == 0
    assert '"source_pack_version": "latin-mvp-50-v1"' in result.output
    assert '"first_item_key": "latin-mvp-0001"' in result.output
    assert '"last_item_key": "latin-mvp-0050"' in result.output
    assert "C:\\" not in result.output
    assert "/Users/" not in result.output


def test_generate_latin_mvp_calls_latin_service_with_latin_request() -> None:
    captured: list[LatinGenerationRequest] = []

    class FakeLatinService(LatinMvpGenerationService):
        def start(self, request: LatinGenerationRequest):  # type: ignore[override]
            captured.append(request)
            return super().start(request)

    result = runner.invoke(create_app(latin_mvp_service=FakeLatinService()), ["generate-latin-mvp"])

    assert result.exit_code == 0
    assert isinstance(captured[0], LatinGenerationRequest)
    assert captured[0].source_type == "latin-mvp"


def test_existing_generate_command_rejects_latin_language_frequency_path() -> None:
    result = runner.invoke(
        create_app(),
        ["generate", "--language", "la", "--source", "frequency"],
    )

    assert result.exit_code != 0
    assert "Invalid value for '--language'" in result.output


def test_existing_generate_command_rejects_latin_mvp_source_option() -> None:
    result = runner.invoke(
        create_app(),
        ["generate", "--language", "en", "--source", "latin-mvp"],
    )

    assert result.exit_code != 0
    assert "--source must be one of: frequency, word-list, highlights" in result.output
