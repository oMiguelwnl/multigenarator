"""Domain contracts and issue detection for APKG deck audits."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class AuditIssueType(str, Enum):
    """Normalized deck-audit issue categories."""

    GRAMMAR_METADATA = "grammar_metadata"
    INFLECTION_DESCRIPTION = "inflection_description"
    WRONG_SENSE = "wrong_sense"
    INCOMPLETE_DECK = "incomplete_deck"
    INCOMPLETE_LEVEL = "incomplete_level"
    INVALID_TRANSLATION = "invalid_translation"
    DUPLICATE_FIELD = "duplicate_field"
    MISSING_MEDIA = "missing_media"


@dataclass(frozen=True)
class AuditCard:
    """Stable representation of one audited Anki note/card."""

    note_id: int
    note_guid: str
    model_id: int
    model_name: str
    sort_index: str
    card_identifier: str
    fields: dict[str, str]


@dataclass(frozen=True)
class AuditIssue:
    """Bounded issue evidence for a single audited field."""

    note_id: int
    note_guid: str
    card_identifier: str
    field_name: str
    issue_type: AuditIssueType
    severity: str
    message: str
    evidence: str
    recommended_action: str


_GRAMMAR_METADATA_RE = re.compile(
    r"\b(?:masculine|feminine|neuter|animate|inanimate|accusative|genitive|dative|"
    r"prepositional|instrumental|nominative|singular|plural|short|past|indicative|"
    r"perfective|imperfective)\b",
    re.IGNORECASE,
)
_INFLECTION_RE = re.compile(
    r"\b(?:inflection of|genitive of|accusative of|dative of|prepositional of|"
    r"instrumental of|nominative of)\b",
    re.IGNORECASE,
)
_DOSTICH_WORDS = {"дости́чь", "достичь"}


def detect_card_issues(card: AuditCard) -> list[AuditIssue]:
    """Return normalized Definition issues found in an audited card."""

    field_name, definition = _definition_field(card)
    if field_name is None:
        return []

    issues: list[AuditIssue] = []
    normalized_definition = _normalize(definition)
    if _INFLECTION_RE.search(normalized_definition):
        issues.append(
            _issue(
                card,
                field_name=field_name,
                issue_type=AuditIssueType.INFLECTION_DESCRIPTION,
                message="Definition describes an inflection instead of the word's semantic meaning.",
                evidence=definition,
                recommended_action="Replace the Definition with the semantic meaning for this word form.",
            )
        )
    elif _looks_like_grammar_metadata_only(normalized_definition):
        issues.append(
            _issue(
                card,
                field_name=field_name,
                issue_type=AuditIssueType.GRAMMAR_METADATA,
                message="Definition appears to contain grammar metadata instead of semantic meaning.",
                evidence=definition,
                recommended_action="Rewrite the Definition as a clear English semantic meaning.",
            )
        )

    if _is_dostich_wrong_sense(card, normalized_definition):
        issues.append(
            _issue(
                card,
                field_name=field_name,
                issue_type=AuditIssueType.WRONG_SENSE,
                message="Known wrong sense for дости́чь; expected meaning: to achieve, to attain, to reach.",
                evidence=definition,
                recommended_action="Replace the Definition with: verb: to achieve, to attain, to reach.",
            )
        )

    return issues


def audit_deck_package(read_result: object) -> list[AuditIssue]:
    """Return package-level and per-card blocking audit issues."""

    cards = list(getattr(read_result, "cards", []))
    issues = [issue for card in cards for issue in detect_card_issues(card)]
    issues.extend(_detect_incomplete_frequency_deck(cards))
    issues.extend(_detect_invalid_translations(cards))
    issues.extend(_detect_duplicate_fields(cards))
    issues.extend(_detect_missing_media(read_result))
    return issues


def _detect_incomplete_frequency_deck(cards: list[AuditCard]) -> list[AuditIssue]:
    if not _looks_like_frequency_deck(cards):
        return []
    issues: list[AuditIssue] = []
    if len(cards) != 3000:
        issues.append(
            _package_issue(
                cards,
                issue_type=AuditIssueType.INCOMPLETE_DECK,
                message=f"Frequency deck has {len(cards)}/3000 cards.",
                evidence=str(len(cards)),
                recommended_action="Regenerate or repair the job before treating this APKG as final.",
            )
        )
    level_counts = {1: 0, 2: 0, 3: 0}
    for card in cards:
        level = _level_for_card(card)
        if level in level_counts:
            level_counts[level] += 1
    for level, count in level_counts.items():
        if count != 1000:
            issues.append(
                _package_issue(
                    cards,
                    issue_type=AuditIssueType.INCOMPLETE_LEVEL,
                    message=f"level_{level} has {count}/1000 cards.",
                    evidence=f"level_{level}={count}",
                    recommended_action="Export only complete 1000-card frequency levels or use an explicit partial workflow.",
                )
            )
    return issues


def _detect_invalid_translations(cards: list[AuditCard]) -> list[AuditIssue]:
    from multilang.services.text_validation import looks_like_invalid_translation

    issues: list[AuditIssue] = []
    for card in cards:
        translation = card.fields.get("Translation", "")
        if looks_like_invalid_translation(translation):
            issues.append(
                _issue(
                    card,
                    field_name="Translation",
                    issue_type=AuditIssueType.INVALID_TRANSLATION,
                    message="Translation appears to be a provider/server/quota/captcha/HTML error page.",
                    evidence=translation,
                    recommended_action="Regenerate the translation with a healthy provider before export.",
                )
            )
    return issues


def _detect_duplicate_fields(cards: list[AuditCard]) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    for field_name in ("word", "Word", "Example Sentence", "Translation"):
        seen: dict[str, AuditCard] = {}
        for card in cards:
            raw = card.fields.get(field_name, "")
            normalized = _normalize(raw)
            if not normalized:
                continue
            first = seen.get(normalized)
            if first is None:
                seen[normalized] = card
                continue
            issues.append(
                _issue(
                    card,
                    field_name=field_name,
                    issue_type=AuditIssueType.DUPLICATE_FIELD,
                    message=f"Duplicate {field_name} value also appears on {first.card_identifier}.",
                    evidence=raw,
                    recommended_action="Remove or repair duplicate exported note content.",
                )
            )
    return issues


def _detect_missing_media(read_result: object) -> list[AuditIssue]:
    cards = list(getattr(read_result, "cards", []))
    media_files = set(getattr(read_result, "media_files", set()))
    issues: list[AuditIssue] = []
    for card in cards:
        for field_name in ("word_audio", "sentence_audio"):
            value = card.fields.get(field_name, "")
            for match in re.finditer(r"\[sound:([^\]]+)\]", value):
                media_name = match.group(1)
                if media_name not in media_files:
                    issues.append(
                        _issue(
                            card,
                            field_name=field_name,
                            issue_type=AuditIssueType.MISSING_MEDIA,
                            message=f"Sound reference {media_name} is missing from the APKG media manifest.",
                            evidence=media_name,
                            recommended_action="Regenerate the APKG with all referenced audio files included.",
                        )
                    )
    return issues


def _definition_field(card: AuditCard) -> tuple[str | None, str]:
    for field_name in ("Definitions", "Definition"):
        value = card.fields.get(field_name)
        if value is not None:
            return field_name, value
    return None, ""


def _looks_like_grammar_metadata_only(definition: str) -> bool:
    if not _GRAMMAR_METADATA_RE.search(definition):
        return False
    semantic_markers = (" to ", ";", "meaning", " a ", " an ", " the ")
    return not any(marker in f" {definition} " for marker in semantic_markers)


def _is_dostich_wrong_sense(card: AuditCard, definition: str) -> bool:
    word = _normalize(card.fields.get("word", card.fields.get("Word", ""))).strip()
    return word in _DOSTICH_WORDS and ("to amount to" in definition or "to come to" in definition)


def _issue(
    card: AuditCard,
    *,
    field_name: str,
    issue_type: AuditIssueType,
    message: str,
    evidence: str,
    recommended_action: str,
) -> AuditIssue:
    return AuditIssue(
        note_id=card.note_id,
        note_guid=card.note_guid,
        card_identifier=card.card_identifier,
        field_name=field_name,
        issue_type=issue_type,
        severity="error",
        message=message,
        evidence=_bounded(evidence),
        recommended_action=recommended_action,
    )


def _package_issue(
    cards: list[AuditCard],
    *,
    issue_type: AuditIssueType,
    message: str,
    evidence: str,
    recommended_action: str,
) -> AuditIssue:
    card = cards[0] if cards else AuditCard(0, "package", 0, "", "", "package", {})
    return AuditIssue(
        note_id=card.note_id,
        note_guid=card.note_guid,
        card_identifier="package",
        field_name="__package__",
        issue_type=issue_type,
        severity="error",
        message=message,
        evidence=_bounded(evidence),
        recommended_action=recommended_action,
    )


def _looks_like_frequency_deck(cards: list[AuditCard]) -> bool:
    if not cards:
        return False
    return all("SortIndex" in card.fields for card in cards) and any(
        {"word", "Definitions", "Translation", "word_audio", "sentence_audio"}.issubset(card.fields)
        for card in cards
    )


def _level_for_card(card: AuditCard) -> int | None:
    try:
        sort_index = int(str(card.sort_index or "0"))
    except ValueError:
        return None
    if 1 <= sort_index <= 3000:
        return ((sort_index - 1) // 1000) + 1
    return None


def _bounded(value: str, *, limit: int = 160) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}…"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


__all__ = ["AuditCard", "AuditIssue", "AuditIssueType", "audit_deck_package", "detect_card_issues"]
