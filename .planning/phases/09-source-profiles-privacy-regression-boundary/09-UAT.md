---
status: complete
phase: 09-source-profiles-privacy-regression-boundary
source:
  - 09-01-SUMMARY.md
  - 09-02-SUMMARY.md
  - 09-03-SUMMARY.md
  - 09-04-SUMMARY.md
started: 2026-05-04T12:22:11Z
updated: 2026-05-04T12:27:54Z
---

## Current Test

[testing complete]

## Tests

### 1. Existing Frequency Deck Contract
expected: Frequency mode should still use the normal generated-card export contract: the field list includes Translation, word_audio, sentence_audio, and Image; the note type remains Multilang::Card; and highlight-only fields or note types do not leak into frequency exports.
result: pass
evidence: User confirmed this matched observed behavior.

### 2. Custom Word-List Contract
expected: Custom word-list mode should still use the manual-card export contract with Translation, the existing APKG/CSV/TSV export behavior, and no highlight note type or highlight-only sentence rules leaking into the flow.
result: pass
evidence: User asked to continue from this checkpoint, treated as approval under verify-work pass semantics.

### 3. Highlight Boundary Gating
expected: kindle-highlights should be representable internally for domain and export isolation, but the user-facing CLI generate command should still reject --source kindle-highlights until Phase 11 wires highlight generation.
result: pass
evidence: `uv run python -m multilang.cli generate --language en --source kindle-highlights` rejected the source with `--source must be one of: frequency, word-list`.

### 4. Privacy Redaction Boundary
expected: WebDAV credentials, authorization tokens, raw highlight paths, book metadata, private snippets, nested sensitive mappings, and exception messages should redact sensitive values to [REDACTED], while .gitignore excludes local highlight caches, raw Kindle exports, WebDAV secret files, and .env.* files.
result: pass
evidence: Included in Phase 09 evidence suite; `tests/security/test_redaction.py` passed.

### 5. Regression Evidence Boundary
expected: The Phase 09 evidence suite should remain runnable and green, proving source profiles, export isolation, redaction helpers, existing frequency/custom E2E export flows, and broad pytest collection before highlight work proceeds.
result: pass
evidence: `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/security/test_redaction.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q` passed with 46 tests; `uv run pytest --collect-only -q` collected 247 tests.

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None.
