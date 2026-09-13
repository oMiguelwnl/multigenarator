from decimal import Decimal

import pytest


def test_preflight_preserves_all_forms_and_unknown_cost():
    from multilang.services.qualification_workload import qualification_workload

    report = qualification_workload(headwords=100, observed_forms=450, selected_forms=None)
    assert report.headword_candidates == 100
    assert report.observed_form_candidates == 450
    assert report.selected_form_cards is None
    assert report.expected_card_count is None
    assert report.expected_cost is None
    assert report.provider_calls_executed == 0
    assert "reviewed_importance_selection" in report.blockers


def test_concrete_selected_workload_counts_cache_and_pricing_without_calling_providers():
    from multilang.services.qualification_workload import qualification_workload

    report = qualification_workload(
        headwords=100,
        observed_forms=450,
        selected_forms=400,
        optional_role_cards=7,
        reviewed_grounding_cards=500,
        cached_text_cards=20,
        cached_word_audio=10,
        cached_sentence_audio=9,
        text_request_price=Decimal("0.01"),
        audio_request_price=Decimal("0.002"),
        price_basis="Explicit synthetic per-request test price; not a real tariff",
    )
    assert report.expected_card_count == 507
    assert report.content_units == 500
    assert report.text_requests == 480
    assert report.word_audio_requests == 490
    assert report.sentence_audio_requests == 491
    assert report.expected_cost == Decimal("6.762")
    assert report.price_basis.startswith("Explicit")
    assert report.production_eligible is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"selected_forms": 2, "observed_forms": 1},
        {"cached_word_audio": 999, "selected_forms": 0},
        {"text_request_price": "0.01"},
    ],
)
def test_invalid_or_unattributed_pricing_is_rejected(kwargs):
    from multilang.services.qualification_workload import qualification_workload

    with pytest.raises(ValueError):
        qualification_workload(headwords=100, **kwargs)


def test_optional_reverse_roles_share_content_audio_and_cache_denominators():
    from multilang.services.qualification_workload import qualification_workload

    report = qualification_workload(headwords=10, selected_forms=0, optional_role_cards=10)
    assert report.expected_card_count == 20
    assert (
        report.text_requests == report.word_audio_requests == report.sentence_audio_requests == 10
    )
    with pytest.raises(ValueError):
        qualification_workload(
            headwords=10, selected_forms=0, optional_role_cards=10, cached_word_audio=11
        )
