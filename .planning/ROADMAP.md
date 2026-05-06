# Roadmap: Multilang Anki Card Generator

## Milestones

- [x] **v1.0 MVP** - Phases 1-7 shipped 2026-04-29. Archive: [v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md). Requirements: [v1.0-REQUIREMENTS.md](./milestones/v1.0-REQUIREMENTS.md).
- [x] **v1.1 Card Quality Refresh** - Phase 08 completed 2026-05-02 with audio prominence, AI-generated pronunciation, spoken-form display, and normal deck CSS refresh from `total.md`.
- [ ] **v1.2 Kindle Highlights and Template Refresh** - Add Kindle highlight ingestion, local normalization, highlight cards/export, WebDAV fetch, phonetics template refresh, and evidence that existing modes still work.

## Current Focus

Phase 11: Highlight Pipeline Integration.

## Phases

- [x] **Phase 08: Card Quality Refresh** - Generated non-phonetics Anki cards have prominent Azure word audio, AI-generated IPA, readable spoken-form hints beside IPA, and the user-provided normal deck styling.
- [x] **Phase 09: Source Profiles, Privacy, and Regression Boundary** - Existing frequency/custom decks stay stable while highlight mode, source profiles, and redaction boundaries are introduced.
- [x] **Phase 10: Local Kindle Normalization and Candidate Extraction** - Local Kindle exports become deterministic normalized highlights and reviewable vocabulary candidates without external formatter dependency. (completed 2026-05-05)
- [x] **Phase 11: Highlight Pipeline Integration** - Highlight candidates enter the existing job, grounding, resume, and duplicate-prevention flow as a new deck mode. (completed 2026-05-05)
- [x] **Phase 12: Highlight Generation, Audio, and QA** - Highlight cards receive privacy-aware text generation, richer concise examples, validation, and audio. (completed 2026-05-05)
- [x] **Phase 13: Highlight Export and Template** - Highlight decks export with a dedicated note type, English fields, no Translation field, and responsive Definition-on-back cards. (completed 2026-05-06)
- [ ] **Phase 14: WebDAV Highlight Fetch Adapter** - Kindle highlight exports can be fetched securely from WebDAV with clear failures and idempotent import summaries.
- [ ] **Phase 15: Phonetics Template Refresh** - Phonetics cards use the supplied layout, sentence translation back reveal, Multilang colors, and no unused fields.
- [ ] **Phase 16: End-to-End v1.2 Audit** - Local Kindle highlights, highlight export, phonetics export, and existing-mode regressions are proven with evidence.

## Phase Details

### Phase 08: Card Quality Refresh

**Goal**: Generated non-phonetics Anki cards have prominent Azure word audio, AI-generated IPA, readable spoken-form hints beside IPA, and the user-provided normal deck styling.  
**Depends on**: Phase 5, Phase 6  
**Requirements**: QUAL-AUDIO-01, QUAL-PRON-01, QUAL-PRON-02, QUAL-THEME-01  
**Success Criteria** (what must be TRUE):
  1. User hears prominent Azure word audio on generated non-phonetics cards while sentence audio remains usable.
  2. User sees AI-generated IPA rather than Kaikki IPA on generated card candidates.
  3. User sees spoken-form hints next to IPA on exported generated cards.
  4. User sees the supplied normal deck CSS without changes to the phonetics deck.
**Plans**: 4 plans complete

Plans:

- [x] 08-01-PLAN.md — Add Azure SSML prominence for word audio while preserving sentence audio behavior.
- [x] 08-02-PLAN.md — Add AI pronunciation generation and replace Kaikki IPA for generated card candidates.
- [x] 08-03-PLAN.md — Persist spoken form and export `/ipa/ (spoken-form)` on every generated card.
- [x] 08-04-PLAN.md — Apply the supplied normal deck CSS without changing the phonetics deck.
**UI hint**: yes

### Phase 09: Source Profiles, Privacy, and Regression Boundary

**Goal**: Existing generation modes remain stable while highlight-specific behavior and privacy rules become explicit boundaries.  
**Depends on**: Phase 08  
**Requirements**: MODE-02, SEC-01, SEC-02  
**Success Criteria** (what must be TRUE):
  1. User can still generate frequency decks with the existing field, audio, and export contracts after highlight source support is introduced.
  2. User can still generate custom word-list decks without highlight note types, fields, or sentence rules leaking into that flow.
  3. User's WebDAV credentials, raw highlight files, book metadata, and private reading text are redacted from logs, errors, reports, and commit candidates.
  4. User receives regression test evidence that existing frequency and custom generation, audio, and export contracts still work before highlight work proceeds.
**Plans**: 5 plans complete

Plans:

- [x] 09-01-PLAN.md — Define explicit source-profile contracts while preserving existing generation modes.
- [x] 09-02-PLAN.md — Apply source-profile boundaries to export field and note-type selection.
- [x] 09-03-PLAN.md — Add privacy redaction helpers and local artifact ignore rules.
- [x] 09-04-PLAN.md — Create v1.2 existing-mode regression evidence before highlight work proceeds.
- [x] 09-05-PLAN.md — Close the T-09-02 privacy leak in unsupported source-profile errors.

### Phase 10: Local Kindle Normalization and Candidate Extraction

**Goal**: A local Kindle export file can become deterministic normalized highlights and reviewable target-language vocabulary candidates.  
**Depends on**: Phase 09  
**Requirements**: INGEST-03, NORM-01, NORM-02, NORM-03, CAND-01, CAND-02, CAND-03  
**Success Criteria** (what must be TRUE):
  1. User can process a local Kindle HTML or text export without using the external Kindle Formatter website.
  2. User keeps target-language characters, punctuation, record order, and source provenance in normalized highlight records.
  3. User receives clear rejected-highlight reasons for unusable, malformed, empty, unsafe, or language-mismatched fragments instead of silent continuation.
  4. User receives deterministic vocabulary candidates for all supported languages with duplicate filtering and first-seen ordering.
  5. User can review imported highlight count, extracted candidate count, rejected count, duplicate count, and planned card count before expensive generation.
**Plans**: 4 plans

Plans:

- [x] 10-01-PLAN.md — Define local Kindle highlight contracts and deterministic HTML/text parsing.
- [x] 10-02-PLAN.md — Extract deterministic filtered vocabulary candidates from normalized highlights.
- [x] 10-03-PLAN.md — Add a privacy-safe local Kindle import preview and count-only CLI command.
- [x] 10-04-PLAN.md — Prove the local parser-to-preview flow with integration and regression evidence.

### Phase 11: Highlight Pipeline Integration

**Goal**: Highlight candidates run through the existing Multilang job pipeline as a duplicate-safe `highlights` deck mode.  
**Depends on**: Phase 10  
**Requirements**: MODE-01, INGEST-04  
**Success Criteria** (what must be TRUE):
  1. User can choose a `highlights` deck mode alongside frequency-deck and custom word-list modes.
  2. User can rerun the same highlight import without duplicate cards because content hashes, candidate keys, and import manifests are stable.
  3. User sees a visible import summary showing what was reused, skipped as duplicate, newly planned, or blocked.
  4. User's highlight candidates preserve enough internal provenance for audit while using the existing grounding, job, and resume behavior.
**Plans**: 4 plans

Plans:

- [x] 11-01-PLAN.md — Define stable content-derived highlight import and candidate identity.
- [x] 11-02-PLAN.md — Persist private highlight records separately from safe import manifests.
- [x] 11-03-PLAN.md — Wire highlights through lexical grounding, job orchestration, resume, and duplicate prevention.
- [x] 11-04-PLAN.md — Expose public `generate --source highlights` and count-only lifecycle summaries.

### Phase 12: Highlight Generation, Audio, and QA

**Goal**: Highlight-mode cards receive the requested learner-facing content, privacy-aware generation, validation, and playable audio.  
**Depends on**: Phase 11  
**Requirements**: GEN-01, GEN-02, GEN-03  
**Success Criteria** (what must be TRUE):
  1. User receives highlight cards with word or headword, IPA and spoken-pronunciation behavior, definition, example sentence, word audio, sentence audio, and blank `Image`.
  2. User receives concise but grammatically richer highlight examples that include the target word and pass language and length validation.
  3. User's private highlight text is minimized or redacted in prompts, reports, and errors while preserving internal source provenance for audit and sense/context use.
  4. User can distinguish highlight generation QA outcomes from frequency/custom QA outcomes in review evidence.
**Plans**: 4 plans

Plans:

- [x] 12-01-PLAN.md — Apply highlight source-profile validation for richer examples without Translation dependency.
- [x] 12-02-PLAN.md — Add minimized, redacted highlight context to provider/local example generation.
- [x] 12-03-PLAN.md — Prove highlight card content, word audio, sentence audio, and blank Image assembly.
- [x] 12-04-PLAN.md — Add source-aware highlight QA reports and regression evidence.

### Phase 13: Highlight Export and Template

**Goal**: Generated highlight cards export to Anki-compatible artifacts with the requested dedicated study template.  
**Depends on**: Phase 12  
**Requirements**: EXPORT-01, EXPORT-02, EXPORT-03  
**Success Criteria** (what must be TRUE):
  1. User can export highlight decks to APKG, CSV, and TSV with a dedicated highlight note type, exact English field names, and no `Translation` field.
  2. User sees highlight card fronts with prompt-side content only and card backs with `{{FrontSide}}`, an answer divider, and `Definition`.
  3. User sees centered, responsive, Multilang-colored highlight cards with safe packaged media references.
  4. User receives export validation that no highlight template contains dangling field references or mixed-source note model collisions.
**Plans**: 3 plans
**UI hint**: yes

Plans:

- [x] 13-01-PLAN.md — Create the dedicated highlight template and source-aware template validation.
- [x] 13-02-PLAN.md — Wire the validated highlight template into APKG export with media and mixed-source safety.
- [x] 13-03-PLAN.md — Prove strict highlight CSV/TSV/APKG export evidence and existing-mode regression boundaries.

### Phase 14: WebDAV Highlight Fetch Adapter

**Goal**: Kindle highlight exports can be fetched from a configured WebDAV source without leaking secrets or masking remote failures.  
**Depends on**: Phase 13  
**Requirements**: INGEST-01, INGEST-02  
**Success Criteria** (what must be TRUE):
  1. User can configure Kindle WebDAV URL, username, and secret without editing source code or exposing credentials in logs or artifacts.
  2. User can list remote Kindle highlight exports, select a file, and fetch it into the same local normalization path used by file imports.
  3. User receives distinct auth, path, network, malformed response, and empty-source failure messages.
  4. User can rerun WebDAV fetches against unchanged content and see an idempotent, redacted sync summary.
**Plans**: TBD

### Phase 15: Phonetics Template Refresh

**Goal**: Phonetics exports use the provided front layout and refreshed back behavior without breaking existing Russian phonetics audio.  
**Depends on**: Phase 13  
**Requirements**: PHON-01, PHON-02, PHON-03  
**Success Criteria** (what must be TRUE):
  1. User sees phonetics card fronts using the provided layout for spellings, sound, letter audio, example word, word audio, word translation, example sentence, and sentence audio.
  2. User sees `Sentence Translation` revealed on the phonetics card back using Multilang colors.
  3. User receives phonetics exports without `Notes`, `is_priming`, or `is_sentence` fields or dangling references.
  4. User can still play existing Russian phonetics letter, word, and sentence audio after the template refresh.
**Plans**: TBD
**UI hint**: yes

### Phase 16: End-to-End v1.2 Audit

**Goal**: The complete v1.2 flow is proven from representative inputs through importable Anki artifacts, with regressions and privacy evidence checked.  
**Depends on**: Phase 14, Phase 15  
**Requirements**: EVID-01  
**Success Criteria** (what must be TRUE):
  1. User receives end-to-end evidence that a local Kindle fixture becomes generated highlight cards and importable Anki exports.
  2. User receives phonetics template export evidence showing the refreshed field set, layout behavior, and audio references.
  3. User receives regression evidence that existing frequency and custom generation, audio, and export contracts still pass after all v1.2 changes.
  4. User receives a final audit summary showing no unmapped v1.2 requirements, no known secret leaks, and clear remaining caveats.
**Plans**: TBD

## Progress

| Milestone | Phases | Plans | Status | Shipped |
|-----------|--------|-------|--------|---------|
| v1.0 MVP | 1-7 | 34/34 | Complete | 2026-04-29 |
| v1.1 Card Quality Refresh | 8 | 4/4 | Complete | 2026-05-02 |
| v1.2 Kindle Highlights and Template Refresh | 9-16 | 5/9+TBD | In progress | - |

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 08. Card Quality Refresh | 4/4 | Complete | 2026-05-02 |
| 09. Source Profiles, Privacy, and Regression Boundary | 5/5 | Complete | 2026-05-04 |
| 10. Local Kindle Normalization and Candidate Extraction | 4/4 | Complete    | 2026-05-05 |
| 11. Highlight Pipeline Integration | 4/4 | Complete   | 2026-05-05 |
| 12. Highlight Generation, Audio, and QA | 4/4 | Complete    | 2026-05-05 |
| 13. Highlight Export and Template | 3/3 | Complete    | 2026-05-06 |
| 14. WebDAV Highlight Fetch Adapter | 0/TBD | Not started | - |
| 15. Phonetics Template Refresh | 0/TBD | Not started | - |
| 16. End-to-End v1.2 Audit | 0/TBD | Not started | - |
