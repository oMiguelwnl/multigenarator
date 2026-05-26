from __future__ import annotations

from dataclasses import dataclass

from multilang.domain.exporting import ExportQualityGateResult
from multilang.services.generation_report import write_generation_report


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
        provider_call_summary=[{"provider": "litellm", "operation": "sentence", "status": "success", "calls": 1, "retry_attempts": 0, "latency_ms_total": 12, "latency_ms_p95": 12, "total_tokens": 9, "estimated_cost": 0.0, "fallback_count": 0, "circuit_open_blocks": 0}],
    )

    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "## Provider Calls" in markdown
    assert "provider:litellm operation:sentence status:success" in markdown
