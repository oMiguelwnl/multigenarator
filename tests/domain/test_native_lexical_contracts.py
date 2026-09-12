"""Native contracts must preserve semantic authority and reject ambiguity."""

from decimal import Decimal

import pytest


def test_language_profiles_are_explicitly_gated_and_preserve_legacy_languages():
    from multilang.services.language_profiles import LanguageProfileRegistry

    registry = LanguageProfileRegistry()
    assert len(registry.all()) == 23
    assert registry.get("ko").explanation_language == "en"
    assert registry.get("en").explanation_language == "pt"
    assert registry.get("la").family == "classical"
    assert registry.get("la").explanation_language == "pt"
    for profile in registry.all():
        with pytest.raises(ValueError, match="not enabled"):
            profile.require("core")
    with pytest.raises(ValueError):
        registry.get("../../secrets")


def test_capability_requires_evidence_and_missing_policy_fails_closed():
    from multilang.domain.language_profiles import CapabilityEvidence
    from multilang.services.language_profiles import LanguageProfileRegistry

    with pytest.raises(ValueError):
        CapabilityEvidence(state="enabled", version="1")
    evidence = CapabilityEvidence(
        state="enabled", version="1", evidence_sha256="a" * 64
    )
    profile = (
        LanguageProfileRegistry()
        .get("en")
        .model_copy(update={"capabilities": {"core": evidence}})
    )
    profile.require("core")
    with pytest.raises(ValueError, match="RANK-01"):
        profile.require("core", policy_groups=("RANK-01",))


def identity(**changes):
    from multilang.domain.lexical_identity import LexicalIdentity

    return LexicalIdentity(
        **{
            "language": "en",
            "normalized_lemma": "run",
            "part_of_speech": "VERB",
            "sense_id": "motion",
            "profile_version": "1",
            "normalizer_version": "nfc-1",
            "analyzer_version": "fixture-1",
            "source_id": "fixture",
            "source_version": "1",
            "source_sha256": "a" * 64,
            **changes,
        }
    )


def test_semantic_identity_is_nfc_and_ignores_source_version_and_rank():
    a = identity(language="pt", normalized_lemma="cafe\u0301")
    b = identity(language="pt", normalized_lemma="café", source_version="2")
    assert a.normalized_lemma == "café"
    assert a.lexical_identity_id == b.lexical_identity_id
    assert (
        a.lexical_identity_id
        != identity(language="pt", normalized_lemma="cafe").lexical_identity_id
    )
    assert (
        a.lexical_identity_id
        != identity(
            language="pt", normalized_lemma="café", sense_id="other"
        ).lexical_identity_id
    )
    assert (
        identity().lexical_identity_id
        != identity(part_of_speech="NOUN").lexical_identity_id
    )
    assert (
        identity().model_dump(mode="json")["lexical_identity_id"]
        == identity().lexical_identity_id
    )
    with pytest.raises(ValueError):
        identity(rank=1)
    with pytest.raises(ValueError):
        identity(part_of_speech="unknown")


def test_computed_identity_roundtrips_but_tampering_is_rejected():
    original = identity()
    assert type(original).model_validate(original.model_dump(mode="json")) == original
    bad = original.model_dump(mode="json")
    bad["lexical_identity_id"] = "lex:1:" + "f" * 64
    with pytest.raises(ValueError):
        type(original).model_validate(bad)


def test_native_mappings_cannot_mutate_a_frozen_policy():
    from multilang.domain.language_profiles import CapabilityEvidence
    from multilang.services.language_profiles import LanguageProfileRegistry

    profile = LanguageProfileRegistry().get("en")
    with pytest.raises(TypeError):
        profile.capabilities["core"] = CapabilityEvidence(
            state="enabled", evidence_sha256="a" * 64
        )


def test_forms_keep_distinct_analyses_and_mwe_requires_explicit_segmentation():
    from multilang.domain.lexical_identity import (
        MorphologicalAnalysis,
        MultiWordExpression,
        SurfaceForm,
    )

    common = {
        "lexical_identity_id": identity().lexical_identity_id,
        "analyzer_id": "fixture",
        "analyzer_version": "1",
        "confidence": "1",
        "evidence_sha256": "a" * 64,
    }
    past = MorphologicalAnalysis(
        **common, features={"mood": "indicative", "tense": "past"}
    )
    irrealis = MorphologicalAnalysis(
        **common, features={"mood": "irrealis", "tense": "past"}
    )
    a = SurfaceForm(
        lexical_identity_id=identity().lexical_identity_id,
        text="were",
        analysis=past,
        source_id="fixture",
        source_sha256="a" * 64,
        attestation=10,
        context="They were ready.",
    )
    b = a.model_copy(update={"analysis": irrealis, "context": "If I were ready."})
    assert a.surface_form_id != b.surface_form_id
    assert a.analysis.morphological_analysis_id != b.analysis.morphological_analysis_id
    with pytest.raises(ValueError):
        MultiWordExpression(
            identity=identity(normalized_lemma="take care"), segments=()
        )


def test_important_forms_are_selected_by_versioned_evidence_without_top_n():
    from multilang.domain.lexical_identity import (
        ImportantFormPolicy,
        MorphologicalAnalysis,
        SurfaceForm,
    )

    lexeme = identity()
    policy = ImportantFormPolicy(
        policy_id="forms-en",
        version="1",
        weights={"irregularity": "1"},
        minimum_score="0.5",
        attestation_threshold=2,
        analysis_confidence_threshold="0.99",
        approval_sha256="b" * 64,
    )
    forms = []
    for text in ("ran", "running", "runs"):
        analysis = MorphologicalAnalysis(
            lexical_identity_id=lexeme.lexical_identity_id,
            analyzer_id="fixture",
            analyzer_version="1",
            features={"tense": text},
            confidence="1",
            evidence_sha256="a" * 64,
        )
        forms.append(
            SurfaceForm(
                lexical_identity_id=lexeme.lexical_identity_id,
                text=text,
                analysis=analysis,
                source_id="fixture",
                source_sha256="a" * 64,
                attestation=3,
                evidence_values={"irregularity": "1"},
            )
        )
    selected = policy.select(forms)
    assert len(selected) == 3
    assert all(row.score == Decimal(1) for row in selected)
    assert policy.select(forms + forms) == selected
    with pytest.raises(ValueError):
        ImportantFormPolicy(
            policy_id="bad",
            version="1",
            weights={"irregularity": "0.2"},
            minimum_score="0.5",
            attestation_threshold=1,
            analysis_confidence_threshold="0.9",
            approval_sha256="b" * 64,
        )
