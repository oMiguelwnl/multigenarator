"""Provider-backed sentence generation and translation adapters."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from multilang.security.redaction import redact_exception, redact_sensitive_text
from multilang.services.text_generation import (
    DefinitionGenerationRequest,
    DefinitionGenerationResult,
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceTranslationRequest,
    SentenceTranslationResult,
)
from multilang.settings import Settings


CompletionFunc = Callable[..., Any]
TranslatorFactory = Callable[[str], Any]
GoogleTranslatorFactory = Callable[..., Any]

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
}

_DEEPL_TARGET_LANGUAGES = {
    "pt": "PT-BR",
    "es": "ES",
    "en": "EN-US",
    "fr": "FR",
    "de": "DE",
    "it": "IT",
    "pl": "PL",
    "tr": "TR",
    "ro": "RO",
    "ru": "RU",
    "nl": "NL",
}

_SYSTEM_PROMPT = """You create one natural learner example sentence for an Anki vocabulary card.
Return only a JSON object with keys: sentence, intended_sense, uncertainty_notes."""

_DEFINITION_SYSTEM_PROMPT = """You create concise learner dictionary definitions for Anki vocabulary cards.
Return only a JSON object with key: definitions_html."""


class LiteLLMSentenceAdapter:
    """Generate natural example sentences and learner definitions through LiteLLM."""

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

    @property
    def provider(self) -> str:
        return "litellm"

    @property
    def model(self) -> str:
        return self._model

    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        response = self._completion(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _sentence_prompt(request)},
            ],
            temperature=0.35,
            response_format={"type": "json_object"},
            **({"api_key": self._api_key} if self._api_key else {}),
        )
        payload = _json_payload_from_response(response)
        sentence = str(payload.get("sentence") or "").strip()
        if not sentence:
            raise ValueError("LiteLLM sentence response did not include a sentence")

        return SentenceGenerationResult(
            sentence=sentence,
            intended_sense=_optional_string(payload.get("intended_sense")),
            uncertainty_notes=_string_list(payload.get("uncertainty_notes")),
            provenance={
                "source": "provider-text-generator",
                "provider": "litellm",
                "model": self._model,
                **_usage_metadata(response),
                **({"source_type": request.source_type} if request.source_type else {}),
            },
        )

    def generate_definition(self, request: DefinitionGenerationRequest) -> DefinitionGenerationResult:
        response = self._completion(
            model=self._model,
            messages=[
                {"role": "system", "content": _DEFINITION_SYSTEM_PROMPT},
                {"role": "user", "content": _definition_prompt(request)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            **({"api_key": self._api_key} if self._api_key else {}),
        )
        payload = _json_payload_from_response(response)
        definitions_html = str(payload.get("definitions_html") or "").strip()
        if not definitions_html:
            raise ValueError("LiteLLM definition response did not include definitions_html")

        return DefinitionGenerationResult(
            definitions_html=definitions_html,
            provenance={
                "source": "provider-definition-generator",
                "provider": "litellm",
                "model": self._model,
                **_usage_metadata(response),
            },
        )


class DeepLTranslationAdapter:
    """Translate generated sentences through DeepL."""

    def __init__(
        self,
        settings: Settings,
        *,
        translator_factory: TranslatorFactory | None = None,
    ) -> None:
        if not settings.deepl_api_key:
            raise ValueError("DeepL translation requires a DeepL API key")
        self._translator = (translator_factory or _deepl_translator)(settings.deepl_api_key)

    @property
    def provider(self) -> str:
        return "deepl"

    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        target_lang = _DEEPL_TARGET_LANGUAGES.get(request.translation_target_language)
        if target_lang is None:
            raise ValueError(f"unsupported DeepL target language: {request.translation_target_language}")

        result = self._translator.translate_text(request.sentence, target_lang=target_lang)
        translation = str(getattr(result, "text", result)).strip()
        if not translation:
            raise ValueError("DeepL translation response did not include text")

        return SentenceTranslationResult(
            translation=translation,
            provenance={
                "source": "provider-translator",
                "provider": "deepl",
                "target_lang": target_lang,
            },
        )


class GoogleTranslateAdapter:
    """Translate generated sentences through Google Translate via deep-translator."""

    def __init__(self, *, translator_factory: GoogleTranslatorFactory | None = None) -> None:
        self._translator_factory = translator_factory or _google_translator

    @property
    def provider(self) -> str:
        return "google_translate"

    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        translator = self._translator_factory(source="auto", target=request.translation_target_language)
        translation = str(translator.translate(request.sentence)).strip()
        if not translation:
            raise ValueError("Google Translate response did not include text")

        return SentenceTranslationResult(
            translation=translation,
            provenance={
                "source": "provider-translator",
                "provider": "google_translate",
                "target_lang": request.translation_target_language,
            },
        )


class FallbackTranslationAdapter:
    """Try the primary provider, then use a configured fallback translator."""

    def __init__(
        self,
        *,
        primary: Any,
        fallback: Any,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        try:
            return self._primary.translate_sentence(request)
        except Exception as exc:
            result = self._fallback.translate_sentence(request)
            provenance = dict(result.provenance)
            provenance["fallback_from"] = type(self._primary).__name__
            provenance["fallback_reason"] = redact_exception(exc)
            return result.model_copy(update={"provenance": provenance})


def can_use_litellm(settings: Settings) -> bool:
    return settings.text_generation_provider == "litellm" and bool(_litellm_api_key(settings))


def can_use_deepl(settings: Settings) -> bool:
    return settings.translation_provider == "deepl" and bool(settings.deepl_api_key)


def can_use_google_translate(settings: Settings) -> bool:
    return settings.translation_provider == "google"


def _sentence_prompt(request: SentenceGenerationRequest) -> str:
    target_name = _LANGUAGE_NAMES.get(request.target_language, request.target_language)
    definition = _clean_definition(request.definitions_html) or "No definition provided."
    if request.source_type == "kindle-highlights":
        context = redact_sensitive_text(request.highlight_context or "").strip()
        lines = [
            f"Target language: {target_name} ({request.target_language})",
            f"Card word/lemma: {request.lemma}",
            f"Study form: {request.display_form}",
            f"Lemma: {request.lemma}",
            f"Definition context: {definition}",
        ]
        if context:
            lines.append(f"Highlight context hint (redacted, for sense guidance only): {context}")
        lines.extend(
            [
                "Rules:",
                "- Write exactly one natural learner sentence in the target language.",
                "- Base the sentence on the card word/lemma; use the source study form only if it is the same normal word form.",
                "- Include the card word exactly when natural; otherwise use a normal inflection of the lemma.",
                "- Do not copy title-cased list input into the middle of the sentence; lowercase ordinary words unless the language normally capitalizes them.",
                "- Keep the sentence between 6 and 16 words.",
                "- Use the highlight context only to choose the sense; do not copy private text wholesale.",
                "- Do not write a dictionary definition, translation, grammar note, or meta sentence.",
                "- Do not use generic discussion templates, placeholder text, or phrases like 'the word'.",
                "- Set uncertainty_notes to an empty array unless there is a real ambiguity.",
            ]
        )
        return "\n".join(lines)
    return "\n".join(
        [
            f"Target language: {target_name} ({request.target_language})",
            f"Card word/lemma: {request.lemma}",
            f"Study form: {request.display_form}",
            f"Lemma: {request.lemma}",
            f"Definition context: {definition}",
            "Rules:",
            "- Write exactly one everyday sentence in the target language.",
            "- Base the sentence on the card word/lemma; use the source study form only if it is the same normal word form.",
            "- Include the card word exactly when natural; otherwise use a normal inflected form of the lemma.",
            "- Do not copy title-cased list input into the middle of the sentence; lowercase ordinary words unless the language normally capitalizes them.",
            "- Keep the sentence between 4 and 12 words.",
            "- Do not write a dictionary definition, translation, grammar note, or meta sentence.",
            "- Do not use generic discussion templates, placeholder text, or phrases like 'the word'.",
            "- Set uncertainty_notes to an empty array unless there is a real ambiguity.",
        ]
    )


def _definition_prompt(request: DefinitionGenerationRequest) -> str:
    source_name = _LANGUAGE_NAMES.get(request.source_language, request.source_language)
    target_name = _LANGUAGE_NAMES.get(request.target_language, request.target_language)
    lines = [
        f"Source word language: {source_name} ({request.source_language})",
        f"Definition output language: {target_name} ({request.target_language})",
        f"Study form: {request.display_form}",
        f"Lemma: {request.lemma}",
    ]
    if request.part_of_speech:
        lines.append(f"Part of speech: {request.part_of_speech}")
    lines.extend(
        [
            "Rules:",
            "- Define the Study form as a word or expression in the source word language, not as an English spelling, letter, acronym, or unrelated homograph.",
            "- Generate the definition from your language knowledge, not from a supplied cache definition.",
            "- Return one concise learner-friendly definition.",
            "- Format definitions_html exactly as '[part of speech]: [meaning]'.",
            "- For short function words such as one-letter prepositions or conjunctions, define their normal source-language meaning.",
            "- Do not return placeholder text such as 'learner definition for ...'.",
            "- Use plain text only; do not include lists, examples, translations, or extra HTML except <br> between multiple senses if necessary.",
        ]
    )
    return "\n".join(lines)


def _clean_definition(value: str | None) -> str:
    if not value:
        return ""
    stripped = _HTML_RE.sub(" ", value)
    return " ".join(stripped.split())


def _litellm_model(settings: Settings) -> str:
    model = settings.text_generation_model.strip()
    if settings.openrouter_api_key and not settings.openai_api_key and not model.startswith("openrouter/"):
        return f"openrouter/{model}"
    return model


def _litellm_api_key(settings: Settings) -> str | None:
    if settings.litellm_api_key:
        return settings.litellm_api_key

    model = settings.text_generation_model.casefold()
    if model.startswith("openrouter/"):
        return settings.openrouter_api_key
    if model.startswith(("openai/", "gpt-")):
        return settings.openai_api_key or settings.openrouter_api_key
    return settings.openrouter_api_key or settings.openai_api_key


def _litellm_completion(**kwargs: Any) -> Any:
    from litellm import completion

    return completion(**kwargs)


def _deepl_translator(api_key: str) -> Any:
    from deepl import Translator

    return Translator(api_key)


def _google_translator(**kwargs: Any) -> Any:
    from deep_translator import GoogleTranslator

    return GoogleTranslator(**kwargs)


def _json_payload_from_response(response: Any) -> dict[str, Any]:
    content = _response_content(response)
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match is None:
            raise ValueError("LiteLLM response was not JSON") from None
        payload = json.loads(match.group(0))

    if not isinstance(payload, dict):
        raise ValueError("LiteLLM response JSON must be an object")
    return payload


def _response_content(response: Any) -> str:
    choices = _get(response, "choices")
    if not choices:
        raise ValueError("LiteLLM response did not include choices")

    choice = choices[0]
    message = _get(choice, "message")
    content = _get(message, "content") if message is not None else None
    if isinstance(content, list):
        content = "".join(str(_get(part, "text") or "") for part in content)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LiteLLM response did not include message content")
    return _strip_code_fence(content.strip())


def _strip_code_fence(content: str) -> str:
    if not content.startswith("```"):
        return content
    lines = content.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return content


def _get(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _usage_metadata(response: Any) -> dict[str, int]:
    usage = _get(response, "usage") or {}
    input_tokens = _get(usage, "prompt_tokens") or _get(usage, "input_tokens")
    output_tokens = _get(usage, "completion_tokens") or _get(usage, "output_tokens")
    total_tokens = _get(usage, "total_tokens")
    result: dict[str, int] = {}
    if input_tokens is not None:
        result["input_tokens"] = int(input_tokens)
    if output_tokens is not None:
        result["output_tokens"] = int(output_tokens)
    if total_tokens is not None:
        result["total_tokens"] = int(total_tokens)
    elif input_tokens is not None or output_tokens is not None:
        result["total_tokens"] = int(input_tokens or 0) + int(output_tokens or 0)
    return result


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item).strip())]


__all__ = [
    "DeepLTranslationAdapter",
    "FallbackTranslationAdapter",
    "GoogleTranslateAdapter",
    "LiteLLMSentenceAdapter",
    "can_use_deepl",
    "can_use_google_translate",
    "can_use_litellm",
]
