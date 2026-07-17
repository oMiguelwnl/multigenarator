"""Fully self-generated Japanese kana deck.

Unlike ``japanese_kana_deck`` (which imports content from a user-provided
package), this module owns all of its content: kana glyphs, romaji, original
Portuguese mnemonics, and Azure ``ja-JP`` audio synthesized at export time. It
covers the full kana set for both scripts -- gojūon, dakuten/handakuten, and
yōon -- and reuses the shared kana note type and template.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from hashlib import sha256
from pathlib import Path

import genanki

from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.japanese_kana_deck import (
    KANA_HIRAGANA_DECK_ID,
    KANA_KATAKANA_DECK_ID,
    DEFAULT_KANA_DECK_NAME,
    KanaCard,
    KanaDeckExportResult,
    build_kana_model,
    build_kana_note,
)
from multilang.settings import Settings

KANA_VOICE_ID = "ja-JP-NanamiNeural"
KANA_LOCALE = "ja-JP"

# Base syllabary: (romaji, hiragana, katakana, hiragana_mnemonic, katakana_mnemonic)
_GOJUON: tuple[tuple[str, str, str, str, str], ...] = (
    ("a", "あ", "ア", "Um 'A' com uma alça; ache o A escondido nele.", "Um 'A' anguloso, como um telhado cortado."),
    ("i", "い", "イ", "Dois traços em pé, como duas enguias lado a lado.", "Uma pessoa de perfil em pé, som 'i'."),
    ("u", "う", "ウ", "Perfil de alguém dizendo 'uuu'.", "Um chapéu pontudo com uma perna, 'u'."),
    ("e", "え", "エ", "Alguém curvado correndo, som 'e'.", "Duas linhas horizontais e uma vertical."),
    ("o", "お", "オ", "Como o あ com um laço a mais, boca em 'o'.", "Um alvo com uma barra, boca aberta 'o'."),
    ("ka", "か", "カ", "Uma faca cortando o ar, 'ka'.", "Metade de uma faca, traço firme 'ka'."),
    ("ki", "き", "キ", "Uma chave (key) pendurada, 'ki'.", "Uma chave simplificada, haste com dois traços."),
    ("ku", "く", "ク", "Um bico de pássaro aberto, 'ku'.", "Um bico anguloso, 'ku'."),
    ("ke", "け", "ケ", "Um saca-rolhas ao lado de um traço, 'ke'.", "Um traço cortado, som 'ke'."),
    ("ko", "こ", "コ", "Duas linhas curtas, como duas cordas.", "Um canto reto tipo 'C', 'ko'."),
    ("sa", "さ", "サ", "Parece o き sem um traço, 'sa'.", "Três traços se cruzando, 'sa'."),
    ("shi", "し", "シ", "Um anzol curvo, 'shi'.", "Duas gotas e uma linha subindo, 'shi'."),
    ("su", "す", "ス", "Um laço com cauda, como um pião, 'su'.", "Duas linhas cruzadas, 'su'."),
    ("se", "せ", "セ", "Um traço cortado por uma curva, 'se'.", "Uma foice pequena, 'se'."),
    ("so", "そ", "ソ", "Um ziguezague de costura, 'so'.", "Duas gotas inclinadas, 'so'."),
    ("ta", "た", "タ", "Um 't' com dois pontos ao lado, 'ta'.", "Um gancho com um traço, 'ta'."),
    ("chi", "ち", "チ", "Um número 5 espelhado, 'chi'.", "Um sinal de mais alongado, 'chi'."),
    ("tsu", "つ", "ツ", "Uma onda rasa, 'tsu'.", "Três gotas (tsunami), 'tsu'."),
    ("te", "て", "テ", "Uma mão estendida (te = mão), 'te'.", "Três traços empilhados, 'te'."),
    ("to", "と", "ト", "Um prego com uma gota, 'to'.", "Um 'T' com um traço, 'to'."),
    ("na", "な", "ナ", "Um nó amarrado, 'na'.", "Uma cruz com gancho, 'na'."),
    ("ni", "に", "ニ", "Um traço e duas linhas, joelhos dobrados.", "Duas linhas horizontais, parece '2', 'ni'."),
    ("nu", "ぬ", "ヌ", "Um macarrão (noodle) enrolado, 'nu'.", "Um 'X' com cauda, 'nu'."),
    ("ne", "ね", "ネ", "Um gato (neko) com rabo enrolado, 'ne'.", "Uma cruz com laço, 'ne'."),
    ("no", "の", "ノ", "Um redemoinho, 'no'.", "Um único traço diagonal, 'no'."),
    ("ha", "は", "ハ", "Um 'h' com um traço extra, 'ha'.", "Duas pernas abertas rindo 'ha ha'."),
    ("hi", "ひ", "ヒ", "Um sorriso largo, 'hi!'.", "Um 'E' sem a barra do meio, 'hi'."),
    ("fu", "ふ", "フ", "Uma montanha (Fuji) com flocos, 'fu'.", "Um único gancho no topo, 'fu'."),
    ("he", "へ", "ヘ", "Um telhado simples, 'he'.", "O mesmo telhado anguloso, 'he'."),
    ("ho", "ほ", "ホ", "Como o は com um traço extra, 'ho'.", "Uma árvore com galhos, 'ho'."),
    ("ma", "ま", "マ", "Um pião com dois laços, 'ma'.", "Um gancho com um traço, 'ma'."),
    ("mi", "み", "ミ", "Um '21' enrolado, 'mi'.", "Três traços, como '3' deitado, 'mi'."),
    ("mu", "む", "ム", "Uma vaca dizendo 'muuu'.", "Um canto simples, 'mu'."),
    ("me", "め", "メ", "Um olho (me = olho) com cílio, 'me'.", "Um 'X' inclinado, 'me'."),
    ("mo", "も", "モ", "Um anzol com dois traços, 'mo'.", "Um anzol com uma barra, 'mo'."),
    ("ya", "や", "ヤ", "Um estilingue em 'Y', 'ya'.", "Um 'Y' anguloso, 'ya'."),
    ("yu", "ゆ", "ユ", "Um peixe curvo, 'yu'.", "Um canto em 'U' deitado, 'yu'."),
    ("yo", "よ", "ヨ", "Um anzol com um traço, 'yo'.", "Um 'E' de costas, 'yo'."),
    ("ra", "ら", "ラ", "Um coelho pulando, 'ra'.", "Um traço com gancho, 'ra'."),
    ("ri", "り", "リ", "Duas linhas curvas paralelas, 'ri'.", "Duas linhas retas, 'ri'."),
    ("ru", "る", "ル", "Um laço com nó embaixo, 'ru'.", "Duas perninhas curtas, 'ru'."),
    ("re", "れ", "レ", "Como o ru sem o laço, 're'.", "Um único bico, 're'."),
    ("ro", "ろ", "ロ", "Como o る sem o laço, 'ro'.", "Um quadrado (boca), 'ro'."),
    ("wa", "わ", "ワ", "Parecido com o ね, com laço, 'wa'.", "Um canto aberto, 'wa'."),
    ("wo", "を", "ヲ", "Um dançarino chutando; partícula 'wo/o'.", "Três traços; partícula 'wo' (rara)."),
    ("n", "ん", "ン", "Um 'h' minúsculo relaxado, som 'n'.", "Duas gotas; parece シ, mas é 'n'."),
)

# Dakuten / handakuten: (romaji, hiragana, katakana, base_romaji)
_DAKUTEN: tuple[tuple[str, str, str, str], ...] = (
    ("ga", "が", "ガ", "ka"), ("gi", "ぎ", "ギ", "ki"), ("gu", "ぐ", "グ", "ku"), ("ge", "げ", "ゲ", "ke"), ("go", "ご", "ゴ", "ko"),
    ("za", "ざ", "ザ", "sa"), ("ji", "じ", "ジ", "shi"), ("zu", "ず", "ズ", "su"), ("ze", "ぜ", "ゼ", "se"), ("zo", "ぞ", "ゾ", "so"),
    ("da", "だ", "ダ", "ta"), ("dji", "ぢ", "ヂ", "chi"), ("dzu", "づ", "ヅ", "tsu"), ("de", "で", "デ", "te"), ("do", "ど", "ド", "to"),
    ("ba", "ば", "バ", "ha"), ("bi", "び", "ビ", "hi"), ("bu", "ぶ", "ブ", "fu"), ("be", "べ", "ベ", "he"), ("bo", "ぼ", "ボ", "ho"),
    ("pa", "ぱ", "パ", "ha"), ("pi", "ぴ", "ピ", "hi"), ("pu", "ぷ", "プ", "fu"), ("pe", "ぺ", "ペ", "he"), ("po", "ぽ", "ポ", "ho"),
)

# Yōon: (romaji, hiragana, katakana, base_romaji)
_YOON: tuple[tuple[str, str, str, str], ...] = (
    ("kya", "きゃ", "キャ", "ki"), ("kyu", "きゅ", "キュ", "ki"), ("kyo", "きょ", "キョ", "ki"),
    ("sha", "しゃ", "シャ", "shi"), ("shu", "しゅ", "シュ", "shi"), ("sho", "しょ", "ショ", "shi"),
    ("cha", "ちゃ", "チャ", "chi"), ("chu", "ちゅ", "チュ", "chi"), ("cho", "ちょ", "チョ", "chi"),
    ("nya", "にゃ", "ニャ", "ni"), ("nyu", "にゅ", "ニュ", "ni"), ("nyo", "にょ", "ニョ", "ni"),
    ("hya", "ひゃ", "ヒャ", "hi"), ("hyu", "ひゅ", "ヒュ", "hi"), ("hyo", "ひょ", "ヒョ", "hi"),
    ("mya", "みゃ", "ミャ", "mi"), ("myu", "みゅ", "ミュ", "mi"), ("myo", "みょ", "ミョ", "mi"),
    ("rya", "りゃ", "リャ", "ri"), ("ryu", "りゅ", "リュ", "ri"), ("ryo", "りょ", "リョ", "ri"),
    ("gya", "ぎゃ", "ギャ", "gi"), ("gyu", "ぎゅ", "ギュ", "gi"), ("gyo", "ぎょ", "ギョ", "gi"),
    ("ja", "じゃ", "ジャ", "ji"), ("ju", "じゅ", "ジュ", "ji"), ("jo", "じょ", "ジョ", "ji"),
    ("bya", "びゃ", "ビャ", "bi"), ("byu", "びゅ", "ビュ", "bi"), ("byo", "びょ", "ビョ", "bi"),
    ("pya", "ぴゃ", "ピャ", "pi"), ("pyu", "ぴゅ", "ピュ", "pi"), ("pyo", "ぴょ", "ピョ", "pi"),
)

# Base glyphs for building derived rows. Yōon can derive from a dakuten base
# (e.g. gya ← ぎ, ja ← じ), so include both the gojūon and dakuten glyphs.
_BASE_GLYPHS = {romaji: (hira, kata) for romaji, hira, kata, *_ in _GOJUON}
_BASE_GLYPHS.update({romaji: (hira, kata) for romaji, hira, kata, _base in _DAKUTEN})


def _build_generated_cards() -> tuple[KanaCard, ...]:
    cards: list[KanaCard] = []
    for script_index, script in enumerate(("Hiragana", "Katakana")):
        use_hira = script == "Hiragana"
        order = 0

        for romaji, hira, kata, hira_mn, kata_mn in _GOJUON:
            order += 1
            cards.append(
                KanaCard(
                    sort_index=order,
                    script=script,
                    kana=hira if use_hira else kata,
                    romaji=romaji,
                    mnemonic=hira_mn if use_hira else kata_mn,
                )
            )

        for romaji, hira, kata, base in _DAKUTEN:
            order += 1
            base_glyph = _BASE_GLYPHS[base][0 if use_hira else 1]
            mark = "handakuten (゜)" if romaji.startswith("p") else "dakuten (゛)"
            cards.append(
                KanaCard(
                    sort_index=order,
                    script=script,
                    kana=hira if use_hira else kata,
                    romaji=romaji,
                    mnemonic=f"{base_glyph} + {mark} → som '{romaji}'.",
                )
            )

        for romaji, hira, kata, base in _YOON:
            order += 1
            base_glyph = _BASE_GLYPHS[base][0 if use_hira else 1]
            # The contracted (small) kana is chosen by the final vowel, so
            # rows like "sha"/"chu"/"jo" still resolve to ゃ/ゅ/ょ correctly.
            small_map = {
                "a": ("ゃ", "ャ"),
                "u": ("ゅ", "ュ"),
                "o": ("ょ", "ョ"),
            }
            small_glyph = small_map[romaji[-1]][0 if use_hira else 1]
            cards.append(
                KanaCard(
                    sort_index=order,
                    script=script,
                    kana=hira if use_hira else kata,
                    romaji=romaji,
                    mnemonic=f"{base_glyph} + {small_glyph} pequeno → '{romaji}'.",
                )
            )

    return tuple(cards)


GENERATED_KANA_CARDS: tuple[KanaCard, ...] = _build_generated_cards()


def export_generated_kana_deck(
    *,
    output_path: Path,
    deck_name: str = DEFAULT_KANA_DECK_NAME,
    cards: tuple[KanaCard, ...] = GENERATED_KANA_CARDS,
    settings: Settings | None = None,
) -> KanaDeckExportResult:
    """Export a fully self-generated kana deck with Azure ja-JP audio."""

    settings = settings or Settings()
    model = build_kana_model()
    synthesizer = AzureSpeechAdapter(settings)
    audio_dir = Path(settings.audio_storage_dir) / "kana" / datetime.now().strftime("%Y-%m-%d")
    media_files: list[Path] = []

    hiragana_deck = genanki.Deck(KANA_HIRAGANA_DECK_ID, f"{deck_name}::Hiragana")
    katakana_deck = genanki.Deck(KANA_KATAKANA_DECK_ID, f"{deck_name}::Katakana")

    hiragana_count = 0
    katakana_count = 0
    for card in cards:
        card = _synthesize_card_audio(
            card=card, synthesizer=synthesizer, audio_dir=audio_dir, media_files=media_files
        )
        note = build_kana_note(card, model=model)
        if card.script == "Katakana":
            katakana_deck.add_note(note)
            katakana_count += 1
        else:
            hiragana_deck.add_note(note)
            hiragana_count += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package([hiragana_deck, katakana_deck])
    package.media_files = [str(path) for path in media_files]
    package.write_to_file(str(output_path))
    return KanaDeckExportResult(
        output_path=output_path,
        card_count=len(cards),
        hiragana_count=hiragana_count,
        katakana_count=katakana_count,
    )


def _synthesize_card_audio(
    *,
    card: KanaCard,
    synthesizer: AzureSpeechAdapter,
    audio_dir: Path,
    media_files: list[Path],
) -> KanaCard:
    try:
        content_hash = sha256(f"{card.script}-{card.kana}".encode("utf-8")).hexdigest()[:16]
        filename = f"kana-{card.romaji}-{content_hash}.mp3"
        output_path = audio_dir / filename
        if not output_path.exists():
            response = synthesizer.synthesize(
                ssml_text=card.kana,
                voice_id=KANA_VOICE_ID,
                locale=KANA_LOCALE,
                output_path=output_path,
                audio_format="audio-24khz-48kbitrate-mono-mp3",
            )
            if not (response.storage_path and response.storage_path.exists()):
                return card
        media_files.append(output_path)
        return replace(card, audio=f"[sound:{output_path.name}]")
    except Exception:
        return card


__all__ = [
    "GENERATED_KANA_CARDS",
    "KANA_LOCALE",
    "KANA_VOICE_ID",
    "export_generated_kana_deck",
]
