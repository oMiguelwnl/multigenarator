"""Build real review subjects and join three independent decisions for delivery.

Preparation deliberately has no review/media placeholders and cannot export.
The existing grammar compiler and exporter remain the final authority checks.
"""

from __future__ import annotations

from base64 import b64decode
from datetime import datetime
from hashlib import sha256
from typing import Literal

from pydantic import Field

from multilang.domain.korean import KoreanConcept, KoreanCurriculumEvidence
from multilang.domain.korean_grammar import (
    KoreanGrammarBootstrapEntry,
    KoreanGrammarSourceBinding,
)
from multilang.domain.korean_grammar import (
    korean_grammar_canonical_json_sha256 as digest,
)
from multilang.domain.korean_grammar_course import Digest, Text, _CourseModel
from multilang.services.korean_foundation_snapshot import resolve_active_korean_foundation_snapshot
from multilang.services.korean_grammar import (
    _phase31_binding_from_snapshot,
    _validate_graph_closure,
)
from multilang.services.korean_grammar_course import (
    _read_course_asset,
    validate_grammar_course_support,
)

KOREAN_BLIND_ASR_PROMPT = (
    "Transcreva exatamente a fala coreana deste áudio. Retorne somente a transcrição "
    "em coreano, sem comentários, sem traduzir e sem acrescentar palavras."
)


def _blind_asr_transcript(response, wav_sha256):
    """Three reference-free audio requests must independently return the same text."""
    from multilang.services.korean_grammar_audio import _spoken_identity

    if response.get("schema_version") != "openrouter-blind-asr-consensus-v1":
        raise ValueError("unsupported_blind_asr_protocol")
    passes = response.get("passes", [])
    if len(passes) != 3:
        raise ValueError("blind_asr_requires_three_passes")
    identifiers, transcripts = set(), []
    for row in passes:
        request, returned = row["request_payload"], row["response"]
        if digest(request) != row["request_sha256"] or digest(returned) != row["response_sha256"]:
            raise ValueError("blind_asr_request_or_response_drift")
        if (set(request) - {"model", "messages", "temperature", "max_tokens", "provider", "reasoning", "stream"}
                or request.get("model") != "google/gemini-2.5-flash-lite"
                or request.get("max_tokens") != 128 or request.get("temperature") != 0
                or request.get("stream", False) is not False):
            raise ValueError("blind_asr_request_scope_drift")
        messages = request.get("messages", [])
        if (len(messages) != 1 or set(messages[0]) != {"role", "content"}
                or messages[0]["role"] != "user"):
            raise ValueError("blind_asr_must_not_receive_reference")
        content = messages[0]["content"]
        if (not isinstance(content, list) or len(content) != 2
                or content[0] != {"type": "text", "text": KOREAN_BLIND_ASR_PROMPT}
                or set(content[1]) != {"type", "input_audio"}
                or content[1]["type"] != "input_audio"):
            raise ValueError("blind_asr_must_not_receive_reference")
        audio = content[1]["input_audio"]
        if (set(audio) != {"data", "format"} or audio["format"] != "wav"
                or not isinstance(audio["data"], str) or len(audio["data"]) > 400_000):
            raise ValueError("invalid_blind_asr_wave")
        try:
            decoded = b64decode(audio["data"], validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid_blind_asr_wave") from exc
        if sha256(decoded).hexdigest() != wav_sha256:
            raise ValueError("blind_asr_wave_substitution")
        identifier = returned.get("id")
        choices = returned.get("choices", [])
        if (not isinstance(identifier, str) or not identifier or identifier in identifiers
                or returned.get("model") != request["model"] or len(choices) != 1
                or choices[0].get("finish_reason") != "stop"):
            raise ValueError("invalid_blind_asr_response_identity")
        message = choices[0].get("message", {})
        transcript = message.get("content")
        if (message.get("role") != "assistant" or message.get("tool_calls")
                or not isinstance(transcript, str) or not 0 < len(transcript.strip()) <= 256):
            raise ValueError("invalid_blind_asr_transcript")
        identifiers.add(identifier)
        transcripts.append(transcript.strip())
    if len({_spoken_identity(t) for t in transcripts}) != 1:
        raise ValueError("blind_asr_disagreement")
    return transcripts[0]


def validate_fresh_review_invocation(review, invocation, *, output_sha256, expected_lane):
    """Bind an AI decision to an actual fresh invocation, not its self-description."""
    if (invocation.get("fresh_context") is not True
            or invocation.get("actor_type") != "ai_model" or invocation.get("is_human") is not False
            or invocation.get("status") != "returned" or invocation.get("exit_code") != 0
            or invocation.get("lane") != expected_lane
            or invocation.get("plan_sha256") != review.get("plan_sha256")
            or invocation.get("output_sha256") != output_sha256
            or review.get("actor_type") != "ai_model" or review.get("is_human") is not False
            or review.get("independence_scope") not in {"fresh_context_same_model", "fresh_context_different_model"}
            or not review.get("pass_id", "").startswith(f"grammar-closeout-{expected_lane}-")):
        raise ValueError("review_invocation_identity_or_freshness_drift")
    try:
        start = datetime.fromisoformat(invocation["started_at"])
        finish = datetime.fromisoformat(invocation["finished_at"])
        valid = start.tzinfo is not None and finish.tzinfo is not None and start <= finish
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError("invalid_review_invocation_timestamps")


def validate_acoustic_identity(observation, *, wav_sha256, asr_record, pronunciation_record):
    """Recompute text support from persisted provider results bound to exact audio.

    The caller verifies report file hashes and supplies a freshly decoded WAV
    hash. Neither a summarized transcript nor assessment scores can be moved to
    another recording by changing only the observation's media hash.
    """
    from multilang.services.korean_grammar_audio import _spoken_identity

    def bound_response(record, mode, evidence_key):
        evidence = observation.get(evidence_key)
        if record is None:
            if evidence is not None:
                raise ValueError("missing_acoustic_provider_evidence")
            return None
        if (evidence != digest(record) or record.get("mode") != mode
                or record.get("wav_sha256") != wav_sha256
                or any(record.get(k) != observation.get(k)
                       for k in ("transport_sha256", "media_sha256", "source_text"))):
            raise ValueError("acoustic_provider_subject_drift")
        response = record.get("provider_response")
        if not isinstance(response, dict) or digest(response) != record.get("provider_response_sha256"):
            raise ValueError("acoustic_provider_response_drift")
        return response

    asr = bound_response(asr_record, "asr", "asr_evidence_sha256")
    assessment = bound_response(pronunciation_record, "pronunciation", "pronunciation_evidence_sha256")
    asr_ok = False
    if asr is not None:
        if asr_record.get("provider") == "openrouter":
            transcript = _blind_asr_transcript(asr, wav_sha256)
            recognized = True
        else:
            best = (asr.get("NBest") or [{}])[0]
            transcript = best.get("Lexical", asr.get("DisplayText", ""))
            recognized = asr.get("RecognitionStatus") == "Success"
        asr_ok = (recognized and bool(observation["source_text"])
                  and _spoken_identity(transcript) == _spoken_identity(observation["source_text"]))
        if (observation.get("asr_status") != "observed"
                or transcript != observation.get("asr_transcript")
                or transcript != asr_record.get("transcript")
                or observation.get("asr_transcript_matches") is not asr_ok
                or asr_record.get("transcript_matches") is not asr_ok):
            raise ValueError("acoustic_transcript_summary_drift")
    elif observation.get("asr_status") == "observed":
        raise ValueError("missing_acoustic_provider_evidence")
    if assessment != observation.get("pronunciation_provider_response"):
        raise ValueError("acoustic_assessment_summary_drift")

    def score(value):
        return value if type(value) in (int, float) and 0 <= value <= 100 else -1

    pa_ok = False
    if assessment is not None:
        best = (assessment.get("NBest") or [{}])[0]
        words = best.get("Words", [])
        pa_ok = (assessment.get("RecognitionStatus") == "Success"
                 and score(best.get("AccuracyScore")) >= 90
                 and score(best.get("CompletenessScore")) >= 95 and bool(words)
                 and all(score(w.get("AccuracyScore")) >= 80
                         and w.get("ErrorType") not in {"Omission", "Insertion"} for w in words))
    if not (asr_ok or pa_ok) or observation.get("automated_text_identity_evidence") != "supported":
        raise ValueError("acoustic_text_identity_unresolved")
    return {"free_asr_match": asr_ok, "reference_pronunciation_screen": pa_ok}


def _sealed(payload):
    return {**payload, "content_hash": digest(payload)}


class _BootstrapLesson(_CourseModel):
    entry_id: Text
    lemma: Text
    source_form: Text
    source_pos: Text
    source_entry_sha256: Digest
    teaching_mode: Literal["lexical_label"]
    definition_pt: Text
    example_sentence: Text
    translation_pt: Text
    context_pt: Text
    ipa: str = Field(max_length=2048)
    word_audio_text: Text
    sentence_audio_text: Text
    editorial_note_pt: Text


class _BootstrapLessons(_CourseModel):
    schema_version: Literal["korean-grammar-bootstrap-lessons-author-v1"]
    status: Literal["author_candidate_pending_independent_review"]
    course_sha256: Digest
    lexical_support_sha256: Digest
    source_id: Text
    source_version: Text
    source_sha256: Digest
    teaching_mode: Literal["lexical_label"]
    editorial_note_pt: Text
    entries: tuple[_BootstrapLesson, ...] = Field(min_length=1, max_length=256)


def prepare_release_candidates(
    course, support, bootstrap_lessons, *, morphology_sha256: str,
    active_snapshot_resolver=resolve_active_korean_foundation_snapshot,
):
    """Freeze the complete graph and all learner text for independent review."""
    support_result = validate_grammar_course_support(course, support)
    if support_result["progression_failures"] or support_result["unresolved"]:
        raise ValueError("unresolved_grammar_course")
    authored = _BootstrapLessons.model_validate(bootstrap_lessons)
    if (authored.course_sha256 != course.content_sha256
            or authored.lexical_support_sha256 != sha256(_read_course_asset("lexical-support.json")).hexdigest()
            or authored.source_id != support.lexical.source_id
            or authored.source_version != support.lexical.source_version
            or authored.source_sha256 != support.lexical.source_sha256):
        raise ValueError("stale_bootstrap_authoring")
    if len(morphology_sha256) != 64 or any(c not in "0123456789abcdef" for c in morphology_sha256):
        raise ValueError("invalid_morphology_subject")
    root, imported = _phase31_binding_from_snapshot(active_snapshot_resolver())
    # The active root makes ALL approved foundation concepts known. Individual
    # edges record the prerequisite for reading a cited Korean lexical label.
    base_id = "orthography.block.unit" if any(c.id == "orthography.block.unit" for c in imported) else "orthography.hangul"
    graph = {c.id: set(c.prerequisite_ids) for c in imported}
    if base_id not in graph:
        raise ValueError("foundation_has_no_hangul_unit")
    order = [c.id for c in imported]

    def closure(ids):
        result, pending = set(), list(ids)
        while pending:
            key = pending.pop()
            if key not in graph:
                raise ValueError("unknown_release_prerequisite")
            if key not in result:
                result.add(key)
                pending.extend(graph[key])
        return tuple(key for key in order if key in result)

    base = closure([base_id])
    expected = {r.entry_id: r for r in support.lexical.entries if r.teaching_mode == "lexical"}
    labels = {r.entry_id: r for r in authored.entries}
    if len(labels) != len(authored.entries) or set(labels) != set(expected):
        raise ValueError("incomplete_bootstrap_lessons")
    bootstrap, bootstrap_candidates, overlays = [], [], []
    sequence = max(c.sequence for c in imported)
    for number, (entry_id, lexical) in enumerate(expected.items(), start=1):
        lesson = labels[entry_id]
        if (lesson.lemma != lexical.lemma or lesson.source_form != lexical.source_form
                or lesson.source_pos != lexical.source_pos
                or lesson.source_entry_sha256 != lexical.source_entry_sha256
                or any(t != lexical.lemma for t in (lesson.example_sentence, lesson.word_audio_text,
                                                    lesson.sentence_audio_text))):
            raise ValueError("bootstrap_lexical_identity_drift")
        target = "lexicon:" + entry_id
        source = KoreanGrammarSourceBinding(**_sealed({
            "source_id": support.lexical.source_id, "source_version": support.lexical.source_version,
            "license_decision": "approved-redistribution", "entry_sha256": lexical.source_entry_sha256,
            "bundle_sha256": support.lexical.source_sha256, "source_backed": True, "synthetic": False,
        }))
        entry = KoreanGrammarBootstrapEntry(**_sealed({
            "entry_id": entry_id, "sequence": number, "target_concept_id": target,
            "lexical_identity_sha256": digest(lexical), "submitted_form": lexical.lemma,
            "canonical_nfc": lexical.lemma, "source_binding": source.model_dump(mode="json"),
            "observed_concept_ids": [*base, target], "prerequisite_concept_ids": list(base),
            "learner_visible": True,
        }))
        bootstrap.append(entry.model_dump(mode="json"))
        payload = {"entry_id": entry_id, "bootstrap_sha256": entry.content_hash,
                   "definitions": lesson.definition_pt + " Contexto: " + lesson.context_pt,
                   "ipa": lesson.ipa, "example_sentence": lesson.example_sentence,
                   "portuguese_translation": lesson.translation_pt}
        if len(payload["definitions"]) > 2048:
            raise ValueError("bootstrap_definition_too_long")
        bootstrap_candidates.append({"entry_id": entry_id, "candidate_sha256": digest(payload), "payload": payload})
        graph[target] = set(base)
        order.append(target)
        overlays.append(KoreanConcept(id=target, domain="lexicon", prerequisite_ids=base, sequence=sequence + number))
    observations = {r.entry_id: r for r in support.observations.entries}
    candidates = []
    guide_ids = {"grammar:" + c.entry_id for c in course.cards if c.category_id == "G0"}
    for number, card in enumerate(course.cards, start=1):
        target = "grammar:" + card.entry_id
        direct = [*base, *("grammar:" + p for p in card.prerequisite_ids)]
        direct.extend("lexicon:" + e.entry_id for e in expected.values() if card.entry_id in e.used_by)
        # Strict lessons also depend on the grammar they actually reuse.
        if card.category_id != "G0":
            direct.extend("grammar:" + p for p in observations[card.entry_id].observed_grammar_ids if p != card.entry_id)
        prerequisites = closure(direct)
        observed = list(dict.fromkeys([*prerequisites, *("grammar:" + p for p in observations[card.entry_id].observed_grammar_ids)]))
        unknown = [x for x in observed if x in guide_ids] if card.category_id == "G0" else [target]
        evidence = KoreanCurriculumEvidence(
            target_concept_id=target, policy="contextual" if card.category_id == "G0" else "strict",
            prerequisite_concept_ids=prerequisites, observed_concept_ids=observed, unknown_concept_ids=unknown,
        )
        source = KoreanGrammarSourceBinding(**_sealed({
            "source_id": "multilang-korean-grammar-course", "source_version": "v1",
            "license_decision": "approved-local-use", "entry_sha256": card.content_sha256,
            "bundle_sha256": course.content_sha256, "source_backed": True, "synthetic": False,
        }))
        payload = {"entry_id": card.entry_id, "sequence": number, "category_id": card.category_id,
                   "target_concept_id": target, "construction_label": card.entry_id,
                   "form": card.form, "function": card.function,
                   "attachment_rule": card.attachment_rule + (" Nota: " + card.notes if card.notes else ""),
                   "register": card.usage_register, "example_sentence": card.example_sentence,
                   "portuguese_translation": card.portuguese_translation,
                   "pronunciation_sample": "Leitura no áudio: " + card.spoken_sample,
                   "spoken_sample": card.spoken_sample, "source_binding": source.model_dump(mode="json"),
                   "evidence": evidence.model_dump(mode="json")}
        candidates.append({"entry_id": card.entry_id, "candidate_sha256": digest(payload), "payload": payload})
        graph[target] = set(prerequisites)
        order.append(target)
        overlays.append(KoreanConcept(id=target, domain="grammar", prerequisite_ids=prerequisites,
                                      sequence=sequence + len(bootstrap) + number))
    _validate_graph_closure(imported_concepts=imported, overlay_concepts=tuple(overlays))
    curriculum = {"phase31_binding": root.model_dump(mode="json"),
                  "imported_concepts": [c.model_dump(mode="json") for c in imported],
                  "overlay_concepts": [c.model_dump(mode="json") for c in overlays],
                  "orientation_concept_ids": [c["payload"]["target_concept_id"] for c in candidates
                                              if c["payload"]["category_id"] == "G0" ]}
    plan = {"schema_version": "korean-grammar-release-candidates-v1", "course_sha256": course.content_sha256,
            "support_sha256": digest(support), "bootstrap_author_sha256": digest(authored),
            "morphology_sha256": morphology_sha256, "curriculum": curriculum,
            "curriculum_sha256": digest(curriculum), "lexical_bootstrap": bootstrap,
            "grammar_candidates": candidates, "bootstrap_candidates": bootstrap_candidates,
            "learner_ready": False}
    return {**plan, "plan_sha256": digest(plan)}


class _Decision(_CourseModel):
    subject_id: Text
    candidate_sha256: Digest
    verdict: Literal["ai_review_passed", "ai_review_failed", "blocked_uncertainty", "blocked_disagreement"]
    reason_pt: Text


class _ReviewPass(_CourseModel):
    pass_id: Text
    actor_type: Literal["ai_model"]
    is_human: Literal[False]
    provider: Text
    model_id: Text
    independence_scope: Literal["fresh_context_same_model", "fresh_context_different_model"]
    plan_sha256: Digest
    decisions: tuple[_Decision, ...] = Field(min_length=1, max_length=256)


def validate_release_reviews(plan, passes):
    """All three passes must accept every exact subject; no majority override."""
    payload = {k: v for k, v in plan.items() if k != "plan_sha256"}
    if digest(payload) != plan["plan_sha256"]:
        raise ValueError("release_plan_drift")
    candidates = [*plan["grammar_candidates"], *plan["bootstrap_candidates"]]
    expected = {c["entry_id"]: c["candidate_sha256"] for c in candidates}
    if len(expected) != len(candidates) or any(digest(c["payload"]) != c["candidate_sha256"] for c in candidates):
        raise ValueError("release_candidate_drift")
    if len(passes) != 3:
        raise ValueError("release_requires_three_review_passes")
    reviewed = [_ReviewPass.model_validate(p) for p in passes]
    if len({p.pass_id for p in reviewed}) != 3:
        raise ValueError("duplicate_release_review_pass")
    for p in reviewed:
        if p.plan_sha256 != plan["plan_sha256"]:
            raise ValueError("stale_release_review")
        decisions = {d.subject_id: d for d in p.decisions}
        if len(decisions) != len(p.decisions) or set(decisions) != set(expected):
            raise ValueError("incomplete_release_review")
        if any(d.candidate_sha256 != expected[key] or d.verdict != "ai_review_passed"
               for key, d in decisions.items()):
            raise ValueError("release_review_not_unanimously_passed")
    return {key: {"candidate_sha256": value, "pass_ids": [p.pass_id for p in reviewed],
                  "pass_sha256": [digest(p) for p in reviewed]} for key, value in expected.items()}


class _ReviewProvenance(_CourseModel):
    policy_sha256: Digest
    route_sha256: Digest
    prompt_sha256: Digest
    output_schema_sha256: Digest
    deterministic_validator_ids: tuple[Text, ...] = Field(min_length=1, max_length=32)


def assemble_reviewed_release(
    course, support, bootstrap_lessons, plan, passes, *, media_bindings,
    review_provenance,
    active_snapshot_resolver=resolve_active_korean_foundation_snapshot,
):
    """Join independently obtained decisions and media with the existing compiler.

    This join performs no provider calls or media approval. The audio lane must
    supply reviewed bindings; export separately rechecks the exact MP3 bytes.
    The orchestration receipt binds native morphology, prompts, routes, schemas
    and validator evidence. Text review does not imply anyone heard the audio.
    """
    from multilang.domain.korean_grammar import (
        KoreanGrammarAIEvidenceBinding,
        KoreanGrammarMediaBinding,
        grammar_content_hash,
    )
    from multilang.domain.korean_grammar_bootstrap import KoreanGrammarBootstrapCard
    from multilang.services.korean_grammar_course import build_grammar_course_bundle

    consensus = validate_release_reviews(plan, passes)
    current = prepare_release_candidates(
        course, support, bootstrap_lessons, morphology_sha256=plan["morphology_sha256"],
        active_snapshot_resolver=active_snapshot_resolver,
    )
    if current != plan:
        raise ValueError("release_source_or_curriculum_drift")
    provenance = _ReviewProvenance.model_validate(review_provenance)
    if set(media_bindings) != set(consensus):
        raise ValueError("incomplete_release_media")
    providers = {p["provider"] for p in passes}
    models = {p["model_id"] for p in passes}

    def media_for(candidate):
        roles = media_bindings[candidate["entry_id"]]
        if set(roles) != {"word", "sentence"}:
            raise ValueError("incomplete_release_media_roles")
        media = {role: KoreanGrammarMediaBinding.model_validate(roles[role]) for role in roles}
        payload = candidate["payload"]
        texts = {"word": payload.get("spoken_sample", payload["example_sentence"]),
                 "sentence": payload["example_sentence"]}
        for role, binding in media.items():
            if (binding.content_hash != grammar_content_hash(binding)
                    or binding.text_sha256 != sha256(texts[role].encode()).hexdigest()
                    or binding.integrity_status != "passed"
                    or binding.acoustic_review_status not in {
                        "ai_acoustic_review_passed", "automated_integrity_passed"}):
                raise ValueError("stale_or_unreviewed_release_media")
        return media

    def review_for(candidate, source_hash, curriculum_hash, media):
        evidence = consensus[candidate["entry_id"]]
        return KoreanGrammarAIEvidenceBinding(**_sealed({
            "policy_id": "multilang-ai-linguistic-review-v1", "actor_type": "ai_model", "is_human": False,
            "provider": next(iter(providers)) if len(providers) == 1 else "multiple-reviewed-providers",
            "model_id": next(iter(models)) if len(models) == 1 else "multiple-reviewed-models",
            **provenance.model_dump(mode="json"),
            "source_sha256": source_hash, "candidate_sha256": candidate["candidate_sha256"],
            "analyzer_sha256": plan["morphology_sha256"], "curriculum_sha256": curriculum_hash,
            "media_sha256": digest([media[role].content_hash for role in ("word", "sentence")]),
            "deterministic_validator_result": "passed", "fresh_context_pass_ids": evidence["pass_ids"],
            "required_pass_count": 3, "consensus_status": "ai_review_passed",
        }))

    authored = {card.entry_id: card for card in course.cards}
    lessons = []
    for candidate in plan["grammar_candidates"]:
        payload = candidate["payload"]
        media = media_for(candidate)
        review = review_for(candidate, payload["source_binding"]["content_hash"],
                            plan["curriculum_sha256"], media)
        lessons.append({
            "entry_id": candidate["entry_id"], "lesson_sha256": authored[candidate["entry_id"]].content_sha256,
            **{key: payload[key] for key in ("pronunciation_sample", "source_binding", "evidence")},
            "review_binding": review.model_dump(mode="json"),
            "word_media_binding": media["word"].model_dump(mode="json"),
            "sentence_media_binding": media["sentence"].model_dump(mode="json"),
            "ready_state": "learner_ready",
        })
    bundle = build_grammar_course_bundle(course, {
        "course_sha256": plan["course_sha256"], "support_sha256": plan["support_sha256"],
        "lexical_bootstrap": plan["lexical_bootstrap"], "lessons": lessons,
    }, support=support, active_snapshot_resolver=active_snapshot_resolver)
    bootstrap_entries = {entry.entry_id: entry for entry in bundle.lexical_bootstrap}
    bootstrap = []
    for candidate in plan["bootstrap_candidates"]:
        media = media_for(candidate)
        review = review_for(candidate, bootstrap_entries[candidate["entry_id"]].source_binding.content_hash,
                            bundle.bundle_sha256, media)
        bootstrap.append(KoreanGrammarBootstrapCard(**_sealed({
            **candidate["payload"], "review_binding": review.model_dump(mode="json"),
            "word_media_binding": media["word"].model_dump(mode="json"),
            "sentence_media_binding": media["sentence"].model_dump(mode="json"),
        })))
    return bundle, tuple(bootstrap)
