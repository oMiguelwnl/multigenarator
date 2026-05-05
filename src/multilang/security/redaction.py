"""Deterministic redaction helpers for private highlight and WebDAV data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import re
from typing import Any

SENSITIVE_VALUE_REDACTION = "[REDACTED]"

_SENSITIVE_KEY_RE = re.compile(r"(?i)(authorization|password|passwd|username|user|secret|token|api[_-]?key)")

_TEXT_PATTERNS = (
    re.compile(r"(?im)(Authorization\s*:\s*)(?:Bearer|Basic)?\s*[^\r\n]+"),
    re.compile(r"(?i)\b(Bearer|Basic)\s+[^\s,;]+"),
    re.compile(r"(?i)\b(password|passwd|username|user|secret|token|api[_-]?key)(\s*[=:]\s*)([^\s,;&]+)"),
    re.compile(r"(?i)https?://[^\s]+/dav[^\s]*"),
    re.compile(r"(?i)(?:^|(?<=\s))\.?/?\.multilang/highlights/raw/[^\s]+"),
    re.compile(r"(?im)\b(Title|Author|Book|Location)(\s*:\s*)([^\r\n]*)"),
)


def redact_sensitive_text(text: str, *, extra_terms: Iterable[str] = ()) -> str:
    """Return *text* with known sensitive shapes replaced by a stable marker."""

    redacted = text
    for term in extra_terms:
        if term:
            redacted = redacted.replace(term, SENSITIVE_VALUE_REDACTION)

    redacted = _TEXT_PATTERNS[0].sub(lambda match: f"{match.group(1)}{SENSITIVE_VALUE_REDACTION}", redacted)
    redacted = _TEXT_PATTERNS[1].sub(lambda match: f"{match.group(1)} {SENSITIVE_VALUE_REDACTION}", redacted)
    redacted = _TEXT_PATTERNS[2].sub(
        lambda match: f"{match.group(1)}{match.group(2)}{SENSITIVE_VALUE_REDACTION}",
        redacted,
    )
    redacted = _TEXT_PATTERNS[3].sub(SENSITIVE_VALUE_REDACTION, redacted)
    redacted = _TEXT_PATTERNS[4].sub(SENSITIVE_VALUE_REDACTION, redacted)
    redacted = _TEXT_PATTERNS[5].sub(
        lambda match: f"{match.group(1)}{match.group(2)}{SENSITIVE_VALUE_REDACTION}",
        redacted,
    )
    return redacted


def redact_mapping(values: Mapping[str, object], *, extra_terms: Iterable[str] = ()) -> dict[str, object]:
    """Redact sensitive keys and nested scalar values while preserving structure."""

    return {
        str(key): _redact_value(key=str(key), value=value, extra_terms=extra_terms)
        for key, value in values.items()
    }


def redact_exception(exc: BaseException, *, extra_terms: Iterable[str] = ()) -> str:
    """Return a redacted exception message without logging side effects."""

    return redact_sensitive_text(str(exc), extra_terms=extra_terms)


def _redact_value(*, key: str, value: object, extra_terms: Iterable[str]) -> object:
    if _SENSITIVE_KEY_RE.search(key):
        return SENSITIVE_VALUE_REDACTION
    if isinstance(value, Mapping):
        return redact_mapping(value, extra_terms=extra_terms)
    if isinstance(value, list):
        return [_redact_value(key="", value=item, extra_terms=extra_terms) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(key="", value=item, extra_terms=extra_terms) for item in value)
    if isinstance(value, str):
        redacted = redact_sensitive_text(value, extra_terms=extra_terms)
        return SENSITIVE_VALUE_REDACTION if _looks_fully_sensitive(value, redacted) else redacted
    return value


def _looks_fully_sensitive(original: str, redacted: str) -> bool:
    return original != redacted and redacted == SENSITIVE_VALUE_REDACTION


__all__ = [
    "SENSITIVE_VALUE_REDACTION",
    "redact_exception",
    "redact_mapping",
    "redact_sensitive_text",
]
