"""Definition policy regressions; all lexical examples are synthetic fixtures."""

import json

import pytest


def test_selected_source_sense_is_used_instead_of_first_meaning():
    from multilang.services.content.definition_policy import select_source_meaning
    from multilang.services.lexical_lookup import LexicalRecord

    record = LexicalRecord(
        term="bank",
        display_form="bank",
        lemma="bank",
        part_of_speech="noun",
        source="fixture",
        sense_id="river",
        definitions=["financial institution", "river edge"],
        definition_language="en",
        definition_senses=[
            {"sense_id": "finance", "meaning": "a financial institution", "language": "en"},
            {"sense_id": "river", "meaning": "the land beside a river", "language": "en"},
        ],
    )
    assert select_source_meaning(record) == ("the land beside a river", "en")
    with pytest.raises(ValueError, match="sense"):
        select_source_meaning(record.model_copy(update={"sense_id": "missing"}))


def test_ambiguous_evidence_is_never_resolved_by_list_order():
    from multilang.services.content.definition_policy import select_source_meaning
    from multilang.services.lexical_lookup import LexicalRecord

    record = LexicalRecord(
        term="bank",
        display_form="bank",
        lemma="bank",
        definitions=["financial institution", "river edge"],
        definition_language="en",
    )
    with pytest.raises(ValueError, match="ambiguous"):
        select_source_meaning(record)


@pytest.mark.parametrize(
    "text",
    [
        "noun: bank",
        "noun: BANK.",
        "noun: \nriver edge",
        "noun: <b>river edge</b>",
        "noun: [sound:bank.mp3]",
        "noun: {{Word}}",
        "verb: the land beside a river",
        "noun: learner definition for bank",
        "noun: genitive of bank",
        "noun: " + "x" * 501,
        "noun: a bank",
        "noun: the bank",
        "noun: .",
        "noun: river edge\u2028financial institution",
        "noun: river edge\u2029financial institution",
    ],
)
def test_invalid_definition_cannot_satisfy_common_contract(text):
    from multilang.services.content.definition_policy import validate_definition

    with pytest.raises(ValueError):
        validate_definition(text, lemma="bank", display_form="bank", part_of_speech="NOUN")


def test_definition_contract_accepts_single_sense_without_rewriting_source():
    from multilang.services.content.definition_policy import validate_definition

    value = "noun: the land beside a river"
    assert (
        validate_definition(value, lemma="bank", display_form="bank", part_of_speech="NOUN")
        == value
    )


def test_definition_rejects_circular_infinitive():
    from multilang.services.content.definition_policy import validate_definition

    with pytest.raises(ValueError, match="circular"):
        validate_definition("verb: to run", lemma="run", display_form="ran", part_of_speech="verb")


@pytest.mark.parametrize("separator", ["\u2028", "\u2029"])
def test_definition_rejects_trailing_unicode_line_separator(separator):
    from multilang.services.content.definition_policy import validate_definition

    with pytest.raises(ValueError, match="one line"):
        validate_definition(
            "noun: a river edge" + separator,
            lemma="bank",
            display_form="bank",
            part_of_speech="noun",
        )


def test_legacy_provider_uses_shared_policy_and_rejects_wrong_pos():
    from multilang.services.provider_text_adapters import LiteLLMSentenceAdapter
    from multilang.services.text_generation import DefinitionGenerationRequest
    from multilang.settings import Settings

    calls = []

    def complete(**kwargs):
        calls.append(kwargs)
        return {
            "choices": [{"message": {"content": json.dumps({"definitions_html": "verb: to run"})}}]
        }

    adapter = LiteLLMSentenceAdapter(Settings(_env_file=None), completion_func=complete)
    request = DefinitionGenerationRequest(
        display_form="bank",
        lemma="bank",
        source_language="en",
        target_language="pt",
        part_of_speech="noun",
        source_definitions=("the land beside a river",),
        source_definition_language="en",
        evidence_source="fixture",
        source_sense_id="river",
    )
    with pytest.raises(ValueError, match="part of speech"):
        adapter.generate_definition(request)
    prompt = calls[0]["messages"][1]["content"]
    assert "definition-single-sense-v2" in prompt
    assert "<br> between multiple senses" not in prompt
    assert "circular" in prompt


def test_grounding_uses_explicit_source_sense_mapping():
    from types import SimpleNamespace

    from multilang.domain.jobs import SupportedLanguage
    from multilang.services.lexical_grounding import LexicalGroundingService
    from multilang.services.lexical_lookup import LexicalRecord
    from multilang.services.word_list_parser import ParsedWordListItem

    record = LexicalRecord(
        term="bank",
        display_form="bank",
        lemma="bank",
        ipa="/bæŋk/",
        part_of_speech="noun",
        sense_id="river",
        source="fixture",
        definitions=["finance", "river"],
        definition_senses=[
            {"sense_id": "river", "meaning": "the land beside a river", "language": "en"}
        ],
    )
    service = LexicalGroundingService(lookup=SimpleNamespace(lookup=lambda **_: record))
    candidate = service.ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(
            line_number=1, submitted_form="bank", display_form="bank", item_key="bank"
        ),
    )
    assert candidate.definitions_html == "noun: the land beside a river"
    assert candidate.provenance.definition.quality_decision == "source_verified"


@pytest.mark.parametrize("meaning", ["bank", "<b>the land beside a river</b>"])
def test_legacy_source_must_also_obey_the_shared_definition_contract(meaning):
    from multilang.services.content.definition_evidence import decide_definition
    from multilang.services.text_generation import DefinitionGenerationRequest

    request = DefinitionGenerationRequest(
        lemma="bank",
        display_form="bank",
        source_language="en",
        target_language="en",
        part_of_speech="noun",
        source_definitions=(meaning,),
        source_definition_language="en",
        evidence_source="fixture",
    )
    decision = decide_definition(request, None)
    assert decision.review_required
    assert decision.definitions_html is None
