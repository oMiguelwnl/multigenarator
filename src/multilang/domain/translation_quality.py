"""Translation error-page rules and strict advisory fidelity contracts."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TranslationFidelityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    sentence: str = Field(min_length=1, max_length=4000)
    translation: str = Field(min_length=1, max_length=4000)
    source_language: str = Field(min_length=2, max_length=16)
    target_language: str = Field(min_length=2, max_length=16)


class TranslationFidelityVerdict(BaseModel):
    """Machine assessment of one exact pair; never human review authority."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    decision: Literal["equivalent", "mismatch", "uncertain"]

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


def looks_like_invalid_translation(value: str) -> bool:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return False
    if _RAW_HTML_RE.search(text):
        return True
    return any(pattern.search(text) for pattern in _INVALID_TRANSLATION_PATTERNS)



__all__ = ["TranslationFidelityRequest", "TranslationFidelityVerdict", "looks_like_invalid_translation"]
