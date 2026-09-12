"""Rank allocation, MWE accounting and manifest invariants."""

from decimal import Decimal, localcontext

import pytest


def corpus(**changes):
    from multilang.domain.ranking import CorpusManifest

    return CorpusManifest(
        **{
            "corpus_id": "c",
            "sha256": "a" * 64,
            "language": "en",
            "version": "1",
            "token_count": 1000,
            "document_count": 10,
            "weight": "1",
            "source_id": "fixture",
            "license_id": "test-only",
            "redistribution_approved": False,
            "domain": "fixture",
            "period": "fixture",
            "variant": "fixture",
            **changes,
        }
    )


def observation(identity_id="lex:1:a", **changes):
    from multilang.domain.ranking import CorpusObservation

    return CorpusObservation(
        **{
            "corpus_id": "c",
            "document_id": "d",
            "occurrence_id": "o",
            "token_start": 0,
            "token_end": 1,
            "surface": "run",
            "occurrence_count": "1",
            "allocations": [
                {"lexical_identity_id": identity_id, "share": "1", "confidence": "1"}
            ],
            **changes,
        }
    )


def policy():
    from multilang.domain.ranking import RankingPolicy

    return RankingPolicy(
        version="1",
        normalizer_version="1",
        analyzer_version="fixture-1",
        tokenizer_version="1",
        tagset_version="1",
        allocation_policy_version="1",
        mwe_policy_version="1",
        confidence_threshold="0.99",
        rank_precision=8,
    )


def calculate(corpora=None, observations=None):
    from multilang.services.ranking import RankingEngine

    return RankingEngine().calculate(
        corpora=[corpus()] if corpora is None else corpora,
        observations=[observation()] if observations is None else observations,
        policy=policy(),
    )


def test_rank_uses_normative_natural_log_frequency_and_document_dispersion():
    result = calculate(observations=[observation(occurrence_count="5")])
    with localcontext() as context:
        context.prec = 50
        expected = ((Decimal(1) + Decimal(5000)).ln() * Decimal("0.1")).quantize(
            Decimal("0.00000001")
        )
    assert result.entries[0].score == expected
    assert result.entries[0].aggregate_allocated_frequency == 5
    assert result.entries[0].rank == 1
    assert result.entries[0].level == 1
    assert result.entries[0].quality_score >= 0


def test_fractional_allocations_and_ties_are_order_independent_and_auditable():
    from multilang.domain.ranking import Allocation

    rows = [
        observation(
            occurrence_id="b",
            token_start=1,
            token_end=2,
            allocations=[
                Allocation(lexical_identity_id="b", share="0.5", confidence="1"),
                Allocation(lexical_identity_id="a", share="0.5", confidence="1"),
            ],
        ),
        observation("z", occurrence_id="a"),
    ]
    first = calculate(observations=rows)
    second = calculate(observations=list(reversed(rows)))
    assert first.manifest_sha256 == second.manifest_sha256
    assert [row.lexical_identity_id for row in first.entries] == ["z", "a", "b"]
    assert first.entries[1].aggregate_allocated_frequency == Decimal("0.5")
    changed = calculate(observations=[rows[0]])
    assert changed.manifest_sha256 != first.manifest_sha256
    assert first.diff(changed)


def test_bad_shares_weights_or_denominators_are_rejected():
    with pytest.raises(ValueError):
        corpus(token_count=0)
    with pytest.raises(ValueError):
        calculate(corpora=[corpus(weight="0.5")])
    with pytest.raises(ValueError):
        observation(
            allocations=[
                {"lexical_identity_id": "a", "share": "0.5", "confidence": "1"}
            ]
        )
    with pytest.raises(ValueError):
        calculate(observations=[observation(corpus_id="unknown")])
    with pytest.raises(ValueError):
        observation(token_end=10**12)


def test_ambiguity_quarantines_whole_occurrence_without_first_sense_fallback():
    result = calculate(
        observations=[
            observation(
                allocations=[
                    {
                        "lexical_identity_id": "first",
                        "share": "0.5",
                        "confidence": "0.1",
                    },
                    {
                        "lexical_identity_id": "second",
                        "share": "0.5",
                        "confidence": "1",
                    },
                ]
            )
        ]
    )
    assert not result.entries
    assert result.quarantine[0].reason == "allocation_confidence_below_threshold"


def test_longest_span_mwe_suppresses_components_in_same_channel_only():
    rows = [
        observation("take", occurrence_id="token-a"),
        observation("care", occurrence_id="token-b", token_start=1, token_end=2),
        observation(
            "mwe",
            occurrence_id="mwe",
            token_start=0,
            token_end=2,
            surface="take care",
            is_mwe=True,
        ),
    ]
    result = calculate(observations=rows)
    assert [item.lexical_identity_id for item in result.entries] == ["mwe"]
    assert len(result.suppressed_occurrence_ids) == 2
    assert calculate(observations=rows[::-1]).manifest_sha256 == result.manifest_sha256


def test_same_span_competing_analyses_are_quarantined_without_first_record_bias():
    result = calculate(
        observations=[
            observation("first", occurrence_id="a"),
            observation("second", occurrence_id="b"),
        ]
    )
    assert not result.entries
    assert len(result.quarantine) == 2
    assert {row.reason for row in result.quarantine} == {"ambiguous_span"}


def test_ranking_input_limit_is_applied_to_stream_before_materializing():
    from multilang.services.ranking import RankingEngine

    with pytest.raises(ValueError, match="observation limit"):
        RankingEngine(max_observations=1).calculate(
            corpora=[corpus()],
            policy=policy(),
            observations=(
                observation(occurrence_id=str(i), token_start=i, token_end=i + 1)
                for i in range(100)
            ),
        )


def test_large_multilingual_rank_has_stable_semantics_and_does_not_publish_partial_core():
    from multilang.domain.ranking import validate_core_ranking

    rows = [
        observation(f"id-{i:04}", occurrence_id=f"o{i}", token_start=i, token_end=i + 1)
        for i in range(3000)
    ]
    result = calculate(corpora=[corpus(token_count=10000)], observations=rows)
    validate_core_ranking(result)
    assert [
        sum(entry.level == level for entry in result.entries) for level in (1, 2, 3)
    ] == [1000] * 3
    with pytest.raises(ValueError, match="3000"):
        validate_core_ranking(calculate())
