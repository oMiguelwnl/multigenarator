---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Korean Learning System and Shared Generation Hardening
status: in_progress
stopped_at: Phase 31 Plan 31-29 complete; Plans 31-30 and 31-31 ready in isolated worktrees
last_updated: "2026-08-27T14:59:16Z"
last_activity: 2026-08-27
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 32
  completed_plans: 26
  percent: 20
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-01)

**Core value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Current focus:** Parallel Phase 31 AI/media closure and Phase 32 offline shared-hardening execution

## Current Position

Phase: 31
Plan: 31-29 complete; 31-30 AI and 31-31 media lanes ready to execute in parallel
Status: Exact common baseline/runtime verified; Phase 31 remains open for lane evidence and the 31-32 join
Last activity: 2026-08-27

Progress: 1 of 5 phases complete

## Performance Metrics

**Velocity:**

- Total plans completed: 78 from shipped/previous milestones
- v2.0 plans completed: 12
- Average duration: 7min for v2.0
- Total v2.0 execution time: 1.29 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 22. Latin Mode Contracts and Isolation | 3 | 21min | 7min |
| 23. Frozen 50-Card Source Pack and Sentence Sequence | 4 | 28min | 7min |
| 24. Morphology Evidence and Gramatica Gate | 4 | 28min | 7min |
| 25. Latin Review Gates and Curated Records | 4 | 28min | 7min |
| 26. Portuguese Translation Quality | 3 | 21min | 7min |
| 27. Latin Audio Policy and Integrity | 6 | 27min | 5min |
| 28. Latin Export and Milestone Evidence | 0 | TBD | N/A |
| 27 | 6 | - | - |

**Recent Trend:**

- Last shipped milestone: v1.3 completed through Phase 21 with focused evidence passing.
- Trend: v2.0 starts from approved Latin requirements and a standard-granularity 7-phase roadmap.

| Phase 22-latin-mode-contracts-and-isolation P1 | 7min | 3 tasks | 5 files |
| Phase 22-latin-mode-contracts-and-isolation P2 | 7min | 3 tasks | 4 files |
| Phase 22-latin-mode-contracts-and-isolation P3 | 7min | 3 tasks | 1 files |
| Phase 23-frozen-50-card-source-pack-and-sentence-sequence P1 | 7min | 3 tasks | 2 files |
| Phase 23-frozen-50-card-source-pack-and-sentence-sequence P2 | 7min | 2 tasks | 2 files |
| Phase 23-frozen-50-card-source-pack-and-sentence-sequence P3 | 7min | 2 tasks | 4 files |
| Phase 23-frozen-50-card-source-pack-and-sentence-sequence P4 | 7min | 2 tasks | 1 files |
| Phase 24-morphology-evidence-and-gramatica-gate P1 | 7min | 2 tasks | 2 files |
| Phase 24-morphology-evidence-and-gramatica-gate P2 | 7min | 2 tasks | 2 files |
| Phase 24-morphology-evidence-and-gramatica-gate P3 | 7min | 3 tasks | 4 files |
| Phase 24-morphology-evidence-and-gramatica-gate P4 | 7min | 2 tasks | 1 files |
| Phase 25-latin-review-gates-and-curated-records P01 | 7min | 2 tasks | 2 files |
| Phase 25-latin-review-gates-and-curated-records P02 | 7min | 2 tasks | 3 files |
| Phase 25-latin-review-gates-and-curated-records P03 | 7min | 2 tasks | 3 files |
| Phase 25-latin-review-gates-and-curated-records P04 | 7min | 2 tasks | 1 files |
| Phase 25-latin-review-gates-and-curated-records P04 | 7min | 2 tasks | 1 files |
| Phase 26-portuguese-translation-quality P02 | 7min | 2 tasks | 2 files |
| Phase 26-portuguese-translation-quality P03 | 7min | 2 tasks | 5 files |
| Phase 27-latin-audio-policy-and-integrity P01 | 4min | 2 tasks | 2 files |
| Phase 27-latin-audio-policy-and-integrity P02 | 7min | 2 tasks | 4 files |
| Phase 27-latin-audio-policy-and-integrity P03 | 2min | 1 tasks | 2 files |
| Phase 27-latin-audio-policy-and-integrity P04 | 4min | 2 tasks | 103 files |
| Phase 27-latin-audio-policy-and-integrity P05 | 6min | 2 tasks | 5 files |
| Phase 27-latin-audio-policy-and-integrity P06 | 4min | 2 tasks | 3 files |
| Phase 28-latin-export-and-milestone-evidence P01 | 3min | 2 tasks | 4 files |
| Phase 28-latin-export-and-milestone-evidence P02 | 5min | 2 tasks | 4 files |
| Phase 28-latin-export-and-milestone-evidence P03 | 4min | 3 tasks | 4 files |

## Accumulated Context

### Decisions

Full current decision history is in `.planning/SPEC.md` and `KOREAN-STRUCTURE.md`. v3.0 decisions affecting execution:

- `ko` is the canonical language identity; `ko-KR` is provider/locale-only.
- Kiwi/`kiwipiepy` is the planned primary morphology engine and Korean morphology fails closed when unavailable.
- Hangul reuses the kana layout, pronunciation reuses the phoneme layout, and frequency/grammar reuse the normal layout with Korean note identities.
- Hangul, pronunciation, and grammar use explicit curriculum-i+1 concept graphs; frequency/custom/highlights use adaptive or contextual ordering.
- Azure `ko-KR` is the only default TTS policy; jamo and phonological-rule audio require deterministic integrity plus AI linguistic/acoustic review.
- The 3000-entry frequency asset is blocked until source, attribution, and redistribution terms are approved.
- Phase 30 execution was gated on reconciling the overlapping Mandarin quick-task surfaces before shared registries were changed.
- The verified remote Phase 30 remains authoritative; restored shared hardening is distributed across Phases 32-34 and must not replace its Korean identity, migration, or matcher contracts.

Historical v2.0/v2.1 decisions retained for reference:

- v2.0 is Classical Latin only; Greek and other Latin variants are out of scope.
- MVP scope is exactly 50 reviewed cards; 300/1000/3000-card Latin scale is deferred.
- Latin uses a separate `la` / Classical Latin generation path, not the modern-language frequency path.
- All MVP groups are included: mode, frequency, source/sentence, grammar, Portuguese text, review, audio, export, evidence/regression.
- Final learner-ready export is approved-only, including source, grammar, translation, and audio readiness gates.
- Source mix is license-gated and must distinguish original Classical Latin, adapted didactic Latin, and reference examples.
- `Gramatica` uses short abbreviations (`sg`, `pl`) with Latin case labels including `Genitivus`.
- [Phase 22-latin-mode-contracts-and-isolation]: Kept Classical Latin out of SupportedLanguage and represented it through LatinGenerationRequest.
- [Phase 22-latin-mode-contracts-and-isolation]: Added a separate generate-latin-mvp command instead of extending generate --source.
- [Phase 22-latin-mode-contracts-and-isolation]: Kept Phase 22 evidence offline and import-only for review/audio boundaries.
- [Phase 23-frozen-50-card-source-pack-and-sentence-sequence]: Frozen Latin MVP source packs fail closed on count, sequence, license gate, target-form presence, and version mismatches.
- [Phase 23-frozen-50-card-source-pack-and-sentence-sequence]: The first-50 Latin MVP pack uses DCC Latin Core Vocabulary rank/source attribution plus truthfully typed project-authored/reference/original sentence provenance.
- [Phase 23-frozen-50-card-source-pack-and-sentence-sequence]: generate-latin-mvp remains isolated and now reports manifest-backed metadata rather than synthetic range-only output.
- [Phase 23-frozen-50-card-source-pack-and-sentence-sequence]: Phase 23 evidence excludes grammar, Portuguese translation, audio, and export fields to preserve later-phase boundaries.
- [Phase 24-morphology-evidence-and-gramatica-gate]: Latin grammar evidence fails closed by accepting only approved grammar_review_status in the source-pack contract.
- [Phase 24-morphology-evidence-and-gramatica-gate]: The frozen Latin MVP asset stores target-form-specific morphology evidence directly beside each source-pack entry.
- [Phase 24-morphology-evidence-and-gramatica-gate]: Latin MVP grammar readiness is derived from validated manifest entries, not caller-provided flags.
- [Phase 24-morphology-evidence-and-gramatica-gate]: Phase 24 evidence maps exactly GRAM-01 through GRAM-04 and keeps later translation/audio/export scope absent.
- [Phase 24-morphology-evidence-and-gramatica-gate]: Morphology evidence must be approved at loader time; unresolved and ambiguous statuses fail closed.
- [Phase 24-morphology-evidence-and-gramatica-gate]: Gramatica accepts concise tokens only, including Genitivus and short Portuguese-facing abbreviations.
- [Phase 24-morphology-evidence-and-gramatica-gate]: CLI and manifest JSON expose aggregate grammar counts and labels, not per-entry evidence notes.
- [Phase 25-latin-review-gates-and-curated-records]: Latin export readiness is centralized in latin_review.py and requires all four gates to be approved.
- [Phase 25-latin-review-gates-and-curated-records]: Blocking review states require explicit reasons so rejection and uncertainty context is preserved.
- [Phase 25-latin-review-gates-and-curated-records]: The curation asset must fail validation on any source-pack identity or provenance drift rather than filling fields implicitly.
- [Phase 25-latin-review-gates-and-curated-records]: Translation and audio gates remain needs_review with phase-specific reasons until Phases 26 and 27.
- [Phase 25-latin-review-gates-and-curated-records]: review-latin-mvp prints stable key=value summary lines plus sorted JSON gate counts for scanner-friendly CLI inspection.
- [Phase 25-latin-review-gates-and-curated-records]: Approved gates require force before status or reason changes, protecting curated approvals from accidental overwrites.
- [Phase 25-latin-review-gates-and-curated-records]: Phase 25 evidence loads the real curation/source-pack assets instead of using mocks.
- [Phase 25-latin-review-gates-and-curated-records]: Translation and audio gates must remain needs_review until their later phases approve them.
- [Phase 25-latin-review-gates-and-curated-records]: Focused Phase 25 evidence loads real curation/source-pack assets rather than stale private runtime templates.
- [Phase 25-latin-review-gates-and-curated-records]: No-scope-creep evidence explicitly proves translation and audio remain pending after review gate setup.
- [Phase 26-portuguese-translation-quality]: The Portuguese translation asset stores learner-facing text in-repo and does not depend on live provider calls.
- [Phase 26-portuguese-translation-quality]: All 50 entries remain needs_review until a future human review artifact explicitly approves them.
- [Phase 26-portuguese-translation-quality]: Portuguese QA summary loading is opt-in so default Latin MVP startup remains provider-free and backward-compatible.
- [Phase 26-portuguese-translation-quality]: The CLI prints only public QA counts/statuses for --portuguese-json, not translation text, secrets, or local paths.
- [Phase 27-latin-audio-policy-and-integrity]: Latin audio uses a separate metadata/readiness service rather than adding Latin to SupportedLanguage or the global Azure voice registry.
- [Phase 27-latin-audio-policy-and-integrity]: Export readiness requires both word and sentence artifacts to be approved and exact-text aligned with the frozen source pack.
- [Phase 27-latin-audio-policy-and-integrity]: Latin audio readiness is source-pack aligned: item order and source_pack_version must match latin-mvp-50-v1 before export can pass.
- [Phase 27-latin-audio-policy-and-integrity]: Latin audio diagnostics expose item_key, audio_kind, and field names only, avoiding local paths and provider-sensitive details.
- [Phase 27-latin-audio-policy-and-integrity]: Initial local playback exploration used eSpeak NG la; Phase 29 supersedes that provider decision for the current MVP export.
- [Phase 27-latin-audio-policy-and-integrity]: Sample generation is local-only and does not contact Azure or any network provider.
- [Phase 29-latin-elevenlabs-audio-refresh]: Google Translate TTS voice `la` is the final approved provider for the current 50-card Classical Latin MVP under pronunciation policy `google_translate_latin`.
- [Phase 27-latin-audio-policy-and-integrity]: Azure remains blocked for Classical Latin until a future review verifies a native Classical Latin/la Azure voice.
- [Phase 29-latin-elevenlabs-audio-refresh]: The full Latin MVP manifest uses `google-translate-tts`, voice `la`, provider version `google-translate-tts-la`, and 100 approved MP3 media artifacts.
- [Phase 27-latin-audio-policy-and-integrity]: Curation audio_gate approval is copied from the playback review artifact while source, translation, grammar, provenance, and sequence fields remain unchanged.
- [Phase 27-latin-audio-policy-and-integrity]: Latin audio readiness output is opt-in through --audio-json and contains aggregate counts only, not media paths or provider raw details.
- [Phase 27-latin-audio-policy-and-integrity]: Phase 27 evidence uses committed source, curation, playback review, and audio manifest assets rather than mocks.
- [Phase 27-latin-audio-policy-and-integrity]: Latin audio export readiness now treats storage_path validation as part of the approval gate, not as a later export concern.
- [Phase 27-latin-audio-policy-and-integrity]: Storage-path diagnostics remain privacy-safe by reporting only item_key, audio_kind, and field=storage_path.
- [Phase 27-latin-audio-policy-and-integrity]: Focused Phase 27 sample tests keep their fake eSpeak NG runner local rather than importing another test module through tests.services.
- [Phase 28-latin-export-and-milestone-evidence]: Latin export rows are built only after source, translation, grammar, and audio gates are approved.
- [Phase 28-latin-export-and-milestone-evidence]: The user's Approve translations response is recorded as the human review event for all 50 Portuguese translation gates.
- [Phase 28-latin-export-and-milestone-evidence]: Latin audio fields expose Anki sound basenames while media_index retains repository-relative WAV paths.
- [Phase 28-latin-export-and-milestone-evidence]: Latin APKG export uses a dedicated note model and model/deck IDs rather than mutating existing export models.
- [Phase 28-latin-export-and-milestone-evidence]: Latin CSV/TSV exports use Anki import headers and the exact Plan 28-01 field order.
- [Phase 28-latin-export-and-milestone-evidence]: The export-latin-mvp CLI prints only artifact path, card/media counts, note type, and status.
- [Phase 28-latin-export-and-milestone-evidence]: Final milestone evidence treats all 30 v2.0 requirement IDs as an exact set from MODE-01 through EVID-03.
- [Phase 28-latin-export-and-milestone-evidence]: Existing-mode evidence directly asserts frequency, manual, highlight, and phonetics contracts rather than relying on the known broad-suite drift.
- [Phase 28-latin-export-and-milestone-evidence]: Latin model and deck IDs are distinct from phoneme and shipped export IDs.
- [Phase 29-latin-elevenlabs-audio-refresh]: ElevenLabs Italian is deferred after all configured keys returned HTTP 402 Payment Required; it is not required for the current Latin MVP export.
- [Phase 29-latin-elevenlabs-audio-refresh]: FineVoice remains research-only and is not wired as an active provider.
- [Phase 29-latin-elevenlabs-audio-refresh]: Current Latin export does not require live provider calls or system-level audio provider uninstall steps.

### Pending Todos

- Repair broad-suite drift before treating full `python -m pytest -q` as authoritative again.
- Execute Phase 31 Plans 31-30 and 31-31 concurrently from their exact prepared worktrees and join them in 31-32.
- Start Phase 32 offline lanes concurrently without bypassing the later Phase 31 production join or licensing gates.
- Approve the Korean frequency-source and redistribution policy before committing a 3000-entry asset.

### Blockers/Concerns

- Human linguistic review is no longer a blocker. Phase 31 still requires AI review consensus, rights dispositions, exact media/integrity/acoustic evidence, canonical activation, and production export.
- Current final frequency loading still permits live `wordfreq` replacement and generic non-Korean suffix fallback; Phase 32 owns fail-closed remediation.
- `wordfreq` supports `ko` as a candidate bootstrap, but its documentation warns against CSV extraction without preserved attribution/licensing information.
- Latin TTS quality is approved only for the current 50-card Google Translate TTS MVP pack; future higher-quality Latin audio should use a new review artifact.
- Source licensing for Phase 23 is license-gated in the frozen source pack; later phases must preserve those provenance fields.
- Broad-suite drift remains known debt; focused regression evidence should stay authoritative until repaired.
- Plan 22-02 listed verification exposes existing CLI/audio drift: `tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters` expects `fallback_audio_items=1`, but current runtime output omits it.

## Deferred Items

Items acknowledged and carried forward:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Latin scale | 300-card pilot and 3000-card Latin deck | Deferred beyond 50-card MVP | v2.0 roadmap |
| Test suite drift | Full-suite collection drift in tests importing removed private runtime template adapters | Known debt | Pre-v1.3 |
| quick_task | 260430-001-russian-card-quality-regression | Missing | v1.3 closeout 2026-05-16 |
| CLI/audio drift | `test_generate_command_default_runtime_reports_audio_counters` missing `fallback_audio_items=1` output | Deferred; unrelated to Phase 22 Latin changes | Phase 22 Plan 22-02 verification |

## Session Continuity

Last session: 2026-08-27T14:59:16Z
Stopped at: Plan 31-29 baseline/runtime complete; isolated AI and media lanes are ready for Plans 31-30 and 31-31
Resume file: None
