"""Canonical numeric Anki model/deck ID registry."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import re
from typing import Iterable


class AnkiIdKind(StrEnum):
    MODEL = "model"
    DECK = "deck"


@dataclass(frozen=True, slots=True)
class AnkiIdRegistration:
    family: str
    role: str
    kind: AnkiIdKind
    value: int
    reserved: bool = False


@dataclass(frozen=True, slots=True)
class AnkiIdRegistryScanIssue:
    code: str
    path: Path
    detail: str


@dataclass(frozen=True, slots=True)
class AnkiIdRegistryScanResult:
    roots: tuple[Path, ...]
    scanned_files: int
    issues: tuple[AnkiIdRegistryScanIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


ANKI_ID_REGISTRY: tuple[AnkiIdRegistration, ...] = (
    AnkiIdRegistration("core", "frequency_model", AnkiIdKind.MODEL, 1_602_300_501),
    AnkiIdRegistration("core", "export_deck", AnkiIdKind.DECK, 1_602_300_502),
    AnkiIdRegistration("core", "manual_model", AnkiIdKind.MODEL, 1_602_300_503),
    AnkiIdRegistration("core", "highlight_model", AnkiIdKind.MODEL, 1_602_300_504),
    AnkiIdRegistration("phoneme", "russian_model", AnkiIdKind.MODEL, 1_602_300_601),
    AnkiIdRegistration("phoneme", "russian_deck", AnkiIdKind.DECK, 1_602_300_602),
    AnkiIdRegistration("phoneme", "polish_model", AnkiIdKind.MODEL, 1_602_300_603),
    AnkiIdRegistration("phoneme", "polish_deck", AnkiIdKind.DECK, 1_602_300_604),
    AnkiIdRegistration("phoneme", "greek_model", AnkiIdKind.MODEL, 1_602_300_605),
    AnkiIdRegistration("phoneme", "greek_deck", AnkiIdKind.DECK, 1_602_300_606),
    AnkiIdRegistration("latin", "mvp_model", AnkiIdKind.MODEL, 1_602_300_701),
    AnkiIdRegistration("latin", "mvp_deck", AnkiIdKind.DECK, 1_602_300_702),
    AnkiIdRegistration("japanese_frequency", "model", AnkiIdKind.MODEL, 1_762_800_701),
    AnkiIdRegistration("japanese_frequency", "deck", AnkiIdKind.DECK, 1_762_800_702),
    AnkiIdRegistration("japanese_kana", "model", AnkiIdKind.MODEL, 1_762_800_801),
    AnkiIdRegistration("japanese_kana", "hiragana_deck", AnkiIdKind.DECK, 1_762_800_802),
    AnkiIdRegistration("japanese_kana", "katakana_deck", AnkiIdKind.DECK, 1_762_800_803),
    AnkiIdRegistration("mandarin", "card_model", AnkiIdKind.MODEL, 1_762_800_901),
    AnkiIdRegistration("korean_foundation", "hangul_model", AnkiIdKind.MODEL, 1_762_801_001),
    AnkiIdRegistration("korean_foundation", "hangul_deck", AnkiIdKind.DECK, 1_762_801_002),
    AnkiIdRegistration("korean_foundation", "pronunciation_model", AnkiIdKind.MODEL, 1_762_801_003),
    AnkiIdRegistration("korean_foundation", "pronunciation_deck", AnkiIdKind.DECK, 1_762_801_004),
    AnkiIdRegistration("korean_frequency", "model", AnkiIdKind.MODEL, 1_762_801_101, reserved=True),
    AnkiIdRegistration("korean_frequency", "parent_deck", AnkiIdKind.DECK, 1_762_801_102, reserved=True),
    AnkiIdRegistration("korean_frequency", "level_1_deck", AnkiIdKind.DECK, 1_762_801_103, reserved=True),
    AnkiIdRegistration("korean_frequency", "level_2_deck", AnkiIdKind.DECK, 1_762_801_104, reserved=True),
    AnkiIdRegistration("korean_frequency", "level_3_deck", AnkiIdKind.DECK, 1_762_801_105, reserved=True),
)

_PRODUCTION_ROOTS = (Path("src/multilang"), Path("scripts"), Path("data"), Path("assets"))
_EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".planning",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "build",
        "dist",
        "node_modules",
        "private",
        "tests",
        "venv",
    }
)
_DATA_SUFFIXES = frozenset({".csv", ".json", ".toml", ".yaml", ".yml"})
_SCANNED_SUFFIXES = _DATA_SUFFIXES | {".py"}
_REGISTRY_RELATIVE_PATH = Path("src/multilang/services/anki_id_registry.py")
_ID_LITERAL_RE = re.compile(r"(?<![A-Za-z0-9_])(?:\d(?:_\d{3}){3}|\d{10})(?![A-Za-z0-9_])")
_DATA_ID_KEY_RE = re.compile(
    r"(?i)(?:anki[_-]?)?(?:model|deck)[_-]?id[^0-9]{0,24}(?P<value>\d(?:_?\d){5,})"
)


def validate_anki_id_registry(entries: Iterable[AnkiIdRegistration]) -> None:
    seen_keys: set[tuple[str, str, AnkiIdKind]] = set()
    values_by_kind: dict[AnkiIdKind, dict[int, AnkiIdRegistration]] = {
        AnkiIdKind.MODEL: {},
        AnkiIdKind.DECK: {},
    }
    values_all: dict[int, AnkiIdRegistration] = {}

    for entry in entries:
        _validate_entry(entry)
        key = (entry.family, entry.role, entry.kind)
        if key in seen_keys:
            raise ValueError(f"duplicate Anki ID key: {entry.family}/{entry.role}/{entry.kind.value}")
        seen_keys.add(key)

        same_kind = values_by_kind[entry.kind].get(entry.value)
        if same_kind is not None:
            raise ValueError(
                f"duplicate {entry.kind.value} Anki ID {entry.value}: "
                f"{same_kind.family}/{same_kind.role} and {entry.family}/{entry.role}"
            )

        any_kind = values_all.get(entry.value)
        if any_kind is not None and any_kind.kind is not entry.kind:
            raise ValueError(
                f"cross-kind Anki ID collision {entry.value}: "
                f"{any_kind.kind.value} {any_kind.family}/{any_kind.role} and "
                f"{entry.kind.value} {entry.family}/{entry.role}"
            )
        values_by_kind[entry.kind][entry.value] = entry
        values_all[entry.value] = entry


def registry_id(*, family: str, role: str, kind: AnkiIdKind) -> int:
    for entry in ANKI_ID_REGISTRY:
        if entry.family == family and entry.role == role and entry.kind is kind:
            return entry.value
    raise ValueError(f"unregistered Anki ID: {family}/{role}/{kind.value}")


def require_registered_anki_id(value: int, *, kind: AnkiIdKind) -> int:
    for entry in ANKI_ID_REGISTRY:
        if entry.value == value and entry.kind is kind:
            return value
    raise ValueError(f"unregistered {kind.value} Anki ID: {value}")


def production_anki_id_roots(*, repo_root: Path | None = None) -> tuple[Path, ...]:
    base = repo_root or Path.cwd()
    return tuple(base / root for root in _PRODUCTION_ROOTS if (base / root).exists())


def scan_anki_id_registry_paths(
    roots: Iterable[Path],
    *,
    registry: Iterable[AnkiIdRegistration] = ANKI_ID_REGISTRY,
) -> AnkiIdRegistryScanResult:
    entries = tuple(registry)
    validate_anki_id_registry(entries)
    known_values = {entry.value for entry in entries}
    known_keys = {(entry.family, entry.role, entry.kind) for entry in entries}
    used_keys: set[tuple[str, str, AnkiIdKind]] = set()
    issues: list[AnkiIdRegistryScanIssue] = []
    scanned_files = 0
    root_tuple = tuple(Path(root) for root in roots)

    for path in _iter_scannable_files(root_tuple):
        scanned_files += 1
        if path.suffix == ".py":
            _scan_python_file(
                path,
                known_values=known_values,
                known_keys=known_keys,
                used_keys=used_keys,
                issues=issues,
            )
        elif path.suffix in _DATA_SUFFIXES:
            _scan_data_file(path, known_values=known_values, issues=issues)

    if scanned_files:
        for entry in entries:
            key = (entry.family, entry.role, entry.kind)
            if key not in used_keys and not entry.reserved:
                issues.append(
                    AnkiIdRegistryScanIssue(
                        code="unused_registration",
                        path=Path("<registry>"),
                        detail=f"unused {entry.kind.value} registration {entry.family}/{entry.role}",
                    )
                )

    return AnkiIdRegistryScanResult(roots=root_tuple, scanned_files=scanned_files, issues=tuple(issues))


def assert_anki_id_registry_clean(
    *,
    production_roots: bool = False,
    roots: Iterable[Path] | None = None,
) -> AnkiIdRegistryScanResult:
    scan_roots = production_anki_id_roots() if production_roots else tuple(roots or ())
    result = scan_anki_id_registry_paths(scan_roots)
    if result.issues:
        first = result.issues[0]
        raise ValueError(
            "Anki ID registry violations: "
            f"{len(result.issues)} issue(s); first={first.code} {first.path}: {first.detail}"
        )
    return result


def _validate_entry(entry: AnkiIdRegistration) -> None:
    if not isinstance(entry.kind, AnkiIdKind):
        raise TypeError("Anki ID kind must be typed")
    if not isinstance(entry.value, int) or entry.value <= 0:
        raise ValueError("Anki ID value must be a positive integer")
    if not entry.family.strip():
        raise ValueError("Anki ID family must not be blank")
    if not entry.role.strip():
        raise ValueError("Anki ID role must not be blank")


def _iter_scannable_files(roots: tuple[Path, ...]) -> Iterable[Path]:
    for root in roots:
        if _excluded_path(root):
            continue
        if root.is_file():
            if _should_scan_file(root):
                yield root
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and _should_scan_file(path):
                yield path


def _should_scan_file(path: Path) -> bool:
    if path.is_symlink() or path.suffix not in _SCANNED_SUFFIXES:
        return False
    return not _excluded_path(path)


def _excluded_path(path: Path) -> bool:
    return any(part in _EXCLUDED_PARTS for part in path.parts)


def _scan_python_file(
    path: Path,
    *,
    known_values: set[int],
    known_keys: set[tuple[str, str, AnkiIdKind]],
    used_keys: set[tuple[str, str, AnkiIdKind]],
    issues: list[AnkiIdRegistryScanIssue],
) -> None:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        issues.append(AnkiIdRegistryScanIssue("parse_error", path, str(exc)))
        return

    is_registry = _is_registry_file(path)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            _scan_python_assignment(node, path=path, known_values=known_values, issues=issues)
        if isinstance(node, ast.Call):
            _scan_registry_call(node, path=path, known_keys=known_keys, used_keys=used_keys, issues=issues)
            _scan_unchecked_dynamic_call(node, path=path, issues=issues)

    if is_registry:
        return
    for match in _ID_LITERAL_RE.finditer(source):
        value = int(match.group(0).replace("_", ""))
        if value in known_values:
            issues.append(
                AnkiIdRegistryScanIssue(
                    code="direct_literal",
                    path=path,
                    detail=f"registered Anki ID literal {value} appears outside registry",
                )
            )


def _scan_python_assignment(
    node: ast.Assign | ast.AnnAssign,
    *,
    path: Path,
    known_values: set[int],
    issues: list[AnkiIdRegistryScanIssue],
) -> None:
    value = node.value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, int):
        return
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if not isinstance(target, ast.Name) or not target.id.endswith(("MODEL_ID", "DECK_ID")):
            continue
        if value.value not in known_values:
            issues.append(
                AnkiIdRegistryScanIssue(
                    code="unknown_declaration",
                    path=path,
                    detail=f"{target.id} declares unregistered Anki ID {value.value}",
                )
            )


def _scan_registry_call(
    node: ast.Call,
    *,
    path: Path,
    known_keys: set[tuple[str, str, AnkiIdKind]],
    used_keys: set[tuple[str, str, AnkiIdKind]],
    issues: list[AnkiIdRegistryScanIssue],
) -> None:
    if _call_name(node.func) != "registry_id":
        return
    family = _constant_keyword(node, "family")
    role = _constant_keyword(node, "role")
    kind = _kind_keyword(node)
    if family is None or role is None or kind is None:
        issues.append(AnkiIdRegistryScanIssue("dynamic_registry_key", path, "registry_id call uses non-literal key"))
        return
    key = (family, role, kind)
    if key not in known_keys:
        issues.append(
            AnkiIdRegistryScanIssue(
                code="unknown_key",
                path=path,
                detail=f"unknown registry key {family}/{role}/{kind.value}",
            )
        )
        return
    used_keys.add(key)


def _scan_unchecked_dynamic_call(
    node: ast.Call,
    *,
    path: Path,
    issues: list[AnkiIdRegistryScanIssue],
) -> None:
    if _call_name(node.func) != "Model" or not node.args:
        return
    first_arg = node.args[0]
    if isinstance(first_arg, ast.Name) and first_arg.id in {"model_id", "deck_model_id"}:
        issues.append(
            AnkiIdRegistryScanIssue(
                code="unchecked_dynamic",
                path=path,
                detail=f"genanki.Model receives unchecked dynamic argument {first_arg.id}",
            )
        )


def _scan_data_file(
    path: Path,
    *,
    known_values: set[int],
    issues: list[AnkiIdRegistryScanIssue],
) -> None:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        issues.append(AnkiIdRegistryScanIssue("parse_error", path, str(exc)))
        return
    for match in _DATA_ID_KEY_RE.finditer(source):
        value = int(match.group("value").replace("_", ""))
        issues.append(
            AnkiIdRegistryScanIssue(
                code="data_literal" if value in known_values else "unknown_declaration",
                path=path,
                detail=f"data file declares Anki-like ID {value}",
            )
        )


def _constant_keyword(node: ast.Call, name: str) -> str | None:
    for keyword in node.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    return None


def _kind_keyword(node: ast.Call) -> AnkiIdKind | None:
    for keyword in node.keywords:
        if keyword.arg != "kind":
            continue
        value = keyword.value
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name) and value.value.id == "AnkiIdKind":
            try:
                return AnkiIdKind[value.attr]
            except KeyError:
                return None
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            try:
                return AnkiIdKind(value.value)
            except ValueError:
                return None
    return None


def _call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _is_registry_file(path: Path) -> bool:
    return path.as_posix().endswith(_REGISTRY_RELATIVE_PATH.as_posix())


validate_anki_id_registry(ANKI_ID_REGISTRY)


__all__ = [
    "ANKI_ID_REGISTRY",
    "AnkiIdKind",
    "AnkiIdRegistration",
    "AnkiIdRegistryScanIssue",
    "AnkiIdRegistryScanResult",
    "assert_anki_id_registry_clean",
    "production_anki_id_roots",
    "registry_id",
    "require_registered_anki_id",
    "scan_anki_id_registry_paths",
    "validate_anki_id_registry",
]
