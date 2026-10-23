"""Immutable offline consolidation of reviewed proposals, not production approval.

Only fragments of an exact source entry and resolved lemma/POS are joined.
Candidate IDs, own readings, derived corrections and form parents survive the
join. This does not infer cross-dictionary equivalence or lemma frequencies.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.services.vocabulary_finalization_resolved import adapt_resolved
from multilang.services.vocabulary_form_association import (
    SCHEMA as FORM_SCHEMA,
)
from multilang.services.vocabulary_form_association import (
    validate_coverage,
    validate_form_link,
)

FLAGS = dict(human_approved=False, production_eligible=False, generation_status="deferred_by_user")
DECISIONS = {"include", "exclude", "uncertain", "unreviewed", "quarantined"}


def _canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _hash(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError("missing or invalid lexical text")
    if any(unicodedata.category(c).startswith("C") for c in value):
        raise ValueError("control character in lexical text")
    return unicodedata.normalize("NFC", value)


def _normalize(row, language):
    row = copy.deepcopy(row)
    if row.get("language") != language:
        raise ValueError("inventory language mismatch")
    if isinstance(row.get("decision"), dict):
        review = row.pop("decision")
        group = row.pop("group")
        row.update(
            decision=review["decision"],
            imported_review=review,
            source_group=group,
            review_unit_id=group["review_unit_id"],
            source_binding=dict(
                entry_id=group["entry_id"],
                packet_path=row.get("source_packet_path"),
                packet_sha256=row.get("source_packet_sha256"),
                source_index=row.get("source_index"),
            ),
        )
    uid = row["review_unit_id"]
    if row["decision"] not in DECISIONS or not isinstance(uid, str) or not uid:
        raise ValueError("invalid review unit")
    group, review = row.get("source_group"), row.get("imported_review")
    resolved = row.get("resolved_content")
    if resolved and resolved.get("review_unit_id", uid) != uid:
        raise ValueError("resolution unit binding differs")
    if review:
        if (
            not resolved
            and not row.get("supplemental_identity")
            and review.get("decision") != row["decision"]
        ):
            raise ValueError("decision differs without derived resolution")
        packet = (row.get("source_binding") or {}).get("packet_sha256")
        if packet and review.get("packet_sha256") and packet != review["packet_sha256"]:
            raise ValueError("review packet binding differs")
    if group:
        if group["review_unit_id"] != uid:
            raise ValueError("source unit binding differs")
        if review and (review["review_unit_id"] != uid or review["entry_id"] != group["entry_id"]):
            raise ValueError("review identity binding differs")
    row.update(
        schema_version="vocabulary-selection-unit-1", record_id=_hash([language, uid]), **FLAGS
    )
    return row


def consolidate(rows, *, language):
    """Return a deterministic preparation view; never infer a semantic decision."""
    if not re.fullmatch("[a-z]{2}", language):
        raise ValueError("invalid language")
    rows = sorted((_normalize(r, language) for r in rows), key=lambda r: r["review_unit_id"])
    if not rows or len(rows) > 250_000:
        raise ValueError("inventory must contain bounded nonempty review units")
    if len({r["review_unit_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate review unit")
    parents, pending, partial, findings = {}, [], [], []
    form_rows = []

    def add(row, entry, lemma, pos, candidate_id, metadata, resolution=None):
        lemma, pos = _text(lemma), _text(pos)
        if pos.casefold() in {"x", "unknown", "unresolved", "none", "null"}:
            raise ValueError("included candidate requires resolved POS")
        identity_scope = (resolution or {}).get("resolved_identity_key")
        identity_parts = [language, entry, lemma, pos]
        if identity_scope:
            identity_parts.append(identity_scope)
        identity_id = "preparation:" + _hash(identity_parts)
        parent = parents.setdefault(
            identity_id,
            dict(
                identity_id=identity_id,
                identity_scope="source-entry-lemma-pos; not cross-source deduplication",
                language=language,
                source_entry_id=entry,
                resolved_identity_scope=identity_scope,
                lemma=lemma,
                pos=pos,
                review_unit_ids=set(),
                displays=set(),
                senses={},
                forms={},
                retained_forms=[],
                final_frequency_rank=None,
                frequency_status="pending_qualified_evidence",
                **FLAGS,
            ),
        )
        parent["review_unit_ids"].add(row["review_unit_id"])
        review = row.get("imported_review") or {}
        parent["displays"].add((resolution or {}).get("display") or review.get("display") or lemma)
        sense = dict(
            candidate_id=candidate_id,
            source_metadata=metadata,
            resolution=resolution,
            readings=sorted(
                [
                    r
                    for r in (row.get("source_group") or {}).get("readings", [])
                    if r.get("candidate_id") == candidate_id
                ],
                key=_canonical,
            ),
        )
        sense_key = (resolution or {}).get("resolved_sense_key") or candidate_id
        sense["resolved_sense_key"] = sense_key
        old = parent["senses"].get(sense_key)
        if old is not None and old != sense:
            raise ValueError("conflicting evidence for repeated candidate")
        parent["senses"][sense_key] = sense
        return parent

    for row in rows:
        resolution = row.get("resolved_content") or {}
        if resolution.get("schema_version") == FORM_SCHEMA:
            if (
                row["decision"] != "include"
                or resolution.get("resolved_candidates")
                or resolution.get("unresolved_questions")
            ):
                raise ValueError("form-only resolution cannot contain lexical decisions")
            validate_coverage(row, resolution.get("form_only_associations", []))
            form_rows.append(row)
            continue
        if row.get("resolved_content"):
            row = adapt_resolved(row)
        uid = row["review_unit_id"]
        if row["decision"] != "include":
            if row["decision"] in {"uncertain", "unreviewed", "quarantined"}:
                pending.append(uid)
            continue
        addition = row.get("supplemental_identity")
        if addition:
            if addition.get("decision") != "accepted_in_preparation_version" or not (
                addition.get("source_evidence")
                or addition.get("evidence")
                or (addition.get("source_lexical_identifiers") and addition.get("evidence_ids"))
            ):
                raise ValueError("supplement requires explicit source evidence")
            parent = add(
                row,
                addition.get("addition_id", uid),
                addition["lemma"],
                addition["pos"],
                addition.get("addition_id", uid),
                addition,
            )
            parent["retained_forms"].extend(
                dict(
                    source_form=form,
                    parent_identity_id=parent["identity_id"],
                    selected_for_card=False,
                    **FLAGS,
                )
                for form in addition.get("forms", [])
                if form.get("disposition") == "retained"
            )
            continue
        group = row["source_group"]
        review = row.get("imported_review") or {}
        available = {c["candidate_id"]: c for c in group["sense_candidates"]}
        if len(available) != len(group["sense_candidates"]):
            raise ValueError("duplicate candidate within review unit")
        resolved = row.get("resolved_content")
        selected = review.get("selected_candidate_ids", [])
        candidates = []
        if resolved:
            for candidate in resolved["resolved_candidates"]:
                cid = candidate["source_candidate_id"]
                if cid not in available:
                    raise ValueError("resolved candidate outside source group")
                if candidate["disposition"] == "retained":
                    if not candidate.get("evidence"):
                        raise ValueError("resolved candidate requires evidence")
                    candidates.append((cid, candidate["lemma"], candidate["pos"], candidate))
            if resolved.get("unresolved_questions") or any(
                c.get("unresolved_questions")
                or c["disposition"] not in {"retained", "omitted", "excluded"}
                for c in resolved["resolved_candidates"]
            ):
                partial.append(uid)
                findings.append(
                    dict(
                        review_unit_id=uid,
                        unresolved_questions=resolved.get("unresolved_questions", []),
                        candidate_questions=[
                            dict(
                                source_candidate_id=c["source_candidate_id"],
                                resolved_sense_key=c.get("resolved_sense_key"),
                                disposition=c["disposition"],
                                unresolved_questions=c.get("unresolved_questions", []),
                            )
                            for c in resolved["resolved_candidates"]
                            if c.get("unresolved_questions")
                            or c["disposition"] not in {"retained", "omitted", "excluded"}
                        ],
                        unbound_forms=resolved.get("preparation_unbound_forms", []),
                        **FLAGS,
                    )
                )
        else:
            if (
                not selected
                or len(set(selected)) != len(selected)
                or not set(selected) <= available.keys()
            ):
                raise ValueError("include requires exact selected source candidates")
            candidates = [
                (
                    cid,
                    review.get("lemma") or group["lemma"],
                    review.get("pos") or group["pos"],
                    None,
                )
                for cid in selected
            ]
        if not candidates:
            if uid in partial:
                continue
            raise ValueError("include without retained candidates")
        by_candidate, by_resolution = {}, {}
        for cid, lemma, pos, resolution in candidates:
            parent = add(row, group["entry_id"], lemma, pos, cid, available[cid], resolution)
            by_candidate.setdefault(cid, []).append(parent)
            by_resolution[(resolution or {}).get("resolved_sense_key") or cid] = parent
        forms = (resolved or {}).get("resolved_forms", {})
        selected_forms = forms.get("selected_forms", review.get("selected_forms", []))
        source_forms = {
            f["form_id"]: f for f in forms.get("source_forms", group.get("forms_for_review", []))
        }
        for form in selected_forms:
            fid, cid = form["form_id"], form["parent_candidate_id"]
            if fid not in source_forms or cid not in by_candidate:
                raise ValueError("selected form lacks exact retained candidate parent")
            source_form = source_forms[fid]
            entry_ids = source_form.get("parent_entry_ids", [])
            if (entry_ids and group["entry_id"] not in entry_ids) or (
                not entry_ids and cid not in source_form.get("evidence_candidate_ids", [])
            ):
                raise ValueError("selected form source entry binding differs")
            if form.get("form") is not None and _text(form["form"]) != _text(source_form["form"]):
                raise ValueError("selected form text differs from source")
            value = dict(selection=form, source=source_forms[fid])
            rid = form.get("parent_resolution_id")
            if rid:
                parent = by_resolution.get(rid)
                if parent is None or not any(parent is p for p in by_candidate[cid]):
                    raise ValueError("form resolution parent differs")
            else:
                if len(by_candidate[cid]) != 1:
                    raise ValueError("form parent is ambiguous between resolved senses")
                parent = by_candidate[cid][0]
            key = _hash([fid, cid, rid])
            if key in parent["forms"] and parent["forms"][key] != value:
                raise ValueError("conflicting form binding")
            parent["forms"][key] = value
        for derived in (resolved or {}).get("derived_identities", []):
            ids = derived.get("source_candidate_ids", [])
            if not ids or not set(ids) <= available.keys() or not derived.get("evidence"):
                raise ValueError("derived identity lacks exact source evidence")
            did = derived.get("identity_id") or derived.get("derived_identity_id") or _hash(derived)
            add(row, "derived:" + did, derived["lemma"], derived["pos"], did, derived, derived)

    for row in form_rows:
        for link in row["resolved_content"]["form_only_associations"]:
            parent = parents.get(link.get("parent_identity_id"))
            form = validate_form_link(row, link, parent)
            parent["retained_forms"].append(form)
            parent["review_unit_ids"].add(row["review_unit_id"])

    identities = []
    for key in sorted(parents):
        parent = parents[key]
        for field in ("review_unit_ids", "displays"):
            parent[field] = sorted(parent[field])
        for field in ("senses", "forms"):
            parent[field] = [parent[field][k] for k in sorted(parent[field])]
        parent["retained_forms"].sort(key=_canonical)
        identities.append(parent)
    return dict(
        language=language,
        snapshot_rows=rows,
        identities=identities,
        pending_review_units=pending,
        partially_unresolved_units=partial,
        form_only_units=[r["review_unit_id"] for r in form_rows],
        preparation_findings=findings,
        counts=dict(Counter(r["decision"] for r in rows)),
        **FLAGS,
    )


def source_order_preview(identities, evidence, *, source):
    """Order explicit source-bound parents only; never upgrade to final ranking.

    The caller must audit the exact source rows and parent mapping. A preview is
    intentionally distinct from the qualified generation contract.
    """
    if source.get("rank_meaning") != "published_frequency" or source.get("counting_unit") not in {
        "lemma-pos",
        "lexical-identity",
    }:
        raise ValueError("source rows or surface priorities are not lexical frequency")
    if not all(source.get(k) for k in ("source_id", "version", "sha256", "license")):
        raise ValueError("frequency source metadata incomplete")
    if not re.fullmatch("[0-9a-f]{64}", source["sha256"]):
        raise ValueError("frequency source hash invalid")
    by_id = {r["identity_id"]: r for r in identities}
    if len(by_id) != len(identities):
        raise ValueError("duplicate identity")
    rows, seen = [], set()
    for row in evidence:
        iid = row["identity_id"]
        if (
            iid not in by_id
            or iid in seen
            or type(row.get("source_rank")) is not int
            or row["source_rank"] < 1
        ):
            raise ValueError("invalid source rank or parent mapping")
        if not re.fullmatch("[0-9a-f]{64}", row.get("source_record_sha256", "")) or not row.get(
            "source_locator"
        ):
            raise ValueError("rank requires bound source record")
        seen.add(iid)
        rows.append(copy.deepcopy(row))
    rows.sort(key=lambda r: (r["source_rank"], r["identity_id"]))
    for position, row in enumerate(rows, 1):
        row.update(
            position=position,
            band=f"core-{(position - 1) // 1000 + 1}" if position <= 3000 else "expansion",
            final_frequency_approved=False,
            **FLAGS,
        )
    return dict(
        source=source,
        ordered=rows,
        unranked_identity_count=len(by_id) - len(seen),
        unranked_identity_ids=sorted(by_id.keys() - seen),
        ordering_status="source_bound_preview",
        final_frequency_approved=False,
        **FLAGS,
    )


def _plain(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("paths cannot traverse symlinks")
    return path


def _read(path, expected):
    path = _plain(path)
    if not path.is_file() or path.stat().st_size > 256 * 1024**2:
        raise ValueError("input must be a bounded regular file")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("input hash mismatch")
    return raw


def publish_inventory(*, inputs, output):
    """Validate immutable snapshots, consolidate, and publish a new version.

    No reads of .env, database access, provider calls, or native review imports.
    The completion manifest is written last; a failed publication is not ready.
    """
    output = _plain(output)
    if output.exists():
        raise ValueError("output exists; choose a new version")
    languages = [r["language"] for r in inputs]
    if not inputs or len(set(languages)) != len(languages):
        raise ValueError("one explicit input per language required")
    inputs = sorted(inputs, key=lambda r: r["language"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".finalization-", dir=output.parent) as temporary:
        stage = Path(temporary)
        files, snapshot_files, counts, reports = {}, {}, {}, {}
        language_metadata, attachments, extra_pins = {}, {}, {}

        def write_raw(name, raw):
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            files[name] = hashlib.sha256(raw).hexdigest()
            if name.startswith("snapshot/"):
                snapshot_files[name.removeprefix("snapshot/")] = files[name]

        def write(name, value, jsonl=False):
            raw = (
                ("\n".join(_canonical(r) for r in value) + ("\n" if value else ""))
                if jsonl
                else _canonical(value) + "\n"
            ).encode()
            write_raw(name, raw)

        for reference in inputs:
            raw = _read(reference["path"], reference["sha256"])
            result = consolidate(
                (json.loads(s) for s in raw.splitlines() if s.strip()),
                language=reference["language"],
            )
            del raw
            lang = result["language"]
            origin = reference.get("source_manifest")
            if origin:
                origin_path = _plain(origin["path"])
                origin_raw = _read(origin_path, origin["sha256"])
                extra_pins[str(origin_path)] = origin["sha256"]
                original = json.loads(origin_raw)
                if lang in original.get("language_metadata", {}):
                    language_metadata[lang] = original["language_metadata"][lang]
                for name in original.get("attachments", {}):
                    relative = Path(name)
                    if relative.is_absolute() or ".." in relative.parts:
                        raise ValueError("invalid attachment path")
                    source_name = name if name in original["files"] else "attachments/" + name
                    attachment_path = origin_path.parent / source_name
                    sha = original["files"][source_name]
                    raw = _read(attachment_path, sha)
                    extra_pins[str(attachment_path)] = sha
                    payload = json.loads(raw)
                    if (
                        isinstance(original["attachments"], dict)
                        and payload != original["attachments"][name]
                    ):
                        raise ValueError("attachment content differs from source manifest")
                    destination = f"attachments/{origin['sha256']}/{relative.as_posix()}"
                    attachments[destination] = payload
                    write_raw("snapshot/" + destination, raw)
            counts[lang] = {d: result["counts"].get(d, 0) for d in sorted(DECISIONS)}
            write(f"snapshot/inventory/{lang}.jsonl", result["snapshot_rows"], True)
            write(f"languages/{lang}/identities.jsonl", result["identities"], True)
            write(
                f"languages/{lang}/preparation-findings.jsonl", result["preparation_findings"], True
            )
            pending_ids = set(result["pending_review_units"] + result["partially_unresolved_units"])
            write(
                f"languages/{lang}/pending-review.jsonl",
                [r for r in result["snapshot_rows"] if r["review_unit_id"] in pending_ids],
                True,
            )
            write(
                f"languages/{lang}/pending-frequency.json",
                [r["identity_id"] for r in result["identities"]],
            )
            reports[lang] = dict(
                review_units=len(result["snapshot_rows"]),
                decisions=counts[lang],
                included_identities=len(result["identities"]),
                selected_sense_associations=sum(len(r["senses"]) for r in result["identities"]),
                selected_form_associations=sum(len(r["forms"]) for r in result["identities"]),
                retained_form_associations=sum(
                    len(r["retained_forms"]) for r in result["identities"]
                ),
                form_only_units=len(result["form_only_units"]),
                partially_unresolved_units=len(result["partially_unresolved_units"]),
                final_frequency_ranked_identities=0,
                **FLAGS,
            )
            del result
        manifest = dict(
            schema_version="vocabulary-selection-snapshot-1",
            files=dict(snapshot_files),
            total_records=sum(sum(c.values()) for c in counts.values()),
            languages=counts,
            language_metadata=language_metadata,
            attachments=attachments,
            source_inputs=inputs,
            temporal_scope="explicit_versioned_export_composition",
            **FLAGS,
        )
        manifest["snapshot_id"] = _hash(manifest)
        write("snapshot/manifest.json", manifest)
        summary = dict(
            schema_version="vocabulary-finalization-1",
            languages=reports,
            source_inputs=inputs,
            final_frequency_approved=False,
            coverage_90_percent_verified=False,
            identity_policy="exact-source-entry-lemma-pos; candidate IDs and own readings preserved",
            counting_note="Preparation identities and sense associations are not final card counts.",
            **FLAGS,
        )
        write("summary.json", summary)
        write("inputs.json", inputs)
        for reference in inputs:
            _read(reference["path"], reference["sha256"])
        for name, sha in extra_pins.items():
            _read(name, sha)
        # Exclusive mkdir prevents concurrent publications from replacing an empty destination.
        output.mkdir()
        for child in stage.iterdir():
            child.rename(output / child.name)
        with (output / "manifest.json").open("x", encoding="utf-8") as stream:
            stream.write(_canonical(dict(files=files, **FLAGS)) + "\n")
    return summary
