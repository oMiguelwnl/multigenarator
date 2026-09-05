"""Contracts for immutable Korean grammar bundles and readiness gates."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
import json
import unicodedata

import pytest
from pydantic import ValidationError


SHA = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _grammar():
    assert util.find_spec("multilang.domain.korean_grammar") is not None, (
        "the Korean grammar domain contract module must exist"
    )
    return import_module("multilang.domain.korean_grammar")


def _canonical_hash(payload: object) -> str:
    data = deepcopy(payload)
    if isinstance(data, dict):
        data.pop("content_hash", None)
    encoded = json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _sealed(payload: dict[str, object]) -> dict[str, object]:
    result = deepcopy(payload)
    result["content_hash"] = _canonical_hash(result)
    return result


def _phase31_binding(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_kind": "active-approved-snapshot",
        "bundle_sha256": SHA,
        "receipt_sha256": SHA,
        "snapshot_manifest_sha256": SHA,
        "snapshot_root_sha256": SHA,
        "concept_registry_member_sha256": SHA,
        "imported_concept_ids": ["orthography.hangul", "phonology.basic"],
        "content_hash": SHA,
    }
    payload.update(overrides)
    return payload


def _source_binding(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_id": "grammar.bootstrap.source",
        "source_version": "2026.08",
        "license_decision": "approved-local-use",
        "entry_sha256": SHA_B,
        "bundle_sha256": SHA_B,
        "source_backed": True,
        "synthetic": False,
        "content_hash": SHA_B,
    }
    payload.update(overrides)
    return payload


def _review_binding(*, consensus_status: str = "ai_review_passed") -> dict[str, object]:
    return {
        "policy_id": "multilang-ai-linguistic-review-v1",
        "policy_sha256": SHA,
        "actor_type": "ai_model",
        "is_human": False,
        "provider": "offline-fixture",
        "model_id": "fixture-reviewer",
        "route_sha256": SHA,
        "prompt_sha256": SHA,
        "output_schema_sha256": SHA,
        "source_sha256": SHA_B,
        "candidate_sha256": SHA_B,
        "analyzer_sha256": SHA_B,
        "curriculum_sha256": SHA_B,
        "media_sha256": SHA_C,
        "deterministic_validator_ids": ["grammar-schema-v1", "strict-i-plus-1-v1"],
        "deterministic_validator_result": "passed",
        "fresh_context_pass_ids": ["pass-a", "pass-b"],
        "required_pass_count": 2,
        "consensus_status": consensus_status,
        "content_hash": SHA_C,
    }


def _media_binding(*, acoustic_status: str = "ai_acoustic_review_passed") -> dict[str, object]:
    return {
        "text_sha256": SHA,
        "request_sha256": SHA,
        "artifact_sha256": SHA,
        "voice_profile_sha256": SHA,
        "integrity_status": "passed",
        "acoustic_review_status": acoustic_status,
        "content_hash": SHA,
    }


def _bootstrap_entry(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "entry_id": "bootstrap.001",
        "sequence": 1,
        "target_concept_id": "lexicon:annyeonghaseyo",
        "lexical_identity_sha256": SHA,
        "submitted_form": "안녕하세요",
        "canonical_nfc": "안녕하세요",
        "source_binding": _source_binding(),
        "observed_concept_ids": ["orthography.hangul", "lexicon:annyeonghaseyo"],
        "prerequisite_concept_ids": ["orthography.hangul"],
        "learner_visible": True,
        "content_hash": SHA,
    }
    payload.update(overrides)
    return payload


def _grammar_entry(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "entry_id": "grammar.001",
        "sequence": 1,
        "category_id": "G1",
        "target_concept_id": "grammar:topic-particle-eun-neun",
        "construction_label": "topic-particle-eun-neun",
        "form": "은/는",
        "function": "marca o tópico já estabelecido da frase",
        "attachment_rule": "Use 은 depois de consoante final e 는 depois de vogal.",
        "register": "해요체",
        "example_sentence": "저는 학생이에요.",
        "portuguese_translation": "Eu sou estudante.",
        "pronunciation_sample": "저는",
        "spoken_sample": "저는",
        "source_binding": _source_binding(),
        "evidence": {
            "target_concept_id": "grammar:topic-particle-eun-neun",
            "prerequisite_concept_ids": [
                "orthography.hangul",
                "phonology.basic",
                "lexicon:annyeonghaseyo",
            ],
            "observed_concept_ids": [
                "orthography.hangul",
                "phonology.basic",
                "lexicon:annyeonghaseyo",
                "grammar:topic-particle-eun-neun",
            ],
            "unknown_concept_ids": ["grammar:topic-particle-eun-neun"],
            "policy": "strict",
        },
        "review_binding": _review_binding(),
        "word_media_binding": _media_binding(),
        "sentence_media_binding": _media_binding(),
        "ready_state": "learner_ready",
        "content_hash": SHA,
    }
    payload.update(overrides)
    return _sealed(payload)


def test_frozen_binding_requires_exact_active_phase31_hashes() -> None:
    api = _grammar()

    binding = api.Phase31GrammarRootBinding(**_phase31_binding())

    assert binding.source_kind == "active-approved-snapshot"
    assert binding.imported_concept_ids == ("orthography.hangul", "phonology.basic")
    with pytest.raises(ValidationError):
        binding.bundle_sha256 = SHA_B
    with pytest.raises(ValidationError):
        api.Phase31GrammarRootBinding(**_phase31_binding(source_kind="current-candidate"))
    with pytest.raises(ValidationError):
        api.Phase31GrammarRootBinding(**_phase31_binding(receipt_sha256=None))


def test_bootstrap_is_source_backed_visible_and_not_preknown() -> None:
    api = _grammar()

    bootstrap = api.KoreanGrammarBootstrapEntry(**_bootstrap_entry())

    assert bootstrap.learner_visible is True
    assert bootstrap.target_concept_id.startswith("lexicon:")
    assert bootstrap.target_concept_id not in bootstrap.prerequisite_concept_ids
    assert bootstrap.canonical_nfc == "안녕하세요"
    with pytest.raises(ValidationError):
        api.KoreanGrammarBootstrapEntry(**_bootstrap_entry(learner_visible=False))
    with pytest.raises(ValidationError):
        api.KoreanGrammarBootstrapEntry(
            **_bootstrap_entry(source_binding={**_source_binding(), "source_backed": False})
        )


def test_structured_fields_keep_review_and_media_bindings_separate() -> None:
    api = _grammar()

    entry = api.KoreanGrammarEntry(**_grammar_entry())

    assert entry.form == "은/는"
    assert entry.function.startswith("marca")
    assert entry.review_binding.policy_id == "multilang-ai-linguistic-review-v1"
    assert entry.word_media_binding.artifact_sha256 == SHA
    assert entry.sentence_media_binding.artifact_sha256 == SHA
    assert entry.evidence.policy == "strict"
    assert entry.content_hash == _canonical_hash(entry.model_dump(mode="json", by_alias=True))


def test_hashes_and_payloads_are_canonical_and_forbid_unknown_fields() -> None:
    api = _grammar()

    payload = _grammar_entry()
    assert api.korean_grammar_canonical_json_sha256({"b": 1, "a": "가"}) == (
        api.korean_grammar_canonical_json_sha256({"a": "가", "b": 1})
    )
    with pytest.raises(ValidationError):
        api.KoreanGrammarEntry(**{**payload, "unexpected": True})
    with pytest.raises(ValidationError):
        api.KoreanGrammarEntry(**{**payload, "content_hash": "A" * 64})


@pytest.mark.parametrize(
    "mutation",
    [
        {"ready_state": "learner_ready", "source_binding": {**_source_binding(), "synthetic": True}},
        {"ready_state": "learner_ready", "source_binding": {**_source_binding(), "license_decision": "missing"}},
        {"ready_state": "learner_ready", "review_binding": _review_binding(consensus_status="blocked_disagreement")},
        {"ready_state": "learner_ready", "word_media_binding": _media_binding(acoustic_status="stale")},
        {"ready_state": "learner_ready", "sentence_media_binding": _media_binding(acoustic_status="stale")},
    ],
)
def test_production_gate_blocks_synthetic_missing_review_or_missing_media(
    mutation: dict[str, object],
) -> None:
    api = _grammar()

    with pytest.raises(ValidationError):
        api.KoreanGrammarEntry(**_grammar_entry(**mutation))


def test_non_nfc_or_wrong_language_payloads_are_rejected() -> None:
    api = _grammar()
    decomposed = unicodedata.normalize("NFD", "학생이에요")

    with pytest.raises(ValidationError):
        api.KoreanGrammarEntry(**_grammar_entry(example_sentence=decomposed))
    with pytest.raises(ValidationError):
        api.KoreanGrammarEntry(**_grammar_entry(example_sentence="This is English."))
