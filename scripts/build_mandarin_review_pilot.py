"""Build inspectable Mandarin review cards from explicit, source-bound decisions.

Offline only. Keeps the current twelve-field Mandarin template and blank audio.
Decisions are AI review artifacts, not independent approval or production assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import asdict
from html import escape
from pathlib import Path

from multilang.domain.exporting import ExportArtifactFormat, ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import load_card_template
from multilang.services.exporting.presentation import rendered_field_mapping
from multilang.services.exporting.tabular import write_export_tabular_bundle
from multilang.services.mandarin_orthography import MandarinOrthography, derive_mandarin_orthography
from multilang.services.mandarin_review import (
    MandarinPronunciationReview,
    ReviewedMandarinOrthographyService,
    pinyin_key,
    read_cedict,
)
from multilang.services.vocabulary_acquisition import _plain_path
from multilang.services.vocabulary_sources import SourceLimits, _verified_lines
from multilang.settings import Settings


def _render(source: str, values: dict) -> str:
    source = re.sub(r"{{#([^{}]+)}}(.*?){{/\1}}",
                    lambda m: m[2] if values.get(m[1]) else "", source, flags=re.DOTALL)
    return re.sub(r"{{([^{}]+)}}", lambda m: str(values[m[1]]), source)


def build(args) -> dict:
    path = _plain_path(args.decisions)
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    decisions = json.loads("".join(_verified_lines(
        path, digest, SourceLimits(max_bytes=2 * 1024**2, max_records=100_000),
    )))
    if decisions.get("production_eligible") is not False or decisions.get("reviewer") != "Codex AI":
        raise ValueError("pilot must explicitly identify AI review and no production approval")
    by_word = defaultdict(list)
    for entry in read_cedict(args.cedict, expected_sha256=args.cedict_sha256):
        by_word[entry.simplified].append(entry)
    reviews, results = [], []
    cases = decisions["cases"]
    if not 1 <= len(cases) <= 200 or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("pilot requires 1–200 unique cases")
    for case in cases:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case["id"]):
            raise ValueError("invalid case filename")
        source = [e for e in by_word[case["word"]] if e.numbered_pinyin == case["evidence_pinyin"]]
        if not source or case["traditional"] not in {e.traditional for e in source}:
            raise ValueError(f"missing source spelling/reading evidence for {case['id']}")
        if pinyin_key(case["word_pinyin"]) != pinyin_key(case["evidence_pinyin"]):
            alternate = case.get("accepted_alternate", "")
            numbered = " ".join(re.findall(r"[a-zü:]+[1-5]", alternate))
            if (not alternate or pinyin_key(numbered) != pinyin_key(case["word_pinyin"])
                    or not any(f"also pr. [{alternate}]" in e.glosses for e in source)):
                raise ValueError(f"unattested alternate reading for {case['id']}")
        supporting = [e for word in case.get("supporting_words", []) for e in by_word[word]]
        if any(not by_word[word] for word in case.get("supporting_words", [])):
            raise ValueError("missing supporting word evidence")
        review = MandarinPronunciationReview(
            word=case["word"], sentence=case["sentence"],
            orthography=MandarinOrthography(
                word_pinyin=case["word_pinyin"], word_traditional=case["traditional"],
                sentence_pinyin=case["sentence_pinyin"],
                sentence_traditional=case["traditional_sentence"],
            ),
            evidence_record_sha256=tuple(e.line_sha256 for e in source + supporting),
        )
        reviews.append(review)
        before = asdict(derive_mandarin_orthography(word=case["word"], sentence=case["sentence"]))
        after = asdict(review.orthography)
        results.append({
            **case, "reviewer": "Codex AI", "production_eligible": False,
            "before": before, "after": after,
            "changed_fields": [key for key in before if before[key] != after[key]],
            "cedict_evidence": [asdict(e) for e in source + supporting],
        })
    service = ReviewedMandarinOrthographyService(reviews)
    labels = {"NOUN": "substantivo", "VERB": "verbo", "ADJ": "adjetivo", "ADV": "advérbio",
              "AUX": "auxiliar", "PART": "partícula", "PHRASE": "expressão", "INTJ": "saudação"}
    rows = []
    for index, case in enumerate(cases, 1):
        orthography = service.derive(word=case["word"], sentence=case["sentence"])
        label = "classificador" if case.get("features", {}).get("NounType") == "Clf" else labels[case["pos"]]
        rows.append(ExportCardRow(
            identity=ExportCardIdentity(
                language="zh", source_type="word-list", job_id=f"mandarin-ai-review-{digest[:12]}",
                item_key=case["id"], lemma_key=case["word"], sort_index=index,
            ), word=case["word"], front_of_card=case["word"],
            definitions=escape(f"{label}: {case['definition']}"),
            example_sentence=case["sentence"], translation=escape(case["translation"]),
            mandarin_word_pinyin=orthography.word_pinyin,
            mandarin_word_traditional=orthography.word_traditional,
            mandarin_sentence_pinyin=orthography.sentence_pinyin,
            mandarin_sentence_traditional=orthography.sentence_traditional,
        ))
    root = _plain_path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    template = load_card_template("word-list", language=SupportedLanguage.ZH)
    links = []
    for index, (case, row) in enumerate(zip(cases, rows, strict=True)):
        values = rendered_field_mapping(row)
        front = _render(template.front, values)
        back = _render(template.back.replace("{{FrontSide}}", front), values)
        previous = cases[(index - 1) % len(cases)]["id"] + ".html"
        following = cases[(index + 1) % len(cases)]["id"] + ".html"
        page = (
            '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Mandarim · {escape(case["word"])}</title><style>{template.css}\n'
            '.card{flex-direction:column;align-items:center;justify-content:flex-start}'
            '.review-info{font:14px/1.5 sans-serif;color:#c0c5d0;margin:8px 12px 16px;text-align:center}'
            '.review-info a{color:#9dc2ff;margin:0 8px}.review-note{max-width:540px;text-align:left}'
            '</style></head><body class="card nightMode">'
            f'<nav class="review-info">Revisão por IA · {index + 1}/{len(cases)} · sem áudio<br>'
            f'<a href="{previous}">Anterior</a><a href="index.html">Lista</a>'
            f'<a href="{following}">Próximo</a></nav><main id="qa">{back}</main>'
            f'<aside class="review-info review-note">{escape(case["note"])}</aside></body></html>'
        )
        _plain_path(root / f"{case['id']}.html").write_text(page, encoding="utf-8")
        links.append(f'<tr><td><a href="{case["id"]}.html">{escape(case["word"])}</a></td>'
                     f'<td>{escape(case["word_pinyin"])}</td><td>{escape(case["definition"])}</td></tr>')
    index_page = (
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Revisão de mandarim</title><style>body{background:#101218;color:#e9ebf0;'
        'font:17px/1.6 system-ui;max-width:880px;margin:28px auto;padding:0 18px}'
        'a{color:#9dc2ff}td,th{padding:10px;text-align:left;border-bottom:1px solid #424754}'
        'table{border-collapse:collapse;width:100%}td:first-child{font-size:25px;white-space:nowrap}'
        '</style><h1>Revisão de mandarim</h1>'
        f'<p>{len(cases)} contextos revistos por IA com evidências do CC-CEDICT. '
        'Tons lexicais no pinyin; sem áudio e sem aprovação humana independente.</p>'
        '<p>Este piloto mantém o template e os 12 campos do projeto. '
        'A triagem das 3.000 palavras é um relatório separado.</p>'
        '<table><tr><th>Palavra</th><th>Pinyin</th><th>Sentido selecionado</th></tr>'
        + ''.join(links) + '</table></html>'
    )
    _plain_path(root / "index.html").write_text(index_page, encoding="utf-8")
    write_export_tabular_bundle(
        rows=rows, export_format=ExportArtifactFormat.TSV, output_dir=root,
        deck_name="Multilang::Mandarim::Revisão por IA (sem áudio)",
        note_type_name="Multilang::Mandarin Card",
    )
    payload = {"schema_version": 1, "reviewer": "Codex AI", "production_eligible": False,
               "decisions_sha256": digest, "cedict_sha256": args.cedict_sha256,
               "case_count": len(cases), "cases": results,
               "audio_reviewed": False, "independent_review": False,
               "pinyin_policy": decisions["pinyin_policy"],
               "source_attribution": "CC-CEDICT contributors; MDBG distribution; CC-BY-SA-4.0"}
    _plain_path(root / "review.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    _plain_path(root / "cards.json").write_text(
        json.dumps([row.model_dump(mode="json") for row in rows], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"case_count": len(cases), "changed_cases": sum(bool(r["changed_fields"]) for r in results),
            "output": str(root), "production_eligible": False, "audio_reviewed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--cedict", type=Path, required=True)
    parser.add_argument("--cedict-sha256", required=True)
    parser.add_argument("--output", type=Path,
                        default=Settings().example_output_dir / "mandarin" / "review-pilot")
    print(json.dumps(build(parser.parse_args()), ensure_ascii=False, indent=2))
