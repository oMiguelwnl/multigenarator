"""Scanner-readable checks for the final v1.2 audit evidence artifact."""

from __future__ import annotations

import re
from pathlib import Path


EVIDENCE_PATH = Path(".planning/phases/16-end-to-end-v12-audit/16-V12-AUDIT-EVIDENCE.md")

REQUIREMENT_IDS = (
    "INGEST-01",
    "INGEST-02",
    "INGEST-03",
    "INGEST-04",
    "NORM-01",
    "NORM-02",
    "NORM-03",
    "CAND-01",
    "CAND-02",
    "CAND-03",
    "MODE-01",
    "MODE-02",
    "GEN-01",
    "GEN-02",
    "GEN-03",
    "EXPORT-01",
    "EXPORT-02",
    "EXPORT-03",
    "PHON-01",
    "PHON-02",
    "PHON-03",
    "SEC-01",
    "SEC-02",
    "EVID-01",
)

REQUIRED_HEADINGS = (
    "Requirement Coverage",
    "Commands Run",
    "Pass Signals",
    "Privacy Checklist",
    "Remaining Caveats",
)

FORBIDDEN_PRIVACY_MARKERS = (
    "reader-secret",
    "WEBDAV_PASSWORD",
    "dav/private",
    "/home/",
    "Secret Novel",
    "Location: 123",
)


def test_final_v12_audit_evidence_is_complete_and_privacy_safe() -> None:
    content = EVIDENCE_PATH.read_text(encoding="utf-8")

    for heading in REQUIRED_HEADINGS:
        assert f"## {heading}" in content

    coverage_rows = re.findall(r"^\| ([-A-Z0-9]+) \| ([^|]+) \| ([^|]+) \|", content, flags=re.MULTILINE)
    coverage = {requirement_id: status.strip() for requirement_id, _phase, status in coverage_rows}

    assert set(coverage) == set(REQUIREMENT_IDS)
    assert coverage["EVID-01"] == "PASS"
    assert all(coverage[requirement_id] in {"COMPLETE", "PASS"} for requirement_id in REQUIREMENT_IDS)

    assert "test_v12_highlight_local_e2e_audit.py" in content
    assert "test_v12_phonetics_and_existing_modes_audit.py" in content
    assert "test_v12_final_audit_evidence.py" in content
    assert "24/24" in content

    for marker in FORBIDDEN_PRIVACY_MARKERS:
        assert marker not in content
