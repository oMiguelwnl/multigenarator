"""Least-power checkpoint authority validation for Korean frequency work."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.korean import raw_bytes_sha256


runner = CliRunner()
_HASH = "a" * 64


def _write_authority(tmp_path: Path, payload: dict[str, object], *, duplicate: bool = False) -> Path:
    path = tmp_path / "AUTHORITY.md"
    section = "```json\n" + json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n```\n"
    path.write_text("human prose is not authority\n" + section + (section if duplicate else ""), encoding="utf-8")
    return path


def _bound_file(tmp_path: Path) -> dict[str, object]:
    artifact = tmp_path / "retrieval-result.json"
    payload = b'{"status":"valid"}\n'
    artifact.write_bytes(payload)
    return {
        "path": artifact.name,
        "sha256": raw_bytes_sha256(payload),
        "byte_count": len(payload),
    }


def _source_authority(tmp_path: Path) -> dict[str, object]:
    return {
        "schema_version": "korean-checkpoint-authority-v1",
        "kind": "source-access",
        "powers": ["retrieve-source"],
        "expected_kind": "source-access",
        "bindings": [_bound_file(tmp_path)],
        "expectations": {"source_id": "nikl-korean-learners-vocabulary"},
    }


def test_kind_binding_and_nested_sidecar_authority_passes_with_exact_hashes(tmp_path: Path) -> None:
    from multilang.services.korean_checkpoint_authority import validate_korean_checkpoint_authority

    authority_file = _write_authority(tmp_path, _source_authority(tmp_path))

    result = validate_korean_checkpoint_authority(authority_file, expected_kind="source-access")

    assert result.kind == "source-access"
    assert result.powers == ("retrieve-source",)
    assert result.binding_count == 1
    assert result.authority_sha256 == raw_bytes_sha256(authority_file.read_bytes())


def test_marker_prose_duplicate_sections_and_extra_fields_are_rejected(tmp_path: Path) -> None:
    from multilang.services.korean_checkpoint_authority import validate_korean_checkpoint_authority

    payload = _source_authority(tmp_path)
    prose_only = tmp_path / "PROSE.md"
    prose_only.write_text("I approve all Korean source work", encoding="utf-8")

    for authority_file in (
        prose_only,
        _write_authority(tmp_path, payload, duplicate=True),
        _write_authority(tmp_path, payload | {"private_path": "/home/user/source.txt"}),
    ):
        with pytest.raises(ValueError):
            validate_korean_checkpoint_authority(authority_file, expected_kind="source-access")


def test_source_build_separation_blocks_wrong_or_widened_power(tmp_path: Path) -> None:
    from multilang.services.korean_checkpoint_authority import validate_korean_checkpoint_authority

    widened = _source_authority(tmp_path) | {"powers": ["retrieve-source", "build-inactive-bundle"]}
    wrong_kind = _source_authority(tmp_path) | {"kind": "transformation-build", "expected_kind": "transformation-build"}

    for payload, expected_kind in ((widened, "source-access"), (wrong_kind, "source-access")):
        with pytest.raises(ValueError):
            validate_korean_checkpoint_authority(_write_authority(tmp_path, payload), expected_kind=expected_kind)


def test_remediation_power_requires_dependent_audio_bindings_and_no_new_request(tmp_path: Path) -> None:
    from multilang.services.korean_checkpoint_authority import validate_korean_checkpoint_authority

    valid = {
        "schema_version": "korean-checkpoint-authority-v1",
        "kind": "remediation",
        "powers": ["remediate-bound-text", "reject-dependent-audio"],
        "expected_kind": "remediation",
        "bindings": [_bound_file(tmp_path)],
        "expectations": {"item_key": "level-1-rank-0001"},
        "remediation_entries": [
            {
                "item_key": "level-1-rank-0001",
                "word_spoken_text_sha256": _HASH,
                "sentence_spoken_text_sha256": "b" * 64,
                "dependent_audio_requests": [
                    {"request_sha256": "c" * 64, "profile_sha256": "d" * 64}
                ],
                "allows_new_audio_request": False,
            }
        ],
    }

    result = validate_korean_checkpoint_authority(_write_authority(tmp_path, valid), expected_kind="remediation")
    assert result.kind == "remediation"

    missing_dependency = dict(valid)
    missing_dependency["remediation_entries"] = [dict(valid["remediation_entries"][0]) | {"dependent_audio_requests": []}]  # type: ignore[index]
    new_request = dict(valid)
    new_request["remediation_entries"] = [dict(valid["remediation_entries"][0]) | {"allows_new_audio_request": True}]  # type: ignore[index]

    for payload in (missing_dependency, new_request):
        with pytest.raises(ValueError):
            validate_korean_checkpoint_authority(_write_authority(tmp_path, payload), expected_kind="remediation")


def test_cli_validation_emits_only_safe_hash_and_power_counts(tmp_path: Path) -> None:
    authority_file = _write_authority(tmp_path, _source_authority(tmp_path))

    result = runner.invoke(
        create_app(),
        [
            "validate-korean-checkpoint-authority",
            "--authority-file",
            str(authority_file),
            "--expected-kind",
            "source-access",
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "authority_status=valid",
        "authority_kind=source-access",
        "power_count=1",
        "binding_count=1",
        f"authority_sha256={raw_bytes_sha256(authority_file.read_bytes())}",
    ]
    assert str(tmp_path) not in result.output


def test_cli_validation_failures_are_private_data_free(tmp_path: Path) -> None:
    authority_file = _write_authority(tmp_path, _source_authority(tmp_path) | {"private_path": str(tmp_path / "secret.txt")})

    result = runner.invoke(
        create_app(),
        [
            "validate-korean-checkpoint-authority",
            "--authority-file",
            str(authority_file),
            "--expected-kind",
            "source-access",
        ],
    )

    assert result.exit_code == 1
    assert result.output == "korean_checkpoint_authority_error=operation_failed\n"
    assert str(tmp_path) not in result.output
