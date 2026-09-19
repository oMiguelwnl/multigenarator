"""Bind audio manifests to the displayed text and normalized synthesis request."""

from __future__ import annotations

import re
import unicodedata
from hashlib import sha256
from xml.etree import ElementTree

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord

_WHITESPACE_RE = re.compile(r"\s+")
_SSML_NAMESPACE = "http://www.w3.org/2001/10/synthesis"
_SSML_ATTRIBUTES = {
    "speak": {"version", "{http://www.w3.org/XML/1998/namespace}lang"},
    "voice": {"name"},
    "prosody": {"rate", "pitch", "volume", "duration"},
    "phoneme": {"alphabet", "ph"},
    "break": {"time", "strength"},
    "sub": {"alias"},
    "p": set(),
    "s": set(),
}


class AudioIntegrityError(ValueError):
    """Raised when stored audio does not match the exported card text."""


def normalize_tts_text(display_text: str) -> str:
    """Normalize synthesis typography without changing display text, case or accents."""

    return _WHITESPACE_RE.sub(" ", unicodedata.normalize("NFC", display_text).replace("’", "'").strip())


def _tts_text_hash(tts_text: str) -> str:
    return sha256(tts_text.encode("utf-8")).hexdigest()


def _ssml_spoken_text(payload: str) -> str:
    """Read only bounded, inert synthesis markup; never load XML resources.

    Plain text remains valid for the existing non-SSML provider contracts.
    Pronunciation markup keeps its written word. Substitution aliases must
    agree with that word so adapters that flatten markup cannot speak different
    content from adapters that preserve it.
    """

    if len(payload) > 16000 or "<!" in payload or "<?" in payload:
        raise ValueError("ssml declarations or size limit")
    if "<" not in payload:
        return normalize_tts_text(payload)
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError("ssml must be well formed") from exc
    elements = list(root.iter())
    if len(elements) > 256 or root.tag.rsplit("}", 1)[-1] != "speak":
        raise ValueError("ssml structure limit or root mismatch")
    for element in elements:
        name = element.tag.rsplit("}", 1)[-1]
        if (
            name not in _SSML_ATTRIBUTES
            or set(element.attrib) - _SSML_ATTRIBUTES[name]
            or (name == "speak" and element is not root)
            or (element.tag.startswith("{") and not element.tag.startswith(f"{{{_SSML_NAMESPACE}}}"))
        ):
            raise ValueError("ssml contains unsupported markup")
        if name == "break" and (len(element) or (element.text or "").strip()):
            raise ValueError("ssml break must not contain spoken text")
        if name == "sub" and (
            len(element)
            or normalize_tts_text(element.get("alias", "")) != normalize_tts_text(element.text or "")
        ):
            raise ValueError("ssml substitution changes spoken text")
    return normalize_tts_text("".join(root.itertext()))


def _assert_audio_matches_text(
    asset: AudioAssetRecord,
    expected_text: str,
    *,
    asset_kind: AudioAssetKind,
    field_label: str,
    item_key: str | None,
) -> None:
    expected = expected_text.strip()

    def check(field_name: str, actual: object, required: object) -> None:
        if actual != required:
            raise AudioIntegrityError(
                f"{asset_kind.value}_audio does not match exported card {field_label} "
                f"for item_key={item_key or asset.item_key}: field {field_name} "
                f"expected {field_label}={required!r} got {actual!r}"
            )

    if not expected:
        check(field_label, expected_text, "nonempty text")
    check("asset_kind", asset.asset_kind, asset_kind)
    check("display_text", asset.display_text, expected)
    check("normalized_input.display_text", asset.normalized_input.display_text, expected)
    synthesis_text = normalize_tts_text(expected)
    check("normalized_input.tts_text", asset.normalized_input.tts_text, synthesis_text)
    expected_hash = _tts_text_hash(synthesis_text)
    check("normalized_input.text_hash", asset.normalized_input.text_hash, expected_hash)
    check("provenance.text_hash", asset.provenance.text_hash, expected_hash)
    expected_ssml_hash = _tts_text_hash(asset.normalized_input.ssml_text or synthesis_text)
    check("normalized_input.ssml_hash", asset.normalized_input.ssml_hash, expected_ssml_hash)
    check("provenance.ssml_hash", asset.provenance.ssml_hash, expected_ssml_hash)
    try:
        spoken_text = _ssml_spoken_text(asset.normalized_input.ssml_text or synthesis_text)
    except ValueError as exc:
        raise AudioIntegrityError(
            f"{asset_kind.value}_audio has unsupported ssml spoken content "
            f"for item_key={item_key or asset.item_key}"
        ) from exc
    check("normalized_input.ssml_text.spoken_text", spoken_text, synthesis_text)


def assert_word_audio_matches_word(asset: AudioAssetRecord, expected_word: str, item_key: str | None = None) -> None:
    """Check exact displayed Word and its normalized synthesis text and hashes."""

    _assert_audio_matches_text(
        asset, expected_word, asset_kind=AudioAssetKind.WORD, field_label="Word", item_key=item_key,
    )


def assert_sentence_audio_matches_sentence(asset: AudioAssetRecord, expected_sentence: str, item_key: str | None = None) -> None:
    """Check exact displayed ExampleSentence and its normalized synthesis request."""

    _assert_audio_matches_text(
        asset, expected_sentence, asset_kind=AudioAssetKind.SENTENCE,
        field_label="ExampleSentence", item_key=item_key,
    )


def word_audio_matches_word(asset: AudioAssetRecord, expected_word: str) -> bool:
    """Return whether the word audio manifest matches the expected Word."""

    try:
        assert_word_audio_matches_word(asset, expected_word)
    except AudioIntegrityError:
        return False
    return True


__all__ = [
    "AudioIntegrityError", "assert_word_audio_matches_word", "word_audio_matches_word",
    "assert_sentence_audio_matches_sentence", "normalize_tts_text",
]
