"""Publish a source-bound continuation of a frozen vocabulary inventory.

The JSON config lists a pinned baseline publication and pinned review rounds.
Every input and the destination must remain under the project's output/reports/.
This offline command never generates cards, audio or decks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from multilang.services.vocabulary_adjudication import _hash
from multilang.services.vocabulary_continuation_composition import apply_proposal
from multilang.services.vocabulary_finalization import publish_inventory

ROOT = Path(__file__).resolve().parents[1]
REPORTS = (ROOT / "output" / "reports").resolve()
LANGUAGES = set("cs da de el en es fi fr hr hu it ja ko la nb nl pl pt ro ru sv tr zh".split())


def safe_path(name: str) -> Path:
    if not isinstance(name, str) or not name:
        raise ValueError("report path is missing")
    path = (ROOT / name).resolve()
    if not path.is_relative_to(REPORTS):
        raise ValueError("path escapes output/reports")
    return path


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pinned(reference: dict) -> Path:
    path = safe_path(reference["path"])
    if sha(path) != reference["sha256"]:
        raise ValueError(f"pinned file differs: {path}")
    return path


def lines(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def manifest_file(manifest_path: Path, manifest: dict, name: str) -> Path:
    files = manifest.get("files")
    if isinstance(files, dict):
        expected = files.get(name)
        if isinstance(expected, dict):
            expected = expected.get("sha256")
    elif isinstance(files, list):
        found = [item["sha256"] for item in files if item.get("path") == name]
        expected = found[0] if len(found) == 1 else None
    else:
        expected = None
    if not isinstance(expected, str):
        raise ValueError(f"file missing from sealed manifest: {name}")
    path = (manifest_path.parent / name).resolve()
    if not path.is_relative_to(REPORTS) or sha(path) != expected:
        raise ValueError(f"sealed artifact differs: {name}")
    return path


def _binding_map(rows: list[dict]) -> dict[tuple[str, str], dict]:
    result = {}
    for row in rows:
        key = row.get("language", "zh"), row["review_unit_id"]
        if key in result:
            raise ValueError("duplicate proposal binding")
        result[key] = row
    return result


def _round_rows(round_spec: dict) -> tuple[list[tuple[dict, str, str]], dict]:
    path = pinned(round_spec["manifest"])
    manifest = json.loads(path.read_text(encoding="utf-8"))
    proposals_path = manifest_file(path, manifest, round_spec["proposals"])
    proposals = lines(proposals_path)
    mode = round_spec.get("mode", "rows")
    if mode == "envelopes":
        result = []
        for envelope in proposals:
            digest = envelope.get("proposal_sha256")
            if _hash({k: v for k, v in envelope.items() if k != "proposal_sha256"}) != digest:
                raise ValueError("proposal envelope differs")
            row = envelope["replacement"]
            if _hash(row) != envelope.get("replacement_sha256"):
                raise ValueError("proposal replacement differs")
            if (row["language"], row["review_unit_id"]) != (
                envelope["language"], envelope["review_unit_id"]
            ):
                raise ValueError("envelope review unit differs")
            result.append((row, envelope["baseline_row_sha256"], envelope["replacement_sha256"]))
    elif mode == "rows":
        bindings_path = manifest_file(path, manifest, round_spec["bindings"])
        bindings = _binding_map(json.loads(bindings_path.read_text(encoding="utf-8")))
        result = []
        for row in proposals:
            key = row["language"], row["review_unit_id"]
            binding = bindings.pop(key, None)
            if binding is None:
                raise ValueError("proposal has no sealed binding")
            result.append((row, binding["baseline_row_sha256"], binding.get("proposal_row_sha256") or binding.get("replacement_row_sha256")))
        if bindings:
            raise ValueError("sealed binding has no proposal")
    else:
        raise ValueError("unsupported proposal mode")
    return result, dict(manifest_path=str(path), manifest_sha256=sha(path), proposals_path=str(proposals_path), proposals_sha256=sha(proposals_path), count=len(result))


def compose(config_path: Path) -> dict:
    config_path = safe_path(str(config_path))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    baseline_path = pinned(config["baseline_manifest"])
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    output = safe_path(config["output"])
    if output.exists():
        raise ValueError("continuation output already exists")
    inventory = {}
    baseline_counts = {}
    for language in sorted(LANGUAGES):
        path = manifest_file(baseline_path, baseline, f"snapshot/inventory/{language}.jsonl")
        original = lines(path)
        by_unit = {row["review_unit_id"]: row for row in original}
        if len(by_unit) != len(original):
            raise ValueError("duplicate baseline review unit")
        inventory[language] = by_unit
        baseline_counts[language] = len(original)
    rounds = []
    changed = {language: set() for language in LANGUAGES}
    for spec in config["rounds"]:
        proposals, evidence = _round_rows(spec)
        for row, prior_sha, proposal_sha in proposals:
            language, uid = row["language"], row["review_unit_id"]
            if language not in LANGUAGES or uid not in inventory[language]:
                raise ValueError("proposal is outside frozen inventory")
            inventory[language][uid] = apply_proposal(
                inventory[language][uid], row, prior_sha, proposal_sha
            )
            changed[language].add(uid)
        rounds.append(evidence)
    output.mkdir(parents=True, exist_ok=False)
    composition = output / "composition"
    composition.mkdir()
    inputs = []
    for language in sorted(LANGUAGES):
        path = composition / f"{language}.jsonl"
        with path.open("x", encoding="utf-8") as stream:
            for uid in sorted(inventory[language]):
                stream.write(json.dumps(inventory[language][uid], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        inputs.append(dict(language=language, format="selection-snapshot", path=str(path), sha256=sha(path), source_manifest=dict(path=str(baseline_path), sha256=sha(baseline_path))))
    with (output / "publication-inputs.json").open("x", encoding="utf-8") as stream:
        json.dump(inputs, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    published = publish_inventory(inputs=inputs, output=output / "published")
    report = dict(
        schema_version="vocabulary-continuation-composition-1",
        baseline_manifest=dict(path=str(baseline_path), sha256=sha(baseline_path)),
        config=dict(path=str(config_path), sha256=sha(config_path)),
        rounds=rounds,
        changed_review_units={language: sorted(changed[language]) for language in sorted(LANGUAGES)},
        baseline_units=baseline_counts,
        output_units={language: len(inventory[language]) for language in sorted(LANGUAGES)},
        publication_manifest_sha256=sha(output / "published" / "manifest.json"),
        generation_status="deferred_by_user",
        production_eligible=False,
        publication_summary=published,
    )
    with (output / "composition-report.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    report = compose(args.config)
    print(json.dumps(dict(output=report["publication_summary"].get("output"), publication_manifest_sha256=report["publication_manifest_sha256"], changed_units=sum(len(v) for v in report["changed_review_units"].values())), ensure_ascii=False))


if __name__ == "__main__":
    main()
