# Quick Task 003 Verification: Renomear Campos e Template Latin

## Status

human_needed

## Goal Check

Goal: rename Latin card/export fields to `Word`, `Sentence`, and `Grammar`, update the Latin template to keep the frequency-card visual structure with `Grammar` as the Latin-specific extra field, and avoid audio/eSpeak changes.

Result: implementation goal achieved for code/template field contract. Full APKG/CSV/TSV verification needs the missing Latin MVP assets restored in this worktree.

## Evidence

- `LATIN_EXPORT_CARD_FIELD_NAMES` now contains `Word`, `Sentence`, and `Grammar`.
- `LatinExportRow.ordered_field_mapping()` emits `Word`, `Sentence`, and `Grammar`.
- `latin_mvp_card.md` references `{{Word}}`, `{{Sentence}}`, and `{{Grammar}}`.
- Old template/export references `{{Latin Word}}`, `{{Latin Sentence}}`, and `{{Gramatica}}` are absent from `src/`.
- Focused template and isolation tests passed.
- No eSpeak/audio files were changed.

## Commands Run

- `python -m pytest tests/services/test_card_template_loader.py tests/integration/test_v20_existing_modes_regression_evidence.py -q` — passed: `22 passed`.
- `python -m pytest tests/services/test_latin_export.py -q -k "field_order or row_mapping or rejects_nonblank_image or anki_model"` — passed: `4 passed, 7 deselected`.
- `python -m pytest tests/services/test_latin_export.py -q` — blocked by missing `data/latin_mvp/*.json` assets in this worktree.

## Remaining Human/Environment Step

Restore or provide the Latin MVP asset files under `data/latin_mvp/`, then rerun:

```bash
python -m pytest tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_final_milestone_evidence.py -q
```

## Scope Check

- No eSpeak NG removal was performed.
- No audio manifest/provider/runtime behavior was changed.
- No ROADMAP or SPEC files were changed.
