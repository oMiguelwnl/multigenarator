---
phase: 03-sentence-quality-review-loop
verified: 2026-04-21T21:43:41Z
status: verified
score: 8/8 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 6/8
  gaps_closed:
    - "User receives an example sentence that contains the target word and matches the intended meaning of the card."
    - "User receives example sentences that pass the project's quality rules for length, naturalness, and readability."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Sample accepted sentences for naturalness in at least two languages"
    expected: "Accepted sentences are concise, natural, learner-friendly, and not meta text about the word itself."
    why_human: "TEXT-02 includes naturalness/pedagogy judgement. Closed in 03-HUMAN-UAT.md with user approval for sampled English and French outputs."
  - test: "Inspect one generated review report from a seeded flagged run"
    expected: "Each row is actionable for regeneration and clearly shows job_id, item_key, sentence, translation, flags, and reason."
    why_human: "Review report usefulness is partly UX/content quality. Closed in 03-HUMAN-UAT.md with user approval of the seeded flagged report."
---

# Phase 3: Sentence Quality & Review Loop Verification Report

**Phase Goal:** Users can trust the meaning-bearing text on each card and repair weak cards without rerunning the full batch.
**Verified:** 2026-04-21T21:43:41Z
**Status:** verified
**Re-verification:** Yes — after the generic-fallback rejection fix and subsequent human UAT closure

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | User receives an example sentence that contains the target word and matches the intended meaning of the card. | ✓ VERIFIED | The shipped path no longer accepts the generic meta fallback as learner-facing text. `src/multilang/services/text_validation.py:187-210,345-347` rejects meta sentences, `tests/services/test_text_validation.py:87-97` locks that rule, and the direct `alpha` spot-check produced `The word alpha is useful in daily life.` with `validation_status='failed'`. A CLI spot-check persisted the row as `review_required` and printed `flagged_cards=1` instead of accepting it. |
| 2 | User receives example sentences that pass the project's quality rules for length, naturalness, and readability. | ✓ VERIFIED | Deterministic checks cover length/readability and reject placeholder, repetitive, hollow-support, and meta-sentence text (`src/multilang/services/text_validation.py:170-210,322-347`; `tests/services/test_text_validation.py`). Manual naturalness sampling was then closed in `.planning/phases/03-sentence-quality-review-loop/03-HUMAN-UAT.md` with approved English and French samples. |
| 3 | User receives a translation that matches the displayed example sentence. | ✓ VERIFIED | `src/multilang/runtime.py:115-131` translates from `intended_sense` plus `template_kind`, not from raw definitions. `tests/test_runtime_templates.py:25-35` verifies the `wash` pair, and the direct spot-check returned `It is good to wash every day.` / `É bom lavar todos os dias.` with `validation_status='passed'`. |
| 4 | User can review low-confidence cards before final export. | ✓ VERIFIED | `src/multilang/services/text_review.py:37-89` serializes flagged rows into a persisted report with sentence, translation, flags, and stable identity. `src/multilang/cli.py:495-505` prints `flagged_cards=` and `review_report=`, and `tests/cli/test_generate_command.py:194-273` covers flagged and empty-report paths. |
| 5 | User can regenerate a flagged card from the review flow without rerunning the full batch. | ✓ VERIFIED | `src/multilang/cli.py:483-489` wires `--resume` + `--regenerate-item-key`, and `src/multilang/services/regenerate_text_item.py:30-76` updates one persisted row in place. `tests/services/test_regenerate_text_item.py:160-293` and `tests/cli/test_generate_command.py:435-490` verify targeted regeneration without touching other rows. |
| 6 | Phase 3 persists sentence, translation, confidence, validation, and review state separately from lexical candidates with one stable text row per job item. | ✓ VERIFIED | `src/multilang/domain/text_quality.py:13-97`, `src/multilang/repositories/text_repository.py:29-144`, `src/multilang/db/models.py`, and `alembic/versions/20260421_03_text_quality_tables.py:16-58` still enforce one `text_quality_records` row per `(job_id, item_key)`. User-provided disposable-SQLite schema re-verification also passed. |
| 7 | Review output is backed by a persisted artifact that preserves stable item identity for later targeting. | ✓ VERIFIED | `src/multilang/services/text_review.py:37-89` writes deterministic JSON with `job_id` and `item_key`, and `tests/services/test_text_review.py` covers ordering, identity retention, and stable serialization. |
| 8 | The shipped `multilang generate` path wires lexical ingestion, text generation, review reporting, and targeted regeneration on one runtime path. | ✓ VERIFIED | `src/multilang/runtime.py:141-219` composes ingestion, generation, validation, review, and regeneration services, while `src/multilang/cli.py:468-507` runs them on the shipped command. User-provided non-integration pytest evidence remained green (`35 passed`, `32 passed`). |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/multilang/domain/text_quality.py` | Typed text-quality contracts and statuses | ✓ VERIFIED | Stable enums/models for validation, confidence, review, provenance, and row identity remain intact. |
| `src/multilang/repositories/text_repository.py` | Persistence boundary for sentence-quality rows | ✓ VERIFIED | Upsert/get/list/flagged/generation-candidate queries remain substantive and wired to ORM rows. |
| `alembic/versions/20260421_03_text_quality_tables.py` | Migration for persisted Phase 3 rows | ✓ VERIFIED | Migration still creates `text_quality_records`; disposable SQLite re-verification passed per user-provided evidence. |
| `src/multilang/services/text_generation.py` | Sentence-generation and sentence-translation service boundary | ✓ VERIFIED | Still sequences sentence generation before translation and preserves structured provenance. |
| `src/multilang/services/text_validation.py` | Deterministic validation and confidence scoring | ✓ VERIFIED | Meta-sentence rejection now closes the prior generic-fallback acceptance gap. |
| `src/multilang/services/text_review.py` | Review queue and persisted report builder | ✓ VERIFIED | Deterministic review artifact with stable identity and triage ordering remains present. |
| `src/multilang/services/regenerate_text_item.py` | Item-level text regeneration service | ✓ VERIFIED | Regenerates one persisted row by `job_id` + `item_key` and preserves single-row identity. |
| `src/multilang/runtime.py` | Shipped runtime bootstrap for Phase 3 | ✓ VERIFIED | Runtime still emits a generic template for unknown senses, but `GenerateTextItemsService` + `TextValidationService` now block that path from becoming accepted card text. |
| `src/multilang/cli.py` | Shipped CLI review/report/regeneration surface | ✓ VERIFIED | One `multilang generate` path still exposes lexical counts, text counts, review reports, and targeted regeneration flags. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/multilang/services/generate_text_items.py` | `src/multilang/repositories/text_repository.py` | persisted accepted/review-required rows | ✓ WIRED | `execute()` still builds `TextQualityRecord` rows and persists them before marking `JobStage.GENERATE_TEXT` success. |
| `src/multilang/services/text_review.py` | `src/multilang/repositories/text_repository.py` | flagged-row queries and report serialization | ✓ WIRED | `build_review_report()` reads `list_flagged_records(job_id)` and writes the artifact. |
| `src/multilang/cli.py` | `src/multilang/services/regenerate_text_item.py` | `--resume` + `--regenerate-item-key` | ✓ WIRED | CLI still dispatches targeted regeneration on the existing `generate` command. |
| `src/multilang/runtime.py` | lexical meaning context | shipped sentence generation uses grounded meaning or review-required rejection | ✓ WIRED | `definitions_html` still drives `_infer_sense_key()` / `_sense_hint()`, and unknown-sense fallback now gets rejected downstream by `TextValidationService._looks_like_meta_sentence()`. |
| `src/multilang/runtime.py` | generated sentence content | shipped translation matches actual sentence | ✓ WIRED | `_TemplateTranslationAdapter.translate_sentence()` uses `intended_sense` and `template_kind` to mirror the generated sentence shape. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/multilang/runtime.py` | `example_sentence` | `_infer_sense_key()` / `_sense_hint()` over `definitions_html` plus runtime templates | Known senses produce meaning-bearing templates; unknown-sense generic output is rejected before acceptance | ✓ FLOWING (guarded) |
| `src/multilang/runtime.py` | `translation_text` | `intended_sense` + `template_kind` from generated sentence | Yes | ✓ FLOWING |
| `src/multilang/services/text_review.py` | `report.items` | `TextRepository.list_flagged_records(job_id)` over persisted DB rows | Yes | ✓ FLOWING |
| `src/multilang/services/regenerate_text_item.py` | targeted lexical candidate | `LexicalRepository.get_candidate_for_item(job_id, item_key)` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Updated non-integration Phase 3 suite | `uv run pytest tests/test_runtime_templates.py tests/services/test_text_generation.py tests/services/test_text_validation.py tests/services/test_generate_text_items.py tests/services/test_regenerate_text_item.py tests/cli/test_generate_command.py -q` | User-provided evidence: `35 passed` | ✓ PASS |
| Regression subset touching runtime/bootstrap and summaries | `uv run pytest tests/repositories/test_job_repository.py tests/test_job_summary.py tests/cli/test_generate_command.py tests/test_runtime_templates.py tests/services/test_text_validation.py -q` | User-provided evidence: `32 passed` | ✓ PASS |
| Phase 3 schema migration re-check | disposable SQLite Alembic upgrade + table inspection | User-provided evidence: passed against disposable SQLite | ✓ PASS |
| Unknown-sense runtime fallback rejection | direct `uv run python -c ...` spot-check | Returned `The word alpha is useful in daily life.` / `A palavra alpha é útil no dia a dia.` with `status='failed'`, flags `['banned_pattern']` | ✓ PASS |
| Known-sense runtime sentence/translation pair | direct `uv run python -c ...` spot-check | Returned `It is good to wash every day.` / `É bom lavar todos os dias.` with `status='passed'` | ✓ PASS |
| Shipped runtime review routing for weak text | direct `uv run python -c ...` CLI spot-check | Exit `0`; output included `review_required_text_items=1` and `flagged_cards=1`; persisted row stayed `review_required` | ✓ PASS |
| Phase 3 integration tests | `uv run pytest tests/integration/test_text_job_flow.py -q` | Not run per user request | ? SKIP (testing debt) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `TEXT-01` | 03-01, 03-02, 03-03, 03-05 | Example sentence contains the target word and matches the intended meaning of the card | ✓ SATISFIED | Generic meta fallback no longer passes validation; accepted text remains meaning-bearing, and weak rows are routed into review instead of silently shipped. |
| `TEXT-02` | 03-03, 03-05 | Example sentence passes quality rules for length, naturalness, and readability | ✓ SATISFIED | Deterministic rules enforce length/readability and reject placeholder/meta text, and `03-HUMAN-UAT.md` closes the remaining naturalness sampling with user-approved examples. |
| `TEXT-03` | 03-01, 03-02, 03-03, 03-05 | Translation matches the displayed example sentence | ✓ SATISFIED | Runtime translation mirrors sentence meaning/template; focused tests and spot-checks agree. |
| `TEXT-04` | 03-01, 03-03, 03-04, 03-05 | User can review flagged low-confidence cards before final export | ✓ SATISFIED | Flagged rows persist, deterministic review JSON is written, and CLI prints `flagged_cards` / `review_report`. |
| `TEXT-05` | 03-01, 03-04, 03-05 | User can regenerate a flagged card without rerunning the full batch | ✓ SATISFIED | CLI/runtime support `--resume` + `--regenerate-item-key`; targeted row regeneration remains covered by service and CLI tests. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `tests/test_runtime_templates.py` | 38-50 | Test still locks the generic runtime term fallback as expected behavior | ⚠️ Warning | The validator now blocks this path, but the unit test still normalizes a weak template that would be unsafe if the review gate were bypassed later. |
| `tests/integration/test_text_job_flow.py` | 186-219 | Latest re-verification skipped the integration suite and the locale-specific expectation appears stale relative to current runtime templates | ⚠️ Warning | Phase 3 is functionally complete, but the integration re-check debt should be cleaned up before Phase 4 starts leaning on this path heavily. |

### Human Verification Completed

### 1. Multilingual naturalness sample

**Result:** Passed
**Evidence:** `.planning/phases/03-sentence-quality-review-loop/03-HUMAN-UAT.md` records user approval of sampled English and French accepted sentences and translations.

### 2. Review report actionability check

**Result:** Passed
**Evidence:** `.planning/phases/03-sentence-quality-review-loop/03-HUMAN-UAT.md` records user approval that the seeded flagged report row is clear and actionable for regeneration.

### Gaps Summary

No blocking code gaps remain from the previous verification. The latest fix closes the shipped-path failure mode: unknown-sense generic fallback text is now rejected by validation and routed into the persisted review flow instead of being accepted as learner-facing card text. Review/report/regeneration wiring remains intact, schema verification is green, the requested non-integration pytest evidence is clean, and the manual naturalness/report-usability checks were later closed in `03-HUMAN-UAT.md`.

Phase 3 is therefore verified complete. The remaining concern is testing debt rather than a phase blocker: the latest re-verification skipped the integration suite and that coverage should be refreshed, but the phase no longer has open implementation or human-sign-off gaps.

---

_Verified: 2026-04-21T21:43:41Z_
_Verifier: the agent (gsd-verifier)_
