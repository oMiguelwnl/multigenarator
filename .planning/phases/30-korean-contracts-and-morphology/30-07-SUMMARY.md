---
phase: 30-korean-contracts-and-morphology
plan: "07"
subsystem: korean-runtime-and-preview-composition
runtime: opencode
assurance: self_checked
tags: [korean, kiwi, morphology, runtime, cli, webdav, privacy, dependency-injection, tdd]
requires:
  - 30-06
provides:
  - One lazy Korean morphology service per composed runtime/app with one fingerprint shared by grounding and normal/regeneration validation
  - Provider-free local and WebDAV Korean preview composition that reuses injected grounding or one closure-scoped offline resolver
  - Count-only Korean preview success, content-free nonzero failure, and Korean-only Kiwi construction failure
affects: [30-08, 32-frequency-portuguese-text-and-audio, 33-grammar-and-personal-sources]
tech-stack:
  added: []
  patterns:
    - Composition roots own one lazy Kiwi wrapper and inject object identity rather than reconstructing analyzer configuration in consumers
    - CLI preview resolves morphology and lexical lookup locally without constructing text, provider, audio, export, or template services
    - Korean preview failures collapse exceptions and empty resolution to one controlled content-free code
key-files:
  created:
    - .planning/phases/30-korean-contracts-and-morphology/30-07-SUMMARY.md
  modified:
    - src/multilang/runtime.py
    - src/multilang/cli.py
    - tests/test_runtime.py
    - tests/cli/test_kindle_highlight_preview_command.py
    - tests/cli/test_webdav_highlight_commands.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "build_runtime_service creates or accepts exactly one lazy KiwiKoreanMorphologyService and injects that exact object into grounding plus the one validator shared by generation and regeneration."
  - "create_app reuses an injected runtime grounding resolver; otherwise it memoizes one lightweight LexicalGroundingService and one lazy morphology object for both local and WebDAV preview and any later runtime build."
  - "Korean CLI previews fail nonzero on empty, ambiguous, unavailable, or exceptional resolution using one fixed content-free code; successful Korean WebDAV preview emits only aggregate count lines."
patterns-established:
  - "Analyzer lifecycle belongs to the runtime/app composition root; consumers receive identity, not factories or independent defaults."
  - "Private Korean preview text may enter only the in-process resolver and may not appear in success counts, errors, fetched metadata, or exception details."
requirements-advanced: [KMODE-01, KMODE-02, KNLP-01, KNLP-02]
requirements-completed: []
duration: 15m
completed: 2026-08-04
---

# Phase 30 Plan 07: Shared Korean Runtime and Preview Composition Summary

**Runtime grounding, generation validation, regeneration validation, and provider-free highlight previews now share one lazily initialized Kiwi morphology object per runtime/app, with count-only Korean preview success and content-free Korean-only failure.**

## Performance

- **Started:** 2026-08-04T19:57:39Z
- **Completed final checks:** 2026-08-04T20:12:35Z
- **Duration:** approximately 15m
- **Tasks:** 2/2
- **Execution-owned files created/modified:** 8, including this summary, SPEC, and the reviewed session fingerprint
- **Assurance:** `self_checked` with strict RED/GREEN cycles, exact task commands, object-identity/laziness runtime evidence, complete CLI regressions, relevant upstream service regressions, compilation, and scoped patch checks

## Accomplishments

- Added the Korean runtime display name without adding a Korean note type, voice, asset, export, or template route.
- Extended `build_runtime_service` with an injectable Korean morphology seam and created exactly one default wrapper when no test/caller injection is supplied.
- Passed the same wrapper to `LexicalGroundingService` and to the single `TextValidationService` object already shared by `GenerateTextItemsService` and `RegenerateTextItemService`.
- Preserved lazy vendor construction: runtime composition creates the project wrapper but does not construct Kiwi until the first Korean operation; repeated operations attempt vendor construction once.
- Kept analyzer construction failure isolated to Korean while unrelated runtime startup and English behavior remain usable.
- Made `create_app` reuse an injected runtime grounding resolver when present, constructing no second adapter.
- Added one memoized closure-scoped offline grounding resolver for standalone local/WebDAV preview, backed only by `LexicalLookup(Settings.lexicon_data_dir)` and the app's one lazy morphology wrapper.
- Passed the same app morphology wrapper into a later full runtime build rather than creating a second analyzer configuration.
- Made Korean preview success count-only and made unavailable, ambiguous/empty, and exceptional resolution exit nonzero with a fixed content-free error.
- Preserved all existing non-Korean local/WebDAV output and provider-selection behavior.

## TDD Task Evidence

### Task 30-07-01: Compose one lazy Korean adapter across runtime consumers

- **RED:** `UV_OFFLINE=1 uv run pytest tests/test_runtime.py -q` produced **4 failed, 8 passed in 2.01s**. Failures proved the missing injection parameter, absent default wrapper composition, zero wrapper construction where one was required, and missing `Korean` display mapping.
- **GREEN:** Added one runtime-owned/injected morphology object, passed it by identity to grounding and the shared validator, and added the Korean display name.
- **Initial GREEN result:** The exact task command produced **12 passed in 1.99s**.
- **Final task result:** The exact task command later produced **12 passed in 2.28s** after all Plan 30-07 work.

### Task 30-07-02: Reuse the Korean resolver in local and WebDAV previews

- **RED:** `UV_OFFLINE=1 uv run pytest tests/cli/test_kindle_highlight_preview_command.py tests/cli/test_webdav_highlight_commands.py tests/test_runtime.py -q` produced **4 failed, 20 passed in 2.92s**. The injected resolver was unused, standalone preview built no shared resolver, and unavailable local/WebDAV resolution incorrectly returned exit code 0.
- **GREEN:** Added injected-resolver reuse, one closure-scoped offline resolver/morphology pair, count-only Korean WebDAV output, and a content-free fail-closed CLI guard.
- **Test-harness correction:** The first post-implementation run reached every intended branch but four call-text assertions included the synthetic title because the new fixture title did not match the established Kindle parser fixture convention. Changing only the title to the existing `Synthetic Learner Reader` pattern corrected the fixture; no production behavior was changed for this correction.
- **Initial GREEN result:** The exact task command then produced **24 passed in 2.94s**.
- **Final task result:** The exact task command produced **24 passed in 2.97s**.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 runtime command | `12 passed in 2.28s` |
| Task 2 combined command | `24 passed in 2.97s` |
| Korean wiring/privacy selection | `8 passed, 16 deselected in 1.59s` |
| Same-file non-Korean regression selection | `16 passed, 8 deselected in 2.61s` |
| Complete CLI suite | `73 passed in 22.81s` |
| Relevant morphology/grounding/preview/ingestion/validation/generation/regeneration suites | `181 passed in 36.93s` |
| Python compilation of all five Plan 30-07 source/test files | Exit 0 with no output |
| Scoped patch whitespace checks | Exit 0; Windows LF-to-CRLF notices only |
| Phase lifecycle helper | Phase 30 remained `in_progress`; `changed: false` |
| Session fingerprint | `cded6cdcc89d9a80f107d7b48b91024c8ee1de2b0e6ab4fdbd4229b286fcc724` |

Every `uv` command used `UV_OFFLINE=1`. Tests used local SQLite, parser fixtures, typed in-process identities, local lookup objects, and deterministic fakes. No live provider, HTTP, network, paid, quota, audio, export, template, production database, or corpus operation ran.

## Object Identity and Laziness Evidence

The runtime test and an independent offline composition smoke check produced:

```text
grounding_is_shared=True
generation_matcher_is_shared=True
regeneration_matcher_is_shared=True
validators_are_shared=True
factory_calls_after_startup=0
factory_calls_after_two_korean_operations=1
korean_statuses=unavailable,unavailable
failure_is_content_free=True
```

The app-lifecycle smoke check then exercised standalone Korean preview followed by a later runtime-resolving command on the same `create_app` closure:

```text
preview_exit=0
runtime_trigger_exit=0
app_morphology_factory_calls=1
app_offline_grounding_instances=1
preview_uses_app_morphology=True
later_runtime_uses_app_morphology=True
```

- `service.grounding_service._korean_morphology is morphology`.
- `generation_validator.korean_matcher is morphology`.
- `regeneration_validator.korean_matcher is morphology`.
- `generation_validator is regeneration_validator`, so normal generation and regeneration cannot drift to separate fingerprints.
- Runtime startup performs zero vendor-factory calls; two Korean operations produce exactly one construction attempt.
- The unavailable factory's private message never enters typed results.
- The CLI injected-service test replaces adapter construction with a raising sentinel; Korean preview succeeds through the injected grounding resolver with zero second-adapter construction.
- The standalone app test invokes both local and WebDAV Korean preview on one app and proves one morphology factory call, one lightweight grounding resolver instance, two resolver calls, and zero full runtime/provider/audio constructions.
- The independent app-lifecycle smoke proves that preview's morphology object is also the exact object passed into a later runtime build from that app closure.

## High-Leverage Second Pass

| Surface | Trace result |
|---|---|
| Direct runtime composition | One wrapper accepted/created once and injected into grounding plus shared validation |
| Initial generation validation | Uses the shared validator's exact wrapper and fingerprint |
| Regeneration validation | Uses the same validator object and exact wrapper; no regeneration-specific matcher |
| Non-Korean startup | Completes before vendor construction; English deck-name behavior remains operational |
| First Korean operation with failed factory | Returns controlled `unavailable`; failure affects Korean only |
| Repeated Korean operation | Reuses the cached failed initialization; factory count remains one |
| Injected CLI runtime preview | Reuses `service.grounding_service`; second adapter constructor is unreachable |
| Standalone local preview | Uses one closure-scoped `LexicalGroundingService` with local lookup and lazy morphology |
| Standalone WebDAV preview | Reuses that same closure-scoped resolver; successful Korean output contains only five count keys |
| Unavailable/empty/exceptional preview | Exits nonzero with only `korean_resolution_unavailable`; no text, path, vendor detail, or traceback |
| Existing local/WebDAV languages | All prior command tests and output contracts remain green |

The constructor scan found three deliberate fallback sites: one runtime composition site, one memoized CLI app composition site, and the pre-existing standalone `TextValidationService` fallback. Composed runtimes always inject the runtime object, so the standalone validator fallback is not invoked by runtime generation or regeneration and was left unchanged to honor the no-generic-validation-change boundary.

## Files Created/Modified

### Created

- `.planning/phases/30-korean-contracts-and-morphology/30-07-SUMMARY.md` - strict TDD, composition, privacy, regression, and handoff evidence.

### Modified

- `src/multilang/runtime.py` - optional morphology injection, one default wrapper, exact grounding/shared-validator handoff, and Korean display name.
- `src/multilang/cli.py` - injected resolver reuse, memoized offline resolver/morphology composition, safe preview guard, and count-only Korean WebDAV preview.
- `tests/test_runtime.py` - object identity, shared-validator identity, wrapper/vendor laziness, unavailable isolation, safe failure, and display-name evidence.
- `tests/cli/test_kindle_highlight_preview_command.py` - injected resolver reuse, zero second adapter, aggregate-only output, and content-free nonzero failure.
- `tests/cli/test_webdav_highlight_commands.py` - one offline resolver across local/WebDAV calls, zero full runtime construction, count-only Korean output, and content-free failure.
- `.planning/SPEC.md` - Current State advanced through Plan 30-07 while Phase 30 remains open.
- `.planning/.state-fingerprint.json` - reviewed planning-state fingerprint rewritten after the SPEC handoff.

## Git Actions

None. Per explicit user instruction and the carried Phase 30 execution convention, no files were staged or committed, and no branch, push, PR, amend, reset, stash, clean, checkout, restore, tag, or other delivery/destructive action was performed.

## Decisions Made

- Composition owns adapter identity: consumers receive one object rather than receiving factories or independently evaluating defaults.
- The existing one-validator generation/regeneration shape remains authoritative; Plan 30-07 injects into it rather than adding another validation service.
- Standalone previews do not call `build_runtime_service`; they need only settings-based lexical lookup and local morphology.
- An injected runtime service with a usable grounding resolver is always preferred over the lightweight resolver, preventing duplicate app adapters.
- Empty resolution is treated like unavailable/ambiguous resolution at the CLI boundary because preview cannot safely distinguish a real zero from inconclusive morphology.
- Korean WebDAV preview suppresses fetched hash/path/size metadata and emits only aggregate counts; existing non-Korean WebDAV metadata remains unchanged.
- The shared preview builder's prior service-level count contract remains unchanged; nonzero fail-closed behavior is applied specifically at the CLI command boundary owned by this plan.

## Deviations from Plan

None - the plan was implemented within its runtime/CLI composition boundaries. No provider, network, audio, export, template, note type, asset, schema, endpoint, or generic validation behavior was added or changed.

## Issues Encountered

- One initial object-evidence shell command had quoting errors, then a corrected run printed valid evidence but Windows held the SQLite file open during temporary-directory cleanup. The final run explicitly closed the SQLAlchemy session/engine and exited successfully with the same evidence.
- The first Task 2 GREEN attempt exposed a test-fixture title mismatch, not a production defect. The test fixture was aligned to the established parser fixture title and the exact command passed.
- Phase 30 was already open, so `phase-status 30 in_progress` correctly made no ROADMAP change.

## Security and Privacy Review

- Local and cached WebDAV source text is passed only to the in-process resolver; neither success nor failure output echoes it.
- The preview guard catches resolver exceptions, discards raw messages/tracebacks, and emits one fixed reason code.
- Korean WebDAV preview failures print no cached path, remote path, content hash, source text, vendor detail, or traceback.
- Successful Korean preview output is limited to imported, extracted, rejected, duplicate, and planned counts.
- Preview composition never constructs provider, audio, export, or template services and does not require their credentials.
- Analyzer construction remains local and lazy, with one bounded worker inherited from the pinned wrapper configuration.
- No new endpoint, authentication path, schema boundary, network route, provider call, or threat surface outside the plan threat register was introduced.

## Known Stubs

None. Counting resolvers, unavailable factories, typed synthetic identities, and forbidden-runtime sentinels are deterministic test evidence, not runtime stubs. Complete three-mode closure evidence remains intentionally assigned to Plan 30-08.

## User Setup Required

None. No provider, audio, export, network, production database, or credential setup is required for this offline composition work.

## State and Handoff

- `.planning/SPEC.md` records Plans 30-01 through 30-07 complete while Phase 30 remains in progress.
- `.planning/ROADMAP.md` remains open at `[-]`; no Phase 30 completion or requirement checkbox was claimed.
- `KMODE-01`, `KMODE-02`, `KNLP-01`, and `KNLP-02` remain advanced but not complete pending Plan 30-08 and phase verification.
- The reviewed session fingerprint is `cded6cdcc89d9a80f107d7b48b91024c8ee1de2b0e6ab4fdbd4229b286fcc724`.
- Plan 30-08 may consume this composition, but it must not create another Kiwi object, weaken Plan 30-06 identity/fingerprint consensus, expose preview content, or move provider/audio/export/template work into Phase 30.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Strict RED/GREEN cycles, exact task commands, object-identity/laziness smoke evidence, complete CLI regressions, relevant upstream service regressions, Korean/non-Korean selections, compilation, privacy assertions, and scoped patch checks all passed offline.
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
  summary: The first custom Kindle test title entered normalized highlight text; aligning it with the established parser fixture convention fixed only the test harness and preserved the valid RED/GREEN production order.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Windows retained the SQLite handle in the first object-evidence smoke cleanup; explicitly closing the session and engine produced a successful final evidence run without repository changes.
</deltas>

<judgment>
<active_constraints>
Keep `ko` canonical and preserve Plan 30-06's exact persisted identity, equal persisted/active/result fingerprints, typed top-two consensus, content-free failure, and Korean Tatoeba denial. Every composed runtime/app must own at most one lazy morphology wrapper; grounding, normal validation, regeneration validation, and preview must reuse that object. Preview remains local, source-backed, aggregate-only, and provider/audio/export/template free.
</active_constraints>
<unresolved_uncertainty>
Complete offline frequency, word-list, and highlight integration plus broad existing-mode closure remains Plan 30-08. Korean sentence naturalness, register, translation quality, and calibrated length remain Phase 32. No approved production Korean lexical/frequency source or redistribution decision exists.
</unresolved_uncertainty>
<decision_posture>
Object identity at the composition root is the analyzer-policy authority. Prefer a review-required false negative over constructing another analyzer, inferring sense, falling through to generic matching, or exposing private preview content. Lightweight preview is acceptable only because it reuses the same local resolver contract and morphology object without full runtime providers.
</decision_posture>
<anti_regression>
Do not instantiate Kiwi per handler/card/consumer; do not separate generation and regeneration validators; do not make preview call a full provider/audio runtime; do not print Korean WebDAV paths/content/metadata; do not weaken Plan 30-06 matching; and do not alter non-Korean provider selection, CLI highlight output, validation, regeneration, audio, export, or template behavior.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All eight execution-owned files exist, including this summary, the SPEC handoff, and the reviewed planning-state fingerprint.
- The final exact combined task command passed with `24 passed in 2.97s`; the final runtime-only command passed with `12 passed in 2.28s`.
- Object-identity, app-lifecycle reuse, zero-startup-construction, one-attempt-after-two-operations, content-free failure, full CLI, relevant upstream service, compilation, and scoped whitespace claims match captured offline output.
- Required structured sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) and the TDD/object-identity evidence sections are present and substantive.
- Phase 30 remains open at `[-]`, no `30-08-SUMMARY.md` exists, and no requirement checkbox was closed.
- The reviewed session fingerprint rewrote successfully with hash `cded6cdcc89d9a80f107d7b48b91024c8ee1de2b0e6ab4fdbd4229b286fcc724`.
- The staging area remains empty; no git delivery or destructive action occurred.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 07*
*Completed: 2026-08-04*
