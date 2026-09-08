# Korean Transformation Build Authorization

Decision: `authorize-exact-redistributable-build`

This authority grants only inactive local transformation/build for the exact retrieved NIKL bytes and records redistribution permission as a decision field. It does not grant repository commit, publication, release, provider use, Azure use, or production database mutation.

```json
{
  "bindings": [
    {
      "byte_count": 867,
      "path": "source-retrieval-result.json",
      "sha256": "b5f6f1ccc02589be846e05c32d9b6f883616088ac03191cabe113a6b464bdf58"
    },
    {
      "byte_count": 948,
      "path": "source-retrieval-validation.json",
      "sha256": "1ff5948857d744e8f632d73135958cceb8d78917b75ade53abd2dd692d45839f"
    },
    {
      "byte_count": 2350,
      "path": "transformation-preflight.json",
      "sha256": "b8cd4e375dfdca99a9ec3363e18119b02e333750fc6dec01eac0119b2a497e96"
    }
  ],
  "expected_kind": "transformation-build",
  "expectations": {
    "accepted_filename": "한국어 학습용 어휘 목록.txt",
    "attribution_evidence_id": "source-decision-lines-53-57-attribution",
    "backfill_policy": "same-source-rank-order-only",
    "build_power": "inactive-bundle-only",
    "commercial_downstream_use_approved": "false",
    "decision": "authorize-exact-redistributable-build",
    "exact_source_bytes_redistribution": "true",
    "local_use_approved": "true",
    "publication_approved": "false",
    "repository_commit_approved": "false",
    "source_byte_count": "132254",
    "source_bytes_sha256": "3b49681f05d6a7490c13da2a2847e433effdf65da409fd295792d6ee33685064",
    "source_denominator": "5965",
    "source_text_encoding": "cp949",
    "storage_disposition": "private-local-ignored",
    "target_accepted_count": "3000",
    "target_rejection_count": "2965",
    "terms_evidence_id": "source-page-kogl-type1-attribution",
    "transformation_approved": "true",
    "transformed_data_redistribution": "true"
  },
  "kind": "transformation-build",
  "powers": [
    "build-inactive-bundle"
  ],
  "schema_version": "korean-checkpoint-authority-v1"
}
```
