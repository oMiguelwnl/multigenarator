from multilang.services.vocabulary_preparation_order import order_identities


def test_preparation_order_uses_own_source_priority_and_keeps_linked_forms():
    source = {
        "low": dict(review_unit_id="low", source_group=dict(entry_id="e1", source_priority=20, provisional_order=1)),
        "high": dict(review_unit_id="high", source_group=dict(entry_id="e2", source_priority=1, provisional_order=2)),
        "form": dict(review_unit_id="form", source_group=dict(entry_id="different", source_priority=0, provisional_order=0)),
    }
    identities = [
        dict(identity_id="i1", source_entry_id="e1", review_unit_ids=["low", "form"], senses=[dict(candidate_id="c1")]),
        dict(identity_id="i2", source_entry_id="e2", review_unit_ids=["high"], senses=[dict(candidate_id="c2")]),
    ]
    result = order_identities(identities, source, {"form"})
    assert [row["identity_id"] for row in result] == ["i2", "i1"]
    assert [row["preparation_order"] for row in result] == [1, 2]
    assert result[1]["contains_open_review_units"] is True
    assert result[1]["source_priority_values"] == [20]
    assert result[1]["final_frequency_rank"] is None
    assert result[1]["production_eligible"] is False
    assert identities[0].get("preparation_order") is None
