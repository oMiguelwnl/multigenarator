"""Card totals may exceed the initial 3,000-entry frequency core."""

import pytest

from multilang.domain.anki_semantics import SemanticCard
from multilang.domain.datasets import DatasetManifest, DatasetMember
from multilang.domain.jobs import SupportedLanguage
from multilang.services.semantic_anki import summarize_cards, validate_semantic_cards


def _dataset(language, *, count=3001, namespace="expansion"):
    return DatasetManifest(
        language=language,
        kind="lexical",
        namespace=namespace,
        version="synthetic-size-policy-1",
        source_id="original-test-fixture",
        source_sha256="a" * 64,
        policy_version="test-1",
        members=tuple(
            DatasetMember(identity_id=f"test-identity-{rank}", rank=rank)
            for rank in range(1, count + 1)
        ),
    )


@pytest.mark.parametrize("language", [language for language in SupportedLanguage if language != SupportedLanguage.LA])
def test_every_modern_language_accepts_more_than_3000_expansion_identities(language):
    dataset = _dataset(language)

    assert len(dataset.members) == 3001
    assert dataset.members[-1].rank == 3001


def test_larger_inventory_does_not_replace_3000_with_a_6000_product_ceiling():
    dataset = _dataset(SupportedLanguage.JA, count=7001)

    assert len(dataset.members) == 7001
    assert dataset.members[-1].rank == 7001


def test_latin_foundations_are_not_capped_at_3000_cards():
    assert len(_dataset(SupportedLanguage.LA, namespace="foundation").members) == 3001


def test_larger_inventory_still_requires_source_approval_for_production():
    dataset = _dataset(SupportedLanguage.JA)

    with pytest.raises(ValueError, match="redistribution approval"):
        dataset.require_production()


def test_larger_inventory_still_rejects_duplicate_lexical_identities():
    dataset = _dataset(SupportedLanguage.JA)
    duplicate = DatasetMember(identity_id=dataset.members[0].identity_id, rank=3002)

    with pytest.raises(ValueError, match="duplicate lexical identity"):
        DatasetManifest.model_validate(dataset.model_dump(exclude={"dataset_id"}) | {
            "members": (*dataset.members, duplicate),
        })


@pytest.mark.parametrize("language", [SupportedLanguage.EN, SupportedLanguage.JA, SupportedLanguage.KO])
def test_core_counts_lexical_entries_while_important_forms_increase_card_count(language):
    core = [
        SemanticCard(
            parent_lexical_identity_id=f"test-lexical-{rank}",
            language=language,
            parent_lemma=f"test-lemma-{rank}",
            sense_id="test-sense",
            role="headword",
            display_text=f"test-lemma-{rank}",
            context_cue=f"Original test context {rank}.",
            inventory="core",
            rank=rank,
            deck_edition_id="test-size-policy-1",
        )
        for rank in range(1, 3001)
    ]
    parent = core[0]
    form = SemanticCard.model_validate(parent.model_dump() | {
        "role": "important_form",
        "display_text": "test-inflected-form",
        "context_cue": "Original test context for an important form.",
        "surface_form_id": "test-surface",
        "morphological_analysis_id": "test-analysis",
        "prerequisite_card_id": parent.card_id,
    })

    validate_semantic_cards([*core, form], require_full_core=True)
    totals = summarize_cards([*core, form])

    assert totals["core"]["identities"] == 3000
    assert totals["core"]["total"] == 3001
    assert totals["core:level:1"]["headwords"] == 1000
    assert totals["core:level:1"]["total"] == 1001
    assert form.destination == parent.destination
