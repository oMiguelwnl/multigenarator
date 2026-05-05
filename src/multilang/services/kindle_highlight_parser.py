"""Deterministic local Kindle highlight export parser."""

from __future__ import annotations

from html.parser import HTMLParser
import hashlib
from pathlib import Path
import re

from multilang.domain.highlights import (
    HighlightProvenance,
    KindleParseResult,
    NormalizedHighlight,
    RejectedHighlight,
)


_CONTROL_CHARACTER_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SCRIPT_OR_STYLE_RE = re.compile(r"(?is)<\s*(script|style)\b|</\s*(script|style)\s*>")
_WHITESPACE_RE = re.compile(r"\s+")
_TEXT_LOCATION_RE = re.compile(r"(?i)location\s+([^\r\n]+)")


class _KindleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._current_class = ""
        self._capture_kind: str | None = None
        self._buffer: list[str] = []
        self.locations: list[str] = []
        self.highlights: list[tuple[str | None, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        class_names = attrs_map.get("class", "")
        self._current_class = class_names
        if "noteHeading" in class_names:
            self._capture_kind = "heading"
            self._buffer = []
        elif "noteText" in class_names:
            self._capture_kind = "text"
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture_kind is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._capture_kind is None:
            return
        captured = _normalize_whitespace(" ".join(self._buffer))
        if self._capture_kind == "heading":
            self.locations.append(captured)
        elif self._capture_kind == "text":
            location = self.locations[-1] if self.locations else None
            self.highlights.append((location, captured))
        self._capture_kind = None
        self._buffer = []
        self._current_class = ""


def parse_kindle_highlight_export(path: str | Path) -> KindleParseResult:
    """Parse a local Kindle HTML or text export into normalized highlight rows."""

    source_path = Path(path)
    suffix = source_path.suffix.lower()
    if suffix in {".html", ".htm"}:
        source_format = "html"
    elif suffix == ".txt":
        source_format = "text"
    else:
        return KindleParseResult(
            rejected=[
                RejectedHighlight(
                    source_index=0,
                    reason_code="unsupported_format",
                    detail="unsupported Kindle export format",
                )
            ]
        )

    try:
        raw_text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = source_path.read_text(encoding="utf-8-sig", errors="replace")

    if not raw_text.strip():
        return KindleParseResult(
            rejected=[RejectedHighlight(source_index=0, reason_code="empty", detail="empty highlight export")]
        )

    if _is_unsafe_fragment(raw_text):
        return KindleParseResult(
            rejected=[RejectedHighlight(source_index=0, reason_code="unsafe", detail="unsafe highlight fragment")]
        )

    records = _parse_html_records(raw_text) if source_format == "html" else _parse_text_records(raw_text)
    highlights: list[NormalizedHighlight] = []
    rejected: list[RejectedHighlight] = []

    if not records:
        rejected.append(RejectedHighlight(source_index=0, reason_code="malformed", detail="no highlight text records found"))
        return KindleParseResult(highlights=highlights, rejected=rejected)

    for index, (location, text) in enumerate(records):
        normalized_text = _normalize_whitespace(text)
        if not normalized_text:
            rejected.append(RejectedHighlight(source_index=index, reason_code="empty", detail="empty highlight record"))
            continue
        if _is_unsafe_fragment(normalized_text):
            rejected.append(RejectedHighlight(source_index=index, reason_code="unsafe", detail="unsafe highlight fragment"))
            continue

        content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        highlights.append(
            NormalizedHighlight(
                highlight_id=f"{source_format}-{index}-{content_hash[:12]}",
                text=normalized_text,
                provenance=HighlightProvenance(
                    source_path=source_path.name,
                    source_format=source_format,
                    source_index=index,
                    raw_location=location,
                    content_hash=content_hash,
                ),
            )
        )

    return KindleParseResult(highlights=highlights, rejected=rejected)


def _parse_html_records(raw_text: str) -> list[tuple[str | None, str]]:
    parser = _KindleHTMLParser()
    parser.feed(raw_text)
    return parser.highlights


def _parse_text_records(raw_text: str) -> list[tuple[str | None, str]]:
    records: list[tuple[str | None, str]] = []
    for block in raw_text.split("=========="):
        lines = [line.strip() for line in block.splitlines()]
        non_empty_lines = [line for line in lines if line]
        if not non_empty_lines:
            continue

        location = next((line for line in non_empty_lines if "highlight" in line.casefold()), None)
        text_lines = [line for line in non_empty_lines if not _looks_like_metadata_line(line)]
        if not text_lines:
            records.append((location, ""))
            continue
        records.append((_extract_location(location), " ".join(text_lines)))
    return records


def _extract_location(line: str | None) -> str | None:
    if not line:
        return None
    match = _TEXT_LOCATION_RE.search(line)
    return f"Location {match.group(1).strip()}" if match else line


def _looks_like_metadata_line(line: str) -> bool:
    folded = line.casefold()
    return folded.startswith("- your highlight") or folded.startswith("synthetic learner reader")


def _normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _is_unsafe_fragment(text: str) -> bool:
    return bool(_CONTROL_CHARACTER_RE.search(text) or _SCRIPT_OR_STYLE_RE.search(text))


__all__ = ["parse_kindle_highlight_export"]
