"""The authored Korean course must be inspectable without inventing approval."""

import importlib.util
import json
import unicodedata
from pathlib import Path

import pytest
from pydantic import ValidationError


def _course_api():
    assert importlib.util.find_spec("multilang.services.korean_grammar_course") is not None, (
        "the production grammar course authoring/validation service is missing"
    )
    from multilang.services import korean_grammar_course

    return korean_grammar_course


def test_authored_course_covers_every_approved_grammar_block():
    api = _course_api()
    course = api.load_grammar_course()
    assert {card.category_id for card in course.cards} == {f"G{i}" for i in range(14)}
    assert len(course.cards) >= 80
    assert all(card.function and card.attachment_rule and card.portuguese_translation for card in course.cards)
    assert len({card.entry_id for card in course.cards}) == len(course.cards)


def test_course_preflight_does_not_turn_authored_content_into_approved_content():
    api = _course_api()
    report = api.prepare_grammar_course(api.load_grammar_course(), analyze=False)
    assert report["learner_ready"] is False
    assert report["production_bundle_created"] is False
    assert "linguistic_review_missing" in report["blockers"]
    assert "reviewed_audio_missing" in report["blockers"]
    assert report["audio_plan"]["requests"] == 2 * report["grammar_card_count"]


def test_review_pack_is_reproducible_and_bound_to_real_content(tmp_path: Path):
    api = _course_api()
    course = api.load_grammar_course()
    left = api.write_grammar_review_pack(course, tmp_path / "left", analyze=False)
    right = api.write_grammar_review_pack(course, tmp_path / "right", analyze=False)
    assert left["course_sha256"] == right["course_sha256"]
    assert (tmp_path / "left" / "cards.csv").read_bytes() == (tmp_path / "right" / "cards.csv").read_bytes()
    assert (tmp_path / "left" / "index.html").is_file()
    assert not list((tmp_path / "left").glob("*.apkg"))


def test_invalid_text_dependencies_and_category_coverage_are_rejected():
    from multilang.domain.korean_grammar_course import KoreanGrammarCourse

    course = _course_api().load_grammar_course()
    for mutate in (
        lambda cards: cards[0].update(example_sentence=unicodedata.normalize("NFD", "학생이에요.")),
        lambda cards: cards[0].update(prerequisite_ids=[cards[-1]["entry_id"]]),
        lambda cards: cards[0].update(target_surfaces=["없는표면"]),
        lambda cards: cards[0].update(function="<script>alert(1)</script>"),
        lambda cards: cards[0].update(notes="x" * 2048),
        lambda cards: cards.append(cards[0]),
        lambda cards: cards.__setitem__(slice(None), [c for c in cards if c["category_id"] != "G13"]),
    ):
        rows = course.model_dump(mode="json")["cards"]
        mutate(rows)
        with pytest.raises(ValidationError):
            KoreanGrammarCourse(cards=rows)


def test_content_change_invalidates_course_and_lesson_hashes():
    from multilang.domain.korean_grammar_course import KoreanGrammarCourse

    course = _course_api().load_grammar_course()
    rows = course.model_dump(mode="json")["cards"]
    rows[0]["portuguese_translation"] += " (texto revisado)"
    changed = KoreanGrammarCourse(cards=rows)
    assert changed.content_sha256 != course.content_sha256
    assert changed.cards[0].content_sha256 != course.cards[0].content_sha256
    assert changed.cards[1].content_sha256 == course.cards[1].content_sha256


def test_preparation_never_overwrites_existing_files_or_follows_file_symlink(tmp_path):
    api = _course_api()
    course = api.load_grammar_course()
    output = tmp_path / "pack"
    output.mkdir()
    sentinel = output / "index.html"
    sentinel.write_text("keep")
    with pytest.raises(ValueError, match="already_exists"):
        api.write_grammar_review_pack(course, output, analyze=False)
    assert sentinel.read_text() == "keep"
    source = tmp_path / "source"
    source.mkdir()
    (source / "cards-g0-g6.json").symlink_to(sentinel)
    with pytest.raises(OSError):
        api.load_grammar_course(source)


def test_review_csv_neutralizes_formulas_without_changing_canonical_lesson(tmp_path):
    import csv

    api = _course_api()
    course = api.load_grammar_course()
    api.write_grammar_review_pack(course, tmp_path / "pack", analyze=False)
    with (tmp_path / "pack/cards.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert any(card.form.startswith("-") for card in course.cards)
    assert all(not row["Forma"].startswith(("=", "-", "+", "@")) for row in rows)
    saved = json.loads((tmp_path / "pack/course.json").read_text())
    assert saved == course.model_dump(mode="json")


def test_bootstrap_candidates_preserve_source_senses_and_do_not_infer_approval():
    api = _course_api()
    rows = api.parse_nikl_bootstrap_rows(
        "순위\t단어\t품사\t풀이\t등급\n"
        "1\t물01\t명\t\tA\n2\t물02\t명\t\tC\n3\t먹다02\t동\t\tA\n"
        "\t강원도\t고\t江原道\tB\n"
    )
    assert rows[0]["lemma"] == "물"
    assert rows[0]["source_form"] == "물01"
    assert rows[0]["sense_marker"] == "01"
    assert rows[0]["source_pos"] == "명"
    assert rows[0]["source_entry_sha256"] != rows[1]["source_entry_sha256"]
    assert rows[2]["lemma"] == "먹다"
    assert rows[3]["source_frequency_rank"] is None
    assert all(row["status"] == "sense_review_required" for row in rows)


def test_bootstrap_source_parser_rejects_malformed_rows():
    api = _course_api()
    with pytest.raises(ValueError, match="source_row"):
        api.parse_nikl_bootstrap_rows("순위\t단어\t품사\t풀이\t등급\n1\t물\t명\n")


def test_course_bundle_requires_complete_current_evidence_before_resolving_foundation():
    api = _course_api()
    course = api.load_grammar_course()

    def forbidden():
        raise AssertionError("invalid course evidence must fail before foundation access")

    with pytest.raises(ValueError, match="course_evidence"):
        api.build_grammar_course_bundle(course, {
            "course_sha256": course.content_sha256,
            "lexical_bootstrap": [], "lessons": [],
        }, active_snapshot_resolver=forbidden)


def _synthetic_course_evidence(course):
    """Reuse the grammar contract fixture; never a real production approval."""
    from hashlib import sha256

    from test_korean_grammar import _grammar_entry, _sealed, _source_binding

    api = _course_api()
    from multilang.domain.korean_grammar import korean_grammar_canonical_json_sha256 as digest

    support = api.load_grammar_course_support(course)
    bootstrap = []
    for lexical in support.lexical.entries:
        if lexical.teaching_mode != "lexical":
            continue
        source = _source_binding(synthetic=True)
        source.update(source_id=support.lexical.source_id, source_version=support.lexical.source_version,
                      entry_sha256=lexical.source_entry_sha256, bundle_sha256=support.lexical.source_sha256)
        target = "lexicon:" + lexical.entry_id
        bootstrap.append(_sealed({
            "entry_id": lexical.entry_id, "sequence": len(bootstrap) + 1,
            "target_concept_id": target, "lexical_identity_sha256": digest(lexical),
            "submitted_form": lexical.lemma, "canonical_nfc": lexical.lemma,
            "source_binding": _sealed(source), "observed_concept_ids": ["orthography.hangul", target],
            "prerequisite_concept_ids": ["orthography.hangul"], "learner_visible": True,
        }))

    lessons = []
    for card in course.cards:
        entry = _grammar_entry(ready_state="needs_review").model_dump(mode="json", by_alias=True)
        entry["source_binding"]["synthetic"] = True
        for field in ("source_binding", "review_binding", "word_media_binding", "sentence_media_binding"):
            binding = entry[field]
            if field.endswith("media_binding"):
                text = card.spoken_sample if field.startswith("word") else card.example_sentence
                binding["text_sha256"] = sha256(text.encode()).hexdigest()
                binding["integrity_status"] = "missing"
                binding["acoustic_review_status"] = "missing"
            if field == "review_binding":
                binding["consensus_status"] = "blocked_uncertainty"
                binding["deterministic_validator_result"] = "failed"
            binding.pop("content_hash", None)
            entry[field] = _sealed(binding)
        prereqs = ["orthography.hangul", "phonology.basic",
                   *(entry["target_concept_id"] for entry in bootstrap), *(
            "grammar:" + p for p in course.prerequisite_closure(card.entry_id)
        )]
        target = "grammar:" + card.entry_id
        annotation = next(row for row in support.observations.entries if row.entry_id == card.entry_id)
        observed = ["grammar:" + p for p in annotation.observed_grammar_ids]
        observed.extend("lexicon:" + e.entry_id for e in support.lexical.entries
                        if e.teaching_mode == "lexical" and card.entry_id in e.used_by)
        observed = list(dict.fromkeys([*prereqs, *observed]))
        lessons.append({
            "entry_id": card.entry_id, "lesson_sha256": card.content_sha256,
            "pronunciation_sample": card.spoken_sample,
            "source_binding": entry["source_binding"],
            "evidence": {"target_concept_id": target,
                         "policy": "contextual" if card.category_id == "G0" else "strict",
                         "prerequisite_concept_ids": prereqs,
                         "observed_concept_ids": observed,
                         "unknown_concept_ids": [p for p in observed
                                                 if p.startswith("grammar:")]
                         if card.category_id == "G0" else [target]},
            "review_binding": entry["review_binding"],
            "word_media_binding": entry["word_media_binding"],
            "sentence_media_binding": entry["sentence_media_binding"],
            "ready_state": "needs_review",
        })
    return {"course_sha256": course.content_sha256, "support_sha256": digest(support),
            "lexical_bootstrap": bootstrap, "lessons": lessons}


def test_course_binds_to_existing_bundle_without_promoting_missing_review_or_media():
    from test_korean_grammar import _snapshot

    from multilang.services.korean_grammar import validate_korean_grammar_production_readiness

    api = _course_api()
    course = api.load_grammar_course()
    evidence = _synthetic_course_evidence(course)
    bundle = api.build_grammar_course_bundle(course, evidence, active_snapshot_resolver=_snapshot)
    assert len(bundle.orientation_entries) == 8
    assert len(bundle.grammar_entries) + len(bundle.orientation_entries) == len(course.cards)
    assert bundle.orientation_entries[0].example_sentence == course.cards[0].example_sentence
    assert course.cards[0].notes in bundle.orientation_entries[0].attachment_rule
    result = validate_korean_grammar_production_readiness(bundle)
    assert result.ready_state == "blocked"
    assert {"missing_review", "missing_media", "synthetic_source"} <= set(result.blocked_reason_codes)

    evidence["lessons"][0]["lesson_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="stale_lesson_evidence"):
        api.build_grammar_course_bundle(course, evidence, active_snapshot_resolver=_snapshot)


def test_binding_cannot_override_text_or_drop_prerequisite_edges():
    from test_korean_grammar import _snapshot

    api = _course_api()
    course = api.load_grammar_course()
    evidence = _synthetic_course_evidence(course)
    evidence["lessons"][0]["example_sentence"] = "변조된 내용"
    with pytest.raises(ValueError, match="invalid_course_evidence"):
        api.build_grammar_course_bundle(course, evidence, active_snapshot_resolver=_snapshot)
    evidence["lessons"][0].pop("example_sentence")
    index = next(i for i, card in enumerate(course.cards) if card.prerequisite_ids)
    evidence["lessons"][index]["evidence"]["prerequisite_concept_ids"] = []
    with pytest.raises(ValueError, match="omits_teaching_prerequisites"):
        api.build_grammar_course_bundle(course, evidence, active_snapshot_resolver=_snapshot)


def test_compiler_rejects_missing_vocabulary_and_edited_observations():
    from test_korean_grammar import _snapshot

    api = _course_api()
    course = api.load_grammar_course()
    evidence = _synthetic_course_evidence(course)
    evidence["lexical_bootstrap"].pop()
    with pytest.raises(ValueError, match="lexical_inventory"):
        api.build_grammar_course_bundle(course, evidence, active_snapshot_resolver=_snapshot)
    evidence = _synthetic_course_evidence(course)
    row = evidence["lessons"][0]["evidence"]
    row["observed_concept_ids"] = [*row["prerequisite_concept_ids"], "grammar:g0.copula"]
    row["unknown_concept_ids"] = ["grammar:g0.copula"]
    with pytest.raises(ValueError, match="semantic_observations"):
        api.build_grammar_course_bundle(course, evidence, active_snapshot_resolver=_snapshot)


def test_compiler_rejects_bootstrap_content_hash_drift():
    from test_korean_grammar import _snapshot

    api = _course_api()
    course = api.load_grammar_course()
    evidence = _synthetic_course_evidence(course)
    evidence["lexical_bootstrap"][0]["content_hash"] = "0" * 64
    with pytest.raises(ValueError, match="lexical_identity_drift"):
        api.build_grammar_course_bundle(course, evidence, active_snapshot_resolver=_snapshot)


def test_support_recomputes_progression_and_keeps_orientation_separate():
    api = _course_api()
    course = api.load_grammar_course()
    support = api.load_grammar_course_support(course)
    result = api.validate_grammar_course_support(course, support)
    assert result["orientation_count"] == 8
    assert result["strict_count"] == 100
    assert not result["progression_failures"]
    assert result["lexical_entry_count"] == 57
    assert result["construction_entry_count"] == 29
    assert result["learner_ready"] is False
    assert all(r["unknown_grammar_ids"] == [r["entry_id"]]
               for r in result["progression"] if r["policy"] == "strict")


def test_support_rejects_drift_missing_coverage_and_hidden_forward_constructions():
    api = _course_api()
    from multilang.domain.korean_grammar_course import KoreanGrammarCourseSupport

    course = api.load_grammar_course()
    original = api.load_grammar_course_support(course)
    for mutate, reason in (
        (lambda p: p["lexical"].update(course_sha256="0" * 64), "stale"),
        (lambda p: p["observations"]["entries"].pop(), "inventory"),
        (lambda p: p["lexical"]["entries"].__setitem__(slice(None),
             [x for x in p["lexical"]["entries"] if x["lemma"] != "학생"]), "coverage"),
        (lambda p: p["lexical"]["entries"][-1]["used_by"].append("g1.present"), "forward"),
        (lambda p: p["lexical"]["entries"][0].update(source_entry_sha256="a" * 64), "source_identity"),
    ):
        payload = original.model_dump(mode="json")
        mutate(payload)
        with pytest.raises(ValueError, match=reason):
            api.validate_grammar_course_support(course, KoreanGrammarCourseSupport.model_validate(payload))
    payload = original.model_dump(mode="json")
    payload["observations"]["entries"][8]["observed_grammar_ids"].append("g13.shared-reminder")
    report = api.validate_grammar_course_support(course, KoreanGrammarCourseSupport.model_validate(payload))
    assert report["progression_failures"][0]["entry_id"] == "g1.topic"


def test_pack_includes_hash_bound_support_and_learner_glosses(tmp_path):
    api = _course_api()
    course = api.load_grammar_course()
    support = api.load_grammar_course_support(course)
    result = api.write_grammar_review_pack(course, tmp_path / "pack", analyze=False, support=support)
    manifest = json.loads((tmp_path / "pack/manifest.json").read_text())
    assert {"lexical-support.json", "grammar-observations.json"} <= set(manifest["members"])
    html = (tmp_path / "pack/index.html").read_text()
    assert "Introdução guiada" in html
    assert "Vocabulário de apoio" in html
    assert "estudante; pessoa que estuda" in html
    assert "Não classificar toda ocorrência como passiva" not in html
    assert result["support"]["course_sha256"] == course.content_sha256
    assert "strict_concept_mapping_missing" not in result["blockers"]
    assert "morphology_identity_review_required" in result["blockers"]
    schema = json.loads((tmp_path / "pack/evidence-schema.json").read_text())
    assert "support_sha256" in schema["required"]
    assert result["support_sha256"]
