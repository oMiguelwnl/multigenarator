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
    "Spellings",
    "Sound",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Example Sentence",
    "sentence_audio",
    "Sentence Translation",
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
    letter_audio: str = ""
    word_audio: str = ""
    sentence_audio: str = ""

    @property
    def guid(self) -> str:
        payload = f"ru-phoneme|{self.sort_index}|{self.letters}|{self.ipa}"
        return sha256(payload.encode("utf-8")).hexdigest()[:32]


RUSSIAN_PHONEME_CARDS: tuple[RussianPhonemeCard, ...] = (
    RussianPhonemeCard(1, "а", "/a/", "мама", "mother", "Мама нашла карту.", "Mother found a map."),
    RussianPhonemeCard(2, "о", "/o/", "дом", "house", "Оля открыла дом.", "Olya opened the house."),
    RussianPhonemeCard(3, "у", "/u/", "урок", "lesson", "Урок утром начался.", "The lesson started in the morning."),
    RussianPhonemeCard(4, "и", "/i/", "мир", "world", "Ира видит мир.", "Ira sees the world."),
    RussianPhonemeCard(5, "ы", "/ɨ/", "сыр", "cheese", "Сыр лежит дома.", "The cheese is at home."),
    RussianPhonemeCard(6, "э", "/e/", "это", "this", "Это мой эскиз.", "This is my sketch."),
    RussianPhonemeCard(7, "я", "/ja/", "яблоко", "apple", "Яша режет яблоко.", "Yasha cuts an apple."),
    RussianPhonemeCard(8, "ё", "/jo/", "ёлка", "fir tree", "Ёлка стоит рядом.", "The fir tree stands nearby."),
    RussianPhonemeCard(9, "ю", "/ju/", "юла", "spinning top", "Юла крутится быстро.", "The spinning top turns quickly."),
    RussianPhonemeCard(10, "е", "/je/", "енот", "raccoon", "Енот едет домой.", "The raccoon goes home."),
    RussianPhonemeCard(11, "б", "/b/", "брат", "brother", "Брат берёт билет.", "The brother takes a ticket."),
    RussianPhonemeCard(12, "бь", "/bʲ/", "белка", "squirrel", "Белка быстро бежит.", "The squirrel runs quickly."),
    RussianPhonemeCard(13, "п", "/p/", "папа", "father", "Папа пишет письмо.", "Father writes a letter."),
    RussianPhonemeCard(14, "пь", "/pʲ/", "пена", "foam", "Пена покрыла песок.", "Foam covered the sand."),
    RussianPhonemeCard(15, "в", "/v/", "вода", "water", "Вода кипит быстро.", "The water boils quickly."),
    RussianPhonemeCard(16, "вь", "/vʲ/", "ветер", "wind", "Ветер веет вечером.", "The wind blows in the evening."),
    RussianPhonemeCard(17, "ф", "/f/", "флаг", "flag", "Фёдор фотографирует флаг.", "Fyodor photographs a flag."),
    RussianPhonemeCard(18, "фь", "/fʲ/", "фильм", "film", "Филипп смотрит фильм.", "Filipp watches a film."),
    RussianPhonemeCard(19, "д", "/d/", "дом", "house", "Дом стоит далеко.", "The house stands far away."),
    RussianPhonemeCard(20, "дь", "/dʲ/", "день", "day", "Дети делят дивный день.", "The children share a wonderful day."),
    RussianPhonemeCard(21, "т", "/t/", "стол", "table", "Толя тащит стол.", "Tolya drags a table."),
    RussianPhonemeCard(22, "ть", "/tʲ/", "тень", "shadow", "Тень тихо тает.", "The shadow quietly melts."),
    RussianPhonemeCard(23, "з", "/z/", "зуб", "tooth", "Зуб звенит странно.", "The tooth rings strangely."),
    RussianPhonemeCard(24, "зь", "/zʲ/", "зима", "winter", "Зима несёт снег.", "Winter brings snow."),
    RussianPhonemeCard(25, "с", "/s/", "сад", "garden", "Сад стоит сухой.", "The garden stands dry."),
    RussianPhonemeCard(26, "сь", "/sʲ/", "семь", "seven", "Семь семян лежат.", "Seven seeds lie there."),
    RussianPhonemeCard(27, "г", "/g/", "гора", "mountain", "Гора греется утром.", "The mountain warms in the morning."),
    RussianPhonemeCard(28, "гь", "/gʲ/", "гимн", "anthem", "Гимн звучит громко.", "The anthem sounds loud."),
    RussianPhonemeCard(29, "к", "/k/", "кот", "cat", "Кот кладёт камень.", "The cat puts down a stone."),
    RussianPhonemeCard(30, "кь", "/kʲ/", "кит", "whale", "Кит кивает Кире.", "The whale nods to Kira."),
    RussianPhonemeCard(31, "м", "/m/", "мама", "mother", "Мама моет машину.", "Mother washes the car."),
    RussianPhonemeCard(32, "мь", "/mʲ/", "мяч", "ball", "Мяч мягко летит.", "The ball flies softly."),
    RussianPhonemeCard(33, "н", "/n/", "нос", "nose", "Нос нашёл запах.", "The nose found a smell."),
    RussianPhonemeCard(34, "нь", "/nʲ/", "ночь", "night", "Ночь несёт нежность.", "Night brings tenderness."),
    RussianPhonemeCard(35, "л", "/l/", "лук", "onion", "Лара режет лук.", "Lara cuts an onion."),
    RussianPhonemeCard(36, "ль", "/lʲ/", "лес", "forest", "Лена любит летний лес.", "Lena loves the summer forest."),
    RussianPhonemeCard(37, "р", "/r/", "рыба", "fish", "Рыба рисует круг.", "The fish draws a circle."),
    RussianPhonemeCard(38, "рь", "/rʲ/", "река", "river", "Река рядом шумит.", "The river nearby makes noise."),
    RussianPhonemeCard(39, "х", "/x/", "хлеб", "bread", "Хлеб хранит тепло.", "The bread keeps warmth."),
    RussianPhonemeCard(40, "хь", "/xʲ/", "химия", "chemistry", "Химия хитро звучит.", "Chemistry sounds tricky."),
    RussianPhonemeCard(41, "ж", "/ʐ/", "жук", "beetle", "Жук жуёт жёлудь.", "The beetle chews an acorn."),
    RussianPhonemeCard(42, "ш", "/ʂ/", "шар", "ball", "Шура несёт шар.", "Shura carries a ball."),
    RussianPhonemeCard(43, "ц", "/ts/", "цвет", "color", "Цвет важен здесь.", "Color is important here."),
    RussianPhonemeCard(44, "ч", "/tɕ/", "чай", "tea", "Чай остывает быстро.", "The tea cools quickly."),
    RussianPhonemeCard(45, "щ", "/ɕː/", "щука", "pike", "Щука ищет щётку.", "The pike looks for a brush."),
    RussianPhonemeCard(46, "й", "/j/", "йогурт", "yogurt", "Майя ест йогурт.", "Maya eats yogurt."),
    RussianPhonemeCard(47, "ь", "soft sign", "конь", "horse", "Конь пьёт тёплую воду.", "A horse drinks warm water."),
    RussianPhonemeCard(48, "ъ", "separation sign", "объект", "object", "Объект объявил объём.", "The object announced the volume."),
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
    cards: tuple[RussianPhonemeCard, ...] = RUSSIAN_PHONEME_CARDS,
) -> RussianPhonemeDeckExportResult:
    model = build_russian_phoneme_model()
    deck = genanki.Deck(PHONEME_DECK_ID, deck_name)
    for card in cards:
        deck.add_note(build_russian_phoneme_note(card, model=model))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(output_path))
    return RussianPhonemeDeckExportResult(output_path=output_path, card_count=len(cards))


def _phoneme_card_fields(card: RussianPhonemeCard) -> list[str]:
    values = {
        "Spellings": card.letters,
        "Sound": card.ipa,
        "letter_audio": card.letter_audio,
        "Example Word": card.example_word,
        "word_audio": card.word_audio,
        "Word Translation": card.example_word_translation,
        "Example Sentence": card.example_sentence,
        "sentence_audio": card.sentence_audio,
        "Sentence Translation": card.example_sentence_translation,
    }
    return [values[field_name] for field_name in PHONEME_FIELD_NAMES]


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
