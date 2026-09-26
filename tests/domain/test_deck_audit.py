"""Tests for deck audit issue detection."""

from __future__ import annotations

from dataclasses import replace

from multilang.domain.deck_audit import (
    AuditCard,
    AuditIssueType,
    audit_deck_package,
    detect_card_issues,
)
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
    assert AuditIssueType.MISSING_TRACEABILITY_TAGS in issue_types


def test_package_audit_accepts_traceability_tags() -> None:
    card = AuditCard(
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
            "Translation": "Eu corro hoje.",
            "word_audio": "[sound:word.mp3]",
            "sentence_audio": "[sound:sentence.mp3]",
        },
        tags=("multilang", "en", "frequency", "level_1", "rank_0001", "job_job_1"),
    )
    read_result = DeckAuditReadResult(
        source_path_name="deck.apkg",
        input_sha256="abc",
        cards=[card],
        card_count=1,
        media_files={"word.mp3", "sentence.mp3"},
        sound_references={"word.mp3", "sentence.mp3"},
    )

    assert AuditIssueType.MISSING_TRACEABILITY_TAGS not in {issue.issue_type for issue in audit_deck_package(read_result)}


def _frequency_inventory_with_extra_form() -> list[AuditCard]:
    cards = []
    for rank in range(1, 3001):
        cards.append(AuditCard(
            note_id=rank,
            note_guid=f"size-policy-{rank}",
            model_id=202,
            model_name="Multilang::Card",
            sort_index=str(rank),
            card_identifier=f"size-policy-{rank}",
            fields={
                "SortIndex": str(rank),
                "word": f"test-word-{rank}",
                "Definitions": f"noun: a test meaning {rank}",
                "Example Sentence": f"Original test example {rank}.",
                "Translation": f"Exemplo de teste original {rank}.",
                "word_audio": "",
                "sentence_audio": "",
            },
            tags=("multilang", "en", "frequency", f"level_{(rank - 1) // 1000 + 1}", f"rank_{rank:04d}", "job_test"),
        ))
    cards.append(replace(
        cards[0],
        note_id=3001,
        note_guid="size-policy-extra-form",
        card_identifier="size-policy-extra-form",
        fields=cards[0].fields | {
            "word": "test-important-form",
            "Example Sentence": "Original test example for the additional form.",
            "Translation": "Exemplo de teste da forma adicional.",
        },
    ))
    return cards


def _audit_inventory(cards):
    return audit_deck_package(DeckAuditReadResult(
        source_path_name="synthetic-size-policy.apkg",
        input_sha256="a" * 64,
        cards=cards,
        card_count=len(cards),
        media_files=set(),
        sound_references=set(),
    ))


def test_audit_does_not_call_a_complete_core_plus_forms_incomplete():
    issues = _audit_inventory(_frequency_inventory_with_extra_form())

    assert issues == []


def test_extra_cards_do_not_hide_an_incomplete_core_level():
    cards = _frequency_inventory_with_extra_form()
    cards = [card for card in cards if card.sort_index != "2001"]

    issues = _audit_inventory(cards)

    assert any(
        issue.issue_type == AuditIssueType.INCOMPLETE_LEVEL and "level_3" in issue.message
        for issue in issues
    )
