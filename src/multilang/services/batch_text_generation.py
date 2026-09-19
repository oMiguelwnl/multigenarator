"""Batch text generation boundary with per-item validation results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class BatchTextGenerationAdapter(Protocol):
    def generate_batch(self, candidates: list[object], *, language: object) -> list[dict[str, Any]]: ...


@dataclass(slots=True)
class BatchTextGenerationResult:
    """Structural batch outcomes; acceptance does not grant content review approval.

    A malformed batch item remains in failed_items after individual retry so its
    original failure is observable; retried_item_keys records that separate work.
    """

    accepted_items: list[str] = field(default_factory=list)
    failed_items: list[str] = field(default_factory=list)
    retried_item_keys: list[str] = field(default_factory=list)
    fallback_used: bool = False


class BatchTextGenerationService:
    """Validate structured batch output and retry failed items individually."""

    def __init__(self, *, batch_adapter: BatchTextGenerationAdapter | None, item_generator: object) -> None:
        if not callable(getattr(item_generator, "generate_one", None)):
            raise ValueError("item generator must provide generate_one")
        self.batch_adapter = batch_adapter
        self.item_generator = item_generator

    def execute(self, *, candidates: list[object], language: object) -> BatchTextGenerationResult:
        item_keys = [getattr(candidate, "item_key", None) for candidate in candidates]
        if any(not isinstance(key, str) or not key.strip() for key in item_keys):
            raise ValueError("candidate item keys must be nonempty strings")
        if len(set(item_keys)) != len(item_keys):
            raise ValueError("candidate item keys must be unique")
        if self.batch_adapter is None or not candidates:
            return self._fallback(candidates, language=language)
        try:
            rows = self.batch_adapter.generate_batch(candidates, language=language)
        except Exception:
            return self._fallback(candidates, language=language)
        if not isinstance(rows, list):
            return self._fallback(candidates, language=language)

        by_key: dict[str, dict[str, Any]] = {}
        duplicate_keys: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            key = row.get("item_key")
            if not isinstance(key, str):
                continue
            if key in by_key:
                duplicate_keys.add(key)
            by_key[key] = row
        result = BatchTextGenerationResult()
        for candidate in candidates:
            item_key = str(getattr(candidate, "item_key"))
            row = by_key.get(item_key)
            if item_key not in duplicate_keys and _valid_batch_item(row):
                result.accepted_items.append(item_key)
                continue
            self._generate_one(candidate, language=language)
            result.failed_items.append(item_key)
            result.retried_item_keys.append(item_key)
        return result

    def _fallback(self, candidates: list[object], *, language: object) -> BatchTextGenerationResult:
        result = BatchTextGenerationResult(fallback_used=True)
        for candidate in candidates:
            item_key = str(getattr(candidate, "item_key"))
            if self._generate_one(candidate, language=language):
                result.accepted_items.append(item_key)
            else:
                result.failed_items.append(item_key)
        return result

    def _generate_one(self, candidate: object, *, language: object) -> bool:
        try:
            self.item_generator.generate_one(candidate, language=language)
        except Exception:
            # Keep provider payloads and exception text out of the result, and
            # isolate this failure so later candidates still receive their turn.
            return False
        return True


def _valid_batch_item(row: dict[str, Any] | None) -> bool:
    if row is None:
        return False
    return all(
        isinstance(row.get(field), str) and bool(row[field].strip())
        for field in ("item_key", "sentence", "translation")
    )


__all__ = ["BatchTextGenerationResult", "BatchTextGenerationService"]
