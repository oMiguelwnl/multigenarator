"""Deterministic JSON and Markdown report writers for deck audits."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from collections import defaultdict

from multilang.domain.deck_audit import AuditIssue
from multilang.services.deck_audit_reader import DeckAuditReadResult


@dataclass(frozen=True)
class DeckAuditReportResult:
    """Paths and counts for generated audit reports."""

    json_path: Path
    markdown_path: Path
    issue_count: int


def write_deck_audit_reports(
    read_result: DeckAuditReadResult,
    issues: list[AuditIssue],
    output_dir: Path,
) -> DeckAuditReportResult:
    """Write deterministic machine and human deck-audit reports."""

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    sorted_issues = _sorted_issues(issues)
    json_path = target_dir / "deck-audit.json"
    markdown_path = target_dir / "deck-audit.md"

    json_path.write_text(
        json.dumps(
            _json_payload(read_result, sorted_issues),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown_report(read_result, sorted_issues), encoding="utf-8")
    return DeckAuditReportResult(
        json_path=json_path,
        markdown_path=markdown_path,
        issue_count=len(sorted_issues),
    )


def _json_payload(read_result: DeckAuditReadResult, issues: list[AuditIssue]) -> dict[str, object]:
    return {
        "source_path_name": read_result.source_path_name,
        "input_sha256": read_result.input_sha256,
        "card_count": read_result.card_count,
        "issue_count": len(issues),
        "issues": [_issue_payload(issue) for issue in issues],
    }


def _issue_payload(issue: AuditIssue) -> dict[str, object]:
    payload = asdict(issue)
    payload["issue_type"] = issue.issue_type.value
    return payload


def _markdown_report(read_result: DeckAuditReadResult, issues: list[AuditIssue]) -> str:
    lines = [
        "# Deck Audit Report",
        "",
        f"source_path_name={read_result.source_path_name}",
        f"input_sha256={read_result.input_sha256}",
        f"card_count={read_result.card_count}",
        f"issue_count={len(issues)}",
        "",
    ]
    if not issues:
        lines.extend(["## Result", "", "No normalized Definition audit issues found.", ""])
        return "\n".join(lines)

    grouped: dict[str, dict[str, list[AuditIssue]]] = defaultdict(lambda: defaultdict(list))
    for issue in issues:
        grouped[issue.card_identifier][issue.field_name].append(issue)

    for card_identifier in sorted(grouped):
        lines.extend([f"## Card {card_identifier}", ""])
        for field_name in sorted(grouped[card_identifier]):
            lines.extend([f"### Field: {field_name}", ""])
            for issue in grouped[card_identifier][field_name]:
                lines.extend(
                    [
                        f"- **Type:** {issue.issue_type.value}",
                        f"  - **Severity:** {issue.severity}",
                        f"  - **Message:** {issue.message}",
                        f"  - **Evidence:** {issue.evidence}",
                        f"  - **Recommended next action:** {issue.recommended_action}",
                    ]
                )
            lines.append("")
    return "\n".join(lines)


def _sorted_issues(issues: list[AuditIssue]) -> list[AuditIssue]:
    return sorted(
        issues,
        key=lambda issue: (
            issue.card_identifier,
            issue.field_name,
            issue.issue_type.value,
            issue.note_id,
        ),
    )


__all__ = ["DeckAuditReportResult", "write_deck_audit_reports"]
