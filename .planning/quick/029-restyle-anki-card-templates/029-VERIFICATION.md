---
phase: quick-029-restyle-anki-card-templates
runtime: opencode
assurance: self_checked
verified: 2026-07-23T18:40:18Z
status: human_needed
score: 4/4 must-haves verified
overrides_applied: 0
delivery_posture: repo_only
evidence_contract:
  required_kinds: [code]
  recommended_kinds: [test, runtime, human]
  observed_kinds: [code, test, runtime]
  missing_kinds: []
human_verification:
  - test: "Render representative normal, shared phoneme, and Mandarin cards front and back in Anki Desktop and one mobile Anki client (12 observations total)."
    expected: "All three templates match their approved dark references at desktop and mobile sizes; fields remain readable, native replay controls render correctly, overflow is acceptable, and translations appear only after answer reveal."
    why_human: "No Anki Desktop/mobile runtime screenshots or observations exist; source inspection and generated-model tests cannot prove native fonts, controls, pixels, overflow, or reveal appearance."
---

# Quick Task 029: Restyle Anki Card Templates Verification Report

**Task Goal:** Visually restyle the existing normal, shared phoneme, and Mandarin card templates from the supplied references while preserving filenames and every template contract.
**Verified:** 2026-07-23T18:40:18Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Normal cards follow the centered dark hero source design. | ✓ VERIFIED (source/model) | `normal_card.md:451-593` carries the reference palette, 16px shell, blue top border, shadow, centered 42px hero, example callout, circular replay control, and mobile rule corresponding to `freq_card_hero_dark.html:4-30`; generated model assertions pass. |
| 2 | Shared phoneme cards follow the supplied dark-blue source design. | ✓ VERIFIED (source/model) | `russian_phoneme_card.md:307-443` carries the dark shell, target box, spacing hierarchy, dividers, and native SVG replay treatment corresponding to `phoneme_card_restyle.html:4-37`; runtime inspection confirmed identical Russian/Polish/Greek templates and CSS. |
| 3 | Mandarin cards use the dark Mandarin treatment while retaining normal-plus-Mandarin CSS. | ✓ VERIFIED (source/model) | `mandarin_card.md:69-102` supplies explicit dark Pinyin/Traditional hierarchy; `card_template_loader.py:63-80` composes complete normal CSS before Mandarin CSS. Runtime inspection confirmed identical frequency/word-list models and the base CSS prefix. |
| 4 | Filenames, field references/order, front/back markup, and reveal behavior are unchanged. | ✓ VERIFIED | Independent HEAD comparison found identical content before and after each Styling fence in all three production templates. Focused tests and generated-model inspection confirmed 9 normal fields, 12 Mandarin fields, 9 shared phoneme fields, `FrontSide`, hidden front translations, and reveal scripts. |

**Score:** 4/4 must-haves verified at the repository source/model boundary.

Exact native Anki visual equivalence is deliberately not included in that score and remains the human gate below.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/multilang/templates/normal_card.md` | Dark centered normal-card stylesheet | ✓ VERIFIED | Exists, substantive, loaded by the frequency source profile, and differs from HEAD only inside Styling CSS. |
| `src/multilang/templates/russian_phoneme_card.md` | Dark-blue shared phoneme stylesheet | ✓ VERIFIED | Exists, substantive, loaded by `_load_phoneme_template()`, and differs from HEAD only inside Styling CSS. |
| `src/multilang/templates/mandarin_card.md` | Mandarin dark typography layered over normal CSS | ✓ VERIFIED | Exists, substantive, loaded for Mandarin frequency/word-list models, and differs from HEAD only inside Styling CSS. |

Production-scope check: `git diff --name-only -- src` returned exactly these three template paths. Tests and planning evidence also changed, but no other production file did. There were no staged files. Unrelated pre-existing deletions/untracked files remain in the worktree and were not used as task evidence.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `source_profiles.py` | `normal_card.md` | Frequency profile `template_name="normal_card"` | ✓ WIRED | `card_template_loader.py` parses and returns its front/back/CSS. |
| `card_template_loader.py` | `mandarin_card.md` | Mandarin frequency/word-list branch | ✓ WIRED | Lines 63-80 load Mandarin markup and concatenate `base_template.css` before `mandarin_template.css`. |
| `russian_phoneme_deck.py` | `russian_phoneme_card.md` | `_load_phoneme_template()` | ✓ WIRED | Lines 202-216 inject parsed front/back/CSS into generated models; Russian, Polish, and Greek builders share the path. |

### Data-Flow Trace (Level 4)

Not applicable. These artifacts are static Anki template styles; dynamic field flow is the preserved template contract, exercised by generated-model tests rather than a database/API data source.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Focused template/model regressions | `uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q` | `57 passed in 0.86s` | ✓ PASS |
| Only CSS fences changed in production templates | Python HEAD/current section comparison | All three reported `(prefix unchanged=True, suffix unchanged=True, CSS changed=True)` | ✓ PASS |
| Generated model contracts and shared wiring | Focused `uv run python -c ...` model inspection | `normal=9 fields; mandarin=12 fields+base-prefix; phoneme=9 fields shared ru/pl/el; models OK` | ✓ PASS |
| UI proof metadata | Fenced-JSON parse and required-key check | Valid JSON, 8 observations, `result=human_needed` | ✓ PASS |
| Patch hygiene | `git diff --check` on three templates | No whitespace errors | ✓ PASS |

### Requirements Coverage

Quick mode has no roadmap or requirement IDs. Coverage was assessed directly against the four plan must-haves and the user goal.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No TODO/FIXME/placeholder/stub pattern found in the three target templates | — | None |

Disconfirmation note: the passing CSS tests validate semantic stylesheet signatures, not computed pixels. They cannot detect Anki-specific font substitution, native replay-control rendering, or viewport overflow; this is why the report does not claim a full visual pass.

## Human Verification Required

### 1. Native Anki Desktop and Mobile Visual Equivalence

**Test:** Generate representative normal, phoneme, and Mandarin cards and inspect each front and back in Anki Desktop and one mobile Anki client (3 templates × 2 sides × 2 runtimes = 12 observations).

**Expected:** The approved dark palette, hierarchy, spacing, responsive width, audio controls, and Mandarin auxiliary lines render acceptably in both clients. Translation stays hidden on the question side and appears on the answer side.

**Why human:** No native Anki screenshots or runtime observations are available. Repository evidence proves source/model fidelity and contract preservation only.

## Gaps Summary

No programmatic implementation gaps were found. The escalation gate remains open solely for native Anki visual acceptance; automated checks cannot resolve that judgment.

---

_Verified: 2026-07-23T18:40:18Z_
_Verifier: the agent (gsd-verifier)_
