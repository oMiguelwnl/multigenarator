"""Deterministic introductory Russian phoneme Anki deck."""

from __future__ import annotations

from dataclasses import dataclass, replace
from importlib.resources import files
from pathlib import Path
from hashlib import sha256
import re
from datetime import datetime

import genanki

from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.settings import Settings

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
    settings: Settings | None = None,
) -> RussianPhonemeDeckExportResult:
    settings = settings or Settings()
    model = build_russian_phoneme_model()
    deck = genanki.Deck(PHONEME_DECK_ID, deck_name)
    
    # Synthesize audio for all cards
    synthesizer = AzureSpeechAdapter(settings)
    audio_dir = Path(settings.audio_storage_dir) / "phoneme" / datetime.now().strftime("%Y-%m-%d")
    media_files: list[Path] = []
    
    # Synthesize audio for each card
    cards_with_audio = []
    for card in cards:
        card_with_audio = _synthesize_card_audio(
            card=card,
            synthesizer=synthesizer,
            audio_dir=audio_dir,
            media_files=media_files,
        )
        cards_with_audio.append(card_with_audio)
        deck.add_note(build_russian_phoneme_note(card_with_audio, model=model))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = [str(path) for path in media_files]
    package.write_to_file(str(output_path))
    return RussianPhonemeDeckExportResult(output_path=output_path, card_count=len(cards))


def _synthesize_card_audio(
    *,
    card: RussianPhonemeCard,
    synthesizer: AzureSpeechAdapter,
    audio_dir: Path,
    media_files: list[Path],
) -> RussianPhonemeCard:
    """Synthesize audio for letter, word, and sentence of a card."""
    letter_audio = ""
    word_audio = ""
    sentence_audio = ""
    
    try:
        # Synthesize letter audio
        letter_audio_path = _synthesize_text(
            text=card.letters,
            item_id=f"letter-{card.sort_index}",
            synthesizer=synthesizer,
            audio_dir=audio_dir,
        )
        if letter_audio_path:
            letter_audio = f"[sound:{letter_audio_path.name}]"
            media_files.append(letter_audio_path)
    except Exception:
        # Silently skip audio if synthesis fails
        pass
    
    try:
        # Synthesize word audio
        word_audio_path = _synthesize_text(
            text=card.example_word,
            item_id=f"word-{card.sort_index}",
            synthesizer=synthesizer,
            audio_dir=audio_dir,
        )
        if word_audio_path:
            word_audio = f"[sound:{word_audio_path.name}]"
            media_files.append(word_audio_path)
    except Exception:
        pass
    
    try:
        # Synthesize sentence audio
        sentence_audio_path = _synthesize_text(
            text=card.example_sentence,
            item_id=f"sentence-{card.sort_index}",
            synthesizer=synthesizer,
            audio_dir=audio_dir,
        )
        if sentence_audio_path:
            sentence_audio = f"[sound:{sentence_audio_path.name}]"
            media_files.append(sentence_audio_path)
    except Exception:
        pass
    
    # Return card with audio references
    return replace(
        card,
        letter_audio=letter_audio,
        word_audio=word_audio,
        sentence_audio=sentence_audio,
    )


def _synthesize_text(
    *,
    text: str,
    item_id: str,
    synthesizer: AzureSpeechAdapter,
    audio_dir: Path,
) -> Path | None:
    """Synthesize audio for Russian text and return the file path."""
    # Generate unique filename based on content
    content_hash = sha256(text.encode("utf-8")).hexdigest()[:16]
    filename = f"ru-{item_id}-{content_hash}.mp3"
    output_path = audio_dir / filename
    
    # Skip if already synthesized
    if output_path.exists():
        return output_path
    
    # Synthesize using Azure Speech
    response = synthesizer.synthesize(
        ssml_text=text,
        voice_id="ru-RU-DmitryNeural",
        locale="ru-RU",
        output_path=output_path,
        audio_format="audio-24khz-48kbitrate-mono-mp3",
    )
    
    # Verify synthesis was successful
    if response.storage_path and response.storage_path.exists():
        return response.storage_path
    
    return None


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
    template_path = files("multilang").joinpath("templates", "russian_phoneme_card.md")
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
