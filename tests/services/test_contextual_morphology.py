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
