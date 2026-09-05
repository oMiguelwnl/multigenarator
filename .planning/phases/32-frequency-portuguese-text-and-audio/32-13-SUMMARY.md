---
phase: 32-frequency-portuguese-text-and-audio
plan: "13"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 13 Summary

**Completed**: 2026-08-31
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: None blocking. The required existing frequency/custom E2E command was run as separate commands after the chained command exceeded its aggregate timeout; both final-state regressions passed.
**Decisions Made**: Synthetic Korean smoke and exact-scale gates now carry explicit non-production claim limits. Provider/catalog pilot validation is read-only, DB-row-derived, input-invariance-checked, and cannot grant route, voice-profile, synthesis, review, release, or publication authority.
**Notes for Verification**: This plan proves representative APKG wiring, exact synthetic 3000-card/6000-media package structure, and fake provider/catalog reconciliation. It does not prove real Korean content, NIKL rights, live provider calls, Azure catalog capture, synthesis, heard review, production DB execution, observed Anki import/playback, or publication readiness.
**Notes for Next Work**: Continue only offline/autonomous Phase 32 lanes until exact Phase 31 active output plus source/license/provider/Azure/DB authorities exist. Treat the provider/catalog pilot evidence output as supplemental machine evidence, not authorization.

## Deliverables

| Surface | Result |
|---|---|
| Fast APKG smoke | Added `tests/integration/test_korean_frequency_apkg_smoke.py` with two synthetic notes per level, twelve media files, parent/Level 1/2/3 routing inspection, model/field/GUID/tag/media checks, and sentinel rollback on evidence mutation. |
| Synthetic scale contract | Added runtime count/manifest descriptors that distinguish `fast-representative-only` from `synthetic-exact-scale-only` and never claim production-count evidence. |
| Slow exact-scale gate | Added `tests/integration/test_korean_frequency_text_audio_flow.py::test_slow_exact_3000_cards_6000_assets_parent_three_children`, which writes and reopens a synthetic 3000-card/6000-media APKG and verifies 1000 cards in each child deck. |
| Provider/catalog pilot | Added `src/multilang/services/korean_provider_pilot_evidence.py` and CLI command `validate-korean-provider-catalog-pilot-result` for read-only reconciliation of Phase 31 hashes, text/catalog result files, protected input hashes, and provider-call telemetry rows. |

## Pilot Reconciliation Matrix

| Gate | Behavior |
|---|---|
| Phase 31 | Re-runs active snapshot provenance verification and fails on receipt, manifest, or root drift. |
| Authority | Requires binding receipt to match source-review aggregate, plus explicit source/build/final/provider/pilot/catalog hashes. |
| Inputs | Hashes every protected input file before and after validation; output path must be distinct from protected inputs. |
| DB rows | Reads provider-call rows for the explicit job only; wrong-job rows, missing telemetry hashes, synthesis operations, fallback attempts, and forbidden fallback providers fail closed. |
| Denominators | Derives call counts, provider-attempt counts, retry attempts, cache hits, latency totals, token denominator gaps, cost denominator gaps, and provider summaries from DB rows. |
| Privacy | Evidence contains hashes/counts/sanitized summaries only; no item keys, learner text, prompts, provider payloads, credentials, file paths, or private Korean text are emitted. |
| Authority limits | Evidence sets `grants_route_authority=false` and `grants_voice_profile_authority=false`; it cannot approve catalog/profile/audio routes. |

## TDD Evidence

- Task 32-13-01 RED: new smoke test failed on missing `build_korean_frequency_synthetic_export_contract` import.
- Task 32-13-01 GREEN: minimal runtime synthetic export contract descriptor added; smoke test passed.
- Task 32-13-02 RED: exact-scale test failed on missing `build_korean_frequency_synthetic_manifest_shape` import.
- Task 32-13-02 GREEN: runtime synthetic manifest descriptor added; fast contract test, legacy frequency/custom E2E regressions, and supplemental slow APKG gate passed.
- Task 32-13-03 RED: provider/catalog service tests failed because `multilang.services.korean_provider_pilot_evidence` did not exist; CLI tests then failed because `validate-korean-provider-catalog-pilot-result` did not exist.
- Task 32-13-03 GREEN: service and CLI command added; full provider/catalog focused slice passed.

## Verification

- Task 32-13-01 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_korean_frequency_apkg_smoke.py::test_fast_three_level_apkg_smoke_does_not_claim_exact_counts -q` -> `1 passed`.
- Task 32-13-02 fast command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_korean_frequency_text_audio_flow.py::test_exact_scale_contract_builds_expected_manifest_shape_without_export -q` -> `1 passed`.
- Task 32-13-02 legacy regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_frequency_e2e_export_flow.py::test_frequency_sample_generates_audio_and_exports_all_formats -q` -> `1 passed in 499.33s`.
- Task 32-13-02 legacy regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_custom_word_list_e2e_export_flow.py::test_custom_word_list_generates_audio_and_exports_all_formats -q` -> `1 passed in 311.48s`.
- Supplemental slow exact-scale gate passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_korean_frequency_text_audio_flow.py::test_slow_exact_3000_cards_6000_assets_parent_three_children -q` -> `1 passed in 41.03s`.
- Task 32-13-03 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_provider_pilot_evidence.py tests/cli/test_korean_provider_commands.py -k 'provider_catalog_result_validator or phase31 or reconcile or denominator or zero_synthesis or authority_invariance or read_only or mutation' -q` -> `7 passed, 5 deselected`.
- Final new integration smoke passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_korean_frequency_apkg_smoke.py -q` -> `1 passed`.
- Final exact-scale integration file passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_korean_frequency_text_audio_flow.py -q` -> `2 passed`.
- Final provider service file passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_provider_pilot_evidence.py -q` -> `5 passed`.
- Final provider CLI file passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_provider_commands.py -q` -> `7 passed`.
- Whitespace check passed: `git diff --check -- tests/integration/test_korean_frequency_apkg_smoke.py tests/integration/test_korean_frequency_text_audio_flow.py tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/services/test_korean_provider_pilot_evidence.py tests/cli/test_korean_provider_commands.py src/multilang/runtime.py src/multilang/services/korean_provider_pilot_evidence.py src/multilang/cli.py`.
- Planning state update: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` -> unchanged/open; `node .planning/bin/gsdd.mjs session-fingerprint write` -> `29abea17a3e80f4e84e5b7c437d220151ab80e1fb72dcf9d17ea62691bf5b640`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified fast representative APKG wiring, exact synthetic 3000/6000 package counts, existing frequency/custom export regressions, provider/catalog service validation, CLI option/output wiring, protected input invariance, zero synthesis/fallback behavior, and privacy-safe evidence output. No network, provider, Azure synthesis/catalog capture, production DB, real output, Git, release, or publication action was performed.
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
  summary: The plan's chained Task 32-13-02 verification command exceeded its aggregate timeout after the first two checks; the same frequency and custom E2E regressions passed as separate final-state commands with larger timeouts.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `pytest.mark.slow` was not registered in project configuration; the slow test keeps the marker through a local warning-suppressed binding instead of editing out-of-plan pytest config.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and phase verification is pending. Plan 32-13 authorizes only synthetic/offline scale tests and read-only provider/catalog pilot reconciliation. Network, provider, Azure catalog capture, synthesis, production DB mutation, real Korean export, release, Git, and publication effects still require exact later checkpoint authority.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot output, NIKL source/rights facts, transformed 3000-entry inventory, provider model/budget approval, live Azure catalog/profile, heard review outputs, production DB target, real full-suite evidence, Anki import/playback proof, and publication approval remain unresolved.
</unresolved_uncertainty>
<decision_posture>
Representative and exact-scale tests are deliberately separated: fast smoke catches wiring defects, slow exact-scale synthetic APKG proves structural scale, and neither proves production linguistic quality. Provider/catalog pilot evidence is a hash/count-only audit artifact derived from explicit files and DB rows; it cannot authorize live routes, voice profiles, audio, or final output.
</decision_posture>
<anti_regression>
Do not let fast smoke substitute for exact-scale proof; do not call synthetic exact-scale proof production content evidence; do not emit item keys, learner text, prompts, payloads, credentials, file paths, or private Korean text in pilot evidence; do not allow provider/catalog pilot validation to mutate protected inputs or grant route/profile authority; do not permit synthesis, fallback, or forbidden provider rows in provider/catalog pilot evidence; keep Korean package routing based on explicit persisted levels.
</anti_regression>
</judgment>
