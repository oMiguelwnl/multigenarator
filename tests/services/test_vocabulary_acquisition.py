import gzip
import hashlib
import json

import httpx
import pytest


def test_catalog_download_is_bounded_and_content_addressed(tmp_path):
    from multilang.services.vocabulary_acquisition import acquire_source

    content = b'# sent_id = sample\n'
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=httpx.ByteStream(content)))
    with httpx.Client(transport=transport) as client:
        result = acquire_source('en', 'corpus-test', tmp_path, client=client)
    assert result['sha256'] == hashlib.sha256(content).hexdigest()
    assert (tmp_path / result['file']).read_bytes() == content
    assert result['redistribution_approved'] is False
    assert result['source_url'].startswith('https://raw.githubusercontent.com/UniversalDependencies/')


def test_catalog_download_does_not_follow_redirects_or_leave_oversized_sources(tmp_path):
    from multilang.services.vocabulary_acquisition import acquire_source

    for response in [httpx.Response(302, headers={'location': 'http://127.0.0.1/private'}),
                     httpx.Response(200, content=b'123456'),
                     httpx.Response(200, stream=httpx.ByteStream(b'123456'))]:
        with httpx.Client(transport=httpx.MockTransport(lambda request: response)) as client:
            with pytest.raises((ValueError, httpx.HTTPStatusError)):
                acquire_source('en', 'corpus-test', tmp_path, max_bytes=5, client=client)
    assert not list(tmp_path.glob('*.conllu'))
    with pytest.raises(ValueError):
        acquire_source('en', 'https://example.com/file', tmp_path)


def test_multilingual_split_preserves_spelling_and_does_not_alias_languages(tmp_path):
    from multilang.services.vocabulary_acquisition import split_wiktextract

    records = [{'word': word, 'lang_code': lang, 'pos': 'noun', 'senses': [{'glosses': ['x']}]}
               for lang, word in [('de', 'Haus'), ('de', 'HAUS'), ('en', 'house'),
                                  ('sh', 'kuća'), ('hr', 'kuća')]]
    source = tmp_path / 'source.jsonl.gz'
    source.write_bytes(gzip.compress(('\n'.join(json.dumps(r) for r in records)+'\n').encode()))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    result = split_wiktextract(source, digest, tmp_path / 'split',
                              {'de': {'haus'}, 'en': {'house'}, 'hr': {'kuća'}})
    german = [json.loads(line) for line in (tmp_path/'split/de.jsonl').read_text().splitlines()]
    assert [r['word'] for r in german] == ['Haus', 'HAUS']
    assert result['languages']['hr']['record_count'] == 1
    assert result['source_sha256'] == digest
    assert result['selection_policy'] == 'NFC-casefold-candidate-filter-only'
    assert result['production_eligible'] is False


def test_multilingual_split_discards_partial_output_on_source_drift(tmp_path):
    from multilang.services.vocabulary_acquisition import split_wiktextract

    source = tmp_path / 'source.jsonl'
    source.write_text('{}\n')
    with pytest.raises(ValueError, match='checksum'):
        split_wiktextract(source, '0'*64, tmp_path/'split', {'en': {'house'}})
    assert not (tmp_path/'split').exists()
