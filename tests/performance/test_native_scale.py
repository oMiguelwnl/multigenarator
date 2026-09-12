"""Synthetic 22-language workload proves software scale, not linguistic approval."""

import resource
from time import perf_counter

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import (
    LexicalIdentity,
    MorphologicalAnalysis,
    SurfaceForm,
)
from multilang.domain.ranking import (
    CorpusManifest,
    CorpusObservation,
    RankingPolicy,
    validate_core_ranking,
)
from multilang.services.ranking import RankingEngine


@pytest.mark.timeout(300)
def test_66000_identities_and_forms_have_deterministic_independent_language_ranks():
    started = perf_counter()
    all_identities = set()
    all_forms = set()
    manifests = set()
    policy = RankingPolicy(
        version="synthetic-1",
        normalizer_version="nfc-preserve-1",
        analyzer_version="synthetic-1",
        tokenizer_version="synthetic-1",
        tagset_version="synthetic-1",
        allocation_policy_version="synthetic-1",
        mwe_policy_version="synthetic-1",
        confidence_threshold="1",
    )
    for language in SupportedLanguage:
        if language is SupportedLanguage.LA:
            continue
        observations = []
        for index in range(3000):
            identity = LexicalIdentity(
                language=language,
                normalized_lemma=f"fixture-{index}",
                part_of_speech="NOUN",
                sense_id="synthetic-only",
                profile_version="synthetic-1",
                normalizer_version="nfc-preserve-1",
                analyzer_version="synthetic-1",
                source_id="synthetic",
                source_version="1",
                source_sha256="a" * 64,
            )
            identity_id = identity.lexical_identity_id
            analysis = MorphologicalAnalysis(
                lexical_identity_id=identity_id,
                analyzer_id="synthetic",
                analyzer_version="1",
                features={"number": "plural"},
                confidence="1",
                evidence_sha256="b" * 64,
            )
            form = SurfaceForm(
                lexical_identity_id=identity_id,
                text=f"fixture-{index}-form",
                analysis=analysis,
                source_id="synthetic",
                source_sha256="a" * 64,
                attestation=1,
            )
            all_identities.add(identity_id)
            all_forms.add(form.surface_form_id)
            observations.append(
                CorpusObservation(
                    corpus_id="synthetic",
                    document_id="d",
                    occurrence_id=str(index),
                    token_start=index,
                    token_end=index + 1,
                    surface=f"fixture-{index}",
                    allocations=(
                        {
                            "lexical_identity_id": identity_id,
                            "share": "1",
                            "confidence": "1",
                        },
                    ),
                )
            )
        corpus = CorpusManifest(
            corpus_id="synthetic",
            sha256="c" * 64,
            language=language,
            version="1",
            token_count=3000,
            document_count=1,
            weight="1",
            source_id="synthetic",
            license_id="test-only",
            domain="synthetic",
            period="synthetic",
            variant="synthetic",
        )
        result = RankingEngine().calculate(
            corpora=(corpus,), observations=observations, policy=policy
        )
        reverse = RankingEngine().calculate(
            corpora=(corpus,), observations=reversed(observations), policy=policy
        )
        assert result.manifest_sha256 == reverse.manifest_sha256
        validate_core_ranking(result)
        assert len(result.entries) == 3000
        manifests.add(result.manifest_sha256)
    assert len(all_identities) == len(all_forms) == 66_000
    assert len(manifests) == 22
    # Generous regression bounds accommodate shared CI runners and instrumentation.
    assert perf_counter() - started < 300
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 2_000_000  # Linux KiB, < 2 GiB
