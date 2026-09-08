# Korean Final Bundle Authority

This authority is least-power and grants only final-bundle binding for the exact evidence hashes below. It does not grant provider, database, audio, full-run, release, Git, publication action, or delivery powers.

```json
{
  "bindings": [
    {
      "byte_count": 2549,
      "path": "final-bundle-preflight.json",
      "sha256": "2e7cb81601a623927423ffa67cd18c3840c0a12a685b4a68101f51befac4b8a9"
    },
    {
      "byte_count": 948,
      "path": "source-retrieval-validation.json",
      "sha256": "1ff5948857d744e8f632d73135958cceb8d78917b75ade53abd2dd692d45839f"
    },
    {
      "byte_count": 884,
      "path": "source-build-validation.json",
      "sha256": "5fb09f29fb2495de84af9bc737e523f70be17956e1af2f0b86db71640ce3215c"
    },
    {
      "byte_count": 7917997,
      "path": "source-review-ai-consensus.json",
      "sha256": "7a263fec6200f44d0f9ac3211fac931f94f6ca05f4d5df5ea3522eead8f7d19e"
    },
    {
      "byte_count": 247,
      "path": "source-review-aggregate.json",
      "sha256": "a4654937079ed7e4ef618cb1b276e93254f1ae8c34ae5dcd1bd4234a6253af57"
    },
    {
      "byte_count": 1430,
      "path": "source-build-result.json",
      "sha256": "b6beb6d5e49a8616d77a8a7515cdcc07cdfbd017eae564297a5c2f6614d15b6c"
    }
  ],
  "expectations": {
    "exact_byte_redistribution": "approved",
    "private_local_use": "approved",
    "publication_eligible": "true",
    "repository_commit_eligible": "true"
  },
  "expected_kind": "final-bundle",
  "kind": "final-bundle",
  "powers": [
    "bind-final-bundle"
  ],
  "schema_version": "korean-checkpoint-authority-v1"
}
```
