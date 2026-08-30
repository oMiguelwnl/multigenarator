"""Closed, fail-closed contracts for policy-bound AI linguistic review."""

from __future__ import annotations

from copy import deepcopy
from importlib import import_module, util
import inspect
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from pydantic import ValidationError


def _api() -> ModuleType:
    assert util.find_spec("multilang.services.ai_linguistic_review") is not None
    return import_module("multilang.services.ai_linguistic_review")


def _hashed(api: ModuleType, model_name: str, payload: dict[str, object]) -> object:
    payload = deepcopy(payload)
    payload["content_hash"] = api.ai_review_content_hash(payload)
    return getattr(api, model_name).model_validate(payload)


def _policy_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": "multilang-ai-linguistic-review-v1",
        "policy_version": "1",
        "policy_sha256": "a" * 64,
        "standard_pass_count": 2,
        "critical_pass_count": 3,
        "minimum_confidence": 0.8,
        "max_batch_size": 20,
        "max_concurrent_invocations": 4,
        "required_invocations": 21,
        "max_attempts": 42,
        "max_input_tokens": 30_000,
        "max_output_tokens": 12_000,
        "timeout_seconds": 600,
        "repository_provider_spend_usd": 0,
    }


def _subject_payload() -> dict[str, object]:
    projection = {
        "family": "hangul",
        "item_key": "ko-hangul-0001",
        "learner_content": {"canonical_jamo_or_block": "ᄀ"},
        "curriculum_evidence": {"target_concept_id": "orthography.onset.giyeok"},
        "source_references": [{"source_id": "unicode-v15.1", "source_hash": "b" * 64}],
    }
    api = _api()
    return {
        "schema_version": 1,
        "actor_type": "ai_review_subject",
        "subject_id": "ko-hangul-0001",
        "family": "hangul",
        "item_key": "ko-hangul-0001",
        "critical": True,
        "generator_actor_id": "phase31-curation-agent",
        "source_pack_version": "hangul-v2",
        "source_content_sha256": "c" * 64,
        "candidate_sha256": "d" * 64,
        "analyzer_sha256": "e" * 64,
        "curriculum_sha256": "f" * 64,
        "media_sha256": api.NOT_APPLICABLE_SHA256,
        "claim_ids": ("source.name", "curriculum.atomicity"),
        "source_reference_ids": ("unicode-v15.1",),
        "projection": projection,
        "projection_sha256": api.ai_review_content_hash(projection),
    }


def _validator_payload(subject: object) -> dict[str, object]:
    return {
        "schema_version": 1,
        "subject_id": subject.subject_id,
        "subject_content_sha256": subject.content_hash,
        "validator_id": "korean-foundation-curriculum",
        "validator_version": "1",
        "result": "passed",
        "reason_code": "none",
        "executed_at": "2026-08-27T15:00:00Z",
    }


def _attempt_payload(api: ModuleType, policy: object, subject: object) -> dict[str, object]:
    claims = []
    for claim_id in subject.claim_ids:
        claim = {
            "schema_version": 1,
            "claim_id": claim_id,
            "verdict": "passed",
            "confidence": 0.95,
            "reason_code": "none",
            "uncertainty_codes": [],
            "evidence_reference_ids": ["unicode-v15.1"],
        }
        claim["content_hash"] = api.ai_review_content_hash(claim)
        claims.append(claim)
    decision = {
        "schema_version": 1,
        "subject_id": subject.subject_id,
        "subject_content_sha256": subject.content_hash,
        "status": "ai_review_passed",
        "reason_code": "none",
        "uncertainty_codes": [],
        "atomic_claims": claims,
    }
    decision["content_hash"] = api.ai_review_content_hash(decision)
    return {
        "schema_version": 1,
        "actor_type": "ai_model",
        "is_human": False,
        "actor_id": "review-agent",
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "policy_sha256": policy.policy_sha256,
        "route_id": "opencode-local-agent",
        "provider_id": "opencode",
        "provider_api_version": "2026-08-27",
        "model_id": "gpt-5.6-sol",
        "model_version": "2026-08-27",
        "prompt_id": "korean-foundation-linguistic-review",
        "prompt_version": "1",
        "prompt_template_sha256": "1" * 64,
        "output_schema_id": "ai-linguistic-review-pass",
        "output_schema_version": "1",
        "output_schema_sha256": "2" * 64,
        "execution_surface": "opencode-agent",
        "batch_id": "batch-01",
        "pass_id": "pass-1",
        "fresh_context_id": "fresh-context-1",
        "independence_scope": "fresh_context_same_model",
        "attempt_number": 1,
        "started_at": "2026-08-27T15:00:00Z",
        "completed_at": "2026-08-27T15:01:00Z",
        "subject_content_hashes": [subject.content_hash],
        "decisions": [decision],
    }


def test_public_contract_is_closed_and_has_no_provider_client() -> None:
    api = _api()
    expected = {
        "AIReviewAggregate",
        "AIReviewAttempt",
        "AIReviewDecision",
        "AIReviewPolicy",
        "AIReviewSubject",
        "AIValidatorRun",
        "AtomicClaimVerdict",
        "NOT_APPLICABLE_SHA256",
        "ai_review_content_hash",
        "build_ai_review_aggregate",
        "validate_ai_review_attempt",
    }
    assert set(api.__all__) == expected
    source = inspect.getsource(api).casefold()
    for forbidden in ("openai", "anthropic", "litellm", "requests", "httpx", "https://"):
        assert forbidden not in source


def test_policy_requires_exact_bounded_critical_review_ceiling() -> None:
    api = _api()
    policy = _hashed(api, "AIReviewPolicy", _policy_payload())
    assert policy.critical_pass_count == 3
    assert policy.required_invocations == 7 * 3
    assert policy.max_attempts == 7 * 3 * 2

    for field, value in (
        ("critical_pass_count", 2),
        ("max_batch_size", 21),
        ("max_concurrent_invocations", 5),
        ("repository_provider_spend_usd", 1),
        ("max_attempts", 43),
    ):
        payload = _policy_payload()
        payload[field] = value
        with pytest.raises(ValidationError):
            _hashed(api, "AIReviewPolicy", payload)


def test_subject_requires_distinct_exact_hashes_and_canonical_media_sentinel() -> None:
    api = _api()
    subject = _hashed(api, "AIReviewSubject", _subject_payload())
    assert subject.actor_type == "ai_review_subject"
    assert subject.media_sha256 == api.NOT_APPLICABLE_SHA256

    for field in (
        "source_content_sha256",
        "candidate_sha256",
        "analyzer_sha256",
        "curriculum_sha256",
        "media_sha256",
        "projection_sha256",
    ):
        payload = _subject_payload()
        payload.pop(field)
        with pytest.raises(ValidationError):
            _hashed(api, "AIReviewSubject", payload)

    duplicate = _subject_payload()
    duplicate["analyzer_sha256"] = duplicate["candidate_sha256"]
    with pytest.raises(ValidationError):
        _hashed(api, "AIReviewSubject", duplicate)

    stale = _subject_payload()
    stale["projection_sha256"] = "9" * 64
    with pytest.raises(ValidationError):
        _hashed(api, "AIReviewSubject", stale)


def test_attempt_rejects_human_impersonation_generator_reuse_and_bad_provenance() -> None:
    api = _api()
    policy = _hashed(api, "AIReviewPolicy", _policy_payload())
    subject = _hashed(api, "AIReviewSubject", _subject_payload())
    base = _attempt_payload(api, policy, subject)
    attempt = _hashed(api, "AIReviewAttempt", base)
    api.validate_ai_review_attempt(attempt, policy=policy, subjects=(subject,))

    for field, value in (
        ("actor_type", "human"),
        ("is_human", True),
        ("actor_id", subject.generator_actor_id),
        ("policy_sha256", "8" * 64),
        ("execution_surface", "repository-tool"),
        ("independence_scope", "unknown"),
    ):
        payload = _attempt_payload(api, policy, subject)
        payload[field] = value
        with pytest.raises((ValidationError, ValueError)):
            candidate = _hashed(api, "AIReviewAttempt", payload)
            api.validate_ai_review_attempt(candidate, policy=policy, subjects=(subject,))

    extra = _attempt_payload(api, policy, subject)
    extra["human_reviewer"] = "native-speaker"
    with pytest.raises(ValidationError):
        _hashed(api, "AIReviewAttempt", extra)


def test_attempt_rejects_missing_claim_unknown_evidence_low_confidence_and_stale_subject() -> None:
    api = _api()
    policy = _hashed(api, "AIReviewPolicy", _policy_payload())
    subject = _hashed(api, "AIReviewSubject", _subject_payload())

    mutations = []
    missing = _attempt_payload(api, policy, subject)
    missing["decisions"][0]["atomic_claims"].pop()
    mutations.append(missing)
    unknown_evidence = _attempt_payload(api, policy, subject)
    unknown_evidence["decisions"][0]["atomic_claims"][0]["evidence_reference_ids"] = [
        "invented-source"
    ]
    mutations.append(unknown_evidence)
    low = _attempt_payload(api, policy, subject)
    low["decisions"][0]["atomic_claims"][0]["confidence"] = 0.79
    mutations.append(low)
    stale = _attempt_payload(api, policy, subject)
    stale["decisions"][0]["subject_content_sha256"] = "7" * 64
    mutations.append(stale)

    for payload in mutations:
        with pytest.raises((ValidationError, ValueError)):
            attempt = _hashed(api, "AIReviewAttempt", payload)
            api.validate_ai_review_attempt(attempt, policy=policy, subjects=(subject,))


def test_consensus_requires_all_three_fresh_context_passes_and_all_validators() -> None:
    api = _api()
    policy = _hashed(api, "AIReviewPolicy", _policy_payload())
    subject = _hashed(api, "AIReviewSubject", _subject_payload())
    validator = _hashed(api, "AIValidatorRun", _validator_payload(subject))
    attempts = []
    for number in range(1, 4):
        payload = _attempt_payload(api, policy, subject)
        payload.update(
            pass_id=f"pass-{number}",
            fresh_context_id=f"fresh-context-{number}",
        )
        attempts.append(_hashed(api, "AIReviewAttempt", payload))

    aggregate = api.build_ai_review_aggregate(
        policy=policy,
        subjects=(subject,),
        validator_runs=(validator,),
        attempts=tuple(attempts),
        candidate_sha256=subject.candidate_sha256,
        request_sha256="3" * 64,
        validator_manifest_sha256="4" * 64,
        generated_at="2026-08-27T15:02:00Z",
    )
    assert aggregate.total_subjects == 1
    assert aggregate.passing_subjects == 1
    assert aggregate.blocked_subjects == 0
    assert aggregate.decisions[0].status == "ai_review_passed"
    assert aggregate.content_hash == api.ai_review_content_hash(aggregate)

    missing = api.build_ai_review_aggregate(
        policy=policy,
        subjects=(subject,),
        validator_runs=(validator,),
        attempts=tuple(attempts[:2]),
        candidate_sha256=subject.candidate_sha256,
        request_sha256="3" * 64,
        validator_manifest_sha256="4" * 64,
        generated_at="2026-08-27T15:02:00Z",
    )
    assert missing.decisions[0].status == "blocked_uncertainty"
    assert missing.decisions[0].reason_code == "missing-pass"

    failed_payload = _validator_payload(subject)
    failed_payload.update(result="failed", reason_code="curriculum-invalid")
    failed_validator = _hashed(api, "AIValidatorRun", failed_payload)
    failed = api.build_ai_review_aggregate(
        policy=policy,
        subjects=(subject,),
        validator_runs=(failed_validator,),
        attempts=tuple(attempts),
        candidate_sha256=subject.candidate_sha256,
        request_sha256="3" * 64,
        validator_manifest_sha256="4" * 64,
        generated_at="2026-08-27T15:02:00Z",
    )
    assert failed.decisions[0].status == "ai_review_failed"
    assert failed.decisions[0].reason_code == "deterministic-validator-failed"


def test_any_disagreement_or_uncertainty_blocks_without_majority_override() -> None:
    api = _api()
    policy = _hashed(api, "AIReviewPolicy", _policy_payload())
    subject = _hashed(api, "AIReviewSubject", _subject_payload())
    validator = _hashed(api, "AIValidatorRun", _validator_payload(subject))
    attempts = []
    for number in range(1, 4):
        payload = _attempt_payload(api, policy, subject)
        payload.update(
            pass_id=f"pass-{number}",
            fresh_context_id=f"fresh-context-{number}",
        )
        if number == 3:
            claim = payload["decisions"][0]["atomic_claims"][0]
            claim.update(
                verdict="failed", reason_code="linguistic-error"
            )
            claim["content_hash"] = api.ai_review_content_hash(claim)
            decision = payload["decisions"][0]
            decision.update(status="ai_review_failed", reason_code="atomic-claim-failed")
            decision["content_hash"] = api.ai_review_content_hash(decision)
        attempts.append(_hashed(api, "AIReviewAttempt", payload))
    aggregate = api.build_ai_review_aggregate(
        policy=policy,
        subjects=(subject,),
        validator_runs=(validator,),
        attempts=tuple(attempts),
        candidate_sha256=subject.candidate_sha256,
        request_sha256="3" * 64,
        validator_manifest_sha256="4" * 64,
        generated_at="2026-08-27T15:02:00Z",
    )
    assert aggregate.decisions[0].status == "blocked_disagreement"
    assert aggregate.decisions[0].reason_code == "review-disagreement"


def test_exhausted_review_slot_blocks_every_affected_subject_explicitly() -> None:
    api = _api()
    policy = _hashed(api, "AIReviewPolicy", _policy_payload())
    subject = _hashed(api, "AIReviewSubject", _subject_payload())
    validator = _hashed(api, "AIValidatorRun", _validator_payload(subject))

    aggregate = api.build_ai_review_aggregate(
        policy=policy,
        subjects=(subject,),
        validator_runs=(validator,),
        attempts=(),
        candidate_sha256=subject.candidate_sha256,
        request_sha256="3" * 64,
        validator_manifest_sha256="4" * 64,
        generated_at="2026-08-27T15:02:00Z",
        exhausted_subject_ids=(subject.subject_id,),
    )

    assert aggregate.total_subjects == 1
    assert aggregate.passing_subjects == 0
    assert aggregate.blocked_subjects == 1
    assert aggregate.decisions[0].status == "blocked_uncertainty"
    assert aggregate.decisions[0].reason_code == "attempt-cap-exhausted"


def test_cli_exposes_only_fixed_operations_and_no_network_or_provider_imports() -> None:
    path = Path("scripts/review_korean_foundations_ai.py")
    assert path.exists()
    source = path.read_text(encoding="utf-8").casefold()
    for operation in ("project", "ingest-pass", "status", "aggregate", "verify", "record-lane"):
        assert operation in source
    for forbidden in ("requests", "httpx", "openai", "anthropic", "litellm", "shell=true"):
        assert forbidden not in source
    assert "max_attempts" in source
    assert "max_concurrent_invocations" in source
    assert "not_applicable" in source


def test_fixed_projection_balances_all_subjects_below_the_input_token_ceiling() -> None:
    path = Path("scripts/review_korean_foundations_ai.py")
    spec = util.spec_from_file_location("_review_korean_foundations_ai_test", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    subjects = module._build_subjects()
    batches = module._balanced_review_batches(subjects)

    assert len(batches) == 7
    assert sorted(len(batch) for batch in batches) == [19, 20, 20, 20, 20, 20, 20]
    assert {subject.subject_id for batch in batches for subject in batch} == {
        subject.subject_id for subject in subjects
    }
    assert sum(len(batch) for batch in batches) == 139

    for index, batch in enumerate(batches, start=1):
        projection = module._projection_document(module._batch_id(index), batch)
        assert module._projection_token_count(projection) <= (
            module.MAX_INPUT_TOKENS - module.MAX_AGENT_OVERHEAD_TOKENS
        )
        assert all(
            set(projected) == {
                "subject_id",
                "claim_ids",
                "source_reference_ids",
                "claim_evidence",
                "projection",
            }
            for projected in projection["subjects"]
        )
        assert projection["output_schema"]["reason_codes"] == [
            "none",
            "atomic-claim-failed",
            "uncertainty-present",
            "unsupported-evidence",
            "low-confidence",
            "linguistic-error",
            "curriculum-invalid",
        ]
        assert projection["output_schema"]["uncertainty_codes"] == [
            "source-insufficient",
            "linguistic-ambiguity",
            "confidence-below-threshold",
        ]
        assert projection["output_schema"]["compact_keys"] == {
            "v": "schema_version",
            "b": "batch_id",
            "p": "pass_id",
            "d": "decisions",
            "s": "subject_id",
            "a": "atomic_claims",
            "i": "claim_id",
            "c": "confidence",
            "r": "reason_code",
            "u": "uncertainty_codes",
            "e": "evidence_reference_ids",
        }
        assert module._maximum_compact_output_tokens(projection) <= (
            module.MAX_OUTPUT_TOKENS
        )


def test_failed_attempt_ledger_preserves_raw_bytes_and_marks_two_attempts_exhausted(
    tmp_path: Path,
) -> None:
    path = Path("scripts/review_korean_foundations_ai.py")
    spec = util.spec_from_file_location("_review_korean_foundations_ai_failure_test", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EVIDENCE_ROOT = tmp_path
    module.ATTEMPTS_ROOT = tmp_path / "attempts"
    module.FAILED_ATTEMPTS_ROOT = tmp_path / "failed-attempts"
    tmp_path.mkdir(exist_ok=True)

    raw_path = tmp_path / "raw.json"
    raw_path.write_bytes(b'{"malformed":true}\n')
    base = {
        "input": raw_path,
        "batch_id": "batch-01",
        "pass_id": "pass-1",
        "actor_id": "review-agent",
        "route_id": "opencode-cli-tool-less",
        "provider_id": "openai",
        "provider_api_version": "opencode-1.18.25",
        "model_id": "gpt-5.6-sol",
        "model_version": "gpt-5.6-sol",
        "prompt_id": "korean-foundation-linguistic-review",
        "prompt_version": "1",
        "prompt_template_sha256": "1" * 64,
        "independence_scope": "fresh_context_same_model",
        "started_at": "2026-08-28T11:19:38Z",
    }
    for attempt_number in (1, 2):
        args = SimpleNamespace(
            **base,
            attempt_number=attempt_number,
            fresh_context_id=f"fresh-{attempt_number}",
        )
        module._record_failed_attempt(args, "result_schema_invalid")

    failures = module._load_failed_attempts()
    assert len(failures) == 2
    assert failures[0].raw_result_base64 == "eyJtYWxmb3JtZWQiOnRydWV9Cg=="
    assert module._exhausted_slots(failures) == {("batch-01", "pass-1")}


def test_compact_raw_pass_schema_rebuilds_for_ingestion() -> None:
    path = Path("scripts/review_korean_foundations_ai.py")
    spec = util.spec_from_file_location("_review_korean_foundations_ai_raw_test", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    raw = module._RawPass.model_validate(
        {
            "v": 1,
            "b": "batch-01",
            "p": "pass-1",
            "d": [
                {
                    "s": "ko-hangul-0001",
                    "a": [
                        {
                            "i": "source_content.mapping",
                            "v": "u",
                            "c": 0.8,
                            "r": "s",
                            "u": ["s"],
                            "e": ["unicode.hangul-17.0"],
                        }
                    ],
                }
            ],
        }
    )

    assert raw.batch_id == "batch-01"
    assert raw.decisions[0].atomic_claims[0].reason_code == "s"


def test_projection_claims_are_linguistic_and_locally_reviewable() -> None:
    path = Path("scripts/review_korean_foundations_ai.py")
    spec = util.spec_from_file_location("_review_korean_foundations_ai_scope_test", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    subjects = module._build_subjects()
    for subject in subjects:
        if subject.family == "hangul":
            assert subject.claim_ids == (
                "source_content.fields",
                "curriculum_atomicity.evidence",
                "korean_orthography.fields",
                "portuguese.learner-facing-portuguese",
            )
        else:
            assert subject.claim_ids == (
                "source_content.fields",
                "curriculum_atomicity.evidence",
                "korean_phonetics.fields",
                "portuguese.translations",
            )
        assert "source_content.stroke-order" not in subject.claim_ids

    projection = module._projection_document("batch-01", subjects[:1])
    claim_evidence = projection["subjects"][0]["claim_evidence"]
    assert claim_evidence["curriculum_atomicity.evidence"]["basis"] == (
        "deterministic-curriculum-validators"
    )
    phonetics_fields = module._claim_projection_fields("korean_phonetics.fields")
    assert phonetics_fields == (
        "spellings",
        "sound",
        "pronunciation_evidence.canonical_spelling",
        "pronunciation_evidence.normative_pronunciation",
        "pronunciation_evidence.surface_pronunciation",
        "pronunciation_evidence.ipa",
    )
    assert "phonological_rule_ids" not in phonetics_fields
    assert "active_rule_ids" not in phonetics_fields
    assert "internal linguistic competence" in projection["review_instruction"]
    assert "Internal curriculum taxonomy names" in projection["review_instruction"]
    assert "no tools, files, network" in projection["security_boundary"]


def test_pronunciation_review_projection_contains_no_placeholder_linguistic_fields() -> None:
    path = Path("scripts/review_korean_foundations_ai.py")
    spec = util.spec_from_file_location(
        "_review_korean_foundations_ai_placeholder_test", path
    )
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    subjects = module._build_subjects()
    for subject in subjects:
        if subject.family != "pronunciation":
            continue
        projection = subject.projection
        pronunciation_evidence = projection["pronunciation_evidence"]
        checked = (
            projection["spellings"],
            projection["sound"],
            projection["example_word"],
            projection["word_translation"],
            projection["example_sentence"],
            projection["sentence_translation"],
            pronunciation_evidence["canonical_spelling"],
            pronunciation_evidence["normative_pronunciation"],
            pronunciation_evidence["surface_pronunciation"],
        )
        assert "needs_review" not in checked, subject.subject_id
