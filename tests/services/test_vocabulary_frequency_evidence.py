"""Count evidence stays source scoped, bounded and independent of selection."""

import gzip
import hashlib
import importlib
import importlib.util

import pytest

MODULE = "multilang.services.vocabulary_frequency_evidence"


def derive(tmp_path, rows, **kwargs):
    assert importlib.util.find_spec(MODULE), "frequency evidence implementation missing"
    module = importlib.import_module(MODULE)
    path = tmp_path / "source.gz"
    path.write_bytes(gzip.compress("\n".join(rows).encode()))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return module.derive_hrlex_counts(
        path,
        expected_sha256=kwargs.pop("expected_sha256", digest),
        scratch_dir=tmp_path,
        **kwargs,
    )


def row(form="knjige", lemma="knjiga", msd="Ncfpg", pos="NOUN", count=5, relative="0.123"):
    return "\t".join((form, lemma, msd, "_", pos, "_", str(count), relative))


def test_aggregates_attested_tuples_once_with_competition_ties(tmp_path):
    result = derive(
        tmp_path,
        [
            row(),
            row(),
            row("knjiga", count=7),
            row("vidjeti", "vidjeti", "Vmn", "VERB", 12),
            row("nula", "nula", count=0),
        ],
    )
    assert [(r["lemma"], r["upos"], r["count"], r["source_rank"]) for r in result["entries"]] == [
        ("knjiga", "NOUN", 12, 1),
        ("vidjeti", "VERB", 12, 1),
    ]
    assert result["input_rows"] == 5
    assert result["duplicate_rows"] == 1
    assert result["positive_unique_tuples"] == 3
    assert result["frequency_unit"] == "sum_of_attested_wordform_lemma_msd_counts"
    assert result["unique_token_mass_certified"] is False
    assert result["general_frequency_certified"] is False
    assert result["evaluation_holdout"] is False
    assert not list(tmp_path.glob("hrlex-*.sqlite"))


def test_keeps_distinct_analyses_and_reports_mass_without_claiming_disjointness(tmp_path):
    result = derive(tmp_path, [row("test", "a", "N", "NOUN", 4), row("test", "b", "V", "VERB", 9)])
    assert result["attested_tuple_count_sum"] == 13
    assert len(result["entries"]) == 2
    assert result["unique_token_mass_certified"] is False


@pytest.mark.parametrize("change", [dict(count=9), dict(pos="VERB"), dict(count=0)])
def test_rejects_conflicting_duplicate_key(tmp_path, change):
    with pytest.raises(ValueError, match="conflicting tuple"):
        derive(tmp_path, [row(), row(**change)])


def test_exact_duplicate_requires_all_documentary_columns_to_match(tmp_path):
    with pytest.raises(ValueError, match="conflicting tuple"):
        derive(tmp_path, [row(), row(relative="0.124")])


def test_retains_excluded_pos_in_accounting_but_not_rank(tmp_path):
    result = derive(
        tmp_path, [row(), row(",", ",", "Z", "PUNCT", 100), row("x", "x", "X", "_", 10)]
    )
    assert result["attested_tuple_count_sum"] == 115
    assert result["ranked_tuple_count_sum"] == 5
    assert result["excluded_count_by_upos"] == {"PUNCT": 100, "_": 10}
    assert len(result["entries"]) == 1


@pytest.mark.parametrize(
    "bad",
    [
        "bad",
        row(count=-1),
        row(count="1.5"),
        row(relative="NaN"),
        row(relative="Infinity"),
        row(pos="not-upos"),
        row(lemma=""),
    ],
)
def test_rejects_malformed_rows(tmp_path, bad):
    with pytest.raises(ValueError):
        derive(tmp_path, [bad])


def test_rejects_hash_mismatch_before_processing(tmp_path):
    with pytest.raises(ValueError, match="SHA256"):
        derive(tmp_path, [row()], expected_sha256="0" * 64)


@pytest.mark.parametrize(
    "limits",
    [
        dict(max_rows=1),
        dict(max_uncompressed_bytes=5),
        dict(max_compressed_bytes=5),
        dict(max_line_bytes=5),
    ],
)
def test_enforces_resource_limits(tmp_path, limits):
    with pytest.raises(ValueError, match="limit"):
        derive(tmp_path, [row(), row("other")], **limits)


def test_nfc_aggregation_preserves_original_key_without_lowercasing(tmp_path):
    result = derive(
        tmp_path,
        [row("x", "cafe\u0301", count=3), row("y", "café", count=4), row("z", "Café", count=2)],
    )
    assert [(r["lemma"], r["count"]) for r in result["entries"]] == [("café", 7), ("Café", 2)]


def test_unknown_lemma_has_no_imputed_frequency(tmp_path):
    result = derive(tmp_path, [row(count=0)])
    assert result["entries"] == []
    assert result["ranked_tuple_count_sum"] == 0


def test_binds_exact_identity_without_mutation_or_sense_count_duplication(tmp_path):
    evidence = derive(tmp_path, [row()])
    identities = [
        {"language": "hr", "identity_id": "a", "lemma": "knjiga", "pos": "NOUN", "senses": [1, 2]},
        {"language": "hr", "identity_id": "b", "lemma": "knjiga", "pos": "VERB"},
        {"language": "hr", "identity_id": "c", "lemma": "unknown", "pos": "NOUN"},
    ]
    module = importlib.import_module(MODULE)
    assert hasattr(module, "bind_source_counts"), "source binding implementation missing"
    result = module.bind_source_counts(identities, evidence)
    assert result["matched_identity_rows"] == 1
    assert result["unmatched_identity_rows"] == 2
    assert result["matched_unique_lemma_upos"] == 1
    assert result["matched_source_count_sum"] == 5
    binding = result["bindings"][0]
    assert binding["identity_id"] == "a"
    assert binding["source_count"] == 5
    assert binding["sense_frequency"] is None
    assert binding["final_frequency_rank"] is None
    assert "source_count" not in identities[0]


def test_bound_count_is_not_repeated_when_multiple_source_identities_share_key(tmp_path):
    evidence = derive(tmp_path, [row()])
    module = importlib.import_module(MODULE)
    assert hasattr(module, "bind_source_counts"), "source binding implementation missing"
    identities = [
        {"language": "hr", "identity_id": str(i), "lemma": "knjiga", "pos": "NOUN"}
        for i in range(2)
    ]
    result = module.bind_source_counts(identities, evidence)
    assert result["matched_identity_rows"] == 2
    assert result["matched_unique_lemma_upos"] == 1
    assert result["matched_source_count_sum"] == 5


def test_binding_rejects_language_mismatch_and_duplicate_source_keys(tmp_path):
    evidence = derive(tmp_path, [row()])
    module = importlib.import_module(MODULE)
    assert hasattr(module, "bind_source_counts"), "source binding implementation missing"
    with pytest.raises(ValueError, match="language"):
        module.bind_source_counts(
            [{"language": "sh", "identity_id": "a", "lemma": "knjiga", "pos": "NOUN"}], evidence
        )
    evidence["entries"].append(evidence["entries"][0])
    with pytest.raises(ValueError, match="duplicate source"):
        module.bind_source_counts([], evidence)
