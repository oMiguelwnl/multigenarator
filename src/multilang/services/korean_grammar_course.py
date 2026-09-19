"""Prepare substantive Korean content for the existing reviewed-bundle pipeline.

No providers, database writes or approval receipts are created by preparation.
The human-readable preview is also useful for independent linguistic review.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import stat
from collections import Counter
from hashlib import sha256
from html import escape
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from multilang.domain.korean import KoreanCurriculumEvidence
from multilang.domain.korean_grammar import (
    KoreanGrammarAIEvidenceBinding,
    KoreanGrammarBootstrapEntry,
    KoreanGrammarEntry,
    KoreanGrammarMediaBinding,
    KoreanGrammarSourceBinding,
    korean_grammar_canonical_json_sha256,
)
from multilang.domain.korean_grammar_course import (
    KoreanGrammarCourse,
    KoreanGrammarCourseSupport,
)

_FILENAMES = ("cards-g0-g6.json", "cards-g7-g13.json")
_MAX_BYTES = 2_000_000
COURSE_SOURCES = {
    "sejong-curriculum": {
        "title": "Online King Sejong Institute — curriculum",
        "url": "https://www.iksi.or.kr/lms/main/curriculum.do",
        "use": "Curriculum reference; examples and Portuguese explanations are original.",
    },
    "krdict": {
        "title": "National Institute of Korean Language — Korean Basic Dictionary",
        "url": "https://krdict.korean.go.kr/eng/mainAction",
        "use": "Reference for constructions, senses and restrictions; no copied definitions.",
    },
}

# Exact already approved source, not an arbitrary manifest's claim of permission.
_NIKL_SOURCE_SHA256 = "3b49681f05d6a7490c13da2a2847e433effdf65da409fd295792d6ee33685064"
_NIKL_EXTRACT_SHA256 = "93e3cee8c4edbb4db999df0da3760b68f3ad0eaa8193f37a539b6a87a0bff807"


def _read_course_asset(name: str, source_dir: Path | None = None) -> bytes:
    if source_dir is None:
        repository = Path(__file__).resolve().parents[3] / "data/korean_grammar/v1"
        source_dir = repository if repository.is_dir() else None
    raw = (_read_bounded(source_dir / name) if source_dir is not None else
           files("multilang").joinpath("data/korean_grammar/v1", name).read_bytes())
    if not 0 < len(raw) <= _MAX_BYTES:
        raise ValueError("invalid_grammar_course_asset")
    return raw


def parse_nikl_bootstrap_rows(text: str) -> list[dict[str, Any]]:
    """Read the NIKL publisher's homograph numbers without discarding identity.

    This is a source-specific table format, NOT a Korean suffix/morphology rule.
    Multiple senses/POS rows remain separate and require an explicit decision.
    """
    if len(text) > _MAX_BYTES:
        raise ValueError("oversized_nikl_source")
    lines = text.splitlines()
    if not lines or lines[0].split("\t") != ["순위", "단어", "품사", "풀이", "등급"]:
        raise ValueError("invalid_nikl_source_header")
    rows = []
    for number, line in enumerate(lines[1:], start=2):
        if not line:
            continue
        fields = line.split("\t")
        if (
            len(fields) != 5 or (fields[0] and not fields[0].isdigit())
            or len(fields[1]) > 128
        ):
            raise ValueError("invalid_nikl_source_row")
        match = re.fullmatch(r"(.+?)([0-9]{2})?", fields[1])
        if match is None:
            raise ValueError("invalid_nikl_source_row")
        rows.append({
            "lemma": match[1], "source_form": fields[1], "sense_marker": match[2],
            "source_pos": fields[2], "source_gloss": fields[3], "source_level": fields[4],
            "source_frequency_rank": int(fields[0]) if fields[0] else None,
            "source_line_number": number,
            "source_entry_sha256": sha256(line.encode("utf-8")).hexdigest(),
            "status": "sense_review_required",
        })
    return rows


def prepare_grammar_bootstrap_candidates(
    course: KoreanGrammarCourse, source_bundle_dir: Path,
) -> dict[str, Any]:
    """Ground the minimal word list in exact locally approved source bytes."""
    manifest = json.loads(_read_bounded(source_bundle_dir / "manifest.json"))
    if (
        manifest.get("source_id") != "nikl-korean-learners-vocabulary"
        or manifest.get("source_version") != "2003-06-04.revised-2019-05-30"
        or manifest.get("synthetic") is not False
        or manifest.get("license_decision") != "approved-redistribution"
    ):
        raise ValueError("unapproved_grammar_bootstrap_source")
    raw = _read_bounded(source_bundle_dir / "source-snapshot.txt")
    if sha256(raw).hexdigest() != _NIKL_SOURCE_SHA256:
        raise ValueError("grammar_bootstrap_source_hash_mismatch")
    attribution = _read_bounded(source_bundle_dir / "attribution.txt")
    if sha256(attribution).hexdigest() != "bb3c403fb3b7b5ae1042badc2e7fca6e3ca99c1b1138898b45beb24b3052866a":
        raise ValueError("grammar_bootstrap_attribution_hash_mismatch")
    rows = parse_nikl_bootstrap_rows(raw.decode("cp949"))
    lemmas = dict.fromkeys(lemma for card in course.cards for lemma in card.lexical_lemmas)
    candidates = [{
        "lemma": lemma,
        "used_by": [card.entry_id for card in course.cards if lemma in card.lexical_lemmas],
        "source_matches": [row for row in rows if row["lemma"] == lemma],
    } for lemma in lemmas]
    return {
        "schema_version": "korean-grammar-bootstrap-candidates-v1",
        "course_sha256": course.content_sha256,
        "source_id": manifest["source_id"], "source_version": manifest["source_version"],
        "source_sha256": _NIKL_SOURCE_SHA256,
        "attribution": attribution.decode("utf-8"),
        "source_license_decision": manifest["license_decision"],
        "status": "needs_lexical_sense_and_grammar_classification_review",
        "learner_ready": False,
        "missing_source_lemmas": [row["lemma"] for row in candidates if not row["source_matches"]],
        "candidates": candidates,
    }


def _read_bounded(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= _MAX_BYTES:
            raise ValueError("invalid_grammar_course_file")
        data = stream.read(_MAX_BYTES + 1)
        if len(data) > _MAX_BYTES:
            raise ValueError("oversized_grammar_course_file")
        return data


def load_grammar_course(source_dir: Path | None = None) -> KoreanGrammarCourse:
    """Load fixed, bounded files; an installed wheel includes the same assets."""
    if source_dir is None:
        repository = Path(__file__).resolve().parents[3] / "data/korean_grammar/v1"
        source_dir = repository if repository.is_dir() else None
    cards = []
    for name in _FILENAMES:
        if source_dir is not None:
            raw = _read_bounded(source_dir / name)
        else:
            raw = files("multilang").joinpath("data/korean_grammar/v1", name).read_bytes()
            if not 0 < len(raw) <= _MAX_BYTES:
                raise ValueError("invalid_packaged_grammar_course")
        payload = json.loads(raw)
        if not isinstance(payload, list) or len(payload) > 256:
            raise ValueError("invalid_grammar_course_inventory")
        cards.extend(payload)
    return KoreanGrammarCourse(cards=cards)


def load_grammar_course_support(
    course: KoreanGrammarCourse, source_dir: Path | None = None,
    *, source_bundle_dir: Path | None = None,
) -> KoreanGrammarCourseSupport:
    """Read authored observations and senses, never infer review approval."""
    if source_dir is None:
        repository = Path(__file__).resolve().parents[3] / "data/korean_grammar/v1"
        source_dir = repository if repository.is_dir() else None
    payload = {}
    for key, name in (("lexical", "lexical-support.json"),
                      ("observations", "grammar-observations.json")):
        raw = (_read_bounded(source_dir / name) if source_dir is not None else
               files("multilang").joinpath("data/korean_grammar/v1", name).read_bytes())
        if not 0 < len(raw) <= _MAX_BYTES:
            raise ValueError("invalid_grammar_support_file")
        payload[key] = json.loads(raw)
    support = KoreanGrammarCourseSupport.model_validate(payload)
    validate_grammar_course_support(course, support, source_bundle_dir=source_bundle_dir)
    return support


def validate_grammar_course_support(
    course: KoreanGrammarCourse, support: KoreanGrammarCourseSupport,
    *, source_bundle_dir: Path | None = None,
) -> dict[str, Any]:
    """Recompute cumulative teaching state from explicit semantic observations.

    This validates an annotation, not its linguistic completeness. Independent
    review and morphology must still establish what the actual sentence uses.
    Construction-owned senses must not sneak into the lexical bootstrap.
    """
    if any(part.course_sha256 != course.content_sha256
           for part in (support.lexical, support.observations)):
        raise ValueError("stale_course_support")
    positions = {card.entry_id: i for i, card in enumerate(course.cards)}
    observations = {entry.entry_id: entry for entry in support.observations.entries}
    if len(observations) != len(support.observations.entries) or set(observations) != set(positions):
        raise ValueError("invalid_grammar_observation_inventory")
    lexical_ids = [entry.entry_id for entry in support.lexical.entries]
    if len(set(lexical_ids)) != len(lexical_ids):
        raise ValueError("duplicate_grammar_lexical_identity")
    coverage: set[tuple[str, str]] = set()
    for entry in support.lexical.entries:
        if not set(entry.used_by) <= positions.keys():
            raise ValueError("unknown_grammar_lexical_usage")
        if entry.introduced_by is not None and (
            entry.introduced_by not in positions
            or any(positions[used] < positions[entry.introduced_by] for used in entry.used_by)
        ):
            raise ValueError("forward_construction_in_lexical_support")
        coverage.update((used, entry.lemma) for used in entry.used_by)
    required = {(card.entry_id, lemma) for card in course.cards for lemma in card.lexical_lemmas}
    if not required <= coverage:
        raise ValueError("incomplete_grammar_lexical_coverage")
    if source_bundle_dir is not None:
        # Verifies the exact approved snapshot/attribution before row identity.
        prepare_grammar_bootstrap_candidates(course, source_bundle_dir)
        source_rows = parse_nikl_bootstrap_rows(
            _read_bounded(source_bundle_dir / "source-snapshot.txt").decode("cp949")
        )
    else:
        # Trusted bundled subset: custom --source-dir cannot replace this
        # pinned source with its own assertion of an approved hash.
        extract = _read_course_asset("lexical-source-rows.tsv")
        if sha256(extract).hexdigest() != _NIKL_EXTRACT_SHA256:
            raise ValueError("grammar_lexical_source_extract_drift")
        attribution = _read_course_asset("attribution.txt")
        if sha256(attribution).hexdigest() != "bb3c403fb3b7b5ae1042badc2e7fca6e3ca99c1b1138898b45beb24b3052866a":
            raise ValueError("grammar_bootstrap_attribution_hash_mismatch")
        source_rows = parse_nikl_bootstrap_rows(extract.decode("utf-8"))
    identities = {(row["lemma"], row["source_form"], row["source_pos"],
                   row["source_entry_sha256"]) for row in source_rows}
    if any((entry.lemma, entry.source_form, entry.source_pos, entry.source_entry_sha256)
           not in identities for entry in support.lexical.entries):
        raise ValueError("grammar_lexical_source_identity_mismatch")
    source_status = "exact_source_rows_verified"
    orientation_ids = {card.entry_id for card in course.cards if card.category_id == "G0"}
    known = set(orientation_ids)
    progression, failures, unresolved = [], [], []
    for card in course.cards:
        observed = observations[card.entry_id]
        if not set(observed.observed_grammar_ids) <= positions.keys():
            raise ValueError("unknown_grammar_observation")
        guided = card.category_id == "G0"
        unknown = [entry_id for entry_id in observed.observed_grammar_ids
                   if guided or entry_id not in known]
        valid = (card.entry_id in unknown and set(unknown) <= orientation_ids
                 if guided else unknown == [card.entry_id])
        row = {"entry_id": card.entry_id, "policy": "guided_orientation" if guided else "strict",
               "unknown_grammar_ids": unknown, "valid": valid}
        progression.append(row)
        if not valid:
            failures.append(row)
        unresolved.extend({"entry_id": card.entry_id, **item.model_dump(mode="json")}
                          for item in observed.unresolved)
        if not guided:
            known.add(card.entry_id)
    return {
        "course_sha256": course.content_sha256,
        "lexical_sha256": korean_grammar_canonical_json_sha256(support.lexical),
        "observations_sha256": korean_grammar_canonical_json_sha256(support.observations),
        "orientation_count": len(orientation_ids), "strict_count": len(course.cards) - len(orientation_ids),
        "lexical_entry_count": sum(e.teaching_mode == "lexical" for e in support.lexical.entries),
        "construction_entry_count": sum(e.teaching_mode == "construction" for e in support.lexical.entries),
        "source_status": source_status, "progression": progression,
        "progression_failures": failures, "unresolved": unresolved,
        "semantic_review_status": "independent_review_required", "learner_ready": False,
    }


class _LessonEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    entry_id: str = Field(pattern=r"^g(?:[0-9]|1[0-3])\.[a-z0-9-]+$", max_length=96)
    lesson_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pronunciation_sample: str = Field(min_length=1, max_length=2048)
    source_binding: KoreanGrammarSourceBinding
    evidence: KoreanCurriculumEvidence
    review_binding: KoreanGrammarAIEvidenceBinding
    word_media_binding: KoreanGrammarMediaBinding
    sentence_media_binding: KoreanGrammarMediaBinding
    ready_state: Literal["blocked", "needs_review", "learner_ready"]


class _CourseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    course_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    support_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lexical_bootstrap: tuple[KoreanGrammarBootstrapEntry, ...] = Field(max_length=256)
    lessons: tuple[_LessonEvidence, ...] = Field(min_length=14, max_length=256)


def build_grammar_course_bundle(
    course: KoreanGrammarCourse, evidence: dict[str, Any], *, active_snapshot_resolver=None,
    support: KoreanGrammarCourseSupport | None = None,
):
    """Bind authored text to genuine per-lesson evidence and the existing strict builder.

    The sidecar supplies pronunciation, source, concept observations, AI reviews
    and media bindings, never replacement lesson text. Missing evidence is an
    error; there are no fabricated default receipts or empty audio artifacts.
    Export continues to recheck the actual audio bytes and review bindings.
    """
    from multilang.domain.korean_grammar import grammar_content_hash
    from multilang.services.korean_grammar import (
        KoreanGrammarBundleBuilder,
        validate_korean_grammar_strict_graph,
    )
    from multilang.services.korean_grammar_export import (
        grammar_candidate_sha256,
        grammar_review_curriculum_sha256,
    )

    try:
        binding = _CourseEvidence.model_validate(evidence)
    except ValueError:
        raise ValueError("invalid_course_evidence") from None
    if binding.course_sha256 != course.content_sha256:
        raise ValueError("stale_course_evidence")
    support = support if support is not None else load_grammar_course_support(course)
    support_report = validate_grammar_course_support(course, support)
    if binding.support_sha256 != korean_grammar_canonical_json_sha256(support):
        raise ValueError("stale_course_support_evidence")
    if support_report["progression_failures"]:
        raise ValueError("invalid_course_progression")
    expected_lexical = {entry.entry_id: entry for entry in support.lexical.entries
                        if entry.teaching_mode == "lexical"}
    if (len(binding.lexical_bootstrap) != len(expected_lexical)
            or {entry.entry_id for entry in binding.lexical_bootstrap} != set(expected_lexical)):
        raise ValueError("incomplete_course_lexical_inventory")
    for entry in binding.lexical_bootstrap:
        authored = expected_lexical[entry.entry_id]
        if (entry.target_concept_id != "lexicon:" + authored.entry_id
                or entry.content_hash != grammar_content_hash(entry)
                or entry.lexical_identity_sha256 != korean_grammar_canonical_json_sha256(authored)
                or entry.canonical_nfc != authored.lemma
                or entry.source_binding.source_id != support.lexical.source_id
                or entry.source_binding.source_version != support.lexical.source_version
                or entry.source_binding.entry_sha256 != authored.source_entry_sha256
                or entry.source_binding.bundle_sha256 != support.lexical.source_sha256
                or entry.source_binding.content_hash != grammar_content_hash(entry.source_binding)):
            raise ValueError("course_lexical_identity_drift")
    observations = {row.entry_id: row for row in support.observations.entries}
    expected_fields = {
        "entry_id", "lesson_sha256", "pronunciation_sample", "source_binding", "evidence",
        "review_binding", "word_media_binding", "sentence_media_binding", "ready_state",
    }
    by_id = {}
    for lesson in binding.lessons:
        row = lesson.model_dump(mode="json")
        if set(row) != expected_fields or not isinstance(row.get("entry_id"), str):
            raise ValueError("invalid_course_evidence_fields")
        if row["entry_id"] in by_id:
            raise ValueError("duplicate_course_evidence")
        by_id[row["entry_id"]] = row
    if set(by_id) != {card.entry_id for card in course.cards}:
        raise ValueError("incomplete_course_evidence")
    entries = []
    for sequence, card in enumerate(course.cards, start=1):
        row = by_id[card.entry_id]
        if row["lesson_sha256"] != card.content_sha256:
            raise ValueError("stale_lesson_evidence")
        payload = {key: value for key, value in row.items() if key != "lesson_sha256"}
        payload.update({
            "sequence": sequence, "category_id": card.category_id,
            "target_concept_id": "grammar:" + card.entry_id,
            "construction_label": card.entry_id,
            "form": card.form, "function": card.function,
            "attachment_rule": card.attachment_rule + (" Nota: " + card.notes if card.notes else ""),
            "register": card.usage_register,
            "example_sentence": card.example_sentence,
            "portuguese_translation": card.portuguese_translation,
            "spoken_sample": card.spoken_sample,
        })
        payload["content_hash"] = korean_grammar_canonical_json_sha256(payload)
        entry = KoreanGrammarEntry.model_validate(payload)
        required = {"grammar:" + p for p in course.prerequisite_closure(card.entry_id)}
        if not required <= set(entry.evidence.prerequisite_concept_ids):
            raise ValueError("course_evidence_omits_teaching_prerequisites")
        expected_observed = {"grammar:" + p for p in observations[card.entry_id].observed_grammar_ids}
        expected_observed.update("lexicon:" + item.entry_id for item in expected_lexical.values()
                                 if card.entry_id in item.used_by)
        # The existing curriculum contract includes the teaching context in
        # observed_concept_ids. The separate annotation retains surface-only
        # observations, so prerequisite closure is never mistaken for tokens.
        expected_observed.update(concept for concept in entry.evidence.prerequisite_concept_ids
                                 if concept.startswith(("grammar:", "lexicon:")))
        actual_observed = {concept for concept in entry.evidence.observed_concept_ids
                           if concept.startswith(("grammar:", "lexicon:"))}
        if actual_observed != expected_observed:
            raise ValueError("course_evidence_changes_semantic_observations")
        if entry.ready_state == "learner_ready" and support_report["unresolved"]:
            raise ValueError("unresolved_course_semantic_evidence")
        for part in (entry.source_binding, entry.review_binding,
                     entry.word_media_binding, entry.sentence_media_binding):
            if part.content_hash != grammar_content_hash(part):
                raise ValueError("course_evidence_hash_drift")
        if entry.ready_state == "learner_ready" and entry.review_binding.required_pass_count != 3:
            raise ValueError("critical_grammar_requires_three_review_passes")
        expected_policy = "contextual" if card.category_id == "G0" else "strict"
        if entry.evidence.policy != expected_policy:
            raise ValueError("course_orientation_or_strict_policy_mismatch")
        if entry.ready_state == "learner_ready" and (
            entry.review_binding.candidate_sha256 != grammar_candidate_sha256(entry)
            or entry.review_binding.source_sha256 != entry.source_binding.content_hash
            or entry.review_binding.media_sha256 != korean_grammar_canonical_json_sha256([
                entry.word_media_binding.content_hash, entry.sentence_media_binding.content_hash,
            ])
        ):
            raise ValueError("stale_course_review")
        for media, text in ((entry.word_media_binding, card.spoken_sample),
                            (entry.sentence_media_binding, card.example_sentence)):
            if media.text_sha256 != sha256(text.encode()).hexdigest():
                raise ValueError("course_audio_text_drift")
        entries.append(entry)
    options = (
        {"active_snapshot_resolver": active_snapshot_resolver}
        if active_snapshot_resolver is not None else {}
    )
    bundle = KoreanGrammarBundleBuilder(**options).build_bundle(
        lexical_bootstrap=binding.lexical_bootstrap,
        orientation_entries=tuple(entry for entry in entries if entry.category_id == "G0"),
        grammar_entries=tuple(entry for entry in entries if entry.category_id != "G0"),
    )
    validate_korean_grammar_strict_graph(bundle)
    curriculum_hash = grammar_review_curriculum_sha256(bundle)
    if any(entry.ready_state == "learner_ready"
           and entry.review_binding.curriculum_sha256 != curriculum_hash for entry in entries):
        raise ValueError("stale_course_curriculum_review")
    return bundle


def _analyze_course(course: KoreanGrammarCourse, analyzer=None) -> dict[str, Any]:
    if analyzer is None:
        from multilang.services.korean_morphology import KiwiKoreanMorphologyService

        analyzer = KiwiKoreanMorphologyService()
    sentences = dict.fromkeys(text for card in course.cards for text in (
        card.example_sentence, card.spoken_sample
    ))
    analyses = {text: analyzer.analyze(text) for text in sentences}
    rows = []
    for card in course.cards:
        for field in ("example_sentence", "spoken_sample"):
            text = getattr(card, field)
            result = analyses[text]
            rows.append({
                "entry_id": card.entry_id,
                "field": field,
                "text_sha256": sha256(text.encode()).hexdigest(),
                "analysis": result.model_dump(mode="json"),
            })
    unresolved = [
        {"entry_id": row["entry_id"], "field": row["field"],
         "status": row["analysis"]["status"]}
        for row in rows if row["analysis"]["status"] != "resolved"
    ]
    return {
        "status": "blocked" if unresolved else "analyzed",
        "fingerprint": analyzer.fingerprint.model_dump(mode="json"),
        "unresolved": unresolved,
        "records": rows,
        "note": "Analysis is evidence, not a lemma/sense decision or strict-i+1 approval.",
    }


def prepare_grammar_course(
    course: KoreanGrammarCourse, *, analyze: bool = True, analyzer=None,
    support: KoreanGrammarCourseSupport | None = None, lexical_source_bundle: Path | None = None,
) -> dict[str, Any]:
    """Recompute the inventory, dependency closure and exact audio work list."""
    lexical_first_use: dict[str, str] = {}
    for card in course.cards:
        for lemma in card.lexical_lemmas:
            lexical_first_use.setdefault(lemma, card.entry_id)
    audio_requests = [
        {"entry_id": card.entry_id, "role": role, "text": text,
         "text_sha256": sha256(text.encode()).hexdigest(), "characters": len(text)}
        for card in course.cards
        for role, text in (("word", card.spoken_sample), ("sentence", card.example_sentence))
    ]
    morphology = _analyze_course(course, analyzer) if analyze else {"status": "not_run"}
    blockers = [
        "linguistic_review_missing", "reviewed_audio_missing",
        "reviewed_lexical_bootstrap_missing", "strict_concept_mapping_missing",
        "current_foundation_authority_required", "morphology_identity_review_required",
    ]
    if morphology["status"] != "analyzed":
        blockers.append("morphology_not_validated")
    support_report = None
    if support is not None:
        support_report = validate_grammar_course_support(
            course, support, source_bundle_dir=lexical_source_bundle,
        )
        blockers.remove("strict_concept_mapping_missing")
        if support_report["progression_failures"]:
            blockers.append("strict_progression_failed")
        if support_report["unresolved"]:
            blockers.append("concept_observation_uncertainty")
        if support_report["source_status"] != "exact_source_rows_verified":
            blockers.append("lexical_source_rows_not_verified")
    report = {
        "schema_version": "korean-grammar-course-preparation-v1",
        "course_sha256": course.content_sha256,
        "grammar_card_count": len(course.cards),
        "orientation_card_count": sum(card.category_id == "G0" for card in course.cards),
        "strict_card_count": sum(card.category_id != "G0" for card in course.cards),
        "teaching_policy": {"G0": "guided_orientation", "G1-G13": "strict_i_plus_one"},
        "category_counts": dict(Counter(card.category_id for card in course.cards)),
        "learner_ready": False,
        "production_bundle_created": False,
        "blockers": blockers,
        "sources": COURSE_SOURCES,
        "support_sha256": korean_grammar_canonical_json_sha256(support) if support else None,
        "support": support_report,
        "prerequisites": {
            card.entry_id: list(course.prerequisite_closure(card.entry_id)) for card in course.cards
        },
        "lexical_bootstrap_candidates": [
            {"lemma": lemma, "first_used_by": entry_id, "status": "source_and_sense_review_required"}
            for lemma, entry_id in lexical_first_use.items()
        ],
        "audio_plan": {
            "requests": len(audio_requests),
            "characters": sum(row["characters"] for row in audio_requests),
            "unique_texts": len({row["text_sha256"] for row in audio_requests}),
            "provider": "azure", "locale": "ko-KR", "authorized": False,
            "bootstrap_audio_included": False,
            "items": audio_requests,
        },
        "morphology": morphology,
    }
    report["report_sha256"] = korean_grammar_canonical_json_sha256(report)
    return report


def _csv_cell(value: str) -> str:
    # Spreadsheet previews must not turn authored constructions into formulas.
    return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value


def _render_preview(course: KoreanGrammarCourse, support: KoreanGrammarCourseSupport | None = None) -> str:
    navigation = " ".join(f'<a href="#G{i}">G{i}</a>' for i in range(14))
    parts = ["""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Coreano — Partículas e terminações</title>
<style>body{max-width:860px;margin:40px auto;padding:0 20px;font:18px/1.6 system-ui;
color:#182629;background:#fafaf5}nav{display:flex;flex-wrap:wrap;gap:12px}a{color:#17614d}
article{padding:24px 0;border-bottom:1px solid #ccd8d0}h2{margin-top:48px}
.ko{font:1.5em/1.7 sans-serif}dt{font-weight:650}dd{margin:0 0 12px}
.note,small{color:#52625b}code{font-size:.8em}footer{overflow-wrap:anywhere}</style>
<h1>Partículas e terminações do coreano</h1>
<p>Prévia do conteúdo para leitura. A liberação do baralho com áudio depende
das evidências de produção indicadas no relatório de preparação.</p>""", f"<nav>{navigation}</nav>"]
    parts.append("<p>G0 é uma introdução guiada. A sequência estrita começa em G1, "
                 "depois da orientação e do vocabulário de apoio.</p>")
    if support is not None:
        parts.append('<h2 id="vocabulario">Vocabulário de apoio</h2><dl>')
        for entry in support.lexical.entries:
            if entry.teaching_mode == "lexical":
                parts.append(f'<dt lang="ko">{escape(entry.lemma)}</dt>'
                             f'<dd>{escape(entry.meaning_pt)}</dd>')
        parts.append("</dl>")
    current_category = None
    for card in course.cards:
        if card.category_id != current_category:
            current_category = card.category_id
            label = "G0 — Introdução guiada" if current_category == "G0" else current_category
            parts.append(f'<h2 id="{current_category}">{label}</h2>')
        parts.append(
            f'<article id="{card.entry_id}"><small>{card.entry_id}</small>'
            f'<h3 lang="ko">{escape(card.form)}</h3><p>{escape(card.function)}</p>'
            f'<dl><dt>Como se forma</dt><dd>{escape(card.attachment_rule)}</dd>'
            f'<dt>Registro</dt><dd lang="ko">{escape(card.usage_register)}</dd></dl>'
            f'<p class="ko" lang="ko">{escape(card.example_sentence)}</p>'
            f'<p>{escape(card.portuguese_translation)}</p>'
            f'<p class="note">{escape(card.notes)}</p>'
            '<p><small>Pré-requisitos: ' + (
                ", ".join(f'<a href="#{p}">{p}</a>' for p in card.prerequisite_ids)
                or "Hangul e vocabulário de apoio"
            ) + '</small></p></article>'
        )
    parts.append('<footer><h2>Referências</h2><ul>')
    for source in COURSE_SOURCES.values():
        parts.append(f'<li><a href="{source["url"]}">{escape(source["title"])}</a></li>')
    parts.append(f'</ul><small>Revisão: {course.content_sha256}</small></footer></html>')
    return "\n".join(parts)


def write_grammar_review_pack(
    course: KoreanGrammarCourse, output_dir: Path, *, analyze: bool = True, analyzer=None,
    lexical_source_bundle: Path | None = None,
    support: KoreanGrammarCourseSupport | None = None,
) -> dict[str, Any]:
    """Write a new review directory; never overwrite an existing pack or media."""
    report = prepare_grammar_course(course, analyze=analyze, analyzer=analyzer, support=support,
                                    lexical_source_bundle=lexical_source_bundle)
    bootstrap = (
        prepare_grammar_bootstrap_candidates(course, lexical_source_bundle)
        if lexical_source_bundle is not None else None
    )
    output_dir = Path(output_dir)
    if output_dir.is_symlink() or output_dir.exists():
        raise ValueError("grammar_review_output_already_exists")
    # User selects the directory; file names are fixed and never derived from card text.
    output_dir.mkdir(parents=True, exist_ok=False)
    table = io.StringIO(newline="")
    writer = csv.writer(table)
    writer.writerow(("ID", "Bloco", "Forma", "Função", "Formação", "Registro", "Exemplo",
                     "Tradução", "Amostra falada", "Pré-requisitos", "Vocabulário", "Notas", "SHA256"))
    for card in course.cards:
        writer.writerow([_csv_cell(text) for text in (
            card.entry_id, card.category_id, card.form, card.function, card.attachment_rule,
            card.usage_register, card.example_sentence, card.portuguese_translation, card.spoken_sample,
            ", ".join(card.prerequisite_ids), ", ".join(card.lexical_lemmas), card.notes,
            card.content_sha256,
        )])
    artifacts = {
        "course.json": course.model_dump_json(indent=2) + "\n",
        "preflight.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        "cards.csv": table.getvalue(),
        "evidence-schema.json": json.dumps(_CourseEvidence.model_json_schema(), indent=2) + "\n",
        "index.html": _render_preview(course, support),
    }
    if support is not None:
        artifacts["lexical-support.json"] = support.lexical.model_dump_json(indent=2) + "\n"
        artifacts["grammar-observations.json"] = support.observations.model_dump_json(indent=2) + "\n"
    if bootstrap is not None:
        artifacts["bootstrap-candidates.json"] = json.dumps(
            bootstrap, ensure_ascii=False, indent=2
        ) + "\n"
    for name, text in artifacts.items():
        with (output_dir / name).open("x", encoding="utf-8", newline="") as stream:
            stream.write(text)
    manifest = {"course_sha256": course.content_sha256, "members": {
        name: sha256(text.encode()).hexdigest() for name, text in artifacts.items()
    }}
    with (output_dir / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return report
