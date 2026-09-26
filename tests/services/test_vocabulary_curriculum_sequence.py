import hashlib
import json


def test_curriculum_sequence_keeps_expansions_and_bounded_source_prerequisites(tmp_path):
    from multilang.services.vocabulary_curriculum_sequence import build_curriculum_sequences

    root = tmp_path / "prepared"
    (root / "en").mkdir(parents=True)
    entries = []
    for index in range(3):
        entries.append({"entry_id": f"e{index}", "lemma": f"w{index}", "pos": "NOUN",
                        "provisional_order": index + 1, "proposed_band": "core-1" if index < 2 else "expansion-1",
                        "source_priority": index + 1,
                        "sense_candidates": [{"candidate_id": f"s{index}"}]})
    vocab = {"entries": entries}
    (root / "en/vocabulary.json").write_text(json.dumps(vocab))
    request = {"languages": [{"language": "en"}]}
    (root / "request.json").write_text(json.dumps(request))
    manifest = {"files": {
        "request.json": hashlib.sha256((root / "request.json").read_bytes()).hexdigest(),
        "en/vocabulary.json": hashlib.sha256((root / "en/vocabulary.json").read_bytes()).hexdigest(),
    }}
    (root / "manifest.json").write_text(json.dumps(manifest))
    manifest_sha = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
    result = build_curriculum_sequences(root, manifest_sha, output=tmp_path / "sequence", prerequisite_window=1)
    assert result["entry_count"] == 3
    rows = json.loads((tmp_path / "sequence/en/sequence.json").read_text())["rows"]
    assert rows[2]["proposed_band"] == "expansion-1"
    # References use one-based inclusive ranges into this exact sequence,
    # not a copy of 256 long source IDs on every row (several GB at scale).
    assert rows[2]["proposed_prerequisite_range"] == {"start": 2, "end": 2}
    assert rows[0]["proposed_prerequisite_range"] is None
    assert "introduced_source_entry_ids" not in rows[2]
    assert rows[2]["production_eligible"] is False
