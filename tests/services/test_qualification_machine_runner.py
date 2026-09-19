"""Machine runs are local artifacts; synthetic answers never approve real data."""

import json
from datetime import UTC, datetime

import pytest


def request_fixture():
    from multilang.services.qualification_machine import MachineActor, build_machine_request
    from multilang.services.qualification_review import (
        LexicalReviewItem,
        ReviewPacket,
        ReviewSource,
    )

    packet = ReviewPacket(
        packet_id="synthetic",
        language="en",
        split="pilot",
        profile_sha256="b" * 64,
        rubric_sha256="c" * 64,
        items=(
            LexicalReviewItem(
                item_id="word",
                candidate_id="candidate",
                candidate_sha256="d" * 64,
                lemma="go",
                pos="VERB",
                glosses=("To move.",),
                sources=(
                    ReviewSource(
                        source_id="synthetic",
                        source_sha256="a" * 64,
                        record_id="record",
                        excerpt="To move.",
                    ),
                ),
            ),
        ),
    )
    return build_machine_request(
        packet,
        actor=MachineActor(
            actor_id="synthetic-generator",
            context_id="context-1",
            execution_surface="mock",
            provider="mock",
            model="mock-model",
        ),
        run_id="synthetic-run",
    )


def response_fixture(request):
    item = request.packet.items[0]
    return {
        "decisions": [
            {
                "kind": "lexical",
                "item_id": item.item_id,
                "item_sha256": item.item_sha256,
                "decision": "accepted",
                "reason": "Synthetic fixture supported by the supplied gloss.",
                "citations": [
                    {
                        "source_index": 0,
                        "source_sha256": "a" * 64,
                        "start": 0,
                        "end": 8,
                        "quote": "To move.",
                    }
                ],
                "proposed_lemma": "go",
                "proposed_pos": "VERB",
                "proposed_sense_id": "motion",
                "proposed_gloss": "To move.",
            }
        ]
    }


def metadata_fixture():
    from multilang.services.qualification_machine import MachineExecutionMetadata

    return MachineExecutionMetadata(executed_at=datetime(2026, 9, 13, tzinfo=UTC))


def test_export_and_offline_import_are_immutable_and_replayable(tmp_path):
    from multilang.services import qualification_machine_runner as m

    request = request_fixture()
    out = tmp_path / "request"
    first = m.export_machine_request(request, out)
    assert m.export_machine_request(request, out) == first
    answer = json.dumps(response_fixture(request)).encode()
    result = m.import_machine_response(
        request, answer, metadata=metadata_fixture(), output=tmp_path / "answer"
    )
    assert result.origin == "machine"
    assert not result.production_eligible
    assert m.load_machine_submission(tmp_path / "answer") == result
    (out / "messages.json").write_text("[]")
    with pytest.raises(ValueError, match="hash|drift|checksum"):
        m.export_machine_request(request, out)


def test_duplicate_keys_and_overwrite_rejected(tmp_path):
    from multilang.services import qualification_machine_runner as m

    request = request_fixture()
    with pytest.raises(ValueError, match="duplicate"):
        m.import_machine_response(
            request,
            b'{"decisions": [], "decisions": []}',
            metadata=metadata_fixture(),
            output=tmp_path / "bad",
        )
    raw = json.dumps(response_fixture(request)).encode()
    m.import_machine_response(request, raw, metadata=metadata_fixture(), output=tmp_path / "answer")
    changed = response_fixture(request)
    changed["decisions"][0]["reason"] = "A different response."
    with pytest.raises(ValueError, match="drift"):
        m.import_machine_response(
            request,
            json.dumps(changed).encode(),
            metadata=metadata_fixture(),
            output=tmp_path / "answer",
        )


def test_artifact_manifest_cannot_escape_directory(tmp_path):
    from multilang.services import qualification_machine_runner as m

    request = request_fixture()
    m.export_machine_request(request, tmp_path / "request")
    manifest = tmp_path / "request" / "manifest.json"
    data = json.loads(manifest.read_text())
    data["files"]["../external"] = "a" * 64
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        m.export_machine_request(request, tmp_path / "request")


def api_setup():
    from decimal import Decimal

    from multilang.services.qualification_ai_transport import AITransportLimits, MachineRunBudget

    request = request_fixture()
    request = request.model_copy(
        update={"actor": request.actor.model_copy(update={"execution_surface": "api"})}
    )
    budget = MachineRunBudget(
        total_cost=Decimal("0.02"),
        max_calls=2,
        input_cost_per_million=Decimal(1),
        output_cost_per_million=Decimal(1),
        price_basis="Synthetic prices",
    )
    return request, budget, AITransportLimits(max_output_tokens=100)


def fake_transport(request, limits, *, failing=False):
    from types import SimpleNamespace

    class Transport:
        model = request.actor.model
        calls = 0

        def input_token_upper_bound(self, **kwargs):
            return 1000

        def complete(self, **kwargs):
            self.calls += 1
            if failing:
                raise RuntimeError("secret-provider-content")
            return SimpleNamespace(
                payload=response_fixture(request),
                response_model="mock-model",
                input_tokens=50,
                output_tokens=50,
            )

    result = Transport()
    result.limits = limits
    return result


def test_api_success_resumes_without_another_call_and_rejects_config_drift(tmp_path):
    from multilang.services.qualification_machine_runner import run_machine_review

    request, budget, limits = api_setup()
    transport = fake_transport(request, limits)
    output = tmp_path / "run"
    answer = run_machine_review(
        request, transport=transport, budget=budget, output=output, provider_calls_enabled=True
    )
    assert (
        run_machine_review(
            request, transport=transport, budget=budget, output=output, provider_calls_enabled=True
        )
        == answer
    )
    assert transport.calls == 1
    assert json.loads((output / "attempt-000001.json").read_text())["upper_bound_cost"] == "0.0011"
    with pytest.raises(ValueError, match="drift"):
        run_machine_review(
            request,
            transport=transport,
            budget=budget.model_copy(update={"max_calls": 3}),
            output=output,
            provider_calls_enabled=True,
        )


def test_failure_consumes_reservation_and_error_is_redacted(tmp_path):
    from multilang.services.qualification_machine_runner import run_machine_review

    request, budget, limits = api_setup()
    transport = fake_transport(request, limits, failing=True)
    budget = budget.model_copy(update={"max_calls": 1})
    for _ in range(2):
        with pytest.raises(ValueError) as error:
            run_machine_review(
                request,
                transport=transport,
                budget=budget,
                output=tmp_path / "run",
                provider_calls_enabled=True,
            )
        assert "secret-provider-content" not in str(error.value)
    assert transport.calls == 1
    assert "secret-provider-content" not in "".join(
        p.read_text() for p in (tmp_path / "run").glob("*.json")
    )


def test_no_call_before_explicit_budget_and_provider_enable(tmp_path):
    from decimal import Decimal

    from multilang.services.qualification_machine_runner import run_machine_review

    request, budget, limits = api_setup()
    transport = fake_transport(request, limits)
    with pytest.raises(ValueError, match="enabled"):
        run_machine_review(
            request, transport=transport, budget=budget, output=tmp_path / "disabled"
        )
    with pytest.raises(ValueError):
        run_machine_review(
            request,
            transport=transport,
            budget=budget.model_copy(update={"total_cost": Decimal(0)}),
            output=tmp_path / "zero",
            provider_calls_enabled=True,
        )
    assert transport.calls == 0
