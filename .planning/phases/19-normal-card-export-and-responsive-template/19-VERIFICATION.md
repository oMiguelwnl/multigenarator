---
phase: 19-normal-card-export-and-responsive-template
status: passed
verified: 2026-05-13
requirements: [TMPL-01, TMPL-02, TMPL-03]
automated_checks: 64
human_verification: []
gaps: []
---

# Phase 19 Verification: Normal Card Export and Responsive Template

## Result

**Status:** passed

Phase 19 achieved its goal: normal generated-card exports use the revised field contract and responsive sentence/audio layout without affecting highlight or phonetics cards.

## Must-Have Verification

| Must-have | Evidence | Status |
|---|---|---|
| Normal APKG, CSV, and TSV exports have no redundant `Front of Card` field or dangling template reference. | `tests/domain/test_exporting.py`, `tests/services/test_export_anki_package.py`, `tests/services/test_export_tabular_bundle.py`, `tests/integration/test_v13_normal_template_export_contract.py` | passed |
| `sentence_audio` appears beside `Example Sentence` through responsive normal-card markup/CSS. | `src/multilang/templates/normal_card.md`, `tests/services/test_card_template_loader.py`, `tests/services/test_export_anki_package.py`, `tests/integration/test_v13_normal_template_export_contract.py` | passed |
| Highlight template behavior remains unchanged after normal schema/CSS changes. | `tests/services/test_export_anki_package.py`, `tests/integration/test_highlight_export_artifacts.py`, `tests/integration/test_v13_normal_template_export_contract.py` | passed |
| Phonetics template behavior remains unchanged after normal schema/CSS changes. | `tests/integration/test_russian_phoneme_template_refresh_flow.py`, `tests/integration/test_v13_normal_template_export_contract.py` | passed |

## Requirement Traceability

| Requirement | Verification |
|---|---|
| TMPL-01 | Normal frequency fields are `SortIndex, word, IPA, Definitions, Example Sentence, Translation, word_audio, sentence_audio, Image`; normal template references `{{word}}` and not `{{Front of Card}}`; APKG/CSV/TSV evidence confirms the artifact contract. |
| TMPL-02 | `.exampleSentenceLine`, `.exampleSentenceText`, and `.sentenceAudioButton` keep sentence audio beside the example sentence with bounded flex behavior. |
| TMPL-03 | Highlight/manual note models keep their dedicated field tuple and phonetics keeps `PHONEME_FIELD_NAMES`; forbidden normal fields are not introduced. |

## Automated Checks

```text
python -m pytest tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py tests/integration/test_highlight_export_artifacts.py tests/integration/test_russian_phoneme_template_refresh_flow.py -q
```

Result: **64 passed**.

## Schema Drift Gate

`gsd-tools verify schema-drift 19` reported `drift_detected: false`.

## Code Review Gate

Code review was configured on, but the `gsd:code-review` skill is not installed in this runtime. Per workflow rules, this is non-blocking and phase verification proceeded using deterministic tests and artifact inspection.

## Gaps

None.

## Human Verification

None required.
