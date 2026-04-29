---
status: passed
phase: 04-audio-synthesis
source: [04-VERIFICATION.md]
started: 2026-04-26T14:08:02Z
updated: 2026-04-26T14:10:54Z
total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0
---

## Current Test

human review completed and approved

## Tests

### 1. Live Azure shipped-path synthesis
expected: The default runtime should create non-zero `word_audio` and `sentence_audio` files, and CLI output should report audio counters without crashing.

evidence:
- command: `MULTILANG_DATABASE_URL='sqlite+pysqlite:///./.multilang/live-smoke-azure/smoke-audio.db' MULTILANG_LEXICON_DATA_DIR='./.multilang/live-smoke-azure/lexicon' MULTILANG_AUDIO_STORAGE_DIR='./.multilang/live-smoke-azure/audio' uv run python -m multilang.cli generate --language en --source word-list --input-file .multilang/live-smoke-azure/words.txt --lexicon-source-file .multilang/live-smoke-azure/kaikki-en.jsonl.gz`
- CLI counters:
  - `grounded_candidates=1`
  - `text_processed_items=1`
  - `accepted_text_items=1`
  - `audio_processed_items=2`
  - `audio_reused_items=0`
  - `fallback_audio_items=0`
  - `failed_audio_items=0`
- generated artifacts:
  - word audio: `.multilang/live-smoke-azure/audio/word/2026-04-24/en-US/en-US-JennyNeural-476994559e873a621c524b49c195ad4d14876ac168022ae43c0b3fe2868d82ef-696e2202bf544339fd45099ea0f3296216ade012a3ff3f9e5bbd42e91e5726a9.mp3` (`8496` bytes)
  - sentence audio: `.multilang/live-smoke-azure/audio/sentence/2026-04-24/en-US/en-US-JennyNeural-f30d12e0c4f27183a58bb52a3397a052a24572934d37a02c616821714ff8f8e3-468503515746b07c18f6271bbfa3a244f4bc4b05847e634dd907f0487135f057.mp3` (`14688` bytes)

review prompt:
- Did a live default-runtime run complete successfully with valid Azure Speech credentials?
- Were both `word_audio` and `sentence_audio` artifacts created with non-zero content and visible CLI counters?

result: passed

notes: user requested the phase be marked complete after human verification.

### 2. Real playback and pronunciation quality
expected: Both files should be playable and should pronounce the headword/example sentence naturally enough for learner use.

evidence:
- reviewed files:
  - `.multilang/live-smoke-azure/audio/word/2026-04-24/en-US/en-US-JennyNeural-476994559e873a621c524b49c195ad4d14876ac168022ae43c0b3fe2868d82ef-696e2202bf544339fd45099ea0f3296216ade012a3ff3f9e5bbd42e91e5726a9.mp3`
  - `.multilang/live-smoke-azure/audio/sentence/2026-04-24/en-US/en-US-JennyNeural-f30d12e0c4f27183a58bb52a3397a052a24572934d37a02c616821714ff8f8e3-468503515746b07c18f6271bbfa3a244f4bc4b05847e634dd907f0487135f057.mp3`
- operator feedback: user approved the generated result after the live smoke run (`"gostei"`).

review prompt:
- Did the generated audio files play successfully?
- Was the pronunciation quality acceptable for learner use?

result: passed

notes: user requested the phase be marked complete after human verification.

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None.
