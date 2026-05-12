"""Tests for deck audit issue detection."""

from __future__ import annotations

from multilang.domain.deck_audit import AuditCard, AuditIssueType, detect_card_issues


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
