# Morphology Model Selection and Comparison Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development for the
> independent tasks below. The user approved implementation; continue without
> another execution question.

**Goal:** Select morphology models by language and compare accuracy, coverage,
latency and memory reproducibly before adopting a different model.

**Architecture:** Extend the existing pinned model manager. Use a dedicated
comparison service and isolated workers around the existing evaluator. Compose
selection through Settings and the current vocabulary CLI.

**Tech Stack:** Python, Pydantic v2, Stanza/Kiwi/Fugashi, Typer, pytest.

**Spec:** `docs/superpowers/specs/2026-09-13-morphology-model-comparison.md`

## Global Constraints

- No GSD/GSDD, paid provider calls, production DB writes, deploy, staging or commits.
- Preserve previous checkout changes and all legacy Anki/identity/review contracts.
- `fast` keeps the current defaults and legacy manifest/fingerprint compatibility.
- Preparation is explicit; status, evaluation and runtime must stay offline.
- Pin and verify every model dependency; never enable remote custom code.
- Preserve evaluation denominators, metric definitions and native null metrics.
- Model recommendations use `dev` only and never activate or qualify a language.
- Run heavy model processes sequentially with bounded time and output.

## Task 1: Profile-aware model manager

**Files:** `services/language_models.py`, optional focused transformer-artifact
module, `tests/services/test_language_models.py` and focused new tests.

**Interfaces:** Add keyword `profile="fast"` to `stanza_processors`,
`prepare_model`, `model_status`, `load_stanza_pipeline`; add
`available_model_profiles(language, root) -> dict` for offline capability/status.
Use separate `<language>.<profile>.manifest.json` files beside the legacy
`<language>.manifest.json` (legacy is fast). Alternative manifest metadata binds
profile and any external dependencies. No caller may silently fall back to fast.

- [x] Write tests for alternate selection and observe failure.
  ```python
  assert stanza_processors(registry, "en", profile="balanced")["pos"] == "combined_charlm"
  assert stanza_processors(registry, "en")["pos"] == "combined_nocharlm"
  ```
- [x] Implement selection, capability inventory, atomic preparation and isolated
  manifests with exact required files. Resolve and bind external transformer
  artifacts from the trusted configured model, load them locally and preserve
  legacy fingerprints. Native backends only support their current fast profile.
- [x] Test tampering, unsupported profiles, shared artifact inventory and offline
  loading; run focused model tests. Record real constraints in the task report.

## Task 2: Automatic comparison service

**Files:** new `services/model_comparison.py` and worker module, minimal changes
to `services/vocabulary_evaluation.py`, new focused comparison tests.

**Interfaces:** `ModelComparisonRequest` contains `model_root`, `datasets`
(`language`, `corpus`, `corpus_sha256`, `split`), `profiles`, `max_sentences`,
`timeout_seconds`, `threads`; `compare_models(request, *, output: Path) -> dict`.
Workers instantiate `LocalContextualMorphologyService(model_root=...,
model_profiles={language: profile}, threads=...)` supplied by Task 3.

- [x] Test equal samples, same baseline, measured deltas and rejection of
  recommendations from test data; observe failures.
  ```python
  assert test_report["recommendation"] is None
  assert worse_coverage_candidate["decision"] != "recommended"
  ```
- [x] Implement sequential isolated workers using fixed modules and structured
  JSON, offline environment, timeout/process cleanup and bounded files. Record
  peak RSS and elapsed time. Missing/failed models retain explicit status.
- [x] Reuse the evaluator through an explicit development entry point while
  keeping `evaluate_corpus` test-only. Preserve metric rules and evaluator v3.
- [x] Add per-feature diagnostics from verified observations. Recommend only
  candidates that improve a comparable metric without regression or lost coverage
  on dev. Ties preserve baseline; no production activation or approval.
- [x] Exercise subprocess timeout, malformed/hash-mismatched input, immutable
  output, null metrics and fixtures end to end. Record commands and results.

## Task 3: Configuration, runtime and CLI composition

**Files:** `settings.py`, `services/contextual_morphology.py` constructor/loading
only, `native_runtime.py`, `vocabulary_cli.py`, `qualification_cli.py`, focused
CLI/configuration/runtime tests.

- [x] Reproduce missing language-specific profile selection with focused tests.
- [x] Add validated `native_language_model_profiles`, preserving empty defaults.
  Thread the selected profile and bounded CPU threads through analyzer loading.
  Keep existing two-argument model seams when default configuration is used.
- [x] Add profile options to model status/preparation/evaluation and a
  `model-options` command. Add `compare-models REQUEST SHA256 OUTPUT` using the
  comparison service; show controlled error categories without private payloads.
- [x] Test dispatch, invalid languages/profiles, configuration and native runtime
  wiring; preserve existing command defaults and qualification behavior.

## Task 4: Integration and measured evidence

**Files:** operator documentation, plan/verification records; no production data.

- [x] Run affected tests and inspect per-task independent reviews; fix findings.
- [x] Exercise the new CLI against local corpora and model inventory. Use bounded
  real comparisons where prepared resources permit; explicitly distinguish
  unavailable alternatives, diagnostics on test data and dev recommendations.
- [x] Run Ruff, build and strict documentation validation. Document commands,
  performance tradeoffs and actual results; report no unmeasured accuracy gains.

## Execution record

Task-specific baseline, briefs and reports are preserved under
`.multilang/verification/model-comparison/`. Prior work is excluded from review
diffs using the baseline snapshot. No Git writes are required for this task.

Completed on 2026-09-19. Three independent 25-sentence test pilots completed via
the CLI (German, Turkish and Russian; fast/balanced). Results and resource costs
are documented in `docs/morphology-model-comparison.md`; none qualified for a
change without regression, and test data cannot recommend a profile.

Fresh verification: 152 affected tests plus 2 additional lightweight tests passed.
Feature-scoped Ruff, sdist/wheel creation and strict MkDocs generation passed;
the new modules were verified inside both distribution formats. Prior real
English and offline tiny-transformer smoke tests also passed. Independent reviews
approved the feature with no open findings. The final whole-repository Ruff check
reported 10 import-order findings in concurrently edited Korean audio/learning
and qualification-preview files outside this feature; see `ruff-final.log` in
the verification directory. No global clean-lint claim is made for that snapshot.
