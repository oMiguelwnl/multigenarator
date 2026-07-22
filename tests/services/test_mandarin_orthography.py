"""Deterministic Mandarin orthography contract tests."""

from __future__ import annotations

import importlib
import importlib.util

import pytest


def _orthography_module():
    module_name = "multilang.services.mandarin_orthography"
    spec = importlib.util.find_spec(module_name)
    assert spec is not None, "Mandarin orthography service must exist"
    return importlib.import_module(module_name)


def test_derives_phrase_aware_tonal_pinyin_and_traditional_forms() -> None:
    module = _orthography_module()

    value = module.derive_mandarin_orthography(word="中国", sentence="我去银行。")

    assert value.word_pinyin == "zhōng guó"
    assert value.word_traditional == "中國"
    assert value.sentence_pinyin == "wǒ qù yín háng。"
    assert value.sentence_traditional == "我去銀行。"


def test_phrase_dictionary_resolves_polyphonic_reading() -> None:
    module = _orthography_module()

    assert module.tonal_pinyin("银行") == "yín háng"


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("", "empty"),
        ("hello", "Han"),
        ("銀行", "Simplified"),
        ("銀行へ行く", "kana"),
        ("中国abc", "Latin"),
        ("中国Ж", "unsupported"),
    ],
)
def test_rejects_empty_non_han_traditional_japanese_and_latin_text(
    value: str,
    reason: str,
) -> None:
    module = _orthography_module()

    with pytest.raises(module.MandarinOrthographyError, match=reason):
        module.validate_simplified_mandarin(value)


def test_normalizes_nfkc_before_derivation() -> None:
    module = _orthography_module()

    assert module.validate_simplified_mandarin("　中国　") == "中国"


def test_rejects_sentence_without_han_even_when_word_is_valid() -> None:
    module = _orthography_module()

    with pytest.raises(module.MandarinOrthographyError, match="Han"):
        module.derive_mandarin_orthography(word="中国", sentence="hello world")


def test_rejects_unmapped_han_fallback_in_pinyin_output() -> None:
    module = _orthography_module()

    with pytest.raises(module.MandarinOrthographyError, match="pinyin"):
        module.tonal_pinyin("㐂")
