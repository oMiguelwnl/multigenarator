# Quick Task 024 Plan: Japanese Generation And Validation Support

## Objective

Add the remaining non-export runtime support needed for Japanese text generation: local/offline templates, fallback service maps, and Japanese-aware validation for no-space sentences.

Approach context: This is stage 3 of the split Japanese pipeline work. Stages 1 and 2 registered Japanese defaults/provider text routing and added frequency assets. This task avoids export field/template routing, which remains a separate follow-up.

No UI proof rationale: This task changes backend service maps, text validation behavior, and focused tests only; it has no rendered UI surface.

## Task 1: Add Japanese Runtime Generation/Fallback Maps

<files>
- `src/multilang/services/provider_pronunciation_adapters.py`
- `src/multilang/services/language_identifier.py`
- `src/multilang/services/highlight_candidate_extraction.py`
- `src/multilang/services/tatoeba_sentence_source.py`
- `src/multilang/services/local_text_adapter.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `src/multilang/services/part_of_speech.py`
- `tests/services/test_local_text_adapter.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`
</files>

<action>
- Add Japanese names/codes to pronunciation prompt naming, corpus language-id, highlight stopwords, Tatoeba API routing (`jpn`), local sentence/translation templates, local definition labels, and fallback TTS maps.
- Add high-confidence Japanese function-word POS labels for common particles/pronouns/conjunctions.
- Add focused tests for local Japanese generation and fallback TTS voice selection.
</action>

<done>
- Local generation can create a Japanese sentence containing the target term.
- Tatoeba and fallback TTS adapters can resolve Japanese without key errors.
- Japanese closed-class words can infer POS labels where covered.
</done>

<verify>
- `uv run pytest tests/services/test_local_text_adapter.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py -q`
</verify>

## Task 2: Add Japanese-Aware Text Validation

<files>
- `src/multilang/services/text_validation.py`
- `tests/services/test_text_validation.py`
</files>

<action>
- Add Japanese script detection for hiragana, katakana, and CJK ideographs.
- Let Japanese target-form validation use substring matching because normal Japanese sentences do not need spaces around words.
- Let Japanese sentence-length validation use character count rather than whitespace token count.
- Add tests proving a natural Japanese sentence without spaces passes and a non-Japanese sentence for `target_language="ja"` fails language validation.
</action>

<done>
- Natural no-space Japanese sentences are not rejected solely for tokenization reasons.
- Wrong-script Japanese-target sentences still fail language validation.
</done>

<verify>
- `uv run pytest tests/services/test_text_validation.py::test_validation_accepts_no_space_japanese_sentence tests/services/test_text_validation.py::test_validation_rejects_non_japanese_sentence_for_japanese_target -q`
</verify>

## Deferred Follow-Up Task

- Stage 4: Japanese export routing to `Multilang::Japanese Card`.
