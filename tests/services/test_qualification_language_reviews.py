"""Review aggregation binds the original packets and preserves every unresolved item."""

import hashlib
import importlib
import json
from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from multilang.services.qualification_machine import (
    MachineActor,
    MachineExecutionMetadata,
    accept_machine_response,
    build_machine_request,
    reconcile_machine_reviews,
)
from multilang.services.qualification_machine_runner import json_bytes, verify_artifact
from multilang.services.qualification_review import LexicalReviewItem, ReviewPacket, ReviewSource


def api():
    return importlib.import_module("multilang.services.qualification_language_reviews")


def ref(path, value):
    path.write_bytes(json_bytes(value))
    return {"path": path, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture(
    tmp_path,
    *,
    language="pt",
    verdict="accepted",
    changed=False,
    missing_judgment=False,
    original_pos="NOUN",
    lemma="casa",
):
    packet = ReviewPacket(
        packet_id="review-" + language,
        language=language,
        split="calibration",
        profile_sha256="a" * 64,
        rubric_sha256="b" * 64,
        items=(
            LexicalReviewItem(
                item_id="house",
                candidate_id="candidate:house",
                candidate_sha256="c" * 64,
                lemma=lemma,
                pos=original_pos,
                glosses=("house",),
                sources=(
                    ReviewSource(
                        source_id="dictionary",
                        source_sha256="d" * 64,
                        record_id="house",
                        excerpt="house",
                    ),
                ),
            ),
        ),
    )
    request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="original", context_id="original", execution_surface="mock"),
        run_id="original",
    )
    original = ref(tmp_path / (language + "-request.json"), request)
    if changed:
        packet = packet.model_copy(update={"packet_id": "another-packet"})
    proposal_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="proposer", context_id="proposal", execution_surface="mock"),
        run_id="proposal",
    )
    decision = dict(
        kind="lexical",
        item_id="house",
        item_sha256=packet.items[0].item_sha256,
        decision=verdict,
        reason="source review",
        citations=[dict(source_index=0, source_sha256="d" * 64, start=0, end=5, quote="house")],
    )
    if verdict in {"accepted", "corrected"}:
        decision.update(
            proposed_lemma=lemma,
            proposed_pos="NOUN",
            proposed_sense_id="dwelling",
            proposed_gloss="house",
        )
    metadata = MachineExecutionMetadata(executed_at=datetime.now(UTC))
    proposal = accept_machine_response(
        proposal_request, {"decisions": [decision]}, metadata=metadata
    )
    judgment_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="judge", context_id="judge", execution_surface="mock"),
        run_id="judge",
        proposal=proposal,
    )
    judgment = accept_machine_response(
        judgment_request, {"decisions": [] if missing_judgment else [decision]}, metadata=metadata
    )
    result = reconcile_machine_reviews(packet, proposal, judgment)
    return original, ref(tmp_path / (language + "-result.json"), result)


def test_aggregation_replays_reviews_and_keeps_missing_language_pending(tmp_path):
    pt, result = fixture(tmp_path)
    es, _ = fixture(tmp_path, language="es")
    config = api().LanguageReviewsInput(requests=(pt, es), results=(result,))
    report = api().build_language_reviews(config)
    assert report["prepared_items"] == 2 and report["reviewed_items"] == 1
    assert report["counts"] == {"machine_agreement": 1, "awaiting_review": 1}
    assert report["production_eligible"] is False and report["qualified"] is False
    assert report["languages"][1]["items"][0]["status"] == "awaiting_review"


@pytest.mark.parametrize(
    "verdict,expected", [("rejected", "machine_rejected"), ("inconclusive", "blocked_uncertainty")]
)
def test_unresolved_and_rejected_are_not_accepted(tmp_path, verdict, expected):
    request, result = fixture(tmp_path, verdict=verdict)
    report = api().build_language_reviews(
        api().LanguageReviewsInput(requests=(request,), results=(result,))
    )
    assert report["counts"] == {expected: 1}


def test_result_from_another_packet_is_rejected(tmp_path):
    request, result = fixture(tmp_path, changed=True)
    with pytest.raises(ValueError, match="packet"):
        api().build_language_reviews(
            api().LanguageReviewsInput(requests=(request,), results=(result,))
        )


def test_missing_judgment_is_not_counted_as_reviewed(tmp_path):
    request, result = fixture(tmp_path, missing_judgment=True)
    report = api().build_language_reviews(
        api().LanguageReviewsInput(requests=(request,), results=(result,))
    )
    assert report["reviewed_items"] == 0
    assert report["counts"] == {"blocked_uncertainty": 1}


def test_consensus_correction_is_displayed_alongside_original_identity(tmp_path):
    request, result = fixture(tmp_path, verdict="corrected", original_pos="VERB")
    report = api().build_language_reviews(
        api().LanguageReviewsInput(requests=(request,), results=(result,))
    )
    item = report["languages"][0]["items"][0]
    assert item["pos"] == "NOUN" and item["original_pos"] == "VERB"
    assert item["sense_id"] == "dwelling"


def test_source_text_is_escaped_in_report_html(tmp_path):
    request, result = fixture(tmp_path, lemma="<em>casa</em>")
    api().export_language_reviews(
        api().LanguageReviewsInput(requests=(request,), results=(result,)), tmp_path / "output"
    )
    html = (tmp_path / "output/report.html").read_text()
    assert "<em>casa</em>" not in html
    assert "&lt;em&gt;casa&lt;/em&gt;" in html


def test_duplicate_or_unrequested_language_is_rejected(tmp_path):
    request, result = fixture(tmp_path)
    es, es_result = fixture(tmp_path, language="es")
    for requests, results in [
        ((request, request), (result,)),
        ((request,), (es_result,)),
        ((request, es), (result, result)),
    ]:
        with pytest.raises(ValueError, match="language"):
            api().build_language_reviews(
                api().LanguageReviewsInput(requests=requests, results=results)
            )


def test_modified_result_bytes_are_rejected(tmp_path):
    request, result = fixture(tmp_path)
    result["path"].write_bytes(b"{}")
    with pytest.raises(ValueError, match="checksum"):
        api().build_language_reviews(
            api().LanguageReviewsInput(requests=(request,), results=(result,))
        )


def test_public_cli_writes_bound_immutable_report(tmp_path):
    from multilang.cli import app

    request, result = fixture(tmp_path)
    config = ref(
        tmp_path / "config.json", api().LanguageReviewsInput(requests=(request,), results=(result,))
    )
    output = tmp_path / "report"
    run = CliRunner().invoke(
        app,
        [
            "native",
            "vocabulary",
            "qualification",
            "ai",
            "review-languages",
            str(config["path"]),
            config["sha256"],
            str(output),
        ],
    )
    assert run.exit_code == 0, run.output
    verify_artifact(output, kind="machine-language-reviews")
    report = json.loads((output / "report.json").read_text())
    assert report["reviewed_items"] == 1
    assert "machine_agreement" in (output / "report.html").read_text()
