---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Card Quality Remediation and Deck Validation
status: milestone_complete
stopped_at: v1.3 milestone completed and archived
last_updated: "2026-05-16T17:56:48.493Z"
last_activity: 2026-05-16
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 16
  completed_plans: 16
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-16)

**Core value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Current focus:** Define the next milestone with `/gsd-new-milestone`

## Current Position

Phase: Next milestone
Plan: Not started
Status: v1.3 milestone complete — ready for next milestone definition
Last activity: 2026-05-16

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 68
- v1.0 plans completed: 34
- v1.1 plans completed: 4
- v1.2 planned phases: 8
- v1.2 requirements mapped: 24/24
- v1.3 plans completed: 16
- v1.3 requirements mapped: 15/15

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 17. Deck Quality Audit and Issue Reports | 0 | TBD | N/A |
| 18. Text Field Remediation | 0 | TBD | N/A |
| 19. Normal Card Export and Responsive Template | 0 | TBD | N/A |
| 20. Word Audio Integrity Gate | 0 | TBD | N/A |
| 21. Validation Fixtures and Milestone Evidence | 0 | TBD | N/A |
| 18 | 3 | - | - |
| 19 | 3 | - | - |
| 20 | 3 | - | - |
| 21 | 4 | - | - |

**Recent Trend:**

- Last completed milestone work: Phase 16 End-to-End v1.2 Audit completed 2026-05-08.
- Trend: v1.3 begins from completed highlight/template work and focuses on correcting known card-quality defects found in generated decks.

| Phase 17 P03 | 20min | 3 tasks | 2 files |
| Phase 18 P01 | unknown | 2 tasks | 4 files |
| Phase 18 P03 | unknown | 2 tasks | 3 files |
| Phase 19 P01 | 22min | 2 tasks | 6 files |
| Phase 19 P02 | 16min | 2 tasks | 3 files |
| Phase 18 P02 | unknown | 2 tasks | 5 files |
| Phase 19 P03 | 18min | 2 tasks | 1 files |
| Phase 20 P01 | 14min | 2 tasks | 2 files |
| Phase 20 P02 | 4min | 2 tasks | 2 files |
| Phase 20 P02 | 4min | 2 tasks | 2 files |
| Phase 20 P03 | 7min | 2 tasks | 4 files |
| Phase 20 P03 | 8min | 2 tasks | 4 files |
| Phase 21 P01 | 3min | 2 tasks | 2 files |
| Phase 21 P02 | 4min | 2 tasks | 4 files |
| Phase 21 P03 | 7min | 2 tasks | 3 files |
| Phase 21 P04 | 2min | 2 tasks | 3 files |

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
- [Phase 13-highlight-export-and-template]: APKG model creation delegates template selection to load_card_template(source_type=...) so SourceProfile remains the single routing contract.
- [Phase 13-highlight-export-and-template]: Template loader validation errors are surfaced as ExportAnkiPackageError at the APKG boundary for clear pre-write failure behavior.
- [Phase 13-highlight-export-and-template]: Treat highlight CSV/TSV import metadata as a strict contract equal to APKG template/model wiring.
- [Phase 13-highlight-export-and-template]: Use synthetic highlight rows and local temporary audio for evidence so export tests do not leak private reading text or paths.
- [Phase 14-webdav-highlight-fetch-adapter]: WebDAV credentials are env-only settings; no CLI username or secret flags are exposed.
- [Phase 14-webdav-highlight-fetch-adapter]: WebDAV list/fetch behavior is isolated behind an injectable transport so tests and evidence never require live credentials.
- [Phase 14-webdav-highlight-fetch-adapter]: Fetched WebDAV exports are cached under ignored `.multilang/highlights/cache/` using SHA-256 content identity before entering the existing Kindle highlight parser/ingest path.
- [Phase 14-webdav-highlight-fetch-adapter]: `--webdav-remote-path` is valid only with public `--source highlights` and mutually exclusive with local `--input-file`.
- [Phase 15-phonetics-template-refresh]: Russian phonetics exports use a refreshed nine-field note contract while keeping `sort_index` internal for ordering and GUIDs.
- [Phase 15-phonetics-template-refresh]: Phonetics sentence translation follows the v1 hidden-front and `{{FrontSide}}` back-reveal pattern, with neutral/purple styling inspired by `fonetico.md`.
- [Phase 16-end-to-end-v12-audit]: Local highlight audit evidence uses only synthetic Kindle fixtures, tmp_path media, and deterministic fakes while tying APKG/CSV/TSV assertions to the same assembled highlight row.
- [Phase 16-end-to-end-v12-audit]: Final audit wrappers re-execute phonetics, frequency, custom, CLI, and highlight privacy evidence while asserting source field tuples and note types remain isolated.
- [Phase 16-end-to-end-v12-audit]: Final v1.2 audit evidence is scanner-readable and self-tested for 24/24 requirement coverage, command references, privacy marker exclusions, pass signals, and caveats.
- [v1.3]: Treat IPA repetition, morphology-only definitions, translation mismatches, and audio/word mismatches as validation failures before export.
- [v1.3]: Remove redundant `Front of Card` from normal generated-card exports while keeping highlight and phonetics behavior isolated.
- [v1.3]: Use `card_issues_normalized.md` and the known APKG as the normalized defect catalog for remediation evidence.
- [Phase 17]: Known APKG audit evidence is generated under ignored .multilang/audits because reports may contain private deck excerpts.
- [Phase 17]: The audit-deck command composes APKG reader, Definition issue detector, and deterministic report writer without invoking mutation services.
- [Phase 18]: Keep spoken_form available for audio/provenance but never append it to exported IPA.
- [Phase 18]: Use conservative length and definition-gloss heuristics to reject isolated-word translations only when the source sentence has enough context.
- [Phase 19]: Keep ExportCardRow.front_of_card as backward-compatible construction data while excluding it from normal exports.
- [Phase 19]: Use a dedicated .exampleSentenceLine flex row so sentence audio stays beside the example text without overflow.
- [Phase 18]: Keep definition remediation deterministic and provider-free, correcting known senses or falling back to substantive lexical source definitions.
- [Phase 19]: Use synthetic tmp_path artifact evidence for normal template/export regression coverage.
- [Phase 20]: Word audio integrity is exact-match only; stored display text, normalized display text, TTS text, and provenance hashes must match exported Word.
- [Phase 20]: Reusable WORD audio is accepted only after passing the exact Word integrity helper; mismatches are regenerated and excluded from reuse counts.
- [Phase 20]: Assembly validates word audio against lexical_candidate.lemma, and runtime export refreshes persisted audio rows before validating snapshots.
- [Phase 21]: Reuse existing text, template, and audio validators through a thin v1.3 facade instead of duplicating detection logic.
- [Phase 21]: Normalize validator output into bounded issue objects with stable enum values for downstream fixtures and evidence.
- [Phase 21]: Use the shared v1.3 validation facade for fixture execution while extending existing validator boundaries where fixtures exposed missing correctness checks. — Keeps VAL-02 fixtures tied to one validation surface while closing correctness gaps discovered by executable examples.
- [Phase 21]: Keep VAL-02 fixture data synthetic and traceable to card_issues_normalized.md source lines instead of private APKG excerpts. — Preserves evidence quality without leaking private deck contents.
- [Phase 21]: Use focused scanner-readable command references for milestone closeout instead of embedding private audit report contents. — Preserves milestone evidence quality without committing private deck text.
- [Phase 21]: Assert existing deck-mode safety through exported field tuples and note/template boundaries rather than duplicating validation logic. — Keeps VAL-03 tied to source-of-truth export contracts.
- [Phase 21]: Detect sentence_audio references with a bounded whitespace-tolerant Anki field regex — Closes the valid Anki whitespace formatting bypass without changing public issue taxonomy.
- [Phase 21]: Preserve dangling-template-field precedence before sentence_audio layout validation — Invalid template references still report dangling_template_field instead of layout issues.

### Pending Todos

- Define the next milestone with fresh requirements and roadmap.
- Repair broad-suite drift before treating full `python -m pytest -q` as authoritative again.

### Blockers/Concerns

- Known follow-up debt from PROJECT.md: full-suite collection drift remains in tests that import removed private runtime template adapters; focused milestone evidence should stay authoritative until broad suite drift is repaired.
- Research was explicitly skipped for v1.3; do not treat existing `.planning/research/SUMMARY.md` as current v1.3 research.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260421-001 | implement Tatoeba as a filtered secondary sentence source with advanced reranking and validation, never as the raw default primary source | 2026-04-23 | b833e22 | Verified | [260421-001-tatoeba-filtered-secondary-source](./quick/260421-001-tatoeba-filtered-secondary-source/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Test suite drift | Full-suite collection drift in tests importing removed private runtime template adapters | Known debt | Pre-v1.3 |
| quick_task | 260430-001-russian-card-quality-regression | missing | v1.3 closeout 2026-05-16 |

## Session Continuity

Last session: 2026-05-16T17:56:48.493Z
Stopped at: v1.3 milestone completed and archived
Resume file: None
