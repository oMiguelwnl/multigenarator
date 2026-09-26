import hashlib
import json

import pytest


def bundle():
    return {"schema_version": "mandarin-pronunciation-1", "reviewer": "ChatGPT active session",
            "independent_human_review": False, "contexts": [{
                "word": "长", "sentence": "这条路很长。",
                "orthography": {"word_pinyin": "cháng", "word_traditional": "長",
                    "sentence_pinyin": "zhè tiáo lù hěn cháng。", "sentence_traditional": "這條路很長。"},
                "word_spoken_pinyin": "cháng", "sentence_spoken_pinyin": "zhè tiáo lù hěn cháng。",
                "evidence_record_sha256": ["a" * 64],
            }]}


def save(tmp_path, data):
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_store_uses_reviewed_context_and_refuses_changed_sentence(tmp_path):
    from multilang.services.mandarin_pronunciation_store import load_pronunciation_store

    path, digest = save(tmp_path, bundle())
    store = load_pronunciation_store(path, digest)
    assert store.derive(word="长", sentence="这条路很长。").word_pinyin == "cháng"
    assert store.spoken(word="长", sentence="这条路很长。") == ("cháng", "zhè tiáo lù hěn cháng。")
    with pytest.raises(ValueError, match="review"):
        store.derive(word="长", sentence="孩子长高了。")
    with pytest.raises(ValueError, match="checksum"):
        load_pronunciation_store(path, "b" * 64)
    with pytest.raises(ValueError):
        load_pronunciation_store(path, None)


def test_empty_store_blocks_automatic_pronunciation_fallback():
    from multilang.services.mandarin_pronunciation_store import load_pronunciation_store

    with pytest.raises(ValueError, match="review"):
        load_pronunciation_store(None, None).derive(word="长", sentence="这条路很长。")


def test_spoken_tone_can_differ_but_not_the_segmental_reading(tmp_path):
    from multilang.services.mandarin_pronunciation_store import load_pronunciation_store

    data = bundle()
    data["contexts"][0]["word_spoken_pinyin"] = "zhǎng"
    path, digest = save(tmp_path, data)
    with pytest.raises(ValueError, match="spoken"):
        load_pronunciation_store(path, digest)


def test_ssml_uses_reviewed_tones_neutral_tone_and_escapes_text():
    from multilang.services.mandarin_pronunciation_store import mandarin_phoneme_body

    value = mandarin_phoneme_body("你好，朋友。", "ní hǎo，péng you。")
    assert 'ph="ni 2 - hao 3">你好</phoneme>，' in value
    assert 'ph="peng 2 - you 5">朋友</phoneme>。' in value
    assert 'alphabet="sapi"' in value
    with pytest.raises(ValueError):
        mandarin_phoneme_body("你好", 'nǐ <break/> hǎo')
    with pytest.raises(ValueError):
        mandarin_phoneme_body("你好", 'nǐ')


def test_sapi_encodes_umlaut_vowel_and_ue_final_as_documented():
    from multilang.services.mandarin_pronunciation_store import mandarin_phoneme_body

    assert 'ph="nv 3"' in mandarin_phoneme_body("女", "nǚ")
    assert 'ph="lue 4"' in mandarin_phoneme_body("略", "lüè")


def test_store_rejects_duplicate_contexts_and_unknown_authority_fields(tmp_path):
    from multilang.services.mandarin_pronunciation_store import load_pronunciation_store

    for mutate in (lambda d: d["contexts"].append(d["contexts"][0]),
                   lambda d: d.update(production_eligible=True)):
        data = bundle()
        mutate(data)
        path, digest = save(tmp_path, data)
        with pytest.raises(ValueError):
            load_pronunciation_store(path, digest)
