"""Offline and provider-ready validation for generated Latin MVP cards."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from multilang.services.latin_card_generation import LatinGeneratedCard
from multilang.services.latin_source_pack import validate_latin_gramatica, validate_latin_target_presence


class LatinCardValidationIssue(BaseModel):
    """One validation issue from local checks or the OpenRouter judge."""

    sequence: int = Field(ge=1)
    code: str = Field(min_length=1)
    detail: str = Field(min_length=1)


LatinCardJudge = Callable[[LatinGeneratedCard], list[LatinCardValidationIssue | dict[str, object]]]


class LatinCardValidationService:
    """Validate generated Latin cards before they are promoted into source assets."""

    def __init__(self, judge: LatinCardJudge | None = None) -> None:
        self.judge = judge

    def validate(self, card: LatinGeneratedCard) -> list[LatinCardValidationIssue]:
        issues: list[LatinCardValidationIssue] = []
        if not card.definition or not card.definition.strip():
            issues.append(self._issue(card, "missing_definition", "definition must be provided"))
        if not validate_latin_target_presence(card.target_form, card.latin_sentence, "orthographic_normalization"):
            issues.append(self._issue(card, "target_form_missing", "target form must appear in the Latin sentence"))
        try:
            validate_latin_gramatica(card.gramatica)
        except ValueError as exc:
            issues.append(self._issue(card, "invalid_gramatica", str(exc)))
        lowered = f"{card.lemma} {card.target_form} {card.latin_sentence}".casefold()
        if "lemma1" in lowered or "lemma2" in lowered:
            issues.append(self._issue(card, "dummy_content", "dummy lemma placeholder remains"))
        if self.judge is not None:
            issues.extend(LatinCardValidationIssue.model_validate(item) for item in self.judge(card))
        return issues

    @staticmethod
    def _issue(card: LatinGeneratedCard, code: str, detail: str) -> LatinCardValidationIssue:
        return LatinCardValidationIssue(sequence=card.sequence, code=code, detail=detail)


__all__ = [
    "LatinCardValidationIssue",
    "LatinCardValidationService",
]
