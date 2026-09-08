# Korean Bounded Pilot Authorization

This least-power checkpoint authorizes a future bounded text/catalog pilot only. It does not authorize audio synthesis, profile sampling, production database migration, full generation, review application, export, release, publication, or delivery.

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
      "byte_count": 2073,
      "path": "provider-review-authorization.md",
      "sha256": "f5e3097ed470f513223d72d16d1710d6689423025ef292be2d3ccd1d844a0f20"
    },
    {
      "byte_count": 195,
      "path": "provider-review-authority-validation.json",
      "sha256": "0b5039c1cbffea38bfef47212c40d5b7e4550fb34c959cee2be6fcfc168cb5b6"
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
  "expected_kind": "pilot",
  "expectations": {
    "audio_synthesis_allowed": "false",
    "catalog_identity": "ko-KR-voice-catalog",
    "catalog_route_policy_sha256": "e0e9be8f0d3cf5aeed2f75800041e04bdc0af057c4ca90000c2e472e1cb5527d",
    "cost_ceiling_usd": "1.00",
    "credential_aliases_text": "MULTILANG_OPENAI_API_KEY,MULTILANG_DEEPL_API_KEY",
    "db_migration_allowed": "false",
    "definition_route_policy_sha256": "ce2838cf50302daea7347c028f50f977b3ce2ff68bb774a099d5da969d28ddc2",
    "enabled_operations": "catalog,definition,judge,repair,sentence_generation,translation",
    "fallback_policy": "none",
    "full_run_allowed": "false",
    "judge_route_policy_sha256": "a4a35fc12869f1466cc9f284b121c0c616b7eb65150cd36c8fd0e53d42e57109",
    "latency_ceiling_ms": "60000",
    "max_attempts": "2",
    "max_batch_items": "10",
    "max_concurrency": "1",
    "pilot_item_count": "10",
    "profile_sample_allowed": "false",
    "provider_policy_file_sha256": "c0b4fcc9a05b07258bf096396cc1c8ee712cf8db26e09dd05e4a4db0a4302aee",
    "provider_policy_sha256": "6174ebd73b7e2963285bb2e44205dde10ef9d3917e50c90850b483b3c8a6fc79",
    "provider_review_validation_sha256": "0b5039c1cbffea38bfef47212c40d5b7e4550fb34c959cee2be6fcfc168cb5b6",
    "publication_allowed": "false",
    "release_allowed": "false",
    "repair_route_policy_sha256": "8f4c00d52f796cc08074302ec71fbbf534229b8920f87c776afabd162b2d96aa",
    "sentence_route_policy_sha256": "f85b4aa4c27755bebefd9ad4b45b32e03e5faaeeaf2d2aad4c169a732396688b",
    "text_review_policy_file_sha256": "78d671e81feb48864f2db4ea1a0a30d08fcc0fd9b4118c4b04d4ceeec7d0ef6c",
    "timeout_seconds": "60.0",
    "token_ceilings": "4096_input_1024_output_5120_total",
    "translation_route_policy_sha256": "78c5e2b302f80a3645ab4d53df2c24bb44ecc1188b0cee3ff83762645e2bc061",
    "word_audio_allowed": "false"
  },
  "kind": "pilot",
  "powers": [
    "run-bounded-pilot"
  ],
  "schema_version": "korean-checkpoint-authority-v1"
}
```
