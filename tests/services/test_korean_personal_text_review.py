"""Local-only, current-content AI review evidence for Korean personal cards."""

import importlib
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.models import LexicalCandidate, ReviewCurrentPointerModel
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
)
from multilang.domain.text_quality import ConfidenceLabel, ReviewStatus, ValidationStatus
from multilang.services.ai_linguistic_review import ai_review_content_hash
from multilang.services.text_validation import TextValidationResult


def _module():
    return importlib.import_module("multilang.services.korean_personal_text_review")


def _seal(payload):
    return {**payload, "content_hash": ai_review_content_hash(payload)}


def _setup(tmp_path):
    helpers = runpy.run_path(str(Path(__file__).with_name("test_korean_learning_runtime.py")))
    runtime, job_id, engine = helpers["setup_runtime"](tmp_path)
    helpers["_bind_fake_policy"](runtime, job_id)
    fingerprint = KoreanAnalyzerFingerprint(analyzer_name="kiwi", analyzer_package_version="0.20.4",
        model_package_version="0.20.4-model", model_type="cong", enabled_dialects="standard",
        num_workers=1, integrate_allomorph=True, top_n=2, split_complex=False,
        compatible_jamo=False, normalize_coda=False, z_coda=False, typos=None,
        oov_handling="chr", policy_version="kiwi-top2-consensus-v1")
    identity = KoreanLexicalIdentity(submitted_form="집", canonical_nfc="집", lemma="집", part_of_speech="NNG",
        sense_id="house", register="standard", morpheme_signature=(KoreanSignatureItem(form="집", pos="NNG"),),
        analyzer_fingerprint=fingerprint, status="resolved")
    row = runtime.session.scalar(select(LexicalCandidate).where(LexicalCandidate.item_key == "row-1"))
    row.korean_identity = identity.model_dump(mode="json")
    row.lemma_key = identity.lexical_key
    runtime.session.commit()
    runtime._snapshot_fields(job_id, "row-1")
    runtime.review_edit(job_id=job_id, item_id="row-1", field="translation", value="Existe uma casa.",
        actor_id="operator", request_id="edit", expected_pointer_version=1)
    validator = SimpleNamespace(validate=lambda **kwargs: TextValidationResult(validation_status=ValidationStatus.PASSED,
        validation_flags=[], confidence_score=1, confidence_label=ConfidenceLabel.HIGH))
    runtime.review_validate(job_id=job_id, item_id="row-1", validator=validator)
    return runtime, job_id, engine


def _evidence(snapshot):
    module = _module()
    passes = []
    for index in range(3):
        claims = [_seal(dict(schema_version=1, claim_id=claim, verdict="passed", confidence=0.99,
            reason_code="none", uncertainty_codes=[], evidence_reference_ids=snapshot["evidence_reference_ids"]))
            for claim in module.CLAIM_IDS]
        decision = _seal(dict(schema_version=1, subject_id=snapshot["subject_id"],
            subject_content_sha256=snapshot["content_hash"], status="ai_review_passed", reason_code="none",
            uncertainty_codes=[], atomic_claims=claims))
        passes.append(_seal(dict(schema_version=1, actor_type="ai_model", is_human=False,
            actor_id=f"judge-{index}", pass_id=f"pass-{index}", fresh_context_id=f"context-{index}",
            independence_scope="fresh_context_same_model", provider=snapshot["judge_provider"],
            model=snapshot["judge_model"], model_version="fixture-v1", provider_api_version="fixture-v1",
            provider_policy_sha256=snapshot["provider_policy_sha256"], review_policy_sha256=module.REVIEW_POLICY_SHA256,
            route_policy_sha256=snapshot["judge_route_sha256"], response_schema_sha256=snapshot["judge_schema_sha256"],
            prompt_id="personal-text-review", prompt_version="1", prompt_template_sha256="b" * 64,
            started_at="2026-09-19T00:00:00Z", completed_at="2026-09-19T00:01:00Z", decision=decision)))
    validators = [_seal(dict(schema_version=1, subject_id=snapshot["subject_id"],
        subject_content_sha256=snapshot["content_hash"], validator_id=name, validator_version="1",
        result="passed", reason_code="none", executed_at="2026-09-19T00:00:00Z")) for name in module.VALIDATOR_IDS]
    return _seal(dict(schema_version=1, snapshot=snapshot, validators=validators, passes=passes))


def test_edit_validate_apply_persists_current_ai_review_without_manual_self_approval(tmp_path):
    runtime, job_id, engine = _setup(tmp_path)
    module = _module()
    pointer = runtime._pointer(job_id, "row-1", "translation")
    runtime.review_decide(job_id=job_id, item_id="row-1", field="translation",
        revision_id=pointer.current_revision_id, expected_pointer_version=pointer.pointer_version,
        actor_id="operator", request_id="manual-approve", decision="approved")
    assert runtime.texts.get_text_record(job_id, "row-1").review_status is ReviewStatus.REVIEW_REQUIRED
    assert not module.personal_text_review_current(runtime.session, job_id, "row-1")
    snapshot = module.prepare_personal_text_evidence(runtime, job_id=job_id, item_id="row-1")
    assert all(value not in str(snapshot) for value in ("집", "Existe uma casa", "fixture-sense", str(tmp_path)))
    evidence = _evidence(snapshot)
    command = dict(job_id=job_id, item_id="row-1", evidence=evidence, actor_id="operator", request_id="apply")
    result = module.apply_personal_text_evidence(runtime, **command)
    assert result["status"] == "ai_review_passed"
    assert module.apply_personal_text_evidence(runtime, **command)["replayed"] is True
    record = runtime.texts.get_text_record(job_id, "row-1")
    assert record.review_status is ReviewStatus.ACCEPTED
    assert record.provider_review_evidence.review_receipt_sha256 == record.text_review_receipt_sha256
    obligations = runtime._personal_obligations(job_id, SimpleNamespace(source_family="custom", item_id="row-1"))
    assert obligations.ai_review_current and obligations.integrity_current
    runtime.session.close()
    with Session(engine) as session:
        assert module.personal_text_review_current(session, job_id, "row-1")


@pytest.mark.parametrize("failure", ["content", "identity", "source", "policy", "policy-payload", "pointer",
    "duplicate-pass", "duplicate-context", "judge-model", "low-confidence", "missing-claim", "uncertain",
    "validator", "rejected-history"])
def test_stale_or_incomplete_evidence_never_restores_ai_acceptance(tmp_path, failure):
    runtime, job_id, _engine = _setup(tmp_path)
    module = _module()
    evidence = _evidence(module.prepare_personal_text_evidence(runtime, job_id=job_id, item_id="row-1"))
    candidate, record, _values = runtime._values(job_id, "row-1")
    if failure == "content":
        candidate.definitions_html = "definição alterada"
    elif failure == "identity":
        candidate.korean_identity = {**candidate.korean_identity, "sense_id": "changed-sense"}
    elif failure == "source":
        candidate.provenance = {**candidate.provenance, "source": "changed-source"}
    elif failure == "policy":
        runtime._job(job_id).korean_provider_policy_sha256 = "f" * 64
    elif failure == "policy-payload":
        job = runtime._job(job_id)
        job.korean_provider_policy = {**job.korean_provider_policy, "policy_id": "changed-policy"}
    elif failure == "pointer":
        runtime._pointer(job_id, "row-1", "translation").pointer_version += 1
    elif failure == "rejected-history":
        pointer = runtime._pointer(job_id, "row-1", "translation")
        runtime.review_decide(job_id=job_id, item_id="row-1", field="translation", revision_id=pointer.current_revision_id,
            expected_pointer_version=pointer.pointer_version, actor_id="operator", request_id="reject", decision="rejected")
        runtime.review_decide(job_id=job_id, item_id="row-1", field="translation", revision_id=pointer.current_revision_id,
            expected_pointer_version=pointer.pointer_version, actor_id="operator", request_id="approve-after-reject", decision="approved")
    elif failure in {"duplicate-pass", "duplicate-context"}:
        field = "pass_id" if failure == "duplicate-pass" else "fresh_context_id"
        evidence["passes"][1] = _seal({**evidence["passes"][1], field: evidence["passes"][0][field]})
    elif failure == "missing-claim":
        decision = evidence["passes"][0]["decision"]
        decision["atomic_claims"] = decision["atomic_claims"][:-1]
        evidence["passes"][0] = _seal({**evidence["passes"][0], "decision": _seal(decision)})
    elif failure == "judge-model":
        evidence["passes"][0] = _seal({**evidence["passes"][0], "model": "wrong-model"})
    elif failure == "low-confidence":
        decision = evidence["passes"][0]["decision"]
        decision["atomic_claims"][0] = _seal({**decision["atomic_claims"][0], "confidence": 0.79})
        evidence["passes"][0] = _seal({**evidence["passes"][0], "decision": _seal(decision)})
    elif failure == "uncertain":
        decision = evidence["passes"][0]["decision"]
        decision["atomic_claims"][0] = _seal({**decision["atomic_claims"][0], "verdict": "uncertain",
            "reason_code": "uncertainty-present", "uncertainty_codes": ["linguistic-ambiguity"]})
        decision.update(status="blocked_uncertainty", reason_code="uncertainty-present", uncertainty_codes=["linguistic-ambiguity"])
        evidence["passes"][0] = _seal({**evidence["passes"][0], "decision": _seal(decision)})
    elif failure == "validator":
        evidence["validators"][0] = _seal({**evidence["validators"][0], "result": "failed", "reason_code": "failed"})
    runtime.session.commit()
    with pytest.raises(ValueError):
        module.apply_personal_text_evidence(runtime, job_id=job_id, item_id="row-1", evidence=_seal(evidence),
            actor_id="operator", request_id="apply")
    assert runtime.texts.get_text_record(job_id, "row-1").review_status is not ReviewStatus.ACCEPTED


def test_current_receipt_allows_later_approval_but_refuses_rejection_or_changed_identity(tmp_path):
    runtime, job_id, _engine = _setup(tmp_path)
    module = _module()
    evidence = _evidence(module.prepare_personal_text_evidence(runtime, job_id=job_id, item_id="row-1"))
    command = dict(job_id=job_id, item_id="row-1", evidence=evidence, actor_id="operator", request_id="apply")
    module.apply_personal_text_evidence(runtime, **command)
    pointer = runtime._pointer(job_id, "row-1", "translation")
    runtime.review_decide(job_id=job_id, item_id="row-1", field="translation", revision_id=pointer.current_revision_id,
        expected_pointer_version=pointer.pointer_version, actor_id="operator", request_id="approve", decision="approved")
    assert module.personal_text_review_current(runtime.session, job_id, "row-1")
    candidate, _record, _values = runtime._values(job_id, "row-1")
    candidate.korean_identity = {**candidate.korean_identity, "sense_id": "changed-sense"}
    runtime.session.commit()
    assert not module.personal_text_review_current(runtime.session, job_id, "row-1")
    assert not runtime._personal_obligations(job_id,
        SimpleNamespace(source_family="custom", item_id="row-1")).ai_review_current
    with pytest.raises(ValueError):
        module.apply_personal_text_evidence(runtime, **command)


@pytest.mark.parametrize("failure", ["dirty", "receipt-revoked", "request-conflict"])
def test_application_refuses_dirty_state_revoked_receipt_and_reused_request(tmp_path, failure):
    runtime, job_id, _engine = _setup(tmp_path)
    module = _module()
    evidence = _evidence(module.prepare_personal_text_evidence(runtime, job_id=job_id, item_id="row-1"))
    command = dict(job_id=job_id, item_id="row-1", evidence=evidence, actor_id="operator", request_id="apply")
    if failure == "dirty":
        candidate, _record, _values = runtime._values(job_id, "row-1")
        candidate.definitions_html = "edição ainda não salva"
    else:
        module.apply_personal_text_evidence(runtime, **command)
        if failure == "receipt-revoked":
            record = runtime.texts.get_text_record(job_id, "row-1")
            runtime.texts.upsert_text_record(record.model_copy(update={"review_status": ReviewStatus.REVIEW_REQUIRED}))
        else:
            evidence["passes"][0] = _seal({**evidence["passes"][0], "pass_id": "new-pass"})
            command["evidence"] = _seal(evidence)
    with pytest.raises(ValueError):
        module.apply_personal_text_evidence(runtime, **command)


@pytest.mark.parametrize("changed", ["content", "pointer"])
def test_job_lock_rereads_generic_writer_changes_from_another_session(tmp_path, monkeypatch, changed):
    runtime, job_id, engine = _setup(tmp_path)
    module = _module()
    evidence = _evidence(module.prepare_personal_text_evidence(runtime, job_id=job_id, item_id="row-1"))
    real_lock = module.lock_job_for_update

    def lock_after_generic_writer(session, selected_job):
        with Session(engine) as writer:
            if changed == "content":
                candidate = writer.scalar(select(LexicalCandidate).where(
                    LexicalCandidate.job_id == job_id, LexicalCandidate.item_key == "row-1"))
                candidate.definitions_html = "conteúdo editado em outro fluxo"
            else:
                pointer = writer.scalar(select(ReviewCurrentPointerModel).where(
                    ReviewCurrentPointerModel.job_id == job_id, ReviewCurrentPointerModel.item_id == "row-1",
                    ReviewCurrentPointerModel.field_name == "translation"))
                pointer.pointer_version += 1
            writer.commit()
        return real_lock(session, selected_job)

    monkeypatch.setattr(module, "lock_job_for_update", lock_after_generic_writer)
    with pytest.raises(ValueError, match="text_review_(stale_revision|snapshot_stale)"):
        module.apply_personal_text_evidence(runtime, job_id=job_id, item_id="row-1", evidence=evidence,
            actor_id="operator", request_id="racing-apply")
    assert not module.personal_text_review_current(runtime.session, job_id, "row-1")
    assert "korean_personal_text_reviews" not in runtime._job(job_id).resume_state


def test_cli_prepares_private_safe_snapshot_and_applies_local_evidence(tmp_path):
    import json

    import typer
    from typer.testing import CliRunner

    commands = importlib.import_module("multilang.cli_commands.korean_personal_text_review")
    runtime, job_id, _engine = _setup(tmp_path)
    app = typer.Typer()
    commands.register_commands(app, lambda: runtime)
    runner = CliRunner()
    result = runner.invoke(app, ["prepare-text-evidence", "--job-id", job_id, "--item-id", "row-1"])
    assert result.exit_code == 0, result.output
    snapshot = json.loads(result.output)
    assert "Existe uma casa" not in result.output
    from multilang.cli import create_app
    integrated_app = create_app(korean_learning_service=runtime)
    for alias in ("korean", "phase33"):
        result = runner.invoke(integrated_app, [alias, "review", "prepare-text-evidence",
            "--job-id", job_id, "--item-id", "row-1"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.output) == snapshot
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text(json.dumps(_evidence(snapshot)), encoding="utf-8")
    result = runner.invoke(app, ["apply-text-evidence", "--job-id", job_id, "--item-id", "row-1",
        "--evidence-file", str(evidence_file), "--actor-id", "operator", "--request-id", "cli-apply"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "ai_review_passed"
    assert _module().personal_text_review_current(runtime.session, job_id, "row-1")


def test_cli_bounds_input_and_closes_owned_session_without_leaking_errors(tmp_path):
    import typer
    from typer.testing import CliRunner

    commands = importlib.import_module("multilang.cli_commands.korean_personal_text_review")
    closed = []
    runtime = SimpleNamespace(owned_session=True, session=SimpleNamespace(
        close=lambda: closed.append(True), new=False, dirty=False, deleted=False))
    app = typer.Typer()
    commands.register_commands(app, lambda: runtime)
    runner = CliRunner()
    result = runner.invoke(app, ["prepare-text-evidence", "--job-id", "private-job", "--item-id", "secret-item"])
    assert result.exit_code == 1
    assert result.output == "korean_error=text_review_operation_failed\n"
    assert closed == [True]
    private_file = tmp_path / "private-reading.json"
    private_file.write_text("private content" * 100_000, encoding="utf-8")
    result = runner.invoke(app, ["apply-text-evidence", "--job-id", "private-job", "--item-id", "secret-item",
        "--evidence-file", str(private_file), "--actor-id", "operator", "--request-id", "oversized"])
    assert result.exit_code == 1
    assert "private" not in result.output
    assert "secret" not in result.output
    assert str(tmp_path) not in result.output
