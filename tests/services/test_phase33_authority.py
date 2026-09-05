"""Phase 33 authority and review-input safety tests."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from multilang.services.phase33_authority import (
    Phase33AuthorityError,
    build_phase33_authority_preflight,
    read_phase33_review_input,
    validate_phase33_authority,
)


_HASH = "a" * 64


def test_authority_preflight_exact_allowlist_safe_ids_hashes_counts_only_and_four_audio_roots(tmp_path: Path) -> None:
    result = build_phase33_authority_preflight(
        job_id="job-33",
        policy_sha256=_HASH,
        curriculum_sha256="b" * 64,
        profile_sha256="c" * 64,
        source_sha256="d" * 64,
        target_sha256="e" * 64,
        output_pairs=("prepared=/tmp/prepared.json",),
        audio_roots={
            "word": tmp_path / "word",
            "sentence": tmp_path / "sentence",
            "staging": tmp_path / "staging",
            "journal": tmp_path / "journal",
        },
        custom_safe_ids=("custom-1",),
        highlight_safe_ids=("highlight-1",),
        migration_revision="20260828_19",
        private_capability="phase33-private-token-v1",
        max_private_tokens=24,
    )

    assert result.status == "ready"
    assert result.job_id == "job-33"
    assert result.migration_revision == "20260828_19"
    assert result.private_capability == "phase33-private-token-v1"
    assert result.max_private_tokens == 24
    assert result.custom_count == 1
    assert result.highlight_count == 1
    assert set(result.audio_root_identities) == {"word", "sentence", "staging", "journal"}
    assert "custom-1" not in json.dumps(result.model_dump(mode="json"))
    assert "highlight-1" not in json.dumps(result.model_dump(mode="json"))


def test_authority_preflight_rejects_omitted_option_alternate_root_and_empty_personal_sources(tmp_path: Path) -> None:
    base = dict(
        job_id="job-33",
        policy_sha256=_HASH,
        curriculum_sha256="b" * 64,
        profile_sha256="c" * 64,
        source_sha256="d" * 64,
        target_sha256="e" * 64,
        output_pairs=("prepared=/tmp/prepared.json",),
        audio_roots={
            "word": tmp_path / "word",
            "sentence": tmp_path / "sentence",
            "staging": tmp_path / "staging",
        },
        custom_safe_ids=(),
        highlight_safe_ids=("highlight-1",),
        migration_revision="20260828_19",
        private_capability="phase33-private-token-v1",
        max_private_tokens=24,
    )

    with pytest.raises(Phase33AuthorityError, match="four audio roots"):
        build_phase33_authority_preflight(**base)

    base["audio_roots"] = {
        "word": tmp_path / "word",
        "sentence": tmp_path / "sentence",
        "staging": tmp_path / "staging",
        "journal": tmp_path / "journal",
    }
    with pytest.raises(Phase33AuthorityError, match="nonempty"):
        build_phase33_authority_preflight(**base)


def test_validate_authority_kinds_private_cap_and_revision_path_are_exact(tmp_path: Path) -> None:
    authority = tmp_path / "authority.json"
    authority.write_text(
        json.dumps(
            {
                "kind": "phase33-local-migration",
                "job_id": "job-33",
                "policy_sha256": _HASH,
                "migration_revision": "20260828_19",
                "private_capability": "phase33-private-token-v1",
                "max_private_tokens": 24,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = validate_phase33_authority(authority, expected_kind="phase33-local-migration")

    assert result.status == "valid"
    assert result.authority_sha256 == sha256(authority.read_bytes()).hexdigest()
    assert result.kind == "phase33-local-migration"

    with pytest.raises(Phase33AuthorityError, match="kind"):
        validate_phase33_authority(authority, expected_kind="phase33-audio")


def test_review_input_fixed_root_descriptor_safe_regular_typed_and_hashed(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    inbox = project_root / ".multilang" / "phase33" / "review-inputs"
    inbox.mkdir(parents=True)
    value = inbox / "edit.txt"
    value.write_text("safe edited value", encoding="utf-8")

    result = read_phase33_review_input(value, project_root=project_root, kind="value")

    assert result.relative_path == ".multilang/phase33/review-inputs/edit.txt"
    assert result.size_bytes == len("safe edited value".encode("utf-8"))
    assert result.sha256 == sha256(b"safe edited value").hexdigest()
    assert result.text == "safe edited value"


def test_review_input_rejects_wider_path_symlink_oversize_encoding_and_schema_before_value_release(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    inbox = project_root / ".multilang" / "phase33" / "review-inputs"
    inbox.mkdir(parents=True)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(Phase33AuthorityError, match="fixed inbox"):
        read_phase33_review_input(outside, project_root=project_root, kind="value")

    link = inbox / "link.txt"
    link.symlink_to(outside)
    with pytest.raises(Phase33AuthorityError, match="symlink"):
        read_phase33_review_input(link, project_root=project_root, kind="value")

    bad_json = inbox / "evidence.json"
    bad_json.write_text('{"unknown": true}', encoding="utf-8")
    with pytest.raises(Phase33AuthorityError, match="schema"):
        read_phase33_review_input(bad_json, project_root=project_root, kind="evidence")
