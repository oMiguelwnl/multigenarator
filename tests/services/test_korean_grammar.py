"""Service contracts for Korean grammar roots, overlays, and strict evidence."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
import json
from types import SimpleNamespace

import pytest

from multilang.domain.korean import KoreanConcept


SHA = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _grammar_service():
    assert util.find_spec("multilang.services.korean_grammar") is not None, (
        "the Korean grammar service module must exist"
    )
    return import_module("multilang.services.korean_grammar")


def _grammar_domain():
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


def _source_binding(*, synthetic: bool = False) -> dict[str, object]:
    return {
        "source_id": "grammar.source",
        "source_version": "2026.08",
        "license_decision": "approved-local-use",
        "entry_sha256": SHA_B,
        "bundle_sha256": SHA_B,
        "source_backed": True,
        "synthetic": synthetic,
        "content_hash": SHA_B,
    }


def _review_binding(*, status: str = "ai_review_passed", passes: tuple[str, ...] = ("a", "b")) -> dict[str, object]:
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
        "fresh_context_pass_ids": list(passes),
        "required_pass_count": len(passes),
        "consensus_status": status,
        "content_hash": SHA_C,
    }


def _media_binding() -> dict[str, object]:
    return {
        "text_sha256": SHA,
        "request_sha256": SHA,
        "artifact_sha256": SHA,
        "voice_profile_sha256": SHA,
        "integrity_status": "passed",
        "acoustic_review_status": "ai_acoustic_review_passed",
        "content_hash": SHA,
    }


def _bootstrap(
    target: str = "lexicon:annyeonghaseyo",
    *,
    sequence: int = 1,
    source: dict[str, object] | None = None,
):
    api = _grammar_domain()
    return api.KoreanGrammarBootstrapEntry(
        **_sealed(
            {
                "entry_id": f"bootstrap.{sequence:03d}",
                "sequence": sequence,
                "target_concept_id": target,
                "lexical_identity_sha256": SHA,
                "submitted_form": "안녕하세요",
                "canonical_nfc": "안녕하세요",
                "source_binding": source or _source_binding(),
                "observed_concept_ids": ["orthography.hangul", target],
                "prerequisite_concept_ids": ["orthography.hangul"],
                "learner_visible": True,
            }
        )
    )


def _grammar_entry(
    target: str = "grammar:topic-particle-eun-neun",
    *,
    sequence: int = 1,
    prerequisites: tuple[str, ...] = (
        "orthography.hangul",
        "phonology.basic",
        "lexicon:annyeonghaseyo",
    ),
    observed: tuple[str, ...] | None = None,
    unknown: tuple[str, ...] | None = None,
    policy: str = "strict",
    category_id: str = "G1",
    review: dict[str, object] | None = None,
    ready_state: str = "learner_ready",
):
    api = _grammar_domain()
    observed_ids = observed or (*prerequisites, target)
    unknown_ids = unknown or (target,)
    return api.KoreanGrammarEntry(
        **_sealed(
            {
                "entry_id": f"grammar.{sequence:03d}",
                "sequence": sequence,
                "category_id": category_id,
                "target_concept_id": target,
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
                    "target_concept_id": target,
                    "prerequisite_concept_ids": list(prerequisites),
                    "observed_concept_ids": list(observed_ids),
                    "unknown_concept_ids": list(unknown_ids),
                    "policy": policy,
                },
                "review_binding": review or _review_binding(),
                "word_media_binding": _media_binding(),
                "sentence_media_binding": _media_binding(),
                "ready_state": ready_state,
            }
        )
    )


def _snapshot(*, source_kind: str = "active-approved-snapshot") -> SimpleNamespace:
    registry = SimpleNamespace(
        concepts=(
            KoreanConcept(
                id="orthography.hangul",
                domain="orthography",
                prerequisite_ids=(),
                sequence=1,
            ),
            KoreanConcept(
                id="phonology.basic",
                domain="phonology",
                prerequisite_ids=("orthography.hangul",),
                sequence=2,
            ),
        )
    )
    members = (
        SimpleNamespace(role="concept_registry", sha256=SHA_C),
        SimpleNamespace(role="hangul_source_pack", sha256=SHA),
    )
    return SimpleNamespace(
        source_kind=source_kind,
        bundle_sha256=SHA,
        receipt_sha256=SHA,
        snapshot_manifest_sha256=SHA,
        snapshot_root_sha256=SHA,
        concept_registry=registry,
        members=members,
    )


def test_resolve_once_binds_active_root_and_imported_concepts_are_immutable() -> None:
    service = _grammar_service()
    calls = 0

    def resolver():
        nonlocal calls
        calls += 1
        return _snapshot()

    bundle = service.KoreanGrammarBundleBuilder(active_snapshot_resolver=resolver).build_bundle(
        lexical_bootstrap=(_bootstrap(),),
        grammar_entries=(_grammar_entry(),),
    )

    assert calls == 1
    assert bundle.phase31_binding.concept_registry_member_sha256 == SHA_C
    assert bundle.phase31_binding.imported_concept_ids == (
        "orthography.hangul",
        "phonology.basic",
    )
    with pytest.raises(Exception):
        bundle.imported_concepts[0].sequence = 99


@pytest.mark.parametrize(
    "source_kind",
    ["current-candidate", "v1-history", "request-only", "test-fixture"],
)
def test_candidate_history_or_test_snapshots_fail_closed(source_kind: str) -> None:
    service = _grammar_service()

    with pytest.raises(service.KoreanGrammarError) as exc_info:
        service.KoreanGrammarBundleBuilder(
            active_snapshot_resolver=lambda: _snapshot(source_kind=source_kind)
        ).build_bundle(lexical_bootstrap=(_bootstrap(),), grammar_entries=(_grammar_entry(),))

    assert exc_info.value.reason_code.value == "phase31_not_active"


def test_overlay_rejects_collision_cycle_forward_edges_and_incomplete_closure() -> None:
    service = _grammar_service()
    builder = service.KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot)

    with pytest.raises(service.KoreanGrammarError) as collision:
        builder.build_bundle(
            lexical_bootstrap=(_bootstrap(sequence=1), _bootstrap(sequence=2)),
            grammar_entries=(_grammar_entry(),),
        )
    assert collision.value.reason_code.value == "concept_collision"

    cyclic_entry = _grammar_entry(
        prerequisites=(
            "orthography.hangul",
            "phonology.basic",
            "lexicon:annyeonghaseyo",
            "grammar:connective-go",
        ),
        observed=(
            "orthography.hangul",
            "phonology.basic",
            "lexicon:annyeonghaseyo",
            "grammar:connective-go",
            "grammar:topic-particle-eun-neun",
        ),
    )
    other_entry = _grammar_entry(
        target="grammar:connective-go",
        sequence=2,
        prerequisites=(
            "orthography.hangul",
            "phonology.basic",
            "lexicon:annyeonghaseyo",
            "grammar:topic-particle-eun-neun",
        ),
        observed=(
            "orthography.hangul",
            "phonology.basic",
            "lexicon:annyeonghaseyo",
            "grammar:topic-particle-eun-neun",
            "grammar:connective-go",
        ),
        unknown=("grammar:connective-go",),
    )
    with pytest.raises(service.KoreanGrammarError) as cycle:
        builder.build_bundle(
            lexical_bootstrap=(_bootstrap(),),
            grammar_entries=(cyclic_entry, other_entry),
        )
    assert cycle.value.reason_code.value == "concept_cycle"

    with pytest.raises(service.KoreanGrammarError) as forward:
        builder.build_bundle(
            lexical_bootstrap=(_bootstrap(),),
            grammar_entries=(cyclic_entry,),
        )
    assert forward.value.reason_code.value == "forward_dependency"

    missing_closure = _grammar_entry(prerequisites=("phonology.basic", "lexicon:annyeonghaseyo"))
    with pytest.raises(service.KoreanGrammarError) as closure:
        builder.build_bundle(
            lexical_bootstrap=(_bootstrap(),),
            grammar_entries=(missing_closure,),
        )
    assert closure.value.reason_code.value == "incomplete_closure"


def test_strict_recomputes_exactly_one_unknown_after_bootstrap() -> None:
    service = _grammar_service()
    bundle = service.KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=(_bootstrap(),),
        grammar_entries=(_grammar_entry(),),
    )

    result = service.validate_korean_grammar_strict_graph(bundle)

    assert result.ready_state == "learner_ready"
    assert result.admitted_bootstrap_concept_ids == ("lexicon:annyeonghaseyo",)
    assert result.admitted_grammar_concept_ids == ("grammar:topic-particle-eun-neun",)
    assert result.blocked_reason_codes == ()


@pytest.mark.parametrize(
    ("entry", "reason"),
    [
        (_grammar_entry(policy="adaptive"), "strict_policy_required"),
        (
            _grammar_entry(
                observed=(
                    "orthography.hangul",
                    "phonology.basic",
                    "lexicon:annyeonghaseyo",
                    "grammar:topic-particle-eun-neun",
                    "grammar:hidden-register",
                )
            ),
            "exactly_one_unknown_required",
        ),
        (
            _grammar_entry(unknown=("grammar:serialized-lie",)),
            "serialized_unknown_mismatch",
        ),
        (
            _grammar_entry(category_id="speech-levels"),
            "broad_target_category",
        ),
    ],
)
def test_hidden_broad_serialized_or_non_strict_evidence_blocks(entry, reason: str) -> None:
    service = _grammar_service()

    with pytest.raises(service.KoreanGrammarError) as exc_info:
        service.KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
            lexical_bootstrap=(_bootstrap(),),
            grammar_entries=(entry,),
        )

    assert exc_info.value.reason_code.value == reason


def test_review_cannot_override_graph_failure_and_synthetic_readiness_stays_blocked() -> None:
    service = _grammar_service()
    builder = service.KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot)
    bad_graph_entry = _grammar_entry(
        observed=(
            "orthography.hangul",
            "phonology.basic",
            "lexicon:annyeonghaseyo",
            "grammar:topic-particle-eun-neun",
            "grammar:hidden-register",
        ),
        review=_review_binding(status="ai_review_passed", passes=("a", "b", "c")),
    )

    with pytest.raises(service.KoreanGrammarError) as exc_info:
        builder.build_bundle(
            lexical_bootstrap=(_bootstrap(),),
            grammar_entries=(bad_graph_entry,),
        )
    assert exc_info.value.reason_code.value == "exactly_one_unknown_required"

    synthetic_bundle = builder.build_bundle(
        lexical_bootstrap=(_bootstrap(source=_source_binding(synthetic=True)),),
        grammar_entries=(_grammar_entry(ready_state="blocked"),),
    )
    result = service.validate_korean_grammar_production_readiness(synthetic_bundle)

    assert result.ready_state == "blocked"
    assert "synthetic_source" in result.blocked_reason_codes
