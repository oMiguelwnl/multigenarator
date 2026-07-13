"""Provider-backed pronunciation generation adapters."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from multilang.services.provider_text_adapters import (
    CompletionFunc,
    _json_payload_from_response,
    _litellm_api_key,
    _litellm_completion,
    _litellm_model,
)
from multilang.settings import Settings


_SYSTEM_PROMPT = """You generate pronunciation data for an Anki vocabulary card. Return only JSON with keys: ipa, spoken_form, uncertainty_notes."""
_HTML_RE = re.compile(r"<[^>]+>")
_LANGUAGE_NAMES = {
    "pt": "Portuguese",
    "es": "Spanish",
    "en": "English",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pl": "Polish",
    "tr": "Turkish",
    "ro": "Romanian",
    "ru": "Russian",
    "nl": "Dutch",
    "nb": "Norwegian Bokmal",
    "sv": "Swedish",
    "fi": "Finnish",
}


class PronunciationGenerationRequest(BaseModel):
    target_language: str = Field(min_length=2)
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions_html: str | None = None


class PronunciationGenerationResult(BaseModel):
    ipa: str = Field(min_length=1)
    spoken_form: str = Field(min_length=1)
    uncertainty_notes: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class LiteLLMPronunciationAdapter:
    """Generate IPA and readable spoken forms through LiteLLM."""

    def __init__(
        self,
        settings: Settings,
        *,
        completion_func: CompletionFunc | None = None,
    ) -> None:
        self._settings = settings
        self._model = _litellm_model(settings)
        self._api_key = _litellm_api_key(settings)
        self._completion = completion_func or _litellm_completion

    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> PronunciationGenerationResult:
        response = self._completion(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _pronunciation_prompt(request)},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            **({"api_key": self._api_key} if self._api_key else {}),
        )
        payload = _json_payload_from_response(response)
        ipa = str(payload.get("ipa") or "").strip()
        spoken_form = str(payload.get("spoken_form") or "").strip()
        if not ipa:
            raise ValueError("LiteLLM pronunciation response did not include IPA")
        if not spoken_form:
            raise ValueError("LiteLLM pronunciation response did not include spoken_form")

        return PronunciationGenerationResult(
            ipa=ipa,
            spoken_form=spoken_form,
            uncertainty_notes=_string_list(payload.get("uncertainty_notes")),
            provenance={
                "source": "provider-pronunciation-generator",
                "provider": "litellm",
                "model": self._model,
            },
        )


def _pronunciation_prompt(request: PronunciationGenerationRequest) -> str:
    target_name = _LANGUAGE_NAMES.get(request.target_language, request.target_language)
    definition = _clean_definition(request.definitions_html) or "No definition provided."
    return "\n".join(
        [
            f"Target language: {target_name} ({request.target_language})",
            f"Display form: {request.display_form}",
            f"Lemma: {request.lemma}",
            f"Definitions: {definition}",
            "Generate pronunciation for the Display form exactly; do not switch to the lemma, translation, or a related word.",
            "Return JSON keys ipa, spoken_form, uncertainty_notes.",
            "Use IPA for ipa and a learner-readable pronunciation for spoken_form.",
        ]
    )


def _clean_definition(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(_HTML_RE.sub(" ", value).split())


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item).strip())]


__all__ = [
    "LiteLLMPronunciationAdapter",
    "PronunciationGenerationRequest",
    "PronunciationGenerationResult",
]
