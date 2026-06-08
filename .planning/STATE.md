---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 27-04-PLAN.md
last_updated: "2026-06-08T17:00:26.643Z"
last_activity: 2026-06-08
progress:
  total_phases: 7
  completed_phases: 5
  total_plans: 23
  completed_plans: 22
  percent: 96
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-01)

**Core value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Current focus:** Phase 27 — latin-audio-policy-and-integrity

## Current Position

Phase: 27 (latin-audio-policy-and-integrity) — EXECUTING
Plan: 5 of 5
Status: Ready to execute
Last activity: 2026-06-08

Progress: [██████████] 96%

## Performance Metrics

**Velocity:**

- Total plans completed: 72 from shipped/previous milestones
- v2.0 plans completed: 11
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
| 27. Latin Audio Policy and Integrity | 3 | 13min | 4min |
| 28. Latin Export and Milestone Evidence | 0 | TBD | N/A |

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

## Accumulated Context

### Decisions

Full decision history is in `.planning/PROJECT.md`. Current v2.0 decisions affecting execution:

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
- [Phase 27-latin-audio-policy-and-integrity]: eSpeak NG la is the only locally synthesizeable Latin candidate for playback review; Azure multilingual remains blocked without a verified native Classical Latin/la locale.
- [Phase 27-latin-audio-policy-and-integrity]: Sample generation is local-only and does not contact Azure or any network provider.
- [Phase 27-latin-audio-policy-and-integrity]: Approved eSpeak NG voice la for the 50-card Classical Latin MVP only under pronunciation policy classical_approx.
- [Phase 27-latin-audio-policy-and-integrity]: Azure remains blocked for Classical Latin until a future review verifies a native Classical Latin/la Azure voice.
- [Phase 27-latin-audio-policy-and-integrity]: The full Latin MVP manifest uses the Plan 27-03 approved eSpeak NG provider espeak-ng, voice la, and pronunciation policy classical_approx.
- [Phase 27-latin-audio-policy-and-integrity]: Curation audio_gate approval is copied from the playback review artifact while source, translation, grammar, provenance, and sequence fields remain unchanged.

### Pending Todos

- Execute Phase 27 Plan 27-05 to expose audio readiness summaries and scanner-readable Phase 27 evidence.
- Repair broad-suite drift before treating full `python -m pytest -q` as authoritative again.

### Blockers/Concerns

- Latin TTS quality remains an explicit `classical_approx` caveat even after user approval; future higher-quality Latin audio should use a new review artifact.
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

Last session: 2026-06-08T17:00:26.636Z
Stopped at: Completed 27-04-PLAN.md
Resume file: None
