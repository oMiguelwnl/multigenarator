"""Deterministic Azure voice registry for supported deck languages."""

from __future__ import annotations

from pydantic import BaseModel, Field

from multilang.domain.jobs import SupportedLanguage

VOICE_REGISTRY_VERSION = "2026-04-24"


class VoiceSelectionError(ValueError):
    """Raised when no approved voice is available for a language."""


class VoiceOption(BaseModel):
    voice_id: str = Field(min_length=1)
    locale: str = Field(min_length=1)


class VoicePlan(BaseModel):
    preferred: VoiceOption
    same_locale_alternates: tuple[VoiceOption, ...] = ()
    alternate_locale_alternates: tuple[VoiceOption, ...] = ()

    def ordered_candidates(self) -> tuple[VoiceOption, ...]:
        return (
            self.preferred,
            *self.same_locale_alternates,
            *self.alternate_locale_alternates,
        )


class VoiceSelection(BaseModel):
    language: SupportedLanguage
    voice_id: str = Field(min_length=1)
    locale: str = Field(min_length=1)
    registry_version: str = Field(min_length=1)
    fallback_used: bool = False


_VOICE_REGISTRY: dict[SupportedLanguage, VoicePlan] = {
    SupportedLanguage.PT: VoicePlan(
        preferred=VoiceOption(voice_id="pt-BR-FranciscaNeural", locale="pt-BR"),
        same_locale_alternates=(VoiceOption(voice_id="pt-BR-AntonioNeural", locale="pt-BR"),),
        alternate_locale_alternates=(VoiceOption(voice_id="pt-PT-RaquelNeural", locale="pt-PT"),),
    ),
    SupportedLanguage.ES: VoicePlan(
        preferred=VoiceOption(voice_id="es-ES-ElviraNeural", locale="es-ES"),
        same_locale_alternates=(VoiceOption(voice_id="es-ES-AlvaroNeural", locale="es-ES"),),
        alternate_locale_alternates=(VoiceOption(voice_id="es-MX-DaliaNeural", locale="es-MX"),),
    ),
    SupportedLanguage.EN: VoicePlan(
        preferred=VoiceOption(voice_id="en-US-JennyNeural", locale="en-US"),
        same_locale_alternates=(VoiceOption(voice_id="en-US-GuyNeural", locale="en-US"),),
        alternate_locale_alternates=(VoiceOption(voice_id="en-GB-SoniaNeural", locale="en-GB"),),
    ),
    SupportedLanguage.FR: VoicePlan(
        preferred=VoiceOption(voice_id="fr-FR-DeniseNeural", locale="fr-FR"),
        same_locale_alternates=(VoiceOption(voice_id="fr-FR-HenriNeural", locale="fr-FR"),),
        alternate_locale_alternates=(VoiceOption(voice_id="fr-CA-SylvieNeural", locale="fr-CA"),),
    ),
    SupportedLanguage.DE: VoicePlan(
        preferred=VoiceOption(voice_id="de-DE-KatjaNeural", locale="de-DE"),
        same_locale_alternates=(VoiceOption(voice_id="de-DE-ConradNeural", locale="de-DE"),),
        alternate_locale_alternates=(VoiceOption(voice_id="de-AT-IngridNeural", locale="de-AT"),),
    ),
    SupportedLanguage.RU: VoicePlan(
        preferred=VoiceOption(voice_id="ru-RU-SvetlanaNeural", locale="ru-RU"),
        same_locale_alternates=(VoiceOption(voice_id="ru-RU-DmitryNeural", locale="ru-RU"),),
    ),
    SupportedLanguage.NL: VoicePlan(
        preferred=VoiceOption(voice_id="nl-NL-ColetteNeural", locale="nl-NL"),
        same_locale_alternates=(VoiceOption(voice_id="nl-NL-MaartenNeural", locale="nl-NL"),),
        alternate_locale_alternates=(VoiceOption(voice_id="nl-BE-DenaNeural", locale="nl-BE"),),
    ),
}


def get_voice_registry() -> dict[SupportedLanguage, VoicePlan]:
    return _VOICE_REGISTRY.copy()


def select_voice(
    language: SupportedLanguage,
    *,
    available_voice_ids: set[str] | None = None,
) -> VoiceSelection:
    plan = _VOICE_REGISTRY[language]
    for index, candidate in enumerate(plan.ordered_candidates()):
        if available_voice_ids is not None and candidate.voice_id not in available_voice_ids:
            continue
        return VoiceSelection(
            language=language,
            voice_id=candidate.voice_id,
            locale=candidate.locale,
            registry_version=VOICE_REGISTRY_VERSION,
            fallback_used=index > 0,
        )

    raise VoiceSelectionError(
        f"No approved Azure voice available for language {language.value}"
    )


__all__ = [
    "VOICE_REGISTRY_VERSION",
    "VoicePlan",
    "VoiceSelection",
    "VoiceSelectionError",
    "get_voice_registry",
    "select_voice",
]
