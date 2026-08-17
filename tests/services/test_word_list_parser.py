"""Tests for plain-text word list parsing."""

from __future__ import annotations

from pathlib import Path
import unicodedata

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


def test_parse_word_list_splits_loose_lines_and_preserves_quoted_phrases(tmp_path: Path) -> None:
    word_list = _write_text(
        tmp_path / "words.md",
        'alpha "Robe de soie" bravo "Frais ruban"\n',
    )

    result = parse_word_list(word_list)

    assert [item.display_form for item in result.items] == [
        "alpha",
        "Robe de soie",
        "bravo",
        "Frais ruban",
    ]
    assert [item.item_key for item in result.items] == [
        "alpha",
        "robe de soie",
        "bravo",
        "frais ruban",
    ]
    assert [item.line_number for item in result.items] == [1, 1, 1, 1]


def test_parse_word_list_keeps_comma_separated_multiword_entries_together(tmp_path: Path) -> None:
    word_list = _write_text(
        tmp_path / "words.md",
        "- Robe de soie, Frais ruban; carte postale\n",
    )

    result = parse_word_list(word_list)

    assert [item.display_form for item in result.items] == [
        "Robe de soie",
        "Frais ruban",
        "carte postale",
    ]


def test_parse_word_list_splits_dense_titlecase_line_and_preserves_lowercase_phrase_parts(
    tmp_path: Path,
) -> None:
    word_list = _write_text(
        tmp_path / "words.md",
        "Loge Aplomb Remercia Canne Noue Étoiles Soupçonnée Fouiller Établi Vernis "
        "Éphémère Duvet Ôte Commencement Aisance Soins Robe de soie Guimpe "
        "Dentelle Soulier Frais ruban\n",
    )

    result = parse_word_list(word_list)

    assert [item.display_form for item in result.items] == [
        "Loge",
        "Aplomb",
        "Remercia",
        "Canne",
        "Noue",
        "Étoiles",
        "Soupçonnée",
        "Fouiller",
        "Établi",
        "Vernis",
        "Éphémère",
        "Duvet",
        "Ôte",
        "Commencement",
        "Aisance",
        "Soins",
        "Robe de soie",
        "Guimpe",
        "Dentelle",
        "Soulier",
        "Frais ruban",
    ]


def test_parse_word_list_rejects_non_utf8_input(tmp_path: Path) -> None:
    word_list = tmp_path / "words.txt"
    word_list.write_bytes("olá".encode("latin-1"))

    with pytest.raises(ValueError, match="UTF-8"):
        parse_word_list(word_list)


def test_parse_word_list_converges_nfd_and_nfc_without_losing_submitted_evidence(
    tmp_path: Path,
) -> None:
    nfc = "학교"
    nfd = unicodedata.normalize("NFD", nfc)
    word_list = _write_text(
        tmp_path / "korean-words.txt",
        f"  {nfd}  \n{nfc}\n물\n",
    )

    result = parse_word_list(word_list)

    assert [item.submitted_form for item in result.items] == [f"  {nfd}  ", "물"]
    assert [item.display_form for item in result.items] == [nfc, "물"]
    assert [item.item_key for item in result.items] == [nfc, "물"]
    assert [item.line_number for item in result.items] == [1, 3]
    assert [(warning.code, warning.line_number) for warning in result.warnings] == [
        ("duplicate_item", 2),
    ]
    assert "line 1" in result.warnings[0].detail
