"""Deterministic introductory phoneme Anki decks."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from hashlib import sha256
from datetime import datetime

import genanki

from multilang.services.azure_speech_adapter import AzureSpeechAdapter
import multilang.services.phoneme_deck as _phoneme_deck
from multilang.services.phoneme_deck import (
    PHONEME_FIELD_NAMES,
    PhonemeCard,
    PhonemeNote,
    build_phoneme_model,
    build_phoneme_note,
    phoneme_card_fields,
)
from multilang.settings import Settings

PHONEME_MODEL_ID = 1_602_300_601
PHONEME_DECK_ID = 1_602_300_602
PHONEME_NOTE_TYPE_NAME = "Multilang::Russian Phoneme"
DEFAULT_RUSSIAN_PHONEME_DECK_NAME = "Multilang Russian::Intro Phonemes"
POLISH_PHONEME_MODEL_ID = 1_602_300_603
POLISH_PHONEME_DECK_ID = 1_602_300_604
POLISH_PHONEME_NOTE_TYPE_NAME = "Multilang::Polish Phoneme"
DEFAULT_POLISH_PHONEME_DECK_NAME = "Multilang Polish::Intro Phonemes"
GREEK_PHONEME_MODEL_ID = 1_602_300_605
GREEK_PHONEME_DECK_ID = 1_602_300_606
GREEK_PHONEME_NOTE_TYPE_NAME = "Multilang::Greek Phoneme"
DEFAULT_GREEK_PHONEME_DECK_NAME = "Multilang Greek::Intro Phonemes"
GREEK_PHONEME_VOICE_ID = "el-GR-AthinaNeural"
GREEK_PHONEME_LOCALE = "el-GR"
POLISH_PHONEME_VOICE_ID = "pl-PL-AgnieszkaNeural"
POLISH_PHONEME_LOCALE = "pl-PL"
RUSSIAN_PHONEME_VOICE_ID = "ru-RU-DmitryNeural"
RUSSIAN_PHONEME_LOCALE = "ru-RU"


@dataclass(frozen=True)
class RussianPhonemeCard(PhonemeCard):
    """Compatibility name for the shared phoneme card shape."""

    language_code: str = "ru"

    @property
    def guid(self) -> str:
        payload = f"{self.language_code}-phoneme|{self.sort_index}|{self.letters}|{self.ipa}"
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


POLISH_PHONEME_CARDS: tuple[RussianPhonemeCard, ...] = (
    RussianPhonemeCard(1, "ą", "/ɔ̃/", "mąż", "marido", "To jest mój mąż.", "Este é meu marido.", language_code="pl"),
    RussianPhonemeCard(2, "ę", "/ɛ̃/", "ręka", "mão", "Moja ręka jest zimna.", "Minha mão está fria.", language_code="pl"),
    RussianPhonemeCard(3, "ł", "/w/", "mały", "pequeno", "To jest mały dom.", "Esta é uma casa pequena.", language_code="pl"),
    RussianPhonemeCard(4, "ń", "/ɲ/", "koń", "cavalo", "Koń biegnie szybko.", "O cavalo corre rápido.", language_code="pl"),
    RussianPhonemeCard(5, "ś", "/ɕ/", "środa", "quarta-feira", "Dzisiaj jest środa.", "Hoje é quarta-feira.", language_code="pl"),
    RussianPhonemeCard(6, "ź", "/ʑ/", "źle", "mal", "Czuję się źle.", "Estou me sentindo mal.", language_code="pl"),
    RussianPhonemeCard(7, "ż", "/ʐ/", "żona", "esposa", "Moja żona jest lekarzem.", "Minha esposa é médica.", language_code="pl"),
    RussianPhonemeCard(8, "ć", "/t͡ɕ/", "ćma", "mariposa", "Ćma leci do światła.", "A mariposa voa para a luz.", language_code="pl"),
    RussianPhonemeCard(9, "ó", "/u/", "mówić", "falar", "Lubię mówić po polsku.", "Eu gosto de falar polonês.", language_code="pl"),
    RussianPhonemeCard(10, "cz", "/t͡ʂ/", "czekolada", "chocolate", "Lubię czekoladę.", "Eu gosto de chocolate.", language_code="pl"),
    RussianPhonemeCard(11, "sz", "/ʂ/", "szkoła", "escola", "Idę do szkoły.", "Eu vou para a escola.", language_code="pl"),
    RussianPhonemeCard(12, "rz", "/ʐ/", "rzeka", "rio", "Rzeka jest długa.", "O rio é longo.", language_code="pl"),
    RussianPhonemeCard(13, "ch", "/x/", "chleb", "pão", "Jem chleb.", "Eu como pão.", language_code="pl"),
    RussianPhonemeCard(14, "dz", "/d͡z/", "dzwon", "sino", "Słyszę dzwon.", "Eu ouço um sino.", language_code="pl"),
    RussianPhonemeCard(15, "dź", "/d͡ʑ/", "dźwięk", "som", "Ten dźwięk jest głośny.", "Este som é alto.", language_code="pl"),
    RussianPhonemeCard(16, "dż", "/d͡ʐ/", "dżem", "geleia", "Jem chleb z dżemem.", "Eu como pão com geleia.", language_code="pl"),
)


GREEK_PHONEME_CARDS: tuple[RussianPhonemeCard, ...] = (
    RussianPhonemeCard(1, "α", "/a/", "αγάπη", "amor", "Η αγάπη είναι δυνατή.", "O amor é forte.", language_code="el"),
    RussianPhonemeCard(2, "ε, αι", "/e/", "ένα", "um", "Ένα παιδί γελά.", "Uma criança ri.", language_code="el"),
    RussianPhonemeCard(3, "η, ι, υ, ει, οι", "/i/", "ήλιος", "sol", "Ο ήλιος λάμπει.", "O sol brilha.", language_code="el"),
    RussianPhonemeCard(4, "ο, ω", "/o/", "ώρα", "hora", "Η ώρα περνά.", "A hora passa.", language_code="el"),
    RussianPhonemeCard(5, "ου", "/u/", "ουρανός", "céu", "Ο ουρανός είναι καθαρός.", "O céu está limpo.", language_code="el"),
    RussianPhonemeCard(6, "β", "/v/", "βιβλίο", "livro", "Το βιβλίο είναι νέο.", "O livro é novo.", language_code="el"),
    RussianPhonemeCard(7, "γ + α/ο/ου", "/ɣ/", "γάλα", "leite", "Το γάλα είναι κρύο.", "O leite está frio.", language_code="el"),
    RussianPhonemeCard(8, "γ + ε/ι", "/ʝ/", "γέλιο", "riso", "Το γέλιο βοηθά.", "O riso ajuda.", language_code="el"),
    RussianPhonemeCard(9, "δ", "/ð/", "δρόμος", "estrada", "Ο δρόμος είναι μακρύς.", "A estrada é longa.", language_code="el"),
    RussianPhonemeCard(10, "ζ", "/z/", "ζάχαρη", "açúcar", "Η ζάχαρη είναι γλυκιά.", "O açúcar é doce.", language_code="el"),
    RussianPhonemeCard(11, "θ", "/θ/", "θέμα", "tema", "Το θέμα είναι απλό.", "O tema é simples.", language_code="el"),
    RussianPhonemeCard(12, "κ", "/k/", "καφές", "café", "Ο καφές είναι ζεστός.", "O café está quente.", language_code="el"),
    RussianPhonemeCard(13, "λ", "/l/", "λεμόνι", "limão", "Το λεμόνι είναι ξινό.", "O limão é azedo.", language_code="el"),
    RussianPhonemeCard(14, "μ", "/m/", "μήλο", "maçã", "Το μήλο είναι κόκκινο.", "A maçã é vermelha.", language_code="el"),
    RussianPhonemeCard(15, "ν", "/n/", "νύχτα", "noite", "Η νύχτα είναι ήσυχη.", "A noite é tranquila.", language_code="el"),
    RussianPhonemeCard(16, "π", "/p/", "πόρτα", "porta", "Η πόρτα ανοίγει.", "A porta abre.", language_code="el"),
    RussianPhonemeCard(17, "ρ", "/r/", "νερό", "água", "Το νερό είναι κρύο.", "A água está fria.", language_code="el"),
    RussianPhonemeCard(18, "σ, ς", "/s/", "σπίτι", "casa", "Το σπίτι είναι μικρό.", "A casa é pequena.", language_code="el"),
    RussianPhonemeCard(19, "τ", "/t/", "τραπέζι", "mesa", "Το τραπέζι είναι μεγάλο.", "A mesa é grande.", language_code="el"),
    RussianPhonemeCard(20, "φ", "/f/", "φως", "luz", "Το φως λάμπει.", "A luz brilha.", language_code="el"),
    RussianPhonemeCard(21, "χ + α/ο/ου", "/x/", "χάρτης", "mapa", "Ο χάρτης είναι παλιός.", "O mapa é antigo.", language_code="el"),
    RussianPhonemeCard(22, "χ + ε/ι", "/ç/", "χέρι", "mão", "Το χέρι γράφει.", "A mão escreve.", language_code="el"),
    RussianPhonemeCard(23, "ψ", "/ps/", "ψάρι", "peixe", "Το ψάρι κολυμπά.", "O peixe nada.", language_code="el"),
    RussianPhonemeCard(24, "ξ", "/ks/", "ξύλο", "madeira", "Το ξύλο είναι στεγνό.", "A madeira está seca.", language_code="el"),
    RussianPhonemeCard(25, "μπ", "/b/", "μπαμπάς", "pai", "Ο μπαμπάς μιλά.", "O pai fala.", language_code="el"),
    RussianPhonemeCard(26, "ντ", "/d/", "ντομάτα", "tomate", "Η ντομάτα είναι κόκκινη.", "O tomate é vermelho.", language_code="el"),
    RussianPhonemeCard(27, "τσ", "/ts/", "τσάι", "chá", "Το τσάι είναι ζεστό.", "O chá está quente.", language_code="el"),
    RussianPhonemeCard(28, "τζ", "/dz/", "τζάμι", "vidro", "Το τζάμι λάμπει.", "O vidro brilha.", language_code="el"),
)


RussianPhonemeNote = PhonemeNote


@dataclass(frozen=True)
class RussianPhonemeDeckExportResult:
    output_path: Path
    card_count: int


def build_russian_phoneme_model() -> genanki.Model:
    return _build_phoneme_model(model_id=PHONEME_MODEL_ID, note_type_name=PHONEME_NOTE_TYPE_NAME)


def build_polish_phoneme_model() -> genanki.Model:
    return _build_phoneme_model(model_id=POLISH_PHONEME_MODEL_ID, note_type_name=POLISH_PHONEME_NOTE_TYPE_NAME)


def build_greek_phoneme_model() -> genanki.Model:
    return _build_phoneme_model(model_id=GREEK_PHONEME_MODEL_ID, note_type_name=GREEK_PHONEME_NOTE_TYPE_NAME)


def _build_phoneme_model(*, model_id: int, note_type_name: str) -> genanki.Model:
    return build_phoneme_model(model_id=model_id, note_type_name=note_type_name)


def build_russian_phoneme_note(
    card: RussianPhonemeCard,
    *,
    model: genanki.Model | None = None,
) -> genanki.Note:
    return _build_phoneme_note(card, model=model or build_russian_phoneme_model())


def build_polish_phoneme_note(
    card: RussianPhonemeCard,
    *,
    model: genanki.Model | None = None,
) -> genanki.Note:
    return _build_phoneme_note(card, model=model or build_polish_phoneme_model())


def build_greek_phoneme_note(
    card: RussianPhonemeCard,
    *,
    model: genanki.Model | None = None,
) -> genanki.Note:
    return _build_phoneme_note(card, model=model or build_greek_phoneme_model())


def _build_phoneme_note(card: RussianPhonemeCard, *, model: genanki.Model) -> genanki.Note:
    return build_phoneme_note(card, model=model)


def export_russian_phoneme_deck(
    *,
    output_path: Path,
    deck_name: str = DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
    cards: tuple[RussianPhonemeCard, ...] = RUSSIAN_PHONEME_CARDS,
    settings: Settings | None = None,
) -> RussianPhonemeDeckExportResult:
    return _export_phoneme_deck(
        output_path=output_path,
        deck_id=PHONEME_DECK_ID,
        deck_name=deck_name,
        model=build_russian_phoneme_model(),
        cards=cards,
        settings=settings,
        language_code="ru",
        voice_id=RUSSIAN_PHONEME_VOICE_ID,
        locale=RUSSIAN_PHONEME_LOCALE,
    )


def export_polish_phoneme_deck(
    *,
    output_path: Path,
    deck_name: str = DEFAULT_POLISH_PHONEME_DECK_NAME,
    cards: tuple[RussianPhonemeCard, ...] = POLISH_PHONEME_CARDS,
    settings: Settings | None = None,
) -> RussianPhonemeDeckExportResult:
    return _export_phoneme_deck(
        output_path=output_path,
        deck_id=POLISH_PHONEME_DECK_ID,
        deck_name=deck_name,
        model=build_polish_phoneme_model(),
        cards=cards,
        settings=settings,
        language_code="pl",
        voice_id=POLISH_PHONEME_VOICE_ID,
        locale=POLISH_PHONEME_LOCALE,
    )


def export_greek_phoneme_deck(
    *,
    output_path: Path,
    deck_name: str = DEFAULT_GREEK_PHONEME_DECK_NAME,
    cards: tuple[RussianPhonemeCard, ...] = GREEK_PHONEME_CARDS,
    settings: Settings | None = None,
) -> RussianPhonemeDeckExportResult:
    return _export_phoneme_deck(
        output_path=output_path,
        deck_id=GREEK_PHONEME_DECK_ID,
        deck_name=deck_name,
        model=build_greek_phoneme_model(),
        cards=cards,
        settings=settings,
        language_code="el",
        voice_id=GREEK_PHONEME_VOICE_ID,
        locale=GREEK_PHONEME_LOCALE,
    )


def _export_phoneme_deck(
    *,
    output_path: Path,
    deck_id: int,
    deck_name: str,
    model: genanki.Model,
    cards: tuple[RussianPhonemeCard, ...],
    settings: Settings | None,
    language_code: str,
    voice_id: str,
    locale: str,
) -> RussianPhonemeDeckExportResult:
    settings = settings or Settings()
    deck = genanki.Deck(deck_id, deck_name)

    # Synthesize audio for all cards
    synthesizer = AzureSpeechAdapter(settings)
    audio_dir = Path(settings.audio_storage_dir) / "phoneme" / datetime.now().strftime("%Y-%m-%d")
    media_files: list[Path] = []

    # Synthesize audio for each card
    for card in cards:
        card = card if card.language_code == language_code else replace(card, language_code=language_code)
        card_with_audio = _synthesize_card_audio(
            card=card,
            synthesizer=synthesizer,
            audio_dir=audio_dir,
            media_files=media_files,
            language_code=language_code,
            voice_id=voice_id,
            locale=locale,
        )
        deck.add_note(_build_phoneme_note(card_with_audio, model=model))

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
    language_code: str,
    voice_id: str,
    locale: str,
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
            language_code=language_code,
            voice_id=voice_id,
            locale=locale,
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
            language_code=language_code,
            voice_id=voice_id,
            locale=locale,
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
            language_code=language_code,
            voice_id=voice_id,
            locale=locale,
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
    language_code: str,
    voice_id: str,
    locale: str,
) -> Path | None:
    """Synthesize audio for phoneme deck text and return the file path."""
    # Generate unique filename based on content
    content_hash = sha256(text.encode("utf-8")).hexdigest()[:16]
    filename = f"{language_code}-{item_id}-{content_hash}.mp3"
    output_path = audio_dir / filename
    
    # Skip if already synthesized
    if output_path.exists():
        return output_path
    
    # Synthesize using Azure Speech
    response = synthesizer.synthesize(
        ssml_text=text,
        voice_id=voice_id,
        locale=locale,
        output_path=output_path,
        audio_format="audio-24khz-48kbitrate-mono-mp3",
    )
    
    # Verify synthesis was successful
    if response.storage_path and response.storage_path.exists():
        return response.storage_path
    
    return None


def _phoneme_card_fields(card: RussianPhonemeCard) -> list[str]:
    return phoneme_card_fields(card)


def _load_phoneme_template() -> dict[str, str]:
    return _phoneme_deck._load_phoneme_template()


__all__ = [
    "DEFAULT_GREEK_PHONEME_DECK_NAME",
    "DEFAULT_POLISH_PHONEME_DECK_NAME",
    "DEFAULT_RUSSIAN_PHONEME_DECK_NAME",
    "GREEK_PHONEME_CARDS",
    "GREEK_PHONEME_DECK_ID",
    "GREEK_PHONEME_LOCALE",
    "GREEK_PHONEME_MODEL_ID",
    "GREEK_PHONEME_NOTE_TYPE_NAME",
    "GREEK_PHONEME_VOICE_ID",
    "PHONEME_DECK_ID",
    "PHONEME_FIELD_NAMES",
    "PHONEME_MODEL_ID",
    "PHONEME_NOTE_TYPE_NAME",
    "POLISH_PHONEME_CARDS",
    "POLISH_PHONEME_DECK_ID",
    "POLISH_PHONEME_LOCALE",
    "POLISH_PHONEME_MODEL_ID",
    "POLISH_PHONEME_NOTE_TYPE_NAME",
    "POLISH_PHONEME_VOICE_ID",
    "RUSSIAN_PHONEME_CARDS",
    "RUSSIAN_PHONEME_LOCALE",
    "RUSSIAN_PHONEME_VOICE_ID",
    "RussianPhonemeCard",
    "RussianPhonemeDeckExportResult",
    "build_greek_phoneme_model",
    "build_greek_phoneme_note",
    "build_polish_phoneme_model",
    "build_polish_phoneme_note",
    "build_russian_phoneme_model",
    "build_russian_phoneme_note",
    "export_greek_phoneme_deck",
    "export_polish_phoneme_deck",
    "export_russian_phoneme_deck",
]
