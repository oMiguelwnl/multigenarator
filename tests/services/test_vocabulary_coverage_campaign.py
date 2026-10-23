"""Coverage must not turn missing evidence into admitted vocabulary."""

import hashlib
import importlib.util
import json

import pytest


def api():
    name = "multilang.services.vocabulary_coverage_campaign"
    assert importlib.util.find_spec(name) is not None, "Coverage campaign service is missing"
    return importlib.import_module(name)


def unit(lemma="go", pos="VERB", decision="include", uid="u1", language="en"):
    return {
        "language": language,
        "review_unit_id": uid,
        "decision": decision,
        "source_group": {
            "lemma": lemma,
            "pos": pos,
            "sense_candidates": [
                {"candidate_id": uid + ":sense", "source_record_sha256": "a" * 64}
            ],
        },
        "imported_review": {
            "display": lemma,
            "pos": pos,
            "selected_candidate_ids": [uid + ":sense"] if decision == "include" else [],
        },
    }


def token(form="went", lemma="go", pos="VERB", i="1", doc="d1"):
    return {
        "form": form,
        "lemma": lemma,
        "pos": pos,
        "token_id": i,
        "document_id": doc,
        "sentence_id": "s1",
        "kind": "word",
    }


def test_only_selected_candidates_enter_index_and_missing_annotations_remain():
    m = api()
    index = m.build_index([unit(), unit("maybe", "ADV", "uncertain", "u2")])
    result = m.measure(
        index,
        "en",
        [token(), token("maybe", "maybe", "ADV", "2"), token("unknown", None, None, "3")],
    )
    assert result["counts"]["denominator"] == 3
    assert result["counts"]["exact_matches"] == 1
    assert {g["category"] for g in result["gaps"]} == {"pending_review", "missing_annotation"}
    assert result["coverage_90_percent_verified"] is False


def test_nfc_preserves_case_and_no_suffix_or_compound_guessing():
    m = api()
    index = m.build_index(
        [
            unit("été", "NOUN"),
            unit("I", "PRON", uid="u2"),
            unit("수석", "NOUN", uid="u3", language="ko"),
        ]
    )
    r = m.measure(
        index,
        "en",
        [
            token("été", "e\u0301te\u0301", "NOUN"),
            token("i", "i", "ADP", "2"),
            token("going", "going", "VERB", "3"),
        ],
    )
    assert r["counts"]["exact_matches"] == 1
    r = m.measure(index, "ko", [token("수석은", "수석+은", "NOUN")])
    assert r["counts"]["exact_matches"] == 0
    assert r["gaps"][0]["category"] == "annotation_structure"


def test_pos_mismatch_is_not_missing_vocabulary_and_exclusions_are_counted():
    m = api()
    index = m.build_index([unit("be", "VERB")])
    rows = [
        token("is", "be", "AUX"),
        token(".", ".", "PUNCT", "2"),
        token("London", "London", "PROPN", "3"),
        token("42", "42", "NUM", "4"),
        token("two", "two", "NUM", "5"),
    ]
    r = m.measure(index, "en", rows)
    assert r["counts"]["denominator"] == 2
    assert r["counts"]["lemma_matches"] == 1
    assert r["counts"]["exact_matches"] == 0
    assert r["counts"]["excluded_punctuation"] == 1
    assert {g["category"] for g in r["gaps"]} == {"pos_mismatch", "candidate_absent"}


def test_duplicate_occurrence_fails_and_empty_denominator_is_null():
    m = api()
    index = m.build_index([unit()])
    with pytest.raises(ValueError, match="duplicate occurrence"):
        m.measure(index, "en", [token(), token()])
    assert m.measure(index, "en", [token(".", ".", "PUNCT")])["exact_percent"] is None


def test_include_without_selected_evidence_fails():
    m = api()
    row = unit()
    row["imported_review"]["selected_candidate_ids"] = []
    with pytest.raises(ValueError, match="selected"):
        m.build_index([row])


def test_derived_candidate_pos_and_addition_provenance_are_respected():
    m = api()
    row = unit("att", "CCONJ", language="sv")
    row["resolved_content"] = {
        "resolved_candidates": [
            {
                "disposition": "retained",
                "lemma": "att",
                "pos": "SCONJ",
                "source_candidate_id": "u1:sense",
            },
            {
                "disposition": "quarantined",
                "lemma": "x",
                "pos": "NOUN",
                "source_candidate_id": "bad",
            },
        ]
    }
    index = m.build_index([row])
    r = m.measure(index, "sv", [token("att", "att", "SCONJ")])
    assert r["counts"]["exact_matches"] == 1


def test_holdout_never_exports_gaps_or_expansion_tasks():
    m = api()
    r = m.measure(
        m.build_index([unit()]), "en", [token("absent", "absent", "NOUN")], role="holdout"
    )
    assert r["gaps"] == []
    assert r["counts"]["denominator"] == 1
    assert r["coverage_90_percent_verified"] is False


def test_gap_dispersion_counts_documents_without_creating_ranks():
    m = api()
    r = m.measure(
        m.build_index([unit()]),
        "en",
        [
            token("new", "new", "ADJ", "1", "a"),
            token("new", "new", "ADJ", "2", "a"),
            token("new", "new", "ADJ", "1", "b"),
        ],
    )
    gap = r["gaps"][0]
    assert (gap["occurrences"], gap["documents"]) == (3, 2)
    assert gap["decision"] == "needs_review"
    assert gap["frequency_rank"] is None


def test_reviewed_link_requires_existing_target_and_exact_pos():
    m = api()
    index = m.build_index([unit("be", "VERB")])
    link = {
        "lemma": "be",
        "pos": "AUX",
        "target_lemma": "be",
        "target_pos": "VERB",
        "evidence_id": "review:1",
    }
    r = m.measure(index, "en", [token("is", "be", "AUX")], links=[link])
    assert r["counts"]["exact_matches"] == 0
    assert r["counts"]["compatible_matches"] == 1
    assert (
        m.measure(index, "en", [token("be", "be", "NOUN")], links=[link])["counts"][
            "compatible_matches"
        ]
        == 0
    )
    link["target_lemma"] = "absent"
    with pytest.raises(ValueError, match="target"):
        m.measure(index, "en", [token()], links=[link])


def test_corpus_contract_rejects_seen_holdout():
    m = api()
    with pytest.raises(ValueError, match="holdout"):
        m.CorpusSpec.model_validate(
            {
                "language": "en",
                "label": "sample",
                "path": "x",
                "sha256": "a" * 64,
                "format": "reference-jsonl",
                "modality": "written",
                "role": "holdout",
                "previously_inspected": True,
                "version": "1",
                "license": "test",
            }
        )


def spec(path, **kwargs):
    return api().CorpusSpec.model_validate(
        {
            "language": "en",
            "label": "fixture",
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "format": "reference-jsonl",
            "modality": "written",
            "version": "fixture-1",
            "license": "test",
            **kwargs,
        }
    )


def test_reference_reader_checks_hash_language_and_token_identity(tmp_path):
    m = api()
    path = tmp_path / "corpus.jsonl"
    row = {
        "language": "en",
        "document_id": "d1",
        "sentence_id": "s1",
        "text": "went",
        "source_sha256": "b" * 64,
        "tokens": [{"index": 1, "text": "went", "lemma": "go", "pos": "VERB"}],
    }
    path.write_text(json.dumps(row) + "\n")
    config = spec(path)
    assert list(m.corpus_tokens(config))[0]["token_id"] == "1"
    path.write_text(json.dumps({**row, "language": "fr"}) + "\n")
    with pytest.raises(ValueError, match="checksum"):
        list(m.corpus_tokens(config))
    with pytest.raises(ValueError, match="language"):
        list(m.corpus_tokens(spec(path)))


def test_holdout_cannot_reuse_exposed_source_or_sentences(tmp_path):
    m = api()
    path = tmp_path / "corpus.jsonl"
    path.write_text("{}\n")
    c = spec(path, role="holdout", previously_inspected=False)
    with pytest.raises(ValueError, match="exposed"):
        m.validate_corpora([c], exposed_hashes={c.sha256})
    registry = m.OverlapGuard()
    list(registry.observe("en", "diagnostic", [token()]))
    with pytest.raises(ValueError, match="overlap"):
        list(registry.observe("en", "holdout", [token(doc="different-id")]))


def test_restricted_annotation_link_never_spills_to_other_forms():
    m = api()
    link = {
        "lemma": "be",
        "pos": "AUX",
        "target_lemma": "be",
        "target_pos": "VERB",
        "evidence_id": "r1",
        "restrictions": {"form": ["is"]},
    }
    r = m.measure(
        m.build_index([unit("be", "VERB")]),
        "en",
        [token("is", "be", "AUX"), token("was", "be", "AUX", "2")],
        links=[link],
    )
    assert r["counts"]["compatible_matches"] == 1


def test_conllu_counts_components_not_range_and_keeps_missing_lemma(tmp_path):
    m = api()
    path = tmp_path / "corpus.conllu"
    path.write_text(
        "# sent_id = s1\n# text = can't\n"
        "1-2\tcan't\t_\t_\t_\t_\t_\t_\t_\t_\n"
        "1\tca\tcan\tAUX\t_\t_\t0\troot\t_\t_\n"
        "2\tn't\t_\tPART\t_\t_\t1\tadvmod\t_\t_\n\n"
    )
    rows = list(m.corpus_tokens(spec(path, format="conllu")))
    assert len(rows) == 2
    assert rows[1]["lemma"] is None


def test_token_reader_missing_pos_is_not_excluded_by_legacy_flag(tmp_path):
    m = api()
    path = tmp_path / "corpus.jsonl"
    path.write_text(json.dumps({**token(pos=None), "lexical_occurrence_eligible": False}) + "\n")
    r = m.measure(m.build_index([unit()]), "en", m.corpus_tokens(spec(path, format="token-jsonl")))
    assert r["counts"]["denominator"] == 1


def test_atomic_campaign_rejects_stale_snapshot_hash_without_output(tmp_path):
    m = api()
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "manifest.json").write_text("{}\n")
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "snapshot": str(snapshot),
                "snapshot_manifest_sha256": "a" * 64,
                "corpora": [],
                "exposed_hashes": [],
            }
        )
    )
    destination = tmp_path / "result"
    with pytest.raises(ValueError, match="checksum|hash"):
        m.run_campaign(config, hashlib.sha256(config.read_bytes()).hexdigest(), destination)
    assert not destination.exists()


def mini_snapshot(path):
    from multilang.domain.lexical_identity import canonical_sha256

    path.mkdir()
    (path / "inventory").mkdir()
    row = {
        **unit(),
        "record_id": canonical_sha256(["en", "u1"]),
        "production_eligible": False,
        "generation_status": "deferred_by_user",
    }
    inventory = path / "inventory/en.jsonl"
    inventory.write_text(json.dumps(row) + "\n")
    manifest = {
        "schema_version": "vocabulary-selection-snapshot-1",
        "production_eligible": False,
        "generation_status": "deferred_by_user",
        "total_records": 1,
        "languages": {
            "en": {"include": 1, "exclude": 0, "uncertain": 0, "unreviewed": 0, "quarantined": 0}
        },
        "files": {"inventory/en.jsonl": hashlib.sha256(inventory.read_bytes()).hexdigest()},
    }
    manifest["snapshot_id"] = canonical_sha256(manifest)
    (path / "manifest.json").write_text(json.dumps(manifest))
    return hashlib.sha256((path / "manifest.json").read_bytes()).hexdigest()


def test_campaign_real_snapshot_writes_review_packet_and_binds_outputs(tmp_path):
    m = api()
    snapshot = tmp_path / "snapshot"
    digest = mini_snapshot(snapshot)
    path = tmp_path / "tokens.jsonl"
    path.write_text(json.dumps(token()) + "\n" + json.dumps(token("new", "new", "ADJ", "2")) + "\n")
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "snapshot": str(snapshot),
                "snapshot_manifest_sha256": digest,
                "corpora": [spec(path, format="token-jsonl").model_dump(mode="json")],
            }
        )
    )
    destination = tmp_path / "result"
    result = m.run_campaign(config, hashlib.sha256(config.read_bytes()).hexdigest(), destination)
    assert result["results"][0]["exact_percent"] == 50
    assert result["languages"]["en"]["missing_modalities"] == ["spoken"]
    packet = json.loads((destination / "en/first-review-packet.json").read_text())
    assert packet[0]["lemma"] == "new"
    for name, sha in json.loads((destination / "manifest.json").read_text())["files"].items():
        assert hashlib.sha256((destination / name).read_bytes()).hexdigest() == sha
    with pytest.raises(ValueError, match="already exists"):
        m.run_campaign(config, hashlib.sha256(config.read_bytes()).hexdigest(), destination)


def test_campaign_annotation_links_require_bound_evidence(tmp_path):
    m = api()
    snapshot = tmp_path / "snapshot"
    digest = mini_snapshot(snapshot)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "snapshot": str(snapshot),
                "snapshot_manifest_sha256": digest,
                "corpora": [],
                "links": {"en": [{"evidence_id": "absent"}]},
            }
        )
    )
    with pytest.raises(ValueError, match="evidence"):
        m.run_campaign(config, hashlib.sha256(config.read_bytes()).hexdigest(), tmp_path / "result")


def test_annotation_restrictions_reject_strings_and_unknown_predicates():
    m = api()
    link = {
        "lemma": "go",
        "pos": "AUX",
        "target_lemma": "go",
        "target_pos": "VERB",
        "evidence_id": "r",
        "restrictions": {"form": "went"},
    }
    with pytest.raises(ValueError, match="restriction"):
        m.measure(m.build_index([unit()]), "en", [token()], links=[link])
    link["restrictions"] = {"typo": ["went"]}
    with pytest.raises(ValueError, match="restriction"):
        m.measure(m.build_index([unit()]), "en", [token()], links=[link])


def test_conllu_genre_filter_deduplication_and_original_pos(tmp_path):
    m = api()
    path = tmp_path / "sample.conllu"

    def sentence(sid, genre):
        return (
            f"# sent_id = {sid}\n# genre = {genre}\n"
            "1\twent\tgo\tVERB\tVBD\t_\t0\troot\t_\tLang=en\n\n"
        )

    path.write_text(sentence("s1", "spoken") + sentence("s2", "spoken") + sentence("s3", "written"))
    rows = list(
        m.corpus_tokens(
            spec(path, format="conllu", filter_genre="spoken", deduplicate_analysis_variants=True)
        )
    )
    assert len(rows) == 1
    assert rows[0]["original_pos"] == "VBD"


def test_annotation_link_rejects_stale_target_review_binding():
    m = api()
    link = {
        "lemma": "go",
        "pos": "AUX",
        "target_lemma": "go",
        "target_pos": "VERB",
        "evidence_id": "r",
        "required_review_units": ["old-unit"],
    }
    with pytest.raises(ValueError, match="review binding"):
        m.measure(m.build_index([unit()]), "en", [token()], links=[link])


def test_invalid_pos_remains_missing_annotation_in_denominator():
    m = api()
    result = m.measure(m.build_index([unit()]), "en", [token(pos="malformed")])
    assert result["counts"]["denominator"] == 1
    assert result["gaps"][0]["category"] == "missing_annotation"


def test_pending_gap_links_back_to_the_existing_assignment():
    m = api()
    row = {
        **unit(decision="uncertain"),
        "session_id": "en-0001",
        "source_binding": {"packet_sha256": "a" * 64, "source_index": 2},
    }
    result = m.measure(m.build_index([row]), "en", [token()])
    ref = result["gaps"][0]["source_review_units"][0]
    assert (ref["review_unit_id"], ref["session_id"]) == ("u1", "en-0001")
    assert ref["source_binding"]["source_index"] == 2


def test_swedish_source_word_and_empty_transcription_marker_are_distinct(tmp_path):
    m = api()
    word = token()
    del word["kind"]
    word["token_kind"] = "source_word_or_punctuation"
    marker = {
        **token("", None, None, "2"),
        "kind": "transcription_marker",
        "lexical_occurrence_eligible": False,
    }
    path = tmp_path / "tokens.jsonl"
    path.write_text(json.dumps(word) + "\n" + json.dumps(marker) + "\n")
    result = m.measure(
        m.build_index([unit()]), "en", m.corpus_tokens(spec(path, format="token-jsonl"))
    )
    assert result["counts"]["denominator"] == 1
    assert result["counts"]["exact_matches"] == 1
    assert result["counts"]["excluded_speech_event"] == 1


def test_punctuation_kind_does_not_count_as_a_speech_event():
    m = api()
    row = {**token(".", ".", "PUNCT"), "kind": "punctuation"}
    r = m.measure(m.build_index([unit()]), "en", [row])
    assert r["counts"]["excluded_punctuation"] == 1


def test_bound_derived_review_can_resolve_a_historical_uncertain_selection():
    m = api()
    row = unit("min", "ADJ", decision="uncertain", language="da")
    row["decision"] = "include"
    row["resolved_content"] = {
        "resolved_candidates": [
            {
                "disposition": "retained",
                "lemma": "min.",
                "pos": "ADJ",
                "source_candidate_id": "u1:sense",
            }
        ]
    }
    index = m.build_index([row])
    assert ("da", "min.", "ADJ") in index.keys
    assert ("da", "min", "ADJ") not in index.keys


@pytest.mark.parametrize(
    "evidence",
    [
        {"source_evidence": [{"url": "https://example.org/dictionary/1"}]},
        {"evidence": [{"url": "https://example.org/dictionary/1"}]},
        {
            "evidence_ids": ["review-1"],
            "source_lexical_identifiers": [
                {"dictionary": "test", "entry_id": "1", "url": "https://example.org/dictionary/1"}
            ],
        },
    ],
)
def test_official_supplement_evidence_variants_are_indexed(evidence):
    m = api()
    row = {
        **unit("i", "ADP", language="nb"),
        "source_group": None,
        "imported_review": None,
        "supplemental_identity": {
            "lemma": "i",
            "pos": "ADP",
            "decision": "accepted_in_preparation_version",
            **evidence,
        },
    }
    assert ("nb", "i", "ADP") in m.build_index([row]).keys
    row["supplemental_identity"]["decision"] = "pending"
    with pytest.raises(ValueError, match="addition"):
        m.build_index([row])


def test_missing_pos_never_matches_an_unresolved_inventory_pos():
    m = api()
    index = m.build_index([unit("min", None)])
    result = m.measure(index, "en", [token("min", "min", None)])
    assert result["counts"]["exact_matches"] == 0
    assert result["counts"]["denominator"] == 1


def test_derived_identities_are_bound_to_their_original_source_candidates():
    m = api()
    row = unit("jewel", "NOUN")
    row["resolved_content"] = {
        "resolved_candidates": [
            {
                "disposition": "retained",
                "lemma": "jewels",
                "pos": "NOUN",
                "source_candidate_id": "u1:sense",
            }
        ],
        "derived_identities": [
            {
                "lemma": "jewel",
                "pos": "NOUN",
                "source_candidate_ids": ["u1:sense"],
                "evidence": [{"type": "unit_evidence_reference"}],
            }
        ],
    }
    index = m.build_index([row])
    assert ("en", "jewel", "NOUN") in index.keys
    row["resolved_content"]["derived_identities"][0]["source_candidate_ids"] = ["unknown"]
    with pytest.raises(ValueError, match="derived identity"):
        m.build_index([row])


def preparation_unit(lemma="go", pos="VERB", decision="include", uid="u1", language="en"):
    row = unit(lemma, pos, decision, uid, language)
    row["source_group"].update(entry_id=uid, review_unit_id=uid, forms_for_review=[], readings=[])
    row["imported_review"].update(
        entry_id=uid, review_unit_id=uid, decision=decision, selected_forms=[]
    )
    return row


def preparation_form_case():
    from multilang.services.vocabulary_adjudication import _hash
    from multilang.services.vocabulary_finalization import consolidate
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    raw_parent = dict(word="žlutý", lang_code="cs", pos="adj", senses=[dict(glosses=["yellow"])])
    raw_form = dict(
        word="žlutých",
        lang_code="cs",
        pos="adj",
        senses=[dict(glosses=["genitive/locative plural of žlutý"])],
    )
    rows = []
    for raw, uid, decision in [(raw_parent, "parent", "include"), (raw_form, "form", "uncertain")]:
        row = preparation_unit(raw["word"], "ADJ", decision, uid, "cs")
        cid = "candidate:" + _hash(dict(record=_hash(raw), sense=0))
        row["source_group"]["sense_candidates"] = [
            dict(candidate_id=cid, source_record_sha256=_hash(raw))
        ]
        row["imported_review"]["selected_candidate_ids"] = [cid] if decision == "include" else []
        rows.append(row)
    parent = consolidate([rows[0]], language="cs")["identities"][0]
    link = dict(
        source_candidate_id=rows[1]["source_group"]["sense_candidates"][0]["candidate_id"],
        source_record=raw_form,
        source_record_sha256=_hash(raw_form),
        source_sense_index=0,
        parent_identity_id=parent["identity_id"],
        parent_candidate_id=parent["senses"][0]["candidate_id"],
        parent_record=raw_parent,
        parent_record_sha256=_hash(raw_parent),
        parent_relation_quote="genitive/locative plural of žlutý",
        features=["plural", "genitive-or-locative"],
        rationale="Explicit dictionary form relation bound to the exact retained parent sense.",
    )
    return rows[0], prepare_form_resolution(rows[1], [link], {parent["identity_id"]: parent})


def preparation_api():
    m = api()
    assert callable(getattr(m, "build_preparation_index", None)), (
        "Finalization-aware index is missing"
    )
    return m


def test_preparation_index_validates_form_links_without_promoting_forms_to_lemmas():
    import copy

    m = preparation_api()
    rows = list(preparation_form_case())
    before = copy.deepcopy(rows)
    index = m.build_preparation_index(iter(rows))
    assert rows == before
    assert dict(index.keys) == {("cs", "žlutý", "ADJ"): {"parent", "form"}}
    assert ("cs", "žlutých") not in index.lemmas
    assert index.units["cs", "include"] == 2
    assert index.source_refs["cs", "žlutých"][0]["review_unit_id"] == "form"
    result = m.measure(
        index, "cs", [token("žlutých", "žlutý", "ADJ"), token("žlutých", "žlutých", "ADJ", "2")]
    )
    assert result["counts"]["denominator"] == 2
    assert result["counts"]["exact_matches"] == 1
    assert result["coverage_90_percent_verified"] is False


@pytest.mark.parametrize("damage", ["parent_absent", "source_tampered", "duplicate_unit"])
def test_preparation_index_rejects_broken_parent_evidence(damage):
    m = preparation_api()
    parent, form = preparation_form_case()
    rows = [parent, form]
    if damage == "parent_absent":
        rows = [form]
    elif damage == "source_tampered":
        form["resolved_content"]["form_only_associations"][0]["source_record"]["word"] = "forged"
    else:
        rows.append(parent)
    with pytest.raises(ValueError):
        m.build_preparation_index(rows)


def test_preparation_index_adapts_nordic_resolutions_and_skips_documentary_classes():
    m = preparation_api()
    row = preparation_unit("source", "NOUN", uid="nordic", language="da")
    row["resolved_content"] = dict(
        resolved_candidates=[
            dict(
                source_candidate_id="nordic:sense",
                derived_candidate_id="reading-1",
                lemma="ét",
                pos="NOUN",
                disposition="retained",
                evidence=[{"type": "bound-fixture"}],
            ),
            dict(
                source_candidate_id="nordic:sense",
                derived_candidate_id="reading-2",
                lemma="⌀",
                pos="SYMBOL",
                disposition="retained",
                evidence=[{"type": "bound-fixture"}],
            ),
        ],
        resolved_forms=[],
        unresolved_questions=[],
    )
    index = m.build_preparation_index([row])
    assert dict(index.keys) == {("da", "ét", "NOUN"): {"nordic"}}
    assert ("da", "⌀") not in index.lemmas
    result = m.measure(index, "da", [token("ét", "e\u0301t", "NOUN"), token("⌀", "⌀", "NOUN", "2")])
    assert result["counts"]["exact_matches"] == 1
    assert result["counts"]["lemma_matches"] == 1


def test_preparation_index_preserves_partial_pending_units_without_inventing_pos():
    m = preparation_api()
    row = preparation_unit("maybe", "X", uid="partial")
    row["resolved_content"] = dict(
        resolved_candidates=[
            dict(
                source_candidate_id="partial:sense",
                lemma="maybe",
                pos=None,
                disposition="retained",
                evidence=[{"type": "bound-fixture"}],
            )
        ],
        resolved_forms=[],
        unresolved_questions=[],
    )
    index = m.build_preparation_index([row])
    assert not index.keys
    assert index.units["en", "include"] == 1
    assert index.source_refs["en", "maybe"][0]["decision"] == "include"
    assert index.source_refs["en", "maybe"][0]["preparation_pending"] is True
    result = m.measure(index, "en", [token("maybe", "maybe", "ADV")])
    assert result["gaps"][0]["category"] == "pending_review"


def test_preparation_index_rejects_repeated_language_groups():
    m = preparation_api()
    rows = [
        preparation_unit(uid="a"),
        preparation_unit(uid="b", language="da"),
        preparation_unit(uid="c"),
    ]
    with pytest.raises(ValueError, match="language.*group|group.*language"):
        m.build_preparation_index(iter(rows))


def test_campaign_rejects_unknown_inventory_format_before_creating_output(tmp_path):
    m = api()
    snapshot = tmp_path / "snapshot"
    digest = mini_snapshot(snapshot)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            dict(
                snapshot=str(snapshot),
                snapshot_manifest_sha256=digest,
                corpora=[],
                inventory_format="typo",
            )
        )
    )
    destination = tmp_path / "result"
    with pytest.raises(ValueError, match="inventory format"):
        m.run_campaign(config, hashlib.sha256(config.read_bytes()).hexdigest(), destination)
    assert not destination.exists()


def test_campaign_finalization_snapshot_uses_validated_lexical_identities(tmp_path):
    from multilang.services.vocabulary_finalization import publish_inventory

    m = api()
    source = tmp_path / "source.jsonl"
    source.write_text("\n".join(json.dumps(r) for r in preparation_form_case()) + "\n")
    published = tmp_path / "published"
    publish_inventory(
        inputs=[
            dict(
                language="cs",
                path=str(source),
                sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            )
        ],
        output=published,
    )
    snapshot = published / "snapshot"
    path = tmp_path / "tokens.jsonl"
    path.write_text(json.dumps(token("žlutých", "žlutý", "ADJ")) + "\n")
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            dict(
                snapshot=str(snapshot),
                snapshot_manifest_sha256=hashlib.sha256(
                    (snapshot / "manifest.json").read_bytes()
                ).hexdigest(),
                inventory_format="finalization-snapshot",
                corpora=[spec(path, language="cs", format="token-jsonl").model_dump(mode="json")],
            )
        )
    )
    result = m.run_campaign(
        config, hashlib.sha256(config.read_bytes()).hexdigest(), tmp_path / "result"
    )
    assert result["inventory_format"] == "finalization-snapshot"
    assert result["languages"]["cs"]["selected_lemma_pos_keys"] == 1
    assert result["results"][0]["counts"]["exact_matches"] == 1
    assert result["coverage_90_percent_verified"] is False
    assert result["generation_status"] == "deferred_by_user"
