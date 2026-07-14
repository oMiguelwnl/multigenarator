"""Tests for library-backed pronunciation adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from multilang.services.library_pronunciation_adapters import (
    FallbackPronunciationAdapter,
    LibraryPronunciationAdapter,
    PronunciationLibraryResolver,
    _configure_espeak_library,
)
from multilang.services.provider_pronunciation_adapters import (
    PronunciationGenerationRequest,
    PronunciationGenerationResult,
)


def make_request(language: str = "pt") -> PronunciationGenerationRequest:
    return PronunciationGenerationRequest(
        target_language=language,
        display_form="casa",
        lemma="casa",
        definitions_html="noun: house",
    )


def resolver(name: str, languages: dict[str, str], calls: list[tuple[str, str]], value: str | None) -> PronunciationLibraryResolver:
    def generate(language_code: str, text: str) -> str | None:
        calls.append((name, language_code))
        return value

    return PronunciationLibraryResolver(name=name, language_codes=languages, generate=generate)


def test_library_adapter_uses_gruut_first_for_covered_languages() -> None:
    calls: list[tuple[str, str]] = []
    adapter = LibraryPronunciationAdapter(
        resolvers=[
            resolver("gruut", {"pt": "pt"}, calls, "ˈkaza"),
            resolver("phonemizer-espeak", {"pt": "pt-br"}, calls, "kˈaza"),
            resolver("epitran", {"pt": "por-Latn"}, calls, "kaza"),
        ]
    )

    result = adapter.generate_pronunciation(make_request("pt"))

    assert result.ipa == "/ˈkaza/"
    assert result.spoken_form == "casa"
    assert result.provenance["source"] == "library-pronunciation-generator"
    assert result.provenance["provider"] == "gruut"
    assert calls == [("gruut", "pt")]


def test_library_adapter_uses_phonemizer_first_when_gruut_does_not_cover_language() -> None:
    calls: list[tuple[str, str]] = []
    adapter = LibraryPronunciationAdapter(
        resolvers=[
            resolver("gruut", {"pt": "pt"}, calls, "ignored"),
            resolver("phonemizer-espeak", {"pl": "pl"}, calls, "dɔm"),
            resolver("epitran", {"pl": "pol-Latn"}, calls, "dom"),
        ]
    )

    result = adapter.generate_pronunciation(make_request("pl"))

    assert result.ipa == "/dɔm/"
    assert result.provenance["provider"] == "phonemizer-espeak"
    assert calls == [("phonemizer-espeak", "pl")]


def test_library_adapter_falls_back_to_epitran_after_phonemizer_miss() -> None:
    calls: list[tuple[str, str]] = []
    adapter = LibraryPronunciationAdapter(
        resolvers=[
            resolver("phonemizer-espeak", {"tr": "tr"}, calls, None),
            resolver("epitran", {"tr": "tur-Latn"}, calls, "ev"),
        ]
    )

    result = adapter.generate_pronunciation(make_request("tr"))

    assert result.ipa == "/ev/"
    assert result.provenance["provider"] == "epitran"
    assert calls == [("phonemizer-espeak", "tr"), ("epitran", "tur-Latn")]


def test_default_resolver_order_matches_language_policy() -> None:
    adapter = LibraryPronunciationAdapter()

    assert adapter.resolver_names_for_language("pt") == ["gruut", "phonemizer-espeak", "epitran"]
    assert adapter.resolver_names_for_language("pl") == ["phonemizer-espeak", "epitran"]


def test_configure_espeak_library_uses_existing_windows_library(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import phonemizer.backend as backend_module
    import phonemizer.backend.espeak.wrapper as wrapper_module

    library_path = tmp_path / "libespeak-ng.dll"
    library_path.write_bytes(b"")
    calls: list[str] = []
    available = False

    class FakeEspeakBackend:
        @staticmethod
        def is_available() -> bool:
            return available

    class FakeEspeakWrapper:
        @staticmethod
        def set_library(path: str) -> None:
            nonlocal available
            calls.append(path)
            available = True

    monkeypatch.setattr(backend_module, "EspeakBackend", FakeEspeakBackend)
    monkeypatch.setattr(wrapper_module, "EspeakWrapper", FakeEspeakWrapper)

    _configure_espeak_library(candidates=[library_path])

    assert calls == [str(library_path)]


class FailingPronunciationAdapter:
    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> PronunciationGenerationResult:
        raise ValueError("missing")


class FixedPronunciationAdapter:
    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> PronunciationGenerationResult:
        return PronunciationGenerationResult(
            ipa="/fixed/",
            spoken_form="FIXED",
            provenance={"source": "provider-pronunciation-generator"},
        )


def test_fallback_adapter_uses_later_adapter_after_failure() -> None:
    adapter = FallbackPronunciationAdapter([FailingPronunciationAdapter(), FixedPronunciationAdapter()])

    result = adapter.generate_pronunciation(make_request())

    assert result.ipa == "/fixed/"
    assert result.provenance["source"] == "provider-pronunciation-generator"


def test_fallback_adapter_rejects_empty_adapter_list() -> None:
    with pytest.raises(ValueError, match="at least one"):
        FallbackPronunciationAdapter([])
