"""Snapshot persistence must preserve pending work and never activate generation."""

import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, select

from multilang.domain.lexical_identity import canonical_sha256


def api():
    spec = importlib.util.find_spec("multilang.services.vocabulary_selection_snapshot")
    assert spec is not None, "Vocabulary selection snapshot service is missing"
    return importlib.import_module("multilang.services.vocabulary_selection_snapshot")


def fixture_plan(tmp_path):
    path = Path(__file__).with_name("test_vocabulary_session_partitions.py")
    spec = importlib.util.spec_from_file_location("partition_fixture", path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    from multilang.services.vocabulary_session_partitions import partition_vocabulary_sessions

    args = helper._source(tmp_path)
    import hashlib

    from multilang.services.vocabulary_session_review import (
        export_session_request,
        import_session_review,
    )

    source = args["packets"] / "en/00000.json"
    request = args["requests"] / "en"
    exported = export_session_request(
        source, hashlib.sha256(source.read_bytes()).hexdigest(), indices=[0, 1], output=request
    )
    import_session_review(
        request=request,
        request_sha256=exported["request_sha256"],
        response=helper._response(request),
        context_id="fixture",
        output=args["reviews"] / "en",
    )
    plan = tmp_path / "plan"
    partition_vocabulary_sessions(**args, output=plan)
    import json

    digest = canonical_sha256(json.loads((plan / "plan.json").read_text()))
    return plan, digest


def test_export_roundtrip_all_languages_pending_and_source_evidence(tmp_path):
    service = api()
    plan, digest = fixture_plan(tmp_path)
    output = tmp_path / "snapshot"
    result = service.export_selection_snapshot(
        plan=plan, plan_sha256=digest, work=tmp_path / "work", output=output
    )
    assert result["total_records"] == 8
    assert result["languages"]["en"]["include"] == 2
    assert result["languages"]["ja"]["unreviewed"] == 4
    assert result["production_eligible"] is False
    rows = list(service.snapshot_records(output))
    assert len(rows) == 8 and all(r["source_group"]["sense_candidates"] for r in rows)
    assert sum(r["decision"] == "include" for r in rows) == 2
    assert all(r["production_eligible"] is False for r in rows)
    with pytest.raises(ValueError, match="exist"):
        service.export_selection_snapshot(
            plan=plan, plan_sha256=digest, work=tmp_path / "work", output=output
        )
    # File corruption must fail before an import can publish any DB records.
    p = output / "inventory/en.jsonl"
    p.write_bytes(p.read_bytes() + b"{}\n")
    with pytest.raises(ValueError, match="hash"):
        list(service.snapshot_records(output))


def test_database_immutable_idempotent_and_queryable(tmp_path):
    service = api()
    plan, digest = fixture_plan(tmp_path)
    output = tmp_path / "snapshot"
    report = service.export_selection_snapshot(
        plan=plan, plan_sha256=digest, work=tmp_path / "work", output=output
    )
    engine = create_engine("sqlite:///" + str(tmp_path / "database.db"))
    service.migrate_selection_schema(engine)
    assert set(inspect(engine).get_table_names()) == {
        "vocabulary_selection_snapshots",
        "vocabulary_selection_units",
        "vocabulary_selection_schema_version",
    }
    first = service.persist_selection_snapshot(engine, output)
    again = service.persist_selection_snapshot(engine, output)
    assert first["snapshot_id"] == again["snapshot_id"] == report["snapshot_id"]
    assert again["status"] == "already_present"
    checked = service.verify_database_snapshot(engine, output)
    assert checked["verified_records"] == 8
    from multilang.db.vocabulary_selection_models import VocabularySelectionUnit

    with engine.connect() as c:
        rows = c.execute(
            select(VocabularySelectionUnit).where(VocabularySelectionUnit.language == "ja")
        ).all()
    assert len(rows) == 4


def test_manifest_traversal_and_duplicate_records_rejected(tmp_path):
    service = api()
    import json

    p = tmp_path / "snapshot"
    p.mkdir()
    manifest = {
        "schema_version": "vocabulary-selection-snapshot-1",
        "files": {"../escape": "a" * 64},
    }
    (p / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        list(service.snapshot_records(p))


def test_conflicting_derived_review_does_not_overwrite_new_import():
    service = api()
    source = {"lemma": "i"}
    row = {
        "source_group": source,
        "source_binding": {"packet_sha256": "a"},
        "imported_review": {"review_sha256": "new"},
        "decision": "exclude",
    }
    overlay = {
        "provenance": {
            "historical_imported_review": {"review_sha256": "old", "packet_sha256": "a"},
            "source_group": source,
        },
        "resolved_content": {"resolved_unit_disposition": "include", "resolved_candidates": []},
    }
    got = service._apply_overlay(row, overlay)
    assert got["decision"] == "uncertain"
    assert got["imported_review"]["review_sha256"] == "new"
    assert got["derived_review_conflict"] == overlay
    assert "resolved_content" not in got
    row = {
        "source_group": source,
        "source_binding": {"packet_sha256": "a"},
        "imported_review": {"review_sha256": "old"},
        "decision": "exclude",
    }
    assert service._apply_overlay(row, overlay)["decision"] == "include"


def test_invalid_duplicate_rolls_back_entire_database_import(tmp_path):
    service = api()
    import hashlib
    import json

    from sqlalchemy import func

    from multilang.db.vocabulary_selection_models import VocabularySelectionSnapshot

    plan, digest = fixture_plan(tmp_path)
    output = tmp_path / "snapshot"
    service.export_selection_snapshot(
        plan=plan, plan_sha256=digest, work=tmp_path / "work", output=output
    )
    file = output / "inventory/en.jsonl"
    lines = file.read_text().splitlines()
    lines[1] = lines[0]
    file.write_text("\n".join(lines) + "\n")
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["files"]["inventory/en.jsonl"] = hashlib.sha256(file.read_bytes()).hexdigest()
    manifest["snapshot_id"] = canonical_sha256(
        {k: v for k, v in manifest.items() if k != "snapshot_id"}
    )
    (output / "manifest.json").write_text(json.dumps(manifest))
    engine = create_engine("sqlite:///" + str(tmp_path / "db.sqlite"))
    service.migrate_selection_schema(engine)
    with pytest.raises(ValueError, match="duplicate"):
        service.persist_selection_snapshot(engine, output)
    with engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(VocabularySelectionSnapshot)) == 0


def test_portable_zip_contains_verified_snapshot_and_refuses_overwrite(tmp_path):
    service = api()
    assert hasattr(service, "bundle_selection_snapshot"), "Portable archive is missing"
    import zipfile

    plan, digest = fixture_plan(tmp_path)
    output = tmp_path / "snapshot"
    service.export_selection_snapshot(
        plan=plan, plan_sha256=digest, work=tmp_path / "work", output=output
    )
    archive = tmp_path / "selection.zip"
    receipt = service.bundle_selection_snapshot(output, archive)
    assert receipt["bytes"] == archive.stat().st_size
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert z.read("snapshot/inventory/en.jsonl") == (output / "inventory/en.jsonl").read_bytes()
        assert z.read("snapshot/manifest.json") == (output / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="exist"):
        service.bundle_selection_snapshot(output, archive)
