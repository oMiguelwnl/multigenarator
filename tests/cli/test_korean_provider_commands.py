"""CLI coverage for staged Korean frequency provider/text commands."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typer.main import get_command
from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app
from multilang.db.provisioning import ensure_database_schema
from multilang.domain.jobs import SupportedLanguage
from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate, ProviderCallLogRepository
from multilang.runtime import RuntimeTextResult


runner = CliRunner()

HASHES = tuple(f"{index:x}" * 64 for index in range(1, 16))


def _base_args(tmp_path: Path) -> list[str]:
    bundle_root = tmp_path / "bundle"
    return [
        "--database-url",
        f"sqlite+pysqlite:///{tmp_path / 'korean.db'}",
        "--job-id",
        "job-ko",
        "--phase31-active-pointer-sha256",
        HASHES[0],
        "--phase31-active-pointer-content-sha256",
        HASHES[1],
        "--phase31-validation-receipt-sha256",
        HASHES[2],
        "--phase31-snapshot-manifest-sha256",
        HASHES[3],
        "--phase31-snapshot-root-sha256",
        HASHES[4],
        "--frequency-bundle-root",
        str(bundle_root),
        "--frequency-bundle-manifest-sha256",
        HASHES[5],
        "--frequency-bundle-content-sha256",
        HASHES[6],
        "--source-retrieval-sha256",
        HASHES[7],
        "--source-build-result-sha256",
        HASHES[8],
        "--source-review-aggregate-sha256",
        HASHES[9],
        "--provider-policy-sha256",
        HASHES[10],
        "--pilot-authority-sha256",
        HASHES[11],
        "--binding-receipt-sha256",
        HASHES[9],
    ]


def _full_args(tmp_path: Path) -> list[str]:
    return [
        *_base_args(tmp_path),
        "--catalog-locator-sha256",
        HASHES[12],
        "--catalog-content-sha256",
        HASHES[13],
        "--profile-sample-authority-sha256",
        HASHES[14],
        "--provider-review-authority-sha256",
        "a" * 64,
        "--heard-review-authority-sha256",
        "b" * 64,
    ]


def _options(command_name: str) -> tuple[str, ...]:
    root = get_command(create_app())
    command = root.commands.get(command_name)
    assert isinstance(command, click.Command)
    return tuple(option for parameter in command.params for option in parameter.opts)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_korean_frequency_text_commands_expose_only_explicit_authority_options() -> None:
    expected_common = {
        "--database-url",
        "--job-id",
        "--phase31-active-pointer-sha256",
        "--phase31-active-pointer-content-sha256",
        "--phase31-validation-receipt-sha256",
        "--phase31-snapshot-manifest-sha256",
        "--phase31-snapshot-root-sha256",
        "--frequency-bundle-root",
        "--frequency-bundle-manifest-sha256",
        "--frequency-bundle-content-sha256",
        "--source-retrieval-sha256",
        "--source-build-result-sha256",
        "--source-review-aggregate-sha256",
        "--provider-policy-sha256",
        "--pilot-authority-sha256",
        "--binding-receipt-sha256",
    }
    expected_audio = {
        "--catalog-locator-sha256",
        "--catalog-content-sha256",
        "--profile-sample-authority-sha256",
        "--provider-review-authority-sha256",
        "--heard-review-authority-sha256",
    }

    assert expected_common <= set(_options("prepare-korean-frequency-job"))
    assert expected_common | expected_audio <= set(_options("bind-korean-frequency-audio-authority"))
    assert expected_common | expected_audio <= set(_options("check-korean-frequency-job-binding"))
    assert expected_common | expected_audio | {"--max-items", "--missing-only", "--synthesize-audio"} <= set(
        _options("generate-korean-frequency-text")
    )
    for command_name in (
        "prepare-korean-frequency-job",
        "bind-korean-frequency-audio-authority",
        "check-korean-frequency-job-binding",
        "generate-korean-frequency-text",
    ):
        options = set(_options(command_name))
        assert "--provider" not in options
        assert "--model" not in options
        assert "--fallback-provider" not in options
        assert "--phase31-path" not in options


def test_korean_review_and_audio_commands_expose_explicit_authority_options() -> None:
    expected_review_import = {"--batch-file", "--receipt-file"}
    expected_review_apply = {"--database-url", "--job-id", "--aggregate-file", "--authority-file", "--mode"}
    expected_audio = {
        "--database-url",
        "--job-id",
        "--phase31-validation-receipt-sha256",
        "--phase31-snapshot-manifest-sha256",
        "--phase31-snapshot-root-sha256",
        "--binding-receipt-sha256",
        "--provider-policy-sha256",
        "--pilot-authority-sha256",
        "--catalog-locator-sha256",
        "--catalog-content-sha256",
        "--profile-sample-authority-sha256",
    }

    assert expected_review_import <= set(_options("import-korean-production-text-review-batch"))
    assert expected_review_apply <= set(_options("apply-korean-frequency-text-review"))
    assert expected_audio | {"--endpoint-url", "--catalog-result-file"} <= set(_options("capture-korean-azure-catalog"))
    assert expected_audio | {"--catalog-result-file", "--voice-profile-file", "--max-items", "--missing-only"} <= set(
        _options("synthesize-korean-frequency-audio")
    )
    assert expected_audio | {"--pilot-result-file", "--evidence-file"} <= set(
        _options("validate-korean-audio-pilot-result")
    )
    assert {"--batch-file", "--receipt-file"} <= set(_options("import-korean-production-audio-review-batch"))
    assert {"--database-url", "--job-id", "--aggregate-file", "--authority-file", "--mode"} <= set(
        _options("apply-korean-frequency-audio-review")
    )
    for command_name in (
        "import-korean-production-text-review-batch",
        "apply-korean-frequency-text-review",
        "capture-korean-azure-catalog",
        "synthesize-korean-frequency-audio",
        "validate-korean-audio-pilot-result",
        "import-korean-production-audio-review-batch",
        "apply-korean-frequency-audio-review",
    ):
        options = set(_options(command_name))
        assert "--provider" not in options
        assert "--model" not in options
        assert "--fallback-provider" not in options


def test_provider_catalog_result_validator_cli_exposes_read_only_inputs() -> None:
    options = set(_options("validate-korean-provider-catalog-pilot-result"))

    assert {
        "--database-url",
        "--job-id",
        "--phase31-active-pointer-sha256",
        "--phase31-active-pointer-content-sha256",
        "--phase31-validation-receipt-sha256",
        "--phase31-snapshot-manifest-sha256",
        "--phase31-snapshot-root-sha256",
        "--frequency-bundle-root",
        "--frequency-bundle-manifest-sha256",
        "--frequency-bundle-content-sha256",
        "--source-retrieval-sha256",
        "--source-build-result-sha256",
        "--source-review-aggregate-sha256",
        "--provider-policy-sha256",
        "--pilot-authority-sha256",
        "--binding-receipt-sha256",
        "--catalog-locator-sha256",
        "--catalog-content-sha256",
        "--final-authority-sha256",
        "--binding-receipt-file",
        "--frequency-bundle-manifest-file",
        "--source-retrieval-authority-file",
        "--source-build-authority-file",
        "--source-review-aggregate-file",
        "--final-authority-file",
        "--provider-policy-file",
        "--pilot-authority-file",
        "--text-result-file",
        "--catalog-result-file",
        "--expected-item-count",
        "--evidence-file",
    } <= options
    assert "--provider" not in options
    assert "--model" not in options
    assert "--fallback-provider" not in options


def test_validate_korean_provider_catalog_pilot_result_reconciles_rows_and_writes_read_only_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'korean.db'}"
    engine = create_engine(database_url)
    ensure_database_schema(engine, database_url)
    session = Session(engine)
    try:
        repository = ProviderCallLogRepository(session)
        repository.insert(
            ProviderCallLogCreate(
                job_id="job-ko",
                item_key="sample-1",
                operation="definition",
                provider="openai",
                model="gpt-fixture",
                status="success",
                attempt=1,
                latency_ms=100,
                route_policy_sha256=HASHES[10],
                budget_snapshot_sha256=HASHES[11],
                cache_key_sha256=HASHES[12],
                response_schema_sha256=HASHES[13],
                input_tokens=10,
                output_tokens=20,
                total_tokens=30,
                estimated_cost=0.01,
            )
        )
        repository.insert(
            ProviderCallLogCreate(
                job_id="job-ko",
                item_key="catalog",
                operation="catalog",
                provider="azure",
                status="success",
                attempt=1,
                latency_ms=50,
                route_policy_sha256=HASHES[10],
                budget_snapshot_sha256=HASHES[11],
                cache_key_sha256=HASHES[12],
                response_schema_sha256=HASHES[13],
                input_tokens=None,
                output_tokens=None,
                total_tokens=None,
                estimated_cost=None,
            )
        )
    finally:
        session.close()
        engine.dispose()

    input_files = [
        _write_json(tmp_path / "binding.json", {"kind": "binding"}),
        _write_json(tmp_path / "manifest.json", {"kind": "manifest"}),
        _write_json(tmp_path / "source-retrieval.json", {"kind": "source-retrieval"}),
        _write_json(tmp_path / "source-build.json", {"kind": "source-build"}),
        _write_json(tmp_path / "source-review.json", {"kind": "source-review"}),
        _write_json(tmp_path / "final-authority.json", {"kind": "final-authority"}),
        _write_json(tmp_path / "provider-policy.json", {"kind": "provider-policy"}),
        _write_json(tmp_path / "pilot-authority.json", {"kind": "pilot-authority"}),
        _write_json(
            tmp_path / "text-result.json",
            {
                "job_id": "job-ko",
                "binding_receipt_sha256": HASHES[9],
                "provider_policy_sha256": HASHES[10],
                "pilot_authority_sha256": HASHES[11],
                "processed_items": 2,
                "accepted_items": 1,
                "review_required_items": 1,
                "private_text": "안녕하세요 should not leak",
            },
        ),
        _write_json(
            tmp_path / "catalog-result.json",
            {
                "job_id": "job-ko",
                "catalog_locator_sha256": HASHES[12],
                "catalog_content_sha256": HASHES[13],
                "provider_policy_sha256": HASHES[10],
                "pilot_authority_sha256": HASHES[11],
                "voices": [{"voice_id": "ko-KR-SunHiNeural", "locale": "ko-KR"}],
            },
        ),
    ]
    before = {path: _sha256_file(path) for path in input_files}
    monkeypatch.setattr(
        cli_module,
        "verify_active_korean_foundation_snapshot_provenance",
        lambda **_: SimpleNamespace(
            receipt_sha256=HASHES[2],
            snapshot_manifest_sha256=HASHES[3],
            snapshot_root_sha256=HASHES[4],
        ),
    )

    evidence_file = tmp_path / "evidence" / "provider-catalog-pilot.json"
    result = runner.invoke(
        create_app(),
        [
            "validate-korean-provider-catalog-pilot-result",
            *_full_args(tmp_path),
            "--final-authority-sha256",
            HASHES[14],
            "--binding-receipt-file",
            str(input_files[0]),
            "--frequency-bundle-manifest-file",
            str(input_files[1]),
            "--source-retrieval-authority-file",
            str(input_files[2]),
            "--source-build-authority-file",
            str(input_files[3]),
            "--source-review-aggregate-file",
            str(input_files[4]),
            "--final-authority-file",
            str(input_files[5]),
            "--provider-policy-file",
            str(input_files[6]),
            "--pilot-authority-file",
            str(input_files[7]),
            "--text-result-file",
            str(input_files[8]),
            "--catalog-result-file",
            str(input_files[9]),
            "--expected-item-count",
            "2",
            "--evidence-file",
            str(evidence_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "korean_provider_catalog_pilot_evidence_status=validated" in result.output
    after = {path: _sha256_file(path) for path in input_files}
    assert after == before
    payload = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert payload["job_id"] == "job-ko"
    assert payload["provider_call_count"] == 2
    assert payload["synthesis_attempt_count"] == 0
    assert payload["missing_token_denominator_count"] == 1
    assert payload["missing_cost_denominator_count"] == 1
    assert payload["grants_route_authority"] is False
    assert payload["grants_voice_profile_authority"] is False
    assert "안녕하세요" not in evidence_file.read_text(encoding="utf-8")


def test_synthesize_korean_frequency_audio_delegates_with_exact_authority(tmp_path: Path, monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_synthesize(**kwargs: object) -> object:
        calls.append(dict(kwargs))
        return SimpleNamespace(processed_items=2, reused_items=0, fallback_items=0, failed_items=0)

    monkeypatch.setattr(cli_module, "synthesize_korean_frequency_audio", fake_synthesize, raising=False)

    result = runner.invoke(
        create_app(),
        [
            "synthesize-korean-frequency-audio",
            *_full_args(tmp_path),
            "--catalog-result-file",
            str(tmp_path / "catalog.json"),
            "--voice-profile-file",
            str(tmp_path / "profile.json"),
            "--max-items",
            "1",
            "--missing-only",
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0]["authority"].job_id == "job-ko"
    assert calls[0]["catalog_result_file"] == tmp_path / "catalog.json"
    assert calls[0]["voice_profile_file"] == tmp_path / "profile.json"
    assert calls[0]["max_items"] == 1
    assert calls[0]["missing_only"] is True
    assert "korean_frequency_audio_status=synthesized" in result.output


def test_generate_korean_frequency_text_uses_runtime_helper_with_exact_authority(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    class FakeRuntimeService:
        def generate_text(self, **kwargs: object) -> RuntimeTextResult:
            calls.append(("generate_text", dict(kwargs)))
            return RuntimeTextResult(processed_items=1, accepted_items=0, review_required_items=1)

    def fake_builder(**kwargs: object) -> FakeRuntimeService:
        calls.append(("build_runtime", dict(kwargs)))
        return FakeRuntimeService()

    monkeypatch.setattr(cli_module, "build_korean_frequency_text_runtime_service", fake_builder, raising=False)

    result = runner.invoke(
        create_app(),
        [
            "generate-korean-frequency-text",
            *_full_args(tmp_path),
            "--max-items",
            "1",
            "--no-synthesize-audio",
        ],
    )

    assert result.exit_code == 0, result.output
    assert [name for name, _ in calls] == ["build_runtime", "generate_text"]
    runtime_authority = calls[0][1]["runtime_authority"]
    assert runtime_authority.job_id == "job-ko"
    assert runtime_authority.binding_receipt_sha256 == HASHES[9]
    assert runtime_authority.authority.phase31_validation_receipt_sha256 == HASHES[2]
    assert runtime_authority.authority.phase31_snapshot_manifest_sha256 == HASHES[3]
    assert runtime_authority.authority.phase31_snapshot_root_sha256 == HASHES[4]
    assert runtime_authority.authority.stage == "full"
    assert calls[1][1]["job_id"] == "job-ko"
    assert calls[1][1]["deck_language"] is SupportedLanguage.KO
    assert calls[1][1]["max_items"] == 1
    assert calls[1][1]["synthesize_audio"] is False
    assert "korean_frequency_text_status=generated" in result.output


def test_generate_korean_frequency_text_drift_stops_before_generation(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []

    def fake_builder(**kwargs: object) -> object:
        calls.append("build_runtime")
        raise ValueError("private drift detail")

    monkeypatch.setattr(cli_module, "build_korean_frequency_text_runtime_service", fake_builder, raising=False)

    result = runner.invoke(create_app(), ["generate-korean-frequency-text", *_full_args(tmp_path)])

    assert result.exit_code == 1
    assert calls == ["build_runtime"]
    assert result.output == "korean_frequency_text_error=operation_failed\n"
    assert "private drift detail" not in result.output
