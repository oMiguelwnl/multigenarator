"""Real source formats must remain evidence, never automatic release approval."""

import gzip
import hashlib
import json

import pytest


def test_conllu_empty_initial_nodes_and_misc_flags_are_not_word_tokens(tmp_path):
    from multilang.services.vocabulary_sources import read_conllu

    path = tmp_path / "real-format.conllu"
    path.write_text(
        "# text = Hello!\n"
        "0.1\tmissing\tmissing\tPRON\t_\t_\t_\t_\t1:nsubj\t_\n"
        "1\tHello\thello\tINTJ\t_\t_\t0\troot\t_\t_S|SpaceAfter=No\n"
        "2\t!\t!\tPUNCT\t_\t_\t1\tpunct\t_\tCxnElt=A|CxnElt=B\n\n"
    )
    import hashlib

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    sentence = list(read_conllu(path, language="en", expected_sha256=digest))[0]
    assert [(token.text, token.start, token.end) for token in sentence.tokens] == [
        ("Hello", 0, 5),
        ("!", 5, 6),
    ]
    assert sentence.tokens[1].misc == "CxnElt=A|CxnElt=B"


def source(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def test_conllu_preserves_forms_features_and_source_document(tmp_path):
    from multilang.services.vocabulary_sources import read_conllu

    data = (
        "# newdoc id = doc1\n# sent_id = s1\n# text = They went home.\n"
        "1\tThey\tthey\tPRON\t_\tNumber=Plur\t2\tnsubj\t_\t_\n"
        "2\twent\tgo\tVERB\t_\tTense=Past|VerbForm=Fin\t0\troot\t_\t_\n"
        "3\thome\thome\tADV\t_\t_\t2\tadvmod\t_\tSpaceAfter=No\n"
        "4\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n"
    ).encode()
    path, digest = source(tmp_path, "test.conllu", data)
    rows = tuple(read_conllu(path, language="en", expected_sha256=digest))
    assert len(rows) == 1
    assert rows[0].document_id == "doc1"
    token = rows[0].tokens[1]
    assert (token.text, token.lemma, token.pos) == ("went", "go", "VERB")
    assert (token.start, token.end) == (5, 9)
    assert token.features["Tense"] == "Past"
    assert rows[0].text[token.start : token.end] == token.text
    assert rows[0].tokens[1].sense_id is None


@pytest.mark.parametrize("header", ["newdoc id", "newdoc_id"])
def test_conllu_document_headers_persist_until_next_document(tmp_path, header):
    from multilang.services.vocabulary_sources import read_conllu

    sentence = "# text = casa\n1\tcasa\tcasa\tNOUN\t_\t_\t0\troot\t_\t_\n\n"
    data = f"# {header} = first\n{sentence}{sentence}# {header} = second\n{sentence}"
    path, digest = source(tmp_path, "documents.conllu", data.encode())
    rows = tuple(read_conllu(path, language="pt", expected_sha256=digest))
    assert [row.document_id for row in rows] == ["first", "first", "second"]


def test_conllu_absent_document_headers_keep_unknown_source_container(tmp_path):
    from multilang.services.vocabulary_sources import read_conllu

    data = b"# text = casa\n1\tcasa\tcasa\tNOUN\t_\t_\t0\troot\t_\t_\n\n"
    path, digest = source(tmp_path, "unknown.conllu", data + data)
    rows = tuple(read_conllu(path, language="pt", expected_sha256=digest))
    assert [row.document_id for row in rows] == [f"source-{digest}"] * 2


@pytest.mark.parametrize("second_header", ["newdoc id", "newdoc_id"])
def test_conllu_conflicting_document_headers_fail_closed(tmp_path, second_header):
    from multilang.services.vocabulary_sources import read_conllu

    data = (
        f"# newdoc id = first\n# {second_header} = second\n"
        "# text = casa\n1\tcasa\tcasa\tNOUN\t_\t_\t0\troot\t_\t_\n\n"
    )
    path, digest = source(tmp_path, "conflict.conllu", data.encode())
    with pytest.raises(ValueError, match="conflicting CoNLL-U document headers"):
        tuple(read_conllu(path, language="pt", expected_sha256=digest))


def test_conllu_matching_document_aliases_do_not_conflict(tmp_path):
    from multilang.services.vocabulary_sources import read_conllu

    data = (
        "# newdoc id = first\n# newdoc_id = first\n"
        "# text = casa\n1\tcasa\tcasa\tNOUN\t_\t_\t0\troot\t_\t_\n\n"
    )
    path, digest = source(tmp_path, "same.conllu", data.encode())
    assert tuple(read_conllu(path, language="pt", expected_sha256=digest))[0].document_id == "first"


def test_conllu_does_not_invent_character_spans_for_contractions(tmp_path):
    from multilang.services.vocabulary_sources import read_conllu

    data = (
        "# text = du pain\n1-2\tdu\t_\t_\t_\t_\t_\t_\t_\t_\n"
        "1\tde\tde\tADP\t_\t_\t0\troot\t_\t_\n"
        "2\tle\tle\tDET\t_\t_\t1\tdet\t_\t_\n"
        "3\tpain\tpain\tNOUN\t_\t_\t1\tobj\t_\t_\n"
    ).encode()
    path, digest = source(tmp_path, "test.conllu", data)
    doc = tuple(read_conllu(path, language="fr", expected_sha256=digest))[0]
    assert doc.tokens[0].start is None
    assert doc.tokens[1].start is None
    assert (doc.tokens[2].start, doc.tokens[2].end) == (3, 7)


def test_conllu_checks_source_hash_and_rejects_malformed_rows(tmp_path):
    from multilang.services.vocabulary_sources import read_conllu

    path, digest = source(tmp_path, "bad.conllu", b"1\tgo\n")
    with pytest.raises(ValueError, match="checksum"):
        tuple(read_conllu(path, language="en", expected_sha256="0" * 64))
    with pytest.raises(ValueError, match="ten columns"):
        tuple(read_conllu(path, language="en", expected_sha256=digest))


def test_wiktextract_retains_distinct_senses_and_never_creates_approved_ids(tmp_path):
    from multilang.services.vocabulary_sources import read_wiktextract

    payload = {
        "word": "bank",
        "lang_code": "en",
        "pos": "noun",
        "senses": [
            {"glosses": ["A financial institution."], "examples": [{"text": "The bank is open."}]},
            {"glosses": ["The edge of a river."]},
        ],
    }
    data = (json.dumps(payload) + "\n").encode()
    path, digest = source(tmp_path, "words.jsonl.gz", gzip.compress(data))
    rows = tuple(read_wiktextract(path, language="en", expected_sha256=digest))
    assert len(rows) == 2
    assert rows[0].pos == "NOUN"
    assert rows[0].candidate_id != rows[1].candidate_id
    assert rows[0].examples == ("The bank is open.",)
    assert all(row.stable_sense_id is None for row in rows)
    assert all(row.review_status == "pending" for row in rows)


def test_language_aliases_are_not_source_approval(tmp_path):
    from multilang.services.vocabulary_sources import read_wiktextract

    data = (
        json.dumps(
            {"word": "grad", "lang_code": "sh", "pos": "noun", "senses": [{"glosses": ["city"]}]}
        )
        + "\n"
    ).encode()
    path, digest = source(tmp_path, "words.jsonl", data)
    assert tuple(read_wiktextract(path, language="hr", expected_sha256=digest)) == ()


def test_dictionary_inflections_are_not_new_headwords(tmp_path):
    from multilang.services.vocabulary_sources import read_wiktextract

    data = (
        json.dumps(
            {
                "word": "went",
                "lang_code": "en",
                "pos": "verb",
                "senses": [{"glosses": ["past of go"], "form_of": [{"word": "go"}]}],
            }
        )
        + "\n"
    ).encode()
    path, digest = source(tmp_path, "words.jsonl", data)
    row = tuple(read_wiktextract(path, language="en", expected_sha256=digest))[0]
    assert row.form_of == ("go",)
    assert row.kind == "inflection"


def test_source_limits_and_symlinks_are_enforced(tmp_path):
    from multilang.services.vocabulary_sources import SourceLimits, read_wiktextract

    data = b'{"word":"go","lang_code":"en","pos":"verb","senses":[]}\n'
    path, digest = source(tmp_path, "words.jsonl", data)
    with pytest.raises(ValueError, match="byte limit"):
        tuple(
            read_wiktextract(
                path, language="en", expected_sha256=digest, limits=SourceLimits(max_bytes=10)
            )
        )
    link = tmp_path / "link.jsonl"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="symlink"):
        tuple(read_wiktextract(link, language="en", expected_sha256=digest))


@pytest.mark.parametrize("token_range", ["1-100000", "1-3"])
def test_multiword_ranges_are_bounded_and_must_have_real_members(tmp_path, token_range):
    from multilang.services.vocabulary_sources import SourceLimits, read_conllu

    data = (
        f"# text = du\n{token_range}\tdu\t_\t_\t_\t_\t_\t_\t_\t_\n"
        "1\tde\tde\tADP\t_\t_\t0\troot\t_\t_\n"
        "2\tle\tle\tDET\t_\t_\t1\tdet\t_\t_\n"
    ).encode()
    path, digest = source(tmp_path, "range.conllu", data)
    with pytest.raises(ValueError, match="range|limit"):
        tuple(
            read_conllu(
                path,
                language="fr",
                expected_sha256=digest,
                limits=SourceLimits(max_tokens_per_sentence=4),
            )
        )


def test_dictionary_filter_preserves_case_and_scalar_source_sense_identifier(tmp_path):
    from multilang.services.vocabulary_sources import read_wiktextract

    record = {
        "word": "Haus",
        "lang_code": "de",
        "pos": "noun",
        "tags": ["standard"],
        "senses": [{"glosses": ["house"], "senseid": "source:house"}],
    }
    path, digest = source(tmp_path, "case.jsonl", (json.dumps(record) + "\n").encode())
    rows = list(read_wiktextract(path, language="de", expected_sha256=digest, lemmas={"haus"}))
    assert len(rows) == 1
    assert rows[0].lemma == "Haus"
    assert rows[0].source_sense_ids == ("source:house",)
    assert rows[0].tags == ("standard",)
