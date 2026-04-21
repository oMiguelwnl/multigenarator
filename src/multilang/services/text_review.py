"""Build persisted review reports for flagged text rows."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from multilang.domain.text_quality import ConfidenceLabel, TextQualityRecord


class ReviewReportItem(BaseModel):
    confidence_label: ConfidenceLabel
    example_sentence: str | None = None
    item_key: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    review_reason: str | None = None
    translation_text: str | None = None
    validation_flags: list[str] = Field(default_factory=list)


class ReviewReport(BaseModel):
    job_id: str = Field(min_length=1)
    generated_at: str | None = None
    item_count: int = Field(ge=0)
    items: list[ReviewReportItem] = Field(default_factory=list)
    report_path: Path | None = Field(default=None, exclude=True)


class TextReviewService:
    """Serialize flagged text rows into a deterministic review artifact."""

    def __init__(self, *, text_repository: object) -> None:
        self.text_repository = text_repository

    def build_review_report(self, *, job_id: str, output_path: Path | str) -> ReviewReport:
        items = [self._to_item(record) for record in self.text_repository.list_flagged_records(job_id)]
        items.sort(key=self._sort_key)
        report_path = Path(output_path) if items else None

        report = ReviewReport(
            job_id=job_id,
            item_count=len(items),
            items=items,
            report_path=report_path,
        )
        self._write_report(report)
        return report

    def _to_item(self, record: TextQualityRecord) -> ReviewReportItem:
        return ReviewReportItem(
            job_id=record.job_id,
            item_key=record.item_key,
            example_sentence=record.example_sentence,
            translation_text=record.translation_text,
            confidence_label=record.confidence_label,
            validation_flags=[flag.code.value for flag in record.validation_flags],
            review_reason=record.review_reason,
        )

    def _sort_key(self, item: ReviewReportItem) -> tuple[int, int, int, str]:
        return (
            self._review_priority(item),
            self._confidence_priority(item.confidence_label),
            -len(item.validation_flags),
            item.item_key,
        )

    def _review_priority(self, item: ReviewReportItem) -> int:
        return 0 if item.review_reason or item.validation_flags else 1

    def _confidence_priority(self, confidence_label: ConfidenceLabel) -> int:
        priorities = {
            ConfidenceLabel.LOW: 0,
            ConfidenceLabel.MEDIUM: 1,
            ConfidenceLabel.HIGH: 2,
        }
        return priorities[confidence_label]

    def _write_report(self, report: ReviewReport) -> None:
        if report.report_path is None:
            return
        report.report_path.parent.mkdir(parents=True, exist_ok=True)
        payload = report.model_dump(mode="json", exclude={"report_path"})
        report.report_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


__all__ = ["ReviewReport", "ReviewReportItem", "TextReviewService"]
