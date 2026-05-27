"""Optional morphology-backed target lemma validation."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Protocol


_TOKEN_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


@dataclass(frozen=True, slots=True)
class MorphologyValidationResult:
    matched: bool
    reliable: bool
    provider: str
    detail: str


class MorphologicalAnalyzer(Protocol):
    def contains_target_lemma(
        self,
        *,
        sentence_text: str,
        target_language: str,
        display_form: str,
        lemma: str,
    ) -> MorphologyValidationResult: ...


class OptionalStanzaMorphologicalAnalyzer:
    """Use installed Stanza models for lemma checks; otherwise report inconclusive."""

    def __init__(self) -> None:
        self._pipelines: dict[str, object | None] = {}

    def contains_target_lemma(
        self,
        *,
        sentence_text: str,
        target_language: str,
        display_form: str,
        lemma: str,
    ) -> MorphologyValidationResult:
        pipeline = self._pipeline_for(target_language)
        if pipeline is None:
            return MorphologyValidationResult(
                matched=False,
                reliable=False,
                provider="stanza",
                detail=f"no local Stanza morphology pipeline for {target_language}",
            )

        try:
            document = pipeline(sentence_text)
        except Exception as exc:  # noqa: BLE001 - Stanza/model errors should not break fallback validation.
            return MorphologyValidationResult(
                matched=False,
                reliable=False,
                provider="stanza",
                detail=f"Stanza morphology failed: {type(exc).__name__}",
            )

        target_keys = _target_keys(display_form, lemma)
        observed: set[str] = set()
        for sentence in getattr(document, "sentences", []) or []:
            for word in getattr(sentence, "words", []) or []:
                observed.update(_target_keys(str(getattr(word, "text", "") or ""), str(getattr(word, "lemma", "") or "")))

        matched = not target_keys.isdisjoint(observed)
        return MorphologyValidationResult(
            matched=matched,
            reliable=True,
            provider="stanza",
            detail="target lemma matched by Stanza" if matched else "target lemma absent from Stanza lemmas",
        )

    def _pipeline_for(self, language: str) -> object | None:
        language = language.casefold()
        if language in self._pipelines:
            return self._pipelines[language]
        try:
            import stanza  # type: ignore[import-not-found]

            pipeline = stanza.Pipeline(
                lang=language,
                processors="tokenize,pos,lemma",
                download_method=None,
                verbose=False,
            )
        except Exception:  # noqa: BLE001 - unavailable package or models means deterministic fallback.
            pipeline = None
        self._pipelines[language] = pipeline
        return pipeline


def _target_keys(*values: str) -> set[str]:
    keys: set[str] = set()
    for value in values:
        normalized = _normalize(value)
        if normalized:
            keys.add(normalized)
            keys.update(_normalize(token) for token in _TOKEN_RE.findall(value))
    return {key for key in keys if key}


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    stripped = "".join(character for character in decomposed if unicodedata.category(character) != "Mn")
    return " ".join(_TOKEN_RE.findall(stripped))


__all__ = ["MorphologicalAnalyzer", "MorphologyValidationResult", "OptionalStanzaMorphologicalAnalyzer"]
