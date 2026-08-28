---
phase: 32-frequency-portuguese-text-and-audio
plan: "03"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 03 Summary

**Completed**: 2026-08-28
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Recoverable factual discoveries only. The canonical worktree was dirty before and after execution; dirty Phase 31 AI and media sibling worktrees were present during final preflight/control-map; no sibling worktree was modified. The local shell lacked `rg`, so the privacy scan used the built-in content-search tool instead.
**Decisions Made**: No product, legal, provider, Azure, release, production database, human-approval, or publication decisions. Added local technical contracts for locator hashes, staged authority, and optional repository evidence within the approved offline scope.
**Notes for Verification**: This plan proves disposable-database CAS/evidence round trips and privacy-safe typed persistence only. It does not prove real Phase 31 activation, NIKL source rights, live Azure catalog/synthesis, provider execution, production database migration, final export eligibility, or publication readiness.
**Notes for Next Work**: Continue only offline Phase 32 lanes until exact Phase 31 active snapshot plus source/license/provider/Azure checkpoint authority exists. Later consuming code must reload these authority/evidence fields instead of reconstructing authority from paths, provider payloads, or prompts.

## Completed Work

- Added `src/multilang/services/authority_locator.py` as the sole authority-locator hash helper: it anchors to the project root, rejects root/target unavailability, path escape, symlink components, unsafe non-files, and descriptor drift, then hashes the NFC/normcase POSIX repo-relative locator with an 8-byte length prefix without returning or persisting the raw path.
- Added `KoreanFrequencyJobAuthority` in `src/multilang/domain/korean.py` with lowercase SHA-256 validation and staged required-hash rules for `pilot_base`, `pilot_audio`, and `full` authority.
- Added staged Korean authority persistence in `src/multilang/repositories/job_repository.py`: `bind_execution_authority`, `bind_audio_authority`, `load_korean_authority`, `require_korean_attempt_authority`, and `count_provider_attempts` now support exact retry, stage upgrade, column-vs-JSON drift detection, and operation-stage attempt guards.
- Added `KoreanFrequencyLexicalEvidence` and `LexicalCardCandidate.korean_frequency_evidence` in `src/multilang/domain/lexicon.py` to keep source ID/version/rank/POS/sense/confidence/license/curation/bundle/source/review/analyzer evidence separate from provider-authored fields.
- Added explicit lexical repository mappings for `frequency_bundle_sha256`, `frequency_source_sha256`, `source_review_receipt_sha256`, `source_review_aggregate_sha256`, and `lexical_evidence`, including strict reload reconstruction and drift rejection.
- Added `KoreanTextSelectionEvidence`, `KoreanAdaptiveIPlusOneEvidence`, `KoreanProviderReviewEvidence`, and `text_review_receipt_sha256` in `src/multilang/domain/text_quality.py`; accepted Korean text with Phase 32 evidence now requires an exact text review receipt and cannot be self-approved by machine/provider evidence alone.
- Added explicit text repository round trips for selection, adaptive i+1, provider-review, and text-review receipt evidence while preserving legacy rows with missing optional evidence.
- Added `AudioReviewStatus` plus Azure/audio evidence fields in `src/multilang/domain/audio.py` for provider SDK version, voice profile, catalog receipt, synthesis request, artifact hash, audio review, heard review, fallback origin, and rejection reason; approved audio now requires synthesized status, no fallback, and exact profile/artifact/review hashes.
- Added audio repository round trips for catalog/profile/request/artifact/review/heard evidence and kept `ready_for_korean_final_export` false for legacy or unapproved/fallback assets.

## CAS Matrix

- `pilot_base`: bound through `bind_execution_authority`; requires Phase 31 pointer locator/content, validation receipt, snapshot manifest/root, frequency bundle locator/content, source retrieval/build/review aggregate, provider policy, and pilot authority hashes.
- `pilot_audio`: bound through `bind_audio_authority`; requires all `pilot_base` facts plus catalog locator/content and profile-sample authority hashes.
- `full`: bound through `bind_audio_authority` or execution binding; requires all `pilot_audio` facts plus provider-review and heard-review authority hashes.
- Exact retry: same payload returns the existing authority without updating the row or adding provider attempts.
- Drift: any same-stage or lower-stage locator/content/order/stage/prestate drift raises before provider-attempt insertion.
- Stage guard: text/catalog operations require base authority, audio sample operations require audio authority, and production/full operations require full authority.

## Privacy Scan

- Narrowed scan of touched Plan 32-03 source surfaces for `private_path|raw_path|credential|secret|traceback` found no matches in `authority_locator.py`, `job_repository.py`, `lexical_repository.py`, `text_repository.py`, `audio_repository.py`, `text_quality.py`, `audio.py`, or `korean.py`.
- A broader initial scan found pre-existing credential/raw-path terms in unrelated WebDAV/Azure/foundation-export files; those were outside the Plan 32-03 write set and were not modified.
- The new evidence payloads persist hash/control/status fields only; no prompts, provider payload bodies, private roots, reviewer notes, credentials, raw exceptions, or raw authority paths were added.

## Verification

- RED for Task 32-03-03: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_phase32_text_audio_evidence.py -k 'text or audio or selection or adaptive or catalog or profile or artifact or review or legacy' -q` failed during collection with `ImportError: cannot import name 'AudioReviewStatus'`.
- GREEN for Task 32-03-03: same command passed with `4 passed`.
- Task 32-03-01 focused verification passed: `4 passed, 4 deselected` for `tests/repositories/test_job_repository.py -k 'execution_authority or locator or compare_and_set or exact_retry or attempt_guard'`.
- Task 32-03-02 focused verification passed: `4 passed, 5 deselected` for `tests/repositories/test_lexical_repository.py -k 'korean_frequency or provenance or identity or non_korean'`.
- Text/audio repository regression verification passed: `6 passed` for `tests/repositories/test_text_repository.py tests/repositories/test_audio_repository.py`.
- Full repository verification passed: `42 passed, 5 warnings` for `tests/repositories -q`; warnings were existing Alembic `path_separator` deprecation warnings.
- `git diff --check` passed with no output.
- Planning preflight allowed final state mutation: `node .planning/bin/gsdd.mjs lifecycle-preflight execute 32 --expects-mutation phase-status` returned `status: allowed`.
- Phase status helper kept Phase 32 open/in progress: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` returned `changed: false` because ROADMAP was already `[-]`.
- Session fingerprint was written after SPEC/ROADMAP state review: hash `0181058054ffbbafc45d5013f837a77eb4d3739ec7f43035a979bf67c15dffa6`.

## TDD Evidence

- Task 32-03-01 RED: repository tests targeted missing locator hashing, staged authority models, exact retry/no-update semantics, drift rejection, and attempt guards. GREEN: added locator helper, job authority contract, and repository CAS/guard methods; focused verification passed.
- Task 32-03-02 RED: lexical tests targeted missing Korean frequency lexical evidence, hash-column mappings, identity agreement, and legacy non-Korean readability. GREEN: added strict evidence model plus explicit persistence/reload drift checks; focused verification passed.
- Task 32-03-03 RED: text/audio evidence tests failed on missing `AudioReviewStatus` and related evidence symbols. GREEN: added strict text/audio evidence models, validation gates, and repository round trips; focused and regression verification passed.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified all Plan 32-03 task surfaces offline with synthetic fixtures and disposable repository tests. No live network, provider, Azure, production DB, source retrieval, asset activation, export, release, or publication action was performed.
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
  summary: `node .planning/bin/gsdd.mjs lifecycle-preflight execute 32 --expects-mutation phase-status` allowed execution but reported canonical dirty worktree state. Work stayed within the Plan 32-03 source/planning surfaces and no unrelated dirty files were reverted or intentionally modified.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `node .planning/bin/gsdd.mjs control-map --json` reported dirty unannotated Phase 31 AI and media sibling worktrees. Plan 32-03 did not modify any sibling worktree or overlapping Phase 31 evidence/media files.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The local shell environment did not provide `rg`, so the privacy scan used the built-in content-search tool with explicit include filters against the touched Plan 32-03 source surfaces.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and is not phase-verified. No live source retrieval, real source transformation, final bundle activation, provider call, Azure catalog or synthesis call, production database migration, review approval, asset commit, release, or publication is authorized by this summary. Korean frequency authority remains least-power and staged across exact Phase 31, source/build/review, provider, audio, heard-review, export, and release facts.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot, NIKL source bytes/terms/attribution, local-use and redistribution decisions, genuine transformed 3,000-entry inventory, complete source review, provider models/budgets, Azure live voice/profile/catalog, generated text/audio bytes, AI/provider review outputs, heard-review outputs, production DB target authority, Anki import/playback evidence, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Continue with offline fail-closed infrastructure that persists only reloaded hash-bound authority and separate machine/review evidence. Treat every external or production side effect as a separate checkpoint; passing repository tests do not imply content rights, provider authority, audio approval, production migration, export readiness, or publication readiness.
</decision_posture>
<anti_regression>
Do not redefine `canonical_authority_locator_sha256`; do not persist raw paths, prompts, provider payloads, private roots, reviewer notes, credentials, or raw exceptions. Do not weaken Phase 30 Korean NFC/source-backed identity/Kiwi matching. Do not introduce live `wordfreq`, spreadsheet/HWP parser authority, generic suffix rescue, provider-authored identity, source/build power conflation, unchecked provider attempts, fallback audio as export-ready, production DB mutation without exact checkpoint authority, GUID changes, or Korean production promotion from synthetic fixtures.
</anti_regression>
</judgment>
