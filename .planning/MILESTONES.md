# Project Milestones: Multilang Anki Card Generator

Entries are kept newest first.

## ✅ v2.1 — Latin Google TTS Finalization (Shipped: 2026-06-22)

- Status: shipped
- Shipped: 2026-06-22

**Delivered:** Finalized the current 50-card Classical Latin MVP on an approved Google Translate TTS (`la`) word/sentence audio pack while keeping export fail-closed and removing active eSpeak NG or live ElevenLabs dependencies.

**Phases completed:** 29 (1 plan)

**Key accomplishments:**

- Locked Google Translate TTS `la` as the approved current Latin MVP provider.
- Preserved 100 approved word/sentence media artifacts with exact-text and manifest integrity gates.
- Recorded ElevenLabs as deferred after billing/quota failure and FineVoice as research-only.
- Verified APKG/CSV/TSV export readiness without an active eSpeak NG dependency.

**Evidence:** `.planning/phases/29-latin-elevenlabs-audio-refresh/29-VERIFICATION.md` (`status: passed`, 5/5 must-haves)

**Archives:**

- Roadmap: `.planning/milestones/v2.1-ROADMAP.md`
- Requirements: `.planning/milestones/v2.1-REQUIREMENTS.md`

**Closeout note:** Archived during the 2026-07-20 GSDD planning-state migration. This is a repo-local closeout claim, not a public release/tag claim.

---

## ✅ v2.0 — Classical Latin MVP (Shipped: 2026-06-08)

- Status: shipped
- Shipped: 2026-06-08

**Delivered:** A reviewed, reproducible 50-card Classical Latin deck path with frozen sources, lemma-frequency ordering, morphology and grammar evidence, Portuguese translations, approved audio gates, and APKG/CSV/TSV export.

**Phases completed:** 22-28 (27 plans recorded in the legacy roadmap)

**Key accomplishments:**

- Isolated Classical Latin from the modern-language frequency path.
- Froze a licensed/provenance-aware 50-card source and sentence pack.
- Added morphology, `Gramatica`, translation, review, and audio readiness gates.
- Exported a dedicated Latin note type with stable fields and packaged media.

**Evidence:** Phase 25-28 verification artifacts are present and passed; Phases 22-24 predate the current verifier artifact convention. The original milestone roadmap recorded v2.0 as shipped on 2026-06-08.

**Archives:**

- Roadmap: `.planning/milestones/v2.0-ROADMAP.md`
- Requirements: `.planning/milestones/v2.0-REQUIREMENTS.md`

**Closeout note:** Migrated from legacy GSD artifacts without retroactively claiming a current-schema milestone audit for Phases 22-24.

---

## v1.3 Card Quality Remediation and Deck Validation (Shipped: 2026-05-16)

**Delivered:** A card-quality hardening milestone that audits generated decks, remediates learner-facing text/audio defects, revises the normal-card export/template contract, and adds executable evidence that normalized issue categories stay covered.

**Phases completed:** 17-21 (16 plans, 27 best-effort tasks)

**Key accomplishments:**

- Added non-mutating APKG audit support with stable JSON/Markdown issue reports for normalized card-quality defects.
- Corrected IPA, Definition, and Translation remediation so exported learner-facing text avoids repeated word forms, morphology-only definitions, wrong known senses, and isolated-word translations.
- Removed redundant `Front of Card` from normal generated-card exports and kept responsive sentence audio isolated from highlight/manual/phonetics templates.
- Added exact word-audio integrity gates that regenerate corrupted reusable WORD audio or block APKG/CSV/TSV export before mismatched audio reaches learners.
- Added a shared v1.3 validation facade plus executable normalized issue fixtures, including whitespace-tolerant `sentence_audio` layout detection.
- Produced final scanner-readable milestone evidence proving 15/15 v1.3 requirements and existing deck-mode safety.

**Stats:**

- 5 phases, 16 plans, 27 best-effort tasks.
- 57 files changed from the v1.2 baseline snapshot used during closeout.
- 5,571 insertions and 74 deletions from that baseline snapshot.
- Focused closeout regression gate: 175 passed.

**Archives:**

- Roadmap: `.planning/milestones/v1.3-ROADMAP.md`
- Requirements: `.planning/milestones/v1.3-REQUIREMENTS.md`

**Known deferred items at close:** 1 (see `.planning/STATE.md` Deferred Items)

**What's next:** Define the next milestone with `/gsd-new-milestone`, including fresh requirements.

---

## v1.0 MVP (Shipped: 2026-04-29)

**Delivered:** A trust-first Python CLI pipeline that turns supported-language frequency decks or custom word lists into grounded, audio-backed, Anki-safe export artifacts.

**Phases completed:** 1-7 (34 plans total)

**Key accomplishments:**

- Built the `multilang generate` CLI path with supported-language validation, visible progress, resumability, and duplicate-safe reruns.
- Added lexical grounding for frequency decks and custom word lists with deterministic candidate identity, `wordfreq` frequency windows, and cached Kaikki lookup.
- Added text generation, validation, review reports, item-level regeneration, and a filtered Tatoeba secondary fallback path.
- Added Azure-first word and sentence audio synthesis with persistence, reuse, fallback accounting, and live/human verification evidence.
- Added fixed-schema export to `.apkg`, CSV, and TSV with stable note identity, blank `Image`, hidden/revealed `Translation`, and packaged media validation.
- Closed the milestone audit gap by proving representative custom and frequency inputs reach accepted text, audio, and export artifacts end to end.

**Stats:**

- 326 tracked files changed through HEAD before archival.
- 34,913 tracked insertions through HEAD before archival.
- 14,552 tracked Python LOC.
- 7 phases, 34 plans, 68 best-effort tasks.
- 11 days from first project commit to v1.0 closeout.

**Git range:** `4484e5d` -> `2e41502`

**Archives:**

- Roadmap: `.planning/milestones/v1.0-ROADMAP.md`
- Requirements: `.planning/milestones/v1.0-REQUIREMENTS.md`
- Audit: `.planning/milestones/v1.0-MILESTONE-AUDIT.md`

**Known deferred items at close:** 1 (see `.planning/STATE.md` Deferred Items)

**What's next:** Define the next milestone with `/gsd-new-milestone`, including fresh requirements.

---
