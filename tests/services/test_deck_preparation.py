"""Reusable pre-generation files must preserve evidence and never create decks."""

import hashlib
import json

import pytest


def _file(tmp_path, name, data, *, jsonl=False):
    path = tmp_path / name
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in data)
        if jsonl
        else json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _candidate(lemma, ident, *, language="de", pos="VERB", **extra):
    return {
        "language": language,
        "lemma": lemma,
        "pos": pos,
        "candidate_id": ident,
        "source_record_sha256": "a" * 64,
        "glosses": ["source meaning"],
        "review_status": "pending",
        **extra,
    }


def _request(tmp_path, rows, *, language="de", priorities=None, kind="candidates"):
    candidates = _file(tmp_path, "candidates.jsonl", rows, jsonl=True)
    priority = _file(
        tmp_path,
        "priority.json",
        {
            "source": "fixture-frequency",
            "ranking_status": "candidate_priority_only",
            "rows": priorities or [{"form": "ging", "rank": 1}, {"form": "gehen", "rank": 5}],
        },
    )
    return {
        "languages": [
            {"language": language, "sources": [{**candidates, "kind": kind}], "priority": priority}
        ],
        "expected_languages": [language],
    }


def _prepare(tmp_path, request, name="result"):
    from multilang.services.deck_preparation import DeckPreparationRequest, prepare_deck_inputs

    output = tmp_path / name
    summary = prepare_deck_inputs(DeckPreparationRequest.model_validate(request), output=output)
    language = request["languages"][0]["language"]
    vocabulary = json.loads((output / language / "vocabulary.json").read_text())
    return summary, vocabulary, output


def test_existing_senses_forms_and_order_survive_without_approval_or_generation(tmp_path):
    rows = [
        _candidate("gehen", "sense-1", forms=[{"form": "ging", "tags": ["past"]}]),
        _candidate("gehen", "sense-2", glosses=["to function"]),
        _candidate("ging", "form-1", kind="inflection", form_of=["gehen"]),
    ]
    summary, vocabulary, output = _prepare(tmp_path, _request(tmp_path, rows))
    assert len(vocabulary["entries"]) == 1
    entry = vocabulary["entries"][0]
    assert entry["lemma"] == "gehen"
    assert {x["candidate_id"] for x in entry["sense_candidates"]} == {"sense-1", "sense-2"}
    assert entry["selected_sense_id"] is None
    assert entry["source_priority"] == 1
    assert entry["provisional_order"] == 1
    assert entry["final_frequency_rank"] is None
    forms = [json.loads(x) for x in (output / "de" / "forms.jsonl").read_text().splitlines()]
    assert any(x["form"] == "ging" and x["parent_entry_ids"] == [entry["entry_id"]] for x in forms)
    assert all(x["selected_for_card"] is False for x in forms)
    assert vocabulary["coverage"]["spoken_percent"] is None
    assert vocabulary["coverage"]["written_percent"] is None
    assert vocabulary["coverage"]["target_percent"] == 90
    assert summary["generation"]["status"] == "deferred_by_user"
    assert summary["generation"]["provider_calls_executed"] == 0
    assert not list(output.rglob("*.apkg"))
    assert not list(output.rglob("*.mp3"))


def test_more_than_3000_lemmas_are_preserved_with_provisional_expansions(tmp_path):
    rows = [_candidate(f"Wort{i}", f"c{i}", pos="NOUN") for i in range(3002)]
    priority = [{"form": row["lemma"], "rank": i + 1} for i, row in enumerate(rows)]
    _, vocabulary, _ = _prepare(tmp_path, _request(tmp_path, rows, priorities=priority))
    assert len(vocabulary["entries"]) == 3002
    assert vocabulary["entries"][999]["proposed_band"] == "core-1"
    assert vocabulary["entries"][1000]["proposed_band"] == "core-2"
    assert vocabulary["entries"][3000]["proposed_band"] == "expansion-1"


def test_duplicate_sources_do_not_duplicate_senses_and_case_is_preserved(tmp_path):
    rows = [_candidate("Sie", "c1", pos="PRON"), _candidate("sie", "c2", pos="PRON")]
    request = _request(tmp_path, rows)
    request["languages"][0]["sources"] *= 2
    _, vocabulary, _ = _prepare(tmp_path, request)
    assert {e["lemma"] for e in vocabulary["entries"]} == {"Sie", "sie"}
    assert sum(len(e["sense_candidates"]) for e in vocabulary["entries"]) == 2


def test_nfc_equivalents_are_grouped_but_sense_ids_are_not_merged(tmp_path):
    rows = [_candidate("café", "a", pos="NOUN"), _candidate("cafe\u0301", "b", pos="NOUN")]
    _, vocabulary, _ = _prepare(tmp_path, _request(tmp_path, rows))
    assert len(vocabulary["entries"]) == 1
    assert len(vocabulary["entries"][0]["sense_candidates"]) == 2


@pytest.mark.parametrize(
    "language",
    [
        "pt",
        "es",
        "en",
        "fr",
        "de",
        "el",
        "it",
        "pl",
        "tr",
        "ro",
        "ru",
        "nl",
        "da",
        "nb",
        "sv",
        "fi",
        "hu",
        "cs",
        "hr",
        "ja",
        "zh",
        "ko",
    ],
)
def test_each_modern_language_has_deferred_preparation_and_sentence_policy(tmp_path, language):
    request = _request(tmp_path, [_candidate("lemma", "c1", language=language)], language=language)
    _, vocabulary, _ = _prepare(tmp_path, request)
    assert vocabulary["language"] == language
    assert vocabulary["sentence_policy"]["status"] == "draft_requires_curriculum_review"
    assert (
        vocabulary["sentence_policy"]["known_vocabulary_basis"]
        == "previously_introduced_not_observed_mastery"
    )


def test_manifest_coverage_requires_every_requested_language(tmp_path):
    from multilang.services.deck_preparation import DeckPreparationRequest

    request = _request(tmp_path, [_candidate("gehen", "a")])
    request["expected_languages"].append("ja")
    with pytest.raises(ValueError, match="language coverage"):
        DeckPreparationRequest.model_validate(request)


def test_tampered_input_is_rejected_without_publishing_partial_results(tmp_path):
    request = _request(tmp_path, [_candidate("gehen", "a")])
    (tmp_path / "candidates.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="checksum"):
        _prepare(tmp_path, request)
    assert not (tmp_path / "result").exists()


def test_conflicting_candidate_id_and_language_mismatch_fail_closed(tmp_path):
    request = _request(tmp_path, [_candidate("gehen", "same"), _candidate("kommen", "same")])
    with pytest.raises(ValueError, match="conflicting candidate"):
        _prepare(tmp_path, request)
    request = _request(tmp_path, [_candidate("go", "a", language="en")])
    with pytest.raises(ValueError, match="language mismatch"):
        _prepare(tmp_path, request)


def test_source_and_output_symlinks_are_rejected_and_existing_output_preserved(tmp_path):
    request = _request(tmp_path, [_candidate("gehen", "a")])
    link = tmp_path / "linked.jsonl"
    link.symlink_to(tmp_path / "candidates.jsonl")
    request["languages"][0]["sources"][0]["path"] = str(link)
    with pytest.raises(ValueError, match="symlink"):
        _prepare(tmp_path, request)
    request["languages"][0]["sources"][0]["path"] = str(tmp_path / "candidates.jsonl")
    existing = tmp_path / "result"
    existing.mkdir()
    (existing / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="new output"):
        _prepare(tmp_path, request)
    assert (existing / "keep.txt").read_text() == "keep"


def test_japanese_priority_links_do_not_choose_one_reading_or_sense(tmp_path):
    rows = [
        _candidate("生", "a", language="ja", forms=[{"form": "生", "reading": "せい"}]),
        _candidate("生", "b", language="ja", forms=[{"form": "生", "reading": "なま"}]),
    ]
    request = _request(
        tmp_path,
        rows,
        language="ja",
        priorities=[{"form": "生", "rank": 2, "candidate_ids": ["a", "b"]}],
    )
    _, vocabulary, _ = _prepare(tmp_path, request)
    entry = vocabulary["entries"][0]
    assert entry["selected_sense_id"] is None
    assert {x["reading"] for x in entry["readings"]} == {"せい", "なま"}
    assert vocabulary["sentence_policy"]["length_unit"] == "analyzer_units_pending_calibration"


def test_non_mandarin_source_evidence_remains_explicitly_unqualified(tmp_path):
    rows = [_candidate("詞", "a", language="zh", tags=["Cantonese"])]
    _, vocabulary, _ = _prepare(tmp_path, _request(tmp_path, rows, language="zh"))
    assert "mandarin_scope_review_required" in vocabulary["entries"][0]["review_reasons"]
    assert vocabulary["entries"][0]["selected_for_generation"] is False


def test_existing_korean_identity_is_preserved_without_claiming_new_approval(tmp_path):
    rows = [
        {
            "language": "ko",
            "lexical_identity": {
                "lemma": "가게",
                "part_of_speech": "NNG",
                "sense_id": "nikl:1",
                "status": "resolved",
            },
            "source_rank": 1,
            "final_rank": 1,
            "curation_decision": "accepted",
            "license_decision": "approved-redistribution",
        }
    ]
    request = _request(tmp_path, rows, language="ko", kind="korean_inventory")
    _, vocabulary, _ = _prepare(tmp_path, request)
    sense = vocabulary["entries"][0]["sense_candidates"][0]
    assert sense["source_sense_ids"] == ["nikl:1"]
    assert sense["existing_source_state"]["curation_decision"] == "accepted"
    assert vocabulary["entries"][0]["selected_for_generation"] is False


def test_latin_existing_inventory_is_kept_in_its_own_path_without_copying_content(tmp_path):
    source = _file(
        tmp_path,
        "latin.json",
        {
            "language_code": "la",
            "entries": [
                {
                    "item_key": "latin-1",
                    "lemma": "amor",
                    "target_form": "amor",
                    "sequence": 1,
                    "latin_sentence": "Old content",
                    "morphology_evidence": {"part_of_speech": "subst"},
                }
            ],
        },
    )
    request = {
        "languages": [{"language": "la", "sources": [{**source, "kind": "latin_inventory"}]}],
        "expected_languages": ["la"],
    }
    _, vocabulary, output = _prepare(tmp_path, request)
    assert vocabulary["path"] == "classical_latin"
    assert vocabulary["entries"][0]["lemma"] == "amor"
    assert "Old content" not in (output / "la" / "vocabulary.json").read_text()


def test_offline_cli_is_available_without_runtime_or_provider(tmp_path):
    from typer.testing import CliRunner

    from multilang.vocabulary_cli import create_vocabulary_app

    request = _request(tmp_path, [_candidate("gehen", "a")])
    ref = _file(tmp_path, "request.json", request)
    result = CliRunner().invoke(
        create_vocabulary_app(),
        ["prepare-deck-inputs", ref["path"], ref["sha256"], str(tmp_path / "delivery")],
    )
    assert result.exit_code == 0, result.output
    assert (
        json.loads((tmp_path / "delivery" / "summary.json").read_text())["generation"][
            "provider_calls_executed"
        ]
        == 0
    )


def test_diagnostic_corpus_counts_unknowns_without_becoming_general_coverage_or_ranking(tmp_path):
    corpus = _file(
        tmp_path,
        "corpus.jsonl",
        [
            {
                "language": "de",
                "document_id": "doc-1",
                "sentence_id": "s-1",
                "text": "Gehen kommen .",
                "source_sha256": "b" * 64,
                "tokens": [
                    {"index": 1, "text": "Gehen", "lemma": "gehen", "pos": "VERB"},
                    {"index": 2, "text": "kommen", "lemma": "kommen", "pos": "VERB"},
                    {"index": 3, "text": ".", "lemma": ".", "pos": "PUNCT"},
                    {"index": 4, "text": "unknown", "lemma": None, "pos": "X"},
                ],
            }
        ],
        jsonl=True,
    )
    request = _request(tmp_path, [_candidate("gehen", "a")])
    request["languages"][0]["diagnostic_corpora"] = [corpus, corpus]
    _, vocabulary, output = _prepare(tmp_path, request)
    report = json.loads((output / "de" / "report.json").read_text())
    diagnostic = report["diagnostic_lemma_availability"]
    assert diagnostic["lexical_tokens"] == 3
    assert diagnostic["matched_tokens"] == 1
    assert diagnostic["missing_lemma_annotation_tokens"] == 1
    assert diagnostic["excluded_punctuation_or_symbol_tokens"] == 1
    assert diagnostic["percent"] == pytest.approx(100 / 3, abs=0.001)
    assert diagnostic["general_language_coverage"] is False
    assert diagnostic["used_for_ranking"] is False
    assert vocabulary["coverage"]["target_achieved"] is None
    assert vocabulary["entries"][0]["provisional_order"] == 1


def test_deck_preparation_does_not_make_network_requests(tmp_path, monkeypatch):
    import socket

    def forbidden(*args, **kwargs):
        raise AssertionError("preparation must be offline")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    _prepare(tmp_path, _request(tmp_path, [_candidate("gehen", "a")]))


def test_test_corpus_must_not_supply_preparation_priority(tmp_path):
    request = _request(tmp_path, [_candidate("gehen", "a")])
    request["languages"][0]["priority"] = _file(
        tmp_path,
        "priority-from-test.json",
        {
            "source": "test-corpus",
            "test_corpus_used": True,
            "rows": [{"form": "gehen", "rank": 1}],
        },
    )
    with pytest.raises(ValueError, match="test corpus"):
        _prepare(tmp_path, request)
    assert not (tmp_path / "result").exists()


def test_failure_in_later_language_does_not_publish_earlier_language(tmp_path):
    request = _request(tmp_path, [_candidate("gehen", "a")])
    missing = {"path": str(tmp_path / "missing.jsonl"), "sha256": "f" * 64, "kind": "candidates"}
    request["languages"].append({"language": "en", "sources": [missing]})
    request["expected_languages"].append("en")
    with pytest.raises(FileNotFoundError):
        _prepare(tmp_path, request)
    assert not (tmp_path / "result").exists()
