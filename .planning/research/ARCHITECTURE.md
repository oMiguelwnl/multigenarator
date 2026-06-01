# Architecture Research: v2.0 Classical Latin MVP Integration

**Project:** Multilang Anki Card Generator  
**Milestone:** v2.0 Classical Latin MVP  
**Researched:** 2026-06-01  
**Scope:** Integrate a 50-card Classical Latin MVP into the existing Python CLI/batch architecture without rewriting shipped frequency, custom word-list, or Kindle-highlight flows.  
**Overall confidence:** HIGH for integration shape and existing-code boundaries; MEDIUM for exact Latin NLP/TTS quality until phase evidence runs against curated fixtures and human audio review.

## Executive Recommendation

Add Latin as a **separate source/profile family** that reuses the existing job, repository, audio, validation, and genanki infrastructure, but does **not** pretend Latin is just another modern `frequency` language. The new path should be `source_type="latin-mvp"`, `language="la"`, and should assemble cards from curated Latin-specific assets rather than from `wordfreq` or normal LLM sentence generation.

Recommended MVP flow:

```text
latin curated source pack
  -> NEW LatinFrequencyAssetLoader       # lemma ranks + DCC/Core support metadata
  -> NEW LatinSentenceSourceCatalog      # sentence, source citation, license/provenance
  -> NEW LatinMorphologyAnalyzer         # CLTK first, Morpheus/curated fallback validation
  -> NEW LatinCardAssembler              # Portuguese translation + short Gramatica + review status
  -> existing job/repository boundary    # persisted as Latin records/snapshots
  -> modified audio provider registry    # eSpeak NG first for la, Azure multilingual as evaluated fallback only
  -> NEW Latin export row/model/template # Latin-specific APKG fields
```

Do **not** route Latin through the normal frequency-deck text generator as the primary source of truth. For v2.0, the most reliable architecture is a **curated evidence pipeline**: every accepted Latin card stores the lemma rank, sentence source, morphological analysis, Portuguese-facing fields, audio metadata, and review status. AI may assist translation or grammar drafting later, but the export gate should trust only reviewed structured records.

## Boundaries to Preserve

| Existing boundary | Preserve how | Why |
|---|---|---|
| Frequency/custom/highlight source profiles | Add `latin-mvp`; do not change existing profile values or field names. | Prevents Latin field/template rules from leaking into shipped deck modes. |
| `GenerationJob` lifecycle | Reuse jobs/resume/progress, but add Latin stages. | Keeps operational behavior consistent. |
| Provider adapters | Add a Latin audio adapter/selector behind the existing audio abstraction. | Avoids provider-specific calls inside card assembly/export. |
| Export snapshotting | Latin gets its own export row contract; normal `ExportCardRow` remains untouched except source dispatch. | Latin fields differ enough that aliasing normal fields would create brittle mappings. |
| Validation gates | Add Latin-specific validators before export; keep v1.3 normal-card validators unchanged. | Latin grammar/source/review checks are different from IPA/translation remediation. |
| Tests with deterministic local/fallback adapters | Use fake CLTK/Morpheus/eSpeak adapters and golden fixtures. | v2.0 evidence must be reproducible without network or installed native tools. |

## Target Latin Data Flow

```text
CLI: multilang latin build-mvp --limit 50 --asset-version latin-mvp-2026-06
  |
  |-- LatinSourcePackLoader
  |     reads versioned local assets:
  |       latin_lemma_frequencies.csv/json
  |       latin_sentence_catalog.csv/json
  |       latin_translation_review.csv/json
  |       optional morph_overrides.csv/json
  |
  |-- LatinCandidatePlanner
  |     joins lemma rank + Rafael-Falcon progression policy
  |     emits 50 ordered LatinCardCandidate records
  |
  |-- LatinMorphologyAnalyzer
  |     CLTK Latin pipeline for tokenization/lemmatization/morph features
  |     Morpheus/curated override as fallback/cross-check
  |     emits LatinMorphologyEvidence + confidence
  |
  |-- LatinGrammarNoteBuilder
  |     deterministic formatter for `Gramatica`
  |     never free-form at export boundary
  |
  |-- LatinCardReviewService
  |     requires review_status = approved for export
  |     stores rejection/uncertainty reasons
  |
  |-- GenerateAudioItemsService / AudioSynthesisService
  |     audio_kind = word/sentence
  |     provider plan = espeak-ng la first, Azure multilingual only if explicitly approved by review
  |
  |-- LatinExportAssembler
  |     builds LatinExportCardRow with fixed field order
  |
  `-- export_anki_package
        source_type = latin-mvp
        note type = Multilang::Latin Card
        template = latin_card
        APKG + CSV/TSV evidence
```

## Component Map: New vs Modified vs Unchanged

| Component | Status | Conceptual module | Recommendation |
|---|---|---|---|
| Supported language enum | Modified | `multilang.domain.jobs.SupportedLanguage` | Add `LA = "la"` only where source profile is Latin-aware. If normal frequency generation assumes 3x1000, guard it so `la` cannot accidentally run as normal `frequency`. |
| Source profiles | Modified | `multilang.domain.source_profiles` | Extend `SourceType` with `"latin-mvp"`. Add profile fields if needed: `requires_review_status`, `template_name="latin_card"`, `note_type_name="Multilang::Latin Card"`, `exports_translation_field=False`, `max_sentence_tokens` Latin-specific. |
| Latin domain contracts | New | `multilang.domain.latin` | Add Pydantic models for frequency entry, source sentence, morphology evidence, grammar note, review status, and Latin export row. Keep Latin grammar terms as enums. |
| Latin source pack loader | New | `multilang.services.latin_assets` | Load frozen local CSV/JSON assets. Validate source licenses/provenance at load time. Do not scrape live sites during generation. |
| Latin frequency planning | New | `multilang.services.latin_frequency` | Use DCC Core Vocabulary ranks/support metadata plus project-curated lemma ranks. Store final MVP rank as project-owned asset; do not rely on `wordfreq`. |
| Latin sentence catalog | New | `multilang.services.latin_sentence_sources` | Store short real or didactic Latin sentences with source citation, text type, difficulty tags, license/provenance, and target form span. |
| Latin morphology adapter | New | `multilang.services.latin_morphology` | Wrap CLTK as primary Python-friendly analyzer; support Morpheus/curated override as cross-check. Output normalized project enums, not raw tool output. |
| Grammar note builder | New | `multilang.services.latin_grammar_notes` | Deterministically format `Gramatica` from normalized morphology/syntax fields. No free-form grammar strings at export. |
| Review service | New | `multilang.services.latin_review` | Enforce `needs_review`, `approved`, `rejected`, `approved_with_audio_warning` policies. Export only approved cards unless a phase explicitly allows warning exports. |
| Audio registry/selection | Modified | `audio_voice_registry`, `audio_synthesis`, new `espeak_ng_speech_adapter` | Add provider-selection by `language=la`. Use eSpeak NG for MVP because it has explicit Latin support and local deterministic operation. Keep Azure as experimental fallback only after voice-gallery/human review; Azure docs do not list a Latin locale, though multilingual voices exist. |
| Audio metadata/integrity | Modified | `domain.audio`, `audio_integrity` | Track `provider`, `voice_id`, `locale_or_voice="la"`, `pronunciation_policy`, `quality_status`, input hash, and whether audio is experimental. Existing word-audio exact-match checks should apply to `target_form`. |
| Persistence | Modified or new tables | `db.models` + Alembic | Prefer one or two Latin-specific tables rather than overloading `lexical_candidates`/`text_quality_records`: `latin_cards` and optional `latin_source_sentences`. Keep export snapshots in existing `card_exports` only if field JSON can preserve Latin-specific fields; otherwise add Latin export snapshot JSON. |
| Export contracts | New + modified dispatch | `domain.exporting`, `export_anki_package`, `export_tabular_bundle` | Add `LatinExportCardRow`, `LATIN_EXPORT_CARD_FIELD_NAMES`, and exact source-type model selection. Do not force Latin through normal `ExportCardRow` aliases. |
| Template | New | `templates/latin_card.md` | Front: target form, Latin sentence, word/sentence audio. Back: lemma, Portuguese word translation, sentence translation, `Gramatica`, source, blank `Image`. |
| CLI/runtime | Modified | `cli.py`, `runtime.py` | Add a focused Latin command or source option. Prefer `latin build-mvp`, `latin validate`, `latin export` commands over hidden flags on normal generation. |
| Existing frequency/custom/highlight services | Unchanged except guard tests | `frequency_decks`, `ingest_lexical_items`, highlight services | Do not add Latin branches inside every existing service. Latin should enter shared infra at job/audio/export boundaries only. |

## Recommended Domain Contracts

Add `multilang.domain.latin` with explicit enums and Pydantic models:

```python
class LatinReviewStatus(str, Enum):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    APPROVED_WITH_AUDIO_WARNING = "approved_with_audio_warning"
    REJECTED = "rejected"

class LatinCase(str, Enum):
    NOMINATIVUS = "Nominativus"
    VOCATIVUS = "Vocativus"
    ACCUSATIVUS = "Accusativus"
    GENITIVUS = "Genitivus"
    DATIVUS = "Dativus"
    ABLATIVUS = "Ablativus"

class LatinCardCandidate(BaseModel):
    language_code: Literal["la"] = "la"
    frequency_rank: int
    frequency_source: str
    lemma: str
    target_form: str
    latin_sentence: str
    source_citation: str
    source_url: str | None = None
    sentence_kind: Literal["classical", "didactic"]
    difficulty_tags: tuple[str, ...] = ()

class LatinMorphologyEvidence(BaseModel):
    target_form: str
    lemma: str
    part_of_speech: str
    case: LatinCase | None = None
    number: str | None = None
    gender: str | None = None
    declension_or_conjugation: str | None = None
    syntactic_function: str
    analyzer: str
    confidence: Literal["high", "medium", "low"]
    ambiguity_notes: str | None = None

class LatinCardRecord(BaseModel):
    candidate: LatinCardCandidate
    short_translation_pt: str
    sentence_translation_pt: str
    grammar: str
    morphology: LatinMorphologyEvidence
    review_status: LatinReviewStatus
    reviewer_notes: str = ""
    word_audio: str = ""
    sentence_audio: str = ""
    image: Literal[""] = ""
```

Key rule: `Genitivus` is the only exported spelling. Accept `Genetivus` only as import/user-note input and normalize it before persistence/export.

## Persistence and Migration Guidance

### Prescriptive recommendation

Add Latin-specific persistence for the MVP:

| Table | Purpose | Required columns |
|---|---|---|
| `latin_card_records` | Source of truth for reviewed Latin MVP cards | `id`, `job_id`, `item_key`, `frequency_rank`, `frequency_source`, `lemma`, `target_form`, `latin_sentence`, `short_translation_pt`, `sentence_translation_pt`, `grammar`, `source_citation`, `source_url`, `sentence_kind`, `morphology_json`, `review_status`, `reviewer_notes`, `provenance_json`, timestamps |
| `latin_source_sentences` (optional but recommended) | Reusable catalog of Latin sentences | `id`, `source_key`, `latin_sentence`, `source_citation`, `source_url`, `license_note`, `difficulty_tags`, `provenance_json` |

Why not only JSON in `lexical_candidates.provenance`? Latin has first-class fields (`Gramatica`, source citation, review status, target form, Portuguese translation) that need export gates and audit evidence. A dedicated table is clearer and safer than hiding core card state in `provenance`.

Existing tables remain useful:

- `generation_jobs`: `language="la"`, `source_type="latin-mvp"`, source fingerprint from asset-version + 50 selected item keys.
- `generation_items`: one item per Latin card candidate.
- `audio_assets`: store Latin word/sentence audio metadata; extend metadata shape, not necessarily table columns.
- `deck_exports`: normal artifact metadata.
- `provider_call_logs`: reusable for Azure or other provider attempts; eSpeak local synthesis can also log provider=`espeak-ng` for evidence.

## Latin Source Asset Strategy

### Frequency resources

Use a **project-frozen Latin MVP frequency asset**, seeded from DCC Core Vocabulary and/or a CLTK/Perseus-derived lemma count, then manually curated for 50 cards. `wordfreq` does not cover Latin per the milestone seed, and normal modern-language frequency windows do not apply.

Recommended asset fields:

```text
rank, lemma, display_headword, pos, dcc_rank, corpus_rank, pedagogic_priority,
falcon_stage, include_in_mvp, notes, source_refs
```

DCC is useful because it exposes Latin headwords, parts of speech, semantic groups, and frequency rank, with Portuguese pages available. Treat it as support data, not the only authority for sentence choice.

### Sentence resources

Store source sentences in a local catalog. Each row must include:

- Latin sentence text.
- `target_form` and target span/token index.
- Source citation (`Vergil, Aeneid 1.1`, `Disticha Catonis`, etc.).
- Source URL/repository if applicable.
- License/provenance note.
- Sentence kind: `classical` or `didactic`.
- Difficulty tags: `simple_svo`, `nominativus`, `accusativus`, `ablativus`, `poetry_complexity`, etc.

Perseus canonical Latin literature is a credible source for classical texts but has CC-BY-SA obligations and warns that metadata may vary. Perseus Treebank Data is useful for syntactic/morphological evaluation fixtures and is CC-BY-SA 3.0 US. Do license/provenance checks before packaging substantial text excerpts.

## Morphology and Grammar Boundaries

### Analyzer strategy

Use CLTK as the primary integration seam because it is a Python library for pre-modern-language NLP and has current releases/docs. Do **not** let raw CLTK output leak into cards. Normalize into project enums and require a reviewed override when ambiguous.

Morpheus is useful as a secondary validator because it is a Perseus morphological parser with Latin stem libraries, but it is older/native-tool oriented. Use it behind a `LatinMorphologyAnalyzer` protocol so tests can fake it and Windows setup does not block the whole MVP.

```python
class LatinMorphologyAnalyzer(Protocol):
    def analyze(self, sentence: str, target_form: str, lemma_hint: str) -> LatinMorphologyEvidence: ...
```

### Grammar-note generation

`Gramatica` should be a deterministic formatter, not an LLM field:

```text
{target_form}: {pos_abbrev} {gender?}, {declension/conjugation?}, {case?} {number?}, {syntactic_function}.
```

Examples:

```text
virum: subst masc, 2a declinacao, Accusativus singularis, OD.
cano: v, 3a conjugacao, 1a pessoa singular, praesens indicativus activus, verbo principal.
```

If analysis is ambiguous, do not export silently. Either set `review_status="needs_review"` or include a controlled uncertainty marker in reviewer notes, not in the final grammar field unless explicitly approved.

## Audio Provider Selection

### Recommendation

For the 50-card MVP, implement a local `EspeakNgSpeechAdapter` and make it the default Latin provider. eSpeak NG officially supports more than 100 languages and is a command-line synthesizer that can output WAV; the seed confirms `-v la` is available. Its formant synthesis is clear but less natural, so audio quality must be reviewable.

Azure Speech should remain **experimental for Latin** in v2.0. Microsoft’s current language-support page lists many TTS locales and multilingual voices, but it does not list a dedicated Latin locale. Multilingual voices may pronounce Latin text, but the project should not mark that as accepted without human playback evidence. Add Azure Latin candidates only behind a config flag such as `latin_audio_provider=azure-multilingual-experimental` and persist `quality_status="needs_audio_review"`.

### Adapter boundary

```python
class SpeechSynthesisAdapter(Protocol):
    def synthesize(self, request: AudioSynthesisRequest) -> AudioSynthesisResult: ...

class EspeakNgSpeechAdapter:
    # shells out to espeak-ng with fixed args, timeout, and output path
    # test with fake subprocess runner
```

Audio validation additions:

- Word audio input text must equal `target_form`, not lemma.
- Sentence audio input text must equal `latin_sentence` after normalized whitespace.
- Store provider/voice/version/command hash.
- MVP export gate should either require both audio files or explicitly allow `approved_with_audio_warning`; choose one in requirements before implementation.

## Latin APKG Export Contract

Add a dedicated Latin note type rather than overloading normal or highlight cards.

### Field order

```python
LATIN_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "Target Form",
    "Latin Sentence",
    "word_audio",
    "sentence_audio",
    "Lemma",
    "Translation PT",
    "Sentence Translation PT",
    "Gramatica",
    "Source",
    "Review Status",
    "Image",
)
```

`Review Status` may be included for MVP evidence. If the final study card should hide it, keep it on the note but not visibly rendered, or export it in CSV/TSV evidence only. The roadmap should decide this explicitly.

### Template behavior

Front:

- `Target Form`
- `Latin Sentence`
- word audio and sentence audio

Back:

- `Lemma`
- `Translation PT`
- `Sentence Translation PT`
- `Gramatica`
- `Source`
- blank `Image`

Export gate:

- Mixed source types fail fast.
- `source_type="latin-mvp"` selects `Multilang::Latin Card`, `templates/latin_card.md`, and Latin fields.
- `Image` must be blank.
- `Review Status` must be `approved` unless the phase requirement explicitly permits `approved_with_audio_warning`.

## Validation Boundaries

| Boundary | Validator | Blocks export when |
|---|---|---|
| Frequency asset | `LatinFrequencyAssetValidator` | duplicate ranks, missing lemma, no source, non-MVP rank gap, rank not stable for selected 50 |
| Sentence source | `LatinSentenceCatalogValidator` | missing citation/source, target form absent, sentence too long, prohibited complex tag for early MVP, license note missing |
| Morphology | `LatinMorphologyValidator` | lemma mismatch, case outside approved enum, `Genetivus` not normalized, ambiguity unreviewed |
| Grammar note | `LatinGrammarNoteValidator` | does not start with target form, missing POS/function, unsupported case label, too long/free-form explanation |
| Portuguese fields | `LatinPortugueseTextValidator` | empty word/sentence translation, translation is just the Latin word, obvious placeholder/review text |
| Review | `LatinReviewValidator` | `needs_review` or `rejected` card selected for APKG |
| Audio | `LatinAudioIntegrityValidator` | missing required audio, word-audio text mismatch, stale synthesized hash, experimental provider without approved status |
| Export | `LatinExportQualityGate` | wrong field order, nonblank image, mixed source types, fewer/more than requested 50 cards |

## Suggested Build Order Starting at Phase 22

### Phase 22: Latin contracts, source profile, and export isolation

Build first:

- `SupportedLanguage.LA` and `source_type="latin-mvp"` guards.
- `multilang.domain.latin` enums/models.
- `LATIN_EXPORT_CARD_FIELD_NAMES`, `LatinExportCardRow`, source-specific genanki model dispatch.
- Tests proving frequency, word-list, and Kindle-highlight field orders/templates are unchanged.

Rationale: Latin schema/export isolation must exist before source/morph/audio work, otherwise implementation will overload normal card fields.

### Phase 23: Versioned Latin source packs and frequency planning

Build:

- Local asset directory and loader for lemma ranks, sentence catalog, translation/review seed rows.
- `LatinCandidatePlanner` with deterministic 50-card selection.
- Validation for DCC/project rank metadata and Rafael-Falcon progression tags.

Rationale: MVP content must be reproducible and reviewable before automated morphology/audio is introduced.

### Phase 24: Morphology normalization and grammar notes

Build:

- `LatinMorphologyAnalyzer` protocol with deterministic fake adapter.
- CLTK adapter behind optional dependency/config.
- Curated override mechanism for ambiguous forms.
- `LatinGrammarNoteBuilder` and validators for case/function labels.

Rationale: `Gramatica` is the highest-risk learner-facing new field; solve it before APKG/audio polish.

### Phase 25: Review status and persistence

Build:

- Alembic migration for `latin_card_records` and optional `latin_source_sentences`.
- Repository/service for review transitions.
- Export gate requiring approved cards.

Rationale: Review state is the safety mechanism for morphology, translation, source quality, and audio uncertainty.

### Phase 26: Latin audio provider adapter and integrity checks

Build:

- `EspeakNgSpeechAdapter` with fake subprocess tests and local timeout/error handling.
- Audio selection policy for `la`.
- Word/sentence audio metadata and exact-input validation against `target_form` and `latin_sentence`.
- Human-review evidence artifact for representative audio samples.

Rationale: Audio has uncertain quality and native-tool dependency; keep it after card content is stable.

### Phase 27: Latin APKG/CSV/TSV export evidence

Build:

- `templates/latin_card.md`.
- Latin APKG export, CSV/TSV export, and 50-card quality gate.
- End-to-end smoke: source pack -> reviewed records -> mocked or local audio -> APKG.
- Regression tests proving existing frequency/custom/highlight exports still pass.

Rationale: Packaging should be the final integration phase after source, grammar, review, and audio contracts are stable.

## Test Evidence Strategy

| Test layer | Evidence to add | Must prove |
|---|---|---|
| Domain unit | Latin enums/model validation | `Genitivus` canonicalization, review statuses, nonblank required fields |
| Asset fixtures | 5-card and 50-card source packs | Stable rank ordering, source citations, target form spans |
| Morphology unit | Fake analyzer + override fixtures for nouns, verbs, prepositions, enclitics | Normalized cases/functions and ambiguity handling |
| Grammar golden files | Input morphology -> exact `Gramatica` strings | Short deterministic format, no unsupported labels |
| Persistence | Repository round-trip for Latin records | JSON morphology/provenance preserved, review transitions audited |
| Audio | Fake eSpeak adapter and optional installed-tool smoke | Word/sentence exact input, stale audio blocked, provider metadata saved |
| Export contract | Latin field order/template/model tests | No normal/highlight field leakage; blank image; source shown on back |
| E2E | 3-card fast fixture and 50-card MVP evidence run | Pipeline produces APKG/CSV/TSV with approved cards only |
| Regression | Existing frequency/custom/highlight focused suites | Latin changes do not rewrite shipped flows |

## Integration Risks and Mitigations

### Risk 1: Latin treated as normal `frequency`

**Consequence:** 3x1000 deck gates, normal fields, `wordfreq`, IPA, and modern-language translations leak into Latin.  
**Mitigation:** explicit `latin-mvp` source profile, dispatch tests, and CLI guard that rejects `language=la source_type=frequency` until a future scaled Latin phase defines it.

### Risk 2: Morphological ambiguity creates false grammar notes

**Consequence:** learner studies incorrect case/function.  
**Mitigation:** store analyzer confidence and ambiguity notes; require curated override or approval before export.

### Risk 3: Source licensing/provenance forgotten

**Consequence:** APKG uses text without traceable source or incompatible obligations.  
**Mitigation:** source catalog requires citation/license note; export gate blocks missing source.

### Risk 4: eSpeak audio is technically present but pedagogically poor

**Consequence:** MVP meets automation but not study quality.  
**Mitigation:** audio quality status and human playback checklist; allow roadmap decision whether `approved_with_audio_warning` is exportable.

### Risk 5: Review status becomes decorative

**Consequence:** `needs_review` cards ship.  
**Mitigation:** DB/repository review transitions plus export gate; tests with rejected/needs-review rows.

## Sources and Evidence

- `.planning/PROJECT.md` — current v2.0 Latin goals, constraints, existing architecture, and validated v1.3 state. [HIGH]
- `.planning/ROADMAP.md` — current phase numbering; v1.3 ended at Phase 21, so v2.0 should start at Phase 22 unless reset. [HIGH]
- `LATIN-STRUCTURE.md` — user-approved Latin MVP direction, fields, grammar examples, frequency/morphology/source/audio questions. [HIGH]
- Code inspection: `domain.exporting`, `domain.source_profiles`, `db.models`, `audio_voice_registry`, existing services/repositories. [HIGH]
- CLTK GitHub/docs — Python NLP toolkit for pre-modern languages; current repo shows installation and Latin language code examples, latest release v1.5.0 May 2025. https://github.com/cltk/cltk [MEDIUM-HIGH]
- Dickinson College Commentaries Latin Core Vocabulary — Latin headwords, definitions, parts of speech, semantic groups, frequency ranks, and Portuguese view. https://dcc.dickinson.edu/latin-core-list1 [HIGH]
- Perseus Canonical Latin Literature — canonical XML Latin literature repository, CC-BY-SA-4.0, active releases through 2026. https://github.com/PerseusDL/canonical-latinLit [MEDIUM-HIGH]
- Perseus Treebank Data — published treebank data, current data v2.0 with v2.1 release, CC-BY-SA-3.0 US. https://github.com/PerseusDL/treebank_data [MEDIUM-HIGH]
- Perseus Morpheus — Latin/Greek morphological parser with Latin stem library, native build/run model. https://github.com/PerseusDL/morpheus [MEDIUM]
- eSpeak NG — command-line/local TTS, more than 100 languages, WAV output, formant synthesis quality caveat. https://github.com/espeak-ng/espeak-ng [HIGH]
- Azure Speech language/voice support — current Microsoft docs list TTS locales and multilingual voices but no dedicated Latin locale found in fetched table. https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts [HIGH for Azure support table, MEDIUM for negative Latin conclusion]
