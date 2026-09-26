"""Build a provisional, source-bound study order before card generation."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_review import _plain_path, _read_bytes


def build_curriculum_sequences(
    prepared: Path, manifest_sha256: str, *, output: Path, prerequisite_window: int = 256,
) -> dict:
    """Freeze order and expansion bands while keeping semantic approval pending.

    The source preparation's provisional order is reused only as an ordering
    hint. Rows retain source candidate IDs and never masquerade as approved
    lexical identities. Sentence curricula are attached after sense review and
    contextual analysis, so this step cannot generate card content.
    """
    if type(prerequisite_window) is not int or not 1 <= prerequisite_window <= 256:
        raise ValueError("prerequisite window must be between 1 and 256")
    prepared, output = _plain_path(prepared), _plain_path(output)
    if output.exists():
        raise ValueError("curriculum output requires a new directory")
    manifest = json.loads(_read_bytes(prepared / "manifest.json", manifest_sha256))
    request = json.loads(_read_bytes(prepared / "request.json", manifest["files"]["request.json"]))
    codes = [SupportedLanguage(row["language"]).value for row in request["languages"]]
    if not codes or len(codes) != len(set(codes)):
        raise ValueError("invalid curriculum language inventory")
    output.parent.mkdir(parents=True, exist_ok=True)
    checksums: dict[str, str] = {}
    reports = []
    total_bytes = 0
    with TemporaryDirectory(prefix=".curriculum-sequence-", dir=output.parent) as temporary:
        stage = Path(temporary) / "delivery"
        stage.mkdir()

        def write(relative: str, value: object) -> None:
            nonlocal total_bytes
            content = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":")) + "\n").encode("utf-8")
            total_bytes += len(content)
            if total_bytes > 2 * 1024**3 or len(content) > 128 * 1024**2:
                raise ValueError("curriculum sequence output byte limit exceeded")
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            checksums[relative] = hashlib.sha256(content).hexdigest()

        for language in codes:
            vocabulary = json.loads(_read_bytes(
                prepared / language / "vocabulary.json",
                manifest["files"][f"{language}/vocabulary.json"], limit=128 * 1024**2,
            ))
            entries = vocabulary["entries"]
            if any(type(row.get("provisional_order")) is not int for row in entries):
                raise ValueError("curriculum source order is incomplete")
            ordered = sorted(entries, key=lambda row: (row["provisional_order"], row["entry_id"]))
            if [row["provisional_order"] for row in ordered] != list(range(1, len(ordered) + 1)):
                raise ValueError("curriculum source order is not contiguous")
            rows = []
            band_counts = Counter()
            for position, entry in enumerate(ordered, start=1):
                previous = ordered[max(0, position - 1 - prerequisite_window):position - 1]
                prior_refs = [row["entry_id"] for row in previous]
                row = {
                    "sequence": position,
                    "entry_id": entry["entry_id"],
                    "lemma": entry["lemma"],
                    "pos": entry["pos"],
                    "source_priority": entry.get("source_priority"),
                    "provisional_order": entry["provisional_order"],
                    "proposed_band": entry.get("proposed_band"),
                    "source_candidate_ids": [sense["candidate_id"]
                                              for sense in entry.get("sense_candidates", [])],
                    "proposed_prerequisite_range": (
                        {"start": max(1, position - prerequisite_window), "end": position - 1}
                        if previous else None
                    ),
                    "proposed_prerequisite_count": len(prior_refs),
                    "proposed_prerequisite_sha256": canonical_sha256(prior_refs),
                    "allowed_morphology_features": [],
                    "curriculum_status": "pending_curation_and_contextual_analysis",
                    "production_eligible": False,
                }
                rows.append(row)
                band_counts[entry.get("proposed_band") or "unassigned"] += 1
            relative = f"{language}/sequence.json"
            write(relative, {"schema_version": "vocabulary-curriculum-sequence-2",
                             "language": language, "source_vocabulary_sha256": manifest["files"][f"{language}/vocabulary.json"],
                             "prerequisite_window": prerequisite_window,
                             "generation_status": "deferred_by_user", "rows": rows})
            report = {"language": language, "entry_count": len(rows),
                      "band_counts": dict(sorted(band_counts.items())),
                      "prerequisite_window": prerequisite_window,
                      "curriculum_status": "pending_curation_and_contextual_analysis",
                      "production_eligible": False}
            reports.append(report)
            write(f"{language}/index.json", report)
        summary = {
            "schema_version": "vocabulary-curriculum-sequences-2",
            "source_manifest_sha256": manifest_sha256, "languages": reports,
            "entry_count": sum(report["entry_count"] for report in reports),
            "generation_status": "deferred_by_user",
            "curriculum_status": "pending_curation_and_contextual_analysis",
            "production_eligible": False,
        }
        write("summary.json", summary)
        (stage / "manifest.json").write_text(json.dumps({"files": checksums}, sort_keys=True) + "\n")
        if output.exists():
            raise ValueError("curriculum output requires a new directory")
        os.rename(stage, output)
    return summary


__all__ = ["build_curriculum_sequences"]
