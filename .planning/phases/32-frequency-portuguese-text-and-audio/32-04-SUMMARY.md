---
phase: 32-frequency-portuguese-text-and-audio
plan: "04"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 04 Summary

**Completed**: 2026-08-29
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Recoverable factual discoveries only. `src/multilang/services/ingest_lexical_items.py` did not require a direct edit because Korean frequency ingestion now fails closed at `build_frequency_level` before any seed or `wordfreq` branch unless explicit frozen entries are supplied. Adjacent regression `tests/services/test_korean_language_support.py` has a pre-existing out-of-plan `ko-KR` allowlist failure in Phase 31 media/acoustic files and was not modified.
**Decisions Made**: No legal, provider, Azure, source-rights, production database, release, or publication decisions. Added offline technical contracts for evidence reload, final frozen Korean entry loading, and selected-Kiwi projection only.
**Notes for Verification**: This summary proves synthetic reloads, disposable-database persistence, exact bundle locator/content rehashing, and content-free morphology projection. It does not prove real NIKL rights, real frequency inventory approval, live provider execution, Azure catalog/synthesis, production DB migration, learner-ready Korean content, APKG import, or publication readiness.
**Notes for Next Work**: Continue only offline Phase 32 lanes until exact Phase 31 active snapshot plus source/license/provider/Azure checkpoint authority exists. Downstream code must pass explicit frozen Korean entries and source-review hashes; any missing or drifted authority must produce zero provider attempts.

## Completed Work

- Added `tests/integration/test_frequency_evidence_persistence.py` covering export evidence reload, stable GUID preservation, blank `Image`, provider route/cache/budget/schema hashes, retry/fallback/token/cost/latency persistence, denominator counts, and persisted-value privacy scanning.
- Extended `ExportCardRow` and `ExportDeckArtifact` with `frequency_level`, `frequency_bundle_sha256`, `export_manifest_sha256`, and `export_gate_receipt_sha256` fields where applicable, without adding those fields to learner-facing export mappings or GUID input.
- Wired export evidence through `ExportRepository` for card snapshots and deck artifacts using the existing DB columns.
- Extended `ProviderCallLogCreate` and `ProviderCallLogRepository` to persist route policy, budget snapshot, cache key, and response schema hashes, while collapsing failure summaries to controlled redacted labels.
- Added `load_korean_final_frequency_entries` in `src/multilang/services/korean_frequency.py` to require `job_id`, bundle root, binding receipt, reloaded `KoreanFrequencyJobAuthority`, and repo-root locator hashing before reading final entries.
- Added `project_korean_match_status` as the shared `match` / `mismatch` / `inconclusive` projection for selected-Kiwi outcomes.
- Updated `build_frequency_level` and `build_frequency_deck` so Korean final frequency candidates require explicit `KoreanFrequencyEntry` rows plus source-review hashes and never route to live `wordfreq`, seed fallback, first-sense lookup, or provider-authored identity.
- Added Korean final candidate projection to `LexicalCardCandidate` with source rank, final rank, level, POS, sense, license, curation, source hash, review hashes, and analyzer fingerprint preserved in `KoreanFrequencyLexicalEvidence`.
- Updated `LexicalGroundingService.ground_frequency_candidate` to pass through already-grounded Korean candidates that carry frozen frequency identity/evidence instead of reanalyzing or rewriting them.
- Updated Korean text validation mismatch details to include `projection=mismatch` for selected-Kiwi mismatch and `projection=inconclusive` for missing, invalid, ambiguous, OOV, unavailable, or fingerprint-drifted evidence without echoing sentence, lemma, sense, prompt, or source content.

## Persistence Scan

- The new integration test expires and reloads SQLAlchemy rows from `GenerationJob`, `CardExportModel`, `DeckExportModel`, and `ProviderCallLogModel` in an in-memory DB.
- Export evidence survives reload while `note_guid` remains derived only from `ExportCardIdentity`; changing bundle/gate evidence does not change the GUID.
- Provider rows retain operation, route policy hash, budget hash, cache key hash, response schema hash, attempt, fallback origin, latency, token counts, estimated cost, and success/failure status.
- Persisted-value scan rejects private roots, raw prompts, raw payload markers, credentials, source rows, and reviewer notes. Failure summaries are reduced to controlled labels such as `provider_error: redacted provider failure`.
- Provider summaries include missing-value denominators when hash evidence is present: `token_value_count` and `cost_value_count` report observed numerator counts rather than implying complete telemetry.

## Locator Trace

- `load_korean_final_frequency_entries` validates the existing inactive build result with `validate_korean_source_build_result` before runtime use.
- It hashes the safe repo-relative `manifest.json` locator via `canonical_authority_locator_sha256` and compares it to `authority.frequency_bundle_locator_sha256`.
- It compares manifest root content to `authority.frequency_bundle_content_sha256`.
- It compares build result retrieval/source authority and exact `build-result.json` bytes to the reloaded authority fields.
- It compares the supplied binding receipt to `authority.source_review_aggregate_sha256`.
- It reads `curated-inventory.jsonl` only after those checks pass, validates 3000 contiguous entries with 1000 per level, and checks entry source hashes against the build result.

## Fallback Poison Matrix

- Missing Korean frozen entries: raises `ValueError` before calling `iter_wordlist`.
- Missing Korean source-review hash inputs: raises `ValueError` before candidate creation.
- Rejected Korean lemma in final mode: reduces usable frozen entries and raises count drift instead of backfilling.
- Mutable assets directory or version lookup: bypassed for Korean final mode because entries must be supplied explicitly.
- Seed fallback flag set to true for Korean: ignored; explicit frozen entries are still required.
- Already-grounded Korean final candidate with frozen evidence: returned unchanged; no source reanalysis or generic lexical lookup occurs.
- Selected-Kiwi `MATCHED`: allowed to pass text target validation.
- Selected-Kiwi `MISMATCH`: blocks with `projection=mismatch`.
- Selected-Kiwi ambiguous, OOV, unavailable, missing, invalid, malformed, or fingerprint-drifted states: block with `projection=inconclusive`.
- Generic suffix, token, substring, whitespace, Stanza, Japanese, or Mandarin fallback: not reached for Korean target matching.

## TDD Evidence

- Task 32-04-01 RED: `tests/integration/test_frequency_evidence_persistence.py` failed on missing `ExportCardRow.frequency_level` and missing `ProviderCallLogCreate.route_policy_sha256`. GREEN: added export evidence fields, repository round trips, provider hash persistence, controlled redaction, and denominator summaries.
- Task 32-04-02 RED: Korean frequency tests failed on missing `load_korean_final_frequency_entries`, Korean `build_frequency_level` calling live `wordfreq`, and missing `korean_final_entries` API. GREEN: added locator-bound loader and explicit frozen-entry projection.
- Task 32-04-03 RED: Korean text validation tests failed because morphology details lacked match/mismatch/inconclusive projection; lexical grounding test initially had a test import typo that was corrected before production changes. GREEN: added shared projection and frozen-candidate pass-through.

## Verification

- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/integration/test_frequency_evidence_persistence.py -k 'export or provider or frequency_level or guid or route or denominator or redaction or staged_reload' -q` -> `2 passed`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_frequency.py -k 'final_runtime or locator or binding_drift or idempotent or poison or persisted_candidate' -q && UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_frequency_decks.py -k 'korean or build_frequency' -q` -> `1 passed, 13 deselected`; `8 passed, 20 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_lexical_grounding.py -k 'korean and (consensus or mismatch or ambiguous or oov or fingerprint)' -q && UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_text_validation.py -k 'korean' -q` -> `3 passed, 39 deselected`; `23 passed, 33 deselected`.
- Full modified frequency tests passed: `tests/integration/test_frequency_evidence_persistence.py tests/services/test_frequency_decks.py -q` -> `30 passed`.
- Full Korean frequency tests passed: `tests/services/test_korean_frequency.py -q` -> `14 passed`.
- Full lexical/text validation tests passed on rerun with a larger timeout: `tests/services/test_lexical_grounding.py tests/services/test_text_validation.py -q` -> `98 passed, 3 warnings`.
- Adjacent provider telemetry regression passed: `tests/repositories/test_provider_call_log_repository.py -q` -> `2 passed`.
- Migration schema parity passed: `tests/test_migration_schema_parity.py -q` -> `12 passed, 14 warnings`.
- Export-only adjacent checks passed: `tests/services/test_assemble_export_cards.py -q` -> `28 passed`; `tests/services/test_export_anki_package.py -q` -> `29 passed`; targeted Korean export identity check passed.
- Adjacent broad command `tests/services/test_assemble_export_cards.py tests/services/test_export_anki_package.py tests/services/test_korean_language_support.py -q` found one out-of-plan failure: `test_production_uses_ko_kr_only_at_the_explicit_locale_constant` reports pre-existing `ko-KR` occurrences in Phase 31 media/acoustic files outside Plan 32-04.
- Planning preflight allowed state mutation: `node .planning/bin/gsdd.mjs lifecycle-preflight execute 32 --expects-mutation phase-status` returned `status: allowed` with known dirty-worktree warnings.
- Phase status helper kept Phase 32 open/in progress: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` returned `changed: false` because ROADMAP was already `[-]`.
- Session fingerprint was written after SPEC/ROADMAP state review: hash `986513abb397ce3897afe0175c2aefa47583e0344a46aa2b65479fc57837d510`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified all Plan 32-04 task surfaces offline with synthetic fixtures and disposable repository tests. No live network, provider, Azure, production DB, real source retrieval, asset activation, export release, Git commit, or publication action was performed.
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
  summary: Preflight/control-map allowed execution but reported canonical dirty worktree state and invalid sibling worktree inspection for `/tmp/multilang-phase31-ai` and `/tmp/multilang-phase31-media`. Work stayed within Plan 32-04 source/test surfaces plus required GSDD state artifacts.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `src/multilang/services/ingest_lexical_items.py` was listed as a planned modification, but the no-live-Korean-final edge was enforced lower in `build_frequency_level`; direct ingest edits would have added an untested API surface and were unnecessary for fail-closed behavior.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The adjacent Korean locale allowlist test fails because of existing `ko-KR` literals in Phase 31 media/acoustic code outside this plan. The failure was recorded as residual risk and not repaired under Plan 32-04.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and is not phase-verified. No live source retrieval, real source transformation, final bundle activation, provider call, Azure catalog or synthesis call, production database migration, review approval, asset commit, release, or publication is authorized by this summary. Korean final frequency runtime must be driven by explicit frozen entries and reloaded hash-bound authority only.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot, NIKL source bytes/terms/attribution, local-use and redistribution decisions, genuine transformed 3,000-entry inventory, complete source review, provider models/budgets, Azure live voice/profile/catalog, generated text/audio bytes, AI/provider review outputs, heard-review outputs, production DB target authority, Anki import/playback evidence, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Continue with offline fail-closed infrastructure and hash-only evidence. Treat missing Korean frozen entries, source-review receipts, authority drift, selected-Kiwi mismatch, and analyzer inconclusive states as blockers rather than repair opportunities. Passing synthetic repository tests do not imply content rights, provider authority, audio approval, production migration, export readiness, or publication readiness.
</decision_posture>
<anti_regression>
Do not persist raw paths, prompts, provider payloads, private roots, reviewer notes, credentials, raw exceptions, or source rows. Do not add Korean final runtime edges to live `wordfreq`, mutable asset discovery, seed fallback, first-sense lookup, provider-authored identity, generic suffix rescue, Stanza fallback, or GUID changes. Do not weaken blank `Image`, stable export field order, Korean NFC/source-backed identity, selected-Kiwi fail-closed target matching, or staged authority comparisons.
</anti_regression>
</judgment>
