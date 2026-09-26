"""Prepare, synthesize with Azure, and export a source-reviewed Mandarin pilot.

Text and pronunciation decisions come from the connected assistant session.
No LLM API is used. Only 'synthesize --allow-provider-calls' contacts Azure.
"""

from __future__ import annotations

import argparse
import json
import re
from html import escape
from pathlib import Path

from multilang.domain.exporting import ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import load_card_template
from multilang.services.exporting.package import export_anki_package
from multilang.services.exporting.presentation import rendered_field_mapping
from multilang.services.mandarin_pilot import prepare_pilot, synthesize_pilot, verified_pilot_rows
from multilang.services.qualification_machine_runner import json_bytes, read_json
from multilang.services.vocabulary_review import _plain_path


def _render(source, values):
    source = re.sub(r"{{#([^{}]+)}}(.*?){{/\1}}",
                    lambda m: m[2] if values.get(m[1]) else "", source, flags=re.DOTALL)
    return re.sub(r"{{([^{}]+)}}", lambda m: str(values[m[1]]), source)


def export(root: Path, deck: Path) -> dict:
    root, deck = _plain_path(root), _plain_path(deck)
    rows, media = verified_pilot_rows(root)
    template = load_card_template("word-list", language=SupportedLanguage.ZH)
    links = []
    for index, row in enumerate(rows):
        values = rendered_field_mapping(row)
        front = _render(template.front, values)
        back = _render(template.back.replace("{{FrontSide}}", front), values)
        back = re.sub(r"\[sound:([a-f0-9]{64}\.mp3)\]",
                      r'<audio hidden preload="none" src="media/\1"></audio>'
                      '<button type="button" class="pilot-play" aria-label="Ouvir áudio" '
                      'onclick="this.previousElementSibling.currentTime=0;'
                      'this.previousElementSibling.play()">▶</button>', back)
        identifier = f"card-{index + 1:03d}.html"
        previous = f"card-{(index - 1) % len(rows) + 1:03d}.html"
        following = f"card-{(index + 1) % len(rows) + 1:03d}.html"
        html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>Mandarim · {escape(row.word)}</title><style>{template.css}'
                '.card{flex-direction:column;align-items:center;justify-content:flex-start}'
                '.pilot-nav{font:14px/1.5 system-ui;margin:12px;text-align:center}'
                '.pilot-nav a{color:#9dc2ff;margin:0 10px}audio[hidden]{display:none}'
                '.pilot-play{display:inline-flex;align-items:center;justify-content:center;'
                'width:34px;height:34px;padding:0;border:1px solid #777;border-radius:50%;'
                'background:transparent;color:#c1c7d3;font-size:17px;cursor:pointer}'
                '</style></head><body class="card nightMode">'
                f'<nav class="pilot-nav">Piloto revisado por IA · {index + 1}/{len(rows)}<br>'
                f'<a href="{previous}">Anterior</a><a href="index.html">Lista</a>'
                f'<a href="{following}">Próximo</a></nav><main id="qa">{back}</main></body></html>')
        _plain_path(root / identifier).write_text(html, encoding="utf-8")
        links.append(f'<li><a href="{identifier}">{escape(row.word)} · {escape(row.mandarin_word_pinyin)}</a></li>')
    _plain_path(root / "index.html").write_text(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Piloto de mandarim</title><style>body{background:#101218;color:#e9ebf0;font:18px/1.7 system-ui;'
        'max-width:760px;margin:32px auto;padding:0 20px}a{color:#9dc2ff}ul{columns:2}</style>'
        f'<h1>Piloto de mandarim</h1><p>{len(rows)} contextos revisados por IA, com áudio Azure. '
        'Pinyin e cores mostram os tons lexicais; a fala pode realizar mudanças de tom.</p><ul>'
        + ''.join(links) + '</ul></html>', encoding="utf-8")
    _plain_path(root / "cards.json").write_bytes(json_bytes([r.model_dump(mode="json") for r in rows]))
    result = export_anki_package(rows=rows, media_index=media, output_path=deck,
                                deck_name="Multilang::Mandarim::Piloto revisado por IA")
    return {"notes": result.card_count, "media_files": len(result.media_files),
            "preview": str(root / "index.html"), "deck": str(result.output_path)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--cards", type=Path, required=True)
    prepare.add_argument("--cards-sha256", required=True)
    prepare.add_argument("--bundle-path", type=Path, required=True)
    prepare.add_argument("--bundle-sha256", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    synth = commands.add_parser("synthesize")
    synth.add_argument("--root", type=Path, required=True)
    synth.add_argument("--allow-provider-calls", action="store_true")
    exports = commands.add_parser("export")
    exports.add_argument("--root", type=Path, required=True)
    exports.add_argument("--deck", type=Path, required=True)
    args = vars(parser.parse_args(argv))
    operation = args.pop("command")
    if operation == "prepare":
        args["rows"] = [ExportCardRow.model_validate(r) for r in read_json(args.pop("cards"), args.pop("cards_sha256"))]
        result = prepare_pilot(**args)
    elif operation == "synthesize":
        if not args.pop("allow_provider_calls"):
            parser.error("Azure synthesis requires --allow-provider-calls")
        from multilang.settings import Settings
        result = synthesize_pilot(**args, settings=Settings())
    else:
        result = export(**args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
