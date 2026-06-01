# Project Research Summary: v2.0 Classical Latin MVP

**Project:** Multilang Anki Card Generator  
**Domain:** Classical Latin Anki vocabulary deck generation for Portuguese-speaking learners  
**Researched:** 2026-06-01  
**Confidence:** MEDIUM-HIGH overall; HIGH for scope/architecture boundaries, MEDIUM for Latin TTS quality and exact content curation.

## Executive Summary

v2.0 should add a **separate Classical Latin reading-card mode**, not treat Latin as the twelfth modern frequency language. The MVP is a reviewed **50-card** deck ordered by lemma frequency and didactic suitability, with each card centered on a target form in a traceable Latin sentence, Portuguese word/sentence translations, a short standardized `Gramatica` note, word and sentence audio, source attribution, review status, and APKG/CSV/TSV evidence.

The recommended approach is a **curated evidence pipeline** on top of the existing Python 3.12/uv/Pydantic/SQLAlchemy/genanki product. Keep the current app stack and add a thin Latin layer: frozen DCC-seeded lemma assets, local sentence/source catalogs, CLTK 1.5.0-compatible morphology hooks, optional Collatinus/Morpheus-style cross-checks behind tool boundaries, deterministic grammar formatting, human review gates, and eSpeak NG `la` as the default experimental Latin audio provider.

The main risk is producing plausible but wrong learner content: incorrect lemma ranks, ambiguous grammar labels, unlicensed text reuse, weak Portuguese translations, or bad Latin audio presented as authoritative. Mitigate by failing closed: no approved export without source/license metadata, target-form validation, standardized grammar vocabulary, review status, audio provenance/quality status, and regression tests proving existing frequency/custom/highlight/phonetics exports remain unchanged.

## Bottom-line Recommendation

Build v2.0 as a **small, reviewed, reproducible Classical Latin MVP**:

- Add `source_type="latin-mvp"` / Classical Latin mode with a dedicated Latin note type and export row.
- Freeze a 50-lemma MVP list seeded from **Dickinson College Commentaries Latin Core Vocabulary**, with `frequency_rank`, `frequency_source`, and `didactic_order`.
- Use curated, cited sentence fixtures from DCC/Perseus/public-domain or explicitly marked didactic sources; do not scrape live sources during generation.
- Generate/curate Portuguese fields and `Gramatica`, but require review before learner export.
- Use **eSpeak NG `-v la`** for MVP audio unless sample review rejects it; keep Azure multilingual only as an experimental fallback, not claimed Latin support.
- Export only approved cards by default, with APKG/CSV/TSV and scanner-readable requirement evidence.

## Key Findings

### Stack Additions and Selected Defaults

Keep the validated Multilang backbone: Python 3.12, uv, Typer CLI, Pydantic v2 domain contracts, SQLAlchemy/Alembic persistence, existing job/repository/audio/export infrastructure, and genanki APKG packaging.

**Add for Latin MVP:**

- **DCC Latin Core Vocabulary** — default frequency-by-lemma seed; freeze project-owned 50-card asset with provenance.
- **CLTK `==1.5.0`** — Python 3.12-compatible Latin NLP adapter; do not upgrade to CLTK 2.x unless the project moves to Python 3.13.
- **Collatinus/Morpheus-style cross-checks** — optional external validation/tool boundary for ambiguous morphology; avoid bundling/linking GPL data without review.
- **Local Latin asset packs** — lemma frequencies, sentence catalog, translation/review seeds, morphology overrides, source registry.
- **eSpeak NG 1.52+ `la`** — selected default Latin TTS for availability and deterministic local execution; quality remains review-gated.
- **Latin Pydantic models/enums** — `LatinCardRecord`, `LatinMorphologyEvidence`, `LatinReviewStatus`, `LatinCase`, `LatinCitation`, `LatinAudioMetadata`.

**Do not add in v2.0:** a full Latin corpus frequency engine, Google TTS, unverified Azure Latin claims, Tatoeba as primary Latin source, LLM-only morphology, or a Python 3.13 migration solely for CLTK 2.x.

### Feature Table Stakes

**Must have:**

- Separate Classical Latin mode isolated from existing modern-language deck modes.
- Reproducible 50-card MVP cap and versioned source pack.
- Frequency by lemma with stored rank/source and didactic order.
- Target form in a traceable Latin sentence, with source type, citation, URL/work metadata, and license note.
- Portuguese short translation and Portuguese sentence translation.
- Short standardized `Gramatica` field; final labels use `Genitivus`, not `Genetivus`.
- No separate learner-facing `Classe` field; preserve blank `Image`.
- Review states: `needs_review`, `approved`, `rejected`; approved-only learner export by default.
- Word and sentence audio with provider/voice/pronunciation/quality metadata.
- Dedicated Latin APKG plus CSV/TSV evidence with stable field order and packaged media.
- Regression evidence that normal frequency, custom word-list, highlight, and phonetics modes are unchanged.

**Differentiators to include if feasible:**

- Rafael Falcon-style progression rules: simple contexts first, gradual case/function complexity, avoid poetry-heavy first batch.
- Didactic suitability scoring and rejection reason codes.
- Source-type labeling: `classical_text`, `adapted_didactic`, `reference_example`.
- Enclitic-aware target matching for `-que`, `-ve`, `-ne` and related forms.
- Grammar uncertainty handling that blocks learner export unless reviewed.
- Audio A/B sample report for eSpeak vs any Azure multilingual candidate.

**Defer:** Greek, ecclesiastical/medieval/neolatin tracks, 300/1000/3000-card Latin scale, AI tutor/grammar course, automatic images, poetry-heavy progression, interactive reviewer UI, field-level Latin regeneration, human-recorded audio pack, source corpus browser, and multiple cards per lemma/sense.

## Architecture / Build-order Implications

Add Latin as a **source/profile family** that enters shared infrastructure only at stable boundaries: jobs, repositories, audio manifest, validation facade, and export packaging. Do not thread Latin-specific branches through the existing modern-language frequency generator.

**Major components:**

1. **Latin source profile and contracts** — `language="la"`, `source_type="latin-mvp"`, strict Pydantic models/enums, review statuses, Latin export row.
2. **Latin source pack loader** — reads frozen lemma frequency asset, sentence catalog, source registry, translation/review seeds, and morphology overrides.
3. **Latin candidate planner** — joins DCC/frequency evidence with Rafael Falcon didactic order and emits 50 ordered candidates.
4. **Latin morphology analyzer** — CLTK adapter plus fake/test adapter and curated overrides; outputs normalized project enums only.
5. **Grammar note builder** — deterministic `Gramatica` formatter from reviewed morphology/syntax, not a free-form LLM export field.
6. **Review/persistence layer** — `latin_card_records` and optional `latin_source_sentences`; approved fields are immutable by default.
7. **Latin audio adapter** — `EspeakNgSpeechAdapter` behind existing audio abstraction, with exact text hashes and quality status.
8. **Latin export assembler** — dedicated `Multilang::Latin Card` note type/template and `LATIN_EXPORT_CARD_FIELD_NAMES`.

## Suggested Roadmap Phases

### Phase 22: Latin Contracts, Source Profile, and Regression Harness

**Rationale:** Prevent Latin from mutating shipped note types or normal frequency behavior.  
**Delivers:** `la` guards, `latin-mvp` source profile, Latin domain models/enums, export field tuple, template dispatch, existing-mode regression snapshots.  
**Avoids:** Latin treated as a modern language; global schema/template regressions.  
**Research flag:** Standard implementation; no extra research beyond code inspection.

### Phase 23: Source Registry, Frozen Frequency Asset, and Sentence Catalog

**Rationale:** Content provenance and reproducibility must exist before morphology/audio/generation.  
**Delivers:** DCC-seeded top-50 asset, source/license registry, sentence catalog, orthography/macron/enclitic normalization policy, didactic order fields.  
**Avoids:** unlicensed text reuse, DCC misuse, unstable frequency identity.  
**Research flag:** Needs focused source/license validation and first-50 curation decisions.

### Phase 24: Morphology Normalization and `Gramatica` Validators

**Rationale:** Grammar notes are the highest-risk learner-facing new field.  
**Delivers:** analyzer protocol, CLTK 1.5.0 optional adapter, fake adapter tests, morphology overrides, grammar style guide, deterministic formatter, case/function validators.  
**Avoids:** LLM-only grammar, ambiguous forms accepted as fact, `Genetivus` leakage.  
**Research flag:** Needs empirical validation on the 50-card fixture set.

### Phase 25: Review Workflow, Persistence, and Curated 50-card Records

**Rationale:** Human approval is the safety gate across sources, translation, grammar, and audio policy.  
**Delivers:** `latin_card_records`, review transitions, immutable approved fields, rejection/uncertainty reasons, approved-only export queue, case/function distribution report.  
**Avoids:** decorative review status and provider overwrites of curated data.  
**Research flag:** Standard patterns; product decisions needed on visible review status.

### Phase 26: Portuguese Translation / Generation QA

**Rationale:** Portuguese fields must match the selected Latin sense and grammar context.  
**Delivers:** structured sense/translation records, LLM/human drafting workflow, prompt minimization, translation validators, reviewer evidence.  
**Avoids:** dictionary-generic glosses, free paraphrases, English-only leakage.  
**Research flag:** Needs reviewer calibration for literal vs natural Portuguese style.

### Phase 27: Latin Audio Provider and Integrity Checks

**Rationale:** Latin TTS availability is clear; learner-quality pronunciation is not.  
**Delivers:** eSpeak NG adapter, provider selection for `la`, audio metadata, exact word/sentence hash checks, sample playback review, policy for `approved_with_audio_warning` or blocking.  
**Avoids:** Azure fallback misuse, wrong target-form audio, bad TTS presented as authoritative.  
**Research flag:** Needs audio bakeoff/human playback validation.

### Phase 28: Latin APKG/CSV/TSV Export and Milestone Evidence

**Rationale:** Packaging should happen after schema, content, review, and audio gates are stable.  
**Delivers:** Latin card template, APKG/CSV/TSV exports, media manifest inspection, Anki import/playback evidence, source/privacy scanner, existing-mode regression evidence, requirement coverage artifacts.  
**Avoids:** APKG imports that display wrong fields/media; source leakage in artifacts.  
**Research flag:** Standard Anki/genanki patterns; requires evidence, not new research.

### Phase Ordering Rationale

- Start with contracts/profile isolation because Latin has a different card contract from normal, highlight, and phonetics decks.
- Freeze sources and ranks before generation because every downstream identity, review, and export artifact depends on stable lemma/source keys.
- Solve morphology and grammar before audio/export because wrong `Gramatica` is more damaging than missing polish.
- Put review/persistence before provider-heavy work so generated translations/audio cannot overwrite approved content.
- Export last because APKG correctness depends on field order, review status, media references, source metadata, and regression evidence.

## Watch-outs / Pitfalls

1. **Do not route Latin through normal frequency generation.** Use `latin-mvp` and a dedicated Latin note/export row.
2. **Do not claim frequency-by-lemma without a frozen auditable rank artifact.** Store DCC rank/source, project rank, didactic order, and overrides.
3. **Do not trust morphology-only output.** Latin case/function labels need ambiguity handling and review.
4. **Do not reuse text without license/provenance.** Source registry and citation/license notes are export blockers.
5. **Do not let Rafael Falcon progression become vague prose.** Encode difficulty tags, blocked constructions, and ordering rules.
6. **Do not present experimental TTS as authoritative.** eSpeak/Azure samples require playback review and quality status.
7. **Do not export unreviewed cards as learner-ready.** Draft/debug exports must be distinct from final APKG.
8. **Do not mutate existing note types or field tuples.** Latin gets a new profile/template; existing modes get regression evidence.
9. **Do not leak raw corpus pages, source commentary, local paths, provider secrets, or full prompts into committed artifacts.**

## Open Decisions for Requirements / Early Phases

- **Distribution/licensing policy:** Are CC BY-SA source excerpts acceptable in redistributed APKGs? If not, prioritize public-domain/project-authored didactic sentences.
- **Audio gate:** Must final MVP include approved audio, or can cards export with `approved_with_audio_warning` / experimental audio?
- **Pronunciation policy:** Classical approximation, ecclesiastical/traditional, or explicitly experimental for v2.0?
- **First-50 source mix:** Original classical text only, adapted didactic sentences, or a marked mixture?
- **Rafael Falcon implementation rules:** Exact early ordering, blocked constructions, and case/function progression.
- **Grammar terminology style:** `singularis/pluralis` vs `sg/pl`; Latin tense/mood/voice terms vs Portuguese terms.
- **Locative handling:** Include `Locativus` internally while restricting final MVP case examples, or expose it when needed?
- **Review visibility:** Should `Review Status` be visible on the Anki card, hidden in note fields, or only in CSV/TSV evidence?
- **CLTK dependency mode:** Runtime dependency, optional extra, or dev/import-only until Windows stability is proven?
- **Card identity:** Stable GUID tuple should be finalized before curation: likely `latin_mvp_version + lemma + source_id + citation + target_form`.

## Suggested Requirement Categories

- **LATIN-MODE:** separate Classical Latin source/profile, variant metadata, existing-mode regression guards.
- **LATIN-SCOPE:** reproducible 50-card MVP cap, source pack versioning, no 3000-card scaling in v2.0.
- **LATIN-FREQ:** lemma-based ranking, DCC/project frequency metadata, didactic order, frequency audit report.
- **LATIN-SOURCE:** sentence catalog, source registry, citation/license/provenance, source-type labeling.
- **LATIN-SENTENCE:** target-form presence, sentence length/difficulty, enclitic/orthography handling, Rafael Falcon progression rules.
- **LATIN-GRAMMAR:** morphology evidence, grammar style guide, `Gramatica` formatter, allowed case/function labels, ambiguity gates.
- **LATIN-PT:** Portuguese word translation, sentence translation, contextual sense QA, immutable reviewed text.
- **LATIN-REVIEW:** review states, approved-only learner export, rejection/reopen workflow, reviewer evidence.
- **LATIN-AUDIO:** eSpeak/Azure policy, word/sentence audio, provider metadata, playback review, exact text integrity.
- **LATIN-EXPORT:** dedicated note type/template, field order, blank `Image`, APKG/CSV/TSV, Anki import/playback evidence.
- **LATIN-EVIDENCE/REGRESSION:** scanner-readable requirement coverage, artifact/license/privacy scanner, unchanged existing deck modes.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack | MEDIUM-HIGH | Existing Python stack is proven; DCC/CLTK 1.5/eSpeak choices are well supported, but TTS quality and optional native tools need validation. |
| Features | MEDIUM-HIGH | User intent and table stakes are explicit; exact first-50 content and Falcon progression rules require calibration. |
| Architecture | HIGH | Separate source profile, frozen assets, validators, review gates, and dedicated export contracts align with existing v1.x architecture. |
| Pitfalls | MEDIUM-HIGH | Main risks are well identified from prior shipped modes plus Latin-specific ambiguity/licensing/TTS constraints. |

**Overall confidence:** MEDIUM-HIGH.

### Gaps to Address

- **Licensing reuse:** resolve before selecting production sentence fixtures.
- **Audio acceptability:** run sample playback review before promising learner-quality Latin audio.
- **First-50 curation:** define exact lemmas, didactic order, sources, and replacements.
- **Grammar style guide:** freeze labels, abbreviations, locative/uncertainty handling, and tense/mood language.
- **Portuguese translation style:** decide literal vs natural balance and reviewer standards.
- **Broad-suite drift:** existing broad test drift should not be treated as authoritative until repaired; use focused regression evidence in v2.0 phases.

## Sources

### Primary (HIGH confidence)

- `.planning/PROJECT.md` — current product state, v2.0 goal, constraints, shipped v1.x evidence.
- `LATIN-STRUCTURE.md` — user-approved Latin product direction, card fields, Rafael Falcon guidance, open decisions.
- `.planning/research/FEATURES.md` — Latin table stakes, differentiators, anti-features, requirement seeds.
- `.planning/research/ARCHITECTURE.md` — integration boundaries, data flow, component map, build order.
- `.planning/research/PITFALLS.md` — critical pitfalls, mitigations, phase warnings, evidence recommendations.
- DCC Latin Core Vocabulary/About/Terms — lemma/core vocabulary, ranks, Portuguese localization, CC BY-SA implications.
- CLTK PyPI/GitHub — CLTK 1.5.0 Python 3.12 compatibility; CLTK 2.x Python 3.13 constraint.
- eSpeak NG docs — explicit Latin `la` support and local WAV generation.
- Azure Speech language/voice support — no dedicated Classical Latin locale found; multilingual voices require validation.

### Secondary (MEDIUM-HIGH / MEDIUM confidence)

- PerseusDL canonical Latin literature / Scaife — credible source discovery and canonical citations; per-text licensing must be verified.
- Collatinus, Perseus Morpheus, UD Latin Perseus/treebanks — useful morphology/reference fixtures; licensing/integration constraints require careful boundaries.
- Anki manual / genanki behavior — field/media/template constraints; import/playback evidence still required.

---
*Research completed: 2026-06-01*  
*Ready for requirements and roadmap: yes.*
