---
phase: 30-korean-contracts-and-morphology
plan: "08"
subsystem: korean-offline-closure-evidence
runtime: opencode
assurance: self_checked
tags: [korean, kiwi, morphology, sqlite, persistence, privacy, canonical-code, regression, tdd]
requires:
  - 30-07
provides:
  - Offline three-mode Korean evidence through real runtime composition, disposable SQLite, commit/expire/reload, and real Kiwi
  - Persisted-identity proof for NFC inflection, POS homographs, strict matching, and durable review outcomes
  - Scanner-readable locale-only ko-KR gate plus unchanged generic field, blank Image, and exact ko tag compatibility
  - Focused, existing-mode, Python 3.12, dependency-lock, and full-suite regression evidence
affects: [phase-30-verification, 31-hangul-and-pronunciation-i-plus-one, 33-grammar-and-personal-sources, 34-export-review-and-evidence]
tech-stack:
  added: []
  patterns:
    - Closure tests fake only external sentence, translation, and audio boundaries while retaining real orchestration, database lifecycle, and linguistic analysis
    - Persisted Korean identity is expired and reloaded before it drives matcher and review assertions
    - Production locale scans use one exact path-and-line allowlist instead of broad substring exceptions
key-files:
  created:
    - tests/integration/test_korean_modern_flow.py
    - .planning/phases/30-korean-contracts-and-morphology/30-08-SUMMARY.md
  modified:
    - tests/services/test_korean_language_support.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Phase 30 closure evidence uses real runtime services, SQLite persistence, session expiration/reload, and real Kiwi; only network/provider/audio boundaries are deterministic fakes."
  - "The production ko-KR allowlist contains exactly the explicit KOREAN_PROVIDER_LOCALE constant line; every internal job, key, path, cache, persisted language, and tag remains ko."
  - "Generic note construction proves compatibility only: it does not claim Korean templates, APKG readiness, approved content/media, or visual acceptance."
patterns-established:
  - "A closure integration must prove behavior from source mode through durable reload rather than asserting only in-memory domain objects."
  - "Private-source evidence may retain raw text only in its private repository; public rows and manifests expose hashes, indexes, and canonical lexical identity without paths or excerpts."
requirements-advanced: [KMODE-01, KMODE-02, KNLP-01, KNLP-02]
requirements-completed: []
duration: 30m
completed: 2026-08-04
---

# Phase 30 Plan 08: Offline Korean Closure Evidence Summary

**All three Korean modern source modes now have offline executable evidence through real runtime wiring, durable SQLite reload, and real Kiwi, with strict persisted-identity matching, private-highlight boundaries, canonical `ko` enforcement, and 1,168-test regression proof.**

## Performance

- **Started:** approximately 2026-08-04T20:13:00Z
- **Completed final checks:** 2026-08-04T20:43:16Z
- **Duration:** approximately 30m
- **Tasks:** 2/2
- **Execution-owned files created/modified:** 5, including this summary, the SPEC handoff, and the reviewed session fingerprint
- **Assurance:** `self_checked` with strict RED/GREEN cycles, every exact plan command, focused homograph/privacy traces, canonical allowlist review, compilation, no-touch checks, and a full offline suite

## Accomplishments

- Added one scanner-readable integration that runs frequency, word-list, and Kindle-highlight requests as canonical `ko` through `build_runtime_service` using real ingestion/repositories, disposable SQLite, and the shared real Kiwi service.
- Committed the test database transaction, called `session.expire_all()`, and reloaded jobs/candidates before comparing typed Korean identity and driving matching/review assertions.
- Proved the three modes persist one core identity for `공부하다`: NFC canonical value, lemma, POS, source-backed sense, ordered morpheme signature, and analyzer fingerprint agree after reload.
- Proved an NFD submitted inflection survives persistence while a noun/predicate homograph remains POS-distinct and fails closed through both direct matching and text validation.
- Proved private highlights retain valid one-syllable and attached/compound morphology while public persistence omits the raw excerpt, input path/name, context, normalized-text key, source-path key, and token dump.
- Exercised the existing generic note builder for representative frequency, word-list, and highlight rows, preserving each established field set, blank `Image`, and exactly one `ko` tag without modifying exporter or template source.
- Added a production scanner across `src/**/*.py` and `scripts/**/*.py` whose only accepted `ko-KR` occurrence is the exact `KOREAN_PROVIDER_LOCALE` declaration.
- Reasserted three-mode run-key identity, Portuguese definition/translation policy, missing unapproved Korean frequency asset, absent Korean voice/Tatoeba fallback, exact Kiwi dependency pins, and canonical runtime/tag identity.
- Passed every focused, existing-mode, Python 3.12, dependency-lock, and full-suite gate without modifying production code.

## TDD Task Evidence

### Task 30-08-01: Prove offline Korean three-mode identity, persistence, privacy, and generic tags

- **Initial RED:** `uv run pytest tests/integration/test_korean_modern_flow.py -q` produced **1 failed in 0.16s** before the flow helper existed.
- **First GREEN:** The first mode contract produced **1 passed in 3.18s**.
- **Second RED:** Reloaded identity/matcher/review assertions produced **1 failed, 1 passed in 5.37s**.
- **Second GREEN:** The two implemented contracts produced **2 passed in 7.61s**.
- **Third RED:** NFD and POS-homograph evidence produced **1 failed, 2 passed in 9.68s**.
- **First third-cycle GREEN attempt:** Real Kiwi reached the intended flow but rejected ambiguous synthetic `물`/`학교` projections, producing **1 failed, 2 passed in 9.50s**. Diagnostic runs confirmed the production fail-closed behavior was correct.
- **Corrected third GREEN:** Replacing only the ambiguous fixture with the consensus-stable `눈은 매일 공부해요` evidence produced **3 passed in 9.48s**; no production code changed.
- **Fourth RED:** Private-persistence and generic-artifact assertions produced **2 failed, 2 passed in 11.72s**.
- **Fourth GREEN:** Completing the privacy/artifact evidence produced **4 passed in 11.70s**.
- **Final exact task result:** `uv run pytest tests/integration/test_korean_modern_flow.py -q` produced **4 passed in 11.72s**.

### Task 30-08-02: Enforce canonical scan and complete anti-regression closure

- **RED:** Adding the exact production scan and cross-contract test produced **1 failed, 7 passed in 0.79s** because the new cross-contract expectations were not yet complete.
- **GREEN:** Completing the narrow allowlist, run-key/policy/asset/tag assertions, and generic row helper produced **8 passed in 0.79s**.
- **Final exact task result:** `uv run pytest tests/services/test_korean_language_support.py -q` produced **8 passed in 0.77s**.

No task commits were created because the user explicitly prohibited all Git delivery actions. The RED/GREEN command evidence was preserved directly instead.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 integration command | `4 passed in 11.72s` |
| Task 2 canonical support command | `8 passed in 0.77s` |
| Exact focused Phase 30 command | `401 passed, 10 warnings in 51.53s` |
| Exact named existing-mode matrix | `36 passed in 6.93s` |
| Explicit Python 3.12 real-Kiwi smoke | CPython `3.12.13`; `1 passed, 23 deselected in 2.23s` |
| Dependency lock | `Resolved 200 packages in 1ms` from `uv lock --check` |
| Full suite | `1168 passed, 17 warnings in 255.27s (0:04:15)` |
| Homograph/private-highlight second pass | `2 passed, 2 deselected in 7.65s` |
| Canonical allowlist/job-policy second pass | `2 passed, 6 deselected in 0.81s` |
| Python compilation of both Plan 30-08 test files | Exit 0 with no output |
| Exporter/template/Japanese no-touch status and scoped whitespace check | Exit 0 with no output |
| Session fingerprint | `9a49229ec074882cfc638b1da2759a8b453cb9336010ff210986aa9f4f51e344` |

The focused warnings were the 10 known Alembic `path_separator` deprecations from migration parity. The full suite added five instances of that same warning from export-repository tests, one third-party `dateparser` `utcnow()` deprecation, and one third-party `jsonlines` invalid-escape syntax warning. No test failed and no warning was caused by Plan 30-08.

The Python 3.12 smoke used an isolated temporary `UV_PROJECT_ENVIRONMENT` with `UV_OFFLINE=1`, resolved all 196 environment packages from local cache, and made no live provider call. All integration evidence used local temporary files/SQLite, reviewed synthetic lexical records, deterministic provider-boundary fakes, and a forbidden audio adapter.

## High-Leverage Second Pass

### POS homograph trace

1. The NFD word-list fixture submits `배우가` after `공부해요` and preserves input order plus submitted form.
2. The reviewed local source record resolves `배우` specifically as the noun/actor sense; real Kiwi persists POS `NNG` in `KoreanLexicalIdentity`.
3. After commit, expiration, and reload, `그 배우가 오늘 새 영화를 촬영해요.` matches that noun identity.
4. `저는 학교에서 매일 한국어를 배워요.` contains the predicate “to learn,” not the noun/actor sense; direct matching returns `mismatch`.
5. Passing the same reloaded noun identity through `TextValidationService` produces validation status `failed`, proving no surface-substring or suffix fallback accepts the homograph.

### Private highlight trace

1. A temporary private Kindle file contains `눈은 매일 공부해요` and is ingested through the real highlight route.
2. Real extraction retains the valid one-syllable noun surface `눈은` and the compound predicate surface `공부해요`; persisted identities resolve to `눈` and `공부하다`.
3. The compound signature remains ordered as `공부/NNG`, `하/XSV` after reload.
4. The private repository retains one normalized-text record but has no source-path attribute.
5. Public candidate rows/manifests contain hashed source identity and canonical lexical data; serialized inspection finds no raw excerpt, temporary path/name, context, normalized-text key, source-path key, or token dump.
6. Representative generic rows retain their existing source-specific fields, blank `Image`, and one exact `ko` tag; `ko-KR` never appears in tags.

### Canonical and no-touch review

- The scanner traverses every Python file under production `src` and `scripts` roots.
- Its allowlist is exactly one tuple: `src/multilang/domain/korean.py` plus `KOREAN_PROVIDER_LOCALE: Final = "ko-KR"`.
- No aliases, internal job/run/cache/path/tag identities, Korean frequency asset, Korean voice, or Korean Tatoeba call are allowed.
- Scoped status checks found no Plan 30-08 modification to APKG/tabular exporters, card-template loading, Japanese furigana, templates, or snapshots.
- Focused and full suites were both run after the final tests and second-pass assertions were complete.

## Files Created/Modified

### Created

- `tests/integration/test_korean_modern_flow.py` - real-runtime three-mode, persistence/reload, strict matching, privacy, and generic artifact evidence.
- `.planning/phases/30-korean-contracts-and-morphology/30-08-SUMMARY.md` - TDD, regression, security, and bounded handoff evidence.

### Modified

- `tests/services/test_korean_language_support.py` - narrow production `ko-KR` scanner plus three-mode canonical policy/run-key/tag checks.
- `.planning/SPEC.md` - Current State advanced through Plan 30-08 while Phase 30 and all four requirements remain open for verification.
- `.planning/.state-fingerprint.json` - reviewed planning-state fingerprint rewritten after the SPEC-only handoff.

No production source file, migration, dependency file, lockfile, Korean asset/voice, exporter, template, UI, or Japanese snapshot was modified by Plan 30-08.

## Git Actions

None. Per explicit user instruction and the carried Phase 30 execution convention, no file was staged or committed, and no branch, push, PR, amend, reset, stash, clean, checkout, restore, tag, or other delivery/destructive action was performed.

## Decisions Made

- Integration fakes stop at external sentence, translation, and audio seams. Runtime composition, repositories, SQLite lifecycle, ingestion, identity validation, matcher behavior, note construction, and Kiwi remain real.
- Core lexical identity equality intentionally excludes submitted surface form because frequency, word-list, and highlight surfaces differ while canonical lemma/POS/sense/signature/fingerprint must agree.
- Homograph evidence uses source-backed noun sense authority and treats the related predicate surface as a strict mismatch rather than inferring a shared lemma from spelling.
- Privacy evidence distinguishes the encrypted/private repository from public candidates/manifests instead of pretending all local storage must omit source text.
- Existing generic note construction is sufficient for Phase 30 compatibility evidence; final Korean note types, APKG/import integrity, media, and visual review remain later-phase work.
- Phase 30 remains open until verification. Execution does not complete the phase or its requirements.

## Deviations from Plan

None - the plan was completed within its test-only production boundary. No missing production wiring was hidden with a fake, and no exporter, template, Japanese snapshot, asset, voice, provider, schema, or UI scope was added.

## Issues Encountered

- Real Kiwi correctly rejected the first ambiguous synthetic `물`/`학교` fixture. Analyzer diagnostics showed that production was behaving fail-closed, so only the reviewed test sentence was changed to the stable `눈은 매일 공부해요` case.
- A direct `uv run --python 3.12` environment replacement initially failed because VS Code formatter/linter processes held `.venv/Scripts` files open on Windows. The interrupted replacement also removed pytest from that environment; `uv sync --extra dev` restored it. The required smoke then passed in a separate temporary Python 3.12 environment, leaving the project environment and lock contract intact.

## Security and Privacy Review

- Raw highlight text enters only the local private import boundary and real in-process morphology service; no HTTP, provider, TTS, upload, or production-database operation occurs.
- The public manifest/candidate serialization check rejects the exact excerpt, full path, file name, context key, raw-normalized-text key, source-path key, and token-dump key.
- Public source identifiers are fixed-length hashes; canonical identity fields are retained only because they are required for deterministic local matching and review.
- The audio adapter raises on voice discovery or synthesis, proving the integration cannot silently query or synthesize Korean audio.
- Tatoeba is disabled and separately asserted to return before invoking a candidate provider for Korean.
- No new endpoint, authentication path, file-access behavior, schema boundary, network route, or production threat surface outside the plan threat register was introduced.

## Known Stubs

None. Empty collections, blank `Image`, deterministic adapters, temporary source fixtures, and forbidden-audio sentinels are assertions or bounded test evidence rather than runtime stubs. They do not prevent the Phase 30 contract/morphology objective.

## User Setup Required

None. This plan needs no provider credential, network access, Korean voice, production asset, production database, export application, or visual review.

## State and Handoff

- `.planning/SPEC.md` records Plans 30-01 through 30-08 implemented while Phase 30 remains in progress pending verification.
- `.planning/ROADMAP.md` was not changed by Plan 30-08 and remains open at `[-]`.
- `KMODE-01`, `KMODE-02`, `KNLP-01`, and `KNLP-02` remain advanced but unchecked; verification owns requirement and phase closure.
- The Korean frequency source, attribution, and redistribution decision remains the active later-phase blocker; no `assets/frequency/ko` path exists.
- The reviewed session fingerprint is `9a49229ec074882cfc638b1da2759a8b453cb9336010ff210986aa9f4f51e344`.
- Next action is Phase 30 verification against the bounded contract/morphology claim. Do not infer learner-content quality, audio approval, template/APKG readiness, visual acceptance, or milestone completion from this plan.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Strict RED/GREEN cycles, both exact task commands, the exact focused and named matrices, explicit Python 3.12 real-Kiwi smoke, lock check, 1,168-test full suite, homograph/private second pass, canonical allowlist review, compilation, privacy scan, and no-touch checks all passed offline.
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
  summary: Real Kiwi exposed ambiguity in the first synthetic 물/학교 highlight fixture; replacing only that fixture with consensus-stable 눈/공부 evidence preserved strict production behavior and completed the intended trace.
- class: environment_constraint
  impact: recoverable
  disposition: proceeded
  summary: Windows editor language-server processes locked the project virtual environment during direct Python 3.12 selection; restoring the dev environment and using an isolated offline Python 3.12 environment completed the exact smoke without repository or lock changes.
</deltas>

<judgment>
<active_constraints>
Keep `ko` as the sole internal/public Korean identity and `ko-KR` only as the explicit provider locale constant. Preserve NFC values, source-backed lemma/POS/sense, ordered same-eojeol signatures, exact analyzer fingerprints, top-two consensus, commit/expire/reload durability, and fail-closed matching. Raw highlight excerpts and paths remain private. Do not add a Korean frequency asset, voice, live provider call, note type, template, or final export claim without the owning later-phase approval and evidence.
</active_constraints>
<unresolved_uncertainty>
No approved production Korean lexical/frequency source or redistribution decision exists. Phase 30 proves contracts and morphology only; Korean sentence naturalness/register/Portuguese quality, approved Azure audio, curricula, final note/template topology, APKG/import/media integrity, and Desktop/mobile visual acceptance remain Phases 31-34.
</unresolved_uncertainty>
<decision_posture>
Prefer persisted source identity and a review-required false negative over guessing a lemma, sense, POS, signature, or locale alias. Treat generic field/tag evidence as compatibility, not learner-ready export proof. Phase verification, not execution, decides whether Phase 30 requirements close.
</decision_posture>
<anti_regression>
Do not broaden the `ko-KR` allowlist, bypass reload with in-memory assertions, replace real Kiwi positives with mocked morphology, leak private excerpts or paths into public/provider-visible artifacts, add Korean Tatoeba/audio fallbacks, or alter existing exporter/template/Japanese/modern/Mandarin/Latin/phoneme behavior to satisfy Korean closure.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All five execution-owned files exist, including both test artifacts, this summary, the SPEC handoff, and the reviewed planning-state fingerprint.
- Every exact plan verification passed after the tests were final: Task 1 `4 passed`, Task 2 `8 passed`, focused Phase 30 `401 passed`, existing-mode matrix `36 passed`, Python 3.12 smoke `1 passed`, lock check resolved 200 packages, and full suite `1168 passed`.
- The focused homograph/private and canonical-policy selections, Python compilation, scoped whitespace check, and exporter/template/Japanese no-touch check all passed.
- Phase 30 remains open at `[-]`; `KMODE-01`, `KMODE-02`, `KNLP-01`, and `KNLP-02` remain unchecked; no Phase 31 or milestone claim was made.
- Required structured sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) are present and substantive.
- Planning-state drift is clean, the reviewed fingerprint matches `9a49229ec074882cfc638b1da2759a8b453cb9336010ff210986aa9f4f51e344`, and the Phase 30 verification preflight is allowed.
- The staging area is empty. No commit check applies because all Git delivery actions were explicitly prohibited.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 08*
*Completed: 2026-08-04*
