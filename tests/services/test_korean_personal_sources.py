"""Tests for fail-closed Korean personal-source resolution and decisions."""

from __future__ import annotations

from typing import Any

from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
)
from multilang.domain.personal_sources import (
    KoreanPersonalSourceIdentitySelection,
    KoreanPersonalSourceResolutionFailure,
    PersonalSourceDecisionCommand,
    PersonalSourceRow,
)
from multilang.services.korean_personal_sources import KoreanPersonalSourceService


HASH_A = "a" * 64
HASH_B = "b" * 64


def _fingerprint(*, package_version: str = "0.20.4") -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version=package_version,
        model_package_version="0.20.4-model",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def _row(position: int, submitted_form: str) -> PersonalSourceRow:
    return PersonalSourceRow(
        input_position=position,
        line_number=position,
        submitted_form=submitted_form,
        display_form=submitted_form.strip(),
        normalized_duplicate_key=submitted_form.strip().casefold(),
    )


def _identity(
    submitted_form: str,
    *,
    lemma: str,
    part_of_speech: str = "VV",
    sense_id: str = "fixture-sense-1",
    signature: tuple[KoreanSignatureItem, ...] | None = None,
    analyzer_fingerprint: KoreanAnalyzerFingerprint | None = None,
) -> KoreanLexicalIdentity:
    fingerprint = analyzer_fingerprint or _fingerprint()
    return KoreanLexicalIdentity(
        submitted_form=submitted_form,
        canonical_nfc=submitted_form,
        lemma=lemma,
        part_of_speech=part_of_speech,
        sense_id=sense_id,
        register="polite",
        morpheme_signature=signature or (KoreanSignatureItem(form=lemma, pos=part_of_speech),),
        analyzer_fingerprint=fingerprint,
        status="resolved",
    )


def _selection(identity: KoreanLexicalIdentity) -> KoreanPersonalSourceIdentitySelection:
    return KoreanPersonalSourceIdentitySelection(
        language="ko",
        lexical_identity=identity,
        analyzer_fingerprint=identity.analyzer_fingerprint,
        top_two_consensus=True,
        source_consensus=True,
        source_id="fixture-source",
        source_version="fixture-v1",
        source_entry_hash=HASH_A,
        source_selector_hash=HASH_B,
    )


class _Resolver:
    def __init__(self, *results: Any) -> None:
        self._results = list(results)
        self.calls: list[str] = []
        self.fallback_calls: list[str] = []

    def resolve(self, submitted_form: str) -> Any:
        self.calls.append(submitted_form)
        return self._results.pop(0)

    def resolve_with_suffix_fallback(self, submitted_form: str) -> None:
        self.fallback_calls.append(submitted_form)
        raise AssertionError("heuristic fallback must not run")


def test_inflected_form_resolves_to_source_backed_lemma_without_losing_surface() -> None:
    row = _row(1, "먹었어요")
    identity = _identity("먹었어요", lemma="먹다")
    resolver = _Resolver(_selection(identity))

    outcome = KoreanPersonalSourceService(resolver=resolver).resolve_rows((row,))[0]

    assert outcome.resolution_status == "resolved"
    assert outcome.row.submitted_form == "먹었어요"
    assert outcome.lexical_identity == identity
    assert outcome.lexical_identity.lemma == "먹다"
    assert outcome.identity_evidence.source_version == "fixture-v1"
    assert outcome.identity_evidence.source_entry_hash == HASH_A
    assert outcome.identity_evidence.analyzer_fingerprint == _fingerprint()
    assert resolver.calls == ["먹었어요"]


def test_compound_predicate_preserves_complete_derivational_signature() -> None:
    signature = (
        KoreanSignatureItem(form="공부", pos="NNG"),
        KoreanSignatureItem(form="하다", pos="XSV"),
    )
    identity = _identity(
        "공부하다",
        lemma="공부하다",
        part_of_speech="VV",
        signature=signature,
    )
    resolver = _Resolver(_selection(identity))

    outcome = KoreanPersonalSourceService(resolver=resolver).resolve_rows((_row(1, "공부하다"),))[0]

    assert outcome.resolution_status == "resolved"
    assert tuple((item.form, item.pos) for item in outcome.lexical_identity.morpheme_signature) == (
        ("공부", "NNG"),
        ("하다", "XSV"),
    )


def test_distinct_surface_forms_with_same_source_identity_remain_card_bearing() -> None:
    base = _identity("먹다", lemma="먹다")
    inflected = _identity("먹었어요", lemma="먹다")
    resolver = _Resolver(_selection(base), _selection(inflected))

    outcomes = KoreanPersonalSourceService(resolver=resolver).resolve_rows(
        (_row(1, "먹다"), _row(2, "먹었어요"))
    )

    assert [outcome.row.stable_item_key for outcome in outcomes] == ["먹다", "먹었어요"]
    assert [outcome.row.is_card_bearing for outcome in outcomes] == [True, True]
    assert outcomes[0].lexical_identity.lexical_key == outcomes[1].lexical_identity.lexical_key


def test_ambiguity_oov_and_unavailable_analysis_return_needs_review() -> None:
    resolver = _Resolver(
        KoreanPersonalSourceResolutionFailure(status="ambiguous", reason_code="ambiguous_analysis"),
        KoreanPersonalSourceResolutionFailure(status="oov", reason_code="oov"),
        KoreanPersonalSourceResolutionFailure(status="unavailable", reason_code="analysis_unavailable"),
    )

    outcomes = KoreanPersonalSourceService(resolver=resolver).resolve_rows(
        (_row(1, "배"), _row(2, "없는말"), _row(3, "학교"))
    )

    assert [outcome.resolution_status for outcome in outcomes] == [
        "needs_review",
        "needs_review",
        "needs_review",
    ]
    assert [outcome.review_reason_code for outcome in outcomes] == [
        "ambiguous_analysis",
        "oov",
        "analysis_unavailable",
    ]
    assert all(outcome.lexical_identity is None for outcome in outcomes)


def test_missing_sense_pos_signature_or_fingerprint_drift_returns_needs_review() -> None:
    good_identity = _identity("먹다", lemma="먹다")
    invalid_identity_payload = good_identity.model_dump(mode="python", by_alias=True) | {
        "sense_id": "unknown",
    }
    invalid_selection_payload = _selection(good_identity).model_dump(mode="python") | {
        "lexical_identity": invalid_identity_payload,
    }
    drifted_selection_payload = _selection(good_identity).model_dump(mode="python") | {
        "analyzer_fingerprint": _fingerprint(package_version="0.20.5"),
    }
    malformed_signature_payload = good_identity.model_dump(mode="python", by_alias=True) | {
        "morpheme_signature": (),
    }
    malformed_selection_payload = _selection(good_identity).model_dump(mode="python") | {
        "lexical_identity": malformed_signature_payload,
    }
    resolver = _Resolver(
        invalid_selection_payload,
        _selection(good_identity).model_dump(mode="python") | {"source_consensus": False},
        drifted_selection_payload,
        malformed_selection_payload,
    )

    outcomes = KoreanPersonalSourceService(resolver=resolver).resolve_rows(
        (_row(1, "먹다"), _row(2, "먹다"), _row(3, "먹다"), _row(4, "먹다"))
    )

    assert [outcome.resolution_status for outcome in outcomes] == [
        "needs_review",
        "needs_review",
        "needs_review",
        "needs_review",
    ]
    assert [outcome.review_reason_code for outcome in outcomes] == [
        "malformed_identity",
        "non_consensus",
        "fingerprint_drift",
        "malformed_identity",
    ]


def test_no_fallback_is_attempted_for_unresolved_korean_identity() -> None:
    resolver = _Resolver(
        KoreanPersonalSourceResolutionFailure(status="oov", reason_code="oov"),
    )

    outcome = KoreanPersonalSourceService(resolver=resolver).resolve_rows((_row(1, "맛있었어요"),))[0]

    assert outcome.resolution_status == "needs_review"
    assert outcome.review_reason_code == "oov"
    assert resolver.calls == ["맛있었어요"]
    assert resolver.fallback_calls == []


def test_adaptive_proposal_records_excessive_prerequisites_without_strict_claim() -> None:
    identity = _identity("먹었어요", lemma="먹다")
    service = KoreanPersonalSourceService(resolver=_Resolver(_selection(identity)))
    outcome = service.resolve_rows((_row(1, "먹었어요"),))[0]

    proposal = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        known_concept_ids=("lexicon:eat",),
        threshold=1,
    )

    assert proposal.status == "requires_decision"
    assert proposal.evidence.policy == "adaptive"
    assert proposal.evidence.novelty_count == 2
    assert proposal.evidence.reason_codes == ("excessive_prerequisites",)
    assert proposal.available_decisions == ("bridge", "defer")


def test_unresolved_identity_stays_needs_review_before_bridge_or_defer() -> None:
    service = KoreanPersonalSourceService(
        resolver=_Resolver(KoreanPersonalSourceResolutionFailure(status="ambiguous", reason_code="ambiguous_analysis"))
    )
    outcome = service.resolve_rows((_row(1, "배"),))[0]

    proposal = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:pear",),
        prerequisite_concept_ids=("lexicon:pear",),
        known_concept_ids=(),
        threshold=1,
    )

    assert proposal.status == "needs_review"
    assert proposal.available_decisions == ("needs_review",)
    assert proposal.evidence.reason_codes == ("unresolved_identity",)


def test_bridge_requires_explicit_decision_and_does_not_auto_insert() -> None:
    identity = _identity("먹었어요", lemma="먹다")
    service = KoreanPersonalSourceService(resolver=_Resolver(_selection(identity)))
    outcome = service.resolve_rows((_row(1, "먹었어요"),))[0]
    proposal = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        known_concept_ids=("lexicon:eat",),
        threshold=1,
    )

    without_decision = service.project_preparation_order((outcome,), decisions=())
    bridge = service.record_prerequisite_decision(
        proposal,
        PersonalSourceDecisionCommand(
            input_position=1,
            row_item_key="먹었어요",
            expected_proposal_id=proposal.proposal_id,
            expected_policy_hash=proposal.evidence.policy_hash,
            expected_prerequisite_concept_ids=proposal.evidence.prerequisite_concept_ids,
            decision="bridge",
            reviewed_prerequisite_ids=("grammar:past", "grammar:polite"),
            actor_id="local-reviewer",
            reason_code="operator_bridge",
        ),
    )
    with_decision = service.project_preparation_order((outcome,), decisions=(bridge,))

    assert [item.kind for item in without_decision] == ["user_row"]
    assert [item.kind for item in with_decision] == [
        "bridge_reference",
        "bridge_reference",
        "user_row",
    ]
    assert [item.bridge_reference_id for item in with_decision[:2]] == [
        "grammar:past",
        "grammar:polite",
    ]
    assert outcome.row.input_position == 1


def test_defer_preserves_position_while_blocking_current_preparation() -> None:
    identity = _identity("먹었어요", lemma="먹다")
    service = KoreanPersonalSourceService(resolver=_Resolver(_selection(identity)))
    outcome = service.resolve_rows((_row(1, "먹었어요"),))[0]
    proposal = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:eat", "grammar:past"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past"),
        known_concept_ids=("lexicon:eat",),
        threshold=0,
    )

    decision = service.record_prerequisite_decision(
        proposal,
        PersonalSourceDecisionCommand(
            input_position=1,
            row_item_key="먹었어요",
            expected_proposal_id=proposal.proposal_id,
            expected_policy_hash=proposal.evidence.policy_hash,
            expected_prerequisite_concept_ids=proposal.evidence.prerequisite_concept_ids,
            decision="defer",
            actor_id="local-reviewer",
            reason_code="operator_defer",
        ),
    )
    prepared = service.project_preparation_order((outcome,), decisions=(decision,))

    assert decision.decision == "defer"
    assert decision.blocks_current_preparation is True
    assert [(item.kind, item.input_position, item.preparation_status) for item in prepared] == [
        ("user_row", 1, "deferred"),
    ]


def test_exact_retry_is_idempotent_for_bridge_decision() -> None:
    identity = _identity("먹었어요", lemma="먹다")
    service = KoreanPersonalSourceService(resolver=_Resolver(_selection(identity)))
    outcome = service.resolve_rows((_row(1, "먹었어요"),))[0]
    proposal = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:eat", "grammar:past"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past"),
        known_concept_ids=("lexicon:eat",),
        threshold=0,
    )
    command = PersonalSourceDecisionCommand(
        input_position=1,
        row_item_key="먹었어요",
        expected_proposal_id=proposal.proposal_id,
        expected_policy_hash=proposal.evidence.policy_hash,
        expected_prerequisite_concept_ids=proposal.evidence.prerequisite_concept_ids,
        decision="bridge",
        reviewed_prerequisite_ids=("grammar:past",),
        actor_id="local-reviewer",
        reason_code="operator_bridge",
    )

    first = service.record_prerequisite_decision(proposal, command)
    retry = service.record_prerequisite_decision(proposal, command)

    assert retry == first


def test_policy_drift_or_dependency_drift_returns_decision_to_needs_review() -> None:
    identity = _identity("먹었어요", lemma="먹다")
    service = KoreanPersonalSourceService(resolver=_Resolver(_selection(identity)))
    outcome = service.resolve_rows((_row(1, "먹었어요"),))[0]
    original = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:eat", "grammar:past"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past"),
        known_concept_ids=("lexicon:eat",),
        threshold=0,
    )
    policy_drift = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:eat", "grammar:past"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past"),
        known_concept_ids=("lexicon:eat",),
        threshold=2,
    )
    dependency_drift = service.assess_prerequisites(
        outcome,
        observed_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        prerequisite_concept_ids=("lexicon:eat", "grammar:past", "grammar:polite"),
        known_concept_ids=("lexicon:eat",),
        threshold=0,
    )
    command = PersonalSourceDecisionCommand(
        input_position=1,
        row_item_key="먹었어요",
        expected_proposal_id=original.proposal_id,
        expected_policy_hash=original.evidence.policy_hash,
        expected_prerequisite_concept_ids=original.evidence.prerequisite_concept_ids,
        decision="bridge",
        reviewed_prerequisite_ids=("grammar:past",),
        actor_id="local-reviewer",
        reason_code="operator_bridge",
    )

    policy_result = service.record_prerequisite_decision(policy_drift, command)
    dependency_result = service.record_prerequisite_decision(dependency_drift, command)

    assert (policy_result.decision, policy_result.reason_code) == (
        "needs_review",
        "policy_drift",
    )
    assert (dependency_result.decision, dependency_result.reason_code) == (
        "needs_review",
        "dependency_drift",
    )
