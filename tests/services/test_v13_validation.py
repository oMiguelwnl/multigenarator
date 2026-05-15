"""Tests for the v1.3 normalized validation facade."""

from __future__ import annotations

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.exporting import FREQUENCY_EXPORT_CARD_FIELD_NAMES
from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import CardTemplate, load_card_template
from multilang.services.v13_validation import (
    V13ValidationIssueType,
    validate_v13_card,
    validate_v13_template_contract,
)


def make_row(
    *,
    word: str = "громко",
    ipa: str | None = "[ˈɡromkə]",
    definitions: str = "adverb: loudly",
    example_sentence: str = "Он говорит громко каждый день.",
    translation: str = "He speaks loudly every day.",
    word_audio: str = "[sound:gromko.mp3]",
) -> ExportCardRow:
    identity = ExportCardIdentity(
        language=SupportedLanguage.RU,
        source_type="frequency",
        job_id="job-v13-validation",
        item_key=f"item-{word}",
        lemma_key=word,
        sort_index=1,
    )
    return ExportCardRow(
        identity=identity,
        word=word,
        front_of_card=word,
        ipa=ipa,
        definitions=definitions,
        example_sentence=example_sentence,
        translation=translation,
        word_audio=word_audio,
        sentence_audio="[sound:sentence.mp3]",
        image="",
    )


def issue_types(row: ExportCardRow) -> set[V13ValidationIssueType]:
    return {issue.issue_type for issue in validate_v13_card(row)}


def make_audio_record(*, word: str = "громко", asset_kind: AudioAssetKind = AudioAssetKind.WORD) -> AudioAssetRecord:
    normalized = NormalizedTtsInput(
        display_text=word,
        tts_text=word,
        ssml_text=f'<speak version="1.0">{word}</speak>',
    )
    return AudioAssetRecord(
        job_id="job-v13-validation",
        item_key=f"item-{word}",
        asset_kind=asset_kind,
        display_text=word,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="ru-RU-SvetlanaNeural",
            locale="ru-RU",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path="audio/word/gromko.mp3",
            byte_size=4096,
            duration_ms=900,
            status=AudioSynthesisStatus.SYNTHESIZED,
        ),
    )


def test_rejects_ipa_that_repeats_word_in_parentheses() -> None:
    issues = validate_v13_card(make_row(ipa="[ˈɡromkə] (гро́мко)"))

    assert [(issue.field_name, issue.issue_type) for issue in issues] == [
        ("IPA", V13ValidationIssueType.IPA_WORD_REPETITION)
    ]
    assert "громко" not in issues[0].message
    assert "/" not in issues[0].message


def test_rejects_banned_definition_patterns() -> None:
    inflection_issues = validate_v13_card(make_row(definitions="noun: inflection of заболева́ние"))
    grammar_issues = validate_v13_card(
        make_row(word="дальнего", definitions="adjective: masculine animate accusative singular")
    )

    assert ("Definitions", V13ValidationIssueType.DEFINITION_BANNED_PATTERN) in {
        (issue.field_name, issue.issue_type) for issue in inflection_issues
    }
    assert ("Definitions", V13ValidationIssueType.DEFINITION_BANNED_PATTERN) in {
        (issue.field_name, issue.issue_type) for issue in grammar_issues
    }


def test_rejects_isolated_word_translation_for_sentence() -> None:
    row = make_row(
        word="дости́чь",
        ipa="[dɐˈstʲitɕ]",
        definitions="verb: to achieve, to attain, to reach",
        example_sentence="Он хочет достичь цели завтра.",
        translation="to achieve",
    )

    issues = validate_v13_card(row)

    assert ("Translation", V13ValidationIssueType.TRANSLATION_EXAMPLE_MISMATCH) in {
        (issue.field_name, issue.issue_type) for issue in issues
    }


def test_clean_text_fields_return_no_issues_and_word_fallback_ipa_is_allowed() -> None:
    row = make_row(
        word="громко",
        ipa="громко",
        definitions="adverb: loudly, with a loud sound",
        example_sentence="Он говорит громко каждый день.",
        translation="He speaks loudly every day.",
    )

    assert issue_types(row) == set()


def test_word_audio_metadata_mismatch_is_normalized() -> None:
    row = make_row(word="громко", word_audio="[sound:gromko.mp3]")
    asset = make_audio_record(word="тихо")

    issues = validate_v13_card(row, word_audio_asset=asset)

    assert ("word_audio", V13ValidationIssueType.WORD_AUDIO_WORD_MISMATCH) in {
        (issue.field_name, issue.issue_type) for issue in issues
    }


def test_matching_word_audio_metadata_returns_no_audio_issue() -> None:
    row = make_row(word="громко", word_audio="[sound:gromko.mp3]")
    asset = make_audio_record(word="громко")

    issues = validate_v13_card(row, word_audio_asset=asset)

    assert V13ValidationIssueType.WORD_AUDIO_WORD_MISMATCH not in {issue.issue_type for issue in issues}


def test_dangling_template_field_is_normalized() -> None:
    template = CardTemplate(
        front="{{Front of Card}} {{Translation}}",
        back="{{FrontSide}} {{Definitions}}",
        css=".card { color: blue; }",
        source_template_name="normal_card",
    )

    issues = validate_v13_template_contract(template, FREQUENCY_EXPORT_CARD_FIELD_NAMES)

    assert [(issue.field_name, issue.issue_type) for issue in issues] == [
        ("template", V13ValidationIssueType.DANGLING_TEMPLATE_FIELD)
    ]


def test_project_normal_template_matches_v13_field_contract() -> None:
    assert validate_v13_template_contract(load_card_template("frequency"), FREQUENCY_EXPORT_CARD_FIELD_NAMES) == []
