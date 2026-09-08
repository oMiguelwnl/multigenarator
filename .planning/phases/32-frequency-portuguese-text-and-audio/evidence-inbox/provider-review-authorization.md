# Korean Provider Route Review Authorization

This least-power checkpoint authorizes review of the offline provider route policy only. It does not authorize provider calls, DeepL calls, Azure catalog queries, audio synthesis, database mutation, full generation, export, release, publication, or delivery.

```json
{
  "bindings": [
    {
      "byte_count": 6516,
      "path": "provider-pilot-preflight.json",
      "sha256": "644e501a8352bfff4725508b2710755c6773a488cac265873944484f9c32af64"
    },
    {
      "byte_count": 5489,
      "path": "provider-policy.json",
      "sha256": "c0b4fcc9a05b07258bf096396cc1c8ee712cf8db26e09dd05e4a4db0a4302aee"
    },
    {
      "byte_count": 1299,
      "path": "text-review-policy.json",
      "sha256": "78d671e81feb48864f2db4ea1a0a30d08fcc0fd9b4118c4b04d4ceeec7d0ef6c"
    },
    {
      "byte_count": 1634,
      "path": "final-bundle-authorization.md",
      "sha256": "4a23d51fd64ee121e08217b235207ef3519df54828c451d03323418de9bc6e68"
    },
    {
      "byte_count": 192,
      "path": "final-bundle-authority-validation.json",
      "sha256": "a778f6a8d8fe433773efe203e7fd5075e60420a46d60fcf01ccf030ad8afd673"
    }
  ],
  "expected_kind": "provider-review",
  "expectations": {
    "audio_synthesis_allowed": "false",
    "catalog_route_policy_sha256": "e0e9be8f0d3cf5aeed2f75800041e04bdc0af057c4ca90000c2e472e1cb5527d",
    "credential_aliases_text": "MULTILANG_OPENAI_API_KEY,MULTILANG_DEEPL_API_KEY",
    "fallback_policy": "none",
    "final_bundle_authority_sha256": "4a23d51fd64ee121e08217b235207ef3519df54828c451d03323418de9bc6e68",
    "full_run_allowed": "false",
    "provider_policy_file_sha256": "c0b4fcc9a05b07258bf096396cc1c8ee712cf8db26e09dd05e4a4db0a4302aee",
    "provider_policy_sha256": "6174ebd73b7e2963285bb2e44205dde10ef9d3917e50c90850b483b3c8a6fc79",
    "text_review_policy_file_sha256": "78d671e81feb48864f2db4ea1a0a30d08fcc0fd9b4118c4b04d4ceeec7d0ef6c"
  },
  "kind": "provider-review",
  "powers": [
    "review-provider-route"
  ],
  "schema_version": "korean-checkpoint-authority-v1"
}
```
