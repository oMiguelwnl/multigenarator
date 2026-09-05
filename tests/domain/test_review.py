"""Immutable field revision and review contract tests."""

from __future__ import annotations

from importlib import import_module, util
from types import ModuleType

import pytest
from pydantic import ValidationError


HEX = "a" * 64


def _api() -> ModuleType:
    assert util.find_spec("multilang.domain.review") is not None
    return import_module("multilang.domain.review")


def _hashes(api: ModuleType) -> tuple[object, ...]:
    return (api.HashBinding(name="source", sha256="1" * 64),)


def _generator(api: ModuleType) -> object:
    return api.GeneratorMetadata(
        generator_id="generator-1",
        generator_version="1",
        route_id="offline-fixture",
        request_sha256="2" * 64,
    )


def _creation(api: ModuleType, *, source_kind: str = "generated") -> object:
    return api.RevisionCreationEvidence(
        actor_type="generator",
        actor_id="generator-1",
        source_kind=source_kind,
        created_at="2026-08-30T12:00:00Z",
        evidence_sha256="3" * 64,
    )


def _revision(
    api: ModuleType,
    *,
    field: object | None = None,
    revision_id: str = "rev-1",
    revision_no: int = 1,
    value: str = "learner value",
    source_kind: str = "generated",
    initial_status: object | None = None,
    dependency_hashes: tuple[object, ...] = (),
) -> object:
    payload = {"kind": "text", "value": value}
    return api.FieldRevision(
        job_id="job-1",
        item_id="item-1",
        field=field or api.ReviewField.DEFINITION,
        revision_id=revision_id,
        revision_no=revision_no,
        content_hash=api.canonical_command_sha256(payload),
        payload=payload,
        source_hashes=_hashes(api),
        dependency_hashes=dependency_hashes,
        generator=_generator(api),
        creation_evidence=_creation(api, source_kind=source_kind),
        initial_status=initial_status or api.ReviewStatus.REVIEW_REQUIRED,
        created_at="2026-08-30T12:00:00Z",
    )


def _validator(api: ModuleType, *, result: str = "passed") -> object:
    return api.ReviewValidatorOutcome(
        validator_id="grammar-validator",
        validator_version="1",
        result=result,
        reason_code="none" if result == "passed" else "deterministic-validator-failed",
        output_sha256="4" * 64,
        executed_at="2026-08-30T12:01:00Z",
    )


def _ai_pass(
    api: ModuleType,
    *,
    pass_id: str,
    fresh_context_id: str,
    decision: str = "passed",
) -> object:
    return api.AIReviewPass(
        pass_id=pass_id,
        fresh_context_id=fresh_context_id,
        provider_id="offline-provider",
        model_id="offline-model",
        route_id="offline-route",
        prompt_sha256="5" * 64,
        output_schema_sha256="6" * 64,
        decision=decision,
        reason_code="none" if decision == "passed" else "review-disagreement",
        uncertainty_codes=() if decision != "uncertain" else ("source-insufficient",),
        confidence=0.95 if decision == "passed" else 0.4,
        started_at="2026-08-30T12:02:00Z",
        completed_at="2026-08-30T12:03:00Z",
    )


def _ai_evidence(
    api: ModuleType,
    *,
    candidate_sha256: str,
    required_pass_count: int = 2,
    source_kind: str = "production",
    validator_result: str = "passed",
) -> object:
    passes = tuple(
        _ai_pass(api, pass_id=f"pass-{index}", fresh_context_id=f"fresh-{index}")
        for index in range(1, required_pass_count + 1)
    )
    return api.AILinguisticReviewEvidence(
        evidence_id="evidence-1",
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
        candidate_sha256=candidate_sha256,
        analyzer_sha256="c" * 64,
        curriculum_sha256="d" * 64,
        media_sha256="e" * 64,
        validator_outcomes=(_validator(api, result=validator_result),),
        passes=passes,
        required_pass_count=required_pass_count,
        status="ai_review_passed",
        reason_code="none",
        uncertainty_codes=(),
        source_kind=source_kind,
        orchestrated_at="2026-08-30T12:04:00Z",
    )


def test_revision_contract_is_frozen_and_generated_content_starts_review_required() -> None:
    api = _api()

    revision = _revision(api, value="private definition")

    assert revision.initial_status is api.ReviewStatus.REVIEW_REQUIRED
    assert revision.payload["value"] == "private definition"
    with pytest.raises(ValidationError):
        revision.revision_no = 2

    with pytest.raises(ValidationError, match="generated content cannot start accepted"):
        _revision(api, initial_status=api.ReviewStatus.ACCEPTED)


def test_pointer_model_keeps_candidate_and_approved_separate_versions() -> None:
    api = _api()

    pointer = api.FieldPointer(
        job_id="job-1",
        item_id="item-1",
        field=api.ReviewField.DEFINITION,
        candidate_revision_id="rev-2",
        candidate_content_hash="2" * 64,
        approved_revision_id="rev-1",
        approved_content_hash="1" * 64,
        version=4,
    )

    assert pointer.candidate_identity == ("rev-2", "2" * 64)
    assert pointer.approved_identity == ("rev-1", "1" * 64)
    assert pointer.candidate_identity != pointer.approved_identity
    with pytest.raises(ValidationError):
        pointer.version = 5


def test_stable_access_identity_and_command_sha256_are_content_free() -> None:
    api = _api()
    selector = api.ReviewListSelector(
        job_id="job-1",
        fields=(api.ReviewField.DEFINITION,),
        statuses=(api.ReviewStatus.REVIEW_REQUIRED,),
        source_types=("grammar",),
        snapshot_sha256="1" * 64,
        policy_sha256="2" * 64,
    )
    same_selector = selector.model_copy(
        update={"statuses": (api.ReviewStatus.REVIEW_REQUIRED,)}
    )
    changed_selector = selector.model_copy(
        update={"statuses": (api.ReviewStatus.ACCEPTED,)}
    )

    command_sha256 = api.canonical_command_sha256(selector)
    event = api.ReviewAccessEvent(
        event_id="access-1",
        actor_id="reviewer-1",
        request_id="request-1",
        action=api.ReviewAccessAction.LIST,
        command_sha256=command_sha256,
        result_id="result-1",
        result_hash="3" * 64,
        result_count=2,
        occurred_at="2026-08-30T12:05:00Z",
    )

    assert event.stable_identity == ("reviewer-1", "request-1", api.ReviewAccessAction.LIST)
    assert api.canonical_command_sha256(same_selector) == command_sha256
    assert api.canonical_command_sha256(changed_selector) != command_sha256
    serialized = event.model_dump_json()
    for leaked in ("private definition", "value", "payload", "prompt"):
        assert leaked not in serialized


def test_audio_unique_revision_path_uses_request_profile_extension_not_artifact_hash() -> None:
    api = _api()
    request_sha256 = "4" * 64
    artifact_sha256 = "5" * 64

    final_path = api.derive_audio_final_path(
        field=api.ReviewField.WORD_AUDIO,
        item_id="item-1",
        revision_id="rev-1",
        request_sha256=request_sha256,
        profile_extension="mp3",
    )

    assert final_path == f"word_audio/item-1/rev-1/{request_sha256}.mp3"
    assert artifact_sha256 not in final_path
    assert "artifact" not in final_path


def test_same_hash_distinct_paths_are_allowed_but_no_shared_final_path() -> None:
    api = _api()
    artifact_sha256 = "5" * 64
    reservation_1 = api.AudioPublicationReservation(
        reservation_id="reservation-1",
        job_id="job-1",
        item_id="item-1",
        field=api.ReviewField.WORD_AUDIO,
        revision_id="rev-1",
        revision_no=1,
        revision_content_hash="1" * 64,
        request_sha256="2" * 64,
        profile_extension="mp3",
        final_path="word_audio/item-1/rev-1/" + "2" * 64 + ".mp3",
        authority_sha256="3" * 64,
        root_prestate_sha256="4" * 64,
        version=1,
        reserved_at="2026-08-30T12:06:00Z",
    )
    reservation_2 = reservation_1.model_copy(
        update={
            "reservation_id": "reservation-2",
            "revision_id": "rev-2",
            "revision_no": 2,
            "final_path": "word_audio/item-1/rev-2/" + "2" * 64 + ".mp3",
        }
    )
    transition_1 = api.AudioPublicationTransition(
        transition_id="transition-1",
        reservation_id=reservation_1.reservation_id,
        status=api.AudioPublicationStatus.PUBLISHED,
        from_version=2,
        to_version=3,
        final_path=reservation_1.final_path,
        artifact_sha256=artifact_sha256,
        evidence_sha256="6" * 64,
        reason_code="none",
        occurred_at="2026-08-30T12:07:00Z",
    )
    transition_2 = transition_1.model_copy(
        update={
            "transition_id": "transition-2",
            "reservation_id": reservation_2.reservation_id,
            "final_path": reservation_2.final_path,
        }
    )

    assert transition_1.artifact_sha256 == transition_2.artifact_sha256
    assert transition_1.final_path != transition_2.final_path

    invalid_shared_path = reservation_2.model_dump()
    invalid_shared_path["final_path"] = reservation_1.final_path
    with pytest.raises(ValidationError, match="final path must match reservation identity"):
        api.AudioPublicationReservation.model_validate(invalid_shared_path)


def test_publication_reservation_and_reservation_transition_are_immutable_replayable() -> None:
    api = _api()
    reservation = api.AudioPublicationReservation(
        reservation_id="reservation-1",
        job_id="job-1",
        item_id="item-1",
        field=api.ReviewField.SENTENCE_AUDIO,
        revision_id="rev-1",
        revision_no=1,
        revision_content_hash="1" * 64,
        request_sha256="2" * 64,
        profile_extension="ogg",
        final_path="sentence_audio/item-1/rev-1/" + "2" * 64 + ".ogg",
        authority_sha256="3" * 64,
        root_prestate_sha256="4" * 64,
        version=1,
        reserved_at="2026-08-30T12:06:00Z",
    )
    transition = api.AudioPublicationTransition(
        transition_id="transition-1",
        reservation_id="reservation-1",
        status=api.AudioPublicationStatus.RESERVED,
        from_version=0,
        to_version=1,
        final_path=reservation.final_path,
        artifact_sha256=None,
        evidence_sha256="6" * 64,
        reason_code="none",
        occurred_at="2026-08-30T12:07:00Z",
    )

    assert transition.status is api.AudioPublicationStatus.RESERVED
    assert transition.to_version == reservation.version
    with pytest.raises(ValidationError):
        reservation.final_path = "sentence_audio/item-1/alternate.mp3"
    with pytest.raises(ValidationError):
        transition.status = api.AudioPublicationStatus.FINALIZED


def test_alternate_destination_is_rejected_for_audio_publication() -> None:
    api = _api()

    with pytest.raises(ValidationError, match="final path must match reservation identity"):
        api.AudioPublicationReservation(
            reservation_id="reservation-1",
            job_id="job-1",
            item_id="item-1",
            field=api.ReviewField.WORD_AUDIO,
            revision_id="rev-1",
            revision_no=1,
            revision_content_hash="1" * 64,
            request_sha256="2" * 64,
            profile_extension="mp3",
            final_path="word_audio/item-1/alternate/" + "2" * 64 + ".mp3",
            authority_sha256="3" * 64,
            root_prestate_sha256="4" * 64,
            version=1,
            reserved_at="2026-08-30T12:06:00Z",
        )


def test_accepted_decisions_require_ai_evidence_and_stale_bindings_are_exact() -> None:
    api = _api()
    revision = _revision(api)
    evidence = _ai_evidence(api, candidate_sha256=revision.content_hash)

    accepted = api.ReviewDecision(
        decision_id="decision-1",
        job_id=revision.job_id,
        item_id=revision.item_id,
        field=revision.field,
        revision_id=revision.revision_id,
        revision_no=revision.revision_no,
        content_hash=revision.content_hash,
        status=api.ReviewStatus.ACCEPTED,
        actor_type="ai_model",
        actor_id="review-agent",
        policy_sha256=evidence.policy_sha256,
        evidence=evidence,
        reason_code="none",
        created_at="2026-08-30T12:08:00Z",
    )

    assert accepted.status is api.ReviewStatus.ACCEPTED
    assert accepted.evidence.policy_id == "multilang-ai-linguistic-review-v1"
    with pytest.raises(ValidationError, match="accepted decision requires evidence"):
        api.ReviewDecision(
            decision_id="decision-2",
            job_id=revision.job_id,
            item_id=revision.item_id,
            field=revision.field,
            revision_id=revision.revision_id,
            revision_no=revision.revision_no,
            content_hash=revision.content_hash,
            status=api.ReviewStatus.ACCEPTED,
            actor_type="ai_model",
            actor_id="review-agent",
            policy_sha256=evidence.policy_sha256,
            evidence=None,
            reason_code="none",
            created_at="2026-08-30T12:08:00Z",
        )
    with pytest.raises(ValidationError, match="deterministic failure cannot be accepted"):
        _ai_evidence(
            api,
            candidate_sha256=revision.content_hash,
            validator_result="failed",
        )

    dependency = api.FieldDependencyBinding(
        source_field=api.ReviewField.SENTENCE,
        source_revision_id="sentence-rev-1",
        source_revision_no=1,
        source_content_hash="f" * 64,
        relation="translated_from",
    )
    stale = api.ReviewDecision(
        decision_id="decision-3",
        job_id=revision.job_id,
        item_id=revision.item_id,
        field=api.ReviewField.TRANSLATION,
        revision_id="translation-rev-1",
        revision_no=1,
        content_hash="e" * 64,
        status=api.ReviewStatus.STALE,
        actor_type="system",
        actor_id="dependency-staler",
        policy_sha256=evidence.policy_sha256,
        evidence=None,
        reason_code="source-sentence-changed",
        dependency_binding=dependency,
        created_at="2026-08-30T12:09:00Z",
    )

    assert stale.dependency_binding == dependency
    assert stale.status is api.ReviewStatus.STALE
