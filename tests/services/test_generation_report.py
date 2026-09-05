from __future__ import annotations

from dataclasses import dataclass
import json
from types import SimpleNamespace

from multilang.domain.audio import AudioAssetKind, AudioProvider, AudioReviewStatus, AudioSynthesisStatus
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow, ExportQualityGateResult
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.text_quality import ReviewStatus, ValidationStatus
from multilang.services.generation_report import write_generation_report


_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64
_HASH_E = "e" * 64
_HASH_F = "f" * 64


@dataclass
class DummyIssue:
    message: str


def test_generation_report_includes_provider_call_summary(tmp_path) -> None:
    export_path = tmp_path / "deck.apkg"
    export_path.write_bytes(b"deck")

    result = write_generation_report(
        job=type("Job", (), {"id": "job-1", "language": "en", "source_type": "frequency", "status": "completed", "total_items": 1, "completed_items": 1, "failed_items": 0})(),
        export_artifact=type("Artifact", (), {"output_path": export_path, "export_format": "apkg", "status": "completed", "card_count": 1})(),
        rows=[],
        text_records=[],
        audio_assets=[],
        gate_result=ExportQualityGateResult(passed=True, partial=False, card_count=1, level_counts={1: 1}, issues=[], warnings=[]),
        output_dir=tmp_path,
        provider_call_summary=[{"provider": "litellm", "operation": "sentence", "status": "success", "calls": 1, "retry_attempts": 0, "latency_ms_total": 12, "latency_ms_avg": 12, "latency_ms_p95": 12, "total_tokens": 9, "estimated_cost": 0.0, "fallback_count": 0, "circuit_open_blocks": 0}],
    )

    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "## Provider Calls" in markdown
    assert "provider:litellm operation:sentence status:success" in markdown
    assert "gate_passed=True" in markdown
    assert "audio_fallback_count=0" in markdown


def make_korean_row(*, item_key: str, sort_index: int, frequency_level: int) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type="frequency",
            job_id="job-ko",
            item_key=item_key,
            lemma_key=f"ko:{item_key}",
            sort_index=sort_index,
        ),
        sort_index=sort_index,
        frequency_level=frequency_level,
        frequency_bundle_sha256=_HASH_A,
        export_gate_receipt_sha256=_HASH_B,
        text_review_receipt_sha256=_HASH_C,
        word_audio_artifact_sha256=_HASH_D,
        sentence_audio_artifact_sha256=_HASH_E,
        word=item_key,
        front_of_card=item_key,
        ipa=f"/{item_key}/",
        definitions="substantivo: fixture",
        example_sentence="LEAK-KOREAN-SENTENCE",
        translation="LEAK-PORTUGUESE-TRANSLATION",
        word_audio=f"[sound:{item_key}-word.mp3]",
        sentence_audio=f"[sound:{item_key}-sentence.mp3]",
    )


def make_text_record() -> object:
    return SimpleNamespace(
        review_status=ReviewStatus.ACCEPTED,
        validation_status=ValidationStatus.PASSED,
        text_review_receipt_sha256=_HASH_C,
        example_sentence="LEAK-KOREAN-SENTENCE",
        translation_text="LEAK-PORTUGUESE-TRANSLATION",
        adaptive_i_plus_one_evidence=SimpleNamespace(
            known_concept_count=2,
            observed_concept_ids=("ko:foundation", "ko:lexeme"),
            incidental_concept_ids=("ko:foundation",),
        ),
        candidate_selection_evidence=SimpleNamespace(initial_candidate_count=2, repair_attempt_count=1),
    )


def make_audio_asset(*, item_key: str, asset_kind: AudioAssetKind) -> object:
    return SimpleNamespace(
        item_key=item_key,
        asset_kind=asset_kind,
        display_text="LEAK-AUDIO-TEXT",
        provenance=SimpleNamespace(
            provider=AudioProvider.AZURE,
            status=AudioSynthesisStatus.SYNTHESIZED,
            audio_review_status=AudioReviewStatus.APPROVED,
            fallback_used=False,
            artifact_sha256=_HASH_D if asset_kind is AudioAssetKind.WORD else _HASH_E,
            storage_path=f"/private/audio/{item_key}-{asset_kind.value}.mp3",
        ),
    )


def test_korean_generation_report_binds_exact_apkg_hash_counts_denominators_and_privacy(tmp_path) -> None:
    from multilang.services import generation_report as report_module

    rows = [
        make_korean_row(item_key="어휘1", sort_index=1, frequency_level=1),
        make_korean_row(item_key="어휘2", sort_index=1001, frequency_level=2),
        make_korean_row(item_key="어휘3", sort_index=2001, frequency_level=3),
    ]
    audio_assets = [
        make_audio_asset(item_key=row.identity.item_key, asset_kind=kind)
        for row in rows
        for kind in (AudioAssetKind.WORD, AudioAssetKind.SENTENCE)
    ]
    provider_call = SimpleNamespace(
        provider="litellm",
        operation="sentence_generation",
        status="success",
        attempt=2,
        latency_ms=123,
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        estimated_cost=0.01,
        fallback_from=None,
        route_policy_sha256=_HASH_A,
        cache_key_sha256=_HASH_B,
        budget_snapshot_sha256=_HASH_C,
        response_schema_sha256=_HASH_D,
    )
    evidence = report_module.build_korean_frequency_export_evidence(
        job=SimpleNamespace(id="job-ko", language="ko", source_type="frequency", status="completed", total_items=3, failed_items=0),
        rows=rows,
        text_records=[make_text_record(), make_text_record(), make_text_record()],
        audio_assets=audio_assets,
        provider_call_records=[provider_call],
        apkg_sha256=_HASH_F,
        binding_receipt_sha256=_HASH_C,
        manifest_sha256=_HASH_B,
        cards_per_level=1,
        expected_items=3,
        expected_word_assets=3,
        expected_sentence_assets=3,
    )
    result = report_module.write_korean_frequency_generation_report(
        evidence,
        json_path=tmp_path / "exact-report.json",
        markdown_path=tmp_path / "exact-report.md",
    )

    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, ensure_ascii=False) + result.markdown_path.read_text(encoding="utf-8")

    assert payload["export"]["apkg_sha256"] == _HASH_F
    assert payload["frequency_bundle"]["content_sha256"] == _HASH_A
    assert payload["frequency_bundle"]["manifest_sha256"] == _HASH_B
    assert payload["frequency_bundle"]["binding_receipt_sha256"] == _HASH_C
    assert payload["level_counts"] == {"1": 1, "2": 1, "3": 1}
    assert payload["audio"]["word"]["approved"] == 3
    assert payload["audio"]["sentence"]["approved"] == 3
    assert payload["audio"]["fallback_count"] == 0
    assert payload["adaptive_i_plus_one"]["history_2_plus_1_count"] == 3
    assert payload["denominators"]["latency_ms_values"] == 1
    assert payload["denominators"]["token_values"] == 1
    assert payload["denominators"]["cost_values"] == 1
    assert payload["denominators"]["cache_key_sha256_values"] == 1
    assert "LEAK-" not in serialized
    assert "/private/" not in serialized
    assert "exact_apkg_sha256=" + _HASH_F in result.markdown_path.read_text(encoding="utf-8")
