"""CLI tests for audit-deck command."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import export_anki_package


runner = CliRunner()


def write_media_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"ID3-audio")
    return path


def make_apkg(tmp_path: Path, *, definitions: str) -> Path:
    row = ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.EN,
            source_type="frequency",
            job_id="job-audit-cli",
            item_key="run",
            lemma_key="en:run",
            sort_index=1,
        ),
        word="run",
        front_of_card="run",
        ipa="/run/",
        definitions=definitions,
        example_sentence="I run today.",
        translation="Eu corro hoje.",
        word_audio="[sound:word.mp3]",
        sentence_audio="[sound:sentence.mp3]",
    )
    output_path = tmp_path / "deck.apkg"
    export_anki_package(
        rows=[row],
        media_index={
            row.word_audio: write_media_file(tmp_path / "audio" / "word.mp3"),
            row.sentence_audio: write_media_file(tmp_path / "audio" / "sentence.mp3"),
        },
        output_path=output_path,
        deck_name="Audit CLI Deck",
    )
    return output_path


def test_audit_deck_command_writes_reports_and_prints_metadata(tmp_path: Path) -> None:
    apkg_path = make_apkg(tmp_path, definitions="noun: genitive/dative/prepositional singular")
    output_dir = tmp_path / "reports"

    result = runner.invoke(
        create_app(),
        ["audit-deck", "--input-apkg", str(apkg_path), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 1
    assert "json_report=" in result.output
    assert "markdown_report=" in result.output
    assert "card_count=1" in result.output
    assert "issue_count=5" in result.output
    assert "input_sha256=" in result.output
    assert (output_dir / "deck-audit.json").exists()
    assert (output_dir / "deck-audit.md").exists()


def test_audit_deck_missing_path_exits_nonzero_without_reports(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    result = runner.invoke(
        create_app(),
        ["audit-deck", "--input-apkg", str(tmp_path / "missing.apkg"), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 1
    assert "APKG file does not exist" in result.output
    assert not output_dir.exists()


def test_audit_deck_rerun_reproducibility_and_non_mutation(tmp_path: Path) -> None:
    apkg_path = make_apkg(tmp_path, definitions="noun: inflection of заболева́ние (zabolevánije)")
    output_dir = tmp_path / "reports"
    before_hash = sha256(apkg_path.read_bytes()).hexdigest()

    first = runner.invoke(
        create_app(),
        ["audit-deck", "--input-apkg", str(apkg_path), "--output-dir", str(output_dir)],
    )
    first_json = (output_dir / "deck-audit.json").read_bytes()
    second = runner.invoke(
        create_app(),
        ["audit-deck", "--input-apkg", str(apkg_path), "--output-dir", str(output_dir)],
    )

    assert first.exit_code == 1
    assert second.exit_code == 1
    assert (output_dir / "deck-audit.json").read_bytes() == first_json
    assert sha256(apkg_path.read_bytes()).hexdigest() == before_hash
    markdown = (output_dir / "deck-audit.md").read_text(encoding="utf-8")
    assert "## Card" in markdown
    assert "### Field: Definitions" in markdown
