"""The vocabulary runner must bind decisions and keep unresolved work visible."""

import hashlib
import json

import pytest

from scripts import qualify_mandarin_inventory as runner


def test_offline_freeze_rejects_source_drift_and_keeps_pending(tmp_path):
    row = {"word": "两个", "flags": ["missing-cedict-entry"], "cedict": [],
           "wiktextract": [], "frequency_candidate": {"rank": 50, "level": 1}}
    path = tmp_path / "audit.jsonl"
    path.write_text(json.dumps(row), encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {"decisions": [{"word": "两个", "disposition": "pending", "components": [],
                             "senses": [], "reason": "Requires a compositional-use decision."}]}
    with pytest.raises(ValueError, match="checksum"):
        runner.freeze(audit=path, audit_sha256="a" * 64, payload=payload, output=tmp_path / "bad")
    result = runner.freeze(audit=path, audit_sha256=digest, payload=payload, output=tmp_path / "ok")
    assert result["pending_count"] == 1
    assert result["qualified_count"] == 0
    assert result["candidate_count"] == 1
    assert result["production_eligible"] is False
    assert (tmp_path / "ok" / "manifest.json").exists()


def test_packet_preserves_exact_source_and_gloss_instead_of_default_reading():
    row = {"word": "也", "flags": [], "frequency_candidate": {"rank": 9, "level": 1},
           "cedict": [
               {"traditional": "也", "simplified": "也", "numbered_pinyin": "Ye3",
                "glosses": ["surname Ye"], "line_sha256": "a" * 64},
               {"traditional": "也", "simplified": "也", "numbered_pinyin": "ye3",
                "glosses": ["also; too"], "line_sha256": "b" * 64},
           ], "wiktextract": []}
    packet = runner.packet_rows([row])
    assert [(c["source_ref"], c["glosses"]) for c in packet[0]["choices"]] == [
        ("c0", ["surname Ye"]), ("c1", ["also; too"])]


def test_offline_freeze_rejects_missing_decisions(tmp_path):
    row = {"word": "也", "flags": [], "cedict": [], "wiktextract": [],
           "frequency_candidate": {"rank": 9, "level": 1}}
    path = tmp_path / "audit.jsonl"
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError, match="word set"):
        runner.freeze(audit=path, audit_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      payload={"decisions": []}, output=tmp_path / "bad")


def test_session_cli_prepares_and_imports_without_provider_calls(tmp_path, capsys):
    row = {"word": "两个", "flags": ["missing-cedict-entry"], "cedict": [], "wiktextract": [],
           "frequency_candidate": {"rank": 50, "level": 1}}
    audit = tmp_path / "audit.jsonl"
    audit.write_text(json.dumps(row), encoding="utf-8")
    digest = hashlib.sha256(audit.read_bytes()).hexdigest()
    request = tmp_path / "request"
    assert runner.main(["prepare", "--audit", str(audit), "--audit-sha256", digest,
                        "--output", str(request), "--limit", "1"]) == 0
    response = tmp_path / "response.json"
    response.write_text(json.dumps({"decisions": [{"word": "两个", "disposition": "compositional",
        "components": ["两", "个"], "senses": [], "reason": "Productive numeral and classifier."}]}))
    request_hash = json.loads((request / "manifest.json").read_text())["binding_sha256"]
    output = tmp_path / "review"
    assert runner.main(["import", "--request", str(request), "--request-sha256", request_hash,
                        "--response", str(response), "--output", str(output)]) == 0
    summary = json.loads((output / "summary.json").read_text())
    assert summary["execution_surface"] == "current_assistant_session"
    assert summary["provider_calls_executed"] == 0
    assert summary["independent_passes"] == 0
    assert summary["candidate_count"] == 1


def test_session_import_refuses_a_changed_request(tmp_path):
    with pytest.raises(ValueError, match="checksum|binding|request"):
        runner.import_review(request=tmp_path, request_sha256="f" * 64,
                             response={"decisions": []}, output=tmp_path / "output")
