"""Export a provisional source-priority order from a frozen publication.

This preserves every included identity; it does not certify frequency or create cards.
"""

from __future__ import annotations

import argparse
import json

from compose_vocabulary_continuation import LANGUAGES, lines, manifest_file, pinned, safe_path, sha

from multilang.services.vocabulary_preparation_order import order_identities


def export(publication_reference: dict, destination: str) -> dict:
    manifest_path = pinned(publication_reference)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary_path = manifest_file(manifest_path, manifest, "summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if set(summary["languages"]) != LANGUAGES:
        raise ValueError("source publication lacks an expected language")
    output = safe_path(destination)
    output.mkdir(parents=True, exist_ok=False)
    reports = {}
    for language in sorted(LANGUAGES):
        names = [
            f"snapshot/inventory/{language}.jsonl",
            f"languages/{language}/identities.jsonl",
            f"languages/{language}/pending-review.jsonl",
        ]
        paths = {name: manifest_file(manifest_path, manifest, name) for name in names}
        source = {row["review_unit_id"]: row for row in lines(paths[names[0]])}
        identities = lines(paths[names[1]])
        pending = {row["review_unit_id"] for row in lines(paths[names[2]])}
        ordered = order_identities(identities, source, pending)
        stats = summary["languages"][language]
        if (
            len(ordered) != stats["included_identities"]
            or len({row["identity_id"] for row in ordered}) != len(ordered)
            or sum(len(row["senses"]) for row in ordered) != stats["selected_sense_associations"]
        ):
            raise ValueError("ordered identity or sense inventory differs")
        path = output / f"{language}.jsonl"
        with path.open("x", encoding="utf-8") as stream:
            for row in ordered:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        reports[language] = dict(
            path=str(path), sha256=sha(path), identities=len(ordered),
            has_source_priority=sum(bool(row["source_priority_values"]) for row in ordered),
            without_source_priority=sum(not row["source_priority_values"] for row in ordered),
            input_pins={name: sha(paths[name]) for name in names},
        )
    result = dict(
        schema_version="source-priority-preparation-order-2",
        status="complete_provisional_order_not_final_frequency",
        inputs=dict(publication_manifest_sha256=sha(manifest_path)),
        languages=reports,
        counts_are_not_cards=True,
        no_3000_cap=True,
        policy="Preserve every identity and own source priority; linked forms do not set parent order. Different source scales are not a certified general frequency.",
        coverage_90_percent_verified=False,
        final_frequency_approved=False,
        generation_status="deferred_by_user",
        production_eligible=False,
    )
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("publication_manifest")
    parser.add_argument("output")
    args = parser.parse_args()
    reference = dict(path=args.publication_manifest, sha256=sha(safe_path(args.publication_manifest)))
    report = export(reference, args.output)
    print(json.dumps(dict(output=args.output, languages=len(report["languages"])), ensure_ascii=False))


if __name__ == "__main__":
    main()
