# Domain Pitfalls: v2.0 Classical Latin MVP

**Project:** Multilang Anki Card Generator  
**Milestone:** v2.0 Classical Latin MVP  
**Domain:** Classical Latin frequency-by-lemma Anki cards with Portuguese explanations, traceable sentences, grammar notes, audio, and APKG export  
**Researched:** 2026-06-01  
**Overall confidence:** MEDIUM-HIGH. HIGH for project integration/export/privacy risks because they build on shipped v1.0-v1.3 evidence and official Anki/Azure/eSpeak/DCC docs. MEDIUM for Latin NLP/source/TTS quality because tool behavior and pronunciation acceptability require empirical validation on the 50-card MVP.

## Context-Specific Risk Summary

Adding Latin is not “add one more language code.” Classical Latin changes the core unit from modern-language word/form frequency to lemma frequency, adds ambiguous morphology and grammar labels, requires sentence provenance and licensing, and likely cannot use the existing Azure-first voice registry without a Latin-specific fallback. The biggest failure mode is silently producing plausible-looking cards whose lemma, case, syntax, Portuguese translation, or audio pronunciation is wrong.

The roadmap should start by freezing Latin contracts and protecting existing deck modes, then select licensed sources and morphology/frequency evidence, then build a small reviewed 50-card corpus before provider-heavy generation or APKG export. Latin validators should fail closed: uncertain morphology, unlicensed source text, untraceable sentence provenance, missing review status, or mismatched audio should block export rather than become learner-facing content.

## Critical Pitfalls

### 1) Treating Latin as a twelfth modern language in the existing frequency pipeline

**What goes wrong:** Latin is threaded through the existing modern-language frequency path by adding `la` to a supported-language enum. The pipeline expects surface-word ranks, IPA-like phonetics, modern TTS voices, normal card schemas, and modern sentence validation. Latin cards then inherit assumptions that do not fit: `wordfreq` coverage, form-level frequency, no grammar note, no source citation, and a modern-language audio fallback.

**Why it happens:** The shipped code already supports 11 languages and has strong reusable abstractions. Reuse is tempting, but Latin requires separate source profiles and card contracts.

**Consequences:** Wrong ordering, missing lemma/source/grammar fields, bad media routing, and regressions in frequency/custom/highlight decks if shared validators/templates are mutated globally.

**Warning signs:**
- `la` is added beside `pt`, `es`, etc. with no `latin_mvp` or classical source profile.
- Latin cards use the normal generated-card field tuple without `lemma`, `target_form`, `Gramatica`, `source`, and `review_status`.
- Tests update global normal-card snapshots to make Latin pass.
- Audio voice lookup falls through to a modern Romance or English voice.

**Prevention:**
- Add Latin as a separate deck mode/profile: `classical_latin_mvp`, not only `language_code=la`.
- Create an explicit Latin card DTO/export row with `target_form`, `lemma`, Portuguese word/sentence translations, `Gramatica`, source citation, review status, and media metadata.
- Keep normal, custom, highlight, and phonetics note types isolated; add regression tests proving their field tuples and templates do not change.
- Reuse shared infrastructure only below stable boundaries: persistence, audio manifest, APKG packaging, validation facade, evidence reports.

**Detection / validation:**
- Contract test: Latin export field tuple differs intentionally from normal/highlight/phonetics tuples.
- Regression suite: one existing fixture per shipped deck mode still exports with unchanged note type, field names, and media references.
- Static check: no Latin-specific branches inside low-level generic APKG media packaging except through source/profile contracts.

**Phase placement recommendation:** Phase 1 - Latin contracts, source-profile boundaries, and existing-mode regression harness.

---

### 2) Frequency-by-lemma built from ambiguous or inconsistent lemmatization

**What goes wrong:** Frequency ranks are calculated from surface forms or from a single lemmatizer output without ambiguity handling. Forms such as `arma`, `canō/cano`, `cum`, `Romae`, `mālum/malum`, `quae`, `sum/esse`, and enclitic-bearing forms are counted under the wrong lemma or split inconsistently across orthographic variants.

**Why it happens:** Latin morphology is highly ambiguous and corpus/tool conventions differ. UD Latin treebanks themselves show multiple Latin corpora with different tokenization, multi-word-token, POS, and morphology behavior; Perseus Hopper explicitly offers automatic lemmatization/morphological analysis, but automatic output still needs context and validation.

**Consequences:** The MVP claims frequency-by-lemma but teaches a distorted top-50. Later scaling to 300/1000 cards becomes expensive because ranks, card IDs, and evidence must be rebuilt.

**Warning signs:**
- Frequency table has no `frequency_source`, corpus version, tokenizer version, lemmatizer version, or ambiguity status.
- Enclitics (`-que`, `-ve`, `-ne`) are counted as part of host lemmas without a rule.
- `v/u`, `j/i`, macrons, punctuation, capitalization, and editorial brackets are normalized differently in frequency and sentence extraction.
- The final list cannot explain why a lemma outranks another lemma.

**Prevention:**
- For the 50-card MVP, freeze a curated lemma list with evidence rather than pretending full automated frequency is solved.
- Store frequency as a versioned artifact: corpus ID, source license, text version, normalizer, tokenizer, lemmatizer(s), ambiguity resolution, rank, count, and reviewer.
- Compare at least two morphology/lexical sources for the top candidates (e.g. CLTK/Perseus-style analysis plus Collatinus/Whitaker/LemLat/manual review if selected later).
- Mark ambiguous lemmatization as `needs_review`; do not export cards whose rank depends on unresolved ambiguity.

**Detection / validation:**
- Golden fixture of Latin forms with expected lemma and ambiguity flags: `virum`, `arma`, `cano`, `Romae`, `cum`, `puellae`, `mecum`, `virumque`, `ne`, `quae`.
- Frequency audit report showing top 50 lemmas, counts/ranks, excluded forms, and manual overrides.
- Reproducibility test: rerun frequency build and assert same rank/order for the frozen MVP artifact.

**Phase placement recommendation:** Phase 2 - source/resource selection and frequency-by-lemma artifact; Phase 3 - morphology validation.

---

### 3) Wrong grammar labels from morphology-only analysis

**What goes wrong:** The `Gramatica` field is generated from morphology alone and presents uncertain or context-dependent labels as fact. A form is labeled `Genitivus` when it is locative, nominative/accusative neuter plural ambiguity is ignored, a participle is labeled as a simple adjective, or a syntactic function (`OD`, `Suj`, `OI`) is guessed without parsing the sentence.

**Why it happens:** The target grammar field combines morphology and syntax: case, number, gender/declension/conjugation, and function in the sentence. Many tools provide possible morphological parses, not the one true function in context.

**Consequences:** Learners memorize incorrect grammar. The deck violates the Rafael Falcon-style requirement: short grammar notes that explain the target form inside the sentence.

**Warning signs:**
- Grammar generation returns one string with no parse alternatives or confidence.
- `Romae` is always `Genitivus` and never locative/review.
- All accusatives are labeled `OD`, including objects of prepositions.
- Prepositions do not validate governed case (`cum` + Ablativus, `ad` + Accusativus).
- Final cards contain `Genetivus` or mixed case nomenclature despite the project decision to use `Genitivus`.

**Prevention:**
- Split internal analysis into `morphology_candidates`, `selected_morphology`, `syntax_function`, `grammar_note`, and `review_status`.
- Standardize an allowed grammar vocabulary before generation: POS abbreviations, cases (`Nominativus`, `Vocativus`, `Accusativus`, `Genitivus`, `Dativus`, `Ablativus`), number terms, syntactic labels, uncertainty markers.
- Require human review for every MVP grammar note; LLM/tool output may draft but not approve.
- Treat uncertain grammar as valid only if explicitly marked for review; approved/exportable cards must not contain unresolved alternatives like “ou locativo, revisar contexto”.

**Detection / validation:**
- Grammar schema validator: allowed labels only; `Genetivus` rejected; grammar must start with `target_form:`.
- Hand-authored test set for the first 50 cards with expected case/function and reviewer ID.
- Adversarial fixtures for locative, preposition + case, neuter plural, deponent verbs, participles, enclitics, and vocative.

**Phase placement recommendation:** Phase 3 - Latin morphology/grammar model and validators; Phase 4 - reviewed MVP card curation.

---

### 4) Using unlicensed or weakly licensed sentence/corpus sources

**What goes wrong:** The project copies classical text, commentary notes, running vocabulary, translations, or curated sentence selections into committed fixtures, prompts, reports, or APKGs without verifying license and attribution obligations. “Classical author is public domain” is mistaken for “this edition/site text and annotations are unrestricted.”

**Why it happens:** Latin source text often derives from modern digital editions or educational sites with their own terms. DCC is valuable and peer-reviewed, but its site states CC BY-SA licensing; that attribution/share-alike obligation must be recorded if content is reused. The Latin Library has broad text coverage, but licensing/edition provenance should not be assumed from the home page alone.

**Consequences:** Legal/compliance risk, blocked distribution, forced source replacement, and contaminated test fixtures/evidence artifacts.

**Warning signs:**
- Source table has URL only, no license, edition, author/work/line, attribution text, or allowed-use note.
- Generated cards include DCC notes/translations as if they were internal content without CC BY-SA handling.
- APKG evidence embeds full scraped pages or private research snippets.
- Corpus source is “Perseus/Latin Library” with no passage-level citation or terms check.

**Prevention:**
- Create a `latin_source_registry` before using any sentence: source ID, title, edition, canonical citation, URL, license, attribution requirement, reuse allowed, derivative/share-alike implications, and evidence link.
- Prefer public-domain original Latin passages or clearly licensed sources for sentence text; avoid copying modern commentary/translation notes unless license-compatible.
- Keep source snippets bounded to the sentence used; do not commit large scraped corpora unless license and project policy allow it.
- Include source attribution in APKG fields/reports where required and in project evidence.

**Detection / validation:**
- Export gate: every Latin card must have `source_id`, canonical citation, and approved license status.
- Artifact scanner: no raw corpus dumps or large scraped pages in `.planning`, fixtures, prompts, or APKG evidence.
- Source registry review checklist before Phase 4 curation starts.

**Phase placement recommendation:** Phase 2 - source/licensing registry before sentence selection; Phase 7 - final artifact audit.

---

### 5) Sentence difficulty undermines the Rafael Falcon-style progression

**What goes wrong:** Frequency selects common lemmas, but examples come from poetry, ornate prose, ellipsis, hyperbaton, rare constructions, or long excerpts. The target word is technically frequent, but the card is not usable for beginner/intermediate reading practice.

**Why it happens:** Classical sources such as Vergil are canonical and rich in frequent vocabulary, but early lines can be syntactically dense. The seed explicitly warns to avoid poetry that is too complex in the first level and to progress from simpler contexts.

**Consequences:** The 50-card MVP feels authentic but frustrating. Grammar notes become too long or incomplete, Portuguese translations drift toward paraphrase, and audio sentence length becomes fatiguing.

**Warning signs:**
- Sentence length limits are character-only and ignore clauses, finite verbs, participles, enclitics, or poetry word order.
- First cards use `Arma virumque cano`-style examples without addressing poetic syntax and enclitic `-que`.
- MVP contains many subordinate clauses before core nominative/accusative/verb patterns.
- Grammar note cannot stay short without hiding essential explanation.

**Prevention:**
- Add a Latin sentence difficulty rubric: max tokens, finite verb count, target form present once, clear syntactic role, allowed case/function set for early cards, no unmarked ellipsis, no poetry-first default.
- Use DCC Core Vocabulary/frequency as a guide, but order the 50 cards by didactic progression where needed; store both frequency rank and didactic order.
- Allow adapted/didactic sentences only if explicitly marked as adapted and sourced/reviewed; never pass adapted sentences off as classical quotations.
- Maintain a “blocked constructions for MVP” list: heavy indirect statement, nested relatives, complex ablative absolutes, extreme hyperbaton, rare archaic forms, unresolved locatives.

**Detection / validation:**
- Sentence validator emits length, token count, finite verb count, target inclusion, source type, difficulty tags, and rejection reasons.
- Human review checklist includes “Rafael Falcon progression fit” and “grammar note can be short and honest.”
- Distribution report for the MVP: cases/functions introduced by card order.

**Phase placement recommendation:** Phase 4 - curated 50-card selection and didactic ordering; Phase 5 - generation/translation QA.

---

### 6) Portuguese translation drift from contextual Latin meaning

**What goes wrong:** The short Portuguese word translation is dictionary-generic while the sentence translation is free or LLM-paraphrased. The learner sees a word gloss that does not fit the sentence, or a sentence translation that hides the target form’s grammar.

**Why it happens:** Latin word meanings shift by context, case, idiom, and construction. Portuguese translation also has a didactic role here: it must clarify the target form and sentence, not just sound natural.

**Consequences:** Cards teach wrong senses and make grammar notes look inconsistent. Reviewers cannot tell whether the problem is translation, morphology, or source sentence selection.

**Warning signs:**
- Word translation and sentence translation are generated in separate calls with no shared target sense.
- Sentence translations omit the target word or collapse it into idiom without explanation.
- Portuguese outputs alternate Brazilian/European terminology or use inconsistent grammar words.
- No validator checks that `short_translation_pt` appears semantically in `sentence_translation_pt`.

**Prevention:**
- Generate/curate translation from a single structured sense record: lemma, target form, selected parse, source sentence, literal gloss, contextual gloss, final sentence translation.
- Prefer didactic Portuguese translation for MVP: accurate and clear over literary elegance.
- Require reviewer approval for both word gloss and sentence translation.
- Store provider/model/version/prompt hash for generated translations; never overwrite approved human-reviewed translations silently.

**Detection / validation:**
- Review report comparing target lemma/form, selected sense, word gloss, sentence translation, and grammar function.
- Validator flags translations that omit the target concept, are too free for early cards, or include unresolved uncertainty.
- Golden Portuguese translations for the first 50 cards with reviewer notes.

**Phase placement recommendation:** Phase 5 - Portuguese generation and QA; Phase 6 - audio/export assembly should consume only approved translations.

---

### 7) Bad Latin TTS pronunciation presented as authoritative audio

**What goes wrong:** Audio is generated because the pipeline requires audio, but pronunciation is modern-language or mechanically Latin-ish. Azure standard voices do not list a dedicated Latin locale in the official TTS language table checked during research; Azure multilingual voices may synthesize Latin-like text but require empirical evaluation. eSpeak NG lists Latin (`la`), but voice quality is synthetic and pronunciation style may not match the desired classical/traditional standard.

**Why it happens:** Existing v1 audio is Azure-first and exact-match validated, but Latin has no obvious high-quality default voice. TTS can sound plausible while pronouncing vowels, stress, `v`, `c`, diphthongs, or macrons poorly.

**Consequences:** Learners internalize wrong pronunciation or lose trust. Audio regressions can also occur if Latin filenames collide with existing media or if fallback audio bypasses v1.3 word-audio integrity gates.

**Warning signs:**
- Latin audio provider is marked `azure` without a tested voice ID/sample pack.
- eSpeak output is accepted solely because `espeak-ng --voices` lists `la`.
- No `pronunciation_style` metadata (`classical`, `ecclesiastical`, `unknown/experimental`).
- Word audio is synthesized from lemma while the exported front shows target form, or vice versa.

**Prevention:**
- Treat Latin TTS as experimental until sample-based human approval. Store provider, voice, command/SDK version, pronunciation style, text synthesized, normalized text hash, and reviewer status.
- Evaluate eSpeak NG `la` and candidate Azure multilingual voices on a fixed sample set before locking MVP audio policy.
- If no acceptable TTS exists, either block export when audio is required or mark audio as experimental in metadata; do not silently use English/Italian/Spanish voices.
- Reuse v1.3 exact word-audio integrity: target-form word audio must match exported `target_form`, sentence audio must match `latin_sentence`.

**Detection / validation:**
- Human playback checklist for at least 20 representative words/sentences: `virum`, `puella`, `caesar`, `cicero`, `veni`, `quae`, `cum`, `Romae`, `arma virumque cano`.
- Automated audio manifest test: filename/hash/voice/provider/text match card snapshot; no collisions with normal/custom/highlight media.
- Source-profile audio fallback matrix specifically includes Latin outcomes: approved, experimental, blocked.

**Phase placement recommendation:** Phase 6 - Latin audio provider evaluation and manifest integration; Phase 7 - APKG playback evidence.

---

### 8) Source leakage into prompts, reports, fixtures, and APKG evidence

**What goes wrong:** Full scraped corpus pages, source-site commentary, local research notes, prompt context, or unreviewed generated text leak into `.planning`, tests, logs, provider requests, or APKG/CSV/TSV artifacts. Even public-domain Latin can be a problem if modern commentary/translation/licensed metadata is bundled accidentally.

**Why it happens:** v1.2/v1.3 already established privacy-safe artifacts for highlights and audit decks, but Latin source work may feel “public” and bypass redaction/minimization discipline.

**Consequences:** Licensing contamination, hard-to-review diffs, provider exposure of unnecessary text, and evidence artifacts that cannot be safely committed.

**Warning signs:**
- Prompt fixtures include entire DCC/Perseus/Latin Library pages instead of a bounded sentence and citation.
- Reports serialize raw provider responses with full source context.
- `.planning/research` or tests contain copied paragraphs of commentary/translation.
- APKG evidence contains rejected/needs-review cards or private/local source paths.

**Prevention:**
- Apply the existing privacy-safe artifact principle to Latin: bounded snippets, hashes, source IDs, and citations rather than raw corpus dumps.
- Separate ignored local corpus cache from committed fixture/evidence directories.
- Prompt minimization: send only sentence, lemma, selected morphology candidates, and citation/license metadata needed for the task.
- Redact provider traces and store only safe summaries in milestone evidence.

**Detection / validation:**
- Artifact scanner for raw source page markers, local paths, provider secrets, large Latin text blocks, and unapproved source URLs.
- Prompt fixture tests assert max context length and required source ID/license fields.
- APKG/CSV/TSV evidence generated from reviewed 50-card rows only.

**Phase placement recommendation:** Phase 1 - privacy/evidence policy; Phase 5 - prompt minimization; Phase 7 - final artifact scanner.

---

### 9) Regressions in shipped deck modes while adding Latin schema/export behavior

**What goes wrong:** Latin needs new fields and templates, so the shared exporter, validators, or card model are changed globally. Existing frequency, custom word-list, highlights, and phonetics exports lose fields, change note type, change audio references, or fail broad/focused tests.

**Why it happens:** The codebase has known broad-suite drift, and v1.3 intentionally changed normal exports while preserving other modes through focused evidence. Latin introduces another schema pressure point.

**Consequences:** v2.0 damages shipped product value. Users of existing languages see broken decks even if Latin works.

**Warning signs:**
- A single `Card` model becomes a union of optional fields for every deck type.
- Template loader chooses fields based on language code instead of source profile/deck mode.
- Existing test snapshots are updated without a migration requirement.
- Broad-suite drift is ignored and focused Latin tests become the only evidence.

**Prevention:**
- Use profile-specific renderers: normal, highlight, phonetics, Latin MVP.
- Add Latin as a new note type/model name; do not mutate normal/highlight/phonetics models.
- Before Latin implementation, repair or quarantine known broad-suite collection drift enough that existing-mode focused regressions are trustworthy.
- Keep v1.3 word-audio and template validators reusable through a facade rather than duplicating/weakening them.

**Detection / validation:**
- Snapshot field tuples and note model names for every deck mode.
- Generate one small APKG/CSV/TSV fixture per existing mode plus Latin; assert no cross-mode template/media leakage.
- Import/reimport smoke test in Anki for Latin note type and at least one existing normal deck.

**Phase placement recommendation:** Phase 1 - regression harness; Phase 7 - integrated APKG regression evidence.

---

### 10) APKG export imports but is pedagogically or technically invalid

**What goes wrong:** The `.apkg` is generated successfully but field replacements are wrong, media references are built dynamically, scheduling leaks into shared decks, note type updates become unreliable, or Latin fields show answer information on the front. Anki may import the package even when the study behavior is wrong.

**Why it happens:** APKG generation success is not the same as Anki contract correctness. Anki field names are case-sensitive; media references should live in fields rather than being constructed in templates; packaged-deck updates become problematic when note types change.

**Consequences:** Cards display missing fields, audio does not package/play, updates duplicate notes, or the learner sees back-side information on the front.

**Warning signs:**
- Template uses `[sound:{{target_form}}.mp3]` or `{{gramatica}}` when the field is `Gramatica`.
- Latin note type reuses a normal model ID/name with incompatible fields.
- No Anki Desktop import evidence; only genanki unit tests.
- Scheduling/review history included in a shared test deck.

**Prevention:**
- Define a dedicated Latin MVP note type with stable field order and versioned model name.
- Put `[sound:file]` media references inside `word_audio` and `sentence_audio` fields; keep media filenames from manifest, not template interpolation.
- Lint templates against the exact Latin field tuple and allow only valid special fields like `FrontSide` on the back.
- Generate decks without scheduling data for distribution/evidence unless explicitly testing scheduling.

**Detection / validation:**
- Static template-field linter for Latin and all existing note types.
- APKG inspection: model fields, note count 50, media count, referenced media all packaged, no unreferenced media.
- Manual or automated Anki import/playback evidence: front/back display, word audio, sentence audio, no missing field markers.

**Phase placement recommendation:** Phase 7 - Latin APKG export, import, and playback evidence.

---

## Moderate Pitfalls

### 11) Lemma/card identity instability after review

**What goes wrong:** Card GUIDs or stable IDs depend on mutable rank/order, generated Portuguese text, or provider output. A reviewer fixes lemma/sentence/grammar and Anki treats it as a new note.

**Prevention:** Base Latin note identity on a stable tuple such as `latin_mvp_version + lemma + source_id + citation + target_form` with explicit migration rules if any element changes.

**Evidence:** Re-export the same reviewed 50 cards after translation/audio regeneration; assert stable note identities unless source/target intentionally changes.

**Phase:** Phase 4 and Phase 7.

### 12) Orthography/macron normalization drift

**What goes wrong:** Frequency uses `u/v` or no macrons, source sentences use editorial macrons, audio uses another form, and Anki displays a fourth form. Exact audio validation then either fails constantly or passes against the wrong text.

**Prevention:** Store separate fields for source text, display text, normalized comparison text, and TTS text. Decide MVP macron policy explicitly.

**Evidence:** Fixtures for `u/v`, `i/j`, macron/no-macron, capitalization, punctuation, enclitic splitting.

**Phase:** Phase 2 and Phase 6.

### 13) Enclitic handling corrupts both target form and grammar

**What goes wrong:** `virumque` is treated as the target form for lemma `vir` without explaining `-que`, or split into `virum` while the displayed sentence still highlights `virumque` inconsistently.

**Prevention:** Add explicit fields/rules for surface token, base target form, enclitic, and display highlight. Grammar may mention enclitic only if learner-facing and short.

**Evidence:** Golden cases for `-que`, `-ve`, `-ne`, `mecum/tecum/secum`, `neque/nec`.

**Phase:** Phase 3.

### 14) Review status becomes decorative instead of a gate

**What goes wrong:** Cards include `review_status=needs_review` but still export in the “usable MVP” deck.

**Prevention:** Export policy must distinguish draft/debug exports from learner exports. Learner APKG requires `approved` for lemma, source/license, grammar, translation, and audio policy.

**Evidence:** Export test with one `needs_review` card fails closed for learner APKG and succeeds only for an explicit draft artifact.

**Phase:** Phase 4 and Phase 7.

### 15) Provider-generated grammar/translation overwrites curated data

**What goes wrong:** A rerun regenerates fields for approved cards and erases human corrections.

**Prevention:** Approved fields are immutable by default. Field-level regeneration must require explicit target field, reviewer reset, and provenance update.

**Evidence:** Persistence test: approved grammar/translation survive rerun; attempted overwrite creates a new draft version or fails.

**Phase:** Phase 5.

### 16) DCC Core Vocabulary mistaken for a complete frequency solution

**What goes wrong:** DCC Core Vocabulary is used as if it were the project’s exact ranked corpus frequency, without noting its pedagogical/core-list design and data sources.

**Prevention:** Use DCC as a strong pedagogical/frequency guide and source of core lemmas, but record whether final ranks are DCC rank, corpus rank, curated order, or didactic order.

**Evidence:** Final MVP table has separate `frequency_rank`, `frequency_source`, and `didactic_order` columns.

**Phase:** Phase 2 and Phase 4.

## Minor Pitfalls

### 17) Inconsistent Portuguese grammar terminology

**What goes wrong:** Cards mix `presente do indicativo`, `praesens indicativus`, `sg`, `singularis`, `objeto direto`, and `OD` without policy.

**Prevention:** Freeze a Latin grammar style guide for v2.0 before curation.

**Phase:** Phase 3.

### 18) Source citation too vague for later auditing

**What goes wrong:** `Vergil, Aeneid` is stored instead of book/line or URL/citation. Reviewers cannot trace the exact sentence.

**Prevention:** Require canonical citation plus source URL/edition/source ID.

**Phase:** Phase 2 and Phase 4.

### 19) Evidence reports too narrative and not scanner-readable

**What goes wrong:** The milestone closes with prose claims but no machine-checkable mapping of 50 cards to requirements.

**Prevention:** Continue v1.3 practice: JSON/CSV evidence with requirement IDs, command references, pass/fail markers, and caveats.

**Phase:** Phase 7.

### 20) Scaling assumptions leak into the 50-card MVP

**What goes wrong:** The team designs a full 3000-card automation system before proving 50 reviewed cards.

**Prevention:** Build the smallest reviewed pipeline that preserves future extensibility: versioned source registry, frequency artifact, validators, APKG evidence.

**Phase:** All phases; especially Phase 4.

## Phase-Specific Warnings

| Recommended Phase | Likely Pitfalls | Required Mitigation / Evidence |
|---|---|---|
| **Phase 1 - Latin contracts and regression harness** | Latin treated as normal language; existing deck modes regress; source leakage policy absent | Dedicated Latin profile/card/export contract; field tuple snapshots for normal/custom/highlight/phonetics; artifact redaction policy; focused existing-mode regression evidence |
| **Phase 2 - Source, license, frequency, and normalization decisions** | Unlicensed corpus use; DCC/Core Vocabulary misuse; bad lemma frequency; orthography drift | Source registry with license/attribution; frozen top-50 candidate artifact; normalizer policy; reproducible frequency report |
| **Phase 3 - Morphology and grammar validators** | Ambiguous forms accepted as fact; wrong case/function labels; enclitics mishandled; `Genetivus` typo leaks | Allowed grammar vocabulary; morphology ambiguity model; golden Latin grammar fixtures; fail-closed grammar validator |
| **Phase 4 - Curated 50-card MVP selection** | Sentence difficulty too high; review status decorative; poor Rafael Falcon progression | Didactic difficulty rubric; human-reviewed card table; case/function distribution report; only approved rows enter learner export queue |
| **Phase 5 - Portuguese translation and generation QA** | Translation drift; provider overwrites reviewed data; excessive prompt context | Structured sense/translation records; immutable approved fields; prompt minimization tests; Portuguese reviewer evidence |
| **Phase 6 - Latin audio evaluation and manifest integration** | Bad TTS pronunciation; Azure fallback misuse; audio text mismatch; media collisions | Latin TTS sample bakeoff; provider/voice/pronunciation metadata; exact target-form/sentence audio integrity; playback review |
| **Phase 7 - Latin APKG export and milestone evidence** | APKG imports but fields/media wrong; existing modes broken; artifacts contain source leakage | Template linter; APKG inspection/import/playback evidence; existing-mode APKG/CSV/TSV regressions; scanner-readable requirement coverage |

## Explicit Validation and Evidence Recommendations

1. **Latin source registry:** one row per source with license, attribution, citation format, allowed use, and evidence URL. Export fails if source status is not approved.
2. **Top-50 frequency artifact:** versioned, reproducible, and curated; contains frequency rank, didactic order, lemma, target form, source sentence ID, ambiguity flags, and reviewer.
3. **Morphology fixture suite:** covers cases, declensions, conjugations, prepositions, locative, vocative, enclitics, deponents, participles, and ambiguous `qui/quae/quod` forms.
4. **Grammar style guide validator:** rejects unsupported labels, `Genetivus`, long explanations, missing `target_form:`, and unresolved uncertainty in approved cards.
5. **Portuguese translation QA:** compares target sense, short gloss, sentence translation, and grammar note; approved translations are immutable unless explicitly reopened.
6. **TTS sample evidence:** fixed word/sentence sample set with provider outputs, reviewer ratings, pronunciation style decision, and fallback/blocking policy.
7. **APKG contract evidence:** note type name/version, field tuple, template references, media manifest, import/playback result, and no scheduling leakage.
8. **Regression evidence for shipped modes:** run representative normal frequency, custom word-list, highlight, and phonetics exports after Latin integration.
9. **Artifact/privacy/license scanner:** verify no raw scraped corpus dumps, local paths, provider secrets, unapproved source text, or full prompt transcripts in committed artifacts.

## Most Important Roadmap Warnings

1. **Do not start with AI generation.** Start with Latin contracts, sources, license, and morphology evidence.
2. **Do not trust one morphology tool silently.** Latin grammar notes require context and review, not just a parse string.
3. **Do not call the deck frequency-based unless ranks are reproducible and lemma-based.** Store evidence for every rank and manual override.
4. **Do not treat audio as solved because a TTS engine accepts Latin text.** Human playback approval is required before learner-facing APKG evidence.
5. **Do not mutate shipped note types.** Latin needs a dedicated note type/profile while existing modes keep their validated contracts.

## Sources

- Project context: `.planning/PROJECT.md`, `.planning/STATE.md`, `LATIN-STRUCTURE.md` — HIGH
- CLTK GitHub/docs: Python NLP library for pre-modern languages; current README documents Latin-capable CLTK, optional Stanza/OpenAI/Ollama backends, and latest GitHub release v1.5.0 (May 2025) — https://github.com/cltk/cltk and https://docs.cltk.org — MEDIUM-HIGH
- Perseus Hopper Open Source: documents Latin morphological analysis, lemmatization, and corpus lemma frequency services — https://www.perseus.tufts.edu/hopper/opensource — MEDIUM-HIGH
- Universal Dependencies Latin treebanks comparison: shows multiple Latin corpora with different tokenization, multi-word-token, POS, and morphology patterns — https://universaldependencies.org/treebanks/la-comparison.html — MEDIUM-HIGH
- Dickinson College Commentaries About/Core Vocabulary: DCC is peer-reviewed, CC BY-SA, and Latin core vocabulary is ~1000 lemmas generated from LASLA/TLG-related data and meant to cover about 75% of typical text words — https://dcc.dickinson.edu/about-dcc and https://dcc.dickinson.edu/latin-core-list1 — HIGH
- eSpeak NG languages documentation: development version lists Latin with BCP-47 code `la`; distributed versions should be checked with `espeak-ng --voices` — https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md — HIGH for existence, MEDIUM for quality suitability
- Azure Speech language/voice support: official TTS table and multilingual voice notes; no dedicated Latin locale found in the checked official table, so Latin via Azure requires sample validation rather than assumption — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts — HIGH
- Anki Manual - Field Replacements: field names are case-sensitive; media references to fields are unsupported and media should be in fields — https://docs.ankiweb.net/templates/fields.html — HIGH
- Anki Manual - Packaged Decks: packaged deck updates are generally not possible when note types change; Anki 23.10+ merge behavior depends on field/template IDs — https://docs.ankiweb.net/importing/packaged-decks.html — HIGH
- The Latin Library home page: broad classical/medieval/neo-Latin coverage, but licensing/edition terms require explicit verification before reuse — https://www.thelatinlibrary.com/ — LOW-MEDIUM for reuse decisions until terms are separately verified
