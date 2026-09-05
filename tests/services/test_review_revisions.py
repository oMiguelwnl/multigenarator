"""Pure append-only review revision service tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from importlib import import_module, util
from types import ModuleType

import pytest


def _apis() -> tuple[ModuleType, ModuleType]:
    assert util.find_spec("multilang.domain.review") is not None
    assert util.find_spec("multilang.services.review_revisions") is not None
    return (
        import_module("multilang.domain.review"),
        import_module("multilang.services.review_revisions"),
    )


def _new_service() -> tuple[ModuleType, ModuleType, object]:
    domain, service_api = _apis()
    return domain, service_api, service_api.ReviewRevisionService()


def _source_hash(domain: ModuleType, value: str = "1") -> tuple[object, ...]:
    return (domain.HashBinding(name="source", sha256=value * 64),)


def _candidate(
    svc: object,
    domain: ModuleType,
    *,
    field: object | None = None,
    value: str = "private value",
    request_id: str = "candidate-1",
    expected_base_revision_id: str | None = None,
    expected_pointer_version: int = 0,
    dependency_hashes: tuple[object, ...] = (),
    action: str = "validated_generation_result",
) -> object:
    return svc.create_candidate(
        actor_id="generator-1",
        request_id=request_id,
        action=action,
        job_id="job-1",
        item_id="item-1",
        field=field or domain.ReviewField.DEFINITION,
        payload={"kind": "audio" if field in {domain.ReviewField.WORD_AUDIO, domain.ReviewField.SENTENCE_AUDIO} else "text", "value": value},
        source_hashes=_source_hash(domain),
        dependency_hashes=dependency_hashes,
        expected_base_revision_id=expected_base_revision_id,
        expected_pointer_version=expected_pointer_version,
    )


def _validator(domain: ModuleType, *, result: str = "passed") -> object:
    return domain.ReviewValidatorOutcome(
        validator_id="grammar-validator",
        validator_version="1",
        result=result,
        reason_code="none" if result == "passed" else "deterministic-validator-failed",
        output_sha256="4" * 64,
        executed_at="2026-08-30T12:01:00Z",
    )


def _ai_pass(domain: ModuleType, *, index: int) -> object:
    return domain.AIReviewPass(
        pass_id=f"pass-{index}",
        fresh_context_id=f"fresh-{index}",
        provider_id="offline-provider",
        model_id="offline-model",
        route_id="offline-route",
        prompt_sha256="5" * 64,
        output_schema_sha256="6" * 64,
        decision="passed",
        reason_code="none",
        uncertainty_codes=(),
        confidence=0.95,
        started_at="2026-08-30T12:02:00Z",
        completed_at="2026-08-30T12:03:00Z",
    )


def _ai_evidence(
    domain: ModuleType,
    revision: object,
    *,
    source_kind: str = "production",
) -> object:
    return domain.AILinguisticReviewEvidence(
        evidence_id=f"evidence-{revision.revision_id}",
        actor_type="ai_model",
        is_human=False,
        policy_id="multilang-ai-linguistic-review-v1",
        policy_sha256="7" * 64,
        provider_id="offline-provider",
        model_id="offline-model",
        route_id="offline-route",
        prompt_id="field-review-prompt",
        prompt_sha256="8" * 64,
        output_schema_id="field-review-schema",
        output_schema_sha256="9" * 64,
        source_sha256="b" * 64,
        candidate_sha256=revision.content_hash,
        analyzer_sha256="c" * 64,
        curriculum_sha256="d" * 64,
        media_sha256="e" * 64,
        validator_outcomes=(_validator(domain),),
        passes=(_ai_pass(domain, index=1), _ai_pass(domain, index=2)),
        required_pass_count=2,
        status="ai_review_passed",
        reason_code="none",
        uncertainty_codes=(),
        source_kind=source_kind,
        orchestrated_at="2026-08-30T12:04:00Z",
    )


def _audio_evidence(
    domain: ModuleType,
    revision: object,
    *,
    final_path: str = "word_audio/item-1/rev/audio.mp3",
    request_sha256: str = "8" * 64,
    artifact_sha256: str = "9" * 64,
) -> object:
    return domain.AudioReviewEvidence(
        evidence_id=f"audio-evidence-{revision.revision_id}",
        status="ai_acoustic_review_passed",
        policy_sha256="7" * 64,
        integrity_sha256="6" * 64,
        request_sha256=request_sha256,
        profile_sha256="5" * 64,
        artifact_sha256=artifact_sha256,
        final_path=final_path,
        revision_content_sha256=revision.content_hash,
        acoustic_review_sha256="4" * 64,
        human_heard_claim=False,
        source_kind="production",
    )


def _approve(
    svc: object,
    domain: ModuleType,
    operation: object,
    *,
    request_id: str = "approve-1",
    evidence: object | None = None,
) -> object:
    revision = operation.revision
    if evidence is None:
        evidence = (
            _audio_evidence(domain, revision)
            if revision.field in {domain.ReviewField.WORD_AUDIO, domain.ReviewField.SENTENCE_AUDIO}
            else _ai_evidence(domain, revision)
        )
    return svc.approve_revision(
        actor_id="review-agent",
        request_id=request_id,
        job_id=revision.job_id,
        item_id=revision.item_id,
        field=revision.field,
        revision_id=revision.revision_id,
        revision_no=revision.revision_no,
        content_hash=revision.content_hash,
        expected_pointer_version=operation.pointer.version,
        evidence=evidence,
    )


def test_list_audit_commit_returns_metadata_after_content_free_event() -> None:
    domain, _service_api, svc = _new_service()
    candidate = _candidate(svc, domain, value="private definition")
    _approve(svc, domain, candidate)
    selector = domain.ReviewListSelector(
        job_id="job-1",
        fields=(domain.ReviewField.DEFINITION,),
        statuses=(domain.ReviewStatus.ACCEPTED,),
        source_types=("grammar",),
        snapshot_sha256="1" * 64,
        policy_sha256="2" * 64,
    )

    result = svc.list_fields(actor_id="auditor-1", request_id="list-1", selector=selector)

    assert result.event.event_id in svc.committed_access_event_ids
    assert result.event.action is domain.ReviewAccessAction.LIST
    assert result.rows == (
        {
            "job_id": "job-1",
            "item_id": "item-1",
            "field": "definition",
            "candidate_revision_id": candidate.revision.revision_id,
            "approved_revision_id": candidate.revision.revision_id,
            "status": "accepted",
            "pointer_version": 2,
        },
    )
    serialized = result.event.model_dump_json() + repr(result.rows)
    assert "private definition" not in serialized
    assert "payload" not in serialized


def test_stable_access_identity_command_hash_replay_and_changed_command_conflict_no_result_on_conflict() -> None:
    domain, service_api, svc = _new_service()
    selector = domain.ReviewListSelector(
        job_id="job-1",
        fields=(domain.ReviewField.DEFINITION,),
        statuses=(domain.ReviewStatus.REVIEW_REQUIRED,),
        source_types=("grammar",),
        snapshot_sha256="1" * 64,
        policy_sha256="2" * 64,
    )
    changed_selector = selector.model_copy(
        update={"statuses": (domain.ReviewStatus.ACCEPTED,)}
    )

    first = svc.list_fields(actor_id="auditor-1", request_id="same", selector=selector)
    replay = svc.list_fields(actor_id="auditor-1", request_id="same", selector=selector)

    assert replay.replayed is True
    assert replay.event.event_id == first.event.event_id
    assert replay.event.stable_identity == first.event.stable_identity
    before = len(svc.committed_access_event_ids)
    with pytest.raises(service_api.ReviewCommandConflict):
        svc.list_fields(
            actor_id="auditor-1",
            request_id="same",
            selector=changed_selector,
        )
    assert len(svc.committed_access_event_ids) == before


def test_concurrent_changed_command_one_winner_no_result_on_conflict() -> None:
    domain, service_api, svc = _new_service()
    selectors = (
        domain.ReviewListSelector(
            job_id="job-1",
            fields=(domain.ReviewField.DEFINITION,),
            statuses=(domain.ReviewStatus.REVIEW_REQUIRED,),
            source_types=("grammar",),
            snapshot_sha256="1" * 64,
            policy_sha256="2" * 64,
        ),
        domain.ReviewListSelector(
            job_id="job-1",
            fields=(domain.ReviewField.TRANSLATION,),
            statuses=(domain.ReviewStatus.REVIEW_REQUIRED,),
            source_types=("grammar",),
            snapshot_sha256="1" * 64,
            policy_sha256="2" * 64,
        ),
    )

    def run(selector: object) -> str:
        try:
            return svc.list_fields(
                actor_id="auditor-1",
                request_id="race",
                selector=selector,
            ).event.event_id
        except service_api.ReviewCommandConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(run, selectors))

    assert sorted(outcomes).count("conflict") == 1
    assert len(svc.committed_access_event_ids) == 1


def test_inspect_audit_and_private_display_audit_before_value() -> None:
    domain, _service_api, svc = _new_service()
    candidate = _candidate(svc, domain, value="private excerpt secret")
    inspect_selector = domain.ReviewInspectSelector(
        job_id="job-1",
        item_id="item-1",
        field=domain.ReviewField.DEFINITION,
        revision_id=candidate.revision.revision_id,
        pointer_version=candidate.pointer.version,
        policy_sha256="2" * 64,
    )

    inspected = svc.inspect_field(
        actor_id="auditor-1",
        request_id="inspect-1",
        selector=inspect_selector,
    )

    assert inspected.event.event_id in svc.committed_access_event_ids
    assert inspected.metadata["revision_id"] == candidate.revision.revision_id
    assert "private excerpt secret" not in repr(inspected.metadata)

    display_selector = domain.PrivateDisplaySelector(
        job_id="job-1",
        item_id="item-1",
        field=domain.ReviewField.DEFINITION,
        revision_id=candidate.revision.revision_id,
        pointer_version=candidate.pointer.version,
        policy_sha256="2" * 64,
        local_acknowledgement=True,
    )
    displayed = svc.private_display_revision(
        actor_id="local-reviewer",
        request_id="display-1",
        selector=display_selector,
    )

    assert displayed.released_after_event_id == displayed.event.event_id
    assert displayed.event.event_id in svc.committed_access_event_ids
    assert displayed.value == candidate.revision.payload
    assert "private excerpt secret" not in displayed.event.model_dump_json()


def test_approve_ai_requires_validated_generation_result_and_rejects_synthetic() -> None:
    domain, service_api, svc = _new_service()
    candidate = _candidate(svc, domain, action="validated_generation_result")

    approved = _approve(svc, domain, candidate)

    assert approved.decision.status is domain.ReviewStatus.ACCEPTED
    assert approved.pointer.approved_revision_id == candidate.revision.revision_id
    synthetic = _candidate(
        svc,
        domain,
        value="synthetic candidate",
        request_id="candidate-2",
        expected_base_revision_id=candidate.revision.revision_id,
        expected_pointer_version=approved.pointer.version,
    )
    synthetic_evidence = _ai_evidence(
        domain,
        synthetic.revision,
        source_kind="synthetic",
    )

    with pytest.raises(service_api.ReviewValidationError, match="synthetic"):
        _approve(
            svc,
            domain,
            synthetic,
            request_id="approve-synthetic",
            evidence=synthetic_evidence,
        )


def test_pending_candidate_prior_approval_preserved_for_edit_and_regenerate() -> None:
    domain, _service_api, svc = _new_service()
    first = _candidate(svc, domain, value="approved definition")
    approved = _approve(svc, domain, first)

    edited = _candidate(
        svc,
        domain,
        value="edited pending definition",
        request_id="edit-1",
        expected_base_revision_id=first.revision.revision_id,
        expected_pointer_version=approved.pointer.version,
        action="edit_to_new_candidate",
    )
    regenerated = _candidate(
        svc,
        domain,
        value="regenerated pending definition",
        request_id="regenerate-1",
        expected_base_revision_id=edited.revision.revision_id,
        expected_pointer_version=edited.pointer.version,
        action="regenerate_field",
    )

    assert edited.revision.initial_status is domain.ReviewStatus.REVIEW_REQUIRED
    assert regenerated.revision.initial_status is domain.ReviewStatus.REVIEW_REQUIRED
    assert edited.pointer.approved_revision_id == first.revision.revision_id
    assert regenerated.pointer.approved_revision_id == first.revision.revision_id
    assert svc.revisions[first.revision.revision_id] == first.revision
    assert svc.latest_decision(first.revision.revision_id).status is domain.ReviewStatus.ACCEPTED


def test_bridge_defer_expected_base_are_exact() -> None:
    domain, service_api, svc = _new_service()
    base = _candidate(svc, domain, value="base")

    bridge = svc.record_bridge_decision(
        actor_id="local-reviewer",
        request_id="bridge-1",
        job_id="job-1",
        item_id="item-1",
        proposal_id="proposal-1",
        base_revision_id=base.revision.revision_id,
        expected_base_revision_id=base.revision.revision_id,
        prerequisite_concept_ids=("grammar.topic",),
    )
    deferred = svc.record_defer_decision(
        actor_id="local-reviewer",
        request_id="defer-1",
        job_id="job-1",
        item_id="item-1",
        proposal_id="proposal-1",
        base_revision_id=base.revision.revision_id,
        expected_base_revision_id=base.revision.revision_id,
        reason_code="prerequisite-over-budget",
    )

    assert bridge.event.action is domain.ReviewTransitionAction.BRIDGE
    assert deferred.event.action is domain.ReviewTransitionAction.DEFER
    with pytest.raises(service_api.ReviewCASConflict):
        svc.record_bridge_decision(
            actor_id="local-reviewer",
            request_id="bridge-stale",
            job_id="job-1",
            item_id="item-1",
            proposal_id="proposal-1",
            base_revision_id=base.revision.revision_id,
            expected_base_revision_id="other-revision",
            prerequisite_concept_ids=("grammar.topic",),
        )


def test_sentence_candidate_no_invalidation() -> None:
    domain, _service_api, svc = _new_service()
    sentence = _candidate(svc, domain, field=domain.ReviewField.SENTENCE, value="old sentence")
    sentence_approved = _approve(svc, domain, sentence, request_id="approve-sentence-old")
    dependency = domain.FieldDependencyBinding(
        source_field=domain.ReviewField.SENTENCE,
        source_revision_id=sentence.revision.revision_id,
        source_revision_no=sentence.revision.revision_no,
        source_content_hash=sentence.revision.content_hash,
        relation="translated_from",
    )
    translation = _candidate(
        svc,
        domain,
        field=domain.ReviewField.TRANSLATION,
        value="old translation",
        request_id="translation-old",
        dependency_hashes=(dependency,),
    )
    translation_approved = _approve(svc, domain, translation, request_id="approve-translation")

    new_sentence = _candidate(
        svc,
        domain,
        field=domain.ReviewField.SENTENCE,
        value="new sentence",
        request_id="sentence-new",
        expected_base_revision_id=sentence.revision.revision_id,
        expected_pointer_version=sentence_approved.pointer.version,
    )

    assert new_sentence.stale_decisions == ()
    assert svc.latest_decision(translation.revision.revision_id).status is domain.ReviewStatus.ACCEPTED
    assert translation_approved.pointer.approved_revision_id == translation.revision.revision_id


def test_sentence_approval_invalidates_prior_bound_translation_and_sentence_audio_only_dependency_hash_history() -> None:
    domain, _service_api, svc = _new_service()
    definition = _approve(
        svc,
        domain,
        _candidate(svc, domain, field=domain.ReviewField.DEFINITION, value="definition"),
        request_id="approve-definition",
    )
    word_audio = _approve(
        svc,
        domain,
        _candidate(svc, domain, field=domain.ReviewField.WORD_AUDIO, value="word audio", request_id="word-audio"),
        request_id="approve-word-audio",
    )
    old_sentence = _candidate(svc, domain, field=domain.ReviewField.SENTENCE, value="old sentence", request_id="sentence-old")
    old_sentence_approved = _approve(svc, domain, old_sentence, request_id="approve-sentence-old")
    dependency = domain.FieldDependencyBinding(
        source_field=domain.ReviewField.SENTENCE,
        source_revision_id=old_sentence.revision.revision_id,
        source_revision_no=old_sentence.revision.revision_no,
        source_content_hash=old_sentence.revision.content_hash,
        relation="translated_from",
    )
    translation = _approve(
        svc,
        domain,
        _candidate(
            svc,
            domain,
            field=domain.ReviewField.TRANSLATION,
            value="old translation",
            request_id="translation-old",
            dependency_hashes=(dependency,),
        ),
        request_id="approve-translation",
    )
    sentence_audio = _approve(
        svc,
        domain,
        _candidate(
            svc,
            domain,
            field=domain.ReviewField.SENTENCE_AUDIO,
            value="sentence audio",
            request_id="sentence-audio-old",
            dependency_hashes=(dependency,),
        ),
        request_id="approve-sentence-audio",
    )
    new_sentence = _candidate(
        svc,
        domain,
        field=domain.ReviewField.SENTENCE,
        value="new sentence",
        request_id="sentence-new",
        expected_base_revision_id=old_sentence.revision.revision_id,
        expected_pointer_version=old_sentence_approved.pointer.version,
    )

    approved_new_sentence = _approve(
        svc,
        domain,
        new_sentence,
        request_id="approve-sentence-new",
    )

    stale_fields = tuple(decision.field for decision in approved_new_sentence.stale_decisions)
    assert stale_fields == (domain.ReviewField.TRANSLATION, domain.ReviewField.SENTENCE_AUDIO)
    assert svc.latest_decision(translation.revision.revision_id).status is domain.ReviewStatus.STALE
    assert svc.latest_decision(sentence_audio.revision.revision_id).status is domain.ReviewStatus.STALE
    assert svc.latest_decision(definition.revision.revision_id).status is domain.ReviewStatus.ACCEPTED
    assert svc.latest_decision(word_audio.revision.revision_id).status is domain.ReviewStatus.ACCEPTED
    assert translation.decision.status is domain.ReviewStatus.ACCEPTED
    assert sentence_audio.decision.status is domain.ReviewStatus.ACCEPTED


def test_definition_local_and_word_audio_local() -> None:
    domain, _service_api, svc = _new_service()
    sentence = _approve(
        svc,
        domain,
        _candidate(svc, domain, field=domain.ReviewField.SENTENCE, value="sentence"),
        request_id="approve-sentence",
    )
    translation = _approve(
        svc,
        domain,
        _candidate(svc, domain, field=domain.ReviewField.TRANSLATION, value="translation", request_id="translation"),
        request_id="approve-translation",
    )
    definition = _approve(
        svc,
        domain,
        _candidate(svc, domain, field=domain.ReviewField.DEFINITION, value="definition", request_id="definition"),
        request_id="approve-definition",
    )
    word_audio = _approve(
        svc,
        domain,
        _candidate(svc, domain, field=domain.ReviewField.WORD_AUDIO, value="word audio", request_id="word-audio"),
        request_id="approve-word-audio",
    )

    assert definition.stale_decisions == ()
    assert word_audio.stale_decisions == ()
    assert svc.latest_decision(sentence.revision.revision_id).status is domain.ReviewStatus.ACCEPTED
    assert svc.latest_decision(translation.revision.revision_id).status is domain.ReviewStatus.ACCEPTED


def test_policy_drift_marks_declared_dependents_only_and_preserves_history() -> None:
    domain, _service_api, svc = _new_service()
    definition = _candidate(svc, domain, field=domain.ReviewField.DEFINITION, value="definition")
    definition_approved = _approve(svc, domain, definition)
    bound_dependency = domain.FieldDependencyBinding(
        source_field=domain.ReviewField.DEFINITION,
        source_revision_id=definition.revision.revision_id,
        source_revision_no=definition.revision.revision_no,
        source_content_hash=definition.revision.content_hash,
        relation="policy",
    )
    unbound_dependency = bound_dependency.model_copy(
        update={"source_content_hash": "f" * 64}
    )
    sentence = _approve(
        svc,
        domain,
        _candidate(
            svc,
            domain,
            field=domain.ReviewField.SENTENCE,
            value="bound sentence",
            request_id="sentence-bound",
            dependency_hashes=(bound_dependency,),
        ),
        request_id="approve-bound-sentence",
    )
    translation = _approve(
        svc,
        domain,
        _candidate(
            svc,
            domain,
            field=domain.ReviewField.TRANSLATION,
            value="unbound translation",
            request_id="translation-unbound",
            dependency_hashes=(unbound_dependency,),
        ),
        request_id="approve-unbound-translation",
    )

    drift = svc.mark_declared_dependents_stale(
        actor_id="policy-checker",
        request_id="policy-drift-1",
        job_id="job-1",
        item_id="item-1",
        source_field=domain.ReviewField.DEFINITION,
        source_content_hash=definition.revision.content_hash,
        reason_code="policy-drift",
    )

    assert tuple(decision.revision_id for decision in drift.stale_decisions) == (sentence.revision.revision_id,)
    assert svc.latest_decision(sentence.revision.revision_id).status is domain.ReviewStatus.STALE
    assert svc.latest_decision(translation.revision.revision_id).status is domain.ReviewStatus.ACCEPTED
    assert svc.latest_decision(definition.revision.revision_id).status is domain.ReviewStatus.ACCEPTED
    assert definition_approved.decision in svc.decisions


def test_audio_publication_reservation_finalization_uses_revision_path_and_no_provider_call() -> None:
    domain, _service_api, svc = _new_service()
    audio = _candidate(svc, domain, field=domain.ReviewField.WORD_AUDIO, value="audio pending")
    request_sha256 = "8" * 64

    reserved = svc.reserve_audio_publication(
        actor_id="audio-worker",
        request_id="reserve-1",
        job_id="job-1",
        item_id="item-1",
        field=domain.ReviewField.WORD_AUDIO,
        revision_id=audio.revision.revision_id,
        revision_no=audio.revision.revision_no,
        revision_content_hash=audio.revision.content_hash,
        request_sha256=request_sha256,
        profile_extension="mp3",
        authority_sha256="3" * 64,
        root_prestate_sha256="4" * 64,
    )
    staged = svc.transition_audio_publication(
        actor_id="audio-worker",
        request_id="stage-1",
        reservation_id=reserved.reservation.reservation_id,
        expected_version=reserved.reservation.version,
        status=domain.AudioPublicationStatus.STAGED,
        evidence_sha256="5" * 64,
    )
    published = svc.transition_audio_publication(
        actor_id="audio-worker",
        request_id="publish-1",
        reservation_id=reserved.reservation.reservation_id,
        expected_version=staged.reservation.version,
        status=domain.AudioPublicationStatus.PUBLISHED,
        artifact_sha256="9" * 64,
        evidence_sha256="6" * 64,
    )
    finalized = svc.finalize_audio_publication(
        actor_id="audio-worker",
        request_id="finalize-1",
        reservation_id=reserved.reservation.reservation_id,
        expected_version=published.reservation.version,
        artifact_sha256="9" * 64,
        evidence_sha256="7" * 64,
        expected_pointer_version=audio.pointer.version,
    )

    assert request_sha256 in reserved.reservation.final_path
    assert "9" * 64 not in reserved.reservation.final_path
    assert finalized.pointer.candidate_revision_id == audio.revision.revision_id
    assert finalized.reservation.final_path == reserved.reservation.final_path
    assert svc.provider_call_count == 0
