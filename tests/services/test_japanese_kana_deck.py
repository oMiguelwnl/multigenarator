"""Tests for the Japanese kana deck importer/exporter."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import genanki
import zstandard

from multilang.services.anki_id_registry import AnkiIdKind, registry_id
from multilang.services.japanese_kana_deck import (
    KANA_HIRAGANA_DECK_ID,
    KANA_KATAKANA_DECK_ID,
    KANA_FIELD_NAMES,
    KANA_MODEL_ID,
    KANA_NOTE_TYPE_NAME,
    KanaCard,
    build_kana_model,
    build_kana_note,
    decode_media_map,
    export_kana_deck,
    import_kana_cards_from_apkg,
)


def test_japanese_kana_ids_are_registry_backed_without_local_numeric_declarations() -> None:
    source = Path("src/multilang/services/japanese_kana_deck.py").read_text(encoding="utf-8")

    assert KANA_MODEL_ID == registry_id(
        family="japanese_kana", role="model", kind=AnkiIdKind.MODEL
    )
    assert KANA_HIRAGANA_DECK_ID == registry_id(
        family="japanese_kana", role="hiragana_deck", kind=AnkiIdKind.DECK
    )
    assert KANA_KATAKANA_DECK_ID == registry_id(
        family="japanese_kana", role="katakana_deck", kind=AnkiIdKind.DECK
    )
    assert "1_762_800_801" not in source
    assert "1_762_800_802" not in source
    assert "1_762_800_803" not in source

# Source field layout mirrors Jo Mako-style kana note types (both scripts on
# every note). Only used to build a synthetic fixture package for the tests.
_SOURCE_FIELDS = [
    "Hiragana",
    "Katakana",
    "Romaji",
    "Audio",
    "Picture_Hiragana",
    "Mnemonic_Hiragana",
    "Picture_Katakana",
    "Mnemonic_Katakana",
    "Strokes_Hiragana",
    "Strokes_Katakana",
    "Gifs_Hiragana",
    "Gifs_Katakana",
]

_PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f5f0000000049454e44ae426082"
)


def _protobuf_len_delimited(field: int, payload: bytes) -> bytes:
    key = (field << 3) | 2
    return bytes([key]) + bytes([len(payload)]) + payload


def _build_new_format_media_blob(names: list[str]) -> bytes:
    entries = b"".join(
        _protobuf_len_delimited(1, _protobuf_len_delimited(1, name.encode("utf-8")))
        for name in names
    )
    return zstandard.ZstdCompressor().compress(entries)


def _write_source_apkg(path: Path, media_dir: Path) -> None:
    media_dir.mkdir(parents=True, exist_ok=True)
    hira_model = genanki.Model(
        1234500001,
        "Japanese Jo Mako's Kana - Hiragana",
        fields=[{"name": name} for name in _SOURCE_FIELDS],
        templates=[{"name": "Card 1", "qfmt": "{{Hiragana}}", "afmt": "{{Romaji}}"}],
    )
    kata_model = genanki.Model(
        1234500002,
        "Japanese Jo Mako's Kana - Katakana",
        fields=[{"name": name} for name in _SOURCE_FIELDS],
        templates=[{"name": "Card 1", "qfmt": "{{Katakana}}", "afmt": "{{Romaji}}"}],
    )

    pic_h = media_dir / "あ.jpg"
    pic_k = media_dir / "ア.jpg"
    audio = media_dir / "a.mp3"
    for f in (pic_h, pic_k):
        f.write_bytes(_PNG_1PX)
    audio.write_bytes(b"ID3fakeaudio")

    def fields(h, k, romaji):
        return [
            h, k, romaji, f"[sound:{audio.name}]",
            f'<img src="{pic_h.name}">', f"{romaji} mnemonic hiragana",
            f'<img src="{pic_k.name}">', f"{romaji} mnemonic katakana",
            "", "", "", "",
        ]

    deck = genanki.Deck(1234500009, "Source Kana")
    deck.add_note(genanki.Note(model=hira_model, fields=fields("あ", "ア", "a")))
    deck.add_note(genanki.Note(model=hira_model, fields=fields("い", "イ", "i")))
    deck.add_note(genanki.Note(model=kata_model, fields=fields("あ", "ア", "a")))

    package = genanki.Package(deck)
    package.media_files = [str(pic_h), str(pic_k), str(audio)]
    package.write_to_file(str(path))


# --- pure helper tests ---------------------------------------------------------


def test_decode_media_map_reads_new_format_protobuf() -> None:
    blob = _build_new_format_media_blob(["katakana_he.png", "か.jpg", "audio.mp3"])
    mapping = decode_media_map(blob)
    assert mapping == {"0": "katakana_he.png", "1": "か.jpg", "2": "audio.mp3"}


def test_decode_media_map_reads_legacy_json() -> None:
    blob = b'{"0": "a.png", "1": "b.mp3"}'
    assert decode_media_map(blob) == {"0": "a.png", "1": "b.mp3"}


def test_kana_card_referenced_media_extracts_all_asset_names() -> None:
    card = KanaCard(
        sort_index=1,
        script="Hiragana",
        kana="あ",
        romaji="a",
        picture='<img src="あ.jpg">',
        strokes='<img src="stroke_a.png">',
        gif='<img src="a.gif">',
        audio="[sound:a.mp3]",
    )
    assert card.referenced_media() == {"あ.jpg", "stroke_a.png", "a.gif", "a.mp3"}


def test_build_kana_model_uses_template_and_fields() -> None:
    model = build_kana_model()
    assert model.name == KANA_NOTE_TYPE_NAME
    assert tuple(f["name"] for f in model.fields) == KANA_FIELD_NAMES
    front = model.templates[0]["qfmt"]
    back = model.templates[0]["afmt"]
    assert "{{Kana}}" in front
    assert "{{Romaji}}" in back
    assert "{{Mnemonic}}" in back
    assert ".kanaCard" in model.css


def test_build_kana_note_maps_fields_in_order() -> None:
    card = KanaCard(
        sort_index=3, script="Katakana", kana="ア", romaji="a", audio="[sound:a.mp3]"
    )
    note = build_kana_note(card, model=build_kana_model())
    assert note.fields == ["3", "Katakana", "ア", "a", "", "", "", "", "[sound:a.mp3]"]
    assert note.guid == card.guid


# --- import / export end-to-end (synthetic legacy package) ---------------------


def test_import_kana_cards_splits_by_script(tmp_path: Path) -> None:
    src = tmp_path / "source-kana.apkg"
    _write_source_apkg(src, tmp_path / "src-media")

    cards, media_files = import_kana_cards_from_apkg(src, media_dir=tmp_path / "out-media")

    scripts = sorted(card.script for card in cards)
    assert scripts == ["Hiragana", "Hiragana", "Katakana"]
    hira = next(c for c in cards if c.script == "Hiragana")
    assert hira.kana == "あ"
    assert hira.romaji == "a"
    assert "mnemonic hiragana" in hira.mnemonic
    assert 'src="あ.jpg"' in hira.picture
    assert hira.audio == "[sound:a.mp3]"
    # Extracted media files exist on disk.
    assert media_files
    assert all(path.exists() for path in media_files)


def test_export_kana_deck_writes_apkg_with_both_scripts(tmp_path: Path) -> None:
    src = tmp_path / "source-kana.apkg"
    _write_source_apkg(src, tmp_path / "src-media")
    output_path = tmp_path / "japanese-kana.apkg"

    result = export_kana_deck(
        source_apkg=src, output_path=output_path, media_dir=tmp_path / "kana-media"
    )

    assert result.output_path == output_path
    assert result.card_count == 3
    assert result.hiragana_count == 2
    assert result.katakana_count == 1
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
