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


def _bounded(value: str, *, limit: int = 160) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}…"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


__all__ = ["AuditCard", "AuditIssue", "AuditIssueType", "detect_card_issues"]
