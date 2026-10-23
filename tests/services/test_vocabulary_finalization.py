"""Acceptance checks for derived inventories; no provider or native review writes."""

import copy
import hashlib
import json

import pytest

from multilang.services.vocabulary_finalization import (
    consolidate,
    publish_inventory,
    source_order_preview,
)


def unit(
    uid="one", *, entry="entry", lemma="Haus", pos="NOUN", candidate="sense-a", decision="include"
):
    group = dict(
        entry_id=entry,
        review_unit_id=uid,
        lemma=lemma,
        pos=pos,
        sense_candidates=[
            dict(candidate_id=candidate, glosses=["house"], source_record_sha256="a" * 64)
        ],
        readings=[],
        forms_for_review=[],
        provisional_order=9999,
        source_priority=1,
    )
    review = dict(
        entry_id=entry,
        review_unit_id=uid,
        lemma=lemma,
        pos=pos,
        display=lemma,
        decision=decision,
        selected_candidate_ids=[candidate] if decision == "include" else [],
        selected_forms=[],
        human_approved=False,
        production_eligible=False,
        review_sha256="b" * 64,
    )
    return dict(
        language="de",
        group=group,
        decision=review,
        human_approved=False,
        production_eligible=False,
        generation_status="deferred_by_user",
    )


def test_fragments_consolidate_without_losing_senses_or_inventing_frequency():
    rows = [unit(), unit("two", candidate="sense-b"), unit("pending", decision="uncertain")]
    before = copy.deepcopy(rows)
    result = consolidate(rows, language="de")
    assert rows == before
    assert len(result["identities"]) == 1
    identity = result["identities"][0]
    assert len(identity["senses"]) == 2
    assert identity["final_frequency_rank"] is None
    assert result["pending_review_units"] == ["pending"]
    assert consolidate(reversed(rows), language="de") == result


def test_same_spelling_different_source_identity_or_pos_never_merged():
    result = consolidate(
        [unit(), unit("two", entry="other"), unit("three", pos="VERB")], language="de"
    )
    assert len(result["identities"]) == 3


def test_own_readings_and_selected_forms_keep_their_candidate_parent():
    row = unit()
    row["group"]["readings"] = [
        dict(candidate_id="sense-a", form="Haus", reading="haus"),
        dict(candidate_id="unselected", form="Haus", reading="wrong"),
    ]
    row["group"]["forms_for_review"] = [
        dict(form_id="plural", form="Häuser", evidence_candidate_ids=["sense-a"])
    ]
    row["decision"]["selected_forms"] = [
        dict(form_id="plural", parent_candidate_id="sense-a", reason="irregularity")
    ]
    identity = consolidate([row], language="de")["identities"][0]
    assert identity["senses"][0]["readings"] == [row["group"]["readings"][0]]
    assert identity["forms"][0]["selection"]["parent_candidate_id"] == "sense-a"


@pytest.mark.parametrize(
    "damage",
    ["duplicate", "unknown_candidate", "unknown_form", "wrong_language", "source_conflict"],
)
def test_invalid_bindings_fail_closed(damage):
    row = unit()
    rows = [row]
    if damage == "duplicate":
        rows.append(copy.deepcopy(row))
    elif damage == "unknown_candidate":
        row["decision"]["selected_candidate_ids"] = ["missing"]
    elif damage == "unknown_form":
        row["decision"]["selected_forms"] = [dict(form_id="missing", parent_candidate_id="sense-a")]
    elif damage == "wrong_language":
        row["language"] = "en"
    else:
        other = unit("two")
        other["group"]["sense_candidates"][0]["glosses"] = ["conflicting"]
        rows.append(other)
    with pytest.raises(ValueError):
        consolidate(rows, language="de")


def test_resolved_content_keeps_candidate_corrections_and_partial_uncertainty():
    row = unit()
    row = dict(
        language="de",
        review_unit_id="one",
        decision="include",
        source_group=row["group"],
        imported_review=row["decision"],
        resolved_content=dict(
            resolved_candidates=[
                dict(
                    source_candidate_id="sense-a",
                    disposition="retained",
                    lemma="Häuschen",
                    pos="NOUN",
                    evidence=[{"note": "source-bound correction"}],
                ),
            ],
            derived_identities=[],
        ),
    )
    result = consolidate([row], language="de")
    assert result["identities"][0]["lemma"] == "Häuschen"
    assert result["identities"][0]["senses"][0]["resolution"]["evidence"]
    assert result["snapshot_rows"][0]["resolved_content"] == row["resolved_content"]


def test_published_order_ties_expansions_and_senses_stay_with_parent():
    rows = [unit(str(i), entry=str(i), lemma=f"word{i}") for i in range(3002)]
    result = consolidate(rows, language="de")
    evidence = [
        dict(
            identity_id=r["identity_id"],
            source_rank=i + 1,
            source_record_sha256="c" * 64,
            source_locator=str(i),
        )
        for i, r in enumerate(result["identities"])
    ]
    source = dict(
        rank_meaning="published_frequency",
        counting_unit="lemma-pos",
        source_id="test",
        version="1",
        sha256="d" * 64,
        license="test-fixture",
    )
    preview = source_order_preview(result["identities"], evidence, source=source)
    assert len(preview["ordered"]) == 3002
    assert [preview["ordered"][i]["band"] for i in [999, 1000, 1999, 2000, 2999, 3000]] == [
        "core-1",
        "core-2",
        "core-2",
        "core-3",
        "core-3",
        "expansion",
    ]
    assert preview["final_frequency_approved"] is False
    assert source_order_preview(result["identities"], reversed(evidence), source=source) == preview
    assert (
        source_order_preview(result["identities"], evidence[:1], source=source)[
            "unranked_identity_count"
        ]
        == 3001
    )
    for meaning in ("source_ordinal", "candidate_priority_only"):
        with pytest.raises(ValueError):
            source_order_preview(
                result["identities"], evidence, source={**source, "rank_meaning": meaning}
            )


def test_versioned_export_validates_hashes_and_never_overwrites(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(json.dumps(unit()) + "\n")
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "new-version"
    summary = publish_inventory(
        inputs=[dict(language="de", path=str(source), sha256=sha)], output=output
    )
    assert summary["languages"]["de"]["included_identities"] == 1
    from multilang.services.vocabulary_selection_snapshot import snapshot_records

    assert len(list(snapshot_records(output / "snapshot"))) == 1
    with pytest.raises(ValueError):
        publish_inventory(inputs=[dict(language="de", path=str(source), sha256=sha)], output=output)
    source.write_text("changed")
    with pytest.raises(ValueError):
        publish_inventory(
            inputs=[dict(language="de", path=str(source), sha256=sha)], output=tmp_path / "bad"
        )
    assert not (tmp_path / "bad").exists()


def test_snapshot_metadata_and_attachments_are_preserved_and_hash_checked(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(json.dumps(unit()) + "\n")
    attachment = tmp_path / "links.json"
    attachment.write_text('{"reviewed":true}')
    manifest = tmp_path / "source-manifest.json"
    metadata = {"de": {"derived_identities": [{"id": "retained-relation-target"}]}}
    manifest.write_text(
        json.dumps(
            dict(
                language_metadata=metadata,
                attachments=["links.json"],
                files={"links.json": hashlib.sha256(attachment.read_bytes()).hexdigest()},
            )
        )
    )
    inputs = [
        dict(
            language="de",
            path=str(source),
            sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            source_manifest=dict(
                path=str(manifest), sha256=hashlib.sha256(manifest.read_bytes()).hexdigest()
            ),
        )
    ]
    output = tmp_path / "result"
    publish_inventory(inputs=inputs, output=output)
    produced = json.loads((output / "snapshot/manifest.json").read_bytes())
    assert produced["language_metadata"] == metadata
    assert len(produced["attachments"]) == 1
    copied = next(iter(produced["attachments"]))
    assert (output / "snapshot" / copied).read_bytes() == attachment.read_bytes()
    attachment.write_text('{"reviewed":false}')
    with pytest.raises(ValueError):
        publish_inventory(inputs=inputs, output=tmp_path / "bad-attachment")


def test_input_symlink_is_rejected(tmp_path):
    source = tmp_path / "source.jsonl"
    source.write_text(json.dumps(unit()) + "\n")
    link = tmp_path / "link.jsonl"
    link.symlink_to(source)
    with pytest.raises(ValueError):
        publish_inventory(
            inputs=[
                dict(
                    language="de",
                    path=str(link),
                    sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                )
            ],
            output=tmp_path / "result",
        )


def test_form_attestation_candidate_can_differ_from_selected_lexical_parent():
    row = unit(lemma="der", pos="DET")
    row["group"]["forms_for_review"] = [
        dict(
            form_id="den",
            form="den",
            evidence_candidate_ids=["inflection-record"],
            parent_entry_ids=["entry"],
            source_parent_lemmas=["der"],
        )
    ]
    row["decision"]["selected_forms"] = [
        dict(
            form_id="den",
            form="den",
            parent_candidate_id="sense-a",
            reason="frequent_grammatical_contrast",
        )
    ]
    result = consolidate([row], language="de")
    assert result["identities"][0]["forms"][0]["source"]["evidence_candidate_ids"] == [
        "inflection-record"
    ]
    row["group"]["forms_for_review"][0]["parent_entry_ids"] = ["unrelated-entry"]
    with pytest.raises(ValueError):
        consolidate([row], language="de")


@pytest.mark.parametrize("damage", ["decision", "packet", "resolution_unit", "form_text"])
def test_independent_review_binding_mismatches_are_rejected(damage):
    base = unit()
    row = dict(
        language="de",
        review_unit_id="one",
        decision="include",
        source_group=base["group"],
        imported_review=base["decision"],
    )
    if damage == "decision":
        row["imported_review"]["decision"] = "exclude"
    elif damage == "packet":
        row["source_binding"] = {"packet_sha256": "a" * 64}
        row["imported_review"]["packet_sha256"] = "b" * 64
    elif damage == "resolution_unit":
        row["resolved_content"] = dict(review_unit_id="other", resolved_candidates=[])
    else:
        row["source_group"]["forms_for_review"] = [
            dict(form_id="plural", form="Häuser", evidence_candidate_ids=["sense-a"])
        ]
        row["imported_review"]["selected_forms"] = [
            dict(form_id="plural", form="incorrect", parent_candidate_id="sense-a")
        ]
    with pytest.raises(ValueError):
        consolidate([row], language="de")


def test_preview_validates_source_hash_and_cannot_approve_evidence():
    identity = consolidate([unit()], language="de")["identities"][0]
    source = dict(
        source_id="test",
        version="1",
        sha256="a" * 64,
        license="fixture",
        rank_meaning="published_frequency",
        counting_unit="lemma-pos",
    )
    evidence = [
        dict(
            identity_id=identity["identity_id"],
            source_rank=1,
            source_record_sha256="b" * 64,
            source_locator="1",
            production_eligible=True,
            human_approved=True,
            final_frequency_approved=True,
        )
    ]
    preview = source_order_preview([identity], evidence, source=source)
    for field in ("production_eligible", "human_approved", "final_frequency_approved"):
        assert preview["ordered"][0][field] is False
    with pytest.raises(ValueError):
        source_order_preview([identity], evidence, source={**source, "sha256": "invalid"})


def test_supplemental_forms_are_retained_without_authorizing_cards():
    row = dict(
        language="de",
        review_unit_id="addition",
        decision="include",
        supplemental_identity=dict(
            addition_id="added",
            decision="accepted_in_preparation_version",
            lemma="Haus",
            pos="NOUN",
            evidence=[{"source": "fixture"}],
            forms=[
                dict(
                    form="Häuser",
                    disposition="retained",
                    morphology={"Number": "Plur"},
                    source="fixture",
                    canonical_generation=False,
                )
            ],
        ),
    )
    identity = consolidate([row], language="de")["identities"][0]
    assert identity["retained_forms"][0]["source_form"] == row["supplemental_identity"]["forms"][0]
    assert identity["retained_forms"][0]["selected_for_card"] is False


def test_explicit_derived_homonyms_and_missing_pos_survive_consolidation():
    base = unit()
    resolved = [
        dict(
            source_candidate_id="sense-a",
            derived_candidate_id=name,
            homonym=name,
            disposition="retained",
            lemma="for",
            pos="NOUN",
            evidence=[{"source": "fixture"}],
        )
        for name in ("feed", "lining")
    ]
    resolved.append(
        dict(
            source_candidate_id="sense-a",
            derived_candidate_id="abbreviation",
            lemma="min.",
            pos=None,
            disposition="retained",
            evidence=[{"source": "fixture"}],
        )
    )
    row = dict(
        language="de",
        review_unit_id="one",
        decision="include",
        source_group=base["group"],
        imported_review=base["decision"],
        resolved_content=dict(resolved_candidates=resolved, resolved_forms=[]),
    )
    result = consolidate([row], language="de")
    assert len(result["identities"]) == 2
    assert result["partially_unresolved_units"] == ["one"]
    assert (
        result["preparation_findings"][0]["unresolved_questions"][0]["type"]
        == "preparation_missing_pos"
    )
    assert result["snapshot_rows"][0]["resolved_content"] == row["resolved_content"]
    row["resolved_content"]["resolved_candidates"] = resolved[-1:]
    assert consolidate([row], language="de")["identities"] == []
