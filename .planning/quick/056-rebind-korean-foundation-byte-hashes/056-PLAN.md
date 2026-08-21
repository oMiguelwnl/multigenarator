# Quick Task 056 Plan: Rebind Korean Foundation Byte Hashes

## Objective

Repair the Phase 31 evidence-chain regression by binding review requests, tests, and recorded hash tables to the exact Korean foundation bytes already committed in `c90aa0b`, without changing any candidate JSON payload or fabricating review evidence.

## Root Cause

The committed curation and media manifests retain their expected canonical `content_hash` values, counts, identities, and pending states, but their final serialized file bytes do not match stale pre-serialization SHA-256 pins. The two request Markdown files also differ from their stale recorded byte hashes and currently bind the stale manifest byte hashes.

## Scope

Update only byte-hash bindings and their exact historical tables. Do not edit the five candidate JSON files, canonical content hashes, curriculum/media payloads, review statuses, human checkpoint counts, evidence inbox, receipts, snapshots, activation state, or exports.

## Must-Haves

- The five candidate JSON files remain byte-identical to `407c4c3`.
- Curation remains canonically bound to `76d08bfa4c2780111a8d7fd89e73c86ee5393609ba1f40c003cc6e77745aff6b` and media to `e7ef7ed570b28ed70bb09a68426567ac5a2dc3df8bb33acb357d32c281e861dc`.
- Review requests bind the committed curation file SHA-256 `6c422c5c5edf581af39f91773b40f72ac5570b84b76cd38d6f18bea4ef190c00` and media file SHA-256 `9f53766ea174c963e4904dd6172e490079ad693aded8dcb025a952327c90f0e1`.
- Request SHA pins are recomputed only after the candidate bindings are corrected.
- Every request and candidate remains `needs_review`; the correction supplies no human, rights, playback, receipt, snapshot, activation, or export evidence.

## Tasks

### 1. Rebind request contracts and exact hash records

<action>
Replace the stale curation and media file hashes in both request contracts. Recompute the resulting request file hashes and update the Phase 31 exact-hash tables while preserving the prior plan narrative and all canonical-content hashes.
</action>

<files>
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-CURRICULUM-REVIEW.md`
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-AUDIO-PLAYBACK-REVIEW.md`
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-04-SUMMARY.md`
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-07-SUMMARY.md`
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-09-SUMMARY.md`
</files>

<verify>
Run `sha256sum` for both candidate manifests and both request files. Confirm `git diff --exit-code -- data/korean_foundations` succeeds and both request JSON payloads still declare `request_status=needs_review`, `evidence_supplied=false`, and `human_checkpoint_count=0`.
</verify>

### 2. Refresh deterministic pins and prove the evidence chain

<action>
Update the two focused test modules to pin the exact committed candidate bytes and newly rebound request bytes. Do not weaken, remove, or bypass any content, qualification, rights, playback, continuity, or canonical-mutation assertion.
</action>

<files>
- `tests/services/test_korean_foundation_review_requests.py`
- `tests/services/test_korean_foundation_evidence.py`
</files>

<verify>
Run `uv run pytest tests/services/test_korean_foundation_review_requests.py tests/services/test_korean_foundation_evidence.py tests/services/test_korean_foundation_snapshot.py tests/integration/test_korean_foundations_flow.py -q`, then the full offline suite with `uv run pytest -q`.
</verify>

## Completion Guard

Stop if any candidate JSON byte changes, any canonical `content_hash` changes, any pending state becomes approved, or any evidence/production root is created. This quick task repairs deterministic bindings only.
