---
phase: quick-030-unify-dark-card-layouts
runtime: opencode
assurance: self_checked
verified: 2026-07-24T19:59:06Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
delivery_posture: repo_only
evidence_contract:
  required_kinds: [code, test]
  recommended_kinds: [human]
  observed_kinds: [code, test]
  missing_kinds: []
re_verification:
  previous_status: human_needed
  previous_score: 5/5
  gaps_closed:
    - "User-directed scope correction verified: Japanese frequency and Kana are restored to their repository/HEAD baseline and retain their original light/night purple palettes."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Render all five template families front and back in a browser and native Anki Desktop/mobile clients."
    expected: "Normal, shared phoneme, and Mandarin render with the revised always-dark design and panel-contained answers; Japanese frequency and Kana retain their original light/night purple designs, controls, links, and media blocks."
    why_human: "No browser-rendering artifact, screenshot, Anki Desktop run, or mobile Anki observation exists; source and generated-model checks cannot establish visual acceptance."
<git_delivery_check>
  branch: "Monarch"
  commits_ahead_of_main: unknown
  pr_state: unknown
</git_delivery_check>
---

# Quick Task 030: Corrected Dark Card Scope Verification Report

**Corrected Task Goal:** Apply the always-dark blue design and answer-panel containment only to normal, shared phoneme, and Mandarin; keep Japanese frequency and Kana at their original production designs; and preview all five front/back pairs accurately.
**Verified:** 2026-07-24T19:59:06Z
**Status:** human_needed
**Re-verification:** Yes — after explicit user-directed scope correction

## Verification Basis

- Plan: `.planning/quick/030-unify-dark-card-layouts/030-PLAN.md`
- The corrected summary and proof bundle were inspected, but their claims were treated as untrusted and checked against current source, repository-index blob hashes, generated models, relevant suites, and preview structure.
- Plan runtime/assurance: missing / missing; summary runtime/assurance: opencode / self_checked; verifier runtime/assurance: opencode / self_checked.
- The summary handoff, scope-change delta, and corrected anti-regression rules were checked explicitly.
- Delivery is repo-only. No browser or native Anki rendering claim is accepted.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Normal, shared phoneme, and Mandarin retain the requested always-dark blue design. | ✓ VERIFIED (source/model) | Generated normal and Mandarin CSS carries the locked dark palette and Mandarin remains prefixed by normal CSS; Russian/Polish/Greek models remain identical and use the same dark palette. Focused assertions pass. |
| 2 | Normal and Mandarin answer translations, and the phoneme sentence translation, remain inside their example panels without reveal drift. | ✓ VERIFIED | Balanced-panel assertions pass; `FrontSide`, hidden translation IDs, reveal scripts, phoneme IIFE/noscript fallback, field references, and audio references remain present. |
| 3 | Japanese frequency and Kana remain exactly at their pre-task repository design. | ✓ VERIFIED | Independent SHA-1 blob comparison after canonical LF normalization matched both working files to their repository index/HEAD baseline entries. Source and generated-model tests confirm original light `#fdf6e3`/white and night purple `#0b0716`/`#171226` palettes. |
| 4 | Japanese/Kana fields, pedagogy, controls, links, and media ordering remain unchanged. | ✓ VERIFIED | Japanese retains the furigana toggle, filters, two audio fields, optional image, meanings, and Jisho/Images/Weblio links. Kana retains recognition/reveal sides and Gif → divider → Romaji/Audio → Picture → Strokes → Mnemonic. Dedicated suites pass. |
| 5 | The preview accurately shows three revised dark families and two original Japanese families across all front/back pairs. | ✓ VERIFIED (source only) | Exactly five front and five back articles exist. Normal/phoneme/Mandarin use the dark shell; both Japanese articles use `jp-original`; both Kana articles use `kana-original`; preview copy and CSS explicitly distinguish the corrected mixed scope. |

**Score:** 5/5 must-haves verified

### Required Artifacts

| Artifact | Exists | Substantive | Wired | Status / details |
|----------|--------|-------------|-------|------------------|
| `src/multilang/templates/normal_card.md` | Yes | Yes | Yes | ✓ Loaded by normal source profiles; panel-contained translation and always-dark final CSS. |
| `src/multilang/templates/russian_phoneme_card.md` | Yes | Yes | Yes | ✓ `_load_phoneme_template()` feeds all three phoneme model builders identically. |
| `src/multilang/templates/mandarin_card.md` | Yes | Yes | Yes | ✓ Loader uses its markup and prefixes its CSS with complete normal CSS. |
| `src/multilang/templates/japanese_card.md` | Yes | Yes | Yes | ✓ Baseline-identical after EOL normalization; original palette and dedicated/integrated wiring verified. |
| `src/multilang/templates/japanese_kana_card.md` | Yes | Yes | Yes | ✓ Baseline-identical after EOL normalization; original palette and imported/generated wiring verified. |
| `modified_templates_preview.html` | Yes | Yes | Standalone | ✓ Ten labeled states accurately distinguish three dark families from two original Japanese families. |
| `.planning/quick/030-unify-dark-card-layouts/UI-PROOF.md` | Yes | Yes | Yes | ✓ Corrected mixed-scope proof metadata with 10 observations and bounded claims. |
| `tests/services/test_export_anki_package.py` | Yes | Yes | Yes | ✓ The adjacent model assertion matches panel-contained markup and still checks hidden translation, `FrontSide`, reveal script, and dark CSS. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `normal_card.md` | `mandarin_card.md` | `card_template_loader` CSS composition | ✓ WIRED | Runtime assertion confirms Mandarin CSS starts with normal CSS. |
| `russian_phoneme_card.md` | Russian/Polish/Greek models | `_load_phoneme_template()` | ✓ WIRED | Templates and CSS are byte-equal across generated models. |
| `japanese_card.md` | Japanese frequency paths | integrated and dedicated loaders | ✓ WIRED | Both parse the same file; generated model retains toggle/fields/links. |
| `japanese_kana_card.md` | imported/generated Kana decks | `build_kana_model()` | ✓ WIRED | Exact field and media conditional order verified. |

### Data-Flow Trace (Level 4)

Static Anki templates do not fetch runtime data. The relevant flow is field contract → parsed template → generated `genanki.Model`; generated-model inspection verified that path for all five families. Live field substitution and rendering remain part of the human gate.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Focused quick-030 contracts | `uv run pytest tests/services/test_card_template_loader.py -q` | 24 passed | ✓ PASS |
| Dedicated phoneme/Japanese/Kana suites | Plan's four-suite pytest command | 29 passed | ✓ PASS |
| Corrected combined focused suites | Six relevant test modules | 78 passed | ✓ PASS |
| Generated model wiring and palette scope | Independent model inspection | Three dark families + original Japanese/Kana palettes OK | ✓ PASS |
| Preview pair count and mixed-scope classes | Independent source validation | Five pairs; two `jp-original` and two `kana-original` articles | ✓ PASS |
| UI proof structure | Independent fenced-JSON validation | Required keys, 10 observations, artifacts and privacy metadata valid | ✓ PASS |
| Quick-029 regression suite | `uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q` | 60 passed | ✓ PASS |
| Patch hygiene | Prior scoped verification evidence | No whitespace errors were reported before this no-Git re-verification | ✓ PASS |

No Git command was used in this re-verification. Japanese/Kana baseline identity was checked read-only by comparing canonicalized working-file blob hashes with the repository index entries; prior verification had established that the index was unstaged relative to HEAD.

### UI Proof Slot Comparison

| Slot | Status | Evidence |
|------|--------|----------|
| `five-template-browser-preview` | satisfied at source/test boundary | Ten articles and ten corrected observations distinguish three revised dark families from original Japanese/Kana. No rendered-browser claim is made. |
| `native-anki-five-template-acceptance` | missing human evidence | No Desktop/mobile observations or rendering artifacts exist. This remains a human gate and cannot be waived by static HTML. |

### Requirements Coverage

Quick mode declares no roadmap requirement IDs. The user-directed correction supersedes the original five-family dark-style truth. The five corrected observable truths above cover final scope, preservation, preview accuracy, and UI claim boundaries.

### Anti-Patterns and Scope

| Location | Finding | Severity | Impact |
|----------|---------|----------|--------|
| `tests/services/test_export_anki_package.py:179` | Exact markup expectation follows the semantic panel wrapper | — | Hidden/reveal and CSS assertions remain. |
| Three modified production templates | No TODO/FIXME/placeholder/stub patterns found | — | None |
| Japanese/Kana templates | Repository-baseline blob hashes match after EOL normalization | — | No quick-030 semantic or production diff. |

Disconfirmation check: semantic CSS tests do not compute browser styles, and source checks do not execute Anki's reveal/furigana/native replay behavior. This is why automated closure is complete while visual acceptance remains human-needed.

## Human Verification Still Required

### 1. Browser and Native Anki Five-Family Acceptance

**Test:** Inspect normal, shared phoneme, Mandarin, Japanese frequency, and Kana front/back in a browser, Anki Desktop, and a representative portrait-mobile Anki client.

**Expected:** Normal/phoneme/Mandarin show the revised dark layout and answer containment. Japanese frequency and Kana retain their original light/night purple appearance and existing controls/media behavior.

**Why human:** There are no screenshots, browser runtime observations, or native Anki artifacts. This gate remains after automated verification of the corrected scope.

## Gaps Summary

No automated implementation or regression gaps remain under the corrected scope. Japanese frequency and Kana match the repository baseline after EOL normalization and their original-palette tests pass. Normal, phoneme, and Mandarin retain the dark/panel changes. The 60-test quick-029 suite, 24-test quick-030 suite, 29-test dedicated suite, and 78-test corrected combined suite all pass. Exact browser and native Anki visual acceptance remains the sole human escalation gate.

Git delivery metadata is incomplete because this repository has no local `main` ref and `gh` is unavailable. The current branch is `Monarch`; no files were staged, committed, reverted, or cleaned during verification.

---

_Verified: 2026-07-24T19:59:06Z_
_Verifier: the agent (gsd-verifier)_
