"""Vocabulary and grammar prerequisites must be checked against local analyses."""

import hashlib
from types import SimpleNamespace

import pytest


def _policy(language="en", **changes):
    from multilang.domain.sentence_curriculum import SentenceCurriculum

    data = {
        "language": language,
        "inventory_sha256": "b" * 64,
        "analyzer_fingerprint": "a" * 64,
        "target": {"lemma": "go", "pos": "VERB"},
        "introduced": [{"lemma": "we", "pos": "PRON"}, {"lemma": "home", "pos": "NOUN"}],
        "allowed_features": [["Tense", "Past"]],
        "min_units": 3,
        "max_units": 8,
    }
    return SentenceCurriculum.model_validate({**data, **changes})


def _analysis(text="We went home.", language="en", **changes):
    from multilang.services.contextual_morphology import ContextualAnalysis, ContextualToken

    digest = hashlib.sha256(text.encode()).hexdigest()
    rows = [
        ("We", "we", "PRON", 0, 2, ()),
        ("went", "go", "VERB", 3, 7, (("Tense", "Past"),)),
        ("home", "home", "NOUN", 8, 12, ()),
        (".", ".", "PUNCT", 12, 13, ()),
    ]
    return ContextualAnalysis.model_validate({
        "language": language, "status": "complete", "reason": "fixture",
        "sentence_sha256": digest, "model_fingerprint": "a" * 64,
        "tokens": [ContextualToken(text=s, lemma=lemma, pos=p, start=a, end=b,
                                   features=f, sentence_sha256=digest,
                                   model_fingerprint="a" * 64) for s, lemma, p, a, b, f in rows],
        **changes,
    })


def test_attested_inflection_uses_lemma_pos_and_analyzer_length():
    from multilang.services.sentence_curriculum import check_sentence_curriculum

    result = check_sentence_curriculum("We went home.", _policy(), _analysis())
    assert result.passed
    assert result.lexical_units == 3
    assert result.knowledge_basis == "previously_introduced_not_observed_mastery"
    assert result.senses_disambiguated is False


def test_new_lexeme_and_unintroduced_grammar_are_visible():
    from multilang.services.sentence_curriculum import check_sentence_curriculum

    policy = _policy(introduced=[{"lemma": "we", "pos": "PRON"}], allowed_features=[])
    result = check_sentence_curriculum("We went home.", policy, _analysis())
    assert not result.passed
    assert "new_lexical_prerequisite" in result.codes
    assert "new_grammar_prerequisite" in result.codes
    assert result.unintroduced == (("home", "NOUN"),)
    assert result.unintroduced_features == (("Tense", "Past"),)


def test_homograph_pos_does_not_count_as_the_target():
    from multilang.services.sentence_curriculum import check_sentence_curriculum

    result = check_sentence_curriculum("We went home.", _policy(target={"lemma": "go", "pos": "NOUN"}), _analysis())
    assert not result.passed
    assert "curriculum_target_missing" in result.codes


@pytest.mark.parametrize("change", [
    {"status": "unavailable", "tokens": (), "reason": "missing_model"},
    {"language": "de"},
    {"sentence_sha256": "f" * 64, "tokens": () , "status": "invalid"},
])
def test_unavailable_or_wrong_analysis_fails_closed(change):
    from multilang.services.sentence_curriculum import check_sentence_curriculum

    assert not check_sentence_curriculum("We went home.", _policy(), _analysis(**change)).passed


def test_model_drift_and_silently_dropped_text_are_rejected():
    from multilang.services.sentence_curriculum import check_sentence_curriculum

    assert not check_sentence_curriculum("We went home.", _policy(analyzer_fingerprint="c" * 64), _analysis()).passed
    analysis = _analysis()
    dropped = analysis.model_copy(update={"tokens": (analysis.tokens[0], analysis.tokens[1], analysis.tokens[-1])})
    assert "incomplete_sentence_analysis" in check_sentence_curriculum("We went home.", _policy(), dropped).codes


def test_length_uses_lexical_units_and_has_a_real_upper_limit():
    from multilang.services.sentence_curriculum import check_sentence_curriculum

    result = check_sentence_curriculum("We went home.", _policy(min_units=1, max_units=2), _analysis())
    assert "curriculum_sentence_too_long" in result.codes


def test_japanese_units_are_not_han_or_whitespace_counts():
    from multilang.services.contextual_morphology import ContextualAnalysis, ContextualToken
    from multilang.services.sentence_curriculum import check_sentence_curriculum

    text = "猫が寝る。"
    digest = hashlib.sha256(text.encode()).hexdigest()
    tokens = [ContextualToken(text=s, lemma=lemma, pos=p, start=a, end=b,
                             sentence_sha256=digest, model_fingerprint="a"*64)
              for s,lemma,p,a,b in [("猫","猫","NOUN",0,1),("が","が","ADP",1,2),("寝る","寝る","VERB",2,4),("。","。","PUNCT",4,5)]]
    analysis = ContextualAnalysis(language="ja",status="complete",reason="fixture",tokens=tokens,
                                  sentence_sha256=digest,model_fingerprint="a"*64)
    policy = _policy("ja", target={"lemma":"猫","pos":"NOUN"},
                     introduced=[{"lemma":"が","pos":"ADP"},{"lemma":"寝る","pos":"VERB"}],
                     allowed_features=[],max_units=3)
    assert check_sentence_curriculum(text,policy,analysis).passed


def test_context_survives_provenance_and_sentence_request_and_prompt():
    from multilang.domain.jobs import SupportedLanguage
    from multilang.domain.lexicon import LexicalCardCandidate, LexicalProvenance
    from multilang.services.provider_text_adapters import _sentence_prompt
    from multilang.services.text_generation import SentenceGenerationRequest

    provenance = LexicalProvenance(source="fixture", sentence_curriculum=_policy())
    restored = LexicalProvenance.model_validate_json(provenance.model_dump_json())
    candidate = LexicalCardCandidate(submitted_form="went",display_form="went",lemma="go",lemma_key="go",
                                     translation_target_language="pt",grounding_status="grounded",provenance=restored)
    request = SentenceGenerationRequest.from_candidate(candidate=candidate,deck_language=SupportedLanguage.EN,source_type="frequency")
    assert request.sentence_curriculum == _policy()
    prompt = _sentence_prompt(request)
    assert "analyzer lexical units" in prompt
    assert "between 4 and 12 words" not in prompt
    assert "previously introduced" in prompt
    assert "sentence_curriculum" not in LexicalProvenance(source="legacy").model_dump()


def test_normal_validator_enforces_the_persisted_curriculum_without_providers():
    from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation
    from multilang.services.text_validation import TextValidationService

    service = TextValidationService(require_translation_fidelity=False,
                                   contextual_analyzer=SimpleNamespace(analyze=lambda lang,text:_analysis()))
    result = service.validate(sentence=GeneratedSentence(text="We went home.",target_language="en",provenance={"source":"fixture"}),
        translation=GeneratedTranslation(text="Fomos para casa.",target_language="pt",provenance={"source":"fixture"}),display_form="went",lemma="go",
        definitions_html=None,require_translation=False,sentence_curriculum=_policy(introduced=[]))
    assert any(flag.code.value == "curriculum_mismatch" for flag in result.validation_flags)


def test_context_rejects_unknown_pos_non_nfc_and_duplicate_prerequisites():
    with pytest.raises(ValueError):
        _policy(target={"lemma":"go","pos":"X"})
    with pytest.raises(ValueError):
        _policy(target={"lemma":"cafe\u0301","pos":"NOUN"})
    with pytest.raises(ValueError):
        _policy(introduced=[{"lemma":"we","pos":"PRON"}]*2)


@pytest.mark.parametrize("service_name", ["generate", "regenerate"])
def test_both_generation_and_regeneration_validate_the_stored_curriculum(service_name):
    from multilang.domain.jobs import SupportedLanguage
    from multilang.domain.lexicon import LexicalCardCandidate, LexicalProvenance
    from multilang.services.generate_text_items import GenerateTextItemsService
    from multilang.services.regenerate_text_item import RegenerateTextItemService
    from multilang.services.text_generation import GeneratedTextBundle
    from multilang.services.text_validation import TextValidationService

    klass = GenerateTextItemsService if service_name == "generate" else RegenerateTextItemService
    service = klass.__new__(klass)
    service.text_validation_service = TextValidationService(require_translation_fidelity=False,
        contextual_analyzer=SimpleNamespace(analyze=lambda lang, text: _analysis()))
    candidate = LexicalCardCandidate(submitted_form="went", display_form="went", lemma="go", lemma_key="go",
        translation_target_language="pt", grounding_status="grounded",
        provenance=LexicalProvenance(source="fixture", sentence_curriculum=_policy(introduced=[])))
    bundle = GeneratedTextBundle.model_validate({
        "sentence": {"text":"We went home.", "target_language":"en", "provenance":{"source":"fixture"}},
        "translation": {"text":"Fomos para casa.", "target_language":"pt", "provenance":{"source":"fixture"}},
    })
    result = service._validate_bundle(bundle=bundle, candidate=candidate, source_type="frequency", deck_language=SupportedLanguage.EN)
    assert any(f.code.value == "curriculum_mismatch" for f in result.validation_flags)
