"""Locked Typer surface for the pathless Korean foundation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import inspect
import json
from pathlib import Path
import socket
import stat
from types import SimpleNamespace
from typing import Any

import click
import pytest
from typer.main import get_command
from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app
from multilang.services.korean_curriculum import KoreanFoundationFamily


runner = CliRunner()

HASHES = tuple(str(index) * 64 for index in range(1, 7))
RECEIPT_SHA256, BUNDLE_SHA256, MANIFEST_SHA256, ROOT_SHA256, PRESTATE_SHA256, AUTHORIZATION_SHA256 = HASHES
CURRENT_BUNDLE_SHA256 = (
    "36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0"
)
CURRENT_BUNDLE_RELPATH = Path("candidate-bundles") / CURRENT_BUNDLE_SHA256

EXPECTED_COMMAND_OPTIONS = {
    "inspect-inbox": (),
    "validate-and-write-receipt": ("--confirmed-index-sha256",),
    "check-receipt": ("--expected-receipt-sha256",),
    "prepare-snapshot": ("--expected-receipt-sha256",),
    "verify-prepared": ("--expected-receipt-sha256",),
    "activate": (
        "--expected-receipt-sha256",
        "--authorization-sha256",
    ),
    "verify-active": ("--expected-receipt-sha256",),
    "check": ("--family",),
    "export": ("--family", "--format", "--output"),
    "inspect-exports": (),
}

FORBIDDEN_OPTIONS = (
    "--source",
    "--source-path",
    "--inbox",
    "--inbox-path",
    "--receipt",
    "--receipt-path",
    "--snapshot",
    "--snapshot-root",
    "--pointer",
    "--pointer-path",
    "--url",
    "--archive",
    "--input-apkg",
    "--import",
    "--allow-unapproved",
    "--bypass",
    "--force",
    "--repair",
    "--recover",
    "--provider",
    "--test-hook",
)

CANONICAL_CANDIDATES = tuple(
    Path("data/korean_foundations") / filename
    for filename in (
        "korean-concepts-v1.json",
        "current-candidate.json",
    )
) + tuple(
    Path("data/korean_foundations") / CURRENT_BUNDLE_RELPATH / filename
    for filename in (
        "bundle-manifest.json",
        "hangul-v2.json",
        "pronunciation-i-plus-1-v2.json",
        "korean-foundations-v2-curation.json",
        "korean-foundations-v2-media.json",
    )
)
CANONICAL_STATE_PATHS = (
    *CANONICAL_CANDIDATES,
    Path(".planning/phases/31-hangul-and-pronunciation-i-plus-1/31-CURRICULUM-REVIEW.md"),
    Path(".planning/phases/31-hangul-and-pronunciation-i-plus-1/31-AUDIO-PLAYBACK-REVIEW.md"),
    Path(".planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox"),
    Path("data/korean_foundations/validation-receipt.json"),
    Path("data/korean_foundations/snapshots"),
    Path("data/korean_foundations/active-foundations.json"),
    Path(".multilang/exports/korean-foundations"),
)


def _foundation_group(app: Any | None = None) -> click.Group:
    root = get_command(app or create_app())
    command = root.commands.get("korean-foundations")
    assert isinstance(command, click.Group)
    return command


def _option_declarations(command: click.Command) -> tuple[str, ...]:
    declarations: list[str] = []
    for parameter in command.params:
        assert isinstance(parameter, click.Option)
        assert parameter.secondary_opts == []
        assert len(parameter.opts) == 1
        declarations.extend(parameter.opts)
    return tuple(declarations)


def _tree_digest(paths: tuple[Path, ...]) -> str:
    root = Path.cwd().resolve()
    rows: list[tuple[str, str, str]] = []
    for configured in paths:
        path = configured if configured.is_absolute() else root / configured
        label = configured.as_posix()
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
        json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


@dataclass
class _FakeReceipt:
    evidence_bundle_sha256: str = BUNDLE_SHA256
    _receipt_write_status: str = "written"

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return {
            "schema_version": 1,
            "receipt_version": "fixture-receipt-v1",
            "evidence_bundle_sha256": self.evidence_bundle_sha256,
        }


def _receipt_file_sha256(receipt: _FakeReceipt) -> str:
    raw = (
        json.dumps(
            receipt.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    return sha256(raw).hexdigest()


def test_exact_group_commands_options_and_create_app_injection_are_locked() -> None:
    assert tuple(inspect.signature(create_app).parameters) == (
        "conflict_checker",
        "generate_executor",
        "service",
        "review_report_builder",
        "webdav_service_factory",
        "latin_mvp_service",
    )

    group = _foundation_group()
    assert set(group.commands) == set(EXPECTED_COMMAND_OPTIONS)
    for command_name, expected_options in EXPECTED_COMMAND_OPTIONS.items():
        command = group.commands[command_name]
        assert _option_declarations(command) == expected_options
        assert all(parameter.required for parameter in command.params)

    filesystem_options = [
        (command_name, parameter.name)
        for command_name, command in group.commands.items()
        for parameter in command.params
        if isinstance(parameter.type, click.Path)
    ]
    assert filesystem_options == [("export", "output")]


@pytest.mark.parametrize("forbidden_option", FORBIDDEN_OPTIONS)
def test_forbidden_path_import_bypass_provider_and_hook_options_are_rejected(
    forbidden_option: str,
) -> None:
    result = runner.invoke(
        create_app(),
        ["korean-foundations", "inspect-inbox", forbidden_option, "fixture-value"],
    )

    assert result.exit_code == 2
    assert "No such option" in result.output


@pytest.mark.parametrize(
    "command,option",
    [
        ("validate-and-write-receipt", "--confirmed-index-sha256"),
        ("check-receipt", "--expected-receipt-sha256"),
        ("prepare-snapshot", "--expected-receipt-sha256"),
        ("verify-prepared", "--expected-receipt-sha256"),
        ("activate", "--expected-receipt-sha256"),
        ("activate", "--authorization-sha256"),
        ("verify-active", "--expected-receipt-sha256"),
    ],
)
@pytest.mark.parametrize(
    "malformed_hash",
    ("a" * 63, "A" * 64, "g" * 64, "../" + "a" * 61),
)
def test_malformed_hashes_fail_with_controlled_parser_exits_before_services(
    command: str,
    option: str,
    malformed_hash: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("a malformed hash reached a service")

    for name in (
        "validate_and_write_fixed_korean_foundation_validation_receipt",
        "check_korean_foundation_validation_receipt_continuity",
        "prepare_korean_foundation_snapshot_from_receipt",
        "verify_prepared_korean_foundation_snapshot",
        "activate_prepared_korean_foundation_snapshot_from_receipt",
        "verify_active_korean_foundation_snapshot_provenance",
    ):
        monkeypatch.setattr(cli_module, name, forbidden, raising=False)

    arguments = ["korean-foundations", command]
    if command == "activate":
        arguments.extend(
            [
                "--expected-receipt-sha256",
                RECEIPT_SHA256,
                "--authorization-sha256",
                AUTHORIZATION_SHA256,
            ]
        )
        arguments[arguments.index(option) + 1] = malformed_hash
    else:
        arguments.extend([option, malformed_hash])
    result = runner.invoke(create_app(), arguments)

    assert result.exit_code == 2
    assert "lowercase SHA-256" in result.output
    assert result.exception is not None


@pytest.mark.parametrize(
    "arguments",
    [
        ["check", "--family", "kana"],
        [
            "export",
            "--family",
            "hangul",
            "--format",
            "json",
            "--output",
            "artifact.json",
        ],
        [
            "export",
            "--family",
            "korean-pronunciation",
            "--format",
            "apkg",
            "--output",
            "artifact.apkg",
        ],
    ],
)
def test_unknown_family_and_format_values_are_rejected(arguments: list[str]) -> None:
    result = runner.invoke(create_app(), ["korean-foundations", *arguments])

    assert result.exit_code == 2
    assert "Invalid value" in result.output


def test_every_success_command_routes_only_locked_values_and_emits_exact_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    receipt = _FakeReceipt()
    receipt_sha256 = _receipt_file_sha256(receipt)

    def record(name: str, value: object) -> object:
        calls.append((name, value if isinstance(value, dict) else {}))
        return value

    monkeypatch.setattr(
        cli_module,
        "inspect_fixed_korean_foundation_evidence_inbox",
        lambda: record(
            "inspect-inbox",
            SimpleNamespace(
                complete=True,
                index_sha256=RECEIPT_SHA256,
                evidence_member_count=519,
            ),
        ),
        raising=False,
    )

    def write_receipt(**kwargs: object) -> _FakeReceipt:
        calls.append(("validate-and-write-receipt", kwargs))
        return receipt

    monkeypatch.setattr(
        cli_module,
        "validate_and_write_fixed_korean_foundation_validation_receipt",
        write_receipt,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "check_korean_foundation_validation_receipt_continuity",
        lambda **kwargs: (
            calls.append(("check-receipt", kwargs))
            or SimpleNamespace(
                receipt_sha256=RECEIPT_SHA256,
                evidence_bundle_sha256=BUNDLE_SHA256,
            )
        ),
        raising=False,
    )
    prepared = SimpleNamespace(
        receipt_sha256=RECEIPT_SHA256,
        bundle_sha256=BUNDLE_SHA256,
        snapshot_manifest_sha256=MANIFEST_SHA256,
        snapshot_root_sha256=ROOT_SHA256,
        active_prestate_sha256=PRESTATE_SHA256,
        authorization_sha256=AUTHORIZATION_SHA256,
    )
    monkeypatch.setattr(
        cli_module,
        "prepare_korean_foundation_snapshot_from_receipt",
        lambda **kwargs: (
            calls.append(("prepare-snapshot", kwargs)) or prepared
        ),
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "verify_prepared_korean_foundation_snapshot",
        lambda **kwargs: (
            calls.append(("verify-prepared", kwargs)) or prepared
        ),
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "activate_prepared_korean_foundation_snapshot_from_receipt",
        lambda **kwargs: (
            calls.append(("activate", kwargs))
            or SimpleNamespace(
                activated=True,
                already_active=False,
                receipt_sha256=RECEIPT_SHA256,
                bundle_sha256=BUNDLE_SHA256,
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "verify_active_korean_foundation_snapshot_provenance",
        lambda **kwargs: (
            calls.append(("verify-active", kwargs))
            or SimpleNamespace(
                receipt_sha256=RECEIPT_SHA256,
                bundle_sha256=BUNDLE_SHA256,
                snapshot_root_sha256=ROOT_SHA256,
            )
        ),
        raising=False,
    )

    def build_bundle(**kwargs: object) -> object:
        calls.append(("check", kwargs))
        family = kwargs["family"]
        assert isinstance(family, KoreanFoundationFamily)
        count = 92 if family is KoreanFoundationFamily.HANGUL else 47
        media_count = 184 if family is KoreanFoundationFamily.HANGUL else 141
        return SimpleNamespace(rows=tuple(range(count)), media=tuple(range(media_count)))

    monkeypatch.setattr(
        cli_module,
        "build_korean_foundation_export_bundle",
        build_bundle,
        raising=False,
    )

    def export_foundation(**kwargs: object) -> object:
        calls.append(("export", kwargs))
        return SimpleNamespace(card_count=92, media_count=184)

    monkeypatch.setattr(
        cli_module,
        "export_korean_foundation",
        export_foundation,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "_inspect_fixed_korean_foundation_exports",
        lambda: record(
            "inspect-exports",
            SimpleNamespace(
                artifact_count=6,
                receipt_sha256=RECEIPT_SHA256,
                bundle_sha256=BUNDLE_SHA256,
                snapshot_root_sha256=ROOT_SHA256,
            ),
        ),
        raising=False,
    )

    app = create_app()
    invocations = (
        (
            ["inspect-inbox"],
            [
                "inbox_status=complete_unvalidated",
                f"evidence_index_sha256={RECEIPT_SHA256}",
                "declared_member_count=519",
            ],
        ),
        (
            [
                "validate-and-write-receipt",
                "--confirmed-index-sha256",
                RECEIPT_SHA256,
            ],
            [
                "receipt_write_status=written",
                f"receipt_sha256={receipt_sha256}",
                f"bundle_sha256={BUNDLE_SHA256}",
            ],
        ),
        (
            ["check-receipt", "--expected-receipt-sha256", RECEIPT_SHA256],
            [
                "receipt_status=continuous",
                f"receipt_sha256={RECEIPT_SHA256}",
                f"bundle_sha256={BUNDLE_SHA256}",
            ],
        ),
        (
            ["prepare-snapshot", "--expected-receipt-sha256", RECEIPT_SHA256],
            [
                f"receipt_sha256={RECEIPT_SHA256}",
                f"bundle_sha256={BUNDLE_SHA256}",
                f"snapshot_manifest_sha256={MANIFEST_SHA256}",
                f"snapshot_root_sha256={ROOT_SHA256}",
                f"active_prestate_sha256={PRESTATE_SHA256}",
                f"authorization_sha256={AUTHORIZATION_SHA256}",
                "snapshot_status=prepared_inactive",
            ],
        ),
        (
            ["verify-prepared", "--expected-receipt-sha256", RECEIPT_SHA256],
            [
                f"receipt_sha256={RECEIPT_SHA256}",
                f"bundle_sha256={BUNDLE_SHA256}",
                f"snapshot_manifest_sha256={MANIFEST_SHA256}",
                f"snapshot_root_sha256={ROOT_SHA256}",
                f"active_prestate_sha256={PRESTATE_SHA256}",
                f"authorization_sha256={AUTHORIZATION_SHA256}",
                "prepared_status=verified",
            ],
        ),
        (
            [
                "activate",
                "--expected-receipt-sha256",
                RECEIPT_SHA256,
                "--authorization-sha256",
                AUTHORIZATION_SHA256,
            ],
            [
                "activation_status=activated",
                f"receipt_sha256={RECEIPT_SHA256}",
                f"bundle_sha256={BUNDLE_SHA256}",
            ],
        ),
        (
            ["verify-active", "--expected-receipt-sha256", RECEIPT_SHA256],
            [
                "active_status=verified",
                f"receipt_sha256={RECEIPT_SHA256}",
                f"bundle_sha256={BUNDLE_SHA256}",
                f"snapshot_root_sha256={ROOT_SHA256}",
            ],
        ),
        (
            ["check", "--family", "hangul"],
            [
                "family=hangul",
                "readiness_status=ready",
                "card_count=92",
                "media_count=184",
            ],
        ),
        (
            [
                "export",
                "--family",
                "hangul",
                "--format",
                "apkg",
                "--output",
                str(tmp_path / "hangul.apkg"),
            ],
            [
                "family=hangul",
                "format=apkg",
                "export_status=written",
                "card_count=92",
                "media_count=184",
            ],
        ),
        (
            ["inspect-exports"],
            [
                "export_set_status=verified",
                "artifact_count=6",
                f"receipt_sha256={RECEIPT_SHA256}",
                f"bundle_sha256={BUNDLE_SHA256}",
                f"snapshot_root_sha256={ROOT_SHA256}",
            ],
        ),
    )
    for arguments, expected_lines in invocations:
        result = runner.invoke(app, ["korean-foundations", *arguments])
        assert result.exit_code == 0, result.output
        assert result.output.splitlines() == expected_lines
        assert str(tmp_path) not in result.output

    assert calls == [
        ("inspect-inbox", {}),
        (
            "validate-and-write-receipt",
            {"confirmed_index_sha256": RECEIPT_SHA256},
        ),
        (
            "check-receipt",
            {"expected_receipt_sha256": RECEIPT_SHA256},
        ),
        (
            "prepare-snapshot",
            {"expected_receipt_sha256": RECEIPT_SHA256},
        ),
        (
            "verify-prepared",
            {"expected_receipt_sha256": RECEIPT_SHA256},
        ),
        (
            "activate",
            {
                "expected_receipt_sha256": RECEIPT_SHA256,
                "authorization_sha256": AUTHORIZATION_SHA256,
            },
        ),
        (
            "verify-active",
            {"expected_receipt_sha256": RECEIPT_SHA256},
        ),
        ("check", {"family": KoreanFoundationFamily.HANGUL}),
        (
            "export",
            {
                "family": KoreanFoundationFamily.HANGUL,
                "export_format": cli_module.ExportArtifactFormat.APKG,
                "output_destination": tmp_path / "hangul.apkg",
            },
        ),
        ("inspect-exports", {}),
    ]


def test_combined_receipt_writer_reports_idempotent_current_without_new_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _FakeReceipt(_receipt_write_status="already_current")
    calls: list[dict[str, object]] = []

    def writer(**kwargs: object) -> _FakeReceipt:
        calls.append(kwargs)
        return receipt

    monkeypatch.setattr(
        cli_module,
        "validate_and_write_fixed_korean_foundation_validation_receipt",
        writer,
        raising=False,
    )
    result = runner.invoke(
        create_app(),
        [
            "korean-foundations",
            "validate-and-write-receipt",
            "--confirmed-index-sha256",
            RECEIPT_SHA256,
        ],
    )

    assert result.exit_code == 0
    assert result.output.splitlines()[0] == "receipt_write_status=already_current"
    assert calls == [{"confirmed_index_sha256": RECEIPT_SHA256}]
    group = _foundation_group()
    for forbidden_command in (
        "validate-object",
        "write-object",
        "write-receipt",
        "repair-receipt",
    ):
        assert forbidden_command not in group.commands


def test_service_failures_are_content_free_and_unexpected_errors_are_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "C:/private/reviewer/민감한-source.json"

    def invalid() -> object:
        raise ValueError(secret)

    monkeypatch.setattr(
        cli_module,
        "inspect_fixed_korean_foundation_evidence_inbox",
        invalid,
        raising=False,
    )
    controlled = runner.invoke(
        create_app(), ["korean-foundations", "inspect-inbox"]
    )
    assert controlled.exit_code == 1
    assert controlled.output == "korean_foundations_error=operation_failed\n"
    assert secret not in controlled.output

    def unexpected() -> object:
        raise RuntimeError("programmer failure")

    monkeypatch.setattr(
        cli_module,
        "inspect_fixed_korean_foundation_evidence_inbox",
        unexpected,
        raising=False,
    )
    unhandled = runner.invoke(
        create_app(), ["korean-foundations", "inspect-inbox"]
    )
    assert isinstance(unhandled.exception, RuntimeError)
    assert unhandled.output == ""


def test_production_defaults_refuse_before_writes_without_candidate_or_runtime_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = _tree_digest(CANONICAL_STATE_PATHS)
    candidate_paths = {path.resolve(strict=False) for path in CANONICAL_CANDIDATES}
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path.resolve(strict=False) in candidate_paths:
            raise AssertionError("production refusal fell back to top-level candidates")
        return original_read_bytes(path)

    def forbidden_construction(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("foundation CLI constructed a runtime/provider/DB service")

    with monkeypatch.context() as context:
        context.setattr(Path, "read_bytes", guarded_read_bytes)
        context.setattr(cli_module, "build_runtime_service", forbidden_construction)
        context.setattr(
            cli_module,
            "KiwiKoreanMorphologyService",
            forbidden_construction,
        )
        context.setattr(
            cli_module,
            "LexicalGroundingService",
            forbidden_construction,
        )
        context.setattr(socket, "create_connection", forbidden_construction)
        context.setattr(socket.socket, "connect", forbidden_construction)

        app = create_app()
        refusal_cases = (
            (["inspect-inbox"], "inbox_incomplete"),
            (
                [
                    "validate-and-write-receipt",
                    "--confirmed-index-sha256",
                    "0" * 64,
                ],
                "index_missing",
            ),
            (
                ["check-receipt", "--expected-receipt-sha256", "0" * 64],
                "receipt_missing",
            ),
            (
                ["prepare-snapshot", "--expected-receipt-sha256", "0" * 64],
                "receipt_missing",
            ),
            (
                ["verify-prepared", "--expected-receipt-sha256", "0" * 64],
                "receipt_missing",
            ),
            (
                [
                    "activate",
                    "--expected-receipt-sha256",
                    "0" * 64,
                    "--authorization-sha256",
                    "1" * 64,
                ],
                "receipt_missing",
            ),
            (
                ["verify-active", "--expected-receipt-sha256", "0" * 64],
                "receipt_missing",
            ),
            (["check", "--family", "hangul"], "production_not_active"),
            (["inspect-exports"], "production_not_active"),
        )
        for arguments, expected_reason in refusal_cases:
            result = runner.invoke(app, ["korean-foundations", *arguments])
            assert result.exit_code == 1
            assert result.output == f"korean_foundations_error={expected_reason}\n"
            assert str(Path.cwd()) not in result.output

        for family in ("hangul", "pronunciation"):
            for format_name in ("apkg", "csv", "tsv"):
                destination = tmp_path / (
                    f"{family}.apkg" if format_name == "apkg" else f"{family}-{format_name}"
                )
                result = runner.invoke(
                    app,
                    [
                        "korean-foundations",
                        "export",
                        "--family",
                        family,
                        "--format",
                        format_name,
                        "--output",
                        str(destination),
                    ],
                )
                assert result.exit_code == 1
                assert result.output == (
                    "korean_foundations_error=production_not_active\n"
                )
                assert not destination.exists()
        assert list(tmp_path.iterdir()) == []

    assert _tree_digest(CANONICAL_STATE_PATHS) == before


def test_foundation_callbacks_do_not_route_through_existing_runtime_construction() -> None:
    group = _foundation_group()
    forbidden_fragments = (
        "resolve_service(",
        "build_runtime_service(",
        "KiwiKoreanMorphologyService(",
        "AzureSpeechAdapter(",
        "Tatoeba",
        "wordfreq",
        "create_engine(",
    )
    for command in group.commands.values():
        source = inspect.getsource(command.callback)
        assert not any(fragment in source for fragment in forbidden_fragments)
