"""Bounded APKG scheduling reads using a disposable, read-only SQLite copy."""

from __future__ import annotations

import sqlite3
import stat
import zipfile
from collections.abc import Iterable
from contextlib import contextmanager
from hashlib import sha256
from itertools import islice
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from time import monotonic

from multilang.domain.content import canonical_content_hash
from multilang.domain.learning import (
    HistoryAlias,
    HistoryImport,
    HistoryLimits,
    MappedLearnerState,
)


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def bounded_apkg_collection(path: Path, *, limits: HistoryLimits | None = None):
    """Expose a bounded read-only connection, never a live collection or writable package."""
    limits = HistoryLimits.model_validate((limits or HistoryLimits()).model_dump())
    source = Path(path)
    if (
        source.suffix.casefold() != ".apkg"
        or source.is_symlink()
        or not source.is_file()
    ):
        raise ValueError(
            "only a local regular APKG package is supported; live collections are prohibited"
        )
    if source.stat().st_size > limits.max_archive_bytes:
        raise ValueError("APKG archive byte limit exceeded")
    started = monotonic()
    before = _hash_file(source)
    connection = None

    def deadline():
        if monotonic() - started > limits.max_seconds:
            raise ValueError("APKG processing time limit exceeded")

    try:
        with TemporaryDirectory(prefix="native-history-") as temporary:
            database = Path(temporary) / "collection.anki2"
            with zipfile.ZipFile(source) as archive:
                members = archive.infolist()
                if len(members) > limits.max_members or len(
                    {info.filename for info in members}
                ) != len(members):
                    raise ValueError("APKG member limit or duplicate archive member")
                total = 0
                for info in members:
                    deadline()
                    member = PurePosixPath(info.filename)
                    if (
                        not member.parts
                        or member.is_absolute()
                        or ".." in member.parts
                        or "\\" in info.filename
                        or "\x00" in info.filename
                        or ":" in member.parts[0]
                        or stat.S_ISLNK(info.external_attr >> 16)
                        or info.flag_bits & 1
                    ):
                        raise ValueError("unsafe APKG archive member")
                    if (
                        info.file_size > limits.max_member_bytes
                        or info.file_size / max(info.compress_size, 1)
                        > limits.max_compression_ratio
                    ):
                        raise ValueError("APKG decompression limit exceeded")
                    total += info.file_size
                if total > limits.max_total_uncompressed_bytes:
                    raise ValueError("APKG uncompressed byte limit exceeded")
                if "collection.anki2" not in archive.namelist():
                    raise ValueError(
                        "unsupported APKG format: bounded collection.anki2 required"
                    )
                copied = 0
                with (
                    archive.open("collection.anki2") as source_member,
                    database.open("xb") as output,
                ):
                    while chunk := source_member.read(65536):
                        deadline()
                        copied += len(chunk)
                        if copied > limits.max_member_bytes:
                            raise ValueError("APKG collection byte limit exceeded")
                        output.write(chunk)
            connection = sqlite3.connect(
                f"{database.as_uri()}?mode=ro&immutable=1", uri=True
            )
            connection.enable_load_extension(False)
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.setlimit(
                sqlite3.SQLITE_LIMIT_LENGTH, min(limits.max_member_bytes, 1024 * 1024)
            )
            connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 16384)
            connection.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 256)
            steps = 0

            def progress():
                nonlocal steps
                steps += 1000
                return int(
                    steps > limits.max_sqlite_operations
                    or monotonic() - started > limits.max_seconds
                )

            connection.set_progress_handler(progress, 1000)
            yield connection, before
            deadline()
    except (zipfile.BadZipFile, sqlite3.DatabaseError, OSError, RuntimeError) as exc:
        raise ValueError(
            "APKG could not be processed safely within configured limits"
        ) from exc
    finally:
        if connection is not None:
            connection.close()
    if _hash_file(source) != before:
        raise ValueError("APKG changed during read-only import")


def _require_tables(connection: sqlite3.Connection) -> None:
    required = {
        "notes": {"id", "guid", "mid"},
        "cards": {"id", "nid", "ord", "reps", "lapses", "ivl"},
        "revlog": {"id", "cid"},
    }
    tables = dict(
        connection.execute(
            "SELECT name,type FROM sqlite_master WHERE name IN ('notes','cards','revlog')"
        )
    )
    for table, columns in required.items():
        if tables.get(table) != "table":
            raise ValueError("unsupported Anki scheduling schema")
        # Names come from the fixed allowlist above, never from package content.
        existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if not columns <= existing:
            raise ValueError("unsupported Anki scheduling schema drift")


def read_anki_history(
    path: Path,
    *,
    aliases: Iterable[HistoryAlias],
    namespace: str,
    limits: HistoryLimits | None = None,
) -> HistoryImport:
    if not namespace.startswith("user:") or len(namespace) <= 5:
        raise ValueError("APKG history requires a private user namespace")
    limits = HistoryLimits.model_validate((limits or HistoryLimits()).model_dump())
    alias_list = tuple(islice(aliases, limits.max_cards + 1))
    if len(alias_list) > limits.max_cards:
        raise ValueError("APKG alias limit exceeded")
    mapping: dict[tuple[str, int, int], HistoryAlias] = {}
    for alias in alias_list:
        key = (alias.note_guid, alias.template_ordinal, alias.model_id)
        if key in mapping:
            raise ValueError("ambiguous duplicate history alias")
        mapping[key] = HistoryAlias.model_validate(alias.model_dump())
    states: dict[str, MappedLearnerState] = {}
    duplicate_semantics: set[str] = set()
    quarantined = 0
    with bounded_apkg_collection(path, limits=limits) as (connection, input_hash):
        _require_tables(connection)
        # Fixed read allowlist. No SQL from notes, templates, extensions or caller.
        allowed_actions = {
            sqlite3.SQLITE_SELECT,
            sqlite3.SQLITE_READ,
            sqlite3.SQLITE_FUNCTION,
        }
        connection.set_authorizer(
            lambda action, *_: (
                sqlite3.SQLITE_OK if action in allowed_actions else sqlite3.SQLITE_DENY
            )
        )
        card_count = connection.execute("SELECT count(*) FROM cards").fetchone()[0]
        review_count = connection.execute("SELECT count(*) FROM revlog").fetchone()[0]
        if card_count > limits.max_cards or review_count > limits.max_reviews:
            raise ValueError("APKG card/review count limit exceeded")
        note_count = connection.execute("SELECT count(*) FROM notes").fetchone()[0]
        if note_count > limits.max_cards:
            raise ValueError("APKG note count limit exceeded")
        for table in ("notes", "cards", "revlog"):
            # A forged schema can omit Anki's primary keys and amplify a join.
            # Verify the fixed key columns before aggregating any relationships.
            if (
                connection.execute(
                    f"SELECT 1 FROM {table} WHERE typeof(id) != 'integer' LIMIT 1"
                ).fetchone()
                or connection.execute(
                    f"SELECT 1 FROM {table} GROUP BY id HAVING count(*) > 1 LIMIT 1"
                ).fetchone()
            ):
                raise ValueError("APKG duplicate or invalid scheduling key")
        # Aggregate once; avoid one query per card and bound the in-memory result.
        reviews = {
            row[0]: (row[1], row[2])
            for row in connection.execute(
                "SELECT cid,count(*),max(id) FROM revlog GROUP BY cid"
            )
        }
        query = "SELECT c.id,n.guid,n.mid,c.ord,c.reps,c.lapses,c.ivl FROM cards c LEFT JOIN notes n ON n.id=c.nid ORDER BY c.id"
        for (
            card_id,
            guid,
            model_id,
            ordinal,
            repetitions,
            lapses,
            interval,
        ) in connection.execute(query):
            alias = mapping.get((guid, ordinal, model_id))
            if alias is None or alias.semantic_card_id in duplicate_semantics:
                quarantined += 1
                continue
            if alias.semantic_card_id in states:
                del states[alias.semantic_card_id]
                duplicate_semantics.add(alias.semantic_card_id)
                quarantined += 2
                continue
            try:
                counts, last_review = reviews.get(card_id, (0, None))
                states[alias.semantic_card_id] = MappedLearnerState(
                    semantic_card_id=alias.semantic_card_id,
                    parent_lexical_identity_id=alias.parent_lexical_identity_id,
                    repetitions=repetitions,
                    lapses=lapses,
                    interval_days=max(interval, 0),
                    review_count=counts,
                    last_review_ms=last_review,
                    mapping_evidence_sha256=alias.evidence_sha256,
                )
            except (ValueError, TypeError):
                quarantined += 1
    mapping_hash = canonical_content_hash(
        sorted(
            (alias.model_dump() for alias in alias_list),
            key=lambda row: (
                row["note_guid"],
                row["template_ordinal"],
                row["model_id"],
            ),
        )
    )
    return HistoryImport(
        namespace=namespace,
        input_sha256=input_hash,
        mapping_sha256=mapping_hash,
        states=tuple(states[key] for key in sorted(states)),
        quarantined_count=quarantined,
    )
