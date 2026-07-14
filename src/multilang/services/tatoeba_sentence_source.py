"""Deterministic Tatoeba fallback sentence filtering and selection."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Protocol

from pydantic import BaseModel, Field

from multilang.services.text_generation import SentenceGenerationResult

_TOKEN_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_META_PREFIXES = (
    "example",
    "for example",
    "the word",
    "a palavra",
    "la palabra",
    "le mot",
    "das wort",
    "het woord",
    "слово",
)
_REFLEXIVE_MARKERS = (
    " me ",
    " te ",
    " se ",
    " nos ",
    " os ",
    " myself ",
    " yourself ",
    " himself ",
    " herself ",
    " ourselves ",
    " yourselves ",
    " themselves ",
    " mich ",
    " dich ",
    " sich ",
    " ons ",
    " zich ",
)
_REFLEXIVE_SUFFIXES = ("se", "ся", "сь")
_TATOEBA_API_CODES = {
    "cs": "ces",
    "de": "deu",
    "en": "eng",
    "es": "spa",
    "fi": "fin",
    "fr": "fra",
    "it": "ita",
    "nb": "nob",
    "nl": "nld",
    "pl": "pol",
    "pt": "por",
    "ro": "ron",
    "ru": "rus",
    "sv": "swe",
    "tr": "tur",
}


class TatoebaCandidateProvider(Protocol):
    def search_candidates(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        translation_target_language: str,
    ) -> list["TatoebaCandidateRow"]: ...


class TatoebaCandidateRow(BaseModel):
    sentence_id: int
    sentence_text: str = Field(min_length=1)
    target_language: str = Field(min_length=2)
    translation_language: str = Field(min_length=2)
    linked_translations: list[str] = Field(default_factory=list)
    base: int = 0
    is_direct_translation: bool = True


class StaticTatoebaCandidateProvider:
    """Deterministic in-memory provider for tests and disabled runtime paths."""

    def __init__(self, rows: list[TatoebaCandidateRow] | None = None) -> None:
        self._rows = list(rows or [])

    def search_candidates(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        translation_target_language: str,
    ) -> list[TatoebaCandidateRow]:
        return list(self._rows)


class TatoebaApiCandidateProvider:
    """Fetch candidate rows from the public Tatoeba search API."""

    def __init__(
        self,
        *,
        base_url: str = "https://tatoeba.org/en/api_v0/search",
        timeout_seconds: int = 10,
        page_limit: int = 3,
    ) -> None:
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._page_limit = page_limit

    def search_candidates(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        translation_target_language: str,
    ) -> list[TatoebaCandidateRow]:
        target_api = _TATOEBA_API_CODES[target_language]
        translation_api = _TATOEBA_API_CODES[translation_target_language]
        rows_by_id: dict[int, TatoebaCandidateRow] = {}

        for query in _query_terms(display_form=display_form, lemma=lemma):
            for page in range(1, self._page_limit + 1):
                payload = self._fetch_page(
                    query=query,
                    target_language=target_api,
                    translation_language=translation_api,
                    page=page,
                )
                for result in payload.get("results", []):
                    row = _result_to_row(
                        result,
                        target_language=target_language,
                        translation_target_language=translation_target_language,
                    )
                    if row is None:
                        continue
                    existing = rows_by_id.get(row.sentence_id)
                    if existing is None or _row_priority(row) > _row_priority(existing):
                        rows_by_id[row.sentence_id] = row

        return list(rows_by_id.values())

    def _fetch_page(
        self,
        *,
        query: str,
        target_language: str,
        translation_language: str,
        page: int,
    ) -> dict:
        params = urllib.parse.urlencode(
            {
                "from": target_language,
                "query": query,
                "sort": "relevance",
                "to": translation_language,
                "trans_filter": "limit",
                "trans_to": translation_language,
                "page": page,
            }
        )
        request = urllib.request.Request(f"{self._base_url}?{params}")
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            return json.load(response)


class TatoebaSentenceSource:
    """Return one deterministic fallback sentence or no sentence."""

    min_sentence_tokens = 4

    def __init__(self, *, candidate_provider: TatoebaCandidateProvider) -> None:
        self._candidate_provider = candidate_provider

    def select_sentence(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        translation_target_language: str,
    ) -> SentenceGenerationResult | None:
        try:
            candidates = self._candidate_provider.search_candidates(
                display_form=display_form,
                lemma=lemma,
                target_language=target_language,
                translation_target_language=translation_target_language,
            )
        except Exception:
            return None

        eligible: list[tuple[tuple[int, ...], TatoebaCandidateRow]] = []

        for candidate in candidates:
            if candidate.target_language != target_language:
                continue
            if candidate.translation_language != translation_target_language:
                continue
            if not [text.strip() for text in candidate.linked_translations if text.strip()]:
                continue
            if self._fails_hard_filters(candidate.sentence_text):
                continue
            if not self._matches_target(candidate.sentence_text, display_form=display_form, lemma=lemma):
                continue

            eligible.append(
                (
                    self._score_candidate(candidate.sentence_text, display_form=display_form, lemma=lemma, candidate=candidate),
                    candidate,
                )
            )

        if not eligible:
            return None

        _, selected = sorted(
            eligible,
            key=lambda entry: (entry[0], entry[1].sentence_id),
            reverse=True,
        )[0]
        sentence_text = selected.sentence_text.strip()
        return SentenceGenerationResult(
            sentence=sentence_text,
            provenance={
                "source": "tatoeba",
                "sentence_id": selected.sentence_id,
                "base": selected.base,
                "is_direct_translation": selected.is_direct_translation,
            },
        )

    def _fails_hard_filters(self, sentence: str) -> bool:
        stripped = sentence.strip()
        token_count = len(_tokenize(stripped))
        lowered = f" {_normalize(stripped)} "
        return (
            token_count < self.min_sentence_tokens
            or "?" in stripped
            or stripped.endswith("!")
            or any(lowered.strip().startswith(prefix) for prefix in _META_PREFIXES)
        )

    def _matches_target(self, sentence: str, *, display_form: str, lemma: str) -> bool:
        keys = _match_keys(display_form) | _match_keys(lemma)
        sentence_terms = {key for token in _tokenize(sentence) for key in _match_keys(token)}
        return not keys.isdisjoint(sentence_terms)

    def _score_candidate(
        self,
        sentence: str,
        *,
        display_form: str,
        lemma: str,
        candidate: TatoebaCandidateRow,
    ) -> tuple[int, ...]:
        normalized = _normalize(sentence)
        token_count = len(_tokenize(sentence))
        target_first = _target_is_first_token(sentence, display_form=display_form, lemma=lemma)
        reflexive_display = _is_reflexive_form(display_form)
        reflexive_sentence = _contains_reflexive_marker(normalized)

        return (
            1 if candidate.base == 0 else 0,
            1 if self._matches_target(sentence, display_form=display_form, lemma=display_form) else 0,
            1 if candidate.is_direct_translation else 0,
            1 if reflexive_display and reflexive_sentence else 0,
            1 if 5 <= token_count <= 9 else 0,
            1 if sentence.strip().endswith(".") else 0,
            0 if target_first and token_count <= 5 else 1,
            -abs(7 - token_count),
            -candidate.sentence_id,
        )


def _tokenize(value: str) -> list[str]:
    return _TOKEN_RE.findall(value.casefold())


def _normalize(value: str) -> str:
    return " ".join(_tokenize(value))


def _match_keys(value: str) -> set[str]:
    normalized = _normalize(value)
    if not normalized:
        return set()

    keys = {normalized}
    for token in normalized.split():
        keys.add(token)
        if token.endswith(_REFLEXIVE_SUFFIXES) and len(token) > 4:
            keys.add(token[:-2])
        for suffix in ("ing", "ed", "es", "s", "ar", "er", "ir", "ando", "iendo", "ado", "ido", "o", "a"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                keys.add(token[: -len(suffix)])
    return keys


def _is_reflexive_form(value: str) -> bool:
    normalized = _normalize(value)
    tokens = normalized.split()
    return any(token in {"se", "me", "nos", "te"} for token in tokens) or any(
        normalized.endswith(suffix) for suffix in _REFLEXIVE_SUFFIXES
    )


def _contains_reflexive_marker(normalized_sentence: str) -> bool:
    padded = f" {normalized_sentence} "
    return any(marker in padded for marker in _REFLEXIVE_MARKERS)


def _target_is_first_token(sentence: str, *, display_form: str, lemma: str) -> bool:
    tokens = _tokenize(sentence)
    if not tokens:
        return False
    first = tokens[0]
    targets = _match_keys(display_form) | _match_keys(lemma)
    return first in targets


def _query_terms(*, display_form: str, lemma: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for value in (display_form.strip(), lemma.strip()):
        normalized = value.casefold()
        if value and normalized not in seen:
            seen.add(normalized)
            terms.append(value)
    return terms


def _flatten_translations(result: dict) -> list[dict]:
    translations: list[dict] = []
    for bucket in result.get("translations", []):
        translations.extend(bucket)
    return translations


def _result_to_row(
    result: dict,
    *,
    target_language: str,
    translation_target_language: str,
) -> TatoebaCandidateRow | None:
    translations = [
        item
        for item in _flatten_translations(result)
        if item.get("lang") == _TATOEBA_API_CODES[translation_target_language]
    ]
    linked_texts = [item.get("text", "").strip() for item in translations if item.get("text", "").strip()]
    if not linked_texts:
        return None

    return TatoebaCandidateRow(
        sentence_id=int(result["id"]),
        sentence_text=str(result["text"]),
        target_language=target_language,
        translation_language=translation_target_language,
        linked_translations=linked_texts,
        base=int(result.get("base", 0) or 0),
        is_direct_translation=any(bool(item.get("isDirect")) for item in translations),
    )


def _row_priority(row: TatoebaCandidateRow) -> tuple[int, int, int]:
    return (1 if row.is_direct_translation else 0, 1 if row.base == 0 else 0, len(row.linked_translations))


__all__ = [
    "StaticTatoebaCandidateProvider",
    "TatoebaApiCandidateProvider",
    "TatoebaCandidateRow",
    "TatoebaSentenceSource",
]
