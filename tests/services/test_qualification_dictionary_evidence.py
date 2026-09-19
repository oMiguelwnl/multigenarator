"""Original dictionary qualifiers remain separate, exact, and source-bound."""

import gzip
import hashlib
import importlib
import json
import unicodedata

import pytest
from typer.testing import CliRunner

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine_evidence import _lexical_projection
from multilang.services.qualification_machine_revision import MachineRevisionSupplement
from multilang.services.qualification_machine_runner import json_bytes, verify_artifact
from multilang.services.qualification_machine_sources import load_verified_review_excerpt
from multilang.services.qualification_review import LexicalReviewItem, ReviewPacket, ReviewSource
from multilang.services.vocabulary_sources import read_wiktextract


def api():
    module = "multilang.services.qualification_dictionary_evidence"
    assert importlib.util.find_spec(module), "original dictionary evidence recovery is missing"
    return importlib.import_module(module)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_bytes(json_bytes(value))
    return {"path": str(path), "sha256": sha(path)}


def dataset(tmp_path, *, compressed=False, all_items=False, large=False, presentation=False):
    record = {
        "word": "cafe\u0301",
        "lang_code": "pt",
        "pos": "noun",
        "tags": ["masculine"],
        "topics": ["drink"],
        "raw_tags": ["entry-label"],
        "categories": [{"name": "Portuguese nouns"}],
        "senses": [
            {
                "glosses": ["coffee"],
                "raw_glosses": ["(rare) cafe\u0301"],
                "topics": ["food"],
                "raw_tags": ["regional label"],
                "categories": ["sense category"],
                "tags": ["rare"],
                "senseid": ["pt:coffee"],
                "examples": [{"text": "Um cafe\u0301."}],
            },
            {"glosses": ["cafe"], "raw_glosses": ["a coffee shop"], "tags": ["countable"]},
        ],
    }
    if large:
        record["senses"][0]["raw_glosses"] = ["x" * 65000]
    if presentation:
        record["senses"][0]["glosses"] = ["a" * 5000]
        record["senses"][0]["senseid"] = ["source:" + "b" * 200]
    dictionary = tmp_path / ("dictionary.jsonl.gz" if compressed else "dictionary.jsonl")
    data = (json.dumps(record) + "\n").encode()
    dictionary.write_bytes(gzip.compress(data) if compressed else data)
    candidates = tuple(read_wiktextract(dictionary, language="pt", expected_sha256=sha(dictionary)))
    items = tuple(
        LexicalReviewItem(
            item_id="lexical:" + candidate.candidate_id,
            candidate_id=candidate.candidate_id,
            candidate_sha256=canonical_sha256(candidate.model_dump(mode="json")),
            lemma=candidate.lemma,
            pos=candidate.pos,
            glosses=tuple(
                part
                for gloss in candidate.glosses
                for part in (gloss[i : i + 4096] for i in range(0, len(gloss), 4096))
            ),
            source_sense_ids=candidate.source_sense_ids,
            sources=(
                ReviewSource(
                    source_id="prepared-dictionary",
                    source_sha256=sha(dictionary),
                    record_id=candidate.candidate_id,
                    excerpt="Normalized dictionary candidate",
                ),
            ),
        )
        for candidate in (() if presentation else candidates if all_items else candidates[:1])
    )
    if presentation:
        from multilang.services.qualification_pilot import _lexical_item

        items = (
            _lexical_item(
                candidates[0],
                {"dictionary_sha256": sha(dictionary)},
                {candidates[0].source_record_sha256: "noun"},
            ),
        )
    packet = ReviewPacket(
        packet_id="dictionary-recovery-fixture",
        language="pt",
        split="pilot",
        profile_sha256="a" * 64,
        rubric_sha256="b" * 64,
        items=items,
    )
    config = {
        "packet": save(tmp_path / "packet.json", packet),
        "dictionary": {"path": str(dictionary), "sha256": sha(dictionary)},
    }
    input_path = tmp_path / "input.json"
    save(input_path, config)
    return record, candidates, packet, config, input_path


def prepare(input_path, output):
    return api().prepare_dictionary_evidence(input_path, sha(input_path), output)


def test_recovery_preserves_exact_sense_qualifiers_nfd_and_historical_hashes(tmp_path):
    record, candidates, packet, config, input_path = dataset(tmp_path, compressed=True)
    originals = {p: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    output = tmp_path / "supplement"
    result = prepare(input_path, output)
    manifest = verify_artifact(output, kind="machine-dictionary-evidence")
    assert result == manifest
    supplements = json.loads((output / "supplements.json").read_text())["supplements"]
    assert len(supplements) == 1
    supplement = MachineRevisionSupplement.model_validate(supplements[0])
    assert supplement.item_ids == (packet.items[0].item_id,)
    source = load_verified_review_excerpt(supplement.reference, language=packet.language)
    assert unicodedata.is_normalized("NFC", source.excerpt)
    assert "\\u0301" in source.excerpt
    evidence = json.loads(source.excerpt)
    assert evidence["sense_index"] == 0
    assert evidence["sense"] == record["senses"][0]
    assert evidence["record"]["word"] == record["word"]
    for field in ("topics", "raw_tags", "categories", "tags"):
        assert evidence["record"][field] == record[field]
    assert evidence["candidate_sha256"] == packet.items[0].candidate_sha256
    assert evidence["source_record_sha256"] == candidates[0].source_record_sha256
    provenance = json.loads((output / "provenance.json").read_text())
    assert provenance["input"]["sha256"] == sha(input_path)
    assert provenance["dictionary"] == config["dictionary"]
    assert provenance["packet_sha256"] == packet.packet_sha256
    assert provenance["production_eligible"] is False
    assert provenance["items"][0]["item_sha256"] == packet.items[0].item_sha256
    assert all(path.read_bytes() == original for path, original in originals.items())
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    assert prepare(input_path, output) == manifest
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_multiple_senses_get_separate_exact_excerpts(tmp_path):
    record, _, packet, _, input_path = dataset(tmp_path, all_items=True)
    output = tmp_path / "out"
    prepare(input_path, output)
    supplements = json.loads((output / "supplements.json").read_text())["supplements"]
    for index, raw in enumerate(supplements):
        supplement = MachineRevisionSupplement.model_validate(raw)
        evidence = json.loads(
            load_verified_review_excerpt(supplement.reference, language="pt").excerpt
        )
        assert evidence["sense_index"] == index
        assert evidence["sense"] == record["senses"][index]
        assert supplement.item_ids == (packet.items[index].item_id,)


def test_recovery_understands_existing_packet_gloss_chunks_and_projected_sense_ids(tmp_path):
    record, _, packet, _, input_path = dataset(tmp_path, presentation=True)
    assert len(packet.items[0].glosses) == 2
    assert packet.items[0].source_sense_ids != tuple(record["senses"][0]["senseid"])
    output = tmp_path / "out"
    prepare(input_path, output)
    evidence = json.loads((output / "evidence.jsonl").read_text())
    assert evidence["sense"] == record["senses"][0]


@pytest.mark.parametrize("field", ["input", "dictionary", "packet"])
def test_recovery_rejects_checksum_drift(tmp_path, field):
    _, _, _, config, input_path = dataset(tmp_path)
    expected = sha(input_path)
    if field == "input":
        input_path.write_bytes(input_path.read_bytes() + b" ")
    else:
        config[field]["sha256"] = "0" * 64
        save(input_path, config)
        expected = sha(input_path)
    with pytest.raises(ValueError, match="checksum|binding"):
        api().prepare_dictionary_evidence(input_path, expected, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("candidate_sha256", "0" * 64),
        ("lemma", "invented"),
        ("pos", "VERB"),
        ("glosses", ["invented sense"]),
        ("source_sense_ids", ["invented:sense"]),
        ("candidate_id", "candidate:" + "0" * 64),
        ("language", "es"),
        ("sense_swap", None),
    ],
)
def test_recovery_rejects_identity_language_or_sense_swap(tmp_path, field, value):
    _, candidates, packet, config, input_path = dataset(tmp_path)
    raw = packet.model_dump(mode="json", exclude_computed_fields=True)
    if field == "language":
        raw["language"] = value
    elif field == "sense_swap":
        raw["items"][0]["candidate_id"] = candidates[1].candidate_id
        raw["items"][0]["sources"][0]["record_id"] = candidates[1].candidate_id
    else:
        raw["items"][0][field] = value
    config["packet"] = save(tmp_path / "packet.json", raw)
    save(input_path, config)
    with pytest.raises(ValueError, match="candidate|identity|language|missing|binding"):
        prepare(input_path, tmp_path / "out")


@pytest.mark.parametrize("field", ["input", "packet", "dictionary", "output"])
def test_recovery_refuses_symlink_paths(tmp_path, field):
    _, _, _, config, input_path = dataset(tmp_path)
    output = tmp_path / "out"
    link = tmp_path / "link"
    if field == "output":
        link.symlink_to(tmp_path, target_is_directory=True)
        output = link / "out"
    elif field == "input":
        link.symlink_to(input_path)
        input_path = link
    else:
        link.symlink_to(config[field]["path"])
        config[field]["path"] = str(link)
        save(input_path, config)
    with pytest.raises(ValueError, match="symlink"):
        prepare(input_path, output)


@pytest.mark.parametrize(
    "limit",
    [
        "max_bytes",
        "max_expanded_bytes",
        "max_line_bytes",
        "max_records",
        "max_output_bytes",
        "max_unique_entries",
    ],
)
def test_recovery_enforces_source_and_output_limits(tmp_path, limit):
    _, _, packet, config, input_path = dataset(tmp_path, all_items=True, compressed=True)
    if limit == "max_records":
        path = tmp_path / "dictionary.jsonl.gz"
        path.write_bytes(gzip.compress(gzip.decompress(path.read_bytes()) + b"\n"))
        config["dictionary"]["sha256"] = sha(path)
        raw = packet.model_dump(mode="json", exclude_computed_fields=True)
        for item in raw["items"]:
            item["sources"][0]["source_sha256"] = sha(path)
        config["packet"] = save(tmp_path / "packet.json", raw)
    config["limits"] = {limit: 1}
    save(input_path, config)
    with pytest.raises(ValueError, match="limit|bounded"):
        prepare(input_path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_oversized_original_sense_is_rejected_instead_of_silently_truncated(tmp_path):
    *_, input_path = dataset(tmp_path, large=True)
    with pytest.raises(ValueError, match="excerpt|limit"):
        prepare(input_path, tmp_path / "out")


def test_recovery_rejects_more_supplements_than_revision_can_consume(tmp_path):
    _, _, packet, config, input_path = dataset(tmp_path)
    raw = packet.model_dump(mode="json", exclude_computed_fields=True)
    item = raw["items"][0]
    raw["items"] = [
        {**item, "item_id": f"lexical:fixture-{index}", "candidate_id": f"candidate:{index:064x}"}
        for index in range(129)
    ]
    config["packet"] = save(tmp_path / "packet.json", raw)
    save(input_path, config)
    with pytest.raises(ValueError, match="supplement limit"):
        prepare(input_path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_artifact_replay_rejects_changed_input_without_overwriting(tmp_path):
    _, _, _, config, input_path = dataset(tmp_path)
    output = tmp_path / "out"
    prepare(input_path, output)
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    config["limits"] = {"max_records": 100}
    save(input_path, config)
    with pytest.raises(ValueError, match="drift"):
        prepare(input_path, output)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_shared_parser_preserves_legacy_candidate_hashes(tmp_path):
    _, candidates, _, _, _ = dataset(tmp_path)
    assert canonical_sha256([row.model_dump(mode="json") for row in candidates]) == (
        "44479798073741fb7b870fda2e7190c1d7d82a5b8d344431512710249a4d7414"
    )


def test_normalized_projection_does_not_claim_original_dictionary_completeness(tmp_path):
    _, candidates, _, _, _ = dataset(tmp_path)
    encoded, omitted = _lexical_projection(candidates[0])
    payload = json.loads(encoded)
    assert not omitted and payload["projection_complete"] is True
    assert payload["projection_scope"] == "normalized-candidate-fields"
    assert payload["original_dictionary_complete"] is False


def test_public_cli_produces_reusable_revision_supplements(tmp_path):
    from multilang.qualification_machine_cli import create_machine_qualification_app

    *_, input_path = dataset(tmp_path)
    output = tmp_path / "cli-output"
    result = CliRunner().invoke(
        create_machine_qualification_app(),
        [
            "prepare-dictionary-evidence",
            str(input_path),
            sha(input_path),
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    verify_artifact(output, kind="machine-dictionary-evidence")
    supplement = json.loads((output / "supplements.json").read_text())["supplements"][0]
    assert load_verified_review_excerpt(
        MachineRevisionSupplement.model_validate(supplement).reference, language="pt"
    ).excerpt
