"""Deterministic local sentence and translation adapters for shipped runtime tests."""

from __future__ import annotations

import re

from multilang.domain.jobs import SupportedLanguage
from multilang.services.text_generation import (
    DefinitionGenerationRequest,
    DefinitionGenerationResult,
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
        "cs": "používat",
        "de": "benutzen",
        "en": "use",
        "es": "usar",
        "fi": "käyttää",
        "fr": "utiliser",
        "hu": "használni",
        "it": "usare",
        "nb": "bruke",
        "nl": "gebruiken",
        "pl": "używać",
        "pt": "usar",
        "ro": "folosi",
        "ru": "использовать",
        "sv": "använda",
        "tr": "kullanmak",
    },
    "wash": {
        "cs": "umýt se",
        "de": "waschen",
        "en": "wash",
        "es": "lavarse",
        "fi": "peseytyä",
        "fr": "se laver",
        "hu": "mosakodni",
        "it": "lavarsi",
        "nb": "vaske seg",
        "nl": "wassen",
        "pl": "myć się",
        "pt": "lavar",
        "ro": "a se spăla",
        "ru": "мыться",
        "sv": "tvätta sig",
        "tr": "yıkanmak",
    },
}

_VERB_TEMPLATES = {
    "cs": "Můj bratr chce zítra {term}.",
    "de": "Meine Schwester möchte morgen {term}.",
    "en": "My brother wants to {term} tomorrow.",
    "es": "Mi hermano quiere {term} mañana.",
    "fi": "Veljeni haluaa {term} huomenna.",
    "fr": "Mon frère veut {term} demain.",
    "hu": "A testvérem holnap {term} akar.",
    "it": "Mio fratello vuole {term} domani.",
    "nb": "Broren min vil {term} i morgen.",
    "nl": "Mijn broer wil morgen {term}.",
    "pl": "Mój brat chce jutro {term}.",
    "pt": "Meu irmão quer {term} amanhã.",
    "ro": "Fratele meu vrea să {term} mâine.",
    "ru": "Мой брат хочет {term} завтра.",
    "sv": "Min bror vill {term} i morgon.",
    "tr": "Kardeşim yarın {term} istiyor.",
}

_TERM_TEMPLATES = {
    "cs": "Sousedé diskutují o {term} během večeře.",
    "de": "Nachbarn besprechen {term} beim Abendessen.",
    "en": "Friends discuss {term} during lunch.",
    "es": "Los vecinos comentan {term} durante la cena.",
    "fi": "Naapurit keskustelevat {term} päivällisellä.",
    "fr": "Des voisins discutent {term} pendant le dîner.",
    "hu": "A szomszédok vacsora közben {term} szóról beszélnek.",
    "it": "I vicini discutono {term} durante la cena.",
    "nb": "Naboer diskuterer {term} under middagen.",
    "nl": "Buren bespreken {term} tijdens het avondeten.",
    "pl": "Sąsiedzi omawiają {term} podczas kolacji.",
    "pt": "Amigos comentam {term} durante o almoço.",
    "ro": "Vecinii discută {term} în timpul cinei.",
    "ru": "Соседи обсуждают {term} за ужином.",
    "sv": "Grannar diskuterar {term} under middagen.",
    "tr": "Komşular akşam yemeğinde {term} tartışır.",
}

_HIGHLIGHT_TEMPLATES = {
    "cs": "Čtenáři si všimnou {term} v klidné kapitole.",
    "de": "Die Leserin bemerkt {term} in der stillen Szene.",
    "en": "Readers notice {term} during the quiet chapter tonight.",
    "es": "Los lectores notan {term} durante el capítulo tranquilo.",
    "fi": "Lukijat huomaavat {term} rauhallisessa luvussa.",
    "fr": "Les lecteurs remarquent {term} pendant le chapitre calme.",
    "hu": "Az olvasók észreveszik {term} szót a csendes fejezetben.",
    "it": "I lettori notano {term} durante il capitolo silenzioso.",
    "nb": "Lesere legger merke til {term} i det rolige kapittelet.",
    "nl": "Lezers merken {term} op tijdens het rustige hoofdstuk.",
    "pl": "Czytelnicy zauważają {term} podczas spokojnego rozdziału.",
    "pt": "Leitores percebem {term} durante o capítulo silencioso.",
    "ro": "Cititorii observă {term} în timpul capitolului liniștit.",
    "ru": "Читатели замечают {term} во время тихой главы.",
    "sv": "Läsare lägger märke till {term} i det lugna kapitlet.",
    "tr": "Okurlar sakin bölümde {term} ifadesini fark eder.",
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

    def generate_definition(self, request: DefinitionGenerationRequest) -> DefinitionGenerationResult:
        label = _definition_label(request.part_of_speech)
        return DefinitionGenerationResult(
            definitions_html=f"{label}: learner definition for {request.lemma}",
            provenance={"source": "runtime-local-definition-generator", "provider": "local"},
        )

    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult:
        if request.source_type == "kindle-highlights":
            return _generate_highlight_sentence(request)

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
            template_kind = "verb" if _uses_verb_template(request, sense_key=sense_key) else "term"
            templates = _VERB_TEMPLATES if template_kind == "verb" else _TERM_TEMPLATES
            sentence = templates[request.target_language].format(term=_sentence_term(request))
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
        if request.template_kind == "definition":
            return SentenceTranslationResult(
                translation=_translate_definition_text(request.sentence, request.translation_target_language),
                provenance={"source": "runtime-local-definition-translator", "provider": "local"},
            )

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

    if first_gloss.startswith("learner definition for "):
        candidate = first_gloss.removeprefix("learner definition for ").strip()
        return candidate or display_form

    if first_gloss.startswith("definition for "):
        candidate = first_gloss.removeprefix("definition for ").strip()
        return candidate or display_form

    if first_gloss.startswith("to "):
        candidate = first_gloss.removeprefix("to ").strip()
        return candidate or display_form

    return first_gloss


def _generate_highlight_sentence(request: SentenceGenerationRequest) -> SentenceGenerationResult:
    if request.target_language not in _HIGHLIGHT_TEMPLATES:
        raise ValueError(f"unsupported runtime template language: {request.target_language}")
    sentence = _HIGHLIGHT_TEMPLATES[request.target_language].format(term=_sentence_term(request))
    return SentenceGenerationResult(
        sentence=sentence,
        intended_sense=_sense_hint(request.definitions_html, request.display_form),
        uncertainty_notes=[],
        provenance={
            "source": "runtime-local-generator",
            "provider": "local",
            "source_type": "kindle-highlights",
            "template_kind": "highlight",
        },
    )


def _infer_sense_key(definitions_html: str | None, display_form: str) -> str | None:
    candidates = [display_form.casefold(), _sense_hint(definitions_html, display_form).casefold()]
    for candidate in candidates:
        if candidate in _SENSE_ALIASES:
            return _SENSE_ALIASES[candidate]
    return None


def _uses_verb_template(request: SentenceGenerationRequest, *, sense_key: str | None) -> bool:
    return sense_key is not None or _definition_has_verb_label(request.definitions_html) or _first_gloss(
        request.definitions_html
    ).startswith("to ")


def _definition_has_verb_label(definitions_html: str | None) -> bool:
    if not definitions_html:
        return False
    first_segment = definitions_html.split("<br>", 1)[0]
    stripped = _DEFINITION_RE.sub(" ", first_segment)
    return bool(re.match(r"\s*verb\s*:", stripped, flags=re.IGNORECASE))


def _sentence_term(request: SentenceGenerationRequest) -> str:
    term = request.display_form.strip()
    lemma = request.lemma.strip()
    if lemma and term.casefold() != lemma.casefold():
        term = lemma
    return _lowercase_sentence_term(term, target_language=request.target_language)


def _lowercase_sentence_term(term: str, *, target_language: str) -> str:
    if target_language == SupportedLanguage.DE.value or not term[:1].isupper():
        return term
    return term[:1].casefold() + term[1:]


def _localized_sense(sense_hint: str | None, *, language: str) -> str:
    if not sense_hint:
        return "this"

    sense_key = _SENSE_ALIASES.get(sense_hint.casefold(), sense_hint.casefold())
    return _SENSE_TRANSLATIONS.get(sense_key, {}).get(language, sense_hint)


_DEFINITION_LABELS = {
    "cs": {"noun": "podstatné jméno", "verb": "sloveso", "adjective": "přídavné jméno", "adverb": "příslovce"},
    "de": {"noun": "Substantiv", "verb": "Verb", "adjective": "Adjektiv", "adverb": "Adverb"},
    "en": {"noun": "noun", "verb": "verb", "adjective": "adjective", "adverb": "adverb"},
    "es": {"noun": "sustantivo", "verb": "verbo", "adjective": "adjetivo", "adverb": "adverbio"},
    "fi": {"noun": "substantiivi", "verb": "verbi", "adjective": "adjektiivi", "adverb": "adverbi"},
    "fr": {"noun": "nom", "verb": "verbe", "adjective": "adjectif", "adverb": "adverbe"},
    "hu": {"noun": "főnév", "verb": "ige", "adjective": "melléknév", "adverb": "határozószó"},
    "it": {"noun": "sostantivo", "verb": "verbo", "adjective": "aggettivo", "adverb": "avverbio"},
    "nb": {"noun": "substantiv", "verb": "verb", "adjective": "adjektiv", "adverb": "adverb"},
    "nl": {"noun": "zelfstandig naamwoord", "verb": "werkwoord", "adjective": "bijvoeglijk naamwoord", "adverb": "bijwoord"},
    "pl": {"noun": "rzeczownik", "verb": "czasownik", "adjective": "przymiotnik", "adverb": "przysłówek"},
    "pt": {"noun": "substantivo", "verb": "verbo", "adjective": "adjetivo", "adverb": "advérbio"},
    "ro": {"noun": "substantiv", "verb": "verb", "adjective": "adjectiv", "adverb": "adverb"},
    "ru": {"noun": "существительное", "verb": "глагол", "adjective": "прилагательное", "adverb": "наречие"},
    "sv": {"noun": "substantiv", "verb": "verb", "adjective": "adjektiv", "adverb": "adverb"},
    "tr": {"noun": "isim", "verb": "fiil", "adjective": "sıfat", "adverb": "zarf"},
}


def _definition_label(value: str | None) -> str:
    if value is None:
        return "term"
    normalized = " ".join(value.replace("-", " ").replace("_", " ").casefold().split())
    return _DEFINITION_LABELS["en"].get(normalized, normalized or "term")


def _translate_definition_text(text: str, language: str) -> str:
    if language == "en":
        return text

    label, separator, meaning = text.partition(":")
    normalized_label = label.casefold().strip()
    translated_label = _DEFINITION_LABELS.get(language, {}).get(normalized_label, label.strip())
    translated_meaning = _translate_definition_meaning(meaning.strip() if separator else text, language)
    return f"{translated_label}: {translated_meaning}" if separator else translated_meaning


def _translate_definition_meaning(meaning: str, language: str) -> str:
    normalized = meaning.casefold().strip()
    if normalized.startswith("definition for "):
        term = meaning.removeprefix("definition for ").strip()
        prefixes = {
            "cs": "definice slova",
            "de": "Definition für",
            "es": "definición de",
            "fi": "määritelmä sanalle",
            "fr": "définition de",
            "hu": "meghatározás:",
            "it": "definizione di",
            "nb": "definisjon av",
            "nl": "definitie van",
            "pl": "definicja słowa",
            "pt": "definição de",
            "ro": "definiție pentru",
            "ru": "определение для",
            "sv": "definition av",
            "tr": "tanımı",
        }
        return f"{prefixes.get(language, 'definition for')} {term}".strip()
    if normalized.startswith("to "):
        sense = normalized.removeprefix("to ").strip()
        return _localized_sense(sense, language=language)
    return meaning


def _first_gloss(definitions_html: str | None) -> str:
    if not definitions_html:
        return ""

    first_segment = definitions_html.split("<br>", 1)[0]
    stripped = _DEFINITION_RE.sub(" ", first_segment)
    normalized = " ".join(stripped.casefold().split())
    return re.sub(r"^[a-z][a-z -]{1,40}:\s+", "", normalized).strip()


__all__ = ["LocalSentenceAdapter", "LocalTranslationAdapter"]
