"""Shared static presentation for package, tabular and semantic exports."""

from html import unescape

from multilang.domain.exporting import ExportCardRow
from multilang.services.mandarin_orthography import render_mandarin_sentence


def rendered_field_mapping(
    row: ExportCardRow,
    *,
    field_names: tuple[str, ...] | None = None,
    cloze_span: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Keep snapshots immutable and format Mandarin from their saved pinyin."""
    mapping = row.ordered_field_mapping(field_names=field_names)
    if row.identity.language.value == "zh" and "Sentence Pinyin" in mapping:
        mapping["Example Sentence"] = render_mandarin_sentence(
            sentence=unescape(row.example_sentence),
            sentence_pinyin=unescape(row.mandarin_sentence_pinyin or ""),
            cloze_span=cloze_span,
        )
    return mapping
