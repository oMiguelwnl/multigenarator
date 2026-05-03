# Research Summary: v1.2 Kindle Highlights and Template Refresh

**Project:** Multilang Anki Card Generator  
**Milestone:** v1.2 Kindle Highlights and Template Refresh  
**Researched:** 2026-05-03  
**Confidence:** HIGH for integration/export direction; MEDIUM for exact Kindle export normalization until real fixtures are validated.

## Executive Summary

v1.2 should add **Kindle highlights as a third deck input mode** beside existing frequency and custom word-list flows. The correct implementation is not a new app, new pipeline, or browser automation around Kindle Formatter; it is a deterministic pre-ingestion path that fetches highlights from WebDAV, normalizes them locally, extracts vocabulary candidates, and then reuses Multilang’s existing lexical grounding, text generation, audio, and genanki export infrastructure.

The core design decision is to introduce explicit **source profiles** for `frequency`, `word-list`, and `kindle-highlights`. Highlight mode needs different ingestion, richer-but-concise example rules, a separate Anki note type, no exported `Translation` field, `Definition` on the back, and English field names. Existing frequency/custom-word decks must remain stable and must not inherit highlight behavior.

The main risks are regression of shipped v1.0/v1.1 contracts, leaking WebDAV credentials or private reading data, vague Kindle Formatter parity, and invalid Anki template/media behavior. Mitigate by building regression/source-profile boundaries first, making local-file normalization fixture-driven before remote WebDAV, adding redacted import reports, and testing generated APKGs rather than only rendered HTML.

## Key Findings

### Stack Additions

- **Keep existing stack:** Python 3.12, uv, Typer, Pydantic v2, SQLAlchemy/Alembic, existing generation/audio/export services, Azure-first audio, and genanki remain the right base.
- **Add `defusedxml==0.7.1`:** required for safe parsing of WebDAV `PROPFIND` XML / `207 Multi-Status` responses.
- **Use `httpx==0.28.1` if not already pinned:** direct WebDAV methods (`PROPFIND`, `GET`) are enough; do not add a WebDAV-specific package for v1.2.
- **Use stdlib normalization tools:** `html.parser`, `html`, `re`, `unicodedata`, `hashlib`, `datetime`, `pathlib`, and `csv` are sufficient until real Kindle fixtures prove otherwise.
- **Optional dev dependency:** `respx==0.23.1` only if current HTTPX mocking is insufficient.
- **Do not add:** Playwright/Selenium, BeautifulSoup/lxml by default, pandas, new DB/queue, new LLM provider, or new Anki export library.

### Table-Stakes Features

- Configure WebDAV URL/username/secret without hard-coding or logging secrets.
- List and fetch Kindle export files via WebDAV, with clear auth/path/timeout/empty-directory failures.
- Accept a **local Kindle export file** through the same normalization path for tests and offline fallback.
- Locally normalize Kindle-exported HTML/text into deterministic highlight records, preserving diacritics, Cyrillic, Turkish characters, punctuation, source hash, record order, and provenance.
- Extract target-language vocabulary candidates from highlights with filtering, deterministic keys, dedupe, and a visible report of imported/rejected/duplicate/planned cards.
- Add `highlights` / `kindle-highlights` generation mode without changing frequency or custom word-list behavior.
- Generate highlight cards with word/headword, IPA, definition, concise richer example sentence, word audio, sentence audio, and blank `Image`.
- Export highlight cards with English fields and **no `Translation` field**; front shows prompt content, back shows `{{FrontSide}}` plus `Definition`.
- Refresh phonetics cards with the supplied front layout, `Sentence Translation` revealed on the back, removed `Notes`/`is_priming`/`is_sentence`, fixed field names, playable audio, and Multilang colors.

### Architecture Path

Implement highlights as:

```text
WebDAV or local file
  -> raw artifact by content hash
  -> KindleHighlightNormalizer
  -> HighlightVocabularyExtractor
  -> existing lexical ingestion/grounding
  -> existing text generation with highlight source profile
  -> existing Azure audio
  -> source-specific export mapping and genanki model
```

Recommended component changes:

- Add `SourceProfile` mapping for translation export, sentence length, note type, and template selection.
- Extend generation source type with `kindle-highlights` / `highlights` consistently.
- Add `domain.highlights` Pydantic contracts: source document, normalized highlight, vocabulary item.
- Add `KindleHighlightNormalizer` as a pure, fixture-tested local service.
- Add `HighlightVocabularyExtractor` with deterministic ordering, dedupe, and provenance.
- Add `WebDavHighlightSource` as a thin adapter only; normalizer consumes local raw artifacts, not live streams.
- Reuse existing DB tables where possible; store highlight metadata in provenance JSON for v1.2 rather than adding book/highlight tables prematurely.
- Add `HIGHLIGHT_EXPORT_CARD_FIELD_NAMES`, highlight model ID/name, source-specific template loading, and mixed-source export guard.
- Keep phonetics refresh isolated in `russian_phoneme_deck.py` and `templates/russian_phoneme_card.md`.

## Roadmap Implications

Phase numbering should begin at **Phase 09**.

### Phase 09: Source Profiles, Contracts, Privacy, and Regression Harness

**Rationale:** Protect shipped frequency/custom-word behavior before threading in a new source.  
**Delivers:** explicit source profiles, source-type constants, export field mapping guardrails, redaction rules, non-regression tests for existing decks.  
**Avoids:** highlights being treated as frequency, global schema renames, secret leaks, note-type collisions.  
**Research flag:** Standard patterns; no deeper research needed.

### Phase 10: Local Kindle Normalization and Candidate Extraction

**Rationale:** Local fixture-driven normalization is the core product behavior and should work before remote I/O.  
**Delivers:** highlight contracts, raw-to-normalized fixture tests, Kindle Formatter-style text artifacts, candidate extractor, dedupe/provenance, local-file CLI path.  
**Avoids:** brittle formatter automation, noisy tokens, lost sense context, malformed export crashes.  
**Research flag:** Needs fixture validation against real user Kindle exports.

### Phase 11: Highlight Ingestion into Existing Pipeline

**Rationale:** Prove highlights can reuse grounding, jobs, resume, duplicate prevention, and existing quality services.  
**Delivers:** highlight ingestion branch, input fingerprint based on content/candidate keys, provenance JSON, candidate reports, regression evidence for existing modes.  
**Avoids:** duplicate cards, timestamp-only reruns, context-free generation.  
**Research flag:** Standard implementation once Phase 10 contracts are stable.

### Phase 12: Highlight Generation Profile, Audio, and QA

**Rationale:** Highlight cards need a different study behavior but should reuse current generation/audio infrastructure.  
**Delivers:** richer-but-concise example policy, 6-16-ish token validation profile, target inclusion checks, no exported translation, prompt minimization, audio manifest collision tests.  
**Avoids:** long learner-hostile examples, wrong sense, private raw-highlight prompt dumps, media collisions.  
**Research flag:** Needs deeper QA tuning across supported languages.

### Phase 13: Highlight Template and Export

**Rationale:** Export should happen after source/profile behavior is stable; Anki field contracts are user-visible.  
**Delivers:** dedicated highlight note type/template, English fields, no `Translation`, `Definition` on back, centered responsive CSS, APKG/CSV/TSV snapshots, mixed-source export failure.  
**Avoids:** dangling fields, definition visible on front, fragile JS/media behavior, invalid note updates.  
**Research flag:** Standard Anki/genanki patterns; verify in Anki Desktop.

### Phase 14: WebDAV Fetch Adapter

**Rationale:** Remote fetch is valuable but should not block local highlight generation; isolate network variability.  
**Delivers:** settings/env config, `PROPFIND`/`GET`, safe XML parsing, content-hash artifact storage, idempotent imports, distinct failure messages, redacted sync report.  
**Avoids:** naive GET-only sync, duplicate imports, credential leaks, provider-specific coupling to one WebDAV server.  
**Research flag:** Needs validation against the real WebDAV provider after fake-server tests pass.

### Phase 15: Phonetics Template Refresh

**Rationale:** Independent renderer/export work; keep separate to reduce regression blast radius.  
**Delivers:** supplied front layout, `Sentence Translation` on back, removed unused fields, field-name typo cleanup, Multilang colors, focused phonetics APKG/template tests.  
**Avoids:** phonetics data-model churn, missing audio fields, dangling `Notes`/`is_priming`/`is_sentence` references.  
**Research flag:** Standard template work; no additional research needed.

### Phase 16: End-to-End Audit

**Rationale:** v1.2 crosses ingestion, generation, media, and export boundaries; unit tests are not enough.  
**Delivers:** local fixture -> generated highlight deck -> APKG import evidence, optional real WebDAV smoke, existing frequency/custom regression evidence, phonetics import evidence.  
**Avoids:** integration-only failures and Anki/media surprises.  
**Research flag:** No research; evidence-gathering phase.

## Recommended Requirement Categories

- **KINDLE-INGEST:** WebDAV config, listing/download, local-file fallback, idempotent manifest, failure reporting.
- **KINDLE-NORM:** local formatter-style parser, deterministic normalization, character preservation, rejection reasons, provenance.
- **KINDLE-CANDIDATES:** tokenization/filtering, lemma/headword normalization, duplicate strategy, report/dry-run.
- **HIGHLIGHT-MODE:** new deck mode, source profile, pipeline integration, no regression of frequency/custom flows.
- **HIGHLIGHT-GENERATION:** concise richer examples, sense/context handling, validators, prompt privacy, audio reuse.
- **HIGHLIGHT-EXPORT:** dedicated note type, English fields, no `Translation`, `Definition` on back, responsive Multilang template, APKG/CSV/TSV snapshots.
- **PHONETICS-TEMPLATE:** supplied front layout, `Sentence Translation` back reveal, removed unused fields, audio references, Multilang colors.
- **REGRESSION/SECURITY:** redaction, secret exclusion, fixture safety, existing-mode export stability, Anki import/reimport evidence.

## Risks and Watch-Outs

1. **Do not replace frequency decks.** Highlights are a new mode; frequency and custom word-list flows must remain regression-tested.
2. **Do not automate Kindle Formatter.** Define Multilang’s own local normalization contract with golden fixtures.
3. **Treat highlights as private data.** Redact credentials, paths, titles, raw text, and prompt payloads; keep raw downloads out of git.
4. **Do not reuse normal note types for highlight behavior.** Use dedicated model names/IDs and exact field lists.
5. **Avoid fragile Anki behavior.** Prefer native media fields; do not depend on autoplay JS or dynamic media filenames.
6. **WebDAV is not just GET.** Handle `PROPFIND`, `207 Multi-Status`, ETags, redirects, trailing slashes, timeouts, and auth errors.
7. **Richer examples still need bounds.** Validate target inclusion, sentence count, length, and complexity.
8. **Real Kindle fixtures are mandatory.** Exact HTML/text shape is the main unknown.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack additions | HIGH | HTTPX, defusedxml, stdlib parsing, Pydantic, SQLAlchemy, and genanki are well matched to the scope. |
| Feature scope | HIGH | User intent is explicit in project context and `alter_organizado.md`; research consistently supports separate highlight mode. |
| Architecture | HIGH | Source profiles plus fetch/normalize/extract/reuse-existing-pipeline is the clearest low-regression path. |
| WebDAV behavior | MEDIUM-HIGH | Protocol is clear, but real provider quirks must be tested. |
| Kindle normalization | MEDIUM | Needs real exported Kindle fixtures; external formatter is inspiration, not a formal spec. |
| Templates/export | HIGH | Anki/genanki constraints are clear; still requires import/reimport smoke evidence. |

## Sources

- `.planning/research/STACK.md` — stack additions and dependency guidance.
- `.planning/research/FEATURES.md` — v1.2 feature table stakes and requirement seeds.
- `.planning/research/ARCHITECTURE.md` — integration path, source profiles, component map, safe build order.
- `.planning/research/PITFALLS.md` — critical risks, mitigations, and phase placement.
- `.planning/PROJECT.md` — active v1.2 milestone constraints and current product state.
- `alter_organizado.md` — user-provided WebDAV, Kindle Formatter, highlight template, sentence, and phonetics requirements.

---
*Ready for requirements and roadmap: yes.*
