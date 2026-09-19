"""Conservative native Kiwi categories, without inferred lexical identities."""

from __future__ import annotations

import unicodedata

_UPOS = {
    "NNG": "NOUN",
    "NNP": "PROPN",
    "NNB": "NOUN",
    "NR": "NUM",
    "NP": "PRON",
    "VV": "VERB",
    "VA": "ADJ",
    "VX": "AUX",
    "VCP": "AUX",
    "VCN": "ADJ",
    "MM": "DET",
    "MAG": "ADV",
    "MAJ": "CCONJ",
    "IC": "INTJ",
    "SN": "NUM",
    "JKS": "ADP",
    "JKC": "ADP",
    "JKG": "ADP",
    "JKO": "ADP",
    "JKB": "ADP",
    "JKV": "ADP",
    "JKQ": "ADP",
    "JX": "ADP",
    "JC": "CCONJ",
}
_EXPLICIT_PUNCTUATION = frozenset({"SF", "SP", "SS", "SSO", "SSC", "SE", "SO"})


def kiwi_to_upos(pos: str) -> str:
    """Map a validated base tag; callers must preserve compound/OOV boundaries.

    The numeric and postposition categories apply to single native morphemes,
    never to an inferred head of a compound. JK/JX and JC follow Table 2 of:
    https://universaldependencies.org/udw20/papers/2020.udw2020-1.12.pdf
    SN is Kiwi's numeric category; SL/SH identify scripts, not lexical POS:
    https://github.com/bab2min/Kiwi/blob/main/README.md#품사-태그

    This retains existing coarse lexical mappings and is not a full contextual
    UD conversion. Unknown tags, roots, derivation and endings stay unresolved.
    """
    return _UPOS.get(pos, "X")


def is_kiwi_punctuation(pos: str, surface: str) -> bool:
    """Respect native punctuation roles and reject arbitrary special characters.

    Kiwi explicitly includes angle brackets in SS/SSO/SSC and tilde in SO,
    although Unicode classifies those characters as symbols. Generic SW also
    contains foreign-script material, so only Unicode punctuation is safe there.
    The caller must additionally prove vendor source offsets and surface form.
    """
    if not surface:
        return False
    if pos in _EXPLICIT_PUNCTUATION:
        return all(unicodedata.category(character).startswith(("P", "S")) for character in surface)
    if pos == "SW":
        return all(unicodedata.category(character).startswith("P") for character in surface)
    return False
