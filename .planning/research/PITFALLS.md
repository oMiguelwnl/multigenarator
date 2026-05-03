# v1.2 Pitfalls: Kindle Highlights and Template Refresh

**Project:** Multilang Anki Card Generator  
**Milestone:** v1.2 Kindle Highlights and Template Refresh  
**Researched:** 2026-05-03  
**Overall confidence:** HIGH for Anki/WebDAV/export-contract risks; MEDIUM for Kindle Formatter parity because the formatter is small and public but has no formal spec or releases.

## Context-Specific Risk Summary

v1.2 adds a new reading-derived input source to an already shipped Python generator. The main failure mode is not “can WebDAV fetch a file?”; it is accidentally weakening stable v1.0/v1.1 contracts while threading a new source, new note/template behavior, local normalization, and revised phonetics rendering through existing generation/export paths.

The roadmap should isolate this milestone into phases that first protect existing frequency/custom-word flows, then add secure ingestion, then normalize locally with fixture parity, then introduce highlight-mode generation and templates, and only then refresh phonetics templates with export/import evidence.

## Critical Pitfalls

### 1) Replacing frequency/custom-word flows instead of adding a third input mode

**What goes wrong:** Kindle highlights are implemented as “the new source” and code paths that previously handled frequency decks or custom word lists are edited in-place. The shipped 3-level frequency flow, stable ten-field schema, resume behavior, or custom-list flow regresses.

**Impact:** High. This would break validated v1.0 value while adding v1.2.

**Warning signs:**
- CLI flags or config names imply only one global `source` path.
- Tests for v1.0 frequency/custom list generation are skipped because templates changed.
- Highlight code branches on deck type inside low-level exporters or audio adapters.
- Existing note schema fields are renamed globally to satisfy the highlight template.

**Prevention:**
- Introduce `InputSource` / `DeckMode` as a boundary: `frequency`, `custom_words`, `highlights`.
- Keep canonical card/domain objects separate from Anki note-type renderers.
- Add non-regression tests proving existing frequency and custom word-list fixtures produce byte/stable-field-compatible exports except where intentionally versioned.
- Make “highlights replace wordfreq” a user-facing mode choice, not a codebase-wide replacement.

**Test / verification strategy:**
- Run one fixture per existing mode through generation -> audio manifest -> `.apkg`/CSV/TSV export.
- Snapshot the original ten fields: `SortIndex`, `word`, `Front of Card`, `IPA`, `Definitions`, `Example Sentence`, `Translation`, `word_audio`, `sentence_audio`, `Image`.
- Verify no highlight-specific note type appears in existing exports.

**Phase placement recommendation:** Phase 1 - integration boundary and regression harness before touching WebDAV.

---

### 2) Treating WebDAV as simple file download

**What goes wrong:** The importer assumes one URL maps directly to one static file and uses naive GET/listing logic. WebDAV servers expose collections, member URLs, redirects, trailing-slash behavior, XML `PROPFIND` responses, ETags, timestamps, locks, and partial failure statuses.

**Impact:** High. Ingestion becomes flaky, duplicates are imported, or changed highlights are missed.

**Warning signs:**
- Code hard-codes one filename and has no `PROPFIND` integration test.
- The sync state stores only “last run time” and not remote path + ETag/Last-Modified/content hash.
- 207 Multi-Status responses are not parsed.
- Paths fail when the collection URL lacks or gains a trailing slash.

**Prevention:**
- Model WebDAV as a sync adapter with explicit operations: discover collection, list candidates, fetch selected object, persist remote metadata.
- Use `Depth: 1` listing unless recursive sync is explicitly required.
- Store remote URL/path, ETag if available, last modified, size, content hash, and imported-at timestamp.
- Make ingestion idempotent: same remote content cannot create duplicate highlight records.
- Handle redirects, 401/403/404/423/5xx, network timeouts, and malformed XML distinctly.

**Test / verification strategy:**
- Mock WebDAV `PROPFIND` 207 Multi-Status, direct GET, redirects, missing trailing slash, auth failure, and stale ETag cases.
- Re-run sync twice against identical fixtures; assert zero duplicates.
- Change only remote content hash; assert existing import record versions instead of creating unrelated rows.

**Phase placement recommendation:** Phase 2 - WebDAV ingestion adapter and sync-state model.

**Sources:** RFC 4918 defines WebDAV collections, `PROPFIND`, `Depth`, ETag handling, Multi-Status, and security considerations.

---

### 3) Leaking WebDAV credentials or learner reading data

**What goes wrong:** Credentials, full highlight text, book titles, author names, or remote paths end up in logs, screenshots, CSV debug artifacts, test fixtures, exception traces, or AI-provider prompts.

**Impact:** Critical. WebDAV credentials grant access to personal files; highlights reveal what the learner reads and studies.

**Warning signs:**
- Config examples include real URLs/usernames/passwords.
- Failed HTTP requests log full authorization headers or full response bodies.
- Raw highlights are sent to an LLM before local minimization.
- Golden fixtures are copied from a real Kindle library without redaction.
- `.env`, local config, or fetched highlight files are candidates for commit.

**Prevention:**
- Use environment variables or a local secrets file excluded from git; never store credentials in `.planning`, test fixtures, or generated decks.
- Redact `Authorization`, usernames, passwords, tokens, remote paths, book titles, and raw highlight text in logs.
- Persist only what is needed: normalized candidate terms, minimal provenance IDs, content hashes, and optional redacted source labels.
- Default to local parsing before AI; if sending any source text to AI, send only the minimal selected highlight snippet and record user-visible consent/config.
- Add `.gitignore` entries for downloaded WebDAV files, raw Kindle exports, local sync cache, and secrets.

**Test / verification strategy:**
- Unit-test log redaction and exception formatting.
- Add a secret-scanning check over fixtures and generated artifacts.
- Use fake WebDAV credentials and synthetic book/highlight fixtures only.
- Verify AI prompt fixtures do not contain full raw highlight dumps.

**Phase placement recommendation:** Phase 1 - security/privacy baseline; Phase 2 - WebDAV adapter; Phase 4 - AI generation prompt minimization.

**Sources:** RFC 4918 security sections call out authentication, denial-of-service, privacy around properties/locks, XML entity risks, and malicious content hosting.

---

### 4) Copying Kindle Formatter output superficially without defining normalization semantics

**What goes wrong:** The local formatter only “splits by comma” and misses real Kindle export cleanup: metadata lines, separators, blank lines, clipped highlights, repeated highlights, punctuation, encodings, language-specific punctuation, multi-line highlights, and book/title boundaries.

**Impact:** High. The generated vocabulary set becomes noisy and non-reproducible.

**Warning signs:**
- There is no fixture pair of raw Kindle export -> expected normalized output.
- Parser logic depends on one personal export sample.
- Normalizer does not preserve enough provenance to explain why a candidate exists.
- Comma splitting corrupts phrases, decimals, names, clauses, or quoted text.

**Prevention:**
- Treat Kindle Formatter as behavior inspiration, not a spec. Define Multilang’s own local normalization contract.
- Build parser stages: decode -> segment records -> remove Kindle metadata -> normalize whitespace/punctuation -> deduplicate -> extract candidate terms/snippets.
- Preserve stable source provenance: book/source hash, highlight index, raw snippet hash, normalized text.
- Add fixture families for accented characters, em dashes, quotes, multi-line highlights, duplicate highlights, empty notes, and malformed exports.

**Test / verification strategy:**
- Golden tests for raw export fixtures and normalized comma-separated/text outputs.
- Differential smoke check against Kindle Formatter for representative examples, but do not rely on browser automation.
- Property tests for idempotence: `normalize(normalize(x)) == normalize(x)` where applicable.

**Phase placement recommendation:** Phase 3 - local parsing and normalization, before any card generation.

**Sources:** `pch/kindle-formatter` README says it is a simple browser-only tool for cleaning Kindle desktop exports into plain text and that highlights are processed locally in the browser; it has no formal API/release contract.

---

### 5) Losing source context needed for sense disambiguation

**What goes wrong:** Highlight ingestion extracts isolated words, discards surrounding sentence/book context, and then uses the existing custom-word generation path. Polysemous words get the wrong definition/example because reading context was thrown away.

**Impact:** High for learning quality.

**Warning signs:**
- Highlight candidate records contain only `word` and `language`.
- Definition generation prompt does not include the original highlight sentence/snippet.
- QA cannot explain which highlight produced a card.
- Common words from highlights receive generic frequency-deck definitions instead of context-relevant senses.

**Prevention:**
- Store both candidate term and source snippet/context window.
- Add `source_mode=highlights`, `source_snippet`, `source_language`, `source_hash`, and `candidate_extraction_reason` metadata.
- Use the highlight snippet for sense selection, but generate a new concise example sentence rather than copying the full highlight by default.
- Mark low-confidence sense matches for review instead of exporting silently.

**Test / verification strategy:**
- Fixture with ambiguous terms; assert selected definition follows highlight context.
- Verify exported highlight cards do not expose private source snippets unless explicitly intended.
- Add review report fields that map card -> source highlight ID/hash.

**Phase placement recommendation:** Phase 3 - normalized candidate schema; Phase 4 - highlight-specific generation.

---

### 6) Generating highlight cards by reusing the translation-bearing normal deck schema

**What goes wrong:** Highlight decks still include `Translation`, put `Definition` on the front, or reuse field names from the frequency note type. The new template requirement says `Definition` belongs on the back, there is no `Translation` field, field names should be English, and layout should be centered/responsive.

**Impact:** High. The deck may import but not match the requested study behavior.

**Warning signs:**
- Template conditionally hides `Translation` instead of using a separate highlight note type.
- The exporter fills blank translation fields for highlight decks “for compatibility.”
- Front template includes too much answer information.
- Field names mix Portuguese (`Palavra`, `Significado`) with English (`Definition`).

**Prevention:**
- Define a dedicated highlight note type with explicit fields, e.g. `SortIndex`, `Word`, `IPA`, `Example Sentence`, `Definition`, `word_audio`, `sentence_audio`, `Image` plus any stable hidden ID if needed.
- Keep highlight field names English and template-specific; do not globally rename existing fields.
- Use a renderer map from canonical domain card -> note type fields.
- Add a template contract test: front has no definition/translation; back has definition; no `Translation` field exists.

**Test / verification strategy:**
- Snapshot front/back HTML and field list for highlight `.apkg`/CSV.
- Import into Anki Desktop or inspect generated model fields; confirm no missing field replacements.
- Verify cards remain usable when optional `IPA`, audio, or `Image` is blank.

**Phase placement recommendation:** Phase 5 - highlight Anki note type/template/export.

**Sources:** Anki field replacements are case-sensitive; `{{FrontSide}}` is only valid on the back; media references should live in fields rather than constructed from templates.

---

### 7) Breaking Anki update/import semantics by changing note types in place

**What goes wrong:** Existing note types are modified to add/remove fields for highlights or phonetics. Anki can import missing notes, but updating existing notes becomes unreliable when note types change; newer Anki versions have merge behavior, but relying on user-side merging is brittle.

**Impact:** High. Users may get duplicates, failed updates, or full-sync surprises.

**Warning signs:**
- One model ID/name is reused for incompatible field sets.
- Existing templates lose fields like `Translation` because highlight decks do not need them.
- The phonetics note type removes `Notes`, `is_priming`, or `is_sentence` without versioning/migration tests.
- Re-import tests are missing.

**Prevention:**
- Version note types intentionally: e.g. `Multilang Normal v1`, `Multilang Highlight v1`, `Multilang Phonetics v2`.
- Preserve old model IDs/field IDs where update compatibility is required; otherwise use new model names and document migration.
- Keep stable note identity independent of display field changes.
- Test import and re-import behavior on Anki 23.10+ assumptions instead of relying on manual merges.

**Test / verification strategy:**
- Generate v1.1 normal deck and v1.2 normal/highlight/phonetics decks; import/reimport in a disposable Anki profile.
- Assert existing normal cards update or remain untouched as intended.
- Confirm highlight and phonetics note types do not collide with normal decks.

**Phase placement recommendation:** Phase 5 - export contract; Phase 6 - phonetics template refresh.

**Sources:** Anki packaged deck docs warn that updates are generally not possible when the note type changes; Anki 23.10 adds more merge/update options but template/field IDs matter.

---

### 8) Making templates depend on unsupported or fragile Anki behavior

**What goes wrong:** Template refresh uses browser JavaScript assumptions, autoplay logic, dynamic media references, CSS that only works on desktop, or fields that no longer exist. The supplied highlight template includes autoplay JS and Portuguese field names; the phonetics template includes fields targeted for removal.

**Impact:** Medium to high. Cards may work in preview but fail on AnkiMobile/AnkiDroid or exported decks.

**Warning signs:**
- Template references `{{Notes}}`, `{{is_priming}}`, `{{is_sentence}}`, `{{Palavra}}`, or `{{Significado}}` after field changes.
- Audio is only triggered by custom JS rather than Anki media fields.
- CSS uses fixed top spacing instead of flexible centering.
- Responsiveness is checked only in browser dev tools, not Anki.

**Prevention:**
- Prefer Anki-native `[sound:file]` media fields and simple field replacements.
- Remove or isolate autoplay JS; do not depend on autoplay being allowed.
- Implement responsive centering with conservative CSS (`min-height`, flex column, safe max-width, mobile-friendly font sizing).
- Run a field-reference linter over every template and model field set.

**Test / verification strategy:**
- Static parse templates and fail if any `{{Field}}` reference is not in the note type.
- Snapshot rendered HTML for empty and full optional fields.
- Human import/playback check in Anki Desktop; if possible, spot-check AnkiMobile/AnkiDroid later.

**Phase placement recommendation:** Phase 5 - highlight templates; Phase 6 - phonetics template refresh.

**Sources:** Anki docs state field names are case-sensitive; `FrontSide` audio does not automatically replay; media references constructed from field names are unsupported.

---

### 9) Overcorrecting example sentences into long, complex learner-hostile text

**What goes wrong:** The new rule says highlight examples can be grammatically richer, but generation creates long sentences, embedded clauses, idioms, or rare constructions that obscure the target word.

**Impact:** Medium-high. The deck feels more authentic but less studyable.

**Warning signs:**
- Average sentence length rises sharply compared with v1.1.
- Sentences require advanced grammar unrelated to the target word.
- TTS sentence audio becomes long and fatiguing.
- Generated examples no longer contain the target lemma/form clearly.

**Prevention:**
- Define explicit bounds: “concise but richer” means one natural sentence, target word present, one optional subordinate/prepositional phrase, no paragraph-length outputs.
- Use language-aware length bands instead of one universal character limit.
- Keep examples generated from lexical context but not copied verbatim from private highlights unless desired.
- Validate target inclusion, sentence count, length, punctuation, and banned complexity patterns.

**Test / verification strategy:**
- Add golden examples for each supported language category.
- Track sentence length distribution and rejection reasons in review reports.
- Run validator fixtures where examples are too short, too long, missing target, or too complex.

**Phase placement recommendation:** Phase 4 - highlight-specific generation and QA rules.

---

### 10) Ignoring malformed, adversarial, or huge highlight files

**What goes wrong:** The importer trusts remote content. A corrupted export, huge file, unusual encoding, HTML/script-like text, XML entity payload, or binary file causes crashes, memory blowups, bad prompts, or unsafe rendered fields.

**Impact:** High for robustness and security.

**Warning signs:**
- Parser reads entire remote content without size limits.
- No content-type/extension validation.
- Raw highlight text is inserted into HTML templates without escaping/sanitization.
- XML parsing for WebDAV allows external entities.

**Prevention:**
- Enforce max file size, allowed content types/extensions, decode policy, and timeout limits.
- Use safe XML parsing for WebDAV responses; disable external entity resolution.
- Escape user-derived text before inserting into HTML fields; allow only intentional Anki media markup.
- Quarantine failed imports with redacted error summaries.

**Test / verification strategy:**
- Fuzz malformed exports, invalid UTF-8, very long lines, embedded HTML/script, and malicious XML entity samples.
- Assert importer fails closed with no partial card generation.
- Verify rendered template output escapes raw highlight text.

**Phase placement recommendation:** Phase 2 - WebDAV adapter; Phase 3 - parser/normalizer hardening.

**Sources:** RFC 4918 notes XML entity and malicious content risks in WebDAV security considerations.

---

## Moderate Pitfalls

### 11) Poor duplicate strategy across highlight, custom, and frequency decks

**What goes wrong:** The same word appears in a frequency deck and a highlight deck, or in multiple books/highlights, and the system either suppresses useful context-specific cards or floods the user with duplicates.

**Impact:** Medium-high.

**Prevention:**
- Deduplicate at two levels: exact source highlight duplicates, and configurable lexical duplicates.
- Keep highlight deck identity separate from frequency identity: same lemma can have a distinct highlight-sense card when context differs.
- Report duplicates instead of silently dropping them.

**Test / verification strategy:**
- Fixtures with same word in multiple highlights and existing custom list.
- Assertions for exact duplicate suppression and context-specific retention.

**Phase placement recommendation:** Phase 3 - candidate normalization; Phase 4 - card selection.

---

### 12) Treating book/highlight language as globally equal to target language

**What goes wrong:** Highlights from bilingual text, quotes, names, or mixed-language passages are processed as the selected target language.

**Impact:** Medium.

**Prevention:**
- Detect/validate language at highlight snippet and candidate level.
- Allow user override but flag mismatches.
- Reject or review candidates whose language does not match the deck language.

**Test / verification strategy:**
- Mixed-language fixtures and proper-noun-heavy highlights.
- QA report listing rejected language mismatches.

**Phase placement recommendation:** Phase 3 - normalization and candidate filtering.

---

### 13) Audio naming collisions between deck modes

**What goes wrong:** Highlight word/sentence audio files use the same filenames as frequency/custom cards, causing packaged media collisions or stale playback.

**Impact:** Medium.

**Prevention:**
- Include deck mode, language, normalized note ID, audio type, voice ID, and synthesis hash in media filenames or manifests.
- Keep media references inside fields and package all referenced media.

**Test / verification strategy:**
- Generate normal and highlight decks containing the same word; assert media names differ or hashes match intentionally.
- Import `.apkg` and run Anki media check manually/automated where possible.

**Phase placement recommendation:** Phase 4 - generation/audio; Phase 5 - export packaging.

---

### 14) Phonetics template refresh accidentally changes generation semantics

**What goes wrong:** A visual template change leaks back into phonetics data generation: fields are removed from data models before confirming whether they are unused, `Sentence Translation` stops being populated, or audio fields change names.

**Impact:** Medium-high.

**Prevention:**
- Treat phonetics refresh as a renderer/export change unless requirements explicitly require generation-model changes.
- Remove `Notes`, `is_priming`, and `is_sentence` only from the note type/template after proving no runtime code depends on them.
- Add a phonetics fixture asserting front layout, back `Sentence Translation`, and audio field references.

**Test / verification strategy:**
- Static field-reference linter.
- Focused phonetics export/import smoke test with word audio, letter audio, sentence audio, and sentence translation.

**Phase placement recommendation:** Phase 6 - phonetics template refresh after highlight export is stable.

---

## Minor Pitfalls

### 15) No user-visible sync/reporting summary

**What goes wrong:** The user cannot tell whether WebDAV import found files, skipped duplicates, rejected malformed highlights, or generated cards.

**Prevention:** Emit a redacted sync report: files discovered, files fetched, highlights parsed, candidates extracted, duplicates skipped, cards generated, cards requiring review.

**Phase placement recommendation:** Phase 2 and Phase 4.

### 16) Unclear fallback for WebDAV unavailable/offline mode

**What goes wrong:** Generation blocks entirely when WebDAV is down, even if a previously downloaded export or local file could be used.

**Prevention:** Support explicit local-file import path and cached-last-fetch behavior with clear warnings.

**Phase placement recommendation:** Phase 2.

### 17) Planning around one personal WebDAV provider only

**What goes wrong:** The code accidentally fits `https://otaru.infini-cloud.net/dav/` quirks and fails against other WebDAV-compliant servers.

**Prevention:** Keep provider-specific behavior in config/adapter tests; rely on RFC-level WebDAV concepts for core logic.

**Phase placement recommendation:** Phase 2.

## Phase Placement Matrix

| Recommended Phase | Risks to Address | Required Evidence Before Moving On |
|---|---|---|
| **Phase 1 - Contracts, privacy, and regression harness** | Existing flows regress; credentials/log leaks; note-type collision strategy unclear | Existing frequency/custom fixtures still pass; redaction tests pass; deck-mode and note-type contracts documented |
| **Phase 2 - WebDAV ingestion adapter** | Naive GET-only WebDAV; bad sync state; auth failures; offline behavior | Mock WebDAV `PROPFIND`/GET tests, idempotent sync test, redacted sync report, local-file fallback |
| **Phase 3 - Local Kindle normalization and candidate extraction** | Formatter parity gaps; malformed files; lost context; duplicate chaos; language mismatch | Golden raw->normalized fixtures, candidate provenance records, parser hardening tests, duplicate/language reports |
| **Phase 4 - Highlight-specific generation and QA** | Wrong sense; too-long examples; prompt privacy; audio/media collisions | Ambiguous-term fixtures, sentence quality validators, prompt minimization tests, audio manifest tests |
| **Phase 5 - Highlight template and export** | Wrong fields; definition visible on front; translation retained; Anki import/update breakage | Highlight note type snapshot, template field linter, `.apkg` import/reimport smoke test |
| **Phase 6 - Phonetics template refresh** | Removed fields break runtime; missing `Sentence Translation`; mobile/Anki template fragility | Phonetics field linter, export/import smoke test, visual/template snapshots |
| **Phase 7 - End-to-end audit** | Integrated pipeline only works in unit tests | WebDAV/local fixture -> normalized candidates -> generated highlight deck -> `.apkg` import evidence; existing mode regression evidence |

## Most Important Roadmap Warnings

1. **Do not start with the template.** First freeze deck-mode boundaries and protect existing exports.
2. **Treat WebDAV and raw highlights as private data.** Redaction, local parsing, and prompt minimization are milestone requirements, not polish.
3. **Make normalization fixture-driven.** Kindle Formatter is not a stable API; Multilang needs its own documented behavior.
4. **Use separate note types for separate study behaviors.** Highlight and phonetics templates should not mutate the normal frequency deck contract.
5. **Verify in Anki, not just generated HTML.** Field replacement, media packaging, and note-type update behavior are Anki integration contracts.

## Sources

- Project context: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `alter_organizado.md` — HIGH
- RFC 4918 WebDAV specification: https://www.rfc-editor.org/rfc/rfc4918 — HIGH
- Anki Manual - Field Replacements: https://docs.ankiweb.net/templates/fields.html — HIGH
- Anki Manual - Packaged Decks / updating note types: https://docs.ankiweb.net/importing/packaged-decks.html — HIGH
- Kindle Formatter GitHub README: https://github.com/pch/kindle-formatter — MEDIUM
