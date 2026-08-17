"""Private end-to-end proof for the fixed Korean foundation CLI workflow."""

from __future__ import annotations

import csv
from hashlib import sha256
from importlib import import_module, util
import json
from pathlib import Path
import socket
import sqlite3
import stat
import sys
from types import ModuleType, SimpleNamespace
from typing import Any
import zipfile

import pytest
from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app


runner = CliRunner()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_ROOT = (
    PROJECT_ROOT
    / ".planning"
    / "phases"
    / "31-hangul-and-pronunciation-i-plus-1"
)
CANONICAL_STATE_PATHS = (
    PROJECT_ROOT / "data" / "korean_foundations",
    PHASE_ROOT / "31-CURRICULUM-REVIEW.md",
    PHASE_ROOT / "31-AUDIO-PLAYBACK-REVIEW.md",
    PHASE_ROOT / "evidence-inbox",
    PROJECT_ROOT / ".multilang" / "exports" / "korean-foundations",
)

LOCKED_EXPORT_NAMES = {
    "hangul.apkg",
    "hangul-csv",
    "hangul-tsv",
    "pronunciation-i-plus-1.apkg",
    "pronunciation-i-plus-1-csv",
    "pronunciation-i-plus-1-tsv",
}


def _load_private_helper(filename: str, module_name: str) -> ModuleType:
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    module_path = PROJECT_ROOT / "tests" / "services" / filename
    spec = util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _evidence_helpers() -> ModuleType:
    return _load_private_helper(
        "test_korean_foundation_evidence.py",
        "_plan_31_10_evidence_fixture_helpers",
    )


def _snapshot_helpers() -> ModuleType:
    return _load_private_helper(
        "test_korean_foundation_snapshot.py",
        "_plan_31_10_snapshot_fixture_helpers",
    )


def _canonical_state_digest() -> str:
    rows: list[tuple[str, str, str]] = []
    for path in CANONICAL_STATE_PATHS:
        label = path.relative_to(PROJECT_ROOT).as_posix()
        if not path.exists() and not path.is_symlink():
            rows.append((label, "absent", ""))
            continue
        candidates = (path, *sorted(path.rglob("*"))) if path.is_dir() else (path,)
        for candidate in candidates:
            relative = (
                label
                if candidate == path
                else f"{label}/{candidate.relative_to(path).as_posix()}"
            )
            metadata = candidate.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                rows.append((relative, "link", str(candidate.readlink())))
            elif stat.S_ISDIR(metadata.st_mode):
                rows.append((relative, "directory", ""))
            elif stat.S_ISREG(metadata.st_mode):
                rows.append((relative, "file", sha256(candidate.read_bytes()).hexdigest()))
            else:
                rows.append((relative, "special", str(metadata.st_mode)))
    return sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _artifact_digest(path: Path) -> str:
    if path.is_file():
        return sha256(path.read_bytes()).hexdigest()
    rows = [
        (candidate.relative_to(path).as_posix(), sha256(candidate.read_bytes()).hexdigest())
        for candidate in sorted(path.rglob("*"))
        if candidate.is_file()
    ]
    return sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _parse_output(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        key, value = line.split("=", 1)
        assert key not in values
        values[key] = value
    return values


def _invoke(app: Any, *arguments: str) -> dict[str, str]:
    result = runner.invoke(app, ["korean-foundations", *arguments])
    assert result.exit_code == 0, (
        f"arguments={arguments!r} output={result.output!r} "
        f"exception={result.exception!r}"
    )
    return _parse_output(result.output)


def _forbid_external_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError(
            "Korean foundation flow constructed a provider/network/DB/frequency runtime"
        )

    monkeypatch.setattr(cli_module, "build_runtime_service", forbidden)
    monkeypatch.setattr(cli_module, "KiwiKoreanMorphologyService", forbidden)
    monkeypatch.setattr(cli_module, "LexicalGroundingService", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


def _build_cli_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> SimpleNamespace:
    evidence_helpers = _evidence_helpers()
    snapshot_helpers = _snapshot_helpers()
    evidence_api = import_module("multilang.services.korean_foundation_evidence")
    snapshot_api = import_module("multilang.services.korean_foundation_snapshot")
    export_api = import_module("multilang.services.korean_foundation_export")
    fixture = evidence_helpers._build_complete_fixture(
        tmp_path,
        export_ready=True,
    )
    evidence_helpers._install_fixture_paths(evidence_api, monkeypatch, fixture)
    snapshot_helpers._install_snapshot_fixture_paths(
        snapshot_api,
        monkeypatch,
        fixture.project_root,
    )
    export_root = fixture.project_root / ".multilang" / "exports" / (
        "korean-foundations"
    )
    monkeypatch.setattr(
        cli_module,
        "_KOREAN_FOUNDATION_EXPORT_ROOT",
        export_root,
        raising=False,
    )
    _forbid_external_construction(monkeypatch)
    return SimpleNamespace(
        app=create_app(),
        fixture=fixture,
        evidence_api=evidence_api,
        snapshot_api=snapshot_api,
        export_api=export_api,
        evidence_helpers=evidence_helpers,
        snapshot_helpers=snapshot_helpers,
        paths=snapshot_api._FIXED_PATHS,
        export_root=export_root,
    )


def _prepare_cli_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> SimpleNamespace:
    state = _build_cli_fixture(tmp_path, monkeypatch)
    receipt_output = _invoke(
        state.app,
        "validate-and-write-receipt",
        "--confirmed-index-sha256",
        state.fixture.index_sha256,
    )
    receipt_sha256 = receipt_output["receipt_sha256"]
    prepared = _invoke(
        state.app,
        "prepare-snapshot",
        "--expected-receipt-sha256",
        receipt_sha256,
    )
    state.receipt_sha256 = receipt_sha256
    state.prepared = prepared
    return state


def _expected_export_paths(root: Path) -> dict[tuple[str, str], Path]:
    return {
        ("hangul", "apkg"): root / "hangul.apkg",
        ("hangul", "csv"): root / "hangul-csv",
        ("hangul", "tsv"): root / "hangul-tsv",
        ("pronunciation", "apkg"): root / "pronunciation-i-plus-1.apkg",
        ("pronunciation", "csv"): root / "pronunciation-i-plus-1-csv",
        ("pronunciation", "tsv"): root / "pronunciation-i-plus-1-tsv",
    }


def _family_contract(api: ModuleType, family: str) -> tuple[int, int, tuple[str, ...]]:
    if family == "hangul":
        return (
            api.KOREAN_HANGUL_MODEL_ID,
            api.KOREAN_HANGUL_DECK_ID,
            api.HANGUL_FIELD_NAMES,
        )
    return (
        api.KOREAN_PRONUNCIATION_MODEL_ID,
        api.KOREAN_PRONUNCIATION_DECK_ID,
        api.KOREAN_PRONUNCIATION_FIELD_NAMES,
    )


def _inspect_apkg_deep(
    path: Path,
    *,
    family: str,
    bundle: object,
    api: ModuleType,
    workspace: Path,
) -> None:
    model_id, deck_id, field_names = _family_contract(api, family)
    expected_media = {item.basename: item for item in bundle.media}
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        assert len(names) == len(set(names))
        assert set(names) == {
            "collection.anki2",
            "media",
            *(str(index) for index in range(len(expected_media))),
        }
        assert all(
            not name.startswith(("/", "\\"))
            and ".." not in name.replace("\\", "/").split("/")
            for name in names
        )
        media_map = json.loads(archive.read("media").decode("utf-8"))
        expected_names = sorted(expected_media)
        assert media_map == {
            str(index): basename for index, basename in enumerate(expected_names)
        }
        for index, basename in enumerate(expected_names):
            payload = archive.read(str(index))
            expected = expected_media[basename]
            assert payload == expected.content
            assert sha256(payload).hexdigest() == expected.sha256
        collection_bytes = archive.read("collection.anki2")

    collection = workspace / f"{family}-collection.anki2"
    collection.write_bytes(collection_bytes)
    connection = sqlite3.connect(collection)
    try:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        decks = json.loads(connection.execute("select decks from col").fetchone()[0])
        notes = connection.execute(
            "select guid, mid, flds, tags from notes order by id"
        ).fetchall()
        cards = connection.execute("select did from cards order by id").fetchall()
    finally:
        connection.close()
    collection.unlink()

    assert set(models) == {str(model_id)}
    assert [field["name"] for field in models[str(model_id)]["flds"]] == list(
        field_names
    )
    assert str(deck_id) in decks
    assert len(notes) == len(bundle.rows)
    assert len(cards) == len(bundle.rows)
    assert {value for (value,) in cards} == {deck_id}
    for (guid, note_model_id, fields, tags), row in zip(
        notes,
        bundle.rows,
        strict=True,
    ):
        assert note_model_id == model_id
        assert guid == api.stable_korean_foundation_guid(
            family=bundle.family,
            source_pack_version=row.source_pack_version,
            item_key=row.item_key,
        )
        assert fields.split("\x1f") == row.ordered_fields()
        tag_values = tags.split()
        assert {"multilang", "ko", "korean_foundation"} <= set(tag_values)
        assert f"family_{family}" in tag_values
        assert f"item_{row.item_key.replace('-', '_')}" in tag_values


def _inspect_tabular_deep(
    path: Path,
    *,
    family: str,
    format_name: str,
    bundle: object,
    api: ModuleType,
) -> None:
    model_id, deck_id, field_names = _family_contract(api, family)
    table_name = (
        f"korean-hangul-foundation.{format_name}"
        if family == "hangul"
        else f"korean-pronunciation-i-plus-1.{format_name}"
    )
    assert {child.name for child in path.iterdir()} == {
        table_name,
        "notes-metadata.json",
        "media-checksums.json",
        "media",
    }
    delimiter = "," if format_name == "csv" else "\t"
    lines = (path / table_name).read_text(encoding="utf-8").splitlines()
    assert lines[0] == ("#separator:Comma" if format_name == "csv" else "#separator:Tab")
    assert lines[1] == "#html:true"
    assert lines[4] == f"#columns:{delimiter.join(field_names)}"
    rows = list(csv.reader(lines[5:], delimiter=delimiter))
    assert rows == [row.ordered_fields() for row in bundle.rows]

    metadata = json.loads((path / "notes-metadata.json").read_text(encoding="utf-8"))
    checksums = json.loads((path / "media-checksums.json").read_text(encoding="utf-8"))
    assert metadata["family"] == family
    assert metadata["snapshot_bundle_sha256"] == bundle.snapshot_bundle_sha256
    assert metadata["model_id"] == model_id
    assert metadata["deck_id"] == deck_id
    assert checksums["family"] == family
    assert checksums["snapshot_bundle_sha256"] == bundle.snapshot_bundle_sha256
    assert len(metadata["notes"]) == len(bundle.rows)
    for note, row in zip(metadata["notes"], bundle.rows, strict=True):
        assert note["item_key"] == row.item_key
        assert note["guid"] == api.stable_korean_foundation_guid(
            family=bundle.family,
            source_pack_version=row.source_pack_version,
            item_key=row.item_key,
        )
        assert "ko" in note["tags"]

    media_root = path / "media"
    copied = {item.name: item for item in media_root.iterdir()}
    expected_checksums = {item["basename"]: item for item in checksums["files"]}
    assert set(copied) == set(expected_checksums)
    for basename, item in expected_checksums.items():
        payload = copied[basename].read_bytes()
        assert len(payload) == item["size_bytes"]
        assert sha256(payload).hexdigest() == item["sha256"]

    references = {
        match.group(1) or match.group(2)
        for row in rows
        for field in row
        for match in [
            __import__("re").search(
                r"\[sound:([^\]]+)\]|<img src=\"([^\"]+)\">",
                field,
            )
        ]
        if match is not None
    }
    assert references == set(copied)


def test_complete_cli_flow_through_active_provenance_and_all_six_exports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_before = _canonical_state_digest()
    state = _build_cli_fixture(tmp_path, monkeypatch)

    inbox = _invoke(state.app, "inspect-inbox")
    assert inbox == {
        "inbox_status": "complete_unvalidated",
        "evidence_index_sha256": state.fixture.index_sha256,
        "declared_member_count": "519",
    }

    receipt = _invoke(
        state.app,
        "validate-and-write-receipt",
        "--confirmed-index-sha256",
        state.fixture.index_sha256,
    )
    receipt_sha256 = sha256(state.fixture.receipt_path.read_bytes()).hexdigest()
    assert receipt == {
        "receipt_write_status": "written",
        "receipt_sha256": receipt_sha256,
        "bundle_sha256": receipt["bundle_sha256"],
    }
    assert receipt["bundle_sha256"] == json.loads(
        state.fixture.receipt_path.read_text(encoding="utf-8")
    )["evidence_bundle_sha256"]
    retry = _invoke(
        state.app,
        "validate-and-write-receipt",
        "--confirmed-index-sha256",
        state.fixture.index_sha256,
    )
    assert retry["receipt_write_status"] == "already_current"
    assert retry["receipt_sha256"] == receipt_sha256

    continuity = _invoke(
        state.app,
        "check-receipt",
        "--expected-receipt-sha256",
        receipt_sha256,
    )
    assert continuity == {
        "receipt_status": "continuous",
        "receipt_sha256": receipt_sha256,
        "bundle_sha256": receipt["bundle_sha256"],
    }

    prepared = _invoke(
        state.app,
        "prepare-snapshot",
        "--expected-receipt-sha256",
        receipt_sha256,
    )
    assert prepared["snapshot_status"] == "prepared_inactive"
    assert prepared["receipt_sha256"] == receipt_sha256
    prepared_manifest = json.loads(
        (
            state.paths.snapshot_root
            / prepared["bundle_sha256"]
            / "snapshot-manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert prepared_manifest["bundle_sha256"] == prepared["bundle_sha256"]
    assert prepared_manifest["evidence_bundle_sha256"] == receipt["bundle_sha256"]
    assert state.paths.active_pointer.exists() is False
    before_verify = state.snapshot_helpers._tree_state(state.fixture.project_root)
    with monkeypatch.context() as poison:
        state.snapshot_helpers._poison_snapshot_write_primitives(
            state.snapshot_api,
            state.evidence_api,
            poison,
        )
        verified = _invoke(
            state.app,
            "verify-prepared",
            "--expected-receipt-sha256",
            receipt_sha256,
        )
    assert verified == {
        "receipt_sha256": prepared["receipt_sha256"],
        "bundle_sha256": prepared["bundle_sha256"],
        "snapshot_manifest_sha256": prepared["snapshot_manifest_sha256"],
        "snapshot_root_sha256": prepared["snapshot_root_sha256"],
        "active_prestate_sha256": prepared["active_prestate_sha256"],
        "authorization_sha256": prepared["authorization_sha256"],
        "prepared_status": "verified",
    }
    assert state.snapshot_helpers._tree_state(state.fixture.project_root) == before_verify

    activated = _invoke(
        state.app,
        "activate",
        "--expected-receipt-sha256",
        receipt_sha256,
        "--authorization-sha256",
        prepared["authorization_sha256"],
    )
    assert activated == {
        "activation_status": "activated",
        "receipt_sha256": receipt_sha256,
        "bundle_sha256": prepared["bundle_sha256"],
    }
    active = _invoke(
        state.app,
        "verify-active",
        "--expected-receipt-sha256",
        receipt_sha256,
    )
    assert active == {
        "active_status": "verified",
        "receipt_sha256": receipt_sha256,
        "bundle_sha256": prepared["bundle_sha256"],
        "snapshot_root_sha256": prepared["snapshot_root_sha256"],
    }

    readiness = {
        family: _invoke(state.app, "check", "--family", family)
        for family in ("hangul", "pronunciation")
    }
    assert readiness["hangul"] == {
        "family": "hangul",
        "readiness_status": "ready",
        "card_count": "92",
        "media_count": "184",
    }
    assert readiness["pronunciation"] == {
        "family": "pronunciation",
        "readiness_status": "ready",
        "card_count": "47",
        "media_count": "141",
    }

    paths = _expected_export_paths(state.export_root)
    for (family, format_name), destination in paths.items():
        output = _invoke(
            state.app,
            "export",
            "--family",
            family,
            "--format",
            format_name,
            "--output",
            str(destination),
        )
        assert output["family"] == family
        assert output["format"] == format_name
        assert output["export_status"] == "written"
        assert output["card_count"] == ("92" if family == "hangul" else "47")
        assert output["media_count"] == ("184" if family == "hangul" else "141")
        assert destination.exists()
        assert str(destination) not in "\n".join(f"{key}={value}" for key, value in output.items())

    assert {child.name for child in state.export_root.iterdir()} == LOCKED_EXPORT_NAMES
    export_set = _invoke(state.app, "inspect-exports")
    assert export_set == {
        "export_set_status": "verified",
        "artifact_count": "6",
        "receipt_sha256": receipt_sha256,
        "bundle_sha256": prepared["bundle_sha256"],
        "snapshot_root_sha256": prepared["snapshot_root_sha256"],
    }

    bundles = {
        family.value: state.export_api.build_korean_foundation_export_bundle(
            family=family
        )
        for family in state.export_api.KoreanFoundationFamily
    }
    inspection_workspace = tmp_path / "independent-apkg-inspection"
    inspection_workspace.mkdir()
    for (family, format_name), destination in paths.items():
        bundle = bundles[family]
        assert bundle.snapshot_bundle_sha256 == prepared["bundle_sha256"]
        if format_name == "apkg":
            _inspect_apkg_deep(
                destination,
                family=family,
                bundle=bundle,
                api=state.export_api,
                workspace=inspection_workspace,
            )
        else:
            _inspect_tabular_deep(
                destination,
                family=family,
                format_name=format_name,
                bundle=bundle,
                api=state.export_api,
            )
    assert list(inspection_workspace.iterdir()) == []

    artifact_hashes = {
        f"{family}_{format_name}_sha256": _artifact_digest(destination)
        for (family, format_name), destination in paths.items()
    }
    print(f"integration_receipt_sha256={receipt_sha256}")
    print(f"integration_bundle_sha256={prepared['bundle_sha256']}")
    print(
        "integration_snapshot_manifest_sha256="
        f"{prepared['snapshot_manifest_sha256']}"
    )
    print(f"integration_snapshot_root_sha256={prepared['snapshot_root_sha256']}")
    print(f"integration_authorization_sha256={prepared['authorization_sha256']}")
    for key, value in sorted(artifact_hashes.items()):
        print(f"{key}={value}")

    extra = state.export_root / "unexpected.txt"
    extra.write_text("must not be ignored\n", encoding="utf-8")
    before_extra_refusal = state.snapshot_helpers._tree_state(state.fixture.project_root)
    rejected = runner.invoke(
        state.app,
        ["korean-foundations", "inspect-exports"],
    )
    assert rejected.exit_code == 1
    assert rejected.output == "korean_foundations_error=operation_failed\n"
    assert state.snapshot_helpers._tree_state(state.fixture.project_root) == (
        before_extra_refusal
    )
    extra.unlink()
    assert _canonical_state_digest() == canonical_before


@pytest.mark.parametrize(
    "drift_case",
    [
        "missing-member",
        "source-member",
        "media-member",
        "manifest-file",
        "root-extra",
        "manifest-tuple",
        "root-hash",
        "receipt",
        "active-prestate",
    ],
)
def test_cli_verify_prepared_drift_is_write_poisoned_and_zero_write(
    drift_case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _prepare_cli_fixture(tmp_path, monkeypatch)
    target = state.paths.snapshot_root / state.prepared["bundle_sha256"]
    manifest_path = target / "snapshot-manifest.json"
    if drift_case == "missing-member":
        (target / "review" / "rights.json").unlink()
    elif drift_case == "source-member":
        path = target / "content" / "hangul-v1.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "media-member":
        path = next(
            candidate
            for candidate in (target / "media").rglob("*")
            if candidate.is_file()
        )
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "manifest-file":
        manifest_path.write_bytes(manifest_path.read_bytes() + b" ")
    elif drift_case == "root-extra":
        (target / "review" / "unmanifested.json").write_bytes(b"{}\n")
    elif drift_case in {"manifest-tuple", "root-hash"}:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if drift_case == "manifest-tuple":
            payload["active_prestate_sha256"] = "7" * 64
        else:
            payload["snapshot_root_sha256"] = "6" * 64
        payload["bundle_sha256"] = state.snapshot_helpers._bundle_sha256(payload)
        manifest_path.write_bytes(
            (
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8")
        )
    elif drift_case == "receipt":
        state.fixture.receipt_path.write_bytes(
            state.fixture.receipt_path.read_bytes() + b" "
        )
    else:
        state.fixture.active_pointer.write_bytes(
            state.snapshot_helpers._valid_pointer_bytes("6")
        )

    before = state.snapshot_helpers._tree_state(state.fixture.project_root)
    with monkeypatch.context() as poison:
        state.snapshot_helpers._poison_snapshot_write_primitives(
            state.snapshot_api,
            state.evidence_api,
            poison,
        )
        result = runner.invoke(
            state.app,
            [
                "korean-foundations",
                "verify-prepared",
                "--expected-receipt-sha256",
                state.receipt_sha256,
            ],
        )
    assert result.exit_code == 1
    assert result.output.startswith("korean_foundations_error=")
    assert str(state.fixture.project_root) not in result.output
    assert state.snapshot_helpers._tree_state(state.fixture.project_root) == before


@pytest.mark.parametrize(
    "drift_case",
    [
        "receipt",
        "confirmed-index",
        "reviewer",
        "rights",
        "media",
        "snapshot-member",
        "snapshot-manifest",
        "authorization",
        "active-prestate",
    ],
)
def test_cli_activation_refuses_stale_authority_before_recovery_or_write(
    drift_case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _prepare_cli_fixture(tmp_path, monkeypatch)
    stale = state.paths.snapshot_root / ".staging-cli-activation-drift"
    stale.mkdir()
    (stale / "sentinel.bin").write_bytes(b"must remain")
    authorization = state.prepared["authorization_sha256"]
    if drift_case == "receipt":
        path = state.fixture.receipt_path
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "confirmed-index":
        path = state.fixture.index_path
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "reviewer":
        path = state.fixture.inbox / "reviewers" / "korean-phonetics.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "rights":
        path = state.fixture.inbox / "rights.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "media":
        path = state.fixture.inbox / "media" / "hangul-audio-0001.wav"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "snapshot-member":
        path = (
            state.paths.snapshot_root
            / state.prepared["bundle_sha256"]
            / "content"
            / "korean-concepts-v1.json"
        )
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "snapshot-manifest":
        path = (
            state.paths.snapshot_root
            / state.prepared["bundle_sha256"]
            / "snapshot-manifest.json"
        )
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "authorization":
        authorization = "f" * 64
    else:
        state.fixture.active_pointer.write_bytes(
            state.snapshot_helpers._valid_pointer_bytes("7")
        )
    before = state.snapshot_helpers._tree_state(state.fixture.project_root)

    result = runner.invoke(
        state.app,
        [
            "korean-foundations",
            "activate",
            "--expected-receipt-sha256",
            state.receipt_sha256,
            "--authorization-sha256",
            authorization,
        ],
    )

    assert result.exit_code == 1
    assert result.output.startswith("korean_foundations_error=")
    assert str(state.fixture.project_root) not in result.output
    assert state.snapshot_helpers._tree_state(state.fixture.project_root) == before
    assert stale.is_dir()


def test_cli_verify_active_rejects_pointer_drift_without_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _prepare_cli_fixture(tmp_path, monkeypatch)
    _invoke(
        state.app,
        "activate",
        "--expected-receipt-sha256",
        state.receipt_sha256,
        "--authorization-sha256",
        state.prepared["authorization_sha256"],
    )
    payload = json.loads(state.paths.active_pointer.read_text(encoding="utf-8"))
    payload["authorization_sha256"] = "f" * 64
    state.paths.active_pointer.write_bytes(
        (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
    )
    before = state.snapshot_helpers._tree_state(state.fixture.project_root)

    result = runner.invoke(
        state.app,
        [
            "korean-foundations",
            "verify-active",
            "--expected-receipt-sha256",
            state.receipt_sha256,
        ],
    )

    assert result.exit_code == 1
    assert result.output == (
        "korean_foundations_error=active_provenance_invalid\n"
    )
    assert state.snapshot_helpers._tree_state(state.fixture.project_root) == before
