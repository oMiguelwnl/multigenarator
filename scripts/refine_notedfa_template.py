"""Refine the supplied notedfa APKG without changing its study data or media.

The original modern Anki archive remains the source of truth. Only the CSS,
example layout and their modification times are replaced in a copied package.
Anki protobuf definitions:
https://github.com/ankitects/anki/blob/main/proto/anki/notetypes.proto
https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto
"""
from __future__ import annotations

import copy
import hashlib
import html
import json
import re
import sqlite3
import time
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote

import zstandard
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

from multilang.services.anki_id_registry import AnkiIdKind, registry_id
from multilang.settings import Settings

ROOT = Path.cwd()
SOURCE = ROOT / "notedfa.apkg"
settings = Settings()
OUT = ROOT / settings.preview_output_dir / "notedfa"
REPORTS = ROOT / settings.report_output_dir / "notedfa"
TARGET = ROOT / settings.export_output_dir / "notedfa_melhorado.apkg"
TEMPLATE = ROOT / "src/multilang/templates/notedfa_refined.md"
LIMIT = 32 * 1024 * 1024
NTID = registry_id(family="core", role="frequency_model", kind=AnkiIdKind.MODEL)


def protobuf_types():
    """Known fields only; protobuf retains all unknown fields on round trips."""
    file = descriptor_pb2.FileDescriptorProto(name="notedfa.proto", package="notedfa", syntax="proto3")
    definitions = {
        "NoteConfig": [("css", 3, 9, False, "")],
        "TemplateConfig": [("q_format", 1, 9, False, ""), ("a_format", 2, 9, False, "")],
        "MediaEntry": [("name", 1, 9, False, ""), ("size", 2, 13, False, ""), ("sha1", 3, 12, False, "")],
        "MediaEntries": [("entries", 1, 11, True, ".notedfa.MediaEntry")],
    }
    for name, fields in definitions.items():
        message = file.message_type.add(name=name)
        for field_name, number, kind, repeated, type_name in fields:
            field = message.field.add(name=field_name, number=number, type=kind, label=3 if repeated else 1)
            if type_name:
                field.type_name = type_name
    pool = descriptor_pool.DescriptorPool()
    pool.Add(file)
    return {name: message_factory.GetMessageClass(pool.FindMessageTypeByName(f"notedfa.{name}")) for name in definitions}


TYPES = protobuf_types()


def decode(kind, blob):
    message = TYPES[kind]()
    message.ParseFromString(blob)
    return message


def without_fields(kind, blob, names):
    message = decode(kind, blob)
    for name in names:
        message.ClearField(name)
    return message.SerializeToString()


def snapshot(connection):
    tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    result = {}
    for table in tables:
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", table):
            raise ValueError("Unexpected table name in input package")
        result[table] = sorted(connection.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr)
    return result


def refined_css(original):
    palette = {
        "--color-text-primary": "#edf3f7",
        "--color-nightMode-text-primary": "#edf3f7",
        "--color-card-background": "#151b22",
        "--color-nightMode-card-background": "#151b22",
        "--color-box-shadow": "rgba(0, 0, 0, 0.24)",
        "--color-audio-button": "#79bbf4",
        "--color-list-bullets": "#6f9fca",
        "--color-sentence-translation": "#a8c9e5",
        "--color-nightMode-sentence-translation": "#a8c9e5",
        "--color-header": "#8faec7",
        "--color-nightMode-header": "#8faec7",
        "--color-divider": "#2b3743",
        "--color-nightMode-divider": "#2b3743",
    }
    css = original
    for key, value in palette.items():
        css, count = re.subn(re.escape(key) + r":\s*[^;]+;", f"{key}: {value};", css)
        assert count == 1, key
    css = css.replace("background: #0a1628;", "background: #0b1016;")
    css = css.replace("border-top: 4px solid #2563eb;", "border-top: 4px solid #4d93ca;")
    css = css.replace("color: #1e3a8a;", "color: #c7e3f9;")
    css = css.replace("color: #93c5fd;", "color: #c7e3f9;")
    css = css.replace("color: var(--color-divader);", "color: #a0b2c2;")
    css = css.replace("opacity: 0.7;", "opacity: 1;")
    css += """

/* Refine the supplied compact layout; original font sizes stay unchanged. */
html,
.card,
.nightMode.card,
body.nightMode {
  background: #0b1016;
  color: var(--color-text-primary);
}

#qa { min-width: 0; }
.customCard { width: 100%; min-width: 0; }
.wordBlock { min-width: 0; }
.targetWord { overflow-wrap: anywhere; }
.targetWordContainer { gap: 12px; }

.examplePanel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  column-gap: 8px;
  min-width: 0;
}
.exampleSentenceLine {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.exampleSentenceText { min-width: 0; line-height: 1.5; }
.sentenceTranslation {
  grid-column: 1;
  padding-top: 8px;
  padding-right: 0;
  line-height: 1.5;
  min-width: 0;
}
.wordAudioButtonBack,
.sentenceAudioButton { flex: 0 0 32px; width: 32px; margin: 0; }
.replay-button,
.soundLink {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  margin: 0;
  background: transparent;
  border: 0;
  border-radius: 0;
  color: var(--color-audio-button);
  vertical-align: middle;
}
.replay-button:focus-visible,
.soundLink:focus-visible { outline: 2px solid #79bbf4; outline-offset: 2px; }
.image { height: auto; padding: 12px 16px; }
.image img { max-height: 210px !important; height: auto !important; display: block; }
"""
    return css


def refined_front(original):
    before = """    <div class="indent">
      {{Example Sentence}}
      <span class="wordAudioButtonBack">{{sentence_audio}}</span>
    </div>
    <div id="translation" class="sentenceTranslation indent" style="display:none;">
      {{Translation}}
    </div>"""
    after = """    <div class="examplePanel indent">
      <div class="exampleSentenceLine">
        <span class="exampleSentenceText">{{Example Sentence}}</span>
        <span class="sentenceAudioButton">{{sentence_audio}}</span>
      </div>
      <div id="translation" class="sentenceTranslation" style="display:none;">
        {{Translation}}
      </div>
    </div>"""
    assert original.count(before) == 1
    return original.replace(before, after)


def write_previews(original_front, front, back, original_css, css, names, note_fields, media_files):
    def render(template, values):
        text = re.sub(r"{{#([^{}]+)}}(.*?){{/\1}}", lambda m: m[2] if values.get(m[1]) else "", template, flags=re.S)
        return re.sub(r"{{([^{}]+)}}", lambda m: values[m[1]], text)

    values = {name: html.escape(value) for name, value in zip(names, note_fields, strict=True)}
    audio_elements = []
    for index, field in enumerate(("word_audio", "sentence_audio")):
        match = re.fullmatch(r"\[sound:([^\]]+)\]", note_fields[names.index(field)])
        assert match and match[1] in media_files
        src = "media/" + quote(match[1])
        values[field] = (f'<a class="replay-button" href="#" data-audio="notedfa-audio-{index}" aria-label="Ouvir áudio">'
                         '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="29"/><path d="M25 18v28l22-14z"/></svg></a>')
        audio_elements.append(f'<audio id="notedfa-audio-{index}" src="{html.escape(src)}" preload="metadata"></audio>')
    audio_script = """<script>document.querySelectorAll('[data-audio]').forEach(button=>button.addEventListener('click',event=>{event.preventDefault();const sound=document.getElementById(button.dataset.audio);sound.currentTime=0;sound.play().catch(()=>{});}));</script>"""
    for version, qfmt, style in (("original", original_front, original_css), ("improved", front, css)):
        rendered_front = render(qfmt, values)
        for side in ("front", "back"):
            body = rendered_front if side == "front" else render(back, values | {"FrontSide": rendered_front})
            page = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                    f'<title>notedfa · {version} · {side}</title><style>{style}</style></head>'
                    f'<body class="card"><main id="qa">{body}</main>{"".join(audio_elements)}{audio_script}</body></html>')
            (OUT / f"{version}-{side}.html").write_text(page, encoding="utf-8")
    index = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>notedfa · Template melhorado</title>
<style>body{margin:0;background:#0b1016;color:#edf3f7;font:16px/1.5 system-ui,sans-serif}.controls{max-width:400px;margin:16px auto;padding:0 16px;display:flex;align-items:center;justify-content:space-between;gap:12px}button{font:inherit;color:#c7e3f9;background:#151b22;border:1px solid #2b3743;border-radius:8px;padding:8px 14px;min-height:44px}iframe{display:block;border:0;width:100%;height:650px}</style></head><body>
<div class="controls"><span>notedfa · <span id="side">Verso</span></span><button id="flip" type="button">Ver frente</button></div><iframe id="preview" src="improved-back.html" title="Cartão de exemplo"></iframe>
<script>let back=true;document.getElementById('flip').addEventListener('click',()=>{back=!back;document.getElementById('preview').src=back?'improved-back.html':'improved-front.html';document.getElementById('side').textContent=back?'Verso':'Frente';document.getElementById('flip').textContent=back?'Ver frente':'Mostrar resposta';});</script></body></html>"""
    (OUT / "index.html").write_text(index, encoding="utf-8")


def main():
    for directory in (OUT, OUT / "media", REPORTS, TARGET.parent):
        directory.mkdir(parents=True, exist_ok=True)
    original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    decompressor = zstandard.ZstdDecompressor()
    with zipfile.ZipFile(SOURCE) as archive, TemporaryDirectory() as temporary:
        assert archive.read("meta") == b"\x08\x03"
        original_db = decompressor.decompress(archive.read("collection.anki21b"), max_output_size=LIMIT)
        database = Path(temporary) / "collection.anki2"
        database.write_bytes(original_db)
        with sqlite3.connect(database) as connection:
            # Read-only names are unchanged. This supplies the collation needed
            # by SQLite's integrity check for Anki's Unicode-name indexes.
            connection.create_collation("unicase", lambda a, b: (a.casefold() > b.casefold()) - (a.casefold() < b.casefold()))
            before = snapshot(connection)
            assert len(before["notes"]) == len(before["cards"]) == 1
            assert {r[2] for r in before["notes"]} == {NTID}
            note_row = connection.execute("SELECT * FROM notetypes WHERE id=?", (NTID,)).fetchone()
            template_row = connection.execute("SELECT * FROM templates WHERE ntid=? AND ord=0", (NTID,)).fetchone()
            note_config = decode("NoteConfig", note_row[4])
            template_config = decode("TemplateConfig", template_row[5])
            original_css = note_config.css
            original_front, back = template_config.q_format, template_config.a_format
            css, front = refined_css(original_css), refined_front(original_front)
            assert sorted(re.findall(r"{{[^{}]+}}", front)) == sorted(re.findall(r"{{[^{}]+}}", original_front))
            note_config.css, template_config.q_format = css, front
            new_note_blob, new_template_blob = note_config.SerializeToString(), template_config.SerializeToString()
            assert without_fields("NoteConfig", new_note_blob, ["css"]) == without_fields("NoteConfig", note_row[4], ["css"])
            assert without_fields("TemplateConfig", new_template_blob, ["q_format"]) == without_fields("TemplateConfig", template_row[5], ["q_format"])
            now = max(int(time.time()), note_row[2] + 1, template_row[3] + 1)
            connection.execute("UPDATE notetypes SET config=?, mtime_secs=? WHERE id=?", (new_note_blob, now, NTID))
            connection.execute("UPDATE templates SET config=?, mtime_secs=? WHERE ntid=? AND ord=0", (new_template_blob, now, NTID))
            connection.execute("UPDATE col SET mod=?", (now * 1000,))
            connection.commit()
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            after = snapshot(connection)
            for table in before:
                if table not in {"notetypes", "templates", "col"}:
                    assert before[table] == after[table], table
            assert len(before["notetypes"]) == len(after["notetypes"]) == 1
            assert note_row[:2] == after["notetypes"][0][:2]
            assert note_row[3] == after["notetypes"][0][3]
            unchanged_templates_before = [r for r in before["templates"] if r[0] != NTID]
            assert unchanged_templates_before == [r for r in after["templates"] if r[0] != NTID]
            expected_col = list(before["col"][0])
            expected_col[2] = now * 1000
            assert after["col"] == [tuple(expected_col)]
            names = [r[0] for r in connection.execute("SELECT name FROM fields WHERE ntid=? ORDER BY ord", (NTID,))]
            note_fields = before["notes"][0][6].split("\x1f")
        updated_db = database.read_bytes()
        compressed = zstandard.ZstdCompressor(level=9).compress(updated_db)
        assert decompressor.decompress(compressed, max_output_size=LIMIT) == updated_db
        with zipfile.ZipFile(TARGET, "w") as output:
            for member in archive.infolist():
                output.writestr(copy.copy(member), compressed if member.filename == "collection.anki21b" else archive.read(member))
        with zipfile.ZipFile(TARGET) as updated:
            assert updated.testzip() is None
            assert archive.namelist() == updated.namelist()
            for member in archive.namelist():
                if member != "collection.anki21b":
                    assert archive.read(member) == updated.read(member), member
        media = decode("MediaEntries", decompressor.decompress(archive.read("media"), max_output_size=LIMIT))
        media_files = []
        for index, entry in enumerate(media.entries):
            if Path(entry.name).name != entry.name or not entry.name.endswith(".mp3"):
                raise ValueError("Unexpected media filename")
            content = decompressor.decompress(archive.read(str(index)), max_output_size=LIMIT)
            assert len(content) == entry.size
            # SHA-1 is required by Anki's existing media format, not used as
            # a security primitive or introduced for new content identity.
            assert hashlib.sha1(content).digest() == entry.sha1
            (OUT / "media" / entry.name).write_bytes(content)
            media_files.append(entry.name)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == original_hash
    TEMPLATE.write_text("# notedfa — compact dark refinement\n\nBased on the supplied notedfa.apkg. Not registered as a replacement for other deck templates.\n\n## Front Template\n\n```html\n" + front + "\n```\n\n## Back Template\n\n```html\n" + back + "\n```\n\n## Styling (CSS)\n\n```css\n" + css + "\n```\n", encoding="utf-8")
    for filename, text in (("front.html", front), ("back.html", back), ("styling.css", css), ("original-styling.css", original_css)):
        (OUT / filename).write_text(text, encoding="utf-8")
    write_previews(original_front, front, back, original_css, css, names, note_fields, media_files)
    report = {"source": str(SOURCE), "source_sha256": original_hash, "apkg": str(TARGET),
              "sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(), "notes": 1, "cards": 1,
              "media_files": len(media_files), "field_names": names, "notetype_id": NTID,
              "preserved": "all note/card/review/field/deck rows, auxiliary metadata, media bytes, note identities and original file",
              "changes": "CSS, example layout, modification times", "package_inspection": "passed",
              "native_anki_import_tested": False,
              "format_reference": "https://github.com/ankitects/anki/blob/main/proto/anki/notetypes.proto"}
    (REPORTS / "package-inspection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
