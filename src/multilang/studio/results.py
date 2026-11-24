"""Review the operator's local copy of a completed genanki export."""

import html
import json
import os
import re
import shutil
import sqlite3
import struct
import time
import zlib
from collections.abc import Callable
from contextlib import closing
from hashlib import sha1, sha256
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from uuid import UUID
from zipfile import ZipFile

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.background import BackgroundTask

SOUND = re.compile(r"\[sound:([^\]]+)\]", re.IGNORECASE)
IMAGE = re.compile(r'<img\b[^>]*\bsrc\s*=\s*["\x27]([^"\x27]+)["\x27][^>]*>', re.I)
NEW_IMAGE = re.compile(r"studio-[0-9a-f]{64}\.png")
TEXT_FIELDS = {
    "Definition", "Definitions", "Example Sentence", "Sentence", "Sentence Translation",
    "Translation", "Word Translation", "Mnemonic", "Grammar",
}
IMAGE_FIELDS = {"Image", "Picture"}
SENTENCE_FIELDS = {"Sentence", "Example Sentence"}
SENTENCE_READINGS = {"Sentence Furigana", "Sentence Romaji", "Sentence Pinyin", "Traditional Sentence"}
MEDIA_TYPES = {
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg", ".m4a": "audio/mp4",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
}


class NoteEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: str = Field(pattern=r"^[0-9a-f]{64}$")
    fields: dict[str, str] = Field(min_length=1, max_length=20)


def plain(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", SOUND.sub("", value), flags=re.I)
    return html.unescape(re.sub(r"<[^>]*>", "", value)).strip()


def editable_text(name: str, fields: dict[str, str]) -> bool:
    if name not in TEXT_FIELDS or (name in SENTENCE_FIELDS and SENTENCE_READINGS.intersection(fields)):
        return False
    value = re.sub(r"<br\s*/?>", "", fields[name], flags=re.I)
    return "{{" not in value and not re.search(r"<[^>]+>", value)


def note_revision(nid: int, modified: int, raw: str) -> str:
    return sha256(f"{nid}:{modified}:{raw}".encode()).hexdigest()


def reviewed_png(data: bytes) -> bytes:
    invalid = HTTPException(422, "Escolha uma imagem PNG estática válida de até 5 MB.")
    if (len(data) < 57 or len(data) > 5_000_000
            or not data.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")):
        raise invalid
    width, height, depth, color, compression, filters, interlace = struct.unpack(">IIBBBBB", data[16:29])
    if not width or not height or width * height > 20_000_000:
        raise HTTPException(422, "A imagem deve ter até 20 megapixels.")
    depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
    if depth not in depths.get(color, ()) or compression or filters or interlace not in (0, 1):
        raise invalid
    bits = depth * {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    passes = ((0, 0, 1, 1),) if not interlace else (
        (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
        (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2),
    )
    expected = 0
    for x, y, dx, dy in passes:
        columns, rows = len(range(x, width, dx)), len(range(y, height, dy))
        if columns:
            expected += rows * (1 + (columns * bits + 7) // 8)

    # Keep pixel data and transparency. Ancillary chunks can carry arbitrary metadata.
    output = bytearray(data[:8])
    inflater = zlib.decompressobj()
    palette_size = 0
    offset = 8
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset:offset + 4], "big")
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data) or zlib.crc32(data[offset + 4:end - 4]) != int.from_bytes(data[end - 4:end], "big"):
            raise invalid
        payload = data[offset + 8:end - 4]
        if kind == b"IDAT":
            if color == 3 and not palette_size:
                raise invalid
            try:
                while payload:
                    block = inflater.decompress(payload, min(65536, expected + 1))
                    expected -= len(block)
                    if expected < 0 or inflater.unused_data:
                        raise invalid
                    payload = inflater.unconsumed_tail
            except zlib.error:
                raise invalid from None
        elif kind == b"IEND":
            if length or end != len(data) or expected or not inflater.eof:
                raise invalid
            output.extend(data[offset:end])
            return bytes(output)
        elif kind == b"PLTE":
            if palette_size or not length or length % 3 or length > 768:
                raise invalid
            palette_size = length // 3
        elif kind == b"tRNS":
            if not (color == 0 and length == 2 or color == 2 and length == 6
                    or color == 3 and 0 < length <= palette_size):
                raise invalid
        elif kind == b"IHDR":
            if offset != 8:
                raise invalid
        elif kind == b"acTL" or not kind[:1].islower():
            raise invalid
        else:
            offset = end
            continue
        output.extend(data[offset:end])
        offset = end
    raise invalid


def working_collection(package: Path, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "collection.anki2"
    if target.is_file():
        return target
    with TemporaryDirectory(dir=directory) as temp:
        candidate = Path(temp) / "collection.anki2"
        with ZipFile(package) as archive:
            member = archive.getinfo("collection.anki2")
            if member.file_size > 256 * 1024 * 1024:
                raise HTTPException(413, "A coleção excede o limite da revisão local.")
            with archive.open(member) as source, candidate.open("wb") as destination:
                shutil.copyfileobj(source, destination)
        try:
            os.link(candidate, target)
        except FileExistsError:
            pass
    return target


def manifest(archive: ZipFile) -> dict[str, str]:
    info = archive.getinfo("media")
    if info.file_size > 8 * 1024 * 1024:
        raise HTTPException(413, "O índice de mídias excede o limite da revisão local.")
    return json.loads(archive.read(info))


class Review:
    def __init__(self, source: Path, directory: Path):
        self.source = source
        self.directory = directory
        self.collection = working_collection(source, directory)

    def connect(self):
        db = sqlite3.connect(self.collection)
        db.execute("pragma trusted_schema=off")
        return db

    def describe(self, db, rows):
        models = json.loads(db.execute("select models from col").fetchone()[0])
        with ZipFile(self.source) as archive:
            media = {name: key for key, name in manifest(archive).items()}
        notes = []
        for nid, mid, raw, modified in rows:
            model = models[str(mid)]
            values = dict(zip((f["name"] for f in model["flds"]), raw.split("\x1f"), strict=True))
            fields = []
            for name, value in values.items():
                image = IMAGE.search(value) if name in IMAGE_FIELDS else None
                fields.append({
                    "name": name, "text": plain(value),
                    "editable": editable_text(name, values),
                    "imageField": name in IMAGE_FIELDS, "hasImage": bool(image),
                    "audio": [media[file] for file in SOUND.findall(value) if file in media
                              and MEDIA_TYPES.get(Path(file).suffix.lower(), "").startswith("audio/")],
                })
            titles = ("Word", "word", "Target Word", "Kana", "JamoOrBlock", "Sound", "Example Word")
            by_name = {field["name"]: field["text"] for field in fields}
            title = next((by_name[key] for key in titles if by_name.get(key)), model["name"])
            notes.append({"id": str(nid), "title": title, "model": model["name"], "fields": fields,
                          "revision": note_revision(nid, modified, raw)})
        return notes

    def edit(self, nid: int, revision: str, replacements: dict[str, str], image: bytes | None = None):
        with closing(self.connect()) as db, db:
            db.execute("begin immediate")
            row = db.execute("select mid, flds, mod from notes where id=?", (nid,)).fetchone()
            if not row:
                raise HTTPException(404, "Nota não encontrada.")
            mid, raw, modified = row
            if note_revision(nid, modified, raw) != revision:
                raise HTTPException(409, "Outra edição foi salva. Recarregue a nota antes de editar.")
            model = json.loads(db.execute("select models from col").fetchone()[0])[str(mid)]
            names = [field["name"] for field in model["flds"]]
            values = dict(zip(names, raw.split("\x1f"), strict=True))
            for name, value in replacements.items():
                if name not in values:
                    raise HTTPException(422, "Campo desconhecido para este modelo.")
                if name in IMAGE_FIELDS:
                    if value:
                        raise HTTPException(422, "Escolha um arquivo de imagem.")
                    if image is None:
                        values[name] = ""
                    else:
                        filename = f"studio-{sha256(image).hexdigest()}.png"
                        if not (self.directory / filename).exists():
                            with TemporaryDirectory(dir=self.directory) as temporary:
                                candidate = Path(temporary) / filename
                                candidate.write_bytes(image)
                                candidate.replace(self.directory / filename)
                        values[name] = f'<img src="{filename}">'
                    continue
                if (not editable_text(name, values) or not value.strip()
                        or len(value) > 6000 or re.search(r"[\x00-\x08\x0b-\x1f]|\[(?:sound|anki):|\{\{", value, re.I)):
                    raise HTTPException(422, "Use texto simples em um campo de conteúdo editável.")
                if value.strip() == plain(values[name]):
                    continue
                audio_refs = SOUND.findall(values[name])
                values[name] = html.escape(value.strip()).replace("\n", "<br>")
                if name in SENTENCE_FIELDS:
                    if "sentence_audio" in values:
                        values["sentence_audio"] = ""
                else:
                    values[name] += "".join(f"<br>[sound:{ref}]" for ref in audio_refs)
            updated = "\x1f".join(values.values())
            if updated != raw:
                sort_field = values[names[model.get("sortf", 0)]]
                checksum = int(sha1(plain(values[names[0]]).encode()).hexdigest()[:8], 16)
                modified = max(int(time.time()), modified + 1)
                db.execute("update notes set flds=?, sfld=?, csum=?, mod=?, usn=-1 where id=?",
                           (updated, plain(sort_field), checksum, modified, nid))
            return self.describe(db, [(nid, mid, updated, modified)])[0]


def create_results_router(resolve_package: Callable[[UUID], Path], *, review_root: Path):
    router = APIRouter(prefix="/studio-api/productions/{production_id}")

    def review(production_id):
        return Review(resolve_package(production_id), review_root / str(production_id))

    @router.get("/result")
    def result(production_id: UUID, offset: int = Query(0, ge=0, le=2**31),
               limit: int = Query(25, ge=1, le=100), q: str = Query("", max_length=200)):
        document = review(production_id)
        with closing(document.connect()) as db:
            db.create_function("contains_text", 1, lambda raw: q.casefold() in plain(raw).casefold())
            where = " where contains_text(flds)" if q.strip() else ""
            total = db.execute("select count(*) from notes" + where).fetchone()[0]
            rows = db.execute("select id,mid,flds,mod from notes" + where + " order by id limit ? offset ?",
                              (limit, offset))
            return {"total": total, "notes": document.describe(db, rows)}

    @router.patch("/result/{nid}")
    def edit(production_id: UUID, nid: int, payload: NoteEdit):
        return review(production_id).edit(nid, payload.revision, payload.fields)

    @router.put("/result/{nid}/image")
    def upload_image(production_id: UUID, nid: int, revision: str, field: str,
                     data: bytes = Body(media_type="image/png")):
        if field not in IMAGE_FIELDS:
            raise HTTPException(422, "Escolha um campo de imagem.")
        return review(production_id).edit(nid, revision, {field: ""}, image=reviewed_png(data))

    def read_media(archive, key, filename, prefix):
        content_type = MEDIA_TYPES.get(Path(filename).suffix.lower(), "")
        if not content_type.startswith(prefix):
            raise HTTPException(404, "Mídia indisponível.")
        if archive.getinfo(key).file_size > 50_000_000:
            raise HTTPException(413, "Mídia grande demais para reprodução no Estúdio.")
        return Response(archive.read(key), media_type=content_type)

    @router.get("/media/{number}")
    def media(production_id: UUID, number: int):
        with ZipFile(resolve_package(production_id)) as archive:
            key = str(number)
            return read_media(archive, key, manifest(archive).get(key, ""), "audio/")

    @router.get("/result/{nid}/image")
    def image(production_id: UUID, nid: int, field: str):
        document = review(production_id)
        with closing(document.connect()) as db:
            row = db.execute("select mid,flds from notes where id=?", (nid,)).fetchone()
            if row and field in IMAGE_FIELDS:
                model = json.loads(db.execute("select models from col").fetchone()[0])[str(row[0])]
                fields = dict(zip((f["name"] for f in model["flds"]), row[1].split("\x1f"), strict=True))
                match = IMAGE.search(fields.get(field, ""))
                if match:
                    name = html.unescape(match.group(1))
                    if NEW_IMAGE.fullmatch(name) and (document.directory / name).is_file():
                        return FileResponse(document.directory / name, media_type="image/png")
                    with ZipFile(document.source) as archive:
                        for key, filename in manifest(archive).items():
                            if filename == name:
                                return read_media(archive, key, name, "image/")
        raise HTTPException(404, "Imagem indisponível.")

    @router.get("/export")
    def export(production_id: UUID):
        document = review(production_id)
        with NamedTemporaryFile(suffix=".apkg", delete=False) as file:
            target = Path(file.name)
        try:
            with TemporaryDirectory() as temporary, ZipFile(document.source) as original:
                snapshot = Path(temporary) / "collection.anki2"
                with closing(document.connect()) as source, closing(sqlite3.connect(snapshot)) as db:
                    source.backup(db)
                    images = set()
                    for (fields,) in db.execute("select flds from notes where flds like '%studio-%'"):
                        images.update(name for name in IMAGE.findall(fields) if NEW_IMAGE.fullmatch(name))
                with ZipFile(target, "w") as archive:
                    members = manifest(original)
                    for entry in original.infolist():
                        if entry.filename not in {"collection.anki2", "media"}:
                            with original.open(entry) as src, archive.open(entry, "w") as dst:
                                shutil.copyfileobj(src, dst)
                    archive.write(snapshot, "collection.anki2")
                    next_key = max(map(int, members), default=-1) + 1
                    for filename in sorted(images.difference(members.values())):
                        key = str(next_key)
                        archive.write(document.directory / filename, key)
                        members[key] = filename
                        next_key += 1
                    archive.writestr("media", json.dumps(members))
            return FileResponse(target, media_type="application/octet-stream",
                                filename=document.source.name, background=BackgroundTask(target.unlink, missing_ok=True))
        except BaseException:
            target.unlink(missing_ok=True)
            raise

    return router
