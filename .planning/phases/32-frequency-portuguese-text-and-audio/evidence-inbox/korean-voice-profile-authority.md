# Korean Voice Profile Authority

This checkpoint records the user/operator choice for the Korean ordinary frequency audio voice profile. It authorizes only offline profile binding from the existing sanitized catalog evidence.

```json
{
  "schema_version": "korean-voice-profile-authority-v1",
  "kind": "voice-profile-authority",
  "selected_voice_id": "ko-KR-SunHi:DragonHDLatestNeural",
  "locale": "ko-KR",
  "region": "eastus",
  "catalog_result_file_sha256": "8341efaf3a1fab5f062f63c4934a93f3f1b4c5472b1612a4736b0125164824ec",
  "catalog_locator_sha256": "11a249b96ea150d7745dffd9ad4d9f816b34c27445a0963321500269f2de29f6",
  "catalog_content_sha256": "f0e081489197d3ec0acbc40c03c6cccacf2e90f7c1070d2588a3585c7e238e7f",
  "provider_policy_sha256": "6174ebd73b7e2963285bb2e44205dde10ef9d3917e50c90850b483b3c8a6fc79",
  "pilot_authority_sha256": "db2b2c1bff644ccf2e90bf59ab00d5c4a88c009d1c03bc8e8fbf8146e9be2ced",
  "catalog_voice_count": 16,
  "catalog_query_count": 1,
  "catalog_synthesis_attempt_count": 0,
  "profile_policy_version": "korean-neutral-ssml-v1",
  "ssml_policy": "neutral",
  "output_format": "audio-24khz-48kbitrate-mono-mp3",
  "usage_scope": [
    "ordinary-frequency-word-audio",
    "ordinary-frequency-sentence-audio"
  ],
  "powers": [
    "bind-voice-profile"
  ],
  "synthesis_allowed": false,
  "fallback_policy": "none",
  "grants_route_authority": false,
  "grants_voice_profile_authority": true,
  "grants_audio_authority": false,
  "grants_review_authority": false,
  "grants_export_authority": false,
  "grants_release_authority": false,
  "grants_publication_authority": false,
  "grants_delivery_authority": false
}
```

No live Azure query, audio generation, fallback, review application, export, release, publication, delivery, commit, PR, or Phase 32 closure is authorized by this checkpoint.
