"""Batch text generation boundary with per-item validation results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class BatchTextGenerationAdapter(Protocol):
    def generate_batch(self, candidates: list[object], *, language: object) -> list[dict[str, Any]]: ...


@dataclass(slots=True)
class BatchTextGenerationResult:
    accepted_items: list[str] = field(default_factory=list)
    failed_items: list[str] = field(default_factory=list)
    retried_item_keys: list[str] = field(default_factory=list)
    fallback_used: bool = False


class BatchTextGenerationService:
    """Validate structured batch output and retry failed items individually."""

    def __init__(self, *, batch_adapter: BatchTextGenerationAdapter | None, item_generator: object) -> None:
        self.batch_adapter = batch_adapter
        self.item_generator = item_generator

    def execute(self, *, candidates: list[object], language: object) -> BatchTextGenerationResult:
        if self.batch_adapter is None or not candidates:
            return self._fallback(candidates, language=language)
        try:
            rows = self.batch_adapter.generate_batch(candidates, language=language)
        except (NotImplementedError, AttributeError, ValueError):
            return self._fallback(candidates, language=language)

        by_key = {str(row.get("item_key", "")): row for row in rows if isinstance(row, dict)}
        result = BatchTextGenerationResult()
        for candidate in candidates:
            item_key = str(getattr(candidate, "item_key"))
            row = by_key.get(item_key)
            if _valid_batch_item(row):
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
            self._generate_one(candidate, language=language)
            result.accepted_items.append(item_key)
        return result

    def _generate_one(self, candidate: object, *, language: object) -> None:
        generator = getattr(self.item_generator, "generate_one", None)
        if callable(generator):
            generator(candidate, language=language)


def _valid_batch_item(row: dict[str, Any] | None) -> bool:
    if row is None:
        return False
    return all(str(row.get(field) or "").strip() for field in ("item_key", "sentence", "translation"))


__all__ = ["BatchTextGenerationResult", "BatchTextGenerationService"]
