"""Plain-text word-list parsing with deterministic diagnostics."""

from __future__ import annotations

from pathlib import Path
import re
import shlex
import unicodedata

from pydantic import BaseModel, Field


class WordListWarning(BaseModel):
    """Structured parse warning for non-fatal input issues."""

    code: str = Field(min_length=1)
    line_number: int = Field(ge=1)
    detail: str = Field(min_length=1)


class ParsedWordListItem(BaseModel):
    """Normalized custom word-list item."""

    line_number: int = Field(ge=1)
    submitted_form: str = Field(min_length=1)
    display_form: str = Field(min_length=1)
    item_key: str = Field(min_length=1)


class ParsedWordList(BaseModel):
    """Parsed word-list payload plus deterministic warnings."""

    items: list[ParsedWordListItem] = Field(default_factory=list)
    warnings: list[WordListWarning] = Field(default_factory=list)


def normalize_word_list_key(value: str) -> str:
    """Normalize submitted text into a stable dedupe key."""

    canonical = unicodedata.normalize("NFC", value)
    return " ".join(canonical.split()).casefold()


_MARKDOWN_LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
_ENTRY_SEPARATOR_RE = re.compile(r"[,;|]")
_DENSE_LIST_SENTENCE_PUNCTUATION_RE = re.compile(r"[.!?]")


def split_dense_word_list_line(line: str) -> list[str]:
    """Split dense title-cased word lists while preserving phrases.

    This supports copied lists such as ``Loge Aplomb Robe de soie`` where a
    capitalized token starts the next entry and lower-case tokens stay attached
    to the current entry. Ordinary one-entry lines are left untouched by
    returning an empty list.
    """

    stripped = _MARKDOWN_LIST_PREFIX_RE.sub("", line.strip())
    if not stripped:
        return []
    if any(quote in stripped for quote in {'"', "'", "‘", "’", "“", "”"}):
        return []
    if _ENTRY_SEPARATOR_RE.search(stripped) or _DENSE_LIST_SENTENCE_PUNCTUATION_RE.search(
        stripped
    ):
        return []

    tokens = [_strip_dense_token(token) for token in stripped.split()]
    tokens = [token for token in tokens if token]
    if len(tokens) < 3:
        return []

    entry_start_count = sum(1 for token in tokens if _looks_like_dense_entry_start(token))
    if entry_start_count < 3:
        return []

    entries: list[str] = []
    current: list[str] = []
    for token in tokens:
        if current and _looks_like_dense_entry_start(token):
            entries.append(" ".join(current))
            current = [token]
            continue
        current.append(token)

    if current:
        entries.append(" ".join(current))
    if len(entries) < 3:
        return []
    return entries


def _strip_dense_token(token: str) -> str:
    return token.strip().strip("()[]{}")


def _looks_like_dense_entry_start(token: str) -> bool:
    stripped = token.lstrip("¿¡\"'‘’“”")
    return bool(stripped) and stripped[0].isalpha() and stripped[0].isupper()


def split_loose_word_list_line(line: str) -> list[str]:
    """Split a loose word-list line while preserving quoted multiword terms.

    Backwards compatibility matters: a normal line such as ``Adiós amigo`` is
    still one submitted item. Lines that opt into loose-list syntax by using
    shell-style quotes, commas, semicolons, pipes, or markdown list prefixes may
    contain multiple entries.
    """

    stripped_line = line.strip()
    stripped = _MARKDOWN_LIST_PREFIX_RE.sub("", stripped_line)
    if not stripped:
        return []

    has_markdown_prefix = stripped != stripped_line
    has_separator_syntax = bool(_ENTRY_SEPARATOR_RE.search(stripped))
    has_quote_syntax = any(quote in stripped for quote in {'"', "'"})
    has_loose_syntax = has_markdown_prefix or has_separator_syntax or has_quote_syntax
    if not has_loose_syntax:
        dense_entries = split_dense_word_list_line(stripped)
        if dense_entries:
            return dense_entries
        return [line]

    if has_markdown_prefix and not has_separator_syntax and not has_quote_syntax:
        dense_entries = split_dense_word_list_line(stripped)
        if dense_entries:
            return dense_entries
        return [stripped]

    if has_separator_syntax:
        entries: list[str] = []
        for chunk in _ENTRY_SEPARATOR_RE.split(stripped):
            chunk = chunk.strip()
            if not chunk:
                continue
            if any(quote in chunk for quote in {'"', "'"}):
                entries.extend(split_loose_word_list_line(chunk))
            else:
                entries.append(chunk)
        return entries

    try:
        parts = shlex.split(stripped, posix=True)
    except ValueError:
        # Unbalanced quotes should not drop user data. Fall back to separator
        # splitting, leaving quote characters visible for later review.
        return [part.strip() for part in _ENTRY_SEPARATOR_RE.split(stripped) if part.strip()]

    return [part.strip() for part in parts if part.strip()]


def parse_word_list(path: str | Path) -> ParsedWordList:
    """Parse a UTF-8 plain-text word list with explicit diagnostics."""

    word_list_path = Path(path)
    try:
        raw_text = word_list_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"word list must be UTF-8 plain text: {word_list_path}") from exc

    items: list[ParsedWordListItem] = []
    warnings: list[WordListWarning] = []
    first_line_by_key: dict[str, int] = {}

    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        submitted_forms = split_loose_word_list_line(raw_line)
        if not submitted_forms:
            warnings.append(
                WordListWarning(
                    code="blank_line",
                    line_number=line_number,
                    detail="blank line ignored during word-list parsing",
                )
            )
            continue

        for submitted_form in submitted_forms:
            display_form = unicodedata.normalize("NFC", submitted_form.strip())
            item_key = normalize_word_list_key(display_form)
            if item_key in first_line_by_key:
                warnings.append(
                    WordListWarning(
                        code="duplicate_item",
                        line_number=line_number,
                        detail=(
                            f"duplicate normalized item '{item_key}' already seen on "
                            f"line {first_line_by_key[item_key]}"
                        ),
                    )
                )
                continue

            first_line_by_key[item_key] = line_number
            items.append(
                ParsedWordListItem(
                    line_number=line_number,
                    submitted_form=submitted_form,
                    display_form=display_form,
                    item_key=item_key,
                )
            )

    return ParsedWordList(items=items, warnings=warnings)


__all__ = [
    "ParsedWordList",
    "ParsedWordListItem",
    "WordListWarning",
    "normalize_word_list_key",
    "parse_word_list",
    "split_dense_word_list_line",
    "split_loose_word_list_line",
]
