"""Service contracts for Korean grammar roots, overlays, and strict evidence."""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
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


def _exportable_bundle(tmp_path, *, ready_state="learner_ready", bad_text=False):
    from support.audio import SILENT_MP3

    from multilang.services.korean_grammar import KoreanGrammarBundleBuilder

    entry = _grammar_entry(prerequisites=("orthography.hangul", "phonology.basic"), ready_state=ready_state)
    payload = entry.model_dump(mode="json", by_alias=True)
    payload["source_binding"] = _sealed(payload["source_binding"])
    paths = {}
    for role, text in (("word", entry.spoken_sample), ("sentence", entry.example_sentence)):
        path = tmp_path / f"{role}.mp3"
        path.write_bytes(SILENT_MP3 * (1 if role == "word" else 2))
        digest = sha256(path.read_bytes()).hexdigest()
        paths[digest] = path
        binding = payload[f"{role}_media_binding"]
        binding["artifact_sha256"] = digest
        binding["text_sha256"] = sha256(("stale" if bad_text else text).encode()).hexdigest()
        payload[f"{role}_media_binding"] = _sealed(binding)
    entry = _grammar_domain().KoreanGrammarEntry(**_sealed(payload))
    bundle = KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=(), grammar_entries=(entry,),
    )
    return _seal_export_reviews(bundle), paths


def _seal_export_reviews(bundle):
    from multilang.services.korean_grammar_export import (
        grammar_candidate_sha256,
        grammar_review_curriculum_sha256,
    )
    entries = []
    for entry in bundle.grammar_entries:
        payload = entry.model_dump(mode="json", by_alias=True)
        review = payload["review_binding"]
        review.update(candidate_sha256=grammar_candidate_sha256(entry),
            source_sha256=entry.source_binding.content_hash,
            curriculum_sha256=grammar_review_curriculum_sha256(bundle),
            media_sha256=_canonical_hash([entry.word_media_binding.content_hash, entry.sentence_media_binding.content_hash]))
        payload["review_binding"] = _sealed(review)
        entries.append(_grammar_domain().KoreanGrammarEntry(**_sealed(payload)))
    return _grammar_service().KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=bundle.lexical_bootstrap, grammar_entries=tuple(entries))


def test_grammar_export_assembles_reviewed_content_with_all_teaching_fields(tmp_path):
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows

    bundle, paths = _exportable_bundle(tmp_path)
    result = assemble_korean_grammar_export_rows(
        bundle=bundle, job_id="grammar-export", media_paths=paths, active_snapshot_resolver=_snapshot,
    )
    assert len(result.rows) == 1
    row = result.rows[0]
    entry = bundle.grammar_entries[0]
    assert row.word == entry.form
    assert all(value in row.definitions for value in (entry.function, entry.attachment_rule, entry.register, entry.spoken_sample))
    assert row.translation == entry.portuguese_translation
    assert row.image == ""
    assert set(result.media_index.values()) == set(paths.values())


def test_grammar_export_rejects_undecodable_media_even_with_matching_receipts(tmp_path):
    from multilang.services.korean_grammar import KoreanGrammarBundleBuilder
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows

    bundle, paths = _exportable_bundle(tmp_path)
    payload = bundle.grammar_entries[0].model_dump(mode="json", by_alias=True)
    path = paths.pop(payload["word_media_binding"]["artifact_sha256"])
    path.write_bytes(b"ID3 invalid MP3")
    digest = sha256(path.read_bytes()).hexdigest()
    paths[digest] = path
    payload["word_media_binding"]["artifact_sha256"] = digest
    payload["word_media_binding"] = _sealed(payload["word_media_binding"])
    bundle = KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=(), grammar_entries=(_grammar_domain().KoreanGrammarEntry(**_sealed(payload)),))
    bundle = _seal_export_reviews(bundle)

    with pytest.raises(ValueError, match="audio must be decodable MP3"):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="grammar-export", media_paths=paths,
            active_snapshot_resolver=_snapshot)


def test_grammar_changed_text_cannot_reuse_linguistic_review(tmp_path):
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows
    bundle, paths = _exportable_bundle(tmp_path)
    payload = bundle.grammar_entries[0].model_dump(mode="json", by_alias=True)
    payload["portuguese_translation"] = "Outra tradução sem revisão."
    entry = _grammar_domain().KoreanGrammarEntry(**_sealed(payload))
    changed = _grammar_service().KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=(), grammar_entries=(entry,))
    with pytest.raises(ValueError, match="review"):
        assemble_korean_grammar_export_rows(bundle=changed, job_id="grammar-export", media_paths=paths,
            active_snapshot_resolver=_snapshot)


@pytest.mark.parametrize("name", ['bad".mp3', "<script>.mp3", "bad\\path.mp3"])
def test_grammar_media_names_cannot_inject_sound_field_markup(tmp_path, name):
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows
    bundle, paths = _exportable_bundle(tmp_path)
    digest = next(iter(paths))
    renamed = tmp_path / name
    paths[digest].rename(renamed)
    paths[digest] = renamed
    with pytest.raises(ValueError, match="basename"):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="grammar-export", media_paths=paths,
            active_snapshot_resolver=_snapshot)


def test_grammar_delivery_ids_cannot_collide(tmp_path):
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows
    bundle, paths = _exportable_bundle(tmp_path)
    bundle = bundle.model_copy(update={"grammar_entries": bundle.grammar_entries * 2})
    with pytest.raises(ValueError, match="identifiers"):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="grammar-export", media_paths=paths,
            active_snapshot_resolver=_snapshot)


def _bootstrap_teaching_fixture(tmp_path):
    from support.audio import SILENT_MP3

    from multilang.domain.korean_grammar import korean_grammar_canonical_json_sha256
    from multilang.domain.korean_grammar_bootstrap import (
        KoreanGrammarBootstrapCard,
        bootstrap_candidate_sha256,
    )
    from multilang.services.korean_grammar import KoreanGrammarBundleBuilder

    simple, paths = _exportable_bundle(tmp_path)
    bootstrap = _bootstrap(source=_sealed(_source_binding()))
    bundle = KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=(bootstrap,), grammar_entries=simple.grammar_entries)
    bundle = _seal_export_reviews(bundle)
    payload = dict(entry_id=bootstrap.entry_id, bootstrap_sha256=bootstrap.content_hash,
        definitions="saudação formal", ipa="", example_sentence=bootstrap.canonical_nfc + ".",
        portuguese_translation="Olá.")
    media_hashes = []
    for role, text in (("word", bootstrap.canonical_nfc), ("sentence", payload["example_sentence"])):
        path = tmp_path / f"bootstrap-{role}.mp3"
        path.write_bytes(SILENT_MP3 * (3 if role == "word" else 4))
        digest = sha256(path.read_bytes()).hexdigest()
        paths[digest] = path
        binding = simple.grammar_entries[0].word_media_binding.model_dump(mode="json")
        binding.update(text_sha256=sha256(text.encode()).hexdigest(), artifact_sha256=digest)
        payload[f"{role}_media_binding"] = _sealed(binding)
        media_hashes.append(payload[f"{role}_media_binding"]["content_hash"])
    review = _review_binding()
    review.update(source_sha256=bootstrap.source_binding.content_hash,
        candidate_sha256=bootstrap_candidate_sha256(payload), curriculum_sha256=bundle.bundle_sha256,
        media_sha256=korean_grammar_canonical_json_sha256(media_hashes))
    payload["review_binding"] = _sealed(review)
    return bundle, paths, KoreanGrammarBootstrapCard(**_sealed(payload))


def test_bootstrap_cards_are_reviewed_and_delivered_before_grammar(tmp_path):
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows
    bundle, paths, teaching = _bootstrap_teaching_fixture(tmp_path)
    result = assemble_korean_grammar_export_rows(bundle=bundle, job_id="grammar-export", media_paths=paths,
        bootstrap_cards=(teaching,), active_snapshot_resolver=_snapshot)
    assert [row.identity.item_key for row in result.rows] == [bundle.lexical_bootstrap[0].entry_id, bundle.grammar_entries[0].entry_id]
    assert [row.sort_index for row in result.rows] == [1, 2]
    assert len(result.media_index) == 4
    assert result.rows[0].translation == teaching.portuguese_translation


def test_bootstrap_export_rejects_resealed_bundle_with_stale_metadata_hash(tmp_path):
    from multilang.domain.korean_grammar_bootstrap import KoreanGrammarBootstrapCard
    from multilang.services.korean_grammar import KoreanGrammarBundleBuilder
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows

    bundle, paths, teaching = _bootstrap_teaching_fixture(tmp_path)
    changed = bundle.lexical_bootstrap[0].model_copy(update={"lexical_identity_sha256": SHA_B})
    bundle = KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(
        lexical_bootstrap=(changed,), grammar_entries=bundle.grammar_entries)
    bundle = _seal_export_reviews(bundle)
    payload = teaching.model_dump(mode="json")
    payload["review_binding"]["curriculum_sha256"] = bundle.bundle_sha256
    payload["review_binding"] = _sealed(payload["review_binding"])
    teaching = KoreanGrammarBootstrapCard(**_sealed(payload))

    with pytest.raises(ValueError, match="bootstrap source or curriculum review drift"):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="grammar-export", media_paths=paths,
            bootstrap_cards=(teaching,), active_snapshot_resolver=_snapshot)


@pytest.mark.parametrize("failure", ["missing", "duplicate", "content", "review", "bytes", "curriculum"])
def test_bootstrap_delivery_rejects_incomplete_or_stale_evidence(tmp_path, failure):
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows
    bundle, paths, teaching = _bootstrap_teaching_fixture(tmp_path)
    if failure == "content":
        teaching = teaching.model_copy(update={"definitions": "changed"})
    if failure in {"review", "curriculum"}:
        review = teaching.review_binding.model_copy(update={
            "consensus_status": "stale"} if failure == "review" else {"curriculum_sha256": "f" * 64})
        teaching = teaching.model_copy(update={"review_binding": review})
    if failure == "bytes":
        paths[teaching.word_media_binding.artifact_sha256].write_bytes(b"changed")
    cards = () if failure == "missing" else (teaching, teaching) if failure == "duplicate" else (teaching,)
    with pytest.raises(ValueError):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="grammar-export", media_paths=paths,
            bootstrap_cards=cards, active_snapshot_resolver=_snapshot)


@pytest.mark.parametrize("export_format", ["apkg", "csv", "tsv"])
@pytest.mark.parametrize("with_bootstrap", [False, True])
def test_runtime_grammar_export_updates_readiness_only_while_evidence_is_current(tmp_path, monkeypatch, export_format, with_bootstrap):
    import json

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from multilang.db.base import Base
    from multilang.services import korean_foundation_snapshot, korean_grammar_export
    from multilang.services.korean_learning_runtime import KoreanLearningRuntime

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    bootstrap_file = None
    if with_bootstrap:
        bundle, paths, teaching = _bootstrap_teaching_fixture(media_dir)
        bootstrap_file = tmp_path / "bootstrap.json"
        bootstrap_file.write_text(json.dumps([teaching.model_dump(mode="json")]), encoding="utf-8")
    else:
        bundle, paths = _exportable_bundle(media_dir)
    expected_cards = 2 if with_bootstrap else 1
    assembler = korean_grammar_export.assemble_korean_grammar_export_rows
    monkeypatch.setattr(korean_grammar_export, "assemble_korean_grammar_export_rows",
        lambda **kwargs: assembler(**kwargs, active_snapshot_resolver=_snapshot))
    monkeypatch.setattr(korean_foundation_snapshot, "resolve_active_korean_foundation_snapshot", _snapshot)
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'grammar.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        runtime = KoreanLearningRuntime(session)
        job_id = runtime.import_grammar_bundle(bundle=bundle)["job_id"]
        assert runtime.process(job_id=job_id, source="grammar", mode="start")["review_required"] == expected_cards
        exported = runtime.export_grammar(job_id=job_id, media_dir=media_dir,
            output_dir=tmp_path / "export", export_format=export_format, bootstrap_cards_file=bootstrap_file)
        assert exported["card_count"] == expected_cards
        if export_format != "apkg":
            assert {p.name for p in (tmp_path / "export" / "collection.media").iterdir()} == {p.name for p in paths.values()}
    with Session(engine) as session:
        reopened = KoreanLearningRuntime(session)
        assert reopened.status(job_id)["safe_sources"]["grammar"]["ready_count"] == expected_cards
        assert reopened.process(job_id=job_id, source="grammar", mode="resume")["accepted"] == expected_cards
        if export_format != "apkg":
            delivered = next((tmp_path / "export" / "collection.media").iterdir())
            original = delivered.read_bytes()
            delivered.write_bytes(b"changed copy")
            assert reopened.status(job_id)["safe_sources"]["grammar"]["ready_count"] == 0
            delivered.write_bytes(original)
            assert reopened.status(job_id)["safe_sources"]["grammar"]["ready_count"] == expected_cards
        next(iter(paths.values())).write_bytes(b"changed")
        assert reopened.status(job_id)["safe_sources"]["grammar"]["ready_count"] == 0


@pytest.mark.parametrize("failure", ["text", "bytes", "review", "bundle", "snapshot", "empty"])
def test_grammar_export_blocks_stale_content_or_missing_review(tmp_path, failure):
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows

    bundle, paths = _exportable_bundle(
        tmp_path, ready_state="needs_review" if failure == "review" else "learner_ready", bad_text=failure == "text",
    )
    if failure == "bytes":
        next(iter(paths.values())).write_bytes(b"changed")
    if failure == "bundle":
        bundle = bundle.model_copy(update={"bundle_sha256": "f" * 64})
    if failure == "empty":
        bundle = _grammar_service().KoreanGrammarBundleBuilder(active_snapshot_resolver=_snapshot).build_bundle(lexical_bootstrap=(), grammar_entries=())
    snapshot = _snapshot()
    if failure == "snapshot":
        snapshot.bundle_sha256 = "d" * 64
    with pytest.raises(ValueError):
        assemble_korean_grammar_export_rows(bundle=bundle, job_id="grammar-export", media_paths=paths, active_snapshot_resolver=lambda: snapshot)


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
