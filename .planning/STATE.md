---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Audit
status: executing
stopped_at: None
last_updated: "2026-05-07T14:32:59Z"
last_activity: 2026-05-07 -- Phase 15 completed
progress:
  total_phases: 9
  completed_phases: 8
  total_plans: 30
  completed_plans: 30
  percent: 94
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-06)

**Core value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Current focus:** Phase 16 — End-to-End v1.2 Audit

## Current Position

Phase: 16
Plan: Not started
Status: Ready to plan
Last activity: 2026-05-07 -- Phase 15 completed

Progress: [█████████░] 94%

## Performance Metrics

**Velocity:**

- Total plans completed: 52
- v1.0 plans completed: 34
- v1.1 plans completed: 4
- Best-effort task count from v1.0 summaries: 68
- v1.2 planned phases: 8
- v1.2 requirements mapped: 24/24

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-job-orchestration-recovery | 6 | 34 min | 6 min |
| 02-input-decks-lexical-grounding | 5 | 2h 7m | 25 min |
| 03-sentence-quality-review-loop | 5 | 1h 17m | 15 min |
| 04-audio-synthesis | 5 | 1h 3m | 13 min |
| 05-anki-safe-export-contract | 5 | 17 min | 3 min |
| 06-end-to-end-text-acceptance-pipeline | 4 | 40 min | 10 min |
| 07-milestone-evidence-audit-hygiene | 4 | 20 min | 5 min |
| 08-card-quality-refresh | 4 | complete | complete |
| 10 | 4 | - | - |
| 12 | 4 | - | - |
| 13 | 3 | - | - |

**Recent Trend:**

- Last completed milestone work: Phase 08 Card Quality Refresh completed 2026-05-02.
- Trend: v1.2 begins from a stable card-quality refresh but must protect existing frequency/custom flows while adding highlights.

| Phase 10 P01 | unknown | 2 tasks | 5 files |
| Phase 10 P02 | unknown | 2 tasks | 3 files |
| Phase 10 P03 | unknown | 2 tasks | 5 files |
| Phase 10 P04 | unknown | 2 tasks | 2 files |
| Phase 11-highlight-pipeline-integration P01 | unknown | 2 tasks | 4 files |
| Phase 11-highlight-pipeline-integration P02 | unknown | 2 tasks | 4 files |
| Phase 11-highlight-pipeline-integration P03 | unknown | 2 tasks | 4 files |
| Phase 11-highlight-pipeline-integration P04 | unknown | 2 tasks | 5 files |
| Phase 12-highlight-generation-audio-and-qa P01 | 18min | 2 tasks | 4 files |
| Phase 12-highlight-generation-audio-and-qa P02 | 22min | 2 tasks | 10 files |
| Phase 12-highlight-generation-audio-and-qa P03 | 15min | 2 tasks | 4 files |
| Phase 12-highlight-generation-audio-and-qa P04 | 18min | 2 tasks | 6 files |
| Phase 13-highlight-export-and-template P01 | 3min | 2 tasks | 3 files |
| Phase 13-highlight-export-and-template P02 | 2min | 2 tasks | 2 files |
| Phase 13-highlight-export-and-template P03 | 2min | 2 tasks | 3 files |
| Phase 14-webdav-highlight-fetch-adapter P01 | 25min | 2 tasks | 5 files |
| Phase 14-webdav-highlight-fetch-adapter P02 | 25min | 2 tasks | 2 files |
| Phase 14-webdav-highlight-fetch-adapter P03 | 25min | 2 tasks | 2 files |
| Phase 14-webdav-highlight-fetch-adapter P04 | 25min | 2 tasks | 4 files |
| Phase 15-phonetics-template-refresh P01 | 12min | 2 tasks | 3 files |
| Phase 15-phonetics-template-refresh P02 | 28min | 3 tasks | 4 files |

## Accumulated Context

### Decisions

Full decision history is in `.planning/PROJECT.md` and `.planning/milestones/v1.0-ROADMAP.md`. Current carry-forward decisions:

- Keep the core value centered on trustworthy multilingual Anki card generation.
- Keep Python/uv as the implementation backbone.
- Keep Tatoeba secondary-only behind filtering, reranking, and validation.
- Keep Azure Speech as the primary audio direction with documented fallback behavior.
- Preserve existing frequency-deck and custom word-list behavior while adding highlights as a third input mode.
- Normalize Kindle highlights locally instead of depending on the external Kindle Formatter website.
- Treat WebDAV credentials, raw highlight exports, book metadata, and private reading text as sensitive data that must be redacted from logs, prompts, reports, artifacts, and commits.
- Use dedicated highlight export/template behavior rather than mutating the normal deck note type.
- Keep the phonetics template refresh isolated from normal and highlight deck generation.
- Source-specific behavior is resolved through explicit `SourceProfile` contracts rather than implicit string fallback branches.
- `kindle-highlights` is internally representable for domain/export isolation but remains blocked from the user-facing CLI until Phase 11.
- Highlight exports must use a dedicated note model and omit `Translation`; mixed-source exports fail closed.
- Future highlight/WebDAV diagnostics should use `multilang.security.redaction` before logging/reporting private data.
- Unsupported source-profile errors omit rejected private/path-bearing input entirely and list only safe supported source keys.
- [Phase 10]: Store Kindle parser provenance source paths as file names rather than absolute paths to avoid leaking private local paths.
- [Phase 10]: Keep highlight candidate extraction provider-free and DB-free with deterministic in-module stopword filtering.
- [Phase 10]: Expose Kindle highlights only through a count-only preview command while keeping generate --source kindle-highlights blocked until Phase 11.
- [Phase 10]: Use synthetic fixture and count-only evidence to prove local Kindle normalization without committing private exports.
- [Phase 11-highlight-pipeline-integration]: Highlight candidates use source content hash plus lemma hash instead of sequence-only keys.
- [Phase 11-highlight-pipeline-integration]: Persist normalized highlight text only in private import records; manifests stay hash/count-only.
- [Phase 11-highlight-pipeline-integration]: Public CLI accepts highlights while internal profile remains kindle-highlights.
- [Phase 12-highlight-generation-audio-and-qa]: Validation behavior is resolved through SourceProfile contracts before deterministic checks, including translation-required and sentence-token policies.
- [Phase 12-highlight-generation-audio-and-qa]: Highlight prompt context is retrieved by safe highlight id and redacted/bounded before any generation adapter receives it.
- [Phase 12-highlight-generation-audio-and-qa]: Provider and local highlight generation carry source_type metadata so downstream QA can distinguish highlight output.
- [Phase 12-highlight-generation-audio-and-qa]: Highlight export rows use source profile export policy to blank Translation while preserving audio, IPA/spoken form, definitions, sentence, and Image.
- [Phase 12-highlight-generation-audio-and-qa]: Review reports include safe source_type and translation_required fields while redacting text fields before serialization.
- [Phase 13-highlight-export-and-template]: Keep normal frequency and word-list templates on CARD_TEMPLATE.md while routing kindle-highlights to HIGHLIGHT_CARD_TEMPLATE.md through SourceProfile.template_name.
- [Phase 13-highlight-export-and-template]: Validate template references against the resolved export field tuple and allow only FrontSide as a non-field Anki helper.
- [Phase 13-highlight-export-and-template]: APKG model creation now delegates template selection to load_card_template(source_type=...) so SourceProfile remains the single routing contract.
- [Phase 13-highlight-export-and-template]: Template loader validation errors are surfaced as ExportAnkiPackageError at the APKG boundary for clear pre-write failure behavior.
- [Phase 13-highlight-export-and-template]: Treat highlight CSV/TSV import metadata as a strict contract equal to APKG template/model wiring.
- [Phase 13-highlight-export-and-template]: Use synthetic highlight rows and local temporary audio for evidence so export tests do not leak private reading text or paths.
- [Phase 14-webdav-highlight-fetch-adapter]: WebDAV credentials are env-only settings; no CLI username or secret flags are exposed.
- [Phase 14-webdav-highlight-fetch-adapter]: WebDAV list/fetch behavior is isolated behind an injectable transport so tests and evidence never require live credentials.
- [Phase 14-webdav-highlight-fetch-adapter]: Fetched WebDAV exports are cached under ignored `.multilang/highlights/cache/` using SHA-256 content identity before entering the existing Kindle highlight parser/ingest path.
- [Phase 14-webdav-highlight-fetch-adapter]: `--webdav-remote-path` is valid only with public `--source highlights` and mutually exclusive with local `--input-file`.
- [Phase 15-phonetics-template-refresh]: Russian phonetics exports use a refreshed nine-field note contract while keeping `sort_index` internal for ordering and GUIDs.
- [Phase 15-phonetics-template-refresh]: Phonetics sentence translation follows the v1 hidden-front and `{{FrontSide}}` back-reveal pattern, with neutral/purple styling inspired by `fonetico.md`.

### Pending Todos

- Plan Phase 10 local Kindle normalization using Phase 09 source-profile and redaction boundaries, including the T-09-02 omit-unsafe-input error pattern.
- Keep v1.2 requirement coverage at 24/24 as phases are planned and executed.
- Preserve Phase 08 completion information until v1.1 is archived.

### Blockers/Concerns

- Broad pytest collection now succeeds (`uv run pytest --collect-only -q` collected 247 tests during Phase 09), but future phases should keep the Phase 09 evidence commands green before relying on wider execution.
- Exact Kindle export shapes still need real fixture validation; Phase 10 should be fixture-driven and fail closed for malformed or unsafe highlight fragments.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260421-001 | implement Tatoeba as a filtered secondary sentence source with advanced reranking and validation, never as the raw default primary source | 2026-04-23 | b833e22 | Verified | [260421-001-tatoeba-filtered-secondary-source](./quick/260421-001-tatoeba-filtered-secondary-source/) |

## Deferred Items

Items acknowledged and carried forward from v1.0 milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| tests | full-suite runtime template adapter import drift | resolved by Phase 09 collect-only evidence | 2026-05-04 |

## Session Continuity

Last session: 2026-05-07T14:32:59Z
Stopped at: Completed 15-02-PLAN.md
Resume file: None
