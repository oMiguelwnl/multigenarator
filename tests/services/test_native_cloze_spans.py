"""Cloze masks only the exact occurrence verified by the linguistic matcher."""

import pytest

from multilang.domain.anki_semantics import SemanticCard
from multilang.domain.content import ContentRequest, TargetMatchEvidence
from multilang.services.native_content import NativeContentService
from multilang.services.semantic_anki import _render_card


def generate_card(sentence, *, target_span=None, role="cloze"):
    card = SemanticCard(
        parent_lexical_identity_id="lex-he",
        language="en",
        parent_lemma="he",
        sense_id="male-pronoun",
        role=role,
        display_text="he",
        context_cue="Subject pronoun",
        inventory="core",
        rank=1,
        deck_edition_id="en-1",
    )
    request = ContentRequest(
        lexical_identity_id=card.parent_lexical_identity_id,
        card_id=card.card_id,
        language="en",
        language_profile_version="1",
        lemma=card.parent_lemma,
        display_text=card.display_text,
        sense_id=card.sense_id,
        context_cue=card.context_cue,
        namespace="core",
        deck_edition_id=card.deck_edition_id,
        grounding_sha256="a" * 64,
        target_concept_id="pronoun-he",
    )

    def matcher(request, _sentence):
        span = {"target_span": target_span} if target_span is not None else {}
        return TargetMatchEvidence(
            lexical_identity_id=request.lexical_identity_id,
            sense_id=request.sense_id,
            target_concept_id=request.target_concept_id,
            matched=True,
            observed_concept_ids=(request.target_concept_id,),
            analyzer_version="fixture-1",
            evidence_sha256="b" * 64,
            **span,
        )

    service = NativeContentService(
        generator=lambda _: {
            "definition": "A male subject pronoun.",
            "example_sentence": sentence,
            "translation": "Fixture translation.",
        },
        matcher=matcher,
        provider="fixture",
        model_version="1",
    )
    return SemanticCard.model_validate(
        card.model_dump() | {"content": service.generate(request)}
    )


def test_cloze_does_not_infer_target_from_substring_when_span_is_missing():
    card = generate_card("He likes the book.")
    with pytest.raises(ValueError, match="verified target span"):
        _render_card(card, prototype=True)


def test_cloze_masks_only_verified_occurrence_among_other_substrings():
    card = generate_card("the boy says he knows the answer.", target_span=(13, 15))
    front, _, _ = _render_card(card, prototype=True)
    assert front == "the boy says […] knows the answer."


def test_cloze_rendering_rechecks_persisted_span_against_sentence():
    card = generate_card("the boy says he knows the answer.", target_span=(13, 15))
    evidence = card.content.target_evidence.model_copy(update={"target_span": (0, 2)})
    content = card.content.model_copy(update={"target_evidence": evidence})
    with pytest.raises(ValueError, match="verified target span"):
        _render_card(card.model_copy(update={"content": content}), prototype=True)


def test_cloze_prototype_without_content_requires_verified_target_span():
    card = generate_card("He likes the book.").model_copy(update={"content": None})
    with pytest.raises(ValueError, match="verified target span"):
        _render_card(card, prototype=True)


@pytest.mark.parametrize("span", [(0, 2), (13, 99), (-1, 2), (15, 13), (13, 13), (13, 14)])
def test_generation_rejects_invalid_or_mismatched_verified_span(span):
    with pytest.raises(ValueError, match="span"):
        generate_card("the boy says he knows the answer.", target_span=span)


def test_non_cloze_generation_and_rendering_do_not_require_target_span():
    card = generate_card("He likes the book.", role="headword")
    front, _, _ = _render_card(card, prototype=True)
    assert front == "he"
    assert "target_span" not in card.content.target_evidence.model_dump(mode="json")
