"""Provider-ready Latin MVP card generation contracts."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field


class LatinCardGenerationSeed(BaseModel):
    """One lemma/form request for Latin card generation."""

    sequence: int = Field(ge=1)
    lemma: str = Field(min_length=1)
    target_form: str = Field(min_length=1)
    part_of_speech: str = Field(min_length=1)


class LatinGeneratedCard(BaseModel):
    """Structured output expected from the OpenRouter card generation step."""

    sequence: int = Field(ge=1)
    lemma: str = Field(min_length=1)
    target_form: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    latin_sentence: str = Field(min_length=1)
    gramatica: str = Field(min_length=1)
    morphology_note: str = Field(min_length=1)


LatinCardGenerator = Callable[[list[LatinCardGenerationSeed]], list[LatinGeneratedCard | dict[str, object]]]


class LatinCardGenerationService:
    """Generate structured Latin cards through an injected provider adapter."""

    def __init__(self, generator: LatinCardGenerator) -> None:
        self.generator = generator

    def generate(self, seeds: list[LatinCardGenerationSeed]) -> list[LatinGeneratedCard]:
        if not seeds:
            raise ValueError("Latin card generation requires at least one seed")
        cards = [LatinGeneratedCard.model_validate(item) for item in self.generator(seeds)]
        expected_sequences = [seed.sequence for seed in seeds]
        actual_sequences = [card.sequence for card in cards]
        if actual_sequences != expected_sequences:
            raise ValueError("generated Latin cards must preserve seed sequence order")
        return cards


__all__ = [
    "LatinCardGenerationSeed",
    "LatinCardGenerationService",
    "LatinGeneratedCard",
]
