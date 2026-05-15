"""Scanner-readable checks for the final v1.3 milestone evidence artifact."""

from __future__ import annotations

import re
from pathlib import Path


EVIDENCE_PATH = Path(
    ".planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md"
)

REQUIREMENT_IDS = (
    "AUDIT-01",
    "AUDIT-02",
    "AUDIT-03",
    "IPA-01",
    "DEF-01",
    "DEF-02",
    "TRNS-01",
    "TMPL-01",
    "TMPL-02",
    "TMPL-03",
    "AUD-01",
    "AUD-02",
    "VAL-01",
    "VAL-02",
    "VAL-03",
)

REQUIRED_HEADINGS = (
    "Requirement Coverage",
    "Commands Run",
    "Pass Signals",
    "Mode Isolation",
    "Privacy Checklist",
    "Remaining Caveats",
)

REQUIRED_COMMAND_REFERENCES = (
    "tests/cli/test_audit_deck_command.py",
    "tests/services/test_text_field_remediation.py",
    "tests/services/test_text_validation.py",
    "tests/integration/test_v13_normal_template_export_contract.py",
    "tests/services/test_audio_integrity.py",
    "tests/integration/test_v13_normalized_issue_fixtures.py",
    "tests/integration/test_v13_existing_modes_regression_evidence.py",
    "tests/integration/test_v13_final_milestone_evidence.py",
)

FORBIDDEN_PRIVACY_MARKERS = (
    "raw APKG excerpt",
    "WEBDAV_PASSWORD",
    "WEBDAV_USERNAME",
    "reader-secret",
    "dav/private",
    "/home/",
    "C:\\Users\\",
    "Secret Novel",
    "Location: 123",
    "private-token",
)


def test_final_v13_milestone_evidence_is_complete_runnable_and_privacy_safe() -> None:
    content = EVIDENCE_PATH.read_text(encoding="utf-8")

    for heading in REQUIRED_HEADINGS:
        assert f"## {heading}" in content

    coverage_rows = re.findall(
        r"^\| ([-A-Z0-9]+) \| ([^|]+) \| ([^|]+) \|",
        content,
        flags=re.MULTILINE,
    )
    coverage = {requirement_id: status.strip() for requirement_id, _phase, status in coverage_rows}

    assert set(coverage) == set(REQUIREMENT_IDS)
    assert coverage["VAL-03"] == "PASS"
    assert all(coverage[requirement_id] in {"COMPLETE", "PASS"} for requirement_id in REQUIREMENT_IDS)
    assert "15/15" in content

    for command_reference in REQUIRED_COMMAND_REFERENCES:
        assert command_reference in content

    assert "frequency" in content
    assert "word-list" in content
    assert "kindle-highlights" in content
    assert "Russian phonetics" in content
    assert "privacy-safe" in content

    for marker in FORBIDDEN_PRIVACY_MARKERS:
        assert marker not in content
