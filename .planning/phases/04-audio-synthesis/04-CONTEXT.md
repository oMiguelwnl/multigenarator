# Phase 4: Audio Synthesis - Context

**Gathered:** 2026-04-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate reliable, playable `word_audio` and `sentence_audio` for cards whose Phase 3 text passed validation. This phase covers Azure-first TTS synthesis, TTS-safe input normalization, deterministic fallback handling, persisted audio provenance, media-integrity checks, and resume/rerun-safe asset reuse. Anki `[sound:...]` formatting, media packaging, and final export behavior remain outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Audio persistence
- **D-01:** Audio should get its own persisted boundary rather than being embedded into lexical or text records, because synthesis has a separate lifecycle, failure mode, and reuse policy.
- **D-02:** Persist one stable audio record per `(job_id, item_key, asset_kind)` so reruns and resumes can reuse existing `word` and `sentence` assets safely instead of duplicating them.
- **D-03:** Each audio record should preserve enough provenance to debug and re-synthesize deterministically, including `provider`, `voice_id`, `locale`, `format`, `text_hash`, `ssml_hash`, `storage_path`, `byte_size`, `duration_ms` when available, `status`, and `fallback_used`.

### Synthesis gate and stage model
- **D-04:** Audio should run only for items whose Phase 3 text record is accepted. Review-required text should not receive audio in Phase 4.
- **D-05:** Keep one job-level stage, `synthesize_audio`, and model finer-grained progress or failure inside the persisted audio records rather than by adding extra job stages.

### TTS input and voice policy
- **D-06:** Keep learner-facing display text separate from synthesis input. Phase 4 may derive normalized `tts_text` or SSML-safe input, but that must not mutate the visible card text.
- **D-07:** Azure TTS is the primary provider for all seven supported languages, and Phase 4 should introduce a versioned voice matrix or equivalent deterministic registry for preferred and approved fallback voices.
- **D-08:** Voice fallback must be explicit, deterministic, and persisted in provenance. The locked fallback order is: preferred Azure voice for the language, alternate Azure voice in the same locale, approved alternate Azure locale/voice for the same language, then fail the audio record instead of silently omitting audio.

### Media integrity and reuse
- **D-09:** Audio filenames or storage keys must be deterministic from normalized synthesis input plus voice configuration so reruns reuse assets instead of producing duplicates for the same content.
- **D-10:** Phase 4 should validate media integrity before accepting an audio record: the file must exist, have non-zero bytes, keep a stable storage path, and record duration metadata when the provider exposes it.

### the agent's Discretion
- Exact schema column names and repository/API shapes, as long as the locked identity and provenance rules are preserved.
- Exact on-disk storage layout, as long as it remains deterministic and Phase 5 can package it later.
- Exact CLI wording for audio counters, warnings, and fallback diagnostics.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` - Phase 4 goal, dependency on Phase 3, and success criteria for `word_audio`, `sentence_audio`, and safe reruns.
- `.planning/REQUIREMENTS.md` - `AUDI-01` and `AUDI-02`, plus the phase traceability table.
- `.planning/PROJECT.md` - Product constraints, supported languages, Azure-first audio direction, and trust-first quality expectations.
- `.planning/STATE.md` - Carry-forward decisions from Phases 1 through 3, plus the open concern about voice inventory and fallback policy that this phase must close.

### Research guidance
- `.planning/research/ARCHITECTURE.md` - Confirms audio belongs after accepted text and before export, with a separate media-integrity gate.
- `.planning/research/STACK.md` - Recommends Azure Speech Service, the Azure Python SDK, SSML support, and separate word/sentence audio generation.
- `.planning/research/PITFALLS.md` - Warns against assuming Azure voice coverage without a voice matrix and against mixing display text with TTS-specific text.

### Existing product contract
- `CARD_TEMPLATE.md` - Already reserves `{{word_audio}}` and `{{sentence_audio}}` placeholders, which Phase 4 should populate semantically without taking over final export formatting.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/multilang/domain/jobs.py` - Already defines `JobStage.SYNTHESIZE_AUDIO`, giving Phase 4 a natural stage boundary in the existing lifecycle.
- `src/multilang/runtime.py` and `src/multilang/cli.py` - Already expose one shipped path on `multilang generate`, so audio should extend that same runtime instead of adding a separate command.
- `src/multilang/db/models.py` - Already separates job, lexical, and text persistence, which strongly suggests Phase 4 should add a dedicated audio persistence boundary following the same pattern.
- `src/multilang/settings.py` - Already centralizes typed runtime configuration and should be extended for Azure speech credentials, audio output settings, and voice-registry overrides.

### Established Patterns
- The shipped surface remains one CLI entry point: `multilang generate`.
- The codebase uses a CLI -> service -> repository split with repository-backed runtime behavior.
- Resume and duplicate-safe rerun already depend on deterministic identifiers and persisted stage state, so audio caching and storage keys must remain deterministic too.

### Integration Points
- Phase 4 should consume accepted text records after Phase 3 and persist audio artifacts before Phase 5 export logic is added.
- Audio persistence should attach to stable `job_id` and `item_key` identity so targeted reruns and interrupted jobs can safely reuse media.
- The card template already expects separate word and sentence audio values, but Phase 5 remains responsible for final Anki-compatible export formatting.

</code_context>

<specifics>
## Specific Ideas

- Keep `word_audio` and `sentence_audio` as separate assets with separate provenance and reuse decisions.
- Normalize synthesis input before hashing so harmless punctuation or whitespace drift does not create duplicate files for the same audible output.
- Treat the voice matrix as a first-class artifact for the seven supported languages, especially to close the known Dutch fallback risk before implementation hardens.
- Add audio counters to the shipped CLI path in the same style as lexical and text counters so operators can audit accepted, reused, failed, and fallback-generated assets.

</specifics>

<deferred>
## Deferred Ideas

- Secondary TTS providers can wait until Azure-first synthesis is stable.
- Rich per-language SSML tuning beyond the minimal stable synthesis contract can wait until baseline voices are verified.
- Human review UX for audio quality can wait until after Phase 4 ships deterministic synthesis and fallback behavior.
- Final `[sound:...]` field formatting and media packaging stay deferred to Phase 5.

</deferred>

---

*Phase: 04-audio-synthesis*
*Context gathered: 2026-04-24*
