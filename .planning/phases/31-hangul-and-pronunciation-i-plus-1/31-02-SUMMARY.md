---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "02"
subsystem: korean-foundation-inventory
runtime: opencode
assurance: self_checked
tags: [korean, hangul, unicode, curriculum, strict-i-plus-1, provenance, sha256, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "01"
    provides: Frozen foundation contracts, fixed-path loaders, positional Jamo mapping, and recomputed strict-i+1 admission
provides:
  - Shared 139-concept orthography/phonology registry with deterministic predecessor closure
  - Complete 92-entry H0-H10 Hangul candidate inventory with exact 19/21/27 modern positional identities
  - Validated zero-entry P0-P13 pronunciation skeleton inheriting all 92 orthographic concepts
  - Real-manifest coverage, hash, Unicode, graph, pending-state, and mutation evidence
affects: [31-03, korean-foundation-review, korean-foundation-media, korean-foundation-export]
tech-stack:
  added: []
  patterns:
    - Complete inventories declare exact stage/category coverage and fail closed on omission or drift
    - Skeleton inventories declare future coverage without claiming populated learner records
    - Canonical machine identity uses modern positional conjoining Jamo; Compatibility Jamo is display-only mapping
key-files:
  created:
    - data/korean_foundations/korean-concepts-v1.json
    - data/korean_foundations/hangul-v1.json
    - data/korean_foundations/pronunciation-i-plus-1-v1.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-02-SUMMARY.md
  modified:
    - src/multilang/services/korean_curriculum.py
    - tests/services/test_korean_curriculum.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Use one registry for 92 orthographic and 47 phonological concepts so pronunciation inherits Hangul identity rather than duplicating it."
  - "Distinguish a complete Hangul inventory from an honest pronunciation skeleton with validated inventory_status values."
  - "Keep every human and media review status at needs_review; hashes and source citations are integrity evidence, not approval."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-02]
requirements-completed: []
duration: "continuation handoff; exact start timestamp unavailable"
completed: 2026-08-05
---

# Phase 31 Plan 02: Shared Registry, Complete Hangul Inventory, and Pronunciation Skeleton Summary

**A hash-bound 139-concept DAG now drives a complete 92-entry H0-H10 Hangul candidate pack and an explicit P0-P13 pronunciation skeleton without fabricating learner copy, media, or approval.**

## Performance

- **Completed final checks:** 2026-08-05T20:51:03Z
- **Tasks:** 3/3
- **Assurance:** `self_checked` through task-level RED/GREEN cycles, final sequential focused checks, the complete 85-test curriculum suite, Phase 30 regressions, manifest scans, and high-leverage traces
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Froze one deterministic registry with **139 concepts**: **92 orthography** and **47 phonology**.
- Completed **92 contiguous Hangul candidates** across H0-H10 with per-entry canonical hashes, source provenance, required media-slot declarations, and recomputed one-target-unknown evidence.
- Proved exact modern inventories: **19 choseong**, **21 jungseong**, and **27 non-empty jongseong**, including **11 complex final clusters** and normative H3 `ㅂ` with no `㄂`.
- Kept machine identity in NFC modern conjoining Jamo while storing Compatibility Jamo only in explicit positional display mappings.
- Froze a **zero-entry** pronunciation pack with exact P0-P13 declarations for all **47 categories** and ordered inheritance of all **92 orthographic concepts** for Plan 31-03.
- Kept all human/media review values at `needs_review`; no approval, media bytes, provider/voice metadata, learner-ready export, or remote loading path was introduced.

## TDD Task Evidence

### Task 31-02-01: Registry, bootstrap, skeletons, and coverage validators

- **RED:** Fixed loaders failed because the three production manifests did not exist.
- **GREEN:** Registry/header/bootstrap/skeleton tests produced `31 passed, 25 deselected` before later-task records were added.
- **Final sequential check:** `32 passed, 53 deselected in 0.77s`.

### Task 31-02-02: H1-H6 modern onset and vowel foundations

- **RED:** Exact H1-H6 records and 19/21 positional inventory evidence were absent.
- **GREEN:** The first focused completed slice produced `11 passed, 57 deselected`.
- **Final sequential check:** `11 passed, 74 deselected in 0.45s`.

### Task 31-02-03: H7-H10 and cross-pack orthographic identity

- **RED:** H7-H10 coverage, exact finals, complete-pack hashes, and cross-pack audits were absent.
- **First GREEN check:** `11 passed, 1 failed, 73 deselected`; implementation passed, but the test helper incorrectly classified structural `inventory_status: complete` as a review approval status.
- **GREEN:** The helper was narrowed to review-status fields and produced `12 passed, 73 deselected in 0.64s`.
- **Final sequential check:** `12 passed, 73 deselected in 0.53s`.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 focused gate, rerun sequentially | `32 passed, 53 deselected in 0.77s` |
| Task 2 focused gate, rerun sequentially | `11 passed, 74 deselected in 0.45s` |
| Task 3 focused/mutation gate, rerun sequentially | `12 passed, 73 deselected in 0.53s` |
| Complete curriculum source/mutation suite | `85 passed in 1.97s` |
| Phase 30 domain/morphology/language/integration regressions | `123 passed in 42.10s` |
| Approval/path/secret/remote-media/halfwidth/HTML scans | No findings in the three manifests |
| Review-status audit | Only `needs_review`; structural inventory states are `complete` and `skeleton` |
| Fixed-loader security audit | Static local paths only; bounded UTF-8 JSON; no caller path, URL, archive, APKG, pickle, YAML, or code evaluation |
| Phase 30 canonicalizer source hash | `d3ab62a1f26d494d024ccf3c5c9ed20fd4efdbc18d05d71d441209337e83fb6b` (unchanged) |
| Reviewed planning fingerprint | `912b8a49a880de1da350fc3b6529e8d464c5e1f59c4333c151d5bd1865f56ac0` |

Ruff is not installed in the offline environment, so the supplemental Ruff check returned `program not found`. No dependency or lockfile change was attempted; all required pytest and scanner gates passed.

## Inventory Evidence

| Artifact | Inventory |
|---|---|
| Shared registry | 139 concepts: 92 orthography, 47 phonology |
| Hangul H0-H10 | H0 `7`, H1 `6`, H2 `3`, H3 `9`, H4 `8`, H5 `9`, H6 `7`, H7 `8`, H8 `27`, H9 `3`, H10 `5` |
| Modern Jamo | 19 choseong, 21 jungseong, 27 non-empty jongseong |
| H7/H8 | Batchim position plus seven coda-output categories; all 27 modern finals including 11 complex clusters |
| Pronunciation skeleton | P0-P13 declared in order, 47 categories, 0 entries, 92 inherited orthographic IDs |

The complete Hangul validator admitted **92/92** targets in sequence. Every record recomputed exactly its own target as unknown before admission. All 35 H7/H8 positional/coda target IDs occur in the pronunciation skeleton's inherited identity list; no phonological target is pre-known.

## Hash and Provenance Evidence

| Artifact | Canonical content hash | File SHA-256 |
|---|---|---|
| Registry | `89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d` | `79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625` |
| Hangul pack | `2bdbfb60aaca1419c2bb20abc8fb9954941bc8f92cb2361c3bc778b01c9b599c` | `80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1` |
| Pronunciation skeleton | `6950fc842c1c91b92402219b9a54bdf375f853dd61072e700ed866ec7e3744f6` | `a4604d2fdf48b39150faea080f7f6df40d2c13334f9195885cdeaa247b606aad` |

Both packs bind to registry hash `89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d`. Provenance is inert identity/version/hash metadata only:

- `unicode.hangul-17.0` / `unicode-17.0.0` / `6006005d2a1fd7e63e5cab103aeb22487b8f3980f01efc37b76e569859429c7b`
- `unicode.uax15-r57` / `uax15-r57` / `ba490809ca63d80e4d5eb9877f3065aa9235bf129511efedf8951cd4189ce85a`
- `nikl.orthography-0001` / `nikl-orthography-0001` / `13712afb60ada5cac9cd164c223344c3e9e6eb1e567ace3dd57997d566ac91e4`
- `nikl.pronunciation-0002` / `nikl-pronunciation-0002` / `a7f939a7dd4454df1c6cf8acab61b04436ede8902c23ae6282315066eeeb4408`

No source URL, fetch behavior, credential, approval, or redistributed corpus was added.

## High-Leverage Trace

- **H0:** `ko-hangul-0001` observes only `orthography.jamo.unit`, recomputes it as the sole unknown, and admits it before any later target.
- **H8:** `ko-hangul-0060` uses canonical jongseong `ᆪ`, display mapping `ㄳ`, known H7 coda prerequisites, and sole target `orthography.h8.final.kiyeok.sios`.
- **Cross-pack:** The pronunciation skeleton inherits all 92 completed orthographic identities and declares P0-P13 independently; its first future pronunciation record therefore cannot redefine or masquerade a Hangul identity.

## Files Created/Modified

- `data/korean_foundations/korean-concepts-v1.json` — shared immutable concept DAG.
- `data/korean_foundations/hangul-v1.json` — complete H0-H10 candidate source pack.
- `data/korean_foundations/pronunciation-i-plus-1-v1.json` — explicit P0-P13 population skeleton.
- `src/multilang/services/korean_curriculum.py` — exact field/media/coverage contracts and complete-versus-skeleton admission state.
- `tests/services/test_korean_curriculum.py` — real-manifest inventory, Unicode, hash, strict-evidence, and mutation proof.
- `.planning/SPEC.md` and `.planning/.state-fingerprint.json` — Plan 31-02 handoff while Phase 31 remains open.

## Decisions Made

- One registry remains the source of identity for both families; pronunciation inherits completed orthography and adds only phonological targets.
- `inventory_status: complete` enables exact entry coverage enforcement for Hangul, while `inventory_status: skeleton` truthfully permits zero pronunciation entries until Plan 31-03.
- Required media slots are schema obligations, not evidence that bytes or playback approval exist.
- H9/H10 retain only the smallest approved structure-level concepts; grammar constructions remain outside this phase.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Correctness] Extended the existing source-pack schema for exact production coverage**
- **Found during:** Task 31-02-01.
- **Issue:** The plan assigned only data/tests, but the Plan 31-01 pack contract could not distinguish a deliberately empty skeleton from a falsely complete pack or enforce exact learner-field/media/stage coverage.
- **Fix:** Added exact field/media schemas, `inventory_status`, deterministic H0-H10/P0-P13 declarations, and `coverage_mismatch` admission failure.
- **Files modified:** `src/multilang/services/korean_curriculum.py`, `tests/services/test_korean_curriculum.py`.
- **Impact:** Directly closes the plan's tampering and false-completeness threat; no new architecture, dependency, provider, or caller-controlled input was added.

**2. [Rule 1 - Test Bug] Made task-focused assertions monotonic after full-pack completion**
- **Found during:** Final sequential focused rerun.
- **Issue:** Early-task tests assumed the production pack would permanently contain only H0 or H0-H6, and the status helper conflated structural inventory state with human review state.
- **Fix:** Scoped stage assertions to their intended records, validated total count against the current final pack, and restricted review scanning to review-status fields.
- **Files modified:** `tests/services/test_korean_curriculum.py`.
- **Verification:** All three focused commands then passed sequentially, followed by all 85 curriculum tests.

**Total deviations:** 2 auto-fixed correctness gaps. Neither changed approved linguistic scope.

## Issues Encountered

- An initial pair of final focused commands was accidentally launched concurrently. Both completed, but the authoritative evidence above comes from a fresh sequential rerun of all three commands, as the plan requires.
- Supplemental ad hoc inventory scripts initially used incorrect raw-JSON key names and the Windows default output encoding; corrected read-only scripts produced the reported counts and traces.
- Ruff is unavailable offline; no installation or dependency change was made.

## Security and Privacy Review

- Public loaders remain no-argument functions over three fixed repository paths, with one-megabyte pre/post-read bounds and content-free error reason codes.
- JSON models are frozen and extra-forbidden; registry, pack, and entry hashes are independently recomputed.
- Manifest scans found no approved state, secret, absolute path, URL, remote media, halfwidth Hangul, unsupported HTML, provider/voice field, or media bytes.
- No network endpoint, authentication path, database/schema boundary, provider call, archive parser, export writer, or user/private data path was introduced; there are no additional threat flags.

## Known Stubs and Intentionally Omitted Content

- `pronunciation-i-plus-1-v1.json` intentionally has `entries: []`; Plan 31-03 owns all P0-P13 learner records.
- Hangul `reading_or_name`, `sound`, and `mnemonic` values remain unset where human evidence is absent. Required media slots are declarations only and stay `needs_review`.
- No P0-P13 content, media bytes, production provider/voice, review approval, template, export, frequency asset, grammar content, personal-source content, or visual/playback claim is included.
- These omissions are required fail-closed states and do not prevent this plan's registry/Hangul/skeleton objective.

## Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other Git delivery/destructive operation was performed.

## Authentication Gates

None.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-02 complete and Plan 31-03 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; `.planning/ROADMAP.md` remains open at `[-]` and Phase 31 was not marked complete.
- `KHAN-01`, `KHAN-02`, and `KPRO-02` are advanced but not marked complete because reviewed learner-ready and populated-pronunciation criteria remain later work.
- The reviewed planning fingerprint is `912b8a49a880de1da350fc3b6529e8d464c5e1f59c4333c151d5bd1865f56ac0`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All three focused commands passed in required sequence; all 85 curriculum tests and 123 Phase 30 regression tests passed; exact inventory/hash/provenance traces and forbidden-surface scans passed offline.
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
  summary: The existing pack model needed an explicit complete-versus-skeleton state plus exact field/media/stage coverage enforcement to represent the plan honestly and reject false completeness.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Early focused tests encoded temporary partial-pack counts and a broad status-key scan; they were made monotonic against the final production pack without weakening assertions.
</deltas>

<judgment>
<active_constraints>
Preserve Phase 30 `canonicalize_korean()` unchanged. Machine identity is NFC modern positional conjoining Jamo; Compatibility Jamo is display mapping only. Source loading remains fixed-path, bounded, local, hash-bound, provider-free, and content-safe. Every human/media status remains `needs_review` until genuine later evidence exists.
</active_constraints>
<unresolved_uncertainty>
P0-P13 learner candidates, pronunciation evidence, Portuguese copy, reviewer identities, licensed media bytes, playback evidence, templates, exports, and release authorization remain unresolved later Phase 31 work. The Korean frequency source and redistribution decision remains a Phase 32 blocker.
</unresolved_uncertainty>
<decision_posture>
Prefer exact atomic coverage, shared identity, and independently recomputed one-unknown evidence over inferred completeness. Represent absent content as an explicit blocked skeleton rather than filling it with unsupported linguistic claims.
</decision_posture>
<anti_regression>
Do not change the canonicalizer hash, substitute Compatibility or halfwidth Jamo for machine identity, omit any H0-H10 category from a complete pack, duplicate inherited orthography in pronunciation, trust serialized hashes/unknowns, add caller paths or remote fetching, or turn pending fields/media declarations into approval.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All three manifests, the curriculum service/tests, the SPEC handoff, fingerprint, and this summary exist.
- Fixed loaders parsed all artifacts; the shared validator admitted 92 Hangul entries, and the pronunciation skeleton retained 0 entries plus 92 inherited orthographic IDs.
- Every final focused, mutation, complete-curriculum, and Phase 30 regression check reported above passed.
- Rewriting the reviewed planning fingerprint reproduced `912b8a49a880de1da350fc3b6529e8d464c5e1f59c4333c151d5bd1865f56ac0`.
- Required `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>` sections are present; Phase 31 remains open and no Git action was taken.

---
*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 02*
*Completed: 2026-08-05*
