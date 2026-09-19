"""Plain-text word-list parsing with deterministic diagnostics."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel, Field

from multilang.domain.korean import canonicalize_korean
from multilang.domain.personal_sources import PersonalSourceRow


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


class ParsedKoreanOrderedWordList(BaseModel):
    """Korean opt-in ordered ledger preserving every nonblank row."""

    rows: list[PersonalSourceRow] = Field(default_factory=list)
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


def _split_list_syntax(text: str, *, whitespace: bool) -> tuple[list[str], bool, bool]:
    """Split outside grouping quotes; apostrophes inside words stay literal."""
    pairs = {'"': '"', "'": "'", "“": "”", "‘": "’"}
    parts: list[str] = []
    buffer: list[str] = []
    closing = None
    grouped = False
    separated = False
    index = 0
    while index < len(text):
        char = text[index]
        if closing:
            if char == "\\" and index + 1 < len(text) and text[index + 1] == closing:
                if not whitespace:
                    buffer.append(char)
                buffer.append(text[index + 1])
                index += 2
                continue
            if char == closing:
                closing = None
                if not whitespace:
                    buffer.append(char)
            else:
                buffer.append(char)
        elif char in pairs and (index == 0 or text[index - 1].isspace() or text[index - 1] in ",;|"):
            closing = pairs[char]
            grouped = True
            if not whitespace:
                buffer.append(char)
        elif (char.isspace() if whitespace else char in ",;|"):
            separated = True
            if value := "".join(buffer).strip():
                parts.append(value)
            buffer = []
        else:
            buffer.append(char)
        index += 1
    if closing:
        return [text], False, False
    if value := "".join(buffer).strip():
        parts.append(value)
    return parts, grouped, separated


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
    chunks, has_quote_syntax, has_separator_syntax = _split_list_syntax(stripped, whitespace=False)
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
        for chunk in chunks:
            tokens, grouped, _ = _split_list_syntax(chunk, whitespace=True)
            entries.extend(tokens if grouped else [chunk])
        return entries

    parts, grouped, _ = _split_list_syntax(stripped, whitespace=True)
    return parts if grouped else [stripped]


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


def parse_korean_ordered_word_list(path: str | Path) -> ParsedKoreanOrderedWordList:
    """Parse Korean custom input without dropping ordered duplicate rows."""

    word_list_path = Path(path)
    try:
        raw_text = word_list_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"word list must be UTF-8 plain text: {word_list_path}") from exc

    rows: list[PersonalSourceRow] = []
    warnings: list[WordListWarning] = []
    first_position_by_key: dict[str, int] = {}
    input_position = 0

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
            display_form = canonicalize_korean(submitted_form.strip())
            duplicate_key = normalize_word_list_key(display_form)
            input_position += 1
            duplicate_of_position = first_position_by_key.get(duplicate_key)
            if duplicate_of_position is None:
                first_position_by_key[duplicate_key] = input_position
            else:
                warnings.append(
                    WordListWarning(
                        code="duplicate_item",
                        line_number=line_number,
                        detail=(
                            "duplicate normalized item already seen at input "
                            f"position {duplicate_of_position}"
                        ),
                    )
                )
            rows.append(
                PersonalSourceRow(
                    input_position=input_position,
                    line_number=line_number,
                    submitted_form=submitted_form,
                    display_form=display_form,
                    normalized_duplicate_key=duplicate_key,
                    duplicate_of_position=duplicate_of_position,
                )
            )

    return ParsedKoreanOrderedWordList(rows=rows, warnings=warnings)


__all__ = [
    "ParsedKoreanOrderedWordList",
    "ParsedWordList",
    "ParsedWordListItem",
    "WordListWarning",
    "normalize_word_list_key",
    "parse_korean_ordered_word_list",
    "parse_word_list",
    "split_dense_word_list_line",
    "split_loose_word_list_line",
]
