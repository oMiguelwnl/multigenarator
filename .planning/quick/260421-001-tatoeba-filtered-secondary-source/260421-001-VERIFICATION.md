---
phase: quick-260421-001-tatoeba-filtered-secondary-source
verified: 2026-04-23T17:45:52Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Quick Task 260421-001 Verification Report

**Phase Goal:** implement Tatoeba as a filtered secondary sentence source with advanced reranking and validation, never as the raw default primary source.
**Verified:** 2026-04-23T17:45:52Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Primary sentence generation success never queries Tatoeba. | ✓ VERIFIED | `TextGenerationService.generate_bundle()` only uses the primary sentence/translation adapters and has no Tatoeba dependency (`src/multilang/services/text_generation.py:109-130`). `GenerateTextItemsService` calls Tatoeba only inside the failed-validation branch (`src/multilang/services/generate_text_items.py:84-94,171-194`). Covered by `test_generate_text_items_skips_tatoeba_when_first_pass_validation_succeeds` (`tests/services/test_generate_text_items.py:260-289`). |
| 2 | A failed first-pass sentence can use Tatoeba only on the single repair branch after deterministic filtering and reranking. | ✓ VERIFIED | Failed validation triggers exactly one `_attempt_tatoeba_repair()` call with `repair_attempt_count = 1` (`src/multilang/services/generate_text_items.py:84-94`). `TatoebaSentenceSource.select_sentence()` applies language checks, linked-translation eligibility, hard filters, target matching, and tuple-based deterministic scoring before selecting one sentence (`src/multilang/services/tatoeba_sentence_source.py:176-274`). Covered by `tests/services/test_tatoeba_sentence_source.py` and `tests/services/test_generate_text_items.py:292-370`. |
| 3 | Final translation text still comes from the normal translation adapter, never from Tatoeba-linked translation text. | ✓ VERIFIED | Fallback bundles are built through `SentenceTranslationRequest.from_sentence(sentence_result=...)`, which only uses the selected sentence/intended sense/template kind (`src/multilang/services/text_generation.py:52-67,132-149`). Tatoeba linked translations are used only as eligibility input in `TatoebaSentenceSource`; they are not forwarded into translation results (`src/multilang/services/tatoeba_sentence_source.py:201-232,347-364`). Covered by `test_tatoeba_fallback_translation_uses_selected_sentence_not_linked_translation_text` (`tests/services/test_text_generation.py:194-221`). |
| 4 | If the best Tatoeba candidate still fails validation, the item is persisted as review_required after one repair attempt. | ✓ VERIFIED | After fallback generation, the repaired bundle is validated by the normal validator and persisted with `ReviewStatus.REVIEW_REQUIRED` when validation still fails (`src/multilang/services/generate_text_items.py:188-194,144-169`). Covered by `test_generate_text_items_flags_review_after_one_failed_repair` and `test_generate_text_items_keeps_review_required_when_tatoeba_has_no_usable_candidate` (`tests/services/test_generate_text_items.py:210-257,340-370`). |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/multilang/services/tatoeba_sentence_source.py` | Secondary-only Tatoeba candidate filtering and deterministic reranking | ✓ VERIFIED | Substantive 376-line service with API/static providers, hard filters, reflexive-aware matching, and deterministic score ordering; wired into runtime + repair flow (`:96-142,168-274`). |
| `src/multilang/services/generate_text_items.py` | Repair-branch routing that swaps second generation attempt for Tatoeba fallback | ✓ VERIFIED | Service performs primary generate/validate once, then single repair attempt through injected Tatoeba source only on failure (`:76-94,171-194`). |
| `src/multilang/services/text_validation.py` | Final quality gates rejecting weak fallback sentences before acceptance | ✓ VERIFIED | Validator checks target-form presence, length, banned/meta/question/short-command patterns, and translation mismatch before acceptance (`:91-148,189-247,354-379`). |
| `src/multilang/runtime.py` | Runtime wiring for shipped path fallback boundary | ✓ VERIFIED | `build_runtime_service()` injects `TatoebaSentenceSource` with API/static provider selection and passes it into `GenerateTextItemsService` (`src/multilang/runtime.py:188-223`). |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `generate_text_items.py` | `tatoeba_sentence_source.py` | failed-first-pass repair branch only | ✓ WIRED | `_attempt_tatoeba_repair()` calls `select_sentence()` only after failed validation, then runs fallback generation and revalidation (`src/multilang/services/generate_text_items.py:179-194`). |
| `tatoeba_sentence_source.py` | `text_generation.py` | selected fallback sentence with provenance `source=tatoeba` | ✓ WIRED | `select_sentence()` emits `SentenceGenerationResult(provenance={"source": "tatoeba", ...})`; `generate_bundle_from_fallback()` turns that into a normal `SentenceTranslationRequest.from_sentence(...)` (`src/multilang/services/tatoeba_sentence_source.py:223-232`; `src/multilang/services/text_generation.py:132-149`). |
| `text_generation.py` | `text_validation.py` | fallback sentence uses standard translation and validator path | ✓ WIRED | Fallback and primary bundles both flow through `GenerateTextItemsService._validate_bundle()` into `TextValidationService.validate(...)` (`src/multilang/services/generate_text_items.py:80,193`; `src/multilang/services/text_validation.py:91-148`). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `tatoeba_sentence_source.py` | `candidates` / `selected.sentence_text` | `candidate_provider.search_candidates(...)` from API or injected provider rows | Yes | ✓ FLOWING |
| `generate_text_items.py` | `fallback_sentence` | `tatoeba_sentence_source.select_sentence(...)` after failed validation | Yes | ✓ FLOWING |
| `text_generation.py` | `translation_request.sentence` | `SentenceTranslationRequest.from_sentence(sentence_result=...)` | Yes; uses selected fallback sentence, not linked translation text | ✓ FLOWING |
| `text_validation.py` | `sentence.text` + `translation.text` | `GeneratedTextBundle` from primary or fallback path | Yes; validator checks actual bundle content before persistence | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Focused quick-task behavior suite | `uv run pytest tests/services/test_tatoeba_sentence_source.py tests/services/test_text_generation.py tests/services/test_generate_text_items.py tests/services/test_text_validation.py tests/cli/test_generate_command.py tests/test_job_summary.py -q` | `44 passed in 117.81s` | ✓ PASS |
| Non-gating integration regression check | `uv run pytest tests/integration/test_text_job_flow.py -q` | `3 failed` | ⚠️ DEBT |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `TEXT-01` | quick-260421-001 | Example sentence contains target word and matches intended meaning | ✓ SATISFIED | Target-form checks remain enforced in both selector and validator; failed bundles are repaired or routed to review (`src/multilang/services/tatoeba_sentence_source.py:205-210`; `src/multilang/services/text_validation.py:150-170`). |
| `TEXT-02` | quick-260421-001 | Example sentence passes quality rules for length, naturalness, readability | ✓ SATISFIED (quick-task scope) | Deterministic filters reject questions, fragments, meta sentences, and short command-like fallbacks before acceptance (`src/multilang/services/tatoeba_sentence_source.py:234-243`; `src/multilang/services/text_validation.py:189-219,359-379`). |
| `TEXT-03` | quick-260421-001 | Translation matches displayed example sentence | ✓ SATISFIED | Fallback translation uses the selected sentence through the normal translation adapter (`src/multilang/services/text_generation.py:52-67,132-159`; `tests/services/test_text_generation.py:194-221`). |
| `TEXT-04` | quick-260421-001 | User can review flagged low-confidence cards before final export | ✓ SATISFIED | Unusable fallback results persist as `review_required` with validation flags/reasons intact (`src/multilang/services/generate_text_items.py:144-169`; `tests/services/test_generate_text_items.py:210-257,340-370`). |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `src/multilang/runtime.py` | 96-122 | Intentional `placeholder` review-path sentinel | ℹ️ Info | Existing runtime test hook; it routes obvious bad text into review and is not evidence of hollow Tatoeba wiring. |
| `tests/integration/test_text_job_flow.py` | 139-223 | Stale expectations vs current validator/runtime behavior | ⚠️ Warning | Integration suite still expects pre-change acceptance counts and an older Spanish sentence. User asked not to gate this quick task on integration failures; treat as testing debt unless broader runtime behavior is being re-opened. |

### Human Verification Required

None.

### Gaps Summary

No blocking gaps found against this quick-task goal. The codebase now enforces a secondary-only Tatoeba boundary, uses deterministic filtering/reranking before fallback acceptance, preserves the standard translation path, and routes unusable fallback output to review after one repair attempt. The remaining integration failures are real follow-up debt, but they do not disprove the quick-task contract the user asked to verify.

---

_Verified: 2026-04-23T17:45:52Z_
_Verifier: the agent (gsd-verifier)_ 
