"""Published lemma rates remain source-scoped, not card or coverage claims."""

import importlib
import importlib.util
from copy import deepcopy

import pytest

MODULE = "multilang.services.vocabulary_published_frequency"
HEAD = "\t".join(
    [
        "1_Mot",
        "2_Phono",
        "3_Phono_IPA",
        "4_Lemme",
        "5_Cgram",
        "6_CgramOrtho",
        "7_Genre",
        "8_Nombre",
        "9_InfoVER",
        "10_FreqMot",
        "11_FreqOrtho",
        "12_FreqLemme",
        "13_CDOrtho",
        "14_IsLem",
    ]
)


def api():
    assert importlib.util.find_spec(MODULE), "published frequency parser implementation missing"
    return importlib.import_module(MODULE)


def lex(form="chats", lemma="chat", pos="NOM", freq="12.50"):
    return "\t".join([form, "", "", lemma, pos, pos, "m", "p", "", "1", "1", freq, "", "0"])


def bnc(lemma="cat", pos="NoC", marker="%", value="12"):
    return "\t".join(["", lemma, pos, marker, value, "90", "0.95"])


def ident(i="a", lemma="chat", pos="NOUN", lang="fr"):
    return dict(identity_id=i, lemma=lemma, pos=pos, language=lang, final_frequency_rank=None)


def test_repeated_lemma_rate_is_not_summed_and_competition_ties_are_preserved():
    p = api().parse_lexique410(
        HEAD
        + "\n"
        + lex()
        + "\n"
        + lex("chat")
        + "\n"
        + lex("chien", "chien", freq="12.50")
        + "\n"
        + lex("arbre", "arbre", freq="2")
    )
    assert [(r["lemma"], r["frequency_per_million"], r["source_rank"]) for r in p["entries"]] == [
        ("chat", "12.5", 1),
        ("chien", "12.5", 1),
        ("arbre", "2", 3),
    ]
    assert p["entries"][0]["source_lines"] == [2, 3]
    assert p["frequency_unit"] == "published_occurrences_per_million"
    assert not p["is_coverage_measurement"] and not p["general_frequency_certified"]


def test_conflicting_lemma_rates_are_quarantined_not_maximized():
    p = api().parse_lexique410(HEAD + "\n" + lex() + "\n" + lex("chat", freq="14"))
    assert p["entries"] == []
    assert p["quarantined_groups"][0]["reason"] == "conflicting_published_lemma_rates"
    assert p["quarantined_groups"][0]["values"] == ["12.5", "14"]


def test_invalid_pos_misalignment_is_accounted_without_guessing():
    p = api().parse_lexique410(HEAD + "\n" + lex("feeder", "m", "s", "") + "\n" + lex(pos="CON"))
    assert p["entries"] == []
    assert p["excluded_counts"]["unmapped_or_ambiguous_source_pos"] == 2


def test_same_lemma_in_different_pos_is_kept_separate():
    p = api().parse_lexique410(
        HEAD
        + "\n"
        + lex("orange", "orange", freq="12")
        + "\n"
        + lex("orange", "orange", "ADJ", "5")
    )
    assert {(r["pos"], r["frequency_per_million"]) for r in p["entries"]} == {
        ("NOUN", "12"),
        ("ADJ", "5"),
    }


def test_colliding_source_subclasses_are_not_summed_or_selected():
    p = api().parse_lexique410(
        HEAD + "\n" + lex("que", "que", "PRO:rel", "12") + "\n" + lex("que", "que", "PRO:int", "5")
    )
    assert p["entries"] == []
    assert p["quarantined_groups"][0]["reason"] == "multiple_source_classes_for_same_inventory_key"


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-2", "bad"])
def test_nonfinite_negative_or_invalid_rates_fail(bad):
    with pytest.raises(ValueError, match="rate"):
        api().parse_lexique410(HEAD + "\n" + lex(freq=bad))


def test_lexique_header_and_row_shape_are_strict():
    with pytest.raises(ValueError, match="header"):
        api().parse_lexique410("Mot\tLemme\nchat\tchat")
    with pytest.raises(ValueError, match="columns"):
        api().parse_lexique410(HEAD + "\nchat\tchat")


def test_bnc_variant_rows_and_rounded_zero_are_not_added_to_lemma():
    p = api().parse_bnc(
        bnc()
        + "\n"
        + bnc("@", "@", "cats", "9")
        + "\n"
        + bnc("@", "@", "cat", "3")
        + "\n"
        + bnc("rare", "NoC", ":", "0")
    )
    assert len(p["entries"]) == 1 and p["entries"][0]["frequency_per_million"] == "12"
    assert p["excluded_counts"] == {"variant_row": 2, "nonpositive_published_rate": 1}


def test_bnc_ambiguous_classes_and_auxiliary_verb_aggregation_not_bound():
    p = api().parse_bnc(
        "\n".join(
            [
                bnc("be", "Verb"),
                bnc("have", "Verb"),
                bnc("do", "Verb"),
                bnc("all", "DetP"),
                bnc("and", "Conj"),
            ]
        )
    )
    assert not p["entries"]
    assert p["excluded_counts"]["verb_auxiliary_function_not_disambiguated"] == 3


def test_bnc_no_automatic_html_case_or_multiword_rewriting():
    p = api().parse_bnc(
        "\n".join(
            [
                bnc("CAT"),
                bnc("cat"),
                bnc("a_bit", "Adv", ":"),
                bnc("&aacute;", "NoC", ":"),
                bnc("alright*", "Adv", ":"),
            ]
        )
    )
    assert {r["lemma"] for r in p["entries"]} == {"CAT", "cat"}
    assert p["excluded_counts"]["encoded_or_editorially_marked_headword"] == 3


def test_bnc_spoken_written_columns_stay_separate():
    text = "Word\tPoS\t\tFrSp\tRa\tDiSp\t\tLogLi\tFrWr\tRa\tDiWr\n\n\tcat\tNoC\t%\t30\t10\t0.9\t+\t12.0\t4\t90\t0.8"
    sp = api().parse_bnc(text, modality="spoken")
    wr = api().parse_bnc(text, modality="written")
    assert sp["entries"][0]["frequency_per_million"] == "30"
    assert wr["entries"][0]["frequency_per_million"] == "4"
    assert sp["publication_cutoff_per_million"] == 160


@pytest.mark.parametrize(
    "text", [bnc("cat", "@"), bnc("@", "NoC"), bnc(marker="?"), bnc() + "\n" + bnc(value="13")]
)
def test_bnc_rejects_invalid_markers_or_duplicate_headword_keys(text):
    with pytest.raises(ValueError):
        api().parse_bnc(text)


def test_bounds_are_enforced():
    with pytest.raises(ValueError, match="limit"):
        api().parse_bnc(bnc(), max_bytes=2)
    with pytest.raises(ValueError, match="limit"):
        api().parse_bnc(bnc() + "\n" + bnc("dog"), max_rows=1)


def test_bindings_share_key_without_summing_for_each_sense_and_preserve_input():
    p = api().parse_lexique410(HEAD + "\n" + lex())
    rows = [ident(), ident("b"), ident("c", "CHAT"), ident("d", "chat", "VERB")]
    original = deepcopy(rows)
    result = api().bind_published_frequency(rows, p)
    assert rows == original
    assert result["matched_identity_rows"] == 2 and result["unmatched_identity_rows"] == 2
    assert result["matched_source_keys"] == 1
    assert result["bindings"][0]["identity_ids"] == ["a", "b"]
    assert result["bindings"][0]["final_frequency_rank"] is None
    assert (
        result["general_frequency_certified"] is False
        and result["coverage_90_percent_verified"] is False
    )
    assert (
        result["bindings"][0]["frequency_scope"]
        == "aggregate_lemma_source_class_not_individual_sense"
    )


def test_binding_rejects_duplicate_identity_or_wrong_language():
    p = api().parse_lexique410(HEAD + "\n" + lex())
    with pytest.raises(ValueError, match="duplicate"):
        api().bind_published_frequency([ident(), ident()], p)
    with pytest.raises(ValueError, match="language"):
        api().bind_published_frequency([ident(lang="en")], p)


def test_lexique_missing_lemma_is_quarantined_not_inferred_from_form():
    result = api().parse_lexique410(HEAD + "\n" + lex("bin", "", "ADJ", "0.728"))
    assert result["entries"] == []
    assert result["excluded_counts"] == {"invalid_source_lemma": 1}
    assert result["excluded_examples"][0]["line"] == 2


def test_bnc_actual_leading_tab_header_and_editorial_rate_flags_are_not_guessed():
    header = "\tWord\tPoS\t\tFrSp\tRa\tDiSp\t\tLogLi\tFrWr\tRa\tDiWr"
    ordinary = "\tcat\tNoC\t%\t30\t10\t0.9\t+\t12.0\t4\t90\t0.8"
    marked = "\tsit\tVerb\t%\t418\t10\t0.84#\t+\t484.4&&\t287#\t90\t0.89#"
    variant = "\t@\t@\tlies\t9#\t10\t0.82&&\t-\t390.8\t44#\t90\t0.94#"
    for modality in ("spoken", "written"):
        result = api().parse_bnc("\n".join((header, ordinary, marked, variant)), modality=modality)
        assert [r["lemma"] for r in result["entries"]] == ["cat"]
        assert result["excluded_counts"] == {"editorially_marked_rate": 1, "variant_row": 1}


def test_bnc_whitespace_separator_is_not_a_record():
    result = api().parse_bnc(" \t \n" + bnc())
    assert result["source_rows"] == 1
    assert len(result["entries"]) == 1


def test_bnc_single_empty_trailing_column_is_harmless_but_nonempty_is_rejected():
    result = api().parse_bnc(bnc() + "\t")
    assert len(result["entries"]) == 1
    with pytest.raises(ValueError, match="columns"):
        api().parse_bnc(bnc() + "\textra")


@pytest.mark.parametrize("bad", ["1e999999999", "1e-999999999", "1000001", "0." + "1" * 50])
def test_pathological_or_out_of_unit_rates_are_rejected_before_formatting(bad):
    with pytest.raises(ValueError, match="rate"):
        api().parse_lexique410(HEAD + "\n" + lex(freq=bad))
