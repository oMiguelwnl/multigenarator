from decimal import Decimal, localcontext

import pytest


def api():
    from multilang.domain.form_evidence import (
        CorpusEvidenceContext,
        EvidenceDocument,
        EvidenceOccurrence,
    )
    from multilang.services.form_evidence import measure_form_evidence

    return CorpusEvidenceContext, EvidenceDocument, EvidenceOccurrence, measure_form_evidence


def fixture():
    Context, Document, Occurrence, measure = api()
    context = Context(
        language="en",
        split="calibration",
        source_sha256s=("a" * 64,),
        token_count=20,
        documents=(
            Document(
                source_sha256="a" * 64, document_id="d1", text_sha256="b" * 64, token_count=10
            ),
            Document(
                source_sha256="a" * 64, document_id="d2", text_sha256="c" * 64, token_count=10
            ),
        ),
    )
    occurrence = Occurrence(
        language="en",
        split="calibration",
        source_sha256="a" * 64,
        document_id="d1",
        sentence_id="s1",
        sentence="They went.",
        start=5,
        end=9,
        text="went",
        lemma="go",
        pos="VERB",
        features={"tense": "Past"},
    )
    return context, occurrence, measure


def test_deduplication_counts_and_unknown_sense_are_explicit():
    context, occurrence, measure = fixture()
    other = occurrence.model_copy(update={"document_id": "d2"})
    report = measure(context, [occurrence, other, occurrence])
    (item,) = report.measurements
    assert item.observed_count == 2
    assert item.document_count == 2
    assert item.frequency_per_million == Decimal(100000)
    assert item.dispersion == 1
    assert item.sense_id is None
    assert report.duplicate_occurrences == 1
    assert item.evidence_values == {"frequency": Decimal("0.5")}
    assert "irregularity" in item.missing_reasons
    assert item.production_eligible is False
    assert measure(context, [other, occurrence, occurrence]) == report


def test_missing_document_boundaries_do_not_invent_dispersion():
    context, occurrence, measure = fixture()
    context = context.model_copy(update={"documents": ()})
    result = measure(context, [occurrence.model_copy(update={"document_id": None})])
    (item,) = result.measurements
    assert item.document_count is None
    assert item.dispersion is None
    assert "document" in item.dispersion_missing_reason


def test_duplicate_documents_are_not_independent_evidence():
    context, occurrence, measure = fixture()
    same = context.documents[1].model_copy(update={"text_sha256": "b" * 64})
    context = context.model_copy(update={"documents": (context.documents[0], same)})
    result = measure(context, [occurrence, occurrence.model_copy(update={"document_id": "d2"})])
    assert result.effective_token_count == 10
    assert result.measurements[0].observed_count == 1
    assert result.measurements[0].document_count == 1


@pytest.mark.parametrize(
    "change",
    [
        {"split": "evaluation"},
        {"source_sha256": "d" * 64},
        {"language": "pt"},
        {"document_id": "missing"},
    ],
)
def test_wrong_source_or_split_rejected(change):
    context, occurrence, measure = fixture()
    with pytest.raises(ValueError):
        measure(context, [occurrence.model_copy(update=change)])


@pytest.mark.parametrize(
    "change", [{"text": "gone"}, {"end": 10}, {"sentence": "cafe\u0301 went."}]
)
def test_exact_nfc_source_spans_required(change):
    _, occurrence, _ = fixture()
    with pytest.raises(ValueError):
        occurrence.model_copy(update=change)


def test_conflicting_same_occurrence_is_ambiguous_not_double_counted():
    context, occurrence, measure = fixture()
    alternative = occurrence.model_copy(update={"lemma": "wend"})
    report = measure(context, [occurrence, alternative])
    assert report.ambiguous_occurrences == 1
    assert not report.measurements


def test_same_surface_different_analysis_preserved_at_distinct_spans():
    context, occurrence, measure = fixture()
    alternative = occurrence.model_copy(update={"sentence_id": "s2", "features": {"tense": "Pres"}})
    assert len(measure(context, [occurrence, alternative]).measurements) == 2


def test_empty_unknown_pos_and_overflow():
    context, occurrence, measure = fixture()
    assert measure(context, []).measurements == ()
    unknown = occurrence.model_copy(update={"pos": "X"})
    assert measure(context, [unknown]).ineligible_occurrences == 1
    with pytest.raises(ValueError, match="limit"):
        measure(context, [occurrence] * 4, max_occurrences=3)


def test_population_hash_binds_normalization_population():
    context, occurrence, measure = fixture()
    a = measure(context, [occurrence])
    b = measure(
        context,
        [
            occurrence,
            occurrence.model_copy(update={"sentence_id": "s2", "text": "went", "lemma": "wend"}),
        ],
    )
    assert a.population_sha256 != b.population_sha256


def test_unsupported_pos_and_reserved_sense_cannot_be_measured_as_resolved():
    _, occurrence, _ = fixture()
    for update in ({"pos": "MADEUP"}, {"sense_id": "unknown"}, {"sense_id": "X"}):
        with pytest.raises(ValueError):
            occurrence.model_copy(update=update)


def test_frequency_ties_use_population_midrank():
    context, occurrence, measure = fixture()
    items = [
        occurrence,
        occurrence.model_copy(update={"sentence_id": "s2"}),
        occurrence.model_copy(update={"sentence_id": "s3", "lemma": "wend"}),
        occurrence.model_copy(update={"sentence_id": "s4", "features": {"mood": "Ind"}}),
    ]
    report = measure(context, items)
    ratings = sorted(m.evidence_values["frequency"] for m in report.measurements)
    with localcontext() as arithmetic:
        arithmetic.prec = 50
        assert ratings == [Decimal(1) / 3, Decimal(1) / 3, Decimal(5) / 6]


def test_native_morpheme_evidence_is_preserved_without_identifier_truncation():
    context, occurrence, measure = fixture()
    native = '[{"form":"학교","tag":"NNG"}]' * 40
    occurrence = occurrence.model_copy(update={"features": {"Morphemes": native}})
    assert measure(context, [occurrence]).measurements[0].features["Morphemes"] == native
