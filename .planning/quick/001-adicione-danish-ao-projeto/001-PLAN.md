# Quick Task 001 Plan: adicione Danish ao projeto

## Objective
Add Danish (`da`) as a supported project language across the existing modern-language contracts and provider configuration surfaces, with focused tests proving the new code path is accepted.

## Context
- Codebase maps identify `src/multilang/domain/jobs.py`, `src/multilang/settings.py`, `src/multilang/runtime.py`, provider adapters, language identification, and audio voice registry as the safe surfaces for language-support changes.
- Frequency curated assets live under `assets/frequency/{language}/`; generating a full Danish frozen 3000-row asset set is out of this quick task unless explicitly widened.
- Full test suite has known drift; use focused domain/settings/provider tests as the verification gate.
- Planner/executor/verifier template files referenced by the workflow were not present under `.planning/templates/`; this plan follows the loaded `gsdd-quick` contract directly.

## no_ui_proof_rationale
This quick task changes backend/domain/provider configuration only. It does not make rendered UI claims.

## Tasks

### Task 1: Add Danish to language contracts
<files>
- `src/multilang/domain/jobs.py`
- `src/multilang/settings.py`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
</files>
<action>
Add `SupportedLanguage.DA = "da"`, include `"da"` in the settings `SupportedLanguageCode` literal and default supported languages, and update contract tests to assert Danish is accepted.
</action>
<done>
Danish appears in the supported-language enum, default settings list, and contract tests; `GenerationRequest(language="da", ...)` validates as `SupportedLanguage.DA`.
</done>
<verify>
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py -q`
</verify>

### Task 2: Wire Danish through provider/runtime support surfaces
<files>
- `src/multilang/runtime.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/language_identifier.py`
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `src/multilang/services/highlight_candidate_extraction.py`
- `tests/services/test_audio_voice_registry.py`
</files>
<action>
Add Danish names/codes to runtime deck naming, text/translation provider language maps, corpus language identification, TTS voice selection, fallback speech adapters, and highlight stopword filtering. Use Azure `da-DK-ChristelNeural` as the preferred voice with `da-DK-JeppeNeural` fallback.
</action>
<done>
Danish has deck naming, provider language/DeepL mappings, corpus language-id inclusion, Azure voice selection, fallback speech-adapter mappings, and highlight stopwords covered by focused tests where applicable.
</done>
<verify>
- `uv run pytest tests/services/test_audio_voice_registry.py -q`
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_audio_voice_registry.py -q`
</verify>

### Task 3: Record execution evidence
<files>
- `.planning/quick/001-adicione-danish-ao-projeto/001-SUMMARY.md`
- `.planning/quick/001-adicione-danish-ao-projeto/001-VERIFICATION.md`
- `.planning/quick/LOG.md`
</files>
<action>
Persist a quick-task summary, verifier report, and log row after implementation and focused verification complete.
</action>
<done>
The quick task directory contains persisted summary and verification reports, and `.planning/quick/LOG.md` has one row for quick task 001 with the final status.
</done>
<verify>
- `test -f .planning/quick/001-adicione-danish-ao-projeto/001-SUMMARY.md`
- `test -f .planning/quick/001-adicione-danish-ao-projeto/001-VERIFICATION.md`
</verify>
