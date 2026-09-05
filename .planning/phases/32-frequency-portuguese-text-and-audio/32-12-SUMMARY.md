---
phase: 32-frequency-portuguese-text-and-audio
plan: "12"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 12 Summary

**Completed**: 2026-08-30
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: None blocking. Work stayed inside the declared source/test write-set plus required GSDD state artifacts and did not perform network, provider, Azure, production DB, release, publication, or Git actions.
**Decisions Made**: Korean frequency final export is explicitly evidence-bound: every final row needs persisted rank/level, one bundle hash, accepted text review receipt, reviewed non-fallback word and sentence audio artifact hashes, and a row export-gate receipt. Korean APKG packaging routes by `frequency_level` only, never rank or item-key arithmetic.
**Notes for Verification**: This proves synthetic/offline export eligibility, APKG topology, archive inspection, rollback, and exact report wiring. It does not prove real Korean 3000-entry content, live Azure/provider output, human/AI review validity beyond persisted hashes, production DB execution, observed Anki import/render/playback, or final Phase 34 closure.
**Notes for Next Work**: The explicit command is `export-korean-frequency-apkg --database DB --job-id ID --binding-receipt FILE --bundle-root ROOT --manifest-file FILE --output FILE --generation-report-json FILE --generation-report-markdown FILE --cards-per-level 1000 --expected-items 3000 --expected-word-assets 3000 --expected-sentence-assets 3000 --no-partial`. Real use still needs exact upstream authorities and evidence files.

## Eligibility Matrix

| Gate | Behavior |
|---|---|
| Source rows | Korean final frequency rows require `SupportedLanguage.KO`, `source_type=frequency`, one immutable `frequency_bundle_sha256`, unique rank/GUID/lemma key, explicit `frequency_level`, and exact level counts. |
| Text evidence | Assembly requires accepted/passed text with `text_review_receipt_sha256` and adaptive evidence bound to the same frequency bundle. |
| Audio evidence | Word and sentence assets must be synthesized, reviewed approved, non-fallback, artifact-hashed, request-hash aligned, and exact-text matched before row creation. |
| Learner identity | Field order, blank `Image`, note GUID input, tags, and learner-facing field values remain unchanged; internal hashes are not exported as card columns. |
| Partial handling | Korean final validation ignores partial allowance and fails closed on incomplete rows or inferred levels. |

## Package Audit

| Surface | Result |
|---|---|
| Model | Korean frequency uses the registered `korean_frequency/model` ID with the existing `Multilang::Card` schema. |
| Deck topology | One registered parent plus registered `Level 1`, `Level 2`, and `Level 3` child decks are created in one APKG. |
| Routing | Cards route by persisted `row.frequency_level` only. Unknown, missing, or inferred levels fail before destination replacement. |
| Inspection | Staged APKGs are reopened and checked for deck/model IDs, fields, note GUIDs, card routing, card count, and media manifest before atomic replacement. |
| Rollback | Invalid Korean package validation preserves existing destination bytes and removes owned temp output. |

## Report Contract

| Report Area | Privacy-Safe Content |
|---|---|
| Export binding | APKG SHA-256, bundle hash, manifest hash, binding receipt hash, expected/card counts, and level counts. |
| Evidence counts | Text review totals, adaptive history counts, lexical duplicate/rejection counts, 3000/3000-style audio expected/approved counts, fallback count, and artifact hash count. |
| Provider telemetry | Sanitized provider/operation/status summaries plus retry, cache-key, token, cost, and latency denominators. |
| Exclusions | No learner text, prompts, provider payloads, credentials, review notes, media paths, or private filesystem paths. |

## TDD Evidence

- Task 32-12-01 RED: after fixing an accidental test-helper return regression, Korean assembly tests failed on missing explicit final rank/evidence checks (`4 failed`) and tabular tests failed because `cards_per_level`/`expected_items` validation was missing (`2 failed`).
- Task 32-12-01 GREEN: assembly and tabular focused checks passed `12 passed, 20 deselected` and `6 passed, 10 deselected`.
- Task 32-12-02 RED: Korean APKG tests failed because `export_anki_package` had no `cards_per_level`/`expected_items` Korean topology support (`2 failed`).
- Task 32-12-02 GREEN: APKG focused checks passed `10 passed, 22 deselected`.
- Task 32-12-03 RED: report tests failed on missing `build_korean_frequency_export_evidence`, and CLI tests failed because `export-korean-frequency-apkg` did not exist (`1 failed`; `2 failed`).
- Task 32-12-03 GREEN: report and CLI focused checks passed `1 passed, 1 deselected` and `4 passed, 4 deselected`.

## Verification

- Task 32-12-01 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_assemble_export_cards.py -k 'korean or guid or field or level or audio or partial' -q` -> `12 passed, 20 deselected`.
- Task 32-12-01 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_export_tabular_bundle.py -k 'korean or field or level' -q` -> `6 passed, 10 deselected`.
- Task 32-12-02 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_export_anki_package.py -k 'korean or parent or child or atomic or guid or media' -q` -> `10 passed, 22 deselected`.
- Task 32-12-03 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_generation_report.py -k 'korean or denominator or privacy or exact_apkg' -q` -> `1 passed, 1 deselected`.
- Task 32-12-03 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_export_command.py -k 'korean_frequency or explicit_database or generation_report or no_partial or registry or output' -q` -> `4 passed, 4 deselected`.
- Required command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync multilang check-anki-id-registry --production-roots` -> `anki_id_registry_status=clean`, `scanned_files=202`, `issue_count=0`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/test_runtime.py -q` -> `15 passed`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_export_command.py -q` -> `8 passed`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_generation_report.py -q` -> `2 passed`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_export_tabular_bundle.py -q` -> `16 passed`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_assemble_export_cards.py -q` -> `32 passed`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_export_anki_package.py -q` -> `32 passed`.
- Whitespace check passed: `git diff --check -- tests/services/test_assemble_export_cards.py tests/services/test_export_tabular_bundle.py tests/services/test_export_anki_package.py tests/services/test_generation_report.py tests/cli/test_export_command.py src/multilang/domain/exporting.py src/multilang/services/assemble_export_cards.py src/multilang/services/export_tabular_bundle.py src/multilang/services/export_anki_package.py src/multilang/services/generation_report.py src/multilang/runtime.py src/multilang/cli.py`.
- Planning state update: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` -> unchanged/open; `node .planning/bin/gsdd.mjs session-fingerprint write` -> `129e09e9d3747adb970621f93fe89c37ff18b316f1082d121330fb04387d474d`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified exact Korean final row eligibility, non-partial tabular prewrite validation, registered parent/three-child APKG packaging, staged archive inspection, rollback preservation, explicit-database CLI wiring, privacy-safe exact report payloads, existing modified export surfaces, and production-root Anki ID registry cleanliness. No network, provider, Azure, production DB, real Korean export output, observed Anki import/playback, Git, release, or publication action was performed.
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
  summary: Direct export-only runtime construction would otherwise require default live text/translation credentials; the exact Korean export command builds the runtime with local text/translation providers because it only reads persisted evidence and writes export artifacts.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Adding the APKG-level prewrite registry guard makes package tests slower because each direct package export scans production roots; verification completed with extended timeouts and the guard remained clean.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and phase verification is pending. Plan 32-12 authorizes only synthetic/offline eligibility, APKG packaging, report, CLI, and runtime wiring. Network, provider, Azure, production DB, real review approval, source transformation, 3000-entry asset use, full-suite closure, export release, Git, and publication effects still require exact later authorities.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot output, NIKL rights/source facts, real transformed 3000-entry inventory, source review, provider model/budget, live Azure catalog/synthesis, heard review outputs, production DB authority, final full-suite evidence, Anki import/playback proof, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Korean frequency final output is fail-closed and evidence-first: persisted manifest level, exact bundle/text/audio hashes, registered deck IDs, staged archive inspection, and one canonical report evidence object are required before output replacement. Existing language/export modes keep their schema and GUID behavior; Korean-specific final strictness is isolated to `ko` frequency rows.
</decision_posture>
<anti_regression>
Do not reintroduce rank/item-key arithmetic for Korean frequency level routing; do not export internal Korean evidence hashes as learner fields; do not weaken reviewed non-fallback word/sentence audio requirements; do not allow `--allow-partial` or missing `--no-partial` to produce Korean final output; do not bypass staged APKG inspection before replacement; do not remove registered Korean frequency parent/Level 1/Level 2/Level 3 IDs; do not include learner text, prompts, payloads, credentials, review notes, media paths, or private paths in Korean exact generation reports.
</anti_regression>
</judgment>
