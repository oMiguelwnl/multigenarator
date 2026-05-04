"""Tests for explicit source-profile contracts."""

from __future__ import annotations

import pytest

from multilang.domain.source_profiles import (
    SOURCE_PROFILES,
    SUPPORTED_SOURCE_TYPES,
    get_source_profile,
)


def test_frequency_source_profile_exports_translation_with_normal_template() -> None:
    profile = get_source_profile("frequency")

    assert profile.source_type == "frequency"
    assert profile.requires_translation_validation is True
    assert profile.exports_translation_field is True
    assert profile.min_sentence_tokens == 4
    assert profile.max_sentence_tokens == 12
    assert profile.note_type_name == "Multilang::Card"
    assert profile.template_name == "normal_card"


def test_word_list_source_profile_exports_translation_with_manual_note_type() -> None:
    profile = get_source_profile("word-list")

    assert profile.source_type == "word-list"
    assert profile.requires_translation_validation is True
    assert profile.exports_translation_field is True
    assert profile.min_sentence_tokens == 4
    assert profile.max_sentence_tokens == 12
    assert profile.note_type_name == "Multilang::Manual Card"
    assert profile.template_name == "normal_card"


def test_kindle_highlights_source_profile_omits_translation_with_highlight_template() -> None:
    profile = get_source_profile("kindle-highlights")

    assert profile.source_type == "kindle-highlights"
    assert profile.requires_translation_validation is False
    assert profile.exports_translation_field is False
    assert profile.min_sentence_tokens == 6
    assert profile.max_sentence_tokens == 16
    assert profile.note_type_name == "Multilang::Highlight Card"
    assert profile.template_name == "highlight_card"


def test_unknown_source_profile_error_omits_private_input() -> None:
    unknown = "missing-source /home/user/.multilang/highlights/raw/private.html secret text"

    with pytest.raises(ValueError) as exc_info:
        get_source_profile(unknown)

    message = str(exc_info.value)
    assert "unsupported source_type" in message
    assert "frequency" in message
    assert "word-list" in message
    assert "kindle-highlights" in message
    assert "missing-source" not in message
    assert "/home/user" not in message
    assert ".multilang" not in message
    assert "private.html" not in message
    assert "secret" not in message
    assert "text" not in message


def test_supported_source_types_match_profile_keys() -> None:
    assert SUPPORTED_SOURCE_TYPES == tuple(SOURCE_PROFILES.keys())
