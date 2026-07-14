"""Shared part-of-speech normalization for learner-facing card text."""

from __future__ import annotations

import unicodedata

CANONICAL_PART_OF_SPEECH_LABELS = (
    "noun",
    "verb",
    "adjective",
    "adverb",
    "article",
    "preposition",
    "postposition",
    "conjunction",
    "pronoun",
    "determiner",
    "particle",
    "numeral",
    "interjection",
    "proper noun",
    "auxiliary verb",
)

_GENERIC_PART_OF_SPEECH_VALUES = {"", "term", "unknown", "word"}

_PART_OF_SPEECH_ALIASES = {
    "adj": "adjective",
    "adjective": "adjective",
    "adv": "adverb",
    "adverb": "adverb",
    "article": "article",
    "aux": "auxiliary verb",
    "auxiliary": "auxiliary verb",
    "auxiliary verb": "auxiliary verb",
    "conj": "conjunction",
    "conjunction": "conjunction",
    "det": "determiner",
    "determiner": "determiner",
    "interj": "interjection",
    "interjection": "interjection",
    "noun": "noun",
    "num": "numeral",
    "number": "numeral",
    "numeral": "numeral",
    "particle": "particle",
    "postp": "postposition",
    "postposition": "postposition",
    "prep": "preposition",
    "preposition": "preposition",
    "pron": "pronoun",
    "pronoun": "pronoun",
    "proper": "proper noun",
    "proper noun": "proper noun",
    "verb": "verb",
}


def canonical_part_of_speech_label(value: str | None) -> str | None:
    """Return the canonical POS label for a trusted source value."""

    if value is None:
        return None
    normalized = _normalize_label_key(value)
    if normalized in _GENERIC_PART_OF_SPEECH_VALUES:
        return None
    return _PART_OF_SPEECH_ALIASES.get(normalized)


def infer_function_word_part_of_speech(
    *,
    source_language: str | None,
    display_form: str,
    lemma: str,
) -> str | None:
    """Infer POS for high-confidence closed-class words in supported languages."""

    language = str(source_language or "").casefold()
    if not language:
        return None
    language_map = _FUNCTION_WORD_LABELS.get(language)
    if language_map is None:
        return None
    for value in (display_form, lemma):
        label = language_map.get(_normalize_lookup_key(value))
        if label is not None:
            return label
    return None


def resolve_part_of_speech_label(
    *,
    part_of_speech: str | None,
    source_language: str | None,
    display_form: str,
    lemma: str,
) -> str | None:
    """Resolve source POS first, then deterministic function-word inference."""

    return canonical_part_of_speech_label(part_of_speech) or infer_function_word_part_of_speech(
        source_language=source_language,
        display_form=display_form,
        lemma=lemma,
    )


def _language_map(rows: dict[str, tuple[str, ...]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for label, words in rows.items():
        canonical_label = canonical_part_of_speech_label(label)
        if canonical_label is None:
            raise ValueError(f"unknown canonical POS label: {label}")
        for word in words:
            key = _normalize_lookup_key(word)
            existing = mapping.get(key)
            if existing is not None and existing != canonical_label:
                raise ValueError(f"ambiguous function-word POS entry: {word}")
            mapping[key] = canonical_label
    return mapping


def _normalize_label_key(value: str) -> str:
    return " ".join(value.replace("-", " ").replace("_", " ").casefold().split())


def _normalize_lookup_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return " ".join(without_marks.split())


_FUNCTION_WORD_LABELS = {
    "pt": _language_map(
        {
            "article": ("o", "os", "um", "uma", "uns", "umas"),
            "preposition": ("em", "de", "para", "com", "por", "sem", "sobre", "entre"),
            "conjunction": ("e", "ou", "mas"),
            "pronoun": ("eu", "tu", "ele", "ela", "nos", "nós", "eles", "elas", "isso", "isto", "algo", "nada", "tudo", "alguém", "ninguém"),
            "adverb": ("não",),
        }
    ),
    "es": _language_map(
        {
            "article": ("el", "la", "los", "las", "un", "una", "unos", "unas"),
            "preposition": ("en", "de", "para", "con", "por", "sin", "sobre", "entre"),
            "conjunction": ("y", "o", "pero"),
            "pronoun": ("yo", "tú", "tu", "ella", "nosotros", "vosotros", "ellos", "ellas", "algo", "nada", "todo", "alguien", "nadie"),
            "adverb": ("no",),
        }
    ),
    "en": _language_map(
        {
            "article": ("the", "a", "an"),
            "preposition": ("in", "on", "with", "to", "from", "of", "for", "by", "between"),
            "conjunction": ("and", "or", "but"),
            "pronoun": ("i", "you", "he", "she", "it", "we", "they", "something", "nothing", "everything", "someone", "somebody", "anyone", "nobody", "no one"),
            "adverb": ("not",),
        }
    ),
    "fr": _language_map(
        {
            "article": ("le", "la", "les", "un", "une"),
            "preposition": ("dans", "sur", "avec", "de", "pour", "par", "entre", "sans"),
            "conjunction": ("et", "ou", "mais"),
            "pronoun": ("je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "rien", "tout", "quelqu'un", "personne", "quelque chose"),
            "adverb": ("ne", "pas"),
        }
    ),
    "de": _language_map(
        {
            "article": ("der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "einem", "einen"),
            "preposition": ("in", "auf", "mit", "zu", "von", "für", "aus", "bei", "nach", "über", "unter"),
            "conjunction": ("und", "oder", "aber"),
            "pronoun": ("ich", "du", "er", "sie", "es", "wir", "ihr", "etwas", "nichts", "alles", "jemand", "niemand", "man"),
            "adverb": ("nicht",),
        }
    ),
    "it": _language_map(
        {
            "article": ("il", "lo", "la", "i", "gli", "le", "un", "una"),
            "preposition": ("in", "su", "con", "di", "a", "da", "per", "tra", "fra"),
            "conjunction": ("e", "o", "ma"),
            "pronoun": ("io", "tu", "lui", "lei", "noi", "voi", "loro", "qualcosa", "niente", "tutto", "qualcuno", "nessuno"),
            "adverb": ("non",),
        }
    ),
    "pl": _language_map(
        {
            "preposition": ("w", "na", "z", "do", "od", "przez", "dla"),
            "conjunction": ("i", "lub", "ale"),
            "pronoun": ("ja", "ty", "on", "ona", "ono", "my", "wy", "oni", "one", "to", "co", "coś", "nic", "wszystko", "ktoś", "nikt"),
            "particle": ("nie", "czy"),
            "adverb": ("jak",),
        }
    ),
    "tr": _language_map(
        {
            "postposition": ("için", "gibi", "kadar", "ile"),
            "conjunction": ("ve", "veya", "ama"),
            "pronoun": ("ben", "sen", "o", "biz", "siz", "onlar", "bir şey", "hiçbir şey", "her şey", "biri", "kimse"),
            "particle": ("de", "da"),
        }
    ),
    "ro": _language_map(
        {
            "article": ("un", "o"),
            "preposition": ("în", "la", "cu", "de", "pentru", "prin", "fără", "între"),
            "conjunction": ("și", "sau", "dar"),
            "pronoun": ("eu", "tu", "el", "ea", "noi", "voi", "ei", "ele", "ceva", "nimic", "tot", "cineva", "nimeni"),
            "adverb": ("nu",),
        }
    ),
    "ru": _language_map(
        {
            "preposition": ("в", "на", "с", "к", "от", "для", "по", "без", "между"),
            "conjunction": ("и", "или", "но"),
            "pronoun": ("я", "ты", "он", "она", "оно", "мы", "вы", "они", "это", "что-то", "ничто", "всё", "кто-то", "никто"),
            "particle": ("не",),
        }
    ),
    "nl": _language_map(
        {
            "article": ("de", "het", "een"),
            "preposition": ("in", "op", "met", "naar", "van", "voor", "door", "tussen", "zonder"),
            "conjunction": ("en", "of", "maar"),
            "pronoun": ("ik", "jij", "je", "hij", "zij", "we", "wij", "jullie", "iets", "niets", "alles", "iemand", "niemand"),
            "adverb": ("niet",),
        }
    ),
    "da": _language_map(
        {
            "article": ("en", "et"),
            "preposition": ("i", "på", "til", "fra", "med", "for", "mellem"),
            "conjunction": ("og", "eller", "men"),
            "pronoun": ("jeg", "du", "han", "hun", "det", "vi", "de", "noget", "intet", "alt", "nogen", "ingen"),
            "adverb": ("ikke",),
        }
    ),
    "nb": _language_map(
        {
            "article": ("en", "ei", "et"),
            "preposition": ("i", "på", "til", "fra", "med", "for", "mellom"),
            "conjunction": ("og", "eller", "men"),
            "pronoun": ("jeg", "du", "han", "hun", "det", "vi", "dere", "de", "noe", "ingenting", "alt", "noen", "ingen"),
            "adverb": ("ikke",),
        }
    ),
    "sv": _language_map(
        {
            "article": ("en", "ett"),
            "preposition": ("i", "på", "till", "från", "med", "för", "mellan"),
            "conjunction": ("och", "eller", "men"),
            "pronoun": ("jag", "du", "han", "hon", "det", "vi", "ni", "de", "något", "ingenting", "allt", "någon", "ingen"),
            "adverb": ("inte",),
        }
    ),
    "fi": _language_map(
        {
            "postposition": ("kanssa", "varten", "jälkeen", "ennen"),
            "conjunction": ("ja", "tai", "mutta"),
            "pronoun": ("minä", "sinä", "hän", "me", "te", "he", "jotakin", "joku", "kukaan", "kaikki"),
            "particle": ("ei",),
        }
    ),
    "cs": _language_map(
        {
            "preposition": ("v", "ve", "na", "s", "se", "z", "do", "od", "pro", "bez", "mezi", "po", "před", "za", "u"),
            "conjunction": ("a", "nebo", "ale", "že", "když", "protože"),
            "pronoun": ("já", "ty", "on", "ona", "ono", "my", "vy", "oni", "to", "něco", "nic", "všechno", "někdo", "nikdo"),
            "particle": ("ne",),
        }
    ),
    "la": _language_map(
        {
            "preposition": ("in", "cum", "ad", "de", "ex", "per", "sine", "inter"),
            "conjunction": ("et", "aut", "sed"),
            "pronoun": ("ego", "tu", "nos", "vos", "is", "ea", "id", "aliquid", "nihil", "omnia", "aliquis", "nemo"),
        }
    ),
}


__all__ = [
    "CANONICAL_PART_OF_SPEECH_LABELS",
    "canonical_part_of_speech_label",
    "infer_function_word_part_of_speech",
    "resolve_part_of_speech_label",
]
