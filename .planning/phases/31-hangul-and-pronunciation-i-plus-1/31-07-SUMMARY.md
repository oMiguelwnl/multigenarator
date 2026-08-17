---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "07"
subsystem: korean-foundation-review-requests
runtime: opencode
assurance: self_checked
tags: [korean, hangul, pronunciation, review-request, rights, playback, exact-hash, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "03"
    provides: Exact 92-item Hangul and 47-item P0-P13 pronunciation candidate packs
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "04"
    provides: Independent pending curation gates and 509-slot candidate media manifest
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "06"
    provides: Judgment preserving immutable candidate bytes and genuine-evidence boundary
provides:
  - Exact scanner-readable pending request for all 139 curriculum items and 557 content/policy decisions
  - Exact scanner-readable pending request for all 509 media slots and 4,403 item/media decisions
  - Hash-bound selectors, projection digests, gate/role matrices, fixed future filenames, and no-fabrication tests
affects: [31-08, 31-09, 31-10, 31-11, 31-12]
tech-stack:
  added: []
  patterns:
    - Bind exhaustive frozen sets with exact selectors plus canonical projection digests
    - Separate request contracts from evidence and keep every decision needs_review
key-files:
  created:
    - tests/services/test_korean_foundation_review_requests.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-CURRICULUM-REVIEW.md
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-AUDIO-PLAYBACK-REVIEW.md
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-07-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Represent complete item and asset sets with exact bounded selectors and SHA-256 projections over frozen source order rather than copying candidate truth into a second mutable manifest."
  - "Keep four content gates per item in the curriculum request and three media gates per item plus per-asset legal/integrity/playback decisions in the audio request."
  - "Bind candidate display text exactly while leaving spoken text and every human, legal, and exact-byte outcome needs_review."
  - "Name only Plan 31-08 fixed future evidence filenames and create none of them in this plan."
patterns-established:
  - "Request artifacts contain one fenced JSON contract whose exact candidate bindings and aggregate projections are independently recomputable."
  - "Korean phonetics specialist and independent native speaker remain distinct required roles for every audio asset."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
requirements-completed: []
duration: 25min
completed: 2026-08-05
---

# Phase 31 Plan 07: Exact Korean Foundation Review Requests Summary

**Two hash-bound pending contracts now cover every foundation curriculum item, media slot, content gate, legal decision, exact-text binding, and playback role without supplying or implying human evidence.**

## Performance

- **Started:** 2026-08-05T23:17:25Z
- **Completed implementation/state checks:** 2026-08-05T23:42:24Z
- **Duration:** 24m 59s (reported as 25min)
- **Tasks:** 1/1
- **Request/test files created:** 3
- **Planning files updated:** 2, plus this summary
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Created one scanner-readable curriculum request bound to all five candidate manifest versions, canonical hashes, byte hashes, all 139 item identities, exact H0-H10/P0-P13 stage counts, active-rule projections, 557 pending content/policy decisions, and 563 exact role assignments.
- Created one scanner-readable media request bound to all 509 slot identities, 325 required assets, 184 optional assets, exact candidate display-text projections, all rights/integrity/playback categories, and 4,403 pending item/asset decisions.
- Preserved distinct specialist and independent-native playback roles, canonical Portuguese language identity `pt` with no selected regional policy, and fixed Plan 31-08 filenames without creating evidence files.
- Added focused tests that independently reconstruct selectors and projection hashes, compare exact matrices/counts, scan for fabricated evidence, verify request hashes, and pin all candidate bytes.
- Completed the required second-pass reconciliation and proved `human_checkpoint_count=0` from actual task tags and both request contracts.

## Strict TDD Evidence

### Task 31-07-01: Create and verify exact pending curriculum and media review requests

- **RED:** The initial focused run produced `7 failed, 1 passed in 0.36s`; all seven failures were the expected assertion that the two request artifacts did not yet exist.
- **GREEN:** Adding the minimum two scanner-readable request contracts produced `8 passed in 0.20s`.
- **REFACTOR / second-pass strengthening:** Added exact selector expansion, request-file hashes, decision-contract checks, and stronger candidate pending-state assertions. Two test assumptions were exposed and corrected: media source order interleaves kinds per item, and `inventory_status=complete` describes structural completeness independently of `review_status=needs_review`. The strengthened suite returned `8 passed in 0.22s`.
- **Coverage-gap RED:** Source-role reconciliation then exposed six P11-P13 `specialist-atomization-review-required` assignments absent from the first request contract (`1 failed, 7 passed in 0.35s`).
- **Coverage-gap GREEN:** Added one exact six-item specialist-atomization selector under the existing atomicity decisions; the final suite returned `8 passed in 0.22s`.
- **Final focused command:** `8 passed in 0.22s`.
- **Relevant Korean regression matrix:** `167 passed in 26.50s` across curriculum, curation gates, media integrity, and the new request tests.

No commits were created because the user prohibited commits and staging. RED/GREEN evidence is therefore preserved in command results and this summary rather than commit history.

## Exact Curriculum Coverage

| Dimension | Exact count |
|---|---:|
| Registry concepts | 139 |
| Hangul items (H0-H10) | 92 |
| Pronunciation items (P0-P13) | 47 |
| Total item identities | 139 |
| Per-item content gate decisions | 556 |
| Portuguese editorial-policy decisions | 1 |
| Total curriculum decisions | 557 |

### Curriculum role assignments

| Required role | Decisions |
|---|---:|
| `korean-foundation-content-reviewer` | 139 |
| `korean-curriculum-reviewer` | 139 |
| `korean-orthography-reviewer` | 92 |
| `korean-phonetics-specialist` | 53 (47 phonetics gates plus six P11-P13 atomization assignments) |
| `portuguese-reviewer` | 140 (139 item gates plus one editorial-policy decision) |
| **Total role assignments** | **563** |

The decision count remains 557: six existing P11-P13 atomicity decisions require both the curriculum role and an additional phonetics-specialist role rather than creating duplicate decisions.

## Exact Media And Playback Coverage

| Dimension | Exact count |
|---|---:|
| All candidate media slots | 509 |
| Required slots | 325 |
| Optional slots | 184 |
| Hangul slots | 368 (184 required) |
| Pronunciation slots | 141 (all required) |
| Audio slots | 233 |
| Non-audio slots | 276 |
| Per-item media gate decisions | 417 |
| Per-asset legal/integrity/playback decisions | 3,986 |
| Total media/playback decisions | 4,403 |
| Unique item/asset role bindings | 2,134 |

Asset kinds are exact: 92 each of `picture`, `strokes`, `gif`, and Hangul `audio`; 47 each of `letter_audio`, `word_audio`, and `sentence_audio`.

### Media/playback decision-role assignments

| Required role | Decisions |
|---|---:|
| `media-rights-reviewer` | 2,684 |
| `media-integrity-reviewer` | 648 |
| `audio-playback-reviewer` | 372 |
| `korean-phonetics-specialist` | 466 |
| `independent-native-speaker` | 233 |
| **Total** | **4,403** |

Every audio slot requires five distinct role capabilities; the phonetics-specialist and independent-native identities are explicitly constrained to differ. No identity was supplied.

## Exact Artifact Hashes

### Request artifacts

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `31-CURRICULUM-REVIEW.md` | `ec20559593dbc025ccd0ca5485ed1e6fa8c895c4962f58f151a5b1d3025e9bff` | 10,325 |
| `31-AUDIO-PLAYBACK-REVIEW.md` | `877eb42abe57d705d69e4a2ace077bfb905b23cd1ff22a0283fb7f256fabec44` | 17,441 |

### Byte-identical candidate manifests

| Candidate | File SHA-256 | Canonical content SHA-256 |
|---|---|---|
| `korean-concepts-v1.json` | `79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625` | `89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d` |
| `hangul-v1.json` | `80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1` | `2bdbfb60aaca1419c2bb20abc8fb9954941bc8f92cb2361c3bc778b01c9b599c` |
| `pronunciation-i-plus-1-v1.json` | `6a2eb0b6a0a467de6074ffafc2fb674a674ea96c3c2187f339d1c278aa8f55ec` | `641b06f4d1c05c70803b859aa2936fc517a1038ad190ac7c58574da8a93ea49e` |
| `korean-foundations-v1-curation.json` | `6a5ddc06cfdb2ec3546e8854986bbe28ef957d170444dafadb0e97a06980055e` | `76d08bfa4c2780111a8d7fd89e73c86ee5393609ba1f40c003cc6e77745aff6b` |
| `korean-foundations-v1-media.json` | `ad8f05f3846da9874f49a85e045b4d225f15ffdac8fba13cbd39615d94561fcc` | `e7ef7ed570b28ed70bb09a68426567ac5a2dc3df8bb33acb357d32c281e861dc` |

The candidate hashes match the pre-implementation baseline exactly. Candidate curation remains 973/973 gates at `needs_review`; all 509 media slots remain `needs_review`, with no artifact-byte hash and no review record.

## Required Second-Pass Reconciliation

The independent second pass returned `second_pass_status=passed` and recomputed rather than trusted:

- 139 item identities = 92 Hangul + 47 pronunciation.
- 509 asset identities = 368 Hangul + 141 pronunciation.
- 325 required assets = 184 Hangul + 141 pronunciation; 184 Hangul slots remain optional.
- Curriculum decisions = 557 and curriculum role assignments = 563, including six exact P11-P13 specialist-atomization assignments; media/playback decision-role total = 4,403.
- Curriculum item projection SHA-256 = `b5d0c55c4ecaf92651dde54b75a30261b2e9832a0eef1d4861d3e72481d0b27a`.
- Media asset projection SHA-256 = `a61ebccce4457e70a4e6ec59d7759297d9c2512f62094ebe769fc4f7d918e37e`.
- Exact candidate text-binding projection SHA-256 = `5ef47d0c99d209886b7a35659c465983c2cfc0dfa562b054d16bf7fc0a46881c`.
- One H0 Hangul item/audio and the P13 item's three audio slots trace from exact candidate content hashes through all applicable matrices.
- Actual Plan 31-07 task tags contain zero checkpoint tasks; both contracts independently declare zero. Therefore `human_checkpoint_count=0`.
- The future fixed evidence directory, active pointer, snapshot root, and production media root remain absent.

## Final Verification Results

| Check | Exact result |
|---|---|
| Initial RED | `7 failed, 1 passed in 0.36s` (expected missing request artifacts) |
| First GREEN | `8 passed in 0.20s` |
| Strengthened focused suite | `8 passed in 0.22s` |
| Curriculum/review/media/request regression matrix | `167 passed in 26.50s` |
| Python compile | Passed for `test_korean_foundation_review_requests.py` |
| Candidate byte/canonical hashes | All five exact and unchanged |
| Second-pass set/count/hash/role reconciliation | `second_pass_status=passed` |
| Pending-only scan | Every request decision and every candidate gate/slot remains `needs_review` |
| Side-effect boundary | No evidence files, media bytes, provider/network operation, active pointer, snapshot, activation, or output artifact created |
| Human checkpoint proof | `human_checkpoint_count=0` |
| Phase lifecycle | `phase-status 31 in_progress` returned `changed: false` |
| Reviewed planning fingerprint | `d2508b0d98f735acfc1020ee8b1f521618db270f001f6a10825a92a677444496` |

`ruff` was not installed in the offline environment (`program not found`), so it could not provide an additional style check. The authoritative planned pytest command, Python compilation, relevant 167-test matrix, exact-hash checks, and scanner reconciliation all passed.

## Files Created/Modified

### Created

- `tests/services/test_korean_foundation_review_requests.py` - independent scanner/parser, exact set/hash/count/matrix checks, no-fabrication checks, candidate byte pins, and checkpoint proof.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-CURRICULUM-REVIEW.md` - exact pending curriculum/content/Portuguese request contract.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-AUDIO-PLAYBACK-REVIEW.md` - exact pending rights/integrity/text/playback request contract.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-07-SUMMARY.md` - execution evidence and bounded Plan 31-08 handoff.

### Modified

- `.planning/SPEC.md` - records Plan 31-07 complete, every outcome pending, and Plan 31-08 next.
- `.planning/.state-fingerprint.json` - reviewed planning-state baseline.

No source, candidate manifest, service, CLI, provider, evidence, media, snapshot, pointer, activation, or exporter file was modified.

## Decisions Made

- Used exact sequence selectors plus canonical projection SHA-256 values to make complete candidate sets scanner-readable and drift-detectable without creating a second source of linguistic/media truth.
- Split the seven curation gates exactly: four content/curriculum gates in the curriculum request and three media gates in the playback request.
- Named source, attribution, license, reuse, redistribution, exact-byte integrity, exact spoken text, specialist playback, independent-native playback, and heard playback once in a global per-selector matrix; application counts prove exhaustive coverage.
- Bound candidate display text from the exact source projection but left spoken text unresolved because selecting it would fabricate phonetic evidence, especially for raw jamo.
- Kept `pt` as the only Portuguese language identity and requested one regional editorial-policy decision without choosing `pt-BR` or `pt-PT`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test bug] Corrected selector-order and inventory-status assumptions during the required second pass**
- **Found during:** Task 31-07-01 refactor/second-pass strengthening.
- **Issue:** A strengthened assertion incorrectly expected kind-grouped asset selectors to reproduce the media manifest's item-interleaved order, and incorrectly treated structural `inventory_status=complete` as a review outcome.
- **Fix:** Proved selector uniqueness plus exact set equality independently of order, and asserted structural completeness separately from top-level and per-entry pending review state.
- **Files modified:** `tests/services/test_korean_foundation_review_requests.py`.
- **Verification:** The two focused failures became `8 passed`; the complete relevant matrix returned `167 passed`.
- **Committed in:** Not committed; Git actions were explicitly prohibited.

**2. [Rule 2 - Missing critical review coverage] Added the six source-required P11-P13 specialist-atomization role assignments**
- **Found during:** Task 31-07-01 source-role reconciliation after the initial second pass.
- **Issue:** The first curriculum matrix covered every curation gate but did not separately preserve the source packs' additional `specialist-atomization-review-required` role for `ko-pron-0042` through `ko-pron-0047` (P11-P13).
- **Fix:** Added one exact six-item selector attached to the existing `curriculum_atomicity` decisions, with the Korean phonetics specialist role and explicit atomization/active-rule/ordering scopes. Decision count remains 557; role assignments increase from 557 to 563.
- **Files modified:** `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-CURRICULUM-REVIEW.md`, `tests/services/test_korean_foundation_review_requests.py`.
- **Verification:** RED was `1 failed, 7 passed`; GREEN was `8 passed`, with exact source reason code, item keys, stages, scopes, role count, and request hash asserted.
- **Committed in:** Not committed; Git actions were explicitly prohibited.

---

**Total deviations:** 2 auto-fixed (1 Rule 1 test-correctness issue, 1 Rule 2 missing critical review assignment).
**Impact on plan:** Both corrections strengthened exhaustive coverage. No candidate, runtime, provider, evidence, or production scope changed.

## Issues Encountered

- The first ad hoc second-pass command embedded Markdown backticks in a double-quoted shell command, so shell substitution corrupted its parser. It was rerun using bounded first/last JSON-brace extraction and passed; no repository file changed.
- The first final self-check counted structured marker names quoted in prose as extra opening tags. The corrected check compares exact lines and confirms one opening/closing line for each required structured section.
- Offline `ruff` checks could not run because the executable is not installed. This was non-blocking because the planned pytest suite, compilation, and broader focused matrix passed.

## Security and Privacy Review

- Both artifacts contain one bounded JSON contract with repository-relative candidate/future filenames, exact hashes, controlled selectors, and no arbitrary path, URL, archive, importer, or network surface.
- No reviewer identity, timestamp, decision outcome, regional Portuguese selection, spoken-text judgment, provider response, media byte, or downstream authority artifact is present.
- Candidate manifests are treated as untrusted frozen input and independently pinned by both canonical content hashes and exact file-byte hashes.
- The specialist/native distinction is structural and count-checked; no person can be inferred or impersonated by the requests.
- Diagnostics and summaries expose only bounded IDs, counts, versions, roles, gates, and hashes. No secret, credential, private path, or provider payload is present.
- No new network endpoint, authentication path, filesystem intake API, database/schema boundary, or production file-access surface was introduced, so there are no additional threat flags beyond the Plan 31-07 threat register.

## Known Stubs

None. `needs_review` is the required substantive state of these request contracts, not a stub. The P13 sentence text shown in the playback trace is copied and hash-bound from the frozen pending candidate; the request does not repair or promote it. Missing human/legal/media evidence is intentionally deferred to the fixed later checkpoint and does not prevent this request-only plan's goal.

## Task Commits and Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other destructive/delivery Git action was performed.

## Authentication Gates

None.

## User Setup Required

None. This plan performs no provider call, network request, credential access, media acquisition, or human checkpoint.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-07 complete and Plan 31-08 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; Phase 31 remains open at `[-]` and `.planning/ROADMAP.md` was not changed by this plan.
- `node .planning/bin/gsdd.mjs session-fingerprint write` produced `d2508b0d98f735acfc1020ee8b1f521618db270f001f6a10825a92a677444496`.
- KHAN-01, KHAN-02, KPRO-01, and KPRO-02 remain unchecked. This plan proves request coverage only, not supplied evidence or learner readiness.
- `.planning/STATE.md` and requirement checkboxes were not advanced because Phase 31 remains open and the established handoff updates only SPEC/fingerprint.

## Next Phase Readiness

- Plan 31-08 can map the exact request matrices into `proposed-curation.json`, `curriculum-review.json`, `proposed-media.json`, `audio-playback-review.json`, `rights.json`, and the four fixed reviewer records using temporary fixtures only.
- The request contracts provide exact versions, candidate/file hashes, item/asset projection hashes, counts, gate scopes, role requirements, distinct-role constraints, and evidence-field requirements needed for fixed schema validation.
- Plan 31-08 must keep both request files and all five candidate manifests byte-identical and must create only its technical README at the future fixed evidence boundary.
- No Plan 31-07 engineering blocker remains. Genuine evidence and media remain unavailable by design.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Strict TDD produced the expected missing-artifact RED and an eight-test GREEN. The strengthened focused suite, 167-test Korean matrix, compile check, five candidate byte/canonical hash pins, two request hashes, exhaustive second-pass item/asset/gate/role reconciliation, pending-only scan, no-side-effect scan, phase-open check, and planning fingerprint passed.
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
  summary: The media candidate source order interleaves slot kinds per item while the compact exhaustive selectors group IDs by kind; exact set equality, not selector-list order, is the correct reconciliation.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Source-pack inventory_status=complete records structural inventory completeness and coexists intentionally with review_status=needs_review; the strengthened test now verifies both dimensions independently.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Six P11-P13 source entries require an additional phonetics-specialist atomization role on their existing atomicity decisions; exact source-role reconciliation added those assignments without duplicating decisions.
</deltas>

<judgment>
<active_constraints>
Preserve Phase 30 canonical `ko`, the Plan 31-04 one-resolution genuine-evidence boundary, Plan 31-05 schemas, Plan 31-06 export refusal, and every candidate byte/hash. These two files are requests only. All human, legal, Portuguese, spoken-text, byte, and playback decisions remain needs_review, and technical fixture success can never become production evidence.
</active_constraints>
<unresolved_uncertainty>
Qualified reviewer identities and qualifications, Portuguese regional policy, source/attribution/license/reuse/redistribution dispositions, exact spoken text, licensed media bytes, exact-byte hashes, heard playback, fixed evidence intake, durable authority, inactive preparation, authorization, activation, and observed Anki behavior remain unavailable and later-plan work.
</unresolved_uncertainty>
<decision_posture>
Prefer exact frozen selectors, independently recomputable projection hashes, exhaustive role/gate matrices, and request-only pending state over duplicated candidate data or any inferred human/legal/media truth. Keep specialist and independent-native authority distinct.
</decision_posture>
<anti_regression>
Do not alter the five candidate manifests or the two request contracts in Plan 31-08. Do not omit any of the 139 items, 509 slots, 557 curriculum decisions, 563 curriculum role assignments (including the six P11-P13 specialist assignments), 4,403 media/playback decisions, fixed role counts, text projections, or hash bindings. Do not add arbitrary intake, fabricate evidence, create canonical evidence files before the named checkpoint, or weaken human_checkpoint_count=0 for Plans 31-07 through 31-10.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All three task artifacts, this summary, SPEC, and the reviewed fingerprint exist at the required paths.
- The final focused rerun returned `8 passed in 0.22s`.
- Both request SHA-256 values match the exact values recorded above, including curriculum request `ec20559593dbc025ccd0ca5485ed1e6fa8c895c4962f58f151a5b1d3025e9bff`, and all five candidate file hashes remain unchanged.
- Required `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>` sections occur exactly once.
- Phase 31 remains open, SPEC points to Plan 31-08, the future evidence directory/pointer/snapshot remain absent, and the fingerprint is `d2508b0d98f735acfc1020ee8b1f521618db270f001f6a10825a92a677444496`.
- Actual task-tag and request-contract reconciliation still proves `human_checkpoint_count=0`.
- No Git staging, commit, cleanup, reset, checkout, or destructive action was performed.

---
*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 07*
*Completed: 2026-08-05*
