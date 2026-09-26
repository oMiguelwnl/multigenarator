import json
import zipfile
from hashlib import sha256
from types import SimpleNamespace

import pytest
from support.audio import SILENT_MP3

from multilang.services import japanese_kana_generated_deck as kana
from multilang.settings import Settings


def test_kana_inventory_preserves_base_guids_and_adds_reading_lessons():
    from multilang.services.japanese_kana_generated_deck import KANA_FOUNDATION_CARDS

    assert len(kana.GENERATED_KANA_CARDS) == 208
    assert len(KANA_FOUNDATION_CARDS) == 218
    assert {c.guid for c in kana.GENERATED_KANA_CARDS} <= {c.guid for c in KANA_FOUNDATION_CARDS}
    for glyph, legacy in [("ぢ", "dji"), ("づ", "dzu"), ("ヂ", "dji"), ("ヅ", "dzu")]:
        card = next(c for c in KANA_FOUNDATION_CARDS if c.kana == glyph)
        assert card.romaji in {"ji", "zu"}
        assert card.guid == sha256(f"ja-kana|{card.script}|{glyph}|{legacy}".encode()).hexdigest()[:32]
    lessons = [c for c in KANA_FOUNDATION_CARDS if c.lesson_id]
    assert len(lessons) == 10
    assert all(c.audio_text and c.audio_text != c.kana for c in lessons)
    assert all(c.picture == "" for c in KANA_FOUNDATION_CARDS)
    for glyph in ("ん", "ン"):
        card = next(c for c in KANA_FOUNDATION_CARDS if c.kana == glyph)
        assert card.audio_text in {"あん。", "アン。"}
        assert "áudio" in card.mnemonic


def test_kana_audio_failure_blocks_production_package(tmp_path, monkeypatch):
    class Unavailable:
        def __init__(self, *args):
            pass

        def synthesize(self, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(kana, "AzureSpeechAdapter", Unavailable)
    output = tmp_path / "deck.apkg"
    with pytest.raises(ValueError, match="audio"):
        kana.export_generated_kana_deck(output_path=output, cards=kana.GENERATED_KANA_CARDS[:1],
            settings=Settings(_env_file=None, audio_storage_dir=tmp_path / "audio"))
    assert not output.exists()


def test_kana_prototype_is_explicit_and_has_a_manifest(tmp_path, monkeypatch):
    def forbidden(*args):
        raise AssertionError("prototype must not instantiate a paid provider")

    monkeypatch.setattr(kana, "AzureSpeechAdapter", forbidden)
    output = tmp_path / "prototype.apkg"
    result = kana.export_generated_kana_deck(output_path=output, prototype=True)
    assert result.card_count == 218
    manifest = json.loads(output.with_suffix(".manifest.json").read_text())
    assert manifest["prototype"] and manifest["audio_count"] == 0
    assert manifest["base_card_count"] == 208 and manifest["lesson_count"] == 10
    with zipfile.ZipFile(output) as archive:
        assert json.loads(archive.read("media")) == {}


def test_kana_audio_cache_includes_voice_and_rejects_fake_audio(tmp_path, monkeypatch):
    calls = []

    class Synthesizer:
        def __init__(self, *args):
            pass

        def synthesize(self, **kwargs):
            calls.append(kwargs)
            path = kwargs["output_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(SILENT_MP3)
            return SimpleNamespace(storage_path=path)

    monkeypatch.setattr(kana, "AzureSpeechAdapter", Synthesizer)
    settings = Settings(_env_file=None, audio_storage_dir=tmp_path / "audio")
    arguments = dict(cards=kana.GENERATED_KANA_CARDS[:1], settings=settings)
    kana.export_generated_kana_deck(output_path=tmp_path / "one.apkg", **arguments)
    kana.export_generated_kana_deck(output_path=tmp_path / "two.apkg", **arguments)
    assert len(calls) == 1
    monkeypatch.setattr(kana, "KANA_VOICE_ID", "ja-JP-KeitaNeural")
    kana.export_generated_kana_deck(output_path=tmp_path / "three.apkg", **arguments)
    assert len(calls) == 2
    cached = settings.audio_storage_dir / "kana" / calls[-1]["output_path"].name
    cached.write_bytes(b"not-real-audio")
    kana.export_generated_kana_deck(output_path=tmp_path / "four.apkg", **arguments)
    assert len(calls) == 3


def test_verified_strokes_are_packaged_and_untrusted_svg_is_rejected(tmp_path):
    from multilang.services.japanese_kana_strokes import build_kana_stroke_media

    source = tmp_path / "kanjivg"
    source.mkdir()
    svg = '<!-- Copyright (C) Synthetic Stroke Fixture. --><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 109 109"><g><path id="kvg:03042-s1" d="M10,10 L80,80"/></g></svg>'
    path = source / "03042.svg"
    path.write_text(svg)
    manifest = {"files": {"03042.svg": sha256(svg.encode()).hexdigest()}, "source": "KanjiVG",
                "license": "CC-BY-SA-3.0"}
    manifest_path = source / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    card = next(c for c in kana.GENERATED_KANA_CARDS if c.kana == "あ")
    rendered, media, report = build_kana_stroke_media((card,), source=source, output=tmp_path / "media",
        manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest())
    assert rendered[0].strokes.startswith('<img src="')
    assert rendered[0].picture == ""
    assert media and all(p.is_file() for p in media)
    assert "Copyright (C) Synthetic Stroke Fixture." in media[0].read_text()
    assert report["covered_cards"] == 1
    path.write_text(svg.replace("<g>", '<script>alert(1)</script><g>'))
    with pytest.raises(ValueError, match="checksum"):
        build_kana_stroke_media((card,), source=source, output=tmp_path / "other",
            manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest())
    manifest["files"]["03042.svg"] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="unsafe"):
        build_kana_stroke_media((card,), source=source, output=tmp_path / "unsafe",
            manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest())


def test_kana_source_acquisition_pins_revision_and_reports_missing_files(tmp_path):
    import httpx

    from multilang.services.vocabulary_acquisition import acquire_source
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M1 1 L2 2"/></svg>'
    def respond(request):
        if request.url.host == "api.github.com":
            return httpx.Response(200, json={"sha": "a" * 40})
        assert request.url.host == "raw.githubusercontent.com"
        assert "/" + "a" * 40 + "/kanji/" in request.url.path
        return httpx.Response(200, content=svg) if request.url.path.endswith("03042.svg") else httpx.Response(404)
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        report = acquire_source(language="ja", kind="kana-strokes", root=tmp_path, client=client)
    assert report["revision"] == "a" * 40
    assert report["downloaded_files"] == 1 and report["missing_files"]
    manifest = tmp_path / report["directory"] / "manifest.json"
    assert sha256(manifest.read_bytes()).hexdigest() == report["manifest_sha256"]
