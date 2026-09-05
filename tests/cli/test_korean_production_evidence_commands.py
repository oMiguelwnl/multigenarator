"""CLI coverage for Korean production evidence validators."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import click
from typer.main import get_command
from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app
from multilang.services.korean_production_evidence import (
    KoreanProductionEvidence,
    KoreanProductionEvidenceAuthority,
    KoreanProductionReviewAggregate,
)


runner = CliRunner()


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


HASHES = {
    "phase31_pointer": _hash("phase31-pointer"),
    "phase31_pointer_content": _hash("phase31-pointer-content"),
    "phase31_validation": _hash("phase31-validation"),
    "phase31_manifest": _hash("phase31-manifest"),
    "phase31_root": _hash("phase31-root"),
    "frequency_manifest": _hash("frequency-manifest"),
    "frequency_content": _hash("frequency-content"),
    "source_access": _hash("source-access"),
    "source_retrieval": _hash("source-retrieval"),
    "source_transformation": _hash("source-transformation"),
    "source_build": _hash("source-build"),
    "source_review": _hash("source-review"),
    "final_bundle": _hash("final-bundle"),
    "provider_policy": _hash("provider-policy"),
    "provider_review": _hash("provider-review"),
    "budget": _hash("budget"),
    "retry": _hash("retry"),
    "full_run": _hash("full-run"),
    "catalog_locator": _hash("catalog-locator"),
    "catalog_content": _hash("catalog-content"),
    "profile": _hash("profile"),
    "heard": _hash("heard"),
    "full_binding": _hash("full-binding"),
    "content_promotion": _hash("content-promotion"),
    "text_review_aggregate": _hash("text-review-aggregate"),
    "text_review_application": _hash("text-review-application"),
    "audio_review_aggregate": _hash("audio-review-aggregate"),
    "audio_review_application": _hash("audio-review-application"),
}


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


def _input_files(tmp_path: Path) -> dict[str, Path]:
    names = {
        "binding_receipt": "binding.json",
        "frequency_bundle_manifest": "frequency-manifest.json",
        "source_access_authority": "source-access.json",
        "source_retrieval_authority": "source-retrieval.json",
        "source_transformation_authority": "source-transformation.json",
        "source_build_authority": "source-build.json",
        "source_review_aggregate": "source-review.json",
        "final_bundle_authority": "final-bundle.json",
        "provider_policy": "provider-policy.json",
        "provider_review_authority": "provider-review.json",
        "budget_authority": "budget.json",
        "retry_policy": "retry.json",
        "full_run_authority": "full-run.json",
        "catalog_result": "catalog-result.json",
        "voice_profile": "voice-profile.json",
        "heard_review_authority": "heard-review.json",
        "full_binding_receipt": "full-binding.json",
        "text_result": "text-result.json",
        "audio_result": "audio-result.json",
        "content_promotion_authority": "content-promotion.json",
        "text_review_aggregate": "text-review-aggregate.json",
        "text_review_application_receipt": "text-review-application.json",
        "audio_review_aggregate": "audio-review-aggregate.json",
        "audio_review_application_receipt": "audio-review-application.json",
        "generation_report_json": "generation-report.json",
        "generation_report_markdown": "generation-report.md",
        "apkg": "korean-frequency.apkg",
    }
    files = {
        label: _write_json(tmp_path / name, {"label": label, "private": "LEAK-CONTENT"})
        for label, name in names.items()
        if label not in {"generation_report_markdown", "apkg"}
    }
    files["generation_report_markdown"] = tmp_path / names["generation_report_markdown"]
    files["generation_report_markdown"].write_text("exact_apkg_sha256=fixture\nLEAK-CONTENT\n", encoding="utf-8")
    files["apkg"] = tmp_path / names["apkg"]
    files["apkg"].write_bytes(b"fixture-apkg")
    return files


def _common_args(tmp_path: Path, files: dict[str, Path], evidence_file: Path) -> list[str]:
    return [
        "--database-url",
        f"sqlite+pysqlite:///{tmp_path / 'production.db'}",
        "--job-id",
        "job-ko-production",
        "--phase31-active-pointer-sha256",
        HASHES["phase31_pointer"],
        "--phase31-active-pointer-content-sha256",
        HASHES["phase31_pointer_content"],
        "--phase31-validation-receipt-sha256",
        HASHES["phase31_validation"],
        "--phase31-snapshot-manifest-sha256",
        HASHES["phase31_manifest"],
        "--phase31-snapshot-root-sha256",
        HASHES["phase31_root"],
        "--frequency-bundle-root",
        str(tmp_path / "bundle"),
        "--frequency-bundle-manifest-sha256",
        HASHES["frequency_manifest"],
        "--frequency-bundle-content-sha256",
        HASHES["frequency_content"],
        "--source-access-authority-sha256",
        HASHES["source_access"],
        "--source-retrieval-sha256",
        HASHES["source_retrieval"],
        "--source-transformation-sha256",
        HASHES["source_transformation"],
        "--source-build-result-sha256",
        HASHES["source_build"],
        "--source-review-aggregate-sha256",
        HASHES["source_review"],
        "--final-bundle-authority-sha256",
        HASHES["final_bundle"],
        "--provider-policy-sha256",
        HASHES["provider_policy"],
        "--provider-review-authority-sha256",
        HASHES["provider_review"],
        "--budget-authority-sha256",
        HASHES["budget"],
        "--retry-policy-sha256",
        HASHES["retry"],
        "--full-run-authority-sha256",
        HASHES["full_run"],
        "--catalog-locator-sha256",
        HASHES["catalog_locator"],
        "--catalog-content-sha256",
        HASHES["catalog_content"],
        "--profile-sample-authority-sha256",
        HASHES["profile"],
        "--heard-review-authority-sha256",
        HASHES["heard"],
        "--full-binding-receipt-sha256",
        HASHES["full_binding"],
        "--binding-receipt-file",
        str(files["binding_receipt"]),
        "--frequency-bundle-manifest-file",
        str(files["frequency_bundle_manifest"]),
        "--source-access-authority-file",
        str(files["source_access_authority"]),
        "--source-retrieval-authority-file",
        str(files["source_retrieval_authority"]),
        "--source-transformation-authority-file",
        str(files["source_transformation_authority"]),
        "--source-build-authority-file",
        str(files["source_build_authority"]),
        "--source-review-aggregate-file",
        str(files["source_review_aggregate"]),
        "--final-bundle-authority-file",
        str(files["final_bundle_authority"]),
        "--provider-policy-file",
        str(files["provider_policy"]),
        "--provider-review-authority-file",
        str(files["provider_review_authority"]),
        "--budget-authority-file",
        str(files["budget_authority"]),
        "--retry-policy-file",
        str(files["retry_policy"]),
        "--full-run-authority-file",
        str(files["full_run_authority"]),
        "--catalog-result-file",
        str(files["catalog_result"]),
        "--voice-profile-file",
        str(files["voice_profile"]),
        "--heard-review-authority-file",
        str(files["heard_review_authority"]),
        "--full-binding-receipt-file",
        str(files["full_binding_receipt"]),
        "--text-result-file",
        str(files["text_result"]),
        "--audio-result-file",
        str(files["audio_result"]),
        "--expected-item-count",
        "3000",
        "--evidence-file",
        str(evidence_file),
    ]


def _final_args(files: dict[str, Path], audit_json: Path, audit_markdown: Path) -> list[str]:
    return [
        "--content-promotion-authority-sha256",
        HASHES["content_promotion"],
        "--content-promotion-authority-file",
        str(files["content_promotion_authority"]),
        "--text-review-aggregate-sha256",
        HASHES["text_review_aggregate"],
        "--text-review-aggregate-file",
        str(files["text_review_aggregate"]),
        "--text-review-application-sha256",
        HASHES["text_review_application"],
        "--text-review-application-receipt-file",
        str(files["text_review_application_receipt"]),
        "--audio-review-aggregate-sha256",
        HASHES["audio_review_aggregate"],
        "--audio-review-aggregate-file",
        str(files["audio_review_aggregate"]),
        "--audio-review-application-sha256",
        HASHES["audio_review_application"],
        "--audio-review-application-receipt-file",
        str(files["audio_review_application_receipt"]),
        "--apkg-file",
        str(files["apkg"]),
        "--generation-report-json",
        str(files["generation_report_json"]),
        "--generation-report-markdown",
        str(files["generation_report_markdown"]),
        "--expected-word-assets",
        "3000",
        "--expected-sentence-assets",
        "3000",
        "--cards-per-level",
        "1000",
        "--audit-json",
        str(audit_json),
        "--audit-markdown",
        str(audit_markdown),
    ]


def _evidence(mode: str) -> KoreanProductionEvidence:
    return KoreanProductionEvidence(
        mode=mode,
        job_id="job-ko-production",
        evidence_sha256=_hash(f"{mode}-evidence"),
        expected_item_count=3000,
        lexical_candidate_count=3000,
        level_counts={1: 1000, 2: 1000, 3: 1000},
        text_record_count=3000,
        text_review_required_count=3000 if mode == "run_result" else 0,
        text_accepted_count=0 if mode == "run_result" else 3000,
        text_histories_with_two_initial_candidates=3000,
        text_histories_with_single_repair_or_less=3000,
        hard_gate_passed_count=3000,
        adaptive_evidence_count=3000,
        word_pending_audio_review_count=3000 if mode == "run_result" else 0,
        sentence_pending_audio_review_count=3000 if mode == "run_result" else 0,
        word_reviewed_audio_count=0 if mode == "run_result" else 3000,
        sentence_reviewed_audio_count=0 if mode == "run_result" else 3000,
        audio_request_hash_count=6000,
        audio_artifact_hash_count=6000,
        provider_call_count=4,
        provider_attempt_count=4,
        retry_attempt_count=1,
        cache_hit_count=0,
        synthesis_attempt_count=1,
        fallback_attempt_count=0,
        missing_token_denominator_count=0,
        missing_cost_denominator_count=0,
        latency_ms_total=480,
        provider_summaries=(),
        authority={"provider_policy_sha256": HASHES["provider_policy"]},
        grants_review_application_authority=False,
        grants_content_promotion_authority=False,
        grants_release_authority=False,
    )


def _authority_payload() -> dict[str, str]:
    return {
        "job_id": "job-ko-production",
        "phase31_pointer_locator_sha256": HASHES["phase31_pointer"],
        "phase31_pointer_content_sha256": HASHES["phase31_pointer_content"],
        "phase31_validation_receipt_sha256": HASHES["phase31_validation"],
        "phase31_snapshot_manifest_sha256": HASHES["phase31_manifest"],
        "phase31_snapshot_root_sha256": HASHES["phase31_root"],
        "frequency_bundle_locator_sha256": HASHES["frequency_manifest"],
        "frequency_bundle_content_sha256": HASHES["frequency_content"],
        "source_access_authority_sha256": HASHES["source_access"],
        "source_retrieval_sha256": HASHES["source_retrieval"],
        "source_transformation_sha256": HASHES["source_transformation"],
        "source_build_result_sha256": HASHES["source_build"],
        "source_review_aggregate_sha256": HASHES["source_review"],
        "final_bundle_authority_sha256": HASHES["final_bundle"],
        "provider_policy_sha256": HASHES["provider_policy"],
        "provider_review_authority_sha256": HASHES["provider_review"],
        "budget_authority_sha256": HASHES["budget"],
        "retry_policy_sha256": HASHES["retry"],
        "full_run_authority_sha256": HASHES["full_run"],
        "catalog_locator_sha256": HASHES["catalog_locator"],
        "catalog_content_sha256": HASHES["catalog_content"],
        "profile_sample_authority_sha256": HASHES["profile"],
        "heard_review_authority_sha256": HASHES["heard"],
        "full_binding_receipt_sha256": HASHES["full_binding"],
    }


def _review_aggregate() -> KoreanProductionReviewAggregate:
    return KoreanProductionReviewAggregate(
        job_id="job-ko-production",
        aggregate_sha256=_hash("review-aggregate"),
        expected_item_count=3000,
        receipt_file_count=1,
        text_receipt_count=3000,
        word_integrity_receipt_count=3000,
        sentence_integrity_receipt_count=3000,
        heard_word_sample_count=300,
        heard_sentence_sample_count=300,
        risk_case_count=0,
        risk_case_receipt_count=0,
        receipt_sha256s=(_hash("receipt"),),
        coverage_roots={"text": _hash("text-root")},
        authority={"full_binding_receipt_sha256": HASHES["full_binding"]},
        grants_review_application_authority=False,
        grants_content_promotion_authority=False,
        grants_release_authority=False,
    )


def test_production_evidence_commands_expose_required_flags_and_no_provider_defaults() -> None:
    run_options = set(_options("validate-korean-production-run-result"))
    final_options = set(_options("validate-korean-production-evidence"))
    common = {
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
        "--source-access-authority-sha256",
        "--source-retrieval-sha256",
        "--source-transformation-sha256",
        "--source-build-result-sha256",
        "--source-review-aggregate-sha256",
        "--final-bundle-authority-sha256",
        "--provider-policy-sha256",
        "--provider-review-authority-sha256",
        "--budget-authority-sha256",
        "--retry-policy-sha256",
        "--full-run-authority-sha256",
        "--catalog-locator-sha256",
        "--catalog-content-sha256",
        "--profile-sample-authority-sha256",
        "--heard-review-authority-sha256",
        "--full-binding-receipt-sha256",
        "--binding-receipt-file",
        "--frequency-bundle-manifest-file",
        "--source-access-authority-file",
        "--source-retrieval-authority-file",
        "--source-transformation-authority-file",
        "--source-build-authority-file",
        "--source-review-aggregate-file",
        "--final-bundle-authority-file",
        "--provider-policy-file",
        "--provider-review-authority-file",
        "--budget-authority-file",
        "--retry-policy-file",
        "--full-run-authority-file",
        "--catalog-result-file",
        "--voice-profile-file",
        "--heard-review-authority-file",
        "--full-binding-receipt-file",
        "--text-result-file",
        "--audio-result-file",
        "--expected-item-count",
        "--evidence-file",
    }
    final_only = {
        "--content-promotion-authority-sha256",
        "--content-promotion-authority-file",
        "--text-review-aggregate-sha256",
        "--text-review-aggregate-file",
        "--text-review-application-sha256",
        "--text-review-application-receipt-file",
        "--audio-review-aggregate-sha256",
        "--audio-review-aggregate-file",
        "--audio-review-application-sha256",
        "--audio-review-application-receipt-file",
        "--apkg-file",
        "--generation-report-json",
        "--generation-report-markdown",
        "--expected-word-assets",
        "--expected-sentence-assets",
        "--cards-per-level",
        "--audit-json",
        "--audit-markdown",
    }

    assert common <= run_options
    assert common | final_only <= final_options
    for options in (run_options, final_options):
        assert "--provider" not in options
        assert "--model" not in options
        assert "--fallback-provider" not in options
        assert "--phase31-path" not in options


def test_validate_korean_production_run_result_cli_writes_hash_only_output_read_only(tmp_path: Path, monkeypatch) -> None:
    files = _input_files(tmp_path)
    before = {label: _sha256_file(path) for label, path in files.items() if path.is_file()}
    calls: list[tuple[str, dict[str, Any]]] = []

    monkeypatch.setattr(
        cli_module,
        "load_korean_production_evidence_rows",
        lambda **kwargs: calls.append(("load", kwargs)) or object(),
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "validate_korean_production_run_result",
        lambda **kwargs: calls.append(("validate", kwargs)) or _evidence("run_result"),
        raising=False,
    )

    evidence_file = tmp_path / "out" / "run-evidence.json"
    result = runner.invoke(
        create_app(),
        ["validate-korean-production-run-result", *_common_args(tmp_path, files, evidence_file)],
    )

    assert result.exit_code == 0, result.output
    assert [name for name, _ in calls] == ["load", "validate"]
    assert calls[0][1]["job_id"] == "job-ko-production"
    assert calls[1][1]["authority"].full_run_authority_sha256 == HASHES["full_run"]
    assert calls[1][1]["expected_item_count"] == 3000
    assert calls[1][1]["protected_hashes"]["text_result"][0] == before["text_result"]
    assert calls[1][1]["protected_hashes"]["text_result"][1] == before["text_result"]
    assert {label: _sha256_file(path) for label, path in files.items() if path.is_file()} == before
    payload = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert payload["mode"] == "run_result"
    assert payload["provider_call_count"] == 4
    assert "LEAK-CONTENT" not in evidence_file.read_text(encoding="utf-8")
    assert "korean_production_run_evidence_status=validated" in result.output


def test_validate_korean_production_review_batches_cli_writes_content_free_aggregate(tmp_path: Path, monkeypatch) -> None:
    authority_file = _write_json(tmp_path / "authority.json", _authority_payload())
    receipt_dir = tmp_path / "receipts"
    _write_json(receipt_dir / "receipt.json", {"kind": "fixture"})
    aggregate_file = tmp_path / "aggregate.json"
    calls: list[tuple[str, dict[str, Any]]] = []

    monkeypatch.setattr(
        cli_module,
        "load_korean_production_evidence_rows",
        lambda **kwargs: calls.append(("load", kwargs)) or object(),
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "validate_korean_production_review_batches",
        lambda **kwargs: calls.append(("aggregate", kwargs)) or _review_aggregate(),
        raising=False,
    )

    result = runner.invoke(
        create_app(),
        [
            "validate-korean-production-review-batches",
            "--database-url",
            "sqlite+pysqlite:///fixture.db",
            "--job-id",
            "job-ko-production",
            "--authority-file",
            str(authority_file),
            "--receipt-dir",
            str(receipt_dir),
            "--expected-item-count",
            "3000",
            "--expected-heard-sample-count",
            "300",
            "--aggregate-file",
            str(aggregate_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert [name for name, _ in calls] == ["load", "aggregate"]
    assert isinstance(calls[1][1]["authority"], KoreanProductionEvidenceAuthority)
    assert calls[1][1]["receipt_files"] == [receipt_dir / "receipt.json"]
    assert "korean_production_review_aggregate_status=validated" in result.output
    payload = json.loads(aggregate_file.read_text(encoding="utf-8"))
    assert payload["mode"] == "review_aggregate"
    assert "LEAK" not in aggregate_file.read_text(encoding="utf-8")


def test_validate_korean_production_evidence_cli_writes_final_result_evidence_and_audits(tmp_path: Path, monkeypatch) -> None:
    files = _input_files(tmp_path)
    calls: list[tuple[str, dict[str, Any]]] = []

    monkeypatch.setattr(
        cli_module,
        "load_korean_production_evidence_rows",
        lambda **kwargs: calls.append(("load", kwargs)) or object(),
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "validate_korean_production_final_evidence",
        lambda **kwargs: calls.append(("validate_final", kwargs)) or _evidence("final_result"),
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "build_korean_production_audit_payload",
        lambda evidence: calls.append(("audit_payload", {"evidence": evidence}))
        or {"mode": evidence.mode, "evidence_sha256": evidence.evidence_sha256},
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "render_korean_production_audit_markdown",
        lambda payload: calls.append(("audit_markdown", {"payload": payload}))
        or f"mode={payload['mode']}\nevidence_sha256={payload['evidence_sha256']}\n",
        raising=False,
    )

    evidence_file = tmp_path / "out" / "final-evidence.json"
    audit_json = tmp_path / "out" / "final-audit.json"
    audit_markdown = tmp_path / "out" / "final-audit.md"
    result = runner.invoke(
        create_app(),
        [
            "validate-korean-production-evidence",
            *_common_args(tmp_path, files, evidence_file),
            *_final_args(files, audit_json, audit_markdown),
        ],
    )

    assert result.exit_code == 0, result.output
    assert [name for name, _ in calls] == ["load", "validate_final", "audit_payload", "audit_markdown"]
    final_call = calls[1][1]
    assert final_call["apkg_file"] == files["apkg"]
    assert final_call["generation_report_json"] == files["generation_report_json"]
    assert final_call["generation_report_markdown"] == files["generation_report_markdown"]
    assert final_call["expected_word_assets"] == 3000
    assert final_call["cards_per_level"] == 1000
    assert json.loads(evidence_file.read_text(encoding="utf-8"))["mode"] == "final_result"
    assert json.loads(audit_json.read_text(encoding="utf-8"))["mode"] == "final_result"
    assert "mode=final_result" in audit_markdown.read_text(encoding="utf-8")
    assert "LEAK-CONTENT" not in evidence_file.read_text(encoding="utf-8")
    assert "LEAK-CONTENT" not in audit_json.read_text(encoding="utf-8")
    assert "LEAK-CONTENT" not in audit_markdown.read_text(encoding="utf-8")
    assert "korean_production_final_evidence_status=validated" in result.output


def test_validate_korean_production_evidence_failure_is_content_free_read_only_and_preserves_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    files = _input_files(tmp_path)
    evidence_file = tmp_path / "out" / "run-evidence.json"
    evidence_file.parent.mkdir(parents=True)
    evidence_file.write_text("sentinel\n", encoding="utf-8")

    monkeypatch.setattr(cli_module, "load_korean_production_evidence_rows", lambda **_: object(), raising=False)

    def fail_validate(**_: object) -> object:
        raise ValueError("LEAK-CONTENT private drift")

    monkeypatch.setattr(cli_module, "validate_korean_production_run_result", fail_validate, raising=False)

    result = runner.invoke(
        create_app(),
        ["validate-korean-production-run-result", *_common_args(tmp_path, files, evidence_file)],
    )

    assert result.exit_code == 1
    assert result.output == "korean_production_evidence_error=operation_failed\n"
    assert evidence_file.read_text(encoding="utf-8") == "sentinel\n"
