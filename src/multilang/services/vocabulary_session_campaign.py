"""Resume file-based assistant reviews without providers, credentials or generation."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine_runner import read_json, verify_artifact
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_session_review import export_session_request, load_session_review


def _catalog(packets: Path, manifest_sha256: str):
    packets = _plain_path(packets)
    manifest = read_json(packets / "manifest.json", manifest_sha256)
    summary = read_json(packets / "summary.json", manifest["files"]["summary.json"])
    if summary.get("generation_status") != "deferred_by_user":
        raise ValueError("generation must remain deferred")
    languages, refs = {}, {}
    for row in summary["languages"]:
        language = SupportedLanguage(row["language"]).value
        if language in languages:
            raise ValueError("duplicate catalog language")
        languages[language] = row
        for item in row["packets"]:
            relative = item["path"]
            if not re.fullmatch(rf"{language}/[0-9]{{5}}\.json", relative):
                raise ValueError("invalid source packet path")
            if manifest["files"].get(relative) != item["sha256"] or item["sha256"] in refs:
                raise ValueError("source packet manifest mismatch or duplicate")
            if type(item["entries"]) is not int or not 1 <= item["entries"] <= 64:
                raise ValueError("invalid packet unit count")
            refs[item["sha256"]] = {**item, "language": language}
        if row["packet_count"] != len(row["packets"]) or row["review_unit_count"] != sum(
            item["entries"] for item in row["packets"]
        ):
            raise ValueError("catalog language totals mismatch")
    if not languages or any(summary[field] != sum(row[field] for row in languages.values())
                            for field in ("entry_count", "review_unit_count", "packet_count")):
        raise ValueError("catalog totals mismatch")

    @lru_cache(maxsize=8)
    def packet(digest):
        if digest not in refs:
            raise ValueError("request is not in the source packet inventory")
        reference = refs[digest]
        data = json.loads(_read_bytes(packets / reference["path"], digest, limit=16 * 1024**2))
        expected = canonical_sha256({k: v for k, v in data.items() if k != "packet_sha256"})
        if (data.get("packet_sha256") != expected or data.get("language") != reference["language"]
                or data.get("generation_status") != "deferred_by_user"
                or len(data["groups"]) != reference["entries"]):
            raise ValueError("source packet binding or metadata mismatch")
        return data

    return summary, refs, packet


def _artifacts(root: Path):
    root = _plain_path(root)
    if not root.exists():
        return []
    paths = []
    for path in sorted(root.iterdir()):
        if path.name.startswith("."):
            continue
        path = _plain_path(path)
        if path.is_dir():
            paths.append(path)
        if len(paths) > 200_000:
            raise ValueError("session artifact inventory exceeds limit")
    return paths


def _state(*, packets: Path, manifest_sha256: str, requests: Path, reviews: Path):
    summary, refs, packet = _catalog(packets, manifest_sha256)
    request_map, reviewed, saved_reviews = {}, {}, {}
    for path in _artifacts(requests):
        manifest = verify_artifact(path, kind="vocabulary-session-request")
        request = read_json(path / "request.json")
        digest = canonical_sha256(request)
        if digest != manifest["binding_sha256"]:
            raise ValueError("session request binding changed")
        source = packet(request["packet_sha256"])
        indices = request["source_indices"]
        if (request.get("language") != source["language"]
                or request.get("generation_status") != "deferred_by_user"
                or not isinstance(indices, list) or not indices
                or any(type(i) is not int or i < 0 or i >= len(source["groups"]) for i in indices)
                or len(set(indices)) != len(indices)
                or request["groups"] != [source["groups"][i] for i in indices]):
            raise ValueError("session request differs from its source packet")
        # Keep only routing metadata. Holding every copied dictionary payload
        # would scale memory with the entire multi-language source corpus.
        request_map[digest] = {"path": path, "data": {
            "language": request["language"], "source_indices": indices,
        }, "reviewed": False}
    for path in _artifacts(reviews):
        manifest = verify_artifact(path, kind="vocabulary-session-review")
        if manifest["binding_sha256"] in saved_reviews:
            continue  # An exact copy does not count as another review.
        saved = read_json(path / "result.json")
        if saved.get("request_sha256") not in request_map:
            raise ValueError("session review has no bound request")
        request = request_map[saved["request_sha256"]]
        result = load_session_review(request=request["path"], output=path)
        saved_reviews[manifest["binding_sha256"]] = result
    superseded = set()
    for result in saved_reviews.values():
        previous = result.get("supersedes_review_sha256")
        if previous is not None:
            if previous not in saved_reviews or saved_reviews[previous]["request_sha256"] != result["request_sha256"]:
                raise ValueError("correction lacks the exact superseded request and review")
            if previous in superseded:
                raise ValueError("competing session corrections need explicit reconciliation")
            superseded.add(previous)
    for digest, result in saved_reviews.items():
        seen, previous = {digest}, result.get("supersedes_review_sha256")
        while previous is not None:
            if previous in seen:
                raise ValueError("cyclic session corrections need explicit reconciliation")
            seen.add(previous)
            previous = saved_reviews[previous].get("supersedes_review_sha256")
        if digest in superseded:
            continue
        request_map[result["request_sha256"]]["reviewed"] = True
        for row in result["decisions"]:
            key = (result["language"], row["review_unit_id"])
            if key in reviewed:
                raise ValueError("overlapping session decisions need explicit reconciliation")
            reviewed[key] = {**row, "request_sha256": result["request_sha256"],
                             "review_sha256": digest,
                             "packet_sha256": result["packet_sha256"]}
    return summary, refs, packet, request_map, reviewed


def prepare_next_session_review(
    *, packets: Path, manifest_sha256: str, requests: Path, reviews: Path,
    language: str, batch_size: int = 8,
) -> dict:
    language = SupportedLanguage(language).value
    if type(batch_size) is not int or not 1 <= batch_size <= 64:
        raise ValueError("session batch size must be between 1 and 64")
    summary, refs, packet, request_map, reviewed = _state(
        packets=packets, manifest_sha256=manifest_sha256, requests=requests, reviews=reviews,
    )
    if language not in {row["language"] for row in summary["languages"]}:
        raise ValueError("language absent from source inventory")
    for digest, item in request_map.items():
        if item["data"]["language"] == language and not item["reviewed"]:
            return {"status": "awaiting_session_review", "request": str(item["path"]),
                    "request_sha256": digest, "source_indices": item["data"]["source_indices"],
                    "provider_calls_executed": 0, "generation_status": "deferred_by_user"}
    for digest, reference in refs.items():
        if reference["language"] != language:
            continue
        data = packet(digest)
        indices = [i for i, group in enumerate(data["groups"])
                   if (language, group["review_unit_id"]) not in reviewed][:batch_size]
        if not indices:
            continue
        name = f"{language}-{Path(reference['path']).stem}-{indices[0]:03d}-{len(indices):03d}"
        destination = _plain_path(requests) / name
        exported = export_session_request(packets / reference["path"], digest,
                                          indices=indices, output=destination)
        return {"status": "awaiting_session_review", "request": str(destination),
                "request_sha256": exported["request_sha256"], "source_indices": indices,
                "provider_calls_executed": 0, "generation_status": "deferred_by_user"}
    return {"status": "first_pass_complete", "language": language,
            "production_eligible": False, "provider_calls_executed": 0,
            "generation_status": "deferred_by_user"}


def session_progress(*, packets: Path, manifest_sha256: str, requests: Path, reviews: Path):
    summary, _, _, request_map, reviewed = _state(
        packets=packets, manifest_sha256=manifest_sha256, requests=requests, reviews=reviews,
    )
    languages, proposals = [], {}
    fields = ("reviewed_units", "unreviewed_units", "proposal_include_units", "proposal_exclude_units",
              "proposal_uncertain_units", "proposed_source_senses", "proposed_form_sense_pairs",
              "touched_source_groups", "completed_source_groups", "fragment_identity_conflicts")
    for source in summary["languages"]:
        language = source["language"]
        rows = [row for (lang, _), row in reviewed.items() if lang == language]
        rows.sort(key=lambda row: (row.get("source_priority") or 10**12, row["entry_id"],
                                   row["source_group_fragment_index"]))
        counts = Counter(row["decision"] for row in rows)
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["entry_id"]].append(row)
        completed = conflicts = 0
        for fragments in grouped.values():
            expected = {row["source_group_fragment_count"] for row in fragments}
            if len(expected) != 1 or next(iter(expected)) < 1:
                raise ValueError("fragment count drift")
            count = next(iter(expected))
            indices = [row["source_group_fragment_index"] for row in fragments]
            if len(set(indices)) != len(indices) or any(i < 0 or i >= count for i in indices):
                raise ValueError("fragment index drift")
            completed += set(indices) == set(range(count))
            identities = {(row["display"], row["pos"]) for row in fragments if row["decision"] == "include"}
            conflicts += len(identities) > 1
        record = {
            "language": language, "source_groups": source["entry_count"],
            "total_review_units": source["review_unit_count"],
            "reviewed_units": len(rows), "unreviewed_units": source["review_unit_count"] - len(rows),
            "proposal_include_units": counts["include"], "proposal_exclude_units": counts["exclude"],
            "proposal_uncertain_units": counts["uncertain"],
            "proposed_source_senses": sum(len(row["selected_candidate_ids"]) for row in rows),
            "proposed_form_sense_pairs": sum(len(row["selected_forms"]) for row in rows),
            "touched_source_groups": len(grouped), "completed_source_groups": completed,
            "fragment_identity_conflicts": conflicts, "production_eligible": False,
            "spoken_general_coverage": None, "written_general_coverage": None,
            "coverage_status": "not_measured_on_finalized_inventory",
        }
        if record["unreviewed_units"] < 0 or len(grouped) > source["entry_count"]:
            raise ValueError("review counts exceed source inventory")
        languages.append(record)
        proposals[language] = rows
    report = {
        "schema_version": "vocabulary-session-progress-1", "packets_manifest_sha256": manifest_sha256,
        "prepared_manifest_sha256": summary["source_manifest_sha256"],
        "total_source_groups": summary["entry_count"], "total_review_units": summary["review_unit_count"],
        **{field: sum(row[field] for row in languages) for field in fields}, "languages": languages,
        "pending_requests": sum(not item["reviewed"] for item in request_map.values()),
        "review_status": "single_session_proposals_require_validation", "independent_passes": 0,
        "order_status": "provisional_source_priority_requires_disambiguation",
        "coverage_90_percent_verified": False, "production_eligible": False, "human_approved": False,
        "generation_status": "deferred_by_user", "provider_calls_executed": 0,
        "new_card_texts": 0, "new_translations": 0, "new_audio": 0, "new_decks": 0,
    }
    return report, proposals


def write_session_progress(*, output: Path, **kwargs) -> dict:
    report, proposals = session_progress(**kwargs)
    output = _plain_path(output)
    if output.exists():
        raise ValueError("session report requires a new destination")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".session-progress-", dir=output.parent) as temporary:
        stage = Path(temporary) / "report"
        stage.mkdir()
        hashes, total = {}, 0
        for name, data in [("summary.json", report), *[(f"{language}.json", {
            "language": language, "review_status": report["review_status"],
            "production_eligible": False, "generation_status": "deferred_by_user", "decisions": rows,
        }) for language, rows in proposals.items()]]:
            content = (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
            total += len(content)
            if len(content) > 128 * 1024**2 or total > 2 * 1024**3:
                raise ValueError("session report size limit exceeded")
            (stage / name).write_bytes(content)
            hashes[name] = hashlib.sha256(content).hexdigest()
        (stage / "manifest.json").write_text(json.dumps({"files": hashes}, sort_keys=True) + "\n")
        if output.exists():
            raise ValueError("session report requires a new destination")
        os.rename(stage, output)
    return report
