"""Render bounded, checksum-verified KanjiVG geometry into inert stroke SVGs.

No source XML, styling, links, events or scripts are embedded in Anki. Each
derived image contains original attribution and a CC BY-SA link in metadata.
"""

from __future__ import annotations

import json
import os
import re
from contextlib import ExitStack
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET
from xml.parsers import expat

import httpx

from multilang.services.vocabulary_acquisition import _plain_path

_SVG = "http://www.w3.org/2000/svg"
_ATTRIBUTION = ("KanjiVG, Copyright Ulrich Apel and contributors; "
    "https://kanjivg.tagaini.net/ ; CC BY-SA 3.0 "
    "https://creativecommons.org/licenses/by-sa/3.0/ . "
    "Multilang adaptation: geometry recomposed, stroke numbers and colors added.")


def acquire_kana_strokes(root: Path, *, max_bytes: int, client=None) -> dict:
    """Acquire only required kana at one resolved, immutable Git commit."""
    from multilang.services.japanese_kana_generated_deck import KANA_FOUNDATION_CARDS
    if not 1 <= max_bytes <= 8 * 1024**3:
        raise ValueError("invalid kana source byte budget")
    root = _plain_path(root)
    root.mkdir(parents=True, exist_ok=True)
    used = 0
    with ExitStack() as stack:
        http = client or stack.enter_context(httpx.Client(timeout=30, follow_redirects=False, trust_env=False))

        def download(url, limit, optional=False):
            nonlocal used
            with http.stream("GET", url, follow_redirects=False) as response:
                if optional and response.status_code == 404:
                    return None
                if response.is_redirect:
                    raise ValueError("kana source redirects are forbidden")
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes(8192):
                    used += len(chunk)
                    data.extend(chunk)
                    if len(data) > limit or used > max_bytes:
                        raise ValueError("kana source byte limit exceeded")
                return bytes(data)

        revision = json.loads(download("https://api.github.com/repos/KanjiVG/kanjivg/commits/master", 1024 * 1024)).get("sha", "")
        if not re.fullmatch(r"[a-f0-9]{40}", revision):
            raise ValueError("KanjiVG revision is not an immutable commit")
        directory = "kanjivg-" + revision
        target = _plain_path(root / directory)
        if target.exists():
            raise ValueError("KanjiVG snapshot already exists; use its verified manifest")
        staging = Path(stack.enter_context(TemporaryDirectory(prefix=".kana-source-", dir=root))) / directory
        staging.mkdir()
        names = sorted({f"{ord(c):05x}.svg" for card in KANA_FOUNDATION_CARDS for c in card.kana
                        if '\u3040' <= c <= '\u30ff' and c != '・'})
        hashes, missing = {}, []
        for name in names:
            data = download(f"https://raw.githubusercontent.com/KanjiVG/kanjivg/{revision}/kanji/{name}", 128 * 1024, True)
            if data is None:
                missing.append(name)
                continue
            _geometry(data)
            (staging / name).write_bytes(data)
            hashes[name] = sha256(data).hexdigest()
        manifest = {"schema_version": 1, "source": "KanjiVG", "license": "CC-BY-SA-3.0",
            "revision": revision, "files": hashes, "missing_files": missing, "attribution": _ATTRIBUTION}
        path = staging / "manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report = {"directory": directory, "revision": revision, "manifest_sha256": sha256(path.read_bytes()).hexdigest(),
            "downloaded_files": len(hashes), "missing_files": missing, "bytes": used}
        os.rename(staging, target)
        return report


def _verified_file(path: Path, expected: str, limit: int) -> bytes:
    path = _plain_path(path)
    if not re.fullmatch(r"[a-f0-9]{64}", expected) or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("invalid or oversized KanjiVG source")
    data = path.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError("KanjiVG checksum mismatch")
    return data


def _geometry(data: bytes) -> tuple[str, ...]:
    parser = expat.ParserCreate(namespace_separator="|")
    paths, depth, nodes = [], 0, 0

    def reject(*args):
        raise ValueError("unsafe KanjiVG SVG content")

    def start(name, attributes):
        nonlocal depth, nodes
        depth += 1
        nodes += 1
        local = name.split("|")[-1]
        if depth > 32 or nodes > 2048 or local not in {"svg", "g", "path", "text", "title", "desc", "metadata"}:
            reject()
        if depth == 1 and name != _SVG + "|svg":
            reject()
        if any(key.lower().startswith("on") or key.split("|")[-1] in {"href", "src"}
               or "url(" in value.lower() for key, value in attributes.items()):
            reject()
        if local == "path":
            geometry = attributes.get("d", "")
            # Only SVG path commands and finite, bounded numbers are copied.
            if not geometry or len(geometry) > 8192 or not re.fullmatch(r"[MmLlHhVvCcSsQqTtAaZz0-9eE+.,\s-]+", geometry):
                reject()
            numbers = re.findall(r"[+-]?(?:\d*\.\d+|\d+)(?:[eE][+-]?\d+)?", geometry)
            if any(not -10000 <= float(number) <= 10000 for number in numbers) or len(paths) >= 64:
                reject()
            if "transform" in attributes:
                reject()
            paths.append(geometry)
        elif local == "g" and "transform" in attributes:
            # KanjiVG's stroke-number labels use transforms, but geometry may
            # never inherit one that this renderer would silently discard.
            if "StrokeNumbers" not in attributes.get("id", ""):
                reject()

    def end(name):
        nonlocal depth
        depth -= 1

    # KanjiVG's internal ATTLIST declarations are harmless metadata. Never
    # resolve its external SVG DTD or accept an entity declaration.
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.EntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject
    parser.ProcessingInstructionHandler = reject
    parser.StartElementHandler, parser.EndElementHandler = start, end
    try:
        parser.Parse(data, True)
    except expat.ExpatError as exc:
        raise ValueError("malformed KanjiVG SVG") from exc
    if not paths:
        raise ValueError("KanjiVG SVG has no strokes")
    return tuple(paths)


def build_kana_stroke_media(cards, *, source: Path, output: Path, manifest_sha256: str):
    source, output = _plain_path(source), _plain_path(output)
    manifest = json.loads(_verified_file(source / "manifest.json", manifest_sha256, 256 * 1024))
    if manifest.get("source") != "KanjiVG" or manifest.get("license") != "CC-BY-SA-3.0":
        raise ValueError("KanjiVG source attribution and license are required")
    files = manifest.get("files", {})
    if not isinstance(files, dict) or len(files) > 512 or any(not re.fullmatch(r"[0-9a-f]{5}\.svg", key) for key in files):
        raise ValueError("invalid KanjiVG file manifest")
    output.mkdir(parents=True, exist_ok=True)
    parsed, credits, media, rendered, missing = {}, {}, [], [], set()
    covered = 0
    for card in cards:
        glyphs = [glyph for glyph in card.kana if '\u3040' <= glyph <= '\u30ff' and glyph != '・']
        names = [f"{ord(glyph):05x}.svg" for glyph in glyphs]
        absent = [name for name in names if name not in files]
        if not names or absent:
            missing.update(absent)
            rendered.append(replace(card, strokes=""))
            continue
        for name in names:
            if name not in parsed:
                data = _verified_file(source / name, files[name], 128 * 1024)
                parsed[name] = _geometry(data)
                # Preserve source copyright/license comments as escaped XML
                # text, never as executable source markup.
                credits[name] = "\n".join(comment.strip() for comment in
                    re.findall(r"<!--(.*?)-->", data.decode("utf-8"), re.DOTALL)
                    if "Copyright" in comment)
        svg = ET.Element("svg", {"xmlns": _SVG, "viewBox": f"0 0 {109 * len(names)} 109"})
        ET.SubElement(svg, "metadata").text = _ATTRIBUTION + "\n" + "\n".join(sorted({credits[name] for name in names}))
        for index, name in enumerate(names):
            group = ET.SubElement(svg, "g", {"transform": f"translate({index * 109} 0)"})
            for order, geometry in enumerate(parsed[name], 1):
                ET.SubElement(group, "path", {"d": geometry, "fill": "none", "stroke": f"hsl({(order - 1) * 47 % 360},65%,38%)",
                    "stroke-width": "3", "stroke-linecap": "round", "stroke-linejoin": "round"})
                start = re.match(r"\s*[Mm]\s*([+-]?[\d.]+)[,\s]+([+-]?[\d.]+)", geometry)
                if start:
                    ET.SubElement(group, "text", {"x": start[1], "y": start[2], "font-size": "8",
                        "fill": "#111", "stroke": "white", "stroke-width": "0.3"}).text = str(order)
        data = ET.tostring(svg, encoding="utf-8", xml_declaration=True)
        path = _plain_path(output / f"kana-strokes-{sha256(data).hexdigest()}.svg")
        path.write_bytes(data)
        media.append(path)
        rendered.append(replace(card, strokes=f'<img src="{path.name}" alt="Ordem dos traços">'))
        covered += 1
    return tuple(rendered), tuple(dict.fromkeys(media)), {
        "requested_cards": len(cards), "covered_cards": covered,
        "missing_glyph_files": sorted(missing), "source_manifest_sha256": manifest_sha256,
        "attribution": _ATTRIBUTION, "animation": False,
    }
