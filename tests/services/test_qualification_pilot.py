import hashlib
import json

import pytest

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_preparation import prepare_vocabulary


def api():
    from multilang.services import qualification_pilot

    return qualification_pilot


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepared(tmp_path, language="en"):
    records = [
        {
            "word": "go",
            "lang_code": language,
            "pos": "verb",
            "forms": [
                {"form": "went", "tags": ["past", "irregular"]},
                {"form": "going", "tags": ["participle"]},
            ],
            "senses": [{"glosses": ["move"]}, {"glosses": ["function"]}],
        },
        {
            "word": "went",
            "lang_code": language,
            "pos": "verb",
            "senses": [{"glosses": ["past of go"], "form_of": [{"word": "go"}]}],
        },
        {
            "word": "bank",
            "lang_code": language,
            "pos": "noun",
            "senses": [{"glosses": ["institution"]}, {"glosses": ["river edge"]}],
        },
        {
            "word": "A",
            "lang_code": language,
            "pos": "character",
            "senses": [{"glosses": ["letter"]}],
        },
    ]
    path = tmp_path / "dictionary.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in records))
    output = tmp_path / "prepared"
    prepare_vocabulary(
        language=language, dictionary=path, dictionary_sha256=sha(path), output=output
    )
    return output


def make_pilot(tmp_path, **changes):
    module = api()
    source = tmp_path / "prepared"
    if not source.exists():
        source = prepared(tmp_path)
    request = dict(
        language="en",
        prepared_inputs=(
            module.PreparedVocabularyInput(
                directory=source, manifest_sha256=sha(source / "manifest.json")
            ),
        ),
        seed_words=("missing", "go", "bank", "a"),
        headword_count=1,
        profile_sha256="a" * 64,
        rubric_sha256="b" * 64,
        output=tmp_path / "pilot",
    )
    request.update(changes)
    return module.prepare_qualification_pilot(**request)


def packet_items(root, manifest, kind=None):
    return [
        item
        for entry in manifest["packets"]
        for item in json.loads((root / entry["path"] / "packet.json").read_text())["items"]
        if kind is None or item["kind"] == kind
    ]


def test_seed_selection_keeps_all_senses_and_associated_forms_without_scores(tmp_path):
    manifest = make_pilot(tmp_path)
    assert manifest["selected_headwords"] == ["go"]
    assert manifest["lexical_candidate_count"] == 2
    assert manifest["inflection_candidate_count"] == 1
    assert manifest["dictionary_form_proposal_count"] == 3
    candidates = [
        json.loads(line) for line in (tmp_path / "pilot/candidates.jsonl").read_text().splitlines()
    ]
    assert {c["lemma"] for c in candidates} == {"go", "went"}
    assert [c["stable_sense_id"] for c in candidates] == [None] * 3
    items = packet_items(tmp_path / "pilot", manifest)
    assert len([item for item in items if item["kind"] == "lexical"]) == 2
    forms = [item for item in items if item["kind"] == "form"]
    assert {item["text"] for item in forms} == {"went", "going"}
    assert all(item["proposed_ratings"] == {} for item in forms)
    assert all(item["canonical_sense_id"] is None for item in forms)
    assert "missing_calibration_corpus" in manifest["blockers"]
    assert manifest["production_eligible"] is False
    assert manifest["workload"]["important_form_cards"] is None
    assert manifest["workload"]["provider_calls_executed"] == 0


def test_pilot_is_deterministic_sharded_and_preserves_source_files(tmp_path):
    source = prepared(tmp_path)
    before = {p.name: sha(p) for p in source.iterdir()}
    first = make_pilot(tmp_path, packet_item_limit=1)
    second = make_pilot(tmp_path, output=tmp_path / "second", packet_item_limit=1)
    assert first == second
    assert all(packet["item_count"] == 1 for packet in first["packets"])
    assert before == {p.name: sha(p) for p in source.iterdir()}
    with pytest.raises(ValueError, match="exists"):
        make_pilot(tmp_path)


def test_missing_words_and_unknown_pos_are_visible_without_noun_guess(tmp_path):
    manifest = make_pilot(tmp_path, seed_words=("missing", "a"), headword_count=3)
    assert manifest["selected_headwords"] == []
    assert manifest["missing_seed_words"] == ["missing"]
    assert "insufficient_source_backed_headwords" in manifest["blockers"]
    assert manifest["unknown_pos_candidates"][0]["lemma"] == "A"
    assert manifest["unknown_pos_candidates"][0]["source_pos"] is None
    lexical = packet_items(tmp_path / "pilot", manifest, "lexical")
    assert lexical[0]["pos"] == "X"


@pytest.mark.parametrize("corruption", ["manifest", "candidates", "symlink"])
def test_prepared_input_checksums_and_plain_paths_are_required(tmp_path, corruption):
    source = prepared(tmp_path)
    request = api().PreparedVocabularyInput(
        directory=source, manifest_sha256=sha(source / "manifest.json")
    )
    if corruption == "manifest":
        (source / "manifest.json").write_text("{}")
    elif corruption == "candidates":
        (source / "candidates.jsonl").write_text("{}\n")
    else:
        link = tmp_path / "linked"
        link.symlink_to(source, target_is_directory=True)
        request = request.model_copy(update={"directory": link})
    with pytest.raises(ValueError, match="checksum|symlink"):
        make_pilot(tmp_path, prepared_inputs=(request,))
    assert not (tmp_path / "pilot").exists()


def evaluation(tmp_path):
    from multilang.services.contextual_morphology import (
        ContextualAnalysis,
        ContextualToken,
        sentence_hash,
    )
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    path = tmp_path / "eval.conllu"
    path.write_text(
        "# newdoc id = eval-doc\n# sent_id = eval-sentence\n# text = go\n"
        "1\tgo\tgo\tVERB\t_\t_\t0\troot\t_\t_\n\n"
    )

    class Analyzer:
        def analyze(self, language, text):
            return ContextualAnalysis(
                language=language,
                status="complete",
                sentence_sha256=sentence_hash(text),
                model_fingerprint="c" * 64,
                reason="test-fixture",
                tokens=(
                    ContextualToken(
                        text="go",
                        lemma="go",
                        pos="VERB",
                        start=0,
                        end=2,
                        sentence_sha256=sentence_hash(text),
                        model_fingerprint="c" * 64,
                    ),
                ),
            )

    output = tmp_path / "evaluated"
    evaluate_corpus(
        language="en", corpus=path, corpus_sha256=sha(path), output=output, analyzer=Analyzer()
    )
    return api().EvaluationInput(
        directory=output, manifest_sha256=sha(output / "manifest.json")
    ), sha(path)


def test_evaluation_cases_are_separate_pending_packets_and_not_frequency_input(tmp_path):
    source, _ = evaluation(tmp_path)
    manifest = make_pilot(tmp_path, evaluation_input=source)
    cases = packet_items(tmp_path / "pilot", manifest, "case")
    assert len(cases) == 1
    assert cases[0]["expected_match"] is None
    assert cases[0]["proposal_tokens"][0]["lemma"] == "go"
    assert all(p["split"] == "evaluation" for p in manifest["packets"] if p["kind"] == "case")
    assert manifest["measurement_count"] == 0
    assert "insufficient_evaluation_cases" in manifest["blockers"]
    assert (tmp_path / "pilot/evaluation-observations.jsonl").exists()


def corpus_evidence(*, source_sha="d" * 64, sentence="went", split="calibration"):
    from multilang.domain.form_evidence import CorpusEvidenceContext, EvidenceOccurrence

    context = CorpusEvidenceContext(
        language="en", split=split, source_sha256s=(source_sha,), token_count=1
    )
    occurrences = (
        EvidenceOccurrence(
            language="en",
            split=split,
            source_sha256=source_sha,
            sentence_id="measurement",
            sentence=sentence,
            start=0,
            end=len(sentence),
            text=sentence,
            lemma="go",
            pos="VERB",
            features={"Tense": "Past"},
        ),
    )
    return context, occurrences


def test_real_measurements_are_distinct_from_unobserved_dictionary_forms(tmp_path):
    context, occurrences = corpus_evidence()
    manifest = make_pilot(tmp_path, evidence_context=context, occurrences=occurrences)
    assert manifest["measurement_count"] == 1
    forms = packet_items(tmp_path / "pilot", manifest, "form")
    measured = [f for f in forms if f["measurement_sha256"]]
    assert len(measured) == 1
    assert measured[0]["measurements"]["observed_count"] == "1"
    assert set(measured[0]["proposed_ratings"]) == {"frequency"}
    assert measured[0]["canonical_sense_id"] is None
    assert all("irregularity" not in f["proposed_ratings"] for f in forms)
    assert "missing_calibration_corpus" not in manifest["blockers"]


def test_measured_forms_bind_all_documents_and_sentences_beyond_displayed_examples(tmp_path):
    from multilang.domain.form_evidence import (
        CorpusEvidenceContext,
        EvidenceDocument,
        EvidenceOccurrence,
    )
    from multilang.services.contextual_morphology import sentence_hash

    source_sha = "d" * 64
    texts = ("He went.", "They went.", "The bank.")
    documents = tuple(
        EvidenceDocument(
            source_sha256=source_sha,
            document_id=f"doc-{index}",
            text_sha256=sentence_hash(text + " Full document context."),
            token_count=1,
        )
        for index, text in enumerate(texts)
    )
    context = CorpusEvidenceContext(
        language="en", split="calibration", source_sha256s=(source_sha,),
        token_count=3, documents=documents,
    )
    occurrences = tuple(
        EvidenceOccurrence(
            language="en", split="calibration", source_sha256=source_sha,
            document_id=documents[index].document_id, sentence_id=f"sentence-{index}",
            sentence=text, start=text.index(surface), end=text.index(surface) + len(surface),
            text=surface, lemma=lemma, pos=pos,
        )
        for index, (text, surface, lemma, pos) in enumerate(
            ((texts[0], "went", "go", "VERB"), (texts[1], "went", "go", "VERB"),
             (texts[2], "bank", "bank", "NOUN"))
        )
    )
    manifest = make_pilot(tmp_path, evidence_context=context, occurrences=occurrences)
    measured = next(
        item for item in packet_items(tmp_path / "pilot", manifest, "form")
        if item["measurement_sha256"]
    )
    assert len(measured["sources"]) == 1
    expected = {canonical_sha256(["source", source_sha])}
    for document, text in zip(documents[:2], texts[:2], strict=True):
        expected.add(canonical_sha256(["document-content", document.text_sha256]))
        expected.add(canonical_sha256(["sentence-text", sentence_hash(text)]))
    assert measured["evidence_source_keys"] == sorted(expected)
    assert measured["measurements"]["observed_count"] == "2"


@pytest.mark.parametrize("leak", ["same_source", "same_sentence", "evaluation_split"])
def test_evaluation_evidence_cannot_enter_calibration(tmp_path, leak):
    evaluation_input, source_sha = evaluation(tmp_path)
    context, occurrences = corpus_evidence(
        source_sha=source_sha if leak == "same_source" else "d" * 64,
        sentence="go" if leak == "same_sentence" else "went",
        split="evaluation" if leak == "evaluation_split" else "calibration",
    )
    with pytest.raises(ValueError, match="evaluation|calibration|held-out"):
        make_pilot(
            tmp_path,
            evaluation_input=evaluation_input,
            evidence_context=context,
            occurrences=occurrences,
        )
    assert not (tmp_path / "pilot").exists()


def test_pilot_output_limit_fails_atomically(tmp_path):
    from multilang.services.vocabulary_sources import SourceLimits

    with pytest.raises(ValueError, match="output byte limit"):
        make_pilot(tmp_path, limits=SourceLimits(max_output_bytes=100))
    assert not (tmp_path / "pilot").exists()


def test_category_sidecar_keeps_original_candidate_hash_and_raw_category(tmp_path):
    source = prepared(tmp_path)
    original = next(
        json.loads(line)
        for line in (source / "candidates.jsonl").read_text().splitlines()
        if json.loads(line)["lemma"] == "A"
    )
    sidecar = tmp_path / "categories.json"
    sidecar.write_text(json.dumps({original["source_record_sha256"]: "character"}))
    manifest = make_pilot(
        tmp_path,
        seed_words=("a",),
        source_categories=api().SourceCategoryInput(path=sidecar, sha256=sha(sidecar)),
    )
    unknown = manifest["unknown_pos_candidates"][0]
    assert unknown["source_pos"] == "character"
    assert unknown["candidate_id"] == original["candidate_id"]
    selected = json.loads((tmp_path / "pilot/unknown-pos-candidates.jsonl").read_text())
    assert canonical_sha256(selected) == canonical_sha256(original)
    item = packet_items(tmp_path / "pilot", manifest, "lexical")[0]
    assert "character" in item["sources"][0]["excerpt"]


def test_ambiguous_raw_conjunction_does_not_consume_headword_quota(tmp_path):
    records = [
        {
            "word": "because",
            "lang_code": "en",
            "pos": "conj",
            "senses": [{"glosses": ["for the reason that"]}],
        },
        {
            "word": "bank",
            "lang_code": "en",
            "pos": "noun",
            "senses": [{"glosses": ["institution"]}],
        },
    ]
    dictionary = tmp_path / "dictionary.jsonl"
    dictionary.write_text("".join(json.dumps(row) + "\n" for row in records))
    prepare_vocabulary(
        language="en",
        dictionary=dictionary,
        dictionary_sha256=sha(dictionary),
        output=tmp_path / "prepared",
    )
    original = next(
        json.loads(line)
        for line in (tmp_path / "prepared/candidates.jsonl").read_text().splitlines()
        if json.loads(line)["lemma"] == "because"
    )
    categories = tmp_path / "categories.json"
    categories.write_text(json.dumps({original["source_record_sha256"]: "conj"}))
    manifest = make_pilot(
        tmp_path,
        seed_words=("because", "bank"),
        source_categories=api().SourceCategoryInput(path=categories, sha256=sha(categories)),
    )
    assert manifest["selected_headwords"] == ["bank"]
    assert manifest["source_category_candidate_counts"]["conj"] == 1
    item = next(
        item
        for item in packet_items(tmp_path / "pilot", manifest, "lexical")
        if item["lemma"] == "because"
    )
    assert item["pos"] == "X"
    assert item["candidate_sha256"] == canonical_sha256(original)
    assert "conj" in item["sources"][0]["excerpt"]
    assert "CCONJ" in item["sources"][0]["excerpt"]


def test_inflection_parent_keeps_exact_source_case_when_seed_is_casefolded(tmp_path):
    records = [
        {"word": "GO", "lang_code": "en", "pos": "noun", "senses": [{"glosses": ["board game"]}]},
        {
            "word": "went",
            "lang_code": "en",
            "pos": "verb",
            "senses": [{"glosses": ["past of go"], "form_of": [{"word": "go"}]}],
        },
    ]
    dictionary = tmp_path / "dictionary.jsonl"
    dictionary.write_text("".join(json.dumps(row) + "\n" for row in records))
    prepare_vocabulary(
        language="en",
        dictionary=dictionary,
        dictionary_sha256=sha(dictionary),
        output=tmp_path / "prepared",
    )
    manifest = make_pilot(tmp_path, seed_words=("go",))
    assert manifest["selected_headwords"] == ["GO"]
    (item,) = packet_items(tmp_path / "pilot", manifest, "form")
    assert item["lemma"] == "go"


def test_duplicate_prepared_inputs_do_not_duplicate_proposals(tmp_path):
    source = prepared(tmp_path)
    input_ = api().PreparedVocabularyInput(
        directory=source, manifest_sha256=sha(source / "manifest.json")
    )
    first = make_pilot(tmp_path)
    duplicate = make_pilot(
        tmp_path, prepared_inputs=(input_, input_), output=tmp_path / "duplicate"
    )
    assert first == duplicate
