from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

from multilang.services.batch_text_generation import BatchTextGenerationService


@dataclass
class FakeBatchAdapter:
    rows: list[dict[str, object]]
    calls: int = 0

    def generate_batch(self, candidates: list[object], *, language: object) -> list[dict[str, object]]:
        self.calls += 1
        return self.rows


@dataclass
class FakeItemGenerator:
    calls: list[str] = field(default_factory=list)

    def generate_one(self, candidate: object, *, language: object) -> None:
        self.calls.append(str(getattr(candidate, "item_key")))


def test_batch_text_generation_accepts_json_partial_success_and_retries_failed_items() -> None:
    candidates = [SimpleNamespace(item_key="a"), SimpleNamespace(item_key="b")]
    item_generator = FakeItemGenerator()
    service = BatchTextGenerationService(
        batch_adapter=FakeBatchAdapter(rows=[{"item_key": "a", "sentence": "A works.", "translation": "A works."}]),
        item_generator=item_generator,
    )

    result = service.execute(candidates=candidates, language="en")

    assert result.accepted_items == ["a"]
    assert result.failed_items == ["b"]
    assert result.retried_item_keys == ["b"]
    assert item_generator.calls == ["b"]


def test_batch_text_generation_invalid_item_retries_only_that_item() -> None:
    candidates = [SimpleNamespace(item_key="a"), SimpleNamespace(item_key="b")]
    item_generator = FakeItemGenerator()
    service = BatchTextGenerationService(
        batch_adapter=FakeBatchAdapter(rows=[{"item_key": "a", "sentence": "", "translation": "x"}, {"item_key": "b", "sentence": "B works.", "translation": "B works."}]),
        item_generator=item_generator,
    )

    result = service.execute(candidates=candidates, language="en")

    assert result.accepted_items == ["b"]
    assert result.retried_item_keys == ["a"]
    assert item_generator.calls == ["a"]


def test_batch_text_generation_falls_back_to_per_item_when_unavailable() -> None:
    candidates = [SimpleNamespace(item_key="a"), SimpleNamespace(item_key="b")]
    item_generator = FakeItemGenerator()
    service = BatchTextGenerationService(batch_adapter=None, item_generator=item_generator)

    result = service.execute(candidates=candidates, language="en")

    assert result.fallback_used is True
    assert result.accepted_items == ["a", "b"]
    assert item_generator.calls == ["a", "b"]
