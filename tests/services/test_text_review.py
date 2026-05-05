"""Tests for persisted text review reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.text_review import TextReviewService


def make_record(
    *,
    item_key: str,
    confidence_label: ConfidenceLabel = ConfidenceLabel.LOW,
    validation_flags: list[ValidationFlag] | None = None,
    review_reason: str = "low_confidence",
    review_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED,
    example_sentence: str = "I wash the cup at home.",
    translation_text: str = "Eu lavo a xícara em casa.",
) -> TextQualityRecord:
    return TextQualityRecord(
        job_id="job-123",
        item_key=item_key,
        lexical_candidate_id=f"lex-{item_key}",
        example_sentence=example_sentence,
        translation_text=translation_text,
        generation_status=TextGenerationStatus.GENERATED,
        validation_status=ValidationStatus.FAILED,
        review_status=review_status,
        repair_attempt_count=1,
        confidence_score=0.21,
        confidence_label=confidence_label,
        validation_flags=validation_flags
        or [
            ValidationFlag(
                code=ValidationFlagCode.LOW_CONFIDENCE,
                detail="confidence dropped below threshold",
            )
        ],
        review_reason=review_reason,
        sentence_provenance=TextProvenance(source="generator"),
        translation_provenance=TextProvenance(source="translator"),
    )


@dataclass
class FakeTextRepository:
    records: list[TextQualityRecord]
    source_metadata: dict[str, dict[str, object]] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)

    def list_flagged_records(self, job_id: str) -> list[TextQualityRecord]:
        self.calls.append(job_id)
        return list(self.records)

    def get_source_metadata_for_item(self, job_id: str, item_key: str) -> dict[str, object] | None:
        return self.source_metadata.get(item_key)


def build_service(
    *records: TextQualityRecord,
    source_metadata: dict[str, dict[str, object]] | None = None,
) -> tuple[TextReviewService, FakeTextRepository]:
    repository = FakeTextRepository(records=list(records), source_metadata=source_metadata or {})
    return TextReviewService(text_repository=repository), repository


def test_build_review_report_orders_highest_risk_items_first(tmp_path: Path) -> None:
    service, repository = build_service(
        make_record(item_key="line-medium", confidence_label=ConfidenceLabel.MEDIUM),
        make_record(
            item_key="line-high-risk",
            validation_flags=[
                ValidationFlag(code=ValidationFlagCode.LOW_CONFIDENCE, detail="low confidence"),
                ValidationFlag(code=ValidationFlagCode.BANNED_PATTERN, detail="placeholder text"),
            ],
        ),
        make_record(item_key="line-low-risk", confidence_label=ConfidenceLabel.HIGH),
    )

    report = service.build_review_report(job_id="job-123", output_path=tmp_path / "review.json")

    assert repository.calls == ["job-123"]
    assert [item.item_key for item in report.items] == [
        "line-high-risk",
        "line-medium",
        "line-low-risk",
    ]


def test_review_report_keeps_job_and_item_identity(tmp_path: Path) -> None:
    service, _ = build_service(make_record(item_key="line-7"))

    report = service.build_review_report(job_id="job-123", output_path=tmp_path / "review.json")

    assert report.job_id == "job-123"
    assert report.items[0].item_key == "line-7"
    assert report.items[0].job_id == "job-123"
    assert report.items[0].review_reason == "low_confidence"
    assert report.items[0].validation_flags == ["low_confidence"]


def test_build_review_report_writes_deterministic_json_artifact(tmp_path: Path) -> None:
    service, _ = build_service(make_record(item_key="line-7"))

    report = service.build_review_report(job_id="job-123", output_path=tmp_path / "review.json")

    assert report.report_path == tmp_path / "review.json"
    assert report.report_path.read_text(encoding="utf-8") == "".join(
        [
            "{\n",
            '  "job_id": "job-123",\n',
            '  "generated_at": null,\n',
            '  "item_count": 1,\n',
            '  "items": [\n',
            "    {\n",
            '      "confidence_label": "low",\n',
            '      "example_sentence": "I wash the cup at home.",\n',
            '      "item_key": "line-7",\n',
            '      "job_id": "job-123",\n',
            '      "review_reason": "low_confidence",\n',
            '      "source_type": "word-list",\n',
            '      "translation_text": "Eu lavo a x\u00edcara em casa.",\n',
            '      "translation_required": true,\n',
            '      "validation_flags": [\n',
            '        "low_confidence"\n',
            "      ]\n",
            "    }\n",
            "  ]\n",
            "}\n",
        ]
    )


def test_review_report_items_include_source_type_and_translation_policy(tmp_path: Path) -> None:
    service, _ = build_service(
        make_record(item_key="highlight:abc:wash", translation_text="translation omitted"),
        source_metadata={"highlight:abc:wash": {"source_type": "kindle-highlights"}},
    )

    report = service.build_review_report(job_id="job-123", output_path=tmp_path / "review.json")

    assert report.items[0].source_type == "kindle-highlights"
    assert report.items[0].translation_required is False


def test_highlight_review_report_redacts_private_text_and_paths(tmp_path: Path) -> None:
    private_sentence = "Book: Secret Novel\nReaders wash every cup. Location: 123 https://reader.example/dav/private"
    service, _ = build_service(
        make_record(
            item_key="highlight:abc:wash",
            example_sentence=private_sentence,
            translation_text="user=private-token should be hidden",
        ),
        source_metadata={"highlight:abc:wash": {"source_type": "kindle-highlights"}},
    )

    report = service.build_review_report(job_id="job-123", output_path=tmp_path / "review.json")
    payload = report.report_path.read_text(encoding="utf-8")

    assert "Secret Novel" not in payload
    assert "Location: 123" not in payload
    assert "dav/private" not in payload
    assert "private-token" not in payload
    assert report.items[0].source_type == "kindle-highlights"
    assert report.items[0].validation_flags == ["low_confidence"]
