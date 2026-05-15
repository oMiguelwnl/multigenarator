# v1.3 Milestone Evidence: Card Quality Remediation and Deck Validation

This privacy-safe artifact closes v1.3 with scanner-readable evidence for audit behavior, text-field corrections, normal-card export/template changes, word-audio integrity, validator fixtures, and unchanged behavior for non-normal deck modes. It references runnable focused suites rather than embedding private deck contents.

## Requirement Coverage

| Requirement | Phase | Status | Evidence |
|-------------|-------|--------|----------|
| AUDIT-01 | Phase 17 | COMPLETE | `tests/cli/test_audit_deck_command.py` plus `tests/services/test_deck_audit_reader.py` prove APKG audit reports by note/card field. |
| AUDIT-02 | Phase 17 | COMPLETE | `tests/services/test_deck_audit_reports.py` and `tests/domain/test_deck_audit.py` cover Definition issue grouping and normalized defect output. |
| AUDIT-03 | Phase 17 | COMPLETE | `tests/cli/test_audit_deck_command.py` proves reproducible output and non-mutating APKG audit behavior. |
| IPA-01 | Phase 18 | COMPLETE | `tests/services/test_assemble_export_cards.py` and `tests/services/test_lexical_grounding.py` prove IPA-only export and word fallback. |
| DEF-01 | Phase 18 | COMPLETE | `tests/services/test_text_field_remediation.py` proves morphology-only Definition remediation and validation. |
| DEF-02 | Phase 18 | COMPLETE | `tests/services/test_text_field_remediation.py` proves the known `дости́чь` correction to "to achieve, to attain, to reach". |
| TRNS-01 | Phase 18 | COMPLETE | `tests/services/test_text_validation.py` and `tests/services/test_generate_text_items.py` prove sentence Translation mismatch gates. |
| TMPL-01 | Phase 19 | COMPLETE | `tests/integration/test_v13_normal_template_export_contract.py` proves APKG/CSV/TSV normal exports omit `Front of Card`. |
| TMPL-02 | Phase 19 | COMPLETE | `tests/integration/test_v13_normal_template_export_contract.py` proves normal sentence-audio responsive layout selectors are exported. |
| TMPL-03 | Phase 19 | COMPLETE | `tests/integration/test_v13_normal_template_export_contract.py`, `tests/integration/test_highlight_export_artifacts.py`, and `tests/integration/test_russian_phoneme_template_refresh_flow.py` prove template isolation. |
| AUD-01 | Phase 20 | COMPLETE | `tests/services/test_audio_integrity.py` and `tests/services/test_generate_audio_items.py` prove mismatched `word_audio` detection and regeneration boundaries. |
| AUD-02 | Phase 20 | COMPLETE | `tests/services/test_assemble_export_cards.py` and `tests/integration/test_export_job_flow.py` prove export blocking for unrepaired word-audio mismatches. |
| VAL-01 | Phase 21 | COMPLETE | `tests/services/test_v13_validation.py` proves normalized IPA, Definition, Translation, template, and word-audio validators. |
| VAL-02 | Phase 21 | COMPLETE | `tests/integration/test_v13_normalized_issue_fixtures.py` executes `tests/fixtures/v13/card_issues_normalized_cases.json`. |
| VAL-03 | Phase 21 | PASS | `tests/integration/test_v13_final_milestone_evidence.py` and `tests/integration/test_v13_existing_modes_regression_evidence.py` prove final evidence and mode isolation. |

Coverage signal: **15/15** v1.3 requirements are COMPLETE or PASS.

## Commands Run

Focused evidence commands used across Phases 17-21:

| Area | Runnable command reference | Signal |
|------|----------------------------|--------|
| Audit behavior | `python -m pytest tests/cli/test_audit_deck_command.py tests/services/test_deck_audit_reader.py tests/services/test_deck_audit_reports.py tests/domain/test_deck_audit.py -q` | APKG audit reports are reproducible and non-mutating. |
| IPA and Definition remediation | `python -m pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py tests/services/test_assemble_export_cards.py -q` | IPA-only and semantic Definition corrections are enforced before export. |
| Translation correction | `python -m pytest tests/services/test_text_validation.py tests/services/test_generate_text_items.py -q` | Sentence Translation mismatches route to repair or review. |
| Normal export and responsive template | `python -m pytest tests/integration/test_v13_normal_template_export_contract.py tests/integration/test_highlight_export_artifacts.py tests/integration/test_russian_phoneme_template_refresh_flow.py -q` | Normal APKG/CSV/TSV contract and template isolation are verified. |
| Word-audio integrity | `python -m pytest tests/integration/test_export_job_flow.py tests/services/test_assemble_export_cards.py tests/services/test_generate_audio_items.py tests/services/test_audio_integrity.py -q` | Mismatched WORD audio is regenerated or blocked before export. |
| Shared v1.3 validators | `python -m pytest tests/services/test_v13_validation.py -q` | The shared v1.3 validation facade emits stable normalized issue types. |
| Normalized fixtures | `python -m pytest tests/integration/test_v13_normalized_issue_fixtures.py -q` | Synthetic fixture cases execute through the shared validation facade. |
| Existing mode isolation | `python -m pytest tests/integration/test_v13_existing_modes_regression_evidence.py -q` | frequency, word-list, kindle-highlights, and Russian phonetics contracts remain isolated. |
| Final milestone evidence scanner | `python -m pytest tests/integration/test_v13_final_milestone_evidence.py tests/integration/test_v13_existing_modes_regression_evidence.py tests/integration/test_v13_normalized_issue_fixtures.py -q` | Final artifact coverage, command references, privacy safety, and VAL-03 evidence pass. |

## Pass Signals

- Phase 17 focused audit suite reported `16 passed` and generated known-deck local audit reports under ignored runtime storage.
- Phase 18 focused suites reported passing IPA, Definition, and Translation remediation checks before export/review boundaries.
- Phase 19 integrated suite reported normal APKG/CSV/TSV exports without `Front of Card`, with sentence-audio layout CSS and isolated highlight/manual/phonetics templates.
- Phase 20 focused suite reported `38 passed` for generation-time repair and fail-closed export gates when `word_audio` metadata does not match `Word`.
- Phase 21 Plan 01 service suite passed for VAL-01 normalized validators.
- Phase 21 Plan 02 fixture suite passed for VAL-02 executable normalized issue cases.
- Phase 21 Plan 03 suite passes for VAL-03 final milestone and existing-mode regression evidence.
- Combined requirement result: **15/15** v1.3 requirements have scanner-readable COMPLETE or PASS rows.

## Mode Isolation

| Mode | Expected contract | Regression proof |
|------|-------------------|------------------|
| frequency | Revised normal fields: `SortIndex`, `word`, `IPA`, `Definitions`, `Example Sentence`, `Translation`, `word_audio`, `sentence_audio`, blank `Image`; no `Front of Card` export field. | `tests/integration/test_v13_existing_modes_regression_evidence.py` and `tests/integration/test_v13_normal_template_export_contract.py` |
| word-list | Manual/highlight-style fields with `Word`, `Definition`, `sentence_audio`, blank `Image`; no `Translation` or `word_audio` export field. | `tests/integration/test_v13_existing_modes_regression_evidence.py` |
| kindle-highlights | Dedicated `Multilang::Highlight Card` note type, source-profile field tuple, no normal `word` field, no `Translation`, no `word_audio`. | `tests/integration/test_v13_existing_modes_regression_evidence.py` and `tests/integration/test_highlight_export_artifacts.py` |
| Russian phonetics | Dedicated Russian phonetics note contract using `PHONEME_FIELD_NAMES`; no normal/highlight learner field leakage. | `tests/integration/test_v13_existing_modes_regression_evidence.py` and `tests/integration/test_russian_phoneme_template_refresh_flow.py` |

## Privacy Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| No committed private deck content | PASS | The artifact references command outputs and summaries only. Private local audit reports remain in ignored runtime storage. |
| No absolute user paths | PASS | Scanner test blocks common absolute path markers and this file uses repository-relative paths. |
| No WebDAV secrets | PASS | Scanner test blocks WebDAV credential marker strings. |
| No private reading text | PASS | Scanner test blocks known private reading markers used in source-aware privacy tests. |
| Synthetic test fixtures only | PASS | VAL-02 and VAL-03 evidence tests use synthetic rows, temp media, and fixture metadata. |

## Remaining Caveats

- Focused milestone evidence is authoritative for v1.3 closure. Broad full-suite collection drift from removed private runtime template adapters remains known follow-up debt from `.planning/PROJECT.md`.
- The known-deck audit reports are intentionally stored outside committed artifacts because audit findings may contain private deck field text.
- Live Azure playback quality remains outside this scanner evidence; deterministic audio integrity is proven through stored synthesis metadata and local fakes.
