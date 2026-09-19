"""Persisted Phase 33 operations, with no live provider dependencies."""

from hashlib import sha256
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import ReviewAccessEventModel, ReviewFieldRevisionModel
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.text_repository import TextRepository
from multilang.services import korean_learning_runtime as runtime_module


def setup_runtime(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'learning.sqlite'}")
    Base.metadata.create_all(engine)
    session = Session(engine)
    job = JobRepository(session).create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
        run_key="phase33-test", source_fingerprint="fixture", total_items=2,
    )
    for key in ("row-1", "row-2"):
        LexicalRepository(session).upsert_candidate(
            job_id=job.id, run_key=job.run_key, item_key=key,
            source_type="word-list", normalized_source=key,
            candidate=LexicalCardCandidate(
                submitted_form="집", display_form="집", lemma="집", lemma_key=f"ko:{key}",
                definitions_html="casa", definition_language="pt", translation_target_language="pt",
                grounding_status=GroundingStatus.GROUNDED, provenance=LexicalProvenance(source="manual"),
            ),
        )
        candidate = LexicalRepository(session).get_candidate_for_item(job.id, key)
        TextRepository(session).upsert_text_record(TextQualityRecord(
            job_id=job.id, item_key=key, lexical_candidate_id=candidate.id,
            example_sentence="집이 있어요.", translation_text="Há uma casa.",
            generation_status=TextGenerationStatus.GENERATED, validation_status=ValidationStatus.PASSED,
            review_status=ReviewStatus.ACCEPTED, confidence_label=ConfidenceLabel.HIGH,
            sentence_provenance=TextProvenance(source="fixture"),
            translation_provenance=TextProvenance(source="fixture"),
        ))
    return runtime_module.KoreanLearningRuntime(session), job.id, engine


def test_status_process_and_review_survive_new_session_without_provider(tmp_path):
    runtime, job_id, engine = setup_runtime(tmp_path)
    before = runtime.status(job_id)
    assert before["denominators"]["not_attempted"]["count"] == 2
    result = runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    assert result["processed"] == 1
    assert result["accepted"] == 0
    assert result["review_required"] == 1
    runtime.session.close()

    reopened = runtime_module.KoreanLearningRuntime(Session(engine))
    status = reopened.status(job_id)
    assert status["denominators"]["processed"]["ids"] == ["row-1"]
    rows = reopened.review_list(job_id=job_id, actor_id="operator", request_id="read-1",
                                status="needs_review", field="sentence", source="custom")
    assert len(rows["rows"]) == 1
    assert reopened.session.scalar(select(ReviewAccessEventModel)).id == rows["access_event_id"]
    assert "집" not in str(rows)
    resumed = reopened.process(job_id=job_id, source="custom", mode="resume")
    assert resumed["processed"] == 2


def test_edit_preserves_other_fields_and_records_before_after_history(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    rows = runtime.review_list(job_id=job_id, actor_id="op", request_id="list", status="needs_review",
                               field="sentence", source="custom")["rows"]
    selected = rows[0]
    edited = runtime.review_edit(job_id=job_id, item_id="row-1", field="sentence", value="저 집이 커요.",
                                 actor_id="op", request_id="edit-1",
                                 expected_pointer_version=selected["pointer_version"])
    assert edited["pointer_status"] == "needs_review"
    text = TextRepository(runtime.session).get_text_record(job_id, "row-1")
    assert text.example_sentence == "저 집이 커요."
    assert text.translation_text == "Há uma casa."
    assert text.review_status is ReviewStatus.REVIEW_REQUIRED
    revisions = runtime.session.scalars(select(ReviewFieldRevisionModel).where(
        ReviewFieldRevisionModel.item_id == "row-1", ReviewFieldRevisionModel.field_name == "sentence"
    ).order_by(ReviewFieldRevisionModel.revision_no)).all()
    assert len(revisions) == 2
    assert revisions[-1].previous_revision_sha256 == revisions[0].value_sha256
    assert revisions[-1].value_sha256 == sha256("저 집이 커요.".encode()).hexdigest()
    assert "phase33_field_history" not in text.sentence_provenance.metadata
    history = runtime.jobs.get_job(job_id).resume_state["korean_field_history"]
    assert history[-1]["before"] == "집이 있어요."
    assert history[-1]["after"] == "저 집이 커요."


def test_missing_job_or_empty_source_is_controlled_refusal(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="unknown_job"):
        runtime.status("missing")
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="empty_source"):
        runtime.process(job_id=job_id, source="grammar", mode="start")


def test_reject_is_durable_and_stale_approval_cannot_select_old_revision(tmp_path):
    runtime, job_id, engine = setup_runtime(tmp_path)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    selected = runtime.review_list(job_id=job_id, actor_id="op", request_id="list", status="needs_review",
                                   field="sentence", source="custom")["rows"][0]
    result = runtime.review_decide(job_id=job_id, item_id="row-1", field="sentence",
        revision_id=selected["candidate_revision_id"], expected_pointer_version=selected["pointer_version"],
        actor_id="op", request_id="reject", decision="rejected")
    assert result["pointer_status"] == "rejected"
    runtime.session.close()
    reopened = runtime_module.KoreanLearningRuntime(Session(engine))
    assert len(reopened.review_list(job_id=job_id, actor_id="op", request_id="again", status="rejected",
                                    field="sentence", source="custom")["rows"]) == 1


def test_custom_import_retains_duplicates_and_unresolved_rows_with_safe_status(tmp_path):
    runtime, _job_id, _engine = setup_runtime(tmp_path)
    from multilang.domain.personal_sources import KoreanPersonalSourceResolutionFailure
    from multilang.repositories.korean_personal_source_repository import (
        KoreanPersonalSourceRepository,
    )

    class Unavailable:
        def resolve(self, value):
            return KoreanPersonalSourceResolutionFailure(status="unavailable", reason_code="resolver_error")

    source = tmp_path / "private-book.txt"
    source.write_text("집\n집\n학교\n", encoding="utf-8")
    result = runtime.import_custom(input_file=source, resolver=Unavailable())
    inventory = KoreanPersonalSourceRepository(runtime.session).list_inventory(result["job_id"], "word-list")
    assert [row.submitted_form for row in inventory.rows] == ["집", "집", "학교"]
    assert inventory.rows[1].duplicate_of_position == 1
    assert all(row.latest_decision is not None for row in inventory.rows)
    assert result["needs_review"] == 2
    assert "집" not in str(runtime.status(result["job_id"]))
    assert runtime.import_custom(input_file=source, resolver=Unavailable())["job_id"] == result["job_id"]


def test_cli_alias_uses_persisted_service_and_unknown_job_fails(tmp_path):
    import json

    from typer.testing import CliRunner

    from multilang.cli import create_app
    runtime, job_id, _engine = setup_runtime(tmp_path)
    app = create_app(korean_learning_service=runtime)
    result = CliRunner().invoke(app, ["korean", "status", "--job-id", job_id])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["safe_sources"]["custom"]["eligible_count"] == 2
    missing = CliRunner().invoke(app, ["korean", "process", "--job-id", "missing", "--source", "custom", "--mode", "start"])
    assert missing.exit_code != 0
    assert "unknown_job" in missing.output


@pytest.mark.parametrize("passed", [True, False])
def test_edited_sentence_requires_validation_before_field_approval(tmp_path, passed):
    from types import SimpleNamespace

    from multilang.db.models import LexicalCandidate
    from multilang.domain.korean import (
        KoreanAnalyzerFingerprint,
        KoreanLexicalIdentity,
        KoreanSignatureItem,
    )
    from multilang.domain.text_quality import ValidationFlag, ValidationFlagCode
    from multilang.services.text_validation import TextValidationResult
    runtime, job_id, _engine = setup_runtime(tmp_path)
    fingerprint = KoreanAnalyzerFingerprint(analyzer_name="kiwi", analyzer_package_version="0.20.4",
        model_package_version="0.20.4-model", model_type="cong", enabled_dialects="standard",
        num_workers=1, integrate_allomorph=True, top_n=2, split_complex=False,
        compatible_jamo=False, normalize_coda=False, z_coda=False, typos=None,
        oov_handling="chr", policy_version="kiwi-top2-consensus-v1")
    identity = KoreanLexicalIdentity(submitted_form="집", canonical_nfc="집", lemma="집",
        part_of_speech="NNG", sense_id="house", register="standard",
        morpheme_signature=(KoreanSignatureItem(form="집", pos="NNG"),),
        analyzer_fingerprint=fingerprint, status="resolved")
    candidate = runtime.session.scalar(select(LexicalCandidate).where(LexicalCandidate.item_key == "row-1"))
    candidate.korean_identity = identity.model_dump(mode="json")
    candidate.lemma_key = identity.lexical_key
    runtime.session.commit()
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    edited = runtime.review_edit(job_id=job_id, item_id="row-1", field="sentence", value="저 집이 커요.",
        actor_id="op", request_id="edit", expected_pointer_version=1)
    command = dict(job_id=job_id, item_id="row-1", field="sentence", decision="approved", actor_id="op",
        request_id="approve", revision_id=edited["revision"]["revision_id"], expected_pointer_version=2)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="deterministic_validation_required"):
        runtime.review_decide(**command)
    validator = SimpleNamespace(validate=lambda **kwargs: TextValidationResult(
        validation_status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
        validation_flags=[] if passed else [ValidationFlag(code=ValidationFlagCode.MORPHOLOGY_MISMATCH, detail="wrong target")],
        confidence_score=1.0 if passed else 0.0, confidence_label=ConfidenceLabel.HIGH if passed else ConfidenceLabel.LOW))
    runtime.review_validate(job_id=job_id, item_id="row-1", validator=validator)
    if passed:
        assert runtime.review_decide(**command)["pointer_status"] == "approved"
        assert runtime.review_decide(**command)["replayed"] is True
    else:
        with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="deterministic_validation_required"):
            runtime.review_decide(**command)


def test_stale_session_cannot_reject_superseded_revision(tmp_path):
    runtime, job_id, engine = setup_runtime(tmp_path)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    other = runtime_module.KoreanLearningRuntime(Session(engine))
    stale_pointer = other._pointer(job_id, "row-1", "sentence")
    old_revision = stale_pointer.current_revision_id
    runtime.review_edit(job_id=job_id, item_id="row-1", field="sentence", value="저 집이 커요.",
        actor_id="op", request_id="edit", expected_pointer_version=1)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="stale_revision"):
        other.review_decide(job_id=job_id, item_id="row-1", field="sentence", decision="rejected",
            actor_id="op", request_id="stale", revision_id=old_revision, expected_pointer_version=1)
    other.session.close()


def _bind_fake_policy(runtime, job_id):
    from multilang.domain.korean_provider import (
        KoreanProviderBudget,
        KoreanProviderPolicy,
        KoreanProviderRoute,
        KoreanProviderTask,
    )
    budget = KoreanProviderBudget(max_attempts=1, max_input_tokens=10000, max_output_tokens=1024,
        max_total_tokens=11024, max_estimated_cost_usd=1, max_latency_ms=1000,
        timeout_seconds=1, max_batch_items=1, max_concurrency=1)
    policy = KoreanProviderPolicy(routes=tuple(KoreanProviderRoute(task=task, provider="fake", model="fixture",
        budget=budget, cache_namespace="field-test", response_schema_sha256="a" * 64) for task in KoreanProviderTask))
    job = runtime.jobs.get_job(job_id)
    job.korean_provider_policy = policy.model_dump(mode="json")
    job.korean_provider_policy_sha256 = policy.policy_sha256
    runtime.session.commit()


def test_field_regeneration_persists_value_and_replay_makes_no_second_call(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    import runpy
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    migration = runpy.run_path(str(Path("alembic/versions/20260828_19_grammar_personal_sources.py")))
    with _engine.begin() as connection, Operations.context(MigrationContext.configure(connection)):
        migration["_create_append_only_guards"]()
    _bind_fake_policy(runtime, job_id)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    calls = []

    class Provider:
        provider = "fake"
        model = "fixture"
        def translate_sentence(self, request):
            from multilang.services.text_generation import SentenceTranslationResult
            calls.append(request.sentence)
            return SentenceTranslationResult(translation="Existe uma casa.", provenance={"provider": "fake",
                "input_tokens": 20, "output_tokens": 5, "total_tokens": 25, "estimated_cost": 0.001})

    command = dict(job_id=job_id, item_id="row-1", field="translation", actor_id="op", request_id="regen-1",
        expected_pointer_version=1, provider_factory=lambda field, route: Provider())
    result = runtime.review_regenerate(**command)
    assert result["pointer_status"] == "needs_review"
    assert TextRepository(runtime.session).get_text_record(job_id, "row-1").translation_text == "Existe uma casa."
    assert TextRepository(runtime.session).get_text_record(job_id, "row-1").example_sentence == "집이 있어요."
    assert runtime.review_regenerate(**command)["replayed"] is True
    assert len(calls) == 1
    from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
    attempt = ProviderCallLogRepository(runtime.session).list_for_job(job_id)[0]
    assert (attempt.input_tokens, attempt.output_tokens, attempt.total_tokens, attempt.estimated_cost) == (20, 5, 25, 0.001)


def test_field_regeneration_unknown_outcome_cannot_repeat_provider(tmp_path):
    from multilang.services.generation_leases import GenerationLeaseManager
    runtime, job_id, engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    calls = []
    class Provider:
        provider = "fake"
        model = "fixture"
        def translate_sentence(self, request):
            calls.append(1)
            raise TimeoutError("private provider detail")
    command = dict(job_id=job_id, item_id="row-1", field="translation", actor_id="op", request_id="unknown",
        expected_pointer_version=1, provider_factory=lambda field, route: Provider())
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="regeneration_failed"):
        runtime.review_regenerate(**command)
    assert GenerationLeaseManager(engine).status(job_id)["state"] == "recovery_required"
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="regeneration_recovery_required"):
        runtime.review_regenerate(**command)
    assert len(calls) == 1


def test_field_regeneration_stale_version_and_conflicting_request_never_call_provider(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    from types import SimpleNamespace

    from multilang.services.text_generation import SentenceTranslationResult
    calls = []
    provider = SimpleNamespace(provider="fake", model="fixture", translate_sentence=lambda request: (
        calls.append(request) or SentenceTranslationResult(translation="Existe uma casa.")))
    command = dict(job_id=job_id, item_id="row-1", field="translation", actor_id="op", request_id="same",
        expected_pointer_version=1, provider_factory=lambda field, route: provider)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="stale_revision"):
        runtime.review_regenerate(**{**command, "expected_pointer_version": 9})
    assert calls == []
    runtime.review_regenerate(**command)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="review_request_conflict"):
        runtime.review_regenerate(**{**command, "item_id": "row-2"})
    assert len(calls) == 1


def test_field_regeneration_cli_forwards_explicit_selected_field(tmp_path):
    from types import SimpleNamespace

    from typer.testing import CliRunner

    from multilang.cli import create_app
    calls = []
    service = SimpleNamespace(review_regenerate=lambda **kwargs: calls.append(kwargs) or {"pointer_status": "needs_review"})
    result = CliRunner().invoke(create_app(korean_learning_service=service), ["korean", "review", "regenerate",
        "--job-id", "job", "--item-id", "row-1", "--field", "sentence", "--actor-id", "op",
        "--request-id", "one", "--expected-pointer-version", "3"])
    assert result.exit_code == 0, result.output
    assert calls == [dict(job_id="job", item_id="row-1", field="sentence", actor_id="op",
                          request_id="one", expected_pointer_version=3)]


def test_edit_replay_does_not_duplicate_history_or_restore_superseded_value(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    command = dict(job_id=job_id, item_id="row-1", field="translation", value="Existe uma casa.",
        actor_id="op", request_id="first-edit", expected_pointer_version=1)
    first = runtime.review_edit(**command)
    runtime.review_edit(**{**command, "value": "A casa existe.", "request_id": "second-edit", "expected_pointer_version": 2})
    assert runtime.review_edit(**command) == {**first, "replayed": True}
    assert runtime.texts.get_text_record(job_id, "row-1").translation_text == "A casa existe."
    assert len(runtime.jobs.get_job(job_id).resume_state["korean_field_history"]) == 2


def test_stale_job_session_merges_field_history_from_other_session(tmp_path):
    runtime, job_id, engine = setup_runtime(tmp_path)
    runtime.process(job_id=job_id, source="custom", mode="start")
    stale_job = runtime.jobs.get_job(job_id)
    other = runtime_module.KoreanLearningRuntime(Session(engine))
    other.review_edit(job_id=job_id, item_id="row-1", field="translation", value="Existe uma casa.",
        actor_id="op", request_id="other-edit", expected_pointer_version=1)
    runtime.review_edit(job_id=job_id, item_id="row-2", field="translation", value="A casa existe.",
        actor_id="op", request_id="current-edit", expected_pointer_version=1)
    assert len(runtime.jobs.get_job(job_id).resume_state["korean_field_history"]) == 2
    assert stale_job.id == job_id
    other.session.close()


def test_review_request_identity_cannot_be_reused_for_different_decision(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    revision_id = runtime._pointer(job_id, "row-1", "translation").current_revision_id
    command = dict(job_id=job_id, item_id="row-1", field="translation", revision_id=revision_id,
        decision="approved", actor_id="op", request_id="decide", expected_pointer_version=1)
    runtime.review_decide(**command)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="review_request_conflict"):
        runtime.review_decide(**{**command, "decision": "rejected", "expected_pointer_version": 2})


def test_regeneration_preserves_selected_approved_field_without_provider_call(tmp_path):
    from types import SimpleNamespace
    runtime, job_id, _engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    revision_id = runtime._pointer(job_id, "row-1", "translation").current_revision_id
    runtime.review_decide(job_id=job_id, item_id="row-1", field="translation", revision_id=revision_id,
        decision="approved", actor_id="op", request_id="approve", expected_pointer_version=1)
    calls = []
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="approved_field_preserved"):
        runtime.review_regenerate(job_id=job_id, item_id="row-1", field="translation", actor_id="op",
            request_id="regenerate", expected_pointer_version=2,
            provider_factory=lambda field, route: calls.append(field) or SimpleNamespace(provider="fake", model="fixture"))
    assert calls == []
    assert runtime._pointer(job_id, "row-1", "translation").review_status == "approved"


def test_personal_status_and_resume_recompute_stale_accepted_obligations_without_generation(tmp_path):
    from multilang.domain.jobs import FieldObligationSummary, ItemTerminalStatus, JobStage
    runtime, job_id, _engine = setup_runtime(tmp_path)
    runtime.jobs.record_phase33_skipped_current(job_id, item_id="row-1", stage=JobStage.GENERATE_TEXT.value,
        terminal_status=ItemTerminalStatus.ACCEPTED, obligations=FieldObligationSummary(
            ai_review_current=True, integrity_current=True, word_audio_required=True, word_audio_current=True,
            sentence_audio_required=True, sentence_audio_current=True))
    result = runtime.status(job_id)
    assert result["denominators"]["accepted"]["count"] == 0
    assert result["denominators"]["review_required"]["ids"] == ["row-1"]
    result = runtime.process(job_id=job_id, source="custom", mode="resume")
    assert result["accepted"] == 0
    assert result["review_required"] == 2
    assert result["complete"] is False


def _personal_record_with_reviewed_audio(runtime, job_id, tmp_path, *, sentence_text):
    from multilang.domain.audio import (
        AudioAssetKind,
        AudioAssetRecord,
        AudioProvenance,
        NormalizedTtsInput,
    )
    from multilang.domain.text_quality import KoreanProviderReviewEvidence
    from multilang.repositories.audio_repository import AudioRepository
    record = runtime.texts.get_text_record(job_id, "row-1")
    runtime.texts.upsert_text_record(record.model_copy(update={
        "text_review_receipt_sha256": "b" * 64,
        "provider_review_evidence": KoreanProviderReviewEvidence(reviewer_class="ai_policy_linguistic_review",
            policy_sha256=runtime.jobs.get_job(job_id).korean_provider_policy_sha256,
            review_receipt_sha256="a" * 64, decision="accepted")}))
    for role, text in ((AudioAssetKind.WORD, "집"), (AudioAssetKind.SENTENCE, sentence_text)):
        normalized = NormalizedTtsInput(display_text=text, tts_text=text, synthesis_request_sha256="c" * 64)
        AudioRepository(runtime.session).upsert_audio_asset(AudioAssetRecord(job_id=job_id, item_key="row-1", asset_kind=role,
            display_text=text, normalized_input=normalized, provenance=AudioProvenance(provider="azure",
                voice_id="ko-KR-SunHiNeural", locale="ko-KR", format="mp3", text_hash=normalized.text_hash,
                ssml_hash=normalized.ssml_hash, storage_path=str(tmp_path / f"{role.value}.mp3"), byte_size=12,
                status="synthesized", voice_profile_sha256="d" * 64, catalog_receipt_sha256="e" * 64,
                synthesis_request_sha256="c" * 64, artifact_sha256="f" * 64, audio_review_status="approved",
                audio_review_receipt_sha256="a" * 64, heard_review_receipt_sha256="b" * 64)))


def test_personal_audio_obligations_are_bound_to_current_sentence(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    _personal_record_with_reviewed_audio(runtime, job_id, tmp_path, sentence_text="다른 집이 있어요.")
    result = runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    assert result["accepted"] == 0
    assert result["review_required"] == 1
    obligations = runtime._personal_obligations(job_id, SimpleNamespace(source_family="custom", item_id="row-1"))
    assert obligations.word_audio_current
    assert not obligations.sentence_audio_current


def test_text_rejection_invalidates_acceptance_and_manual_approval_does_not_restore_ai_review(tmp_path):
    runtime, job_id, _engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    _personal_record_with_reviewed_audio(runtime, job_id, tmp_path, sentence_text="집이 있어요.")
    assert runtime.texts.get_text_record(job_id, "row-1").review_status is ReviewStatus.ACCEPTED
    assert runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)["accepted"] == 0
    pointer = runtime._pointer(job_id, "row-1", "sentence")
    revision = pointer.current_revision_id
    command = dict(job_id=job_id, item_id="row-1", field="sentence", revision_id=revision,
        expected_pointer_version=1, actor_id="op", request_id="reject-current", decision="rejected")
    runtime.review_decide(**command)
    record = runtime.texts.get_text_record(job_id, "row-1")
    assert record.review_status is ReviewStatus.REVIEW_REQUIRED
    assert runtime.status(job_id)["denominators"]["accepted"]["count"] == 0
    assert record.text_review_receipt_sha256 == "b" * 64
    runtime.review_decide(**{**command, "request_id": "approve-current", "decision": "approved",
        "expected_pointer_version": 2})
    assert runtime.status(job_id)["denominators"]["accepted"]["count"] == 0
    assert runtime.texts.get_text_record(job_id, "row-1").review_status is ReviewStatus.REVIEW_REQUIRED


def test_personal_status_refuses_text_that_drifted_from_current_revision(tmp_path):
    from multilang.db.models import LexicalCandidate
    runtime, job_id, _engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    _personal_record_with_reviewed_audio(runtime, job_id, tmp_path, sentence_text="집이 있어요.")
    # Legacy accepted flags and hashes cannot replace evidence bound to this snapshot.
    assert runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)["accepted"] == 0
    item = SimpleNamespace(source_family="custom", item_id="row-1")
    assert runtime._personal_obligations(job_id, item).integrity_current
    candidate = runtime.session.scalar(select(LexicalCandidate).where(
        LexicalCandidate.job_id == job_id, LexicalCandidate.item_key == "row-1"))
    candidate.definitions_html = "Uma definição alterada sem revisão."
    runtime.session.commit()
    assert runtime.status(job_id)["denominators"]["accepted"]["count"] == 0
    assert not runtime._personal_obligations(job_id, item).integrity_current


def test_validation_refuses_result_when_another_session_edits_during_analysis(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from multilang.services.generate_text_items import GenerateTextItemsService
    from multilang.services.text_validation import TextValidationResult
    runtime, job_id, engine = setup_runtime(tmp_path)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    other = runtime_module.KoreanLearningRuntime(Session(engine))
    monkeypatch.setattr(GenerateTextItemsService, "_to_candidate", lambda *args: SimpleNamespace(
        korean_identity=SimpleNamespace(sense_id="house"), display_form="집", lemma="집", definitions_html="casa"))
    def validate(**kwargs):
        other.review_edit(job_id=job_id, item_id="row-1", field="translation", value="Existe uma casa.",
            actor_id="other", request_id="concurrent", expected_pointer_version=1)
        return TextValidationResult(validation_status=ValidationStatus.PASSED, validation_flags=[],
            confidence_score=1, confidence_label=ConfidenceLabel.HIGH)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="stale_revision"):
        runtime.review_validate(job_id=job_id, item_id="row-1", validator=SimpleNamespace(validate=validate))
    record = runtime.texts.get_text_record(job_id, "row-1")
    assert record.translation_text == "Existe uma casa."
    assert record.validation_status is ValidationStatus.PENDING
    other.session.close()


def test_personal_regeneration_cannot_bypass_frequency_authority(tmp_path):
    from multilang.db.models import LexicalCandidate
    runtime, job_id, _engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    candidate = runtime.session.scalar(select(LexicalCandidate).where(
        LexicalCandidate.job_id == job_id, LexicalCandidate.item_key == "row-1"))
    candidate.source_type = "frequency"
    runtime.session.commit()
    calls = []
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="personal_source_required"):
        runtime.review_regenerate(job_id=job_id, item_id="row-1", field="translation", actor_id="op",
            request_id="not-frequency-authority", expected_pointer_version=1,
            provider_factory=lambda field, route: calls.append(field))
    assert calls == []


def test_highlight_import_is_local_idempotent_and_keeps_private_excerpt_separate(tmp_path):
    from multilang.domain.korean import (
        KoreanAnalyzerFingerprint,
        KoreanLexicalIdentity,
        KoreanSignatureItem,
    )
    from multilang.repositories.highlight_import_repository import HighlightImportRepository
    from multilang.services.lexical_grounding import KoreanResolvedLexeme
    runtime, _job_id, _engine = setup_runtime(tmp_path)
    identity = KoreanLexicalIdentity(submitted_form=None, canonical_nfc="집", lemma="집",
        part_of_speech="NNG", sense_id="house", register="standard", status="resolved",
        morpheme_signature=(KoreanSignatureItem(form="집", pos="NNG"),),
        analyzer_fingerprint=KoreanAnalyzerFingerprint(analyzer_name="kiwi", analyzer_package_version="0.23.2",
            model_package_version="0.23.0", model_type="cong", enabled_dialects="standard", num_workers=1,
            integrate_allomorph=True, top_n=2, split_complex=False, compatible_jamo=False, normalize_coda=False,
            z_coda=False, typos=None, oov_handling="chr", policy_version="kiwi-top2-consensus-v1"))
    class Grounding:
        def resolve_korean_highlight_text(self, text):
            return tuple(KoreanResolvedLexeme(surface_form="집", word_position=index, identity=identity) for index in (0, 1))
        def ground_highlight_candidate(self, *, language, candidate, rate_limiter=None):
            return LexicalCardCandidate(submitted_form="집", display_form="집", lemma="집", lemma_key=identity.lexical_key,
                korean_identity=identity, definitions_html="casa", definition_language="pt",
                translation_target_language="pt", grounding_status=GroundingStatus.GROUNDED,
                provenance=LexicalProvenance(source="manual"))
    source = tmp_path / "secret-book.txt"
    private_text = "집이 보여요. Trecho privado de leitura."
    source.write_text(f"Private Book Title\n- Your Highlight at Location 1\n{private_text}\n==========", encoding="utf-8")
    result = runtime.import_highlights(input_file=source, grounding_service=Grounding())
    assert result["imported_highlights"] == 1
    assert result["extracted_candidates"] == 1
    assert result["duplicate_candidates"] == 1
    assert result["planned_cards"] == 1
    assert all(item.startswith("highlight-ko-") for item in result["item_ids"])
    assert not any(value in str(result) for value in ("집", private_text, "Private Book Title", source.name, str(tmp_path)))
    private_repository = HighlightImportRepository(runtime.session)
    inventory = private_repository.list_korean_safe_inventory(result["job_id"])
    record = private_repository.load_private_excerpt_revision(result["job_id"], inventory.rows[0].excerpt_revision_id)
    assert private_text in record.normalized_text
    assert runtime.texts.list_records_for_job(result["job_id"]) == []
    again = runtime.import_highlights(input_file=source, grounding_service=Grounding())
    assert again["job_id"] == result["job_id"]
    assert again["reused_existing_items"] == 1


@pytest.mark.parametrize("kind", ["symlink", "oversize", "directory"])
def test_highlight_import_refuses_unsafe_or_oversized_input_before_parser(tmp_path, kind):
    runtime, _job_id, _engine = setup_runtime(tmp_path)
    source = tmp_path / "input.txt"
    if kind == "symlink":
        target = tmp_path / "target.txt"
        target.write_text("private", encoding="utf-8")
        source.symlink_to(target)
    elif kind == "directory":
        source.mkdir()
    else:
        source.write_bytes(b"x" * 1_000_001)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="invalid_highlight_input"):
        runtime.import_highlights(input_file=source, grounding_service=object())


def test_highlight_import_cli_only_forwards_input_to_importer(tmp_path):
    import json
    from types import SimpleNamespace

    from typer.testing import CliRunner

    from multilang.cli import create_app
    source = tmp_path / "input.txt"
    source.write_text("local", encoding="utf-8")
    calls = []
    service = SimpleNamespace(import_highlights=lambda **kwargs: calls.append(kwargs) or {"job_id": "safe-job"})
    result = CliRunner().invoke(create_app(korean_learning_service=service),
        ["korean", "import-highlights", "--input-file", str(source)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"job_id": "safe-job"}
    assert calls == [{"input_file": source}]


def test_regeneration_refuses_lexical_identity_change_during_provider_call(tmp_path):
    from types import SimpleNamespace

    from multilang.db.models import LexicalCandidate
    from multilang.services.text_generation import SentenceTranslationResult
    runtime, job_id, engine = setup_runtime(tmp_path)
    _bind_fake_policy(runtime, job_id)
    runtime.process(job_id=job_id, source="custom", mode="start", max_items=1)
    def generate(request):
        with Session(engine) as other:
            candidate = other.scalar(select(LexicalCandidate).where(
                LexicalCandidate.job_id == job_id, LexicalCandidate.item_key == "row-1"))
            candidate.lemma = "학교"
            other.commit()
        return SentenceTranslationResult(translation="Existe uma casa.")
    provider = SimpleNamespace(provider="fake", model="fixture", translate_sentence=generate)
    with pytest.raises(runtime_module.KoreanLearningRuntimeError, match="stale_revision"):
        runtime.review_regenerate(job_id=job_id, item_id="row-1", field="translation", actor_id="op", request_id="drift",
            expected_pointer_version=1, provider_factory=lambda field, route: provider)
    assert runtime.texts.get_text_record(job_id, "row-1").translation_text == "Há uma casa."
