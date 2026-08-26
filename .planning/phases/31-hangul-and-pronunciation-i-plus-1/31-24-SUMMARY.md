---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "24"
runtime: opencode
assurance: self_checked
---

# Phase 31: Hangul and Pronunciation i+1 - Plan 24 Summary

**Completed**: 2026-08-25
**Tasks**: 3
**Git Actions**: None
**Deviations**: None
**Decisions Made**: Evidence, snapshot, and export consumers now treat the exact `current-candidate` v2 bundle as the default Korean foundation provenance source while preserving explicit v1 history only.

## Completed Work

- Added RED/GREEN coverage for exact v2 evidence bindings across `current-candidate.json`, `bundle-manifest.json`, the four v2 bundle members, and the two regenerated review requests.
- Migrated evidence validation to reject v1, draft, mixed, stale-request, and incomplete v2 bundle states before writing a validation receipt.
- Migrated snapshot authority preparation to carry v2 source members into immutable snapshot copy members while keeping `content/korean-concepts-v1.json` as the registry side input.
- Migrated export bundle validation to require `hangul-v2` and `pronunciation-i-plus-1-v2` for current production exports, without changing field order, model/deck IDs, media binding, or GUID formula.
- Preserved inactive production behavior: missing active pointer, missing receipt, and export attempts remain blocked and write-free.

## Verification

- RED evidence: `set +e; OUTPUT="$(UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_evidence.py::test_evidence_contract_binds_exact_v2_candidate_and_request_hashes -q 2>&1)"; STATUS=$?; set -e; test "$STATUS" -eq 1 && case "$OUTPUT" in *AssertionError*|*assert*) ;; *) exit 1 ;; esac` passed before implementation.
- RED snapshot/export: `set +e; OUTPUT="$(UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_snapshot.py::test_snapshot_and_export_bind_exact_v2_and_refuse_before_activation -q 2>&1)"; STATUS=$?; set -e; test "$STATUS" -eq 1 && case "$OUTPUT" in *AssertionError*|*assert*) ;; *) exit 1 ;; esac` passed before implementation.
- `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_evidence.py -q` -> 38 passed.
- `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_snapshot.py -q -k 'not (activation or active_provenance or authorized or abrupt or concurrent or idempotent or repository)'` -> 46 passed, 24 deselected.
- `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_snapshot.py -q -k 'activation or active_provenance or authorized or abrupt or concurrent or idempotent or repository'` -> 24 passed, 46 deselected.
- `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_export.py -q` -> 45 passed.
- `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_curriculum.py tests/services/test_korean_foundation_review.py tests/services/test_korean_foundation_media.py -q` -> 162 passed.
- `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_curriculum.py tests/services/test_korean_foundation_review.py tests/services/test_korean_foundation_media.py tests/services/test_korean_foundation_evidence.py tests/services/test_korean_foundation_snapshot.py tests/services/test_korean_foundation_export.py -q` -> 315 passed.
- `git diff --check` passed.

## Notes For Verification

- Claim limit: exact v2 service-boundary migration and blocked production state only.
- No canonical validation receipt, canonical snapshot, active pointer, export artifact, review approval, rights disposition, playback evidence, or production readiness was created or claimed.
- The final full six-suite run took 34 minutes 15 seconds; earlier single-file snapshot runs timed out due to the slow activation/concurrency cases, so snapshot was also verified in two split groups before the final matrix.

## Notes For Next Work

- Plan 31-25 can now test CLI/integration and pre-evidence isolation against a coherent blocked v2 service layer.
- Plan 31-26 and later still own genuine qualified reviews, Portuguese policy, rights dispositions, exact media/playback evidence, receipt, inactive snapshot, activation, and local exports.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified RED/GREEN named tests, evidence full suite, split snapshot suite, export suite, adjacent curriculum/review/media suites, full six-suite matrix, and diff whitespace checks.
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
- none
</deltas>

<judgment>
<active_constraints>
- No provider, network, LLM, TTS, Azure, database, activation, evidence-intake, export, or asset/request mutation work occurred in this plan.
- Production remains fail-closed until genuine evidence, receipt, snapshot authorization, activation, and export gates are completed later.
- Explicit v1-history loading remains historical only and must not become a fallback from v2 current candidates.
</active_constraints>
<unresolved_uncertainty>
- Genuine qualified reviews, Portuguese policy, rights dispositions, exact media, playback evidence, canonical receipt, inactive snapshot, activation, local exports, and observed Anki acceptance remain unresolved.
- CLI/integration and full cross-mode behavior remain Plan 31-25 scope.
</unresolved_uncertainty>
<decision_posture>
- Default Korean foundation consumers now bind to the exact v2 `current-candidate` bundle and regenerated review-request hashes.
- Candidate selection remains separate from active snapshot authority; missing evidence or activation still blocks snapshot resolution and exports.
</decision_posture>
<anti_regression>
- Evidence index candidate bindings must remain the six exact v2 entries: pointer, bundle manifest, Hangul v2, pronunciation v2, curation v2, and media v2.
- Evidence must reject v1, draft, mixed, stale-request, and incomplete member states before receipt writes.
- Snapshot copy members must carry v2 Hangul/pronunciation/curation/media source members and only keep `content/korean-concepts-v1.json` as the registry input.
- Export validation must require current v2 source-pack versions while preserving model/deck IDs, GUID formula, field order, and media reference integrity.
- Missing receipt, missing active pointer, and inactive production paths must stay write-free and scanner-safe.
</anti_regression>
</judgment>
