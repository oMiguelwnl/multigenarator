"""Review the operator's local copy of a completed genanki export."""

import getpass
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
from datetime import UTC, datetime
from functools import lru_cache
from hashlib import file_digest, sha1, sha256
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Annotated, BinaryIO, Literal
from uuid import UUID
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi import Path as PathParam
from fastapi.responses import FileResponse, Response
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from starlette.background import BackgroundTask

from multilang.domain.exporting import ExportArtifactFormat
from multilang.studio.approved_exports import write_approved_tables

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


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: str = Field(pattern=r"^[0-9a-f]{64}$")


class ApprovalReceipt(ApprovalRequest):
    productionId: UUID
    operator: str = Field(min_length=1)
    approvedAt: AwareDatetime
    snapshotSha256: str = Field(pattern=r"^[0-9a-f]{64}$")


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


def working_collection(package: Path | BinaryIO, directory: Path) -> Path:
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


@lru_cache(maxsize=64)
def _file_hash(path: Path, signature: tuple[int, ...]) -> str:
    # Completed packages and published snapshots are immutable in Studio.
    # Cache their digest across page reads, keyed by filesystem identity and version.
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def file_hash(path: Path) -> str:
    stat = path.stat()
    return _file_hash(path, (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))


def approval_receipts(directory: Path) -> list[Path]:
    return sorted((directory / "approvals").glob("[0-9]*/receipt.json"), reverse=True)


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

    @staticmethod
    def reserve_edit(db: sqlite3.Connection) -> None:
        try:
            db.execute("begin immediate")
        except sqlite3.OperationalError as exc:
            if exc.sqlite_errorcode == sqlite3.SQLITE_BUSY:
                raise HTTPException(409, "Outra sessão está gravando a revisão. Tente novamente.") from exc
            raise

    def edit(self, nid: int, revision: str, replacements: dict[str, str], image: bytes | None = None):
        with closing(self.connect()) as db, db:
            self.reserve_edit(db)
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

    def write_package(self, target: Path, *, for_approval: bool = False) -> None:
        with TemporaryDirectory() as temporary, ZipFile(self.source) as original:
            snapshot = Path(temporary) / "collection.anki2"
            with closing(self.connect()) as source, closing(sqlite3.connect(snapshot)) as db:
                source.backup(db)
                images = set()
                required_media = set()
                query = "select flds from notes" if for_approval else "select flds from notes where flds like '%studio-%'"
                for (fields,) in db.execute(query):
                    names = {html.unescape(name) for name in IMAGE.findall(fields)}
                    images.update(name for name in names if NEW_IMAGE.fullmatch(name))
                    if for_approval:
                        required_media.update(names)
                        required_media.update(SOUND.findall(fields))
            with ZipFile(target, "w") as archive:
                members = manifest(original)
                if for_approval and (
                    set(members).difference(original.namelist())
                    or required_media.difference(members.values(), images)
                ):
                    raise HTTPException(409, "Há mídias ausentes nesta revisão.")
                if for_approval:
                    for key, filename in members.items():
                        if filename in images:
                            with original.open(key) as stream:
                                digest = file_digest(stream, "sha256").hexdigest()
                            if filename != f"studio-{digest}.png":
                                raise HTTPException(409, "O pacote contém uma imagem diferente da revisada.")
                for entry in original.infolist():
                    if entry.filename not in {"collection.anki2", "media"}:
                        with original.open(entry) as src, archive.open(entry, "w") as dst:
                            shutil.copyfileobj(src, dst)
                archive.write(snapshot, "collection.anki2")
                next_key = max(map(int, members), default=-1) + 1
                for filename in sorted(images.difference(members.values())):
                    key = str(next_key)
                    path = self.directory / filename
                    if not path.is_file():
                        raise HTTPException(409, "Há imagens ausentes nesta revisão.")
                    image = path.read_bytes()
                    if filename != f"studio-{sha256(image).hexdigest()}.png":
                        raise HTTPException(409, "A imagem revisada perdeu a integridade.")
                    archive.writestr(key, image)
                    members[key] = filename
                    next_key += 1
                archive.writestr("media", json.dumps(members))

    def revision(self, db: sqlite3.Connection) -> str:
        # Read the complete SQLite image through its own connection: this also
        # includes committed WAL pages and the models, tags and scheduling data.
        collection_hash = sha256(db.serialize()).hexdigest()
        version = f"{self.directory.name}:{collection_hash}:{file_hash(self.source)}"
        return sha256(version.encode()).hexdigest()

    def approval_status(self, db: sqlite3.Connection) -> dict:
        revision = self.revision(db)
        receipts = approval_receipts(self.directory)
        latest = None
        state = "pending"
        if receipts:
            latest = json.loads(receipts[0].read_text(encoding="utf-8"))
            snapshot = receipts[0].with_name("snapshot.apkg")
            if not snapshot.is_file() or file_hash(snapshot) != latest["snapshotSha256"]:
                raise HTTPException(409, "O snapshot aprovado está ausente ou danificado.")
            state = "approved" if revision == latest["revision"] else "needs_approval"
        return {"revision": revision, "state": state, "latest": latest}

    def approve(self, expected: str) -> dict:
        with closing(self.connect()) as guard, guard:
            # All Studio editors acquire this same SQLite writer reservation.
            # A separate read connection can back up the committed collection
            # while the reservation prevents another edit or approval.
            self.reserve_edit(guard)
            source_hash = file_hash(self.source)
            status = self.approval_status(guard)
            if status["revision"] != expected:
                raise HTTPException(409, "A produção mudou. Recarregue as notas antes de aprovar.")
            if status["state"] == "approved":
                return status
            if not guard.execute("select 1 from notes limit 1").fetchone():
                raise HTTPException(409, "A produção não contém notas para aprovar.")
            approvals = self.directory / "approvals"
            approvals.mkdir(exist_ok=True)
            sequence = len(approval_receipts(self.directory)) + 1
            with TemporaryDirectory(dir=approvals, prefix=".pending-") as tmp:
                staging = Path(tmp)
                snapshot = staging / "snapshot.apkg"
                self.write_package(snapshot, for_approval=True)
                if file_hash(self.source) != source_hash:
                    raise HTTPException(409, "O pacote de origem mudou durante a aprovação.")
                receipt = {
                    "productionId": self.directory.name,
                    "revision": expected,
                    "operator": getpass.getuser(),
                    "approvedAt": datetime.now(UTC).isoformat(),
                    "snapshotSha256": file_hash(snapshot),
                }
                (staging / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
                # Readers see either the entire decision and its bytes or neither.
                staging.rename(approvals / f"{sequence:012d}")
            return {"revision": expected, "state": "approved", "latest": receipt}


def create_results_router(resolve_package: Callable[[UUID], Path], *, review_root: Path):
    router = APIRouter(prefix="/studio-api/productions/{production_id}")

    def review(production_id):
        return Review(resolve_package(production_id), review_root / str(production_id))

    @router.get("/result")
    def result(production_id: UUID, offset: int = Query(0, ge=0, le=2**31),
               limit: int = Query(25, ge=1, le=100), q: str = Query("", max_length=200)):
        document = review(production_id)
        with closing(document.connect()) as db:
            db.execute("begin")
            db.create_function("contains_text", 1, lambda raw: q.casefold() in plain(raw).casefold())
            where = " where contains_text(flds)" if q.strip() else ""
            total = db.execute("select count(*) from notes" + where).fetchone()[0]
            rows = db.execute("select id,mid,flds,mod from notes" + where + " order by id limit ? offset ?",
                              (limit, offset))
            return {"total": total, "notes": document.describe(db, rows),
                    "approval": document.approval_status(db)}

    @router.get("/approvals")
    def approvals(production_id: UUID):
        receipts = approval_receipts(review_root / str(production_id))
        if not receipts:
            resolve_package(production_id)
        return [json.loads(path.read_text(encoding="utf-8")) for path in receipts]

    def export_directory():
        with TemporaryDirectory() as temporary:
            yield Path(temporary)

    @router.get("/approvals/{digest}/export/{fmt}")
    def approved_export(production_id: UUID, digest: Annotated[str, PathParam(pattern=r"^[0-9a-f]{64}$")],
                        fmt: Literal["csv", "tsv"], directory: Annotated[Path, Depends(export_directory)]):
        for receipt_path in approval_receipts(review_root / str(production_id)):
            try:
                receipt = ApprovalReceipt.model_validate_json(receipt_path.read_bytes())
                if receipt.productionId != production_id or receipt.snapshotSha256 != digest:
                    continue
                with receipt_path.with_name("snapshot.apkg").open("rb") as snapshot:
                    if file_digest(snapshot, "sha256").hexdigest() != digest:
                        raise ValueError("Snapshot digest mismatch")
                    snapshot.seek(0)
                    collection = working_collection(snapshot, directory)
                target = write_approved_tables(collection, ExportArtifactFormat(fmt), production_id, digest)
            except (FileNotFoundError, BadZipFile, sqlite3.DatabaseError, KeyError,
                    IndexError, TypeError, ValueError) as exc:
                raise HTTPException(409, "O snapshot aprovado está ausente ou danificado.") from exc
            media_types = {".csv": "text/csv", ".tsv": "text/tab-separated-values", ".zip": "application/zip"}
            return FileResponse(target, filename=target.name, media_type=media_types[target.suffix])
        raise HTTPException(404, "Aprovação não encontrada para esta produção.")

    @router.post("/approvals")
    def approve(production_id: UUID, payload: ApprovalRequest):
        return review(production_id).approve(payload.revision)

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
            document.write_package(target)
            return FileResponse(target, media_type="application/octet-stream",
                                filename=document.source.name, background=BackgroundTask(target.unlink, missing_ok=True))
        except BaseException:
            target.unlink(missing_ok=True)
            raise

    return router
