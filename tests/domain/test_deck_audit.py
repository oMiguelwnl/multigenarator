"""Tests for deck audit issue detection."""

from __future__ import annotations

from multilang.domain.deck_audit import AuditCard, AuditIssueType, audit_deck_package, detect_card_issues
from multilang.services.deck_audit_reader import DeckAuditReadResult


def make_card(*, word: str = "местности", definitions: str = "noun: genitive/dative/prepositional singular") -> AuditCard:
    return AuditCard(
        note_id=101,
        note_guid="guid-101",
        model_id=202,
        model_name="Multilang::Card",
        sort_index="1",
        card_identifier="guid-101:1",
        fields={"word": word, "Definitions": definitions},
    )


def test_detects_grammar_metadata_definition_issue() -> None:
    issues = detect_card_issues(make_card())

    assert [issue.issue_type for issue in issues] == [AuditIssueType.GRAMMAR_METADATA]
    assert issues[0].field_name == "Definitions"
    assert issues[0].note_id == 101
    assert issues[0].card_identifier == "guid-101:1"
    assert "semantic meaning" in issues[0].message


def test_detects_inflection_description_definition_issue() -> None:
    issues = detect_card_issues(
        make_card(definitions="noun: inflection of заболева́ние (zabolevánije)")
    )

    assert [issue.issue_type for issue in issues] == [AuditIssueType.INFLECTION_DESCRIPTION]
    assert "inflection of" in issues[0].evidence


def test_detects_known_wrong_sense_for_dostich() -> None:
    issues = detect_card_issues(make_card(word="дости́чь", definitions="verb: to amount to, to come to"))

    assert [issue.issue_type for issue in issues] == [AuditIssueType.WRONG_SENSE]
    assert "to achieve, to attain, to reach" in issues[0].message


def test_allows_semantic_definitions() -> None:
    assert detect_card_issues(make_card(word="run", definitions="verb: to run; to operate")) == []


def test_package_audit_detects_incomplete_invalid_duplicate_and_missing_media() -> None:
    cards = [
        AuditCard(
            note_id=1,
            note_guid="guid-1",
            model_id=2,
            model_name="Multilang::Card",
            sort_index="1",
            card_identifier="guid-1:1",
            fields={
                "SortIndex": "1",
                "word": "run",
                "Definitions": "verb: to run",
                "Example Sentence": "I run today.",
                "Translation": "Error 500 (Server Error)!!1500.That's an error.",
                "word_audio": "[sound:word.mp3]",
                "sentence_audio": "[sound:sentence.mp3]",
            },
        ),
        AuditCard(
            note_id=2,
            note_guid="guid-2",
            model_id=2,
            model_name="Multilang::Card",
            sort_index="1001",
            card_identifier="guid-2:1001",
            fields={
                "SortIndex": "1001",
                "word": "run",
                "Definitions": "verb: to run",
                "Example Sentence": "I run today.",
                "Translation": "I run today.",
                "word_audio": "[sound:word.mp3]",
                "sentence_audio": "[sound:missing.mp3]",
            },
        ),
    ]
    read_result = DeckAuditReadResult(
        source_path_name="deck.apkg",
        input_sha256="abc",
        cards=cards,
        card_count=2,
        media_files={"word.mp3", "sentence.mp3"},
        sound_references={"word.mp3", "sentence.mp3", "missing.mp3"},
    )

    issue_types = {issue.issue_type for issue in audit_deck_package(read_result)}

    assert AuditIssueType.INCOMPLETE_DECK in issue_types
    assert AuditIssueType.INCOMPLETE_LEVEL in issue_types
    assert AuditIssueType.INVALID_TRANSLATION in issue_types
    assert AuditIssueType.DUPLICATE_FIELD in issue_types
    assert AuditIssueType.MISSING_MEDIA in issue_types
