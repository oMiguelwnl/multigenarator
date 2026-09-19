"""Target current machine decisions explicitly, preserving v1 reviews and source files."""

from collections import defaultdict
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256, normalize_identity_text
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact
from multilang.services.qualification_machine_sources import (
    VerifiedReviewExcerpt,
    load_verified_review_excerpt,
)
from multilang.services.qualification_review import ReviewPacket


class MachineRevisionSelection(NativeContract):
    item_id: Identifier
    purpose: Literal["resolve_pending", "resolve_identity_conflict", "complete_importance"]


class MachineRevisionSupplement(NativeContract):
    reference: VerifiedReviewExcerpt
    item_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=5000)

    @model_validator(mode="after")
    def unique_targets(self):
        if len(set(self.item_ids)) != len(self.item_ids):
            raise ValueError("duplicate supplement target")
        return self


class MachineRevisionParent(NativeContract):
    item_id: Identifier
    item_sha256: Sha256
    result_sha256: Sha256
    status: Literal[
        "machine_agreement", "machine_rejected", "blocked_uncertainty", "blocked_disagreement"
    ]
    reason_codes: tuple[Identifier, ...]


class MachineRevisionPlan(NativeContract):
    schema_version: Literal["machine-review-revision-1"] = "machine-review-revision-1"
    round_id: Identifier
    root_result_sha256: Sha256
    parent_state_sha256: Sha256
    language: SupportedLanguage
    profile_sha256: Sha256
    rubric_sha256: Sha256
    split: Literal["pilot", "calibration", "evaluation"]
    selections: tuple[MachineRevisionSelection, ...] = Field(min_length=1, max_length=5000)
    parents: tuple[MachineRevisionParent, ...] = Field(min_length=1, max_length=5000)
    supplements: tuple[MachineRevisionSupplement, ...] = Field(default=(), max_length=128)
    packet: ReviewPacket
    origin: Literal["machine"] = "machine"
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def coherent_selection(self):
        ids = tuple(row.item_id for row in self.selections)
        if len(set(ids)) != len(ids) or ids != tuple(row.item_id for row in self.parents):
            raise ValueError("revision parent selection mismatch")
        if ids != tuple(row.item_id for row in self.packet.items):
            raise ValueError("revision packet item selection mismatch")
        if (self.language, self.profile_sha256, self.rubric_sha256, self.split) != (
            self.packet.language,
            self.packet.profile_sha256,
            self.packet.rubric_sha256,
            self.packet.split,
        ):
            raise ValueError("revision packet scope mismatch")
        if any(set(row.item_ids) - set(ids) for row in self.supplements):
            raise ValueError("supplement target outside revision selection")
        return self

    @computed_field
    @property
    def revision_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def machine_revision_state_sha256(root_result_sha256, entries):
    """Bind effective decisions and their reviewed sources, independent of display names."""
    return canonical_sha256(
        {
            "root_result_sha256": root_result_sha256,
            "entries": [
                row.model_dump(mode="json") for row in sorted(entries, key=lambda r: r.item_id)
            ],
        }
    )


def _effective(entries, results):
    indexes = {}
    for digest, result in results.items():
        indexes[digest] = (
            {row.item_id: row for row in result.packet.items},
            {row.item_id: row for row in result.decisions},
        )
    items, outcomes = {}, {}
    for entry in entries:
        source_items, source_outcomes = indexes[entry.source_result_sha256]
        items[entry.item_id] = source_items[entry.item_id]
        outcomes[entry.item_id] = source_outcomes[entry.item_id]
    return items, outcomes


def _conflicts(outcomes):
    groups = defaultdict(list)
    for outcome in outcomes.values():
        decision = outcome.decision
        if (
            outcome.status == "machine_agreement"
            and decision is not None
            and decision.kind == "lexical"
        ):
            groups[
                (
                    normalize_identity_text(decision.proposed_lemma),
                    decision.proposed_pos,
                    decision.proposed_sense_id,
                )
            ].append(decision)
    by_item = {}
    for group in groups.values():
        if len({(row.proposed_lemma, row.proposed_gloss) for row in group}) > 1:
            ids = frozenset(row.item_id for row in group)
            by_item.update({item_id: ids for item_id in ids})
    return by_item


def _make_plan(root_sha, entries, results, *, round_id, selections, supplements):
    selections = tuple(
        sorted(
            (MachineRevisionSelection.model_validate(row) for row in selections),
            key=lambda r: r.item_id,
        )
    )
    if not 1 <= len(selections) <= 5000 or len({row.item_id for row in selections}) != len(
        selections
    ):
        raise ValueError("revision requires a bounded unique selection")
    supplements = tuple(MachineRevisionSupplement.model_validate(row) for row in supplements)
    if len(supplements) > 128:
        raise ValueError("revision supplement limit exceeded")
    selected = {row.item_id for row in selections}
    effective = {row.item_id: row for row in entries}
    if selected - effective.keys():
        raise ValueError("revision item is not in current campaign")
    items, outcomes = _effective(entries, results)
    conflict_groups = _conflicts(outcomes)
    parents, revised = [], []
    root_packet = results[root_sha].packet
    extra_sources = defaultdict(list)
    for supplement in supplements:
        if set(supplement.item_ids) - selected:
            raise ValueError("supplement target outside revision selection")
        source = load_verified_review_excerpt(supplement.reference, language=root_packet.language)
        for item_id in supplement.item_ids:
            extra_sources[item_id].append(source)
    for selection in selections:
        item_id, purpose = selection.item_id, selection.purpose
        item, outcome, entry = items[item_id], outcomes[item_id], effective[item_id]
        if purpose == "resolve_pending":
            if outcome.status not in {"blocked_uncertainty", "blocked_disagreement"}:
                raise ValueError("resolve_pending purpose requires a pending decision")
        elif purpose == "complete_importance":
            if item.kind != "form" or outcome.status != "machine_agreement":
                raise ValueError("complete_importance purpose requires a current agreed form")
        elif item_id not in conflict_groups:
            raise ValueError("resolve_identity_conflict purpose requires a current conflict")
        else:
            group = conflict_groups[item_id]
            targeted = {
                row.item_id for row in selections if row.purpose == "resolve_identity_conflict"
            }
            if not group <= targeted:
                raise ValueError("complete identity conflict coverage is required")
            for sibling in sorted(group - {item_id}):
                extra_sources[item_id].extend(items[sibling].sources)
        sources, seen = (
            list(item.sources),
            {canonical_sha256(row.model_dump(mode="json")) for row in item.sources},
        )
        for source in extra_sources[item_id]:
            digest = canonical_sha256(source.model_dump(mode="json"))
            if digest not in seen:
                sources.append(source)
                seen.add(digest)
        revised.append(
            type(item).model_validate(
                item.model_dump(mode="json", exclude_computed_fields=True)
                | {"sources": tuple(sources)}
            )
        )
        parents.append(
            MachineRevisionParent(
                item_id=item_id,
                item_sha256=item.item_sha256,
                result_sha256=entry.source_result_sha256,
                status=entry.status,
                reason_codes=entry.reason_codes,
            )
        )
    state_sha = machine_revision_state_sha256(root_sha, entries)
    packet = ReviewPacket(
        packet_id="machine-revision:"
        + canonical_sha256(
            {
                "parent": state_sha,
                "round": round_id,
                "selection": [row.model_dump(mode="json") for row in selections],
                "items": [row.item_sha256 for row in revised],
                "supplements": [row.model_dump(mode="json") for row in supplements],
            }
        ),
        language=root_packet.language,
        profile_sha256=root_packet.profile_sha256,
        rubric_sha256=root_packet.rubric_sha256,
        split=root_packet.split,
        items=tuple(revised),
    )
    return MachineRevisionPlan(
        round_id=round_id,
        root_result_sha256=root_sha,
        parent_state_sha256=state_sha,
        language=packet.language,
        profile_sha256=packet.profile_sha256,
        rubric_sha256=packet.rubric_sha256,
        split=packet.split,
        selections=selections,
        parents=tuple(parents),
        supplements=supplements,
        packet=packet,
    )


def validate_machine_revision(root_result_sha256, entries, results, plan):
    """Replay exact current-state/source-file bindings; reference files must remain available."""
    plan = MachineRevisionPlan.model_validate(plan.model_dump(mode="json"))
    if (
        plan.root_result_sha256 != root_result_sha256
        or plan.parent_state_sha256 != machine_revision_state_sha256(root_result_sha256, entries)
    ):
        raise ValueError("stale machine revision parent state")
    replay = _make_plan(
        root_result_sha256,
        entries,
        results,
        round_id=plan.round_id,
        selections=plan.selections,
        supplements=plan.supplements,
    )
    if replay != plan:
        raise ValueError("machine revision item, source or parent binding drift")
    return plan


def build_machine_revision(campaign, *, round_id, selections, supplements=()):
    from multilang.services.qualification_machine_campaign import MachineCampaign

    campaign = MachineCampaign.model_validate(campaign.model_dump(mode="json"))
    if round_id in {"initial", *(row.plan.round_id for row in campaign.rounds)}:
        raise ValueError("duplicate machine revision round")
    root_sha = campaign.base_result.result_sha256
    results = {root_sha: campaign.base_result}
    for row in campaign.rounds:
        results.update({result.result_sha256: result for result in row.qualifications})
    return _make_plan(
        root_sha,
        campaign.entries,
        results,
        round_id=round_id,
        selections=selections,
        supplements=supplements,
    )


def export_machine_revision(plan: MachineRevisionPlan, output: Path):
    """Tasks remain non-citeable review instructions, supplied separately to the agent."""
    plan = MachineRevisionPlan.model_validate(plan.model_dump(mode="json"))
    questions = {
        "resolve_pending": "Resolve the recorded uncertainty against exact source excerpts. Reject an unsupported original analysis explicitly; do not invent a replacement or hide a remaining uncertainty.",
        "resolve_identity_conflict": "Review the whole shared identity across these source records. Propose one consistent gloss when they are the same sense, or source-supported distinct sense keys. Preserve construction differences as evidence, not an invented extra sense.",
        "complete_importance": "Reassess this form with the supplied evidence and the declared rubric. Justify each rating with exact citations; omit unavailable learner, curriculum or pronunciation evidence. Do not derive include from the scoring threshold.",
    }
    tasks = {
        "evidence_role": "review_instructions",
        "revision_sha256": plan.revision_sha256,
        "tasks": [
            dict(item_id=row.item_id, purpose=row.purpose, question=questions[row.purpose])
            for row in plan.selections
        ],
    }
    return persist_artifact(
        output,
        kind="machine-targeted-revision",
        binding=plan.revision_sha256,
        files={
            "plan.json": json_bytes(plan),
            "packet.json": json_bytes(plan.packet),
            "tasks.json": json_bytes(tasks),
        },
    )
