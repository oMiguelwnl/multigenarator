# Quick Task 026 Plan: Japanese Furigana Generation

## Objective

Add Japanese morphology dependencies and generate Anki-native furigana for dynamic Japanese export rows instead of exporting raw reading/furigana fallbacks.

Approach context: User asked to add the recommended Japanese libraries (`fugashi`, `unidic-lite`) and implement the previously described furigana stage. Earlier quick tasks added Japanese runtime registration, frequency assets, validation, and export routing. This task focuses only on contextual readings/furigana at export assembly.

No UI proof rationale: This task changes backend text processing/export data and tests only; it has no rendered UI surface.

## Task 1: Add Japanese Morphology Dependencies

<files>
- `pyproject.toml`
- `uv.lock`
</files>

<action>
- Add `fugashi>=1.3,<2.0` and `unidic-lite>=1.0,<2.0` to project dependencies.
- Refresh `uv.lock` through the package manager.
</action>

<done>
- `uv run python -c "import fugashi, unidic_lite"` succeeds.
</done>

<verify>
- `uv run python -c "import fugashi, unidic_lite"`
</verify>

## Task 2: Implement Japanese Furigana Service

<files>
- `src/multilang/services/japanese_furigana.py`
- `tests/services/test_japanese_furigana.py`
</files>

<action>
- Create a small service that uses `fugashi.Tagger` with `unidic_lite.DICDIR`.
- Convert UniDic katakana readings to hiragana.
- Format token surfaces as Anki furigana (`漢字[かな]`) only when the surface contains kanji and a reliable reading exists.
- Preserve kana-only tokens and punctuation as-is.
- Add focused tests for `学校に行く。`, `父親は今年50歳になる。`, kana-only text, and katakana-to-hiragana conversion.
</action>

<done>
- The service returns bracketed readings for kanji tokens and leaves kana-only text unchanged.
- Missing/failed readings fail closed through a clear exception for kanji-bearing text.
</done>

<verify>
- `uv run pytest tests/services/test_japanese_furigana.py -q`
</verify>

## Task 3: Integrate Furigana Into Japanese Export Assembly

<files>
- `src/multilang/domain/exporting.py`
- `src/multilang/services/assemble_export_cards.py`
- `tests/services/test_assemble_export_cards.py`
- `tests/services/test_export_anki_package.py`
</files>

<action>
- Add optional `word_reading` and `sentence_furigana` export row values for Japanese fields.
- During Japanese frequency assembly, generate `Word Reading` from the display word and `Sentence Furigana` from the accepted sentence.
- Keep non-Japanese export behavior unchanged, including IPA requirement.
- Add/adjust tests so Japanese assembly emits `学校[がっこう]` and `学校[がっこう]に行[い]く。` instead of raw fallbacks.
- Adjust the Japanese note-field mapping test so APKG notes preserve generated reading/furigana values.
</action>

<done>
- Dynamic Japanese export rows include generated Anki furigana in Japanese-specific fields.
- Non-Japanese assembly tests still pass.
</done>

<verify>
- `uv run pytest tests/services/test_japanese_furigana.py tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_export_anki_package.py::test_build_multilang_note_maps_japanese_frequency_fields -q`
</verify>
