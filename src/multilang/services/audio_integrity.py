"""Strict integrity checks for reusable word-audio assets."""

from __future__ import annotations

from hashlib import sha256

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord


class AudioIntegrityError(ValueError):
    """Raised when stored word audio does not match the exported card Word."""


def _tts_text_hash(tts_text: str) -> str:
    return sha256(tts_text.encode("utf-8")).hexdigest()


def _item_label(asset: AudioAssetRecord, item_key: str | None) -> str:
    return item_key or asset.item_key


def _raise_mismatch(*, asset: AudioAssetRecord, expected_word: str, field_name: str, actual: object, item_key: str | None) -> None:
    label = _item_label(asset, item_key)
    raise AudioIntegrityError(
        "word_audio does not match exported card Word "
        f"for item_key={label}: field {field_name} expected Word={expected_word!r} got {actual!r}"
    )


def assert_word_audio_matches_word(asset: AudioAssetRecord, expected_word: str, item_key: str | None = None) -> None:
    """Assert a word-audio asset's manifest metadata exactly matches ``expected_word``.

    Only surrounding whitespace on the caller-provided card Word is ignored. Stored
    display text, normalized display text, synthesis text, and provenance hash are
    otherwise compared exactly so stale reusable audio cannot pass through export.
    """

    expected = expected_word.strip()
    if not expected:
        _raise_mismatch(asset=asset, expected_word=expected, field_name="Word", actual=expected_word, item_key=item_key)

    if asset.asset_kind is not AudioAssetKind.WORD:
        _raise_mismatch(asset=asset, expected_word=expected, field_name="asset_kind", actual=asset.asset_kind.value, item_key=item_key)

    if asset.display_text != expected:
        _raise_mismatch(asset=asset, expected_word=expected, field_name="display_text", actual=asset.display_text, item_key=item_key)

    if asset.normalized_input.display_text != expected:
        _raise_mismatch(
            asset=asset,
            expected_word=expected,
            field_name="normalized_input.display_text",
            actual=asset.normalized_input.display_text,
            item_key=item_key,
        )

    if asset.normalized_input.tts_text != expected:
        _raise_mismatch(
            asset=asset,
            expected_word=expected,
            field_name="normalized_input.tts_text",
            actual=asset.normalized_input.tts_text,
            item_key=item_key,
        )

    expected_hash = _tts_text_hash(asset.normalized_input.tts_text)
    if asset.provenance.text_hash != expected_hash:
        _raise_mismatch(
            asset=asset,
            expected_word=expected,
            field_name="provenance.text_hash",
            actual=asset.provenance.text_hash,
            item_key=item_key,
        )


def word_audio_matches_word(asset: AudioAssetRecord, expected_word: str) -> bool:
    """Return whether ``asset`` can safely be used as word audio for ``expected_word``."""

    try:
        assert_word_audio_matches_word(asset, expected_word)
    except AudioIntegrityError:
        return False
    return True


__all__ = ["AudioIntegrityError", "assert_word_audio_matches_word", "word_audio_matches_word"]
