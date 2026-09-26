from hashlib import sha256

import pytest

from multilang.domain.highlights import HighlightInputMode, HighlightProvenance, NormalizedHighlight
from multilang.domain.jobs import SupportedLanguage
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates
from multilang.services.japanese_furigana import format_japanese_furigana
from multilang.services.text_validation import _japanese_contains_target


def test_explicit_word_reading_drives_furigana_and_romaji():
    from multilang.services.japanese_romaji import romanize_japanese

    assert format_japanese_furigana("人気", reading="ひとけ") == "人気[ひとけ]"
    assert romanize_japanese("人気", reading="ひとけ") == "Hitoke"
    assert format_japanese_furigana("食べる", reading="たべる") == "食[た]べる"
    with pytest.raises(ValueError):
        format_japanese_furigana("人気", reading="<script>")


def test_sentence_matching_respects_reviewed_homograph_reading():
    assert _japanese_contains_target("この店は人気がある。", display_form="人気", lemma="人気", reading="にんき")
    assert not _japanese_contains_target("この店は人気がある。", display_form="人気", lemma="人気", reading="ひとけ")


def test_reviewed_reading_survives_database_json_provenance():
    from types import SimpleNamespace

    from multilang.services.japanese_analysis import candidate_japanese_reading
    row = SimpleNamespace(spoken_form="きょう", provenance={"source": "JMdict", "notes": ["japanese_reading=きょう"]})
    assert candidate_japanese_reading(row) == "きょう"


def test_text_generation_restores_the_reviewed_japanese_spoken_form():
    from types import SimpleNamespace

    from multilang.services.generate_text_items import GenerateTextItemsService
    from multilang.services.japanese_analysis import candidate_japanese_reading
    row = SimpleNamespace(submitted_form="今日", display_form="今日", lemma="今日", lemma_key="ja-today",
        frequency_rank=1, frequency_level=1, definitions_html="noun: today", definition_language="en",
        ipa=None, spoken_form="きょう", translation_target_language="en", grounding_status="grounded",
        warning_code=None, warning_detail=None, korean_identity=None,
        provenance={"source": "JMdict", "notes": ["japanese_reading=きょう"]})
    restored = GenerateTextItemsService._to_candidate(None, row)
    assert candidate_japanese_reading(restored) == "きょう"


@pytest.mark.parametrize(("sentence", "target", "expected"), [
    ("私は学生です。", "生", False),
    ("日本に行きます。", "日", False),
    ("昨日パンを食べました。", "食べる", True),
    ("学校に行きました。", "行く", True),
    ("図書館で勉強します。", "図書館", True),
])
def test_japanese_target_requires_lexical_boundaries(sentence, target, expected):
    assert _japanese_contains_target(sentence, display_form=target, lemma=target) is expected


def test_analysis_preserves_spans_base_reading_pos_and_dictionary_identity():
    from multilang.services.japanese_analysis import analyze_japanese, japanese_dictionary_identity

    text = " 昨日、パンを食べました。 "
    tokens = analyze_japanese(text)
    eaten = next(token for token in tokens if token.surface == "食べ")
    assert text[eaten.start:eaten.end] == "食べ"
    assert eaten.lemma == eaten.orthographic_base == "食べる"
    assert eaten.reading == "たべ"
    assert eaten.lemma_reading == "たべる"
    assert eaten.pos == "VERB" and eaten.known
    fingerprint = japanese_dictionary_identity()
    assert len(fingerprint["model_artifact_sha256"]) == 64


def test_japanese_target_can_require_a_reading():
    from multilang.services.japanese_analysis import japanese_target_spans

    assert japanese_target_spans("今日は晴れです。", "今日", reading="きょう")
    assert not japanese_target_spans("今日は晴れです。", "今日", reading="こんにち")


def test_furigana_preserves_source_whitespace_and_punctuation():
    assert format_japanese_furigana("学校 に\n行く。") == "学校[がっこう] に\n行[い]く。"


def highlight(text):
    return NormalizedHighlight(highlight_id="synthetic-ja", text=text,
                               provenance=HighlightProvenance(source_path="synthetic", source_format="text",
                               source_index=0, content_hash=sha256(text.encode()).hexdigest()))


def test_highlight_text_extracts_lemmas_and_keeps_private_context_out_of_candidates():
    text = "学校に行きました。昨日パンを食べました。"
    result = extract_highlight_candidates([highlight(text)], language=SupportedLanguage.JA)
    forms = {c.display_form for c in result.candidates}
    assert {"学校", "行く", "昨日", "パン", "食べる"} <= forms
    assert "行き" not in forms and "食べ" not in forms
    assert not forms & {"に", "を", "ます", "た"}
    assert text not in result.model_dump_json()


def test_japanese_highlights_ignore_layout_spaces_and_numeric_dates():
    result = extract_highlight_candidates([highlight(" 「学校」に　2026年に行きます。 ")], language=SupportedLanguage.JA)
    assert not result.errors
    assert {"学校", "行く"} <= {candidate.display_form for candidate in result.candidates}
    assert "2026" not in {candidate.display_form for candidate in result.candidates}


def test_highlight_vocabulary_keeps_intentional_expression():
    result = extract_highlight_candidates([highlight("気を付ける")], language=SupportedLanguage.JA,
                                          input_mode=HighlightInputMode.VOCABULARY)
    assert [c.display_form for c in result.candidates] == ["気を付ける"]


def test_unknown_model_does_not_fall_back_to_substring_matching(monkeypatch):
    from multilang.services import japanese_analysis

    def unavailable():
        raise japanese_analysis.JapaneseAnalysisError("dictionary unavailable")

    monkeypatch.setattr(japanese_analysis, "japanese_tagger", unavailable)
    assert not _japanese_contains_target("学校に行く。", display_form="学校", lemma="学校")
    result = extract_highlight_candidates([highlight("学校に行く。")], language=SupportedLanguage.JA)
    assert not result.candidates
    assert result.errors[0].reason_code == "japanese_analysis_unavailable"


def test_highlight_evidence_keeps_offsets_and_reaches_lexical_lookup(tmp_path):
    import json

    from multilang.services.lexical_grounding import LexicalGroundingService
    from multilang.services.lexical_lookup import LexicalLookup

    text = "今日は晴れです。"
    extraction = extract_highlight_candidates([highlight(text)], language=SupportedLanguage.JA)
    candidate = next(c for c in extraction.candidates if c.display_form == "今日")
    evidence = candidate.japanese_evidence
    assert text[evidence.start:evidence.end] == "今日"
    assert evidence.reading == "きょう"
    directory = tmp_path / "ja"
    directory.mkdir()
    records = [{"term": "今日", "display_form": "今日", "lemma": "今日", "definitions": ["この日。"],
        "definition_language": "ja", "part_of_speech": "noun", "source": "fixture",
        "sense_id": sense, "japanese_reading": reading} for sense, reading in [("today", "きょう"), ("nowadays", "こんにち")]]
    (directory / "lexical-index.json").write_text(json.dumps({"今日": records}, ensure_ascii=False))
    service = LexicalGroundingService(LexicalLookup(tmp_path))
    grounded = service.ground_highlight_candidate(language=SupportedLanguage.JA, candidate=candidate)
    assert grounded.warning_code != "highlight_grounding_missing"
    assert grounded.spoken_form == "きょう"
    assert grounded.lemma_key == candidate.lemma_key


def test_vocabulary_highlight_normalizes_inflection_but_preserves_function_words():
    result = extract_highlight_candidates([highlight("食べました")], language=SupportedLanguage.JA,
                                          input_mode=HighlightInputMode.VOCABULARY)
    assert [c.display_form for c in result.candidates] == ["食べる"]
    result = extract_highlight_candidates([highlight("に")], language=SupportedLanguage.JA,
                                          input_mode=HighlightInputMode.VOCABULARY)
    assert [c.display_form for c in result.candidates] == ["に"]
