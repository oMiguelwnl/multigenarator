# Quick Task 056 Summary: Rebind Korean Foundation Byte Hashes

## Status

Completed. Focused Korean foundation regressions and the full offline test suite passed.

## Root Cause

The committed curation and media manifests had valid canonical `content_hash` values, expected inventories, and fully pending review state, but four recorded file-byte pins did not identify the bytes committed in `c90aa0b`:

| Artifact | Stale recorded SHA-256 | Committed/pre-fix SHA-256 | Corrected SHA-256 |
|---|---|---|---|
| `korean-foundations-v1-curation.json` | `6a5ddc06cfdb2ec3546e8854986bbe28ef957d170444dafadb0e97a06980055e` | `6c422c5c5edf581af39f91773b40f72ac5570b84b76cd38d6f18bea4ef190c00` | unchanged committed bytes |
| `korean-foundations-v1-media.json` | `ad8f05f3846da9874f49a85e045b4d225f15ffdac8fba13cbd39615d94561fcc` | `9f53766ea174c963e4904dd6172e490079ad693aded8dcb025a952327c90f0e1` | unchanged committed bytes |
| `31-CURRICULUM-REVIEW.md` | `ec20559593dbc025ccd0ca5485ed1e6fa8c895c4962f58f151a5b1d3025e9bff` | `e375accae6a280f7b4d14cfa01790b898aec9653baa9cd68c5f862b870925581` | `788aea87abb9d710617b86d8e05878151184d9ec92e4d3f0e013747c3655ae57` |
| `31-AUDIO-PLAYBACK-REVIEW.md` | `877eb42abe57d705d69e4a2ace077bfb905b23cd1ff22a0283fb7f256fabec44` | `53d7ce9eb7e72722064139545da286128c314fedcf45fe71903fd64cc5e324db` | `867aeb8e2fc79257aa1f55661f2e59f644062cedacbe55f42a65cc2f7cc424c9` |

The two request files changed only because their JSON contracts now bind the exact committed curation and media file bytes. No candidate JSON was edited.

## Changes

- Rebound both Phase 31 review requests to the committed curation and media file hashes.
- Updated exact byte pins in `tests/services/test_korean_foundation_review_requests.py` and `tests/services/test_korean_foundation_evidence.py` without weakening assertions.
- Corrected the exact hash records in `31-04-SUMMARY.md`, `31-07-SUMMARY.md`, and `31-09-SUMMARY.md` with explicit no-approval notes.
- Added the Quick 056 plan and this execution summary.

## Preserved Contracts

- All five files under `data/korean_foundations/` remained byte-identical to task start and have no Git diff.
- Curation canonical content SHA-256 remains `76d08bfa4c2780111a8d7fd89e73c86ee5393609ba1f40c003cc6e77745aff6b`.
- Media canonical content SHA-256 remains `e7ef7ed570b28ed70bb09a68426567ac5a2dc3df8bb33acb357d32c281e861dc`.
- The inventory remains 139 records, 973 pending curation gates, 509 pending media slots, and 325 required media slots.
- Both requests remain `request_only=true`, `request_status=needs_review`, `evidence_supplied=false`, and `human_checkpoint_count=0`.
- No reviewer, rights, playback, receipt, snapshot, activation, export, or approval evidence was added.

## TDD Evidence

Baseline reproduction before rebinding:

```text
tests/services/test_korean_foundation_review_requests.py: 4 failed, 4 passed
tests/services/test_korean_foundation_evidence.py: 32 failed, 5 passed
```

The failures consistently originated at stale exact-byte assertions before downstream contract and continuity checks could execute.

Focused green verification after rebinding:

```text
tests/services/test_korean_foundation_review_requests.py: 8 passed in 1.08s
tests/services/test_korean_foundation_evidence.py: 37 passed in 519.39s
tests/services/test_korean_foundation_snapshot.py: 69 passed in 1312.03s
tests/integration/test_korean_foundations_flow.py: 20 passed in 764.94s
Focused total: 134 passed
```

Full offline regression:

```text
1646 passed, 16 warnings in 3385.20s
```

The 16 warnings are existing third-party deprecations from `dateparser` and Alembic.

## Outcome

Phase 31 deterministic evidence assembly is executable again against the exact committed candidates and requests. This is a byte-binding correction only; Phase 31 remains open at its first human checkpoint and no learner-ready status was granted.
