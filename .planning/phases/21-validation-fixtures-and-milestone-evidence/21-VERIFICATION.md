---
phase: 21-validation-fixtures-and-milestone-evidence
verified: 2026-05-15T13:42:07Z
status: gaps_found
score: 8/9 must-haves verified
overrides_applied: 0
gaps:
  - truth: "User gets regression coverage for the normalized sentence_audio layout issue across valid Anki field-reference formatting."
    status: partial
    reason: "validate_v13_template_contract only enforces sentence_audio layout selectors when the template contains the literal substring '{{sentence_audio}}'; valid whitespace-formatted references such as '{{ sentence_audio }}' pass template reference validation but bypass the layout check."
    artifacts:
      - path: "src/multilang/services/v13_validation.py"
        issue: "Line 130 checks for literal '{{sentence_audio}}' instead of using whitespace-tolerant Anki reference parsing."
      - path: "tests/integration/test_v13_normalized_issue_fixtures.py"
        issue: "Fixture suite covers the literal sentence_audio reference but not the whitespace-formatted valid Anki reference edge case."
    missing:
      - "Use a whitespace-tolerant sentence_audio reference detector, e.g. re.search(r'{{\\s*sentence_audio\\s*}}', template.front + template.back), before enforcing layout selectors."
      - "Add a regression fixture/test where '{{ sentence_audio }}' is present without required layout selectors and must emit sentence_audio_layout."
---

# Phase 21: Validation Fixtures and Milestone Evidence Verification Report

**Phase Goal:** User receives repeatable validation and evidence that the normalized issue catalog is covered and existing deck modes remain safe.  
**Verified:** 2026-05-15T13:42:07Z  
**Status:** gaps_found  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can run validators for IPA word repetition, banned Definition patterns, Translation/example mismatch, `word_audio`/`Word` mismatch, and dangling template fields. | ✓ VERIFIED | `src/multilang/services/v13_validation.py` exports `V13ValidationIssueType`, `validate_v13_card`, and `validate_v13_template_contract`; it delegates Definition, Translation, template reference, and audio checks to existing services. Focused Phase 21 tests passed: `15 passed in 0.53s`. |
| 2 | User receives normalized issue types and field-specific diagnostics without private deck excerpts or absolute paths. | ✓ VERIFIED | `V13ValidationIssue` is immutable and bounds messages; tests assert private word/path details are absent from IPA issue messages; final evidence scanner blocks absolute path and secret markers. |
| 3 | User gets regression fixtures covering the normalized examples from `card_issues_normalized.md`. | ⚠️ PARTIAL | `tests/fixtures/v13/card_issues_normalized_cases.json` covers all eight summary action groups and executable tests assert coverage. However the sentence-audio layout validator misses valid whitespace-formatted `{{ sentence_audio }}` references, so normalized layout coverage is incomplete for Anki-valid formatting. |
| 4 | User can rerun one fixture suite and see each known bad example fail with the expected normalized validator issue. | ✓ VERIFIED | `tests/integration/test_v13_normalized_issue_fixtures.py` loads every fixture, builds card/template/audio inputs, and asserts exact `issue_type.value` lists. The suite passed in the focused run. |
| 5 | User receives final milestone evidence proving audit behavior, text corrections, normal-card export contract, and word-audio integrity. | ✓ VERIFIED | `21-V13-MILESTONE-EVIDENCE.md` contains 15/15 requirement rows, command references, pass signals, and evidence links for Phases 17-21. |
| 6 | User receives regression evidence that frequency, custom word-list, highlight, and phonetics deck behavior remains unaffected outside intended normal-card changes. | ✓ VERIFIED | `tests/integration/test_v13_existing_modes_regression_evidence.py` asserts frequency, word-list/manual, kindle-highlight, and Russian phonetics field/model boundaries. |
| 7 | User can rerun scanner-readable tests that verify evidence coverage and privacy safety. | ✓ VERIFIED | `tests/integration/test_v13_final_milestone_evidence.py` checks required headings, all 15 requirement IDs, command references, mode names, `15/15`, and forbidden privacy markers. |
| 8 | VAL-01, VAL-02, and VAL-03 requirement IDs are accounted for against `.planning/REQUIREMENTS.md`. | ✓ VERIFIED | REQUIREMENTS.md maps VAL-01, VAL-02, and VAL-03 to Phase 21; plan frontmatter claims exactly these IDs across 21-01, 21-02, and 21-03; final evidence includes all three rows. |
| 9 | Sentence-audio layout validation cannot be bypassed by valid Anki template reference formatting. | ✗ FAILED | Spot-check with a malformed template containing `{{ sentence_audio }}` returned `[]` issues, confirming code review finding WR-01. |

**Score:** 8/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/multilang/services/v13_validation.py` | Reusable v1.3 validator facade over text, template, and audio checks | ⚠️ PARTIAL | Substantive and wired, but sentence-audio layout detection uses literal `{{sentence_audio}}` and misses valid whitespace references. |
| `tests/services/test_v13_validation.py` | Focused VAL-01 branch coverage | ✓ VERIFIED | Covers IPA, Definition, Translation, word audio, dangling template field, and project normal template checks. |
| `tests/fixtures/v13/card_issues_normalized_cases.json` | Scanner-readable fixture catalog | ✓ VERIFIED | Contains `source_document`, eight coverage groups, bad/corrected cases, source lines, expected issue types, and pass expectations. |
| `tests/integration/test_v13_normalized_issue_fixtures.py` | Fixture runner against validators | ⚠️ PARTIAL | Substantive and wired to validators, but lacks the whitespace-formatted sentence_audio layout regression noted above. |
| `.planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md` | Final v1.3 milestone evidence | ✓ VERIFIED | Contains requirement coverage, commands, pass signals, mode isolation, privacy checklist, and caveats. |
| `tests/integration/test_v13_final_milestone_evidence.py` | Scanner-readable evidence validation | ✓ VERIFIED | Verifies headings, 15/15 requirement coverage, command refs, mode refs, and privacy exclusions. |
| `tests/integration/test_v13_existing_modes_regression_evidence.py` | Existing-mode regression evidence | ✓ VERIFIED | Verifies frequency, word-list/manual, highlight, and Russian phonetics contracts. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/multilang/services/v13_validation.py` | `text_field_remediation.py` | `validate_definition_html` | ✓ WIRED | Imported and used in `validate_v13_card`. |
| `src/multilang/services/v13_validation.py` | `text_validation.py` | `TextValidationService` | ✓ WIRED | Imported and used with `GeneratedSentence`/`GeneratedTranslation`. |
| `src/multilang/services/v13_validation.py` | `audio_integrity.py` | `assert_word_audio_matches_word` | ✓ WIRED | Imported and used when `word_audio_asset` is supplied. |
| `tests/integration/test_v13_normalized_issue_fixtures.py` | `src/multilang/services/v13_validation.py` | `validate_v13_card`, `validate_v13_template_contract` | ✓ WIRED | Fixture runner imports and calls both functions based on `validator` type. |
| `tests/fixtures/v13/card_issues_normalized_cases.json` | `card_issues_normalized.md` | case/source-line metadata | ✓ WIRED | Coverage groups match the eight summary action lines 123-130. |
| `tests/integration/test_v13_final_milestone_evidence.py` | `21-V13-MILESTONE-EVIDENCE.md` | scanner path and regex coverage rows | ✓ WIRED | Test reads evidence artifact and verifies required rows/references. |
| `tests/integration/test_v13_existing_modes_regression_evidence.py` | export/model source contracts | constants and model builders | ✓ WIRED | Imports field-name constants and model builders to assert actual source-profile contracts. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `validate_v13_card` | `row`, `word_audio_asset` | `ExportCardRow`, `AudioAssetRecord`, existing validators | Yes | ✓ FLOWING — delegates to real text/audio validators and emits normalized issues from actual validation outcomes. |
| `validate_v13_template_contract` | `template`, `field_names` | `CardTemplate`, field tuple, `validate_template_references` | Partial | ⚠️ HOLLOW EDGE — dangling field validation flows, but sentence_audio layout enforcement is gated by literal substring rather than parsed reference semantics. |
| `test_v13_normalized_issue_fixtures.py` | `catalog["cases"]` | JSON fixture file | Yes | ✓ FLOWING — fixtures are loaded from disk and executed through validators. |
| `test_v13_final_milestone_evidence.py` | `content` | Evidence Markdown file | Yes | ✓ FLOWING — scanner reads the actual committed artifact. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Focused Phase 21 suites pass | `python -m pytest tests/services/test_v13_validation.py tests/integration/test_v13_normalized_issue_fixtures.py tests/integration/test_v13_final_milestone_evidence.py tests/integration/test_v13_existing_modes_regression_evidence.py -q` | `15 passed in 0.53s` | ✓ PASS |
| Whitespace-formatted `sentence_audio` reference with missing layout selectors is rejected | Python snippet constructing `CardTemplate(front='<div>{{Example Sentence}}</div><div>{{ sentence_audio }}</div>', ...)` and calling `validate_v13_template_contract(...)` | Returned `[]` issue types | ✗ FAIL |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VAL-01 | 21-01-PLAN.md | User can run validators for IPA repetition, banned Definition patterns, Translation/example mismatch, `word_audio`/`Word` mismatch, and dangling template fields. | ✓ SATISFIED | `v13_validation.py` implements facade and `tests/services/test_v13_validation.py` passes. |
| VAL-02 | 21-02-PLAN.md | User gets regression fixtures covering normalized issue examples from `card_issues_normalized.md`. | ⚠️ PARTIAL | Fixture catalog and runner exist and pass, but sentence_audio layout coverage has the whitespace-reference bypass gap. |
| VAL-03 | 21-03-PLAN.md | User gets final milestone evidence proving audit, corrections, normal-card export contract, and unaffected existing modes. | ✓ SATISFIED | Evidence artifact and scanner/mode regression tests exist and pass. |

No orphaned Phase 21 requirements found in `.planning/REQUIREMENTS.md`; VAL-01, VAL-02, and VAL-03 are all claimed by plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/multilang/services/v13_validation.py` | 130 | Literal `"{{sentence_audio}}" in template.front + template.back` | 🛑 Blocker | Valid Anki reference formatting with whitespace bypasses normalized sentence-audio layout validation. |

### Human Verification Required

None required to identify the blocking automated gap. After the whitespace-reference gap is fixed, visual confirmation of sentence-audio placement at desktop/mobile widths remains recommended for UI confidence, but the current phase is blocked first by the deterministic validator gap.

### Gaps Summary

Phase 21 substantially delivered the validator facade, executable fixture catalog, final evidence artifact, and mode-isolation proof. The focused Phase 21 suite passes, and all three requirement IDs are accounted for. However, code review WR-01 is confirmed against the actual code: `validate_v13_template_contract` misses valid whitespace-formatted `sentence_audio` references, allowing malformed normal-card templates to pass without `sentence_audio_layout`. This leaves the normalized issue catalog coverage incomplete and blocks full goal achievement until the detector and fixture coverage are tightened.

---

_Verified: 2026-05-15T13:42:07Z_  
_Verifier: the agent (gsd-verifier)_
