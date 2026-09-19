"""Replayable review histories and source-bound drafts across machine rounds."""

from collections import Counter, defaultdict
from html import escape
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, model_validator

from multilang.domain.language_profiles import Identifier, LanguageProfile, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256, normalize_identity_text
from multilang.services.qualification_machine import MachineQualificationResult
from multilang.services.qualification_machine_draft import (
    MachineDraftIssue,
    MachineFormMapping,
    MachineLexicalMapping,
    build_machine_vocabulary_draft,
    replay_machine_result,
)
from multilang.services.qualification_machine_followup import (
    MachineFollowupPlan,
    build_machine_followup,
    build_machine_followup_from_previous,
    validate_machine_followup,
)
from multilang.services.vocabulary_review import VocabularyReview


class MachineCampaignRound(NativeContract):
    plan: MachineFollowupPlan
    qualifications: tuple[MachineQualificationResult, ...] = Field(min_length=1, max_length=100)


class MachineCampaignEntry(NativeContract):
    item_id: Identifier
    kind: Literal["lexical", "form", "case"]
    item_sha256: Sha256
    original_item_sha256: Sha256
    source_result_sha256: Sha256
    source_round_id: Identifier
    status: Literal[
        "machine_agreement", "machine_rejected", "blocked_uncertainty", "blocked_disagreement"
    ]
    reason_codes: tuple[Identifier, ...]


class MachineCampaignChange(NativeContract):
    item_id: Identifier
    round_id: Identifier
    previous_result_sha256: Sha256
    result_sha256: Sha256
    before_status: str
    after_status: str
    removed_reason_codes: tuple[Identifier, ...]
    added_reason_codes: tuple[Identifier, ...]


def _entry(item, outcome, result_sha, round_id, original_sha):
    return MachineCampaignEntry(
        item_id=item.item_id,
        kind=item.kind,
        item_sha256=item.item_sha256,
        original_item_sha256=original_sha,
        source_result_sha256=result_sha,
        source_round_id=round_id,
        status=outcome.status,
        reason_codes=outcome.reason_codes,
    )


def _project(base, rounds):
    if (
        len(base.packet.items)
        + sum(len(result.packet.items) for row in rounds for result in row.qualifications)
        > 20000
    ):
        raise ValueError("machine campaign item history limit exceeded")
    base = replay_machine_result(base)
    results = {base.result_sha256: base}
    outcomes = {row.item_id: row for row in base.decisions}
    entries = {
        item.item_id: _entry(
            item, outcomes[item.item_id], base.result_sha256, "initial", item.item_sha256
        )
        for item in base.packet.items
    }
    contexts = {base.proposal.request.actor.context_id, base.judgment.request.actor.context_id}
    round_ids, changes = {"initial"}, []
    for row in rounds:
        plan = row.plan
        if plan.round_id in round_ids:
            raise ValueError("duplicate machine campaign round")
        parent = results.get(plan.base_result_sha256)
        if parent is None:
            raise ValueError("machine followup parent is not in campaign history")
        validate_machine_followup(parent, plan)
        expected = {item.item_id: item for item in plan.enrichment.packet.items}
        for item_id in expected:
            if (
                item_id not in entries
                or entries[item_id].source_result_sha256 != parent.result_sha256
            ):
                raise ValueError("stale machine followup cannot replace a newer decision")
        seen, next_contexts = set(), set()
        for result in row.qualifications:
            result = replay_machine_result(result)
            if result.result_sha256 in results:
                raise ValueError("duplicate machine result in campaign")
            packet = result.packet
            if (packet.language, packet.profile_sha256, packet.rubric_sha256, packet.split) != (
                plan.language,
                plan.profile_sha256,
                plan.rubric_sha256,
                plan.split,
            ):
                raise ValueError("machine followup packet scope changed")
            new_contexts = {
                result.proposal.request.actor.context_id,
                result.judgment.request.actor.context_id,
            }
            if new_contexts & (contexts | next_contexts):
                raise ValueError("machine followup requires fresh execution contexts")
            next_contexts.update(new_contexts)
            decisions = {decision.item_id: decision for decision in result.decisions}
            for item in packet.items:
                if item.item_id in seen:
                    raise ValueError("duplicate machine followup item coverage")
                if expected.get(item.item_id) != item:
                    raise ValueError("machine followup item differs from enriched packet")
                seen.add(item.item_id)
                prior = entries[item.item_id]
                outcome = decisions[item.item_id]
                entries[item.item_id] = _entry(
                    item, outcome, result.result_sha256, plan.round_id, prior.original_item_sha256
                )
                changes.append(
                    MachineCampaignChange(
                        item_id=item.item_id,
                        round_id=plan.round_id,
                        previous_result_sha256=prior.source_result_sha256,
                        result_sha256=result.result_sha256,
                        before_status=prior.status,
                        after_status=outcome.status,
                        removed_reason_codes=tuple(
                            sorted(set(prior.reason_codes) - set(outcome.reason_codes))
                        ),
                        added_reason_codes=tuple(
                            sorted(set(outcome.reason_codes) - set(prior.reason_codes))
                        ),
                    )
                )
            results[result.result_sha256] = result
        if seen != set(expected):
            raise ValueError("machine followup result coverage is incomplete")
        round_ids.add(plan.round_id)
        contexts.update(next_contexts)
    return tuple(entries.values()), tuple(changes)


class MachineCampaign(NativeContract):
    schema_version: Literal[1] = 1
    campaign_id: Identifier
    base_result: MachineQualificationResult
    rounds: tuple[MachineCampaignRound, ...] = Field(default=(), max_length=25)
    entries: tuple[MachineCampaignEntry, ...] = Field(min_length=1, max_length=5000)
    changes: tuple[MachineCampaignChange, ...] = Field(default=(), max_length=20000)
    origin: Literal["machine"] = "machine"
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def checked_projection(self):
        if (self.entries, self.changes) != _project(self.base_result, self.rounds):
            raise ValueError("machine campaign effective projection drift")
        return self

    @computed_field
    @property
    def campaign_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def build_machine_campaign(base_result, *, campaign_id, rounds=()) -> MachineCampaign:
    base_result = replay_machine_result(base_result)
    rounds = tuple(MachineCampaignRound.model_validate(row) for row in rounds)
    entries, changes = _project(base_result, rounds)
    return MachineCampaign(
        campaign_id=campaign_id,
        base_result=base_result,
        rounds=rounds,
        entries=entries,
        changes=changes,
    )


def append_machine_round(campaign, plan, qualifications) -> MachineCampaign:
    campaign = MachineCampaign.model_validate(campaign.model_dump(mode="json"))
    row = MachineCampaignRound(plan=plan, qualifications=tuple(qualifications))
    return build_machine_campaign(
        campaign.base_result, campaign_id=campaign.campaign_id, rounds=(*campaign.rounds, row)
    )


def prepare_campaign_followup(
    campaign: MachineCampaign,
    *,
    parent_result_sha256: str,
    pipeline: Path,
    manifest_sha256: str,
    round_id: str,
) -> MachineFollowupPlan:
    """Prepare current pending items with the same verified evidence and full ancestry."""
    campaign = MachineCampaign.model_validate(campaign.model_dump(mode="json"))
    if round_id in {"initial", *(row.plan.round_id for row in campaign.rounds)}:
        raise ValueError("duplicate machine campaign round")
    results = {campaign.base_result.result_sha256: campaign.base_result}
    producers = {}
    for row in campaign.rounds:
        for result in row.qualifications:
            results[result.result_sha256] = result
            producers[result.result_sha256] = row.plan
    parent = results.get(parent_result_sha256)
    if parent is None:
        raise ValueError("machine followup parent is not in campaign history")
    pending = {
        row.item_id
        for row in parent.decisions
        if row.status in {"blocked_uncertainty", "blocked_disagreement"}
    }
    if any(
        row.source_result_sha256 != parent_result_sha256
        for row in campaign.entries
        if row.item_id in pending
    ):
        raise ValueError("stale machine followup cannot replace a newer decision")
    ancestry = []
    cursor = parent_result_sha256
    while cursor in producers:
        plan = producers[cursor]
        ancestor = results[plan.base_result_sha256]
        ancestry.append((ancestor, plan))
        cursor = ancestor.result_sha256
    args = dict(pipeline=pipeline, manifest_sha256=manifest_sha256, round_id=round_id)
    if ancestry:
        return build_machine_followup_from_previous(
            parent, history=tuple(reversed(ancestry)), **args
        )
    return build_machine_followup(parent, **args)


class MachineCampaignDraft(NativeContract):
    campaign_sha256: Sha256
    preparation_sha256: Sha256
    source_draft_sha256s: dict[Sha256, Sha256]
    effective_entries: tuple[MachineCampaignEntry, ...]
    proposed_lexical_mappings: tuple[MachineLexicalMapping, ...]
    conflicting_lexical_mappings: tuple[MachineLexicalMapping, ...] = ()
    proposed_form_mappings: tuple[MachineFormMapping, ...]
    pending_native_review: VocabularyReview
    uncertainty_queue: tuple[MachineDraftIssue, ...]
    origin: Literal["machine"] = "machine"
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def draft_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def build_campaign_vocabulary_draft(
    campaign: MachineCampaign,
    *,
    preparation_dir: Path,
    profile: LanguageProfile,
    source_id: str,
    source_version: str,
) -> MachineCampaignDraft:
    campaign = MachineCampaign.model_validate(campaign.model_dump(mode="json"))
    results = {campaign.base_result.result_sha256: campaign.base_result}
    for row in campaign.rounds:
        results.update({result.result_sha256: result for result in row.qualifications})
    selected = defaultdict(set)
    for entry in campaign.entries:
        selected[entry.source_result_sha256].add(entry.item_id)
    lexical, forms, issues, senses, observed, source_hashes = {}, {}, [], {}, {}, {}
    preparation_sha = None
    for digest, item_ids in selected.items():
        result = results[digest]
        draft = build_machine_vocabulary_draft(
            preparation_dir=preparation_dir,
            qualification=result,
            profile=profile,
            source_id=source_id,
            source_version=source_version,
        )
        if preparation_sha is not None and preparation_sha != draft.preparation_sha256:
            raise ValueError("machine campaign preparation changed between round reads")
        preparation_sha = draft.preparation_sha256
        source_hashes[digest] = draft.draft_sha256
        lexical.update(
            {row.item_id: row for row in draft.proposed_lexical_mappings if row.item_id in item_ids}
        )
        forms.update(
            {
                row.item.item_id: row
                for row in draft.proposed_form_mappings
                if row.item.item_id in item_ids
            }
        )
        issues.extend(row for row in draft.uncertainty_queue if row.item_id in item_ids)
        candidate_ids = {
            item.candidate_id
            for item in result.packet.items
            if item.item_id in item_ids and item.kind == "lexical"
        }
        for row in draft.pending_native_review.senses:
            if row.candidate_id in candidate_ids:
                if row.candidate_id in senses and senses[row.candidate_id] != row:
                    raise ValueError("conflicting current machine candidate decisions")
                senses[row.candidate_id] = row
        observed.update(
            {
                row.decision_id: row
                for row in draft.pending_native_review.forms
                if row.decision_id in item_ids
            }
        )
    identities = defaultdict(list)
    for mapping in lexical.values():
        decision = mapping.decision
        identities[
            (
                normalize_identity_text(decision.proposed_lemma),
                decision.proposed_pos,
                decision.proposed_sense_id,
            )
        ].append(mapping)
    conflicts = {}
    for group in identities.values():
        if len({(row.decision.proposed_lemma, row.decision.proposed_gloss) for row in group}) > 1:
            for mapping in group:
                conflicts[mapping.item_id] = lexical.pop(mapping.item_id)
                issues.append(
                    MachineDraftIssue(
                        item_id=mapping.item_id, reason="conflicting_machine_lexical_identity"
                    )
                )
    return MachineCampaignDraft(
        campaign_sha256=campaign.campaign_sha256,
        preparation_sha256=preparation_sha,
        source_draft_sha256s=source_hashes,
        effective_entries=campaign.entries,
        proposed_lexical_mappings=tuple(lexical[k] for k in sorted(lexical)),
        conflicting_lexical_mappings=tuple(conflicts[k] for k in sorted(conflicts)),
        proposed_form_mappings=tuple(forms[k] for k in sorted(forms)),
        uncertainty_queue=tuple(sorted(issues, key=lambda row: (row.item_id, row.reason))),
        pending_native_review=VocabularyReview(
            preparation_sha256=preparation_sha,
            language=profile.language,
            source_id=source_id,
            source_version=source_version,
            senses=tuple(senses[k] for k in sorted(senses)),
            forms=tuple(observed[k] for k in sorted(observed)),
        ),
    )


def render_machine_campaign(campaign: MachineCampaign) -> str:
    campaign = MachineCampaign.model_validate(campaign.model_dump(mode="json"))
    counts = Counter(entry.status for entry in campaign.entries)
    parts = [
        '<!doctype html><html lang="pt"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; base-uri 'none'; form-action 'none'\">",
        "<title>Histórico de revisão por IA</title><body><h1>Histórico de revisão por IA</h1>",
        "<p>" + escape(campaign.campaign_id) + "</p>",
        "<p>Rascunho de máquina. Acordo entre avaliações não é aprovação de produção.</p><ul>",
    ]
    parts.extend(
        "<li>" + escape(status) + ": " + str(count) + "</li>"
        for status, count in sorted(counts.items())
    )
    parts.append("</ul><h2>Decisões atuais</h2>")
    for entry in campaign.entries:
        parts.append(
            "<details><summary>"
            + escape(entry.item_id)
            + " — "
            + escape(entry.status)
            + "</summary><p>Rodada: "
            + escape(entry.source_round_id)
            + "</p><p>"
            + escape(", ".join(entry.reason_codes))
            + "</p><p>Resultado: "
            + escape(entry.source_result_sha256)
            + "</p></details>"
        )
    parts.append("<h2>Alterações entre rodadas</h2><ul>")
    for change in campaign.changes:
        parts.append(
            "<li>"
            + escape(change.item_id)
            + ": "
            + escape(change.before_status)
            + " → "
            + escape(change.after_status)
            + "; motivos retirados: "
            + escape(", ".join(change.removed_reason_codes))
            + "; motivos atuais novos: "
            + escape(", ".join(change.added_reason_codes))
            + "</li>"
        )
    return "".join(parts) + "</ul></body></html>"
