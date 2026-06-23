"""Corpus-backed language identification for generated learner text."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

from wordfreq import zipf_frequency


SUPPORTED_LANGUAGE_CODES = ("pt", "es", "en", "fr", "de", "it", "pl", "tr", "ro", "ru", "nl", "nb")
_TOKEN_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


@dataclass(frozen=True, slots=True)
class LanguageDetectionResult:
    detected_language: str | None
    confidence: float
    reliable: bool
    provider: str
    detail: str


class LanguageIdentifier(Protocol):
    def detect(self, value: str, *, expected_language: str | None = None) -> LanguageDetectionResult: ...


class CorpusLanguageIdentifier:
    """Identify language by comparing token frequencies across supported corpora."""

    min_alpha_tokens = 3
    min_best_score = 2.25
    min_margin = 0.35

    def detect(self, value: str, *, expected_language: str | None = None) -> LanguageDetectionResult:
        tokens = _letter_tokens(value)
        if len(tokens) < self.min_alpha_tokens:
            return LanguageDetectionResult(
                detected_language=None,
                confidence=0.0,
                reliable=False,
                provider="wordfreq",
                detail="not enough alphabetic tokens for corpus language-id",
            )

        scores = {
            language: _average_language_score(tokens, language)
            for language in SUPPORTED_LANGUAGE_CODES
        }
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_language, best_score = ranked[0]
        runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = best_score - runner_up_score
        expected_score = scores.get((expected_language or "").casefold(), 0.0)
        expected_margin = best_score - expected_score
        reliable = best_score >= self.min_best_score and (
            margin >= self.min_margin or (expected_language is not None and expected_margin >= self.min_margin)
        )
        confidence = max(0.0, min(1.0, round((best_score / 7.0) + max(margin, expected_margin) / 3.0, 2)))
        return LanguageDetectionResult(
            detected_language=best_language if reliable else None,
            confidence=confidence,
            reliable=reliable,
            provider="wordfreq",
            detail=f"best={best_language}:{best_score:.2f} expected={expected_language}:{expected_score:.2f} margin={margin:.2f}",
        )


def _letter_tokens(value: str) -> list[str]:
    return [token.casefold() for token in _TOKEN_RE.findall(value) if any(character.isalpha() for character in token)]


def _average_language_score(tokens: list[str], language: str) -> float:
    scores = [max(0.0, zipf_frequency(token, language) - 1.0) for token in tokens]
    return sum(scores) / len(scores) if scores else 0.0


__all__ = ["CorpusLanguageIdentifier", "LanguageDetectionResult", "LanguageIdentifier"]
