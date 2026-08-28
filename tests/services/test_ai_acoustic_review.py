from __future__ import annotations

from hashlib import sha256
from importlib import import_module, util
import json
from types import ModuleType

import pytest
from pydantic import ValidationError


def _acoustic() -> ModuleType:
    assert util.find_spec("multilang.services.ai_acoustic_review") is not None, (
        "the AI acoustic review contract module must exist"
    )
    return import_module("multilang.services.ai_acoustic_review")


def _hash(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _decision_payload(api: ModuleType) -> dict[str, object]:
    audio_hash = "a" * 64
    validator_run = {
        "validator_id": "wav-decoder",
        "validator_version": "v1",
        "result": "passed",
        "subject_sha256": audio_hash,
        "content_hash": "0" * 64,
    }
    validator_run["content_hash"] = api.ai_acoustic_review_sha256(validator_run)
    payload: dict[str, object] = {
        "schema_version": 1,
        "policy_id": "phase31-ai-acoustic-review",
        "policy_version": "2026-08-28",
        "policy_sha256": "b" * 64,
        "actor_type": "ai_model",
        "is_human": False,
        "route": "opencode-tool-less-reviewer",
        "provider_id": "openai",
        "provider_api_version": "responses-2026-08-28",
        "model_id": "gpt-5.5",
        "model_version": "2026-08-28",
        "prompt_id": "phase31-acoustic-pass",
        "prompt_version": "v1",
        "prompt_template_sha256": "c" * 64,
        "output_schema_id": "phase31-ai-acoustic-review-decision",
        "output_schema_version": "v1",
        "output_schema_sha256": "d" * 64,
        "source_content_sha256": "e" * 64,
        "candidate_content_sha256": "f" * 64,
        "analyzer_content_sha256": "1" * 64,
        "curriculum_content_sha256": "2" * 64,
        "media_manifest_sha256": "3" * 64,
        "validator_runs": [validator_run],
        "atomic_gate_verdict": "passed",
        "final_consensus_status": "passing",
        "reason_codes": [],
        "uncertainty_codes": [],
        "confidence": 0.91,
        "pass_id": "batch-01-pass-1",
        "independence_scope": "fresh-context-no-tools",
        "orchestration_started_at": "2026-08-28T00:00:00Z",
        "orchestration_completed_at": "2026-08-28T00:00:01Z",
        "slot_id": "hangul.a.audio",
        "display_text_nfc": "아",
        "spoken_text_nfc": "아",
        "text_sha256": _hash("아"),
        "synthesis_request_sha256": "4" * 64,
        "synthesis_provider_id": "azure-speech-service",
        "synthesis_provider_version": "azure-docs-2026-08-13-ebc37366082bd4d002282e679e4fc07099083d5b",
        "voice_profile_id": "ko-KR-SunHiNeural",
        "voice_profile_version": "azure-docs-2026-08-13-ebc37366082bd4d002282e679e4fc07099083d5b",
        "locale": "ko-KR",
        "ssml_sha256": "5" * 64,
        "prosody_sha256": "6" * 64,
        "output_format": "pcm_s16le_wav",
        "duration_ms": 900,
        "repository_relpath": ".planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/media/hangul-a-audio.wav",
        "artifact_sha256": audio_hash,
        "reviewed_artifact_sha256": audio_hash,
        "actual_byte_sha256": audio_hash,
    }
    payload["canonical_content_hash"] = api.ai_acoustic_review_sha256(payload)
    return payload


def test_ai_acoustic_review_decision_rejects_human_claims_and_byte_drift() -> None:
    api = _acoustic()
    valid = _decision_payload(api)
    assert api.AIAcousticReviewDecision.model_validate(valid).actor_type == "ai_model"

    human = dict(valid)
    human["actor_type"] = "human"
    human["is_human"] = True
    human["canonical_content_hash"] = api.ai_acoustic_review_sha256(human)
    with pytest.raises(ValidationError):
        api.AIAcousticReviewDecision.model_validate(human)

    drifted = dict(valid)
    drifted["actual_byte_sha256"] = "9" * 64
    drifted["canonical_content_hash"] = api.ai_acoustic_review_sha256(drifted)
    with pytest.raises(ValidationError):
        api.AIAcousticReviewDecision.model_validate(drifted)


def test_blocked_acoustic_aggregate_requires_exact_counts_and_hash() -> None:
    api = _acoustic()
    payload = {
        "schema_version": 1,
        "phase": "31-hangul-and-pronunciation-i-plus-1",
        "status": "blocked",
        "media_rights_sha256": "a" * 64,
        "media_authority_sha256": "b" * 64,
        "item_set_sha256": "c" * 64,
        "required_slots": 325,
        "audio_subjects": 233,
        "visual_subjects": 92,
        "passing": 0,
        "blocked": 325,
        "blockers": [
            {
                "slot_id": "hangul.a.audio",
                "media_kind": "audio",
                "reason_code": "azure_speech_credentials_missing",
            }
        ],
    }
    payload["aggregate_root"] = api.ai_acoustic_review_sha256(payload)

    aggregate = api.AIAcousticReviewAggregate.model_validate(payload)
    assert aggregate.status == "blocked"

    changed = dict(payload)
    changed["audio_subjects"] = 232
    changed["aggregate_root"] = api.ai_acoustic_review_sha256(changed)
    with pytest.raises(ValidationError):
        api.AIAcousticReviewAggregate.model_validate(changed)
