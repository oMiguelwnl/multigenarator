"""Deterministic prerequisites for explicit course morphology review.

No provider calls or approvals occur here. The caller must obtain three fresh
independent critical reviews over the returned subject, including the actual
selection/rejection and each lexical/construction claim. Native disagreements
remain visible; this does not change the legacy top-two lexical matcher.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256

from multilang.domain.korean import KoreanMorphologyStatus
from multilang.domain.korean_grammar import korean_grammar_canonical_json_sha256 as digest
from multilang.domain.korean_grammar_course import KoreanGrammarCourse, KoreanGrammarCourseSupport
from multilang.domain.korean_grammar_morphology import (
    GrammarNativeAnalysisRecord,
    GrammarSentenceMorphologyClaims,
    KoreanGrammarMorphologyManifest,
)
from multilang.services.korean_pos import is_kiwi_punctuation

VALIDATOR_ID = "korean-grammar-contextual-morphology-v1"
_LEXICAL = frozenset("NNG NNP NNB NR NP VV VA VX VCN MM MAG MAJ IC SN".split())
_DERIVATIONAL = frozenset("XPN XSN XSV XSA XSM XR".split())
_AFFIX = frozenset("VCP JKS JKC JKG JKO JKB JKV JKQ JX JC EP EF EC ETN ETM XPN XSN XSV XSA XSM XR".split())
_SOURCE_POS = {
    "명": {"NNG", "NNP"}, "대": {"NP"}, "동": {"VV"}, "형": {"VA", "VCN"},
    "부": {"MAG", "MAJ"}, "관": {"MM"}, "보": {"VX"}, "의": {"NNB"},
}
# Authored lexical decompositions, not suffix or whitespace inference. Each
# occurrence still needs an exact source row, native token sequence and review.
_COMPOUNDS = {
    ("공부하다", (("공부", "NNG"), ("하", "XSV"))): "동",
    ("선생님", (("선생", "NNG"), ("님", "XSN"))): "명",
}
_CLAUSE_CONCEPTS = {"g0.argument-omission", "g0.predicate-final"}


def _typed(model, value):
    return model.model_validate(value.model_dump(mode="json") if isinstance(value, model) else value)


def _native_morphemes(text, alternative):
    """Require native evidence covering every non-whitespace source character."""
    if not alternative.surface_spans:
        raise ValueError("missing_native_surface_spans")
    previous, morphemes = 0, {}
    for span_index, span in enumerate(alternative.surface_spans):
        if (span.start < previous or text[span.start:span.end] != span.surface_form
                or any(not c.isspace() for c in text[previous:span.start])):
            raise ValueError("unaligned_native_surface_spans")
        previous = span.end
        for morpheme_index, morpheme in enumerate(span.morphemes):
            if morpheme.oov or morpheme.pos != morpheme.raw_pos.partition("-")[0]:
                raise ValueError("invalid_native_morpheme")
            if is_kiwi_punctuation(morpheme.pos, morpheme.form):
                continue
            if morpheme.pos not in _LEXICAL | _AFFIX:
                raise ValueError("unsupported_native_morphology")
            morphemes[(span_index, morpheme_index)] = morpheme
    if any(not c.isspace() for c in text[previous:]):
        raise ValueError("uncovered_native_source_text")
    return morphemes


def _references(claim, morphemes):
    refs = tuple((r.span_index, r.morpheme_index) for r in claim.morpheme_refs)
    if len(set(refs)) != len(refs) or any(ref not in morphemes for ref in refs):
        raise ValueError("invalid_morpheme_reference")
    if tuple(sorted(refs)) != refs:
        raise ValueError("unordered_morpheme_reference")
    return refs


def validate_grammar_morphology_record(
    course: KoreanGrammarCourse,
    support: KoreanGrammarCourseSupport,
    record: GrammarNativeAnalysisRecord | Mapping,
    claims: GrammarSentenceMorphologyClaims | Mapping,
) -> dict:
    """Validate one candidate; semantic correctness requires external reviews."""
    record = _typed(GrammarNativeAnalysisRecord, record)
    claims = _typed(GrammarSentenceMorphologyClaims, claims)
    cards = {card.entry_id: card for card in course.cards}
    if record.entry_id not in cards or (record.entry_id, record.field) != (claims.entry_id, claims.field):
        raise ValueError("mismatched_morphology_record")
    if any(part.course_sha256 != course.content_sha256
           for part in (support.lexical, support.observations)):
        raise ValueError("stale_morphology_support")
    card = cards[record.entry_id]
    text = getattr(card, record.field)
    text_hash = sha256(text.encode("utf-8")).hexdigest()
    if record.text_sha256 != text_hash or claims.text_sha256 != text_hash:
        raise ValueError("stale_morphology_text")
    analysis = record.analysis
    if claims.analysis_sha256 != digest(analysis):
        raise ValueError("stale_native_analysis")
    if analysis.status != KoreanMorphologyStatus.RESOLVED:
        raise ValueError("unavailable_or_inconclusive_native_analysis")
    alternatives = {row.rank: row for row in analysis.alternatives}
    if set(alternatives) != {1, 2}:
        raise ValueError("invalid_native_alternative_inventory")
    native = {rank: _native_morphemes(text, row) for rank, row in alternatives.items()}
    rejected = claims.rejected_alternatives[0]
    if rejected.rank != 3 - claims.selected_rank or rejected.alternative_sha256 != digest(alternatives[rejected.rank]):
        raise ValueError("stale_rejected_alternative")
    morphemes = native[claims.selected_rank]
    lexical = {entry.entry_id: entry for entry in support.lexical.entries}
    covered_lexical, contextual_pos = set(), []
    for claim in claims.lexical_claims:
        entry = lexical.get(claim.support_entry_id)
        if (entry is None or record.entry_id not in entry.used_by
                or entry.source_entry_sha256 != claim.source_entry_sha256):
            raise ValueError("unbound_lexical_source")
        refs = _references(claim, morphemes)
        if covered_lexical.intersection(refs):
            raise ValueError("duplicate_lexical_morpheme_claim")
        items = tuple(morphemes[ref] for ref in refs)
        if claim.mapping_kind == "compound_lemma":
            key = (entry.lemma, tuple((item.form, item.pos) for item in items))
            if (_COMPOUNDS.get(key) != entry.source_pos
                    or len({ref[0] for ref in refs}) != 1
                    or [ref[1] for ref in refs] != list(range(refs[0][1], refs[0][1] + len(refs)))):
                raise ValueError("unproven_compound_lexical_identity")
        else:
            if len(items) != 1 or items[0].lemma != entry.lemma or items[0].pos not in _LEXICAL:
                raise ValueError("unproven_lexical_lemma")
            pos_matches = items[0].pos in _SOURCE_POS[entry.source_pos]
            if claim.mapping_kind == "exact_lemma" and not pos_matches:
                raise ValueError("lexical_pos_requires_contextual_decision")
            if claim.mapping_kind == "contextual_pos":
                if pos_matches:
                    raise ValueError("unnecessary_contextual_pos_claim")
                contextual_pos.append(entry.entry_id)
        covered_lexical.update(refs)
    required_lexical = {ref for ref, item in morphemes.items()
                        if item.pos in _LEXICAL | _DERIVATIONAL}
    if not required_lexical <= covered_lexical:
        raise ValueError("uncovered_lexical_morpheme")
    observed = next(row for row in support.observations.entries if row.entry_id == card.entry_id)
    ids = [claim.grammar_id for claim in claims.grammar_claims]
    if len(set(ids)) != len(ids) or set(ids) != set(observed.observed_grammar_ids):
        raise ValueError("mismatched_grammar_inventory")
    if observed.unresolved:
        raise ValueError("unresolved_grammar_observation")
    covered_grammar = set()
    for claim in claims.grammar_claims:
        refs = _references(claim, morphemes)
        if (claim.evidence_kind == "clause_structure") != (claim.grammar_id in _CLAUSE_CONCEPTS):
            raise ValueError("invalid_clause_structure_claim")
        if claim.evidence_kind != "clause_structure":
            covered_grammar.update(refs)
    if set(morphemes) - covered_lexical - covered_grammar:
        raise ValueError("uncovered_grammatical_morpheme")
    consensus = alternatives[1].surface_spans == alternatives[2].surface_spans
    subject = {
        "validator": VALIDATOR_ID, "course_sha256": course.content_sha256,
        "support_sha256": digest(support), "native_record": record.model_dump(mode="json"),
        "claims": claims.model_dump(mode="json"),
    }
    return {
        "entry_id": record.entry_id, "field": record.field,
        "validator_id": VALIDATOR_ID, "deterministically_valid": True,
        "native_top2_consensus": consensus, "selected_rank": claims.selected_rank,
        "selected_morpheme_count": len(morphemes),
        "lexical_claim_count": len(claims.lexical_claims),
        "grammar_claim_count": len(claims.grammar_claims),
        "contextual_pos_claims": contextual_pos,
        "review_subject_sha256": digest(subject),
        "status": "contextual_review_required", "required_independent_passes": 3,
        "learner_ready": False,
    }


def validate_grammar_morphology_claims(
    course: KoreanGrammarCourse,
    support: KoreanGrammarCourseSupport,
    records: Sequence[GrammarNativeAnalysisRecord | Mapping],
    manifest: KoreanGrammarMorphologyManifest | Mapping,
) -> dict:
    """Bind a complete 2-fields-per-card candidate to its exact native evidence."""
    manifest = _typed(KoreanGrammarMorphologyManifest, manifest)
    if len(records) > 512:
        raise ValueError("oversized_native_record_inventory")
    native = tuple(_typed(GrammarNativeAnalysisRecord, row) for row in records)
    if manifest.course_sha256 != course.content_sha256 or manifest.support_sha256 != digest(support):
        raise ValueError("stale_morphology_manifest")
    expected = {(card.entry_id, field) for card in course.cards
                for field in ("example_sentence", "spoken_sample")}
    native_by_key = {(row.entry_id, row.field): row for row in native}
    claims_by_key = {(row.entry_id, row.field): row for row in manifest.records}
    if (len(native_by_key) != len(native) or len(claims_by_key) != len(manifest.records)
            or set(native_by_key) != expected or set(claims_by_key) != expected):
        raise ValueError("incomplete_or_duplicate_morphology_record_inventory")
    if any(digest(row.analysis.analyzer_fingerprint) != manifest.analyzer_fingerprint_sha256
           for row in native):
        raise ValueError("mismatched_native_analyzer_fingerprint")
    from multilang.services.korean_grammar_course import validate_grammar_course_support
    support_report = validate_grammar_course_support(course, support)
    if support_report["progression_failures"] or support_report["unresolved"]:
        raise ValueError("invalid_morphology_curriculum")
    results = [validate_grammar_morphology_record(course, support, row, claims_by_key[key])
               for key, row in native_by_key.items()]
    serialized_native = [row.model_dump(mode="json") for row in native]
    return {
        "validator_id": VALIDATOR_ID, "deterministically_valid": True,
        "course_sha256": course.content_sha256, "support_sha256": digest(support),
        "claims_sha256": digest(manifest), "native_records_sha256": digest(serialized_native),
        "review_subject_sha256": digest({
            "validator": VALIDATOR_ID, "manifest": manifest.model_dump(mode="json"),
            "records": serialized_native,
        }),
        "record_count": len(results),
        "native_consensus_count": sum(row["native_top2_consensus"] for row in results),
        "contextual_decision_count": sum(not row["native_top2_consensus"] for row in results),
        "records": results, "status": "contextual_review_required",
        "required_independent_passes": 3, "learner_ready": False,
    }
