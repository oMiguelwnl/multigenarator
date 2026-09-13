from pathlib import Path
from types import SimpleNamespace as NS

import pytest


def api():
    from multilang.services import contextual_morphology

    return contextual_morphology


def doc(*rows):
    return NS(
        sentences=[
            NS(
                tokens=[
                    NS(
                        text=text,
                        start_char=start,
                        end_char=end,
                        words=[NS(text=text, lemma=lemma, upos=pos, feats=features)],
                    )
                    for text, start, end, lemma, pos, features in rows
                ]
            )
        ]
    )


def fake_service(monkeypatch, output):
    module = api()
    monkeypatch.setattr(
        module,
        "model_status",
        lambda *a: {"available": True, "backend": "stanza", "manifest_sha256": "a" * 64},
    )
    monkeypatch.setattr(module, "load_stanza_pipeline", lambda *a: lambda text: output)
    return module.LocalContextualMorphologyService(model_root=Path("/unused"))


def test_offsets_case_diacritics_and_context_identity(monkeypatch):
    service = fake_service(
        monkeypatch,
        doc(
            ("Éva", 0, 3, "Éva", "PROPN", None),
            ("saw", 4, 7, "see", "VERB", "Tense=Past"),
            ("saw", 8, 11, "saw", "NOUN", "Number=Sing"),
        ),
    )
    result = service.analyze("en", "Éva saw saw")
    assert result.status == "complete"
    assert [(t.text, t.lemma, t.start, t.end) for t in result.tokens] == [
        ("Éva", "Éva", 0, 3),
        ("saw", "see", 4, 7),
        ("saw", "saw", 8, 11),
    ]
    assert result.tokens[1].analysis_id != result.tokens[2].analysis_id
    assert dict(result.tokens[1].features) == {"Tense": "Past"}
    with pytest.raises(Exception):
        result.tokens[0].lemma = "Eva"


@pytest.mark.parametrize("text", ["", "x\x00", "\ud800", "e\u0301", "x\u202e"])
def test_invalid_unicode_fails_before_model_loading(monkeypatch, text):
    module = api()
    monkeypatch.setattr(module, "model_status", lambda *a: pytest.fail("loaded invalid input"))
    assert (
        module.LocalContextualMorphologyService(model_root=Path("/unused"))
        .analyze("en", text)
        .status
        == "invalid"
    )


@pytest.mark.parametrize(
    "output",
    [
        doc(("went", -1, 4, "go", "VERB", None)),
        doc(("went", True, 4, "go", "VERB", None)),
        doc(("went", 0, 3, "go", "VERB", None)),
        doc(("went", 0, 4, None, "VERB", None)),
        doc(("went", 0, 4, "go", "MADEUP", None)),
        doc(("went", 0, 4, "go", "VERB", "bad-features")),
        doc(("went", 0, 4, "go", "VERB", "Tense=Past|Tense=Pres")),
        NS(sentences=[]),
        NS(
            sentences=[
                NS(
                    tokens=[
                        NS(
                            text="went",
                            start_char=0,
                            end_char=4,
                            words=[
                                NS(text="we", lemma="we", upos="PRON", feats=None),
                                NS(text="nt", lemma="not", upos="PART", feats=None),
                            ],
                        )
                    ]
                )
            ]
        ),
    ],
)
def test_malformed_vendor_output_fails_closed(monkeypatch, output):
    assert fake_service(monkeypatch, output).analyze("en", "went").status == "inconclusive"


def test_dropped_token_is_inconclusive(monkeypatch):
    service = fake_service(monkeypatch, doc(("went", 2, 6, "go", "VERB", None)))
    assert service.analyze("en", "I went").status == "inconclusive"


def test_missing_models_and_unsupported_language(tmp_path):
    service = api().LocalContextualMorphologyService(model_root=tmp_path)
    assert service.analyze("en", "I went.").status == "unavailable"
    assert service.analyze("la", "amo").status == "unsupported"


def request():
    from multilang.domain.content import ContentRequest

    return ContentRequest(
        lexical_identity_id="lex:go",
        card_id="card:went",
        language="en",
        language_profile_version="1",
        lemma="go",
        display_text="went",
        sense_id="move",
        morphological_analysis_id="morph:past",
        context_cue="past motion",
        namespace="core",
        deck_edition_id="edition",
        grounding_sha256="b" * 64,
        target_concept_id="concept:go",
    )


def binding(result, **changes):
    token = result.tokens[0]
    return (
        api()
        .ReviewedSenseBinding(
            language="en",
            sentence_sha256=result.sentence_sha256,
            start=token.start,
            end=token.end,
            token_analysis_id=token.analysis_id,
            lexical_identity_id="lex:go",
            sense_id="move",
            morphological_analysis_id="morph:past",
            concept_id="concept:go",
            source_sha256="c" * 64,
            reviewer="independent-reviewer",
            review_receipt_sha256="d" * 64,
        )
        .model_copy(update=changes)
    )


def test_target_matching_requires_exact_reviewed_sense_and_analysis(monkeypatch):
    service = fake_service(monkeypatch, doc(("went", 0, 4, "go", "VERB", "Tense=Past")))
    result = service.analyze("en", "went")
    matcher = api().ContextualTargetMatcher(analyzer=service, bindings=())
    assert not matcher(request(), "went").matched
    evidence = api().ContextualTargetMatcher(analyzer=service, bindings=(binding(result),))(
        request(), "went"
    )
    assert evidence.matched
    assert evidence.target_span == (0, 4)
    for changes in (
        {"sense_id": "leave"},
        {"token_analysis_id": "e" * 64},
        {"sentence_sha256": "f" * 64},
        {"start": 1},
    ):
        evidence = api().ContextualTargetMatcher(
            analyzer=service, bindings=(binding(result, **changes),)
        )(request(), "went")
        assert not evidence.matched
    assert (
        not api()
        .ContextualTargetMatcher(
            analyzer=service, bindings=(binding(result), binding(result, sense_id="leave"))
        )(request(), "went")
        .matched
    )


def test_unbound_context_cannot_hide_unknown_concepts(monkeypatch):
    service = fake_service(
        monkeypatch, doc(("went", 0, 4, "go", "VERB", None), ("home", 5, 9, "home", "NOUN", None))
    )
    result = service.analyze("en", "went home")
    assert (
        not api()
        .ContextualTargetMatcher(analyzer=service, bindings=(binding(result),))(
            request(), "went home"
        )
        .matched
    )


def test_model_drift_invalidates_previously_reviewed_binding(monkeypatch):
    service = fake_service(monkeypatch, doc(("went", 0, 4, "go", "VERB", None)))
    result = service.analyze("en", "went")
    matcher = api().ContextualTargetMatcher(analyzer=service, bindings=(binding(result),))
    monkeypatch.setattr(
        api(),
        "model_status",
        lambda *a: {"available": True, "backend": "stanza", "manifest_sha256": "f" * 64},
    )
    assert not matcher(request(), "went").matched


def test_unknown_stanza_tag_is_not_complete(monkeypatch):
    service = fake_service(monkeypatch, doc(("went", 0, 4, "go", "X", None)))
    assert service.analyze("en", "went").status == "inconclusive"


def test_korean_group_cannot_hide_grammar_concepts_in_strict_i_plus_one():
    module = api()
    text = "학교에"
    token = module.ContextualToken(
        text=text,
        lemma="학교",
        pos="NOUN",
        features=(("Morphemes", '[{"pos":"NNG"},{"pos":"JKB"}]'),),
        start=0,
        end=3,
        sentence_sha256=module.sentence_hash(text),
        model_fingerprint="a" * 64,
    )
    result = module.ContextualAnalysis(
        language="ko",
        status="complete",
        tokens=(token,),
        sentence_sha256=token.sentence_sha256,
        model_fingerprint=token.model_fingerprint,
        reason="morphology_only",
    )
    reviewed = binding(result, language="ko")
    req = request().model_copy(
        update={
            "language": "ko",
            "lemma": "학교",
            "display_text": text,
            "i_plus_one_mode": "strict",
        }
    )
    matcher = module.ContextualTargetMatcher(
        analyzer=NS(analyze=lambda *a: result), bindings=(reviewed,)
    )
    assert not matcher(req, text).matched


def test_injected_analyzer_cannot_omit_sentence_context():
    module = api()
    text = "went home"
    token = module.ContextualToken(
        text="went",
        lemma="go",
        pos="VERB",
        start=0,
        end=4,
        sentence_sha256=module.sentence_hash(text),
        model_fingerprint="a" * 64,
    )
    result = module.ContextualAnalysis(
        language="en",
        status="complete",
        tokens=(token,),
        sentence_sha256=token.sentence_sha256,
        model_fingerprint=token.model_fingerprint,
        reason="injected",
    )
    matcher = module.ContextualTargetMatcher(
        analyzer=NS(analyze=lambda *a: result), bindings=(binding(result),)
    )
    assert not matcher(request().model_copy(update={"i_plus_one_mode": "strict"}), text).matched


def test_real_english_inflection():
    root = Path(".multilang/models/stanza-1.10.0")
    if not (root / "en.manifest.json").exists():
        pytest.skip("explicitly prepared English model unavailable")
    service = api().LocalContextualMorphologyService(model_root=root)
    result = service.analyze("en", "I went home.")
    assert result.status == "complete", result.reason
    token = next(t for t in result.tokens if t.text == "went")
    assert (token.lemma, token.pos, token.start, token.end) == ("go", "VERB", 2, 6)
    assert dict(token.features)["Tense"] == "Past"


@pytest.mark.parametrize(("language", "sentence"), [("ko", "학교"), ("ja", "学校に行った。")])
def test_real_east_asian_local_adapters(language, sentence, tmp_path):
    result = api().LocalContextualMorphologyService(model_root=tmp_path).analyze(language, sentence)
    assert result.status in {"complete", "inconclusive"}, result.reason
    assert result.tokens
    for token in result.tokens:
        assert sentence[token.start : token.end] == token.text
        assert token.lemma and token.pos and token.model_fingerprint
    if language == "ja":
        token = next(t for t in result.tokens if t.text == "行っ")
        assert (token.lemma, token.pos) == ("行く", "VERB")
        assert dict(token.features)["pos1"] == "動詞"
    else:
        assert result.tokens[0].pos == "NOUN"


def mwt_document(surface, children):
    result = doc(("Vou", 0, 3, "ir", "VERB", None), ("mercado", 7, 14, "mercado", "NOUN", None))
    result.sentences[0].tokens.insert(
        1,
        NS(
            text=surface,
            start_char=4,
            end_char=6,
            words=[
                NS(text=word, lemma=lemma, upos=pos, feats=None, start_char=start, end_char=end)
                for word, lemma, pos, start, end in children
            ],
        ),
    )
    return result


def test_exact_vendor_mwt_partition_preserves_source_spans(monkeypatch):
    output = mwt_document("ao", [("a", "a", "ADP", 4, 5), ("o", "o", "DET", 5, 6)])
    result = fake_service(monkeypatch, output).analyze("pt", "Vou ao mercado")
    assert result.status == "complete"
    assert result.analyzer_version == "contextual-morphology-2"
    assert [(t.text, t.start, t.end) for t in result.tokens] == [
        ("Vou", 0, 3),
        ("a", 4, 5),
        ("o", 5, 6),
        ("mercado", 7, 14),
    ]
    assert result.blocked_spans == ()


@pytest.mark.parametrize(
    ("surface", "children"),
    [
        ("do", [("de", "de", "ADP", 4, 5), ("o", "o", "DET", 5, 6)]),
        ("ao", [("a", "a", "ADP", None, None), ("o", "o", "DET", None, None)]),
        ("ao", [("a", "a", "ADP", 4, 5), ("o", "o", "DET", 4, 6)]),
        ("ao", [("a", "a", "ADP", 4, 5), ("o", "o", "DET", 5, True)]),
    ],
)
def test_unproven_mwt_keeps_parent_evidence_and_surrounding_words(monkeypatch, surface, children):
    text = f"Vou {surface} mercado"
    result = fake_service(monkeypatch, mwt_document(surface, children)).analyze("pt", text)
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["Vou", "mercado"]
    (blocked,) = result.blocked_spans
    assert (blocked.text, blocked.start, blocked.end) == (surface, 4, 6)
    assert blocked.reason == "unaligned_multiword_expansion"
    assert [c.lemma for c in blocked.constituents] == [c[1] for c in children]
    assert not hasattr(blocked.constituents[0], "start")
    assert blocked.sentence_sha256 == result.sentence_sha256
    matcher = api().ContextualTargetMatcher(analyzer=NS(analyze=lambda *a: result), bindings=())
    assert not matcher(request().model_copy(update={"language": "pt"}), text).matched


def test_unknown_stanza_word_keeps_source_without_inventing_lemma(monkeypatch):
    result = fake_service(
        monkeypatch, doc(("went", 0, 4, "go", "VERB", None), ("zzq", 5, 8, None, "X", None))
    ).analyze("en", "went zzq")
    assert [t.text for t in result.tokens] == ["went"]
    (blocked,) = result.blocked_spans
    assert blocked.text == "zzq"
    assert blocked.constituents[0].lemma is None
    assert result.status == "inconclusive"


def japanese_token(surface, *, lemma, pos, unknown=False):
    from collections import namedtuple

    Feature = namedtuple("Feature", "pos1 pos2 lemma pron")
    return NS(
        surface=surface,
        white_space="",
        is_unk=unknown,
        feature=Feature(pos, "*", lemma, None),
    )


def japanese_service(monkeypatch, vendor_tokens):
    module = api()
    service = module.LocalContextualMorphologyService(model_root=Path("/unused"))
    status = {"available": True, "backend": "fugashi", "manifest_sha256": "a" * 64}
    monkeypatch.setattr(module, "model_status", lambda *a: status)
    fingerprint = module.canonical_sha256({"policy": "contextual-morphology-2", **status})
    service._pipelines[("ja", fingerprint)] = lambda text: vendor_tokens
    return service


def test_japanese_native_unknown_punctuation_does_not_erase_lexical_evidence(monkeypatch):
    service = japanese_service(
        monkeypatch,
        [
            japanese_token("学校", lemma="学校", pos="名詞"),
            japanese_token(",", lemma=None, pos="記号", unknown=True),
            japanese_token("犬", lemma="犬", pos="名詞"),
        ],
    )
    result = service.analyze("ja", "学校,犬")
    assert result.status == "complete"
    assert [(t.text, t.lemma, t.pos) for t in result.tokens] == [
        ("学校", "学校", "NOUN"),
        (",", ",", "PUNCT"),
        ("犬", "犬", "NOUN"),
    ]
    assert all(value is not None for token in result.tokens for _, value in token.features)


def test_japanese_lexical_unknown_is_a_blocker_even_when_mistagged_symbol(monkeypatch):
    service = japanese_service(
        monkeypatch,
        [
            japanese_token("学校", lemma="学校", pos="名詞"),
            japanese_token("xyz", lemma=None, pos="記号", unknown=True),
            japanese_token("犬", lemma="犬", pos="名詞"),
        ],
    )
    result = service.analyze("ja", "学校xyz犬")
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["学校", "犬"]
    assert result.blocked_spans[0].text == "xyz"
    assert result.blocked_spans[0].constituents[0].lemma is None


def test_analysis_rejects_blockers_overlapping_tokens_or_claiming_complete(monkeypatch):
    result = fake_service(
        monkeypatch,
        mwt_document("do", [("de", "de", "ADP", 4, 5), ("o", "o", "DET", 5, 6)]),
    ).analyze("pt", "Vou do mercado")
    payload = result.model_dump(mode="json")
    payload["status"] = "complete"
    with pytest.raises(ValueError):
        api().ContextualAnalysis.model_validate(payload)
    payload["status"] = "inconclusive"
    payload["blocked_spans"][0].update(text="ou", start=1, end=3)
    with pytest.raises(ValueError):
        api().ContextualAnalysis.model_validate(payload)


def test_legacy_analysis_payload_without_blockers_still_loads():
    module = api()
    payload = {
        "language": "en",
        "status": "unavailable",
        "sentence_sha256": "a" * 64,
        "model_fingerprint": "b" * 64,
        "reason": "missing",
        "analyzer_version": "contextual-morphology-1",
    }
    assert module.ContextualAnalysis.model_validate(payload).blocked_spans == ()


def test_english_contraction_accepts_only_observed_vendor_partition(monkeypatch):
    output = doc(("I", 0, 1, "I", "PRON", None), ("go", 8, 10, "go", "VERB", None))
    output.sentences[0].tokens.insert(
        1,
        NS(
            text="don't",
            start_char=2,
            end_char=7,
            words=[
                NS(text="do", lemma="do", upos="AUX", feats=None, start_char=2, end_char=4),
                NS(text="n't", lemma="not", upos="PART", feats=None, start_char=4, end_char=7),
            ],
        ),
    )
    result = fake_service(monkeypatch, output).analyze("en", "I don't go")
    assert result.status == "complete"
    assert [(t.text, t.lemma, t.start, t.end) for t in result.tokens[1:3]] == [
        ("do", "do", 2, 4),
        ("n't", "not", 4, 7),
    ]


def test_missing_vendor_span_retains_known_tokens_and_exact_unanalyzed_source(monkeypatch):
    result = fake_service(monkeypatch, doc(("went", 2, 6, "go", "VERB", None))).analyze(
        "en", "I went home"
    )
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["went"]
    assert [(b.text, b.start, b.end, b.reason) for b in result.blocked_spans] == [
        ("I", 0, 1, "missing_vendor_span"),
        ("home", 7, 11, "missing_vendor_span"),
    ]
    assert all(not b.constituents for b in result.blocked_spans)


def test_korean_compound_keeps_source_morphemes_and_other_lexical_groups(monkeypatch):
    from multilang.domain.korean import KoreanMorphemeEvidence

    def morpheme(form, lemma, pos):
        return KoreanMorphemeEvidence(form=form, lemma=lemma, pos=pos, raw_pos=pos, oov=False)

    words = (
        NS(surface_form="학교", morphemes=(morpheme("학교", "학교", "NNG"),)),
        NS(
            surface_form="공부한다",
            morphemes=(
                morpheme("공부", "공부", "NNG"),
                morpheme("하", "하다", "XSV"),
                morpheme("ᆫ다", "ᆫ다", "EF"),
            ),
        ),
    )
    module = api()
    status = {"available": True, "backend": "kiwi", "manifest_sha256": "a" * 64}
    monkeypatch.setattr(module, "model_status", lambda *a: status)
    service = module.LocalContextualMorphologyService(model_root=Path("/unused"))
    fingerprint = module.canonical_sha256({"policy": "contextual-morphology-2", **status})
    service._pipelines[("ko", fingerprint)] = NS(
        analyze=lambda text: NS(passing=True, alternatives=(NS(words=words), NS(words=words)))
    )
    result = service.analyze("ko", "학교 공부한다")
    assert result.status == "inconclusive"
    assert [t.text for t in result.tokens] == ["학교"]
    (blocker,) = result.blocked_spans
    assert (blocker.text, blocker.start, blocker.end) == ("공부한다", 3, 7)
    assert blocker.reason == "compound_lexical_projection"
    assert [(c.text, c.lemma, c.pos) for c in blocker.constituents] == [
        ("공부", "공부", "NNG"),
        ("하", "하다", "XSV"),
        ("ᆫ다", "ᆫ다", "EF"),
    ]


def test_blocker_constituents_cannot_exhaust_unbounded_memory():
    module = api()
    constituent = dict(text="a", lemma="a", pos="DET")
    with pytest.raises(ValueError):
        module.ContextualBlockedSpan(
            text="a",
            start=0,
            end=1,
            sentence_sha256="a" * 64,
            model_fingerprint="b" * 64,
            reason="unaligned_multiword_expansion",
            constituents=[constituent] * 129,
        )


def test_korean_compound_branch_enforces_span_limit_before_next_projection(monkeypatch):
    module = api()
    monkeypatch.setattr(module, "_MAX_TOKENS", 1)
    words = tuple(
        NS(
            surface_form=surface,
            morphemes=(
                NS(form=surface, lemma=surface, pos="NNG", raw_pos="NNG"),
                NS(form="하", lemma="하다", pos="XSV", raw_pos="XSV"),
            ),
        )
        for surface in ("가", "나")
    )
    pipeline = NS(analyze=lambda text: NS(passing=True, alternatives=(NS(words=words),)))
    with pytest.raises(ValueError, match="token limit"):
        module.LocalContextualMorphologyService._kiwi(pipeline, "가 나")


def test_korean_constituent_limit_applies_before_blocker_construction():
    module = api()
    morphemes = tuple(NS(form="가", lemma="가", pos="NNG", raw_pos="NNG") for _ in range(129))
    words = (NS(surface_form="가", morphemes=morphemes),)
    pipeline = NS(analyze=lambda text: NS(passing=True, alternatives=(NS(words=words),)))
    with pytest.raises(ValueError, match="constituent count"):
        module.LocalContextualMorphologyService._kiwi(pipeline, "가")
