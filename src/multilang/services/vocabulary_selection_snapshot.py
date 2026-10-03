"""Export and persist source-bound vocabulary preparation without generation."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import insert, select

from multilang.db.vocabulary_selection_models import (
    VocabularySelectionSnapshot,
    VocabularySelectionUnit,
)
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine_runner import _locked, read_json
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_session_campaign import _catalog, _review_state
from multilang.services.vocabulary_session_partitions import _assignment, _load_plan, _local_state

SCHEMA = "vocabulary-selection-snapshot-1"
DECISIONS = {"include", "exclude", "uncertain", "unreviewed", "quarantined"}


def _sha(path):
    with _plain_path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def _write_json(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")


def _line(f, value):
    f.write(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        + "\n"
    )


def _now():
    return datetime.now(UTC).isoformat()


def _nordic_overlay(version_path):
    """Explicitly requested derived version; no discovery by recency or filename."""
    if version_path is None:
        return {}, {}, {}, {}
    version = read_json(_plain_path(version_path))
    if version.get("schema_version") != "composed-vocabulary-preparation-version-1":
        raise ValueError("unsupported vocabulary overlay version")
    root = Path.cwd().resolve()
    allowed = root / "output/reports/vocabulary-qualification"
    attachments = {"nordic-version.json": version}
    units, additions, metadata = {}, {}, {}

    def bound(reference):
        path = _plain_path(root / reference["path"]).resolve()
        if not path.is_relative_to(allowed):
            raise ValueError("overlay path outside vocabulary reports")
        if _sha(path) != reference["sha256"]:
            raise ValueError("overlay hash changed")
        return path

    approved = read_json(bound(version["approved_decisions"]))
    attachments["approved-decisions.json"] = approved
    if version.get("root_predicate_correction"):
        attachments["root-predicate-correction.json"] = read_json(
            bound(version["root_predicate_correction"])
        )
    for lang, refs in version["languages"].items():
        if lang not in {"da", "nb", "sv"}:
            raise ValueError("unexpected overlay language")
        with bound(refs["base_inventory"]).open() as f:
            for line in f:
                row = json.loads(line)
                key = (lang, row["review_unit_id"])
                if row["language"] != lang or key in units:
                    raise ValueError("duplicate overlay unit")
                units[key] = row
        metadata[lang] = read_json(bound(refs["base_metadata"]))
        additions[lang] = read_json(bound(refs["additions"]))
        corrections = read_json(bound(refs["candidate_corrections"]))
        for patch in corrections:
            row = units[(lang, patch["review_unit_id"])]
            candidates = [
                c
                for c in row["resolved_content"]["resolved_candidates"]
                if c["source_candidate_id"] == patch["source_candidate_id"]
            ]
            if (
                len(candidates) != 1
                or [candidates[0]["lemma"], candidates[0]["pos"]] != patch["before"]
            ):
                raise ValueError("overlay candidate correction precondition failed")
            candidates[0]["lemma"], candidates[0]["pos"] = patch["after"]
            row.setdefault("snapshot_candidate_corrections", []).append(patch)
        attachments[f"{lang}-metadata.json"] = metadata[lang]
        attachments[f"{lang}-corrections.json"] = corrections
        attachments[f"{lang}-annotation-links.json"] = read_json(
            bound(refs["annotation_compatibility_layer"])
        )
        attachments[f"{lang}-review-decisions.json"] = read_json(bound(refs["review_decisions"]))
    return units, additions, metadata, attachments


def _apply_overlay(row, overlay):
    if overlay is None:
        return row
    historical = overlay["provenance"]["historical_imported_review"]
    current = row.get("imported_review") or {}
    if (
        historical.get("review_sha256") != current.get("review_sha256")
        or historical.get("packet_sha256") != row["source_binding"]["packet_sha256"]
        or overlay["provenance"]["source_group"] != row["source_group"]
    ):
        row["derived_review_conflict"] = overlay
        row["decision"] = "uncertain"
        row["selection_origin"] = "conflicting_review_versions_preserved_for_reconciliation"
    else:
        row["resolved_content"] = overlay["resolved_content"]
        row["derived_review_provenance"] = {
            k: v for k, v in overlay.items() if k not in {"resolved_content", "provenance"}
        }
        row["decision"] = overlay["resolved_content"]["resolved_unit_disposition"]
        row["selection_origin"] = "source_bound_derived_review"
    return row


def export_selection_snapshot(
    *,
    plan: Path,
    plan_sha256: str,
    work: Path,
    output: Path,
    nordic_version: Path | None = None,
    progress=None,
) -> dict:
    output, work = _plain_path(output), _plain_path(work)
    if output.exists():
        raise ValueError("snapshot destination already exists")
    plan, data, references = _load_plan(plan, plan_sha256)
    for relative, digest in data["baseline_files"].items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or path.parts[0] != "baseline":
            raise ValueError("invalid baseline path")
        _read_bytes(plan / path, digest, limit=128 * 1024**2)
    _, _, packet_loader = _catalog(Path(data["packets_directory"]), data["packets_manifest_sha256"])
    _, baseline = _review_state(
        packet=packet_loader, requests=plan / "baseline/requests", reviews=plan / "baseline/reviews"
    )
    if len(baseline) != data["baseline_reviewed_units"]:
        raise ValueError("baseline replay count mismatch")
    overlays, additions, metadata, attachments = _nordic_overlay(nordic_version)
    started = _now()
    languages = sorted({ref["language"] for ref in references.values()})
    if any(not re.fullmatch("[a-z]{2}", lang) for lang in languages):
        raise ValueError("invalid language code")
    counts = {lang: Counter({d: 0 for d in DECISIONS}) for lang in languages}
    seen, applied, session_observations = set(), set(), []
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".selection-", dir=output.parent) as temporary:
        stage = Path(temporary) / "snapshot"
        (stage / "inventory").mkdir(parents=True)
        (stage / "selected").mkdir()
        (stage / "attachments").mkdir()
        with ExitStack() as stack:
            full = {
                lang: stack.enter_context(
                    (stage / f"inventory/{lang}.jsonl").open("x", encoding="utf-8")
                )
                for lang in languages
            }
            selected = {
                lang: stack.enter_context(
                    (stage / f"selected/{lang}.jsonl").open("x", encoding="utf-8")
                )
                for lang in languages
            }

            def emit(row):
                key = (row["language"], row["review_unit_id"])
                if key in seen or row["decision"] not in DECISIONS:
                    raise ValueError("duplicate record or invalid decision")
                seen.add(key)
                row.update(
                    record_id=canonical_sha256(list(key)),
                    production_eligible=False,
                    generation_status="deferred_by_user",
                )
                counts[key[0]][row["decision"]] += 1
                if "derived_review_conflict" in row:
                    counts[key[0]]["overlay_conflicts"] += 1
                _line(full[key[0]], row)
                if row["decision"] == "include":
                    _line(selected[key[0]], row)

            for number, (sid, reference) in enumerate(references.items(), 1):
                assignment, members, packet = _assignment(plan, data, reference)
                folder = work / sid
                observed_start = _now()
                if folder.exists():
                    deadline = time.monotonic() + 30
                    while True:
                        try:
                            with _locked(folder / "operation"):
                                _, _, local = _local_state(work, assignment, members, packet)
                            break
                        except ValueError as exc:
                            if (
                                "holds this output lock" not in str(exc)
                                or time.monotonic() >= deadline
                            ):
                                raise
                            time.sleep(0.1)
                else:
                    local = {}
                lang = assignment["language"]
                for uid, member in members.items():
                    key = (lang, uid)
                    review = baseline.get(key) if member["baseline"] is not None else local.get(key)
                    source = packet(member["packet_sha256"])["groups"][member["source_index"]]
                    if source["review_unit_id"] != uid:
                        raise ValueError("source unit identity mismatch")
                    row = {
                        "schema_version": "vocabulary-selection-unit-1",
                        "language": lang,
                        "review_unit_id": uid,
                        "session_id": sid,
                        "source_group": source,
                        "source_binding": {
                            k: member[k]
                            for k in ("packet_sha256", "packet_path", "source_index", "entry_id")
                        },
                        "imported_review": review,
                        "decision": review["decision"] if review else "unreviewed",
                        "selection_origin": "frozen_baseline"
                        if member["baseline"] is not None
                        else "active_imported_review"
                        if review
                        else "not_yet_reviewed",
                    }
                    overlay = overlays.get(key)
                    if overlay is not None:
                        applied.add(key)
                        row = _apply_overlay(row, overlay)
                    emit(row)
                session_observations.append(
                    {
                        "session_id": sid,
                        "started_at": observed_start,
                        "finished_at": _now(),
                        "assignment_sha256": reference["sha256"],
                        "units": len(members),
                    }
                )
                if progress and number % 20 == 0:
                    progress(f"{number}/{len(references)} sessions captured")
            if len(seen) != data["total_units"] or applied != set(overlays):
                raise ValueError("inventory or overlay has missing assigned units")
            for lang, items in additions.items():
                for item in items:
                    emit(
                        {
                            "schema_version": "vocabulary-selection-unit-1",
                            "language": lang,
                            "review_unit_id": item["addition_id"],
                            "session_id": None,
                            "source_group": None,
                            "source_binding": None,
                            "imported_review": None,
                            "decision": "include",
                            "selection_origin": "independently_sourced_addition",
                            "supplemental_identity": item,
                        }
                    )
        for name, value in attachments.items():
            _write_json(stage / "attachments" / name, value)
        _write_json(stage / "sessions.json", session_observations)
        totals = {
            lang: {**dict(c), "total": sum(c[d] for d in DECISIONS)} for lang, c in counts.items()
        }
        _write_json(stage / "languages.json", totals)
        text = [
            "# Seleção de vocabulário — todos os idiomas",
            "",
            "Fotografia versionada da preparação. Não contém novos cartões, traduções, áudio ou decks.",
            "inventory/ preserva todas as unidades, decisões, fontes, sentidos e formas; selected/ contém apenas unidades incluídas.",
            "Inclusão de uma unidade não aprova todos os seus sentidos: use selected_candidate_ids/selected_forms da revisão, ou disposition=retained no resolved_content.",
            "Os estados uncertain, quarantined e unreviewed continuam explícitos. Nenhuma entrada é liberada automaticamente para geração.",
            "As sessões foram lidas sequencialmente com exclusão mútua por sessão; esta fotografia não é um instante global atômico.",
            "As decisões nórdicas derivadas e seus seis acréscimos são incorporados quando a revisão de origem ainda coincide; divergências preservam as duas versões para reconciliação.",
            "",
            "| Idioma | Incluídas | Excluídas | Dúvidas | Quarentena | Não revisadas |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        text += [
            f"| {lang} | {c['include']} | {c['exclude']} | {c['uncertain']} | {c['quarantined']} | {c['unreviewed']} |"
            for lang, c in totals.items()
        ]
        (stage / "README.md").write_text("\n".join(text) + "\n", encoding="utf-8")
        manifest = {
            "schema_version": SCHEMA,
            "started_at": started,
            "finished_at": _now(),
            "plan_sha256": plan_sha256,
            "source_units": data["total_units"],
            "total_records": len(seen),
            "session_count": len(references),
            "languages": totals,
            "language_metadata": metadata,
            "attachments": attachments,
            "production_eligible": False,
            "generation_status": "deferred_by_user",
            "temporal_scope": "sequential_locked_session_observations",
            "files": {
                str(p.relative_to(stage)): _sha(p) for p in sorted(stage.rglob("*")) if p.is_file()
            },
        }
        manifest["snapshot_id"] = canonical_sha256(manifest)
        _write_json(stage / "manifest.json", manifest)
        stage.rename(output)
    return manifest


def _manifest(output):
    output = _plain_path(output)
    manifest = read_json(output / "manifest.json")
    if (
        manifest.get("schema_version") != SCHEMA
        or manifest.get("production_eligible") is not False
        or manifest.get("generation_status") != "deferred_by_user"
        or manifest.get("snapshot_id")
        != canonical_sha256({k: v for k, v in manifest.items() if k != "snapshot_id"})
    ):
        raise ValueError("invalid snapshot manifest binding")
    for name, digest in manifest["files"].items():
        p = Path(name)
        if (
            p.is_absolute()
            or ".." in p.parts
            or not (output / p).resolve().is_relative_to(output.resolve())
        ):
            raise ValueError("invalid snapshot path")
        if _sha(output / p) != digest:
            raise ValueError("snapshot file hash mismatch")
    return manifest


def snapshot_records(output):
    manifest = _manifest(output)
    seen = set()
    counts = {lang: Counter() for lang in manifest["languages"]}
    for lang in sorted(manifest["languages"]):
        name = f"inventory/{lang}.jsonl"
        if name not in manifest["files"] or not re.fullmatch("[a-z]{2}", lang):
            raise ValueError("missing inventory file")
        with (output / name).open() as f:
            for line in f:
                row = json.loads(line)
                key = canonical_sha256([lang, row["review_unit_id"]])
                if (
                    row["language"] != lang
                    or row["record_id"] != key
                    or key in seen
                    or row["decision"] not in DECISIONS
                    or row.get("production_eligible") is not False
                    or row.get("generation_status") != "deferred_by_user"
                ):
                    raise ValueError("invalid or duplicate snapshot record")
                seen.add(key)
                counts[lang][row["decision"]] += 1
                yield row
    if len(seen) != manifest["total_records"]:
        raise ValueError("snapshot count mismatch")
    for lang, c in counts.items():
        if any(c[d] != manifest["languages"][lang][d] for d in DECISIONS):
            raise ValueError("snapshot decision count mismatch")


def migrate_selection_schema(engine):
    from alembic.config import Config

    from alembic import command

    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).parents[1] / "db/selection_migrations")
    )
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "selection_0001")


def persist_selection_snapshot(engine, output):
    manifest = _manifest(output)
    sid = manifest["snapshot_id"]
    with engine.begin() as connection:
        # Serialize imports of the same immutable version without blocking other versions.
        if engine.dialect.name == "postgresql":
            from sqlalchemy import text

            connection.execute(
                text("SELECT pg_advisory_xact_lock(:key)"), {"key": int(sid[:15], 16)}
            )
        existing = (
            connection.execute(
                select(VocabularySelectionSnapshot).where(VocabularySelectionSnapshot.id == sid)
            )
            .mappings()
            .first()
        )
        if existing:
            if existing["manifest_sha256"] != _sha(output / "manifest.json"):
                raise ValueError("stored snapshot version conflict")
            status = "already_present"
        else:
            connection.execute(
                insert(VocabularySelectionSnapshot),
                {
                    "id": sid,
                    "manifest_sha256": _sha(output / "manifest.json"),
                    "total_records": manifest["total_records"],
                    "payload": manifest,
                },
            )
            batch = []
            for row in snapshot_records(output):
                batch.append(
                    {
                        "snapshot_id": sid,
                        "record_id": row["record_id"],
                        "language": row["language"],
                        "decision": row["decision"],
                        "payload_sha256": canonical_sha256(row),
                        "payload": row,
                    }
                )
                if len(batch) >= 200:
                    connection.execute(insert(VocabularySelectionUnit), batch)
                    batch = []
            if batch:
                connection.execute(insert(VocabularySelectionUnit), batch)
            status = "inserted"
    return {"status": status, "snapshot_id": sid, "records": manifest["total_records"]}


def verify_database_snapshot(engine, output):
    manifest = _manifest(output)
    expected = {row["record_id"]: canonical_sha256(row) for row in snapshot_records(output)}
    count = 0
    with engine.connect() as connection:
        stored = (
            connection.execute(
                select(VocabularySelectionSnapshot).where(
                    VocabularySelectionSnapshot.id == manifest["snapshot_id"]
                )
            )
            .mappings()
            .one()
        )
        if stored["payload"] != manifest or stored["manifest_sha256"] != _sha(
            output / "manifest.json"
        ):
            raise ValueError("database manifest differs from file")
        rows = (
            connection.execution_options(stream_results=True)
            .execute(
                select(VocabularySelectionUnit).where(
                    VocabularySelectionUnit.snapshot_id == manifest["snapshot_id"]
                )
            )
            .mappings()
        )
        for row in rows:
            payload = row["payload"]
            actual = canonical_sha256(payload)
            if (
                expected.pop(row["record_id"], None) != actual
                or row["payload_sha256"] != actual
                or payload["language"] != row["language"]
                or payload["decision"] != row["decision"]
            ):
                raise ValueError("database snapshot payload mismatch")
            count += 1
    if expected or count != manifest["total_records"]:
        raise ValueError("database snapshot count mismatch")
    return {"status": "verified", "snapshot_id": manifest["snapshot_id"], "verified_records": count}


def bundle_selection_snapshot(output, archive):
    """Create a portable ZIP, verifying the bytes actually archived against the manifest."""
    from zipfile import ZIP_DEFLATED, ZipFile

    output, archive = _plain_path(output), _plain_path(archive)
    if archive.exists():
        raise ValueError("archive destination already exists")
    manifest = _manifest(output)
    files = {**manifest["files"], "manifest.json": _sha(output / "manifest.json")}
    archive.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".selection-zip-", dir=archive.parent) as temporary:
        stage = Path(temporary) / "selection.zip"
        with ZipFile(stage, "w", compression=ZIP_DEFLATED, compresslevel=6) as z:
            for name, expected in sorted(files.items()):
                h = hashlib.sha256()
                with (
                    (output / name).open("rb") as src,
                    z.open("snapshot/" + name, "w", force_zip64=True) as dst,
                ):
                    while chunk := src.read(1024 * 1024):
                        h.update(chunk)
                        dst.write(chunk)
                if h.hexdigest() != expected:
                    raise ValueError("file changed while creating archive")
        with ZipFile(stage) as z:
            if z.testzip() is not None:
                raise ValueError("archive checksum verification failed")
        stage.rename(archive)
    return {
        "snapshot_id": manifest["snapshot_id"],
        "archive": str(archive),
        "sha256": _sha(archive),
        "bytes": archive.stat().st_size,
        "files": len(files),
    }
