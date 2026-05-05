# Phase 11: Highlight Pipeline Integration - Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 11 turns locally normalized KOReader-on-Kindle highlight candidates into a duplicate-safe `highlights` deck mode inside the existing Multilang job and lexical grounding pipeline. This phase covers public CLI mode wiring, stable import identity, import manifests, visible duplicate/reuse/blocking counts, private provenance persistence, and resume/rerun behavior. It does not cover highlight text generation quality, audio synthesis, Anki export/template behavior, WebDAV fetching, phonetics templates, or interactive candidate review.

</domain>

<decisions>
## Implementation Decisions

### CLI Mode Shape
- **D-01:** Expose the user-facing generation mode as `generate --source highlights`, not `kindle-highlights` or `koreader-highlights`. The user clarified they are using KOReader on Kindle, so the public deck mode should stay generic while KOReader/Kindle remains an importer/parser detail.
- **D-02:** Reuse `--input-file` for local highlight generation input. Do not add a new required `--highlight-file` flag in Phase 11.
- **D-03:** Keep `preview-kindle-highlights` as a separate count-only preflight command after `generate --source highlights` is enabled. Preview must remain side-effect-free.
- **D-04:** Persist/audit the existing internal source profile key `kindle-highlights` while mapping the public CLI alias `highlights` to that profile. Do not rename the internal `SourceProfile` key unless implementation research finds a concrete compatibility need.

### Duplicate Identity and Import Manifests
- **D-05:** The same normalized highlight content counts as the same import on rerun, even if the source file name or path changes.
- **D-06:** Candidate identity must not depend only on first-seen sequence numbers. If KOReader exports the same highlight content in a different order, the same word from the same source content must be recognized as the existing planned card.
- **D-07:** Across separate highlight imports, skip duplicates when the same normalized source content/candidate is re-imported, but allow the same word to become a distinct candidate when it comes from genuinely different reading context.
- **D-08:** Stable import manifests should contain hashes, candidate keys, and counts only. They must not contain raw highlight text, private snippets, absolute local paths, credentials, or book metadata.

### Import Summary
- **D-09:** `generate --source highlights` should print stable `key=value` summary lines, matching the existing CLI summary style and Phase 10 preview output.
- **D-10:** The default summary should be counts-only. Do not print candidate word lists, highlight snippets, source paths, or book metadata by default.
- **D-11:** If some candidates are blocked but others are usable, continue with usable candidates and report blocked counts/reasons. Do not fail the whole import unless there are no usable candidates or the import itself is unsafe/malformed.
- **D-12:** The visible summary must distinguish the full Phase 11 lifecycle: imported highlights, rejected highlights, extracted candidates, duplicate candidates, reused existing candidates/cards, newly planned candidates/cards, blocked candidates, and planned cards.

### Grounding and Provenance
- **D-13:** Ungrounded highlight candidates should be blocked/reported, not backfilled, replaced, or silently skipped. Frequency-deck backfill behavior must not leak into highlight mode.
- **D-14:** Phase 11 should run highlight mode through job creation/resume, import normalization, candidate extraction, lexical grounding, duplicate prevention, and planning/persistence only. Phase 12 owns generated examples, validation, audio, and highlight QA.
- **D-15:** Store normalized highlight text privately in the DB for later Phase 12 context/audit use, but never print it in CLI summaries, commit it to repo artifacts, include it in import manifests, or expose it in logs/errors/reports without redaction.
- **D-16:** Candidate-level provenance should preserve source content hash, first source index/highlight id, occurrence count, and import manifest identity. Raw highlight text stays in private internal storage, not in candidate rows, summary output, or safe manifests.

### the agent's Discretion
- Exact schema/table names for private highlight storage and safe import manifests.
- Exact candidate-key algorithm, as long as it is stable across same-content reorders and respects D-05 through D-08.
- Exact `key=value` counter names, as long as every lifecycle category in D-12 is represented.
- Exact service/repository split, as long as the existing CLI -> runtime service -> repository pattern is preserved.
- Exact test fixture names and focused verification commands, as long as existing frequency/custom regression boundaries remain covered.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` - Phase 11 goal, dependency on Phase 10, requirements `MODE-01` and `INGEST-04`, and success criteria for highlights mode, duplicate prevention, import summary, and provenance.
- `.planning/REQUIREMENTS.md` - v1.2 requirement definitions, especially `MODE-01`, `INGEST-04`, `MODE-02`, `GEN-03`, and out-of-scope constraints for translations, images, WebDAV, and private highlight data.
- `.planning/PROJECT.md` - Product constraints, current v1.2 milestone goal, key decisions to add highlights as a new mode while preserving existing flows, and privacy/security expectations.
- `.planning/STATE.md` - Carry-forward decisions from Phases 09 and 10, including internal `kindle-highlights` gating, source-profile boundaries, redaction requirements, and Phase 10 local normalization decisions.

### Prior Phase Contracts
- `.planning/phases/01-job-orchestration-recovery/01-CONTEXT.md` - CLI-first single-command shape, progress counters, resume behavior, and duplicate-safe rerun policy.
- `.planning/phases/02-input-decks-lexical-grounding/02-CONTEXT.md` - Lexical identity, custom input preservation, missing lexical data policy, and grounding persistence expectations.
- `.planning/phases/03-sentence-quality-review-loop/03-CONTEXT.md` - Confirms text generation/validation is a separate downstream stage, supporting the Phase 11 boundary of grounding only.
- `.planning/phases/09-source-profiles-privacy-regression-boundary/09-SECURITY.md` - Threat model and mitigations for source profiles, private highlight data, redaction, CLI gating, and existing-mode isolation.
- `.planning/phases/09-source-profiles-privacy-regression-boundary/09-REGRESSION-EVIDENCE.md` - Focused regression commands protecting explicit source profiles, export isolation, redaction, and existing frequency/custom flows.
- `.planning/phases/10-local-kindle-normalization-and-candidate-extraction/10-LOCAL-KINDLE-EVIDENCE.md` - Phase 10 evidence for parser -> candidate extraction -> preview counts, synthetic fixtures, safe rejection output, and current generation gating.
- `.planning/phases/10-local-kindle-normalization-and-candidate-extraction/10-04-SUMMARY.md` - Confirms preview side-effect boundaries and local Kindle/KOReader flow evidence.

### Existing Code Entry Points
- `src/multilang/cli.py` - Current `generate` CLI gate, `preview-kindle-highlights`, `load_requested_item_keys`, request validation, and summary output.
- `src/multilang/domain/source_profiles.py` - Existing internal `kindle-highlights` source profile and export/privacy flags.
- `src/multilang/domain/highlights.py` - Normalized highlight, highlight candidate, and import preview contracts from Phase 10.
- `src/multilang/services/kindle_highlight_parser.py` - Local HTML/text parser and privacy-safe normalized highlight contracts.
- `src/multilang/services/highlight_candidate_extraction.py` - Current deterministic extraction, duplicate counting, and first-seen candidate key behavior that Phase 11 must harden for reorder-safe identity.
- `src/multilang/services/highlight_import_preview.py` - Current count-only preview service.
- `src/multilang/services/generate_job.py` - Existing run key, source fingerprint, resume, rerun, and duplicate partitioning behavior.
- `src/multilang/services/ingest_lexical_items.py` - Existing frequency/word-list ingestion and grounding integration point to extend for highlights.
- `src/multilang/repositories/job_repository.py` - Existing persisted job/item counters, item success/failure state, duplicate skips, and resume validation.
- `src/multilang/repositories/lexical_repository.py` - Existing lexical candidate persistence and provenance JSON shape.
- `src/multilang/db/models.py` - Current persistence model for jobs, items, lexical candidates, text, audio, and exports.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/multilang/domain/source_profiles.py` already defines the internal `kindle-highlights` profile with no translation export and highlight template metadata.
- `src/multilang/domain/jobs.py` already allows `GenerationRequest.source_type` to be `kindle-highlights`, even though the public CLI still blocks it.
- `src/multilang/services/kindle_highlight_parser.py`, `src/multilang/services/highlight_candidate_extraction.py`, and `src/multilang/services/highlight_import_preview.py` provide the Phase 10 parser/extractor/preview path to reuse.
- `src/multilang/services/generate_job.py` and `src/multilang/repositories/job_repository.py` already provide run-key-based rerun/resume/duplicate partitioning.
- `src/multilang/repositories/lexical_repository.py` can persist highlight lexical candidates with source type and provenance once highlight grounding is wired.
- `src/multilang/security/redaction.py` and Phase 09 tests provide the redaction boundary for future highlight diagnostics.

### Established Patterns
- The shipped operator surface is CLI-first and centered on `multilang generate` plus flags.
- CLI output favors stable `key=value` counters rather than prose summaries.
- Runtime composition follows CLI -> runtime service -> service/repository boundaries with SQLAlchemy persistence.
- Existing modes must remain stable while new source behavior is added through explicit source-profile logic.
- Resume/rerun safety depends on deterministic item keys, source fingerprints, run keys, and persisted item stage state.

### Integration Points
- `src/multilang/cli.py` must accept public `--source highlights`, validate `--input-file`, and map it to internal `kindle-highlights` behavior without enabling WebDAV.
- `src/multilang/services/ingest_lexical_items.py` is the likely Phase 11 service boundary for parsing local highlight input, extracting candidates, grounding them, and advancing only to the appropriate post-grounding state.
- `src/multilang/services/input_fingerprint.py` and `src/multilang/services/generate_job.py` must be updated or wrapped so highlight run identity is based on normalized content/candidate hashes, not raw file paths or order-only keys.
- `src/multilang/db/models.py` likely needs private highlight import/provenance storage for normalized text plus safe manifest metadata.
- `tests/integration/test_v12_existing_mode_regression_boundary.py` currently asserts `generate --source kindle-highlights` is blocked; Phase 11 must update this boundary to allow public `highlights` while preserving frequency/custom behavior.

</code_context>

<specifics>
## Specific Ideas

- The user's real source is KOReader on Kindle. Avoid hard-coding assumptions that only fit official Kindle exports when naming the public deck mode or planning future importer evolution.
- Public mode name: `highlights`.
- Internal source/profile key: `kindle-highlights`.
- Local file input: `--input-file`.
- Preview command remains: `preview-kindle-highlights`.
- Summary style remains count-only `key=value` lines.

</specifics>

<deferred>
## Deferred Ideas

- WebDAV fetching, remote listing, auth/path/network error distinctions, and WebDAV sync summaries remain Phase 14.
- Highlight text/example generation, validation, audio, and QA remain Phase 12.
- Highlight APKG/CSV/TSV export, dedicated note type, field names, and template behavior remain Phase 13.
- Interactive candidate approval/rejection UI remains a future requirement, not Phase 11.
- Bilingual highlight decks or adding `Translation` to highlight cards remain out of scope for v1.2.

</deferred>

---

*Phase: 11-highlight-pipeline-integration*
*Context gathered: 2026-05-05*
