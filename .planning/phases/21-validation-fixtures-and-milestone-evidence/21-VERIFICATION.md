---
phase: 21-validation-fixtures-and-milestone-evidence
verified: 2026-05-15T14:05:22Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 8/9
  gaps_closed:
    - "Whitespace-formatted {{ sentence_audio }} references now trigger sentence_audio_layout validation and are covered by fixture/service tests."
  gaps_remaining: []
  regressions: []
---

# Phase 21: Validation Fixtures and Milestone Evidence Verification Report

**Phase Goal:** User receives repeatable validation and evidence that the normalized issue catalog is covered and existing deck modes remain safe.  
**Verified:** 2026-05-15T14:05:22Z  
**Status:** passed  
**Re-verification:** Yes — after gap closure plan 21-04

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can run validators for IPA word repetition, banned Definition patterns, Translation/example mismatch, `word_audio`/`Word` mismatch, and dangling template fields. | ✓ VERIFIED | `src/multilang/services/v13_validation.py` exports `V13ValidationIssueType`, `validate_v13_card`, and `validate_v13_template_contract`; it delegates Definition, Translation, template reference, and audio checks to existing services. Focused Phase 21 suite passed: `18 passed in 0.59s`. |
| 2 | User receives normalized issue types and field-specific diagnostics without private deck excerpts or absolute paths. | ✓ VERIFIED | `V13ValidationIssue` is immutable and bounds messages; tests assert sensitive word/path details are absent from IPA issue messages; final evidence scanner blocks absolute path and secret markers. |
| 3 | User gets regression fixtures covering the normalized examples from `card_issues_normalized.md`. | ✓ VERIFIED | `tests/fixtures/v13/card_issues_normalized_cases.json` covers all eight summary action groups from lines 123-130, including `sentence_audio_layout_bad_whitespace_reference` for `{{ sentence_audio }}`. |
| 4 | User can rerun one fixture suite and see each known bad example fail with the expected normalized validator issue. | ✓ VERIFIED | `tests/integration/test_v13_normalized_issue_fixtures.py` loads every JSON case and asserts exact issue-type output from `validate_v13_card` / `validate_v13_template_contract`; included in passing focused run. |
| 5 | User receives final milestone evidence proving audit behavior, text corrections, normal-card export contract, and word-audio integrity. | ✓ VERIFIED | `21-V13-MILESTONE-EVIDENCE.md` contains 15/15 requirement rows, command references, pass signals, and evidence links for Phases 17-21. |
| 6 | User receives regression evidence that frequency, custom word-list, highlight, and phonetics deck behavior remains unaffected outside intended normal-card changes. | ✓ VERIFIED | `tests/integration/test_v13_existing_modes_regression_evidence.py` asserts frequency, word-list/manual, kindle-highlight, and Russian phonetics field/model boundaries and passed in the focused suite. |
| 7 | User can rerun scanner-readable tests that verify evidence coverage and privacy safety. | ✓ VERIFIED | `tests/integration/test_v13_final_milestone_evidence.py` checks required headings, all 15 requirement IDs, command references, mode names, `15/15`, and forbidden privacy markers. |
| 8 | VAL-01, VAL-02, and VAL-03 requirement IDs are accounted for against `.planning/REQUIREMENTS.md`. | ✓ VERIFIED | `.planning/REQUIREMENTS.md` maps VAL-01, VAL-02, and VAL-03 to Phase 21; plan frontmatter claims exactly these IDs across 21-01 through 21-04; final evidence includes all three rows. |
| 9 | Sentence-audio layout validation cannot be bypassed by valid Anki template reference formatting. | ✓ VERIFIED | `validate_v13_template_contract` now uses `re.search(r"{{\s*sentence_audio\s*}}", template.front + template.back)`. Direct spot-check with missing selectors returned `['sentence_audio_layout']`. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/multilang/services/v13_validation.py` | Reusable v1.3 validator facade over text, template, and audio checks | ✓ VERIFIED | Exists, substantive, imported by tests, delegates to real validators, and contains whitespace-tolerant sentence-audio reference detection at lines 130-141. |
| `tests/services/test_v13_validation.py` | Focused VAL-01 and gap-closure branch coverage | ✓ VERIFIED | Covers IPA, Definition, Translation, word audio, dangling template field, whitespace sentence-audio missing selectors, corrected selectors, and dangling-field precedence. |
| `tests/fixtures/v13/card_issues_normalized_cases.json` | Scanner-readable fixture catalog | ✓ VERIFIED | Valid JSON; contains source document, coverage rows for all eight normalized groups, synthetic bad/corrected cases, and the whitespace sentence-audio regression fixture. |
| `tests/integration/test_v13_normalized_issue_fixtures.py` | Fixture runner against validators | ✓ VERIFIED | Loads the fixture file from disk, constructs card/template/audio inputs, and asserts exact issue-type lists for every case. |
| `.planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md` | Final v1.3 milestone evidence | ✓ VERIFIED | Contains requirement coverage, commands, pass signals, mode isolation, privacy checklist, and caveats. |
| `tests/integration/test_v13_final_milestone_evidence.py` | Scanner-readable evidence validation | ✓ VERIFIED | Verifies headings, 15/15 requirement coverage, command refs, mode refs, and privacy exclusions. |
| `tests/integration/test_v13_existing_modes_regression_evidence.py` | Existing-mode regression evidence | ✓ VERIFIED | Verifies frequency, word-list/manual, highlight, and Russian phonetics source-profile contracts. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/multilang/services/v13_validation.py` | `src/multilang/services/text_field_remediation.py` | `validate_definition_html` | ✓ WIRED | Imported and used in `validate_v13_card`. |
| `src/multilang/services/v13_validation.py` | `src/multilang/services/text_validation.py` | `TextValidationService` | ✓ WIRED | Imported and used with `GeneratedSentence`/`GeneratedTranslation`. |
| `src/multilang/services/v13_validation.py` | `src/multilang/services/audio_integrity.py` | `assert_word_audio_matches_word` | ✓ WIRED | Imported and used when `word_audio_asset` is supplied. |
| `src/multilang/services/v13_validation.py` | template layout rule | `re.search(r"{{\s*sentence_audio\s*}}", template_markup)` | ✓ WIRED | Whitespace-formatted Anki references now flow into `sentence_audio_layout` enforcement. |
| `tests/integration/test_v13_normalized_issue_fixtures.py` | `src/multilang/services/v13_validation.py` | `validate_v13_card`, `validate_v13_template_contract` | ✓ WIRED | Fixture runner imports and calls both functions based on fixture `validator`. |
| `tests/fixtures/v13/card_issues_normalized_cases.json` | `card_issues_normalized.md` | case/source-line metadata | ✓ WIRED | Coverage groups match the eight summary action rows in `card_issues_normalized.md`. |
| `tests/integration/test_v13_final_milestone_evidence.py` | `21-V13-MILESTONE-EVIDENCE.md` | scanner path and regex coverage rows | ✓ WIRED | Test reads the actual evidence artifact and verifies rows/references. |
| `tests/integration/test_v13_existing_modes_regression_evidence.py` | export/model source contracts | constants and model builders | ✓ WIRED | Imports field-name constants and model builders to assert source-profile contracts. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `validate_v13_card` | `row`, `word_audio_asset` | `ExportCardRow`, `AudioAssetRecord`, existing validators | Yes | ✓ FLOWING — delegates to real text/audio validators and emits normalized issues from actual validation outcomes. |
| `validate_v13_template_contract` | `template`, `field_names` | `CardTemplate`, field tuple, `validate_template_references` | Yes | ✓ FLOWING — dangling field validation runs first; parsed sentence-audio references then enforce required layout selectors. |
| `test_v13_normalized_issue_fixtures.py` | `catalog["cases"]` | JSON fixture file | Yes | ✓ FLOWING — fixtures are loaded from disk and executed through validators. |
| `test_v13_final_milestone_evidence.py` | `content` | Evidence Markdown file | Yes | ✓ FLOWING — scanner reads the actual committed artifact. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Fixture catalog is valid JSON | `python -m json.tool tests/fixtures/v13/card_issues_normalized_cases.json` | Exit 0 | ✓ PASS |
| Focused Phase 21 validation/evidence suites pass | `python -m pytest tests/services/test_v13_validation.py tests/integration/test_v13_normalized_issue_fixtures.py tests/integration/test_v13_final_milestone_evidence.py tests/integration/test_v13_existing_modes_regression_evidence.py -q` | `18 passed in 0.59s` | ✓ PASS |
| Whitespace-formatted `sentence_audio` reference with missing layout selectors is rejected | Python snippet constructing `CardTemplate(front='<div>{{Example Sentence}}</div><div>{{ sentence_audio }}</div>', ...)` and calling `validate_v13_template_contract(...)` | Returned `['sentence_audio_layout']` | ✓ PASS |
| Full repository pytest collection | `python -m pytest -q` | `454 passed, 3 failed in 214.21s` | ⚠️ WARNING — failures are outside the focused Phase 21 gate: missing v1.2 evidence artifact, `.gitignore` expectation drift, and an older Russian phoneme CSS assertion. Focused Phase 21 and mode-isolation checks passed. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VAL-01 | 21-01-PLAN.md, 21-04-PLAN.md | User can run validators for IPA repetition, banned Definition patterns, Translation/example mismatch, `word_audio`/`Word` mismatch, dangling template fields, and the tightened sentence-audio layout edge. | ✓ SATISFIED | `v13_validation.py` implements the facade and whitespace detector; `tests/services/test_v13_validation.py` passes in focused run. |
| VAL-02 | 21-02-PLAN.md, 21-04-PLAN.md | User gets regression fixtures covering normalized issue examples from `card_issues_normalized.md`, including valid whitespace Anki field formatting. | ✓ SATISFIED | Fixture catalog includes all eight coverage groups plus `sentence_audio_layout_bad_whitespace_reference`; fixture runner passes. |
| VAL-03 | 21-03-PLAN.md | User gets final milestone evidence proving audit, corrections, normal-card export contract, and unaffected existing modes. | ✓ SATISFIED | Evidence artifact and scanner/mode regression tests exist and pass in focused run. |

No orphaned Phase 21 requirements found in `.planning/REQUIREMENTS.md`; VAL-01, VAL-02, and VAL-03 are all claimed by plan frontmatter and final evidence.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/multilang/services/v13_validation.py` | 142 | `return []` | ℹ️ Info | Intentional clean-result path after validation checks; not a stub because preceding branches populate issues from real validators. |

### Human Verification Required

None for Phase 21 goal achievement. This phase produced deterministic validators, fixture execution, and scanner-readable evidence rather than new visual UI behavior.

### Gaps Summary

No blocking gaps remain. The prior verifier gap is closed: whitespace-formatted `{{ sentence_audio }}` references now trigger the same `sentence_audio_layout` validation as literal `{{sentence_audio}}`, and regression coverage exists at both fixture and service levels. VAL-01, VAL-02, and VAL-03 are accounted for against `.planning/REQUIREMENTS.md`.

---

_Verified: 2026-05-15T14:05:22Z_  
_Verifier: the agent (gsd-verifier)_
