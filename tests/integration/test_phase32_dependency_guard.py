"""Dependency guards for Phase 32 Korean frequency source work."""

from __future__ import annotations

from pathlib import Path


def test_txt_official_source_contract_avoids_spreadsheet_parsers_and_wordfreq_final_authority() -> None:
    service_path = Path("src/multilang/services/korean_frequency.py")
    assert service_path.exists(), "Korean frequency service module must exist"
    source = service_path.read_text(encoding="utf-8")

    assert "한국어 학습용 어휘 목록.txt" in source
    assert "iter_wordlist" not in source
    assert "wordfreq" not in source
    assert ".xls" not in source.lower()
    assert ".hwp" not in source.lower()


def test_dependency_guard_keeps_official_source_commands_out_of_runtime_construction() -> None:
    cli_source = Path("src/multilang/cli.py").read_text(encoding="utf-8")

    for command_name in (
        "retrieve-korean-frequency-source",
        "validate-korean-source-retrieval-result",
    ):
        index = cli_source.index(command_name)
        command_block = cli_source[index : cli_source.index("@cli.command", index + 1)]
        assert "build_runtime_service" not in command_block
        assert "LexicalGroundingService" not in command_block
        assert "KiwiKoreanMorphologyService" not in command_block
        assert "Tatoeba" not in command_block
