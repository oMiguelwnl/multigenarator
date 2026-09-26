"""Source-bound lexical decisions must not guess readings or approve contexts."""

import copy

import pytest


def evidence():
    return {
        "word": "长", "flags": ["multiple-readings"],
        "frequency_candidate": {"rank": "60", "level": "1", "source_rank": "75"},
        "generated": {"pinyin": "zhǎng", "traditional": "長"},
        "cedict": [
            {"traditional": "長", "simplified": "长", "numbered_pinyin": "chang2",
             "glosses": ["long", "length"], "line_sha256": "a" * 64,
             "source_sha256": "c" * 64},
            {"traditional": "長", "simplified": "长", "numbered_pinyin": "zhang3",
             "glosses": ["to grow", "elder"], "line_sha256": "b" * 64,
             "source_sha256": "c" * 64},
        ], "wiktextract": [],
    }


def decision():
    return {"word": "长", "disposition": "lexical", "reason": "Two useful modern readings.",
            "components": [], "senses": [
                {"source_ref": "c0", "gloss_indices": [0], "pos": "ADJ",
                 "label_en": "long in length", "usage": "general"},
                {"source_ref": "c1", "gloss_indices": [0], "pos": "VERB",
                 "label_en": "grow", "usage": "general"},
            ]}


def test_qualification_preserves_distinct_senses_readings_and_parent_level():
    from multilang.services.mandarin_inventory import qualify_decision

    result = qualify_decision(evidence(), decision(), reviewer="fixture-reviewer")
    assert [s["pinyin"] for s in result["senses"]] == ["cháng", "zhǎng"]
    assert len({s["identity"]["lexical_identity_id"] for s in result["senses"]}) == 2
    assert all(s["frequency_level"] == 1 for s in result["senses"])
    assert result["frequency_rank"] == 60
    assert result["pronunciation_context_reviewed"] is False
    assert result["independent_human_review"] is False
    assert result["source_evidence_sha256"]


@pytest.mark.parametrize("change", [
    {"source_ref": "c99"}, {"gloss_indices": [99]}, {"pos": "unknown"},
    {"pinyin": "cuò"},
])
def test_invalid_source_pos_or_invented_reading_is_rejected(change):
    from multilang.services.mandarin_inventory import qualify_decision

    value = decision()
    value["senses"][0].update(change)
    with pytest.raises(ValueError):
        qualify_decision(evidence(), value, reviewer="fixture-reviewer")


def test_compositional_form_retains_rank_without_inventing_lexical_identity():
    from multilang.services.mandarin_inventory import qualify_decision

    row = {**evidence(), "word": "两个", "cedict": []}
    value = {"word": "两个", "disposition": "compositional",
             "reason": "Productive numeral plus classifier.",
             "components": ["两", "个"], "senses": []}
    result = qualify_decision(row, value, reviewer="fixture-reviewer")
    assert result["senses"] == []
    assert result["components"] == ["两", "个"]
    assert result["frequency_rank"] == 60
    value["components"] = ["两", "只"]
    with pytest.raises(ValueError, match="components"):
        qualify_decision(row, value, reviewer="fixture-reviewer")


def test_traditional_homograph_or_other_variety_cannot_supply_a_choice():
    from multilang.services.mandarin_inventory import source_choices

    row = {**evidence(), "word": "干", "cedict": [],
           "generated": {"pinyin": "gān", "traditional": "乾"},
           "wiktextract": [
               {"source_word": "乾", "source_record_sha256": "d" * 64,
                "record_pinyin": ["qián"], "source_pos": "noun", "senses": [
                    {"scope": "mandarin-candidate", "glosses": ["Qian trigram"]}]},
               {"source_word": "干", "source_record_sha256": "e" * 64,
                "record_pinyin": ["gān"], "source_pos": "verb", "senses": [
                    {"scope": "other-variety", "glosses": ["dialect use"]}]},
           ]}
    assert source_choices(row) == []


def test_revision_does_not_change_identity_when_only_rationale_changes():
    from multilang.services.mandarin_inventory import qualify_decision

    original = decision()
    revised = copy.deepcopy(original)
    revised["reason"] = "Clarified review rationale."
    a = qualify_decision(evidence(), original, reviewer="first")
    b = qualify_decision(evidence(), revised, reviewer="second")
    assert [s["identity"] for s in a["senses"]] == [s["identity"] for s in b["senses"]]


def test_batch_requires_exact_word_set_without_duplicate_or_silent_omission():
    from multilang.services.mandarin_inventory import validate_batch

    assert len(validate_batch([evidence()], {"decisions": [decision()]})) == 1
    for payload in [{"decisions": []}, {"decisions": [decision(), decision()]}]:
        with pytest.raises(ValueError, match="word set"):
            validate_batch([evidence()], payload)


def test_reordering_dictionary_records_does_not_change_identity():
    from multilang.services.mandarin_inventory import qualify_decision

    row, value = evidence(), decision()
    first = qualify_decision(row, value, reviewer="test")
    row["cedict"].reverse()
    for sense in value["senses"]:
        sense["source_ref"] = {"c0": "c1", "c1": "c0"}[sense["source_ref"]]
    second = qualify_decision(row, value, reviewer="test")
    assert [s["identity"] for s in first["senses"]] == [s["identity"] for s in second["senses"]]


def test_record_wide_multiple_readings_are_not_assigned_to_each_wiktionary_sense():
    from multilang.services.mandarin_inventory import source_choices

    row = {**evidence(), "cedict": [], "wiktextract": [{
        "source_word": "长", "source_record_sha256": "d" * 64,
        "source_pos": "verb", "record_pinyin": ["cháng", "zhǎng"],
        "senses": [{"scope": "mandarin-candidate", "glosses": ["grow"]}],
    }]}
    assert source_choices(row) == []


def test_homographic_traditional_reading_must_match_the_simplified_pair():
    from multilang.services.mandarin_inventory import source_choices

    row = {**evidence(), "word": "干", "cedict": [{
        "traditional": "乾", "simplified": "干", "numbered_pinyin": "gan1",
        "glosses": ["dry"], "line_sha256": "a" * 64,
    }], "wiktextract": [{
        "source_word": "乾", "source_record_sha256": "d" * 64,
        "source_pos": "noun", "record_pinyin": ["qián"],
        "senses": [{"scope": "mandarin-candidate", "glosses": ["Qian trigram"]}],
    }]}
    assert [c["source_kind"] for c in source_choices(row)] == ["cc-cedict"]


def test_surname_gloss_cannot_silently_become_adverb():
    from multilang.services.mandarin_inventory import qualify_decision

    row, value = evidence(), decision()
    row["cedict"][0]["glosses"] = ["surname Ye"]
    value["senses"] = [{"source_ref": "c0", "gloss_indices": [0], "pos": "ADV"}]
    with pytest.raises(ValueError, match="surname"):
        qualify_decision(row, value, reviewer="test")


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(production_eligible=True),
    lambda d: d["senses"][0].update(gloss_indices=[0, 0]),
    lambda d: d["senses"][0].update(source_record_sha256="e" * 64),
    lambda d: d["senses"][0].update(pos="ADV", invented_field="true"),
])
def test_closed_decisions_reject_duplicates_extra_fields_and_changed_sources(mutation):
    from multilang.services.mandarin_inventory import qualify_decision

    value = decision()
    mutation(value)
    with pytest.raises(ValueError):
        qualify_decision(evidence(), value, reviewer="test")


def test_batch_validates_every_sense_instead_of_only_word_membership():
    from multilang.services.mandarin_inventory import validate_batch

    value = decision()
    value["senses"][0]["gloss_indices"] = [999]
    with pytest.raises(ValueError, match="gloss_indices"):
        validate_batch([evidence()], {"decisions": [value]})


def test_wiktionary_senses_with_same_gloss_index_retain_distinct_stable_identities():
    from multilang.services.mandarin_inventory import qualify_decision, source_choices

    row = {**evidence(), "cedict": [], "wiktextract": [{
        "source_word": "长", "source_record_sha256": "d" * 64,
        "source_pos": "verb", "record_pinyin": ["zhǎng"],
        "senses": [
            {"scope": "mandarin-candidate", "source_sense_id": "grow", "glosses": ["grow"]},
            {"scope": "mandarin-candidate", "source_sense_id": "increase", "glosses": ["increase"]},
        ],
    }]}
    value = {**decision(), "senses": [
        {"source_ref": choice["source_ref"], "gloss_indices": [0], "pos": "VERB"}
        for choice in source_choices(row)
    ]}
    first = qualify_decision(row, value, reviewer="test")
    assert len({s["identity"]["lexical_identity_id"] for s in first["senses"]}) == 2
    row["wiktextract"][0]["senses"].reverse()
    second = qualify_decision(row, value, reviewer="test")
    assert [s["identity"] for s in first["senses"]] == [s["identity"] for s in second["senses"]]


@pytest.mark.parametrize("label", [None, 123, "x" * 513])
def test_sense_labels_must_be_bounded_text_without_silent_truncation(label):
    from multilang.services.mandarin_inventory import qualify_decision

    value = decision()
    value["senses"][0]["label_en"] = label
    with pytest.raises(ValueError, match="sense label"):
        qualify_decision(evidence(), value, reviewer="test")
