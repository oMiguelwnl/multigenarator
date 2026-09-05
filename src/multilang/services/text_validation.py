"""Deterministic validation and confidence scoring for generated text."""

from __future__ import annotations

import re
from dataclasses import dataclass
import unicodedata

from pydantic import BaseModel, Field

from multilang.domain.korean import (
    KOREAN_LANGUAGE_CODE,
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanMatchResult,
    KoreanMatchStatus,
    KoreanTextError,
    canonicalize_korean,
)
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.language_identifier import CorpusLanguageIdentifier, LanguageIdentifier
from multilang.services.korean_frequency import project_korean_match_status
from multilang.services.mandarin_orthography import (
    MandarinOrthographyError,
    script_counts,
    validate_simplified_mandarin,
)
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.morphology import MorphologicalAnalyzer, OptionalStanzaMorphologicalAnalyzer
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
_RAW_HTML_RE = re.compile(r"<\s*/?\s*(?:!doctype|html|head|body|title|script|style|div|span|p|br|h[1-6])\b|&lt;\s*html\b", re.IGNORECASE)
_INVALID_TRANSLATION_PATTERNS = (
    re.compile(r"\berror\s*500\b", re.IGNORECASE),
    re.compile(r"\bserver\s+error\b", re.IGNORECASE),
    re.compile(r"that's\s+an\s+error", re.IGNORECASE),
    re.compile(r"there\s+was\s+an\s+error", re.IGNORECASE),
    re.compile(r"quota\s+(?:exceeded|for this billing period)", re.IGNORECASE),
    re.compile(r"captcha|recaptcha", re.IGNORECASE),
    re.compile(r"request\s+(?:blocked|forbidden|denied)", re.IGNORECASE),
    re.compile(r"temporarily\s+blocked", re.IGNORECASE),
)
# Deterministic fallback used ONLY when the morphological analyzer is
# unavailable/unreliable (Stanza is an optional, usually-absent dependency, so
# in practice this heuristic decides target-form presence for most runs).
# It is a precision/recall trade-off: recursive single-character suffix stripping
# is what lets plural/inflected forms match the lemma (e.g. "gatos" -> "gato"),
# but it can also over-generate short shared stems and produce false matches
# between unrelated words (e.g. "casa" vs "caso" both reduce to "cas"). Retuning
# this list changes both error classes and should be validated against a labelled
# multilingual set rather than adjusted ad hoc.
_MATCHABLE_SUFFIXES = (
    "ami",
    "ach",
    "ego",
    "emu",
    "owi",
    "ami",
    "ого",
    "ему",
    "ами",
    "ях",
    "ους",
    "εις",
    "ων",
    "ος",
    "ου",
    "ες",
    "ης",
    "ας",
    "ει",
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
    "u",
    "y",
    "ą",
    "ę",
    "и",
    "ы",
    "а",
    "я",
    "е",
    "у",
    "ю",
    "ом",
    "ой",
    "ам",
    "ах",
)

_LANGUAGE_SCRIPTS = {
    "el": "GREEK",
    "ru": "CYRILLIC",
}
_LANGUAGE_MARKERS = {
    "en": {"the", "and", "is", "are", "to", "of", "in", "for", "with", "he", "she", "they"},
    "pt": {"o", "a", "os", "as", "de", "do", "da", "na", "no", "que", "e", "em", "esta", "para", "com", "eu", "ele", "ela"},
    "es": {"el", "la", "los", "las", "de", "que", "y", "en", "para", "con", "yo", "él", "ella"},
    "fr": {"le", "la", "les", "de", "des", "du", "et", "est", "dans", "pour", "avec", "je", "il", "elle"},
    "de": {"der", "die", "das", "und", "ist", "im", "in", "für", "mit", "ich", "er", "sie"},
    "el": {"από", "για", "δεν", "είμαι", "είναι", "εγώ", "η", "και", "με", "να", "ο", "που", "σε", "το", "του"},
    "it": {"il", "la", "lo", "gli", "di", "che", "e", "in", "per", "con", "io", "lui", "lei"},
    "pl": {"i", "w", "na", "do", "że", "to", "jest", "się", "nie", "z", "po", "dla"},
    "sv": {"att", "av", "det", "en", "ett", "för", "han", "hon", "i", "jag", "med", "och", "på", "som", "är"},
    "fi": {"että", "ei", "hän", "ja", "kun", "minä", "on", "se", "tämä", "yksi"},
    "hu": {"a", "az", "egy", "én", "és", "ez", "hogy", "is", "mert", "nem", "ő", "van"},
    "cs": {"a", "ale", "do", "já", "je", "jsem", "na", "ne", "ona", "on", "pro", "se", "to", "v", "že"},
    "hr": {"da", "i", "je", "ja", "mi", "na", "ne", "on", "ona", "sam", "se", "to", "u", "za"},
    "ja": {"の", "に", "は", "が", "を", "で", "と", "も", "から", "です", "ます", "する", "いる"},
    "tr": {"ve", "bir", "bu", "için", "ile", "de", "da", "ben", "o", "çok"},
    "ro": {"și", "de", "la", "în", "este", "pentru", "cu", "eu", "el", "ea"},
    "nl": {"de", "het", "een", "en", "is", "in", "voor", "met", "ik", "hij", "zij"},
    "da": {"det", "en", "er", "et", "for", "han", "hun", "i", "jeg", "med", "og", "på", "ikke", "at", "vi", "de", "sig"},
    "nb": {"det", "en", "er", "et", "for", "han", "hun", "i", "jeg", "med", "og", "på"},
}
_FOREIGN_TOKEN_BLOCKLIST = {
    "pl": {"the", "le", "el", "la", "los", "las"},
}


class TextValidationResult(BaseModel):
    validation_status: ValidationStatus
    validation_flags: list[ValidationFlag] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel


@dataclass(slots=True)
class _ValidationContext:
    sentence_text: str
    target_language: str
    translation_text: str
    definition_text: str
    sentence_tokens: list[str]
    uncertainty_notes: list[str]


class TextValidationService:
    """Apply deterministic sentence and translation quality checks."""

    min_sentence_tokens = 4
    max_sentence_tokens = 12

    def __init__(
        self,
        *,
        language_identifier: LanguageIdentifier | None = None,
        morphological_analyzer: MorphologicalAnalyzer | None = None,
        korean_matcher: KiwiKoreanMorphologyService | None = None,
    ) -> None:
        self.language_identifier = language_identifier or CorpusLanguageIdentifier()
        self.morphological_analyzer = morphological_analyzer or OptionalStanzaMorphologicalAnalyzer()
        self.korean_matcher = korean_matcher or KiwiKoreanMorphologyService()

    def validate(
        self,
        *,
        sentence: GeneratedSentence,
        translation: GeneratedTranslation,
        display_form: str,
        lemma: str,
        definitions_html: str | None,
        uncertainty_notes: list[str] | None = None,
        disallowed_sentence_texts: set[str] | None = None,
        require_translation: bool = True,
        min_sentence_tokens: int | None = None,
        max_sentence_tokens: int | None = None,
        korean_identity: KoreanLexicalIdentity | None = None,
    ) -> TextValidationResult:
        context = _ValidationContext(
            sentence_text=sentence.text.strip(),
            target_language=sentence.target_language,
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

        self._check_target_form(
            flags,
            context=context,
            display_form=display_form,
            lemma=lemma,
            korean_identity=korean_identity,
        )
        self._check_sentence_length(
            flags,
            context=context,
            min_sentence_tokens=min_sentence_tokens,
            max_sentence_tokens=max_sentence_tokens,
        )
        self._check_duplicate_sentence(
            flags,
            context=context,
            disallowed_sentence_texts=disallowed_sentence_texts or set(),
        )
        self._check_banned_patterns(
            flags,
            context=context,
            display_form=display_form,
            lemma=lemma,
            definitions_html=definitions_html,
        )
        self._check_language(flags, context=context, translation=translation, require_translation=require_translation)
        if require_translation:
            self._check_translation(flags, context=context, display_form=display_form, lemma=lemma)

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
        korean_identity: KoreanLexicalIdentity | None,
    ) -> None:
        if context.target_language == KOREAN_LANGUAGE_CODE:
            self._check_korean_target(
                flags,
                sentence_text=context.sentence_text,
                korean_identity=korean_identity,
            )
            return
        if context.target_language == "ja" and _japanese_contains_target(
            context.sentence_text,
            display_form=display_form,
            lemma=lemma,
        ):
            return
        if context.target_language == "zh" and _mandarin_contains_target(
            context.sentence_text,
            display_form=display_form,
            lemma=lemma,
        ):
            return

        candidates = _match_keys(display_form) | _match_keys(lemma)
        sentence_terms = {
            key
            for token in context.sentence_tokens
            for key in _match_keys(token)
        }
        heuristic_match = not candidates.isdisjoint(sentence_terms)
        morphology_result = self.morphological_analyzer.contains_target_lemma(
            sentence_text=context.sentence_text,
            target_language=context.target_language,
            display_form=display_form,
            lemma=lemma,
        )
        if morphology_result.reliable:
            if morphology_result.matched:
                return
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.MORPHOLOGY_MISMATCH,
                    detail=f"sentence morphology does not contain the target lemma or study form ({morphology_result.detail})",
                )
            )
            return
        if heuristic_match:
            return
        flags.append(
            ValidationFlag(
                code=ValidationFlagCode.MISSING_TARGET_LEMMA,
                detail="sentence must include the target lemma or required study form",
            )
        )

    def _check_korean_target(
        self,
        flags: list[ValidationFlag],
        *,
        sentence_text: str,
        korean_identity: KoreanLexicalIdentity | None,
    ) -> None:
        if not isinstance(korean_identity, KoreanLexicalIdentity):
            _append_korean_morphology_mismatch(
                flags,
                status="missing" if korean_identity is None else "invalid",
            )
            return

        try:
            KoreanLexicalIdentity.model_validate(
                korean_identity.model_dump(mode="python")
            )
        except (AttributeError, TypeError, ValueError):
            _append_korean_morphology_mismatch(flags, status="invalid")
            return

        try:
            active_fingerprint = self.korean_matcher.fingerprint
            if not isinstance(active_fingerprint, KoreanAnalyzerFingerprint):
                raise TypeError("invalid Korean analyzer fingerprint")
            KoreanAnalyzerFingerprint.model_validate(
                active_fingerprint.model_dump(mode="python")
            )
        except (AttributeError, TypeError, ValueError):
            _append_korean_morphology_mismatch(flags, status="unavailable")
            return

        if korean_identity.analyzer_fingerprint != active_fingerprint:
            _append_korean_morphology_mismatch(
                flags,
                status=KoreanMatchStatus.FINGERPRINT_MISMATCH.value,
            )
            return

        try:
            raw_result = self.korean_matcher.match_target(
                sentence_text,
                korean_identity,
            )
        except Exception:
            _append_korean_morphology_mismatch(flags, status="unavailable")
            return

        if not isinstance(raw_result, KoreanMatchResult):
            _append_korean_morphology_mismatch(flags, status="invalid")
            return
        try:
            result = KoreanMatchResult.model_validate(
                raw_result.model_dump(mode="python")
            )
        except (AttributeError, TypeError, ValueError):
            _append_korean_morphology_mismatch(flags, status="invalid")
            return

        if result.analyzer_fingerprint != active_fingerprint:
            _append_korean_morphology_mismatch(
                flags,
                status=KoreanMatchStatus.FINGERPRINT_MISMATCH.value,
            )
            return
        if result.status is not KoreanMatchStatus.MATCHED:
            _append_korean_morphology_mismatch(
                flags,
                status=result.status.value,
                reason=result.reason_code.value,
            )

    def _check_sentence_length(
        self,
        flags: list[ValidationFlag],
        *,
        context: _ValidationContext,
        min_sentence_tokens: int | None = None,
        max_sentence_tokens: int | None = None,
    ) -> None:
        min_tokens = self.min_sentence_tokens if min_sentence_tokens is None else min_sentence_tokens
        max_tokens = self.max_sentence_tokens if max_sentence_tokens is None else max_sentence_tokens
        if context.target_language == "ja":
            character_count = _japanese_signal_character_count(context.sentence_text)
            if character_count < min_tokens:
                flags.append(
                    ValidationFlag(
                        code=ValidationFlagCode.SENTENCE_TOO_SHORT,
                        detail=f"Japanese sentence has {character_count} signal characters; expected at least {min_tokens}",
                    )
                )
            max_characters = max(max_tokens * 6, 24)
            if character_count > max_characters:
                flags.append(
                    ValidationFlag(
                        code=ValidationFlagCode.SENTENCE_TOO_LONG,
                        detail=f"Japanese sentence has {character_count} signal characters; expected at most {max_characters}",
                    )
                )
            return

        if context.target_language == "zh":
            character_count = script_counts(context.sentence_text).han
            if character_count < min_tokens:
                flags.append(
                    ValidationFlag(
                        code=ValidationFlagCode.SENTENCE_TOO_SHORT,
                        detail=f"Mandarin sentence has {character_count} Han characters; expected at least {min_tokens}",
                    )
                )
            max_characters = max(max_tokens * 6, 24)
            if character_count > max_characters:
                flags.append(
                    ValidationFlag(
                        code=ValidationFlagCode.SENTENCE_TOO_LONG,
                        detail=f"Mandarin sentence has {character_count} Han characters; expected at most {max_characters}",
                    )
                )
            return

        token_count = len(context.sentence_tokens)
        if token_count < min_tokens:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.SENTENCE_TOO_SHORT,
                    detail=f"sentence has {token_count} tokens; expected at least {min_tokens}",
                )
            )
        if token_count > max_tokens:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.SENTENCE_TOO_LONG,
                    detail=f"sentence has {token_count} tokens; expected at most {max_tokens}",
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
            target_language=context.target_language,
            display_form=display_form,
            lemma=lemma,
            definitions_html=definitions_html,
        ) or _has_unexpected_target_capitalization(
            context.sentence_text,
            target_language=context.target_language,
            display_form=display_form,
            lemma=lemma,
        ):
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.BANNED_PATTERN,
                    detail="sentence contains placeholder, robotic, or overly repetitive text",
                )
            )

    def _check_duplicate_sentence(
        self,
        flags: list[ValidationFlag],
        *,
        context: _ValidationContext,
        disallowed_sentence_texts: set[str],
    ) -> None:
        normalized_sentence = _normalize_text(context.sentence_text)
        if normalized_sentence and normalized_sentence in disallowed_sentence_texts:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.DUPLICATE_SENTENCE,
                    detail="sentence must be unique across cards in the same deck generation job",
                )
            )

    def _check_translation(
        self,
        flags: list[ValidationFlag],
        *,
        context: _ValidationContext,
        display_form: str,
        lemma: str,
    ) -> None:
        translation_text = _normalize_text(context.translation_text)
        if not translation_text:
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.TRANSLATION_MISMATCH,
                    detail="translation must not be empty",
                )
            )
            return

        if looks_like_invalid_translation(context.translation_text):
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.TRANSLATION_MISMATCH,
                    detail="translation appears to be a provider, quota, captcha, server-error, or HTML error page",
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
            return

        if _looks_like_isolated_word_translation(
            translation_text,
            context=context,
            display_form=display_form,
            lemma=lemma,
        ):
            flags.append(
                ValidationFlag(
                    code=ValidationFlagCode.TRANSLATION_MISMATCH,
                    detail="translation appears to translate only the study word instead of the full sentence",
                )
            )

    def _check_language(
        self,
        flags: list[ValidationFlag],
        *,
        context: _ValidationContext,
        translation: GeneratedTranslation,
        require_translation: bool,
    ) -> None:
        sentence_mismatch = detect_language_mismatch(
            context.sentence_text,
            expected_language=context.target_language,
            strict_foreign_tokens=True,
            language_identifier=self.language_identifier,
        )
        if sentence_mismatch:
            flags.append(ValidationFlag(code=ValidationFlagCode.LANGUAGE_MISMATCH, detail=sentence_mismatch))
        if require_translation and context.translation_text:
            translation_mismatch = detect_language_mismatch(
                context.translation_text,
                expected_language=translation.target_language,
                strict_foreign_tokens=False,
                language_identifier=self.language_identifier,
            )
            if translation_mismatch:
                flags.append(ValidationFlag(code=ValidationFlagCode.LANGUAGE_MISMATCH, detail=translation_mismatch))

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


def looks_like_invalid_translation(value: str) -> bool:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return False
    if _RAW_HTML_RE.search(text):
        return True
    return any(pattern.search(text) for pattern in _INVALID_TRANSLATION_PATTERNS)


_DEFAULT_LANGUAGE_IDENTIFIER = CorpusLanguageIdentifier()


def detect_language_mismatch(
    value: str,
    *,
    expected_language: str,
    strict_foreign_tokens: bool = False,
    language_identifier: LanguageIdentifier | None = None,
) -> str | None:
    expected = expected_language.casefold()
    if expected == KOREAN_LANGUAGE_CODE:
        try:
            canonical_text = canonicalize_korean(value)
        except KoreanTextError:
            return f"text does not look like language {expected_language}: invalid Korean text"
        if canonical_text != value:
            return f"text does not look like language {expected_language}: non-canonical Korean text"
        if _korean_script_ratio(canonical_text) < 0.55:
            return f"text does not look like language {expected_language}"
        return None
    if expected == "zh":
        try:
            validate_simplified_mandarin(value)
        except MandarinOrthographyError as exc:
            return f"text does not look like language {expected_language}: {exc}"
        return None
    tokens = _tokenize(value)
    if not tokens:
        return None
    detection = (language_identifier or _DEFAULT_LANGUAGE_IDENTIFIER).detect(value, expected_language=expected)
    if detection.reliable and detection.detected_language is not None and detection.detected_language != expected:
        return (
            f"text looks like {detection.detected_language}, expected {expected_language} "
            f"({detection.provider} confidence={detection.confidence:.2f}; {detection.detail})"
        )
    script = _LANGUAGE_SCRIPTS.get(expected)
    if expected == "ja":
        if _japanese_script_ratio(value) < 0.55:
            return f"text does not look like language {expected_language}"
        return None
    if script is not None:
        letter_tokens = [token for token in tokens if any(character.isalpha() for character in token)]
        if letter_tokens and _script_token_ratio(letter_tokens, script) < 0.55:
            return f"text does not look like language {expected_language}"
    if strict_foreign_tokens:
        blocked = _FOREIGN_TOKEN_BLOCKLIST.get(expected, set())
        foreign_tokens = sorted({token for token in tokens if token in blocked})
        if foreign_tokens:
            return f"unexpected foreign tokens for {expected_language}: {', '.join(foreign_tokens)}"
    detected = _detect_language_by_markers(tokens)
    if detected is not None and detected != expected:
        expected_hits = len(set(tokens) & _LANGUAGE_MARKERS.get(expected, set()))
        detected_hits = len(set(tokens) & _LANGUAGE_MARKERS.get(detected, set()))
        if detected_hits >= max(2, expected_hits + 2):
            return f"text looks like {detected}, expected {expected_language}"
    return None


def _detect_language_by_markers(tokens: list[str]) -> str | None:
    counts = {language: len(set(tokens) & markers) for language, markers in _LANGUAGE_MARKERS.items()}
    language, count = max(counts.items(), key=lambda item: item[1])
    return language if count >= 2 else None


def _script_token_ratio(tokens: list[str], script_name: str) -> float:
    matching = 0
    checked = 0
    for token in tokens:
        letters = [character for character in token if character.isalpha()]
        if not letters:
            continue
        checked += 1
        if sum(1 for character in letters if script_name in unicodedata.name(character, "")) / len(letters) >= 0.5:
            matching += 1
    return matching / checked if checked else 1.0


def _korean_script_ratio(value: str) -> float:
    letters = [character for character in value if character.isalpha()]
    if not letters:
        return 0.0
    korean = sum(1 for character in letters if _is_modern_hangul(character))
    return korean / len(letters)


def _is_modern_hangul(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x1100 <= codepoint <= 0x11FF
        or 0xA960 <= codepoint <= 0xA97F
        or 0xAC00 <= codepoint <= 0xD7A3
        or 0xD7B0 <= codepoint <= 0xD7FF
    )


def _japanese_contains_target(value: str, *, display_form: str, lemma: str) -> bool:
    normalized_sentence = _normalize_japanese_lookup(value)
    return any(
        target and target in normalized_sentence
        for target in {_normalize_japanese_lookup(display_form), _normalize_japanese_lookup(lemma)}
    )


def _mandarin_contains_target(value: str, *, display_form: str, lemma: str) -> bool:
    normalized_sentence = _normalize_mandarin_lookup(value)
    return any(
        target and target in normalized_sentence
        for target in {_normalize_mandarin_lookup(display_form), _normalize_mandarin_lookup(lemma)}
    )


def _normalize_mandarin_lookup(value: str) -> str:
    return "".join(unicodedata.normalize("NFKC", str(value or "")).casefold().split())


def _normalize_japanese_lookup(value: str) -> str:
    return "".join(str(value or "").casefold().split())


def _japanese_signal_character_count(value: str) -> int:
    return sum(1 for character in value if _is_japanese_character(character) or character.isalpha())


def _japanese_script_ratio(value: str) -> float:
    letters = [character for character in value if character.isalpha()]
    if not letters:
        return 0.0
    japanese = sum(1 for character in letters if _is_japanese_character(character))
    return japanese / len(letters)


def _is_japanese_character(character: str) -> bool:
    try:
        name = unicodedata.name(character)
    except ValueError:
        return False
    return "HIRAGANA" in name or "KATAKANA" in name or "CJK UNIFIED IDEOGRAPH" in name


def _normalize_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(_TOKEN_RE.findall(value.casefold()))


def _looks_like_isolated_word_translation(
    translation_text: str,
    *,
    context: _ValidationContext,
    display_form: str,
    lemma: str,
) -> bool:
    if len(context.sentence_tokens) < 4:
        return False

    translation_tokens = translation_text.split()
    if len(translation_tokens) > 3:
        return False

    if context.target_language == KOREAN_LANGUAGE_CODE:
        target_keys = {
            key
            for key in (_normalize_text(display_form), _normalize_text(lemma))
            if key
        }
    else:
        target_keys = _match_keys(display_form) | _match_keys(lemma)
    if translation_text in target_keys:
        return True

    definition_glosses = _definition_glosses(context.definition_text)
    return translation_text in definition_glosses


def _definition_glosses(definition_text: str) -> set[str]:
    if not definition_text:
        return set()

    definition_tokens = definition_text.split()
    without_label = " ".join(definition_tokens[1:]) if definition_tokens[:1] and definition_tokens[0] in _DEFINITION_LABEL_TOKENS else definition_text
    candidates = {definition_text, without_label}
    for separator in (",", ";", " or "):
        for value in list(candidates):
            candidates.update(part.strip() for part in value.split(separator))
    candidates.update(match.group(0).strip() for match in re.finditer(r"\bto\s+\w+\b", without_label))
    return {candidate for candidate in candidates if candidate}


_DEFINITION_LABEL_TOKENS = {
    "adjective",
    "adverb",
    "article",
    "conjunction",
    "determiner",
    "interjection",
    "noun",
    "numeral",
    "particle",
    "preposition",
    "pronoun",
    "verb",
}


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
    target_language: str,
    display_form: str,
    lemma: str,
    definitions_html: str | None = None,
) -> bool:
    stripped = value.strip()
    if len(tokens) <= 4 and stripped.endswith("!"):
        return True

    if target_language == KOREAN_LANGUAGE_CODE:
        return False

    if len(tokens) <= 5 and tokens:
        targets = _match_keys(display_form) | _match_keys(lemma)
        return tokens[0] in _GENERIC_SUPPORT_VERBS or (tokens[0] in targets and _definition_looks_verbal(definitions_html))

    return False


def _definition_looks_verbal(value: str | None) -> bool:
    normalized = _normalize_text(value or "")
    return normalized.startswith(("to ", "v ", "verb ", "verbo ", "verbe "))


def _has_unexpected_target_capitalization(
    value: str,
    *,
    target_language: str,
    display_form: str,
    lemma: str,
) -> bool:
    if target_language in {"de", KOREAN_LANGUAGE_CODE} or _starts_with_upper(lemma):
        return False

    target_keys = _match_keys(display_form) | _match_keys(lemma)
    first_token_seen = False
    for match in _TOKEN_RE.finditer(value):
        token = match.group(0)
        if not first_token_seen:
            first_token_seen = True
            continue
        if not _starts_with_upper(token):
            continue
        if _match_keys(token).isdisjoint(target_keys):
            continue
        return True
    return False


def _starts_with_upper(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and stripped[0].isalpha() and stripped[0].isupper()


def _append_korean_morphology_mismatch(
    flags: list[ValidationFlag],
    *,
    status: str,
    reason: str | None = None,
) -> None:
    controlled_detail = (
        f"Korean morphology verification failed (status={status}; "
        f"projection={project_korean_match_status(status)}"
    )
    if reason is not None:
        controlled_detail += f"; reason={reason}"
    controlled_detail += ")"
    flags.append(
        ValidationFlag(
            code=ValidationFlagCode.MORPHOLOGY_MISMATCH,
            detail=controlled_detail,
        )
    )


__all__ = ["TextValidationResult", "TextValidationService", "detect_language_mismatch", "looks_like_invalid_translation"]
