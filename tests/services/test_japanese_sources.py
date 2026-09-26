"""Small original records exercise source semantics and hostile-input bounds."""

import gzip
import hashlib
import json
import lzma

import httpx
import pytest

from multilang.services.vocabulary_preparation import prepare_vocabulary

JMDICT = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE JMdict [<!ENTITY n "noun (common) (futsuumeishi)">]>
<JMdict><entry><ent_seq>1234567</ent_seq>
<k_ele><keb>今日</keb><ke_pri>news1</ke_pri></k_ele>
<k_ele><keb>今日日</keb></k_ele>
<r_ele><reb>きょう</reb><re_restr>今日</re_restr></r_ele>
<r_ele><reb>きょうび</reb><re_restr>今日日</re_restr></r_ele>
<sense><stagk>今日</stagk><stagr>きょう</stagr><pos>&n;</pos><gloss>today</gloss></sense>
<sense><stagk>今日日</stagk><stagr>きょうび</stagr><gloss>nowadays</gloss></sense>
</entry></JMdict>'''

TUBELEX = "word\tcount\tvideos\tchannels\tcount:People\tpos\n今日\t12\t5\t3\t12\t名詞\n食べる\t8\t4\t2\t8\t動詞\n[TOTAL]\t20\t7\t4\t20\t\n"


def write_source(tmp_path, text=JMDICT, name="dictionary.xml.gz"):
    path = tmp_path / name
    content = text.encode()
    if name.endswith(".gz"):
        content = gzip.compress(content)
    if name.endswith(".xz"):
        content = lzma.compress(content)
    path.write_bytes(content)
    return path, hashlib.sha256(content).hexdigest()


def test_jmdict_is_wired_into_preparation_and_preserves_restricted_readings(tmp_path):
    source, digest = write_source(tmp_path)
    result = prepare_vocabulary(language="ja", dictionary=source, dictionary_sha256=digest,
                                output=tmp_path / "prepared", dictionary_format="jmdict")
    candidates = [json.loads(line) for line in (tmp_path / "prepared/candidates.jsonl").read_text().splitlines()]
    assert result["dictionary_format"] == "jmdict"
    assert not result["production_eligible"]
    assert [(c["lemma"], c["pos"], c["sounds"][0]["reading"]) for c in candidates] == [
        ("今日", "NOUN", "きょう"), ("今日日", "NOUN", "きょうび")]
    assert candidates[1]["glosses"] == ["nowadays"]
    assert digest in candidates[0]["source_sense_ids"][0]
    assert candidates[0]["stable_sense_id"] is None


def test_jmdict_filter_accepts_written_and_reading_forms(tmp_path):
    from multilang.services.japanese_sources import read_jmdict

    source, digest = write_source(tmp_path)
    candidates = list(read_jmdict(source, expected_sha256=digest, lemmas={"きょう"}))
    assert [item.lemma for item in candidates] == ["今日"]


@pytest.mark.parametrize("xml", [
    '<!DOCTYPE JMdict SYSTEM "file:///etc/passwd"><JMdict/>',
    '<!DOCTYPE JMdict [<!ENTITY n SYSTEM "file:///etc/passwd">]><JMdict/>',
    '<!DOCTYPE JMdict [<!ENTITY a "expanded"><!ENTITY n "&a;&a;">]><JMdict/>',
    '<!DOCTYPE JMdict [<!ENTITY % remote SYSTEM "https://invalid.test/dtd">%remote;]><JMdict/>',
    JMDICT.replace('<re_restr>今日</re_restr>', '<re_restr>存在しない</re_restr>'),
])
def test_jmdict_rejects_external_expanding_entities_and_dangling_restrictions(tmp_path, xml):
    from multilang.services.japanese_sources import read_jmdict

    source, digest = write_source(tmp_path, xml)
    with pytest.raises(ValueError):
        list(read_jmdict(source, expected_sha256=digest))


def test_jmdict_rejects_wrong_hash_and_expanded_byte_overflow(tmp_path):
    from multilang.services.japanese_sources import read_jmdict
    from multilang.services.vocabulary_sources import SourceLimits

    source, digest = write_source(tmp_path)
    with pytest.raises(ValueError, match="checksum"):
        list(read_jmdict(source, expected_sha256="0" * 64))
    with pytest.raises(ValueError, match="byte limit"):
        list(read_jmdict(source, expected_sha256=digest, limits=SourceLimits(max_expanded_bytes=50)))


def test_preparation_quarantines_conflicting_source_pairs_without_fabricating_readings(tmp_path):
    from multilang.services.vocabulary_preparation import prepare_vocabulary
    xml = '''<!DOCTYPE JMdict [<!ENTITY n "noun">]><JMdict><entry><ent_seq>123456</ent_seq>
    <k_ele><keb>仮</keb></k_ele><r_ele><reb>かり</reb><re_nokanji/></r_ele>
    <sense><stagk>仮</stagk><stagr>かり</stagr><pos>&n;</pos><gloss>synthetic conflicting pair</gloss></sense>
    </entry></JMdict>'''
    source, digest = write_source(tmp_path, xml)
    output = tmp_path / "prepared"
    result = prepare_vocabulary(language="ja", dictionary=source, dictionary_sha256=digest,
        dictionary_format="jmdict", output=output)
    assert result["lexical_candidate_count"] == 0
    assert result["source_diagnostic_count"] == 1
    diagnostic = json.loads((output / "source-diagnostics.json").read_text())[0]
    assert diagnostic["reason"] == "incompatible_jmdict_reading_and_sense_restrictions"


def test_tubelex_reads_aggregate_counts_without_invented_senses_or_occurrences(tmp_path):
    from multilang.services.japanese_sources import read_tubelex

    source, digest = write_source(tmp_path, TUBELEX, "tubelex.tsv.xz")
    rows = list(read_tubelex(source, expected_sha256=digest))
    assert [r.word for r in rows] == ["今日", "食べる"]
    assert (rows[0].count, rows[0].videos, rows[0].channels) == (12, 5, 3)
    assert rows[0].majority_pos == "名詞"
    assert rows[0].category_counts == {"People": 12}
    assert rows[0].source_sha256 == digest
    assert "sense_id" not in rows[0].model_dump()


def test_tubelex_quote_is_a_literal_published_token(tmp_path):
    from multilang.services.japanese_sources import read_tubelex
    source, digest = write_source(tmp_path, TUBELEX.replace("今日", '"'), "tubelex.tsv")
    assert list(read_tubelex(source, expected_sha256=digest))[0].word == '"'


@pytest.mark.parametrize("text", [
    TUBELEX.replace("今日\t12\t5", "今日\t2\t5"),
    TUBELEX.replace("今日\t12", "今日\t-12"),
    TUBELEX.replace("[TOTAL]\t20", "[TOTAL]\t1"),
    TUBELEX.replace("word\tcount", "word\tword"),
])
def test_tubelex_rejects_impossible_counts_and_duplicate_columns(tmp_path, text):
    from multilang.services.japanese_sources import read_tubelex

    source, digest = write_source(tmp_path, text, "tubelex.tsv")
    with pytest.raises(ValueError):
        list(read_tubelex(source, expected_sha256=digest))


@pytest.mark.parametrize("kind, suffix, host", [
    ("lexical-supplement", ".xml.gz", "www.edrdg.org"),
    ("frequency", ".tsv.xz", "raw.githubusercontent.com"),
])
def test_japanese_catalog_downloads_preserve_compression(tmp_path, kind, suffix, host):
    from multilang.services.vocabulary_acquisition import acquire_source

    def respond(request):
        assert request.url.host == host
        return httpx.Response(200, stream=httpx.ByteStream(b"synthetic-source-bytes"))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = acquire_source("ja", kind, tmp_path, client=client)
    assert result["file"].endswith(suffix)
    assert not result["redistribution_approved"]


def test_japanese_frequency_preparation_is_reviewable_and_cli_reachable(tmp_path):
    from typer.testing import CliRunner

    from multilang.vocabulary_cli import create_vocabulary_app

    dictionary, dictionary_hash = write_source(tmp_path)
    frequency, frequency_hash = write_source(tmp_path, TUBELEX, "tubelex.tsv.xz")
    output = tmp_path / "prepared"
    result = CliRunner().invoke(create_vocabulary_app(), ["prepare-japanese", str(dictionary),
        dictionary_hash, str(frequency), frequency_hash, str(output), "--candidate-limit", "2"])
    assert result.exit_code == 0, result.output
    manifest = json.loads((output / "manifest.json").read_text())
    assert not manifest["production_eligible"]
    report = json.loads((output / "frequency-comparison.json").read_text())
    assert report["source_sha256"] == frequency_hash
    assert report["selected_count"] == 2
    assert report["with_lexical_evidence"] == 1
    assert report["without_lexical_evidence"] == ["食べる"]
    assert report["ranking_policy"] == "count-desc-channels-desc-word-v1"
    assert "frequency-comparison.json" in manifest["files"]
    # The existing review path can consume this preparation unchanged.
    result = CliRunner().invoke(create_vocabulary_app(), ["review-template", str(output),
        "jmdict-english", "snapshot", str(tmp_path / "review.json")])
    assert result.exit_code == 0, result.output
