"""Versioned local lexical data for very frequent Polish function words."""

from __future__ import annotations

from multilang.services.lexical_lookup import LexicalRecord, normalize_lexical_key

POLISH_FUNCTION_WORDS_VERSION = "pl-function-words-v1"

_WORDS = {
    "w": ("preposition", "in; at; inside a place, time, or state", "/f/"),
    "i": ("conjunction", "and; connects words, phrases, or clauses", "/i/"),
    "nie": ("particle", "not; marks negation", "/ɲɛ/"),
    "do": ("preposition", "to; toward a place, person, purpose, or limit", "/dɔ/"),
    "to": ("pronoun", "this; that; it; also used as a linking word", "/tɔ/"),
    "jak": ("adverb", "how; as; like; in what way", "/jak/"),
    "co": ("pronoun", "what; that which", "/t͡sɔ/"),
    "czy": ("particle", "whether; introduces yes-or-no questions", "/t͡ʂɨ/"),
}


def lookup_polish_function_word(term: str) -> LexicalRecord | None:
    row = _WORDS.get(normalize_lexical_key(term))
    if row is None:
        return None
    pos, definition, ipa = row
    key = normalize_lexical_key(term)
    return LexicalRecord(
        term=key,
        display_form=key,
        lemma=key,
        definitions=[definition],
        part_of_speech=pos,
        ipa=ipa,
        source=POLISH_FUNCTION_WORDS_VERSION,
    )


__all__ = ["POLISH_FUNCTION_WORDS_VERSION", "lookup_polish_function_word"]
