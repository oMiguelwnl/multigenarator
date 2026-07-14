"""PT-01/PT-02/PT-03 Phase 26 scanner-readable Portuguese translation evidence."""

from __future__ import annotations

import json

from multilang.cli import create_app
from multilang.domain.latin import LatinGenerationRequest
from multilang.domain.source_profiles import get_source_profile
from multilang.services.latin_mvp import LatinMvpGenerationService
from multilang.services.latin_source_pack import load_latin_mvp_source_pack
from multilang.services.latin_translation_quality import (
    DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH,
    LatinPortugueseTranslationQaService,
    load_latin_portuguese_translation_pack,
)


PHASE_26_REQUIREMENTS = ("PT-01", "PT-02", "PT-03")


def test_pt_01_pt_02_asset_has_50_aligned_short_and_sentence_translations() -> None:
    """PT-01/PT-02: every Latin MVP item has validated Portuguese learner text."""

    source_pack = load_latin_mvp_source_pack()
    translation_pack = load_latin_portuguese_translation_pack(DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH)

    assert PHASE_26_REQUIREMENTS == ("PT-01", "PT-02", "PT-03")
    assert len(translation_pack.entries) == 50
    assert [entry.item_key for entry in translation_pack.entries] == [entry.item_key for entry in source_pack.entries]
    assert all(entry.short_translation_pt.strip() for entry in translation_pack.entries)
    assert all(entry.sentence_translation_pt.strip() for entry in translation_pack.entries)


def test_pt_03_deterministic_qa_summary_exposes_quality_and_review_status_counts() -> None:
    """PT-03: deterministic QA proves no leakage, Latin-copy, or dictionary-only failures."""

    source_pack = load_latin_mvp_source_pack()
    translation_pack = load_latin_portuguese_translation_pack(DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH)
    summary = LatinPortugueseTranslationQaService().validate_pack(translation_pack, source_pack).qa_summary()

    assert summary["entry_count"] == 50
    assert summary["passed_count"] == 50
    assert summary["failed_count"] == 0
    assert summary["issue_counts"] == {}
    assert summary["review_status_counts"] == {"needs_review": 0, "approved": 50, "rejected": 0}


def test_phase_26_cli_service_summary_is_public_and_scanner_readable() -> None:
    """PT-03: service/CLI expose only public Portuguese QA counts."""

    summary = LatinMvpGenerationService().start(
        include_portuguese_translation_summary=True,
        request=LatinGenerationRequest(),
    ).manifest_summary()

    portuguese_summary = summary["portuguese_translation_summary"]
    assert portuguese_summary["translation_pack_version"] == "latin-mvp-50-pt-v1"
    assert portuguese_summary["entry_count"] == 50
    assert portuguese_summary["failed_count"] == 0
    serialized = json.dumps(summary, ensure_ascii=False).casefold()
    assert "api key" not in serialized
    assert "provider error" not in serialized
    assert "not authenticated" not in serialized
    assert "c:\\" not in serialized
    assert "/users/" not in serialized

    assert create_app is not None


def test_phase_26_asset_contains_no_secrets_private_paths_or_provider_error_text() -> None:
    """PT-03: committed asset does not leak provider credentials or runtime diagnostics."""

    payload = DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH.read_text(encoding="utf-8")
    serialized = payload.casefold()

    assert "api_key" not in serialized
    assert "api key" not in serialized
    assert "provider error" not in serialized
    assert "translation failed" not in serialized
    assert "unauthorized" not in serialized
    assert "c:\\" not in serialized
    assert "/users/" not in serialized


def test_existing_modes_and_latin_loader_remain_importable() -> None:
    """Isolation: existing modes and Latin source loader remain available offline."""

    assert get_source_profile("frequency").source_type == "frequency"
    assert get_source_profile("word-list").source_type == "word-list"
    assert get_source_profile("kindle-highlights").source_type == "kindle-highlights"
    assert get_source_profile("latin-mvp").source_type == "latin-mvp"
    assert load_latin_mvp_source_pack().source_pack_version == "latin-mvp-50-v1"
    assert LatinMvpGenerationService is not None
    assert create_app is not None
