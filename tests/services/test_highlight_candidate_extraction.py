from __future__ import annotations

import hashlib

import pytest

from multilang.domain.highlights import HighlightImportManifest, HighlightProvenance, NormalizedHighlight
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


def _highlight_with_path(text: str, index: int, source_path: str) -> NormalizedHighlight:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return NormalizedHighlight(
        highlight_id=f"text-{index}-{content_hash[:12]}",
        text=text,
        provenance=HighlightProvenance(
            source_path=source_path,
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

    assert {candidate.display_form for candidate in result.candidates[:3]} == {"niño", "abre", "azul"}
    puerta = next(candidate for candidate in result.candidates if candidate.lemma_key == "puerta")
    assert puerta.first_highlight_id == first.highlight_id
    assert puerta.first_source_index == 0
    assert puerta.occurrence_count == 1
    assert len([candidate for candidate in result.candidates if candidate.lemma_key == "puerta"]) == 2


def test_extract_highlight_candidates_filters_noise_and_preserves_unicode_forms() -> None:
    text = "https://example.test 123 !!! a rápido rápido Привет www música"

    result = extract_highlight_candidates([_highlight(text, 0)], language=SupportedLanguage.PT)

    assert {candidate.display_form for candidate in result.candidates} == {"rápido", "Привет", "música"}
    assert next(candidate for candidate in result.candidates if candidate.lemma_key == "rápido").occurrence_count == 2
    assert result.rejected_token_count >= 5
    assert result.duplicate_count == 1


def test_extract_highlight_candidates_preserves_quoted_multiword_expressions() -> None:
    text = 'Le carnet contient "Robe de soie" et "Frais ruban" pour demain'

    result = extract_highlight_candidates([_highlight(text, 0)], language=SupportedLanguage.FR)

    assert "Robe de soie" in {candidate.display_form for candidate in result.candidates}
    assert "Frais ruban" in {candidate.display_form for candidate in result.candidates}
    assert "robe" not in {candidate.lemma_key for candidate in result.candidates}
    assert "soie" not in {candidate.lemma_key for candidate in result.candidates}


def test_extract_highlight_candidates_splits_dense_word_list_highlight() -> None:
    text = "Loge Aplomb Robe de soie Guimpe Frais ruban"

    result = extract_highlight_candidates([_highlight(text, 0)], language=SupportedLanguage.FR)

    assert {candidate.display_form for candidate in result.candidates} == {
        "Loge",
        "Aplomb",
        "Robe de soie",
        "Guimpe",
        "Frais ruban",
    }
    assert "robe" not in {candidate.lemma_key for candidate in result.candidates}
    assert "soie" not in {candidate.lemma_key for candidate in result.candidates}


def test_candidate_exposes_stable_source_content_hash_without_private_text() -> None:
    private_sentence = "El jardín secreto guarda una palabra privada"
    result = extract_highlight_candidates(
        [_highlight_with_path(private_sentence, 0, "first-export.txt")],
        language=SupportedLanguage.ES,
    )

    candidate = next(candidate for candidate in result.candidates if candidate.lemma_key == "jardín")
    expected_hash = hashlib.sha256(private_sentence.encode("utf-8")).hexdigest()

    assert candidate.source_content_hash == expected_hash
    assert len(candidate.source_content_hash) == 64
    assert candidate.source_content_hash == candidate.source_content_hash.lower()
    assert private_sentence not in str(candidate.model_dump())


def test_manifest_serialization_is_hash_and_count_only() -> None:
    private_sentence = "La carta privada nunca debe aparecer"
    content_hash = hashlib.sha256(private_sentence.encode("utf-8")).hexdigest()
    manifest = HighlightImportManifest(
        import_content_hash=content_hash,
        candidate_keys=["highlight-es-abcdef0123456789-fedcba9876543210"],
        counts={"imported_highlights": 1, "extracted_candidates": 1},
    )

    dumped = manifest.model_dump()

    assert dumped["import_content_hash"] == content_hash
    assert private_sentence not in str(dumped)
    assert "source_path" not in dumped
    assert "raw_location" not in dumped


def test_reordered_highlights_produce_same_sorted_item_keys() -> None:
    first = _highlight("El jardín guarda una linterna", 0)
    second = _highlight("La puerta conserva una llave", 1)

    original = extract_highlight_candidates([first, second], language=SupportedLanguage.ES)
    reordered = extract_highlight_candidates([second, first], language=SupportedLanguage.ES)

    assert sorted(candidate.item_key for candidate in original.candidates) == sorted(
        candidate.item_key for candidate in reordered.candidates
    )


def test_same_lemma_in_different_source_content_has_distinct_item_keys() -> None:
    first = _highlight("El jardín guarda calma", 0)
    second = _highlight("El jardín conserva memoria", 1)

    result = extract_highlight_candidates([first, second], language=SupportedLanguage.ES)
    jardin_candidates = [candidate for candidate in result.candidates if candidate.lemma_key == "jardín"]

    assert len(jardin_candidates) == 2
    assert len({candidate.source_content_hash for candidate in jardin_candidates}) == 2
    assert len({candidate.item_key for candidate in jardin_candidates}) == 2
