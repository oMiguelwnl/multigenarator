"""Normalized v1.3 validation facade for card-quality evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
import unicodedata

from multilang.domain.audio import AudioAssetRecord
from multilang.domain.exporting import ExportCardRow
from multilang.domain.text_quality import ValidationFlagCode
from multilang.services.audio_integrity import AudioIntegrityError, assert_word_audio_matches_word
from multilang.services.card_template_loader import CardTemplate, validate_template_references
from multilang.services.text_field_remediation import validate_definition_html
from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation
from multilang.services.text_validation import TextValidationService


class V13ValidationIssueType(StrEnum):
    """Stable issue taxonomy for v1.3 validation fixtures and evidence."""

    IPA_WORD_REPETITION = "ipa_word_repetition"
    DEFINITION_BANNED_PATTERN = "definition_banned_pattern"
    TRANSLATION_EXAMPLE_MISMATCH = "translation_example_mismatch"
    WORD_AUDIO_WORD_MISMATCH = "word_audio_word_mismatch"
    DANGLING_TEMPLATE_FIELD = "dangling_template_field"
    SENTENCE_AUDIO_LAYOUT = "sentence_audio_layout"


@dataclass(frozen=True, slots=True)
class V13ValidationIssue:
    """Bounded, field-specific validation issue safe for evidence artifacts."""

    field_name: str
    issue_type: V13ValidationIssueType
    severity: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", _bounded_message(self.message))


def validate_v13_card(
    row: ExportCardRow,
    *,
    word_audio_asset: AudioAssetRecord | None = None,
) -> list[V13ValidationIssue]:
    """Validate a normal v1.3 export row against normalized issue categories."""

    issues: list[V13ValidationIssue] = []
    if _ipa_repeats_word(row.ipa, row.word):
        issues.append(
            _issue(
                field_name="IPA",
                issue_type=V13ValidationIssueType.IPA_WORD_REPETITION,
                message="IPA includes a repeated word form beside the phonetic transcription.",
            )
        )

    try:
        validate_definition_html(lemma_key=row.identity.lemma_key, definitions_html=row.definitions)
    except ValueError:
        issues.append(
            _issue(
                field_name="Definitions",
                issue_type=V13ValidationIssueType.DEFINITION_BANNED_PATTERN,
                message="Definitions must describe semantic meaning, not morphology metadata.",
            )
        )

    text_result = TextValidationService().validate(
        sentence=GeneratedSentence(
            text=row.example_sentence,
            target_language=row.identity.language.value,
            intended_sense=None,
            uncertainty_notes=[],
            provenance={"source": "v13_validation"},
        ),
        translation=GeneratedTranslation(
            text=row.translation or " ",
            target_language="en",
            provenance={"source": "v13_validation"},
        ),
        display_form=row.word,
        lemma=row.word,
        definitions_html=row.definitions,
        require_translation=True,
    )
    if ValidationFlagCode.TRANSLATION_MISMATCH in {flag.code for flag in text_result.validation_flags}:
        issues.append(
            _issue(
                field_name="Translation",
                issue_type=V13ValidationIssueType.TRANSLATION_EXAMPLE_MISMATCH,
                message="Translation must correspond to the full example sentence.",
            )
        )

    if word_audio_asset is not None and row.word_audio.strip():
        try:
            assert_word_audio_matches_word(word_audio_asset, row.word, item_key=row.identity.item_key)
        except AudioIntegrityError:
            issues.append(
                _issue(
                    field_name="word_audio",
                    issue_type=V13ValidationIssueType.WORD_AUDIO_WORD_MISMATCH,
                    message="word_audio metadata must exactly match the exported Word field.",
                )
            )

    return issues


def validate_v13_template_contract(
    template: CardTemplate,
    field_names: tuple[str, ...],
) -> list[V13ValidationIssue]:
    """Validate template references and normalize dangling-field failures."""

    try:
        validate_template_references(template, field_names=field_names)
    except ValueError:
        return [
            _issue(
                field_name="template",
                issue_type=V13ValidationIssueType.DANGLING_TEMPLATE_FIELD,
                message="Card template references fields outside the active export contract.",
            )
        ]
    template_markup = template.front + template.back
    if re.search(r"{{\s*sentence_audio\s*}}", template_markup):
        template_surface = " ".join((template.front, template.back, template.css))
        required_selectors = {"exampleSentenceLine", "exampleSentenceText", "sentenceAudioButton"}
        if not required_selectors <= set(re.findall(r"[A-Za-z][A-Za-z0-9_-]+", template_surface)):
            return [
                _issue(
                    field_name="template",
                    issue_type=V13ValidationIssueType.SENTENCE_AUDIO_LAYOUT,
                    message="sentence_audio must stay beside Example Sentence using the normal responsive layout selectors.",
                )
            ]
    return []


def _issue(*, field_name: str, issue_type: V13ValidationIssueType, message: str) -> V13ValidationIssue:
    return V13ValidationIssue(field_name=field_name, issue_type=issue_type, severity="error", message=message)


def _ipa_repeats_word(ipa: str | None, word: str) -> bool:
    if not ipa or not word.strip():
        return False
    normalized_ipa = _normalize_for_match(ipa)
    normalized_word = _normalize_for_match(word)
    if not normalized_ipa or normalized_ipa == normalized_word:
        return False

    parenthetical_values = re.findall(r"[\[(]([^\])]+)[\])]", ipa)
    if any(_normalize_for_match(value) == normalized_word for value in parenthetical_values):
        return True

    without_phonetic_groups = re.sub(r"[\[(][^\])]+[\])]", " ", ipa)
    return any(_normalize_for_match(token) == normalized_word for token in _word_tokens(without_phonetic_groups))


def _word_tokens(value: str) -> list[str]:
    return re.findall(r"[\w\u0300-\u036f]+", value, flags=re.UNICODE)


def _normalize_for_match(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return " ".join(_word_tokens(without_marks))


def _bounded_message(message: str) -> str:
    cleaned = " ".join(message.split())
    return cleaned[:180]


__all__ = [
    "V13ValidationIssue",
    "V13ValidationIssueType",
    "validate_v13_card",
    "validate_v13_template_contract",
]
