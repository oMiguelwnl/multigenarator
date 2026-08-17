---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "04"
subsystem: korean-foundation-review-media-snapshots
runtime: opencode
assurance: self_checked
tags: [korean, human-review, media-integrity, immutable-snapshot, sha256, path-security, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "03"
    provides: Complete hash-bound 92-item Hangul and 47-item pronunciation candidate packs
provides:
  - Independent source, curriculum, orthography, phonetics, Portuguese, rights, integrity, and playback review gates
  - Fixed no-path-input active pointer resolver for one complete immutable foundation snapshot
  - Exact licensed-media validation for paths, headers, duration, text, metadata, bytes, hashes, and qualified reviewer roles
  - Complete inactive candidate manifests with 139 pending curation records and 509 pending media slots
affects: [31-05, 31-08, 31-09, 31-11, 31-12, korean-foundation-export, korean-foundation-activation]
tech-stack:
  added: []
  patterns:
    - Candidate review and media manifests can be complete and valid while remaining non-exportable
    - Production operations resolve one fixed active pointer once and pass a frozen snapshot through every gate
    - Exact media approval binds source, text, rights, provider metadata, bytes, and distinct qualified human receipts
key-files:
  created:
    - src/multilang/services/korean_foundation_review.py
    - src/multilang/services/korean_foundation_snapshot.py
    - src/multilang/services/korean_foundation_media.py
    - tests/services/test_korean_foundation_review.py
    - tests/services/test_korean_foundation_snapshot.py
    - tests/services/test_korean_foundation_media.py
    - data/korean_foundations/korean-foundations-v1-curation.json
    - data/korean_foundations/korean-foundations-v1-media.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-04-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Keep top-level source, curation, and media files candidate-only; production may consume only one fixed active immutable snapshot."
  - "Run source and strict-curriculum validation before considering human review status so approval cannot rescue invalid structure."
  - "Require exact path, text, metadata, rights, bytes, hashes, and distinct specialist/native receipts before required media can be ready."
patterns-established:
  - "One-resolution boundary: active entry points resolve once, then downstream review and media checks reuse the same frozen snapshot."
  - "Content-free diagnostics: failures expose controlled reason codes and bounded item/media identifiers, never Korean text, paths, notes, payloads, or secrets."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
requirements-completed: []
duration: 45min
completed: 2026-08-05
---

# Phase 31 Plan 04: Independent Review, Exact Media, and Immutable Snapshot Gates Summary

**Hash-bound human review, exact-byte licensed media validation, and a one-read immutable-snapshot resolver now protect all 139 Korean foundation candidates while 973 review gates and 509 media slots remain honestly pending and inactive.**

## Performance

- **Execution window:** 2026-08-05T21:20:00Z to 2026-08-05T22:05:22Z
- **Duration:** 45 minutes
- **Tasks:** 3/3
- **Plan files created:** 8 implementation/test/data artifacts
- **Planning files updated:** 2, plus this summary
- **Assurance:** `self_checked` through strict RED/GREEN task gates, adversarial second-pass checks, 178 focused plan/curriculum tests, 126 Korean regressions, and the complete 1,412-test suite
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Added **139 source-aligned curation records**: 92 Hangul and 47 pronunciation, with **973 independently pending gates** and zero learner-ready records.
- Added a fixed, no-argument active pointer and immutable snapshot reader that validates pointer shape, root containment, symlink/reparse safety, exact manifest/member hashes, declared files, and one-read resolution.
- Added **509 deterministic media slots**: 368 Hangul and 141 pronunciation; all remain `needs_review`, candidate-only, byte-free, and inactive.
- Proved that all **325 required slots** can pass using transient test-only PCM WAV/PNG bytes while path, role, rights, text, metadata, format, duration, hash, and byte drift fail closed.
- Preserved the exact Plan 31-02/31-03 registry, Hangul, and pronunciation source bytes and kept production blocked because no active pointer, immutable snapshot, or production media directory exists.

## TDD Task Evidence

### Task 31-04-01: Independent review gates

- **RED:** All 10 focused tests failed because `multilang.services.korean_foundation_review` did not exist.
- **GREEN:** Implemented frozen Pydantic gate/record/manifest models, family-specific applicability, source and curriculum precedence, protected updates, summaries, and production readiness checks.
- **Candidate data:** Materialized 139 exact-order pending records with no reviewer identity, timestamp, approval, or invented linguistic truth.
- **Focused verification:** `10 passed in 1.12s`.
- **Review plus curriculum verification:** `146 passed in 6.85s`.

### Task 31-04-02: Fixed active pointer and immutable snapshot reader

- **RED:** All 19 focused tests failed because `multilang.services.korean_foundation_snapshot` did not exist.
- **GREEN:** Implemented the exact four-field pointer, bounded snapshot manifest, frozen complete resolution result, safe component traversal, exact hashes/sizes/bytes, extra-file denial, and fixed one-read resolver.
- **Production state:** A missing active pointer returns controlled `production_not_active`; candidate files are never a fallback.
- **Focused verification:** `19 passed in 0.50s`.

### Task 31-04-03: Licensed exact media bytes and pending slots

- **RED:** All 13 focused tests initially failed because `multilang.services.korean_foundation_media` did not exist.
- **First implementation run:** `1 passed, 12 failed`; the planned candidate media manifest had not yet been materialized.
- **Builder diagnosis:** The deterministic 509-slot builder exposed one missing `deepcopy` import before writing the candidate.
- **Second GREEN run:** After creating the complete pending manifest, `12 passed, 1 failed`; unsafe-path validation occurred after the aggregate unmanifested-member check.
- **Final GREEN:** Reordered contract validation before member-set checks and reached `13 passed in 19.96s`.
- **Regression repair:** Reused canonical `KOREAN_PROVIDER_LOCALE` rather than introducing a second `ko-KR` literal; the affected regression plus media suite produced `14 passed in 20.21s`.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 3 plan gate: media + review + snapshot | `42 passed in 21.48s` |
| Final review + curriculum + snapshot + media suite | `178 passed in 26.31s` |
| Independent forged approval/path/hash/role/pointer second pass | `33 passed, 9 deselected in 17.65s` |
| Phase 30/Korean identity, morphology, fingerprint, and integration regressions | `126 passed in 37.72s` |
| Full repository test suite | `1412 passed, 16 warnings in 284.71s` |
| Python compilation | Passed for all three new production modules |
| Whitespace scan | Clean across all eight implementation/test/data artifacts |
| Production readiness audit | `production_not_active`; no pointer, snapshot tree, or production media directory |
| Planning lifecycle | `phase-status 31 in_progress` returned `changed: false` |
| Reviewed planning fingerprint | `bda029c32baf953c3de237baeb598f99e5e0465a239145fcd65746ea80511658` |

The 16 full-suite warnings are existing third-party deprecations: one `dateparser` UTC warning and fifteen Alembic `path_separator` warnings. They do not fail tests and were not changed in this plan.

## Review Inventory Evidence

| Family | Records | Applicable pending gates per record | Pending gates |
|---|---:|---:|---:|
| Hangul | 92 | 7 | 644 |
| Pronunciation | 47 | 7 | 329 |
| **Total** | **139** | — | **973** |

- Common gates: source/content, curriculum/atomicity, Portuguese, media rights, media integrity, and audio playback.
- Family gate: Korean orthography for Hangul; Korean phonetics for pronunciation.
- Summary result: 139 blocked records, 0 learner-ready records, and no rejected or approved gate.
- Curation canonical content hash: `76d08bfa4c2780111a8d7fd89e73c86ee5393609ba1f40c003cc6e77745aff6b`.
- Curation file SHA-256: `6a5ddc06cfdb2ec3546e8854986bbe28ef957d170444dafadb0e97a06980055e`.

Approval receipts bind reviewer identity/role/time, source pack version, source item hash, applicable evidence hashes, and the exact gate payload. Approved gate changes require explicit force and remain isolated to the named gate.

## Media Inventory Evidence

| Family / kind | Required | Optional | Total |
|---|---:|---:|---:|
| Hangul audio | 92 | 0 | 92 |
| Hangul strokes PNG | 92 | 0 | 92 |
| Hangul picture PNG | 0 | 92 | 92 |
| Hangul GIF | 0 | 92 | 92 |
| Pronunciation letter audio | 47 | 0 | 47 |
| Pronunciation word audio | 47 | 0 | 47 |
| Pronunciation sentence audio | 47 | 0 | 47 |
| **Total** | **325** | **184** | **509** |

- Required test-fixture playback resolved 233 PCM WAV files and 92 stroke PNG files.
- All 509 committed slots have unique IDs, basenames, and repository-relative snapshot destinations.
- All slots are `needs_review` with controlled reason `media-evidence-required`; no artifact/review hash, rights decision, reviewer receipt, or media byte is present.
- Candidate manifest canonical content hash: `e7ef7ed570b28ed70bb09a68426567ac5a2dc3df8bb33acb357d32c281e861dc`.
- Candidate media file SHA-256: `ad8f05f3846da9874f49a85e045b4d225f15ffdac8fba13cbd39615d94561fcc`.

## Immutable Snapshot Contract

- The fixed pointer path is `data/korean_foundations/active-foundations.json`; no public production API accepts a path, URL, root, archive, APKG, or caller-selected manifest.
- The pointer permits exactly `schema_version`, lowercase 64-hex `bundle_sha256`, contained `snapshot_relpath`, and lowercase 64-hex `snapshot_manifest_sha256`.
- Resolution rejects URLs, absolute paths, drives, traversal, backslashes, archives, symlinks, Windows reparse points, name/hash drift, missing files, and unmanifested files.
- One pointer-byte read selects one complete concept/source/curation/media/review-evidence bundle; downstream review and media operations receive that frozen resolution rather than rereading activation.
- Plan 31-04 deliberately creates no active pointer or snapshot. Plans 31-11/31-12 retain receipt preparation and activation authority.

## High-Leverage Trace

- **Hangul stroke slot:** `ko-hangul-0001` / `hangul.strokes.0001` is bound to source content hash `7f68f731516a1b8428bbe157ec45c8798bee9838b7e47473ae32bb81ade2c111`, deterministic destination `media/hangul/hangul-strokes-0001.png`, and pending status.
- **Pronunciation letter-audio slot:** `ko-pron-0001` / `pron.letter-audio.0001` is bound to source content hash `275eb6bf13f8731cc2be627ad1ee920af6837ca1366a893b355253aaa93adfad`, destination `media/pronunciation/pron-letter-audio-0001.wav`, and pending status.
- An approved-shaped transient slot additionally required exact display/spoken/NFC hashes, provider/voice/locale/SSML/prosody metadata, rights metadata, PCM header/duration, artifact/reviewed hashes, and all qualified human receipts before its bytes resolved.

## Fixed Source Integrity

| Frozen source | File SHA-256 | Result |
|---|---|---|
| Concept registry | `79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625` | Unchanged from Plan 31-03 |
| Hangul pack | `80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1` | Unchanged from Plan 31-03 |
| Pronunciation pack | `6a2eb0b6a0a467de6074ffafc2fb674a674ea96c3c2187f339d1c278aa8f55ec` | Unchanged from Plan 31-03 |

## Files Created/Modified

- `src/multilang/services/korean_foundation_review.py` — independent frozen review models, applicability/source/curriculum checks, protected updates, summaries, and readiness.
- `src/multilang/services/korean_foundation_snapshot.py` — fixed active pointer and complete immutable snapshot validation/resolution.
- `src/multilang/services/korean_foundation_media.py` — deterministic pending-slot construction and exact rights/text/path/header/duration/hash/role/byte validation.
- `data/korean_foundations/korean-foundations-v1-curation.json` — 139 exact-order candidate review records, all pending.
- `data/korean_foundations/korean-foundations-v1-media.json` — 509 deterministic candidate media slots, all pending and byte-free.
- `tests/services/test_korean_foundation_review.py` — 10 review/source/curriculum/update/readiness tests.
- `tests/services/test_korean_foundation_snapshot.py` — 19 fixed-pointer/snapshot/path/hash/one-read tests.
- `tests/services/test_korean_foundation_media.py` — 13 candidate/rights/roles/path/format/hash/byte/readiness tests.
- `.planning/SPEC.md` — records Plan 31-04 complete and Plan 31-05 next.
- `.planning/.state-fingerprint.json` — reviewed planning-state baseline.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-04-SUMMARY.md` — execution evidence and handoff.

## Decisions Made

- Candidate completeness and production readiness are separate states. Complete top-level joins are useful for review but never constitute activation.
- Structural source/curriculum truth is evaluated before gate status. Human approval cannot override a false i+1 graph, wrong source version, or content-hash drift.
- Production consumes one immutable snapshot selected by one fixed pointer read, preventing mixed-version review/media decisions.
- Media approval is exact evidence, not provider success: safe destination, licensed source, attribution, redistribution, exact text/metadata, bytes, headers, duration, hashes, playback, and human roles must all agree.
- Raw jamo/rule display text cannot be approved as its own spoken text, and Korean phonetics specialist and independent native-speaker identities must differ.
- `ko-KR` remains defined only by `KOREAN_PROVIDER_LOCALE`; foundation media validates against that canonical constant.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored the deterministic media manifest builder import**
- **Found during:** Task 31-04-03 candidate materialization.
- **Issue:** `korean_foundation_media_manifest_sha256()` used `deepcopy` without importing it, producing a deterministic `NameError` before the 509-slot candidate could be written.
- **Fix:** Imported `deepcopy` from `copy`.
- **Files modified:** `src/multilang/services/korean_foundation_media.py`.
- **Verification:** The builder produced exactly 509/325/368/141 total/required/Hangul/pronunciation counts and the candidate loaded successfully.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

**2. [Rule 1 - Bug] Validated unsafe slot paths before aggregate member-set checks**
- **Found during:** Task 31-04-03 GREEN run.
- **Issue:** A forged unsafe path first appeared as `unmanifested_media_member`, obscuring the more precise security boundary failure.
- **Fix:** Performed every slot's source identity and path/format contract checks before comparing approved required paths with snapshot members.
- **Files modified:** `src/multilang/services/korean_foundation_media.py`.
- **Verification:** All unsafe POSIX/Windows/URL/traversal cases now return content-free `unsafe_media_path`; all 13 media tests pass.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

**3. [Rule 1 - Regression] Preserved the single canonical Korean provider-locale literal**
- **Found during:** The 126-test Korean regression pass.
- **Issue:** A Pydantic `Literal["ko-KR"]` introduced a second production locale literal, violating Phase 30's one-canonical-definition invariant.
- **Fix:** Imported `KOREAN_PROVIDER_LOCALE` and validated the optional media locale against it.
- **Files modified:** `src/multilang/services/korean_foundation_media.py`.
- **Verification:** The previously failing locale scan and all media tests passed (`14 passed`), then all 126 Korean regressions and all 1,412 repository tests passed.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

---

**Total deviations:** 3 auto-fixed Rule 1 correctness/security issues.
**Impact on plan:** All fixes were local and necessary for deterministic generation, precise fail-closed diagnostics, and Korean identity compatibility. No provider, endpoint, persistence, export, reviewer, approval, or production-media scope was added.

## Issues Encountered

- The first read-only production audit command used escaped newlines directly in `python -c` and received a `SyntaxError`; it was rerun with an explicit multiline `exec` string and passed without changing repository files.
- The first summary-structure self-check counted marker names quoted in prose as additional XML-style sections; the corrected exact-line check passed with one opening/closing line for every required structured section.
- The full suite emits 16 existing third-party deprecation warnings but has no failing test or Plan 31-04 blocker.

## Security and Privacy Review

- All manifests are bounded JSON validated by frozen, extra-forbidden Pydantic models; no pickle, dynamic code evaluation, provider call, or network client was introduced.
- Production entry points accept no caller-controlled filesystem path or URL. Relative media paths reject drives, colons, backslashes, traversal, empty components, unsupported characters, and containment escape.
- Snapshot and media traversal checks every filesystem component with `lstat` and rejects symlinks/Windows reparse points; exact SHA-256, size, bytes, format headers, and WAV duration are independently recomputed.
- Diagnostics expose controlled codes plus bounded item/media identifiers only; Korean source text, reviewer notes, absolute paths, provider payloads, and secrets are absent.
- Test media exists only under pytest `tmp_path`; candidate and planning files remain byte-identical during fixture validation, and no network/provider operation occurs.
- The new file-access and activation surfaces are fully represented in the plan threat model. No additional threat flags were found.

## Known Stubs and Intentionally Blocked Evidence

- Every curation gate intentionally lacks reviewer identity, role, timestamp, and reviewed hashes and remains `needs_review`; qualified receipt collection is later Plan 31-11 scope.
- Every media slot intentionally lacks source/rights approval, provider/voice metadata, artifact/review hashes, and reviewer receipts; no production bytes are present.
- The 92 picture PNG and 92 GIF slots are optional pending identities, while all 325 required slots remain pending until exact licensed bytes and playback evidence exist.
- `data/korean_foundations/active-foundations.json` and `data/korean_foundations/snapshots/` are intentionally absent. Production readiness therefore fails with `production_not_active`.
- These blocked states are the required Plan 31-04 outcome; they prevent learner-ready claims but do not prevent this gate-definition plan from being complete.

## Task Commits and Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other Git delivery/destructive action was performed.

## Authentication Gates

None.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-04 complete and Plan 31-05 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; Phase 31 remains open at `[-]`.
- The reviewed planning fingerprint is `bda029c32baf953c3de237baeb598f99e5e0465a239145fcd65746ea80511658`.
- KHAN-01, KHAN-02, KPRO-01, and KPRO-02 are advanced but remain unchecked because template, export, genuine review/media receipts, immutable snapshot preparation, and activation are later Phase 31 work.

## Next Phase Readiness

- Plan 31-05 can consume stable review/media/snapshot boundaries while extracting language-neutral phoneme mechanics and adding the isolated Korean Hangul template contract.
- No engineering blocker remains for Plan 31-05.
- Production and learner-ready export remain deliberately blocked until genuine qualified receipts, licensed exact bytes, immutable snapshot preparation, and separately authorized activation occur in later plans.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All three TDD task gates passed; 178 focused plan/curriculum tests, 33 adversarial second-pass tests, 126 Korean regressions, and all 1,412 repository tests passed offline. Candidate counts, fixed source hashes, inactive production state, compilation, whitespace, security boundaries, and planning fingerprint were independently checked.
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
  summary: The media manifest hash helper needed its missing deepcopy import before deterministic candidate materialization could run.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Unsafe slot contracts needed validation before aggregate snapshot-member comparison to preserve precise fail-closed path diagnostics.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The media locale field needed to reuse the Phase 30 canonical provider-locale constant instead of introducing a second production literal.
</deltas>

<judgment>
<active_constraints>
Preserve Phase 30 canonical Korean identity and Plan 31-02/31-03 registry/Hangul/pronunciation bytes. Top-level manifests remain candidate-only. Production operations resolve the fixed active pointer once, consume one complete hash-validated immutable snapshot, and expose content-free diagnostics. Source, curriculum, human review, rights, media integrity, and playback remain independent fail-closed gates.
</active_constraints>
<unresolved_uncertainty>
Qualified reviewer identities, Portuguese regional policy, licensed media sources, exact production bytes, provider/voice receipts, heard playback evidence, snapshot preparation, activation authorization, templates, exports, and observed Anki rendering remain later Phase 31 work. The Korean frequency source/redistribution decision remains a Phase 32 blocker.
</unresolved_uncertainty>
<decision_posture>
Prefer complete but honestly pending candidate joins and exact immutable evidence over inferred approval. No status, filename, provider success, or automation output can replace qualified human, licensing, byte-integrity, and playback proof.
</decision_posture>
<anti_regression>
Do not read top-level candidates as production, resolve activation more than once per operation, combine files across snapshots, accept caller paths/URLs, permit traversal/symlink/reparse escape, trust declared hashes without recomputation, allow raw-glyph spoken approval, collapse specialist/native roles, or create production bytes/approvals without the later receipt and activation checkpoints.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All eleven implementation, test, data, planning, fingerprint, and summary artifacts listed above exist.
- The curation and media candidates parse at 139 records/973 pending gates and 509 slots/325 required, with zero learner-ready or approved production records.
- Registry, Hangul, and pronunciation file hashes match the unchanged Plan 31-03 values; candidate canonical/file hashes match this summary.
- The active pointer, immutable snapshot tree, and production media directory are absent, and the production resolver returns `production_not_active`.
- Required `<checks>`, `<handoff>`, `<deltas>`, `<judgment>`, deviation, known-stub, security, and handoff sections are present.
- Lifecycle preflight reports reviewed planning state `clean`; Phase 31 remains `in_progress`, and the fingerprint matches the updated SPEC/unchanged ROADMAP/config inputs.
- `git diff --check` reported no whitespace errors; only existing Windows LF-to-CRLF conversion warnings were emitted. Repository HEAD remains `240b21abb8efce5e028fd0b80d1767cbcac0f145` because Git actions were disabled.

---
*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 04*
*Completed: 2026-08-05*
