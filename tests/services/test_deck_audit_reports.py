"""Tests for deterministic deck audit report writers."""

from __future__ import annotations

import json
from pathlib import Path

from multilang.domain.deck_audit import AuditCard, detect_card_issues
from multilang.services.deck_audit_reader import DeckAuditReadResult
from multilang.services.deck_audit_reports import write_deck_audit_reports


def make_card(
    *,
    note_id: int = 1,
    guid: str = "guid-1",
    card_identifier: str = "guid-1:1",
    field_name: str = "Definitions",
    definition: str = "noun: genitive/dative/prepositional singular",
) -> AuditCard:
    fields = {"word": "местности", "SortIndex": "1", field_name: definition}
    return AuditCard(
        note_id=note_id,
        note_guid=guid,
        model_id=1602300501,
        model_name="Multilang::Card",
        sort_index="1",
        card_identifier=card_identifier,
        fields=fields,
    )


def make_read_result(cards: list[AuditCard]) -> DeckAuditReadResult:
    return DeckAuditReadResult(
        source_path_name="deck.apkg",
        input_sha256="a" * 64,
        cards=cards,
        card_count=len(cards),
        media_files=set(),
        sound_references=set(),
    )


def test_json_report_is_byte_identical_for_identical_inputs(tmp_path: Path) -> None:
    card = make_card()
    issues = detect_card_issues(card)

    first = write_deck_audit_reports(make_read_result([card]), issues, tmp_path / "one")
    second = write_deck_audit_reports(make_read_result([card]), issues, tmp_path / "two")

    assert first.json_path.read_bytes() == second.json_path.read_bytes()


def test_json_contains_metadata_and_sorted_issues(tmp_path: Path) -> None:
    first_card = make_card(note_id=2, guid="guid-2", card_identifier="card-b")
    second_card = make_card(
        note_id=1,
        guid="guid-1",
        card_identifier="card-a",
        definition="noun: inflection of заболева́ние (zabolevánije)",
    )
    issues = detect_card_issues(first_card) + detect_card_issues(second_card)

    result = write_deck_audit_reports(make_read_result([first_card, second_card]), issues, tmp_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert payload["source_path_name"] == "deck.apkg"
    assert payload["input_sha256"] == "a" * 64
    assert payload["card_count"] == 2
    assert payload["issue_count"] == 2
    assert [issue["card_identifier"] for issue in payload["issues"]] == ["card-a", "card-b"]


def test_markdown_groups_issues_by_card_and_field(tmp_path: Path) -> None:
    card = make_card(card_identifier="card-1")
    issues = detect_card_issues(card)

    result = write_deck_audit_reports(make_read_result([card]), issues, tmp_path)
    markdown = result.markdown_path.read_text(encoding="utf-8")

    assert "## Card card-1" in markdown
    assert "### Field: Definitions" in markdown
    assert "grammar_metadata" in markdown
    assert "Rewrite the Definition" in markdown


def test_markdown_empty_issues_writes_explicit_passing_report(tmp_path: Path) -> None:
    card = make_card(definition="verb: to run; to operate")

    result = write_deck_audit_reports(make_read_result([card]), [], tmp_path)
    markdown = result.markdown_path.read_text(encoding="utf-8")

    assert "issue_count=0" in markdown
    assert "No normalized Definition audit issues found." in markdown
