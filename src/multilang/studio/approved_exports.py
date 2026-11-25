"""Write tabular downloads from an extracted, verified approval snapshot."""

import json
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from io import TextIOWrapper
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from typing import TextIO
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.exporting.tabular import tabular_writer


def _write_model(stream: TextIO, fmt: ExportArtifactFormat, model: dict, rows: Iterable[tuple[int, str]]):
    fields = sorted(model["flds"], key=itemgetter("ord"))
    if [field["ord"] for field in fields] != list(range(len(fields))):
        raise ValueError("Invalid field ordinals")
    writer = tabular_writer(stream, fmt)
    writer.writerow([field["name"] for field in fields])
    for _, raw in rows:
        values = raw.split("\x1f")
        if len(values) != len(fields):
            raise ValueError("Note does not match approved model")
        writer.writerow(values)


def write_approved_tables(collection: Path, fmt: ExportArtifactFormat, production: UUID, digest: str) -> Path:
    stem = f"{production}-{digest}"
    with closing(sqlite3.connect(f"{collection.as_uri()}?mode=ro&immutable=1", uri=True)) as db:
        db.execute("pragma trusted_schema=off")
        models = json.loads(db.execute("select models from col").fetchone()[0])
        model_count, = db.execute("select count(distinct mid) from notes").fetchone()
        groups = groupby(db.execute("select mid, flds from notes order by mid, id"), key=itemgetter(0))
        if model_count == 0:
            raise ValueError("Empty approval")
        if model_count == 1:
            mid, rows = next(groups)
            target = collection.with_name(f"{stem}.{fmt.value}")
            with target.open("w", encoding="utf-8", newline="") as stream:
                _write_model(stream, fmt, models[str(mid)], rows)
            return target

        target = collection.with_name(f"{stem}-{fmt.value}.zip")
        index = []
        with ZipFile(target, "w") as archive:
            for mid, rows in groups:
                model = models[str(mid)]
                filename = f"model-{mid:d}.{fmt.value}"
                # Fixed ZIP timestamps keep repeated downloads byte-for-byte identical.
                entry = ZipInfo(filename)
                entry.compress_type = ZIP_DEFLATED
                with archive.open(entry, "w") as data, TextIOWrapper(data, encoding="utf-8", newline="") as stream:
                    _write_model(stream, fmt, model, rows)
                index.append({"id": str(mid), "name": model["name"], "file": filename})
            manifest = {"productionId": str(production), "snapshotSha256": digest, "models": index}
            archive.writestr(ZipInfo("manifest.json"), json.dumps(manifest, ensure_ascii=False))
        return target
