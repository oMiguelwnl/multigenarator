# Quick Task 019 Verification: Add Czech

## Verdict

Passed.

## Goal Check

User request: add the Czech language to the program.

Czech is now registered as ISO code `cs` across the modern-language generation flow, including enum validation, runtime/settings defaults, text and pronunciation providers, deterministic local adapters, audio routing, Tatoeba routing, language validation markers, highlight extraction stopwords, POS inference, frequency assets, and focused tests.

## Evidence

- `GenerationRequest(language="cs", source_type="frequency")` resolves to `SupportedLanguage.CS`.
- `Settings(_env_file=None).supported_languages` includes `cs`.
- Provider maps include `cs` as Czech, DeepL target `CS`, Tatoeba code `ces`, pronunciation support, language-id support, text-validation markers, and highlight stopwords.
- Azure voice selection returns `cs-CZ-VlastaNeural`; ElevenLabs returns locale `cs-CZ`; Google Translate TTS returns language code `cs`.
- `assets/frequency/cs/curated-v1.csv` and `assets/frequency/cs/rejections-v1.csv` exist and pass the existing asset validator.
- Focused test selection passed: `21 passed in 0.98s`.
- Affected test-file sweep passed: `125 passed in 3.22s`.
- `uv run python scripts/build_frequency_assets.py --check --language cs` passed.
- `uv run python scripts/build_frequency_assets.py --check` passed.
- `git diff --check` passed with Windows LF/CRLF warnings only.

## Residual Risks

- The broad suite was not run because known broad-suite drift is documented in `.planning/codebase/CONCERNS.md`.
- Live provider quality for Czech examples, translations, and audio still depends on configured external providers; this task verified routing and deterministic local/test paths, not live network output quality.
