"""Optional morphology-backed target lemma validation."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
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

        expressions = multiword_targets(display_form, lemma)
        if expressions:
            matched = _document_contains_expression(document, expressions)
        else:
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


def _expression_form(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().replace("’", "'").split())


def multiword_targets(*values: str) -> tuple[str, ...]:
    """Keep complete expression alternatives without accepting their components."""
    return tuple(dict.fromkeys(_expression_form(value) for value in values if len(value.split()) > 1))


def contains_whole_expression(text: str, expression: str) -> bool:
    pattern = r"(?<![\w'-])" + re.escape(expression) + r"(?![\w'-])"
    return re.search(pattern, _expression_form(text)) is not None


def _document_contains_expression(document: object, expressions: tuple[str, ...]) -> bool:
    for sentence in getattr(document, "sentences", []) or []:
        words = [
            {_expression_form(str(getattr(word, field, "") or "")) for field in ("text", "lemma")}
            for word in getattr(sentence, "words", []) or []
        ]
        for expression in expressions:
            parts = expression.split()
            for start in range(len(words) - len(parts) + 1):
                if all(part in words[start + offset] for offset, part in enumerate(parts)):
                    return True
    return False


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
