"""Scanner-readable Phase 27 Latin audio policy and integrity evidence."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.latin import LatinGenerationRequest
from multilang.services.latin_audio import (
    assert_latin_audio_manifest_export_ready,
    latin_audio_text_hash,
    load_latin_audio_manifest,
    summarize_latin_audio_manifest,
)
from multilang.services.latin_mvp import LatinMvpGenerationService
from multilang.services.latin_review import load_latin_curated_records
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


PHASE_27_REQUIREMENTS = ("AUD-01", "AUD-02", "AUD-03", "AUD-04")
PHASE_27_REQUIREMENT_EVIDENCE = {
    "AUD-01": "test_phase_27_evidence_loads_real_assets_and_approved_playback_policy",
    "AUD-02": "test_every_latin_mvp_card_has_approved_or_explicitly_rejected_audio",
    "AUD-03": "test_audio_manifest_artifacts_have_required_public_metadata",
    "AUD-04": "test_public_summary_and_integrity_gate_are_scanner_readable_and_path_safe",
}

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYBACK_REVIEW_PATH = REPO_ROOT / ".planning/phases/27-latin-audio-policy-and-integrity/27-AUDIO-PLAYBACK-REVIEW.md"
LATIN_AUDIO_MANIFEST_PATH = REPO_ROOT / "data/latin_mvp/latin-mvp-50-v1-audio.json"


def _playback_review_field(name: str) -> str:
    for line in PLAYBACK_REVIEW_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"missing playback review field: {name}")


def _assert_no_private_or_provider_detail_leaks(payload: object) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert "C:\\" not in rendered
    assert "/Users/" not in rendered
    assert "storage_path" not in rendered
    assert "provider_response" not in rendered
    assert "raw_response" not in rendered
    assert "secret" not in rendered.lower()


def test_phase_27_requirements_are_scanner_readable() -> None:
    assert PHASE_27_REQUIREMENTS == ("AUD-01", "AUD-02", "AUD-03", "AUD-04")
    assert set(PHASE_27_REQUIREMENT_EVIDENCE) == set(PHASE_27_REQUIREMENTS)


def test_phase_27_evidence_loads_real_assets_and_approved_playback_policy() -> None:
    source_pack = load_latin_mvp_source_pack()
    curation_records = load_latin_curated_records()
    audio_manifest = load_latin_audio_manifest()

    assert PLAYBACK_REVIEW_PATH.exists()
    assert LATIN_AUDIO_MANIFEST_PATH.exists()
    assert _playback_review_field("playback_review_status") == "approved"
    assert _playback_review_field("selected_provider") == "google-translate-tts"
    assert _playback_review_field("selected_voice") == "la"
    assert _playback_review_field("pronunciation_policy") == "google_translate_latin"
    assert source_pack.source_pack_version == audio_manifest.source_pack_version == "latin-mvp-50-v1"
    assert len(source_pack.entries) == len(curation_records) == len(audio_manifest.artifacts) == 50


def test_every_latin_mvp_card_has_approved_or_explicitly_rejected_audio() -> None:
    source_pack = load_latin_mvp_source_pack()
    manifest = load_latin_audio_manifest()
    curation_by_key = {record.item_key: record for record in load_latin_curated_records()}

    assert [entry.item_key for entry in source_pack.entries] == [pair.item_key for pair in manifest.artifacts]
    for entry, pair in zip(source_pack.entries, manifest.artifacts, strict=True):
        record = curation_by_key[pair.item_key]
        assert record.audio_gate.status == "approved"
        assert pair.word is not None
        assert pair.sentence is not None
        for artifact, expected_text in ((pair.word, entry.target_form), (pair.sentence, entry.latin_sentence)):
            if artifact.playback_review_status == "approved":
                assert artifact.provider == "google-translate-tts"
                assert artifact.voice == "la"
                assert artifact.pronunciation_policy == "google_translate_latin"
                assert artifact.generated_text == expected_text
                continue
            assert artifact.playback_review_status in {"blocked", "rejected"}
            assert record.audio_gate.status == "rejected"
            assert artifact.fallback_reason

    summary = summarize_latin_audio_manifest(manifest)
    assert summary.approved_items == 50
    assert summary.blocked_items == 0
    assert_latin_audio_manifest_export_ready(manifest)


def test_audio_manifest_artifacts_have_required_public_metadata() -> None:
    source_pack = load_latin_mvp_source_pack()
    manifest = load_latin_audio_manifest()

    for entry, pair in zip(source_pack.entries, manifest.artifacts, strict=True):
        for artifact, expected_kind, expected_text in (
            (pair.word, "word", entry.target_form),
            (pair.sentence, "sentence", entry.latin_sentence),
        ):
            assert artifact is not None
            assert artifact.audio_kind == expected_kind
            assert artifact.provider
            assert artifact.provider_version
            assert artifact.voice
            assert artifact.pronunciation_policy
            assert artifact.generated_text == expected_text
            assert artifact.text_hash == latin_audio_text_hash(expected_text)
            assert artifact.playback_review_status == "approved"
            assert artifact.storage_path.startswith("data/latin_mvp/audio/latin-mvp-50-v1/")
            assert not Path(artifact.storage_path).is_absolute()
            assert "\\" not in artifact.storage_path
            assert ":" not in artifact.storage_path


def test_public_summary_and_integrity_gate_are_scanner_readable_and_path_safe() -> None:
    service_summary = LatinMvpGenerationService().start(
        LatinGenerationRequest(),
        include_audio_summary=True,
    ).manifest_summary()
    cli_result = CliRunner().invoke(create_app(), ["generate-latin-mvp", "--audio-json"])

    assert cli_result.exit_code == 0
    cli_summary = json.loads(cli_result.output)
    for payload in (service_summary, cli_summary):
        _assert_no_private_or_provider_detail_leaks(payload)
        audio_summary = payload["audio_summary"]
        assert audio_summary["entry_count"] == 50
        assert audio_summary["word_count"] == 50
        assert audio_summary["sentence_count"] == 50
        assert audio_summary["approved_count"] == 50
        assert audio_summary["blocked_count"] == 0
        assert audio_summary["provider_counts"] == {"google-translate-tts": 100}
        assert audio_summary["playback_status_counts"] == {"approved": 100}
        assert audio_summary["readiness_status"] == "approved"


def test_phase_27_boundary_keeps_latin_outside_modern_frequency_generation() -> None:
    assert "la" not in {language.value for language in SupportedLanguage}
    generate_result = CliRunner().invoke(create_app(), ["generate", "--language", "la", "--source", "frequency"])
    assert generate_result.exit_code != 0

    records = load_latin_curated_records()
    assert {record.translation_gate.status for record in records} == {"approved"}
    assert {record.audio_gate.status for record in records} == {"approved"}
