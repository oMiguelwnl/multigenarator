"""Resumable selection reviews with a process-safe shared budget and no generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine_runner import (
    _locked,
    json_bytes,
    persist_artifact,
    read_json,
    verify_artifact,
)
from multilang.services.vocabulary_curation import (
    SelectionResponse,
    reconcile_selections,
    selection_messages,
    validate_selections,
)
from multilang.services.vocabulary_review import _plain_path, _read_bytes


def _reserve(root, budget, transport, messages, schema):
    with _locked(root / "budget"):
        path = root / "budget-ledger.json"
        ledger = read_json(path) if path.exists() else {
            "budget_sha256": budget.budget_sha256, "reserved_calls": 0, "reserved_cost": "0",
            "generation_status": "deferred_by_user", "currency": budget.currency,
        }
        if ledger["budget_sha256"] != budget.budget_sha256:
            raise ValueError("shared review budget binding changed")
        reservation = budget.reserve(
            input_tokens=transport.input_token_upper_bound(messages, schema),
            max_output_tokens=transport.limits.max_output_tokens,
            reserved_calls=ledger["reserved_calls"], reserved_cost=Decimal(ledger["reserved_cost"]),
        )
        ledger["reserved_calls"] = reservation.call_number
        ledger["reserved_cost"] = str(reservation.cumulative_reserved_cost)
        pending = root / "budget-ledger.pending"
        pending.write_bytes(json_bytes(ledger))
        pending.replace(path)
        return reservation


def review_selection_packet(*, packet: Path, packet_sha256: str, output: Path, transport, budget) -> dict:
    data = json.loads(_read_bytes(packet, packet_sha256, limit=16 * 1024**2))
    if data.get("packet_sha256") != canonical_sha256({k:v for k,v in data.items() if k != "packet_sha256"}):
        raise ValueError("packet canonical binding mismatch")
    if data.get("generation_status") != "deferred_by_user":
        raise ValueError("selection must remain separate from generation")
    root = _plain_path(output)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / packet_sha256
    binding = canonical_sha256({"packet": packet_sha256, "model": transport.model,
                                "limits": transport.limits.model_dump(mode="json"),
                                "budget": budget.budget_sha256,
                                "response_schema": SelectionResponse.model_json_schema(),
                                "review_policy": "source-only-two-pass-selection-1"})
    with _locked(destination):
        destination.mkdir(exist_ok=True)
        result_path = destination / "result"
        if result_path.exists():
            manifest = verify_artifact(result_path, kind="vocabulary-selection-result")
            if manifest["binding_sha256"] != binding:
                raise ValueError("review result binding changed")
            return read_json(result_path / "result.json")

        def run(phase, proposal=None):
            stage = destination / phase
            if stage.exists():
                manifest = verify_artifact(stage, kind="vocabulary-selection-response")
                if manifest["binding_sha256"] != binding:
                    raise ValueError("review response binding changed")
                response = read_json(stage / "response.json")
                validate_selections(data["groups"], response)
                return response
            attempt = destination / (phase + "-attempt.json")
            if attempt.exists():
                raise ValueError("review attempt already reserved; explicit retry required")
            messages = selection_messages(data["language"], data["groups"], judgment=proposal)
            schema = SelectionResponse.model_json_schema()
            reservation = _reserve(root, budget, transport, messages, schema)
            attempt.write_bytes(json_bytes({"binding_sha256": binding, "phase": phase,
                                            "reserved_at": datetime.now(UTC).isoformat(),
                                            "reservation": reservation.model_dump(mode="json")}))
            try:
                response = transport.complete(messages, schema)
                validate_selections(data["groups"], response.payload)
            except Exception:
                (destination / (phase + "-failure.json")).write_bytes(json_bytes({
                    "status": "provider_or_response_failure", "binding_sha256": binding,
                    "reservation_retained": True, "automatic_retry": False,
                }))
                raise ValueError("curation provider or response failed validation") from None
            metadata = {k:v for k,v in response.model_dump(mode="json").items() if k != "payload"}
            metadata.update(executed_at=datetime.now(UTC).isoformat(), phase=phase,
                            requested_model=transport.model, human_approved=False)
            persist_artifact(stage, kind="vocabulary-selection-response", binding=binding, files={
                "response.json": json_bytes(response.payload), "metadata.json": json_bytes(metadata),
                "reservation.json": json_bytes(reservation),
            })
            return response.payload

        proposal = run("proposal")
        judgment = run("judgment", proposal)
        result = {"language": data["language"], "packet_sha256": packet_sha256,
                  "packet_content_sha256": data["packet_sha256"], "review_binding_sha256": binding,
                  "decisions": reconcile_selections(data["groups"], proposal, judgment),
                  "generation_status": "deferred_by_user", "new_card_texts": 0,
                  "new_translations": 0, "new_audio": 0, "new_decks": 0}
        persist_artifact(result_path, kind="vocabulary-selection-result", binding=binding,
                         files={"result.json": json_bytes(result)})
        return result
