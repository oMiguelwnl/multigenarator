"""Plain-text word-list parsing with deterministic diagnostics."""

from __future__ import annotations

from pathlib import Path

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

    return " ".join(value.split()).casefold()


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

    for line_number, submitted_form in enumerate(raw_text.splitlines(), start=1):
        display_form = submitted_form.strip()
        if not display_form:
            warnings.append(
                WordListWarning(
                    code="blank_line",
                    line_number=line_number,
                    detail="blank line ignored during word-list parsing",
                )
            )
            continue

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
]
