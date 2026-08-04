"""Deterministic Japanese frequency Anki deck.

Adapts two donated Japanese frequency note types into the project's isolated
deck pattern (mirroring the phoneme decks): the Portuguese "FRPG+" sentence
model plus the JP1K-style furigana reveal toggle. The deck ships curated,
sentence-mined example cards with Portuguese translations and renders furigana
through Anki's built-in ``{{furigana:...}}`` filter.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from functools import cached_property
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
import re

import genanki

from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.japanese_romaji import romanize_japanese
from multilang.settings import Settings

JAPANESE_MODEL_ID = 1_762_800_701
JAPANESE_DECK_ID = 1_762_800_702
JAPANESE_NOTE_TYPE_NAME = "Multilang::Japanese Card"
DEFAULT_JAPANESE_DECK_NAME = "Multilang Japanese::Frequency"
JAPANESE_VOICE_ID = "ja-JP-NanamiNeural"
JAPANESE_LOCALE = "ja-JP"
JAPANESE_FIELD_NAMES = (
    "SortIndex",
    "Target Word",
    "Word Reading",
    "Word Romaji",
    "Definition",
    "Sentence",
    "Sentence Furigana",
    "Sentence Romaji",
    "Sentence Translation",
    "word_audio",
    "sentence_audio",
    "Image",
)
_TEMPLATE_SECTION_RE = re.compile(
    r"## Front Template\s+```html\n(?P<front>.*?)```.*?"
    r"## Back Template\s+```html\n(?P<back>.*?)```.*?"
    r"## Styling \(CSS\)\s+```css\n(?P<css>.*?)```",
    re.DOTALL,
)


@dataclass(frozen=True)
class JapaneseCard:
    sort_index: int
    target_word: str
    word_reading: str
    definition: str
    sentence: str
    sentence_furigana: str
    sentence_translation: str
    word_audio: str = ""
    sentence_audio: str = ""
    language_code: str = "ja"

    @cached_property
    def word_romaji(self) -> str:
        return romanize_japanese(self.target_word)

    @cached_property
    def sentence_romaji(self) -> str:
        return romanize_japanese(self.sentence)

    @property
    def guid(self) -> str:
        payload = f"{self.language_code}-frequency|{self.sort_index}|{self.target_word}|{self.sentence}"
        return sha256(payload.encode("utf-8")).hexdigest()[:32]


JAPANESE_FREQUENCY_CARDS: tuple[JapaneseCard, ...] = (
    JapaneseCard(1, "何", "何[なに]", "o que", "何しているの？", "何[なに]しているの？", "O que você está fazendo?"),
    JapaneseCard(2, "父親", "父親[ちちおや]", "pai", "父親は今年50歳になる。", "父親[ちちおや]は 今年[ことし]50 歳[さい]になる。", "Meu pai faz 50 anos este ano."),
    JapaneseCard(3, "水", "水[みず]", "água", "水を飲みたい。", "水[みず]を 飲[の]みたい。", "Quero beber água."),
    JapaneseCard(4, "人", "人[ひと]", "pessoa", "あの人は先生です。", "あの 人[ひと]は 先生[せんせい]です。", "Aquela pessoa é professor."),
    JapaneseCard(5, "時間", "時間[じかん]", "tempo, hora", "時間がありません。", "時間[じかん]がありません。", "Não tenho tempo."),
    JapaneseCard(6, "食べる", "食[た]べる", "comer", "毎日ご飯を食べる。", "毎日[まいにち]ご 飯[はん]を 食[た]べる。", "Como arroz todos os dias."),
    JapaneseCard(7, "行く", "行[い]く", "ir", "学校に行く。", "学校[がっこう]に 行[い]く。", "Vou para a escola."),
    JapaneseCard(8, "見る", "見[み]る", "ver, assistir", "映画を見る。", "映画[えいが]を 見[み]る。", "Assisto a um filme."),
    JapaneseCard(9, "大きい", "大[おお]きい", "grande", "大きい家に住む。", "大[おお]きい 家[いえ]に 住[す]む。", "Moro numa casa grande."),
    JapaneseCard(10, "今日", "今日[きょう]", "hoje", "今日は寒いです。", "今日[きょう]は 寒[さむ]いです。", "Hoje está frio."),
    JapaneseCard(11, "学校", "学校[がっこう]", "escola", "学校は近いです。", "学校[がっこう]は 近[ちか]いです。", "A escola é perto."),
    JapaneseCard(12, "友達", "友達[ともだち]", "amigo", "友達と話す。", "友達[ともだち]と 話[はな]す。", "Converso com um amigo."),
)


class JapaneseNote(genanki.Note):
    @property
    def guid(self) -> str:
        return self._multilang_guid  # type: ignore[attr-defined]


@dataclass(frozen=True)
class JapaneseDeckExportResult:
    output_path: Path
    card_count: int


def build_japanese_model() -> genanki.Model:
    template = _load_japanese_template()
    return genanki.Model(
        JAPANESE_MODEL_ID,
        JAPANESE_NOTE_TYPE_NAME,
        fields=[{"name": field_name} for field_name in JAPANESE_FIELD_NAMES],
        templates=[
            {
                "name": "Japanese Vocab",
                "qfmt": template["front"],
                "afmt": template["back"],
            }
        ],
        css=template["css"],
    )


def build_japanese_note(
    card: JapaneseCard,
    *,
    model: genanki.Model | None = None,
) -> genanki.Note:
    note = JapaneseNote(
        model=model or build_japanese_model(),
        fields=_japanese_card_fields(card),
    )
    note._multilang_guid = card.guid  # type: ignore[attr-defined]
    return note


def export_japanese_frequency_deck(
    *,
    output_path: Path,
    deck_name: str = DEFAULT_JAPANESE_DECK_NAME,
    cards: tuple[JapaneseCard, ...] = JAPANESE_FREQUENCY_CARDS,
    settings: Settings | None = None,
) -> JapaneseDeckExportResult:
    settings = settings or Settings()
    model = build_japanese_model()
    deck = genanki.Deck(JAPANESE_DECK_ID, deck_name)

    synthesizer = AzureSpeechAdapter(settings)
    audio_dir = Path(settings.audio_storage_dir) / "japanese" / datetime.now().strftime("%Y-%m-%d")
    media_files: list[Path] = []

    for card in cards:
        card = card if card.language_code == "ja" else replace(card, language_code="ja")
        card_with_audio = _synthesize_card_audio(
            card=card,
            synthesizer=synthesizer,
            audio_dir=audio_dir,
            media_files=media_files,
        )
        deck.add_note(build_japanese_note(card_with_audio, model=model))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = [str(path) for path in media_files]
    package.write_to_file(str(output_path))
    return JapaneseDeckExportResult(output_path=output_path, card_count=len(cards))


def _synthesize_card_audio(
    *,
    card: JapaneseCard,
    synthesizer: AzureSpeechAdapter,
    audio_dir: Path,
    media_files: list[Path],
) -> JapaneseCard:
    """Synthesize word and sentence audio, skipping silently on failure."""

    word_audio = ""
    sentence_audio = ""

    try:
        word_audio_path = _synthesize_text(
            text=card.target_word,
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
        sentence_audio_path = _synthesize_text(
            text=card.sentence,
            item_id=f"sentence-{card.sort_index}",
            synthesizer=synthesizer,
            audio_dir=audio_dir,
        )
        if sentence_audio_path:
            sentence_audio = f"[sound:{sentence_audio_path.name}]"
            media_files.append(sentence_audio_path)
    except Exception:
        pass

    return replace(card, word_audio=word_audio, sentence_audio=sentence_audio)


def _synthesize_text(
    *,
    text: str,
    item_id: str,
    synthesizer: AzureSpeechAdapter,
    audio_dir: Path,
) -> Path | None:
    content_hash = sha256(text.encode("utf-8")).hexdigest()[:16]
    filename = f"ja-{item_id}-{content_hash}.mp3"
    output_path = audio_dir / filename

    if output_path.exists():
        return output_path

    response = synthesizer.synthesize(
        ssml_text=text,
        voice_id=JAPANESE_VOICE_ID,
        locale=JAPANESE_LOCALE,
        output_path=output_path,
        audio_format="audio-24khz-48kbitrate-mono-mp3",
    )

    if response.storage_path and response.storage_path.exists():
        return response.storage_path

    return None


def _japanese_card_fields(card: JapaneseCard) -> list[str]:
    values = {
        "SortIndex": str(card.sort_index),
        "Target Word": card.target_word,
        "Word Reading": card.word_reading,
        "Word Romaji": card.word_romaji,
        "Definition": card.definition,
        "Sentence": card.sentence,
        "Sentence Furigana": card.sentence_furigana,
        "Sentence Romaji": card.sentence_romaji,
        "Sentence Translation": card.sentence_translation,
        "word_audio": card.word_audio,
        "sentence_audio": card.sentence_audio,
        "Image": "",
    }
    return [values[field_name] for field_name in JAPANESE_FIELD_NAMES]


def _load_japanese_template() -> dict[str, str]:
    template_path = files("multilang").joinpath("templates", "japanese_card.md")
    content = template_path.read_text(encoding="utf-8")
    match = _TEMPLATE_SECTION_RE.search(content)
    if match is None:
        raise ValueError(f"unable to parse Japanese template from {template_path}")
    return {name: match.group(name).strip() for name in ("front", "back", "css")}


__all__ = [
    "DEFAULT_JAPANESE_DECK_NAME",
    "JAPANESE_DECK_ID",
    "JAPANESE_FIELD_NAMES",
    "JAPANESE_FREQUENCY_CARDS",
    "JAPANESE_LOCALE",
    "JAPANESE_MODEL_ID",
    "JAPANESE_NOTE_TYPE_NAME",
    "JAPANESE_VOICE_ID",
    "JapaneseCard",
    "JapaneseDeckExportResult",
    "JapaneseNote",
    "build_japanese_model",
    "build_japanese_note",
    "export_japanese_frequency_deck",
]
