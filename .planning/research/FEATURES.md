# Feature Landscape: v1.2 Kindle Highlights and Template Refresh

**Domain:** reading-derived vocabulary deck generation for an existing multilingual Anki card generator  
**Project:** Multilang  
**Researched:** 2026-05-03  
**Overall confidence:** MEDIUM-HIGH

## Executive Take

v1.2 should add a **third input mode**: Kindle highlights from WebDAV. It should not replace the shipped frequency-deck or custom word-list flows. The user-visible value is: “I exported/highlighted while reading; Multilang finds those highlights, normalizes them locally, extracts useful vocabulary candidates, and produces an Anki deck whose card behavior matches reading-derived study.”

For highlight decks, the product should optimize for **context, deduplication, and clean review behavior**, not for the 3×1000 frequency-deck structure. A highlight deck is naturally bounded by imported reading material: source file/book metadata, highlight text, extracted target words, and a generated card per approved vocabulary item. The learner expects the card to test recall from the target word + pronunciation + example sentence, then reveal the definition on the back. Because this mode is for reading-derived vocabulary, **no `Translation` field should be exported in the highlight note type** unless a later milestone explicitly adds optional bilingual behavior.

The milestone should be treated as an integration and contract-refresh milestone: WebDAV ingestion, local Kindle Formatter-style normalization, candidate extraction, highlight-specific generation rules, new highlight note type/template, and phonetics template refresh. Avoid turning v1.2 into a generic ebook parser, reading app, sync service, or AI tutor.

## v1.2 Scope Recommendation

### Build in v1.2

1. WebDAV fetch from the configured Kindle highlight export location.
2. Local normalization of Kindle-exported HTML/text into plain highlight records.
3. Highlight deck mode that consumes normalized highlights and generates cards without touching normal deck behavior.
4. Highlight note type/template with English field names, centered responsive layout, `Definition` on the back, no `Translation` field, packaged audio, and blank `Image` support.
5. Highlight-specific example rules: concise sentences, target word included, slightly richer grammar than v1.0/v1.1 normal cards, not long or literary.
6. Phonetics note/template refresh using the provided front layout, `Sentence Translation` on the back, removed unused fields, and Multilang colors.
7. Deterministic acceptance evidence: parser fixtures, duplicate/idempotency checks, export field-order checks, template snapshot checks, and small end-to-end highlight deck generation.

### Defer after v1.2

- Sense-aware disambiguation using full highlight context.
- Book/chapter-aware deck organization beyond basic source metadata.
- Automatic Kindle account/device sync.
- Browser extension or live reading capture.
- Optional translations in highlight cards.
- Rich review UI for editing extracted candidates.

## Feature Categories

### 1. Kindle/WebDAV Ingestion

Table-stakes ingestion behavior for v1.2.

| Feature | v1.2? | Why Expected | Complexity | Dependencies | Acceptance Signals |
|---------|-------|--------------|------------|--------------|--------------------|
| Configured WebDAV source URL and credentials | Yes | Automatic import must know where to fetch highlights and must not hard-code private credentials | Medium | Config/secrets layer, HTTP/WebDAV client | CLI accepts config; secrets are read from env/config, never committed or printed; missing config gives actionable error |
| Remote listing and file selection | Yes | A WebDAV location can contain multiple files; user expects the newest/exported highlight file to be found | Medium | WebDAV `PROPFIND`/directory listing support | Given fixture listing, importer chooses newest matching file or user-specified path; unsupported files are skipped with reasons |
| Download with retry and clear failure modes | Yes | Network/auth failures are common and should not silently create empty decks | Medium | HTTP client, job status/reporting | 401/403/auth errors, 404 path errors, timeout errors, and empty directory errors produce distinct messages |
| Local file fallback input | Yes | Needed for tests and for users when WebDAV is unavailable | Low | Existing custom input plumbing | Same normalization pipeline accepts a downloaded/local Kindle export file |
| Import manifest and idempotency | Yes | Re-running should not duplicate cards from the same highlight export | Medium | Persistence, stable hashing | Import stores source URL/path, content hash, fetched timestamp, and normalized record count; rerun reports unchanged/imported/skipped counts |

### 2. Local Kindle Formatter-Style Normalization

The existing external Kindle Formatter page transforms exported Kindle Notebook HTML into plain Markdown/text. v1.2 should reimplement the required subset locally, not automate that website.

| Feature | v1.2? | Why Expected | Complexity | Dependencies | Acceptance Signals |
|---------|-------|--------------|------------|--------------|--------------------|
| Parse Kindle-exported HTML into highlight records | Yes | Raw Kindle export is not directly suitable for vocabulary extraction | Medium-High | HTML parser, fixture examples | Parser extracts book/title metadata when present, highlight text, note text if present, location/page if present, and record order |
| Normalize highlights into comma/newline-separated candidate text | Yes | User explicitly relies on Kindle Formatter-style normalization where highlights are separated clearly | Medium | Parser output | Normalized output is deterministic, UTF-8 safe, strips UI boilerplate, preserves diacritics/Cyrillic/Turkish characters, and separates highlights unambiguously |
| Clean whitespace, punctuation, and duplicated fragments | Yes | Kindle exports often include line breaks, HTML entities, and repeated snippets | Medium | Text normalization | Fixture with messy spacing produces stable clean text; punctuation inside sentences is preserved; wrapper junk is removed |
| Reject unusable highlights | Yes | Very short, numeric-only, URL-only, or non-target-language snippets create bad cards | Medium | Language detection/token validation | Import report lists rejected highlights with reason; rejected rows do not reach AI generation |
| Preserve source provenance | Yes | Users studying reading-derived vocabulary benefit from knowing which highlight/book produced a card | Medium | Data model/export metadata | Internal records keep source file, source title if known, original highlight text, normalized text, and candidate extraction trace |

### 3. Vocabulary Candidate Extraction from Highlights

Highlight mode should turn reading snippets into words to study, not blindly card every token.

| Feature | v1.2? | Why Expected | Complexity | Dependencies | Acceptance Signals |
|---------|-------|--------------|------------|--------------|--------------------|
| Target-language tokenization and candidate filtering | Yes | Highlight text contains articles, punctuation, names, and already-known common function words | High | Existing language configs, lexical grounding | Candidates exclude punctuation/numbers/URLs; preserve accents; support the 11 existing languages; rejected candidate reasons are reportable |
| Lemma/headword normalization using existing lexical grounding | Yes | Cards should be generated for useful vocabulary entries, not random inflected duplicates | High | Existing lexical pipeline | Inflected duplicates collapse where current language tooling supports it; unresolved cases remain as surface forms with warnings |
| Frequency-aware filtering as a ranking signal, not the source | Yes | User says highlights replace `wordfreq` as source; frequency can still help prioritize noise removal | Medium | Existing frequency assets | Highlight occurrence/source order drives inclusion; frequency is only used to rank/filter obvious ultra-common words if configured |
| Duplicate detection against prior highlight imports and existing decks | Yes | Reading decks are rerun often; duplicates are frustrating in Anki | Medium | Card identity strategy | Same language+headword+source mode does not create duplicate notes unless explicitly allowed |
| Small-batch preview/report before generation | Should | Prevents spending AI/TTS budget on bad extraction | Medium | CLI reporting | CLI shows imported highlights, extracted candidates, rejected count, duplicate count, and planned card count before expensive generation |

### 4. Highlight-Specific Card Generation

Highlight cards should reuse v1.0/v1.1 quality infrastructure while changing deck behavior.

| Feature | v1.2? | Why Expected | Complexity | Dependencies | Acceptance Signals |
|---------|-------|--------------|------------|--------------|--------------------|
| New `highlights` deck mode | Yes | Must sit alongside frequency and custom word-list flows | Medium | CLI/job routing, card type discriminator | CLI can generate `frequency`, `word-list`, and `highlights` decks independently; existing flows remain regression-tested |
| Highlight note schema with English fields | Yes | User explicitly requested English field names for the new template | Medium | Export model, genanki note type | Exported highlight note type uses stable English fields such as `Word`, `IPA`, `Definition`, `Example Sentence`, `word_audio`, `sentence_audio`, `Image`; no Portuguese field names remain |
| No `Translation` field in highlight deck | Yes | User explicitly requested no translation for this mode | Low-Medium | Schema/export/template split | CSV/TSV/APKG highlight exports contain no `Translation` column/field; template has no dangling `{{Translation}}` reference |
| `Definition` revealed on back only | Yes | Highlight study flow should test recall before revealing meaning | Low-Medium | Template design | Front preview shows word, IPA/audio, example; back preview adds definition after answer divider |
| Concise but richer example sentences | Yes | User wants more grammatical complexity without long sentences | High | AI prompt/validator | Validator enforces target word presence, target language, max length, and non-trivial grammar; examples are not single-clause baby sentences by default |
| Audio behavior preserved | Yes | Existing product promise includes Azure word and sentence audio | Medium | Azure adapter, media packaging | Highlight cards package playable word and sentence audio with correct field references and no missing media warnings |
| Blank image field preserved | Yes | Existing project decision: user manually adds images | Low | Schema/export | `Image` field exists for highlight cards but is empty unless user supplied content later |

### 5. Highlight Deck Template Behavior

The template is user-visible and should have explicit acceptance criteria, not only “looks better.”

| Feature | v1.2? | Why Expected | Complexity | Dependencies | Acceptance Signals |
|---------|-------|--------------|------------|--------------|--------------------|
| Centered responsive layout | Yes | User identified current option as too top-aligned and less responsive | Medium | CSS/template snapshots, Anki preview | Card content is vertically and horizontally balanced on desktop and mobile-width previews; no overflow for long definitions/examples |
| Multilang visual theme | Yes | New deck should feel part of the existing product | Low-Medium | Existing v1.1 CSS tokens/colors | Uses Multilang dark theme/color palette consistently with normal card refresh |
| English template field names | Yes | Required by user | Low | Schema/template | Front/back/style references match exported fields exactly; field names are case-correct because Anki fields are case-sensitive |
| Back includes `{{FrontSide}}` plus definition | Yes | Standard Anki behavior for basic cards and requested reveal flow | Low | Anki template rules | Back preview reproduces front and shows definition below answer divider |
| Safe media references | Yes | Anki does not reliably package media referenced dynamically from templates | Medium | Export field values | Audio/image references are stored in fields, not generated as dynamic filenames in template |

### 6. Phonetics Template Refresh

This is separate from highlight mode but part of v1.2.

| Feature | v1.2? | Why Expected | Complexity | Dependencies | Acceptance Signals |
|---------|-------|--------------|------------|--------------|--------------------|
| Use provided phonetics front layout | Yes | User supplied a concrete front template | Medium | Phonetics note type/template | Front shows spellings, sound, letter audio, example word, word audio, word translation, example sentence, sentence audio |
| Show `Sentence Translation` on back | Yes | User explicitly wants same behavior as normal cards | Low-Medium | Back template | Front uses hint behavior if desired; back reveals actual `Sentence Translation` reliably |
| Remove unused phonetics fields | Yes | `Notes`, `is_priming`, and `is_sentence` should not be in the deck | Medium | Schema/export/tests | APKG/CSV phonetics exports do not include removed fields; no template references remain |
| Apply Multilang colors | Yes | Visual consistency requirement | Low-Medium | CSS | Phonetics template uses the same color system as current Multilang cards |
| Preserve existing Russian phonetics data behavior | Yes | Existing feature must not regress while template changes | Medium | Regression tests | Russian phonetics deck still exports playable audio and required phonetics fields after schema cleanup |

## Differentiators

These are worth doing when they fit naturally in v1.2, but should not endanger the table stakes.

| Feature | v1.2 Recommendation | Value Proposition | Complexity | Dependencies | Notes |
|---------|---------------------|-------------------|------------|--------------|-------|
| Candidate extraction report with reasons | Include if cheap | Builds trust: user sees why words were included/skipped | Medium | Import/candidate pipeline | Strong requirement-definition candidate because it improves debugging |
| Source-aware tags in Anki | Include minimal version | Lets users filter cards by book/import/source | Low-Medium | Export metadata | Use safe tags like `multilang`, `highlights`, language, source slug |
| Dry-run mode | Include if CLI plumbing exists | Prevents accidental expensive AI/TTS runs | Low-Medium | Pipeline flags | `--dry-run` should stop after normalized highlights + candidate report |
| Incremental imports | Include basic hash-based version | Reruns only new/changed source files | Medium | Manifest | Full sync conflict handling can wait |
| Highlight context stored internally but not shown by default | Include internally | Enables future sense disambiguation and debugging | Medium | Data model | Do not clutter v1.2 card face unless user asks |

## Deferred / Future Ideas

| Future Feature | Why Defer | Prerequisites |
|----------------|-----------|---------------|
| Sense-aware card generation from exact highlight context | High value but requires robust disambiguation and QA | Stored highlight provenance, lexical sense ranking |
| Optional bilingual highlight decks with translation | Conflicts with current explicit “no Translation field” request | New note type or template option |
| Book/chapter subdecks | Nice organization, but source metadata from Kindle exports may be inconsistent | Reliable title/chapter parsing |
| Interactive candidate approval UI | Useful, but v1.2 can use reports and config thresholds first | Review UI/editor milestone |
| Kindle account/device sync | Too broad and likely brittle | Official supported API or stable local export workflow |
| Generic ebook/PDF/website ingestion | Scope creep from Kindle highlights | Abstraction after Kindle mode stabilizes |
| Automatic image sourcing | Already out of scope | Explicit future product decision |

## Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Automating the external Kindle Formatter website | Browser automation is brittle, hard to test, and unnecessary | Reimplement the required normalization locally with fixtures |
| Replacing frequency decks globally with highlights | v1.2 adds a mode; existing shipped flows must keep working | Add `highlights` as a separate deck/input source |
| Treating every highlighted word/token as a card | Creates duplicates, names, function words, and low-value cards | Tokenize, filter, normalize, and report candidates |
| Adding `Translation` back into highlight cards | Directly conflicts with requested highlight template behavior | Keep definition-only reveal; revisit optional bilingual variant later |
| Long literary example sentences copied from highlights by default | Hard to review and may not isolate target vocabulary | Generate concise learner-friendly examples grounded by the word/sense |
| Hiding WebDAV/auth/import failures | Silent empty decks destroy trust | Fail clearly with reason and no exported deck unless user forces partial output |
| Dynamic Anki media filenames in templates | Anki warns that template-scanned media references are unreliable | Store media references inside fields and package them normally |
| Full reading app or SRS replacement | Not the product; Anki remains destination | Export high-quality Anki decks |

## Feature Dependencies

```text
WebDAV configuration
  → Remote listing/download
  → Import manifest/idempotency
  → Local Kindle normalization

Local Kindle normalization
  → Highlight records with provenance
  → Candidate extraction/filtering
  → Dry-run/import report

Candidate extraction/filtering
  → Existing lexical grounding
  → Highlight-specific AI generation
  → Audio generation
  → Highlight card export

Highlight note schema
  → Highlight template field names
  → CSV/TSV/APKG export contracts
  → Template snapshot/import tests

Phonetics schema cleanup
  → Phonetics front/back template refresh
  → Russian phonetics regression evidence
```

## User-Visible Acceptance Criteria for v1.2

### Kindle/WebDAV Import

- User can configure WebDAV URL, username, and secret without editing source code.
- Running highlight import fetches a remote Kindle export or accepts a local fallback file.
- The command reports fetched file name/path, content hash, number of raw highlights, normalized highlights, rejected highlights, extracted candidates, duplicates, and planned cards.
- Bad credentials, missing file, empty file, unsupported file type, and timeout each produce a clear failure message.
- Re-running the same import does not silently create duplicate cards.

### Normalization and Candidate Extraction

- Kindle export boilerplate is removed; highlight text remains readable and deterministic.
- Highlight separators are unambiguous, matching the user’s current Kindle Formatter-style workflow.
- Diacritics, Cyrillic, Turkish dotted/dotless characters, apostrophes, and language-specific punctuation are preserved.
- Non-vocabulary fragments are rejected with reasons.
- Candidate extraction supports all existing target languages without adding new languages.

### Highlight Deck Generation

- User can select/generate `highlights` mode without changing normal frequency or custom word-list commands.
- Highlight cards include word/headword, IPA/spoken pronunciation behavior consistent with current project quality rules, definition, example sentence, word audio, sentence audio, and blank image.
- Highlight cards do **not** include a `Translation` field.
- Examples are concise, target-containing, grammatically natural, and not overly simplistic.
- Audio files are generated/reused through existing Azure-first behavior and packaged in APKG exports.

### Highlight Template

- Front shows the prompt side only: word, IPA, audio controls, and example sentence.
- Back shows `FrontSide`, answer divider, and `Definition`; image appears only if manually populated.
- Layout is centered, responsive, and uses Multilang colors.
- All template field references use exact English field names and pass snapshot/import checks.

### Phonetics Template

- Phonetics front uses the provided layout structure.
- Back reveals `Sentence Translation` correctly.
- `Notes`, `is_priming`, and `is_sentence` are removed from fields and templates.
- Russian phonetics deck exports still work with required audio and translation behavior.

## Suggested v1.2 Requirement IDs

Use these as seeds for `.planning/REQUIREMENTS.md`.

- **KINDLE-INGEST-01:** Multilang can fetch Kindle highlight exports from configured WebDAV storage and fail clearly on auth/path/network errors.
- **KINDLE-INGEST-02:** Multilang can process a local Kindle export file through the same normalization path used by WebDAV imports.
- **KINDLE-NORM-01:** Multilang locally normalizes Kindle-exported highlights into deterministic highlight records without using the external Kindle Formatter site.
- **KINDLE-NORM-02:** Normalization preserves target-language characters and reports rejected unusable highlights.
- **KINDLE-CAND-01:** Multilang extracts filtered vocabulary candidates from normalized highlights with duplicate detection and a user-visible report.
- **HIGHLIGHT-DECK-01:** Multilang supports `highlights` as a separate deck generation mode without regressing frequency or custom word-list flows.
- **HIGHLIGHT-CARD-01:** Highlight cards use a highlight-specific schema with English field names, no `Translation`, blank `Image`, and `Definition` on the back.
- **HIGHLIGHT-EXAMPLE-01:** Highlight examples are concise, target-containing, grammatically natural, and validated before export.
- **HIGHLIGHT-TEMPLATE-01:** Highlight APKG exports use a centered responsive Multilang-colored template matching the requested front/back behavior.
- **PHONETICS-TEMPLATE-01:** Phonetics cards use the provided front layout, reveal `Sentence Translation` on the back, and remove unused fields.
- **REGRESSION-01:** Existing frequency-deck, custom word-list, audio, and export flows remain operational after v1.2 changes.

## Sources and Confidence

- Project context: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `alter_organizado.md` — **HIGH confidence** for user intent and existing milestone constraints.
- Kindle Highlights Formatter page — confirms current external workflow takes Kindle-exported HTML and outputs Markdown/plain text: https://pch.github.io/kindle-formatter/ — **MEDIUM confidence** for behavior; official for that tool but minimal docs.
- WebDAV RFC 4918 — confirms WebDAV collection/resource model, methods such as `PROPFIND`, and network/error considerations: https://datatracker.ietf.org/doc/html/rfc4918 — **HIGH confidence** for protocol expectations.
- Anki Manual: field replacements/templates — confirms field names are case-sensitive, `FrontSide` back behavior, hint fields, and media-reference caveats: https://docs.ankiweb.net/templates/fields.html — **HIGH confidence** for template acceptance criteria.

## Confidence Notes

- **HIGH:** User-requested v1.2 behavior, Anki template constraints, “separate mode not replacement,” no translation field in highlight cards.
- **MEDIUM-HIGH:** WebDAV ingestion shape and idempotent import/report requirements; grounded in WebDAV protocol plus standard batch-import UX.
- **MEDIUM:** Exact Kindle export HTML variability; needs fixture collection from the user’s actual Kindle/WebDAV exports during implementation.
