"""Exact form-review packets replayed from a complete document partition."""

import hashlib
from collections import defaultdict
from typing import Literal

from pydantic import Field, computed_field

from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.form_evidence import measure_form_evidence
from multilang.services.qualification_evaluation_partitions import (
    EvaluationDocumentPartition,
    verify_evaluation_partition,
)
from multilang.services.qualification_evaluation_references import (
    DictionaryReferenceRegistry,
    reference_excerpt,
    verify_dictionary_references,
)
from multilang.services.qualification_review import FormReviewItem, ReviewPacket, ReviewSource


class PartitionReviewBundle(NativeContract):
    schema_version: Literal["partition-review-1"] = "partition-review-1"
    measurement_origin: Literal["aligned-ud-source-annotations"] = "aligned-ud-source-annotations"
    partition: EvaluationDocumentPartition
    references: DictionaryReferenceRegistry
    group_sha256s: tuple[Sha256, ...] = Field(min_length=1, max_length=64)
    context_sha256: Sha256
    population_sha256: Sha256
    packet: ReviewPacket
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def bundle_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def prepare_partition_review(
    partition: EvaluationDocumentPartition,
    references: DictionaryReferenceRegistry,
    *,
    group_sha256s: tuple[str, ...],
    profile_sha256: str,
    rubric_sha256: str,
    packet_id: str,
) -> PartitionReviewBundle:
    partition = verify_evaluation_partition(partition)
    references = verify_dictionary_references(references)
    selected = tuple(group_sha256s)
    if not 1 <= len(selected) <= 64 or len(set(selected)) != len(selected):
        raise ValueError("partition review needs unique bounded group selection")
    if partition.context is None or references.spec.language != partition.spec.language:
        raise ValueError("partition review requires a measured language-compatible population")
    report = measure_form_evidence(partition.context, partition.occurrences)
    partition_sha256 = partition.partition_sha256
    registry_sha256 = references.registry_sha256
    measurements = {row.group_sha256: row for row in report.measurements}
    if set(selected) - measurements.keys():
        raise ValueError("selected form is absent from complete partition measurements")
    grouped = defaultdict(list)
    for occurrence in partition.occurrences:
        grouped[occurrence.group_sha256].append(occurrence)
    documents = {(d.source_sha256, d.document_id): d for d in partition.context.documents}
    items = []
    for key in selected:
        measurement = measurements[key]
        source_rows, keys = (
            {},
            {
                canonical_sha256(["partition", partition_sha256]),
                canonical_sha256(["population", report.population_sha256]),
            },
        )
        for occurrence in grouped[key]:
            source_key = (occurrence.source_sha256, occurrence.document_id, occurrence.sentence_id)
            source_rows[source_key] = ReviewSource(
                source_id="partition-corpus",
                source_sha256=occurrence.source_sha256,
                record_id=key,
                document_id=occurrence.document_id,
                sentence_id=occurrence.sentence_id,
                excerpt=occurrence.sentence,
            )
            keys.update(
                (
                    canonical_sha256(["source", occurrence.source_sha256]),
                    canonical_sha256(
                        ["sentence-text", hashlib.sha256(occurrence.sentence.encode()).hexdigest()]
                    ),
                    canonical_sha256(
                        [
                            "document-content",
                            documents[
                                (occurrence.source_sha256, occurrence.document_id)
                            ].text_sha256,
                        ]
                    ),
                )
            )
        dictionary_rows = [
            record
            for record in references.records
            if (record.lemma, record.pos) == (measurement.lemma, measurement.pos)
        ]
        if not dictionary_rows:
            raise ValueError("selected form has no exact registered dictionary reference")
        sources = tuple(source_rows.values()) + tuple(
            ReviewSource(
                source_id="dictionary-reference-v1",
                source_sha256=registry_sha256,
                record_id=record.record_sha256,
                excerpt=reference_excerpt(record),
            )
            for record in dictionary_rows
        )
        if len(sources) > 64:
            raise ValueError(
                "complete form review exceeds source limit; choose a smaller partition"
            )
        values = {
            "observed_count": measurement.observed_count,
            "frequency_per_million": measurement.frequency_per_million,
            "effective_token_count": report.effective_token_count,
        }
        if measurement.document_count is not None:
            values["document_count"] = measurement.document_count
        if measurement.dispersion is not None:
            values["dispersion"] = measurement.dispersion
        item_sha = canonical_sha256(measurement.model_dump(mode="json"))
        items.append(
            FormReviewItem(
                item_id="partition-form:" + key,
                candidate_id="partition-form:" + key,
                candidate_sha256=item_sha,
                measurement_sha256=item_sha,
                lemma=measurement.lemma,
                pos=measurement.pos,
                text=measurement.text,
                features=measurement.features,
                sources=sources,
                evidence_source_keys=tuple(sorted(keys)),
                measurements=values,
                proposed_ratings={"frequency": measurement.evidence_values["frequency"]},
                missing_reasons=(
                    "UD source annotations are evidence, not a qualified analyzer or sense assignment",
                    "All occurrences of this form group need a coherent reviewed sense; otherwise abstain",
                    "Unsupported importance criteria must be omitted, not set to zero",
                ),
            )
        )
    packet = ReviewPacket(
        packet_id=packet_id,
        language=partition.spec.language,
        split=partition.spec.split,
        profile_sha256=profile_sha256,
        rubric_sha256=rubric_sha256,
        items=tuple(items),
    )
    return PartitionReviewBundle(
        partition=partition,
        references=references,
        group_sha256s=selected,
        context_sha256=report.context_sha256,
        population_sha256=report.population_sha256,
        packet=packet,
    )


def verify_partition_review(bundle: PartitionReviewBundle) -> PartitionReviewBundle:
    bundle = PartitionReviewBundle.model_validate(
        bundle.model_dump(mode="json", exclude_computed_fields=True)
    )
    replay = prepare_partition_review(
        bundle.partition,
        bundle.references,
        group_sha256s=bundle.group_sha256s,
        profile_sha256=bundle.packet.profile_sha256,
        rubric_sha256=bundle.packet.rubric_sha256,
        packet_id=bundle.packet.packet_id,
    )
    if replay != bundle:
        raise ValueError("partition review bundle measurement replay detected drift")
    return replay
