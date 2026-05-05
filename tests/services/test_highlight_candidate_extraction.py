from __future__ import annotations

import hashlib

import pytest

from multilang.domain.highlights import HighlightProvenance, NormalizedHighlight
from multilang.domain.jobs import SupportedLanguage
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates


LANGUAGE_EXAMPLES = {
    SupportedLanguage.PT: "O menino vê a praça bonita",
    SupportedLanguage.ES: "El niño mira la puerta azul",
    SupportedLanguage.EN: "The curious meadow keeps a lantern",
    SupportedLanguage.FR: "Le garçon ouvre la fenêtre verte",
    SupportedLanguage.DE: "Der kleine Garten bleibt ruhig",
    SupportedLanguage.IT: "Il ragazzo trova una piazza nuova",
    SupportedLanguage.PL: "Ten dom ma piękny ogród",
    SupportedLanguage.TR: "Bu çocuk güzel kapıyı açar",
    SupportedLanguage.RO: "Acest copil vede piața veche",
    SupportedLanguage.RU: "Этот дом видит красивый сад",
    SupportedLanguage.NL: "De jongen vindt een mooie tuin",
}


def _highlight(text: str, index: int) -> NormalizedHighlight:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return NormalizedHighlight(
        highlight_id=f"text-{index}-{content_hash[:12]}",
        text=text,
        provenance=HighlightProvenance(
            source_path="local_export.txt",
            source_format="text",
            source_index=index,
            content_hash=content_hash,
        ),
    )


@pytest.mark.parametrize("language,text", LANGUAGE_EXAMPLES.items())
def test_extract_highlight_candidates_supports_every_language(language: SupportedLanguage, text: str) -> None:
    result = extract_highlight_candidates([_highlight(text, 0)], language=language)

    assert result.candidates
    assert all(candidate.first_source_index == 0 for candidate in result.candidates)


def test_extract_highlight_candidates_deduplicates_with_first_seen_provenance() -> None:
    first = _highlight("El niño abre la puerta azul", 0)
    second = _highlight("La puerta azul guarda otro niño", 1)

    result = extract_highlight_candidates([first, second], language=SupportedLanguage.ES)

    assert [candidate.display_form for candidate in result.candidates[:3]] == ["niño", "abre", "puerta"]
    puerta = next(candidate for candidate in result.candidates if candidate.lemma_key == "puerta")
    assert puerta.first_highlight_id == first.highlight_id
    assert puerta.first_source_index == 0
    assert puerta.occurrence_count == 2
    assert result.duplicate_count >= 2


def test_extract_highlight_candidates_filters_noise_and_preserves_unicode_forms() -> None:
    text = "https://example.test 123 !!! a rápido rápido Привет www música"

    result = extract_highlight_candidates([_highlight(text, 0)], language=SupportedLanguage.PT)

    assert [candidate.display_form for candidate in result.candidates] == ["rápido", "Привет", "música"]
    assert result.candidates[0].occurrence_count == 2
    assert result.rejected_token_count >= 5
    assert result.duplicate_count == 1
