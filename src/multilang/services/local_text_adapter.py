"""Deterministic local sentence and translation adapters for shipped runtime tests."""

from __future__ import annotations

import re

from multilang.domain.jobs import SupportedLanguage
from multilang.services.text_generation import (
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceTranslationRequest,
    SentenceTranslationResult,
)

_DEFINITION_RE = re.compile(r"<[^>]+>")

_SENSE_ALIASES = {
    "lavar": "wash",
    "lavarse": "wash",
    "se laver": "wash",
    "use": "use",
    "usar": "use",
    "wash": "wash",
}

_SENSE_TRANSLATIONS = {
    "use": {
        "de": "benutzen",
        "en": "use",
        "es": "usar",
        "fr": "utiliser",
        "it": "usare",
        "nl": "gebruiken",
        "pl": "używać",
        "pt": "usar",
        "ro": "folosi",
        "ru": "использовать",
        "tr": "kullanmak",
    },
    "wash": {
        "de": "waschen",
        "en": "wash",
        "es": "lavarse",
        "fr": "se laver",
        "it": "lavarsi",
        "nl": "wassen",
        "pl": "myć się",
        "pt": "lavar",
        "ro": "a se spăla",
        "ru": "мыться",
        "tr": "yıkanmak",
    },
}

_VERB_TEMPLATES = {
    "de": "Meine Schwester möchte morgen {term}.",
    "en": "My brother wants to {term} tomorrow.",
    "es": "Mi hermano quiere {term} mañana.",
    "fr": "Mon frère veut {term} demain.",
    "it": "Mio fratello vuole {term} domani.",
    "nl": "Mijn broer wil morgen {term}.",
    "pl": "Mój brat chce jutro {term}.",
    "pt": "Meu irmão quer {term} amanhã.",
    "ro": "Fratele meu vrea să {term} mâine.",
    "ru": "Мой брат хочет {term} завтра.",
    "tr": "Kardeşim yarın {term} istiyor.",
}

_TERM_TEMPLATES = {
    "de": "Nachbarn besprechen {term} beim Abendessen.",
    "en": "Friends discuss {term} during lunch.",
    "es": "Los vecinos comentan {term} durante la cena.",
    "fr": "Des voisins discutent {term} pendant le dîner.",
    "it": "I vicini discutono {term} durante la cena.",
    "nl": "Buren bespreken {term} tijdens het avondeten.",
    "pl": "Sąsiedzi omawiają {term} podczas kolacji.",
    "pt": "Amigos comentam {term} durante o almoço.",
    "ro": "Vecinii discută {term} în timpul cinei.",
    "ru": "Соседи обсуждают {term} за ужином.",
    "tr": "Komşular akşam yemeğinde {term} tartışır.",
}

_CURATED_LOCAL_TEXT = {
    "harbor": {
        "sentence": "The fishing boats returned to the harbor before sunset.",
        "translations": {
            "pt": "Os barcos de pesca voltaram ao porto antes do pôr do sol.",
        },
    },
    "lantern": {
        "sentence": "She hung the lantern beside the cabin door.",
        "translations": {
            "pt": "Ela pendurou a lanterna ao lado da porta da cabana.",
        },
    },
    "meadow": {
        "sentence": "Wildflowers covered the meadow in early spring.",
        "translations": {
            "pt": "Flores silvestres cobriam o prado no início da primavera.",
        },
    },
}


class LocalSentenceAdapter:
    """Generate bounded deterministic sentences that satisfy runtime validators."""

    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        curated = _CURATED_LOCAL_TEXT.get(request.display_form.casefold())
        if curated is not None and request.target_language == SupportedLanguage.EN.value:
            return SentenceGenerationResult(
                sentence=curated["sentence"],
                intended_sense=_sense_hint(request.definitions_html, request.display_form),
                uncertainty_notes=[],
                provenance={
                    "source": "runtime-local-generator",
                    "provider": "local",
                    "template_kind": f"curated:{request.display_form.casefold()}",
                },
            )

        sense_key = _infer_sense_key(request.definitions_html, request.display_form)
        sense_hint = _sense_hint(request.definitions_html, request.display_form)
        if request.target_language not in _VERB_TEMPLATES:
            raise ValueError(f"unsupported runtime template language: {request.target_language}")

        if "flag" in request.display_form.casefold():
            sentence = f"placeholder {request.display_form} placeholder"
            template_kind = "flagged"
            uncertainty_notes = ["local runtime inserted a placeholder review case"]
        else:
            template_kind = "verb" if sense_key is not None else "term"
            templates = _VERB_TEMPLATES if template_kind == "verb" else _TERM_TEMPLATES
            sentence = templates[request.target_language].format(term=request.display_form)
            uncertainty_notes = []

        return SentenceGenerationResult(
            sentence=sentence,
            intended_sense=sense_key or sense_hint,
            uncertainty_notes=uncertainty_notes,
            provenance={
                "source": "runtime-local-generator",
                "provider": "local",
                "template_kind": template_kind,
                "sense_key": sense_key,
            },
        )


class LocalTranslationAdapter:
    """Translate local templates without copying source or definition text."""

    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult:
        if request.template_kind and request.template_kind.startswith("curated:"):
            curated = _CURATED_LOCAL_TEXT.get(request.template_kind.split(":", 1)[1])
            if curated is not None:
                translation = curated["translations"].get(request.translation_target_language)
                if translation is not None:
                    return SentenceTranslationResult(
                        translation=translation,
                        provenance={"source": "runtime-local-translator", "provider": "local"},
                    )

        if "placeholder" in request.sentence.casefold():
            translation = request.sentence
        else:
            term = _localized_sense(
                request.intended_sense,
                language=request.translation_target_language,
            )
            template_kind = request.template_kind or "term"
            templates = _VERB_TEMPLATES if template_kind == "verb" else _TERM_TEMPLATES
            template = templates.get(request.translation_target_language)
            translation = template.format(term=term) if template is not None else f"Translated sentence about {term}."
        return SentenceTranslationResult(
            translation=translation,
            provenance={"source": "runtime-local-translator", "provider": "local"},
        )


def _sense_hint(definitions_html: str | None, display_form: str) -> str:
    first_gloss = _first_gloss(definitions_html)
    if not first_gloss:
        return display_form

    if first_gloss.startswith("definition for "):
        candidate = first_gloss.removeprefix("definition for ").strip()
        return candidate or display_form

    if first_gloss.startswith("to "):
        candidate = first_gloss.removeprefix("to ").strip()
        return candidate or display_form

    return first_gloss


def _infer_sense_key(definitions_html: str | None, display_form: str) -> str | None:
    candidates = [display_form.casefold(), _sense_hint(definitions_html, display_form).casefold()]
    for candidate in candidates:
        if candidate in _SENSE_ALIASES:
            return _SENSE_ALIASES[candidate]
    return None


def _localized_sense(sense_hint: str | None, *, language: str) -> str:
    if not sense_hint:
        return "this"

    sense_key = _SENSE_ALIASES.get(sense_hint.casefold(), sense_hint.casefold())
    return _SENSE_TRANSLATIONS.get(sense_key, {}).get(language, sense_hint)


def _first_gloss(definitions_html: str | None) -> str:
    if not definitions_html:
        return ""

    first_segment = definitions_html.split("<br>", 1)[0]
    stripped = _DEFINITION_RE.sub(" ", first_segment)
    return " ".join(stripped.casefold().split())


__all__ = ["LocalSentenceAdapter", "LocalTranslationAdapter"]
