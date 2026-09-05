"""Deterministic vocabulary candidate extraction from normalized highlights."""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256
import re
from typing import Protocol
import unicodedata

from multilang.domain.highlights import (
    HighlightCandidate,
    HighlightCandidateExtractionResult,
    HighlightExtractionError,
    NormalizedHighlight,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import KoreanLexicalIdentity
from multilang.services.word_list_parser import split_dense_word_list_line


_TOKEN_RE = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.UNICODE)
_QUOTED_PHRASE_RE = re.compile(
    r'"(?P<double>[^"]+)"|“(?P<curly_double>[^”]+)”|\'(?P<single>[^\']+)\'|‘(?P<curly_single>[^’]+)’'
)
_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
_WEB_NOISE = {"http", "https", "www", "nbsp", "com", "org", "net", "example", "test"}
_STOPWORDS: dict[SupportedLanguage, set[str]] = {
    SupportedLanguage.PT: {"a", "ao", "as", "de", "do", "da", "e", "em", "o", "os", "um", "uma", "pela"},
    SupportedLanguage.ES: {"a", "de", "del", "el", "en", "la", "las", "los", "un", "una", "y", "otro"},
    SupportedLanguage.EN: {"a", "an", "and", "in", "of", "the", "to"},
    SupportedLanguage.FR: {"au", "de", "des", "du", "et", "la", "le", "les", "un", "une"},
    SupportedLanguage.DE: {"das", "der", "die", "ein", "eine", "und"},
    SupportedLanguage.EL: {"από", "για", "δεν", "είναι", "η", "και", "με", "να", "ο", "σε", "το", "του"},
    SupportedLanguage.IT: {"a", "di", "e", "il", "la", "le", "lo", "un", "una"},
    SupportedLanguage.PL: {"a", "i", "ma", "na", "o", "ten", "ta", "to", "w", "z"},
    SupportedLanguage.TR: {"bu", "bir", "ve"},
    SupportedLanguage.RO: {"acest", "aceasta", "cu", "de", "în", "la", "o", "și", "un", "una"},
    SupportedLanguage.RU: {"а", "в", "и", "на", "не", "с", "то", "этот", "это"},
    SupportedLanguage.NL: {"de", "een", "en", "het", "in", "van"},
    SupportedLanguage.DA: {"at", "de", "den", "det", "en", "er", "et", "i", "og", "på"},
    SupportedLanguage.NB: {"av", "de", "den", "det", "en", "er", "et", "i", "og", "på"},
    SupportedLanguage.SV: {"att", "av", "det", "en", "ett", "för", "i", "med", "och", "på", "som", "är"},
    SupportedLanguage.FI: {"ei", "että", "ja", "joka", "kun", "minä", "on", "se", "tämä", "yksi"},
    SupportedLanguage.HU: {"a", "az", "egy", "és", "hogy", "is", "meg", "mert", "nem", "van"},
    SupportedLanguage.CS: {"a", "ale", "do", "je", "jsem", "na", "ne", "pro", "se", "ta", "ten", "to", "v", "ve", "že"},
    SupportedLanguage.HR: {"da", "do", "i", "je", "na", "ne", "od", "on", "ona", "se", "to", "u", "za"},
    SupportedLanguage.JA: {"の", "に", "は", "が", "を", "で", "と", "も", "から", "です"},
}


class KoreanHighlightResolver(Protocol):
    def resolve_korean_highlight_text(self, text: str) -> Sequence[object]: ...


def extract_highlight_candidates(
    highlights: Sequence[NormalizedHighlight],
    *,
    language: SupportedLanguage,
    korean_resolver: KoreanHighlightResolver | None = None,
) -> HighlightCandidateExtractionResult:
    """Return first-seen ordered candidate forms with duplicate/noise counters."""

    if language is SupportedLanguage.KO:
        return _extract_korean_highlight_candidates(
            highlights,
            resolver=korean_resolver,
        )

    candidates_by_key: dict[tuple[str, str], HighlightCandidate] = {}
    duplicate_count = 0
    rejected_token_count = 0
    stopwords = _STOPWORDS[language]

    for highlight in sorted(highlights, key=lambda item: item.provenance.source_index):
        text_without_urls, removed_urls = _URL_RE.subn(" ", highlight.text)
        rejected_token_count += removed_urls
        for raw_token in _raw_token_like_parts(highlight.text):
            if _URL_RE.match(raw_token) or any(character.isdigit() for character in raw_token):
                rejected_token_count += 1

        dense_entries = split_dense_word_list_line(text_without_urls)
        if dense_entries:
            for entry in dense_entries:
                display_form = _normalize_phrase_display(entry)
                lemma_key = _lemma_key(display_form)
                if not _is_usable_entry(display_form, lemma_key=lemma_key, stopwords=stopwords):
                    rejected_token_count += 1
                    continue
                duplicate_count += _record_candidate(
                    candidates_by_key,
                    language=language,
                    highlight=highlight,
                    display_form=display_form,
                    lemma_key=lemma_key,
                )
            continue

        consumed_spans: list[tuple[int, int]] = []
        for match in _QUOTED_PHRASE_RE.finditer(text_without_urls):
            phrase = next(group for group in match.groups() if group is not None)
            display_form = _normalize_phrase_display(phrase)
            lemma_key = _lemma_key(display_form)
            if not _is_usable_phrase(display_form, lemma_key=lemma_key, stopwords=stopwords):
                continue
            duplicate_count += _record_candidate(
                candidates_by_key,
                language=language,
                highlight=highlight,
                display_form=display_form,
                lemma_key=lemma_key,
            )
            consumed_spans.append(match.span())

        text_for_tokens = _blank_spans(text_without_urls, consumed_spans)

        for match in _TOKEN_RE.finditer(text_for_tokens):
            display_form = _trim_internal_token(match.group(0))
            lemma_key = _lemma_key(display_form)
            if not _is_usable_token(display_form, lemma_key=lemma_key, stopwords=stopwords):
                rejected_token_count += 1
                continue

            duplicate_count += _record_candidate(
                candidates_by_key,
                language=language,
                highlight=highlight,
                display_form=display_form,
                lemma_key=lemma_key,
            )

    return HighlightCandidateExtractionResult(
        candidates=sorted(
            candidates_by_key.values(),
            key=lambda candidate: (
                candidate.first_source_index,
                candidate.lemma_key,
                candidate.item_key,
            ),
        ),
        duplicate_count=duplicate_count,
        rejected_token_count=rejected_token_count,
    )


def _extract_korean_highlight_candidates(
    highlights: Sequence[NormalizedHighlight],
    *,
    resolver: KoreanHighlightResolver | None,
) -> HighlightCandidateExtractionResult:
    candidates_by_key: dict[tuple[str, str], HighlightCandidate] = {}
    duplicate_count = 0
    rejected_token_count = 0
    errors: list[HighlightExtractionError] = []

    for highlight in sorted(highlights, key=lambda item: item.provenance.source_index):
        if resolver is None:
            errors.append(
                HighlightExtractionError(
                    source_index=highlight.provenance.source_index,
                    reason_code="korean_resolver_required",
                )
            )
            rejected_token_count += 1
            continue
        analysis_text = unicodedata.normalize("NFC", highlight.text)
        try:
            raw_lexemes = tuple(resolver.resolve_korean_highlight_text(analysis_text))
        except Exception:
            errors.append(
                HighlightExtractionError(
                    source_index=highlight.provenance.source_index,
                    reason_code="korean_resolution_unavailable",
                )
            )
            rejected_token_count += 1
            continue
        if not raw_lexemes:
            errors.append(
                HighlightExtractionError(
                    source_index=highlight.provenance.source_index,
                    reason_code="korean_resolution_failed",
                )
            )
            rejected_token_count += 1
            continue

        resolved_lexemes: list[tuple[int, KoreanLexicalIdentity]] = []
        malformed = False
        for lexeme in raw_lexemes:
            identity = getattr(lexeme, "identity", None)
            word_position = getattr(lexeme, "word_position", None)
            if (
                not isinstance(identity, KoreanLexicalIdentity)
                or isinstance(word_position, bool)
                or not isinstance(word_position, int)
                or word_position < 0
            ):
                malformed = True
                break
            resolved_lexemes.append((word_position, identity))
        if malformed:
            errors.append(
                HighlightExtractionError(
                    source_index=highlight.provenance.source_index,
                    reason_code="korean_resolution_unavailable",
                )
            )
            rejected_token_count += 1
            continue

        for _word_position, identity in sorted(
            resolved_lexemes,
            key=lambda item: item[0],
        ):
            duplicate_count += _record_korean_candidate(
                candidates_by_key,
                highlight=highlight,
                identity=identity,
            )

    return HighlightCandidateExtractionResult(
        candidates=list(candidates_by_key.values()),
        duplicate_count=duplicate_count,
        rejected_token_count=rejected_token_count,
        errors=errors,
    )


def _record_korean_candidate(
    candidates_by_key: dict[tuple[str, str], HighlightCandidate],
    *,
    highlight: NormalizedHighlight,
    identity: KoreanLexicalIdentity,
) -> int:
    identity_key = identity.lexical_key
    candidate_key = (highlight.provenance.content_hash, identity_key)
    existing = candidates_by_key.get(candidate_key)
    if existing is not None:
        candidates_by_key[candidate_key] = existing.model_copy(
            update={"occurrence_count": existing.occurrence_count + 1}
        )
        return 1

    identity_hash = sha256(identity_key.encode("utf-8")).hexdigest()[:16]
    source_hash = highlight.provenance.content_hash[:16]
    candidates_by_key[candidate_key] = HighlightCandidate(
        item_key=f"highlight-ko-{source_hash}-{identity_hash}",
        source_content_hash=highlight.provenance.content_hash,
        display_form=identity.lemma,
        lemma_key=identity_key,
        first_highlight_id=highlight.highlight_id,
        first_source_index=highlight.provenance.source_index,
        occurrence_count=1,
        korean_identity=identity,
    )
    return 0


def _raw_token_like_parts(text: str) -> list[str]:
    return [part for part in re.split(r"\s+", text) if part]


def _trim_internal_token(token: str) -> str:
    return token.strip("'’-—-")


def _normalize_phrase_display(phrase: str) -> str:
    return " ".join(phrase.split()).strip("'’—- ")


def _lemma_key(token: str) -> str:
    normalized = unicodedata.normalize("NFKC", token)
    return " ".join(normalized.casefold().split())


def _is_usable_token(token: str, *, lemma_key: str, stopwords: set[str]) -> bool:
    if len(lemma_key) <= 1:
        return False
    if lemma_key in stopwords or lemma_key in _WEB_NOISE:
        return False
    if any(character.isdigit() for character in token):
        return False
    if not any(character.isalpha() for character in token):
        return False
    for index, character in enumerate(token):
        if character.isalpha():
            continue
        if character in {"'", "’", "-"} and 0 < index < len(token) - 1:
            if token[index - 1].isalpha() and token[index + 1].isalpha():
                continue
        return False
    return True


def _is_usable_phrase(phrase: str, *, lemma_key: str, stopwords: set[str]) -> bool:
    parts = lemma_key.split()
    if len(parts) < 2:
        return False
    if any(part in stopwords or part in _WEB_NOISE for part in parts):
        # Function-word-containing phrases are still useful if at least two
        # lexical words remain, e.g. "Robe de soie".
        lexical_parts = [part for part in parts if part not in stopwords and part not in _WEB_NOISE]
        if len(lexical_parts) < 2:
            return False
    return all(
        _is_usable_token(part, lemma_key=_lemma_key(part), stopwords=set())
        for part in phrase.split()
    )


def _is_usable_entry(entry: str, *, lemma_key: str, stopwords: set[str]) -> bool:
    if " " in lemma_key:
        return _is_usable_phrase(entry, lemma_key=lemma_key, stopwords=stopwords)
    return _is_usable_token(entry, lemma_key=lemma_key, stopwords=stopwords)


def _blank_spans(text: str, spans: Sequence[tuple[int, int]]) -> str:
    if not spans:
        return text
    characters = list(text)
    for start, end in spans:
        for index in range(start, end):
            characters[index] = " "
    return "".join(characters)


def _record_candidate(
    candidates_by_key: dict[tuple[str, str], HighlightCandidate],
    *,
    language: SupportedLanguage,
    highlight: NormalizedHighlight,
    display_form: str,
    lemma_key: str,
) -> int:
    candidate_key = (highlight.provenance.content_hash, lemma_key)
    if candidate_key in candidates_by_key:
        existing = candidates_by_key[candidate_key]
        candidates_by_key[candidate_key] = existing.model_copy(
            update={"occurrence_count": existing.occurrence_count + 1}
        )
        return 1

    lemma_hash = sha256(lemma_key.encode("utf-8")).hexdigest()[:16]
    source_hash = highlight.provenance.content_hash[:16]
    candidates_by_key[candidate_key] = HighlightCandidate(
        item_key=f"highlight-{language.value}-{source_hash}-{lemma_hash}",
        source_content_hash=highlight.provenance.content_hash,
        display_form=display_form,
        lemma_key=lemma_key,
        first_highlight_id=highlight.highlight_id,
        first_source_index=highlight.provenance.source_index,
        occurrence_count=1,
    )
    return 0


__all__ = ["KoreanHighlightResolver", "extract_highlight_candidates"]
