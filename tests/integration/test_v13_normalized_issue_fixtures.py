"""Executable VAL-02 fixtures for the normalized v1.3 issue catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow, FREQUENCY_EXPORT_CARD_FIELD_NAMES
from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import CardTemplate
from multilang.services.v13_validation import validate_v13_card, validate_v13_template_contract

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "v13" / "card_issues_normalized_cases.json"

REQUIRED_COVERAGE_GROUPS = {
    "ipa_correction",
    "grammar_definition_correction",
    "wrong_sense_definition_correction",
    "definition_analysis_validation",
    "translation_correction",
    "front_of_card_removal",
    "sentence_audio_layout",
    "word_audio_correction",
}


def _fixture_catalog() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_identity(case_id: str, word: str) -> ExportCardIdentity:
    return ExportCardIdentity(
        language=SupportedLanguage.RU,
        source_type="frequency",
        job_id="job-v13-normalized-fixtures",
        item_key=case_id,
        lemma_key=word,
        sort_index=1,
    )


def _make_row(case: dict[str, Any]) -> ExportCardRow:
    payload = case["input"]
    word = payload["word"]
    return ExportCardRow(
        identity=_make_identity(case["id"], word),
        word=word,
        front_of_card=word,
        ipa=payload.get("ipa"),
        definitions=payload["definitions"],
        example_sentence=payload["example_sentence"],
        translation=payload.get("translation", ""),
        word_audio=payload.get("word_audio", "[sound:word.mp3]"),
        sentence_audio=payload.get("sentence_audio", "[sound:sentence.mp3]"),
        image="",
    )


def _make_audio_record(case: dict[str, Any]) -> AudioAssetRecord | None:
    asset_payload = case["input"].get("word_audio_asset")
    if asset_payload is None:
        return None
    display_text = asset_payload["display_text"]
    tts_text = asset_payload.get("tts_text", display_text)
    normalized = NormalizedTtsInput(
        display_text=display_text,
        tts_text=tts_text,
        ssml_text=f'<speak version="1.0">{tts_text}</speak>',
    )
    return AudioAssetRecord(
        job_id="job-v13-normalized-fixtures",
        item_key=case["id"],
        asset_kind=AudioAssetKind.WORD,
        display_text=display_text,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="ru-RU-SvetlanaNeural",
            locale="ru-RU",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "missing-text-hash",
            ssml_hash=normalized.ssml_hash or "missing-ssml-hash",
            storage_path=asset_payload["storage_path"],
            byte_size=4096,
            duration_ms=900,
            status=AudioSynthesisStatus.SYNTHESIZED,
        ),
    )


def _make_template(case: dict[str, Any]) -> CardTemplate:
    payload = case["input"]
    return CardTemplate(
        front=payload["front"],
        back=payload["back"],
        css=payload["css"],
        source_template_name=case["id"],
    )


def _issue_type_values(case: dict[str, Any]) -> list[str]:
    if case["validator"] == "card":
        issues = validate_v13_card(_make_row(case), word_audio_asset=_make_audio_record(case))
    elif case["validator"] == "template":
        issues = validate_v13_template_contract(_make_template(case), FREQUENCY_EXPORT_CARD_FIELD_NAMES)
    else:  # pragma: no cover - fixture schema guard
        raise AssertionError(f"unsupported fixture validator: {case['validator']}")
    return sorted(issue.issue_type.value for issue in issues)


def test_fixture_catalog_tracks_every_summary_action_group() -> None:
    catalog = _fixture_catalog()
    coverage_ids = {entry["id"] for entry in catalog["coverage"]}
    case_groups = {case["group"] for case in catalog["cases"]}

    assert catalog["source_document"] == "card_issues_normalized.md"
    assert REQUIRED_COVERAGE_GROUPS <= coverage_ids
    assert REQUIRED_COVERAGE_GROUPS <= case_groups
    assert {entry["summary_action_line"] for entry in catalog["coverage"]} == set(range(123, 131))
    assert all(case["source_lines"] for case in catalog["cases"])


def test_normalized_issue_fixtures_match_v13_validator_output() -> None:
    catalog = _fixture_catalog()

    for case in catalog["cases"]:
        actual_issue_types = _issue_type_values(case)
        expected_issue_types = sorted(case["expected_issue_types"])

        assert actual_issue_types == expected_issue_types, case["id"]
        assert (not actual_issue_types) is case["expected_pass"], case["id"]
