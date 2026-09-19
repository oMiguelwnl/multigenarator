"""Conservative UniDic POS projection for local morphological evidence.

This retains the existing coarse projection outside affixes. It is not a full
contextual UD conversion: UniDic short-unit tags omit the long-unit and bunsetsu
information required by many Japanese UD rules.
"""

from __future__ import annotations

_BASE_POS = {
    "名詞": "NOUN",
    "代名詞": "PRON",
    "動詞": "VERB",
    "形容詞": "ADJ",
    "形状詞": "ADJ",
    "副詞": "ADV",
    "助詞": "PART",
    "助動詞": "AUX",
    "連体詞": "DET",
    "接続詞": "CCONJ",
    "感動詞": "INTJ",
    "補助記号": "PUNCT",
    "記号": "SYM",
}


def unidic_to_upos(pos1: str | None, pos2: str | None, lemma: str | None) -> str:
    """Project native fields; dictionary presence and lemma validity are separate.

    Affix rules 34–40 need only short-unit POS and the dictionary base, unlike
    the contextual rules elsewhere in the primary Japanese UD conversion table:
    https://udjapanese.github.io/UD_converion_table/POS.html

    ``lemma`` is Fugashi's UniDic lexeme field, never a fallback surface form.
    Unknown categories stay unresolved rather than inheriting a default noun.
    """
    if pos1 == "接頭辞":
        return "NOUN"
    if pos1 == "接尾辞":
        if pos2 == "名詞的":
            return "PART" if lemma == "さ" else "NOUN"
        if pos2 in {"形状詞的", "動詞的"}:
            return "PART"
        if pos2 == "形容詞的":
            return "PART" if isinstance(lemma, str) and "ぽい" in lemma else "AUX"
        return "X"
    if pos1 == "名詞":
        if pos2 == "固有名詞":
            return "PROPN"
        if pos2 == "数詞":
            return "NUM"
    return _BASE_POS.get(pos1, "X")
