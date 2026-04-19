"""Tests for plain-text word list parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from multilang.services.word_list_parser import parse_word_list


def _write_text(path: Path, content: str, *, encoding: str = "utf-8") -> Path:
    path.write_text(content, encoding=encoding)
    return path


def test_parse_word_list_preserves_original_form(tmp_path: Path) -> None:
    word_list = _write_text(
        tmp_path / "words.txt",
        "  Hola\nAdiós amigo  \n  me   gusta  \n",
    )

    result = parse_word_list(word_list)

    assert [item.submitted_form for item in result.items] == ["  Hola", "Adiós amigo  ", "  me   gusta  "]
    assert [item.display_form for item in result.items] == ["Hola", "Adiós amigo", "me   gusta"]
    assert [item.item_key for item in result.items] == ["hola", "adiós amigo", "me gusta"]
    assert [item.line_number for item in result.items] == [1, 2, 3]


def test_parse_word_list_emits_blank_and_duplicate_diagnostics(tmp_path: Path) -> None:
    word_list = _write_text(
        tmp_path / "words.txt",
        "gato\n\n GATO \nperro\n",
    )

    result = parse_word_list(word_list)

    assert [item.display_form for item in result.items] == ["gato", "perro"]
    assert [(warning.code, warning.line_number) for warning in result.warnings] == [
        ("blank_line", 2),
        ("duplicate_item", 3),
    ]
    assert "line 1" in result.warnings[1].detail


def test_parse_word_list_rejects_non_utf8_input(tmp_path: Path) -> None:
    word_list = tmp_path / "words.txt"
    word_list.write_bytes("olá".encode("latin-1"))

    with pytest.raises(ValueError, match="UTF-8"):
        parse_word_list(word_list)
