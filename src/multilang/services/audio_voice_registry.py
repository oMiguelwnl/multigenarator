"""Deterministic Azure voice registry for supported deck languages."""

from __future__ import annotations

from pydantic import BaseModel, Field

from multilang.domain.jobs import SupportedLanguage

VOICE_REGISTRY_VERSION = "2026-07-14c"


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
        preferred=VoiceOption(voice_id="es-ES-TristanMultilingualNeural", locale="es-ES"),
        same_locale_alternates=(VoiceOption(voice_id="es-ES-AlvaroNeural", locale="es-ES"),),
        alternate_locale_alternates=(VoiceOption(voice_id="es-MX-DaliaNeural", locale="es-MX"),),
    ),
    SupportedLanguage.EN: VoicePlan(
        preferred=VoiceOption(voice_id="en-US-Andrew:DragonHDLatestNeural", locale="en-US"),
        same_locale_alternates=(
            VoiceOption(voice_id="en-US-AndrewNeural", locale="en-US"),
            VoiceOption(voice_id="en-US-GuyNeural", locale="en-US"),
        ),
        alternate_locale_alternates=(VoiceOption(voice_id="en-GB-SoniaNeural", locale="en-GB"),),
    ),
    SupportedLanguage.FR: VoicePlan(
        preferred=VoiceOption(voice_id="fr-FR-Remy:DragonHDLatestNeural", locale="fr-FR"),
        same_locale_alternates=(VoiceOption(voice_id="fr-FR-HenriNeural", locale="fr-FR"),),
        alternate_locale_alternates=(VoiceOption(voice_id="fr-CA-SylvieNeural", locale="fr-CA"),),
    ),
    SupportedLanguage.DE: VoicePlan(
        preferred=VoiceOption(voice_id="de-DE-ConradNeural", locale="de-DE"),
        same_locale_alternates=(VoiceOption(voice_id="de-DE-KatjaNeural", locale="de-DE"),),
        alternate_locale_alternates=(VoiceOption(voice_id="de-AT-IngridNeural", locale="de-AT"),),
    ),
    SupportedLanguage.EL: VoicePlan(
        preferred=VoiceOption(voice_id="el-GR-AthinaNeural", locale="el-GR"),
        same_locale_alternates=(VoiceOption(voice_id="el-GR-NestorasNeural", locale="el-GR"),),
    ),
    SupportedLanguage.IT: VoicePlan(
        preferred=VoiceOption(voice_id="it-IT-GiuseppeMultilingualNeural", locale="it-IT"),
        same_locale_alternates=(VoiceOption(voice_id="it-IT-DiegoNeural", locale="it-IT"),),
        alternate_locale_alternates=(VoiceOption(voice_id="it-IT-IsabellaNeural", locale="it-IT"),),
    ),
    SupportedLanguage.PL: VoicePlan(
        preferred=VoiceOption(voice_id="pl-PL-AgnieszkaNeural", locale="pl-PL"),
        same_locale_alternates=(VoiceOption(voice_id="pl-PL-MarekNeural", locale="pl-PL"),),
    ),
    SupportedLanguage.TR: VoicePlan(
        preferred=VoiceOption(voice_id="tr-TR-EmelNeural", locale="tr-TR"),
        same_locale_alternates=(VoiceOption(voice_id="tr-TR-AhmetNeural", locale="tr-TR"),),
    ),
    SupportedLanguage.RO: VoicePlan(
        preferred=VoiceOption(voice_id="ro-RO-AlinaNeural", locale="ro-RO"),
        same_locale_alternates=(VoiceOption(voice_id="ro-RO-EmilNeural", locale="ro-RO"),),
    ),
    SupportedLanguage.RU: VoicePlan(
        preferred=VoiceOption(voice_id="ru-RU-DmitryNeural", locale="ru-RU"),
        same_locale_alternates=(VoiceOption(voice_id="ru-RU-SvetlanaNeural", locale="ru-RU"),),
    ),
    SupportedLanguage.NL: VoicePlan(
        preferred=VoiceOption(voice_id="nl-NL-ColetteNeural", locale="nl-NL"),
        same_locale_alternates=(VoiceOption(voice_id="nl-NL-MaartenNeural", locale="nl-NL"),),
        alternate_locale_alternates=(VoiceOption(voice_id="nl-BE-DenaNeural", locale="nl-BE"),),
    ),
    SupportedLanguage.DA: VoicePlan(
        preferred=VoiceOption(voice_id="da-DK-ChristelNeural", locale="da-DK"),
        same_locale_alternates=(VoiceOption(voice_id="da-DK-JeppeNeural", locale="da-DK"),),
    ),
    SupportedLanguage.NB: VoicePlan(
        preferred=VoiceOption(voice_id="nb-NO-PernilleNeural", locale="nb-NO"),
        same_locale_alternates=(VoiceOption(voice_id="nb-NO-FinnNeural", locale="nb-NO"),),
    ),
    SupportedLanguage.SV: VoicePlan(
        preferred=VoiceOption(voice_id="sv-SE-SofieNeural", locale="sv-SE"),
        same_locale_alternates=(VoiceOption(voice_id="sv-SE-MattiasNeural", locale="sv-SE"),),
    ),
    SupportedLanguage.FI: VoicePlan(
        preferred=VoiceOption(voice_id="fi-FI-NooraNeural", locale="fi-FI"),
        same_locale_alternates=(VoiceOption(voice_id="fi-FI-HarriNeural", locale="fi-FI"),),
    ),
    SupportedLanguage.HU: VoicePlan(
        preferred=VoiceOption(voice_id="hu-HU-NoemiNeural", locale="hu-HU"),
        same_locale_alternates=(VoiceOption(voice_id="hu-HU-TamasNeural", locale="hu-HU"),),
    ),
    SupportedLanguage.CS: VoicePlan(
        preferred=VoiceOption(voice_id="cs-CZ-VlastaNeural", locale="cs-CZ"),
        same_locale_alternates=(VoiceOption(voice_id="cs-CZ-AntoninNeural", locale="cs-CZ"),),
    ),
    SupportedLanguage.HR: VoicePlan(
        preferred=VoiceOption(voice_id="hr-HR-GabrijelaNeural", locale="hr-HR"),
        same_locale_alternates=(VoiceOption(voice_id="hr-HR-SreckoNeural", locale="hr-HR"),),
    ),
    SupportedLanguage.LA: VoicePlan(
        preferred=VoiceOption(voice_id="it-IT-IsabellaNeural", locale="it-IT"),
        same_locale_alternates=(VoiceOption(voice_id="it-IT-DiegoNeural", locale="it-IT"),),
        alternate_locale_alternates=(),
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
