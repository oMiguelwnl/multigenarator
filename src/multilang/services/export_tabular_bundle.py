"""Write UTF-8-safe CSV and TSV fallback export bundles."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from multilang.domain.exporting import ExportArtifactFormat, ExportCardRow, export_field_names_for_rows


@dataclass(frozen=True)
class ExportTabularBundleResult:
    output_path: Path
    card_count: int


def write_export_tabular_bundle(
    *,
    rows: list[ExportCardRow],
    export_format: ExportArtifactFormat,
    output_dir: Path,
    deck_name: str,
    note_type_name: str,
) -> ExportTabularBundleResult:
    if export_format not in {ExportArtifactFormat.CSV, ExportArtifactFormat.TSV}:
        raise ValueError(f"unsupported tabular export format: {export_format.value}")

    output_dir.mkdir(parents=True, exist_ok=True)
    sorted_rows = sorted(rows, key=lambda row: (row.sort_index or 0, row.identity.item_key))
    field_names = export_field_names_for_rows(sorted_rows)
    delimiter = "\t" if export_format is ExportArtifactFormat.TSV else ","
    separator_name = "Tab" if export_format is ExportArtifactFormat.TSV else "Comma"
    suffix = ".tsv" if export_format is ExportArtifactFormat.TSV else ".csv"
    output_path = output_dir / f"multilang-export{suffix}"

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)

    buffer.write(f"#separator:{separator_name}\n")
    buffer.write("#html:true\n")
    buffer.write(f"#notetype:{note_type_name}\n")
    buffer.write(f"#deck:{deck_name}\n")
    buffer.write(f"#columns:{delimiter.join(field_names)}\n")

    for row in sorted_rows:
        mapping = row.ordered_field_mapping(field_names=field_names)
        writer.writerow([
            _serialize_field(mapping[field_name]) for field_name in field_names
        ])

    output_path.write_text(buffer.getvalue(), encoding="utf-8")
    return ExportTabularBundleResult(output_path=output_path, card_count=len(sorted_rows))


def _serialize_field(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


__all__ = ["ExportTabularBundleResult", "write_export_tabular_bundle"]
