# Phase 15 Phonetics Template Evidence

## Verification Command

```bash
uv run pytest tests/services/test_russian_phoneme_deck.py tests/integration/test_russian_phoneme_template_refresh_flow.py -q
```

## Result

PASS — `5 passed in 0.54s` after final verification.

## Final Field Contract

```python
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
```

## Forbidden Fields and References Checked

Automated service and integration tests assert the refreshed model/template does not reference these legacy or unused fields:

- `Notes`
- `is_priming`
- `is_sentence`
- `Definitions`
- `image`
- `IPA`
- `Exemple Sentence`
- `Translation`

`FrontSide` is the only allowed non-field Anki helper in the refreshed back template.

## APKG Smoke Result

The integration test calls `export_russian_phoneme_deck()` with a temporary APKG path, verifies the package contains `collection.anki2`, and confirms the reported card count equals the full static Russian phoneme card set.

## Checkpoint-Backed Visual Behavior

After human checkpoint clarification, the literal text `Sentence Translation` is not shown on the front. The refreshed template follows the v1 reveal pattern: the front carries the `Sentence Translation` field in a hidden `#sentenceTranslation` element, and the back uses `{{FrontSide}}` plus a small script to reveal that existing hidden content. Formatting and colors are inspired by `fonetico.md`'s neutral/purple palette, including the audio button, hint, divider, card surface, header, and sentence translation variables.

The user approved `.multilang/tmp/russian-phonemes-refresh-check-v3.apkg` at the human verification checkpoint: front hides both the literal label and actual translation, back reveals the actual translation, and styling follows the supplied neutral/purple phonetics reference.

## Audio Preservation Evidence

A synthetic `RussianPhonemeCard` carrying `[sound:letter.mp3]`, `[sound:word.mp3]`, and `[sound:sentence.mp3]` is exported into the expected `letter_audio`, `word_audio`, and `sentence_audio` positions. The front template contains all three audio field references, preserving existing Russian phonetics audio rendering behavior.

## Template Isolation

`CARD_TEMPLATE.md` and `HIGHLIGHT_CARD_TEMPLATE.md` were intentionally not modified. Phase 15 changes are isolated to the Russian phonetics-only model/template path.

## Privacy and Safety Notes

This evidence uses only synthetic test paths and static Russian phoneme fixture content. It does not include real audio files, private paths, WebDAV data, raw highlights, credentials, or secrets.
