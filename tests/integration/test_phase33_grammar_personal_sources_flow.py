"""Offline Phase 33 grammar/personal-source integration contract."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from multilang.cli import create_app

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow, export_field_names_for_language_and_source
from multilang.domain.jobs import SupportedLanguage


runner = CliRunner()


def test_phase33_mixed_source_item_isolation_guid_image_private_disclosure_resume_production_refusal() -> None:
    app = create_app()
    status = runner.invoke(
        app,
        [
            "phase33",
            "status",
            "--job-id",
            "job-33",
            "--format",
            "json",
            "--require-exact-authority",
            "--no-private-values",
        ],
    )
    assert status.exit_code == 0, status.output
    status_payload = json.loads(status.output)
    assert status_payload["status"] == "blocked_without_authority"

    process = runner.invoke(
        app,
        ["phase33", "process", "--job-id", "job-33", "--source", "highlight", "--mode", "resume", "--max-items", "1"],
    )
    assert process.exit_code == 0, process.output
    process_payload = json.loads(process.output)
    assert process_payload["source"] == "highlight"
    assert process_payload["mode"] == "resume"
    assert process_payload["no_server"] is True
    assert process_payload["no_fallback"] is True

    field_names = export_field_names_for_language_and_source(language=SupportedLanguage.KO, source_type="korean-grammar")
    row = ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type="korean-grammar",
            job_id="job-33",
            item_key="grammar-g001",
            lemma_key="ko-grammar:g001",
            sort_index=1,
        ),
        word="은/는",
        front_of_card="은/는",
        ipa="[eun/neun]",
        definitions="particle: topic marker",
        example_sentence="저는 학생이에요.",
        translation="Eu sou estudante.",
        word_audio="[sound:g001-word.mp3]",
        sentence_audio="[sound:g001-sentence.mp3]",
    )
    changed_text_row = row.model_copy(update={"example_sentence": "저는 선생님이에요."})

    assert row.ordered_field_mapping(field_names=field_names)["Image"] == ""
    assert row.note_guid == changed_text_row.note_guid
    assert "private" not in json.dumps(status_payload).lower()
    assert "excerpt" not in json.dumps(status_payload).lower()
