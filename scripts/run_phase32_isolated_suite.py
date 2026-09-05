"""Credential-empty Phase 32 isolated-suite harness."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable

from multilang.services.korean_foundation_snapshot import verify_active_korean_foundation_snapshot_provenance


_FORBIDDEN_ENV_FRAGMENTS = (
    "KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "OPENAI",
    "AZURE",
    "DEEPL",
    "LITELLM",
    "OPENROUTER",
)

FULL_SUITE_TIMEOUT_SECONDS = 3600
_SAFE_ENV_NAMES = {
    "LANG",
    "LC_ALL",
    "PATH",
    "PYTHONPATH",
    "TERM",
    "TZ",
    "UV_PROJECT_ENVIRONMENT",
}
_GUARD_SITE_CUSTOMIZE = r'''
from __future__ import annotations

import builtins
import importlib
import json
import os
from pathlib import Path
import socket


_BLOCKED_PROVIDER_MODULE_PREFIXES = (
    "anthropic",
    "azure.cognitiveservices",
    "deepl",
    "deep_translator",
    "google.cloud",
    "google.generativeai",
    "litellm",
    "openai",
)
_ORIGINAL_IMPORT = builtins.__import__
_ORIGINAL_IMPORT_MODULE = importlib.import_module


def _record(kind: str, detail: str) -> None:
    report = os.environ.get("PHASE32_GUARD_REPORT")
    if not report:
        return
    try:
        path = Path(report)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": kind, "detail": detail}, sort_keys=True) + "\n")
    except OSError:
        pass


def _blocked_create_connection(*_args: object, **_kwargs: object) -> object:
    _record("network", "socket.create_connection")
    raise AssertionError("Phase 32 isolated suite blocked network access")


def _blocked_connect(_self: object, *_args: object, **_kwargs: object) -> object:
    _record("network", "socket.socket.connect")
    raise AssertionError("Phase 32 isolated suite blocked network access")


def _blocked_getaddrinfo(*_args: object, **_kwargs: object) -> object:
    _record("network", "socket.getaddrinfo")
    raise AssertionError("Phase 32 isolated suite blocked DNS access")


def _blocked_gethostbyname(*_args: object, **_kwargs: object) -> object:
    _record("network", "socket.gethostbyname")
    raise AssertionError("Phase 32 isolated suite blocked DNS access")


def _is_blocked_provider_module(name: str) -> bool:
    return any(name == prefix or name.startswith(prefix + ".") for prefix in _BLOCKED_PROVIDER_MODULE_PREFIXES)


def _blocked_import(name: str, globals: object = None, locals: object = None, fromlist: object = (), level: int = 0) -> object:
    if level == 0 and _is_blocked_provider_module(name):
        _record("provider", name)
        raise AssertionError("Phase 32 isolated suite blocked provider import")
    return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)


def _blocked_import_module(name: str, package: str | None = None) -> object:
    if _is_blocked_provider_module(name):
        _record("provider", name)
        raise AssertionError("Phase 32 isolated suite blocked provider import")
    return _ORIGINAL_IMPORT_MODULE(name, package)


socket.create_connection = _blocked_create_connection
socket.socket.connect = _blocked_connect
socket.getaddrinfo = _blocked_getaddrinfo
socket.gethostbyname = _blocked_gethostbyname
builtins.__import__ = _blocked_import
importlib.import_module = _blocked_import_module
'''


def build_isolated_environment(source: dict[str, str] | None = None, *, root: Path) -> dict[str, str]:
    base = dict(source or os.environ)
    clean = {
        key: value
        for key, value in base.items()
        if key in _SAFE_ENV_NAMES
        and not any(fragment in key.upper() for fragment in _FORBIDDEN_ENV_FRAGMENTS)
    }
    clean["HOME"] = str(root / "home")
    clean["TMPDIR"] = str(root / "tmp")
    clean["XDG_CACHE_HOME"] = str(root / "xdg-cache")
    clean["XDG_CONFIG_HOME"] = str(root / "xdg-config")
    clean["UV_OFFLINE"] = "1"
    clean["MULTILANG_FORBID_NETWORK"] = "1"
    clean["MULTILANG_FORBID_PROVIDERS"] = "1"
    return clean


def build_pytest_argv(test_paths: Iterable[str]) -> list[str]:
    return ["uv", "run", "--frozen", "--no-sync", "pytest", *list(test_paths)]


def build_full_pytest_argv(project_root: Path) -> list[str]:
    return [
        "uv",
        "run",
        "--project",
        str(project_root),
        "--frozen",
        "--no-sync",
        "pytest",
        str(project_root / "tests"),
    ]


def run_full(
    *,
    preflight_file: Path,
    work_root: Path,
    project_root: Path = Path("."),
    runner=subprocess.run,
    source_environment: dict[str, str] | None = None,
) -> dict[str, object]:
    preflight = json.loads(preflight_file.read_text(encoding="utf-8"))
    if preflight.get("status") != "ready" or preflight.get("shared_venv_unchanged") is not True:
        raise ValueError("pre-source preflight is not ready")

    project_root = project_root.resolve()
    tests_root = project_root / "tests"
    guard_root = work_root / "guard"
    guard_root.mkdir(parents=True, exist_ok=True)
    guard_report = guard_root / "attempts.jsonl"
    (guard_root / "sitecustomize.py").write_text(_GUARD_SITE_CUSTOMIZE, encoding="utf-8")

    environment = build_isolated_environment(source_environment, root=work_root)
    environment["PHASE32_GUARD_REPORT"] = str(guard_report)
    existing_pythonpath = environment.get("PYTHONPATH")
    pythonpath_parts = [str(guard_root), str(project_root / "src")]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    credential_names = _forbidden_environment_names(environment)
    if credential_names:
        raise ValueError("isolated environment still contains credential names")

    timeout_seconds = FULL_SUITE_TIMEOUT_SECONDS
    try:
        completed = runner(
            build_full_pytest_argv(project_root),
            cwd=project_root,
            env=environment,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
        )
        stdout = _process_output_text(getattr(completed, "stdout", ""))
        stderr = _process_output_text(getattr(completed, "stderr", ""))
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = _process_output_text(exc.output)
        stderr = _process_output_text(exc.stderr)
        returncode = None
        timeout_seconds = int(exc.timeout)
        timed_out = True
    network_attempt_count, provider_attempt_count = _guard_attempt_counts(guard_report)
    if timed_out:
        status = "timed_out"
    elif returncode == 0 and not network_attempt_count and not provider_attempt_count:
        status = "passed"
    else:
        status = "failed"
    protected_unchanged = preflight.get("status") == "ready" and preflight.get("shared_venv_unchanged") is True
    report = {
        "mode": "full",
        "status": status,
        "pytest_scope": "tests",
        "pytest_argv": build_full_pytest_argv(project_root),
        "pytest_returncode": returncode,
        "stdout_sha256": sha256(stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": sha256(stderr.encode("utf-8")).hexdigest(),
        "timeout_seconds": timeout_seconds,
        "network_attempt_count": network_attempt_count,
        "provider_attempt_count": provider_attempt_count,
        "credential_name_count": 0,
        "protected_roots_unchanged": protected_unchanged,
        "shared_venv_unchanged": preflight.get("shared_venv_unchanged") is True,
        "dependencies_unchanged": protected_unchanged,
        "recursive_suite_invoked": False,
        "shell": False,
    }
    return report


def _process_output_text(output: object) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return str(output)


def _forbidden_environment_names(environment: dict[str, str]) -> list[str]:
    return sorted(
        name
        for name in environment
        if any(fragment in name.upper() for fragment in _FORBIDDEN_ENV_FRAGMENTS)
    )


def _guard_attempt_counts(report_path: Path) -> tuple[int, int]:
    network = 0
    provider = 0
    if not report_path.exists():
        return network, provider
    for line in report_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("kind") == "network":
            network += 1
        elif event.get("kind") == "provider":
            provider += 1
    return network, provider


def run_dependency_only(
    *,
    expected_receipt_sha256: str,
    expected_snapshot_manifest_sha256: str | None = None,
    expected_snapshot_root_sha256: str | None = None,
    verifier=verify_active_korean_foundation_snapshot_provenance,
    command_inventory: tuple[str, ...],
    protected_paths: tuple[Path, ...],
) -> dict[str, object]:
    report = verifier(expected_receipt_sha256=expected_receipt_sha256)
    expected = {
        "receipt_sha256": expected_receipt_sha256,
        "snapshot_manifest_sha256": expected_snapshot_manifest_sha256,
        "snapshot_root_sha256": expected_snapshot_root_sha256,
    }
    for field, value in expected.items():
        if value is not None and getattr(report, field, None) != value:
            raise ValueError("Phase 31 active authority drift")
    return {
        "mode": "dependency-only",
        "shell": False,
        "network_attempt_count": 0,
        "provider_attempt_count": 0,
        "recursive_suite_invoked": False,
        "phase31": {
            "receipt_sha256": getattr(report, "receipt_sha256", expected_receipt_sha256),
            "snapshot_manifest_sha256": getattr(report, "snapshot_manifest_sha256", None),
            "snapshot_root_sha256": getattr(report, "snapshot_root_sha256", None),
        },
        "command_inventory": list(command_inventory),
        "protected_paths_sha256": _protected_paths_sha256(protected_paths),
    }


def _protected_paths_sha256(paths: tuple[Path, ...]) -> str:
    payload = [str(path) for path in paths]
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 32 isolated-suite checks without live credentials.")
    parser.add_argument("--mode", choices=("dependency-only", "full"), default="dependency-only")
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--expected-snapshot-manifest-sha256")
    parser.add_argument("--expected-snapshot-root-sha256")
    parser.add_argument("--preflight-file", type=Path)
    parser.add_argument("--dependency-output", type=Path)
    parser.add_argument("--readiness-output", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "full":
        if args.preflight_file is None or args.dependency_output is None:
            raise SystemExit("full mode requires --preflight-file and --dependency-output")
        with tempfile.TemporaryDirectory(prefix="phase32-pre-source-suite-", dir="/tmp/opencode") as work_root:
            report = run_full(
                preflight_file=args.preflight_file,
                work_root=Path(work_root),
            )
        dependency_report = {
            "mode": "pre-source-dependency-evidence",
            "dependencies_unchanged": report["dependencies_unchanged"],
            "protected_roots_unchanged": report["protected_roots_unchanged"],
            "shared_venv_unchanged": report["shared_venv_unchanged"],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.dependency_output.write_text(json.dumps(dependency_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.readiness_output is not None:
            args.readiness_output.write_text(_render_readiness(report, dependency_report), encoding="utf-8")
        return 0 if report["status"] == "passed" else 1
    report = run_dependency_only(
        expected_receipt_sha256=args.expected_receipt_sha256,
        expected_snapshot_manifest_sha256=args.expected_snapshot_manifest_sha256,
        expected_snapshot_root_sha256=args.expected_snapshot_root_sha256,
        command_inventory=("multilang --help", "scripts/run_phase32_isolated_suite.py --help"),
        protected_paths=(Path("pyproject.toml"), Path("uv.lock")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _render_readiness(report: dict[str, object], dependency_report: dict[str, object]) -> str:
    return (
        "# Phase 32 Pre-Source Readiness\n\n"
        f"- Suite status: `{report['status']}`\n"
        f"- Pytest scope: `{report['pytest_scope']}`\n"
        f"- Network attempts: `{report['network_attempt_count']}`\n"
        f"- Provider attempts: `{report['provider_attempt_count']}`\n"
        f"- Credential names: `{report['credential_name_count']}`\n"
        f"- Dependencies unchanged: `{dependency_report['dependencies_unchanged']}`\n"
        f"- Protected roots unchanged: `{report['protected_roots_unchanged']}`\n"
        f"- Shared `.venv` unchanged: `{report['shared_venv_unchanged']}`\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
