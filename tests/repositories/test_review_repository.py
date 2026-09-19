"""Repository tests for Phase 33 review and audio publication persistence."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import (
    GenerationJob,
    ReviewAccessEventModel,
    ReviewDecisionModel,
    ReviewFieldRevisionModel,
)
from multilang.repositories.review_repository import (
    ReviewRepository,
    ReviewRepositoryCASConflict,
    ReviewRepositoryConflict,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    _seed_job(session)
    return session


def _seed_job(session: Session) -> None:
    session.add(
        GenerationJob(
            id="job-1",
            run_key="ko-review-run",
            language="ko",
            source_type="grammar",
            source_fingerprint="fixture",
            status="created",
            current_stage="review",
        )
    )
    session.commit()


def test_revision_creation_preserves_history_under_real_append_only_guards() -> None:
    import runpy
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    session = _session()
    engine = session.get_bind()
    migration = runpy.run_path(str(Path(__file__).resolve().parents[2]
        / "alembic/versions/20260828_19_grammar_personal_sources.py"))
    with engine.begin() as connection, Operations.context(MigrationContext.configure(connection)):
        migration["_create_append_only_guards"]()
    repository = ReviewRepository(session)
    first_command = dict(actor_id="editor", request_id="first", job_id="job-1", item_id="item-1",
        field_name="definition", value_sha256=SHA_A, generator_id="operator-edit",
        generator_version="1", route_id=None, expected_pointer_version=0)
    first = repository.create_candidate_revision(**first_command)
    # An omitted history link and explicit None retain the same legacy command ID.
    replay = repository.create_candidate_revision(**first_command, previous_revision_sha256=None)
    assert replay.replayed and replay.revision.revision_id == first.revision.revision_id
    next_command = {**first_command, "request_id": "next", "value_sha256": SHA_B,
        "generator_id": "openai", "generator_version": "model", "route_id": SHA_C,
        "expected_pointer_version": 1, "previous_revision_sha256": SHA_A}
    second = repository.create_candidate_revision(**next_command)
    assert repository.create_candidate_revision(**next_command).replayed
    stored = session.get(ReviewFieldRevisionModel, second.revision.revision_id)
    assert (stored.previous_revision_sha256, stored.generator_id, stored.generator_version, stored.route_id) == (
        SHA_A, "openai", "model", SHA_C)
    with pytest.raises(ReviewRepositoryConflict):
        repository.create_candidate_revision(**{**next_command, "previous_revision_sha256": SHA_D})
    with pytest.raises(IntegrityError, match="append-only"):
        session.execute(text("UPDATE review_field_revisions SET previous_revision_sha256 = :value WHERE id = :id"),
            {"value": SHA_D, "id": second.revision.revision_id})
    session.rollback()
    assert session.scalar(select(func.count(ReviewFieldRevisionModel.id))) == 2
    session.close()
    engine.dispose()


def test_revision_pointer_stable_access_key_changed_hash_conflict_and_no_release_on_conflict() -> None:
    session = _session()
    repository = ReviewRepository(session)

    created = repository.create_candidate_revision(
        actor_id="generator-1",
        request_id="candidate-1",
        job_id="job-1",
        item_id="item-1",
        field_name="definition",
        value_sha256=SHA_A,
        generator_id="generator-1",
        generator_version="v1",
        route_id="grammar-route",
        expected_pointer_version=0,
    )
    replayed = repository.create_candidate_revision(
        actor_id="generator-1",
        request_id="candidate-1",
        job_id="job-1",
        item_id="item-1",
        field_name="definition",
        value_sha256=SHA_A,
        generator_id="generator-1",
        generator_version="v1",
        route_id="grammar-route",
        expected_pointer_version=0,
    )

    assert replayed.replayed is True
    assert replayed.revision.revision_id == created.revision.revision_id
    assert session.scalar(select(func.count(ReviewFieldRevisionModel.id))) == 1
    with pytest.raises(ReviewRepositoryConflict):
        repository.create_candidate_revision(
            actor_id="generator-1",
            request_id="candidate-1",
            job_id="job-1",
            item_id="item-1",
            field_name="definition",
            value_sha256=SHA_B,
            generator_id="generator-1",
            generator_version="v1",
            route_id="grammar-route",
            expected_pointer_version=0,
        )

    approved = repository.approve_revision(
        actor_id="review-agent",
        request_id="approve-1",
        job_id="job-1",
        item_id="item-1",
        field_name="definition",
        revision_id=created.revision.revision_id,
        expected_pointer_version=created.pointer_version,
        decision_sha256=SHA_C,
        reason_code="none",
    )
    assert approved.pointer_status == "approved"
    with pytest.raises(ReviewRepositoryCASConflict):
        repository.approve_revision(
            actor_id="review-agent",
            request_id="approve-stale",
            job_id="job-1",
            item_id="item-1",
            field_name="definition",
            revision_id=created.revision.revision_id,
            expected_pointer_version=created.pointer_version,
            decision_sha256=SHA_D,
            reason_code="none",
        )
    assert session.scalar(select(func.count(ReviewDecisionModel.id))) == 1

    listed = repository.list_fields_with_audit(
        actor_id="auditor-1",
        request_id="list-1",
        job_id="job-1",
        fields=("definition",),
        statuses=("approved",),
        source_types=("grammar",),
        policy_sha256=SHA_A,
        snapshot_sha256=SHA_B,
    )
    assert listed.event.action == "list"
    assert listed.rows[0]["approved_revision_id"] == created.revision.revision_id
    assert "payload" not in repr(listed.rows)
    assert repository.list_fields_with_audit(
        actor_id="auditor-1",
        request_id="list-1",
        job_id="job-1",
        fields=("definition",),
        statuses=("approved",),
        source_types=("grammar",),
        policy_sha256=SHA_A,
        snapshot_sha256=SHA_B,
    ).replayed is True
    before = session.scalar(select(func.count(ReviewAccessEventModel.id)))
    with pytest.raises(ReviewRepositoryConflict):
        repository.list_fields_with_audit(
            actor_id="auditor-1",
            request_id="list-1",
            job_id="job-1",
            fields=("definition",),
            statuses=("needs_review",),
            source_types=("grammar",),
            policy_sha256=SHA_A,
            snapshot_sha256=SHA_B,
        )
    assert session.scalar(select(func.count(ReviewAccessEventModel.id))) == before


def test_two_session_stale_candidate_writer_leaves_no_partial_revision_event(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'review-race.db'}")
    Base.metadata.create_all(engine)
    seed = Session(engine)
    _seed_job(seed)
    seed.close()
    first_session = Session(engine)
    second_session = Session(engine)
    first = ReviewRepository(first_session)
    second = ReviewRepository(second_session)

    first.create_candidate_revision(
        actor_id="generator-1",
        request_id="candidate-1",
        job_id="job-1",
        item_id="item-1",
        field_name="definition",
        value_sha256=SHA_A,
        generator_id="generator-1",
        generator_version="v1",
        route_id="grammar-route",
        expected_pointer_version=0,
    )

    with pytest.raises(ReviewRepositoryConflict):
        second.create_candidate_revision(
            actor_id="generator-2",
            request_id="candidate-2",
            job_id="job-1",
            item_id="item-1",
            field_name="definition",
            value_sha256=SHA_B,
            generator_id="generator-2",
            generator_version="v1",
            route_id="grammar-route",
            expected_pointer_version=0,
        )

    audit = Session(engine)
    try:
        assert audit.scalar(select(func.count(ReviewFieldRevisionModel.id))) == 1
        assert audit.scalar(select(func.count(ReviewAccessEventModel.id))) == 0
    finally:
        audit.close()
        first_session.close()
        second_session.close()


def test_audio_reserve_before_call_unique_revision_path_same_hash_distinct_paths_and_finalize_requires_published() -> None:
    session = _session()
    repository = ReviewRepository(session)
    first = repository.create_candidate_revision(
        actor_id="audio-generator",
        request_id="audio-candidate-1",
        job_id="job-1",
        item_id="item-1",
        field_name="sentence_audio",
        value_sha256=SHA_A,
        generator_id="audio-generator",
        generator_version="v1",
        route_id="audio-route",
        expected_pointer_version=0,
    )
    second = repository.create_candidate_revision(
        actor_id="audio-generator",
        request_id="audio-candidate-2",
        job_id="job-1",
        item_id="item-2",
        field_name="sentence_audio",
        value_sha256=SHA_B,
        generator_id="audio-generator",
        generator_version="v1",
        route_id="audio-route",
        expected_pointer_version=0,
    )

    reservation = repository.reserve_audio_publication(
        job_id="job-1",
        item_id="item-1",
        field_name="sentence_audio",
        field_revision_id=first.revision.revision_id,
        request_sha256=SHA_A,
        final_path="sentence_audio/item-1/rev-1/request.mp3",
        authority_sha256=SHA_B,
        root_prestate_sha256=SHA_C,
        expected_pointer_version=first.pointer_version,
    )
    with pytest.raises(ReviewRepositoryConflict):
        repository.reserve_audio_publication(
            job_id="job-1",
            item_id="item-2",
            field_name="sentence_audio",
            field_revision_id=second.revision.revision_id,
            request_sha256=SHA_A,
            final_path="sentence_audio/item-1/rev-1/request.mp3",
            authority_sha256=SHA_B,
            root_prestate_sha256=SHA_C,
            expected_pointer_version=second.pointer_version,
        )
    with pytest.raises(ReviewRepositoryCASConflict):
        repository.finalize_audio_publication(
            reservation_id=reservation.reservation_id,
            expected_reservation_version=reservation.version,
            artifact_sha256=SHA_D,
            byte_length=100,
            spoken_text_sha256=SHA_A,
            voice_profile_sha256=SHA_B,
            evidence_sha256=SHA_C,
        )

    staged = repository.append_audio_publication_transition(
        reservation_id=reservation.reservation_id,
        from_state="reserved",
        to_state="staged",
        expected_version=reservation.version,
        transition_sha256=SHA_A,
    )
    published = repository.append_audio_publication_transition(
        reservation_id=reservation.reservation_id,
        from_state="staged",
        to_state="published",
        expected_version=staged.version,
        transition_sha256=SHA_B,
    )
    assert [row.reservation_id for row in repository.list_reconcilable_audio_publications()] == [
        reservation.reservation_id
    ]
    finalized = repository.finalize_audio_publication(
        reservation_id=reservation.reservation_id,
        expected_reservation_version=published.version,
        artifact_sha256=SHA_D,
        byte_length=100,
        spoken_text_sha256=SHA_A,
        voice_profile_sha256=SHA_B,
        evidence_sha256=SHA_C,
    )

    second_reservation = repository.reserve_audio_publication(
        job_id="job-1",
        item_id="item-2",
        field_name="sentence_audio",
        field_revision_id=second.revision.revision_id,
        request_sha256=SHA_B,
        final_path="sentence_audio/item-2/rev-1/request.mp3",
        authority_sha256=SHA_B,
        root_prestate_sha256=SHA_C,
        expected_pointer_version=second.pointer_version,
    )
    second_staged = repository.append_audio_publication_transition(
        reservation_id=second_reservation.reservation_id,
        from_state="reserved",
        to_state="staged",
        expected_version=second_reservation.version,
        transition_sha256=SHA_C,
    )
    second_published = repository.append_audio_publication_transition(
        reservation_id=second_reservation.reservation_id,
        from_state="staged",
        to_state="published",
        expected_version=second_staged.version,
        transition_sha256=SHA_D,
    )
    second_finalized = repository.finalize_audio_publication(
        reservation_id=second_reservation.reservation_id,
        expected_reservation_version=second_published.version,
        artifact_sha256=SHA_D,
        byte_length=100,
        spoken_text_sha256=SHA_A,
        voice_profile_sha256=SHA_B,
        evidence_sha256="e" * 64,
    )

    assert finalized.state == "finalized"
    assert second_finalized.artifact_sha256 == SHA_D
