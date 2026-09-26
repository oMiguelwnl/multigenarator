"""Offline cost and integrity preflight for source-bound vocabulary review."""

from __future__ import annotations

import json
import os
import re
from decimal import Decimal, localcontext
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_ai_transport import QualificationAITransport
from multilang.services.vocabulary_curation import SelectionResponse, selection_messages
from multilang.services.vocabulary_review import _plain_path, _read_bytes

_PACKET_PATH = re.compile(r"^(?P<language>[a-z]{2})/(?P<number>[0-9]{5})\.json$")


def _safe_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 2:
        raise ValueError("packet path is outside the packet directory")
    return path


def preflight_curation_packets(
    packets: Path, *, output: Path, transport: QualificationAITransport,
    input_cost_per_million: Decimal = Decimal("0.165"),
    output_cost_per_million: Decimal = Decimal("0.66"),
    price_basis: str = "OpenRouter gpt-4o-mini conservative alternative endpoint rates observed 2026-09-20",
) -> dict:
    """Verify every packet and calculate a conservative two-pass review ceiling.

    This function never invokes a provider. The output is a planning artifact,
    not a billing quote or semantic approval.
    """
    packets, output = _plain_path(packets), _plain_path(output)
    if output.exists():
        raise ValueError("preflight output must not already exist")
    summary = json.loads(_read_bytes(packets / "summary.json"))
    manifest = json.loads(_read_bytes(packets / "manifest.json"))
    if summary.get("generation_status") != "deferred_by_user":
        raise ValueError("packet generation status is not deferred")
    if summary.get("packet_count") != sum(row.get("packet_count", 0) for row in summary["languages"]):
        raise ValueError("packet summary count mismatch")
    schema = SelectionResponse.model_json_schema()
    by_language = {}
    bounds: list[int] = []
    judgment_bounds: list[int] = []
    packet_records = []
    for language_row in summary["languages"]:
        language = language_row["language"]
        language_stats = {"language": language, "packet_count": 0, "calls": 0,
                          "input_token_upper_bound": 0, "max_input_token_upper_bound": 0,
                          "proposal_input_token_upper_bound": 0,
                          "judgment_input_token_upper_bound": 0,
                          "judgments_potentially_exceeding_request_limits": 0,
                          "max_message_bytes": 0}
        for packet_ref in language_row.get("packets", []):
            relative = _safe_relative(packet_ref["path"])
            match = _PACKET_PATH.fullmatch(relative.as_posix())
            if match is None or match.group("language") != language:
                raise ValueError("packet path does not match its language")
            expected = manifest.get("files", {}).get(relative.as_posix())
            if expected != packet_ref.get("sha256"):
                raise ValueError("packet manifest checksum mismatch")
            content = _read_bytes(packets / relative, expected, limit=16 * 1024**2)
            data = json.loads(content)
            without_digest = {key: value for key, value in data.items() if key != "packet_sha256"}
            if data.get("packet_sha256") != canonical_sha256(without_digest):
                raise ValueError("packet canonical binding mismatch")
            if data.get("language") != language or data.get("generation_status") != "deferred_by_user":
                raise ValueError("packet metadata mismatch")
            messages = selection_messages(language, data["groups"])
            bound = transport.input_token_upper_bound(messages, schema)
            # Judgment includes the prior JSON response and a different system
            # instruction. Reusing the proposal's input bound undercounts it.
            # The response is byte-bounded before parsing; re-escaping that JSON
            # inside the request string can at most double its bytes. This bound
            # covers accepted requests; oversized judgments still fail locally.
            empty_judgment_bound = transport.input_token_upper_bound(
                selection_messages(language, data["groups"], judgment={}), schema,
            )
            possible_judgment_bound = empty_judgment_bound + 2 * transport.limits.max_response_bytes
            judgment_bound = min(transport.limits.max_input_tokens, possible_judgment_bound)
            message_bytes = len(json.dumps(messages, ensure_ascii=False,
                                           separators=(",", ":")).encode("utf-8"))
            language_stats["packet_count"] += 1
            language_stats["calls"] += 2
            language_stats["input_token_upper_bound"] += bound + judgment_bound
            language_stats["proposal_input_token_upper_bound"] += bound
            language_stats["judgment_input_token_upper_bound"] += judgment_bound
            language_stats["judgments_potentially_exceeding_request_limits"] += (
                possible_judgment_bound > min(transport.limits.max_input_tokens,
                                               transport.limits.max_input_bytes)
            )
            language_stats["max_input_token_upper_bound"] = max(
                language_stats["max_input_token_upper_bound"], bound, judgment_bound
            )
            language_stats["max_message_bytes"] = max(language_stats["max_message_bytes"], message_bytes)
            bounds.append(bound)
            judgment_bounds.append(judgment_bound)
            packet_records.append({"path": relative.as_posix(), "sha256": expected,
                                   "proposal_input_token_upper_bound": bound,
                                   "judgment_input_token_upper_bound": judgment_bound, "calls": 2})
        by_language[language] = language_stats
    if len(packet_records) != summary["packet_count"]:
        raise ValueError("packet inventory does not match summary")
    if not bounds:
        raise ValueError("packet inventory is empty")
    calls = len(bounds) * 2
    input_tokens = sum(bounds) + sum(judgment_bounds)
    output_tokens = calls * transport.limits.max_output_tokens
    with localcontext() as context:
        context.prec = 80
        input_cost = Decimal(input_tokens) * input_cost_per_million / Decimal(1_000_000)
        output_cost = Decimal(output_tokens) * output_cost_per_million / Decimal(1_000_000)
        total_cost = input_cost + output_cost
    ordered = sorted([*bounds, *judgment_bounds])
    result = {
        "schema_version": "vocabulary-selection-preflight-2",
        "source_packets_sha256": summary["source_manifest_sha256"],
        "model": transport.model,
        "limits": transport.limits.model_dump(mode="json"),
        "languages": list(by_language.values()),
        "packet_count": len(bounds), "review_passes_per_packet": 2, "provider_calls_executed": 0,
        "input_token_upper_bound": input_tokens, "output_token_upper_bound": output_tokens,
        "token_bound_statistics": {
            "min": min(ordered), "median": ordered[len(ordered) // 2],
            "p95": ordered[max(0, int(len(ordered) * 0.95) - 1)], "max": max(ordered),
        },
        "price_assumptions": {"input_usd_per_million": str(input_cost_per_million),
                              "output_usd_per_million": str(output_cost_per_million),
                              "price_basis": price_basis},
        "conservative_cost_ceiling_usd": str(total_cost),
        "actual_cost_may_be_lower": True,
        "cost_scope": "accepted_requests_only_oversized_judgments_fail_before_call",
        "generation_status": "deferred_by_user",
        "semantic_status": "machine_review_pending_human_approval",
        "packet_records_sha256": canonical_sha256(packet_records),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".curation-preflight-", dir=output.parent) as temporary:
        staged = Path(temporary) / output.name
        staged.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        os.rename(staged, output)
    return result


__all__ = ["preflight_curation_packets"]
