# Quick Task 004: DeepL primario e audio Google Translate para Latin

## Objective

Corrigir a configuracao de providers para usar DeepL como traducao primaria, manter Google Translate como candidato de traducao, implementar Google Translate TTS como provedor de audio e deixar ElevenLabs/FineVoice como candidatos de audio.

## Approach Context

User confirmed: implement Google Translate audio via the Google Translate TTS endpoint (`translate_tts`) without adding a dependency. DeepL must be the primary translation provider; Google Translate should be a translation candidate. For audio, Google Translate TTS should be implemented, with ElevenLabs and FineVoice retained as audio candidates.

## Codebase Context

The project uses Python services under `src/multilang/services/`, typed settings in `src/multilang/settings.py`, provider enums in `src/multilang/domain/audio.py`, and runtime provider wiring in `src/multilang/runtime.py`. Existing audio adapters use injectable `urlopen` functions and fake responses in tests. Latin MVP assets remain committed under `data/latin_mvp/`; policy metadata lives in `latin_audio_samples.py`. Tests should avoid live provider calls and use fakes. The worktree is already dirty from previous quick tasks and unrelated files; this task must only touch its planned files and must not modify dirty Latin export/evidence files.

## Task 1: Restore DeepL Primary Translation Policy

<files>
- `src/multilang/settings.py`
- `src/multilang/services/latin_audio_samples.py`
- `tests/services/test_latin_audio_samples.py`
</files>

<action>
Set the default `translation_provider` back to `deepl`. Update Latin provider policy metadata so DeepL is primary translation and Google Translate is a translation candidate, not the primary translation path.
</action>

<verify>
Run `python -m pytest -q tests/services/test_latin_audio_samples.py tests/services/test_provider_text_adapters.py tests/test_settings.py`.
</verify>

## Task 2: Implement Google Translate TTS Audio Adapter

<files>
- `src/multilang/domain/audio.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `src/multilang/runtime.py`
- `tests/services/test_google_translate_speech_adapter.py`
- `tests/test_runtime.py`
</files>

<action>
Add a `google_translate` audio provider enum/settings option, implement a small injectable Google Translate TTS adapter that writes MP3 bytes, strips SSML to plain text, and wire it into runtime audio provider selection.
</action>

<verify>
Run `python -m pytest -q tests/services/test_google_translate_speech_adapter.py tests/test_runtime.py tests/services/test_audio_synthesis.py`.
</verify>

## Task 3: Verify Focused Provider Behavior

<files>
- `src/multilang/services/latin_audio_samples.py`
- `tests/services/test_latin_audio_samples.py`
</files>

<action>
Ensure policy names distinguish Google Translate text candidate from Google Translate TTS audio provider and keep ElevenLabs/FineVoice as audio candidates only.
</action>

<verify>
Run `python -m pytest -q tests/services/test_latin_audio_samples.py tests/services/test_google_translate_speech_adapter.py tests/test_runtime.py`.
</verify>

## No UI Proof Rationale

This task changes backend provider configuration, provider adapters, and tests only. It has no rendered UI surface.
