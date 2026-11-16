import importlib
import json
from pathlib import Path

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.exporting.package import build_multilang_model


def _build_manifest():
    try:
        module = importlib.import_module("multilang.services.anki_template_preview")
    except ModuleNotFoundError:
        pytest.fail("the Anki template preview catalog has not been implemented", pytrace=False)
    return module.build_anki_template_preview_manifest()


def test_preview_catalog_uses_templates_from_existing_export_models():
    manifest = _build_manifest()
    catalog = manifest["catalog"]
    templates = manifest["templates"]

    for key in (
        "frequency:en",
        "word-list:en",
        "kindle-highlights:en",
        "korean-grammar:ko",
        "word-list:la",
        "korean-hangul:ko",
        "japanese-kana:ja",
        "phoneme:ru",
        "phoneme:pl",
        "phoneme:el",
        "korean-pronunciation:ko",
    ):
        assert key in catalog

    for key, source_type, language in (
        ("frequency:en", "frequency", SupportedLanguage.EN),
        ("word-list:en", "word-list", SupportedLanguage.EN),
        ("kindle-highlights:en", "kindle-highlights", SupportedLanguage.EN),
        ("korean-grammar:ko", "korean-grammar", SupportedLanguage.KO),
        ("word-list:la", "word-list", SupportedLanguage.LA),
    ):
        model = build_multilang_model(source_type=source_type, language=language)
        template = templates[catalog[key]]
        assert template["fields"] == [field["name"] for field in model.fields]
        assert template["front"] == model.templates[0]["qfmt"]
        assert template["back"] == model.templates[0]["afmt"]
        assert template["css"] == model.css


def test_preview_catalog_only_advertises_templates_that_exporters_provide():
    catalog = _build_manifest()["catalog"]

    assert "korean-grammar:en" not in catalog
    assert "korean-hangul:ja" not in catalog
    assert "japanese-kana:en" not in catalog


def test_generated_frontend_manifest_matches_current_export_templates():
    manifest_path = (
        Path(__file__).parents[2]
        / "frontend"
        / "apps"
        / "admin"
        / "src"
        / "anki-template-manifest.json"
    )

    assert json.loads(manifest_path.read_text(encoding="utf-8")) == _build_manifest()
