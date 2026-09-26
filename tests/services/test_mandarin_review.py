"""Source-grounded Mandarin review must retain ambiguity and provenance."""

import gzip
import hashlib

import pytest


def _source(tmp_path, text):
    path = tmp_path / "cedict.txt.gz"
    path.write_bytes(gzip.compress(text.encode()))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_cedict_preserves_homographs_and_source_identity(tmp_path):
    from multilang.services.mandarin_review import read_cedict

    path, digest = _source(tmp_path, "# CC-CEDICT\n"
                           "長 长 [chang2] /long/\n長 长 [zhang3] /to grow/\n")
    entries = list(read_cedict(path, expected_sha256=digest))
    assert [e.numbered_pinyin for e in entries] == ["chang2", "zhang3"]
    assert [e.traditional for e in entries] == ["長", "長"]
    assert entries[0].source_sha256 == digest
    assert entries[0].line_number == 2
    assert entries[0].line_sha256 != entries[1].line_sha256
    assert entries[0].glosses == ("long",)


def test_cedict_checksum_and_malformed_records_fail_closed(tmp_path):
    from multilang.services.mandarin_review import read_cedict

    path, digest = _source(tmp_path, "銀行 银行 [yin2 hang2] /bank/\n")
    with pytest.raises(ValueError, match="checksum"):
        list(read_cedict(path, expected_sha256="0" * 64))
    path, digest = _source(tmp_path, "銀行 银行 [[yin2hang2]] /bank/\n")
    with pytest.raises(ValueError, match="v1"):
        list(read_cedict(path, expected_sha256=digest))


def test_lookup_recovers_all_source_traditional_forms_without_merging(tmp_path):
    from multilang.services.mandarin_review import lookup_forms, read_cedict

    path, digest = _source(tmp_path, "乾 干 [gan1] /dry/\n幹 干 [gan4] /to work/\n")
    entries = list(read_cedict(path, expected_sha256=digest))
    forms = lookup_forms(["干"], entries)
    assert set(forms) >= {"干", "乾", "幹"}
    assert forms["乾"] == [{"seed": "干", "kind": "cedict-pair",
                           "source_record_sha256": entries[0].line_sha256}]


def test_only_explicit_mandarin_lexical_readings_count():
    from multilang.services.mandarin_review import mandarin_readings

    record = {"sounds": [
        {"zh_pron": "liǎojiě", "tags": ["Mandarin", "Pinyin", "Standard-Chinese"]},
        {"zh_pron": "liáojiě", "tags": ["Mandarin", "Pinyin", "phonetic"]},
        {"zh_pron": "other", "tags": ["Cantonese", "Pinyin"]},
        {"zh_pron": "liáojie", "tags": ["Mandarin", "Nanjing", "Pinyin"]},
    ]}
    assert mandarin_readings(record) == ("liǎojiě",)


def test_pinyin_comparison_keeps_tones_and_neutral_readings():
    from multilang.services.mandarin_review import pinyin_key

    assert pinyin_key("nu:3 er2") == pinyin_key("nǚ'ér")
    assert pinyin_key("xi3 huan5") == pinyin_key("xǐhuan")
    assert pinyin_key("xi3 huan1") != pinyin_key("xǐhuan")
    assert pinyin_key("liǎojiě") != pinyin_key("liáojiě")
    assert pinyin_key("xíng (Mainland)") is None


def test_traditional_lookup_hint_is_not_sense_approval():
    from multilang.services.mandarin_review import lexical_evidence

    record = {"word": "銀行", "pos": "noun", "sounds": [
        {"zh_pron": "yínháng", "tags": ["Mandarin", "Pinyin"]}],
        "senses": [{"glosses": ["bank"], "id": "bank-source-id"},
                   {"glosses": ["dialect sense"], "tags": ["Cantonese"]}]}
    evidence = lexical_evidence(record)
    assert evidence["source_word"] == "銀行"
    assert evidence["production_eligible"] is False
    assert evidence["senses"][0]["scope"] == "mandarin-candidate"
    assert evidence["senses"][1]["scope"] == "other-variety"


def test_audit_exposes_ambiguous_reading_even_when_default_matches(tmp_path):
    from multilang.services.mandarin_review import audit_word, read_cedict

    path, digest = _source(tmp_path, "長 长 [chang2] /long/\n長 长 [zhang3] /to grow/\n")
    entries = list(read_cedict(path, expected_sha256=digest))
    result = audit_word("长", entries=entries, records=[])
    assert "multiple-readings" in result["flags"]
    assert "missing-structured-mandarin-sense" in result["flags"]
    assert result["production_eligible"] is False
    assert result["status"] == "needs-context-review"


def test_audit_recovers_traditional_pos_without_claiming_approval(tmp_path):
    from multilang.services.mandarin_review import audit_word, read_cedict

    path, digest = _source(tmp_path, "銀行 银行 [yin2 hang2] /bank/\n")
    entries = list(read_cedict(path, expected_sha256=digest))
    record = {"word": "銀行", "pos": "noun", "sounds": [
        {"zh_pron": "yínháng", "tags": ["Mandarin", "Pinyin"]}],
        "senses": [{"glosses": ["bank"], "id": "bank-source-id"}]}
    result = audit_word("银行", entries=entries, records=[record])
    assert result["status"] == "dictionary-supported-candidate"
    assert result["production_eligible"] is False
    assert result["wiktextract"][0]["source_pos"] == "noun"
    assert result["cedict"][0]["line_sha256"] == entries[0].line_sha256


def test_traditional_homograph_with_another_reading_does_not_qualify_seed(tmp_path):
    from multilang.services.mandarin_review import audit_word, read_cedict

    path, digest = _source(tmp_path, "乾 干 [gan1] /dry/\n")
    entries = list(read_cedict(path, expected_sha256=digest))
    record = {"word": "乾", "pos": "noun", "sounds": [
        {"zh_pron": "qián", "tags": ["Mandarin", "Pinyin"]}],
        "senses": [{"glosses": ["the Qian trigram"]}]}
    result = audit_word("干", entries=entries, records=[record])
    assert result["structured_mandarin_record_count"] == 0
    assert "missing-structured-mandarin-sense" in result["flags"]


def test_unknown_source_pos_is_not_treated_as_multilang_pos_support(tmp_path):
    from multilang.services.mandarin_review import audit_word, read_cedict

    path, digest = _source(tmp_path, "銀行 银行 [yin2 hang2] /bank/\n")
    entries = list(read_cedict(path, expected_sha256=digest))
    record = {"word": "銀行", "pos": "unmapped-pos", "sounds": [
        {"zh_pron": "yínháng", "tags": ["Mandarin", "Pinyin"]}],
        "senses": [{"glosses": ["bank"]}]}
    result = audit_word("银行", entries=entries, records=[record])
    assert result["structured_mandarin_record_count"] == 0


def _review(**changes):
    from multilang.services.mandarin_orthography import MandarinOrthography
    from multilang.services.mandarin_review import MandarinPronunciationReview

    values = dict(word="长", sentence="这条路很长。", orthography=MandarinOrthography(
        word_pinyin="cháng", word_traditional="長",
        sentence_pinyin="zhè tiáo lù hěn cháng。", sentence_traditional="這條路很長。",
    ), evidence_record_sha256=("a" * 64,))
    values.update(changes)
    return MandarinPronunciationReview(**values)


def test_context_review_is_exact_and_never_falls_back_to_wrong_default():
    from multilang.services.mandarin_orthography import MandarinOrthographyError
    from multilang.services.mandarin_review import ReviewedMandarinOrthographyService

    service = ReviewedMandarinOrthographyService([_review()])
    value = service.derive(word="长", sentence="这条路很长。")
    assert value.word_pinyin == "cháng"
    with pytest.raises(MandarinOrthographyError, match="review"):
        service.derive(word="长", sentence="孩子长高了。")


def test_review_rejects_misalignment_and_wrong_word_context():
    from dataclasses import replace

    from multilang.services.mandarin_orthography import MandarinOrthographyError

    orthography = _review().orthography
    with pytest.raises(MandarinOrthographyError, match="align"):
        _review(orthography=replace(orthography, sentence_pinyin="zhè tiáo lù。"))
    with pytest.raises(MandarinOrthographyError, match="target"):
        _review(orthography=replace(orthography, word_pinyin="zhǎng"))
    with pytest.raises(MandarinOrthographyError, match="Traditional"):
        _review(orthography=replace(orthography, sentence_traditional="這條路很短。"))


def test_review_requires_evidence_and_rejects_duplicate_contexts():
    from multilang.services.mandarin_orthography import MandarinOrthographyError
    from multilang.services.mandarin_review import ReviewedMandarinOrthographyService

    with pytest.raises(MandarinOrthographyError, match="evidence"):
        _review(evidence_record_sha256=())
    with pytest.raises(MandarinOrthographyError, match="duplicate"):
        ReviewedMandarinOrthographyService([_review(), _review()])


def test_review_accepts_normal_chinese_fullwidth_punctuation():
    from multilang.services.mandarin_orthography import MandarinOrthography
    from multilang.services.mandarin_review import (
        MandarinPronunciationReview,
        ReviewedMandarinOrthographyService,
    )

    review = MandarinPronunciationReview(
        word="你好", sentence="你好，很高兴见到你。",
        orthography=MandarinOrthography(
            word_pinyin="nǐ hǎo", word_traditional="你好",
            sentence_pinyin="nǐ hǎo，hěn gāo xìng jiàn dào nǐ。",
            sentence_traditional="你好，很高興見到你。",
        ), evidence_record_sha256=("b" * 64,),
    )
    service = ReviewedMandarinOrthographyService([review])
    assert service.derive(word=review.word, sentence=review.sentence) == review.orthography
