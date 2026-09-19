"""Course morphology never treats a candidate path as a review approval."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from multilang.domain.korean_grammar import korean_grammar_canonical_json_sha256 as digest
from multilang.services.korean_grammar_course import (
    load_grammar_course,
    load_grammar_course_support,
)
from multilang.services.korean_morphology import KiwiKoreanMorphologyService


@pytest.fixture
def evidence():
    course = load_grammar_course()
    support = load_grammar_course_support(course)
    card = next(c for c in course.cards if c.entry_id == "g1.object")
    forms = [
        ("친구", "친구", "NNG", 0, 2, 0), ("가", "가", "JKS", 2, 1, 0),
        ("밥", "밥", "NNG", 4, 1, 1), ("을", "을", "JKO", 5, 1, 1),
        ("먹", "먹다", "VV", 7, 1, 2), ("어요", "어요", "EF", 8, 2, 2),
        (".", ".", "SF", 10, 1, 2),
    ]
    tokens = [SimpleNamespace(form=f, lemma=lemma, tag=p, start=s, len=n,
                              word_position=w, sent_position=0, oov=False)
              for f, lemma, p, s, n, w in forms]
    alternative = deepcopy(tokens)
    alternative[4].tag = "VX"
    analyzer = KiwiKoreanMorphologyService(
        analyzer_factory=lambda: SimpleNamespace(analyze=lambda *a, **k: [
            (tokens, -1.0), (alternative, -2.0)
        ])
    )
    analysis = analyzer.analyze(card.example_sentence)
    from hashlib import sha256
    record = dict(entry_id=card.entry_id, field="example_sentence",
                  text_sha256=sha256(card.example_sentence.encode()).hexdigest(),
                  analysis=analysis.model_dump(mode="json"))
    def refs(span, morph):
        return [{"span_index": span, "morpheme_index": morph}]
    lexical = []
    for entry_id, span in [("lex.friend", 0), ("lex.cooked-rice", 1), ("lex.eat", 2)]:
        source = next(e for e in support.lexical.entries if e.entry_id == entry_id)
        lexical.append(dict(support_entry_id=entry_id,
                            source_entry_sha256=source.source_entry_sha256,
                            morpheme_refs=refs(span, 0), mapping_kind="exact_lemma",
                            rationale_pt="O lema e a categoria do analisador coincidem com a entrada fonte."))
    claims = dict(
        entry_id=card.entry_id, field="example_sentence", text_sha256=record["text_sha256"],
        analysis_sha256=digest(analysis), selected_rank=1,
        selection_rationale_pt="먹다 rege 밥을 e é verbo principal neste predicado, não auxiliar.",
        rejected_alternatives=[dict(rank=2, alternative_sha256=digest(analysis.alternatives[1]),
                                   rationale_pt="VX carece de verbo principal precedente e conflita com o objeto 밥을.")],
        lexical_claims=lexical,
        grammar_claims=[
            dict(grammar_id=g, morpheme_refs=refs(s, m), evidence_kind=kind,
                 rationale_pt="A função é ancorada neste morfema da análise selecionada.")
            for g, s, m, kind in [
                ("g1.object", 1, 1, "morpheme"), ("g1.subject", 0, 1, "morpheme"),
                ("g1.present", 2, 1, "morpheme"),
                ("g0.predicate-final", 2, 1, "clause_structure")
            ]
        ],
    )
    return course, support, record, claims


def validate(evidence):
    from multilang.services.korean_grammar_morphology import validate_grammar_morphology_record
    return validate_grammar_morphology_record(*evidence)


def test_selected_path_is_reviewable_but_not_analyzer_consensus_or_approval(evidence):
    report = validate(evidence)
    assert report["deterministically_valid"] is True
    assert report["native_top2_consensus"] is False
    assert report["status"] == "contextual_review_required"
    assert report["learner_ready"] is False
    assert report["required_independent_passes"] == 3
    assert report["selected_morpheme_count"] == 6


@pytest.mark.parametrize("drift", ["text", "analysis", "source", "rejected"])
def test_every_source_boundary_is_hash_bound(evidence, drift):
    _, _, record, claims = evidence
    if drift == "text":
        record["text_sha256"] = "0" * 64
    elif drift == "analysis":
        claims["analysis_sha256"] = "0" * 64
    elif drift == "source":
        claims["lexical_claims"][0]["source_entry_sha256"] = "0" * 64
    else:
        claims["rejected_alternatives"][0]["alternative_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        validate(evidence)


def test_grammar_coverage_cannot_be_supplied_by_a_clause_level_claim(evidence):
    evidence[3]["grammar_claims"] = [c for c in evidence[3]["grammar_claims"]
                                      if c["grammar_id"] != "g1.present"]
    with pytest.raises(ValueError, match="grammar_inventory|uncovered"):
        validate(evidence)


def test_wrong_lexical_identity_cannot_pass_by_substring_or_surface(evidence):
    evidence[3]["lexical_claims"][0]["support_entry_id"] = "lex.eat"
    with pytest.raises(ValueError):
        validate(evidence)


def test_native_pos_disagreement_requires_an_explicit_contextual_claim(evidence):
    _, _, record, claims = evidence
    claims["selected_rank"] = 2
    claims["rejected_alternatives"][0].update(
        rank=1, alternative_sha256=digest(record["analysis"]["alternatives"][0]))
    with pytest.raises(ValueError, match="lexical_pos"):
        validate(evidence)
    claims["lexical_claims"][-1]["mapping_kind"] = "contextual_pos"
    report = validate(evidence)
    assert report["contextual_pos_claims"] == ["lex.eat"]
    assert report["learner_ready"] is False


def test_morpheme_index_and_entire_text_coverage_are_checked(evidence):
    evidence[3]["grammar_claims"][0]["morpheme_refs"][0]["morpheme_index"] = 8
    with pytest.raises(ValueError, match="morpheme_reference"):
        validate(evidence)


def test_rejects_missing_alternative_decision(evidence):
    evidence[3]["rejected_alternatives"] = []
    with pytest.raises(ValueError):
        validate(evidence)


def test_complete_manifest_requires_every_field_and_current_course(evidence):
    from multilang.services.korean_grammar_morphology import validate_grammar_morphology_claims
    course, support, record, claims = evidence
    manifest = dict(
        schema_version="korean-grammar-morphology-claims-v1",
        course_sha256=course.content_sha256, support_sha256=digest(support),
        analyzer_fingerprint_sha256=digest(record["analysis"]["analyzer_fingerprint"]),
        records=[claims],
    )
    with pytest.raises(ValueError, match="record_inventory"):
        validate_grammar_morphology_claims(course, support, [record], manifest)


def test_unknown_native_morphology_cannot_be_hidden_by_a_grammar_claim(evidence):
    _, _, record, claims = evidence
    for alternative in record["analysis"]["alternatives"]:
        alternative["words"][2]["morphemes"][1].update(pos="ZZ", raw_pos="ZZ")
        alternative["surface_spans"][2]["morphemes"][1].update(pos="ZZ", raw_pos="ZZ")
    claims["analysis_sha256"] = digest(record["analysis"])
    claims["rejected_alternatives"][0]["alternative_sha256"] = digest(record["analysis"]["alternatives"][1])
    with pytest.raises(ValueError, match="unsupported_native"):
        validate(evidence)


def test_complete_manifest_hashes_all_native_records_and_claims(evidence):
    from multilang.services.korean_grammar_morphology import validate_grammar_morphology_claims
    course, support, record, claims = evidence
    original = next(c for c in course.cards if c.entry_id == "g1.object")
    cards = tuple(original.model_copy(update={"entry_id": f"g{i}.test", "category_id": f"G{i}",
                                             "prerequisite_ids": ()}) for i in range(14))
    course = type(course)(cards=cards)
    entry_ids = tuple(c.entry_id for c in cards)
    support = support.model_copy(update={
        "lexical": support.lexical.model_copy(update={
            "course_sha256": course.content_sha256,
            "entries": tuple(e.model_copy(update={"used_by": entry_ids}) for e in support.lexical.entries
                             if e.entry_id in {"lex.friend", "lex.cooked-rice", "lex.eat"})}),
        "observations": support.observations.model_copy(update={
            "course_sha256": course.content_sha256,
            "entries": tuple(support.observations.entries[0].model_copy(update={
                "entry_id": cid, "observed_grammar_ids": (cid,)}) for cid in entry_ids)})})
    records, candidates = [], []
    for cid in entry_ids:
        for field in ("example_sentence", "spoken_sample"):
            native = deepcopy(record)
            native.update(entry_id=cid, field=field)
            candidate = deepcopy(claims)
            candidate.update(entry_id=cid, field=field)
            candidate["grammar_claims"] = [dict(
                grammar_id=cid, evidence_kind="construction",
                morpheme_refs=[{"span_index": i, "morpheme_index": 1} for i in range(3)],
                rationale_pt="As três marcas gramaticais estão ancoradas nesta construção de teste.")]
            records.append(native)
            candidates.append(candidate)
    manifest = dict(schema_version="korean-grammar-morphology-claims-v1",
                    course_sha256=course.content_sha256, support_sha256=digest(support),
                    analyzer_fingerprint_sha256=digest(record["analysis"]["analyzer_fingerprint"]),
                    records=candidates)
    report = validate_grammar_morphology_claims(course, support, records, manifest)
    assert report["native_records_sha256"] == digest(records)
    assert report["claims_sha256"] == digest(manifest)
    assert report["record_count"] == 28
    assert report["contextual_decision_count"] == 28
    assert report["learner_ready"] is False


def test_derivational_morphemes_need_a_lexical_identity_not_a_grammar_label(evidence):
    _, _, record, claims = evidence
    for alternative in record["analysis"]["alternatives"]:
        alternative["words"][2]["morphemes"][1].update(pos="XSN", raw_pos="XSN")
        alternative["surface_spans"][2]["morphemes"][1].update(pos="XSN", raw_pos="XSN")
    claims["analysis_sha256"] = digest(record["analysis"])
    claims["rejected_alternatives"][0]["alternative_sha256"] = digest(record["analysis"]["alternatives"][1])
    with pytest.raises(ValueError, match="uncovered_lexical"):
        validate(evidence)
