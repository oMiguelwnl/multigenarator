---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "06"
subsystem: korean-foundation-export
runtime: opencode
assurance: self_checked
tags: [korean, hangul, pronunciation, genanki, apkg, csv, tsv, immutable-snapshot, atomic-export, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "03"
    provides: Complete strict-i+1 Hangul and pronunciation source packs
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "04"
    provides: Hash-bound review/media gates and immutable active-snapshot boundary
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "05"
    provides: Exact shared nine-field phoneme mechanics and standalone 15-field Hangul template
provides:
  - One-resolution validated joins from an active immutable Korean foundation snapshot
  - Fixed collision-free Hangul and pronunciation model/deck identities with stable 32-hex GUIDs
  - Deterministic inspected APKG artifacts and atomic CSV/TSV bundles with exact media, checksums, GUIDs, and tags
  - Fail-before-write refusal for missing production activation and invalid snapshot/output/reference state
affects: [31-07, 31-08, 31-09, 31-10, 31-11, 31-12, phase-34-korean-export-evidence]
tech-stack:
  added: []
  patterns:
    - Resolve the fixed active pointer once and retain one typed immutable snapshot through every validation and write
    - Canonicalize and inspect APKG ZIP, media, and SQLite structure before atomic publication
    - Preserve exact tabular note schemas while carrying GUID/tags in a deterministic sidecar beside exact media/checksums
key-files:
  created:
    - src/multilang/services/korean_foundation_export.py
    - tests/services/test_korean_foundation_export.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-06-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Keep foundation export Korean-owned; do not extend generic, Japanese, Latin, Mandarin, or legacy phoneme exporters."
  - "Keep CSV/TSV table columns at the exact 15/9 note schemas and preserve GUID/tags in notes-metadata.json."
  - "Canonicalize ZIP metadata and inspect collection.anki2, media mapping, models, decks, notes, cards, GUIDs, tags, and bytes before APKG publication."
  - "Reject output inside the immutable snapshot and reject traversal, links/reparse points, dangling references, cross-kind media tags, and source identity drift before writing."
patterns-established:
  - "Successful fixture export is available only through a private typed-snapshot seam; the public API accepts family, format, and destination only."
  - "Tabular bundles contain one UTF-8 import table, notes-metadata.json, media-checksums.json, and a flat exact-byte media directory."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
requirements-completed: []
duration: 37min
completed: 2026-08-05
---

# Phase 31 Plan 06: Deterministic Korean Foundation Export Summary

**One immutable snapshot now produces fixed-identity Hangul and pronunciation notes plus deterministic, deeply inspected APKG/CSV/TSV artifacts, while production remains fail-closed until authorized activation.**

## Performance

- **Started:** 2026-08-05T22:34:59Z
- **Completed implementation/state checks:** 2026-08-05T23:12:09Z
- **Duration:** 37m 10s (reported as 37min)
- **Tasks:** 2/2
- **Implementation/test files created:** 2
- **Planning files updated:** 2, plus this summary
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Added exact fixed identities: Hangul model/deck `1762801001/1762801002` and pronunciation model/deck `1762801003/1762801004`, with exact deck names and globally unique source constants.
- Added frozen separate `HangulExportRow` and `KoreanPronunciationExportRow` schemas, exact 15/9 field mapping, escaped learner text, format-specific bounded media tags, canonical tags, Korean models/notes, and stable SHA-256 GUIDs based only on family/version/item key.
- Added one-resolution active-snapshot composition with source graph, immutable member, review-evidence, curation, media-manifest, exact-path, exact-byte, checksum, order, and reference validation.
- Added deterministic APKG generation with fixed genanki timestamps, canonical ZIP metadata, exact media packaging, SQLite model/deck/note/card inspection, and atomic file replacement.
- Added atomic CSV/TSV directory publication with five exact Anki headers, exact note fields, `notes-metadata.json`, `media-checksums.json`, and copied reviewed media whose references and bytes are re-inspected before publication.
- Proved all six missing-production-pointer combinations refuse before creating any requested file, directory, media sibling, checksum, or temporary artifact.

## Strict TDD Evidence

### Task 31-06-01: Join one active immutable snapshot into exact rows, identities, models, and notes

- **Initial RED:** Four focused tests failed because `multilang.services.korean_foundation_export` did not exist (`4 failed`).
- **Initial GREEN:** Fixed constants, exact row schemas, GUIDs, models, notes, escaped text, media tags, and tags produced `4 passed`.
- **Join RED:** Three tests failed because the one-resolution public builder and private typed-snapshot join did not exist (`3 failed, 6 passed`).
- **GREEN:** The validated snapshot join, review-evidence binding, exact media mapping, production refusal, and global ID scan produced `9 passed`.
- **Final task command:** `32 passed, 13 deselected in 32.75s` after the complete plan test surface was present.

### Task 31-06-02: Write and inspect deterministic APKG, CSV, and TSV media bundles atomically

- **Initial RED:** Twenty-one tests failed because APKG/tabular writers, format routing, result contracts, staged inspectors, and public export were absent (`21 failed, 9 passed`).
- **First GREEN attempt:** All tabular/refusal/atomic-failure cases passed, while four APKG cases exposed an open SQLite handle on Windows (`4 failed, 26 passed`).
- **GREEN:** Explicit SQLite connection closure fixed Windows cleanup and produced `30 passed`.
- **Second-pass RED/GREEN:** Source-version drift and traversal checks first produced `5 failed, 1 passed`, then `6 passed`; cross-kind/wrong-format media-tag checks first produced `4 failed`, then `6 passed`; immutable-snapshot output checks first produced `3 failed`, then `3 passed`.
- **Final task command:** `45 passed in 66.04s`.

No commits were created because the user prohibited Git delivery and destructive actions. RED/GREEN evidence is recorded here instead.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 filtered command | `32 passed, 13 deselected in 32.75s` |
| Complete Korean foundation exporter suite | `45 passed in 66.04s` |
| Korean curriculum/review/media/snapshot/phoneme/export matrix | `233 passed in 95.29s` |
| Generic/Latin/kana/phoneme/export regression matrix | `161 passed in 70.77s` |
| Python compile + trailing whitespace/tab scan | Passed for both new source/test files |
| Global fixed-ID scan | All four proposed IDs occur exactly once and collide with no production model/deck constant |
| Stub/forbidden provider/network scan | Clean for the production exporter |
| Generated artifact residue scan | No APKG/CSV/TSV, collection DB, or staging artifact remained in the repository |
| Phase lifecycle | `phase-status 31 in_progress` returned `changed: false` |
| Reviewed planning fingerprint | `9047c122350e28b17ff23275ee8bc7671a9c0fdc27510b2dbcb1b1394ecc9943` |

The regression matrix covered dedicated Korean export, Latin export, generic APKG/tabular export, export-row assembly, Japanese kana static/generated decks, shared phoneme mechanics, and Russian/Polish/Greek compatibility exports. These are archive/table/static contract checks only; no Anki Desktop/mobile import, rendering, responsiveness, or playback acceptance is claimed.

## Artifact Contracts

| Family | Model ID | Deck ID | Note type | Deck name | Fields | Cards in transient fixture | Required media |
|---|---:|---:|---|---|---:|---:|---:|
| Hangul | `1762801001` | `1762801002` | `Multilang::Korean Hangul Foundation` | `Multilang Korean::Foundations::Hangul` | 15 | 92 | 184 |
| Pronunciation | `1762801003` | `1762801004` | `Multilang::Korean Pronunciation i+1` | `Multilang Korean::Foundations::Pronunciation i+1` | 9 | 47 | 141 |

APKG archives contain canonical `collection.anki2`, `media`, and numbered exact-byte media members. CSV/TSV bundles contain the family table, `notes-metadata.json`, `media-checksums.json`, and `media/` with one file for every visible tag and no extras.

## Files Created/Modified

### Created

- `src/multilang/services/korean_foundation_export.py` - immutable-snapshot join, fixed identities, rows/models/notes, stable GUIDs, APKG/tabular writers, deep inspectors, and atomic publication.
- `tests/services/test_korean_foundation_export.py` - transient approved-shaped fixture plus join, identity, GUID, security, archive/SQLite, table/media/checksum, determinism, race, refusal, and no-partial-output proof.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-06-SUMMARY.md` - execution evidence and bounded handoff.

### Modified

- `.planning/SPEC.md` - records Plan 31-06 complete, production still inactive, and Plan 31-07 next.
- `.planning/.state-fingerprint.json` - reviewed planning-state baseline.

No generic exporter, runtime, database, Japanese, Mandarin, Latin, legacy phoneme, provider, CLI, or template file was modified.

## Decisions Made

- Reused `KoreanFoundationFamily` from the curriculum contract rather than introducing a second family identity.
- Kept the public production surface to `family`, `export_format`, and `output_destination`; successful transient tests use a private `ResolvedKoreanFoundationSnapshot` seam.
- Preserved exact table field schemas by placing tabular GUID/tag identity in `notes-metadata.json` rather than adding pseudo-fields to the Anki table.
- Refused pre-existing tabular bundle directories instead of performing a non-atomic recursive overwrite; publication is one inspected `os.replace` into an absent destination.
- Re-read and re-hashed source media immediately before secure staging, then re-verified staged/archive bytes to close the tested media race window.
- Forbid export destinations inside the immutable snapshot so an export cannot mutate its own validated evidence tree.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Windows cleanup bug] Closed the inspected SQLite connection explicitly**
- **Found during:** Task 31-06-02 first GREEN run.
- **Issue:** `sqlite3.Connection`'s context manager commits/rolls back but does not close; Windows retained a handle and blocked staged collection cleanup.
- **Fix:** Added explicit `connection.close()` before unlinking the temporary `collection.anki2`.
- **Files modified:** `src/multilang/services/korean_foundation_export.py`.
- **Verification:** The four failing APKG inspection/determinism cases became `4 passed`; final exporter suite produced `45 passed`.
- **Committed in:** Not committed; Git actions were explicitly disabled.

**2. [Rule 2 - Missing critical identity/path validation] Rejected source drift and output traversal before writes**
- **Found during:** Task 31-06-02 high-leverage mutation pass.
- **Issue:** A forged internal bundle could change a row source-pack version, and an output `Path` containing `..` could escape its apparent parent.
- **Fix:** Enforced exact family source-pack versions, item-key/stage identity, and explicit parent-traversal rejection before staging.
- **Files modified:** `src/multilang/services/korean_foundation_export.py`, `tests/services/test_korean_foundation_export.py`.
- **Verification:** RED was `5 failed, 1 passed`; GREEN was `6 passed`; all no-output assertions passed.
- **Committed in:** Not committed; Git actions were explicitly disabled.

**3. [Rule 2 - Missing critical media/snapshot boundary] Bound media tags to kind/format and protected immutable input**
- **Found during:** Task 31-06-02 security second pass.
- **Issue:** The initial bounded-tag grammar did not distinguish WAV sound fields from PNG/GIF image fields, and a caller could select an output location inside the snapshot being validated.
- **Fix:** Added field-specific sound/image grammars and rejected every resolved output destination at or beneath the immutable snapshot root.
- **Files modified:** `src/multilang/services/korean_foundation_export.py`, `tests/services/test_korean_foundation_export.py`.
- **Verification:** Media RED was `4 failed` then GREEN `6 passed`; snapshot-output RED was `3 failed` then GREEN `3 passed`; final suite produced `45 passed`.
- **Committed in:** Not committed; Git actions were explicitly disabled.

---

**Total deviations:** 3 auto-fixed (1 Rule 1 bug, 2 Rule 2 missing critical safeguards).
**Impact on plan:** All fixes were required for deterministic cleanup, identity integrity, path safety, and immutable evidence protection. No generic surface, provider, runtime, schema, UI, or content scope was added.

## Issues Encountered

- A diagnostic command initially hit Windows CP1252 stdout encoding while printing Korean source records. Setting `PYTHONIOENCODING=utf-8` confirmed the data was valid; no repository code change was needed.
- The repository remains intentionally dirty from prior completed Korean/Mandarin work. Only the two Plan 31-06 implementation/test files and the required planning handoff files were touched by this execution.

## Security and Privacy Review

- Plain learner text is HTML-escaped; only exact basename-only WAV sound tags and PNG/GIF image tags survive unescaped.
- Snapshot roles, declared/resolved members, object bytes, hashes, review-evidence hashes, media manifests, filesystem paths, current bytes, and staged bytes are cross-checked before publication.
- Output rejects traversal, unsafe existing links/reparse points, non-regular APKG targets, pre-existing tabular directories, and any destination inside the immutable snapshot.
- APKG ZIP members reject duplicates/traversal and are inspected without unsafe extraction; SQLite is opened only from a securely created local staging file and closed before cleanup.
- Diagnostics expose bounded family/item/gate/media-kind identifiers only; no source text, local snapshot path, reviewer payload, provider secret, or credential is emitted.
- No network, provider, synthesis, translation, analysis, authentication, endpoint, database schema, or private-highlight surface was introduced. Every new trust surface was already represented in the Plan 31-06 threat register, so there are no additional threat flags.

## Known Stubs

None. Empty Hangul picture/GIF fields are intentional optional media slots in the locked schema, not missing required output. The absent active production pointer and pending genuine review/media are deliberate fail-closed approval boundaries for Plans 31-07 through 31-12, not implementation stubs.

## Task Commits and Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other Git delivery/destructive action was performed.

## Authentication Gates

None.

## User Setup Required

None. The exporter makes no provider/network call and requires no credential, database, Anki runtime, production media acquisition, or manual visual check in this plan.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-06 complete and Plan 31-07 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; Phase 31 remains open at `[-]`.
- `node .planning/bin/gsdd.mjs session-fingerprint write` produced `9047c122350e28b17ff23275ee8bc7671a9c0fdc27510b2dbcb1b1394ecc9943`.
- KHAN-01, KHAN-02, KPRO-01, and KPRO-02 are advanced but remain unchecked: successful transient fixtures prove machinery only, while later plans own real requests/evidence/media, authorization, activation, and observed Anki acceptance.
- `.planning/STATE.md` and requirement checkboxes were not advanced because Phase 31 remains open and the established user-directed handoff is SPEC/fingerprint only.

## Next Phase Readiness

- Plan 31-07 can consume the exact candidate item/media/version/hash sets and create exhaustive pending review requests without changing exporter machinery.
- Plans 31-08 through 31-12 can use the private transient seam for engineering tests while preserving the fixed public one-resolution production boundary.
- No Plan 31-06 engineering blocker remains.
- Production remains deliberately inactive and non-learner-ready until genuine qualified review, rights, licensed media, exact playback evidence, snapshot preparation, authorization, and activation complete.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Strict TDD gates passed. The final task commands produced 32 filtered and 45 complete exporter passes; Korean gate regressions produced 233 passes; generic/Latin/kana/phoneme/export regressions produced 161 passes; compile, whitespace, stub/provider/network, fixed-ID, exact-byte, deterministic archive/table, race, path, no-partial-output, phase-status, and planning-fingerprint checks passed.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: passed
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: SQLite context-manager exit did not close the inspected collection on Windows; explicit closure restored secure staging cleanup.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The first writer validation omitted exact row source-version identity and explicit `..` output rejection; both were added before publication.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The initial bounded media grammar allowed cross-kind tags and did not prohibit writing into immutable input; kind-specific tags and snapshot-root exclusion now enforce both boundaries.
</deltas>

<judgment>
<active_constraints>
Preserve the Phase 30 canonical `ko` identity, Plan 31-04 one-resolution immutable snapshot and genuine-evidence boundary, and Plan 31-05 exact 15/9 schemas. Production accepts no source/path override and stays blocked without the fixed active pointer. Successful transient fixture artifacts are machinery evidence only and must never be promoted to production evidence.
</active_constraints>
<unresolved_uncertainty>
Qualified reviewers, Portuguese policy, media rights, real licensed bytes, playback receipts, canonical evidence intake, snapshot preparation, authorization, activation, and observed Anki Desktop/mobile import/render/playback remain Plan 31-07 onward or Phase 34 work. Archive/SQLite/table inspection cannot establish learner-facing appearance or playback quality.
</unresolved_uncertainty>
<decision_posture>
Prefer a dedicated fail-before-write Korean exporter, fixed identities, immutable joins, exact media bytes, deterministic staged artifacts, deep self-inspection, and narrow public inputs over generic-exporter reuse or approval bypasses. Keep technical fixture proof sharply separated from genuine human/legal/media evidence.
</decision_posture>
<anti_regression>
Do not change the four fixed IDs, exact deck/note names, 15/9 schemas, stable GUID input, canonical tags, one-resolution public boundary, snapshot-root exclusion, exact media/checksum/reference checks, inspected atomic publication, or production refusal. Do not route foundations through generic/Japanese/Latin/Mandarin/legacy phoneme exporters or claim visual/import/playback acceptance from structural tests.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Both implementation/test files and this summary exist at the planned paths and compile successfully.
- The final post-summary exporter rerun produced `45 passed in 67.88s`.
- The required `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>` sections are present and match the executed runtime/assurance.
- The production active pointer and immutable snapshot tree remain absent, so production still refuses rather than consuming top-level candidates.
- Phase 31 remains open, SPEC points to Plan 31-07, and the reviewed planning fingerprint remains `9047c122350e28b17ff23275ee8bc7671a9c0fdc27510b2dbcb1b1394ecc9943`.
- Repository HEAD remains unchanged because Git delivery was explicitly disabled; no commit claim is made.

---
*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 06*
*Completed: 2026-08-05*
