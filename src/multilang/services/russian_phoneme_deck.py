"""Deterministic introductory Russian phoneme Anki deck."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import re

import genanki

PHONEME_MODEL_ID = 1_602_300_601
PHONEME_DECK_ID = 1_602_300_602
PHONEME_NOTE_TYPE_NAME = "Multilang::Russian Phoneme"
DEFAULT_RUSSIAN_PHONEME_DECK_NAME = "Multilang Russian::Intro Phonemes"
PHONEME_FIELD_NAMES = (
    "SortIndex",
    "Spellings",
    "IPA",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Definitions",
    "Exemple Sentence",
    "sentence_audio",
    "Translation",
    "image",
)
_TEMPLATE_SECTION_RE = re.compile(
    r"## Front Template\s+```html\n(?P<front>.*?)```.*?"
    r"## Back Template\s+```html\n(?P<back>.*?)```.*?"
    r"## Styling \(CSS\)\s+```css\n(?P<css>.*?)```",
    re.DOTALL,
)


@dataclass(frozen=True)
class RussianPhonemeCard:
    sort_index: int
    letters: str
    ipa: str
    example_word: str
    example_word_translation: str
    example_sentence: str
    example_sentence_translation: str
    definitions: str | None = None

    @property
    def guid(self) -> str:
        payload = f"ru-phoneme|{self.sort_index}|{self.letters}|{self.ipa}"
        return sha256(payload.encode("utf-8")).hexdigest()[:32]


RUSSIAN_PHONEME_CARDS: tuple[RussianPhonemeCard, ...] = (
    RussianPhonemeCard(1, "а", "/a/", "мама", "mother", "Анна нашла карту.", "Anna found a map."),
    RussianPhonemeCard(2, "о", "/o/", "дом", "house", "Оля открыла окно.", "Olya opened a window."),
    RussianPhonemeCard(3, "у", "/u/", "урок", "lesson", "Утром утки плывут.", "In the morning ducks swim."),
    RussianPhonemeCard(4, "и", "/i/", "мир", "world", "Ира видит синие линии.", "Ira sees blue lines."),
    RussianPhonemeCard(5, "ы", "/ɨ/", "сыр", "cheese", "Сын мыл сырные миски.", "The son washed cheese bowls."),
    RussianPhonemeCard(6, "э", "/e/", "это", "this", "Эдик берёт этот эскиз.", "Edik takes this sketch."),
    RussianPhonemeCard(7, "я", "/ja/", "яблоко", "apple", "Яша ясно тянет лямку.", "Yasha clearly pulls the strap."),
    RussianPhonemeCard(8, "ё", "/jo/", "ёлка", "fir tree", "Ёж несёт мёд.", "A hedgehog carries honey."),
    RussianPhonemeCard(9, "ю", "/ju/", "юла", "spinning top", "Юля любит южный уют.", "Yulia loves southern coziness."),
    RussianPhonemeCard(10, "е", "/je/", "енот", "raccoon", "Елена едет через ельник.", "Elena rides through a spruce grove."),
    RussianPhonemeCard(11, "б", "/b/", "брат", "brother", "Борис берёт большой билет.", "Boris takes a big ticket."),
    RussianPhonemeCard(12, "бь", "/bʲ/", "белка", "squirrel", "Белый берег блестит.", "The white bank shines."),
    RussianPhonemeCard(13, "п", "/p/", "папа", "father", "Павел пишет письмо.", "Pavel writes a letter."),
    RussianPhonemeCard(14, "пь", "/pʲ/", "пена", "foam", "Петя пьёт тёплый сироп.", "Petya drinks warm syrup."),
    RussianPhonemeCard(15, "в", "/v/", "вода", "water", "Вова варит вкусный суп.", "Vova cooks tasty soup."),
    RussianPhonemeCard(16, "вь", "/vʲ/", "ветер", "wind", "Вера видит весенний вечер.", "Vera sees a spring evening."),
    RussianPhonemeCard(17, "ф", "/f/", "флаг", "flag", "Фёдор фотографирует флаг.", "Fyodor photographs a flag."),
    RussianPhonemeCard(18, "фь", "/fʲ/", "фильм", "film", "Филипп смотрит фильм.", "Filipp watches a film."),
    RussianPhonemeCard(19, "д", "/d/", "дом", "house", "Даша держит длинный дуб.", "Dasha holds a long oak."),
    RussianPhonemeCard(20, "дь", "/dʲ/", "день", "day", "Дети делят дивный день.", "The children share a wonderful day."),
    RussianPhonemeCard(21, "т", "/t/", "стол", "table", "Толя тащит тяжёлый таз.", "Tolya drags a heavy basin."),
    RussianPhonemeCard(22, "ть", "/tʲ/", "тень", "shadow", "Тихий тигр тянет тетрадь.", "A quiet tiger pulls a notebook."),
    RussianPhonemeCard(23, "з", "/z/", "зуб", "tooth", "Зоя знает звонкий закон.", "Zoya knows a sonorous law."),
    RussianPhonemeCard(24, "зь", "/zʲ/", "зима", "winter", "Зина несёт зелёное зеркало.", "Zina carries a green mirror."),
    RussianPhonemeCard(25, "с", "/s/", "сад", "garden", "Саша ставит сухой стул.", "Sasha places a dry chair."),
    RussianPhonemeCard(26, "сь", "/sʲ/", "семь", "seven", "Сеня сеет синий салат.", "Senya sows blue lettuce."),
    RussianPhonemeCard(27, "г", "/g/", "гора", "mountain", "Глеб готовит горячий гриб.", "Gleb cooks a hot mushroom."),
    RussianPhonemeCard(28, "гь", "/gʲ/", "гимн", "anthem", "Гена гибко греет гитару.", "Gena flexibly warms a guitar."),
    RussianPhonemeCard(29, "к", "/k/", "кот", "cat", "Коля кладёт красный камень.", "Kolya lays down a red stone."),
    RussianPhonemeCard(30, "кь", "/kʲ/", "кит", "whale", "Кира кидает кислый киви.", "Kira throws a sour kiwi."),
    RussianPhonemeCard(31, "м", "/m/", "мама", "mother", "Марк моет маленькую машину.", "Mark washes a small car."),
    RussianPhonemeCard(32, "мь", "/mʲ/", "мяч", "ball", "Мила меряет мягкий мех.", "Mila measures soft fur."),
    RussianPhonemeCard(33, "н", "/n/", "нос", "nose", "Никита нашёл новый нож.", "Nikita found a new knife."),
    RussianPhonemeCard(34, "нь", "/nʲ/", "ночь", "night", "Нина несёт нежный нектар.", "Nina carries delicate nectar."),
    RussianPhonemeCard(35, "л", "/l/", "лук", "onion", "Лара ломает лунный лук.", "Lara breaks a moonlit bow."),
    RussianPhonemeCard(36, "ль", "/lʲ/", "лес", "forest", "Лена любит летний лес.", "Lena loves the summer forest."),
    RussianPhonemeCard(37, "р", "/r/", "рыба", "fish", "Роман рисует ровную раму.", "Roman draws an even frame."),
    RussianPhonemeCard(38, "рь", "/rʲ/", "река", "river", "Рита рисует резкий ряд.", "Rita draws a sharp row."),
    RussianPhonemeCard(39, "х", "/x/", "хлеб", "bread", "Хор хранит хороший характер.", "The choir keeps a good character."),
    RussianPhonemeCard(40, "хь", "/xʲ/", "химия", "chemistry", "Хитрый хирург хвалит химика.", "A cunning surgeon praises a chemist."),
    RussianPhonemeCard(41, "ж", "/ʐ/", "жук", "beetle", "Женя жарит жёлтый желудь.", "Zhenya fries a yellow acorn."),
    RussianPhonemeCard(42, "ш", "/ʂ/", "шар", "ball", "Шура шьёт широкий шарф.", "Shura sews a wide scarf."),
    RussianPhonemeCard(43, "ц", "/ts/", "цвет", "color", "Цапля царапает цветной цилиндр.", "A heron scratches a colored cylinder."),
    RussianPhonemeCard(44, "ч", "/tɕ/", "чай", "tea", "Чайка чинит чёрный чайник.", "A seagull fixes a black teapot."),
    RussianPhonemeCard(45, "щ", "/ɕː/", "щука", "pike", "Щенок ищет щётку щедро.", "A puppy generously looks for a brush."),
    RussianPhonemeCard(46, "й", "/j/", "йогурт", "yogurt", "Майя играет яркой юлой.", "Maya plays with a bright spinning top."),
    RussianPhonemeCard(47, "ь", "soft sign", "конь", "horse", "Конь пьёт тёплую воду.", "A horse drinks warm water."),
    RussianPhonemeCard(48, "ъ", "separation sign", "объект", "object", "Подъезд объявил объём работы.", "The entrance announced the work volume."),
)


class RussianPhonemeNote(genanki.Note):
    @property
    def guid(self) -> str:
        return self._multilang_guid  # type: ignore[attr-defined]


@dataclass(frozen=True)
class RussianPhonemeDeckExportResult:
    output_path: Path
    card_count: int


def build_russian_phoneme_model() -> genanki.Model:
    template = _load_russian_phoneme_template()
    return genanki.Model(
        PHONEME_MODEL_ID,
        PHONEME_NOTE_TYPE_NAME,
        fields=[{"name": field_name} for field_name in PHONEME_FIELD_NAMES],
        templates=[
            {
                "name": "Phoneme Card",
                "qfmt": template["front"],
                "afmt": template["back"],
            }
        ],
        css=template["css"],
    )


def build_russian_phoneme_note(
    card: RussianPhonemeCard,
    *,
    model: genanki.Model | None = None,
) -> genanki.Note:
    note = RussianPhonemeNote(
        model=model or build_russian_phoneme_model(),
        fields=_phoneme_card_fields(card),
    )
    note._multilang_guid = card.guid  # type: ignore[attr-defined]
    return note


def export_russian_phoneme_deck(
    *,
    output_path: Path,
    deck_name: str = DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
) -> RussianPhonemeDeckExportResult:
    model = build_russian_phoneme_model()
    deck = genanki.Deck(PHONEME_DECK_ID, deck_name)
    for card in RUSSIAN_PHONEME_CARDS:
        deck.add_note(build_russian_phoneme_note(card, model=model))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(output_path))
    return RussianPhonemeDeckExportResult(output_path=output_path, card_count=len(RUSSIAN_PHONEME_CARDS))


def _phoneme_card_fields(card: RussianPhonemeCard) -> list[str]:
    values = {
        "SortIndex": str(card.sort_index),
        "Spellings": card.letters,
        "IPA": card.ipa,
        "letter_audio": "",
        "Example Word": card.example_word,
        "word_audio": "",
        "Word Translation": card.example_word_translation,
        "Definitions": card.definitions or _default_definition(card),
        "Exemple Sentence": card.example_sentence,
        "sentence_audio": "",
        "Translation": card.example_sentence_translation,
        "image": "",
    }
    return [values[field_name] for field_name in PHONEME_FIELD_NAMES]


def _default_definition(card: RussianPhonemeCard) -> str:
    return f"Russian spelling {card.letters} is practiced here with the sound {card.ipa}."


def _load_russian_phoneme_template() -> dict[str, str]:
    template_path = Path(__file__).resolve().parents[3] / "templates" / "russian_phoneme_card.md"
    content = template_path.read_text(encoding="utf-8")
    match = _TEMPLATE_SECTION_RE.search(content)
    if match is None:
        raise ValueError(f"unable to parse Russian phoneme template from {template_path}")
    return {name: match.group(name).strip() for name in ("front", "back", "css")}


__all__ = [
    "DEFAULT_RUSSIAN_PHONEME_DECK_NAME",
    "PHONEME_DECK_ID",
    "PHONEME_FIELD_NAMES",
    "PHONEME_MODEL_ID",
    "PHONEME_NOTE_TYPE_NAME",
    "RUSSIAN_PHONEME_CARDS",
    "RussianPhonemeCard",
    "RussianPhonemeDeckExportResult",
    "build_russian_phoneme_model",
    "build_russian_phoneme_note",
    "export_russian_phoneme_deck",
]
