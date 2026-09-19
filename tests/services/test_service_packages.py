"""Stable compatibility imports share implementations and monkeypatch seams."""

import ast
import importlib
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("legacy", "canonical", "symbol"),
    [
        ("lexical_pipeline", "vocabulary.pipeline", "LexicalPipeline"),
        ("ranking", "vocabulary.ranking", "RankingEngine"),
        ("native_audio", "audio.native", "NativeAudioService"),
        ("audio_integrity", "audio.integrity", "assert_word_audio_matches_word"),
        ("fallback_audio_adapter", "audio.fallback", "FallbackAudioAdapter"),
        ("native_review", "review.native", "NativeReviewService"),
        ("text_review", "review.text", "TextReviewService"),
        ("semantic_anki", "exporting.semantic", "project_cards"),
        ("semantic_anki_fields", "exporting.fields", "semantic_field_note"),
        ("export_tabular_bundle", "exporting.tabular", "write_export_tabular_bundle"),
        ("export_anki_package", "exporting.package", "export_anki_package"),
    ],
)
def test_legacy_import_and_patch_use_canonical_implementation(legacy, canonical, symbol, monkeypatch):
    old = importlib.import_module(f"multilang.services.{legacy}")
    try:
        new = importlib.import_module(f"multilang.services.{canonical}")
    except ModuleNotFoundError:
        pytest.fail(f"service responsibility package is missing: {canonical}")
    assert old is new
    assert getattr(old, symbol) is getattr(new, symbol)
    marker = object()
    monkeypatch.setattr(old, symbol, marker)
    assert getattr(new, symbol) is marker


def test_domain_does_not_depend_on_application_or_persistence():
    domain = Path(__file__).resolve().parents[2] / "src/multilang/domain"
    forbidden = ("multilang.services", "multilang.repositories", "multilang.db", "sqlalchemy")
    violations = []
    for path in domain.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(forbidden):
                violations.append(f"{path.name}:{node.lineno}: {node.module}")
            elif isinstance(node, ast.Import):
                violations.extend(
                    f"{path.name}:{node.lineno}: {name.name}"
                    for name in node.names if name.name.startswith(forbidden)
                )
    assert not violations, "Domain imports application dependencies: " + ", ".join(violations)
