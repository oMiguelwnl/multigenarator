# Phase 4 Research: Audio Synthesis

**Phase:** 4 - Audio Synthesis  
**Researched:** 2026-04-24  
**Status:** Ready for planning  
**Confidence:** HIGH

## Research Answer

Phase 4 should add one persisted audio stage after accepted Phase 3 text and before export. The implementation should keep Azure Speech as the only synthesis provider in v1, use a versioned deterministic voice registry for the seven supported languages, derive TTS-safe input without mutating learner-facing text, synthesize `word` and `sentence` assets separately, validate the produced media before accepting it, and persist enough provenance to safely reuse assets on resume/rerun without regenerating identical audio.

## Decisions to Carry Into Planning

### Stack and provider choices
- Use **`azure-cognitiveservices-speech`** as the Phase 4 provider boundary; keep live SDK calls isolated behind an adapter so tests never require Azure access.
- Keep **Azure Speech** as the only Phase 4 provider. Do not introduce secondary TTS providers in this phase.
- Use **SSML-capable synthesis requests** so the pipeline can preserve a clean separation between visible text and synthesis-specific text handling.

### Phase-4-specific architecture
- Keep **one top-level job stage**: `JobStage.SYNTHESIZE_AUDIO`; model finer-grained word/sentence progress inside persisted audio rows instead of adding more job stages.
- Add a dedicated **audio persistence boundary** keyed by `(job_id, item_key, asset_kind)` so `word` and `sentence` assets remain independently reusable.
- Persist, at minimum: `provider`, `voice_id`, `locale`, `format`, `text_hash`, `ssml_hash`, `storage_path`, `byte_size`, `duration_ms`, `status`, `fallback_used`, plus stable job/item identity.
- Keep the shipped operator surface on **`multilang generate`**. Audio should extend the current runtime pipeline instead of adding a second command.

### Voice and fallback policy
- Create a **versioned voice registry** in code for `pt`, `es`, `en`, `fr`, `de`, `ru`, and `nl`.
- The selection order must be deterministic: preferred Azure voice for the language, alternate Azure voice in the same locale, approved alternate locale/voice for the same language, then fail the audio record visibly.
- Persist the selected voice and whether fallback was used on every successful or failed synthesis attempt.
- Dutch should be planned explicitly with `nl-NL` primary coverage and `nl-BE` as the approved cross-locale fallback path.

### TTS input and media policy
- Derive **TTS-safe normalized input** from accepted card text without mutating `word`, `Example Sentence`, or other learner-facing fields.
- Hash normalized synthesis input plus voice configuration to build **deterministic storage keys** for reuse.
- Validate media before marking a row usable: file exists, file size is non-zero, storage path is stable, and duration is recorded when Azure exposes it.
- Keep **word audio** and **sentence audio** as separate assets with separate provenance and reuse decisions.

## Recommended File Layout

```text
src/multilang/
  domain/audio.py
  repositories/audio_repository.py
  services/audio_voice_registry.py
  services/audio_synthesis.py
  services/generate_audio_items.py

alembic/versions/
  20260424_04_audio_synthesis_tables.py

tests/
  domain/test_audio.py
  repositories/test_audio_repository.py
  services/test_audio_voice_registry.py
  services/test_audio_synthesis.py
  services/test_generate_audio_items.py
  integration/test_audio_job_flow.py
```

## Concrete Design Guidance

### Azure SDK behavior to plan around
- Azure Speech Python synthesis centers on `SpeechConfig`, `SpeechSynthesizer`, and `AudioOutputConfig` / in-memory results.
- The SDK returns `audio_data` and exposes completion/cancellation state; the docs also show `audio_duration` on successful synthesis results, which is enough for Phase 4 provenance.
- Voice choice priority is explicit: SSML voice overrides `speech_synthesis_voice_name`, and `speech_synthesis_voice_name` overrides locale defaults. The planner should therefore keep the chosen voice explicit in the registry and in persisted provenance.

### Supported language coverage
- Azure’s published TTS voice tables include production voices for all seven target languages in this project’s scope, including `de-DE`, `en-US` / `en-GB`, `es-ES` / `es-MX`, `fr-FR` / `fr-CA`, `pt-BR` / `pt-PT`, `ru-RU`, and `nl-NL` / `nl-BE`.
- Because voice catalogs evolve, the project should treat the in-repo registry as the shipping contract for v1 rather than trusting Azure defaults at runtime.

### Storage recommendation
- Keep Phase 4 storage **local and deterministic** under the existing CLI-first artifact style (for example inside `.multilang/audio/...`) while persisting `storage_path` as an abstraction. This avoids adding cloud storage complexity during a phase whose main risk is synthesis correctness and reuse behavior.
- Make `storage_path` stable from `(asset_kind, normalized_input_hash, voice_registry_version, selected_voice)` so resume and rerun logic can reuse assets safely.

## Common Pitfalls To Prevent In Phase 4

- Do not synthesize review-required text; Phase 4 should only consume accepted Phase 3 rows.
- Do not let Azure choose an implicit default voice; always resolve through the versioned registry.
- Do not reuse learner-facing text directly when a TTS-safe normalized variant is required.
- Do not accept a synthesis row just because Azure returned bytes once; verify file existence, byte count, stable path, and duration metadata.
- Do not key asset reuse only by `item_key`; use normalized synthesis input plus voice configuration so real text/voice changes force regeneration while identical requests reuse assets.

## Architectural Responsibility Map

| Layer | Phase 4 Responsibility |
|------|-------------------------|
| CLI | Keep audio on the shipped `multilang generate` path and print audio counters/diagnostics |
| Domain models | Encode asset kinds, statuses, provenance, normalized TTS input, and deterministic voice-selection results |
| Repository | Persist one audio row per `(job_id, item_key, asset_kind)` and query reusable assets |
| Voice registry | Resolve preferred and fallback Azure voices deterministically for each supported language |
| Synthesis service | Normalize TTS input, build SSML/text requests, call Azure, and validate media integrity |
| Runtime orchestrator | Run audio only after accepted text exists and reuse assets on resume/rerun |
| Tests | Lock voice resolution, persistence identity, deterministic paths, integrity checks, and shipped-path reuse behavior |

## Validation Architecture

Phase 4 should remain fully executable with automated checks attached to each new boundary.

- Use **pytest** with fake Azure adapters and temporary filesystem storage.
- Fast plan-level commands should stay focused:
  - `uv run pytest tests/domain/test_audio.py tests/services/test_audio_voice_registry.py tests/repositories/test_audio_repository.py -q`
  - `uv run pytest tests/services/test_audio_synthesis.py tests/services/test_generate_audio_items.py -q`
- Full shipped-path regression command:
  - `uv run pytest tests/cli/test_generate_command.py tests/integration/test_audio_job_flow.py -q`

Required automated coverage:
- voice-registry resolution for all seven supported languages
- deterministic fallback ordering and `fallback_used` persistence
- separate `word` and `sentence` audio row identity
- deterministic storage path/hash reuse
- media-integrity rejection for zero-byte or missing files
- accepted-text-only gating before audio synthesis
- resume/rerun reuse of existing assets without duplicate rows
- shipped-path CLI counters and diagnostics

## Source Coverage Notes For Planning

This research directly supports:
- **AUDI-01** via Azure-first `word_audio`, deterministic fallback, provenance, and reusable asset storage
- **AUDI-02** via Azure-first `sentence_audio`, deterministic fallback, provenance, and reusable asset storage
- **JOB-01/JOB-03 carry-forward behavior** via stable row identity and deterministic asset reuse during resume/rerun

## Recommendation

Proceed to planning with four focused plans: audio contracts and voice registry, audio persistence and migration, synthesis/integrity services, and shipped-path runtime integration with reuse verification.

## Sources

- `.planning/phases/04-audio-synthesis/04-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/ARCHITECTURE.md`
- `.planning/research/STACK.md`
- `.planning/research/PITFALLS.md`
- `CARD_TEMPLATE.md`
- `https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech`
- `https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-speech-synthesis`
- `https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts`

---

*Phase: 04-audio-synthesis*  
*Research completed: 2026-04-24*
