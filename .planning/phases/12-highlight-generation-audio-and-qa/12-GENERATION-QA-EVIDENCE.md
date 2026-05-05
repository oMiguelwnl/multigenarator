# Phase 12 Generation, Audio, and QA Evidence

## Requirement Coverage

| Requirement | Evidence | Pass Signal |
|---|---|---|
| GEN-01 | `tests/integration/test_highlight_generation_audio_flow.py` | Highlight accepted text produces word audio, sentence audio, and a card row with blank Image. |
| GEN-02 | `tests/services/test_generate_text_items.py`, `tests/services/test_provider_text_adapters.py`, `tests/services/test_local_text_adapter.py` | Highlight examples use source-profile rules and bounded redacted context. |
| GEN-03 | `tests/services/test_text_review.py`, `tests/integration/test_v12_existing_mode_regression_boundary.py` | QA reports identify `kindle-highlights` and redact private fields. |

## Commands Run

```bash
python -m pytest tests/services/test_text_review.py tests/security/test_redaction.py -q
python -m pytest tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_highlight_generation_audio_flow.py tests/services/test_text_review.py -q
```

## Expected Pass Signals

- Source-aware review rows include `source_type=kindle-highlights` and `translation_required=false`.
- Existing frequency and custom word-list regression boundaries keep their default note/export contracts.
- Highlight card rows include `Word`, `IPA`, `word_audio`, `Example Sentence`, `sentence_audio`, `Definition`, and blank `Image`.
- Highlight card rows omit learner-facing `Translation` from ordered export fields.

## Privacy Checks

The evidence uses synthetic fixture identifiers and safe source keys only.

Absent from review reports and this evidence artifact:

- Raw private fixture text beyond synthetic count/source-key assertions
- Source file paths
- Book metadata values
- WebDAV-like URLs or secrets

## Safe Counts and Files

| File | Safe Count / Outcome |
|---|---|
| `tests/integration/test_highlight_generation_audio_flow.py` | 1 highlight integration fixture |
| `tests/services/test_text_review.py` | Source-aware QA report coverage |
| `tests/integration/test_v12_existing_mode_regression_boundary.py` | Frequency, word-list, and highlight QA regression boundary |

## Environment Note

`uv` is unavailable in this execution environment, so equivalent verification commands were run with `python -m pytest`.
