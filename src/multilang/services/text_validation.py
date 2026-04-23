"""Deterministic validation and confidence scoring for generated text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, Field

from multilang.domain.text_quality import (
    ConfidenceLabel,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation

_TOKEN_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_BANNED_PATTERNS = (
    "todo",
    "fixme",
    "placeholder",
    "coming soon",
    "lorem ipsum",
)
_GENERIC_SUPPORT_VERBS = {"use", "uso", "utilise", "benutze", "gebruik", "использую"}
_META_SENTENCE_PREFIXES = (
    "example",
    "for example",
    "a palavra",
    "das wort",
    "het woord",
    "la palabra",
    "le mot",
    "the word",
    "слово",
)
_MATCHABLE_SUFFIXES = (
    "arse",
    "erse",
    "irse",
    "rse",
    "ing",
    "ed",
    "ies",
    "amos",
    "emos",
    "imos",
    "aron",
    "eron",
    "ando",
    "iendo",
    "ado",
    "ido",
    "es",
    "en",
    "er",
    "ir",
    "re",
    "ar",
    "se",
    "s",
    "e",
    "o",
    "a",
)


class TextValidationResult(BaseModel):
    validation_status: ValidationStatus
    validation_flags: list[ValidationFlag] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel


@dataclass(slots=True)
class _ValidationContext:
    sentence_text: str
    translation_text: str
    definition_text: str
    sentence_tokens: list[str]
    uncertainty_notes: list[str]


class TextValidationService:
    """Apply deterministic sentence and translation quality checks."""

    min_sentence_tokens = 4
    max_sentence_tokens = 12

    def validate(
        self,
        *,
        sentence: GeneratedSentence,
        translation: GeneratedTranslation,
        display_form: str,
        lemma: str,
        definitions_html: str | None,
        uncertainty_notes: list[str] | None = None,
    ) -> TextValidationResult:
        context = _ValidationContext(
            sentence_text=sentence.text.strip(),
            translation_text=translation.text.strip(),
            definition_text=_normalize_text(definitions_html or ""),
            sentence_tokens=_tokenize(sentence.text),
            uncertainty_notes=[
                note.strip()
                for note in [*(sentence.uncertainty_notes or []), *(uncertainty_notes or [])]
                if note.strip()
            ],
        )
        flags: list[ValidationFlag] = []

        self._check_target_form(flags, context=context, display_form=display_form, lemma=lemma)
        self._check_sentence_length(flags, context=context)
        self._check_banned_patterns(
            flags,
            context=context,
            display_form=display_form,
            lemma=lemma,
            definitions_html=definitions_html,
        )
        self._check_translation(flags, context=context)

        validation_status = ValidationStatus.FAILED if flags else ValidationStatus.PASSED
        confidence_score = self._score(flags=flags, uncertainty_count=len(context.uncertainty_notes))
        confidence_label = self._label_for(
            validation_status=validation_status,
            confidence_score=confidence_score,
            flag_count=len(flags),
            uncertainty_count=len(context.uncertainty_notes),
        )

        if validation_status is ValidationStatus.PASSED and confidence_label is ConfidenceLabel.LOW:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.LOW_CONFIDENCE,
                    detail="confidence dropped below the learner-facing acceptance threshold",
                )
            )
            validation_status = ValidationStatus.FAILED

        return TextValidationResult(
            validation_status=validation_status,
            validation_flags=flags,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
        )

    def _check_target_form(
        self,
        flags: list[ValidationFlag],
        *,
        context: _ValidationContext,
        display_form: str,
        lemma: str,
    ) -> None:
        candidates = _match_keys(display_form) | _match_keys(lemma)
        sentence_terms = {
            key
            for token in context.sentence_tokens
            for key in _match_keys(token)
        }
        if candidates.isdisjoint(sentence_terms):
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.MISSING_TARGET_LEMMA,
                    detail="sentence must include the target lemma or required study form",
                )
            )

    def _check_sentence_length(self, flags: list[ValidationFlag], *, context: _ValidationContext) -> None:
        token_count = len(context.sentence_tokens)
        if token_count < self.min_sentence_tokens:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.SENTENCE_TOO_SHORT,
                    detail=f"sentence has {token_count} tokens; expected at least {self.min_sentence_tokens}",
                )
            )
        if token_count > self.max_sentence_tokens:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.SENTENCE_TOO_LONG,
                    detail=f"sentence has {token_count} tokens; expected at most {self.max_sentence_tokens}",
                )
            )

    def _check_banned_patterns(
        self,
        flags: list[ValidationFlag],
        *,
        context: _ValidationContext,
        display_form: str,
        lemma: str,
        definitions_html: str | None,
    ) -> None:
        lowered_sentence = context.sentence_text.casefold()
        if any(pattern in lowered_sentence for pattern in _BANNED_PATTERNS) or _has_repetitive_tokens(
            context.sentence_tokens
        ) or _looks_like_hollow_support_template(
            context.sentence_tokens,
            display_form=display_form,
            lemma=lemma,
            definitions_html=definitions_html,
        ) or _looks_like_meta_sentence(context.sentence_text) or _looks_like_question_or_prompt(
            context.sentence_text
        ) or _looks_like_short_command(
            context.sentence_text,
            context.sentence_tokens,
            display_form=display_form,
            lemma=lemma,
        ):
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.BANNED_PATTERN,
                    detail="sentence contains placeholder, robotic, or overly repetitive text",
                )
            )

    def _check_translation(self, flags: list[ValidationFlag], *, context: _ValidationContext) -> None:
        translation_text = _normalize_text(context.translation_text)
        if not translation_text:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.TRANSLATION_MISMATCH,
                    detail="translation must not be empty",
                )
            )
            return

        if translation_text == context.definition_text:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.TRANSLATION_MISMATCH,
                    detail="translation appears copied from the lexical definition instead of the sentence",
                )
            )
            return

        if translation_text == _normalize_text(context.sentence_text):
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.TRANSLATION_MISMATCH,
                    detail="translation must not simply repeat the displayed sentence",
                )
            )

    def _score(self, *, flags: list[ValidationFlag], uncertainty_count: int) -> float:
        score = 0.95
        score -= 0.25 * len(flags)
        score -= 0.18 * uncertainty_count
        return max(0.0, min(1.0, round(score, 2)))

    def _label_for(
        self,
        *,
        validation_status: ValidationStatus,
        confidence_score: float,
        flag_count: int,
        uncertainty_count: int,
    ) -> ConfidenceLabel:
        if validation_status is ValidationStatus.FAILED or flag_count >= 2 or confidence_score < 0.55:
            return ConfidenceLabel.LOW
        if uncertainty_count or confidence_score < 0.85:
            return ConfidenceLabel.MEDIUM
        return ConfidenceLabel.HIGH


def _tokenize(value: str) -> list[str]:
    return _TOKEN_RE.findall(value.casefold())


def _normalize_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(_TOKEN_RE.findall(value.casefold()))


def _match_keys(value: str) -> set[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return set()

    keys: set[str] = {normalized}
    for token in normalized.split():
        keys.update(_derive_matchable_forms(token))
    return keys


def _derive_matchable_forms(token: str) -> set[str]:
    derived: set[str] = set()
    queue = [token]

    while queue:
        current = queue.pop()
        if current in derived:
            continue
        derived.add(current)

        for suffix in _MATCHABLE_SUFFIXES:
            if not current.endswith(suffix):
                continue

            stripped = current[: -len(suffix)]
            if len(stripped) < 3:
                continue

            queue.append(stripped)
            if len(stripped) >= 4 and stripped[-1] == stripped[-2]:
                queue.append(stripped[:-1])

    return derived


def _has_repetitive_tokens(tokens: list[str]) -> bool:
    if len(tokens) < 4:
        return False
    run = 1
    previous = ""
    for token in tokens:
        if token == previous:
            run += 1
            if run >= 3:
                return True
        else:
            run = 1
            previous = token
    return False


def _looks_like_hollow_support_template(
    tokens: list[str],
    *,
    display_form: str,
    lemma: str,
    definitions_html: str | None,
) -> bool:
    definition_text = _normalize_text(definitions_html or "")
    if not definition_text.startswith("to "):
        return False

    targets = {token for token in _normalize_text(display_form).split() if token}
    targets.update(token for token in _normalize_text(lemma).split() if token)
    if len(targets) != 1:
        return False

    target = next(iter(targets))
    for previous, current in zip(tokens, tokens[1:], strict=False):
        if current == target and previous in _GENERIC_SUPPORT_VERBS:
            return True
    return False


def _looks_like_meta_sentence(value: str) -> bool:
    normalized = _normalize_text(value)
    return normalized.startswith(_META_SENTENCE_PREFIXES)


def _looks_like_question_or_prompt(value: str) -> bool:
    stripped = value.strip()
    return "?" in stripped or stripped.startswith(("¿", "¿"))


def _looks_like_short_command(
    value: str,
    tokens: list[str],
    *,
    display_form: str,
    lemma: str,
) -> bool:
    stripped = value.strip()
    if len(tokens) <= 4 and stripped.endswith("!"):
        return True

    if len(tokens) <= 5 and tokens:
        targets = _match_keys(display_form) | _match_keys(lemma)
        return tokens[0] in _GENERIC_SUPPORT_VERBS or tokens[0] in targets

    return False


__all__ = ["TextValidationResult", "TextValidationService"]
