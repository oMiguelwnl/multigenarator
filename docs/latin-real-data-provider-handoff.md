# Latin Real Data Provider Handoff

## Goal

Replace the current dummy Latin deck data with real Latin cards and prepare the pipeline to scale later to 2000+ cards and cards generated from user-provided Latin texts.

## Current Problem

The current APKG is only a technical test. It uses dummy data like `lemma1`, `lemma2`, and sentences like `lemma1 amat.`.

Files that must be regenerated:

- `data/latin_mvp/latin-mvp-50-v1.json`
- `data/latin_mvp/latin-mvp-50-v1-curation.json`
- `data/latin_mvp/latin-mvp-50-v1-pt.json`
- `data/latin_mvp/latin-mvp-50-v1-audio.json`
- `data/latin_mvp/audio/latin-mvp-50-v1/*.mp3`
- `exports/latin_mvp/latin-mvp-50.apkg`

## Provider Decisions

- Card generation: OpenRouter.
- Card validation/judging: OpenRouter.
- Translation Latin -> Portuguese: Google Translate first, then OpenRouter validates/repairs.
- DeepL: optional for modern languages, not primary for Latin unless verified.
- Audio primary: Google Translate TTS using Latin (`la`).
- Audio fallback 1: ElevenLabs using Italian voice.
- Audio fallback 2: Azure TTS using Italian voice.
- FineVoice: research-only, do not use in production.

## Required Changes

1. Replace dummy source data with real Latin lemmas from the frequency list at https://mylittlewordland.com/course/415114/as-mil-palavras-mais-frequentes-do-latim (or the DCC equivalent it is based on).
2. Generate real short Latin learner sentences for each lemma using OpenRouter.
3. Validate each card locally and with OpenRouter:
   - target form appears in the sentence
   - sentence is plausible Latin
   - grammar note matches the form
   - Portuguese translation is faithful
   - no dummy/placeholder content remains
4. Generate Portuguese translations with Google Translate, then validate/repair using OpenRouter.
5. Generate audio with this fallback order:
   - Google Translate TTS (`la`)
   - ElevenLabs Italian voice
   - Azure Italian voice
6. Regenerate the APKG only after source, curation, translation, and audio manifests are approved.

## Existing Code To Reuse

- Source pack validation: `src/multilang/services/latin_source_pack.py`
- Audio validation: `src/multilang/services/latin_audio.py`
- Google TTS adapter: `src/multilang/services/google_translate_speech_adapter.py`
- ElevenLabs Latin audio helper: `src/multilang/services/latin_audio_refresh.py`
- Export: `src/multilang/services/latin_export.py`

Do not weaken export validators. The export should still fail if any required artifact is missing or unapproved.

## New Code Suggested

- `src/multilang/services/latin_card_generation.py` for OpenRouter structured card generation.
- `src/multilang/services/latin_card_validation.py` for OpenRouter judge/repair.
- `src/multilang/services/latin_translation_generation.py` for Google Translate + OpenRouter translation validation.
- `src/multilang/services/latin_audio_generation.py` for Google TTS -> ElevenLabs -> Azure fallback.

## Future-Proofing

Do not hard-code the new logic only for 50 cards. The 50-card deck is temporary. Design the generation layer so it can later create:

- 2000+ frequency cards
- level-based decks
- cards from user-provided Latin texts

Do not use `wordfreq` for Latin.

## Acceptance Criteria

- No `lemma1`, `lemma2`, or dummy data remains.
- 50 real Latin cards are generated.
- 50 Portuguese translations are approved.
- 100 real audio files are generated, not placeholders.
- APKG exports successfully.
- The design can scale beyond 50 cards.
