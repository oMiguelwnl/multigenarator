# Phase 29 Research: Latin ElevenLabs Audio Refresh

## Standard Stack

- Use the existing `multilang.services.elevenlabs_speech_adapter.ElevenLabsSpeechAdapter` as the preferred active provider path; it already posts to `POST /v1/text-to-speech/{voice_id}` with `model_id=eleven_multilingual_v2`, accepts `mp3_44100_128`, writes MP3 bytes, and rotates configured API keys.
- Keep `src/multilang/services/latin_audio.py` as the manifest/readiness contract. It already accepts MP3 media by checking the `ID3` marker and stores provider, provider version, voice, pronunciation policy, generated text, text hash, audio kind, playback status, storage path, and fallback reason.
- Generate replacement media as repository-relative MP3 files under the Latin MVP audio tree, using stable basenames such as `latin-mvp-0001-word.mp3` and `latin-mvp-0001-sentence.mp3` so Anki media references remain public and deterministic.
- Use existing pytest evidence patterns: service tests for metadata/readiness, integration tests over committed real assets, and export tests that inspect APKG media packaging.

## Architecture Patterns

- Treat the audio refresh as an asset and policy migration, not a general modern-language audio refactor.
- Add a Latin-specific ElevenLabs generation/manifest helper that joins the frozen source pack to generated audio outputs and writes `data/latin_mvp/latin-mvp-50-v1-audio.json` only after sample approval is recorded.
- Keep representative provider policy separate from full manifest approval. The policy artifact should promote ElevenLabs only after user playback review and should record FineVoice as research-only.
- Preserve fail-closed export readiness: `build_latin_export_rows()` should continue to load the audio manifest and call `assert_latin_audio_manifest_export_ready()` before exporting APKG/CSV/TSV.
- Remove project-level eSpeak NG references only after refreshed manifest/media and export tests pass. Do not remove or uninstall the system package; simply stop requiring it in source code, tests, docs, and planning evidence.

## Don't Hand-Roll

- Do not create a custom HTTP client for ElevenLabs in the Latin path unless the existing adapter cannot support the needed call shape. Reuse or thinly wrap the adapter so credential handling, key rotation, output format, and test doubles stay centralized.
- Do not invent a FineVoice adapter in this phase. FineVoice has public marketing/API claims for a developer platform and broad language support, but this phase should only capture it as a future candidate until API docs, authentication, voice selection, output formats, retention/privacy, and deterministic testability are verified.
- Do not bypass `LatinAudioManifest` or direct export validators by writing sound tags directly in export code.
- Do not keep parallel eSpeak and ElevenLabs manifest paths as a compatibility layer unless a concrete approved fallback requirement is added.

## Common Pitfalls

- Approving provider metadata without human playback review. Replacement samples must be generated and explicitly approved before full manifest promotion.
- Leaving `espeak-ng` as an allowed/expected provider in tests or committed manifest after the refresh. Tests should fail if the refreshed committed assets still depend on eSpeak NG.
- Assuming ElevenLabs output is deterministic. Persist generated media, hashes of generated text, provider version/model, voice ID, and review metadata; do not re-call the provider during export.
- Mixing media formats. Existing readiness accepts RIFF and ID3; export tests must expect MP3 basenames if ElevenLabs is used.
- Removing eSpeak NG too early. The removal step must be last and must not include system uninstall instructions.
- Leaking secrets or private paths in manifests, review artifacts, CLI output, or export evidence.

## Sources

- Existing code: `src/multilang/services/elevenlabs_speech_adapter.py`, `src/multilang/services/latin_audio.py`, `src/multilang/services/latin_export.py`.
- Existing tests: `tests/services/test_elevenlabs_speech_adapter.py`, `tests/services/test_latin_audio.py`, `tests/integration/test_v20_latin_audio_asset.py`, `tests/integration/test_v20_latin_export_evidence.py`.
- ElevenLabs API reference fetched 2026-06-15: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` supports `model_id=eleven_multilingual_v2`, `output_format=mp3_44100_128`, `language_code`, pronunciation dictionaries, and binary audio responses.
- FineVoice site fetched 2026-06-15: markets AI voice generation, developer API, 1,500+ voices, and 154+ languages/accents, but no project adapter or verified Latin voice contract exists in this repo.
