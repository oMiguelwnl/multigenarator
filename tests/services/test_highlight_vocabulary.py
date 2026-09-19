"""Explicit vocabulary inputs preserve complete entries instead of mining text."""

from hashlib import sha256
from types import SimpleNamespace

import pytest

from multilang.domain.highlights import HighlightProvenance, NormalizedHighlight
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates
from multilang.services.input_fingerprint import build_input_fingerprint
from multilang.services.kindle_highlight_parser import parse_kindle_highlight_export
from multilang.services.word_list_parser import parse_word_list


def highlight(text, index=0):
    digest = sha256(text.encode()).hexdigest()
    return NormalizedHighlight(
        highlight_id=f"fixture-{index}", text=text,
        provenance=HighlightProvenance(source_path="fixture.txt", source_format="text",
                                       source_index=index, content_hash=digest),
    )


def test_kindle_vocabulary_preserves_phrases_and_explicit_function_words():
    entries = ["take off", "in spite of", "a", "I", "l'amour"]
    result = extract_highlight_candidates(
        [highlight(text, i) for i, text in enumerate(entries)],
        language=SupportedLanguage.EN, input_mode="vocabulary",
    )
    assert [candidate.display_form for candidate in result.candidates] == entries
    assert result.rejected_token_count == 0


def test_vocabulary_deduplicates_same_entry_across_distinct_highlights():
    result = extract_highlight_candidates(
        [highlight("take off"), highlight(" Take   Off ", 1)],
        language=SupportedLanguage.EN, input_mode="vocabulary",
    )
    assert len(result.candidates) == 1
    assert result.candidates[0].occurrence_count == 2
    assert result.duplicate_count == 1


def test_vocabulary_keys_do_not_depend_on_case_or_export_order():
    def keys(entries):
        return {item.item_key for item in extract_highlight_candidates(
            [highlight(value, i) for i, value in enumerate(entries)],
            language=SupportedLanguage.EN, input_mode="vocabulary",
        ).candidates}
    assert keys(["take off", "harbor"]) == keys(["Harbor", "Take  Off"])


@pytest.mark.parametrize("text", ["!?!", "https://example.org/private", "x" * 257])
def test_invalid_vocabulary_is_reported_without_content(text):
    result = extract_highlight_candidates([highlight(text)], language=SupportedLanguage.EN, input_mode="vocabulary")
    assert not result.candidates
    assert result.rejected_token_count == 1
    assert result.errors[0].reason_code == "invalid_vocabulary_entry"
    assert text not in result.model_dump_json()


def test_preview_counts_invalid_vocabulary(tmp_path):
    from multilang.services.highlight_import_preview import build_highlight_import_preview
    path = tmp_path / "export.txt"
    path.write_text("Book\n- Your Highlight at Location 1\n\n!?!\n==========")
    preview = build_highlight_import_preview(path, language=SupportedLanguage.EN, input_mode="vocabulary")
    assert preview.rejected_highlights == 1
    assert preview.planned_cards == 0


def test_text_mode_keeps_existing_extraction_and_rejects_unknown_mode():
    entry = highlight("The small bird waits")
    default = extract_highlight_candidates([entry], language=SupportedLanguage.EN)
    explicit = extract_highlight_candidates([entry], language=SupportedLanguage.EN, input_mode="text")
    assert default == explicit
    with pytest.raises(ValueError):
        extract_highlight_candidates([entry], language=SupportedLanguage.EN, input_mode="guess")


def test_highlight_input_mode_is_opt_in_and_part_of_job_identity():
    original = GenerationRequest(language="en", source_type="kindle-highlights")
    vocabulary = GenerationRequest(language="en", source_type="kindle-highlights", highlight_input="vocabulary")
    assert "highlight_input" not in original.model_dump()
    assert vocabulary.model_dump()["highlight_input"] == "vocabulary"
    assert build_input_fingerprint(original, requested_item_keys=["x"]) != build_input_fingerprint(vocabulary, requested_item_keys=["x"])
    with pytest.raises(ValueError):
        GenerationRequest(language="en", source_type="word-list", highlight_input="vocabulary")


@pytest.mark.parametrize("text,expected", [
    ('"hello, world"; take off; l\'amour', ["hello, world", "take off", "l'amour"]),
    ("l'amour d'abord", ["l'amour d'abord"]),
    ('"take off" "in spite of"', ["take off", "in spite of"]),
    ("take off;", ["take off"]),
    (",;|", []),
    ('""', []),
])
def test_word_list_preserves_quoted_separators_and_internal_apostrophes(tmp_path, text, expected):
    path = tmp_path / "words.txt"
    path.write_text(text)
    assert [item.display_form for item in parse_word_list(path).items] == expected


def test_kindle_text_metadata_does_not_become_vocabulary(tmp_path):
    path = tmp_path / "My Clippings.txt"
    path.write_text("Actual Book Title (Author)\n- Your Highlight on Location 12 | Added on Friday\n\ntake off\n==========\n")
    parsed = parse_kindle_highlight_export(path)
    assert [item.text for item in parsed.highlights] == ["take off"]


def test_kindle_html_preserves_text_after_nested_formatting(tmp_path):
    path = tmp_path / "export.html"
    path.write_text('<div class="noteHeading">Location <span>12</span></div><div class="noteText">take <b>off</b> soon<br>again</div>')
    parsed = parse_kindle_highlight_export(path)
    assert [item.text for item in parsed.highlights] == ["take off soon again"]
    assert "12" in parsed.highlights[0].provenance.raw_location


def test_vocabulary_candidates_never_send_the_import_as_sentence_context():
    from multilang.domain.lexicon import LexicalProvenance
    from multilang.services.generate_text_items import GenerateTextItemsService

    def forbidden(*_):
        pytest.fail("vocabulary input is not reading context")
    service = GenerateTextItemsService(
        job_repository=None, lexical_repository=None, text_repository=None,
        text_generation_service=None, text_validation_service=None, tatoeba_sentence_source=None,
        highlight_import_repository=SimpleNamespace(get_private_record=forbidden),
    )
    candidate = SimpleNamespace(provenance=LexicalProvenance(
        source="fixture", notes=["first_highlight_id=x", "highlight_input=vocabulary"],
    ))
    assert service._build_highlight_context(job_id="j", source_type="kindle-highlights", candidate=candidate) is None


@pytest.mark.parametrize("fallback", [False, True])
def test_generic_highlight_generation_does_not_call_unused_translator(fallback):
    from multilang.domain.lexicon import LexicalCardCandidate, LexicalProvenance
    from multilang.services.text_generation import (
        SentenceGenerationFallback,
        SentenceGenerationResult,
        TextGenerationService,
    )

    result = SentenceGenerationResult(sentence="The plane will take off before dawn.")
    def forbidden(*_):
        pytest.fail("highlight card does not require a translation provider")
    service = TextGenerationService(
        sentence_adapter=SimpleNamespace(generate_sentence=lambda _: result),
        translation_adapter=SimpleNamespace(translate_sentence=forbidden),
    )
    item = LexicalCardCandidate(
        submitted_form="take off", display_form="take off", lemma="take off", lemma_key="take off",
        definitions_html="verb: to leave the ground", definition_language="en", translation_target_language="pt",
        grounding_status="grounded", provenance=LexicalProvenance(source="fixture"),
    )
    arguments = dict(candidate=item, deck_language=SupportedLanguage.EN, source_type="kindle-highlights")
    bundle = (service.generate_bundle_from_fallback(**arguments, fallback=SentenceGenerationFallback(sentence_result=result))
              if fallback else service.generate_bundle(**arguments))
    assert bundle.translation.text == ""
    assert bundle.translation.provenance.source == "not-required-by-source-profile"


def test_highlight_prompt_treats_isolated_entry_as_the_whole_target():
    from multilang.services.provider_text_adapters import _sentence_prompt
    from multilang.services.text_generation import SentenceGenerationRequest
    prompt = _sentence_prompt(SentenceGenerationRequest(
        display_form="take off", lemma="take off", target_language="en", translation_target_language="pt",
        definitions_html="verb: to leave the ground", source_type="kindle-highlights",
    ))
    assert "whole expression" in prompt
    assert "selected definition" in prompt
    assert "Highlight context hint" not in prompt


def test_empty_provider_translation_still_rejected():
    from multilang.services.text_generation import GeneratedTranslation, SentenceTranslationResult
    with pytest.raises(ValueError):
        SentenceTranslationResult(translation="")
    with pytest.raises(ValueError):
        GeneratedTranslation(text="", target_language="pt", provenance={"source": "provider"})


def test_new_sentence_policy_does_not_reuse_previous_vocabulary_cache():
    from multilang.services.text_generation import (
        SentenceGenerationRequest,
        SentenceGenerationResult,
        TextGenerationService,
    )
    keys = []
    cache = SimpleNamespace(get=lambda key: keys.append(key), put=lambda *args, **kwargs: None)
    service = TextGenerationService(
        sentence_adapter=SimpleNamespace(generate_sentence=lambda _: SentenceGenerationResult(sentence="The plane will take off before dawn.")),
        translation_adapter=None, provider_cache=cache,
    )
    for source in ["frequency", "word-list", "kindle-highlights"]:
        service._generate_sentence(SentenceGenerationRequest(
            display_form="take off", lemma="take off", target_language="en",
            translation_target_language="pt", source_type=source,
        ))
    assert keys[0].prompt_version == "text-generation-v1"
    assert keys[1].prompt_version == keys[2].prompt_version != keys[0].prompt_version
