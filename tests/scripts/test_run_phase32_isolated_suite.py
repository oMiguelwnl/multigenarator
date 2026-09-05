"""Tests for the Phase 32 isolated-suite harness."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


def _load_script_module():
    script_path = Path("scripts/run_phase32_isolated_suite.py")
    spec = importlib.util.spec_from_file_location("run_phase32_isolated_suite", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_isolated_suite_environment_strips_credentials_and_uses_fixed_shell_false_argv(tmp_path: Path) -> None:
    module = _load_script_module()
    env = module.build_isolated_environment(
        {
            "PATH": "/usr/bin",
            "HOME": "/home/private",
            "MULTILANG_AZURE_SPEECH_KEY": "secret",
            "OPENAI_API_KEY": "secret",
            "DEEPL_API_KEY": "secret",
        },
        root=tmp_path,
    )

    assert env["HOME"].startswith(str(tmp_path))
    assert "MULTILANG_AZURE_SPEECH_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "DEEPL_API_KEY" not in env
    assert module.build_pytest_argv(["tests/services/test_korean_audio.py"]) == [
        "uv",
        "run",
        "--frozen",
        "--no-sync",
        "pytest",
        "tests/services/test_korean_audio.py",
    ]


def test_dependency_only_report_verifies_phase31_inventory_without_recursive_suite(tmp_path: Path) -> None:
    module = _load_script_module()
    calls: list[object] = []

    def verifier(*, expected_receipt_sha256: str) -> object:
        calls.append(("verify_phase31", expected_receipt_sha256))
        return type(
            "Report",
            (),
            {
                "receipt_sha256": "a" * 64,
                "snapshot_manifest_sha256": "b" * 64,
                "snapshot_root_sha256": "c" * 64,
            },
        )()

    report = module.run_dependency_only(
        expected_receipt_sha256="a" * 64,
        verifier=verifier,
        command_inventory=("multilang --help", "run_phase32_isolated_suite.py --help"),
        protected_paths=(tmp_path,),
    )

    assert calls == [("verify_phase31", "a" * 64)]
    assert report["mode"] == "dependency-only"
    assert report["shell"] is False
    assert report["network_attempt_count"] == 0
    assert report["provider_attempt_count"] == 0
    assert report["recursive_suite_invoked"] is False
    assert report["command_inventory"] == ["multilang --help", "run_phase32_isolated_suite.py --help"]


def test_dependency_only_report_blocks_phase31_drift(tmp_path: Path) -> None:
    module = _load_script_module()

    def verifier(*, expected_receipt_sha256: str) -> object:
        return type(
            "Report",
            (),
            {
                "receipt_sha256": expected_receipt_sha256,
                "snapshot_manifest_sha256": "0" * 64,
                "snapshot_root_sha256": "c" * 64,
            },
        )()

    with pytest.raises(ValueError, match="Phase 31 active authority drift"):
        module.run_dependency_only(
            expected_receipt_sha256="a" * 64,
            expected_snapshot_manifest_sha256="b" * 64,
            expected_snapshot_root_sha256="c" * 64,
            verifier=verifier,
            command_inventory=(),
            protected_paths=(tmp_path,),
        )


def test_full_report_runs_complete_tests_with_guarded_environment(tmp_path: Path) -> None:
    module = _load_script_module()
    calls: list[dict[str, object]] = []
    project_root = tmp_path / "repo"
    project_root.mkdir()
    tests_root = project_root / "tests"
    tests_root.mkdir()
    (project_root / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    (project_root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    preflight = tmp_path / "preflight.json"
    preflight.write_text(
        '{"status":"ready","shared_venv_unchanged":true,"protected_roots":{"pyproject.toml":{"tree_sha256":"p"}}}',
        encoding="utf-8",
    )

    def runner(argv: list[str], **kwargs: object) -> object:
        calls.append({"argv": argv, **kwargs})
        assert "pytest" in argv
        assert argv[-1] == str(tests_root)
        env = kwargs["env"]
        assert isinstance(env, dict)
        assert env["UV_OFFLINE"] == "1"
        assert env["MULTILANG_FORBID_NETWORK"] == "1"
        assert env["MULTILANG_FORBID_PROVIDERS"] == "1"
        assert "MULTILANG_DATABASE_URL" not in env
        assert "MULTILANG_TEXT_GENERATION_PROVIDER" not in env
        assert "MULTILANG_TRANSLATION_PROVIDER" not in env
        assert "OPENAI_API_KEY" not in env
        assert "DEEPL_API_KEY" not in env
        assert "AZURE_SPEECH_KEY" not in env
        return SimpleNamespace(returncode=0, stdout="1 passed\n", stderr="")

    report = module.run_full(
        preflight_file=preflight,
        work_root=tmp_path / "work",
        project_root=project_root,
        runner=runner,
        source_environment={
            "PATH": "/usr/bin",
            "OPENAI_API_KEY": "secret",
            "DEEPL_API_KEY": "secret",
            "AZURE_SPEECH_KEY": "secret",
        },
    )

    assert len(calls) == 1
    assert calls[0]["shell"] is False
    assert calls[0]["timeout"] == module.FULL_SUITE_TIMEOUT_SECONDS
    assert report["status"] == "passed"
    assert report["pytest_scope"] == "tests"
    assert report["network_attempt_count"] == 0
    assert report["provider_attempt_count"] == 0
    assert report["credential_name_count"] == 0
    assert report["protected_roots_unchanged"] is True
    assert report["shared_venv_unchanged"] is True


def test_full_report_blocks_when_preflight_is_not_ready(tmp_path: Path) -> None:
    module = _load_script_module()
    preflight = tmp_path / "preflight.json"
    preflight.write_text('{"status":"blocked"}', encoding="utf-8")

    with pytest.raises(ValueError, match="pre-source preflight is not ready"):
        module.run_full(
            preflight_file=preflight,
            work_root=tmp_path / "work",
            project_root=tmp_path,
            runner=lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
            source_environment={},
        )


def test_full_report_records_timeout_without_traceback(tmp_path: Path) -> None:
    module = _load_script_module()
    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "tests").mkdir()
    preflight = tmp_path / "preflight.json"
    preflight.write_text(
        '{"status":"ready","shared_venv_unchanged":true,"protected_roots":{}}',
        encoding="utf-8",
    )

    def runner(argv: list[str], **_kwargs: object) -> object:
        raise subprocess.TimeoutExpired(argv, timeout=7, output="partial", stderr="slow")

    report = module.run_full(
        preflight_file=preflight,
        work_root=tmp_path / "work",
        project_root=project_root,
        runner=runner,
        source_environment={"PATH": "/usr/bin"},
    )

    assert report["status"] == "timed_out"
    assert report["timeout_seconds"] == 7
    assert report["pytest_returncode"] is None
    assert report["network_attempt_count"] == 0
    assert report["provider_attempt_count"] == 0


def test_full_cli_uses_external_temp_work_root_and_writes_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_script_module()
    work_roots: list[Path] = []

    def fake_run_full(**kwargs: object) -> dict[str, object]:
        work_root = kwargs["work_root"]
        assert isinstance(work_root, Path)
        work_roots.append(work_root)
        return {
            "credential_name_count": 0,
            "dependencies_unchanged": True,
            "mode": "full",
            "network_attempt_count": 0,
            "protected_roots_unchanged": True,
            "provider_attempt_count": 0,
            "pytest_scope": "tests",
            "shared_venv_unchanged": True,
            "status": "passed",
        }

    monkeypatch.setattr(module, "run_full", fake_run_full)
    suite_output = tmp_path / "suite.json"
    dependency_output = tmp_path / "dependency.json"
    readiness_output = tmp_path / "readiness.md"

    assert module.main(
        [
            "--mode",
            "full",
            "--expected-receipt-sha256",
            "0" * 64,
            "--preflight-file",
            str(tmp_path / "preflight.json"),
            "--dependency-output",
            str(dependency_output),
            "--readiness-output",
            str(readiness_output),
            "--output",
            str(suite_output),
        ]
    ) == 0

    assert work_roots and work_roots[0].as_posix().startswith("/tmp/opencode/phase32-pre-source-suite-")
    assert suite_output.is_file()
    assert dependency_output.is_file()
    assert readiness_output.is_file()


def test_full_guard_blocks_dns_and_real_provider_imports(tmp_path: Path) -> None:
    module = _load_script_module()
    guard_root = tmp_path / "guard"
    guard_root.mkdir()
    report = tmp_path / "attempts.jsonl"
    (guard_root / "sitecustomize.py").write_text(module._GUARD_SITE_CUSTOMIZE, encoding="utf-8")

    child = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib,socket\n"
            "for action in (lambda: socket.getaddrinfo('example.com', 443), "
            "lambda: importlib.import_module('deepl')):\n"
            "    try:\n"
            "        action()\n"
            "    except AssertionError:\n"
            "        pass\n",
        ],
        env={"PYTHONPATH": str(guard_root), "PHASE32_GUARD_REPORT": str(report)},
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert child.returncode == 0
    assert module._guard_attempt_counts(report) == (1, 1)
