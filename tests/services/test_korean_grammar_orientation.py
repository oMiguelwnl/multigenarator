"""Guided G0 introduces a block of concepts before strict grammar lessons."""

from hashlib import sha256

import pytest
from test_korean_grammar import (
    _bootstrap_teaching_fixture,
    _exportable_bundle,
    _grammar_entry,
    _seal_export_reviews,
    _sealed,
    _snapshot,
)

from multilang.domain.korean_grammar import (
    KoreanGrammarEntry,
    build_bundle_sha256,
    korean_grammar_canonical_json_sha256,
)
from multilang.services.korean_grammar import (
    KoreanGrammarBundleBuilder,
    validate_korean_grammar_production_readiness,
)
from multilang.services.korean_grammar_export import (
    assemble_korean_grammar_export_rows,
    grammar_candidate_sha256,
    grammar_review_curriculum_sha256,
)

BASE = ("orthography.hangul", "phonology.basic")
GUIDES = ("grammar:guide-word-order", "grammar:guide-particles")


def _replace(entry, **changes):
    payload = entry.model_dump(mode="json", by_alias=True)
    payload.update(changes)
    return KoreanGrammarEntry(**_sealed(payload))


def _entries():
    guides = tuple(
        _replace(
            _grammar_entry(
                target=target, sequence=index + 1, category_id="G0", policy="contextual",
                prerequisites=(*BASE, *GUIDES[:index]), observed=(*BASE, *GUIDES), unknown=GUIDES,
            ),
            entry_id=f"guide.{index + 1:03d}",
        )
        for index, target in enumerate(GUIDES)
    )
    strict = _grammar_entry(prerequisites=(*BASE, *GUIDES))
    return guides, strict


def _build(guides=None, strict=None, *, bootstrap=()):
    defaults, default_strict = _entries()
    return KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=bootstrap,
        orientation_entries=defaults if guides is None else guides,
        grammar_entries=(default_strict if strict is None else strict,),
    )


def _reviewed_bundle(tmp_path, *, with_bootstrap=False):
    if with_bootstrap:
        old, paths, teaching = _bootstrap_teaching_fixture(tmp_path)
        bootstrap = old.lexical_bootstrap
    else:
        old, paths = _exportable_bundle(tmp_path)
        bootstrap, teaching = (), None
    guides, strict = _entries()
    template = old.grammar_entries[0]

    def media(entry):
        return _replace(entry, source_binding=template.source_binding.model_dump(mode="json"),
            word_media_binding=template.word_media_binding.model_dump(mode="json"),
            sentence_media_binding=template.sentence_media_binding.model_dump(mode="json"))

    bundle = _build(tuple(media(e) for e in guides), media(strict), bootstrap=bootstrap)

    def reviewed(entry):
        review = entry.review_binding.model_dump(mode="json")
        review.update(candidate_sha256=grammar_candidate_sha256(entry),
            source_sha256=entry.source_binding.content_hash,
            curriculum_sha256=grammar_review_curriculum_sha256(bundle),
            media_sha256=korean_grammar_canonical_json_sha256([
                entry.word_media_binding.content_hash, entry.sentence_media_binding.content_hash]))
        return _replace(entry, review_binding=_sealed(review))

    bundle = _build(tuple(reviewed(e) for e in bundle.orientation_entries),
        reviewed(bundle.grammar_entries[0]), bootstrap=bootstrap)
    if teaching is not None:
        from multilang.domain.korean_grammar_bootstrap import KoreanGrammarBootstrapCard
        payload = teaching.model_dump(mode="json")
        payload["review_binding"]["curriculum_sha256"] = bundle.bundle_sha256
        payload["review_binding"] = _sealed(payload["review_binding"])
        teaching = KoreanGrammarBootstrapCard(**_sealed(payload))
    return bundle, paths, (() if teaching is None else (teaching,))


def test_guided_block_introduces_multiple_unknowns_before_strict_g1():
    bundle = _build()
    result = validate_korean_grammar_production_readiness(bundle)
    assert result.ready_state == "learner_ready"
    assert result.admitted_orientation_concept_ids == GUIDES
    assert result.admitted_grammar_concept_ids == (bundle.grammar_entries[0].target_concept_id,)
    assert tuple(c.id for c in bundle.overlay_concepts) == (*GUIDES, bundle.grammar_entries[0].target_concept_id)
    assert bundle.orientation_entries[1].evidence.unknown_concept_ids == GUIDES
    assert "orientation_entries" in bundle.member_hashes


@pytest.mark.parametrize("category,policy", [("G1", "contextual"), ("G0", "strict"), ("G0", "adaptive")])
def test_orientation_rejects_non_g0_or_non_contextual(category, policy):
    guides, strict = _entries()
    payload = guides[0].evidence.model_dump(mode="json")
    payload["policy"] = policy
    with pytest.raises(ValueError):
        _build((_replace(guides[0], category_id=category, evidence=payload), guides[1]), strict)


@pytest.mark.parametrize("failure", ["future_observed", "undeclared_observed", "unknowns", "forward_prerequisite", "closure", "cycle"])
def test_orientation_rejects_hidden_future_concepts_and_invalid_graph(failure):
    guides, strict = _entries()
    evidence = guides[0].evidence.model_dump(mode="json")
    if failure in {"future_observed", "undeclared_observed"}:
        concept = strict.target_concept_id if failure == "future_observed" else "lexicon:undeclared"
        evidence["observed_concept_ids"].append(concept)
        evidence["unknown_concept_ids"].append(concept)
    elif failure == "unknowns":
        evidence["unknown_concept_ids"] = [GUIDES[0]]
    elif failure == "forward_prerequisite":
        evidence["prerequisite_concept_ids"].append(strict.target_concept_id)
    elif failure == "closure":
        evidence["prerequisite_concept_ids"] = ["phonology.basic"]
    else:
        evidence["prerequisite_concept_ids"].append(GUIDES[1])
    with pytest.raises(ValueError):
        _build((_replace(guides[0], evidence=evidence), guides[1]), strict)


@pytest.mark.parametrize("failure", ["missing_review", "missing_media"])
def test_unreviewed_orientation_blocks_production_readiness(failure):
    guides, strict = _entries()
    payload = guides[0].model_dump(mode="json")
    payload["ready_state"] = "blocked"
    if failure == "missing_review":
        payload["review_binding"]["consensus_status"] = "blocked_disagreement"
        payload["review_binding"] = _sealed(payload["review_binding"])
    else:
        payload["word_media_binding"]["integrity_status"] = "missing"
        payload["word_media_binding"] = _sealed(payload["word_media_binding"])
    bundle = _build((KoreanGrammarEntry(**_sealed(payload)), guides[1]), strict)
    result = validate_korean_grammar_production_readiness(bundle)
    assert result.ready_state == "blocked"
    assert failure in result.blocked_reason_codes


def test_empty_orientation_preserves_legacy_bundle_and_member_hashes():
    builder = KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot)
    entry = _grammar_entry(prerequisites=BASE)
    old = builder.build_bundle(lexical_bootstrap=(), grammar_entries=(entry,))
    old_payload = old.model_dump(mode="json", by_alias=True)
    old_payload.pop("bundle_sha256")
    old_payload.pop("orientation_entries", None)
    legacy_hash = korean_grammar_canonical_json_sha256(old_payload)
    current = builder.build_bundle(lexical_bootstrap=(), orientation_entries=(), grammar_entries=(entry,))
    assert current.bundle_sha256 == old.bundle_sha256 == legacy_hash
    assert current.member_hashes == old.member_hashes
    assert "orientation_entries" not in current.member_hashes
    assert "orientation_entries" not in current.model_dump(mode="json")
    assert build_bundle_sha256({**old_payload, "orientation_entries": []}) == legacy_hash


def test_legacy_export_retains_existing_sequence_sort_indices(tmp_path):
    bundle, paths = _exportable_bundle(tmp_path)
    entry = _replace(bundle.grammar_entries[0], sequence=7)
    bundle = KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=(), grammar_entries=(entry,))
    bundle = _seal_export_reviews(bundle)
    exported = assemble_korean_grammar_export_rows(bundle=bundle, job_id="legacy",
        media_paths=paths, active_snapshot_resolver=_snapshot)
    assert exported.rows[0].identity.sort_index == 7


def test_export_orders_bootstrap_then_guided_g0_then_strict_g1(tmp_path):
    bundle, paths, teaching = _reviewed_bundle(tmp_path, with_bootstrap=True)
    exported = assemble_korean_grammar_export_rows(bundle=bundle, job_id="orientation",
        media_paths=paths, bootstrap_cards=teaching, active_snapshot_resolver=_snapshot)
    assert [r.identity.item_key for r in exported.rows] == [bundle.lexical_bootstrap[0].entry_id,
        *[e.entry_id for e in bundle.orientation_entries], bundle.grammar_entries[0].entry_id]
    assert [r.identity.sort_index for r in exported.rows] == [1, 2, 3, 4]
    assert all("Introdução guiada" in r.definitions for r in exported.rows[1:3])
    assert all("strict" not in r.definitions and "i+1" not in r.definitions for r in exported.rows[1:3])


def test_orientation_export_rechecks_active_foundation(tmp_path):
    bundle, paths, teaching = _reviewed_bundle(tmp_path)
    changed = _snapshot()
    changed.bundle_sha256 = sha256(b"new-foundation").hexdigest()
    with pytest.raises(ValueError, match="active foundation evidence drift"):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="orientation",
            media_paths=paths, bootstrap_cards=teaching, active_snapshot_resolver=lambda: changed)


@pytest.mark.parametrize("failure", ["candidate", "curriculum", "media_bytes", "source"])
def test_orientation_export_requires_exact_current_review_and_media(tmp_path, failure):
    bundle, paths, teaching = _reviewed_bundle(tmp_path)
    guide = bundle.orientation_entries[0]
    if failure == "media_bytes":
        paths[guide.word_media_binding.artifact_sha256].write_bytes(b"changed")
    else:
        payload = guide.model_dump(mode="json")
        if failure == "candidate":
            payload["function"] = "outra explicação"
        elif failure == "curriculum":
            payload["review_binding"]["curriculum_sha256"] = sha256(b"stale").hexdigest()
            payload["review_binding"] = _sealed(payload["review_binding"])
        else:
            payload["source_binding"]["entry_sha256"] = sha256(b"different-source").hexdigest()
            payload["source_binding"] = _sealed(payload["source_binding"])
        bundle = _build((KoreanGrammarEntry(**_sealed(payload)), bundle.orientation_entries[1]),
            bundle.grammar_entries[0])
    with pytest.raises(ValueError):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="orientation",
            media_paths=paths, bootstrap_cards=teaching, active_snapshot_resolver=_snapshot)


def test_runtime_import_persists_orientation_inventory_and_total(tmp_path, monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from multilang.db.base import Base
    from multilang.services import korean_foundation_snapshot
    from multilang.services.korean_learning_runtime import KoreanLearningRuntime
    monkeypatch.setattr(korean_foundation_snapshot, "resolve_active_korean_foundation_snapshot", _snapshot)
    bundle = _build()
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'orientation.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        runtime = KoreanLearningRuntime(session)
        result = runtime.import_grammar_bundle(bundle=bundle)
        assert result["imported"] == 3
        assert runtime._job(result["job_id"]).total_items == 3
        assert [item.item_id for item in runtime._inventory(result["job_id"], "grammar")] == [
            *[e.entry_id for e in bundle.orientation_entries], bundle.grammar_entries[0].entry_id]
    with Session(engine) as session:
        assert KoreanLearningRuntime(session).load_grammar_bundle(result["job_id"]) == bundle
    engine.dispose()
