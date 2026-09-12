"""Explicit snapshot, rehearsal and confirmed native migration operations.

The running legacy application never upgrades native tables implicitly. A live
apply is bound to the database, backup, target, topology and rehearsal hashes.
"""

import json
import os
import re
import sqlite3
import subprocess
from collections.abc import Callable
from contextlib import nullcontext
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Literal

from alembic.config import Config
from pydantic import Field, computed_field
from sqlalchemy import MetaData, create_engine, inspect, select
from sqlalchemy.engine import Connection, Engine

from alembic import command
from multilang.domain.anki_semantics import TopologyDecision
from multilang.domain.events import canonical_hash
from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.domain.migration import MigrationContract, MigrationPreview

__all__ = [
    "BackupFile",
    "BackupManifest",
    "BackupService",
    "LegacyAdoptionPreview",
    "MigrationContract",
    "MigrationPreview",
    "MigrationService",
    "RollbackPreview",
    "SchemaAuthorization",
    "database_fingerprint",
    "file_sha256",
    "native_alembic_config",
    "require_schema_authorization",
]

LEGACY_REVISION = "20260828_19"
NATIVE_REVISION = "20260912_20"


def file_sha256(path: Path) -> str:
    result = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def database_fingerprint(
    engine: Engine | Connection,
    *,
    exclude_native: bool = False,
    exclude_tables: frozenset[str] = frozenset(),
) -> str:
    """Hash typed data and schema without credentials, paths or row ordering."""
    metadata = MetaData()
    with nullcontext(engine) if isinstance(engine, Connection) else engine.connect() as connection:
        metadata.reflect(connection)
        if exclude_native:
            from multilang.db import native_models as _native  # noqa: F401
            from multilang.db import task_models as _tasks  # noqa: F401
            from multilang.db.base import Base

            names = {
                table.name for table in Base.metadata.tables.values() if table.info.get("native")
            }
        else:
            names = set()
        digest = {}
        for name, table in sorted(metadata.tables.items()):
            if (
                name in names
                or name in exclude_tables
                or (exclude_native and name == "alembic_version")
            ):
                continue
            rows = []
            for row in connection.execute(select(table)).mappings():
                serial = {
                    key: (value.hex() if isinstance(value, bytes) else value)
                    for key, value in row.items()
                }
                rows.append(
                    sha256(
                        json.dumps(serial, sort_keys=True, ensure_ascii=False, default=str).encode()
                    ).hexdigest()
                )
            digest[name] = {
                "columns": [column.name for column in table.columns],
                "rows": sorted(rows),
            }
        schema_hash = _schema_fingerprint(connection, names=set(digest))
    return canonical_hash({"tables": digest, "schema": schema_hash})


def native_alembic_config(engine: Engine) -> Config:
    from multilang.db.provisioning import find_project_root

    root = find_project_root()
    if root is None:
        from importlib.resources import files

        resource = files("multilang").joinpath("migration_resources")
        root = Path(str(resource))
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option(
        "sqlalchemy.url",
        engine.url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    config.attributes["explicit_database_url"] = True
    return config


class BackupFile(NativeContract):
    relative_path: str
    sha256: Sha256
    byte_size: int = Field(ge=0)


class BackupManifest(NativeContract):
    backend: Literal["sqlite", "postgresql"]
    artifact_path: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    database_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    legacy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_locator_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    files: tuple[BackupFile, ...] = ()

    @computed_field
    @property
    def files_sha256(self) -> str:
        return canonical_hash([item.model_dump(mode="json") for item in self.files])

    @computed_field
    @property
    def snapshot_sha256(self) -> str:
        if not self.files:
            return self.artifact_sha256
        return canonical_hash({"database": self.artifact_sha256, "files": self.files_sha256})


class RollbackPreview(NativeContract):
    migration_id: Sha256
    source_sha256: Sha256
    target_sha256: Sha256
    backup_sha256: Sha256
    source_locator_sha256: Sha256

    @property
    def confirmation_sha256(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))


class LegacyAdoptionPreview(NativeContract):
    source_sha256: Sha256
    schema_sha256: Sha256
    source_locator_sha256: Sha256
    backup_sha256: Sha256
    target_revision: Literal["20260828_19"] = LEGACY_REVISION
    baseline: Literal["legacy-sqlalchemy-create-all"] = "legacy-sqlalchemy-create-all"

    @property
    def confirmation_sha256(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))


@dataclass(frozen=True)
class SchemaAuthorization:
    """Internal capability passed only through Alembic's explicit Config object."""

    source_locator_sha256: str
    backup_sha256: str
    mode: Literal["isolated_rehearsal", "confirmed_apply"]
    target_revision: str = NATIVE_REVISION


def _locator(engine: Engine) -> str:
    if engine.dialect.name == "sqlite" and engine.url.database not in {
        None,
        "",
        ":memory:",
    }:
        return canonical_hash(
            {"backend": "sqlite", "database": str(Path(engine.url.database).resolve())}
        )
    if engine.dialect.name == "postgresql":
        return canonical_hash(
            {
                "backend": "postgresql",
                "host": (engine.url.host or "localhost").lower(),
                "port": engine.url.port or 5432,
                "database": engine.url.database or "postgres",
            }
        )
    return canonical_hash(engine.url.render_as_string(hide_password=True))


def _safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or "\\" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ValueError("backup file path must be a safe relative path")
    return str(path)


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False, mode=0o700)


def _copy_bounded(source: Path, destination: Path, limit: int) -> BackupFile:
    if source.is_symlink() or not source.is_file():
        raise ValueError("backup source must be a regular file")
    if source.stat().st_size > limit:
        raise ValueError("backup file byte limit exceeded")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    digest = sha256()
    size = 0
    descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream, destination.open("xb") as output:
        destination.chmod(0o600)
        while chunk := stream.read(min(1024 * 1024, limit - size + 1)):
            size += len(chunk)
            if size > limit:
                raise ValueError("backup file byte limit exceeded")
            digest.update(chunk)
            output.write(chunk)
    if source.stat().st_size != size or file_sha256(source) != digest.hexdigest():
        raise ValueError("backup source file changed while copying")
    return BackupFile(relative_path=destination.name, sha256=digest.hexdigest(), byte_size=size)


@dataclass(frozen=True)
class _SqlToken:
    kind: Literal["word", "string", "symbol"]
    value: str
    start: int
    end: int


def _quoted_sql_token_end(value: str, start: int, quote: str, *, escapes: bool = False) -> int:
    index = start + 1
    while index < len(value):
        if escapes and value[index] == "\\":
            index = min(index + 2, len(value))
            continue
        if value[index] != quote:
            index += 1
            continue
        if index + 1 < len(value) and value[index + 1] == quote:
            index += 2
            continue
        return index + 1
    return len(value)


def _postgres_sql_tokens(value: str) -> tuple[_SqlToken, ...]:
    """Tokenize only the SQL forms needed for safe CHECK normalization."""
    tokens = []
    index = 0
    while index < len(value):
        character = value[index]
        if character.isspace():
            index += 1
            continue
        start = index
        if value.startswith("--", index):
            newline = value.find("\n", index + 2)
            index = len(value) if newline == -1 else newline
            tokens.append(_SqlToken("symbol", value[start:index], start, index))
            continue
        if value.startswith("/*", index):
            index += 2
            depth = 1
            while index < len(value) and depth:
                if value.startswith("/*", index):
                    depth += 1
                    index += 2
                elif value.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            tokens.append(_SqlToken("symbol", value[start:index], start, index))
            continue
        if character == '"':
            index = _quoted_sql_token_end(value, index, '"')
            tokens.append(_SqlToken("symbol", value[start:index], start, index))
            continue
        if character == "$":
            delimiter_end = index + 1
            if delimiter_end < len(value) and (
                value[delimiter_end].isalpha() or value[delimiter_end] in {"_", "$"}
            ):
                while delimiter_end < len(value) and (
                    value[delimiter_end].isalnum() or value[delimiter_end] == "_"
                ):
                    delimiter_end += 1
                if delimiter_end < len(value) and value[delimiter_end] == "$":
                    delimiter = value[index : delimiter_end + 1]
                    close = value.find(delimiter, delimiter_end + 1)
                    index = len(value) if close == -1 else close + len(delimiter)
                    tokens.append(_SqlToken("symbol", value[start:index], start, index))
                    continue
        if (
            character in {"E", "e", "B", "b", "X", "x", "N", "n"}
            and index + 1 < len(value)
            and value[index + 1] == "'"
        ):
            index = _quoted_sql_token_end(
                value,
                index + 1,
                "'",
                escapes=character in {"E", "e"},
            )
            tokens.append(_SqlToken("symbol", value[start:index], start, index))
            continue
        if character in {"U", "u"} and value.startswith("&'", index + 1):
            index = _quoted_sql_token_end(value, index + 2, "'")
            tokens.append(_SqlToken("symbol", value[start:index], start, index))
            continue
        if character == "'":
            index = _quoted_sql_token_end(value, index, "'")
            closed = index > start + 1 and value[index - 1 : index] == "'"
            tokens.append(
                _SqlToken("string" if closed else "symbol", value[start:index], start, index)
            )
            continue
        if character.isalpha() or character == "_":
            index += 1
            while index < len(value) and (value[index].isalnum() or value[index] in {"_", "$"}):
                index += 1
            tokens.append(_SqlToken("word", value[start:index], start, index))
            continue
        if value.startswith("::", index):
            index += 2
        else:
            index += 1
        tokens.append(_SqlToken("symbol", value[start:index], start, index))
    return tuple(tokens)


def _token_is(token: _SqlToken, value: str) -> bool:
    if token.kind == "word":
        return token.value.casefold() == value.casefold()
    return token.value == value


def _postgres_check_array_cast_edits(
    tokens: tuple[_SqlToken, ...], start: int
) -> tuple[int, tuple[tuple[int, int, str], ...]] | None:
    """Match the exact pg_dump varchar-literal-array cast relocation."""
    if start + 4 >= len(tokens) or not (
        _token_is(tokens[start], "ANY")
        and _token_is(tokens[start + 1], "(")
        and _token_is(tokens[start + 2], "ARRAY")
        and _token_is(tokens[start + 3], "[")
    ):
        return None

    index = start + 4
    element_cast_ends = []
    element_has_text_cast = []
    while index < len(tokens):
        if tokens[index].kind != "string":
            return None
        index += 1
        if index + 2 >= len(tokens) or not (
            _token_is(tokens[index], "::")
            and _token_is(tokens[index + 1], "character")
            and _token_is(tokens[index + 2], "varying")
        ):
            return None
        index += 3
        element_cast_ends.append(tokens[index - 1].end)
        has_text_cast = (
            index + 1 < len(tokens)
            and _token_is(tokens[index], "::")
            and _token_is(tokens[index + 1], "text")
        )
        element_has_text_cast.append(has_text_cast)
        if has_text_cast:
            index += 2
        if index >= len(tokens):
            return None
        if _token_is(tokens[index], ","):
            index += 1
            continue
        if _token_is(tokens[index], "]"):
            index += 1
            break
        return None

    if all(element_has_text_cast):
        if index < len(tokens) and _token_is(tokens[index], ")"):
            return index + 1, ()
        return None
    if any(element_has_text_cast) or index + 3 >= len(tokens):
        return None
    if not (
        _token_is(tokens[index], "::")
        and _token_is(tokens[index + 1], "text")
        and _token_is(tokens[index + 2], "[")
        and _token_is(tokens[index + 3], "]")
        and index + 4 < len(tokens)
        and _token_is(tokens[index + 4], ")")
    ):
        return None

    edits = [(position, position, "::text") for position in element_cast_ends]
    edits.append((tokens[index].start, tokens[index + 3].end, ""))
    return index + 5, tuple(edits)


def _normalize_postgresql_check_sqltext(value: str) -> str:
    """Normalize one proven PostgreSQL dump/restore CHECK rewrite."""
    tokens = _postgres_sql_tokens(value)
    edits = []
    index = 0
    while index < len(tokens):
        match = _postgres_check_array_cast_edits(tokens, index)
        if match is None:
            index += 1
            continue
        index, match_edits = match
        edits.extend(match_edits)
    if not edits:
        return value
    pieces = []
    cursor = 0
    for start, end, replacement in sorted(edits):
        pieces.append(value[cursor:start])
        pieces.append(replacement)
        cursor = end
    pieces.append(value[cursor:])
    return "".join(pieces)


def _check_constraints_for_fingerprint(inspector, name: str) -> list[dict]:
    checks = inspector.get_check_constraints(name)
    if inspector.dialect.name != "postgresql":
        return checks
    return [
        {
            **check,
            "sqltext": _normalize_postgresql_check_sqltext(check["sqltext"]),
        }
        if isinstance(check.get("sqltext"), str)
        else check
        for check in checks
    ]


def _schema_fingerprint(engine: Engine | Connection, *, names: set[str] | None = None) -> str:
    inspector = inspect(engine)
    schema = {}
    for name in sorted(inspector.get_table_names()):
        if names is not None and name not in names:
            continue
        schema[name] = {
            "columns": [
                {
                    "name": c["name"],
                    "type": str(c["type"]),
                    "nullable": c["nullable"],
                    "default": c["default"],
                }
                for c in inspector.get_columns(name)
            ],
            "primary": inspector.get_pk_constraint(name).get("constrained_columns", []),
            "indexes": sorted(inspector.get_indexes(name), key=lambda item: item.get("name", "")),
            "unique": sorted(
                inspector.get_unique_constraints(name),
                key=lambda item: str(item.get("name", "")),
            ),
            "foreign_keys": sorted(
                inspector.get_foreign_keys(name),
                key=lambda item: str(item.get("constrained_columns", [])),
            ),
            "checks": sorted(
                _check_constraints_for_fingerprint(inspector, name),
                key=lambda item: str(item.get("name", "")),
            ),
        }
    return canonical_hash(schema)


def require_schema_authorization(config: Config, connection) -> None:
    authority = config.attributes.get("native_authorization")
    if (
        not isinstance(authority, SchemaAuthorization)
        or authority.target_revision != NATIVE_REVISION
    ):
        raise ValueError("native schema requires preview, backup and explicit authorization")
    if authority.source_locator_sha256 != _locator(connection.engine):
        raise ValueError("native schema authorization database mismatch")


class BackupService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def snapshot(
        self,
        destination: Path,
        *,
        files: dict[str, Path] | None = None,
        max_file_bytes: int = 64 * 1024 * 1024,
        max_total_bytes: int = 512 * 1024 * 1024,
        max_files: int = 10_000,
    ) -> BackupManifest:
        destination = Path(destination)
        if min(max_file_bytes, max_total_bytes, max_files) < 1 or len(files or {}) > max_files:
            raise ValueError("backup file limit exceeded")
        declared = {_safe_relative(key): Path(value) for key, value in (files or {}).items()}
        _private_directory(destination)
        before = database_fingerprint(self.engine)
        legacy = database_fingerprint(self.engine, exclude_native=True)
        backend = self.engine.dialect.name
        artifact = destination / ("database.sqlite3" if backend == "sqlite" else "database.dump")
        if backend == "sqlite":
            source = self.engine.raw_connection()
            try:
                with sqlite3.connect(artifact) as target:
                    source.driver_connection.backup(target)
            finally:
                source.close()
        elif backend == "postgresql":
            self._pg_tool("pg_dump", ["--format=custom", "--no-owner", "--file", str(artifact)])
        else:
            raise ValueError("unsupported backup backend")
        artifact.chmod(0o600)
        if database_fingerprint(self.engine) != before:
            raise ValueError("database drift during snapshot; retry from a quiet baseline")
        copied = []
        total = 0
        for name, path in sorted(declared.items()):
            item = _copy_bounded(
                path,
                destination / "files" / name,
                min(max_file_bytes, max_total_bytes - total),
            )
            total += item.byte_size
            copied.append(item.model_copy(update={"relative_path": name}))
        backup = BackupManifest(
            backend=backend,
            artifact_path=str(artifact.resolve()),
            artifact_sha256=file_sha256(artifact),
            database_sha256=before,
            legacy_sha256=legacy,
            source_locator_sha256=_locator(self.engine),
            files=tuple(copied),
        )
        self.verify(backup)
        manifest = destination / "manifest.json"
        manifest.write_text(backup.model_dump_json(indent=2), encoding="utf-8")
        manifest.chmod(0o600)
        return backup

    def _pg_tool(self, executable: str, args: list[str]) -> None:
        if executable not in {"pg_dump", "pg_restore"}:
            raise ValueError("unsupported PostgreSQL backup tool")
        url = self.engine.url
        host, user, database = (
            url.host or "localhost",
            url.username or "postgres",
            url.database or "postgres",
        )
        if (
            not re.fullmatch(r"[A-Za-z0-9_.:-]+", host)
            or host.startswith("-")
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", user)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", database)
        ):
            raise ValueError("PostgreSQL backup connection fields must be explicit identifiers")
        environment = {key: value for key, value in os.environ.items() if not key.startswith("PG")}
        environment["PGCONNECT_TIMEOUT"] = "15"
        if url.password:
            environment["PGPASSWORD"] = url.password
        for key in ("sslmode", "sslrootcert", "sslcert", "sslkey"):
            if key in url.query:
                environment["PG" + key.upper()] = str(url.query[key])
        command_args = [
            executable,
            *args,
            "--no-password",
            f"--host={host}",
            f"--port={url.port or 5432}",
            f"--username={user}",
            f"--dbname={database}",
        ]
        # Never pass a DSN or password on argv or return stderr with connection details.
        try:
            subprocess.run(
                command_args,
                env=environment,
                check=True,
                capture_output=True,
                timeout=600,
            )
        except (OSError, subprocess.SubprocessError):
            raise ValueError("database backup/restore tool failed") from None

    def verify(self, backup: BackupManifest) -> bool:
        backup = BackupManifest.model_validate(backup.model_dump(mode="json"))
        path = Path(backup.artifact_path)
        if not path.is_file() or path.is_symlink() or file_sha256(path) != backup.artifact_sha256:
            raise ValueError("backup artifact integrity failed")
        if backup.backend == "sqlite":
            with sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True) as connection:
                if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
                    raise ValueError("backup SQLite integrity failed")
            clone = create_engine(f"sqlite:///{path}")
            try:
                if database_fingerprint(clone) != backup.database_sha256:
                    raise ValueError("backup data fingerprint failed")
            finally:
                clone.dispose()
        else:
            try:
                subprocess.run(
                    ["pg_restore", "--list", str(path)],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
            except (OSError, subprocess.SubprocessError):
                raise ValueError("backup archive validation failed") from None
        root = path.parent / "files"
        seen = set()
        for item in backup.files:
            relative = _safe_relative(item.relative_path)
            if relative in seen:
                raise ValueError("duplicate backup file")
            seen.add(relative)
            candidate = root / relative
            if (
                not candidate.is_file()
                or candidate.is_symlink()
                or not candidate.resolve().is_relative_to(root.resolve())
                or candidate.stat().st_size != item.byte_size
                or file_sha256(candidate) != item.sha256
            ):
                raise ValueError("backup file integrity failed")
        return True

    def restore_to(
        self,
        backup: BackupManifest,
        target: Engine,
        *,
        files_destination: Path | None = None,
    ) -> None:
        self.verify(backup)
        if _locator(target) == backup.source_locator_sha256:
            raise ValueError("restore requires an isolated target; source cannot be overwritten")
        if inspect(target).get_table_names():
            raise ValueError("restore target must be empty")
        if target.dialect.name != backup.backend:
            raise ValueError("backup backend mismatch")
        if backup.files and files_destination is None:
            raise ValueError("backup files require an isolated files_destination")
        if files_destination is not None and Path(files_destination).exists():
            raise ValueError("files restore target must be new and isolated")
        if backup.backend == "sqlite":
            raw = target.raw_connection()
            try:
                with sqlite3.connect(
                    f"{Path(backup.artifact_path).as_uri()}?mode=ro", uri=True
                ) as source:
                    source.backup(raw.driver_connection)
            finally:
                raw.close()
        else:
            BackupService(target)._pg_tool(
                "pg_restore", ["--no-owner", "--exit-on-error", backup.artifact_path]
            )
        if database_fingerprint(target) != backup.database_sha256:
            raise ValueError("restored database fingerprint mismatch")
        if backup.files:
            root = Path(files_destination)
            _private_directory(root)
            source_root = Path(backup.artifact_path).parent / "files"
            for item in backup.files:
                copied = _copy_bounded(
                    source_root / _safe_relative(item.relative_path),
                    root / item.relative_path,
                    item.byte_size,
                )
                if copied.sha256 != item.sha256 or copied.byte_size != item.byte_size:
                    raise ValueError("restored file fingerprint mismatch")


class MigrationService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def preview(
        self,
        backup: BackupManifest,
        *,
        topology: TopologyDecision | None = None,
        rehearsal: dict | None = None,
    ) -> MigrationPreview:
        BackupService(self.engine).verify(backup)
        if (
            backup.source_locator_sha256 != _locator(self.engine)
            or database_fingerprint(self.engine) != backup.database_sha256
        ):
            raise ValueError("source database drift invalidates preview")
        return self._preview_contract(backup, topology=topology, rehearsal=rehearsal)

    def _preview_contract(
        self,
        backup: BackupManifest,
        *,
        topology: TopologyDecision | None,
        rehearsal: dict | None,
    ) -> MigrationPreview:
        migration_file = (
            Path(native_alembic_config(self.engine).get_main_option("script_location"))
            / "versions"
            / "20260912_20_native_architecture.py"
        )
        target = canonical_hash(
            {"revision": NATIVE_REVISION, "migration": file_sha256(migration_file)}
        )
        return MigrationPreview(
            source_sha256=backup.database_sha256,
            target_sha256=target,
            backup_sha256=backup.snapshot_sha256,
            source_locator_sha256=backup.source_locator_sha256,
            topology_sha256=canonical_hash(topology.model_dump(mode="json")) if topology else None,
            rehearsal_sha256=canonical_hash(rehearsal) if rehearsal else None,
        )

    def rehearse(
        self,
        backup: BackupManifest,
        clone_path: Path | None = None,
        *,
        clone_engine: Engine | None = None,
    ) -> dict:
        if clone_engine is None:
            if clone_path is None or Path(clone_path).exists():
                raise ValueError("rehearsal requires a new isolated clone path")
            clone = create_engine(f"sqlite:///{Path(clone_path).resolve()}")
        else:
            clone = clone_engine
        try:
            files_target = (
                Path(backup.artifact_path).parent.parent / f"rehearsal-files-{os.urandom(8).hex()}"
                if backup.files
                else None
            )
            BackupService(self.engine).restore_to(backup, clone, files_destination=files_target)
            config = native_alembic_config(clone)
            config.attributes["native_authorization"] = SchemaAuthorization(
                _locator(clone), backup.snapshot_sha256, "isolated_rehearsal"
            )
            command.upgrade(config, NATIVE_REVISION)
            preserved = database_fingerprint(clone, exclude_native=True) == backup.legacy_sha256
            upgraded = "lexical_identities" in inspect(clone).get_table_names()
            command.downgrade(config, LEGACY_REVISION)
            rollback = database_fingerprint(clone) == backup.database_sha256
            if not (preserved and upgraded and rollback):
                raise ValueError("migration rehearsal parity failed")
            result = {
                "source_sha256": backup.database_sha256,
                "backup_sha256": backup.snapshot_sha256,
                "target_revision": NATIVE_REVISION,
                "upgrade_passed": upgraded,
                "rollback_passed": rollback,
                "legacy_rows_preserved": preserved,
                "mode": "isolated-rehearsal",
            }
            return result
        finally:
            if clone_engine is None:
                clone.dispose()

    def apply(
        self,
        preview: MigrationPreview,
        backup: BackupManifest,
        *,
        confirmation_sha256: str,
        topology: TopologyDecision,
        topology_verifier: Callable[[TopologyDecision], bool],
        rehearsal: dict,
        actor: str,
    ) -> dict:
        topology.require_verified(topology_verifier)
        BackupService(self.engine).verify(backup)
        if backup.source_locator_sha256 != _locator(self.engine):
            raise ValueError("migration source locator mismatch")
        expected = self._preview_contract(backup, topology=topology, rehearsal=rehearsal)
        if preview != expected or confirmation_sha256 != expected.confirmation_sha256:
            raise ValueError("migration confirmation or target drift")
        if (
            preview.unresolved_count
            or rehearsal.get("source_sha256") != preview.source_sha256
            or rehearsal.get("backup_sha256") != preview.backup_sha256
            or not all(
                rehearsal.get(key)
                for key in (
                    "upgrade_passed",
                    "rollback_passed",
                    "legacy_rows_preserved",
                )
            )
        ):
            raise ValueError("valid current rehearsal required")
        completed = {
            "migration_id": preview.confirmation_sha256,
            "status": "completed",
            "legacy_preserved": True,
        }
        from multilang.db.native_models import MigrationJournalRecord

        if "migration_journal" in inspect(self.engine).get_table_names():
            with self.engine.connect() as connection:
                previous = (
                    connection.execute(
                        select(MigrationJournalRecord.__table__).where(
                            MigrationJournalRecord.id == preview.confirmation_sha256
                        )
                    )
                    .mappings()
                    .first()
                )
                if (
                    previous is None
                    or previous["status"] != "completed"
                    or previous["payload"].get("preview") != preview.model_dump(mode="json")
                ):
                    raise ValueError(
                        "existing native schema has no matching completed migration journal"
                    )
                self._postflight(connection, backup)
                if not self._current_native_schema(connection):
                    raise ValueError("completed migration schema drift")
            return completed
        if database_fingerprint(self.engine) != backup.database_sha256:
            raise ValueError("source database drift invalidates apply")
        config = native_alembic_config(self.engine)
        config.attributes["native_authorization"] = SchemaAuthorization(
            _locator(self.engine), backup.snapshot_sha256, "confirmed_apply"
        )
        # PostgreSQL wraps DDL and facts in a transaction. SQLite explicitly begins
        # DDL transactions; its default driver otherwise commits schema implicitly.
        with self.engine.connect() as connection:
            if self.engine.dialect.name == "sqlite":
                connection.exec_driver_sql("BEGIN IMMEDIATE")
            else:
                connection.begin()
            try:
                if database_fingerprint(connection) != backup.database_sha256:
                    raise ValueError("source database drift before migration transaction")
                config.attributes["connection"] = connection
                command.upgrade(config, NATIVE_REVISION)
                from sqlalchemy.orm import Session

                from multilang.domain.events import MigrationCompleted
                from multilang.repositories.native_repository import NativeRepository

                with Session(bind=connection) as session:
                    NativeRepository(session).record_event(
                        MigrationCompleted(
                            entity_id=preview.confirmation_sha256,
                            actor=actor,
                            reason="confirmed_migration",
                            revision=1,
                            before_sha256=preview.source_sha256,
                            after_sha256=preview.target_sha256,
                        )
                    )
                    session.add(
                        MigrationJournalRecord(
                            id=preview.confirmation_sha256,
                            source_sha256=preview.source_sha256,
                            target_sha256=preview.target_sha256,
                            backup_sha256=preview.backup_sha256,
                            status="completed",
                            payload={
                                "preview": preview.model_dump(mode="json"),
                                "data_baseline_sha256": self._data_baseline(connection),
                            },
                        )
                    )
                    session.flush()
                self._postflight(connection, backup)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return completed

    @staticmethod
    def _data_baseline(connection: Engine | Connection) -> str:
        return database_fingerprint(connection, exclude_tables=frozenset({"migration_journal"}))

    @staticmethod
    def _postflight(connection: Engine | Connection, backup: BackupManifest) -> None:
        if database_fingerprint(connection, exclude_native=True) != backup.legacy_sha256:
            raise ValueError("legacy postflight failed; migration transaction rolled back")

    @staticmethod
    def _current_native_schema(connection: Connection) -> bool:
        from sqlalchemy import text

        from multilang.db.base import Base

        expected = {
            table.name: set(table.columns.keys())
            for table in Base.metadata.tables.values()
            if table.info.get("native")
        }
        inspector = inspect(connection)
        actual = set(inspector.get_table_names())
        return (
            set(expected) <= actual
            and all(
                columns <= {column["name"] for column in inspector.get_columns(name)}
                for name, columns in expected.items()
            )
            and connection.scalar(text("SELECT version_num FROM alembic_version"))
            == NATIVE_REVISION
        )

    def rollback_preview(self, backup: BackupManifest, migration_id: str) -> RollbackPreview:
        BackupService(self.engine).verify(backup)
        if backup.source_locator_sha256 != _locator(self.engine):
            raise ValueError("rollback source locator mismatch")
        from multilang.db.native_models import MigrationJournalRecord

        if "migration_journal" not in inspect(self.engine).get_table_names():
            raise ValueError("no native migration journal to roll back")
        with self.engine.connect() as connection:
            journal = (
                connection.execute(
                    select(MigrationJournalRecord.__table__).where(
                        MigrationJournalRecord.id == migration_id
                    )
                )
                .mappings()
                .first()
            )
            if (
                journal is None
                or journal["status"] != "completed"
                or journal["backup_sha256"] != backup.snapshot_sha256
            ):
                raise ValueError(
                    "rollback requires the completed migration and its original backup"
                )
            self._postflight(connection, backup)
            if journal["payload"].get("data_baseline_sha256") != self._data_baseline(connection):
                raise ValueError("new data or schema drift prevents destructive rollback")
            return RollbackPreview(
                migration_id=migration_id,
                source_sha256=database_fingerprint(connection),
                target_sha256=backup.database_sha256,
                backup_sha256=backup.snapshot_sha256,
                source_locator_sha256=backup.source_locator_sha256,
            )

    def rollback(
        self,
        preview: RollbackPreview,
        backup: BackupManifest,
        *,
        confirmation_sha256: str,
        actor: str,
    ) -> dict:
        if confirmation_sha256 != preview.confirmation_sha256:
            raise ValueError("rollback confirmation mismatch")
        expected = self.rollback_preview(backup, preview.migration_id)
        if expected != preview:
            raise ValueError("rollback data drift invalidated confirmation")
        config = native_alembic_config(self.engine)
        config.attributes["native_authorization"] = SchemaAuthorization(
            _locator(self.engine), backup.snapshot_sha256, "confirmed_apply"
        )
        with self.engine.connect() as connection:
            if self.engine.dialect.name == "sqlite":
                connection.exec_driver_sql("BEGIN IMMEDIATE")
            else:
                connection.begin()
            try:
                if database_fingerprint(connection) != preview.source_sha256:
                    raise ValueError("rollback data drift before transaction")
                config.attributes["connection"] = connection
                command.downgrade(config, LEGACY_REVISION)
                if database_fingerprint(connection) != backup.database_sha256:
                    raise ValueError("rollback restore verification failed")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        receipt = {
            "migration_id": preview.migration_id,
            "status": "rolled_back",
            "actor": actor,
            "restored_sha256": backup.database_sha256,
            "confirmation_sha256": confirmation_sha256,
        }
        return {**receipt, "receipt_sha256": canonical_hash(receipt)}

    def adoption_preview(self, backup: BackupManifest) -> LegacyAdoptionPreview:
        """Only the exact legacy create_all schema may acquire an Alembic stamp.

        This changes no legacy table. A fresh backup is required after adoption,
        since the explicit version stamp changes the database fingerprint.
        """
        if self.engine.dialect.name != "sqlite":
            raise ValueError(
                "unversioned schema adoption is restricted to the historical SQLite runtime"
            )
        BackupService(self.engine).verify(backup)
        if (
            backup.source_locator_sha256 != _locator(self.engine)
            or database_fingerprint(self.engine) != backup.database_sha256
        ):
            raise ValueError("legacy adoption source drift")
        if "alembic_version" in inspect(self.engine).get_table_names():
            raise ValueError("legacy adoption requires an unversioned database")
        from multilang.db import models as _models  # noqa: F401
        from multilang.db.base import Base

        reference = create_engine("sqlite://")
        try:
            legacy_tables = [
                table for table in Base.metadata.tables.values() if not table.info.get("native")
            ]
            Base.metadata.create_all(reference, tables=legacy_tables)
            expected = _schema_fingerprint(reference)
        finally:
            reference.dispose()
        actual = _schema_fingerprint(self.engine)
        if expected != actual:
            raise ValueError("legacy schema parity failed; explicit reconciliation is required")
        return LegacyAdoptionPreview(
            source_sha256=backup.database_sha256,
            schema_sha256=actual,
            source_locator_sha256=backup.source_locator_sha256,
            backup_sha256=backup.snapshot_sha256,
        )

    def adopt_legacy_schema(
        self,
        preview: LegacyAdoptionPreview,
        backup: BackupManifest,
        *,
        confirmation_sha256: str,
    ) -> dict:
        if confirmation_sha256 != preview.confirmation_sha256 or preview != self.adoption_preview(
            backup
        ):
            raise ValueError("legacy adoption confirmation mismatch or schema drift")
        config = native_alembic_config(self.engine)
        with self.engine.connect() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                if (
                    database_fingerprint(connection) != preview.source_sha256
                    or _schema_fingerprint(connection) != preview.schema_sha256
                ):
                    raise ValueError("legacy adoption source drift before transaction")
                config.attributes["connection"] = connection
                command.stamp(config, LEGACY_REVISION)
                if database_fingerprint(connection, exclude_native=True) != backup.legacy_sha256:
                    raise ValueError("legacy adoption changed existing data")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {
            "status": "adopted",
            "revision": LEGACY_REVISION,
            "new_snapshot_required": True,
        }
