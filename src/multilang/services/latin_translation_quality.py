"""Deterministic Portuguese translation QA for the Classical Latin MVP."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from multilang.services.latin_source_pack import LatinMvpSourcePack, LatinMvpSourcePackEntry

DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH = Path("data") / "latin_mvp" / "latin-mvp-50-v1-pt.json"

LatinPortugueseReviewStatus = Literal["needs_review", "approved", "rejected"]
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_ENGLISH_LEAKAGE_TOKENS = frozenset(
    {
        "the",
        "boy",
        "girl",
        "reads",
        "read",
        "and",
        "is",
        "not",
        "in",
        "with",
        "from",
        "to",
        "provider",
        "error",
        "translation",
        "failed",
    }
)
_PROVIDER_ERROR_PATTERNS = (
    "api key",
    "provider error",
    "translation failed",
    "not authenticated",
    "unauthorized",
)


def _not_blank(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(character for character in decomposed if not unicodedata.combining(character))
    return without_marks.casefold().strip()


def _tokens(value: str) -> list[str]:
    return [_normalized(match.group(0)) for match in _TOKEN_RE.finditer(value)]


class LatinPortugueseTranslationQaStatus(str, Enum):
    """Pass/fail status for deterministic Portuguese translation QA."""

    PASSED = "passed"
    FAILED = "failed"


class LatinPortugueseTranslationEntry(BaseModel):
    """One Portuguese translation record aligned to a Latin MVP source-pack entry."""

    item_key: str = Field(min_length=1)
    source_pack_version: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    target_form: str = Field(min_length=1)
    latin_sentence: str = Field(min_length=1)
    short_translation_pt: str = Field(min_length=1)
    sentence_translation_pt: str = Field(min_length=1)
    translation_notes: str = Field(min_length=1)
    review_status: LatinPortugueseReviewStatus = "needs_review"

    _strip_text = field_validator(
        "item_key",
        "source_pack_version",
        "lemma",
        "target_form",
        "latin_sentence",
        "short_translation_pt",
        "sentence_translation_pt",
        "translation_notes",
    )(_not_blank)


class LatinPortugueseTranslationPack(BaseModel):
    """Frozen Portuguese translation pack for the Latin MVP."""

    language_code: Literal["la"] = "la"
    translation_language: Literal["pt"] = "pt"
    source_pack_version: str = Field(min_length=1)
    translation_pack_version: str = Field(min_length=1)
    entries: list[LatinPortugueseTranslationEntry]

    _strip_text = field_validator("source_pack_version", "translation_pack_version")(_not_blank)


class LatinPortugueseTranslationQaIssue(BaseModel):
    """One deterministic Portuguese translation QA issue."""

    item_key: str = Field(min_length=1)
    code: str = Field(min_length=1)
    field: str = Field(min_length=1)
    detail: str = Field(min_length=1)


class LatinPortugueseTranslationQaResult(BaseModel):
    """QA result and scanner-friendly summary for one entry or pack."""

    status: LatinPortugueseTranslationQaStatus
    issues: list[LatinPortugueseTranslationQaIssue] = Field(default_factory=list)
    source_pack_version: str | None = None
    translation_pack_version: str | None = None
    entry_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    review_status_counts: dict[str, int] = Field(default_factory=dict)

    def qa_summary(self) -> dict[str, object]:
        return {
            "source_pack_version": self.source_pack_version,
            "translation_pack_version": self.translation_pack_version,
            "entry_count": self.entry_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "issue_counts": dict(sorted(Counter(issue.code for issue in self.issues).items())),
            "review_status_counts": {
                status: self.review_status_counts.get(status, 0)
                for status in ("needs_review", "approved", "rejected")
            },
        }


class LatinPortugueseTranslationQaService:
    """Offline deterministic validator for learner-facing Portuguese translations."""

    def validate_entry(self, entry: LatinPortugueseTranslationEntry) -> LatinPortugueseTranslationQaResult:
        issues = self._text_issues(entry)
        return LatinPortugueseTranslationQaResult(
            status=LatinPortugueseTranslationQaStatus.FAILED if issues else LatinPortugueseTranslationQaStatus.PASSED,
            issues=issues,
            source_pack_version=entry.source_pack_version,
            entry_count=1,
            passed_count=0 if issues else 1,
            failed_count=1 if issues else 0,
            review_status_counts={entry.review_status: 1},
        )

    def validate_pack(
        self,
        translations: LatinPortugueseTranslationPack,
        source_pack: LatinMvpSourcePack,
    ) -> LatinPortugueseTranslationQaResult:
        issues: list[LatinPortugueseTranslationQaIssue] = []
        expected_keys = [entry.item_key for entry in source_pack.entries]
        actual_keys = [entry.item_key for entry in translations.entries]
        if actual_keys != expected_keys:
            issues.append(
                LatinPortugueseTranslationQaIssue(
                    item_key="pack",
                    code="item_key_order_mismatch",
                    field="entries",
                    detail="translation entries must match source-pack item keys in order",
                )
            )

        by_key = {entry.item_key: entry for entry in source_pack.entries}
        failed_keys: set[str] = set()
        for entry in translations.entries:
            entry_issues = self._text_issues(entry)
            source_entry = by_key.get(entry.item_key)
            if source_entry is None:
                entry_issues.append(self._issue(entry.item_key, "unknown_item_key", "item_key", "item_key is absent from source pack"))
            else:
                entry_issues.extend(self._alignment_issues(entry, source_entry))
            if entry_issues:
                failed_keys.add(entry.item_key)
                issues.extend(entry_issues)

        review_counts = Counter(entry.review_status for entry in translations.entries)
        failed_count = len(failed_keys)
        passed_count = max(0, len(translations.entries) - failed_count)
        return LatinPortugueseTranslationQaResult(
            status=LatinPortugueseTranslationQaStatus.FAILED if issues else LatinPortugueseTranslationQaStatus.PASSED,
            issues=issues,
            source_pack_version=source_pack.source_pack_version,
            translation_pack_version=translations.translation_pack_version,
            entry_count=len(translations.entries),
            passed_count=passed_count,
            failed_count=failed_count,
            review_status_counts=dict(review_counts),
        )

    def _text_issues(self, entry: LatinPortugueseTranslationEntry) -> list[LatinPortugueseTranslationQaIssue]:
        issues: list[LatinPortugueseTranslationQaIssue] = []
        combined_tokens = set(_tokens(f"{entry.short_translation_pt} {entry.sentence_translation_pt}"))
        leaked = sorted(combined_tokens & _ENGLISH_LEAKAGE_TOKENS)
        if leaked:
            issues.append(self._issue(entry.item_key, "english_leakage", "translation_text", f"English token(s) detected: {', '.join(leaked)}"))
        lowered = _normalized(f"{entry.short_translation_pt} {entry.sentence_translation_pt}")
        for pattern in _PROVIDER_ERROR_PATTERNS:
            if pattern in lowered:
                issues.append(self._issue(entry.item_key, "provider_error_text", "translation_text", f"provider/error text detected: {pattern}"))
        if _normalized(entry.sentence_translation_pt) == _normalized(entry.latin_sentence):
            issues.append(self._issue(entry.item_key, "latin_copy", "sentence_translation_pt", "sentence translation copies the Latin sentence"))
        latin_token_overlap = set(_tokens(entry.latin_sentence)) & set(_tokens(entry.sentence_translation_pt))
        if len(latin_token_overlap) >= max(2, len(set(_tokens(entry.latin_sentence))) - 1):
            issues.append(self._issue(entry.item_key, "latin_copy", "sentence_translation_pt", "sentence translation retains too many Latin tokens"))
        if len(_tokens(entry.latin_sentence)) > 1 and len(_tokens(entry.sentence_translation_pt)) <= 1:
            issues.append(self._issue(entry.item_key, "dictionary_only_sentence", "sentence_translation_pt", "multi-token Latin sentence needs a sentence translation"))
        return issues

    def _alignment_issues(
        self,
        entry: LatinPortugueseTranslationEntry,
        source_entry: LatinMvpSourcePackEntry,
    ) -> list[LatinPortugueseTranslationQaIssue]:
        checks = (
            ("source_pack_version", entry.source_pack_version, source_entry.source_pack_version, "source_pack_version_mismatch"),
            ("lemma", entry.lemma, source_entry.lemma, "lemma_mismatch"),
            ("target_form", entry.target_form, source_entry.target_form, "target_form_mismatch"),
            ("latin_sentence", entry.latin_sentence, source_entry.latin_sentence, "latin_sentence_mismatch"),
        )
        return [
            self._issue(entry.item_key, code, field, f"translation {field} does not match source pack")
            for field, actual, expected, code in checks
            if actual != expected
        ]

    @staticmethod
    def _issue(item_key: str, code: str, field: str, detail: str) -> LatinPortugueseTranslationQaIssue:
        return LatinPortugueseTranslationQaIssue(item_key=item_key, code=code, field=field, detail=detail)


def load_latin_portuguese_translation_pack(path: Path | None = None) -> LatinPortugueseTranslationPack:
    """Load and validate the frozen Portuguese translation pack from committed JSON."""

    pack_path = path or DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH
    try:
        return LatinPortugueseTranslationPack.model_validate(json.loads(pack_path.read_text(encoding="utf-8")))
    except FileNotFoundError as exc:
        raise ValueError("Latin MVP Portuguese translation pack is missing") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Latin MVP Portuguese translation pack JSON is malformed") from exc


__all__ = [
    "DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH",
    "LatinPortugueseTranslationEntry",
    "LatinPortugueseTranslationPack",
    "LatinPortugueseTranslationQaIssue",
    "LatinPortugueseTranslationQaResult",
    "LatinPortugueseTranslationQaService",
    "LatinPortugueseTranslationQaStatus",
    "load_latin_portuguese_translation_pack",
]
