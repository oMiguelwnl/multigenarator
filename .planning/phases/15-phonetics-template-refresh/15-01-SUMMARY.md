---
phase: 15-phonetics-template-refresh
plan: 01
subsystem: russian-phoneme-deck
tags: [phonetics, anki-template, russian, audio]
requires: []
provides: [PHON-01, PHON-02, PHON-03]
affects:
  - templates/russian_phoneme_card.md
  - src/multilang/services/russian_phoneme_deck.py
  - tests/services/test_russian_phoneme_deck.py
tech_stack:
  added: []
  patterns: [genanki-template-contract, focused-pytest-regression]
key_files:
  created: []
  modified:
    - templates/russian_phoneme_card.md
    - src/multilang/services/russian_phoneme_deck.py
    - tests/services/test_russian_phoneme_deck.py
decisions:
  - Keep sort_index internal for deterministic ordering and GUIDs while removing it from exported Anki fields.
  - Map the existing Russian phoneme IPA value into the user-facing Sound field instead of exporting an IPA field.
metrics:
  duration: 12min
  completed: 2026-05-07T14:17:00Z
  tasks: 2
  files: 3
---

# Phase 15 Plan 01: Phonetics Template Refresh Summary

Refreshed the Russian phonetics-only Anki field contract and template so fronts use the supplied phonetics layout, backs reveal sentence translations, and letter/word/sentence audio slots remain renderable.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Lock the refreshed phonetics field and reference contract | d18b448 | `tests/services/test_russian_phoneme_deck.py` |
| 2 | Implement the refreshed phonetics model and template | 2b6c1fa | `templates/russian_phoneme_card.md`, `src/multilang/services/russian_phoneme_deck.py`, `tests/services/test_russian_phoneme_deck.py` |

## Verification

- `uv run pytest tests/services/test_russian_phoneme_deck.py::test_build_russian_phoneme_model_uses_intro_template -q` failed during RED as expected before implementation.
- `uv run pytest tests/services/test_russian_phoneme_deck.py -q` passed after implementation: `3 passed`.
- `CARD_TEMPLATE.md` and `HIGHLIGHT_CARD_TEMPLATE.md` were not modified.

## Changes Made

- Replaced `PHONEME_FIELD_NAMES` with the refreshed nine-field contract: `Spellings`, `Sound`, `letter_audio`, `Example Word`, `word_audio`, `Word Translation`, `Example Sentence`, `sentence_audio`, `Sentence Translation`.
- Preserved `sort_index` only as internal ordering/GUID data.
- Added explicit `letter_audio`, `word_audio`, and `sentence_audio` dataclass values and mapped them to same-named exported fields.
- Rewrote the Russian phoneme template front from the supplied layout and moved sentence translation reveal to the back via `{{FrontSide}}` and deterministic reveal script/fallback markup.
- Switched the phonetics CSS to Multilang color variables while keeping audio button class names renderable.

## Deviations from Plan

None - plan executed as written.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- Found `templates/russian_phoneme_card.md`.
- Found `src/multilang/services/russian_phoneme_deck.py`.
- Found `tests/services/test_russian_phoneme_deck.py`.
- Found commit `d18b448`.
- Found commit `2b6c1fa`.
