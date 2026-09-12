"""Language registration does not implicitly authorize linguistic operations."""

from __future__ import annotations

from collections.abc import Iterable

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import (
    CAPABILITIES,
    POLICY_GROUPS,
    CapabilityEvidence,
    LanguageProfile,
)

_NAMES = {
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
    "ko": "Korean",
    "da": "Danish",
    "nb": "Norwegian Bokmål",
    "sv": "Swedish",
    "fi": "Finnish",
    "hu": "Hungarian",
    "cs": "Czech",
    "hr": "Croatian",
    "el": "Modern Greek",
    "ja": "Japanese",
    "zh": "Mandarin",
    "la": "Classical Latin",
}


def default_language_profiles() -> tuple[LanguageProfile, ...]:
    """Declare all codes with disabled capabilities; no fabricated source/voice approval."""
    profiles = []
    for language in SupportedLanguage:
        script = {
            "ru": ("Cyrillic",),
            "el": ("Greek",),
            "ko": ("Hangul",),
            "ja": ("Han", "Hiragana", "Katakana"),
            "zh": ("Han",),
        }.get(language.value, ("Latin",))
        profiles.append(
            LanguageProfile(
                language=language,
                name=_NAMES[language.value],
                family="classical" if language is SupportedLanguage.LA else "modern",
                explanation_language="pt"
                if language in {SupportedLanguage.EN, SupportedLanguage.LA}
                else "en",
                scripts=script,
                capabilities={name: CapabilityEvidence() for name in CAPABILITIES},
                policies={name: CapabilityEvidence() for name in POLICY_GROUPS},
            )
        )
    return tuple(profiles)


class LanguageProfileRegistry:
    """In-process profile registry with explicit version replacement."""

    def __init__(self, profiles: Iterable[LanguageProfile] | None = None) -> None:
        self._profiles: dict[SupportedLanguage, LanguageProfile] = {}
        for profile in default_language_profiles() if profiles is None else profiles:
            self.register(profile)

    def register(
        self, profile: LanguageProfile, *, replace_version: str | None = None
    ) -> None:
        validated = LanguageProfile.model_validate(profile.model_dump(mode="json"))
        previous = self._profiles.get(validated.language)
        if previous is not None:
            if previous == validated:
                return
            if previous.version == validated.version:
                raise ValueError("profile changes require a new version")
            if replace_version != previous.version:
                raise ValueError("profile replacement requires the previous version")
        self._profiles[validated.language] = validated

    def get(self, language: str | SupportedLanguage) -> LanguageProfile:
        code = SupportedLanguage(language)
        try:
            return self._profiles[code].model_copy(deep=True)
        except KeyError as exc:
            raise ValueError(f"language profile not registered: {code.value}") from exc

    def all(self) -> tuple[LanguageProfile, ...]:
        return tuple(
            self.get(code)
            for code in sorted(self._profiles, key=lambda item: item.value)
        )
