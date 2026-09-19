from types import SimpleNamespace

import pytest

from multilang.domain.text_quality import ValidationFlagCode
from multilang.services.morphology import OptionalStanzaMorphologicalAnalyzer
from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation
from multilang.services.text_validation import TextValidationService


@pytest.mark.parametrize("sentence,valid", [
    ("The plane will take off before dawn.", True),
    ("We take the train home each evening.", False),
    ("We turn off the lights each evening.", False),
    ("Take your coat and turn off the lights.", False),
])
def test_whole_expression_required_without_morphology(monkeypatch, sentence, valid):
    monkeypatch.setattr(OptionalStanzaMorphologicalAnalyzer, "_pipeline_for", lambda *_: None)
    # Target completeness is independent of the separately tested corpus detector.
    service = TextValidationService(
        require_definition_consistency=False, require_translation_fidelity=False,
        language_identifier=SimpleNamespace(detect=lambda *_, **__: SimpleNamespace(reliable=False)),
    )
    result = service.validate(
        sentence=GeneratedSentence(text=sentence, target_language="en", provenance={"source": "fixture"}),
        translation=GeneratedTranslation(text=sentence, target_language="en", provenance={"source": "fixture"}),
        display_form="take off", lemma="take off", definitions_html="verb: leave the ground",
        require_translation=False,
    )
    target_flags = [flag for flag in result.validation_flags if flag.code in {
        ValidationFlagCode.MISSING_TARGET_LEMMA, ValidationFlagCode.MORPHOLOGY_MISMATCH,
    }]
    assert bool(target_flags) is not valid


@pytest.mark.parametrize("words,valid", [
    ([("She", "she"), ("takes", "take"), ("off", "off"), ("early", "early")], True),
    ([("She", "she"), ("takes", "take"), ("the", "the"), ("train", "train")], False),
    ([("Off", "off"), ("we", "we"), ("take", "take")], False),
    ([("take", "take"), ("a", "a"), ("day", "day"), ("off", "off")], False),
])
def test_morphology_requires_ordered_whole_expression(words, valid):
    analyzer = OptionalStanzaMorphologicalAnalyzer()
    document = SimpleNamespace(sentences=[SimpleNamespace(words=[SimpleNamespace(text=text, lemma=lemma) for text, lemma in words])])
    analyzer._pipelines["en"] = lambda _: document
    result = analyzer.contains_target_lemma(
        sentence_text=" ".join(text for text, _ in words), target_language="en",
        display_form="take off", lemma="take off",
    )
    assert result.reliable
    assert result.matched is valid
