"""Tests for Japanese furigana generation."""

from __future__ import annotations

from multilang.services.japanese_furigana import format_japanese_furigana, katakana_to_hiragana


def test_katakana_to_hiragana_preserves_non_katakana() -> None:
    assert katakana_to_hiragana("ガッコウABCー") == "がっこうABCー"


def test_format_japanese_furigana_handles_kanji_and_okurigana() -> None:
    assert format_japanese_furigana("学校に行く。") == "学校[がっこう]に行[い]く。"


def test_format_japanese_furigana_handles_multiple_kanji_tokens_and_numbers() -> None:
    assert format_japanese_furigana("父親は今年50歳になる。") == "父親[ちちおや]は今年[ことし]50歳[さい]になる。"


def test_format_japanese_furigana_treats_iteration_mark_as_kanji() -> None:
    assert format_japanese_furigana("時々行く。") == "時々[ときどき]行[い]く。"


def test_format_japanese_furigana_treats_small_ke_counter_as_kanji_like() -> None:
    assert format_japanese_furigana("三ヶ月") == "三[さん]ヶ月[かげつ]"


def test_format_japanese_furigana_leaves_kana_only_text_plain() -> None:
    assert format_japanese_furigana("こんにちは。") == "こんにちは。"
