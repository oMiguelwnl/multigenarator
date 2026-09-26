import hashlib
import json
from decimal import Decimal

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_ai_transport import (
    AITransportLimits,
    QualificationAITransport,
)
from multilang.services.vocabulary_curation import SelectionResponse, selection_messages


def test_preflight_verifies_packets_and_counts_two_pass_cost_ceiling(tmp_path):
    from multilang.services.vocabulary_curation_preflight import preflight_curation_packets

    root = tmp_path / "packets"
    root.mkdir()
    packet = {
        "language": "en", "generation_status": "deferred_by_user",
        "groups": [{"entry_id": "e", "lemma": "cat", "pos": "NOUN",
                     "sense_candidates": [{"candidate_id": "s", "glosses": ["feline"], "tags": []}],
                     "readings": [], "forms_for_review": []}],
    }
    packet["packet_sha256"] = canonical_sha256(packet)
    content = (json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    (root / "en").mkdir()
    (root / "en/00000.json").write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    summary = {"generation_status": "deferred_by_user", "source_manifest_sha256": "a" * 64,
               "packet_count": 1, "languages": [{"language": "en", "packet_count": 1,
               "packets": [{"path": "en/00000.json", "sha256": digest}]}]}
    (root / "summary.json").write_text(json.dumps(summary))
    (root / "manifest.json").write_text(json.dumps({"files": {"en/00000.json": digest}}))
    transport = QualificationAITransport("fixture/model", AITransportLimits(max_output_tokens=10))
    result = preflight_curation_packets(
        root, output=tmp_path / "preflight.json", transport=transport,
        input_cost_per_million=Decimal("1"), output_cost_per_million=Decimal("1"),
    )
    assert result["packet_count"] == 1
    assert result["provider_calls_executed"] == 0
    assert result["output_token_upper_bound"] == 20
    assert Decimal(result["conservative_cost_ceiling_usd"]) > 0
    proposal = {"decisions": [{"i": 0, "decision": "include", "senses": [0], "display": "cat",
                               "pos": None, "forms": [], "reason": "general_use"}]}
    actual_judgment = transport.input_token_upper_bound(
        selection_messages("en", packet["groups"], judgment=proposal), SelectionResponse.model_json_schema(),
    )
    language = result["languages"][0]
    assert language["judgment_input_token_upper_bound"] >= actual_judgment
    assert language["judgment_input_token_upper_bound"] > language["proposal_input_token_upper_bound"]
    assert result["input_token_upper_bound"] == (
        language["proposal_input_token_upper_bound"] + language["judgment_input_token_upper_bound"]
    )
