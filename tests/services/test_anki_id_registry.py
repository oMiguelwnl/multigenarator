from __future__ import annotations

from pathlib import Path

import pytest

from multilang.services.anki_id_registry import (
    ANKI_ID_REGISTRY,
    AnkiIdKind,
    AnkiIdRegistration,
    assert_anki_id_registry_clean,
    registry_id,
    scan_anki_id_registry_paths,
    validate_anki_id_registry,
)


EXPECTED_BASELINE = {
    ("core", "frequency_model", "model"): 1_602_300_501,
    ("core", "export_deck", "deck"): 1_602_300_502,
    ("core", "manual_model", "model"): 1_602_300_503,
    ("core", "highlight_model", "model"): 1_602_300_504,
    ("phoneme", "russian_model", "model"): 1_602_300_601,
    ("phoneme", "russian_deck", "deck"): 1_602_300_602,
    ("phoneme", "polish_model", "model"): 1_602_300_603,
    ("phoneme", "polish_deck", "deck"): 1_602_300_604,
    ("phoneme", "greek_model", "model"): 1_602_300_605,
    ("phoneme", "greek_deck", "deck"): 1_602_300_606,
    ("latin", "mvp_model", "model"): 1_602_300_701,
    ("latin", "mvp_deck", "deck"): 1_602_300_702,
    ("japanese_frequency", "model", "model"): 1_762_800_701,
    ("japanese_frequency", "deck", "deck"): 1_762_800_702,
    ("japanese_kana", "model", "model"): 1_762_800_801,
    ("japanese_kana", "hiragana_deck", "deck"): 1_762_800_802,
    ("japanese_kana", "katakana_deck", "deck"): 1_762_800_803,
    ("mandarin", "card_model", "model"): 1_762_800_901,
    ("korean_foundation", "hangul_model", "model"): 1_762_801_001,
    ("korean_foundation", "hangul_deck", "deck"): 1_762_801_002,
    ("korean_foundation", "pronunciation_model", "model"): 1_762_801_003,
    ("korean_foundation", "pronunciation_deck", "deck"): 1_762_801_004,
    ("korean_frequency", "model", "model"): 1_762_801_101,
    ("korean_frequency", "parent_deck", "deck"): 1_762_801_102,
    ("korean_frequency", "level_1_deck", "deck"): 1_762_801_103,
    ("korean_frequency", "level_2_deck", "deck"): 1_762_801_104,
    ("korean_frequency", "level_3_deck", "deck"): 1_762_801_105,
}


def test_baseline_contains_every_current_production_declaration_once() -> None:
    validate_anki_id_registry(ANKI_ID_REGISTRY)

    actual = {
        (entry.family, entry.role, entry.kind.value): entry.value
        for entry in ANKI_ID_REGISTRY
    }

    assert actual == EXPECTED_BASELINE
    assert len({entry.value for entry in ANKI_ID_REGISTRY}) == len(ANKI_ID_REGISTRY)


def test_registry_declaration_lookup_uses_typed_kind() -> None:
    assert registry_id(family="core", role="frequency_model", kind=AnkiIdKind.MODEL) == 1_602_300_501
    assert registry_id(family="core", role="export_deck", kind=AnkiIdKind.DECK) == 1_602_300_502

    with pytest.raises(ValueError, match="unregistered Anki ID"):
        registry_id(family="core", role="frequency_model", kind=AnkiIdKind.DECK)


def test_duplicate_same_kind_declaration_fails_closed() -> None:
    duplicate = AnkiIdRegistration(
        family="test",
        role="duplicate_frequency_model",
        kind=AnkiIdKind.MODEL,
        value=1_602_300_501,
    )

    with pytest.raises(ValueError, match="duplicate model Anki ID"):
        validate_anki_id_registry((*ANKI_ID_REGISTRY, duplicate))


def test_cross_kind_collision_fails_closed() -> None:
    collision = AnkiIdRegistration(
        family="test",
        role="deck_uses_model_value",
        kind=AnkiIdKind.DECK,
        value=1_602_300_501,
    )

    with pytest.raises(ValueError, match="cross-kind Anki ID collision"):
        validate_anki_id_registry((*ANKI_ID_REGISTRY, collision))


def test_korean_frequency_ids_are_reserved_without_packaging() -> None:
    assert registry_id(family="korean_frequency", role="model", kind=AnkiIdKind.MODEL) == 1_762_801_101
    assert registry_id(family="korean_frequency", role="parent_deck", kind=AnkiIdKind.DECK) == 1_762_801_102
    assert [
        registry_id(family="korean_frequency", role=f"level_{level}_deck", kind=AnkiIdKind.DECK)
        for level in (1, 2, 3)
    ] == [1_762_801_103, 1_762_801_104, 1_762_801_105]


def test_scanner_detects_literals_config_keys_and_unchecked_dynamics(tmp_path: Path) -> None:
    src_root = tmp_path / "src" / "multilang"
    src_root.mkdir(parents=True)
    (src_root / "bad_ids.py").write_text(
        "import genanki\n"
        "BAD_MODEL_ID = 1_762_801_101\n"
        "UNKNOWN_DECK_ID = 9_999_999_998\n"
        "def build(model_id: int):\n"
        "    return genanki.Model(model_id, 'Dynamic', fields=[], templates=[])\n",
        encoding="utf-8",
    )
    data_root = tmp_path / "data"
    data_root.mkdir()
    (data_root / "ids.json").write_text('{"deck_id": 1762801102}', encoding="utf-8")

    result = scan_anki_id_registry_paths((src_root, data_root))
    codes = {issue.code for issue in result.issues}

    assert "direct_literal" in codes
    assert "data_literal" in codes
    assert "unknown_declaration" in codes
    assert "unchecked_dynamic" in codes


def test_scanner_excludes_non_production_roots(tmp_path: Path) -> None:
    for dirname in ("tests", ".planning", "build", "private"):
        folder = tmp_path / dirname
        folder.mkdir()
        (folder / "ignored.py").write_text("IGNORED_MODEL_ID = 1_762_801_101\n", encoding="utf-8")

    result = scan_anki_id_registry_paths((tmp_path,))

    assert result.passed


def test_scanner_reports_unused_unreserved_registrations(tmp_path: Path) -> None:
    (tmp_path / "empty.py").write_text("VALUE = 1\n", encoding="utf-8")
    extra = AnkiIdRegistration("test", "future_model", AnkiIdKind.MODEL, 8_888_888_888)

    result = scan_anki_id_registry_paths((tmp_path,), registry=(extra,))

    assert any(issue.code == "unused_registration" for issue in result.issues)


def test_prewrite_guard_raises_without_touching_destination(tmp_path: Path) -> None:
    bad_root = tmp_path / "src" / "multilang"
    bad_root.mkdir(parents=True)
    (bad_root / "bad_ids.py").write_text("BAD_DECK_ID = 1_762_801_102\n", encoding="utf-8")
    destination = tmp_path / "exports" / "deck.apkg"
    destination.parent.mkdir()
    destination.write_bytes(b"sentinel")

    with pytest.raises(ValueError, match="Anki ID registry violations"):
        assert_anki_id_registry_clean(roots=(bad_root,))

    assert destination.read_bytes() == b"sentinel"
