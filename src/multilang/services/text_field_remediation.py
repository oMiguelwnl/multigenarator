"""Deterministic remediation for learner-facing generated text fields."""

from __future__ import annotations

import re
import unicodedata
from html import escape

from multilang.services.part_of_speech import canonical_part_of_speech_label, resolve_part_of_speech_label

_KNOWN_DEFINITION_CORRECTIONS = {
    "достичь": "verb: to achieve, to attain, to reach",
}

_RELATION_ONLY_RE = re.compile(
    r"\b(?:inflection|genitive|accusative|dative|instrumental|prepositional|nominative|locative|ablative)\s+of\b"
)
_PLACEHOLDER_DEFINITION_RE = re.compile(r"\blearner\s+definition\s+for\b")
_GRAMMAR_ONLY_TERMS = {
    "ablative",
    "accusative",
    "animate",
    "dative",
    "feminine",
    "genitive",
    "instrumental",
    "locative",
    "masculine",
    "neuter",
    "nominative",
    "indicative",
    "past",
    "perfective",
    "plural",
    "prepositional",
    "short",
    "singular",
    "vocative",
}


def remediate_definition_html(
    *,
    display_form: str,
    lemma: str,
    part_of_speech: str | None,
    generated_html: str | None,
    source_definitions: list[str],
    source_language: str | None = None,
) -> str | None:
    """Return learner-safe definition HTML when deterministic remediation is possible."""

    known = _KNOWN_DEFINITION_CORRECTIONS.get(_normalize_key(lemma)) or _KNOWN_DEFINITION_CORRECTIONS.get(
        _normalize_key(display_form)
    )
    if known is not None:
        return known

    label = _definition_label(
        display_form=display_form,
        lemma=lemma,
        part_of_speech=part_of_speech,
        source_language=source_language,
        generated_html=generated_html,
    ) or "term"

    if generated_html and _is_learner_safe_definition(generated_html):
        return _normalize_definition_label(generated_html, label=label)

    source_meaning = _select_substantive_source_definition(source_definitions)
    if source_meaning is None:
        return generated_html

    formatted = f"{label}: {source_meaning}" if label else source_meaning
    return escape(formatted)


def validate_definition_html(*, lemma_key: str, definitions_html: str | None) -> None:
    """Raise if a Definition field still contains learner-hostile morphology metadata."""

    if not definitions_html or not _is_learner_safe_definition(definitions_html):
        raise ValueError(f"definition for {lemma_key} must be a learner-safe semantic definition")
    known = _KNOWN_DEFINITION_CORRECTIONS.get(_normalize_key(lemma_key))
    if known is not None:
        definition_text = "\n".join(_definition_parts(definitions_html))
        if _normalize_definition_text(definition_text) != _normalize_definition_text(known):
            raise ValueError(f"definition for {lemma_key} must use the known corrected meaning")


def _is_learner_safe_definition(definitions_html: str) -> bool:
    parts = _definition_parts(definitions_html)
    return bool(parts) and all(_is_substantive_definition(part) for part in parts)


def _definition_parts(definitions_html: str) -> list[str]:
    cleaned = re.sub(r"</(?:li|ul)>", "\n", definitions_html)
    cleaned = re.sub(r"<(?:ul|li)[^>]*>", "", cleaned)
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return [part.strip() for part in cleaned.splitlines() if part.strip()]


def _is_substantive_definition(definition: str) -> bool:
    normalized = _without_label(" ".join(definition.casefold().split()))
    if not normalized:
        return False
    if _PLACEHOLDER_DEFINITION_RE.search(normalized):
        return False
    if _RELATION_ONLY_RE.search(normalized):
        return False
    before_of, separator, _ = normalized.partition(" of ")
    if separator:
        relation_words = set(re.findall(r"[a-z]+", before_of))
        if relation_words and relation_words.issubset(_GRAMMAR_ONLY_TERMS):
            return False
    words = set(re.findall(r"[a-z]+", normalized))
    if words and words.issubset(_GRAMMAR_ONLY_TERMS):
        return False
    return True


def _select_substantive_source_definition(source_definitions: list[str]) -> str | None:
    for definition in source_definitions:
        cleaned = " ".join(definition.split())
        if cleaned and _is_substantive_definition(cleaned):
            return cleaned
    return None


def _without_label(value: str) -> str:
    return re.sub(r"^[a-z][a-z -]{1,40}:\s+", "", value).strip()


def _definition_label(
    *,
    display_form: str,
    lemma: str,
    part_of_speech: str | None,
    source_language: str | None,
    generated_html: str | None,
) -> str | None:
    return resolve_part_of_speech_label(
        part_of_speech=part_of_speech,
        source_language=source_language,
        display_form=display_form,
        lemma=lemma,
    ) or _provider_part_of_speech_label(generated_html)


def _normalize_definition_label(definitions_html: str, *, label: str | None) -> str:
    return "<br>".join(_replace_definition_part_label(part, label=label) for part in _definition_parts(definitions_html))


def _provider_part_of_speech_label(definitions_html: str | None) -> str | None:
    if not definitions_html:
        return None
    parts = _definition_parts(definitions_html)
    if not parts:
        return None
    raw_label, separator, _meaning = parts[0].partition(":")
    if not separator:
        return None
    return canonical_part_of_speech_label(raw_label)


def _replace_definition_part_label(part: str, *, label: str | None) -> str:
    meaning = _without_label(part)
    if label is None:
        return meaning or part
    return f"{label}: {meaning}" if meaning else f"{label}: {part}"


def _normalize_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _normalize_definition_text(value: str) -> str:
    return " ".join(_normalize_key(value).split())


__all__ = ["remediate_definition_html", "validate_definition_html"]
