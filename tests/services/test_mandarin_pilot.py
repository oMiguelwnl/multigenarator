import pytest

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow


def row():
    return ExportCardRow(identity=ExportCardIdentity(language="zh", source_type="word-list",
        job_id="test-zh", item_key="long", lemma_key="长", sort_index=1),
        word="长", front_of_card="长", definitions="adjetivo: longo",
        example_sentence="这条路很长。", translation="Esta estrada é longa.",
        mandarin_word_pinyin="cháng", mandarin_word_traditional="長",
        mandarin_sentence_pinyin="zhè tiáo lù hěn cháng。", mandarin_sentence_traditional="這條路很長。")


def test_pilot_prepares_two_audio_requests_without_calls_and_detects_card_drift(tmp_path):
    from test_mandarin_pronunciation_store import bundle, save

    from multilang.services.mandarin_pilot import prepare_pilot

    path, digest = save(tmp_path, bundle())
    result = prepare_pilot(rows=[row()], bundle_path=path, bundle_sha256=digest, output=tmp_path / "pilot")
    assert result["audio_request_count"] == 2
    assert result["provider_calls_executed"] == 0
    bad = row().model_copy(update={"mandarin_word_pinyin": "zhǎng"})
    with pytest.raises(ValueError, match="reading"):
        prepare_pilot(rows=[bad], bundle_path=path, bundle_sha256=digest, output=tmp_path / "bad")


def test_pilot_export_refuses_missing_or_unverified_audio(tmp_path):
    from test_mandarin_pronunciation_store import bundle, save

    from multilang.services.mandarin_pilot import prepare_pilot, verified_pilot_rows

    path, digest = save(tmp_path, bundle())
    root = tmp_path / "pilot"
    prepare_pilot(rows=[row()], bundle_path=path, bundle_sha256=digest, output=root)
    with pytest.raises(ValueError, match="audio"):
        verified_pilot_rows(root)


@pytest.mark.parametrize('mutation', ['path', 'characters', 'duplicate'])
def test_pilot_rejects_internally_inconsistent_input_before_network_or_media(tmp_path, mutation):
    from test_mandarin_pronunciation_store import bundle, save

    from multilang.domain.lexical_identity import canonical_sha256
    from multilang.services.mandarin_pilot import _input, prepare_pilot
    from multilang.services.qualification_machine_runner import (
        json_bytes,
        persist_artifact,
        read_json,
    )

    path, digest = save(tmp_path, bundle())
    original = tmp_path / 'original'
    prepare_pilot(rows=[row()], bundle_path=path, bundle_sha256=digest, output=original)
    payload = read_json(original / 'input/pilot.json')
    if mutation == 'path':
        payload['requests'][0]['id'] = '../outside'
    elif mutation == 'characters':
        payload['summary']['spoken_characters'] = 0
    else:
        payload['requests'][1] = payload['requests'][0]
    root = tmp_path / 'mutated'
    persist_artifact(root / 'input', kind='mandarin-audio-pilot-input', binding=canonical_sha256(payload),
                     files={'pilot.json': json_bytes(payload)})
    with pytest.raises(ValueError, match='pilot'):
        _input(root)
