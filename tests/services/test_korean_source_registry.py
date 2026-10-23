"""Registry preserves literal rows and identities without approving new entries."""

import hashlib
import json
from pathlib import Path

import pytest

from multilang.domain.lexical_identity import canonical_sha256


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path, extra=0):
    bundle = tmp_path / "bundle"
    supplement = tmp_path / "supplement"
    bundle.mkdir()
    supplement.mkdir()
    rows = [
        "1195\t가게\t명\t\tA",
        "\t시험80\t명\t시험 뜻\tC",
        "2\t같이\t부\t함께\tA",
        "3\t같이\t명\t명사\tB",
        "4\t미정\t불\t\tC",
    ]
    rows += [f"{10000 + i}\t추가{i:05}\t명\t\tC" for i in range(extra)]
    (bundle / "source-snapshot.txt").write_bytes(
        ("순위\t단어\t품사\t풀이\t등급\n\n" + "\n".join(rows) + "\n").encode("cp949")
    )
    inventory = [
        {
            "source_rank": i,
            "final_rank": i,
            "lexical_identity": {
                "submitted_form": rows[i - 1].split("\t")[1],
                "lemma": rows[i - 1].split("\t")[1],
                "part_of_speech": "NNG",
                "sense_id": f"nikl:{i}",
            },
        }
        for i in [1, 2]
    ]
    rejections = [
        {
            "source_rank": i,
            "source_form_sha256": hashlib.sha256(rows[i - 1].split("\t")[1].encode()).hexdigest(),
            "reason_code": "unsupported_pos" if i == 5 else "beyond_target_count",
        }
        for i in range(3, len(rows) + 1)
    ]
    for name, records in [("curated-inventory.jsonl", inventory), ("rejections.jsonl", rejections)]:
        (bundle / name).write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
        )
    members = [
        {"relative_path": name, "sha256": _sha(bundle / name), "row_count": count}
        for name, count in [
            ("source-snapshot.txt", len(rows)),
            ("curated-inventory.jsonl", 2),
            ("rejections.jsonl", len(rejections)),
        ]
    ]
    manifest = {
        "source_id": "nikl-korean-learners-vocabulary",
        "source_version": "2003-06-04.revised-2019-05-30",
        "language": "ko",
        "members": members,
        "license_decision": "approved-redistribution",
        "entry_count": 2,
        "rejection_count": len(rejections),
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest))
    links = []
    for r in inventory:
        i = r["source_rank"]
        fields = rows[i - 1].split("\t")
        links.append(
            {
                "candidate_id": "existing-korean:" + canonical_sha256(r["lexical_identity"]),
                "inventory_record_sha256": canonical_sha256(r),
                "source_sense_id": f"nikl:{i}",
                "source_ordinal": i,
                "source_physical_line": i + 2,
                "source_form": fields[1],
                "source_pos": fields[2],
                "source_frequency_rank": int(fields[0]) if fields[0] else None,
                "source_line_utf8_sha256": hashlib.sha256(rows[i - 1].encode()).hexdigest(),
                "review_unit_id": f"group{i}#fragment-0000",
                "packet_path": "ko/00000.json",
            }
        )
    (supplement / "source-links.jsonl").write_text("".join(json.dumps(r) + "\n" for r in links))
    (supplement / "manifest.json").write_text(
        json.dumps(
            {
                "source_sha256": _sha(bundle / "source-snapshot.txt"),
                "inventory_sha256": _sha(bundle / "curated-inventory.jsonl"),
                "output_sha256": _sha(supplement / "source-links.jsonl"),
                "source_encoding": "cp949",
                "linked_candidates": 2,
            }
        )
    )
    return dict(
        bundle=bundle,
        bundle_manifest_sha256=_sha(bundle / "manifest.json"),
        supplement=supplement,
        supplement_manifest_sha256=_sha(supplement / "manifest.json"),
        output=tmp_path / "registry",
    )


def _read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_registry_preserves_rank_missing_homographs_pos_and_existing_aliases(tmp_path):
    from multilang.services.korean_source_registry import build_korean_source_registry

    args = _fixture(tmp_path)
    original = {
        p: _sha(p)
        for directory in [args["bundle"], args["supplement"]]
        for p in directory.iterdir()
    }
    result = build_korean_source_registry(**args)
    rows = _read_rows(args["output"] / "source-rows.jsonl")
    aliases = _read_rows(args["output"] / "existing-aliases.jsonl")
    pending = _read_rows(args["output"] / "pending-review.jsonl")
    assert rows[0]["source_ordinal"] == 1
    assert rows[0]["source_physical_line"] == 3
    assert rows[0]["publisher_rank"] == 1195
    assert rows[1]["publisher_rank"] is None
    assert rows[1]["source_form"] == "시험80"
    assert rows[1]["homograph"]["marker"] == "80"
    assert rows[1]["homograph"]["meaning"] == "not_in_standard_dictionary"
    assert rows[2]["source_form"] == rows[3]["source_form"] == "같이"
    assert rows[2]["source_pos"] != rows[3]["source_pos"]
    assert rows[2]["source_row_id"] != rows[3]["source_row_id"]
    expected = _read_rows(args["supplement"] / "source-links.jsonl")
    assert [r["candidate_id"] for r in aliases] == [r["candidate_id"] for r in expected]
    assert aliases[1]["existing_lemma"] == "시험80"
    assert pending[-1]["review_reason"] == "unsupported_source_pos"
    assert all(r["review_status"] == "pending_review" for r in pending)
    assert result["first_pass_completed_by_registry"] == 0
    assert result["added_to_active_queue"] == 0
    assert (
        result["source_rows"] == 5 and result["existing_links"] == 2 and result["pending_rows"] == 3
    )
    assert all(_sha(p) == digest for p, digest in original.items())
    assert build_korean_source_registry(**args) == result


def test_registry_has_no_3000_source_row_cap(tmp_path):
    from multilang.services.korean_source_registry import build_korean_source_registry

    args = _fixture(tmp_path, extra=3000)
    result = build_korean_source_registry(**args)
    assert result["source_rows"] == 3005
    assert result["pending_rows"] == 3003


@pytest.mark.parametrize(
    "target",
    [
        "source-snapshot.txt",
        "curated-inventory.jsonl",
        "rejections.jsonl",
        "manifest.json",
        "links",
    ],
)
def test_registry_rejects_input_hash_drift_without_output(tmp_path, target):
    from multilang.services.korean_source_registry import build_korean_source_registry

    args = _fixture(tmp_path)
    path = (
        args["supplement"] / "source-links.jsonl" if target == "links" else args["bundle"] / target
    )
    with path.open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="checksum"):
        build_korean_source_registry(**args)
    assert not args["output"].exists()


def test_registry_rejects_rebound_wrong_alias(tmp_path):
    from multilang.services.korean_source_registry import build_korean_source_registry

    args = _fixture(tmp_path)
    path = args["supplement"] / "source-links.jsonl"
    rows = _read_rows(path)
    rows[0]["candidate_id"] = "existing-korean:wrong"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    manifest_path = args["supplement"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"] = _sha(path)
    manifest_path.write_text(json.dumps(manifest))
    args["supplement_manifest_sha256"] = _sha(manifest_path)
    with pytest.raises(ValueError, match="alias"):
        build_korean_source_registry(**args)
    assert not args["output"].exists()


def test_registry_cli_builds_only_offline_artifacts(tmp_path, capsys):
    import importlib.util

    args = _fixture(tmp_path)
    script = Path(__file__).resolve().parents[2] / "scripts/prepare_korean_source_registry.py"
    assert script.is_file()
    spec = importlib.util.spec_from_file_location("registry_cli", script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    argv = [
        arg for key, value in args.items() for arg in ("--" + key.replace("_", "-"), str(value))
    ]
    assert cli.main(argv) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["source_rows"] == 5
    assert result["added_to_active_queue"] == 0
    assert result["production_eligible"] is False


def test_registry_rejects_changed_existing_output(tmp_path):
    from multilang.services.korean_source_registry import build_korean_source_registry

    args = _fixture(tmp_path)
    build_korean_source_registry(**args)
    path = args["output"] / "pending-review.jsonl"
    path.write_text("[]\n")
    with pytest.raises(ValueError, match="checksum"):
        build_korean_source_registry(**args)
    assert path.read_text() == "[]\n"
