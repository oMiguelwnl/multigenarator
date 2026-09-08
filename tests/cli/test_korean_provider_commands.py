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
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderPolicy,
    KoreanProviderRoute,
    KoreanProviderTask,
)
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


def _write_provider_policy(path: Path) -> Path:
    budget = KoreanProviderBudget(
        max_attempts=2,
        max_input_tokens=4096,
        max_output_tokens=1024,
        max_total_tokens=5120,
        max_estimated_cost_usd=1.0,
        max_latency_ms=60000,
        timeout_seconds=60.0,
        max_batch_items=10,
        max_concurrency=1,
    )
    routes = []
    for task in KoreanProviderTask:
        provider = "disabled" if task in {KoreanProviderTask.WORD_AUDIO, KoreanProviderTask.SENTENCE_AUDIO} else "openai"
        if task is KoreanProviderTask.TRANSLATION:
            provider = "deepl"
        if task is KoreanProviderTask.CATALOG:
            provider = "azure-speech"
        routes.append(
            KoreanProviderRoute(
                task=task,
                provider=provider,
                model=None if provider == "disabled" else f"{task.value}-model",
                budget=budget,
                cache_namespace=f"test-{task.value}",
                response_schema_sha256=sha256(f"schema:{task.value}".encode("utf-8")).hexdigest(),
            )
        )
    policy = KoreanProviderPolicy(routes=tuple(routes))
    return _write_json(path, policy.model_dump(mode="json"))


def _grounded_candidate(index: int) -> LexicalCardCandidate:
    return LexicalCardCandidate(
        submitted_form=f"term-{index}",
        display_form=f"term-{index}",
        lemma=f"term-{index}",
        lemma_key=f"term-{index}",
        frequency_rank=index,
        frequency_level=1,
        definition_language="pt",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="test"),
    )


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_voice_profile_catalog(path: Path) -> Path:
    return _write_json(
        path,
        {
            "schema_version": "korean-azure-catalog-pilot-result-v1",
            "job_id": "job-ko",
            "binding_receipt_sha256": HASHES[9],
            "provider_policy_sha256": HASHES[10],
            "pilot_authority_sha256": HASHES[11],
            "catalog_locale": "ko-KR",
            "catalog_locator_sha256": HASHES[12],
            "catalog_content_sha256": HASHES[13],
            "voice_count": 1,
            "catalog_query_count": 1,
            "synthesis_attempt_count": 0,
            "production_database_used": False,
            "voices": [
                {
                    "voice_id": "ko-KR-SunHi:DragonHDLatestNeural",
                    "locale": "ko-KR",
                    "region": "eastus",
                }
            ],
        },
    )


def _write_voice_profile_authority(path: Path, *, catalog_result_file_sha256: str) -> Path:
    payload = {
        "schema_version": "korean-voice-profile-authority-v1",
        "kind": "voice-profile-authority",
        "selected_voice_id": "ko-KR-SunHi:DragonHDLatestNeural",
        "locale": "ko-KR",
        "region": "eastus",
        "catalog_result_file_sha256": catalog_result_file_sha256,
        "catalog_locator_sha256": HASHES[12],
        "catalog_content_sha256": HASHES[13],
        "provider_policy_sha256": HASHES[10],
        "pilot_authority_sha256": HASHES[11],
        "catalog_voice_count": 1,
        "catalog_query_count": 1,
        "catalog_synthesis_attempt_count": 0,
        "profile_policy_version": "korean-neutral-ssml-v1",
        "ssml_policy": "neutral",
        "output_format": "audio-24khz-48kbitrate-mono-mp3",
        "usage_scope": [
            "ordinary-frequency-word-audio",
            "ordinary-frequency-sentence-audio",
        ],
        "powers": ["bind-voice-profile"],
        "synthesis_allowed": False,
        "fallback_policy": "none",
        "grants_route_authority": False,
        "grants_voice_profile_authority": True,
        "grants_audio_authority": False,
        "grants_review_authority": False,
        "grants_export_authority": False,
        "grants_release_authority": False,
        "grants_publication_authority": False,
        "grants_delivery_authority": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Korean Voice Profile Authority\n\n```json\n"
        + json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    return path


def _voice_profile_bind_args(
    *,
    catalog_result_file: Path,
    profile_authority_file: Path,
    voice_profile_file: Path,
    evidence_file: Path,
) -> list[str]:
    return [
        "bind-korean-azure-voice-profile",
        "--job-id",
        "job-ko",
        "--provider-policy-sha256",
        HASHES[10],
        "--pilot-authority-sha256",
        HASHES[11],
        "--catalog-locator-sha256",
        HASHES[12],
        "--catalog-content-sha256",
        HASHES[13],
        "--catalog-result-file",
        str(catalog_result_file),
        "--profile-authority-file",
        str(profile_authority_file),
        "--voice-profile-file",
        str(voice_profile_file),
        "--evidence-file",
        str(evidence_file),
    ]


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
    expected_stage = {"--authority-stage"}
    expected_audio = {
        "--catalog-locator-sha256",
        "--catalog-content-sha256",
        "--profile-sample-authority-sha256",
        "--provider-review-authority-sha256",
        "--heard-review-authority-sha256",
    }

    assert expected_common | expected_stage <= set(_options("prepare-korean-frequency-job"))
    assert expected_common | expected_audio <= set(_options("bind-korean-frequency-audio-authority"))
    assert expected_common | expected_audio | expected_stage <= set(_options("check-korean-frequency-job-binding"))
    assert expected_common | expected_audio | expected_stage | {"--max-items", "--missing-only", "--synthesize-audio", "--text-result-file", "--provider-policy-file"} <= set(
        _options("generate-korean-frequency-text")
    )
    assert expected_common | expected_stage | {"--max-items", "--setup-result-file", "--provider-policy-file"} <= set(
        _options("setup-korean-frequency-live-pilot-candidates")
    )
    for command_name in (
        "prepare-korean-frequency-job",
        "bind-korean-frequency-audio-authority",
        "check-korean-frequency-job-binding",
        "generate-korean-frequency-text",
        "setup-korean-frequency-live-pilot-candidates",
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
    assert expected_audio | {"--endpoint-url", "--catalog-result-file", "--provider-policy-file"} <= set(_options("capture-korean-azure-catalog"))
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
        "--provider-review-authority-sha256",
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


def test_korean_voice_profile_binding_command_exposes_only_explicit_authority_options() -> None:
    options = set(_options("bind-korean-azure-voice-profile"))

    assert {
        "--job-id",
        "--provider-policy-sha256",
        "--pilot-authority-sha256",
        "--catalog-locator-sha256",
        "--catalog-content-sha256",
        "--catalog-result-file",
        "--profile-authority-file",
        "--voice-profile-file",
        "--evidence-file",
    } <= options
    assert "--provider" not in options
    assert "--model" not in options
    assert "--fallback-provider" not in options


def test_bind_korean_azure_voice_profile_writes_sanitized_profile_and_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def forbidden_runtime(*args: object, **kwargs: object) -> object:
        raise AssertionError("database, network, and Azure runtime must not be constructed")

    monkeypatch.setattr(cli_module, "create_engine", forbidden_runtime)
    monkeypatch.setattr(cli_module, "AzureSpeechAdapter", forbidden_runtime)
    catalog_result_file = _write_voice_profile_catalog(tmp_path / "catalog-result.json")
    profile_authority_file = _write_voice_profile_authority(
        tmp_path / "voice-profile-authority.md",
        catalog_result_file_sha256=_sha256_file(catalog_result_file),
    )
    voice_profile_file = tmp_path / "out" / "voice-profile.json"
    evidence_file = tmp_path / "out" / "voice-profile-validation.json"
    before = {
        catalog_result_file: _sha256_file(catalog_result_file),
        profile_authority_file: _sha256_file(profile_authority_file),
    }

    result = runner.invoke(
        create_app(),
        _voice_profile_bind_args(
            catalog_result_file=catalog_result_file,
            profile_authority_file=profile_authority_file,
            voice_profile_file=voice_profile_file,
            evidence_file=evidence_file,
        ),
    )

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == "korean_voice_profile_status=bound"
    assert "profile_sha256=" in result.output
    assert "evidence_sha256=" in result.output
    assert "ko-KR-SunHi" not in result.output
    assert {path: _sha256_file(path) for path in before} == before
    profile = json.loads(voice_profile_file.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert profile["voice_id"] == "ko-KR-SunHi:DragonHDLatestNeural"
    assert profile["provider"] == "azure-speech"
    assert profile["locale"] == "ko-KR"
    assert profile["fallback_policy"] == "none"
    assert profile["profile_authority_sha256"] == _sha256_file(profile_authority_file)
    assert profile["profile_sha256"] == evidence["profile_sha256"]
    assert evidence["status"] == "valid"
    assert evidence["selected_voice_in_catalog"] is True
    assert evidence["synthesis_attempt_count"] == 0
    assert evidence["fallback_attempt_count"] == 0
    assert evidence["static_registry_activated"] is False
    assert evidence["grants_voice_profile_authority"] is True
    assert evidence["grants_audio_authority"] is False
    assert evidence["grants_review_authority"] is False
    assert evidence["grants_export_authority"] is False
    serialized = voice_profile_file.read_text(encoding="utf-8") + evidence_file.read_text(encoding="utf-8")
    assert "prompt" not in serialized.lower()
    assert "completion" not in serialized.lower()
    assert "private" not in serialized.lower()
    assert "sk-" not in serialized
    assert "/home/" not in serialized


def test_bind_korean_azure_voice_profile_rejects_output_input_collision(tmp_path: Path) -> None:
    catalog_result_file = _write_voice_profile_catalog(tmp_path / "catalog-result.json")
    profile_authority_file = _write_voice_profile_authority(
        tmp_path / "voice-profile-authority.md",
        catalog_result_file_sha256=_sha256_file(catalog_result_file),
    )
    before = _sha256_file(catalog_result_file)
    evidence_file = tmp_path / "voice-profile-validation.json"

    result = runner.invoke(
        create_app(),
        _voice_profile_bind_args(
            catalog_result_file=catalog_result_file,
            profile_authority_file=profile_authority_file,
            voice_profile_file=catalog_result_file,
            evidence_file=evidence_file,
        ),
    )

    assert result.exit_code == 1
    assert result.output == "korean_frequency_text_error=operation_failed\n"
    assert _sha256_file(catalog_result_file) == before
    assert not evidence_file.exists()


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
        "verify_active_korean_foundation_snapshot_provenance_with_approved_fallback",
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
            *_base_args(tmp_path),
            "--provider-review-authority-sha256",
            "a" * 64,
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


def test_generate_korean_frequency_text_accepts_pilot_base_without_audio_authority_and_writes_sanitized_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    class FakeRuntimeService:
        def generate_text(self, **kwargs: object) -> RuntimeTextResult:
            calls.append(("generate_text", dict(kwargs)))
            return RuntimeTextResult(processed_items=2, accepted_items=1, review_required_items=1)

    def fake_builder(**kwargs: object) -> FakeRuntimeService:
        calls.append(("build_runtime", dict(kwargs)))
        return FakeRuntimeService()

    monkeypatch.setattr(cli_module, "build_korean_frequency_text_runtime_service", fake_builder, raising=False)

    text_result_file = tmp_path / "result" / "text-result.json"
    result = runner.invoke(
        create_app(),
        [
            "generate-korean-frequency-text",
            *_base_args(tmp_path),
            "--authority-stage",
            "pilot_base",
            "--max-items",
            "2",
            "--no-synthesize-audio",
            "--text-result-file",
            str(text_result_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert [name for name, _ in calls] == ["build_runtime", "generate_text"]
    runtime_authority = calls[0][1]["runtime_authority"]
    assert runtime_authority.authority.stage == "pilot_base"
    assert callable(calls[0][1]["phase31_provenance_verifier"])
    assert calls[1][1]["synthesize_audio"] is False
    payload = json.loads(text_result_file.read_text(encoding="utf-8"))
    assert payload == {
        "accepted_items": 1,
        "audio_synthesis_enabled": False,
        "authority_stage": "pilot_base",
        "binding_receipt_sha256": HASHES[9],
        "failed_audio_items": 0,
        "fallback_audio_items": 0,
        "job_id": "job-ko",
        "pilot_authority_sha256": HASHES[11],
        "processed_items": 2,
        "provider_policy_sha256": HASHES[10],
        "review_required_items": 1,
        "schema_version": "korean-frequency-text-result-v1",
    }
    serialized = text_result_file.read_text(encoding="utf-8")
    assert "prompt" not in serialized.lower()
    assert "completion" not in serialized.lower()
    assert "private" not in serialized.lower()
    assert "sk-" not in serialized
    assert "/home/" not in serialized


def test_setup_korean_frequency_live_pilot_candidates_delegates_with_policy_and_writes_sanitized_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_setup(**kwargs: object) -> dict[str, object]:
        calls.append(dict(kwargs))
        return {
            "schema_version": "korean-live-pilot-candidate-setup-v1",
            "job_id": "job-ko",
            "database_kind": "local_ignored_sqlite",
            "database_relative_path": ".multilang/phase32/pilot/pilot-live-text-catalog.sqlite3",
            "database_gitignore_check": "passed",
            "authority_stage": "pilot_base",
            "candidate_count": 10,
            "ingested_item_count": 10,
            "provider_attempt_count": 0,
            "audio_synthesis_enabled": False,
            "max_items": 10,
            "max_concurrency": 1,
            "max_attempts": 2,
            "cost_ceiling_usd": "1.00",
            "fallback_policy": "none",
            "production_database_used": False,
            "provider_policy_sha256": HASHES[10],
            "pilot_authority_sha256": HASHES[11],
            "final_frequency_bundle_sha256": HASHES[6],
        }

    monkeypatch.setattr(cli_module, "setup_korean_frequency_live_pilot_candidates", fake_setup, raising=False)
    provider_policy_file = _write_provider_policy(tmp_path / "provider-policy.json")
    setup_result_file = tmp_path / "result" / "setup.json"

    result = runner.invoke(
        create_app(),
        [
            "setup-korean-frequency-live-pilot-candidates",
            *_base_args(tmp_path),
            "--provider-policy-file",
            str(provider_policy_file),
            "--authority-stage",
            "pilot_base",
            "--max-items",
            "10",
            "--setup-result-file",
            str(setup_result_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0]["authority"].stage == "pilot_base"
    assert calls[0]["provider_policy"].route_for(KoreanProviderTask.SENTENCE_GENERATION).budget.max_batch_items == 10
    assert calls[0]["max_items"] == 10
    payload = json.loads(setup_result_file.read_text(encoding="utf-8"))
    assert payload["candidate_count"] == 10
    assert payload["provider_attempt_count"] == 0
    serialized = setup_result_file.read_text(encoding="utf-8")
    assert "private" not in serialized.lower()
    assert "sk-" not in serialized


def test_setup_korean_frequency_live_pilot_candidates_helper_writes_local_denominator(
    tmp_path: Path,
    monkeypatch,
) -> None:
    provider_policy = KoreanProviderPolicy.model_validate_json(_write_provider_policy(tmp_path / "policy.json").read_text(encoding="utf-8"))
    authority = cli_module._build_korean_frequency_job_authority(
        stage="pilot_base",
        phase31_active_pointer_sha256=HASHES[0],
        phase31_active_pointer_content_sha256=HASHES[1],
        phase31_validation_receipt_sha256=HASHES[2],
        phase31_snapshot_manifest_sha256=HASHES[3],
        phase31_snapshot_root_sha256=HASHES[4],
        frequency_bundle_manifest_sha256=HASHES[5],
        frequency_bundle_content_sha256=HASHES[6],
        source_retrieval_sha256=HASHES[7],
        source_build_result_sha256=HASHES[8],
        source_review_aggregate_sha256=HASHES[9],
        provider_policy_sha256=provider_policy.policy_sha256,
        pilot_authority_sha256=HASHES[11],
    )
    monkeypatch.setattr(cli_module, "_sqlite_database_relative_path", lambda _: ".multilang/phase32/pilot/pilot-live-text-catalog.sqlite3")
    monkeypatch.setattr(cli_module, "_git_check_ignore", lambda _: "passed")
    monkeypatch.setattr(cli_module, "_verify_korean_frequency_phase31_authority", lambda _: None)
    monkeypatch.setattr(cli_module, "load_korean_final_frequency_entries", lambda **_: ())
    monkeypatch.setattr(cli_module, "build_frequency_level", lambda *_, **__: [_grounded_candidate(index) for index in range(1, 11)])

    payload = cli_module.setup_korean_frequency_live_pilot_candidates(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'pilot.db'}",
        job_id="job-ko",
        authority=authority,
        frequency_bundle_root=tmp_path / "bundle",
        binding_receipt_sha256=HASHES[9],
        provider_policy=provider_policy,
        max_items=10,
    )

    assert payload["candidate_count"] == 10
    assert payload["ingested_item_count"] == 10
    assert payload["provider_attempt_count"] == 0
    assert payload["max_attempts"] == 2


def test_capture_korean_azure_catalog_pilot_does_not_require_dummy_audio_authority(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_capture(**kwargs: object) -> dict[str, object]:
        calls.append(dict(kwargs))
        return {
            "schema_version": "korean-azure-catalog-pilot-result-v1",
            "job_id": "job-ko",
            "provider_policy_sha256": HASHES[10],
            "pilot_authority_sha256": HASHES[11],
            "catalog_locator_sha256": HASHES[12],
            "catalog_content_sha256": HASHES[13],
            "voice_count": 1,
            "catalog_query_count": 1,
            "synthesis_attempt_count": 0,
            "voices": [{"voice_id": "ko-KR-SunHiNeural", "locale": "ko-KR"}],
        }

    monkeypatch.setattr(cli_module, "capture_korean_azure_catalog_pilot", fake_capture, raising=False)
    provider_policy_file = _write_provider_policy(tmp_path / "provider-policy.json")
    catalog_result_file = tmp_path / "result" / "catalog.json"

    result = runner.invoke(
        create_app(),
        [
            "capture-korean-azure-catalog",
            *_base_args(tmp_path),
            "--provider-policy-file",
            str(provider_policy_file),
            "--endpoint-url",
            "https://koreacentral.tts.speech.microsoft.com/cognitiveservices/voices/list",
            "--catalog-result-file",
            str(catalog_result_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0]["job_id"] == "job-ko"
    assert calls[0]["provider_policy"].route_for(KoreanProviderTask.CATALOG).provider == "azure-speech"
    assert calls[0]["endpoint_url"] == "https://koreacentral.tts.speech.microsoft.com/cognitiveservices/voices/list"
    payload = json.loads(catalog_result_file.read_text(encoding="utf-8"))
    assert payload["voice_count"] == 1
    assert payload["synthesis_attempt_count"] == 0
    assert payload["voices"][0]["locale"] == "ko-KR"


def test_generate_korean_frequency_text_rejects_pilot_base_audio_synthesis_before_runtime(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_builder(**kwargs: object) -> object:
        calls.append("build_runtime")
        raise AssertionError("not called")

    monkeypatch.setattr(cli_module, "build_korean_frequency_text_runtime_service", fake_builder, raising=False)

    result = runner.invoke(
        create_app(),
        [
            "generate-korean-frequency-text",
            *_base_args(tmp_path),
            "--authority-stage",
            "pilot_base",
        ],
    )

    assert result.exit_code == 1
    assert calls == []
    assert result.output == "korean_frequency_text_error=operation_failed\n"


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
