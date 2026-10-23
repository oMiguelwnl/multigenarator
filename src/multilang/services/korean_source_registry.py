"""Versioned offline registry of exact NIKL rows; no ranking or review approval."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.korean_grammar_course import parse_nikl_bootstrap_rows
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact, read_json
from multilang.services.qualification_review import _json
from multilang.services.vocabulary_review import _plain_path, _read_bytes


def _jsonl(rows):
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()
        for row in rows
    )


def build_korean_source_registry(
    *,
    bundle: Path,
    bundle_manifest_sha256: str,
    supplement: Path,
    supplement_manifest_sha256: str,
    output: Path,
) -> dict:
    """Preserve all source rows and exactly alias the previously linked candidates."""
    bundle, supplement, output = map(_plain_path, (bundle, supplement, output))
    if output.is_relative_to(bundle) or output.is_relative_to(supplement):
        raise ValueError("registry output must be separate from source artifacts")
    manifest = read_json(bundle / "manifest.json", bundle_manifest_sha256)
    supplemental = read_json(supplement / "manifest.json", supplement_manifest_sha256)
    if (
        manifest.get("source_id") != "nikl-korean-learners-vocabulary"
        or manifest.get("language") != "ko"
        or supplemental.get("source_encoding") != "cp949"
    ):
        raise ValueError("registry requires the documented NIKL Korean CP949 source")
    names = ["source-snapshot.txt", "curated-inventory.jsonl", "rejections.jsonl"]
    members = {}
    for name in names:
        matches = [row for row in manifest["members"] if row["relative_path"] == name]
        if len(matches) != 1:
            raise ValueError("source manifest member missing or duplicated")
        members[name] = matches[0]
    payloads = {
        name: _read_bytes(bundle / name, members[name]["sha256"], limit=32 * 1024**2)
        for name in names
    }
    if (
        supplemental["source_sha256"] != members["source-snapshot.txt"]["sha256"]
        or supplemental["inventory_sha256"] != members["curated-inventory.jsonl"]["sha256"]
    ):
        raise ValueError("supplement source/inventory binding drift")
    link_bytes = _read_bytes(
        supplement / "source-links.jsonl", supplemental["output_sha256"], limit=32 * 1024**2
    )
    parsed = parse_nikl_bootstrap_rows(payloads["source-snapshot.txt"].decode("cp949"))
    inventory = [
        _json(line) for line in payloads["curated-inventory.jsonl"].splitlines() if line.strip()
    ]
    rejections = [_json(line) for line in payloads["rejections.jsonl"].splitlines() if line.strip()]
    links = [_json(line) for line in link_bytes.splitlines() if line.strip()]
    for name, rows in zip(names, (parsed, inventory, rejections), strict=True):
        if len(rows) != members[name]["row_count"]:
            raise ValueError("source manifest row accounting mismatch")
    if (
        len(inventory) != manifest["entry_count"]
        or len(rejections) != manifest["rejection_count"]
        or len(links) != len(inventory)
        or len(links) != supplemental["linked_candidates"]
    ):
        raise ValueError("inventory/supplement row accounting mismatch")

    accepted, rejected, linked = {}, {}, {}
    for records, index, key in (
        (inventory, accepted, "source_rank"),
        (rejections, rejected, "source_rank"),
        (links, linked, "source_ordinal"),
    ):
        for row in records:
            ordinal = row[key]
            if type(ordinal) is not int or not 1 <= ordinal <= len(parsed) or ordinal in index:
                raise ValueError("invalid or duplicate source ordinal")
            index[ordinal] = row
    if (
        set(accepted) & set(rejected)
        or set(accepted) | set(rejected) != set(range(1, len(parsed) + 1))
        or set(linked) != set(accepted)
    ):
        raise ValueError("accepted/rejected/source alias partition mismatch")
    rows, aliases, pending = [], [], []
    for ordinal, item in enumerate(parsed, 1):
        marker = item["sense_marker"]
        meaning = (
            "proper_name_not_disambiguated"
            if item["source_pos"] == "고"
            else "not_in_standard_dictionary"
            if marker == "80"
            else "standard_dictionary_homograph"
            if marker is not None
            else "no_publisher_marker"
        )
        row = {
            "source_row_id": "nikl-source-row:"
            + canonical_sha256(
                {
                    "source_sha256": supplemental["source_sha256"],
                    "ordinal": ordinal,
                    "line_sha256": item["source_entry_sha256"],
                }
            ),
            "source_ordinal": ordinal,
            "source_physical_line": item["source_line_number"],
            "source_form": item["source_form"],
            "source_pos": item["source_pos"],
            "source_hint": item["source_gloss"],
            "source_grade": item["source_level"],
            "publisher_rank": item["source_frequency_rank"],
            "publisher_rank_basis": "NIKL_2002_usage_frequency_report",
            "source_line_utf8_sha256": item["source_entry_sha256"],
            "homograph": {
                "marker": marker,
                "source_base_form": item["lemma"],
                "meaning": meaning,
                "is_dictionary_sense_id": False,
                "alters_existing_lemma": False,
            },
            "selection_status": "not_selected_by_registry",
            "production_eligible": False,
        }
        if ordinal in accepted:
            old, link = accepted[ordinal], linked[ordinal]
            identity = old["lexical_identity"]
            cid = "existing-korean:" + canonical_sha256(identity)
            expected = {
                "candidate_id": cid,
                "inventory_record_sha256": canonical_sha256(old),
                "source_sense_id": identity["sense_id"],
                "source_ordinal": ordinal,
                "source_physical_line": row["source_physical_line"],
                "source_form": row["source_form"],
                "source_pos": row["source_pos"],
                "source_frequency_rank": row["publisher_rank"],
                "source_line_utf8_sha256": row["source_line_utf8_sha256"],
            }
            if (
                any(link.get(key) != value for key, value in expected.items())
                or identity["submitted_form"] != row["source_form"]
                or identity["sense_id"] != f"nikl:{ordinal}"
            ):
                raise ValueError("existing candidate alias does not match exact source row")
            aliases.append(
                {
                    **expected,
                    "source_row_id": row["source_row_id"],
                    "existing_lemma": identity["lemma"],
                    "existing_pos": identity["part_of_speech"],
                    "historical_final_rank": old["final_rank"],
                    "review_unit_id": link["review_unit_id"],
                    "packet_path": link["packet_path"],
                    "review_authority": "unchanged_not_replayed_or_promoted",
                    "production_eligible": False,
                }
            )
            row["registry_role"] = "existing_candidate_alias"
        else:
            rejection = rejected[ordinal]
            if rejection["source_form_sha256"] != hashlib.sha256(
                row["source_form"].encode()
            ).hexdigest() or rejection["reason_code"] not in {
                "unsupported_pos",
                "beyond_target_count",
            }:
                raise ValueError("historical rejection source binding or reason mismatch")
            unsupported = rejection["reason_code"] == "unsupported_pos"
            pending.append(
                {
                    "source_row_id": row["source_row_id"],
                    "source_ordinal": ordinal,
                    "source_form": row["source_form"],
                    "source_pos": row["source_pos"],
                    "historical_rejection_reason": rejection["reason_code"],
                    "review_reason": "unsupported_source_pos"
                    if unsupported
                    else "previously_excluded_by_count",
                    "review_status": "pending_review",
                    "active_queue_member": False,
                    "production_eligible": False,
                }
            )
            row["registry_role"] = "pending_review"
        rows.append(row)
    if len({row["source_row_id"] for row in rows}) != len(rows) or len(
        {row["candidate_id"] for row in aliases}
    ) != len(aliases):
        raise ValueError("registry identity collision")
    binding = {
        "schema_version": "korean-source-registry-1",
        "bundle_manifest_sha256": bundle_manifest_sha256,
        "supplement_manifest_sha256": supplement_manifest_sha256,
        "source_sha256": supplemental["source_sha256"],
        "inventory_sha256": supplemental["inventory_sha256"],
        "links_sha256": supplemental["output_sha256"],
        "source_version": manifest["source_version"],
    }
    summary = {
        **binding,
        "source_rows": len(rows),
        "existing_links": len(aliases),
        "pending_rows": len(pending),
        "pending_reasons": dict(Counter(row["review_reason"] for row in pending)),
        "missing_publisher_rank": sum(row["publisher_rank"] is None for row in rows),
        "generation_status": "deferred_by_user",
        "production_eligible": False,
        "provider_api_calls": 0,
        "added_to_active_queue": 0,
        "first_pass_completed_by_registry": 0,
        "ranking_status": "source_metadata_only_no_final_order",
        "source_license_decision_preserved": manifest.get("license_decision"),
        "new_registry_approval_status": "preparation_only_no_new_linguistic_or_redistribution_approval",
        "sources": {"bundle": str(bundle), "supplement": str(supplement)},
        "metadata_reference": "https://www.korean.go.kr/front/etcData/etcDataView.do?etc_seq=70&mn_id=46",
    }
    persist_artifact(
        output,
        kind="korean-source-registry",
        binding=canonical_sha256(binding),
        files={
            "source-rows.jsonl": _jsonl(rows),
            "existing-aliases.jsonl": _jsonl(aliases),
            "pending-review.jsonl": _jsonl(pending),
            "summary.json": json_bytes(summary),
        },
    )
    return summary
