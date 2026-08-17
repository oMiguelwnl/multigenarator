---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "03"
subsystem: korean-pronunciation-curriculum
runtime: opencode
assurance: self_checked
tags: [korean, pronunciation, strict-i-plus-1, provenance, sha256, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "02"
    provides: Frozen 139-concept registry, complete H0-H10 inventory, and fixed P0-P13 pronunciation skeleton
provides:
  - Complete 47-entry P0-P13 pronunciation candidate inventory
  - Recomputed one-target-unknown and active-rule prerequisite proof for every candidate
  - Exact nine-field learner inputs with separate rich pronunciation evidence and pending media identities
  - Cross-pack mutation coverage for every P-stage family and fixed-source integrity
affects: [31-04, korean-foundation-review, korean-foundation-media, korean-foundation-export]
tech-stack:
  added: []
  patterns:
    - Pronunciation candidates inherit completed orthography and introduce exactly one phonological target
    - Candidate source data remains distinct from qualified approval and export readiness
    - Unavailable specialist, Portuguese, auditory, and media truth is represented as typed needs_review state
key-files:
  created:
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-03-SUMMARY.md
  modified:
    - data/korean_foundations/pronunciation-i-plus-1-v1.json
    - src/multilang/services/korean_curriculum.py
    - tests/services/test_korean_curriculum.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Preserve the Plan 31-02 registry and Hangul bytes; pronunciation inherits all 92 completed orthographic identities."
  - "Treat source-backed Korean forms as reviewable candidates, never specialist approval; all human and media gates remain needs_review."
  - "Reject unrelated alphabetic scripts and any source-candidate self-approval before strict curriculum admission."
requirements-advanced: [KPRO-01, KPRO-02]
requirements-completed: []
duration: 24min
completed: 2026-08-05
---

# Phase 31 Plan 03: Complete P0-P13 Pronunciation Candidate Inventory Summary

**A hash-bound 47-entry P0-P13 pronunciation pack now preserves one-new-concept sequencing, active-rule prerequisites, inherited Hangul identity, exact nine-field inputs, and explicit human/media review blockers.**

## Performance

- **Started:** 2026-08-05T20:55:33Z
- **Completed final checks:** 2026-08-05T21:19:52Z
- **Duration:** 24 minutes
- **Tasks:** 2/2
- **Files created/modified:** 6
- **Assurance:** `self_checked` through strict RED/GREEN task gates, every-stage mutations, the complete 136-test curriculum suite, 126 Phase 30/Korean regressions, fixed-byte checks, and forbidden-surface scans
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Populated all **47 atomic pronunciation targets** across contiguous P0-P13 stages with exact category coverage.
- Recomputed each entry's sole target unknown against **92 inherited orthographic concepts** and all earlier phonological targets.
- Declared **25 active non-target rule references** spanning six distinct prior rules; every reference resolves to an earlier known prerequisite.
- Preserved canonical spelling, normative pronunciation, surface realization, optional IPA, register/context, provenance, active rules, and exact nine-field learner inputs as distinct evidence.
- Kept **241 pending review records**, **141 pending media slots**, all **47 Portuguese translation pairs**, all optional IPA values, and unresolved P11-P13 evidence fail-closed.
- Proved omission, fusion, forged unknown, cycles, forward edges, missing active rules, hash drift, unsupported scripts, and premature approval cannot pass validation.

## TDD Task Evidence

### Task 31-03-01: Populate P0-P7 foundations and core alternations

- **Initial RED correction:** The first draft produced 13 failures while two empty-pack assertions passed vacuously. Those assertions were strengthened before implementation, after which all 15 focused tests failed against the zero-entry skeleton.
- **GREEN:** P0-P7 candidates then passed the focused sequence with `15 passed, 85 deselected`.
- **Final sequential check:** `15 passed, 121 deselected in 1.04s` after the complete P0-P13 pack and later mutation tests existed.
- **Coverage:** P0 timing/vowel/null-onset/sonorant/liquid foundations, P1 onset contrasts, P2 unreleased and seven coda outputs, P3 liaison, P4 tensification, P5 three nasalization families, P6 directional aspiration, and P7 two palatalization targets.

### Task 31-03-02: Complete P8-P13 and audit all three packs

- **RED:** Full-pack tests failed while P8-P13 were absent and the validator did not yet reject unrelated alphabetic candidate text or source-candidate self-approval.
- **First GREEN:** The populated inventory and primary cross-pack gates produced `116 passed`.
- **Second pass:** Added an independent mutation for every P-stage plus cycle, omission, fusion, forward-edge, forged-unknown, active-rule, and hash-drift cases; the final suite produced `136 passed`.
- **Coverage:** P8 liquid processes/`ㄴ` insertion, P9 environment-specific complex codas, P10 four contraction families, blocked P11 reduction, four blocked P12 auditory/prosodic targets, and one explicit blocked P13 ordering relation.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 focused gate, rerun sequentially | `15 passed, 121 deselected in 1.04s` |
| Complete curriculum source/mutation suite | `136 passed in 5.79s` |
| Independent pronunciation mutation/cross-pack/every-stage slice | `40 passed, 96 deselected in 2.84s` |
| Phase 30 and Korean domain/language/morphology/fingerprint/integration regressions | `126 passed in 37.96s` |
| Fixed registry and Hangul byte hashes | Unchanged from Plan 31-02 |
| Approval/URL/secret/TODO/FIXME/placeholder scan | No findings |
| Review-status audit | No `approved` literal; all unavailable human/media evidence remains `needs_review` |
| Planning phase status | `phase-status 31 in_progress` returned `changed: false` |
| Reviewed planning fingerprint | `4d375b00748d230c2b8b6509faeefab791dcc9e82ce8a566fe81d376eb316490` |

## Inventory Evidence

| Stage | Entries | Locked families |
|---|---:|---|
| P0 | 8 | Timing, vowels, null onset, sonorants, and two `ㄹ` environments |
| P1 | 6 | Plain/aspirated/tense and affricate/fricative onset contrasts |
| P2 | 8 | Unreleased coda plus seven output categories |
| P3 | 1 | Vowel-initial morpheme liaison |
| P4 | 1 | Post-obstruent tensification |
| P5 | 3 | Velar, coronal, and labial nasalization |
| P6 | 2 | Two directional `ㅎ` aspiration families |
| P7 | 2 | `ㄷ` and `ㅌ` palatalization |
| P8 | 3 | Liquid assimilation, nasalization, and `ㄴ` insertion |
| P9 | 3 | Complex coda before consonant/vowel and interaction |
| P10 | 4 | `하여`, `되어`, `보아`, and `주어` contraction families |
| P11 | 1 | Register/context-marked reduction candidate |
| P12 | 4 | Phrase accent, focus, boundary intonation, and rate effects |
| P13 | 1 | Explicit rule-ordering relation |

All 47 sequences and target IDs are unique. The validator admitted every target only after recomputing exactly that target as unknown. The pack contains **25 total active non-target declarations** over six distinct prior rule IDs; none is a forward dependency.

The locked learner field order remains:

```text
Spellings, Sound, letter_audio, Example Word, word_audio,
Word Translation, Example Sentence, sentence_audio, Sentence Translation
```

Required media slots are deterministic identities and schema obligations only. They do not imply media bytes, rights, playback evidence, or approval.

## Hash and Provenance Evidence

| Artifact | Canonical content hash | File SHA-256 |
|---|---|---|
| Registry | `89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d` | `79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625` |
| Hangul pack | `2bdbfb60aaca1419c2bb20abc8fb9954941bc8f92cb2361c3bc778b01c9b599c` | `80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1` |
| Pronunciation pack | `641b06f4d1c05c70803b859aa2936fc517a1038ad190ac7c58574da8a93ea49e` | `6a2eb0b6a0a467de6074ffafc2fb674a674ea96c3c2187f339d1c278aa8f55ec` |

The pronunciation file is **468,408 bytes** and remains bound to registry content hash `89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d`. Every entry cites inert NIKL source identity/version/hash metadata; no fetch path, URL, credential, provider, model, or approval is present.

Phase 30 `canonicalize_korean()` source hash remains `d3ab62a1f26d494d024ccf3c5c9ed20fd4efdbc18d05d71d441209337e83fb6b`.

## High-Leverage Trace

- **P3 liaison:** `ko-pron-0023` uses `옷 + 이` / `[오시]`, targets only `phonology.p3.liaison.vowel.initial.morpheme`, and recomputes that target as its sole unknown.
- **P9 interaction:** `ko-pron-0035` uses `읽다` / `[익따]`, declares earlier unreleased-coda and tensification rules, and introduces only `phonology.p9.complex.coda.before.consonant`.
- **P12 auditory candidate:** `ko-pron-0043` targets phrase accent but keeps spelling, sound, specialist atomization, and auditory evidence at `needs_review`, with six explicit pending gates.
- **P13 ordering relation:** `ko-pron-0047` uses candidate spelling `읽는`, declares earlier coda/nasalization/complex-coda rules, introduces only the ordering-relation target, and leaves sound/specialist evidence blocked.

## Files Created/Modified

- `data/korean_foundations/pronunciation-i-plus-1-v1.json` — complete ordered P0-P13 candidate source pack.
- `src/multilang/services/korean_curriculum.py` — bounded candidate-script and no-source-self-approval checks required by the threat model.
- `tests/services/test_korean_curriculum.py` — focused P0-P7, full P8-P13, every-stage, cross-pack, and adversarial mutation proof.
- `.planning/SPEC.md` — Plan 31-03 completion state and Plan 31-04 handoff.
- `.planning/.state-fingerprint.json` — reviewed planning-state baseline.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-03-SUMMARY.md` — execution evidence and judgment.

The fixed registry and Hangul artifacts were read and hashed but not modified.

## Decisions Made

- Reused all Plan 31-02 orthographic identities, including H7/H8 coda concepts; no pronunciation-local duplicate identity was created.
- Retained candidate Korean forms only as source-backed material under specialist review. Provenance and hashes establish integrity, not linguistic approval.
- Kept every Portuguese translation pair as `needs_review` instead of synthesizing unsupported copy.
- Kept optional IPA absent for all 47 entries rather than using romanization, G2P, an LLM, or a provider as authority.
- Kept P11-P13 explicitly non-exportable until qualified atomization, auditory, media-rights, and exact-byte playback evidence exists.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test Bug] Removed vacuous empty-skeleton success from the Task 1 RED gate**
- **Found during:** Task 31-03-01.
- **Issue:** Two initial coverage assertions could pass against the zero-entry pronunciation skeleton, weakening proof that implementation was absent.
- **Fix:** Strengthened the assertions before data implementation so all 15 focused tests failed during RED.
- **Files modified:** `tests/services/test_korean_curriculum.py`.
- **Verification:** Corrected RED produced 15 failures; final focused gate produced `15 passed, 121 deselected`.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

**2. [Rule 2 - Missing Critical Correctness] Enforced script bounds and blocked source-candidate self-approval**
- **Found during:** Task 31-03-02 and its threat-model mutation pass.
- **Issue:** The shared validator did not reject unrelated alphabetic candidate text or every path by which a source candidate could claim review approval.
- **Fix:** Added bounded Korean-candidate text checks and recursive source review-status enforcement with content-free diagnostics.
- **Files modified:** `src/multilang/services/korean_curriculum.py`, `tests/services/test_korean_curriculum.py`.
- **Verification:** Unsupported-script and premature-approval mutations fail; all 136 curriculum tests and 126 regression tests pass.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

---

**Total deviations:** 2 auto-fixed correctness issues (1 test bug, 1 missing critical validation).
**Impact on plan:** Both fixes strengthen the assigned evidence and threat-model gates. No dependency, provider, endpoint, persistence, export, or linguistic approval scope was added.

## Issues Encountered

- The final read-only inventory script initially assumed target/stage fields were top-level. Schema inspection showed `stage_id` and nested `evidence.target_concept_id`; the corrected command produced the counts above without changing production files.
- A read-only high-leverage trace initially hit the Windows CP1252 console limit for Hangul. Rerunning with `PYTHONIOENCODING=utf-8` produced the trace above.
- `rg` is unavailable in this environment (`command not found`), so the equivalent bounded Python scanner was used. It found no approval, URL, secret, TODO, FIXME, or placeholder marker.

## Security and Privacy Review

- Public source loaders remain no-argument, fixed-path, bounded local JSON loaders; no caller-controlled path, URL, archive, APKG, network, or code-evaluation surface was added.
- Pydantic source models remain frozen and extra-forbidden; registry, pack, and entry hashes are recomputed rather than trusted.
- New checks reveal only family/item/stage/reason metadata and do not echo candidate source text or local paths.
- No network endpoint, authentication path, database/schema boundary, provider call, media byte, personal data path, or other new threat surface was introduced; there are no additional threat flags.

## Known Stubs and Intentionally Blocked Evidence

- `pronunciation-i-plus-1-v1.json:491` and equivalent fields on all 47 records retain `ipa: null`; optional IPA requires qualified evidence and is not needed for candidate-inventory completion.
- `pronunciation-i-plus-1-v1.json:483-485` and equivalent fields on all 47 records retain Portuguese word/sentence translation values as `needs_review`; Plan 31-04 and later receipt flows own qualified review.
- `pronunciation-i-plus-1-v1.json:10602-12056` contains intentionally blocked P11-P13 specialist/auditory values. P12 does not invent learner spelling/sound, and P13 preserves candidate `읽는` while leaving sound and ordering approval unresolved.
- All 141 media slots are identities only: no audio bytes, rights decision, voice/provider metadata, checksum-bound playback approval, or export-ready media is present.
- These states are required by the plan's closure limit and do not prevent complete technical P0-P13 candidate coverage.

## Task Commits and Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other Git delivery/destructive action was performed.

## Authentication Gates

None.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-03 complete and Plan 31-04 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; `.planning/ROADMAP.md` remains open at `[-]`.
- `KPRO-01` and `KPRO-02` are advanced but remain unchecked because reviewed learner-ready media, templates, all-format export, and approval are later Phase 31 work.
- The reviewed planning fingerprint is `4d375b00748d230c2b8b6509faeefab791dcc9e82ce8a566fe81d376eb316490`.

## Next Phase Readiness

- Plan 31-04 can define independent Korean phonetics, orthography, Portuguese, auditory, rights, and exact-byte playback gates against a complete immutable candidate inventory.
- No engineering blocker remains for Plan 31-04.
- Learner-ready activation/export remains deliberately blocked until genuine review and media receipts arrive in later plans.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Both task gates passed in sequence; all 136 curriculum tests, 40 independent second-pass tests, 126 Korean regressions, fixed-byte checks, and forbidden-surface scans passed offline.
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
  summary: Initial Task 1 assertions needed strengthening so an empty pronunciation skeleton could not partially satisfy the RED gate.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The existing validator needed bounded unrelated-script and source-self-approval rejection to satisfy the plan's explicit mutation and spoofing mitigations.
</deltas>

<judgment>
<active_constraints>
Preserve Phase 30 `canonicalize_korean()` and Plan 31-02 registry/Hangul bytes unchanged. Source loading remains fixed-path, bounded, local, hash-bound, provider-free, and content-safe. Every candidate introduces one target unknown; all active non-target rules are earlier prerequisites. Candidate provenance never constitutes qualified review.
</active_constraints>
<unresolved_uncertainty>
P11 reductions, P12 auditory/prosodic contrasts, P13 ordering approval, Portuguese regional policy, reviewer identities, licensed exact media, playback evidence, templates, exports, and release authorization remain later Phase 31 work. The Korean frequency source and redistribution decision remains a Phase 32 blocker.
</unresolved_uncertainty>
<decision_posture>
Prefer exact atomic candidate coverage, shared identity, and independently recomputed evidence over invented phonetic or learner-ready truth. Keep every absent fact explicit, actionable, and non-exportable.
</decision_posture>
<anti_regression>
Do not change fixed source hashes, duplicate inherited orthography, omit a P0-P13 category, pre-know the target, hide an active rule, use romanization/G2P/LLM/provider output as authority, synthesize Portuguese or IPA, feed raw glyphs to TTS, or turn source candidates and pending media identities into approval.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All six Plan 31-03 data, service, test, planning, fingerprint, and summary artifacts exist.
- The pronunciation manifest parses with 47 entries and 47 unique targets; its SHA-256 and the fixed registry/Hangul hashes match the values recorded above.
- The reviewed planning fingerprint parses and matches `4d375b00748d230c2b8b6509faeefab791dcc9e82ce8a566fe81d376eb316490`.
- Required `<checks>`, `<handoff>`, `<deltas>`, `<judgment>`, known-stub, deviation, and handoff sections are present.
- `git diff --check` reported no whitespace errors; only existing Windows LF-to-CRLF conversion warnings were emitted.
- Phase 31 remains open, KPRO requirements remain unchecked pending later review/export work, and no Git action was taken.

---
*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 03*
*Completed: 2026-08-05*
