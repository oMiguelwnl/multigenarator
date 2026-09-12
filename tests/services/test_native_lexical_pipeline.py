"""The native pipeline only promotes explicit, qualified source analyses."""

import pytest


def profile():
    from multilang.domain.language_profiles import POLICY_GROUPS, CapabilityEvidence
    from multilang.services.language_profiles import LanguageProfileRegistry

    enabled = CapabilityEvidence(state="enabled", evidence_sha256="e" * 64)
    return (
        LanguageProfileRegistry()
        .get("en")
        .model_copy(
            update={
                "analyzer_id": "source-evidence",
                "analyzer_version": "1",
                "tagset": "fixture",
                "tagset_version": "1",
                "source_ids": ("fixture",),
                "capabilities": {"core": enabled},
                "policies": {name: enabled for name in POLICY_GROUPS},
            }
        )
    )


def source_record(**changes):
    from multilang.services.lexical_pipeline import SourceLexeme

    return SourceLexeme(
        **{
            "record_id": "r1",
            "language": "en",
            "surface": "ran",
            "lemma": "run",
            "part_of_speech": "VERB",
            "sense_id": "motion",
            "source_id": "fixture",
            "source_version": "1",
            "source_sha256": "a" * 64,
            "confidence": "1",
            "features": {"tense": "past"},
            "attestation": 3,
            **changes,
        }
    )


def test_pipeline_resolves_declared_source_evidence_preserving_submitted_form():
    from multilang.services.lexical_pipeline import (
        LexicalPipeline,
        SourceEvidenceAnalyzer,
        StaticLexicalSource,
    )

    result = LexicalPipeline().run(
        profile=profile(),
        source=StaticLexicalSource([source_record()]),
        analyzer=SourceEvidenceAnalyzer(),
    )
    assert len(result.identities) == 1
    assert result.identities[0].lemma == "run"
    assert result.forms[0].text == "ran"
    assert (
        result.forms[0].lexical_identity_id == result.identities[0].lexical_identity_id
    )
    assert not result.quarantine
    assert (
        result.production_eligible is False
    )  # A sample is not an approved 3000-entry Core.


def test_pipeline_requires_profile_and_adapter_qualification_before_reading_source():
    from multilang.services.language_profiles import LanguageProfileRegistry
    from multilang.services.lexical_pipeline import (
        LexicalPipeline,
        SourceEvidenceAnalyzer,
        StaticLexicalSource,
    )

    with pytest.raises(ValueError, match="not enabled"):
        LexicalPipeline().run(
            profile=LanguageProfileRegistry().get("en"),
            source=StaticLexicalSource([source_record()]),
            analyzer=SourceEvidenceAnalyzer(),
        )
    with pytest.raises(ValueError, match="analyzer"):
        LexicalPipeline().run(
            profile=profile().model_copy(update={"analyzer_version": "2"}),
            source=StaticLexicalSource([source_record()]),
            analyzer=SourceEvidenceAnalyzer(),
        )


def test_pipeline_quarantines_unknown_sense_instead_of_inventing_one():
    from multilang.services.lexical_pipeline import (
        LexicalPipeline,
        SourceEvidenceAnalyzer,
        StaticLexicalSource,
    )

    result = LexicalPipeline().run(
        profile=profile(),
        source=StaticLexicalSource([source_record(sense_id=None)]),
        analyzer=SourceEvidenceAnalyzer(),
    )
    assert not result.identities
    assert result.quarantine[0].reason == "unresolved_analysis"


def test_pipeline_refuses_unapproved_sources_language_drift_and_input_limit():
    from multilang.services.lexical_pipeline import (
        LexicalPipeline,
        SourceEvidenceAnalyzer,
        StaticLexicalSource,
    )

    for record in (source_record(source_id="unapproved"), source_record(language="fr")):
        with pytest.raises(ValueError):
            LexicalPipeline().run(
                profile=profile(),
                source=StaticLexicalSource([record]),
                analyzer=SourceEvidenceAnalyzer(),
            )
    with pytest.raises(ValueError, match="record limit"):
        LexicalPipeline(max_records=1).run(
            profile=profile(),
            source=StaticLexicalSource(
                [source_record(), source_record(record_id="r2")]
            ),
            analyzer=SourceEvidenceAnalyzer(),
        )


def test_pipeline_requires_one_resolved_analysis_and_never_chooses_first():
    from multilang.services.lexical_pipeline import (
        LexicalPipeline,
        SourceEvidenceAnalyzer,
        StaticLexicalSource,
    )

    class AmbiguousAnalyzer(SourceEvidenceAnalyzer):
        def analyze(self, *, record, profile):
            first = super().analyze(record=record, profile=profile)[0]
            return (first, first.model_copy(update={"sense_id": "other"}))

    result = LexicalPipeline().run(
        profile=profile(),
        source=StaticLexicalSource([source_record()]),
        analyzer=AmbiguousAnalyzer(),
    )
    assert not result.identities
    assert result.quarantine[0].reason == "ambiguous_analysis"


def test_pipeline_refuses_undeclared_normalization_or_ranking_version_drift():
    from multilang.domain.ranking import RankingPolicy
    from multilang.services.lexical_pipeline import (
        LexicalPipeline,
        SourceEvidenceAnalyzer,
        StaticLexicalSource,
    )

    with pytest.raises(ValueError, match="normalization"):
        LexicalPipeline().run(
            profile=profile().model_copy(
                update={"normalization_version": "unimplemented"}
            ),
            source=StaticLexicalSource([source_record()]),
            analyzer=SourceEvidenceAnalyzer(),
        )
    ranking_policy = RankingPolicy(
        version="1",
        normalizer_version="nfc-preserve-1",
        analyzer_version="other",
        tokenizer_version="1",
        tagset_version="1",
        allocation_policy_version="1",
        mwe_policy_version="1",
        confidence_threshold="1",
    )
    with pytest.raises(ValueError, match="ranking.*version"):
        LexicalPipeline().run(
            profile=profile(),
            source=StaticLexicalSource([source_record()]),
            analyzer=SourceEvidenceAnalyzer(),
            ranking_policy=ranking_policy,
        )
