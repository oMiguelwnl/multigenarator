import json
from hashlib import sha256

import pytest

from multilang.services.native_imports import (
    CSVImporter,
    DictionaryImporter,
    ExternalAPIImporter,
    ImportSource,
)


def source(data):
    return ImportSource(
        source_id="fixture",
        version="1",
        sha256=sha256(data).hexdigest(),
        language="en",
        profile_version="1",
        normalizer_version="nfc-1",
        analyzer_version="reviewed-1",
        license_id="fixture-original",
        attribution="Test authors",
    )


def test_csv_import_preserves_homographs_and_rejects_missing_sense_atomically():
    data = b"lemma,pos,sense\nrun,VERB,move\nrun,NOUN,event\n"
    result = CSVImporter().parse(data, source(data))
    assert len({identity.lexical_identity_id for identity in result}) == 2
    broken = data + b"bank,NOUN,\n"
    with pytest.raises(ValueError, match="sense"):
        CSVImporter().parse(broken, source(broken))


def test_source_integrity_and_closed_dictionary_schema():
    data = json.dumps([{"lemma": "run", "pos": "VERB", "sense": "move"}]).encode()
    assert DictionaryImporter().parse(data, source(data))[0].normalized_lemma == "run"
    with pytest.raises(ValueError, match="checksum"):
        DictionaryImporter().parse(data + b" ", source(data))
    bad = json.dumps([{"lemma": "run", "pos": "VERB", "sense": "move", "core_rank": 1}]).encode()
    with pytest.raises(ValueError):
        DictionaryImporter().parse(bad, source(bad))


def test_external_importer_does_not_contact_unregistered_or_private_hosts():
    importer = ExternalAPIImporter(allowed_hosts={"example.org"})
    for url in (
        "http://example.org/file",
        "https://localhost/file",
        "https://127.0.0.1/file",
        "https://example.org@evil.org/file",
        "https://example.org:444/file",
    ):
        with pytest.raises(ValueError):
            importer.validate_url(url)


def test_import_limits_apply_before_parsing():
    data = b"lemma,pos,sense\nrun,VERB,move\n"
    with pytest.raises(ValueError, match="limit"):
        CSVImporter(max_bytes=4).parse(data, source(data))
