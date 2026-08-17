---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "08"
subsystem: korean-foundation-evidence-and-receipt
runtime: opencode
assurance: self_checked
tags: [korean, evidence, pydantic, filesystem-security, atomic-write, cross-process-lock, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "07"
    provides: Exact hash-bound pending requests for all curriculum, media, rights, and reviewer decisions
provides:
  - Exact fixed evidence-inbox schemas and direct-placement instructions with no arbitrary intake surface
  - Complete source, curriculum, reviewer, Portuguese, rights, playback, media-byte, and active-prestate validation
  - One shared cross-process state lock and one atomic idempotent validate-and-write receipt capability
  - Strictly read-only receipt continuity across every bound authority and prestate hash
affects: [31-09, 31-10, 31-11, 31-12]
tech-stack:
  added: []
  patterns:
    - Fixed pathless public APIs with a private frozen temporary-root composition seam
    - Validate, derive, revalidate, and atomically replace inside one shared lock scope
    - Canonical SHA-256 groups plus a non-self-referential receipt payload digest
key-files:
  created:
    - src/multilang/services/_korean_foundation_state_lock.py
    - src/multilang/services/korean_foundation_evidence.py
    - tests/services/test_korean_foundation_evidence.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/README.md
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-08-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Bind all evidence through one exact fixed inbox and expose no public path, root, URL, archive, importer, upload, or caller-supplied authority object."
  - "Use a Windows named mutex or POSIX directory descriptor lock so all state-changing foundation operations can serialize without leaving lock artifacts."
  - "Treat exact-current receipt retries as byte-preserving idempotence and reject every stale or conflicting receipt without overwrite or repair."
patterns-established:
  - "Receipt authority is constructed only from freshly validated fixed-root bytes under one uninterrupted shared lock."
  - "Read-only continuity starts with the exact receipt-file hash and can neither create temporary files nor repair state."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
requirements-completed: []
duration: 26min
completed: 2026-08-06
---

# Phase 31 Plan 08: Fixed Korean Foundation Evidence and Receipt Summary

**A 519-member fixed evidence boundary now validates all 509 declared media assets and human/legal bindings before one lock-scoped atomic receipt write, with byte-exact idempotence and strictly read-only continuity.**

## Performance

- **Recorded continuation started:** 2026-08-05T23:58:00Z
- **Completed implementation/state/self-checks:** 2026-08-06T00:23:52Z
- **Recorded continuation duration:** 25m 52s (reported as 26min; the RED suite was established before this resumed implementation window)
- **Tasks:** 2/2
- **Core plan artifacts created:** 4
- **Planning artifacts updated/created:** 3, including this summary
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Implemented an exact fixed inbox whose index declares nine JSON evidence/reviewer records and 509 media members; README and generated receipt are excluded from the evidence-bundle hash.
- Added frozen bounded Pydantic contracts and fail-closed validation for source bindings, all 139 curriculum records, qualified/distinct reviewers, Portuguese policy, 509 rights records, 233 playback records, exact text, PCM/PNG/GIF headers, and exact media bytes.
- Added a private shared state lock backed by a Windows named mutex or POSIX locked directory descriptor, leaving no lock file or other filesystem artifact.
- Added the sole public receipt writer: it freshly validates under lock, derives authority privately, detects between-stage evidence/prestate drift, rejects stale receipts, and uses secure same-directory temp creation, fsync, atomic replacement, and parent fsync where supported.
- Added a strictly read-only continuity operation that checks the exact receipt-file hash first and then revalidates every bound source, reviewer, rights, media, index, pointer, and active-prestate input without any repair path.
- Kept the canonical inbox limited to its technical README and preserved all candidate/request bytes and production roots exactly.

## Strict TDD Evidence

### Task 31-08-01: Implement exact fixed inbox schemas and temporary-root evidence assembly

- **RED:** The focused contract run returned `13 failed, 24 deselected in 0.49s`; the expected failure was the absent `multilang.services.korean_foundation_evidence` module and technical README.
- **GREEN:** After adding the fixed path bundle, schemas, safe filesystem assembly, canonical hashing, semantic validators, and README, the same focused command returned `13 passed, 24 deselected in 12.28s`.
- **Refactor:** Filesystem reads use lstat component checks, opened-descriptor identity checks, bounded reads, regular-file enforcement, archive magic rejection, and content-free reason codes.

### Task 31-08-02: Implement lock-scoped receipt writing and zero-write continuity

- **RED:** The full receipt, forged-object, drift, stale-receipt, continuity, and cross-process-lock matrix had already been written and remained red while both production modules were absent.
- **GREEN:** The complete evidence suite returned `37 passed in 66.54s` after implementing the private shared lock, internal receipt derivation, three between-stage rechecks, atomic writer, stale-receipt refusal, and read-only continuity.
- **Refactor / second pass:** An independent temporary fixture traced `ko-hangul-0001` audio and all three `ko-pron-0047` P13 audio members through receipt creation and continuity, returning `second_pass_status=passed`.

No commits were created because the user prohibited commits and staging. RED/GREEN evidence is preserved in command results and this summary rather than commit history.

## Fixed Contract Versions

| Contract | Version |
|---|---|
| Evidence layout | `phase31-korean-foundation-evidence-layout-v1` |
| Evidence policy | `phase31-korean-foundation-evidence-policy-v1` |
| Shared state lock | `phase31-korean-foundation-state-lock-v1` |
| Evidence index | `phase31-korean-foundation-evidence-index-v1` |
| Validation receipt | `phase31-korean-foundation-validation-receipt-v1` |

## Public Surface Proof

The signature/source second pass returned `signature_scan=passed` and confirmed exactly:

```python
inspect_fixed_korean_foundation_evidence_inbox()
validate_and_write_fixed_korean_foundation_validation_receipt(
    *, confirmed_index_sha256: str
)
check_korean_foundation_validation_receipt_continuity(
    *, expected_receipt_sha256: str
)
```

- There is exactly one public function whose name can write/create/mint/repair state: the combined validate-and-write receipt operation.
- No public callable accepts a path, root, URL, archive, APKG, importer, upload, validated object, receipt payload, receipt object, or bypass flag.
- Validated evidence, receipt derivation, atomic writing, temporary paths, and stage hooks remain private and absent from `__all__`.
- Source scanning found no provider, network client, Tatoeba, OpenAI, or `allow_unapproved` surface.

## Exact Evidence Coverage

| Dimension | Exact count |
|---|---:|
| Index plus declared evidence members | 519 |
| Fixed proposed/review/rights records | 5 |
| Qualified reviewer records | 4 |
| Manifest-declared media members | 509 |
| Curriculum items | 139 |
| Playback-reviewed audio members | 233 |
| P11-P13 specialist atomization records | 6 |

The receipt binds separate canonical hashes for the complete evidence bundle, frozen candidates/requests, reviewer/curriculum evidence, rights evidence, media/playback evidence, confirmed index, and active prestate. Its `payload_sha256` excludes itself, and the serialized receipt receives a separate caller-confirmed file hash during continuity checks.

## Failure and Atomicity Guarantees

- Traversal, absolute/drive/backslash paths, URLs, archive/APKG suffixes or magic, links/reparse points, special files, extras, missing members, duplicate basenames, and oversized files fail before receipt creation.
- Reviewer role collapse, unqualified identities, rejected reuse/redistribution, playback text drift, source drift, media-byte drift, and active-prestate drift fail closed with content-free diagnostics.
- Private hooks after validation, after payload derivation, and immediately before writing prove evidence or active-pointer drift leaves no receipt or temp file.
- An exact-current retry returns the same receipt without changing bytes or mtime; stale/conflicting receipts are never overwritten, repaired, or refreshed.
- Continuity uses no lock-file creation, tempfile, replace, `Path.write_bytes`, or `Path.write_text` primitive and rejects receipt/index/reviewer/rights/media/source/prestate drift without repair.

## Final Verification Results

| Check | Exact result |
|---|---|
| Focused Task 1 RED | `13 failed, 24 deselected in 0.49s` |
| Focused Task 1 GREEN | `13 passed, 24 deselected in 12.28s` |
| Complete Plan 31-08 suite | `37 passed in 66.54s` |
| Complete Korean regression matrix | `391 passed in 202.59s` |
| Python compilation | Passed for both services and the evidence test |
| Independent H0/P13 receipt trace | `second_pass_status=passed` |
| Public signature/source scan | `signature_scan=passed` |
| Candidate/request hash pins | All seven exact and unchanged |
| Canonical side-effect scan | `canonical_mutation_count=0` |
| Human checkpoint proof | `human_checkpoint_count=0` |
| Phase lifecycle | `phase-status 31 in_progress` returned `changed: false` |
| Reviewed planning fingerprint | `8ce1fe758a2453d492bd37cf885bae9b7623bebee10919e27e81deee3988d493` |

`ruff` was unavailable in the offline environment (`Failed to spawn: program not found`). The planned pytest commands, 391-test Korean matrix, compilation, independent fixture trace, exact-hash scan, and public-surface scan all passed.

## Files Created/Modified

### Created

- `src/multilang/services/_korean_foundation_state_lock.py` - private artifact-free Windows/POSIX cross-process state lock for receipt, preparation, and activation.
- `src/multilang/services/korean_foundation_evidence.py` - fixed constants, schemas, exact assembly/semantic validation, atomic receipt operation, and read-only continuity.
- `tests/services/test_korean_foundation_evidence.py` - 37 exhaustive temporary-root layout, semantic, drift, atomicity, stale receipt, continuity, lock, and no-canonical-mutation tests.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/README.md` - exact direct-placement layout and explicit no-importer instructions; the canonical inbox's only file.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-08-SUMMARY.md` - execution evidence and bounded Plan 31-09 handoff.

### Modified

- `.planning/SPEC.md` - records Plan 31-08 complete and Plan 31-09 next while Phase 31 remains open.
- `.planning/.state-fingerprint.json` - reviewed planning-state baseline after the SPEC update.

No candidate, request, CLI, provider, canonical evidence, receipt, snapshot, pointer, activation, or export file was modified.

## Decisions Made

- Kept all public APIs pathless. Tests replace one private frozen path bundle rather than widening production intake.
- Used a named kernel mutex on Windows and `flock` on an opened directory descriptor on POSIX, satisfying cross-process serialization without a persistent lock artifact.
- Bound file identity, size, mtime, and SHA-256 into repeated private state fingerprints so same-lock between-stage drift fails before temporary receipt creation.
- Made receipt bytes deterministic and timestamp-free; exact-current retries are therefore no-write idempotent and stale/conflicting bytes are unambiguously rejected.
- Required every optional and required manifest slot to have exact approved evidence bytes because the fixed evidence index declares all 509 members, even though later learner export may use only required slots.

## Deviations from Plan

None - the plan executed exactly as written. No arbitrary intake, canonical evidence, provider call, checkpoint, snapshot, activation, export, or public intermediate-object writer was added.

## Issues Encountered

- `ruff` is not installed in the offline environment. This did not block the authoritative planned tests, Python compilation, broader Korean regressions, or independent second-pass scans.
- The first final self-check counted structured marker names quoted in its own prose as duplicate tags. Removing those quoted literals and checking exact marker lines produced `final_self_check=passed`; no implementation file changed.

## Security and Privacy Review

- All filesystem inputs are fixed constants in production; index member paths must be bounded safe POSIX-relative allowlisted paths and are containment/lstat checked component by component.
- Every file is opened with bounded descriptor reads and identity checks; links/reparse points, special files, archive signatures, mutation during read, and unbounded data fail closed.
- SHA-256 is used for data integrity; no MD5/SHA-1, dynamic code execution, shell command, deserialization, remote fetch, or credential surface was introduced.
- The atomic writer uses `mkstemp` in the receipt directory, restrictive permissions, file fsync, `os.replace`, and parent fsync where supported, with cleanup limited to its own failed temp.
- Public errors contain controlled reason codes only. They do not echo Korean text, reviewer notes, attribution text, absolute paths, provider payloads, or secrets.
- The new fixed filesystem/read/atomic-write surface is fully covered by threats T-31-08-01 through T-31-08-05 in the plan; no additional unregistered threat surface was introduced.

## Known Stubs

None. `fixture-only-*` identities and media are private temporary test evidence deliberately required by this plan; they never enter the canonical inbox or production state. Genuine evidence remains a named future human checkpoint rather than a production stub.

## Task Commits and Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other destructive/delivery Git action was performed.

## Authentication Gates

None.

## User Setup Required

None. This plan performs no provider call, network request, credential access, media acquisition, or human checkpoint.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-08 complete and Plan 31-09 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; Phase 31 remains open at `[-]` and `.planning/ROADMAP.md` was not changed by this plan.
- `node .planning/bin/gsdd.mjs session-fingerprint write` produced `8ce1fe758a2453d492bd37cf885bae9b7623bebee10919e27e81deee3988d493`.
- KHAN-01, KHAN-02, KPRO-01, and KPRO-02 remain unchecked. This plan proves fixture-backed machinery, not supplied evidence or learner-ready decks.
- The repository's authoritative GSDD handoff remains SPEC/ROADMAP/fingerprint based; the legacy `.planning/STATE.md` was not advanced or broadly reconstructed.

## Next Phase Readiness

- Plan 31-09 can import `_korean_foundation_state_lock` and consume exact receipt, index, evidence-group, and `active_prestate_sha256` bindings while keeping preparation and activation on private temporary roots.
- The private frozen path bundle remains available to compose Plan 31-09 tests without exposing production path arguments.
- Canonical evidence, receipt, snapshot, active pointer, and exports remain absent. Genuine reviewer/legal/media evidence is still intentionally deferred to Plan 31-11.
- No Plan 31-08 engineering blocker remains.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Strict TDD produced the expected 13-failure focused RED, a 13-test focused GREEN, and a 37-test complete GREEN. The 391-test Korean matrix, compilation, independent H0/P13 receipt trace, exact seven-file hash pins, pathless public-signature/source scan, cross-process lock test, canonical no-mutation scan, and phase-open planning fingerprint all passed.
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
None.
</deltas>

<judgment>
<active_constraints>
Preserve canonical `ko`, every Plan 31 candidate/request byte and hash, the fixed no-importer boundary, distinct phonetics-specialist/native authority, the one combined receipt writer, and strictly read-only continuity. Temporary approved-shaped fixtures can prove mechanics only and can never become production authority.
</active_constraints>
<unresolved_uncertainty>
Genuine reviewer identities and qualifications, Portuguese regional policy, source/attribution/license/reuse/redistribution decisions, exact spoken text, licensed media bytes, heard playback, canonical receipt creation, immutable snapshot preparation, authorization, activation, and observed Anki behavior remain unavailable and later-plan work.
</unresolved_uncertainty>
<decision_posture>
Prefer one fixed exact local boundary, exhaustive independent semantic gates, deterministic canonical hashes, private composition seams, and fail-before-write state transitions over flexible intake or caller-supplied intermediate authority.
</decision_posture>
<anti_regression>
Do not add public path/root/import/upload/archive/URL inputs, expose validated evidence or receipt payload writers, release the shared lock between validation and atomic replacement, include README/receipt in the evidence bundle, overwrite stale receipts, let continuity write or repair, copy fixtures into canonical paths, or alter any candidate/request byte.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All four core plan artifacts and this summary exist at the required paths.
- The final complete evidence-suite rerun returned `37 passed in 66.63s`.
- The planning fingerprint was independently recomputed from ROADMAP, SPEC, and config bytes and matches `8ce1fe758a2453d492bd37cf885bae9b7623bebee10919e27e81deee3988d493`.
- All four required structured execution sections occur exactly once, and changed-file trailing-whitespace checks passed.
- The canonical inbox still contains only `README.md`; canonical receipt, snapshots, active pointer, and exports remain absent.
- Phase 31 remains open for Plan 31-09, all four requirements remain unchecked, and no Git delivery action was performed.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 08*
*Completed: 2026-08-06*
