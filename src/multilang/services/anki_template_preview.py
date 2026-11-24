"""Export the real Anki note templates for the frontend preview fixture."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from multilang.domain.jobs import SupportedLanguage
from multilang.services.exporting.package import build_multilang_model
from multilang.services.japanese_kana_deck import build_kana_model
from multilang.services.korean_foundation_export import (
    build_korean_hangul_model,
    build_korean_pronunciation_model,
)
from multilang.services.latin_export import build_latin_anki_model
from multilang.services.russian_phoneme_deck import (
    build_greek_phoneme_model,
    build_polish_phoneme_model,
    build_russian_phoneme_model,
)


def build_anki_template_preview_manifest() -> dict[str, Any]:
    """Return a deduplicated catalog copied from the exact models used by exporters."""

    catalog: dict[str, str] = {}
    templates: dict[str, dict[str, Any]] = {}

    def add(key: str, model: Any) -> None:
        if len(model.templates) != 1:
            raise ValueError(f"preview requires exactly one card template: {key}")
        model_template = model.templates[0]
        definition = {
            "fields": [field["name"] for field in model.fields],
            "front": model_template["qfmt"],
            "back": model_template["afmt"],
            "css": model.css,
        }
        serialized = json.dumps(definition, ensure_ascii=False, sort_keys=True)
        template_id = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        templates.setdefault(template_id, definition)
        catalog[key] = template_id

    for source_type in ("frequency", "word-list", "kindle-highlights"):
        for language in SupportedLanguage:
            if language == SupportedLanguage.LA and source_type != "word-list":
                continue
            add(
                f"{source_type}:{language.value}",
                build_multilang_model(source_type=source_type, language=language),
            )

    add(
        "korean-grammar:ko",
        build_multilang_model(
            source_type="korean-grammar",
            language=SupportedLanguage.KO,
        ),
    )
    add("latin-mvp:la", build_latin_anki_model())
    add("korean-hangul:ko", build_korean_hangul_model())
    add("japanese-kana:ja", build_kana_model())
    add("korean-pronunciation:ko", build_korean_pronunciation_model())
    add("phoneme:ru", build_russian_phoneme_model())
    add("phoneme:pl", build_polish_phoneme_model())
    add("phoneme:el", build_greek_phoneme_model())

    return {
        "version": 1,
        "catalog": dict(sorted(catalog.items())),
        "templates": dict(sorted(templates.items())),
    }


__all__ = ["build_anki_template_preview_manifest"]
