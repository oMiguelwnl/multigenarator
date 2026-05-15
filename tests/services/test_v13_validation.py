"""Tests for the v1.3 normalized validation facade."""

from __future__ import annotations

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.v13_validation import V13ValidationIssueType, validate_v13_card


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
        language=SupportedLanguage.RUSSIAN,
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
