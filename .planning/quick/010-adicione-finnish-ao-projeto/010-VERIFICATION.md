# Quick Task 010 Verification: Add Finnish

## Verdict

passed

## Goal Check

Task description: `adicione o Finnish ao projeto`.

Finnish is now registered as language code `fi` in the domain enum, settings defaults, runtime display names, text/pronunciation provider maps, language identification, validation markers, highlight stopwords, local deterministic adapters, Azure voice registry, ElevenLabs fallback routing, Google Translate TTS routing, and committed frequency assets.

## Evidence

- Contract/config smoke checks passed for `GenerationRequest(language="fi")` and `Settings.supported_languages`.
- Provider map smoke checks passed for LiteLLM/DeepL names, pronunciation names, corpus language-id, Tatoeba code `fin`, validation markers, and highlight stopwords.
- Focused Finnish tests passed: local adapter, Azure voice selection, ElevenLabs voice routing, Google Translate TTS routing, domain acceptance, settings default list, frequency asset validation, and CLI unsupported-language regression.
- Frequency asset checks passed for Finnish and for all configured supported languages.
- Focused regression suite passed: `83 passed in 2.74s`.

## Residual Risk

- Live Azure, DeepL, Tatoeba, Google Translate TTS, and ElevenLabs provider calls were not exercised; coverage is deterministic routing/configuration only, matching existing language-addition pattern.
