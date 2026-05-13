---
phase: 20-word-audio-integrity-gate
status: passed
verified: 2026-05-13
requirements: [AUD-01, AUD-02]
automated_checks: 102
human_verification: []
gaps: []
---

# Phase 20 Verification: Word Audio Integrity Gate

## Result

**Status:** passed

Phase 20 achieved its goal: exported normal cards now pass through exact word-audio integrity checks during generation reuse, card assembly, and runtime artifact export. Mismatches are regenerated when safe and blocked with clear diagnostics when persisted snapshots or audio metadata drift.

## Must-Have Verification

| Must-have | Evidence | Status |
|---|---|---|
| User can detect `word_audio` assets whose synthesis text or stored manifest does not exactly match card `Word`. | `src/multilang/services/audio_integrity.py`, `tests/services/test_audio_integrity.py` | passed |
| User receives regenerated `word_audio` when a reusable stored WORD asset mismatches the current lexical Word. | `src/multilang/services/generate_audio_items.py`, `tests/services/test_generate_audio_items.py` | passed |
| User receives a clear validation block before snapshots persist when assembly sees unrepaired word-audio mismatch. | `src/multilang/services/assemble_export_cards.py`, `tests/services/test_assemble_export_cards.py` | passed |
| User receives non-zero APKG, CSV, and TSV export failures when persisted WORD audio later drifts from snapshot `Word`. | `src/multilang/runtime.py`, `tests/integration/test_export_job_flow.py` | passed |
| Highlight/manual behavior remains isolated where source profiles do not export `word_audio`. | `tests/services/test_assemble_export_cards.py`, `tests/services/test_generate_audio_items.py`, prior Phase 19 regression suite | passed |

## Requirement Traceability

| Requirement | Verification |
|---|---|
| AUD-01 | `audio_integrity` compares `display_text`, `normalized_input.display_text`, `normalized_input.tts_text`, and `provenance.text_hash` against `Word`, with exact accented-word and sentence-asset mismatch coverage. |
| AUD-02 | Generation rejects corrupted reusable WORD audio and regenerates it; assembly/runtime export gates block remaining mismatches before learner artifacts are written. |

## Automated Checks

```text
python -m pytest tests/integration/test_export_job_flow.py tests/services/test_assemble_export_cards.py tests/services/test_generate_audio_items.py tests/services/test_audio_integrity.py -q
```

Result: **38 passed**.

```text
python -m pytest tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py tests/integration/test_highlight_export_artifacts.py tests/integration/test_russian_phoneme_template_refresh_flow.py -q
```

Result: **64 passed**.

## Schema Drift Gate

`gsd-tools verify schema-drift 20` reported `drift_detected: false`.

## Code Review Gate

Code review was configured on, but the `gsd:code-review` skill is not installed in this runtime. Per workflow rules, this is non-blocking and phase verification proceeded using deterministic tests and artifact inspection.

## Gaps

None.

## Human Verification

None required.
