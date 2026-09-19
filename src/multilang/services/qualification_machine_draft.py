"""Source-bound machine proposals, native pending inputs and a safe local report."""

from __future__ import annotations

import base64
import hashlib
import html
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import computed_field

from multilang.domain.language_profiles import Identifier, LanguageProfile, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine import (
    MachineFormDecision,
    MachineLexicalDecision,
    MachineQualificationResult,
    reconcile_machine_reviews,
)
from multilang.services.qualification_review import FormReviewItem, LexicalReviewItem
from multilang.services.vocabulary_review import (
    ObservedFormDecision,
    SenseDecision,
    VocabularyReview,
    _load_preparation,
)


class MachineLexicalMapping(NativeContract):
    item_id: Identifier
    candidate_id: Identifier
    candidate_sha256: Sha256
    source_record_sha256: Sha256
    original_lemma: str
    original_pos: Identifier
    source_correction_proposed: bool
    decision: MachineLexicalDecision


class MachineFormMapping(NativeContract):
    item: FormReviewItem
    decision: MachineFormDecision
    native_parent_verified: bool


class MachineDraftIssue(NativeContract):
    item_id: Identifier
    reason: Identifier


class MachineVocabularyDraft(NativeContract):
    origin: Literal["machine"] = "machine"
    qualification_sha256: Sha256
    preparation_sha256: Sha256
    proposed_lexical_mappings: tuple[MachineLexicalMapping, ...]
    proposed_form_mappings: tuple[MachineFormMapping, ...]
    pending_native_review: VocabularyReview
    uncertainty_queue: tuple[MachineDraftIssue, ...]
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def draft_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def replay_machine_result(qualification: MachineQualificationResult) -> MachineQualificationResult:
    checked = MachineQualificationResult.model_validate(qualification.model_dump(mode="json"))
    replay = reconcile_machine_reviews(checked.packet, checked.proposal, checked.judgment)
    if replay != checked:
        raise ValueError("machine qualification reconciliation drift")
    return replay


def build_machine_vocabulary_draft(
    *,
    preparation_dir: Path,
    qualification: MachineQualificationResult,
    profile: LanguageProfile,
    source_id: str,
    source_version: str,
) -> MachineVocabularyDraft:
    result = replay_machine_result(qualification)
    packet = result.packet
    profile = LanguageProfile.model_validate(profile.model_dump(mode="json"))
    if packet.language != profile.language or packet.profile_sha256 != canonical_sha256(
        profile.model_dump(mode="json")
    ):
        raise ValueError("machine qualification profile mismatch")
    if source_id not in profile.source_ids:
        raise ValueError("machine qualification source is not declared in profile")
    manifest, candidates, _corpus, _artifacts = _load_preparation(preparation_dir)
    if manifest["language"] != packet.language.value:
        raise ValueError("machine qualification preparation language mismatch")
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("duplicate preparation candidate")
    consensus = {entry.item_id: entry for entry in result.decisions}
    senses, forms, lexical, form_mappings, issues = {}, [], [], [], []
    for item in packet.items:
        outcome = consensus[item.item_id]
        if outcome.status in {"blocked_uncertainty", "blocked_disagreement"}:
            for reason in outcome.reason_codes:
                issues.append(MachineDraftIssue(item_id=item.item_id, reason=reason))
        if not isinstance(item, (LexicalReviewItem, FormReviewItem)):
            continue
        candidate = by_id.get(item.candidate_id)
        if candidate is None and isinstance(item, LexicalReviewItem):
            raise ValueError("machine lexical candidate missing from verified preparation")
        if candidate is not None:
            if (
                canonical_sha256(candidate.model_dump(mode="json")) != item.candidate_sha256
                or candidate.lemma != item.lemma
            ):
                raise ValueError("machine candidate does not match verified preparation")
            if not any(
                (
                    s.source_id == source_id
                    and s.source_sha256
                    in {candidate.source_record_sha256, manifest.get("dictionary_sha256")}
                )
                or (
                    s.source_id == "prepared-dictionary"
                    and s.source_sha256 == manifest.get("dictionary_sha256")
                    and s.record_id in {candidate.candidate_id, candidate.source_record_sha256}
                )
                for s in item.sources
            ):
                raise ValueError("machine candidate source does not match preparation")
        if isinstance(item, LexicalReviewItem):
            if item.candidate_id in senses:
                raise ValueError("duplicate machine lexical candidate mapping")
            senses[item.candidate_id] = SenseDecision(
                candidate_id=item.candidate_id,
                candidate_sha256=item.candidate_sha256,
                source_record_sha256=candidate.source_record_sha256,
                lemma=candidate.lemma,
                pos=candidate.pos,
            )
            if outcome.status == "machine_agreement" and isinstance(
                outcome.decision, MachineLexicalDecision
            ):
                correction = (outcome.decision.proposed_lemma, outcome.decision.proposed_pos) != (
                    candidate.lemma,
                    candidate.pos,
                )
                lexical.append(
                    MachineLexicalMapping(
                        item_id=item.item_id,
                        candidate_id=item.candidate_id,
                        candidate_sha256=item.candidate_sha256,
                        source_record_sha256=candidate.source_record_sha256,
                        original_lemma=candidate.lemma,
                        original_pos=candidate.pos,
                        source_correction_proposed=correction,
                        decision=outcome.decision,
                    )
                )
                if correction:
                    issues.append(
                        MachineDraftIssue(item_id=item.item_id, reason="source_correction_proposed")
                    )
                if candidate.kind != "lexeme":
                    issues.append(
                        MachineDraftIssue(
                            item_id=item.item_id, reason="inflection_is_not_lexical_identity"
                        )
                    )
        else:
            forms.append(
                ObservedFormDecision(decision_id=item.item_id, candidate_id=item.candidate_id)
            )
            if outcome.status == "machine_agreement" and isinstance(
                outcome.decision, MachineFormDecision
            ):
                form_mappings.append(
                    MachineFormMapping(
                        item=item, decision=outcome.decision, native_parent_verified=False
                    )
                )
            issues.append(
                MachineDraftIssue(
                    item_id=item.item_id, reason="exact_native_form_evidence_required"
                )
            )
    return MachineVocabularyDraft(
        qualification_sha256=result.result_sha256,
        preparation_sha256=manifest["preparation_sha256"],
        proposed_lexical_mappings=tuple(lexical),
        proposed_form_mappings=tuple(form_mappings),
        uncertainty_queue=tuple(issues),
        pending_native_review=VocabularyReview(
            preparation_sha256=manifest["preparation_sha256"],
            language=packet.language,
            source_id=source_id,
            source_version=source_version,
            senses=tuple(senses.values()),
            forms=tuple(forms),
        ),
    )


def render_machine_report(qualification: MachineQualificationResult) -> str:
    result = replay_machine_result(qualification)
    rows = []
    labels = {
        "machine_agreement": "Acordo entre avaliações de IA",
        "machine_rejected": "Rejeitado pelas duas avaliações",
        "blocked_uncertainty": "Evidência insuficiente ou decisão pendente",
        "blocked_disagreement": "Divergência entre avaliações",
    }
    items = {item.item_id: item for item in result.packet.items}
    for outcome in result.decisions:
        item = items[outcome.item_id]
        decision = outcome.decision.model_dump(mode="json") if outcome.decision else None
        payload = {
            "status": outcome.status,
            "item": item.model_dump(mode="json"),
            "machine_decision": decision,
            "reasons": outcome.reason_codes,
        }
        title = getattr(item, "lemma", None) or getattr(item, "text", item.item_id)
        if isinstance(item, FormReviewItem):
            title = item.text + " → " + item.lemma
        summary = outcome.decision.reason if outcome.decision else ", ".join(outcome.reason_codes)
        rows.append(
            "<section><h2>"
            + html.escape(title)
            + "</h2><p><strong>"
            + labels[outcome.status]
            + "</strong></p><p>"
            + html.escape(summary)
            + "</p><details><summary>Decisão e evidências verificáveis</summary><pre>"
            + html.escape(json.dumps(payload, ensure_ascii=False, indent=2))
            + "</pre></details></section>"
        )
    style = "body{font:17px/1.6 system-ui,sans-serif;max-width:64rem;margin:2rem auto;padding:0 1rem;color:#17232c;background:#fafbf9}section{border-top:1px solid #cbd5cf;padding:1rem 0}h1,h2{line-height:1.2}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem;background:#edf1ed;padding:1rem}summary{cursor:pointer}code{overflow-wrap:anywhere}"
    style_hash = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    counts = Counter(entry.status for entry in result.decisions)
    totals = (
        "<ul>"
        + "".join(
            "<li>" + labels[status] + ": " + str(count) + "</li>"
            for status, count in sorted(counts.items())
        )
        + "</ul>"
    )
    return (
        '<!doctype html><html lang="pt"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'sha256-"
        + style_hash
        + "'; base-uri 'none'; form-action 'none'\">"
        "<style>" + style + "</style>"
        "<title>Qualificação por IA</title><h1>Revisão de máquina</h1>"
        "<p>Acordo entre avaliações de IA; não representa revisão humana ou qualificação de produção. "
        "Frequência preservada das fontes; notas da IA não são probabilidades calibradas.</p>"
        + totals
        + "<p>Resultado: <code>"
        + html.escape(result.result_sha256)
        + "</code></p>"
        + "".join(rows)
        + "</html>"
    )
