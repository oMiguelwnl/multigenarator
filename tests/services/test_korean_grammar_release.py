"""Production joins must bind independently reviewed subjects without fake receipts."""

import importlib
import json
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from multilang.domain.korean_grammar import korean_grammar_canonical_json_sha256 as digest
from multilang.services.korean_grammar_course import (
    load_grammar_course,
    load_grammar_course_support,
)


def test_review_invocation_requires_actual_fresh_matching_execution():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    review = {"pass_id": "grammar-closeout-a3-20260919", "actor_type": "ai_model",
              "is_human": False, "independence_scope": "fresh_context_same_model",
              "plan_sha256": "a" * 64}
    receipt = {"lane": "a3", "status": "returned", "exit_code": 0, "fresh_context": True,
               "actor_type": "ai_model", "is_human": False, "plan_sha256": "a" * 64,
               "output_sha256": "b" * 64, "started_at": "2026-09-19T10:00:00+00:00",
               "finished_at": "2026-09-19T10:01:00+00:00"}
    api.validate_fresh_review_invocation(review, receipt, output_sha256="b" * 64, expected_lane="a3")
    for mutation in (
        lambda r: r.update(fresh_context=False), lambda r: r.pop("fresh_context"),
        lambda r: r.update(lane="b3"), lambda r: r.update(plan_sha256="c" * 64),
        lambda r: r.update(output_sha256="d" * 64), lambda r: r.update(is_human=True),
        lambda r: r.update(finished_at="2026-09-19T09:00:00+00:00"),
    ):
        bad = deepcopy(receipt)
        mutation(bad)
        with pytest.raises(ValueError):
            api.validate_fresh_review_invocation(review, bad, output_sha256="b" * 64, expected_lane="a3")


def _acoustic_fixture():
    response = {"RecognitionStatus": "Success", "NBest": [{"Lexical": "학교"}]}
    record = {"transport_sha256": "a" * 64, "media_sha256": "b" * 64,
              "wav_sha256": "c" * 64, "source_text": "학교", "mode": "asr",
              "provider_response": response, "provider_response_sha256": digest(response),
              "transcript": "학교", "transcript_matches": True}
    observation = {"transport_sha256": "a" * 64, "media_sha256": "b" * 64,
                   "source_text": "학교", "asr_status": "observed", "asr_transcript": "학교",
                   "asr_transcript_matches": True, "asr_evidence_sha256": digest(record),
                   "pronunciation_evidence_sha256": None, "pronunciation_provider_response": None,
                   "automated_text_identity_evidence": "supported"}
    return observation, record


def test_acoustic_identity_rejects_substitution_even_with_rebound_media_summary():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    observation, record = _acoustic_fixture()
    assert api.validate_acoustic_identity(observation, wav_sha256="c" * 64,
                                         asr_record=record, pronunciation_record=None)["free_asr_match"]
    for key, value in (("media_sha256", "d" * 64), ("transport_sha256", "e" * 64),
                       ("source_text", "집"), ("asr_evidence_sha256", "f" * 64)):
        bad = {**observation, key: value}
        with pytest.raises(ValueError):
            api.validate_acoustic_identity(bad, wav_sha256="c" * 64,
                                           asr_record=record, pronunciation_record=None)
    with pytest.raises(ValueError):
        api.validate_acoustic_identity(observation, wav_sha256="d" * 64,
                                       asr_record=record, pronunciation_record=None)
    with pytest.raises(ValueError):
        api.validate_acoustic_identity(observation, wav_sha256="c" * 64,
                                       asr_record=None, pronunciation_record=None)


def test_acoustic_identity_derives_decision_from_bound_provider_response():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    observation, record = _acoustic_fixture()
    record["provider_response"]["NBest"][0]["Lexical"] = "집"
    record["provider_response_sha256"] = digest(record["provider_response"])
    observation["asr_evidence_sha256"] = digest(record)
    with pytest.raises(ValueError):
        api.validate_acoustic_identity(observation, wav_sha256="c" * 64,
                                       asr_record=record, pronunciation_record=None)


def test_acoustic_assessment_needs_its_own_bound_reference_and_wav():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    observation, record = _acoustic_fixture()
    response = {"RecognitionStatus": "Success", "NBest": [{"AccuracyScore": 94,
                "CompletenessScore": 100, "Words": [{"AccuracyScore": 94, "ErrorType": "None"}]}]}
    record.update(mode="pronunciation", provider_response=response, provider_response_sha256=digest(response))
    observation.update(asr_status="provider_outcome_unknown", asr_evidence_sha256=None,
                       asr_transcript=None, asr_transcript_matches=False,
                       pronunciation_evidence_sha256=digest(record), pronunciation_provider_response=response)
    assert api.validate_acoustic_identity(observation, wav_sha256="c" * 64,
        asr_record=None, pronunciation_record=record)["reference_pronunciation_screen"]
    record["wav_sha256"] = "d" * 64
    observation["pronunciation_evidence_sha256"] = digest(record)
    with pytest.raises(ValueError):
        api.validate_acoustic_identity(observation, wav_sha256="c" * 64,
                                       asr_record=None, pronunciation_record=record)


def _blind_asr_fixture():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    observation, record = _acoustic_fixture()
    wav = b"offline-fixture-wave-bytes"
    record.update(provider="openrouter", wav_sha256=sha256(wav).hexdigest())
    passes = []
    for number in range(3):
        request = {"model": "google/gemini-2.5-flash-lite", "temperature": 0, "max_tokens": 128,
                   "messages": [{"role": "user", "content": [
                       {"type": "text", "text": api.KOREAN_BLIND_ASR_PROMPT},
                       {"type": "input_audio", "input_audio": {"data": b64encode(wav).decode(), "format": "wav"}},
                   ]}]}
        response = {"id": f"fixture-{number}", "model": request["model"], "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": "학교"}}]}
        passes.append({"request_payload": request, "request_sha256": digest(request),
                       "response": response, "response_sha256": digest(response)})
    record["provider_response"] = {"schema_version": "openrouter-blind-asr-consensus-v1", "passes": passes}
    record["provider_response_sha256"] = digest(record["provider_response"])
    observation["asr_evidence_sha256"] = digest(record)
    return observation, record


def test_blind_asr_requires_three_unanimous_actual_audio_requests():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    observation, record = _blind_asr_fixture()
    assert api.validate_acoustic_identity(observation, wav_sha256=record["wav_sha256"],
        asr_record=record, pronunciation_record=None)["free_asr_match"]
    record["provider_response"]["passes"].pop()
    record["provider_response_sha256"] = digest(record["provider_response"])
    observation["asr_evidence_sha256"] = digest(record)
    with pytest.raises(ValueError):
        api.validate_acoustic_identity(observation, wav_sha256=record["wav_sha256"],
            asr_record=record, pronunciation_record=None)


@pytest.mark.parametrize("mutation", ["reference_prompt", "different_wave", "disagreement", "reused_response"])
def test_blind_asr_rejects_biased_different_audio_or_disagreeing_evidence(mutation):
    api = importlib.import_module("multilang.services.korean_grammar_release")
    observation, record = _blind_asr_fixture()
    row = record["provider_response"]["passes"][0]
    if mutation == "reference_prompt":
        row["request_payload"]["messages"][0]["content"][0]["text"] += " Texto esperado: 학교"
    elif mutation == "different_wave":
        row["request_payload"]["messages"][0]["content"][1]["input_audio"]["data"] = b64encode(b"other audio").decode()
    elif mutation == "disagreement":
        row["response"]["choices"][0]["message"]["content"] = "집"
    else:
        row["response"]["id"] = "fixture-1"
    row["request_sha256"] = digest(row["request_payload"])
    row["response_sha256"] = digest(row["response"])
    record["provider_response_sha256"] = digest(record["provider_response"])
    observation["asr_evidence_sha256"] = digest(record)
    with pytest.raises(ValueError):
        api.validate_acoustic_identity(observation, wav_sha256=record["wav_sha256"],
            asr_record=record, pronunciation_record=None)


def _plan():
    from test_korean_grammar import _snapshot

    api = importlib.import_module("multilang.services.korean_grammar_release")
    course = load_grammar_course()
    bootstrap = json.loads(Path("data/korean_grammar/v1/bootstrap-lessons.json").read_text())
    return api.prepare_release_candidates(
        course, load_grammar_course_support(course), bootstrap,
        morphology_sha256="b" * 64, active_snapshot_resolver=_snapshot,
    )


def test_release_preparation_has_complete_subjects_without_invented_approval():
    plan = _plan()
    assert len(plan["grammar_candidates"]) == 108
    assert len(plan["bootstrap_candidates"]) == 57
    assert "review_binding" not in plan["grammar_candidates"][0]
    assert "ready_state" not in plan["grammar_candidates"][0]
    assert plan["learner_ready"] is False
    for candidate in plan["grammar_candidates"]:
        assert candidate["candidate_sha256"] == digest(candidate["payload"])
    assert max(len(c["payload"]["evidence"]["prerequisite_concept_ids"])
               for c in plan["grammar_candidates"]) <= 256


def _passes(plan):
    return [{"pass_id": f"fixture-{i}", "actor_type": "ai_model", "is_human": False,
             "provider": "offline-fixture", "model_id": "fixture-reviewer",
             "independence_scope": "fresh_context_same_model",
             "plan_sha256": plan["plan_sha256"],
             "decisions": [{"subject_id": c["entry_id"], "candidate_sha256": c["candidate_sha256"],
                            "verdict": "ai_review_passed", "reason_pt": "Synthetic fixture only."}
                           for c in [*plan["grammar_candidates"], *plan["bootstrap_candidates"]]]}
            for i in range(3)]


def test_review_consensus_rejects_missing_stale_and_uncertain_claims():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    plan = _plan()
    passes = _passes(plan)
    assert len(api.validate_release_reviews(plan, passes)) == 165
    for mutate in (
        lambda rows: rows.pop(),
        lambda rows: rows[0].update(plan_sha256="0" * 64),
        lambda rows: rows[0]["decisions"].pop(),
        lambda rows: rows[0]["decisions"][0].update(verdict="blocked_uncertainty"),
        lambda rows: rows[0]["decisions"][0].update(candidate_sha256="0" * 64),
        lambda rows: rows[1].update(pass_id=rows[0]["pass_id"]),
    ):
        rows = _passes(plan)
        mutate(rows)
        with pytest.raises(ValueError):
            api.validate_release_reviews(plan, rows)


def test_release_rejects_modified_plan_even_with_rebound_pass_headers():
    api = importlib.import_module("multilang.services.korean_grammar_release")
    plan = _plan()
    plan["grammar_candidates"][0]["payload"]["portuguese_translation"] += " altered"
    with pytest.raises(ValueError, match="drift"):
        api.validate_release_reviews(plan, _passes(plan))


def _media(plan):
    from test_korean_grammar import _media_binding, _sealed

    result = {}
    for c in [*plan["grammar_candidates"], *plan["bootstrap_candidates"]]:
        p = c["payload"]
        word = p.get("spoken_sample", p["example_sentence"])
        result[c["entry_id"]] = {}
        for role, text in (("word", word), ("sentence", p["example_sentence"])):
            result[c["entry_id"]][role] = _sealed({**_media_binding(),
                "text_sha256": sha256(text.encode()).hexdigest()})
    return result


def _assemble(plan, media):
    from test_korean_grammar import _snapshot

    api = importlib.import_module("multilang.services.korean_grammar_release")
    c = load_grammar_course()
    return api.assemble_reviewed_release(
        c, load_grammar_course_support(c),
        json.loads(Path("data/korean_grammar/v1/bootstrap-lessons.json").read_text()),
        plan, _passes(plan), media_bindings=media,
        review_provenance={"policy_sha256": "a" * 64, "route_sha256": "a" * 64,
            "prompt_sha256": "a" * 64, "output_schema_sha256": "a" * 64,
            "deterministic_validator_ids": ["fixture-validator"]},
        active_snapshot_resolver=_snapshot,
    )


def test_reviewed_join_keeps_bootstrap_before_guided_then_strict_and_rejects_stale_audio():
    from multilang.services.korean_grammar import validate_korean_grammar_production_readiness
    from multilang.services.korean_grammar_export import grammar_review_curriculum_sha256

    plan = _plan()
    media = _media(plan)
    bundle, bootstrap = _assemble(plan, media)
    assert [len(bundle.lexical_bootstrap), len(bundle.orientation_entries), len(bundle.grammar_entries)] == [57, 8, 100]
    assert len(bootstrap) == 57
    assert validate_korean_grammar_production_readiness(bundle).ready_state == "learner_ready"
    assert grammar_review_curriculum_sha256(bundle) == plan["curriculum_sha256"]
    assert all(card.review_binding.curriculum_sha256 == bundle.bundle_sha256 for card in bootstrap)
    media[plan["grammar_candidates"][0]["entry_id"]]["word"]["text_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="media|audio|drift"):
        _assemble(plan, media)


def test_grammar_notes_assign_distinct_new_card_positions_from_curriculum():
    from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
    from multilang.domain.jobs import SupportedLanguage
    from multilang.services.export_anki_package import build_multilang_note

    rows = [ExportCardRow(identity=ExportCardIdentity(
        language=SupportedLanguage.KO, source_type="korean-grammar", job_id="offline-fixture",
        item_key=f"lesson-{position}", lemma_key=f"grammar:lesson-{position}", sort_index=position,
    ), word="학생", front_of_card="학생", definitions="Fixture only.",
        example_sentence="학생이에요.") for position in (57, 58)]
    assert [build_multilang_note(row).due for row in rows] == [57, 58]
