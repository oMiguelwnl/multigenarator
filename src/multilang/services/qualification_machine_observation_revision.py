"""Replayable machine projections of source occurrences, preserving model output.

The original observation and its denominator never change. Exclusion means an
occurrence is left out of this review projection, not removed from the corpus or
classified as nonlexical. Only one replacement at the original physical span is
permitted. These derived measurements and sense labels remain machine proposals.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Annotated, Literal

from pydantic import Field, computed_field, model_validator

from multilang.domain.form_evidence import LEXICAL_UPOS, EvidenceOccurrence, FormEvidenceReport
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import sentence_hash
from multilang.services.form_evidence import measure_form_evidence
from multilang.services.qualification_machine import MachineCaseDecision, MachineQualificationResult
from multilang.services.qualification_machine_draft import replay_machine_result
from multilang.services.qualification_machine_runner import json_bytes
from multilang.services.qualification_machine_sources import (
    VerifiedReviewExcerpt,
    load_verified_review_excerpt,
)
from multilang.services.qualification_observations import CorpusObservationResult
from multilang.services.qualification_review import (
    CaseReviewItem,
    ReviewPacket,
    ReviewSource,
    ReviewToken,
)

Excerpts = Annotated[tuple[VerifiedReviewExcerpt, ...], Field(min_length=1, max_length=16)]


def _sha(value):
    return canonical_sha256(value.model_dump(mode="json", exclude_computed_fields=True))


def _physical(row):
    return row.source_sha256, row.document_id, row.sentence_id, row.sentence, row.start, row.end


def _original(observation):
    original = CorpusObservationResult.model_validate(
        observation.model_dump(mode="json", exclude_computed_fields=True)
    )
    json_bytes(original)
    context, coverage = original.context, original.coverage
    if (
        not 1 <= len(original.occurrences) <= 100000
        or context is None
        or coverage.measured_lexical_tokens != len(original.occurrences)
        or coverage.analyzed_unit_count != len(original.analyses)
        or context.token_count != len(original.occurrences)
        or (context.language, context.split, context.source_sha256s)
        != (original.language, original.split, (original.source_sha256,))
    ):
        raise ValueError("original observation context or count mismatch")
    tokens, units, documents, fingerprints = {}, set(), Counter(), set()
    for unit in original.analyses:
        key = unit.document_id, unit.sentence_id
        if (
            key in units
            or unit.source_sha256 != original.source_sha256
            or unit.analysis.language != original.language.value
            or unit.analysis.sentence_sha256 != sentence_hash(unit.text)
        ):
            raise ValueError("original observation analysis source mismatch")
        units.add(key)
        fingerprints.add(unit.analysis.model_fingerprint)
        for token in unit.analysis.tokens:
            if unit.text[token.start : token.end] != token.text:
                raise ValueError("original observation token span mismatch")
            if token.pos not in LEXICAL_UPOS:
                continue
            document_id = unit.document_id if coverage.document_boundaries_known else None
            physical = (
                original.source_sha256,
                document_id,
                unit.sentence_id,
                unit.text,
                token.start,
                token.end,
            )
            if physical in tokens:
                raise ValueError("duplicate original occurrence span")
            tokens[physical] = token
            documents[unit.document_id] += 1
    seen = set()
    for row in original.occurrences:
        physical = _physical(row)
        token = tokens.get(physical)
        if (
            physical in seen
            or token is None
            or row.language != original.language
            or row.split != original.split
            or (row.text, row.lemma, row.pos, row.features)
            != (token.text, token.lemma, token.pos, dict(token.features))
            or row.sense_id is not None
        ):
            raise ValueError("original occurrence differs from frozen model token")
        seen.add(physical)
    if set(tokens) != seen or tuple(sorted(fingerprints)) != original.model_fingerprints:
        raise ValueError("original observation token inventory mismatch")
    if coverage.document_boundaries_known:
        if coverage.measured_document_count != len(documents) or {
            doc.document_id: doc.token_count for doc in context.documents
        } != dict(documents):
            raise ValueError("original observation document denominator mismatch")
    elif context.documents or coverage.measured_document_count is not None:
        raise ValueError("original observation has unknown document boundaries")
    return original


def _token(row):
    return ReviewToken(
        **{
            key: getattr(row, key)
            for key in ("start", "end", "text", "lemma", "pos", "sense_id", "features")
        }
    )


def _selection(original, wanted):
    if not wanted or len(wanted) > 5000 or len(set(wanted)) != len(wanted):
        raise ValueError("invalid or duplicate occurrence selection")
    by_sha = {_sha(row): row for row in original.occurrences}
    if set(wanted) - set(by_sha):
        raise ValueError("unknown occurrence in revision selection")
    return tuple((key, by_sha[key]) for key in wanted)


def _packet(original, original_sha, revision_id, wanted, profile_sha, rubric_sha, extras):
    items = []
    for key, row in _selection(original, wanted):
        items.append(
            CaseReviewItem(
                item_id="observation-revision:" + key,
                text=row.sentence,
                proposal_tokens=(_token(row),),
                sources=(
                    ReviewSource(
                        source_id="original-corpus-context",
                        source_sha256=row.source_sha256,
                        record_id=key,
                        document_id=row.document_id,
                        sentence_id=row.sentence_id,
                        excerpt=row.sentence,
                    ),
                    *extras.get(key, ()),
                ),
                behavior_tags=("single-occurrence-revision", "preserve-physical-span"),
            )
        )
    return ReviewPacket(
        packet_id="observation-revision:" + canonical_sha256([original_sha, revision_id]),
        language=original.language,
        split=original.split,
        profile_sha256=profile_sha,
        rubric_sha256=rubric_sha,
        items=tuple(items),
    )


def _load_excerpts(supplements, language):
    cache, loaded = {}, {}
    if sum(map(len, supplements.values())) > 128:
        raise ValueError("observation revision supplement limit exceeded")
    for occurrence, references in supplements.items():
        values = []
        for reference in references:
            key = _sha(reference)
            if key not in cache:
                cache[key] = load_verified_review_excerpt(reference, language=language)
            values.append(cache[key])
        loaded[occurrence] = tuple(values)
    return loaded


class MachineObservationRevisionPlan(NativeContract):
    schema_version: Literal["machine-observation-revision-plan-1"] = (
        "machine-observation-revision-plan-1"
    )
    original: CorpusObservationResult
    original_sha256: Sha256
    revision_id: Identifier
    occurrence_sha256s: tuple[Sha256, ...] = Field(min_length=1, max_length=5000)
    supplemental_sources: dict[Sha256, Excerpts] = Field(default_factory=dict, max_length=5000)
    packet: ReviewPacket
    origin: Literal["machine"] = "machine"
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def exact_original_and_packet(self):
        original = _original(self.original)
        if _sha(original) != self.original_sha256:
            raise ValueError("original observation checksum mismatch")
        if set(self.supplemental_sources) - set(self.occurrence_sha256s):
            raise ValueError("supplement targets an unselected occurrence")
        if sum(map(len, self.supplemental_sources.values())) > 128:
            raise ValueError("observation revision supplement limit exceeded")
        extras = {}
        if len(self.packet.items) != len(self.occurrence_sha256s):
            raise ValueError("observation revision packet coverage mismatch")
        for key, item in zip(self.occurrence_sha256s, self.packet.items, strict=True):
            references = self.supplemental_sources.get(key, ())
            if len(item.sources) != len(references) + 1:
                raise ValueError("observation revision supplement inventory mismatch")
            for ref, source in zip(references, item.sources[1:], strict=True):
                if (
                    ref.language != original.language
                    or (source.source_sha256, source.source_id, source.record_id)
                    != (ref.file_sha256, ref.source_id, ref.record_id)
                    or len(source.excerpt) != ref.end - ref.start
                ):
                    raise ValueError("observation revision supplement binding mismatch")
            extras[key] = item.sources[1:]
        expected = _packet(
            original,
            self.original_sha256,
            self.revision_id,
            self.occurrence_sha256s,
            self.packet.profile_sha256,
            self.packet.rubric_sha256,
            extras,
        )
        if expected != self.packet:
            raise ValueError("observation revision packet differs from original occurrences")
        return self

    @computed_field
    @property
    def plan_sha256(self) -> str:
        return _sha(self)


def build_machine_observation_revision(
    observation: CorpusObservationResult,
    *,
    original_sha256: str,
    revision_id: str,
    occurrence_sha256s: Sequence[str],
    profile_sha256: str,
    rubric_sha256: str,
    supplemental_sources: Mapping[str, Sequence[VerifiedReviewExcerpt]] | None = None,
) -> MachineObservationRevisionPlan:
    """Prepare cases; original/occurrence hashes exclude computed Pydantic fields."""
    original = _original(observation)
    if _sha(original) != original_sha256:
        raise ValueError("original observation checksum mismatch")
    wanted = tuple(occurrence_sha256s)
    _selection(original, wanted)
    supplements = {
        key: tuple(
            VerifiedReviewExcerpt.model_validate(ref.model_dump(mode="json")) for ref in refs
        )
        for key, refs in (supplemental_sources or {}).items()
    }
    if set(supplements) - set(wanted):
        raise ValueError("supplement targets an unselected occurrence")
    extras = _load_excerpts(supplements, original.language)
    return MachineObservationRevisionPlan(
        original=original,
        original_sha256=original_sha256,
        revision_id=revision_id,
        occurrence_sha256s=wanted,
        supplemental_sources=supplements,
        packet=_packet(
            original, original_sha256, revision_id, wanted, profile_sha256, rubric_sha256, extras
        ),
    )


class MachineOccurrenceChange(NativeContract):
    occurrence_sha256: Sha256
    item_id: Identifier
    result_sha256: Sha256
    action: Literal["retained_pending", "retained", "replaced", "excluded_from_projection"]
    projected_occurrence_sha256: Sha256 | None
    reason: str = Field(min_length=1, max_length=4000)


def _project(plan, qualification):
    result = replay_machine_result(qualification)
    if result.packet != plan.packet:
        raise ValueError("observation revision qualification packet mismatch")
    outcomes = {row.item_id: row for row in result.decisions}
    replacements, changes, excluded, blockers = {}, [], [], {}
    for key, original in _selection(plan.original, plan.occurrence_sha256s):
        item_id = "observation-revision:" + key
        outcome = outcomes[item_id]
        decision = outcome.decision
        row, action = original, "retained_pending"
        reason = outcome.status
        if outcome.status == "machine_agreement" and isinstance(decision, MachineCaseDecision):
            reason = decision.reason
            if decision.expected_match is False and decision.tokens == ():
                row, action = None, "excluded_from_projection"
                excluded.append(key)
            else:
                if decision.expected_match is not True or len(decision.tokens or ()) != 1:
                    raise ValueError(
                        "revision requires one occurrence or explicit projection exclusion"
                    )
                token = decision.tokens[0]
                if (token.start, token.end, token.text) != (
                    original.start,
                    original.end,
                    original.text,
                ) or token.pos not in LEXICAL_UPOS:
                    raise ValueError("revision must preserve the original lexical occurrence span")
                row = EvidenceOccurrence.model_validate(
                    {
                        **original.model_dump(mode="json", exclude_computed_fields=True),
                        **token.model_dump(mode="json"),
                    }
                )
                action = "retained" if row == original else "replaced"
                if row.sense_id is None:
                    blockers[item_id] = "sense_unresolved"
        else:
            blockers[item_id] = outcome.status
        replacements[key] = row
        changes.append(
            MachineOccurrenceChange(
                occurrence_sha256=key,
                item_id=item_id,
                result_sha256=result.result_sha256,
                action=action,
                projected_occurrence_sha256=None if row is None else _sha(row),
                reason=reason,
            )
        )
    projected = tuple(
        replacement
        for original in plan.original.occurrences
        if (replacement := replacements.get(_sha(original), original)) is not None
    )
    measurement = measure_form_evidence(plan.original.context, projected)
    return projected, tuple(changes), tuple(excluded), blockers, measurement


class MachineObservationRevision(NativeContract):
    schema_version: Literal["machine-observation-revision-1"] = "machine-observation-revision-1"
    plan: MachineObservationRevisionPlan
    qualification: MachineQualificationResult
    occurrences: tuple[EvidenceOccurrence, ...] = Field(max_length=100000)
    changes: tuple[MachineOccurrenceChange, ...] = Field(min_length=1, max_length=5000)
    excluded_occurrence_sha256s: tuple[Sha256, ...] = Field(max_length=5000)
    blockers: dict[Identifier, Identifier] = Field(max_length=5000)
    measurement: FormEvidenceReport
    denominator_policy: Literal["original-aligned-lexical-token-denominator-1"] = (
        "original-aligned-lexical-token-denominator-1"
    )
    analysis_origin: Literal["machine-review-projection-not-model-output"] = (
        "machine-review-projection-not-model-output"
    )
    origin: Literal["machine"] = "machine"
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def replay_projection(self):
        expected = _project(self.plan, self.qualification)
        if expected != (
            self.occurrences,
            self.changes,
            self.excluded_occurrence_sha256s,
            self.blockers,
            self.measurement,
        ):
            raise ValueError("machine observation projection replay mismatch")
        return self

    @computed_field
    @property
    def revision_sha256(self) -> str:
        return _sha(self)


def apply_machine_observation_revision(
    plan: MachineObservationRevisionPlan, qualification: MachineQualificationResult
) -> MachineObservationRevision:
    """Apply only replayed agreement; recheck supplemental bytes before publication."""
    plan = MachineObservationRevisionPlan.model_validate(
        plan.model_dump(mode="json", exclude_computed_fields=True)
    )
    extras = _load_excerpts(plan.supplemental_sources, plan.original.language)
    expected = _packet(
        plan.original,
        plan.original_sha256,
        plan.revision_id,
        plan.occurrence_sha256s,
        plan.packet.profile_sha256,
        plan.packet.rubric_sha256,
        extras,
    )
    if expected != plan.packet:
        raise ValueError("observation revision supplemental source changed")
    qualification = replay_machine_result(qualification)
    occurrences, changes, excluded, blockers, measurement = _project(plan, qualification)
    return MachineObservationRevision(
        plan=plan,
        qualification=qualification,
        occurrences=occurrences,
        changes=changes,
        excluded_occurrence_sha256s=excluded,
        blockers=blockers,
        measurement=measurement,
    )


__all__ = [
    "MachineObservationRevisionPlan",
    "MachineObservationRevision",
    "MachineOccurrenceChange",
    "build_machine_observation_revision",
    "apply_machine_observation_revision",
]
