import hashlib
import io
import tarfile

import pytest


def fixtures(tmp_path):
    lexical = tmp_path / "hr.tab"
    lexical.write_text(
        "# Croatian Wordnet\n00001740-n\thrv:lemma\tkuća\n00002098-n\thrv:lemma\tkuća\n"
    )
    glosses = tmp_path / "wordnet.tar.gz"
    content = (
        b"00001740 03 n 01 house 0 000 | A house.\n00002098 03 n 01 family 0 000 | A family.\n"
    )
    with tarfile.open(glosses, "w:gz") as archive:
        entry = tarfile.TarInfo("WordNet-3.0/dict/data.noun")
        entry.size = len(content)
        archive.addfile(entry, io.BytesIO(content))
    return lexical, glosses


def test_croatian_source_links_join_exact_wordnet30_senses(tmp_path):
    from multilang.services.wordnet_sources import read_croatian_wordnet

    lexical, glosses = fixtures(tmp_path)
    rows = list(
        read_croatian_wordnet(
            lexical,
            expected_sha256=hashlib.sha256(lexical.read_bytes()).hexdigest(),
            glosses=glosses,
            glosses_sha256=hashlib.sha256(glosses.read_bytes()).hexdigest(),
        )
    )
    assert [row.lemma for row in rows] == ["kuća", "kuća"]
    assert [row.glosses for row in rows] == [("A house.",), ("A family.",)]
    assert rows[0].source_sense_ids == ("pwn30:00001740-n",)
    assert rows[0].candidate_id != rows[1].candidate_id
    assert all(row.stable_sense_id is None and row.review_status == "pending" for row in rows)


def test_missing_glosses_and_tar_links_do_not_create_invented_meanings(tmp_path):
    from multilang.services.wordnet_sources import read_croatian_wordnet

    lexical, glosses = fixtures(tmp_path)
    with tarfile.open(glosses, "w:gz") as archive:
        entry = tarfile.TarInfo("WordNet-3.0/dict/data.noun")
        entry.type = tarfile.SYMTYPE
        entry.linkname = "/etc/passwd"
        archive.addfile(entry)
    with pytest.raises(ValueError, match="regular|gloss"):
        list(
            read_croatian_wordnet(
                lexical,
                expected_sha256=hashlib.sha256(lexical.read_bytes()).hexdigest(),
                glosses=glosses,
                glosses_sha256=hashlib.sha256(glosses.read_bytes()).hexdigest(),
            )
        )


def test_croatian_preparation_retains_both_source_checksums(tmp_path):
    from multilang.services.vocabulary_preparation import prepare_vocabulary

    lexical, glosses = fixtures(tmp_path)
    gloss_hash = hashlib.sha256(glosses.read_bytes()).hexdigest()
    result = prepare_vocabulary(
        language="hr",
        dictionary=lexical,
        dictionary_sha256=hashlib.sha256(lexical.read_bytes()).hexdigest(),
        dictionary_format="croatian-wordnet",
        glosses=glosses,
        glosses_sha256=gloss_hash,
        output=tmp_path / "prepared",
    )
    assert result["lexical_candidate_count"] == 2
    assert result["dictionary_format"] == "croatian-wordnet"
    assert result["glosses_sha256"] == gloss_hash
    assert result["resolved_identity_count"] == 0


@pytest.mark.parametrize("metadata_type", [tarfile.GNUTYPE_LONGNAME, tarfile.XHDTYPE])
def test_tar_extension_metadata_is_included_in_expanded_byte_limit(tmp_path, metadata_type):
    import gzip

    from multilang.services.vocabulary_sources import SourceLimits
    from multilang.services.wordnet_sources import read_croatian_wordnet

    lexical, glosses = fixtures(tmp_path)
    header = tarfile.TarInfo("././@LongLink")
    header.type, header.size = metadata_type, 4096
    glosses.write_bytes(gzip.compress(header.tobuf() + b"x" * 4096 + b"\0" * 1024))
    with pytest.raises(ValueError, match="expanded.*limit"):
        list(
            read_croatian_wordnet(
                lexical,
                expected_sha256=hashlib.sha256(lexical.read_bytes()).hexdigest(),
                glosses=glosses,
                glosses_sha256=hashlib.sha256(glosses.read_bytes()).hexdigest(),
                limits=SourceLimits(max_expanded_bytes=1024),
            )
        )
