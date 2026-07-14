"""Library-backed pronunciation generation adapters."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from multilang.services.provider_pronunciation_adapters import (
    PronunciationGenerationRequest,
    PronunciationGenerationResult,
)

PronunciationGenerateFunc = Callable[[str, str], str | None]

_GRUUT_LANG_CODES = {
    "pt": "pt",
    "es": "es-es",
    "en": "en-us",
    "fr": "fr-fr",
    "de": "de-de",
    "it": "it-it",
    "ru": "ru-ru",
    "nl": "nl",
    "sv": "sv-se",
}

_PHONEMIZER_ESPEAK_LANG_CODES = {
    "pt": "pt-br",
    "es": "es",
    "en": "en-us",
    "fr": "fr-fr",
    "de": "de",
    "it": "it",
    "pl": "pl",
    "tr": "tr",
    "ro": "ro",
    "ru": "ru",
    "nl": "nl",
    "da": "da",
    "nb": "nb",
    "sv": "sv",
    "fi": "fi",
}

_EPITRAN_LANG_CODES = {
    "pt": "por-Latn",
    "es": "spa-Latn",
    "en": "eng-Latn",
    "fr": "fra-Latn",
    "de": "deu-Latn",
    "it": "ita-Latn",
    "pl": "pol-Latn",
    "tr": "tur-Latn",
    "ro": "ron-Latn",
    "ru": "rus-Cyrl",
    "nl": "nld-Latn",
    "sv": "swe-Latn",
    "fi": "fin-Latn",
}

_WINDOWS_ESPEAK_LIBRARY_CANDIDATES = (
    Path("C:/Program Files/eSpeak NG/libespeak-ng.dll"),
    Path("C:/Program Files (x86)/eSpeak NG/libespeak-ng.dll"),
)


class PronunciationAdapter(Protocol):
    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> PronunciationGenerationResult: ...


@dataclass(frozen=True)
class PronunciationLibraryResolver:
    name: str
    language_codes: dict[str, str]
    generate: PronunciationGenerateFunc


class LibraryPronunciationAdapter:
    """Generate IPA from deterministic G2P libraries before any AI fallback."""

    def __init__(self, resolvers: Sequence[PronunciationLibraryResolver] | None = None) -> None:
        self._resolvers = tuple(resolvers or _default_resolvers())

    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> PronunciationGenerationResult:
        attempted: list[str] = []
        for resolver, library_language_code in self._ordered_resolvers(request.target_language):
            attempted.append(resolver.name)
            try:
                ipa = _format_ipa(resolver.generate(library_language_code, request.display_form))
            except Exception:
                continue
            if not ipa:
                continue
            return PronunciationGenerationResult(
                ipa=ipa,
                spoken_form=request.display_form,
                uncertainty_notes=[],
                provenance={
                    "source": "library-pronunciation-generator",
                    "provider": resolver.name,
                    "language_code": library_language_code,
                    "attempted_providers": attempted,
                },
            )
        raise ValueError("no library pronunciation resolver returned IPA")

    def resolver_names_for_language(self, language_code: str) -> list[str]:
        """Return configured resolver order for tests and diagnostics."""

        return [resolver.name for resolver, _ in self._ordered_resolvers(language_code)]

    def _ordered_resolvers(self, language_code: str) -> list[tuple[PronunciationLibraryResolver, str]]:
        normalized_language = language_code.casefold()
        ordered: list[tuple[PronunciationLibraryResolver, str]] = []
        for resolver in self._resolvers:
            library_language_code = resolver.language_codes.get(normalized_language)
            if library_language_code is not None:
                ordered.append((resolver, library_language_code))
        return ordered


class FallbackPronunciationAdapter:
    """Try pronunciation adapters in order, stopping on the first usable result."""

    def __init__(self, adapters: Sequence[PronunciationAdapter]) -> None:
        if not adapters:
            raise ValueError("at least one pronunciation adapter is required")
        self.adapters = tuple(adapters)

    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> PronunciationGenerationResult:
        for adapter in self.adapters:
            try:
                return adapter.generate_pronunciation(request)
            except Exception:
                continue
        raise ValueError("all pronunciation adapters failed")


def _default_resolvers() -> tuple[PronunciationLibraryResolver, ...]:
    return (
        PronunciationLibraryResolver(
            name="gruut",
            language_codes=_GRUUT_LANG_CODES,
            generate=_generate_with_gruut,
        ),
        PronunciationLibraryResolver(
            name="phonemizer-espeak",
            language_codes=_PHONEMIZER_ESPEAK_LANG_CODES,
            generate=_generate_with_phonemizer_espeak,
        ),
        PronunciationLibraryResolver(
            name="epitran",
            language_codes=_EPITRAN_LANG_CODES,
            generate=_generate_with_epitran,
        ),
    )


def _generate_with_gruut(language_code: str, text: str) -> str | None:
    from gruut import sentences

    for sentence in sentences(text, lang=language_code):
        spoken_words = []
        for word in sentence:
            if getattr(word, "is_spoken", False) and getattr(word, "phonemes", None):
                spoken_words.append("".join(str(phoneme) for phoneme in word.phonemes))
        if spoken_words:
            return " ".join(spoken_words)
    return None


def _generate_with_phonemizer_espeak(language_code: str, text: str) -> str | None:
    _configure_espeak_library()

    from phonemizer import phonemize

    result = phonemize(
        text,
        language=language_code,
        backend="espeak",
        strip=True,
        preserve_punctuation=False,
        with_stress=True,
        language_switch="remove-flags",
        words_mismatch="ignore",
    )
    return result if isinstance(result, str) else None


def _configure_espeak_library(candidates: Sequence[Path] = _WINDOWS_ESPEAK_LIBRARY_CANDIDATES) -> None:
    """Let phonemizer find common Windows eSpeak NG installs from winget."""

    try:
        from phonemizer.backend import EspeakBackend
        from phonemizer.backend.espeak.wrapper import EspeakWrapper
    except Exception:
        return

    try:
        if EspeakBackend.is_available():
            return
    except Exception:
        return

    for library_path in candidates:
        if not library_path.exists():
            continue
        try:
            EspeakWrapper.set_library(str(library_path))
        except Exception:
            continue
        try:
            if EspeakBackend.is_available():
                return
        except Exception:
            continue


def _generate_with_epitran(language_code: str, text: str) -> str | None:
    _patch_panphon_utf8_data_loading()

    import epitran

    return epitran.Epitran(language_code).transliterate(text)


def _patch_panphon_utf8_data_loading() -> None:
    """Force panphon resource CSVs to load as UTF-8 on Windows cp1252 locales."""

    import panphon.featuretable as featuretable

    if getattr(featuretable.FeatureTable._read_bases, "_multilang_utf8_patch", False):
        return

    def _read_bases_utf8(self: object, fn: str, weights: object) -> tuple[list[tuple[str, object]], dict[str, object], list[str]]:
        spec_to_int = {"+": 1, "0": 0, "-": -1}
        with featuretable.files("panphon").joinpath(fn).open(encoding="utf-8") as file_handle:
            dataframe = featuretable.pd.read_csv(file_handle)
        dataframe["ipa"] = dataframe["ipa"].apply(self.normalize)
        feature_names = list(dataframe.columns[1:])
        dataframe[feature_names] = dataframe[feature_names].map(lambda value: spec_to_int[value])
        segments = [
            (row["ipa"], featuretable.Segment(feature_names, row[1:].to_dict(), weights=weights))
            for (_, row) in dataframe.iterrows()
        ]
        return segments, dict(segments), feature_names

    _read_bases_utf8._multilang_utf8_patch = True  # type: ignore[attr-defined]
    featuretable.FeatureTable._read_bases = _read_bases_utf8


def _format_ipa(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    if not cleaned:
        return None
    if cleaned.startswith(("/", "[", "⟨")):
        return cleaned
    return f"/{cleaned}/"


__all__ = [
    "FallbackPronunciationAdapter",
    "LibraryPronunciationAdapter",
    "PronunciationLibraryResolver",
]
