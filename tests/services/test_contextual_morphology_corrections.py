"""Conservative corrections backed by source spans and published tag contracts."""

from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace as NS

import pytest


def analyze_stanza(monkeypatch, text, *, language="ru", pos="NUM", feats="NumType=Card"):
    from multilang.services import contextual_morphology as module

    word = NS(text=text, lemma=text, upos=pos, feats=feats)
    doc = NS(sentences=[NS(tokens=[NS(text=text, start_char=0, end_char=len(text), words=[word])])])
    monkeypatch.setattr(
        module, "model_status", lambda *a, **k: {"available": True, "backend": "stanza"}
    )
    monkeypatch.setattr(module, "load_stanza_pipeline", lambda *a, **k: lambda text: doc)
    return module.LocalContextualMorphologyService(model_root=Path("/unused")).analyze(
        language, text
    )


@pytest.mark.parametrize(("surface", "pos"), [("42", "NUM"), ("2026", "ADJ"), ("٠٣", "NUM")])
def test_russian_decimal_numerals_have_explicit_written_form(monkeypatch, surface, pos):
    result = analyze_stanza(monkeypatch, surface, pos=pos)
    assert result.status == "complete"
    assert dict(result.tokens[0].features) == {"NumForm": "Digit", "NumType": "Card"}
    assert (result.tokens[0].lemma, result.tokens[0].text) == (surface, surface)


@pytest.mark.parametrize("surface", ["IV", "Ⅳ", "три", "2-й", "3.14", "1/2", "²", "-4"])
def test_numeric_shape_does_not_invent_ambiguous_numeral_features(monkeypatch, surface):
    result = analyze_stanza(monkeypatch, surface)
    assert dict(result.tokens[0].features) == {"NumType": "Card"}


def test_explicit_model_features_are_never_replaced(monkeypatch):
    result = analyze_stanza(monkeypatch, "42", feats="NumForm=Word|NumType=Card")
    assert dict(result.tokens[0].features) == {"NumForm": "Word", "NumType": "Card"}


@pytest.mark.parametrize(("language", "pos"), [("de", "NUM"), ("tr", "NUM"), ("ru", "PROPN")])
def test_decimal_completion_is_limited_to_supported_language_and_pos(monkeypatch, language, pos):
    result = analyze_stanza(monkeypatch, "42", language=language, pos=pos)
    assert dict(result.tokens[0].features) == {"NumType": "Card"}


def test_changed_projection_gets_a_new_fingerprint_and_invalidates_old_evidence(monkeypatch):
    from multilang.domain.lexical_identity import canonical_sha256

    result = analyze_stanza(monkeypatch, "42")
    status = {"available": True, "backend": "stanza"}
    assert result.analyzer_version == "contextual-morphology-4"
    assert result.model_fingerprint == canonical_sha256(
        {"policy": "contextual-morphology-4", **status}
    )
    assert result.model_fingerprint != canonical_sha256(
        {"policy": "contextual-morphology-3", **status}
    )


@pytest.mark.parametrize(
    ("pos1", "pos2", "surface", "lemma", "expected"),
    [
        ("接頭辞", "*", "お", "御", "NOUN"),
        ("接尾辞", "名詞的", "者", "者", "NOUN"),
        ("接尾辞", "形状詞的", "的", "的", "PART"),
        ("接尾辞", "形容詞的", "っぽく", "ぽい", "PART"),
    ],
)
def test_japanese_adapter_accepts_documented_dictionary_affixes(
    monkeypatch, pos1, pos2, surface, lemma, expected
):
    from multilang.services import contextual_morphology as module

    Feature = namedtuple("Feature", "pos1 pos2 lemma")
    token = NS(surface=surface, white_space="", is_unk=False, feature=Feature(pos1, pos2, lemma))
    status = {"available": True, "backend": "fugashi"}
    monkeypatch.setattr(module, "model_status", lambda *a, **k: status)
    service = module.LocalContextualMorphologyService(model_root=Path("/unused"))
    fingerprint = module.canonical_sha256({"policy": module._ANALYZER_VERSION, **status})
    service._pipelines[("ja", fingerprint)] = lambda text: [token]
    result = service.analyze("ja", surface)
    assert result.status == "complete"
    assert [(t.text, t.lemma, t.pos) for t in result.tokens] == [(surface, lemma, expected)]


def kiwi_token(form, pos, start, length, *, word=0, sentence=0, lemma=None, oov=False):
    return NS(
        form=form,
        lemma=lemma or form,
        tag=pos,
        start=start,
        len=length,
        word_position=word,
        sent_position=sentence,
        oov=oov,
    )


def analyze_kiwi(monkeypatch, text, tokens, *, other=None):
    from multilang.services import contextual_morphology as module
    from multilang.services.korean_morphology import KiwiKoreanMorphologyService

    vendor = NS(
        analyze=lambda *a, **k: [(tokens, -1.0), (tokens if other is None else other, -2.0)]
    )
    pipeline = KiwiKoreanMorphologyService(analyzer_factory=lambda: vendor)
    status = {"available": True, "backend": "kiwi"}
    monkeypatch.setattr(module, "model_status", lambda *a, **k: status)
    service = module.LocalContextualMorphologyService(model_root=Path("/unused"))
    fingerprint = module.canonical_sha256({"policy": module._ANALYZER_VERSION, **status})
    service._pipelines[("ko", fingerprint)] = pipeline
    return service.analyze("ko", text)


def test_korean_vendor_spans_preserve_punctuation_and_sentence_boundaries(monkeypatch):
    text = "학교. 집."
    result = analyze_kiwi(
        monkeypatch,
        text,
        [
            kiwi_token("학교", "NNG", 0, 2),
            kiwi_token(".", "SF", 2, 1),
            kiwi_token("집", "NNG", 4, 1, sentence=1),
            kiwi_token(".", "SF", 5, 1, sentence=1),
        ],
    )
    assert result.status == "complete"
    assert [(t.text, t.start, t.end, t.pos) for t in result.tokens] == [
        ("학교", 0, 2, "NOUN"),
        (".", 2, 3, "PUNCT"),
        ("집", 4, 5, "NOUN"),
        (".", 5, 6, "PUNCT"),
    ]


def test_korean_nonlexical_group_keeps_its_source_without_erasing_neighbors(monkeypatch):
    result = analyze_kiwi(
        monkeypatch,
        "학교 ab 집",
        [
            kiwi_token("학교", "NNG", 0, 2),
            kiwi_token("ab", "SL", 3, 2, word=1),
            kiwi_token("집", "NNG", 6, 1, word=2),
        ],
    )
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["학교", "집"]
    assert [(b.text, b.start, b.end, b.reason) for b in result.blocked_spans] == [
        ("ab", 3, 5, "unresolved_morphology")
    ]


@pytest.mark.parametrize(
    ("surface", "tag", "upos"),
    [
        ("6.2", "SN", "NUM"),
        ("가", "JKS", "ADP"),
        ("가", "JKC", "ADP"),
        ("의", "JKG", "ADP"),
        ("를", "JKO", "ADP"),
        ("에", "JKB", "ADP"),
        ("아", "JKV", "ADP"),
        ("고", "JKQ", "ADP"),
        ("도", "JX", "ADP"),
        ("과", "JC", "CCONJ"),
    ],
)
def test_korean_supported_singletons_keep_native_lemma_and_exact_span(
    monkeypatch, surface, tag, upos
):
    import json

    text = "학교 " + surface
    result = analyze_kiwi(
        monkeypatch,
        text,
        [kiwi_token("학교", "NNG", 0, 2), kiwi_token(surface, tag, 3, len(surface), word=1)],
    )
    assert result.status == "complete"
    token = result.tokens[-1]
    assert (token.text, token.lemma, token.pos, token.start, token.end) == (
        surface,
        surface,
        upos,
        3,
        len(text),
    )
    assert json.loads(dict(token.features)["Morphemes"])[0]["raw_pos"] == tag


@pytest.mark.parametrize(("surface", "tag"), [("42", "SN"), ("를", "JKO")])
@pytest.mark.parametrize("oov_rank", [1, 2])
def test_korean_singleton_projection_cannot_bypass_oov_in_either_rank(
    monkeypatch, surface, tag, oov_rank
):
    noun = kiwi_token("학교", "NNG", 0, 2)
    first = [noun, kiwi_token(surface, tag, 3, len(surface), word=1, oov=oov_rank == 1)]
    other = [noun, kiwi_token(surface, tag, 3, len(surface), word=1, oov=oov_rank == 2)]
    result = analyze_kiwi(monkeypatch, "학교 " + surface, first, other=other)
    assert result.status == "inconclusive"
    assert [token.text for token in result.tokens] == ["학교"]
    assert [(span.text, span.reason) for span in result.blocked_spans] == [
        (surface, "unknown_lexical_token")
    ]


def test_korean_singleton_projection_keeps_top_two_tag_disagreement(monkeypatch):
    noun = kiwi_token("학교", "NNG", 0, 2)
    result = analyze_kiwi(
        monkeypatch,
        "학교 과",
        [noun, kiwi_token("과", "JC", 3, 1, word=1)],
        other=[noun, kiwi_token("과", "JKB", 3, 1, word=1)],
    )
    assert result.status == "inconclusive"
    assert not result.blocked_spans
    assert result.tokens[-1].pos == "CCONJ"


def test_korean_nonlexical_multi_morpheme_group_stays_blocked(monkeypatch):
    result = analyze_kiwi(
        monkeypatch,
        "학교 에도",
        [
            kiwi_token("학교", "NNG", 0, 2),
            kiwi_token("에", "JKB", 3, 1, word=1),
            kiwi_token("도", "JX", 4, 1, word=1),
        ],
    )
    assert result.status == "inconclusive"
    assert [(span.text, span.reason) for span in result.blocked_spans] == [
        ("에도", "unresolved_morphology")
    ]


def test_korean_singleton_requires_exact_native_form(monkeypatch):
    result = analyze_kiwi(
        monkeypatch,
        "학교 고",
        [kiwi_token("학교", "NNG", 0, 2), kiwi_token("라고", "JKQ", 3, 1, word=1)],
    )
    assert result.status == "inconclusive"
    assert [(span.text, span.reason) for span in result.blocked_spans] == [
        ("고", "unresolved_morphology")
    ]


def test_korean_native_symbol_punctuation_is_retained_at_its_proven_boundary(monkeypatch):
    result = analyze_kiwi(
        monkeypatch,
        "<학교>~",
        [
            kiwi_token("<", "SSO", 0, 1),
            kiwi_token("학교", "NNG", 1, 2),
            kiwi_token(">", "SSC", 3, 1),
            kiwi_token("~", "SO", 4, 1),
        ],
    )
    assert result.status == "complete"
    assert [(token.text, token.start, token.end, token.pos) for token in result.tokens] == [
        ("<", 0, 1, "PUNCT"),
        ("학교", 1, 3, "NOUN"),
        (">", 3, 4, "PUNCT"),
        ("~", 4, 5, "PUNCT"),
    ]


def test_korean_zero_width_copula_remains_a_compound_blocker(monkeypatch):
    result = analyze_kiwi(
        monkeypatch,
        "학교다.",
        [
            kiwi_token("학교", "NNG", 0, 2),
            kiwi_token("이", "VCP", 2, 0, lemma="이다"),
            kiwi_token("다", "EF", 2, 1),
            kiwi_token(".", "SF", 3, 1),
        ],
    )
    assert result.status == "inconclusive"
    assert [(b.text, b.reason) for b in result.blocked_spans] == [
        ("학교다", "compound_lexical_projection")
    ]
    assert [c.lemma for c in result.blocked_spans[0].constituents] == ["학교", "이다", "다"]
    assert [(t.text, t.pos) for t in result.tokens] == [(".", "PUNCT")]


def test_korean_oov_is_reported_as_unknown_without_becoming_usable(monkeypatch):
    result = analyze_kiwi(
        monkeypatch,
        "학교 큐쯔",
        [
            kiwi_token("학교", "NNG", 0, 2),
            kiwi_token("큐쯔", "NNP", 3, 2, word=1, oov=True),
        ],
    )
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["학교"]
    assert [(b.text, b.reason) for b in result.blocked_spans] == [("큐쯔", "unknown_lexical_token")]


@pytest.mark.parametrize("compound_second", [False, True])
def test_korean_oov_in_second_alternative_cannot_appear_as_resolved_token(
    monkeypatch, compound_second
):
    noun = kiwi_token("학교", "NNG", 0, 2)
    first = [noun, kiwi_token("큐쯔", "NNP", 3, 2, word=1)]
    other = [noun, kiwi_token("큐쯔", "NNP", 3, 2, word=1, oov=True)]
    if compound_second:
        other = [
            noun,
            kiwi_token("큐", "NNP", 3, 1, word=1),
            kiwi_token("쯔", "NNP", 4, 1, word=1, oov=True),
        ]
    result = analyze_kiwi(monkeypatch, "학교 큐쯔", first, other=other)
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["학교"]
    assert [(b.text, b.reason) for b in result.blocked_spans] == [("큐쯔", "unknown_lexical_token")]


def test_korean_alternative_disagreement_in_nonlexical_evidence_fails_closed(monkeypatch):
    noun = kiwi_token("학교", "NNG", 0, 2)
    result = analyze_kiwi(
        monkeypatch,
        "학교 .",
        [noun, kiwi_token(".", "SF", 3, 1, word=1)],
        other=[noun, kiwi_token(".", "SP", 3, 1, word=1)],
    )
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["학교", "."]
    assert result.reason == "ambiguous_or_incomplete_analysis"


def test_korean_legacy_projection_without_vendor_offsets_fails_closed():
    from multilang.services.contextual_morphology import LocalContextualMorphologyService

    result = NS(passing=True, alternatives=(NS(words=(NS(surface_form="학교"),)),))
    with pytest.raises(ValueError, match="surface spans"):
        LocalContextualMorphologyService._kiwi(NS(analyze=lambda text: result), "학교")
