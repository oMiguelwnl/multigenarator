"""CLI tests for the isolated Classical Latin MVP command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.latin import LatinGenerationRequest
from multilang.services.latin_review import load_latin_curated_records, update_latin_review_gate, write_latin_curated_records
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
    assert "grammar_gate_status=approved" in result.output
    assert "grammar_evidence_count=50" in result.output
    assert "gramatica_count=50" in result.output
    assert "grammar_gate_status=approved" in result.output
    assert "grammar_evidence_count=50" in result.output
    assert "gramatica_count=50" in result.output


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
    assert '"grammar_gate_status": "approved"' in result.output
    assert '"grammar_evidence_count": 50' in result.output
    assert '"gramatica_count": 50' in result.output
    assert "C:\\" not in result.output
    assert "/Users/" not in result.output


def test_generate_latin_mvp_portuguese_json_prints_translation_summary() -> None:
    result = runner.invoke(create_app(), ["generate-latin-mvp", "--portuguese-json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["source_pack_version"] == "latin-mvp-50-v1"
    assert payload["portuguese_translation_summary"]["translation_pack_version"] == "latin-mvp-50-pt-v1"
    assert payload["portuguese_translation_summary"]["entry_count"] == 50
    assert payload["portuguese_translation_summary"]["passed_count"] == 50
    assert payload["portuguese_translation_summary"]["failed_count"] == 0
    assert payload["portuguese_translation_summary"]["issue_counts"] == {}
    assert "C:\\" not in result.output
    assert "/Users/" not in result.output


def test_generate_latin_mvp_audio_json_prints_public_audio_summary() -> None:
    result = runner.invoke(create_app(), ["generate-latin-mvp", "--audio-json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["source_pack_version"] == "latin-mvp-50-v1"
    audio_summary = payload["audio_summary"]
    assert audio_summary["manifest_version"] == "latin-mvp-50-v1"
    assert audio_summary["entry_count"] == 50
    assert audio_summary["word_count"] == 50
    assert audio_summary["sentence_count"] == 50
    assert audio_summary["approved_count"] == 50
    assert audio_summary["blocked_count"] == 0
    assert audio_summary["provider_counts"] == {"espeak-ng": 100}
    assert audio_summary["playback_status_counts"] == {"approved": 100}
    assert audio_summary["readiness_status"] == "approved"
    assert "storage_path" not in result.output
    assert "provider_response" not in result.output
    assert "secret" not in result.output.lower()
    assert "C:\\" not in result.output
    assert "/Users/" not in result.output


def test_generate_latin_mvp_audio_json_and_portuguese_json_can_coexist() -> None:
    result = runner.invoke(create_app(), ["generate-latin-mvp", "--audio-json", "--portuguese-json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["audio_summary"]["readiness_status"] == "approved"
    assert payload["portuguese_translation_summary"]["translation_pack_version"] == "latin-mvp-50-pt-v1"


def test_generate_latin_mvp_calls_latin_service_with_latin_request() -> None:
    captured: list[LatinGenerationRequest] = []

    class FakeLatinService(LatinMvpGenerationService):
        def start(self, request: LatinGenerationRequest, **kwargs):  # type: ignore[override]
            captured.append(request)
            return super().start(request, **kwargs)

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


def test_update_latin_review_gate_changes_only_selected_gate() -> None:
    records = load_latin_curated_records()
    updated = update_latin_review_gate(
        records,
        item_key="latin-mvp-0001",
        gate="grammar",
        status="approved",
        reason="resolved_by_phase_24",
        force=True,
    )

    original = records[0]
    changed = updated[0]
    assert changed.grammar_gate.status == "approved"
    assert changed.grammar_gate.reason == "resolved_by_phase_24"
    assert changed.source_gate == original.source_gate
    assert changed.translation_gate == original.translation_gate
    assert changed.audio_gate == original.audio_gate
    assert records[0].grammar_gate.reason is None


def test_update_latin_review_gate_protects_approved_gate_without_force() -> None:
    records = load_latin_curated_records()

    with pytest.raises(ValueError, match="approved gate overwrite requires force"):
        update_latin_review_gate(
            records,
            item_key="latin-mvp-0001",
            gate="source",
            status="rejected",
            reason="changed mind",
        )

    assert records[0].source_gate.status == "approved"


def test_update_latin_review_gate_protects_approved_metadata_without_force() -> None:
    records = load_latin_curated_records()
    current_reason = records[0].source_gate.reason
    approved_with_metadata = update_latin_review_gate(
        records,
        item_key="latin-mvp-0001",
        gate="source",
        status="approved",
        reason=current_reason,
        reviewed_by="first-reviewer@example.test",
        reviewed_at="2026-06-03T17:55:00Z",
        force=True,
    )

    with pytest.raises(ValueError, match="approved gate overwrite requires force"):
        update_latin_review_gate(
            approved_with_metadata,
            item_key="latin-mvp-0001",
            gate="source",
            status="approved",
            reason=current_reason,
            reviewed_by="second-reviewer@example.test",
            reviewed_at="2026-06-03T17:55:00Z",
        )

    assert approved_with_metadata[0].source_gate.reviewed_by == "first-reviewer@example.test"


def test_update_latin_review_gate_requires_reason_for_blocking_statuses() -> None:
    records = load_latin_curated_records()

    with pytest.raises(ValueError, match="reason"):
        update_latin_review_gate(records, item_key="latin-mvp-0001", gate="translation", status="rejected")

    updated = update_latin_review_gate(
        records,
        item_key="latin-mvp-0001",
        gate="translation",
        status="approved",
        reviewed_by="reviewer@example.test",
        reviewed_at="2026-06-02T17:30:00Z",
    )
    assert updated[0].translation_gate.status == "approved"
    assert updated[0].translation_gate.reviewed_by == "reviewer@example.test"


def test_write_latin_curated_records_round_trips_json(tmp_path: Path) -> None:
    output_path = tmp_path / "curation.json"
    records = load_latin_curated_records()

    write_latin_curated_records(records, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload[0]["item_key"] == "latin-mvp-0001"
    assert payload[-1]["item_key"] == "latin-mvp-0050"


def test_review_latin_mvp_summary_prints_gate_counts() -> None:
    result = runner.invoke(create_app(), ["review-latin-mvp", "--summary"])

    assert result.exit_code == 0
    assert "total_records=50" in result.output
    assert "learner_ready_records=0" in result.output
    assert '"translation": {"approved": 0, "needs_review": 50, "rejected": 0}' in result.output
    assert '"audio": {"approved": 0, "needs_review": 50, "rejected": 0}' in result.output


def test_review_latin_mvp_update_writes_file(tmp_path: Path) -> None:
    curation_file = tmp_path / "curation.json"
    write_latin_curated_records(load_latin_curated_records(), curation_file)

    result = runner.invoke(
        create_app(),
        [
            "review-latin-mvp",
            "--curation-file",
            str(curation_file),
            "--item-key",
            "latin-mvp-0001",
            "--gate",
            "grammar",
            "--status",
            "approved",
            "--reason",
            "resolved_by_phase_24",
            "--force",
        ],
    )

    assert result.exit_code == 0
    assert "updated_item_key=latin-mvp-0001" in result.output
    assert "updated_gate=grammar" in result.output
    assert "updated_status=approved" in result.output
    updated = load_latin_curated_records(curation_file)
    assert updated[0].grammar_gate.reason == "resolved_by_phase_24"


def test_review_latin_mvp_update_protects_approved_gate_without_force(tmp_path: Path) -> None:
    curation_file = tmp_path / "curation.json"
    write_latin_curated_records(load_latin_curated_records(), curation_file)

    result = runner.invoke(
        create_app(),
        [
            "review-latin-mvp",
            "--curation-file",
            str(curation_file),
            "--item-key",
            "latin-mvp-0001",
            "--gate",
            "source",
            "--status",
            "rejected",
            "--reason",
            "not acceptable",
        ],
    )

    assert result.exit_code != 0
    assert "approved gate overwrite requires force" in result.output
