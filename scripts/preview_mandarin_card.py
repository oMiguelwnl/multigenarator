"""Generate offline front/back previews using the real Mandarin export template.

Run: .venv/bin/python scripts/preview_mandarin_card.py [output-directory]
Audio icons are illustrative; this does not call a speech or text provider.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import load_card_template
from multilang.services.exporting.presentation import rendered_field_mapping
from multilang.services.mandarin_orthography import derive_mandarin_orthography
from multilang.settings import Settings

_AUDIO_ICON = (
    '<span class="replay-button" role="img" aria-label="Áudio ilustrativo">'
    '<svg viewBox="0 0 48 48" aria-hidden="true">'
    '<path d="M24 2a22 22 0 1 0 0 44 22 22 0 0 0 0-44zM18 12l18 12-18 12z" '
    'fill-rule="evenodd"/></svg></span>'
)


def preview_row() -> ExportCardRow:
    word, sentence = "下载", "他下载了很多电影。"
    orthography = derive_mandarin_orthography(word=word, sentence=sentence)
    return ExportCardRow(
        identity=ExportCardIdentity(
            language="zh", source_type="frequency", job_id="preview",
            item_key=word, lemma_key=word, sort_index=1,
        ),
        word=word, front_of_card=word,
        definitions="verb: transferir um arquivo para o dispositivo",
        example_sentence=sentence, translation="Ele baixou muitos filmes.",
        mandarin_word_pinyin=orthography.word_pinyin,
        mandarin_word_traditional=orthography.word_traditional,
        mandarin_sentence_pinyin=orthography.sentence_pinyin,
        mandarin_sentence_traditional=orthography.sentence_traditional,
    )


def write_previews(output_dir: Path) -> tuple[Path, Path]:
    template = load_card_template("frequency", language=SupportedLanguage.ZH)
    values = rendered_field_mapping(preview_row())
    values.update(word_audio=_AUDIO_ICON, sentence_audio=_AUDIO_ICON)

    def render(source: str) -> str:
        source = re.sub(
            r"{{#([^{}]+)}}(.*?){{/\1}}",
            lambda m: m[2] if values.get(m[1]) else "", source, flags=re.DOTALL,
        )
        return re.sub(r"{{([^{}]+)}}", lambda m: str(values[m[1]]), source)

    front = render(template.front)
    back = render(template.back.replace("{{FrontSide}}", front))
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, label, body in (("front", "Frente", front), ("back", "Verso", back)):
        other = "back" if name == "front" else "front"
        page = (
            '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Mandarim · {label}</title><style>{template.css}\n'
            '.card{flex-direction:column;align-items:center;justify-content:flex-start}'
            '.preview-info{font:14px/1.5 sans-serif;color:#bdc2d0;margin:8px 0 16px;text-align:center}'
            '.preview-info a{color:#8ebaff;text-decoration:underline}'
            '</style></head><body class="card nightMode">'
            f'<aside class="preview-info">Prévia visual · {label} · áudio ilustrativo'
            f' · <a href="{other}.html">Virar cartão</a></aside>'
            f'<main id="qa">{body}</main></body></html>'
        )
        path = output_dir / f"{name}.html"
        path.write_text(page, encoding="utf-8")
        paths.append(path)
    return tuple(paths)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", nargs="?", type=Path,
                        default=Settings().preview_output_dir / "mandarin")
    args = parser.parse_args()
    for path in write_previews(args.output_directory):
        print(path.resolve())
