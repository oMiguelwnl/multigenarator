from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

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


@pytest.mark.parametrize("value", [123, True, ["text"], {"text": "value"}])
def test_non_string_batch_fields_require_individual_retry(value) -> None:
    generator = FakeItemGenerator()
    service = BatchTextGenerationService(
        batch_adapter=FakeBatchAdapter(rows=[{"item_key": "a", "sentence": value, "translation": "Works."}]),
        item_generator=generator,
    )

    result = service.execute(candidates=[SimpleNamespace(item_key="a")], language="en")

    assert result.accepted_items == []
    assert result.retried_item_keys == ["a"]


def test_duplicate_batch_rows_are_ambiguous_even_if_the_last_row_is_valid() -> None:
    generator = FakeItemGenerator()
    service = BatchTextGenerationService(
        batch_adapter=FakeBatchAdapter(rows=[
            {"item_key": "a", "sentence": "First.", "translation": "First."},
            {"item_key": "a", "sentence": "Second.", "translation": "Second."},
            {"item_key": "b", "sentence": "Valid.", "translation": "Valid."},
        ]),
        item_generator=generator,
    )

    result = service.execute(candidates=[SimpleNamespace(item_key="a"), SimpleNamespace(item_key="b")], language="en")

    assert result.accepted_items == ["b"]
    assert result.retried_item_keys == ["a"]


@pytest.mark.parametrize("rows", [None, {"item_key": "a"}, "invalid"])
def test_malformed_batch_envelope_retries_each_candidate(rows) -> None:
    generator = FakeItemGenerator()
    service = BatchTextGenerationService(batch_adapter=FakeBatchAdapter(rows=rows), item_generator=generator)

    result = service.execute(candidates=[SimpleNamespace(item_key="a")], language="en")

    assert result.fallback_used is True
    assert generator.calls == ["a"]


@pytest.mark.parametrize("batch_available", [False, True])
def test_one_individual_failure_does_not_skip_later_candidates(batch_available) -> None:
    calls = []

    def generate_one(candidate, *, language):
        calls.append(candidate.item_key)
        if candidate.item_key == "a":
            raise RuntimeError("private provider payload")

    service = BatchTextGenerationService(
        batch_adapter=FakeBatchAdapter(rows=[]) if batch_available else None,
        item_generator=SimpleNamespace(generate_one=generate_one),
    )

    result = service.execute(candidates=[SimpleNamespace(item_key="a"), SimpleNamespace(item_key="b")], language="en")

    assert calls == ["a", "b"]
    assert "a" in result.failed_items
    assert "a" not in result.accepted_items
    assert "private" not in repr(result)


def test_batch_provider_exception_falls_back_individually() -> None:
    def generate_batch(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    generator = FakeItemGenerator()
    service = BatchTextGenerationService(
        batch_adapter=SimpleNamespace(generate_batch=generate_batch), item_generator=generator,
    )

    result = service.execute(candidates=[SimpleNamespace(item_key="a")], language="en")

    assert result.fallback_used is True
    assert generator.calls == ["a"]


def test_missing_item_generator_cannot_silently_mark_fallback_accepted() -> None:
    with pytest.raises(ValueError, match="generate_one"):
        BatchTextGenerationService(batch_adapter=None, item_generator=object())


def test_duplicate_candidate_keys_fail_before_provider_work() -> None:
    adapter = FakeBatchAdapter(rows=[])
    generator = FakeItemGenerator()
    service = BatchTextGenerationService(batch_adapter=adapter, item_generator=generator)

    with pytest.raises(ValueError, match="unique"):
        service.execute(candidates=[SimpleNamespace(item_key="a"), SimpleNamespace(item_key="a")], language="en")

    assert adapter.calls == 0
    assert generator.calls == []
