# Multilingual Completion Implementation Plan

> Approved by the user's request to implement all remaining proposals. Use
> subagent-driven-development for independent tasks and focused review.

**Goal:** Complete local vocabulary preparation and field-compatible native exports
for all 22 modern languages, with truthful source and qualification evidence.

**Architecture:** Extend the existing contracts, services, CLI and runtime.
Morphological analysis and lexical sense evidence remain independent. Reuse
source adapters, profiles, ranking, versioned content/audio, review and export.

**Spec:** `docs/multilingual-completion-design.md`; master details in
`docs/multilingual-lexical-adaptive-plan-v4.md`.

## Global Constraints

- Stay on `feature/roadmap-4-0-native-architecture`; preserve preexisting files/index.
- No GSDD runtime/workflow and no deployment.
- Preserve per-language field sets/templates, exact forms and contextual audio.
- Preserve exact existing field names and order; no renamed/removed/appended
  metadata fields. Keep linkage in the database/manifest.
- 3000 Core identities per modern language, plus all approved important form cards.
- NFC and case/diacritics preservation; contextual matching; no invented senses.
- No fabricated licenses/reviews/client results or automatic capability approval.
- Bound network/file/model inputs; no secret or private-text logging.

### Task 1: Field-compatible semantic Anki exports

**Files:** `services/semantic_anki.py`, focused new export service if warranted,
`domain/anki_semantics.py`, `services/anki_id_registry.py`, affected native Anki tests.

- [x] Add failing tests inspecting APKG model field names/order and values against
  `domain/exporting.py` for English/Portuguese, Japanese, Mandarin and Korean.
- [x] Test a headword and two inflections; `word`/equivalent is the displayed
  form; contextual explanation and exact audio survive; Image remains blank.
- [x] Reuse existing templates and field mappings with safe content. Keep A/B
  experiment distinction and dynamic-form identities; do not preselect topology.
- [x] Verify adding a form, changing rank/content, reexport and multilingual packages
  preserve semantic IDs and supported field contracts. No technical IDs on cards.
- [x] Run focused tests; report limitations and supply a sample package for inspection.

### Task 2: Source/model inventory and acquisition research

**Files:** `docs/multilingual-source-research.md`; source catalog data under the package.

- [x] Audit all 21 legacy frequency CSVs and the separate Korean bundle.
- [x] Research primary sources for all 22 languages: lexical senses, contextual
  annotated corpora, morphology models, licenses, attribution and access.
- [x] Identify concrete downloadable sources and extraction formats; distinguish
  linguistic metadata, observed frequency, textbook rank and synthetic test data.
- [x] Record exact official URLs and restrictions. Produce machine-readable
  candidates with no implied redistribution or linguistic approval.

### Task 3: Contextual morphology and local model lifecycle

**Files:** new `services/contextual_morphology.py`, `services/language_models.py`,
new tests; dependency changes owned by root for serialized lockfile edits.

- [x] Test NFC/case/diacritics, exact offsets, inflections, multiple candidates,
  same-spelling different analysis, unavailable models and invalid output.
- [x] Implement a uniform immutable analysis result and trusted adapters for
  Stanza's 19 European languages, Kiwi, Fugashi and Mandarin segmentation/POS.
- [x] Keep lexical sense resolution external and fail closed on uncertainty.
- [x] Implement explicit download/model inspection and pinned model fingerprints;
  normal application requests never silently download executable/model content.
- [x] Exercise installed analyzers and acquired Stanza models with real sentences.

### Task 4: Reproducible vocabulary preparation and evaluation

**Files:** new vocabulary preparation domain/services and native CLI subcommands;
existing runtime integration; focused unit/CLI/integration tests.

- [x] Test bounded corpus and dictionary ingestion, multiple source senses,
  deterministic identity/form/rank outputs, ambiguous quarantine and source drift.
- [x] Implement source catalog consumption and local preparation from source
  records with explicit review status, contextual occurrence analysis and explicit sense evidence.
- [x] Export reviewable candidate dataset, all observations, manifest, rejection
  reasons and workload forecast; connect qualified output to existing import.
- [x] Implement evaluation runner over declared UD test splits, per-language coverage
  and uncertainty. Independent goldens and target false-accept rates remain
  external inputs, explicitly unmeasured; automatic annotations are not human review.
- [x] Expose status/prepare/evaluate/model commands and integrate registered
  contextual matching into generation. Verify end-to-end local pilot behavior.

### Task 5: Actual source/model pilots and full-language readiness

- [x] Download legally accessible sources/models and prepare real per-language
  candidates and evaluation inputs with provenance and exact hashes.
- [x] Run all installed language adapters on real material, build review reports,
  and expose genuine missing inputs individually for each of the 22 profiles.
- [ ] External: validate paid live content/audio after actual linguistic review
  and an explicit bounded budget. No paid calls or fabricated approvals.
- [x] Exercise the accessible official Anki backend: import, exact fields, render,
  review and reimport with preserved IDs, scheduling and review history.
- [ ] External: complete the required desktop/mobile client acceptance matrix.

### Task 6: Integration, local database rehearsal, verification and delivery

- [x] Execute PostgreSQL migration/backup/restore on disposable databases if local
  binaries or a permitted container runtime are available.
- [x] Complete integration rerun: 299 passed outside the diagnosed AnyIO
  sandbox restriction. Focused regressions, scoped CI Ruff, lockfile, package
  build, wheel inspection and strict documentation build passed.
- [x] Review changes independently, resolve findings, record actual evidence and
  remaining external blockers. Preserve user changes and do not deploy.

## Delivery evidence

- Practical workflow: `docs/vocabulary-preparation.md`.
- Per-language actual sources, model status and diagnostic hashes:
  `docs/multilingual-readiness.md` and `docs/multilingual-readiness.json`.
- Verification evidence and domain commits: `ROADMAP_4_NATIVE_IMPLEMENTATION.md`.
- External gates are deliberately unchecked; software completion does not grant
  source redistribution, linguistic qualification or production approval.
