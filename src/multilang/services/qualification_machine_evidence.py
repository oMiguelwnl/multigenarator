"""Expand verified local evidence without rewriting sources or measured counts.

New packets bind their exact parent items and the published pipeline manifest.
Every displayed corpus excerpt is an unchanged source sentence. Inclusion in a
measurement is reproduced separately; duplicate or ambiguous evidence is never
silently presented as an additional counted occurrence.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, model_validator

from multilang.domain.form_evidence import (
    CorpusEvidenceContext,
    EvidenceOccurrence,
    FormEvidenceReport,
)
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import sentence_hash
from multilang.services.form_evidence import measure_form_evidence
from multilang.services.qualification_pipeline import QualificationPipelineRequest, _resume
from multilang.services.qualification_review import ReviewPacket, ReviewSource, _json
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_sources import LexicalSenseCandidate, _verified_lines

Coverage = Literal["complete", "partial", "unavailable", "not_applicable"]


class OccurrenceProvenance(NativeContract):
    occurrence_sha256: Sha256
    physical_sha256: Sha256
    source_sha256: Sha256
    document_id: Identifier | None
    sentence_id: Identifier
    sentence_sha256: Sha256
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=512)
    status: Literal[
        "included", "excluded_duplicate_document", "excluded_ambiguous", "excluded_measurement"
    ]
    duplicate_record_count: int = Field(default=0, ge=0)
    source_index: int | None = Field(default=None, ge=0, le=127)


class ItemEvidenceProvenance(NativeContract):
    item_id: Identifier
    parent_item_sha256: Sha256
    enriched_item_sha256: Sha256
    parent_source_packet_sha256s: tuple[Sha256, ...]
    coverage: Coverage
    blockers: tuple[Identifier, ...] = ()
    source_record_sha256: Sha256 | None = None
    candidate_sha256: Sha256 | None = None
    measurement_sha256: Sha256 | None = None
    measured_count: int | None = Field(default=None, ge=0)
    raw_occurrence_count: int = Field(default=0, ge=0)
    included_occurrence_count: int = Field(default=0, ge=0)
    excluded_occurrence_count: int = Field(default=0, ge=0)
    duplicate_occurrence_count: int = Field(default=0, ge=0)
    omitted_occurrence_count: int = Field(default=0, ge=0)
    occurrences: tuple[OccurrenceProvenance, ...] = Field(default=(), max_length=1000000)
    omitted_lexical_fields: dict[Identifier, int] = Field(default_factory=dict, max_length=16)


class MachineEvidenceEnrichment(NativeContract):
    schema_version: Literal[1] = 1
    packet: ReviewPacket
    parent_packet_sha256: Sha256
    pipeline_sha256: Sha256
    pipeline_manifest_file_sha256: Sha256
    item_provenance: tuple[ItemEvidenceProvenance, ...] = Field(min_length=1, max_length=5000)
    coverage: Literal["complete", "partial"]
    production_eligible: Literal[False] = False
    source_authenticity_independently_verified: Literal[False] = False

    @model_validator(mode="after")
    def bound_projection(self):
        by_id = {item.item_id: item.item_sha256 for item in self.packet.items}
        if (
            len(self.item_provenance) != len(by_id)
            or {row.item_id: row.enriched_item_sha256 for row in self.item_provenance} != by_id
        ):
            raise ValueError("enrichment provenance does not match packet items")
        items = {item.item_id: item for item in self.packet.items}
        for proof in self.item_provenance:
            item = items[proof.item_id]
            included = sum(row.status == "included" for row in proof.occurrences)
            duplicates = sum(row.duplicate_record_count for row in proof.occurrences)
            omitted = sum(row.source_index is None for row in proof.occurrences)
            if (
                proof.included_occurrence_count != included
                or proof.excluded_occurrence_count != len(proof.occurrences) - included
                or proof.duplicate_occurrence_count != duplicates
                or proof.raw_occurrence_count != len(proof.occurrences) + duplicates
                or proof.omitted_occurrence_count != omitted
            ):
                raise ValueError("enrichment occurrence provenance count mismatch")
            for occurrence in proof.occurrences:
                if occurrence.source_index is None:
                    continue
                if occurrence.source_index >= len(item.sources):
                    raise ValueError("enrichment source provenance index mismatch")
                source = item.sources[occurrence.source_index]
                if (
                    source.source_sha256 != occurrence.source_sha256
                    or source.record_id != occurrence.physical_sha256
                    or source.document_id != occurrence.document_id
                    or source.sentence_id != occurrence.sentence_id
                    or sentence_hash(source.excerpt) != occurrence.sentence_sha256
                    or source.excerpt[occurrence.start : occurrence.end] != occurrence.text
                ):
                    raise ValueError("enrichment exact source span provenance mismatch")
        expected_coverage = (
            "partial"
            if any(proof.coverage in {"partial", "unavailable"} for proof in self.item_provenance)
            else "complete"
        )
        if self.coverage != expected_coverage:
            raise ValueError("enrichment coverage provenance mismatch")
        return self

    @computed_field
    @property
    def enrichment_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def _pipeline(root, digest):
    # The caller supplies an external byte hash; self-hashes alone are not an
    # authenticity claim. _resume checks every published output against it.
    _read_bytes(root / "manifest.json", digest, limit=1024**2)
    request = QualificationPipelineRequest.model_validate(_json(_read_bytes(root / "request.json")))
    evidence = _json(_read_bytes(root / "source-evidence.json"))
    manifest = _resume(root, request.model_dump(mode="json"), evidence)
    _read_bytes(root / "manifest.json", digest, limit=1024**2)
    return request, manifest


def _artifact(root, manifest, name, *, limit=128 * 1024**2):
    digest = manifest["files"].get(name)
    if digest is None:
        raise ValueError("pipeline evidence artifact is unavailable")
    return _read_bytes(root / name, digest, limit=limit)


def _parent_items(root, manifest, packet):
    wanted = {item.item_id: item.item_sha256 for item in packet.items}
    found = defaultdict(set)
    for row in manifest["pilot"]["packets"]:
        if row["split"] != packet.split:
            continue
        path = "pilot/" + row["path"] + "/packet.json"
        original = ReviewPacket.model_validate(_json(_artifact(root, manifest, path)))
        if (
            original.packet_sha256 != row["packet_sha256"]
            or original.language != packet.language
            or original.profile_sha256 != packet.profile_sha256
            or original.rubric_sha256 != packet.rubric_sha256
        ):
            raise ValueError("parent packet profile or source binding mismatch")
        for item in original.items:
            if item.item_id in wanted and item.item_sha256 == wanted[item.item_id]:
                found[item.item_id].add(original.packet_sha256)
    if set(found) != set(wanted):
        raise ValueError("parent item is not an exact published pipeline item")
    return {key: tuple(sorted(values)) for key, values in found.items()}


def _candidates(root, manifest, limits):
    result = {}
    for name in ("pilot/candidates.jsonl", "pilot/unknown-pos-candidates.jsonl"):
        if name not in manifest["files"]:
            continue
        for line in _verified_lines(root / name, manifest["files"][name], limits):
            if not line.strip():
                continue
            candidate = LexicalSenseCandidate.model_validate(_json(line.encode()))
            if candidate.candidate_id in result and result[candidate.candidate_id] != candidate:
                raise ValueError("conflicting published candidate records")
            result[candidate.candidate_id] = candidate
            if len(result) > limits.max_unique_entries:
                raise ValueError("candidate enrichment record limit exceeded")
    return result


def _measurement_data(root, manifest, limits):
    if "pilot/measurements.json" not in manifest["files"]:
        return None, (), None
    context = CorpusEvidenceContext.model_validate(
        _json(_artifact(root, manifest, "pilot/corpus-context.json"))
    )
    name = "pilot/calibration-occurrences.jsonl"
    occurrences = []
    for line in _verified_lines(root / name, manifest["files"][name], limits):
        if line.strip():
            occurrences.append(EvidenceOccurrence.model_validate(_json(line.encode())))
        if len(occurrences) > min(limits.max_records, 1000000):
            raise ValueError("occurrence enrichment record limit exceeded")
    original = FormEvidenceReport.model_validate(
        _json(_artifact(root, manifest, "pilot/measurements.json"))
    )
    reproduced = measure_form_evidence(context, occurrences)
    if reproduced != original:
        raise ValueError("published measurements differ from source occurrence replay")
    return context, tuple(occurrences), reproduced


def _physical(item, docs):
    document = docs.get((item.source_sha256, item.document_id))
    return canonical_sha256(
        {
            "document": document.text_sha256 if document else item.source_sha256,
            "sentence": [item.sentence_id, item.sentence],
            "start": item.start,
            "end": item.end,
        }
    )


def _occurrence_hash(item):
    return canonical_sha256(item.model_dump(mode="json", exclude_computed_fields=True))


def _classify_occurrences(context, occurrences, measurement):
    """Mirror physical identity, but use the replayed measurement as inclusion authority."""
    docs = {(doc.source_sha256, doc.document_id): doc for doc in context.documents}
    representatives = {}
    for doc in sorted(context.documents, key=lambda doc: (doc.source_sha256, doc.document_id)):
        representatives.setdefault(doc.text_sha256, (doc.source_sha256, doc.document_id))
    grouped_physical, distinct, repeated = defaultdict(set), {}, Counter()
    for item in occurrences:
        document = docs.get((item.source_sha256, item.document_id))
        copied = document is not None and representatives[document.text_sha256] != (
            item.source_sha256,
            item.document_id,
        )
        physical = _physical(item, docs)
        if not copied:
            grouped_physical[physical].add(item.group_sha256)
        if item.group_sha256 == measurement.group_sha256:
            digest = _occurrence_hash(item)
            repeated[digest] += 1
            distinct[digest] = (item, physical, copied)
    included = set(measurement.occurrence_sha256s)
    result = []
    for digest, (item, physical, copied) in sorted(distinct.items()):
        status = (
            "excluded_duplicate_document"
            if copied
            else "excluded_ambiguous"
            if len(grouped_physical[physical]) > 1
            else "included"
            if physical in included
            else "excluded_measurement"
        )
        result.append(
            OccurrenceProvenance(
                occurrence_sha256=digest,
                physical_sha256=physical,
                source_sha256=item.source_sha256,
                document_id=item.document_id,
                sentence_id=item.sentence_id,
                sentence_sha256=sentence_hash(item.sentence),
                start=item.start,
                end=item.end,
                text=item.text,
                status=status,
                duplicate_record_count=repeated[digest] - 1,
            )
        )
    return tuple(result)


def _encoded(value):
    # Escaping, not normalization, preserves raw source strings (including NFD)
    # while the review excerpt itself remains valid NFC text.
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _lexical_projection(candidate):
    fields = ("glosses", "form_of", "forms", "tags", "examples", "sounds", "source_sense_ids")
    payload = {
        "origin": "verified-prepared-candidate-projection",
        "transformation": "JSON-escaped-original-fields-v1",
        "candidate_id": candidate.candidate_id,
        "candidate_sha256": canonical_sha256(candidate.model_dump(mode="json")),
        "source_record_sha256": candidate.source_record_sha256,
        "projection_complete": True,
        "original_field_counts": {key: len(getattr(candidate, key)) for key in fields},
        "omitted_counts": {key: 0 for key in fields},
        "candidate": {
            "lemma": candidate.lemma,
            "pos": candidate.pos,
            "kind": candidate.kind,
            **{key: [] for key in fields},
        },
        "note": "Source evidence only. No approved sense, frequency, rule or qualification is inferred.",
    }
    # Reserve room for counters/false markers before deciding whether to retain
    # each complete source value. We never truncate a string into an alleged quote.
    for key in fields:
        for value in getattr(candidate, key):
            payload["candidate"][key].append(value)
            if len(_encoded(payload)) > 63500:
                payload["candidate"][key].pop()
                payload["omitted_counts"][key] += 1
                payload["projection_complete"] = False
    encoded = _encoded(payload)
    if len(encoded) > 64000:
        raise ValueError("lexical enrichment metadata exceeds excerpt bound")
    return encoded, {key: count for key, count in payload["omitted_counts"].items() if count}


def _lexical(item, candidate, parents):
    common = dict(
        item_id=item.item_id,
        parent_item_sha256=item.item_sha256,
        enriched_item_sha256=item.item_sha256,
        parent_source_packet_sha256s=parents,
    )
    if candidate is None:
        return item, ItemEvidenceProvenance(
            **common, coverage="unavailable", blockers=("published_candidate_unavailable",)
        )
    digest = canonical_sha256(candidate.model_dump(mode="json"))
    sources = [source for source in item.sources if source.record_id == candidate.candidate_id]
    if digest != item.candidate_sha256 or not sources:
        raise ValueError("lexical parent candidate checksum or source binding mismatch")
    if len(item.sources) >= 128:
        return item, ItemEvidenceProvenance(
            **common,
            coverage="unavailable",
            blockers=("review_source_limit",),
            candidate_sha256=digest,
            source_record_sha256=candidate.source_record_sha256,
        )
    excerpt, omitted = _lexical_projection(candidate)
    enriched = item.model_copy(
        update={
            "sources": (
                *item.sources,
                ReviewSource(
                    source_id="prepared-candidate-record",
                    source_sha256=sources[0].source_sha256,
                    record_id=candidate.source_record_sha256,
                    excerpt=excerpt,
                ),
            )
        }
    )
    common["enriched_item_sha256"] = enriched.item_sha256
    return enriched, ItemEvidenceProvenance(
        **common,
        coverage="partial" if omitted else "complete",
        blockers=("lexical_projection_truncated",) if omitted else (),
        source_record_sha256=candidate.source_record_sha256,
        candidate_sha256=digest,
        omitted_lexical_fields=omitted,
    )


def _form(item, context, occurrences, report, parents, pipeline_digest):
    common = dict(
        item_id=item.item_id,
        parent_item_sha256=item.item_sha256,
        enriched_item_sha256=item.item_sha256,
        parent_source_packet_sha256s=parents,
        measurement_sha256=item.measurement_sha256,
    )
    measurement = (
        next(
            (
                row
                for row in report.measurements
                if row.measurement_sha256 == item.measurement_sha256
            ),
            None,
        )
        if report
        else None
    )
    if measurement is None:
        return item, ItemEvidenceProvenance(
            **common, coverage="unavailable", blockers=("published_measurement_unavailable",)
        )
    expected = {
        "observed_count": measurement.observed_count,
        "frequency_per_million": measurement.frequency_per_million,
    }
    if measurement.document_count is not None:
        expected["document_count"] = measurement.document_count
    if measurement.dispersion is not None:
        expected["dispersion"] = measurement.dispersion
    if (
        dict(item.measurements) != expected
        or item.features != measurement.features
        or item.candidate_sha256 != measurement.measurement_sha256
        or (item.lemma, item.pos, item.text, item.canonical_sense_id)
        != (measurement.lemma, measurement.pos, measurement.text, measurement.sense_id)
    ):
        raise ValueError("parent form differs from its replayed measurement")
    rows = _classify_occurrences(context, occurrences, measurement)
    by_hash = {
        _occurrence_hash(occurrence): occurrence
        for occurrence in occurrences
        if occurrence.group_sha256 == measurement.group_sha256
    }
    included = sum(row.status == "included" for row in rows)
    excluded = len(rows) - included
    duplicates = sum(row.duplicate_record_count for row in rows)
    blockers = []
    if included != measurement.observed_count:
        blockers.append("measurement_coverage_mismatch")
    if len(rows) > 127:
        blockers.append("review_source_limit")
    omitted = max(0, len(rows) - 127)
    coverage = "partial" if blockers else "complete"
    notice = {
        "origin": "derived-enrichment-coverage",
        "coverage": coverage,
        "blockers": blockers,
        "measured_count_unchanged": measurement.observed_count,
        "raw_occurrence_count": len(rows) + duplicates,
        "included_occurrence_count": included,
        "excluded_occurrence_count": excluded,
        "duplicate_occurrence_count": duplicates,
        "omitted_occurrence_count": omitted,
        "note": "Only included occurrences enter the frozen measurement. Excluded or repeated records are not additional frequency. Missing contexts remain unavailable; senses remain unreviewed.",
    }
    sources = [
        ReviewSource(
            source_id="enrichment-coverage",
            source_sha256=pipeline_digest,
            record_id=item.item_sha256,
            excerpt=_encoded(notice),
        )
    ]
    bound_rows = []
    for index, row in enumerate(rows):
        if index < 127:
            source_index = len(sources)
            original = by_hash[row.occurrence_sha256]
            sources.append(
                ReviewSource(
                    source_id="calibration-corpus-" + row.status.replace("_", "-"),
                    source_sha256=row.source_sha256,
                    record_id=row.physical_sha256,
                    document_id=row.document_id,
                    sentence_id=row.sentence_id,
                    excerpt=original.sentence,
                )
            )
            row = row.model_copy(update={"source_index": source_index})
        bound_rows.append(row)
    enriched = item.model_copy(update={"sources": tuple(sources)})
    common["enriched_item_sha256"] = enriched.item_sha256
    return enriched, ItemEvidenceProvenance(
        **common,
        coverage=coverage,
        blockers=tuple(blockers),
        measured_count=measurement.observed_count,
        raw_occurrence_count=len(rows) + duplicates,
        included_occurrence_count=included,
        excluded_occurrence_count=excluded,
        duplicate_occurrence_count=duplicates,
        omitted_occurrence_count=omitted,
        occurrences=tuple(bound_rows),
    )


def enrich_machine_packet(
    packet: ReviewPacket, *, pipeline: Path, manifest_sha256: str
) -> MachineEvidenceEnrichment:
    """Return a separately identified packet with verified local source projections."""
    packet = ReviewPacket.model_validate(packet.model_dump(mode="json"))
    root = _plain_path(pipeline)
    request, manifest = _pipeline(root, manifest_sha256)
    if packet.language != request.language:
        raise ValueError("parent packet language does not match pipeline")
    parents = _parent_items(root, manifest, packet)
    candidates = (
        _candidates(root, manifest, request.limits)
        if any(item.kind == "lexical" for item in packet.items)
        else {}
    )
    context, occurrences, report = (
        _measurement_data(root, manifest, request.limits)
        if any(item.kind == "form" and item.measurement_sha256 for item in packet.items)
        else (None, (), None)
    )
    enriched, provenance = [], []
    for item in packet.items:
        if item.kind == "lexical":
            derived, proof = _lexical(
                item, candidates.get(item.candidate_id), parents[item.item_id]
            )
        elif item.kind == "form" and item.measurement_sha256:
            derived, proof = _form(
                item, context, occurrences, report, parents[item.item_id], manifest_sha256
            )
        else:
            derived, proof = (
                item,
                ItemEvidenceProvenance(
                    item_id=item.item_id,
                    parent_item_sha256=item.item_sha256,
                    enriched_item_sha256=item.item_sha256,
                    parent_source_packet_sha256s=parents[item.item_id],
                    coverage="not_applicable",
                ),
            )
        enriched.append(derived)
        provenance.append(proof)
    child = packet.model_copy(
        update={
            "packet_id": "machine-enriched:"
            + canonical_sha256(
                {
                    "parent": packet.packet_sha256,
                    "pipeline": manifest["pipeline_sha256"],
                    "items": [item.item_sha256 for item in enriched],
                }
            ),
            "items": tuple(enriched),
        }
    )
    result = MachineEvidenceEnrichment(
        packet=child,
        parent_packet_sha256=packet.packet_sha256,
        pipeline_sha256=manifest["pipeline_sha256"],
        pipeline_manifest_file_sha256=manifest_sha256,
        item_provenance=tuple(provenance),
        coverage="partial"
        if any(row.coverage in {"partial", "unavailable"} for row in provenance)
        else "complete",
    )
    if (
        len(child.model_dump_json().encode()) > 32 * 1024**2
        or len(result.model_dump_json().encode()) > 128 * 1024**2
    ):
        raise ValueError("machine evidence enrichment exceeds artifact byte limit")
    return result
