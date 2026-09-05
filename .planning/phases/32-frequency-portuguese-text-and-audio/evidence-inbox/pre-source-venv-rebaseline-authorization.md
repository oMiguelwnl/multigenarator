# Phase 32 Pre-Source `.venv` Rebaseline Authorization

Decision: `authorize-non-mutating-current-venv-rebaseline`

User instruction: `Rebaseline current (Recommended)` in response to the Plan 32-18 shared `.venv` gate.

This authority accepts the current shared `.venv` no-follow fingerprint as the Plan 32-18 pre-source comparison baseline. It does not authorize deleting, repairing, syncing, or modifying `.venv`. It does not authorize NIKL retrieval, source transformation, provider calls, Azure calls, production database mutation, release, Git action, or publication.

```json
{
  "accepted_current_venv": {
    "file_count": 24984,
    "link_count": 4,
    "special_count": 0,
    "status": "unsafe",
    "tree_sha256": "c59fa62c6fc469aa896cbc68f2df79c46d0120b072f5bbf41b1e726ef3092526"
  },
  "decision": "authorize-non-mutating-current-venv-rebaseline",
  "expected_kind": "pre-source-venv-rebaseline",
  "granted_powers": [
    "accept-current-shared-venv-fingerprint-for-plan-32-18-preflight"
  ],
  "legacy_receipt_shared_venv_hash": "d6a8151e363a1c511d3a614082c2be646b6f24ef1a2211c4dffece73c57ffbf6",
  "non_authorized_powers": [
    "venv-repair",
    "dependency-sync",
    "source-retrieval",
    "source-transformation",
    "provider-call",
    "azure-call",
    "production-database-mutation",
    "release",
    "git-action",
    "publication"
  ],
  "receipt_file_sha256": "cc039851d275e95ac073ec7efbda4ea9dffc89323e5ff1a0cad27dce7d42d188",
  "schema_version": "phase32-pre-source-venv-rebaseline-v1"
}
```
