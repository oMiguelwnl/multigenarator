"""Japanese kana (hiragana / katakana) Anki deck.

The project ships an original kana note type and template. The actual card
content -- glyphs, romaji, mnemonics, stroke-order art and audio -- is imported
at build time from a user-provided ``.apkg`` (for example a kana study deck the
user already owns) rather than being transcribed into this repository. The
importer understands both the legacy ``collection.anki2`` package layout and the
newer zstd-compressed ``collection.anki21b`` + protobuf media map format.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
import io
import re
import sqlite3
import tempfile
import zipfile

import genanki
import zstandard

KANA_MODEL_ID = 1_762_800_801
KANA_HIRAGANA_DECK_ID = 1_762_800_802
KANA_KATAKANA_DECK_ID = 1_762_800_803
KANA_NOTE_TYPE_NAME = "Multilang::Japanese Kana"
DEFAULT_KANA_DECK_NAME = "Multilang Japanese::Kana"
HIRAGANA_DECK_NAME = f"{DEFAULT_KANA_DECK_NAME}::Hiragana"
KATAKANA_DECK_NAME = f"{DEFAULT_KANA_DECK_NAME}::Katakana"

KANA_FIELD_NAMES = (
    "SortIndex",
    "Script",
    "Kana",
    "Romaji",
    "Mnemonic",
    "Picture",
    "Strokes",
    "Gif",
    "Audio",
)

# Source field names -> our field, per script. The source kana note types keep
# both scripts on every note, so we select the subset that matches the note's
# script and fall back gracefully when a column is absent.
_SOURCE_FIELDS = {
    "Hiragana": {
        "kana": ("Hiragana",),
        "mnemonic": ("Mnemonic_Hiragana", "Mnemonic"),
        "picture": ("Picture_Hiragana", "Picture"),
        "strokes": ("Strokes_Hiragana", "Strokes"),
        "gif": ("Gifs_Hiragana", "Gif_Hiragana", "Gifs"),
    },
    "Katakana": {
        "kana": ("Katakana",),
        "mnemonic": ("Mnemonic_Katakana", "Mnemonic"),
        "picture": ("Picture_Katakana", "Picture"),
        "strokes": ("Strokes_Katakana", "Strokes"),
        "gif": ("Gifs_Katakana", "Gif_Katakana", "Gifs"),
    },
}

_TEMPLATE_SECTION_RE = re.compile(
    r"## Front Template\s+```html\n(?P<front>.*?)```.*?"
    r"## Back Template\s+```html\n(?P<back>.*?)```.*?"
    r"## Styling \(CSS\)\s+```css\n(?P<css>.*?)```",
    re.DOTALL,
)
_MEDIA_REF_RE = re.compile(r'src\s*=\s*"([^"]+)"|\[sound:([^\]]+)\]')


@dataclass(frozen=True)
class KanaCard:
    sort_index: int
    script: str
    kana: str
    romaji: str
    mnemonic: str = ""
    picture: str = ""
    strokes: str = ""
    gif: str = ""
    audio: str = ""

    @property
    def guid(self) -> str:
        payload = f"ja-kana|{self.script}|{self.kana}|{self.romaji}"
        return sha256(payload.encode("utf-8")).hexdigest()[:32]

    def referenced_media(self) -> set[str]:
        names: set[str] = set()
        for value in (self.picture, self.strokes, self.gif, self.audio):
            for match in _MEDIA_REF_RE.finditer(value):
                names.add(match.group(1) or match.group(2))
        return names


class KanaNote(genanki.Note):
    @property
    def guid(self) -> str:
        return self._multilang_guid  # type: ignore[attr-defined]


@dataclass(frozen=True)
class KanaDeckExportResult:
    output_path: Path
    card_count: int
    hiragana_count: int
    katakana_count: int


# --- pure format helpers (unit-tested without a full package) ------------------


_ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def _zstd_decompress(blob: bytes) -> bytes:
    dctx = zstandard.ZstdDecompressor()
    try:
        return dctx.decompress(blob)
    except zstandard.ZstdError:
        return dctx.stream_reader(io.BytesIO(blob)).read()


def _maybe_zstd_decompress(blob: bytes) -> bytes:
    """Decompress only when the blob is zstd-framed.

    New-format packages store each media blob zstd-compressed; legacy packages
    store them raw. Detect by the zstd magic number so both work.
    """

    if blob[:4] == _ZSTD_MAGIC:
        return _zstd_decompress(blob)
    return blob


def _read_varint(blob: bytes, i: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        byte = blob[i]
        i += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, i
        shift += 7


def _protobuf_fields(blob: bytes) -> dict[int, list[bytes]]:
    """Minimal protobuf reader returning length-delimited fields by number."""

    out: dict[int, list[bytes]] = {}
    i = 0
    n = len(blob)
    while i < n:
        key, i = _read_varint(blob, i)
        field = key >> 3
        wire = key & 7
        if wire == 2:
            length, i = _read_varint(blob, i)
            out.setdefault(field, []).append(blob[i : i + length])
            i += length
        elif wire == 0:
            _, i = _read_varint(blob, i)
        elif wire == 5:
            i += 4
        elif wire == 1:
            i += 8
        else:
            break
    return out


def decode_media_map(media_blob: bytes) -> dict[str, str]:
    """Decode the package ``media`` manifest into ``{archive_index: filename}``.

    Supports the legacy plain-JSON manifest and the newer zstd + protobuf
    manifest (repeated entries whose first field is the file name, in archive
    order starting at 0).
    """

    import json

    try:
        return {str(k): v for k, v in json.loads(media_blob.decode("utf-8")).items()}
    except (UnicodeDecodeError, ValueError):
        pass

    decoded = _zstd_decompress(media_blob)
    try:
        return {str(k): v for k, v in json.loads(decoded.decode("utf-8")).items()}
    except (UnicodeDecodeError, ValueError):
        pass

    entries = _protobuf_fields(decoded).get(1, [])
    mapping: dict[str, str] = {}
    for index, entry in enumerate(entries):
        name_field = _protobuf_fields(entry).get(1)
        if name_field:
            mapping[str(index)] = name_field[0].decode("utf-8")
    return mapping


def _kana_card_from_fields(
    *, sort_index: int, script: str, field_values: dict[str, str]
) -> KanaCard | None:
    spec = _SOURCE_FIELDS[script]

    def pick(keys: tuple[str, ...]) -> str:
        for key in keys:
            if field_values.get(key):
                return field_values[key]
        return ""

    kana = pick(spec["kana"])
    romaji = field_values.get("Romaji", "").strip()
    if not kana.strip() or not romaji:
        return None
    return KanaCard(
        sort_index=sort_index,
        script=script,
        kana=kana.strip(),
        romaji=romaji,
        mnemonic=pick(spec["mnemonic"]),
        picture=pick(spec["picture"]),
        strokes=pick(spec["strokes"]),
        gif=pick(spec["gif"]),
        audio=field_values.get("Audio", ""),
    )


def _script_for_notetype(name: str) -> str | None:
    lowered = name.lower()
    if "katakana" in lowered:
        return "Katakana"
    if "hiragana" in lowered:
        return "Hiragana"
    return None


# --- package reading -----------------------------------------------------------


def _open_collection(archive: zipfile.ZipFile, work_dir: Path) -> sqlite3.Connection:
    names = set(archive.namelist())
    if "collection.anki21b" in names:
        data = _zstd_decompress(archive.read("collection.anki21b"))
    elif "collection.anki21" in names:
        data = archive.read("collection.anki21")
    else:
        data = archive.read("collection.anki2")
    db_path = work_dir / "collection.sqlite"
    db_path.write_bytes(data)
    return sqlite3.connect(db_path)


def _iter_notes(con: sqlite3.Connection):
    """Yield ``(script, {field_name: value})`` for every kana note."""

    tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "notetypes" in tables:
        field_order: dict[int, list[str]] = {}
        for ntid, in con.execute("SELECT id FROM notetypes"):
            field_order[ntid] = [
                r[0] for r in con.execute(
                    "SELECT name FROM fields WHERE ntid=? ORDER BY ord", (ntid,)
                )
            ]
        script_by_ntid = {
            ntid: _script_for_notetype(name)
            for ntid, name in con.execute("SELECT id, name FROM notetypes")
        }
        for mid, flds in con.execute("SELECT mid, flds FROM notes"):
            script = script_by_ntid.get(mid)
            if script is None:
                continue
            yield script, dict(zip(field_order.get(mid, []), flds.split("\x1f")))
    else:  # legacy models stored as JSON in col
        import json

        models = json.loads(con.execute("SELECT models FROM col").fetchone()[0])
        field_order = {
            int(mid): [f["name"] for f in mv["flds"]] for mid, mv in models.items()
        }
        script_by_mid = {int(mid): _script_for_notetype(mv["name"]) for mid, mv in models.items()}
        for mid, flds in con.execute("SELECT mid, flds FROM notes"):
            script = script_by_mid.get(mid)
            if script is None:
                continue
            yield script, dict(zip(field_order.get(mid, []), flds.split("\x1f")))


def import_kana_cards_from_apkg(
    apkg_path: Path, *, media_dir: Path
) -> tuple[list[KanaCard], list[Path]]:
    """Extract kana cards and their media from a user-provided ``.apkg``."""

    apkg_path = Path(apkg_path)
    if not apkg_path.is_file():
        raise FileNotFoundError(f"kana source package not found: {apkg_path}")

    media_dir.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, Path] = {}
    cards: list[KanaCard] = []

    with zipfile.ZipFile(apkg_path) as archive:
        names = set(archive.namelist())
        media_map = decode_media_map(archive.read("media")) if "media" in names else {}
        for index, filename in media_map.items():
            if index not in names:
                continue
            target = media_dir / filename
            target.write_bytes(_maybe_zstd_decompress(archive.read(index)))
            extracted[filename] = target

        with tempfile.TemporaryDirectory() as tmp:
            con = _open_collection(archive, Path(tmp))
            try:
                counters = {"Hiragana": 0, "Katakana": 0}
                for script, field_values in _iter_notes(con):
                    counters[script] += 1
                    card = _kana_card_from_fields(
                        sort_index=counters[script],
                        script=script,
                        field_values=field_values,
                    )
                    if card is not None:
                        cards.append(card)
            finally:
                con.close()

    referenced: set[str] = set()
    for card in cards:
        referenced |= card.referenced_media()
    media_files = [extracted[name] for name in referenced if name in extracted]
    return cards, media_files


# --- model / export ------------------------------------------------------------


def build_kana_model() -> genanki.Model:
    template = _load_kana_template()
    return genanki.Model(
        KANA_MODEL_ID,
        KANA_NOTE_TYPE_NAME,
        fields=[{"name": name} for name in KANA_FIELD_NAMES],
        templates=[
            {"name": "Kana Card", "qfmt": template["front"], "afmt": template["back"]}
        ],
        css=template["css"],
    )


def build_kana_note(card: KanaCard, *, model: genanki.Model | None = None) -> genanki.Note:
    note = KanaNote(model=model or build_kana_model(), fields=_kana_card_fields(card))
    note._multilang_guid = card.guid  # type: ignore[attr-defined]
    return note


def export_kana_deck(
    *,
    source_apkg: Path,
    output_path: Path,
    media_dir: Path | None = None,
    deck_name: str = DEFAULT_KANA_DECK_NAME,
) -> KanaDeckExportResult:
    """Import a kana source package and export a project-native kana deck."""

    output_path = Path(output_path)
    work_media_dir = media_dir or output_path.parent / "kana-media"
    cards, media_files = import_kana_cards_from_apkg(source_apkg, media_dir=work_media_dir)

    model = build_kana_model()
    hiragana_deck = genanki.Deck(KANA_HIRAGANA_DECK_ID, f"{deck_name}::Hiragana")
    katakana_deck = genanki.Deck(KANA_KATAKANA_DECK_ID, f"{deck_name}::Katakana")

    hiragana_count = 0
    katakana_count = 0
    for card in cards:
        note = build_kana_note(card, model=model)
        if card.script == "Katakana":
            katakana_deck.add_note(note)
            katakana_count += 1
        else:
            hiragana_deck.add_note(note)
            hiragana_count += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package([hiragana_deck, katakana_deck])
    package.media_files = [str(path) for path in media_files]
    package.write_to_file(str(output_path))
    return KanaDeckExportResult(
        output_path=output_path,
        card_count=len(cards),
        hiragana_count=hiragana_count,
        katakana_count=katakana_count,
    )


def _kana_card_fields(card: KanaCard) -> list[str]:
    values = {
        "SortIndex": str(card.sort_index),
        "Script": card.script,
        "Kana": card.kana,
        "Romaji": card.romaji,
        "Mnemonic": card.mnemonic,
        "Picture": card.picture,
        "Strokes": card.strokes,
        "Gif": card.gif,
        "Audio": card.audio,
    }
    return [values[name] for name in KANA_FIELD_NAMES]


def _load_kana_template() -> dict[str, str]:
    template_path = files("multilang").joinpath("templates", "japanese_kana_card.md")
    content = template_path.read_text(encoding="utf-8")
    match = _TEMPLATE_SECTION_RE.search(content)
    if match is None:
        raise ValueError(f"unable to parse kana template from {template_path}")
    return {name: match.group(name).strip() for name in ("front", "back", "css")}


__all__ = [
    "DEFAULT_KANA_DECK_NAME",
    "HIRAGANA_DECK_NAME",
    "KANA_FIELD_NAMES",
    "KANA_HIRAGANA_DECK_ID",
    "KANA_KATAKANA_DECK_ID",
    "KANA_MODEL_ID",
    "KANA_NOTE_TYPE_NAME",
    "KATAKANA_DECK_NAME",
    "KanaCard",
    "KanaDeckExportResult",
    "KanaNote",
    "build_kana_model",
    "build_kana_note",
    "decode_media_map",
    "export_kana_deck",
    "import_kana_cards_from_apkg",
]
