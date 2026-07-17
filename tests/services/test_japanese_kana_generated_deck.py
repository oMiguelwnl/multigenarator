"""Tests for the fully self-generated Japanese kana deck."""

from __future__ import annotations

import zipfile
from pathlib import Path

from multilang.services.japanese_kana_generated_deck import (
    GENERATED_KANA_CARDS,
    export_generated_kana_deck,
)


class NoOpAzureSpeechAdapter:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def synthesize(self, **_kwargs):
        raise RuntimeError("audio disabled in kana generation tests")


def test_generated_cards_cover_full_kana_set_for_both_scripts() -> None:
    # 46 gojūon + 25 dakuten/handakuten + 33 yōon = 104 per script.
    per_script = 46 + 25 + 33
    assert len(GENERATED_KANA_CARDS) == per_script * 2

    hiragana = [c for c in GENERATED_KANA_CARDS if c.script == "Hiragana"]
    katakana = [c for c in GENERATED_KANA_CARDS if c.script == "Katakana"]
    assert len(hiragana) == per_script
    assert len(katakana) == per_script

    for cards in (hiragana, katakana):
        assert [c.sort_index for c in cards] == list(range(1, per_script + 1))
        # Every glyph distinct within a script.
        assert len({c.kana for c in cards}) == per_script


def test_generated_cards_have_glyph_romaji_and_mnemonic() -> None:
    for card in GENERATED_KANA_CARDS:
        assert card.kana.strip()
        assert card.romaji.strip()
        assert card.mnemonic.strip()

    # Spot-check anchors.
    a_hira = next(c for c in GENERATED_KANA_CARDS if c.script == "Hiragana" and c.romaji == "a")
    assert a_hira.kana == "あ"
    ga_hira = next(c for c in GENERATED_KANA_CARDS if c.script == "Hiragana" and c.romaji == "ga")
    assert ga_hira.kana == "が"
    assert "dakuten" in ga_hira.mnemonic
    kya_kata = next(c for c in GENERATED_KANA_CARDS if c.script == "Katakana" and c.romaji == "kya")
    assert kya_kata.kana == "キャ"


def test_generated_card_guids_are_unique() -> None:
    guids = [c.guid for c in GENERATED_KANA_CARDS]
    assert len(guids) == len(set(guids))


def test_export_generated_kana_deck_writes_apkg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "multilang.services.japanese_kana_generated_deck.AzureSpeechAdapter",
        NoOpAzureSpeechAdapter,
    )
    output_path = tmp_path / "japanese-kana-generated.apkg"

    result = export_generated_kana_deck(output_path=output_path)

    assert result.output_path == output_path
    assert result.card_count == len(GENERATED_KANA_CARDS)
    assert result.hiragana_count == 104
    assert result.katakana_count == 104
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
