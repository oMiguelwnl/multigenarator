---
phase: 30-korean-contracts-and-morphology
plan: "03"
subsystem: lexical-contracts-and-persistence
runtime: opencode
assurance: self_checked
tags: [korean, unicode-nfc, pydantic, sqlalchemy, alembic, json, tdd]
requires:
  - 30-01
  - 30-02
provides:
  - Optional validated Korean lexical identity on shared candidates
  - Source-backed multi-sense lookup and deterministic source inventory
  - NFC-stable word-list item, fingerprint, and run keys
  - Nullable typed Korean identity persistence at Alembic revision 20260804_17
affects: [30-04, 30-05, 30-06, 30-07, 30-08]
tech-stack:
  added: []
  patterns:
    - Pydantic model_dump/model_validate at the JSON persistence boundary
    - NFC before lookup, dedupe, fingerprint, and run-key derivation
    - Linear additive Alembic migration with no default or backfill
key-files:
  created:
    - alembic/versions/20260804_17_korean_lexical_identity.py
    - tests/services/test_input_fingerprint.py
  modified:
    - src/multilang/domain/lexicon.py
    - src/multilang/services/lexical_lookup.py
    - src/multilang/services/word_list_parser.py
    - src/multilang/services/input_fingerprint.py
    - src/multilang/db/models.py
    - src/multilang/repositories/lexical_repository.py
    - tests/domain/test_lexicon.py
    - tests/services/test_lexical_lookup.py
    - tests/services/test_word_list_parser.py
    - tests/repositories/test_lexical_repository.py
    - tests/test_migration_schema_parity.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Legacy lookup returns the first declared record, while lookup_candidates and iter_candidates expose every source-backed sense without selecting one."
  - "Korean source records must provide POS and source-backed sense_id; incomplete Korean source records fail closed."
  - "The Korean migration is revision 20260804_17 directly after accepted sole head 20260804_16, with one nullable JSON column and no backfill."
  - "Persisted Korean identity is serialized and restored only through its Pydantic contract; Kiwi is not rerun during reload."
patterns-established:
  - "Canonical ingress: preserve submitted text, derive NFC display and stable keys."
  - "Durable evidence: validate candidate identity agreement before parameterized ORM persistence."
requirements-advanced: [KMODE-01, KMODE-02, KNLP-01, KNLP-02]
requirements-completed: []
duration: 13m00s
completed: 2026-08-04
---

# Phase 30: Korean Contracts and Morphology - Plan 03 Summary

**Source-backed Korean senses, NFC-stable input identity, and one nullable typed JSON field now preserve complete analyzer evidence across commit, expiration, and reload without reanalysis.**

## Performance

- **Resumed execution duration:** 13m00s
- **Resumed execution started:** 2026-08-04T18:04:07Z
- **Completed checks:** 2026-08-04T18:17:07Z
- **Tasks:** 3/3
- **Execution-owned files created/modified:** 16, including this summary
- **Assurance:** `self_checked` (same-runtime execution, focused tests, migration lifecycle, and high-leverage second pass)

## Accomplishments

- Added optional `KoreanLexicalIdentity` evidence to shared lexical candidates with strict lemma and lexical-key agreement while preserving every existing constructor.
- Added Portuguese definition/translation policy for Korean plus explicit ordered multi-sense lookup and deterministic source-record enumeration without silent sense selection.
- Converged NFC/NFD equivalents before lexical, word-list, fingerprint, and run-key derivation while retaining exact submitted form, first line, and order.
- Added one nullable `lexical_candidates.korean_identity` JSON column and exact Pydantic serialization/restoration through a real commit/expire/reload lifecycle.
- Proved migration upgrade, legacy-row `NULL`, downgrade, re-upgrade, ORM parity, and the linear `20260720_15 -> 20260804_16 -> 20260804_17` topology.

## TDD Task Evidence

### Task 30-03-01: Extend shared lexical candidates and source lookup for Korean identity

- **RED:** `uv run pytest tests/domain/test_lexicon.py tests/services/test_lexical_lookup.py -q` produced **9 failed, 4 passed in 0.27s**. Failures covered missing typed identity, mismatch validation, Korean Portuguese policy, NFC lookup normalization, candidate enumeration, and legacy-compatible APIs.
- **GREEN:** The minimal candidate and lookup implementation produced **13 passed in 0.10s**.
- **REFACTOR:** Replaced post-init mutation with a Pydantic field validator for NFC source records; **13 passed in 0.09s**.
- **Final:** The exact task command produced **13 passed in 0.11s**.

### Task 30-03-02: Make word-list and run-key boundaries NFC-stable

- **RED:** `uv run pytest tests/services/test_word_list_parser.py tests/services/test_input_fingerprint.py -q` produced **2 failed, 8 passed in 0.25s** on NFD/NFC duplicate and fingerprint divergence.
- **GREEN:** NFC-before-key derivation and NFC display assembly produced **10 passed in 0.08s**.
- **REFACTOR:** No structural refactor was needed; the change retained the existing whitespace/case behavior.
- **Final:** The exact task command produced **10 passed in 0.09s**.

### Task 30-03-03: Persist typed Korean identity through Alembic and repository reload

- **Pre-migration gate:** `ScriptDirectory.get_heads()` printed **`['20260804_16']`** and passed the revised exact-head assertion before the migration file was written.
- **RED:** `uv run pytest tests/repositories/test_lexical_repository.py tests/test_migration_schema_parity.py -q` produced **4 failed, 12 passed, 6 warnings in 1.76s**. Failures showed the absent ORM field, absent revision, and missing reload evidence.
- **GREEN:** The ORM, repository, and additive migration produced **16 passed, 10 warnings in 1.89s**.
- **REFACTOR/second pass:** A review-found test-helper placement error was corrected; the complete command remained green at **16 passed, 10 warnings in 1.83s**.
- **Final:** The exact task command produced **16 passed, 10 warnings in 2.31s**.
- **Final head assertion:** `ScriptDirectory.get_heads()` printed **`['20260804_17']`**.

## Final Verification Results

| Check | Exact result |
|---|---|
| Domain and lexical lookup | `13 passed in 0.11s` |
| Word-list and input fingerprint | `10 passed in 0.09s` |
| Repository and migration parity/lifecycle | `16 passed, 10 warnings in 2.31s` |
| Plan 30-02 Korean domain/morphology anti-regression | `45 passed in 26.10s` |
| Affected fingerprint/grounding/Polish/highlight/job callers | `38 passed, 5 warnings in 31.29s` |
| Final Alembic head | `['20260804_17']` |
| Python compilation | Exit 0 with no output |
| ORM column inspection | `korean_identity JSON True None None` |
| Migration scope scan | `card_exports=False`, `execute=False`, `update=False`, `sa.Column count=1` |
| Patch whitespace check | Exit 0; only pre-existing Windows LF-to-CRLF notices |

The ten migration-suite warnings are the pre-existing Alembic `path_separator` deprecation warning. Supplemental warnings came from existing third-party Jieba, Dateparser, and Jsonlines code. No provider or network call ran.

## Migration Topology Evidence

The original execution correctly stopped when the then-plan expected `20260720_15` but discovered the tracked Japanese revision as sole head:

```text
['20260804_16']
AssertionError: ['20260804_16']
```

The revised, rechecked plan accepted that recoverable discovery. Pre-create topology was exactly one head, `20260804_16`. Final history is linear:

```text
20260804_17 (head) -> parent 20260804_16
20260804_16        -> parent 20260720_15
```

The Japanese migration remained byte-identical before and after execution:

```text
3950c55a61d0744dfb04a5f370c254a848cc81678854a07bcd1d43e277338409
```

`git diff -- alembic/versions/20260804_16_japanese_romaji_fields.py` produced no output. Neither that file nor `card_exports` was modified.

## Files Created/Modified

### Created

- `alembic/versions/20260804_17_korean_lexical_identity.py` - One nullable JSON column, parent `20260804_16`, and symmetric single-column downgrade.
- `tests/services/test_input_fingerprint.py` - NFC-equivalent Korean and legacy fingerprint/run-key evidence.
- `.planning/phases/30-korean-contracts-and-morphology/30-03-SUMMARY.md` - Execution, topology, TDD, security, and handoff evidence.

### Modified

- `src/multilang/domain/lexicon.py` - Optional typed identity, mismatch validation, and Korean Portuguese policy.
- `src/multilang/services/lexical_lookup.py` - NFC keys, optional sense/register fields, multi-record lookup, deterministic inventory, and complete-alias deduplication.
- `src/multilang/services/word_list_parser.py` - Exact submitted-form retention with NFC display/item identity.
- `src/multilang/services/input_fingerprint.py` - NFC before existing requested-key normalization.
- `src/multilang/db/models.py` - Nullable `korean_identity` JSON ORM column.
- `src/multilang/repositories/lexical_repository.py` - Pydantic JSON serialization/restoration without reanalysis.
- `tests/domain/test_lexicon.py` - Typed candidate mismatch/round-trip and Portuguese policy evidence.
- `tests/services/test_lexical_lookup.py` - Homograph senses, deterministic inventory, aliases, Korean sense gate, and legacy behavior.
- `tests/services/test_word_list_parser.py` - NFC/NFD dedupe with submitted form, line, order, and warning preservation.
- `tests/repositories/test_lexical_repository.py` - Exact commit/expire/reload and legacy `NULL` lifecycle evidence.
- `tests/test_migration_schema_parity.py` - Sole-head, nullable JSON, legacy no-backfill, downgrade/re-upgrade, and parity evidence.
- `.planning/SPEC.md` - Current State advanced through Plan 30-03 without closing Phase 30.
- `.planning/.state-fingerprint.json` - Reviewed planning state rebaselined after the SPEC update.

## Git Actions

None. Per explicit user instruction, this execution did not stage, commit, push, create a branch/PR, amend, reset, stash, clean, or otherwise perform delivery actions.

## Decisions Made

- `lookup()` remains legacy-compatible by returning the first declared source record; new callers use `lookup_candidates()` or `iter_candidates()` when ambiguity must remain explicit.
- Inventory deduplication occurs only for complete aliases sharing NFC lemma, source POS, source-backed sense ID, register, and source. Distinct POS, sense, or register records remain separate.
- NFC is safe at these shared key boundaries; submitted evidence is never overwritten, and NFKC is not introduced.
- Persistence contains only the validated project identity and complete analyzer fingerprint. Repository restoration never parses prose or reruns Kiwi.
- The accepted migration parent is `20260804_16`; no merge revision, branch, default, backfill, index, or export-table change is needed.

## Deviations from Plan

### Accepted Factual Discovery

**1. Initial Alembic checkpoint and linear topology rebase**
- **Found during:** Original Plan 30-03 migration preflight.
- **Issue:** The original plan expected sole head `20260720_15`, while the live tracked graph had sole head `20260804_16` for the separately owned Japanese snapshot migration.
- **Response:** Execution stopped before mutation. After explicit user acceptance and a fresh plan recheck, the Korean revision moved linearly to `20260804_17` with `down_revision = "20260804_16"`.
- **Boundary proof:** The Japanese file hash remained unchanged and `card_exports` was untouched.
- **Classification:** Recoverable `factual_discovery`; no architecture or scope change.

### Auto-fixed Issues

**2. [Rule 1 - Test bug] Restored a displaced frequency-duplicate regression body**
- **Found during:** Task 30-03-03 high-leverage diff review.
- **Issue:** Initial helper insertion accidentally placed `make_korean_candidate()` inside an existing test boundary, leaving the duplicate assertions unreachable even though the suite was green.
- **Fix:** Moved the helper beside the other factories and restored the original test body before accepting final results.
- **Files modified:** `tests/repositories/test_lexical_repository.py`.
- **Verification:** The complete repository/migration command returned `16 passed, 10 warnings in 1.83s`, then finalized at `16 passed, 10 warnings in 2.31s`.
- **Commit:** None by user instruction.

**Total deviations:** One accepted recoverable topology discovery and one Rule 1 test fix. No product scope, schema intent, or excluded surface changed.

## Issues Encountered

- The first execution stopped exactly at the old topology gate; no tests or production files were changed during that attempt.
- Alembic emits its existing missing-`path_separator` deprecation warning during migration tests. It is unrelated to this plan and was not changed.

## Security and Database Review

- All repository predicates and writes continue through SQLAlchemy expressions; no interpolated SQL was added.
- JSON enters persistence only from `KoreanLexicalIdentity.model_dump(mode="json")` and is restored only through `KoreanLexicalIdentity.model_validate`.
- The migration adds exactly one lowercase snake-case JSON column with `nullable=True`, no client/server default, no data update, and no backfill.
- The migration lifecycle proves a pre-existing row receives `NULL`, survives downgrade/re-upgrade, and remains compatible.
- No raw Kiwi token/vendor object, highlight excerpt, local path, prompt, traceback, production sense data, secret, or provider payload was added to identity JSON or provenance.
- No endpoint, auth path, network call, production corpus, or unplanned trust boundary was introduced.

## Known Stubs

None. No TODO/FIXME/HACK/XXX, rendering placeholder, empty UI data source, or incomplete implementation blocks this plan's scoped goal.

## State and Handoff

- `.planning/SPEC.md` records Plans 30-01 through 30-03 complete while Phase 30 remains in progress.
- `.planning/ROADMAP.md` remains open at `[-]` and was not modified by this execution.
- No requirement checkbox was closed; all four Phase 30 requirements still require later plans and phase verification.
- `node .planning/bin/gsdd.mjs session-fingerprint write` completed with fingerprint `3e9e8501296e83d4e258c226cf5f9af846b9ab147fd5e8c2d8b81f894c37d597`.
- Plan 30-04 can consume deterministic source records and durable `KoreanLexicalIdentity` without allowing Kiwi to author sense IDs.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All three RED/GREEN cycles, exact task commands, migration topology/lifecycle/parity, affected callers, Plan 30-02 anti-regressions, compilation, privacy/schema scans, and the high-leverage second pass passed. Warnings are pre-existing tool/dependency warnings.
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
  disposition: escalated
  summary: The original migration gate expected 20260720_15 but found sole tracked head 20260804_16, so execution stopped before mutation and returned a checkpoint.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The revised and rechecked plan accepted the linear Japanese head and created only Korean revision 20260804_17 with parent 20260804_16, leaving the Japanese migration and card_exports untouched.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: High-leverage review found and corrected an execution-introduced test-helper placement error before final verification.
</deltas>

<judgment>
<active_constraints>
Keep `ko` as the sole product identity and `ko-KR` provider-only. Preserve exact submitted evidence while deriving NFC stable values. Korean source records need explicit source-backed POS/sense data. Persist only validated project identity/fingerprint in the nullable JSON field. Do not touch the Japanese migration, `card_exports`, `ExportRepository`, voice/Tatoeba policy, or production frequency assets.
</active_constraints>
<unresolved_uncertainty>
No approved production Korean lexical source or sense mapping exists, so only reviewed synthetic fixture IDs prove this contract. Source intersection, all three source-mode resolution paths, provider/cache wiring, and accepted generated-card validation remain for later Phase 30 plans.
</unresolved_uncertainty>
<decision_posture>
Preserve ambiguity rather than selecting the first source sense. Treat typed persisted identity as authoritative across resume/reload, and prefer additive nullable schema evolution over backfill or inferred historical identity.
</decision_posture>
<anti_regression>
Existing non-Korean candidates/indexes remain valid without sense or Korean identity. Legacy lookup, word-list order/warnings, run-key behavior, repository duplicates/counts, and existing migration parity must remain green. The Alembic graph must stay a single linear head after `20260804_17`; no later plan may retrofit this evidence through prose, reanalysis, or export-only columns.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All 16 execution-owned files exist, including the required summary.
- Every exact task verification and supplemental anti-regression command passed with the results recorded above.
- Alembic reports sole head `20260804_17` with parent `20260804_16`.
- The Japanese migration and excluded export repository have no execution diff; the staging area is empty.
- Lifecycle preflight reports planning state `clean`; Phase 30 remains open/in progress and no later plan or requirement was closed.
- Required structured sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) are present and substantive.
- No commit check applies because all git delivery actions were explicitly prohibited.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 03*
*Completed: 2026-08-04*
