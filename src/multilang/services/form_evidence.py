"""Deterministic sample statistics without guessed senses or human ratings."""

from collections import Counter, defaultdict
from collections.abc import Iterable
from decimal import Decimal, localcontext

from multilang.domain.form_evidence import (
    LEXICAL_UPOS,
    CorpusEvidenceContext,
    EvidenceOccurrence,
    FormEvidenceMeasurement,
    FormEvidenceReport,
)
from multilang.domain.lexical_identity import canonical_sha256


def measure_form_evidence(
    context: CorpusEvidenceContext,
    occurrences: Iterable[EvidenceOccurrence],
    *,
    max_occurrences: int = 1000000,
) -> FormEvidenceReport:
    if not 1 <= max_occurrences <= 1000000:
        raise ValueError("occurrence limit must be between 1 and 1000000")
    docs = {(d.source_sha256, d.document_id): d for d in context.documents}
    unique_docs = {d.text_sha256: d.token_count for d in context.documents}
    representatives = {}
    for d in sorted(context.documents, key=lambda d: (d.source_sha256, d.document_id)):
        representatives.setdefault(d.text_sha256, (d.source_sha256, d.document_id))
    denominator = sum(unique_docs.values()) if docs else context.token_count
    physical: dict[str, dict[str, EvidenceOccurrence]] = defaultdict(dict)
    duplicate_count = 0
    for index, item in enumerate(occurrences):
        if index >= max_occurrences:
            raise ValueError("occurrence limit exceeded")
        if item.language != context.language or item.split != context.split:
            raise ValueError("occurrence language/split mismatch")
        if item.source_sha256 not in context.source_sha256s:
            raise ValueError("occurrence source not declared")
        document = docs.get((item.source_sha256, item.document_id))
        if docs and document is None:
            raise ValueError("occurrence document not declared")
        if not docs and item.document_id is not None:
            raise ValueError("document boundaries require declared document metadata")
        if document and representatives[document.text_sha256] != (
            item.source_sha256,
            item.document_id,
        ):
            duplicate_count += 1
            continue
        # Keep repeated sentences within a document, but never count copied documents.
        key = canonical_sha256(
            {
                "document": document.text_sha256 if document else item.source_sha256,
                "sentence": [item.sentence_id, item.sentence],
                "start": item.start,
                "end": item.end,
            }
        )
        if item.group_sha256 in physical[key]:
            duplicate_count += 1
        physical[key][item.group_sha256] = item
    grouped: dict[str, list[tuple[str, EvidenceOccurrence]]] = defaultdict(list)
    ambiguous = ineligible = 0
    for key, choices in sorted(physical.items()):
        if len(choices) != 1:
            ambiguous += 1
            continue
        item = next(iter(choices.values()))
        if item.pos not in LEXICAL_UPOS:
            ineligible += 1
            continue
        grouped[item.group_sha256].append((key, item))
    if sum(map(len, grouped.values())) > denominator:
        raise ValueError("observed tokens exceed declared corpus denominator")
    population = {key: len(items) for key, items in sorted(grouped.items())}
    histogram = Counter(population.values())
    lower_counts, cumulative = {}, 0
    for frequency, groups in sorted(histogram.items()):
        lower_counts[frequency] = cumulative
        cumulative += groups
    context_sha = canonical_sha256(
        {
            **context.model_dump(mode="json"),
            "documents": sorted(
                (d.model_dump(mode="json") for d in context.documents),
                key=lambda d: (d["source_sha256"], d["document_id"]),
            ),
            "source_sha256s": sorted(context.source_sha256s),
        }
    )
    population_sha = canonical_sha256({"context": context_sha, "counts": population})
    measurements = []
    with localcontext() as arithmetic:
        arithmetic.prec = 50
        for key, items in sorted(grouped.items()):
            example = items[0][1]
            count = len(items)
            doc_count = (
                len({docs[(i.source_sha256, i.document_id)].text_sha256 for _, i in items})
                if docs
                else None
            )
            less = lower_counts[count]
            equal = histogram[count]
            percentile = (Decimal(less) + Decimal(equal) / 2) / len(population)
            measurements.append(
                FormEvidenceMeasurement(
                    group_sha256=key,
                    language=example.language,
                    lemma=example.lemma,
                    pos=example.pos,
                    text=example.text,
                    features=example.features,
                    sense_id=example.sense_id,
                    observed_count=count,
                    document_count=doc_count,
                    frequency_per_million=Decimal(count) * 1000000 / denominator,
                    dispersion=Decimal(doc_count) / len(unique_docs) if docs else None,
                    dispersion_missing_reason=None
                    if docs
                    else "Source document boundaries are unavailable",
                    evidence_values={"frequency": percentile},
                    missing_reasons={
                        name: "Requires explicit source evidence or independent reviewed rating"
                        for name in (
                            "irregularity",
                            "unpredictability",
                            "ambiguity",
                            "unexpected_pronunciation",
                            "prerequisite",
                            "learning_difficulty",
                        )
                    },
                    occurrence_sha256s=tuple(sorted(k for k, _ in items)),
                    population_sha256=population_sha,
                )
            )
    return FormEvidenceReport(
        context_sha256=context_sha,
        population_sha256=population_sha,
        effective_token_count=denominator,
        effective_document_count=len(unique_docs) if docs else None,
        duplicate_occurrences=duplicate_count,
        ambiguous_occurrences=ambiguous,
        ineligible_occurrences=ineligible,
        measurements=tuple(measurements),
    )
