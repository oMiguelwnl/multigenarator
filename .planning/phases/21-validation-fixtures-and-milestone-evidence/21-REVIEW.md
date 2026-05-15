---
phase: 21-validation-fixtures-and-milestone-evidence
reviewed: 2026-05-15T13:39:03Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - src/multilang/services/v13_validation.py
  - src/multilang/services/text_field_remediation.py
  - tests/services/test_v13_validation.py
  - tests/fixtures/v13/card_issues_normalized_cases.json
  - tests/integration/test_v13_normalized_issue_fixtures.py
  - tests/integration/test_v13_final_milestone_evidence.py
  - tests/integration/test_v13_existing_modes_regression_evidence.py
  - .planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md
findings:
  critical: 0
  warning: 1
  info: 0
  total: 1
status: issues_found
---

# Phase 21: Code Review Report

**Reviewed:** 2026-05-15T13:39:03Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the Phase 21 validation facade, text remediation updates, normalized fixtures, milestone evidence scanners, mode-isolation tests, and evidence artifact. The focused Phase 21 test command passed (`15 passed`). One validator edge case remains: sentence-audio layout validation can be bypassed when the Anki field reference uses valid whitespace formatting.

## Warnings

### WR-01: Sentence-audio layout check misses whitespace-formatted Anki references

**File:** `src/multilang/services/v13_validation.py:130`
**Issue:** `validate_v13_template_contract` only runs the sentence-audio layout selector check when the template contains the literal substring `{{sentence_audio}}`. Anki references with whitespace such as `{{ sentence_audio }}` are accepted by `validate_template_references`, but this condition skips the layout validation, so a malformed normal template can pass without the expected `sentence_audio_layout` issue.
**Fix:** Detect `sentence_audio` with the same reference parsing semantics used by template validation, or use a whitespace-tolerant regex before enforcing selectors. For example:

```python
template_markup = template.front + template.back
if re.search(r"{{\s*sentence_audio\s*}}", template_markup):
    template_surface = " ".join((template.front, template.back, template.css))
    required_selectors = {"exampleSentenceLine", "exampleSentenceText", "sentenceAudioButton"}
    if not required_selectors <= set(re.findall(r"[A-Za-z][A-Za-z0-9_-]+", template_surface)):
        return [
            _issue(
                field_name="template",
                issue_type=V13ValidationIssueType.SENTENCE_AUDIO_LAYOUT,
                message="sentence_audio must stay beside Example Sentence using the normal responsive layout selectors.",
            )
        ]
```

Also add a regression fixture/test with `{{ sentence_audio }}` and missing layout selectors.

---

_Reviewed: 2026-05-15T13:39:03Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
