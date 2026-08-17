---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "05"
subsystem: shared-phoneme-and-hangul-template-contracts
runtime: opencode
assurance: self_checked
tags: [genanki, phoneme, korean, hangul, anki-template, compatibility, static-security, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "04"
    provides: Hash-bound review/media gates and the fixed inactive immutable-snapshot boundary
provides:
  - Language-neutral exact nine-field phoneme model, note, mapping, template-validation, and GUID-injection mechanics
  - Compatibility wrappers preserving Russian, Polish, and Greek identities, templates, GUIDs, inventories, audio, exports, and CLI behavior
  - Standalone Korean Hangul template with exactly 15 fields, Korean classes/fonts, hidden graph evidence, and conditional media
affects: [31-06, korean-foundation-export, russian-phoneme, polish-phoneme, greek-phoneme]
tech-stack:
  added: []
  patterns:
    - Shared phoneme mechanics contain no language inventory, provider, synthesis, export, settings, voice, or locale policy
    - Existing language modules retain identity-specific cards and GUID inputs while delegating exact rendering mechanics
    - Korean template identity is standalone and statically allowlisted rather than coupled to the Japanese implementation
key-files:
  created:
    - src/multilang/services/phoneme_deck.py
    - src/multilang/templates/korean_hangul_card.md
    - tests/services/test_phoneme_deck.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-05-SUMMARY.md
  modified:
    - src/multilang/services/russian_phoneme_deck.py
    - tests/services/test_russian_phoneme_deck.py
    - tests/services/test_card_template_loader.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Keep language_code and the legacy Russian/Polish/Greek GUID formula in the compatibility module; the neutral card shape has no language identity."
  - "Permit only class-scoped font-family declarations as additive phoneme CSS, appended after unchanged shared CSS bytes."
  - "Declare all 15 Hangul fields while rendering only learner fields; target, prerequisite, observed, unknown, and policy evidence remains hidden."
patterns-established:
  - "Compatibility proof freezes __all__, IDs, names, fields, template/CSS hashes, inventories, GUID lists, note mappings, APKG paths, and CLI routes."
  - "Static Hangul proof checks exact fields/references/order, conditional media, Korean fonts/classes, executable-markup absence, and Japanese-token absence without making a visual claim."
requirements-advanced: [KHAN-01, KPRO-01]
requirements-completed: []
duration: 17min
completed: 2026-08-05
---

# Phase 31 Plan 05: Shared Phoneme Mechanics and Korean Hangul Template Summary

**An exact nine-field neutral phoneme layer now preserves every shipped Russian/Polish/Greek identity and rendered byte contract, while a standalone 15-field Korean Hangul template exposes Korean-only static structure with hidden graph evidence and safe conditional media.**

## Performance

- **Started:** 2026-08-05T22:07:24Z
- **Completed implementation/state checks:** 2026-08-05T22:24:11Z
- **Duration:** 16m 47s (reported as 17min)
- **Tasks:** 3/3
- **Implementation/test files created:** 3
- **Implementation/test files modified:** 3
- **Planning files updated:** 2, plus this summary
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Extracted `PhonemeCard`, `PhonemeNote`, the exact nine-field tuple/mapping, fixed shared-template parsing and reference validation, model construction, note construction, and stable GUID injection into `phoneme_deck.py`.
- Restricted additive shared-model CSS to class-scoped `font-family` declarations and preserved the base front, back, and CSS bytes exactly when no override is supplied.
- Kept Russian, Polish, and Greek language identity, fixed IDs/names, inventories, voices/locales, synthesis, broad legacy exception behavior, APKG assembly, filenames, exports, and CLI routes in `russian_phoneme_deck.py`.
- Added exact compatibility fingerprints for public exports, model/deck IDs, note type/deck names, templates/CSS, full inventories, GUID lists, first notes, and field mappings.
- Added a standalone Korean-owned Hangul template with exactly 15 declared fields, Korean class names, Portuguese learner labels, explicit Korean fonts, hidden curriculum evidence, conditional GIF/audio/picture/strokes, bounded media, dark canvas, and replay-button reset.
- Proved Japanese source/template/tests remained untouched and retained their original file hashes.

## Strict TDD Evidence

### Task 31-05-01: Extract exact language-neutral nine-field phoneme mechanics

- **RED:** `tests/services/test_phoneme_deck.py` failed collection with `ModuleNotFoundError: multilang.services.phoneme_deck` (`1 error`).
- **Initial GREEN:** The new neutral module produced `9 passed in 0.29s`.
- **Second-pass RED:** Two focused assertions failed because the first implementation still gave neutral cards a Russian default identity/GUID formula (`2 failed, 8 passed`).
- **Final GREEN:** Language-specific identity moved back to the compatibility wrapper; the neutral fallback uses genanki's field GUID only when neither a supplied nor card-owned GUID exists (`10 passed in 0.32s`).

### Task 31-05-02: Delegate existing phoneme builders without drift

- **RED:** The combined neutral/legacy suite produced `1 failed, 21 passed`; behavior fingerprints passed, while the old module had not yet delegated its separate field tuple/types/helpers.
- **GREEN:** Compatibility types/helpers delegated through the neutral module with all frozen behavior intact (`22 passed in 0.53s`).
- **Final GREEN after the isolation second pass:** `23 passed in 0.65s`.

### Task 31-05-03: Create and statically validate the Korean-owned Hangul template

- **RED:** The filtered loader suite produced `4 failed, 4 passed, 23 deselected` because `korean_hangul_card.md` did not exist.
- **First GREEN attempt:** `1 failed, 7 passed, 23 deselected`; the responsive `.card` block needed to restate the dark canvas background for the cascade-oriented static checker.
- **GREEN:** The exact template contract produced `8 passed, 23 deselected in 0.42s`.

No commits were created because the user prohibited Git delivery and destructive actions. The RED/GREEN evidence is recorded here instead.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 neutral mechanics | `10 passed in 0.32s` |
| Task 2 neutral + compatibility | `23 passed in 0.65s` |
| Task 3 filtered template gate | `8 passed, 23 deselected in 0.42s` |
| Complete phoneme/kana/template/integration matrix | `67 passed in 1.03s` |
| Existing Polish/Greek phoneme CLI exports | `2 passed, 25 deselected in 1.25s` |
| Python compilation | Passed for all five changed Python source/test modules |
| Hangul static contract audit | 15 fields; 25 references; 9 unique learner fields; zero unknown references; zero rendered evidence fields; all four media fields conditional |
| Neutral provider/inventory fixed-file scan | Clean |
| Hangul Japanese semantic/font leakage fixed-file scan | Clean |
| New-file stub and whitespace scans | Clean |
| Changed-line `git diff --check` | Clean; only Windows LF-to-CRLF notices |
| Japanese no-touch diff | Empty, exit 0 |
| Phase lifecycle | `phase-status 31 in_progress` returned `changed: false` |
| Reviewed planning fingerprint | `cb820f09856ac4c53053496c478bc9f84364d08282ebbd3375a0c8d5dd86934b` |

The complete matrix was:

```text
tests/services/test_phoneme_deck.py
tests/services/test_russian_phoneme_deck.py
tests/services/test_japanese_kana_deck.py
tests/services/test_japanese_kana_generated_deck.py
tests/services/test_card_template_loader.py
tests/integration/test_russian_phoneme_template_refresh_flow.py
```

These are code/static/archive regressions only. No visual, responsive, playback, or Anki import acceptance is claimed.

## Compatibility IDs, Names, and Hashes

The following values are identical before and after extraction.

| Language | Model ID | Deck ID | Note type | Deck name | First GUID |
|---|---:|---:|---|---|---|
| Russian | `1602300601` | `1602300602` | `Multilang::Russian Phoneme` | `Multilang Russian::Intro Phonemes` | `b26694cb021c19c5263614fc5cc3cde4` |
| Polish | `1602300603` | `1602300604` | `Multilang::Polish Phoneme` | `Multilang Polish::Intro Phonemes` | `b9b1513bd440672d6bc303a69cda5908` |
| Greek | `1602300605` | `1602300606` | `Multilang::Greek Phoneme` | `Multilang Greek::Intro Phonemes` | `d20e2656a851001d6453c11f70ed127d` |

Shared rendered-contract SHA-256 values:

- Front/qfmt: `8dcd312a1701efe52e8a849b6560a32e34d704e5f23b8301f9929875ee7ca6a2`
- Back/afmt: `c80d95d48c63660edf9e3691588c68af0218a6d45497a07c27f53efd6783eb39`
- CSS: `788a67fec92ef52853cc4ee88ed06868fe840e80fa7922601cab185f98f13b75`
- Existing public `__all__`: `029617341f4080a76fce3d77941705d83f07e01596d400d2a4e8cbd804579ec2`

| Language | Full inventory SHA-256 | Full GUID-list SHA-256 |
|---|---|---|
| Russian | `1f2d95f883826395650242f1e60b6a292142d9c15d2cbf3db0365b9650baac05` | `5f722198b4d3c30b56dc53c5d3e8b3ba0bc3d103a68e833370a68a0d5e785412` |
| Polish | `f47f7be267a1c81e8057f6cc09253035773d0c78decec5ade760b87a13ccadba` | `7b10cee8ca0299ad0db2296c13c368262833e6da7d9a3171ce30c9b713dd07d1` |
| Greek | `44994699c515f5b6e194eb346f7ad7716ba34f59d59f75bbd2d001c2b2f84999` | `fd312fa3d6522cbd1051e2e130310182dbfca4702fb7a74e06c1b1fb79da7722` |

No field value, field order, GUID input, template name, template byte, CSS byte, inventory record, voice/locale, deck identity, audio path, export route, or CLI command was changed.

## No-Touch Evidence

| No-touch artifact | SHA-256 | Result |
|---|---|---|
| `src/multilang/templates/japanese_kana_card.md` | `c7a62af86dacbe3175fe1ed72618eadf762a646b09b67d107a7cbceef9663bf8` | Unchanged |
| `src/multilang/services/japanese_kana_deck.py` | `3dd4375df8b37dee2537b222d8c29645f52901884e5b355a8958e10c1d486624` | Unchanged |
| `src/multilang/templates/russian_phoneme_card.md` | `fdb2b3fc3e922d4181f60906f4cdeed32ecf152c2d8374bc66e33cc136b2bd11` | Unchanged |

`git diff --exit-code` was empty for the Japanese template, source module, and both existing kana test modules.

## Files Created/Modified

### Created

- `src/multilang/services/phoneme_deck.py` - neutral nine-field card/model/note/template/GUID mechanics with strict references and font-only additive CSS.
- `src/multilang/templates/korean_hangul_card.md` - standalone exact 15-field Korean-owned static template.
- `tests/services/test_phoneme_deck.py` - neutral mapping/model/note/GUID/template/CSS contracts.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-05-SUMMARY.md` - execution evidence and bounded handoff.

### Modified

- `src/multilang/services/russian_phoneme_deck.py` - compatibility card identity and legacy behavior retained while neutral mechanics delegate.
- `tests/services/test_russian_phoneme_deck.py` - exact public API, identity, rendered-byte, inventory, GUID, mapping, and delegation fingerprints.
- `tests/services/test_card_template_loader.py` - exact Hangul fields/references/order/fonts/media/security static checks.
- `.planning/SPEC.md` - records Plan 31-05 complete and Plan 31-06 next.
- `.planning/.state-fingerprint.json` - reviewed planning-state baseline.

## Decisions Made

- The neutral card may carry generic ordering and nine learner values, but no default language, locale, voice, inventory, or language-specific GUID formula.
- `build_phoneme_note()` prefers an explicitly supplied GUID, then a compatibility card's existing stable GUID, then genanki's field-based fallback for a plain neutral card.
- Existing `RussianPhonemeCard` remains a same-signature dataclass wrapper and owns the unchanged `{language}-phoneme|sort_index|letters|ipa` SHA-256 input.
- Existing `RussianPhonemeNote` remains importable as an alias to the neutral note type, which the approved approach explicitly permits.
- Additive phoneme CSS is intentionally narrow: class selectors and `font-family` declarations only. Base CSS cannot be replaced through the public builder.
- The Korean template repeats only approved layout mechanics. It does not import, parameterize, modify, or reference Japanese source/template identity.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Isolation Bug] Removed Russian identity from the neutral card layer**
- **Found during:** High-leverage second pass after Task 31-05-02.
- **Issue:** The first extraction moved the legacy `language_code="ru"` default and Russian GUID input formula into `PhonemeCard`, making the nominally neutral module carry Russian semantics.
- **Fix:** Added a failing isolation/fallback test, removed language identity and GUID derivation from `PhonemeCard`, restored both to the `RussianPhonemeCard` compatibility wrapper, and retained explicit/card/fallback GUID injection in the neutral note builder.
- **Files modified:** `src/multilang/services/phoneme_deck.py`, `src/multilang/services/russian_phoneme_deck.py`, `tests/services/test_phoneme_deck.py`.
- **Verification:** RED was `2 failed, 8 passed`; GREEN was `23 passed` across neutral plus compatibility tests, followed by the `67 passed` complete matrix and unchanged compatibility hashes.
- **Committed in:** Not committed; Git actions were explicitly disabled.

---

**Total deviations:** 1 auto-fixed Rule 1 isolation bug.
**Impact on plan:** The fix narrowed the neutral layer to the plan's hard boundary and preserved every legacy identity. No provider, content, media, exporter, CLI, Japanese, or visual scope was added.

## Issues Encountered

- The first Hangul GREEN run showed that the responsive `.card` rule became the final cascade block without explicitly repeating the dark background. Restating the same background in that bounded media query made the static cascade check unambiguous; no visual claim was inferred.
- `rg` was not installed in the environment. An initial supplemental shell scan therefore could not be used; a deterministic Python fixed-file scanner was run instead and found no neutral provider/inventory terms, Japanese leakage, or stub markers.
- A whole-file whitespace probe surfaced trailing spaces in untouched lines of the legacy synthesis block. They predate this extraction, are absent from changed lines/new files, and were deliberately not cleaned because the plan forbids adjacent legacy cleanup.

## Security and Privacy Review

- Shared template loading uses one fixed package resource and validates every Mustache reference against the exact field allowlist plus `FrontSide`; there is no caller path, URL, remote source, dynamic import, or manifest-selected template.
- Additive CSS rejects non-font properties, `@import`, body/root replacement attempts, and other non-class-scoped blocks under the tested grammar.
- The Hangul template has no script, event-handler attribute, CSS import, external URL, or unknown field reference. Its five graph-evidence fields are declared but never rendered.
- The neutral module contains no Settings, Azure adapter, voice/locale, inventory, synthesis, exporter, CLI, network, database, or file-output behavior.
- No source text, reviewer data, media path, provider payload, credential, endpoint, authentication path, or persistence schema was introduced.
- Both new trust surfaces were already represented by the Plan 31-05 threat register; no additional threat flags were found.

## Known Stubs

None. Empty audio defaults are the pre-existing optional nine-field card contract, not hardcoded learner output; callers supply reviewed media values. Hidden graph fields and inactive production review/media state are intentional fail-closed boundaries owned by later Phase 31 plans, not template stubs.

## Task Commits and Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other Git delivery/destructive action was performed.

## Authentication Gates

None.

## User Setup Required

None. This plan makes no provider/network call and requires no credential, database, media acquisition, Anki runtime, or manual visual check.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-05 complete and Plan 31-06 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; Phase 31 remains open at `[-]`.
- The reviewed planning fingerprint is `cb820f09856ac4c53053496c478bc9f84364d08282ebbd3375a0c8d5dd86934b`.
- KHAN-01 and KPRO-01 are advanced but remain unchecked because Plan 31-06 must create Korean model/deck identity and all-format export, later plans must bind genuine review/media evidence, and Phase 34 owns observed Anki acceptance.
- `.planning/STATE.md` and requirement checkboxes were not advanced; the user explicitly requested the phase remain open with SPEC/fingerprint handoff only.

## Next Phase Readiness

- Plan 31-06 can build Korean pronunciation models from `build_phoneme_model()` using exact shared front/back/base CSS and an isolated Korean font declaration.
- Plan 31-06 can parse the standalone Hangul template and validate its exact 15-field references without importing Japanese code.
- No engineering blocker remains for Plan 31-06.
- Production remains deliberately inactive and non-learner-ready under the Plan 31-04 judgment until genuine review, licensing, exact media, snapshot preparation, and activation evidence exists.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All strict TDD gates passed. The final task commands produced 10, 23, and 8 focused passes; the exact kana/phoneme/template/integration matrix produced 67 passes; existing CLI export tests produced 2 passes; compilation, static field/reference/security scans, compatibility fingerprints, no-touch hashes/diff, scoped whitespace checks, open phase status, and planning fingerprint all passed.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: passed
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The first extraction retained a Russian default/GUID formula in the neutral card; a focused RED test moved language identity back to the compatibility wrapper without changing any legacy output.
</deltas>

<judgment>
<active_constraints>
Preserve Phase 30 canonical Korean identity and Plan 31-04 immutable pending-review/media posture. The shared phoneme layer owns only exact nine-field rendering mechanics and fixed-template validation. Russian, Polish, and Greek identity/inventory/audio/export/CLI behavior remains compatibility-owned. The Korean Hangul template is standalone, fixed, Korean-owned, and static; it renders frozen learner values only and hides graph evidence.
</active_constraints>
<unresolved_uncertainty>
Korean model/deck IDs, note construction, immutable-snapshot joins, all-format exports, exact production media, qualified review, activation, and observed Anki rendering/import/playback remain later Plan 31-06 onward or Phase 34 work. Static CSS and markup cannot establish appearance, readability, responsiveness, font availability, playback, or import success.
</unresolved_uncertainty>
<decision_posture>
Reuse exact proven mechanics while isolating language identity. Prefer fixed schemas, byte/hash compatibility, narrow additive font CSS, hidden evidence, conditional media, and no-touch regression proof over parameterized cross-language templates or adjacent legacy cleanup.
</decision_posture>
<anti_regression>
Do not add language/provider/inventory/export policy to phoneme_deck.py; change any Russian/Polish/Greek field, ID, name, GUID input, template/CSS byte, inventory, voice, synthesis, APKG, or CLI behavior; import/parameterize/modify Japanese source or template for Korean; render Hangul graph evidence; add executable/dynamic template markup; or claim visual/import/playback acceptance from these static tests.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All nine implementation, test, planning, fingerprint, and summary artifacts listed by this plan exist.
- The final exact compatibility/kana/phoneme/template/integration matrix reran after summary creation and produced `67 passed in 0.98s`.
- The Japanese no-touch diff remained empty, and repository HEAD remained `240b21abb8efce5e028fd0b80d1767cbcac0f145` because Git actions were disabled.
- The compatibility IDs, names, template/CSS hashes, inventory hashes, GUID-list hashes, and first GUIDs match the pre-extraction baseline.
- The Hangul template parses to exactly 15 fields, has no unknown references or rendered graph evidence, and conditionally guards all four media fields.
- Required `<checks>`, `<handoff>`, `<deltas>`, `<judgment>`, strict-TDD, compatibility, no-touch, deviations, security, known-stub, and state sections are present.
- Phase 31 remains open at `[-]`, SPEC points to Plan 31-06, and the reviewed planning fingerprint is `cb820f09856ac4c53053496c478bc9f84364d08282ebbd3375a0c8d5dd86934b`.

---
*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 05*
*Completed: 2026-08-05*
