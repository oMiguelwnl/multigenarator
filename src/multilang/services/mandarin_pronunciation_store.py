"""Frozen contextual Mandarin readings shared by display and speech generation.

Loading verifies integrity and alignment, not a reviewer's linguistic expertise.
Spoken tone choices are explicit, separate from the lexical tones on the card.
"""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pypinyin.contrib.tone_convert import to_tone3

from multilang.services.mandarin_orthography import (
    MandarinOrthography,
    MandarinOrthographyError,
    render_mandarin_sentence,
    script_counts,
    validate_simplified_mandarin,
)
from multilang.services.mandarin_review import (
    MandarinPronunciationReview,
    ReviewedMandarinOrthographyService,
)
from multilang.services.vocabulary_review import _read_bytes


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Orthography(_Closed):
    word_pinyin: str = Field(min_length=1, max_length=4000)
    word_traditional: str = Field(min_length=1, max_length=4000)
    sentence_pinyin: str = Field(min_length=1, max_length=4000)
    sentence_traditional: str = Field(min_length=1, max_length=4000)


class _Context(_Closed):
    word: str = Field(min_length=1, max_length=512)
    sentence: str = Field(min_length=1, max_length=4000)
    orthography: _Orthography
    word_spoken_pinyin: str | None = Field(default=None, min_length=1, max_length=4000)
    sentence_spoken_pinyin: str | None = Field(default=None, min_length=1, max_length=4000)
    evidence_record_sha256: list[str] = Field(min_length=1, max_length=100)


class _Bundle(_Closed):
    schema_version: Literal["mandarin-pronunciation-1"]
    reviewer: str = Field(min_length=1, max_length=200)
    independent_human_review: Literal[False]
    contexts: list[_Context] = Field(min_length=1, max_length=2000)


def _syllables(text: str, pinyin: str) -> list[str]:
    html = render_mandarin_sentence(sentence=text, sentence_pinyin=pinyin)
    return re.findall(r"<rt>([^<]+)</rt>", html)


def _numbered(syllable: str) -> str:
    value = to_tone3(syllable.lower()).replace("ü", "v").replace("ve", "ue")
    if value[-1:] not in "12345":
        value += "5"
    if not re.fullmatch(r"[a-z]+[1-5]", value) or value == "r5":
        raise MandarinOrthographyError("unsupported spoken Pinyin notation")
    return value


def _key(word: str, sentence: str) -> tuple[str, str]:
    return validate_simplified_mandarin(word), validate_simplified_mandarin(sentence)


class MandarinPronunciationStore(ReviewedMandarinOrthographyService):
    def __init__(self, contexts: list[_Context]) -> None:
        reviews, spoken = [], {}
        for context in contexts:
            orthography = MandarinOrthography(**context.orthography.model_dump())
            review = MandarinPronunciationReview(word=context.word, sentence=context.sentence,
                orthography=orthography, evidence_record_sha256=tuple(context.evidence_record_sha256))
            reviews.append(review)
            readings = (context.word_spoken_pinyin, context.sentence_spoken_pinyin)
            if any(value is not None for value in readings):
                if any(value is None for value in readings):
                    raise MandarinOrthographyError("both spoken readings require review")
                for text, lexical, speech in (
                    (context.word, orthography.word_pinyin, readings[0]),
                    (context.sentence, orthography.sentence_pinyin, readings[1]),
                ):
                    lexical_bases = [_numbered(s)[:-1] for s in _syllables(text, lexical)]
                    spoken_bases = [_numbered(s)[:-1] for s in _syllables(text, speech)]
                    if lexical_bases != spoken_bases:
                        raise MandarinOrthographyError("spoken reading changes the reviewed segmental pronunciation")
                spoken[_key(context.word, context.sentence)] = readings
        super().__init__(reviews)
        self._spoken = spoken

    def spoken(self, *, word: str, sentence: str) -> tuple[str, str]:
        self.derive(word=word, sentence=sentence)
        result = self._spoken.get(_key(word, sentence))
        if result is None:
            raise MandarinOrthographyError("Mandarin audio requires reviewed spoken Pinyin")
        return result


def load_pronunciation_store(path: Path | None, expected_sha256: str | None) -> MandarinPronunciationStore:
    if path is None and expected_sha256 is None:
        return MandarinPronunciationStore([])
    if path is None or expected_sha256 is None:
        raise ValueError("Mandarin review path and checksum are both required")
    payload = json.loads(_read_bytes(path, expected_sha256, limit=8 * 1024**2))
    bundle = _Bundle.model_validate(payload)
    return MandarinPronunciationStore(bundle.contexts)


def mandarin_phoneme_body(text: str, spoken_pinyin: str) -> str:
    """Encode aligned, explicitly reviewed speech using Azure zh-CN SAPI.

    Punctuation and literal numbers stay outside phoneme spans. This function
    never infers sandhi or looks up a new pronunciation.
    """
    syllables = iter(_syllables(text, spoken_pinyin))
    output, characters, phones = [], [], []

    def flush():
        if characters:
            output.append(f'<phoneme alphabet="sapi" ph="{" - ".join(phones)}">'
                          f'{escape("".join(characters))}</phoneme>')
            characters.clear()
            phones.clear()

    for character in text:
        if script_counts(character).han:
            numbered = _numbered(next(syllables))
            characters.append(character)
            phones.append(numbered[:-1] + " " + numbered[-1])
        else:
            flush()
            output.append(escape(character))
    flush()
    return "".join(output)
