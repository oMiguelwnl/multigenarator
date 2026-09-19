---
phase: 34-export-review-and-evidence
verified: 2026-09-19
status: passed
scope: implementation_only
delivery_posture: repo_only
release_claim_posture: repo_closeout
evidence_contract:
  required_kinds: [code, test]
  observed_kinds: [code, test]
  missing_kinds: []
---

# Phase 34: implementation verification

Six-family APKG/CSV/TSV export, real level subdecks, exact media checks, durable leases and migration safety.

This verifies the implementation delivered in `3c7c91a`, not the original
production/delivery outcome. Full original acceptance remains in the archived
roadmap and requirements; pending work is in `KOREAN-PRODUCTION-BACKLOG.md`.

| Requirement | Status | Implementation | Regression evidence |
|---|---|---|---|
| KEXP-01 | passed: implementation | `src/multilang/services/export_anki_package.py` | `tests/integration/test_korean_export_families.py` |
| KEXP-02 | passed: implementation | `src/multilang/services/export_anki_package.py` | `tests/integration/test_korean_export_families.py` |
| KQA-01 | passed: implementation | `src/multilang/services/korean_learning_runtime.py` | `tests/services/test_korean_learning_runtime.py` |
| KQA-02 | passed: implementation | `docs/korean-implementation.json` | `tests/services/test_generation_report.py` |
| GEXP-01 | passed: implementation | `src/multilang/services/export_anki_package.py` | `tests/integration/test_korean_export_families.py` |
| GOPS-01 | passed: implementation | `src/multilang/services/generation_leases.py` | `tests/services/test_generation_leases.py` |
| GEVAL-01 | passed: implementation | `src/multilang/services/generation_report.py` | `tests/services/test_generation_report.py` |

The isolated commit verification recorded 447 passed / 2 skipped / 1 failed
before integration of the concurrent definition-contract commit. The 89-pass
integration rerun resolved that sole Polish fixture/API failure. Latest-result
aggregation is 452 distinct passed / 2 skipped / 0 unresolved failures. No full
repository run is claimed. Earlier working-tree results are a separate dataset.
See `milestones/v3.0-IMPLEMENTATION-EVIDENCE.json` for hashes and scope.

Runtime wiring and cross-phase review/export boundaries were independently
inspected at the committed revision. Live providers and production databases
were not called for closeout; historical paid attempts retain their original
failed/refailure status. Production permissions and review decisions are not
granted by this verification.
