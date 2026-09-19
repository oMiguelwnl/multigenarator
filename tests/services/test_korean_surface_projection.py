"""Vendor span regression tests without constructing another Kiwi model."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from multilang.domain import korean
from multilang.services import korean_morphology as morphology
from multilang.services.korean_morphology import KiwiKoreanMorphologyService


def _token(form, tag, start, length, word=0, sentence=0, *, lemma=None, oov=False):
    return SimpleNamespace(
        form=form,
        lemma=lemma or form,
        tag=tag,
        start=start,
        len=length,
        word_position=word,
        sent_position=sentence,
        oov=oov,
    )


def _analyze(text, tokens):
    vendor = SimpleNamespace(analyze=lambda *a, **k: [(tokens, -1.0), (tokens, -2.0)])
    return KiwiKoreanMorphologyService(analyzer_factory=lambda: vendor).analyze(text)


def _surfaces(result):
    assert result.passing, result.reason_code
    assert hasattr(result.alternatives[0], "surface_spans")
    return result.alternatives[0].surface_spans


def test_zero_width_copula_remains_inside_nonempty_group_evidence():
    result = _analyze(
        "학교다.",
        [
            _token("학교", "NNG", 0, 2),
            _token("이", "VCP", 2, 0, lemma="이다"),
            _token("다", "EF", 2, 1),
            _token(".", "SF", 3, 1),
        ],
    )

    spans = _surfaces(result)
    assert [(s.surface_form, s.start, s.end) for s in spans] == [
        ("학교다", 0, 3),
        (".", 3, 4),
    ]
    assert [(m.form, m.pos) for m in spans[0].morphemes] == [
        ("학교", "NNG"),
        ("이", "VCP"),
        ("다", "EF"),
    ]
    assert [(m.form, m.pos) for m in result.alternatives[0].words[0].lexical_signature] == [
        ("학교", "NNG"),
        ("이", "VCP"),
    ]


def test_zero_width_ending_can_anchor_at_nonempty_group_end():
    result = _analyze(
        "간",
        [_token("가", "VV", 0, 1, lemma="가다"), _token("ᆫ", "ETM", 1, 0)],
    )
    (span,) = _surfaces(result)
    assert (span.surface_form, span.start, span.end) == ("간", 0, 1)
    assert [m.form for m in span.morphemes] == ["가", "ᆫ"]


@pytest.mark.parametrize(
    "tokens",
    [
        [_token("이", "VCP", 0, 0)],
        [_token("가", "NNG", 0, 1), _token("이", "VCP", 2, 0)],
        [_token("가", "NNG", 0, 1), _token("이", "VCP", -1, 0)],
        [_token("가", "NNG", 0, 1), _token("이", "VCP", 0, -1)],
        [_token("가", "NNG", False, 1)],
        [_token("가", "NNG", 0, True)],
        [_token("가", "NNG", 0, 1, word=False)],
        [_token("가", "NNG", 0, 1, sentence=False)],
        [_token("가", "NNG", 0, 1, sentence=None)],
    ],
)
def test_malformed_zero_width_or_boolean_vendor_coordinates_fail_closed(tokens):
    result = _analyze("가 나", tokens)
    assert not result.passing
    assert result.reason_code.value == "malformed_analysis"
    assert not result.alternatives


def test_sentence_relative_word_positions_become_distinct_source_ordered_groups():
    result = _analyze(
        "학교. 집.",
        [
            _token("학교", "NNG", 0, 2),
            _token(".", "SF", 2, 1),
            _token("집", "NNG", 4, 1, sentence=1),
            _token(".", "SF", 5, 1, sentence=1),
        ],
    )
    spans = _surfaces(result)
    assert [(w.word_position, w.surface_form) for w in result.alternatives[0].words] == [
        (0, "학교."),
        (1, "집."),
    ]
    assert [(s.word_position, s.surface_form, s.start, s.end) for s in spans] == [
        (0, "학교", 0, 2),
        (0, ".", 2, 3),
        (1, "집", 4, 5),
        (1, ".", 5, 6),
    ]


def test_nonlexical_number_and_punctuation_groups_retain_vendor_offsets():
    result = _analyze(
        '"6.2 학교!',
        [
            _token('"', "SSO", 0, 1),
            _token("6.2", "SN", 1, 3),
            _token("학교", "NNG", 5, 2, word=1),
            _token("!", "SF", 7, 1, word=1),
        ],
    )
    spans = _surfaces(result)
    assert [(s.surface_form, s.start, s.end) for s in spans] == [
        ('"', 0, 1),
        ("6.2", 1, 4),
        ("학교", 5, 7),
        ("!", 7, 8),
    ]
    assert len(result.alternatives[0].words) == 1
    assert result.alternatives[0].words[0].word_position == 1


def test_internal_quote_keeps_following_particle_as_separate_surface_evidence():
    result = _analyze(
        '"학교"고',
        [
            _token('"', "SSO", 0, 1),
            _token("학교", "NNG", 1, 2),
            _token('"', "SSC", 3, 1),
            _token("고", "JKQ", 4, 1),
        ],
    )
    spans = _surfaces(result)
    assert [s.surface_form for s in spans] == ['"', "학교", '"', "고"]
    assert spans[-1].morphemes[0].pos == "JKQ"
    assert [m.form for m in result.alternatives[0].words[0].morphemes] == ['"', "학교", '"', "고"]


def test_native_brackets_separate_at_vendor_offsets_even_when_unicode_calls_them_symbols():
    result = _analyze(
        "<학교>",
        [
            _token("<", "SSO", 0, 1),
            _token("학교", "NNG", 1, 2),
            _token(">", "SSC", 3, 1),
        ],
    )

    spans = _surfaces(result)
    assert [(span.surface_form, span.start, span.end) for span in spans] == [
        ("<", 0, 1),
        ("학교", 1, 3),
        (">", 3, 4),
    ]
    word = result.alternatives[0].words[0]
    assert word.surface_form == "<학교>"
    assert [(item.form, item.pos) for item in word.lexical_signature] == [("학교", "NNG")]
    assert [item.form for item in word.morphemes] == ["<", "학교", ">"]


def test_native_tilde_separator_preserves_zero_width_copula_and_compound_signature():
    result = _analyze(
        "학교다~",
        [
            _token("학교", "NNG", 0, 2),
            _token("이", "VCP", 2, 0, lemma="이다"),
            _token("다", "EF", 2, 1),
            _token("~", "SO", 3, 1),
        ],
    )

    spans = _surfaces(result)
    assert [(span.surface_form, span.start, span.end) for span in spans] == [
        ("학교다", 0, 3),
        ("~", 3, 4),
    ]
    assert [
        (item.form, item.pos) for item in result.alternatives[0].words[0].lexical_signature
    ] == [("학교", "NNG"), ("이", "VCP")]


def test_generic_special_symbol_is_not_promoted_to_a_punctuation_boundary():
    result = _analyze(
        "학교~",
        [_token("학교", "NNG", 0, 2), _token("~", "SW", 2, 1)],
    )
    spans = _surfaces(result)
    assert [span.surface_form for span in spans] == ["학교~"]
    assert [item.form for item in spans[0].morphemes] == ["학교", "~"]


@pytest.mark.parametrize(
    "tokens",
    [
        [_token("<", "SSO", 0, 1), _token("학교", "NNG", 0, 3)],
        [_token(">", "SSO", 0, 1), _token("학교", "NNG", 1, 2)],
        [_token("<", "SSO", 0, 0), _token("학교", "NNG", 1, 2)],
    ],
)
def test_symbol_separator_requires_exact_nonempty_disjoint_vendor_span(tokens):
    result = _analyze("<학교", tokens)
    assert not result.passing
    assert result.reason_code.value == "malformed_analysis"


def test_symbol_separator_retains_oov_evidence():
    result = _analyze(
        "<학교",
        [_token("<", "SSO", 0, 1, oov=True), _token("학교", "NNG", 1, 2)],
    )
    assert result.status.value == "oov"
    assert not result.passing
    assert all(alternative.has_oov for alternative in result.alternatives)
    assert all(alternative.surface_spans[0].morphemes[0].oov for alternative in result.alternatives)


def test_oov_evidence_in_nonlexical_only_group_cannot_be_dropped():
    result = _analyze(
        "학교 🛸",
        [_token("학교", "NNG", 0, 2), _token("🛸", "SW", 3, 1, word=1, oov=True)],
    )
    assert result.status.value == "oov"
    assert not result.passing
    assert all(a.has_oov for a in result.alternatives)
    assert result.alternatives[0].surface_spans[-1].morphemes[0].oov


def test_vendor_special_tag_for_foreign_script_is_retained_without_punctuation_guess():
    result = _analyze(
        "학교 ひらがな",
        [_token("학교", "NNG", 0, 2), _token("ひらがな", "SW", 3, 4, word=1)],
    )
    spans = _surfaces(result)
    assert [(s.surface_form, s.start, s.end) for s in spans] == [("학교", 0, 2), ("ひらがな", 3, 7)]
    assert spans[-1].morphemes[0].pos == "SW"


@pytest.mark.parametrize(
    ("text", "tokens"),
    [
        ("학교!", [_token("학교", "NNG", 0, 3), _token("!", "SF", 2, 1)]),
        ("학교!", [_token("학교", "NNG", 0, 2), _token("?", "SF", 2, 1)]),
        ("학교가", [_token("학교", "NNG", 0, 2), _token("가", "SF", 2, 1)]),
        ("가X나", [_token("가", "NNG", 0, 1), _token("나", "NNG", 2, 1)]),
        ("학교", [_token("학교", "NNG", 0, 2), _token("교", "NNG", 1, 1, word=1)]),
        (
            "가나다!",
            [_token("가나다", "NNG", 0, 4), _token("나", "NNG", 1, 1), _token("!", "SF", 3, 1)],
        ),
        (
            "학교!",
            [_token("학교", "NNG", 0, 2), _token("!", "SF", 2, 1), _token("가", "NNG", 2, 1)],
        ),
    ],
)
def test_crossing_groups_or_unproven_punctuation_boundaries_fail_closed(text, tokens):
    result = _analyze(text, tokens)
    assert not result.passing
    assert result.reason_code.value == "malformed_analysis"


def test_compound_lexical_morphemes_are_never_split_into_separate_lexical_groups():
    result = _analyze(
        "공부해요!",
        [
            _token("공부", "NNG", 0, 2),
            _token("하", "XSV", 2, 1, lemma="하다"),
            _token("어요", "EF", 2, 2),
            _token("!", "SF", 4, 1),
        ],
    )
    spans = _surfaces(result)
    assert [s.surface_form for s in spans] == ["공부해요", "!"]
    assert [(m.form, m.pos) for m in result.alternatives[0].words[0].lexical_signature] == [
        ("공부", "NNG"),
        ("하", "XSV"),
    ]


def test_surface_span_contract_is_strict_and_legacy_alternatives_remain_readable():
    assert hasattr(korean, "KoreanSurfaceSpan")
    morpheme = korean.KoreanMorphemeEvidence(
        form="학교", lemma="학교", pos="NNG", raw_pos="NNG", oov=False
    )
    word = korean.KoreanWordAnalysis(
        surface_form="학교",
        word_position=0,
        morphemes=(morpheme,),
        lexical_signature=(korean.KoreanSignatureItem(form="학교", pos="NNG"),),
    )
    legacy = korean.KoreanAnalysisAlternative(rank=1, score=-1, words=(word,), has_oov=False)
    assert legacy.surface_spans == ()
    span = dict(surface_form="학교", start=0, end=2, word_position=0, morphemes=(morpheme,))
    for invalid in ({"start": False}, {"end": 1}, {"end": 0}, {"word_position": True}):
        with pytest.raises(ValueError):
            korean.KoreanSurfaceSpan(**{**span, **invalid})
    with pytest.raises(ValueError):
        korean.KoreanAnalysisAlternative(
            rank=1,
            score=-1,
            words=(word,),
            has_oov=False,
            surface_spans=(korean.KoreanSurfaceSpan(**span), korean.KoreanSurfaceSpan(**span)),
        )


@pytest.mark.parametrize("legacy_version", ["kiwi-top2-consensus-v1", "kiwi-top2-consensus-v2"])
def test_projection_policy_fingerprint_changes_and_old_policy_remains_parseable(legacy_version):
    service = KiwiKoreanMorphologyService(analyzer_factory=lambda: None)
    assert service.fingerprint.policy_version == "kiwi-top2-consensus-v3"
    legacy = service.fingerprint.model_dump()
    legacy["policy_version"] = legacy_version
    assert korean.KoreanAnalyzerFingerprint.model_validate(legacy) != service.fingerprint


def test_long_punctuation_group_does_not_repeatedly_scan_every_morpheme():
    class TraversalBudget(list):
        visits = 0

        def __iter__(self):
            for item in super().__iter__():
                self.visits += 1
                assert self.visits <= 8 * len(self), "quadratic group traversal"
                yield item

    noun = korean.KoreanMorphemeEvidence(
        form="학교", lemma="학교", pos="NNG", raw_pos="NNG", oov=False
    )
    punctuation = korean.KoreanMorphemeEvidence(
        form="!", lemma="!", pos="SF", raw_pos="SF", oov=False
    )
    source = "학교" + "!" * 512
    group = TraversalBudget(
        [(noun, 0, 2)] + [(punctuation, index, index + 1) for index in range(2, len(source))]
    )

    spans = morphology._project_surface_spans(group, word_position=0, canonical_text=source)

    assert len(spans) == 513
    assert "".join(span.surface_form for span in spans) == source
    assert all(source[span.start : span.end] == span.surface_form for span in spans)


@pytest.mark.parametrize("separate_groups", [False, True])
def test_surface_span_limit_stops_allocation_before_building_an_extra_span(
    monkeypatch, separate_groups
):
    monkeypatch.setattr(morphology, "_MAX_SURFACE_SPANS", 2, raising=False)
    original = morphology.KoreanSurfaceSpan
    allocations = 0

    def bounded_span(**kwargs):
        nonlocal allocations
        allocations += 1
        assert allocations <= 2, "surface span limit was checked after allocation"
        return original(**kwargs)

    monkeypatch.setattr(morphology, "KoreanSurfaceSpan", bounded_span)
    source = "가 ! !" if separate_groups else "가!!"
    result = _analyze(
        source,
        [
            _token("가", "NNG", 0, 1),
            _token("!", "SF", 2 if separate_groups else 1, 1, word=1 if separate_groups else 0),
            _token("!", "SF", 4 if separate_groups else 2, 1, word=2 if separate_groups else 0),
        ],
    )
    assert not result.passing
    assert result.reason_code.value == "malformed_analysis"
    assert allocations == 2
