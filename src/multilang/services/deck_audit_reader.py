"""Read generated APKG files into deck-audit rows without mutation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import sqlite3
from tempfile import TemporaryDirectory
import zipfile

from multilang.domain.deck_audit import AuditCard


@dataclass(frozen=True)
class DeckAuditReadResult:
    """Result metadata and cards extracted from an APKG audit read."""

    source_path_name: str
    input_sha256: str
    cards: list[AuditCard]
    card_count: int
    media_files: set[str]
    sound_references: set[str]


def read_apkg_cards(path: Path) -> DeckAuditReadResult:
    """Read note fields from an APKG using a temporary SQLite copy only."""

    apkg_path = Path(path)
    if not apkg_path.is_file():
        raise ValueError(f"APKG file does not exist: {apkg_path}")

    before_hash = _sha256_file(apkg_path)
    with TemporaryDirectory(prefix="multilang-apkg-audit-") as temp_dir:
        collection_path = Path(temp_dir) / "collection.anki2"
        media_files = _copy_collection_to_temp(apkg_path, collection_path)
        cards = _read_collection_cards(collection_path)

    after_hash = _sha256_file(apkg_path)
    if after_hash != before_hash:
        raise ValueError("APKG changed while being audited")

    return DeckAuditReadResult(
        source_path_name=apkg_path.name,
        input_sha256=before_hash,
        cards=cards,
        card_count=len(cards),
        media_files=media_files,
        sound_references=_sound_references(cards),
    )


def _copy_collection_to_temp(apkg_path: Path, collection_path: Path) -> set[str]:
    try:
        with zipfile.ZipFile(apkg_path) as archive:
            for info in archive.infolist():
                _reject_unsafe_member(info.filename)
            if "collection.anki2" not in archive.namelist():
                raise ValueError("APKG missing collection.anki2")
            collection_path.write_bytes(archive.read("collection.anki2"))
            return _read_media_manifest(archive)
    except zipfile.BadZipFile as exc:
        raise ValueError("APKG is not a readable zip archive") from exc


def _read_media_manifest(archive: zipfile.ZipFile) -> set[str]:
    if "media" not in archive.namelist():
        return set()
    try:
        payload = json.loads(archive.read("media").decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("APKG has invalid media manifest") from exc
    if not isinstance(payload, dict):
        raise ValueError("APKG media manifest must be a JSON object")
    return {str(value) for value in payload.values()}


def _reject_unsafe_member(name: str) -> None:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts:
        raise ValueError(f"APKG contains path traversal entry: {name}")


def _read_collection_cards(collection_path: Path) -> list[AuditCard]:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(collection_path)
        note_columns = {row[1] for row in connection.execute("pragma table_info(notes)").fetchall()}
        tag_projection = "tags" if "tags" in note_columns else "'' as tags"
        rows = connection.execute(
            f"select id, guid, mid, flds, {tag_projection} from notes order by id"
        ).fetchall()
        if not rows:
            raise ValueError("collection.anki2 contains no note rows")
        models = _read_models(connection)
    except sqlite3.DatabaseError as exc:
        raise ValueError("collection.anki2 is not a readable Anki SQLite database") from exc
    finally:
        if connection is not None:
            connection.close()

    cards: list[AuditCard] = []
    for note_id, guid, model_id, raw_fields, raw_tags in rows:
        model = models.get(str(model_id))
        if model is None:
            raise ValueError(f"note {note_id} references missing model {model_id}")
        field_names = [field["name"] for field in model.get("flds", [])]
        values = str(raw_fields).split("\x1f")
        if len(values) != len(field_names):
            raise ValueError(
                f"note {note_id} field count mismatch: expected {len(field_names)}, found {len(values)}"
            )
        fields = dict(zip(field_names, values, strict=True))
        sort_index = fields.get("SortIndex", "")
        cards.append(
            AuditCard(
                note_id=int(note_id),
                note_guid=str(guid),
                model_id=int(model_id),
                model_name=str(model.get("name", "")),
                sort_index=sort_index,
                card_identifier=f"{guid}:{sort_index or note_id}",
                fields=fields,
                tags=tuple(tag for tag in str(raw_tags or "").split() if tag),
            )
        )
    return cards


def _sound_references(cards: list[AuditCard]) -> set[str]:
    references: set[str] = set()
    for card in cards:
        for value in card.fields.values():
            references.update(match.group(1) for match in _SOUND_RE.finditer(value or ""))
    return references


_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")


def _read_models(connection: sqlite3.Connection) -> dict[str, object]:
    try:
        row = connection.execute("select models from col limit 1").fetchone()
    except sqlite3.DatabaseError as exc:
        raise ValueError("collection.anki2 missing col.models metadata") from exc
    if row is None:
        raise ValueError("collection.anki2 missing col.models metadata")
    try:
        models = json.loads(row[0])
    except json.JSONDecodeError as exc:
        raise ValueError("collection.anki2 has invalid col.models JSON") from exc
    if not isinstance(models, dict) or not models:
        raise ValueError("collection.anki2 has no Anki note models")
    return models


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["DeckAuditReadResult", "read_apkg_cards"]
