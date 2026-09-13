import pytest

from multilang.domain.lexical_identity import ImportantFormPolicy


def values():
    return dict(
        policy_id="test",
        version="1",
        weights={"frequency": "1"},
        minimum_score="0.5",
        attestation_threshold=1,
        analysis_confidence_threshold="0.9",
    )


def test_legacy_policy_hash_is_unchanged():
    policy = ImportantFormPolicy(**values(), approval_sha256="a" * 64)
    assert (
        policy.policy_sha256 == "f93caba91898c95191c416d258a2fe9e25a961c6b231837e3d4c557c700ae3d1"
    )


def test_criteria_are_draft_and_cannot_be_deserialized_as_approved_policy():
    from multilang.domain.lexical_identity import ImportantFormCriteria

    criteria = ImportantFormCriteria(**values())
    assert "approval_sha256" not in criteria.model_dump()
    with pytest.raises(ValueError):
        ImportantFormPolicy.model_validate(criteria.model_dump(exclude_computed_fields=True))
    assert criteria.select(()) == ()


def test_scoring_reuses_exact_decimal_rules_and_missing_confidence_is_closed():
    from decimal import Decimal

    from multilang.domain.lexical_identity import ImportantFormCriteria

    criteria = ImportantFormCriteria(**values())
    assert criteria.score_evidence({"frequency": Decimal("0.5")}, 1, Decimal("0.9")) == Decimal(
        "0.50000000"
    )
    assert criteria.score_evidence({"frequency": Decimal("0.5")}, 1, None) is None
    assert criteria.score_evidence({"frequency": Decimal("0.4")}, 1, Decimal(1)) is None
