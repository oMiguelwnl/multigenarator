"""Audit Mandarin candidates against frozen local CC-CEDICT and Wiktextract.

No providers, approvals, frequency rewrites or production activation. Use
--prepare with the full Wiktextract dump to recover traditional spellings first.
All generated reports live under output/reports by default.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

from multilang.services.mandarin_review import audit_word, lookup_forms, read_cedict
from multilang.services.vocabulary_acquisition import _plain_path, split_wiktextract
from multilang.services.vocabulary_sources import SourceLimits, _verified_lines
from multilang.settings import Settings


def _sha(path: Path) -> str:
    with _plain_path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _dictionary(path: Path, digest: str) -> dict[str, list[dict]]:
    records = defaultdict(list)
    for line in _verified_lines(path, digest, SourceLimits()):
        record = json.loads(line)
        if record.get("lang_code") == "zh":
            records[record["word"]].append(record)
    return records


def _write(root: Path, name: str, value) -> None:
    _plain_path(root / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def run(args) -> dict:
    root = _plain_path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    frequency_sha = _sha(args.frequency)
    frequency_text = "".join(_verified_lines(
        args.frequency, frequency_sha, SourceLimits(max_bytes=4 * 1024**2),
    ))
    candidates = list(csv.DictReader(io.StringIO(frequency_text)))
    words = [row["display_form"] for row in candidates]
    if not words or len(words) != len(set(words)):
        raise ValueError("frequency inventory must be nonempty with unique spellings")
    additional = []
    if args.additional_words:
        additional = json.loads("".join(_verified_lines(
            args.additional_words, _sha(args.additional_words), SourceLimits(max_bytes=1024**2),
        )))
        if (not isinstance(additional, list) or len(additional) > 10_000
                or any(not isinstance(word, str) or not 1 <= len(word) <= 512 for word in additional)):
            raise ValueError("additional lookups must be a bounded list of words")
    entries = list(read_cedict(args.cedict, expected_sha256=args.cedict_sha256))
    forms = lookup_forms(words + additional, entries)
    _write(root, "lookup-forms.json", forms)
    if args.prepare:
        result = split_wiktextract(
            args.wiktextract, args.wiktextract_sha256, args.prepare,
            {"zh": set(forms)}, max_output_bytes=1024**3,
        )
        _write(root, "preparation.json", result)
        return result
    dictionary = _dictionary(args.wiktextract, args.wiktextract_sha256)
    old_dictionary = (
        _dictionary(args.previous_wiktextract, args.previous_sha256)
        if args.previous_wiktextract else None
    )
    by_word = defaultdict(list)
    for entry in entries:
        by_word[entry.simplified].append(entry)
    form_index = defaultdict(set)
    for spelling, reasons in forms.items():
        for reason in reasons:
            form_index[reason["seed"]].add(spelling)
    results = []
    recovered = []
    for row in candidates:
        word = row["display_form"]
        records = [r for form in sorted(form_index[word]) for r in dictionary.get(form, [])]
        result = audit_word(word, entries=by_word[word], records=records)
        result["frequency_candidate"] = row
        if old_dictionary is not None:
            previous = audit_word(word, entries=by_word[word], records=[
                r for form in sorted(form_index[word]) for r in old_dictionary.get(form, [])
            ])
            result["previous_structured_record_count"] = previous["structured_mandarin_record_count"]
            if (not previous["structured_mandarin_record_count"]
                    and result["structured_mandarin_record_count"]):
                recovered.append(word)
        results.append(result)
    report_path = _plain_path(root / "vocabulary-audit.jsonl")
    with report_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    flags = Counter(flag for row in results for flag in row["flags"])
    status = Counter(row["status"] for row in results)
    summary = {
        "schema_version": 1, "language": "zh", "locale": "zh-CN",
        "reviewer": "Codex AI; deterministic source triage, not independent human review",
        "production_eligible": False, "redistribution_approved": False,
        "inventory_count": len(results), "cedict_total_records": len(entries),
        "additional_lookup_words": additional,
        "status_counts": dict(status), "flag_counts": dict(flags),
        "recovered_structured_headwords": recovered,
        "sources": {
            "frequency": {"file": str(args.frequency), "sha256": frequency_sha},
            "cedict": {"file": str(args.cedict), "sha256": args.cedict_sha256,
                       "url": "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz",
                       "attribution": "CC-CEDICT contributors; MDBG distribution",
                       "license": "CC-BY-SA-4.0"},
            "wiktextract": {"file": str(args.wiktextract), "sha256": args.wiktextract_sha256,
                            "url": "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"},
        },
        "limitations": [
            "Dictionary-supported candidates still require lemma/POS/sense selection.",
            "Wiktextract record-level readings are not mapped automatically to each sense.",
            "Converted spellings are lookup hints, not identity or dialect proof.",
            "Reading disagreements include legitimate variants; they are not all errors.",
            "No sentence/audio review or spoken/written occurrence coverage is implied.",
            "Agreement with pypinyin is not an independent dictionary vote.",
        ],
    }
    _write(root, "summary.json", summary)
    _write(root, "review-queue.json", [{
        "word": row["word"], "rank": row["frequency_candidate"].get("rank"),
        "flags": row["flags"],
    } for row in results if row["flags"]])
    lines = [
        "# Triagem do vocabulário de mandarim", "",
        f"{len(results)} candidatos examinados. Revisão automatizada por IA com fontes locais verificadas.",
        "Nenhuma entrada foi marcada como aprovada para produção por esta triagem.", "",
        "| Resultado | Entradas |", "|---|---:|",
        *[f"| {key} | {value} |" for key, value in sorted(status.items())], "",
        f"{len(recovered)} palavras recuperaram evidência estruturada ao consultar grafias tradicionais.",
        "", "## Sinais para revisão", "", "Os sinais se sobrepõem; não somar como entradas distintas.",
        "", "| Sinal | Entradas |", "|---|---:|",
        *[f"| {key} | {value} |" for key, value in sorted(flags.items())], "",
        "`vocabulary-audit.jsonl` preserva grafias, leituras, sentidos, etiquetas e hashes das fontes.",
        "`review-queue.json` contém os candidatos com pendências; `summary.json` guarda totais e fontes.",
        "", "O wordfreq fornece ordem de frequência, não identidades lexicais aprovadas. CC-CEDICT",
        "complementa leituras e grafias; Wiktextract complementa classes e sentidos. A seleção de",
        "sentido e a qualidade de exemplos e áudios exigem etapas próprias. Não há medição de 90%",
        "de cobertura oral/escrita neste relatório.", "",
    ]
    _plain_path(root / "triage.md").write_text("\n".join(lines), encoding="utf-8")
    return {"inventory_count": len(results), "status_counts": dict(status),
            "flag_counts": dict(flags), "recovered": len(recovered), "output": str(root)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frequency", type=Path, default=Path("assets/frequency/zh/curated-v1.csv"))
    parser.add_argument("--additional-words", type=Path, help="JSON list of extra pilot/source lookups")
    parser.add_argument("--cedict", type=Path, required=True)
    parser.add_argument("--cedict-sha256", required=True)
    parser.add_argument("--wiktextract", type=Path, required=True)
    parser.add_argument("--wiktextract-sha256", required=True)
    parser.add_argument("--previous-wiktextract", type=Path)
    parser.add_argument("--previous-sha256")
    parser.add_argument("--prepare", type=Path, help="New cache directory for expanded spellings")
    parser.add_argument("--output", type=Path,
                        default=Settings().report_output_dir / "mandarin" / "linguistic-review")
    args = parser.parse_args()
    if bool(args.previous_wiktextract) != bool(args.previous_sha256):
        parser.error("previous dictionary path and checksum must be supplied together")
    print(json.dumps(run(args), ensure_ascii=False, indent=2))
