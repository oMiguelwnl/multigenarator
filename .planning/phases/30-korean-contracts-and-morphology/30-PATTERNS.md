# Phase 30: Korean Contracts and Morphology - Pattern Map

**Mapped:** 2026-08-03
**Requirements:** KMODE-01, KMODE-02, KNLP-01, KNLP-02
**Files classified:** 40 (26 production/configuration, 14 tests)
**Structural analogs found:** 40 / 40
**Exact Korean morphology algorithm analogs:** 0 / 1

## Inputs And Scope Truth

- No Phase 30 `CONTEXT.md`, `APPROACH.md`, or `RESEARCH.md` exists. This map is inferred from `.planning/SPEC.md`, `.planning/ROADMAP.md`, `KOREAN-STRUCTURE.md`, and the live codebase.
- Lifecycle preflight for planning Phase 30 returned `allowed`; the control map reported a clean `Monarch` worktree at `5b134cc`.
- The Mandarin prerequisite is reconciled in code (`dc63333`), even though stale prose in `SPEC.md`/`STATE.md` still describes it as active.
- Phase 30 is specifically **contracts, registries, Kiwi, Unicode, and target matching** (`KOREAN-STRUCTURE.md:475-481`).

### Locked Outcomes

| Requirement | Concrete implication for this phase |
|---|---|
| KMODE-01 | `SupportedLanguage.KO.value == "ko"`; settings, jobs, run keys, DB rows, prompts, export identities, and Anki tags use `ko`. `ko-KR` is a provider-locale constant only. |
| KMODE-02 | Keep modern frequency/manual/highlight schemas, Japanese models/furigana, Mandarin fields/snapshots, Latin isolation, phoneme decks, and current audio behavior unchanged. |
| KNLP-01 | Normalize Korean canonical values to NFC, preserve submitted input separately, pin Kiwi, persist analyzer/version and typed lemma/POS/morpheme evidence, and cover deterministic golden cases. |
| KNLP-02 | Match a persisted Korean lexical identity against sentence/highlight morpheme signatures. Never fall through to whitespace, substring, suffix stripping, or an “unreliable but probably okay” result. |

### Hard Scope Boundaries

Do **not** create or modify these Phase 31-34 artifacts in Phase 30:

- `assets/frequency/ko/curated-v1.csv` or any redistributed 3000-row Korean asset. The source/license gate is unresolved.
- A Korean Azure voice entry, generated Korean audio, or ElevenLabs/Google consumer-TTS fallback. Exact live Azure voice qualification belongs to Phase 32.
- Korean templates, note-type/model/deck IDs, Hangul cards, pronunciation cards, grammar cards, or final three-real-subdeck topology.
- Romanization fields, Hanja support, dialect support, or learner-visible morphology fields.
- Tatoeba as a default Korean fallback.
- LLM-derived morphology, POS, sense identity, or pronunciation approval.

Phase 30 should prove that the existing generic frequency/manual/highlight export schemas can carry canonical Korean text and `ko` identity. It should not introduce the final Korean export model early.

## File Classification

### Production And Configuration

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `pyproject.toml` | config | batch | Japanese pins in `pyproject.toml:23-33` | exact |
| `uv.lock` | config | batch | Fugashi/Pypinyin lock updates from Japanese/Mandarin | exact |
| `src/multilang/domain/jobs.py` | model | request-response | `SupportedLanguage.JA/ZH` at `domain/jobs.py:12-35` | exact |
| `src/multilang/settings.py` | config | request-response | `SupportedLanguageCode` and defaults at `settings.py:11-64` | exact |
| `src/multilang/domain/korean.py` **(create)** | model | transform | `domain/latin.py:10-76`; `latin_source_pack.py:152-184` | role-match |
| `src/multilang/domain/lexicon.py` | model | CRUD/transform | `LexicalCardCandidate` at `domain/lexicon.py:54-69` | exact |
| `src/multilang/domain/highlights.py` | model | file-I/O/transform | `HighlightCandidate` at `domain/highlights.py:50-66` | exact |
| `src/multilang/services/korean_morphology.py` **(create)** | service | transform | `mandarin_orthography.py:13-64`; `morphology.py:33-96` | partial |
| `src/multilang/runtime.py` | provider/composition root | request-response | shared service construction at `runtime.py:521-629` | exact |
| `src/multilang/services/word_list_parser.py` | utility | file-I/O/transform | key normalization at `word_list_parser.py:36-40,152-203` | exact |
| `src/multilang/services/input_fingerprint.py` | utility | transform | deterministic normalization at `input_fingerprint.py:11-44` | exact |
| `src/multilang/services/lexical_lookup.py` | service | file-I/O/CRUD | normalized index lookup at `lexical_lookup.py:11-61` | exact |
| `src/multilang/services/lexical_grounding.py` | service | CRUD/transform | three grounding entry points at `lexical_grounding.py:67-177` | exact |
| `src/multilang/services/highlight_candidate_extraction.py` | service | file-I/O/transform | generic extraction at `highlight_candidate_extraction.py:49-129` | role-match |
| `src/multilang/services/highlight_import_preview.py` | service | file-I/O/transform | parser-to-extractor composition at `highlight_import_preview.py:13-39` | exact |
| `src/multilang/services/ingest_lexical_items.py` | service | batch/CRUD | mode dispatch and persistence at `ingest_lexical_items.py:67-95,141-174` | exact |
| `src/multilang/services/text_generation.py` | service/model | request-response | typed provider boundary at `text_generation.py:20-48,150-181` | exact |
| `src/multilang/services/generate_text_items.py` | service | batch/request-response | validate/repair/fallback orchestration at `generate_text_items.py:300-449` | exact |
| `src/multilang/services/text_validation.py` | service | transform | morphology seam at `text_validation.py:268-319` | exact |
| `src/multilang/services/provider_text_adapters.py` | provider | request-response | language maps and prompts at `provider_text_adapters.py:38-85,398-450` | exact |
| `src/multilang/services/tatoeba_sentence_source.py` | provider | request-response | adapter code map/filtering at `tatoeba_sentence_source.py:48-69,190-257` | role-match |
| `src/multilang/services/audio_voice_registry.py` | config/service | request-response | fail-closed selection at `audio_voice_registry.py:150-173` | role-match |
| `src/multilang/db/models.py` | model | CRUD | `LexicalCandidate` at `db/models.py:207-248` | exact |
| `src/multilang/repositories/lexical_repository.py` | repository | CRUD | payload/round-trip at `lexical_repository.py:185-235` | exact |
| `alembic/versions/20260803_16_korean_lexical_identity.py` **(create)** | migration | CRUD | `20260502_08_spoken_form.py:14-25` | exact |
| `scripts/build_frequency_assets.py` | utility/config | file-I/O/batch | language iteration at `build_frequency_assets.py:51-69` | exact |

### Tests

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/domain/test_korean.py` **(create)** | test | transform | `tests/domain/test_latin_contracts.py:18-53` | role-match |
| `tests/services/test_korean_morphology.py` **(create)** | test | transform | `tests/services/test_mandarin_orthography.py:18-73` | role-match |
| `tests/services/test_korean_language_support.py` **(create)** | test | request-response | `tests/services/test_mandarin_language_support.py:51-310` | exact |
| `tests/integration/test_korean_modern_flow.py` **(create)** | test | batch/CRUD | `tests/integration/test_mandarin_modern_flow.py:146-333` | exact |
| `tests/domain/test_jobs.py` | test | request-response | exhaustive language set at `test_jobs.py:16-44` | exact |
| `tests/test_settings.py` | test | request-response | ordered default list at `test_settings.py:8-32` | exact |
| `tests/services/test_frequency_decks.py` | test | file-I/O/batch | Mandarin normalization + all-assets gate at `test_frequency_decks.py:127-187,363-374` | role-match |
| `tests/services/test_audio_voice_registry.py` | test | request-response | exhaustive registry coverage at `test_audio_voice_registry.py:17-29` | role-match |
| `tests/repositories/test_lexical_repository.py` | test | CRUD | candidate expire/reload pattern at `test_lexical_repository.py:66-139` | exact |
| `tests/test_migration_schema_parity.py` | test | CRUD | migration parity at `test_migration_schema_parity.py:41-66` | exact |
| `tests/services/test_text_validation.py` | test | transform | injected fake morphology at `test_text_validation.py:31-43,467-499` | exact |
| `tests/services/test_highlight_candidate_extraction.py` | test | file-I/O/transform | ordered/privacy-safe extraction at `test_highlight_candidate_extraction.py:55-85,115-169` | exact |
| `tests/services/test_generate_text_items.py` | test | batch/request-response | Tatoeba call tracking and repair-chain tests | exact |
| `tests/test_runtime.py` | test | request-response | monkeypatched adapter wiring at `test_runtime.py:123-190` | exact |

## Pattern Assignments

### `src/multilang/domain/korean.py` (model, transform)

**Primary analog:** `src/multilang/domain/latin.py`

**Constants + typed model pattern** (`domain/latin.py:10-27`):

```python
LATIN_LANGUAGE_CODE = "la"
LATIN_MVP_CARD_COUNT = 50
DEFAULT_LATIN_SOURCE_PACK_VERSION = "latin-mvp-50-v1"


class LatinDeckMetadata(BaseModel):
    language_code: Literal["la"] = LATIN_LANGUAGE_CODE
    variant: LatinVariant = LatinVariant.CLASSICAL
    source_pack_version: str = Field(default=DEFAULT_LATIN_SOURCE_PACK_VERSION, min_length=1)
    card_count: int = LATIN_MVP_CARD_COUNT
```

Copy this style for canonical constants and typed Korean contracts, but **do not** copy Latin's isolated generation path. Korean belongs in the modern `GenerationRequest` pipeline.

The new module should be the one source for at least:

- canonical code `ko`;
- provider locale `ko-KR`;
- Seoul/modern-standard profile identity;
- NFC normalization/validation;
- immutable morpheme signature items;
- analyzer status/version evidence;
- `KoreanLexicalIdentity` matching `.planning/SPEC.md:85-93`.

**Fail-closed cross-field validation pattern** (`latin_source_pack.py:152-184`):

```python
class LatinMorphologyEvidence(BaseModel):
    lemma: str = Field(min_length=1)
    part_of_speech: LatinPartOfSpeech
    case_label: LatinCaseLabel | None = None
    number: LatinGrammarNumber | None = None
    verbal_analysis: str | None = None
    grammar_review_status: LatinGrammarReviewStatus = "approved"

    @model_validator(mode="after")
    def enforce_resolved_morphology(self) -> "LatinMorphologyEvidence":
        if self.grammar_review_status != "approved":
            raise ValueError("grammar_review_status must be approved")
        ...
        return self
```

Apply the same invariant style: a “resolved” Korean identity cannot have a blank lemma, blank/unknown POS, empty signature, blank sense ID, non-NFC canonical form, or unavailable/ambiguous analysis. Keep unavailable/ambiguous results as a separate result state rather than constructing a valid identity with placeholders.

**Do not copy:** `validate_simplified_mandarin()` uses NFKC (`mandarin_orthography.py:67-87`). Korean canonical learner content requires NFC; compatibility and halfwidth Hangul must be rejected, not silently compatibility-folded.

---

### `src/multilang/services/korean_morphology.py` (service, transform)

**Structural analog 1:** `src/multilang/services/mandarin_orthography.py`

**Error/result/service shape** (`mandarin_orthography.py:13-64`):

```python
class MandarinOrthographyError(ValueError):
    """Raised when Mandarin source text or a derived value is invalid."""


@dataclass(frozen=True, slots=True)
class MandarinOrthography:
    word_pinyin: str
    word_traditional: str
    sentence_pinyin: str
    sentence_traditional: str


class MandarinOrthographyService:
    def derive(self, *, word: str, sentence: str) -> MandarinOrthography:
        return derive_mandarin_orthography(word=word, sentence=sentence)
```

**Structural analog 2:** `src/multilang/services/morphology.py`

**Lazy optional dependency and explicit inconclusive result** (`morphology.py:39-64,80-96`):

```python
pipeline = self._pipeline_for(target_language)
if pipeline is None:
    return MorphologyValidationResult(
        matched=False,
        reliable=False,
        provider="stanza",
        detail=f"no local Stanza morphology pipeline for {target_language}",
    )

try:
    document = pipeline(sentence_text)
except Exception as exc:
    return MorphologyValidationResult(
        matched=False,
        reliable=False,
        provider="stanza",
        detail=f"Stanza morphology failed: {type(exc).__name__}",
    )
```

Use lazy/cached analyzer construction so a Kiwi install/model failure blocks Korean only and does not stop existing languages from booting. Unlike generic Stanza, Korean callers must treat `reliable=False` as a rejection, never permission to use a heuristic.

**Required wiring contract (interface plan, not Kiwi implementation):**

```text
analyze_lexeme(submitted_or_surface_text)
  -> resolved morphology analysis | unavailable | ambiguous | OOV

extract_lexical_identities(highlight_text)
  -> ordered lexical analyses preserving eojeol/compound boundaries

match_target(sentence_text, target_identity)
  -> matched | mismatch | unavailable | ambiguous
```

The adapter must expose normalized morpheme `(form, POS)` signatures, canonical lemma/POS, analyzer name/version, and enough eojeol boundary evidence to keep `공부/NNG + 하/XSV` together. Do not put actual Kiwi token API calls in the plan unless verified against the pinned version's docs/runtime.

**No in-repo algorithm to copy:** the codebase has no Korean analyzer, no Kiwi tag normalization, no Korean irregular reconstruction, and no morphology-aware compound predicate matcher. Use the approved Kiwi docs and deterministic real-analyzer golden tests; never fill this gap with suffix stripping.

---

### `pyproject.toml` and `uv.lock` (config, batch)

**Analog:** language analyzers are bounded in the main dependency list (`pyproject.toml:23-33`):

```toml
"wordfreq[jieba]>=3.1,<4.0",
...
"fugashi>=1.3,<2.0",
"unidic-lite>=1.0,<2.0",
"pypinyin>=0.55,<0.56",
"opencc-python-reimplemented>=0.1.7,<0.2",
```

Add the approved Kiwi/`kiwipiepy` pin as a direct runtime dependency and regenerate `uv.lock`. `KOREAN-STRUCTURE.md:332` requires a fixed compatible family; its source link is for `v0.23.2`. The planner should state the exact selected specifier and verify Windows/Python 3.12 support rather than using an unconstrained lower bound.

Required checks:

```text
uv lock --check
uv run python -c "import kiwipiepy; print(kiwipiepy.__version__)"
```

Current local runtime is Python 3.13.7, but the project contract remains Python `>=3.12`; do not validate only on 3.13.

---

### `src/multilang/domain/jobs.py` and `src/multilang/settings.py` (model/config, request-response)

**Analog:** Japanese and Mandarin append one canonical enum/default value (`domain/jobs.py:12-35`, `settings.py:11-64`):

```python
class SupportedLanguage(str, Enum):
    ...
    LA = "la"
    JA = "ja"
    ZH = "zh"
```

```python
SupportedLanguageCode = Literal[
    ...
    "la",
    "ja",
    "zh",
]

DEFAULT_SUPPORTED_LANGUAGES = (
    ...
    "la",
    "ja",
    "zh",
)
```

Add only `KO = "ko"` / `"ko"`. Do not admit `ko-KR` to either type. Typer already consumes `SupportedLanguage` directly (`cli.py:626-650`), so no separate CLI language parser is needed.

Because `scripts/build_frequency_assets.py` currently treats `DEFAULT_SUPPORTED_LANGUAGES` as “languages with committed assets,” split that capability before adding `ko`; otherwise ordinary `--check` and build-all commands will require or create a license-blocked Korean CSV.

---

### `scripts/build_frequency_assets.py` (utility/config, file-I/O/batch)

**Current conflation to remove** (`build_frequency_assets.py:51-69`):

```python
def build_assets(...):
    for code in _language_codes(language_code):
        _build_language_asset(...)


def _language_codes(language_code: str | None) -> tuple[str, ...]:
    if language_code is None:
        return DEFAULT_SUPPORTED_LANGUAGES
    return (language_code,)
```

Introduce/use an explicit “committed frequency assets currently approved” tuple that excludes `ko`. A direct `--language ko` build/check must fail with an actionable license-gate message rather than seed and write a file. Do not add a silent skip: build-all should be deterministic, and explicit Korean requests should explain why they are blocked.

The production loader already has the right fail-closed missing-asset shape (`frequency_decks.py:196-212`):

```python
if not path.is_file():
    raise FileNotFoundError(f"missing curated frequency asset: {path}")
...
validate_curated_frequency_entries(entries, language=language, version=version)
validate_frequency_rejection_rows(language, version=version, assets_dir=assets_dir)
```

Do not modify `frequency_decks.py` merely to fabricate Phase 30 data. Its generic token normalization is already NFC (`frequency_decks.py:141-159`), and morphology belongs at grounding/curation boundaries.

---

### `src/multilang/services/provider_text_adapters.py` (provider, request-response)

**Analog:** canonical product codes are translated to human/provider names only at the boundary (`provider_text_adapters.py:38-85`):

```python
_LANGUAGE_NAMES = {
    ...
    "ja": "Japanese",
    "zh": "Mandarin Chinese",
}

_DEEPL_TARGET_LANGUAGES = {
    ...
    "ja": "JA",
    "zh": "ZH-HANS",
}
```

Add the Korean human name for LLM prompts. Korean deck translations target Portuguese, so do not add or use `ko-KR` as an internal target language. Only add a DeepL Korean target code if a Phase 30 test genuinely exercises translation *to* Korean and current provider support is verified; normal Korean deck flow is Korean source -> Portuguese target.

**Prompt grounding pattern** (`provider_text_adapters.py:400-440`):

```python
lines = [
    f"Target language: {target_name} ({request.target_language})",
    f"Card word/lemma: {request.lemma}",
    f"Study form: {request.display_form}",
    f"Lemma: {request.lemma}",
    f"Definition context: {definition}",
]
```

Thread the resolved Korean POS/sense/signature into the typed request and prompt so noun/predicate identities produce different request hashes and prompts. Keep highlight context redacted and bounded. The LLM may generate text from this evidence; it may not author or override the evidence.

---

### `src/multilang/services/audio_voice_registry.py` (config/service, request-response)

**Current fail-closed intent** (`audio_voice_registry.py:154-173`):

```python
def select_voice(language: SupportedLanguage, *, available_voice_ids: set[str] | None = None) -> VoiceSelection:
    plan = _VOICE_REGISTRY[language]
    ...
    raise VoiceSelectionError(
        f"No approved Azure voice available for language {language.value}"
    )
```

Adding `SupportedLanguage.KO` makes the indexing expression raise `KeyError`. Change missing-plan handling to the existing domain error (`VoiceSelectionError`) and explicitly test that Korean has no approved voice in Phase 30. Do **not** add a guessed `ko-KR-*Neural` voice to satisfy the exhaustive registry test. Phase 32 owns live catalog discovery and review.

The provider locale constant still belongs in `domain/korean.py` as `ko-KR`; it is not an approved voice selection by itself.

---

### `src/multilang/services/tatoeba_sentence_source.py` (provider, request-response)

**Analog:** provider codes are boundary-only (`tatoeba_sentence_source.py:48-69`):

```python
_TATOEBA_API_CODES = {
    ...
    "ja": "jpn",
    ...
    "zh": "cmn",
}
```

**Current filtering flow** (`tatoeba_sentence_source.py:198-225`):

```python
try:
    candidates = self._candidate_provider.search_candidates(...)
except Exception:
    return None
...
if not self._matches_target(...):
    continue
```

Phase 30 should make Korean's non-default status explicit rather than relying on a missing-map `KeyError` being swallowed. Preferred bounded change: return no Korean fallback before any network request. If a future phase enables Korean Tatoeba as reviewed reference data, it must inject the Korean morpheme matcher and map `ko` to provider code `kor`; it must not copy Mandarin substring matching (`tatoeba_sentence_source.py:278-286`) or generic suffix matching (`:356-369`).

---

### `src/multilang/domain/lexicon.py` (model, CRUD/transform)

**Analog:** `LexicalCardCandidate` is the shared persisted handoff (`domain/lexicon.py:54-69`):

```python
class LexicalCardCandidate(BaseModel):
    submitted_form: str = Field(min_length=1)
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    lemma_key: str = Field(min_length=1)
    ...
    grounding_status: GroundingStatus
    provenance: LexicalProvenance
```

Add one optional typed `korean_identity` field (the model from `domain/korean.py`) rather than scattering raw Kiwi tokens through provenance notes. A model validator can enforce `lemma`/`lemma_key` consistency whenever that identity is present; because `LexicalCardCandidate` does not itself carry deck language, the Korean grounding/repository boundary must enforce that every Korean `GROUNDED` candidate has the identity. Existing non-Korean candidate constructors should remain valid without changes.

`policy_for_language()` currently sends only English decks to Portuguese (`domain/lexicon.py:72-78`). Add Korean to the Portuguese definition/translation policy now so provider requests and persisted contracts do not first ship with an English identity and later drift in Phase 32.

Use a deterministic Korean `lemma_key` that includes canonical lemma + normalized lexical POS + sense ID. Keep the structured values as the source of truth; the string key is for indexing/dedup/GUID continuity, not a replacement for the model.

---

### `src/multilang/domain/highlights.py` (model, file-I/O/transform)

**Analog:** the existing candidate stores only privacy-safe source identity and lexical surface (`domain/highlights.py:50-66`):

```python
class HighlightCandidate(BaseModel):
    item_key: str = Field(min_length=1)
    source_content_hash: str = Field(min_length=64, max_length=64)
    display_form: str = Field(min_length=1)
    lemma_key: str = Field(min_length=1)
    first_highlight_id: str = Field(min_length=1)
    first_source_index: int = Field(ge=0)
    occurrence_count: int = Field(ge=1)
```

Add optional typed Korean morphology analysis/identity evidence needed to ground the candidate. Do not add raw highlight text, local paths, full analyzer dumps, or neighboring reading context. Preserve `source_content_hash` and first-seen ordering.

---

### `src/multilang/db/models.py`, `src/multilang/repositories/lexical_repository.py`, and the new migration (CRUD)

**ORM analog** (`db/models.py:215-243`):

```python
submitted_form: Mapped[str] = mapped_column(String(255), nullable=False)
normalized_source: Mapped[str] = mapped_column(String(255), nullable=False)
display_form: Mapped[str] = mapped_column(String(255), nullable=False)
lemma: Mapped[str] = mapped_column(String(255), nullable=False)
lemma_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
...
provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
```

**Repository serialization pattern** (`lexical_repository.py:185-235`):

```python
return {
    ...
    "lemma": candidate.lemma,
    "lemma_key": candidate.lemma_key,
    ...
    "provenance": candidate.provenance.model_dump(mode="json"),
}

...
return LexicalCardCandidate(
    ...
    provenance=LexicalProvenance.model_validate(row.provenance),
)
```

Smallest coherent schema: add one nullable JSON `korean_identity` column to `lexical_candidates`; serialize with `model_dump(mode="json")`, restore with `KoreanLexicalIdentity.model_validate(...)`, and leave it `NULL` for all existing rows/languages. Keep `lemma_key` indexed for normal queries/dedup.

**Migration analog** (`20260502_08_spoken_form.py:14-25`):

```python
revision = "20260502_08"
down_revision = "20260426_05"


def upgrade() -> None:
    op.add_column("lexical_candidates", sa.Column("spoken_form", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("lexical_candidates", "spoken_form")
```

Use the current unique head `20260720_15` as `down_revision`. Add the ORM column and migration together; `tests/test_migration_schema_parity.py:41-66` is the mandatory guard.

Do not store analyzer evidence only in `LexicalProvenance.notes`; it must survive typed expire/reload and be usable by text validation without parsing strings.

---

### `src/multilang/services/word_list_parser.py`, `input_fingerprint.py`, and `lexical_lookup.py` (utility/service, transform/file-I/O)

**Current key normalization**:

```python
# word_list_parser.py:36-40
def normalize_word_list_key(value: str) -> str:
    return " ".join(value.split()).casefold()

# input_fingerprint.py:11-15
normalized = {item.strip().lower() for item in requested_item_keys if item and item.strip()}

# lexical_lookup.py:11-14
def normalize_lexical_key(value: str) -> str:
    return " ".join(value.split()).casefold()
```

Apply Unicode NFC before whitespace folding/casefolding at each stable-key boundary. Preserve `ParsedWordListItem.submitted_form` as supplied; use NFC for `display_form`/`item_key` so canonically equivalent Hangul deduplicates and produces the same run key. Add `sense_id` (and only source-backed identity metadata) to `LexicalRecord`; Kiwi cannot invent lexical senses.

Do not use NFKC for Korean content. Do not remove jamo or accents by decomposing to NFD as generic Stanza normalization currently does (`morphology.py:109-112`).

---

### `src/multilang/services/lexical_grounding.py` (service, CRUD/transform)

**Three entry-point pattern** (`lexical_grounding.py:67-177`):

```python
def ground_word_list_item(...):
    record = self._lookup_record(language=language, term=item.item_key)
    if record is None:
        return self._pending_candidate(...)
    ...

def ground_frequency_candidate(...):
    record = self._lookup_record(language=language, term=candidate.lemma_key)
    ...

def ground_highlight_candidate(...):
    record = self._lookup_record(language=language, term=candidate.lemma_key)
    if record is None:
        return LexicalCardCandidate(... grounding_status=GroundingStatus.INSUFFICIENT ...)
```

Inject the Korean morphology service and route all three Korean entry points through it before lexical lookup/persistence:

1. NFC-normalize and analyze the submitted/surface value.
2. Reject unavailable, ambiguous, OOV, or structurally invalid analysis with a safe `PENDING`/`INSUFFICIENT` candidate and explicit warning code.
3. Look up the resolved lemma, not the attached surface eojeol.
4. Bind source-backed `sense_id`; verify source POS is compatible with analyzer POS.
5. Persist `KoreanLexicalIdentity` on the grounded candidate.

For Korean, do not use `_ground_frequency_seed_candidate()` as proof of lexical grounding, do not infer POS from a generic function-word table, and do not mark provider-generated IPA authoritative. Existing languages keep their current fallback behavior.

The `_grounded_candidate()` pattern at `lexical_grounding.py:215-320` already centralizes definition/pronunciation construction. Thread Korean identity through this one constructor rather than patching three return objects independently.

---

### `src/multilang/services/highlight_candidate_extraction.py` (service, file-I/O/transform)

**Generic flow to retain for non-Korean languages** (`highlight_candidate_extraction.py:49-129`):

```python
stopwords = _STOPWORDS[language]
...
for match in _TOKEN_RE.finditer(text_for_tokens):
    display_form = _trim_internal_token(match.group(0))
    lemma_key = _lemma_key(display_form)
    if not _is_usable_token(...):
        rejected_token_count += 1
        continue
    duplicate_count += _record_candidate(...)
```

**Why Korean must branch before this code** (`highlight_candidate_extraction.py:144-165`):

```python
def _lemma_key(token: str) -> str:
    normalized = unicodedata.normalize("NFKC", token)
    return " ".join(normalized.casefold().split())

def _is_usable_token(...):
    if len(lemma_key) <= 1:
        return False
```

That path both uses forbidden compatibility normalization and drops valid one-syllable Korean words such as `물`, `집`, and `말`. It also treats an eojeol with attached particle/ending as a lexical lemma.

Add a Korean branch that analyzes the bounded highlight text with Kiwi, emits only resolved lexical identities, preserves valid one-syllable lexemes, keeps derivational compound predicates together, and deduplicates by lemma/POS/sense identity. Analyzer unavailable or ambiguous must block Korean extraction with a privacy-safe error; adding `_STOPWORDS[SupportedLanguage.KO]` alone is not an implementation.

**Privacy-safe candidate identity pattern** (`highlight_candidate_extraction.py:200-226`):

```python
lemma_hash = sha256(lemma_key.encode("utf-8")).hexdigest()[:16]
source_hash = highlight.provenance.content_hash[:16]
candidates_by_key[candidate_key] = HighlightCandidate(
    item_key=f"highlight-{language.value}-{source_hash}-{lemma_hash}",
    source_content_hash=highlight.provenance.content_hash,
    ...
)
```

Retain hash-only/source-index provenance. If the Korean identity key is hashed, include POS/sense in the canonical payload before hashing so homographs do not collide.

---

### `src/multilang/services/highlight_import_preview.py` and `ingest_lexical_items.py` (service, batch/file-I/O)

**Preview composition** (`highlight_import_preview.py:24-39`):

```python
parse_result = parse_kindle_highlight_export(path)
...
extraction_result = extract_highlight_candidates(parse_result.highlights, language=language)
...
return HighlightImportPreview(...)
```

Accept/inject the same morphology service used by actual ingestion. Korean preview must not report whitespace-token counts that actual ingestion later rejects. If no analyzer can be constructed, preview fails closed without including private text/path in the error.

**Mode dispatch and highlight wiring** (`ingest_lexical_items.py:67-95`):

```python
if request.source_type == "frequency":
    return self._ingest_frequency_deck(...)
if request.source_type == "word-list":
    return self._ingest_word_list(...)
if request.source_type == "kindle-highlights":
    return self._ingest_highlights(...)
...
parsed = parse_kindle_highlight_export(request.input_file)
extraction = extract_highlight_candidates(parsed.highlights, language=request.language)
```

Inject one Korean morphology service and pass it to extraction/grounding. Do not instantiate Kiwi once per card. The existing grounding calls at `ingest_lexical_items.py:141-169,305-319,374-399` are the three points where the shared identity must survive into `LexicalRepository`.

Keep existing private-record persistence separate from safe lexical candidates. `GenerateTextItemsService._build_highlight_context()` already retrieves private context only when needed, redacts it, and bounds it (`generate_text_items.py:494-544`); do not move raw context into morphology evidence or provider telemetry.

---

### `src/multilang/services/text_generation.py` (service/model, request-response)

**Typed request construction** (`text_generation.py:20-48`):

```python
class SentenceGenerationRequest(BaseModel):
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions_html: str | None = None
    target_language: str = Field(min_length=2)
    translation_target_language: str = Field(min_length=2)
    source_type: str | None = None
    highlight_context: str | None = None

    @classmethod
    def from_candidate(...):
        ...
```

Thread the optional typed Korean identity into sentence/definition requests. This is not only prompt context: `_cache_key_for_request()` hashes `request.model_dump(mode="json")` (`text_generation.py:405-418`), so POS/sense/signature must participate to prevent a provider cache hit for a different homograph.

Normalize Korean sentence/translation/definition output to NFC at the typed adapter-result boundary before cache, validation, DB persistence, audio hashing, or export. Do not normalize all text with NFKC.

---

### `src/multilang/services/generate_text_items.py` (service, batch/request-response)

**Validation handoff** (`generate_text_items.py:300-325`):

```python
validation = self.text_validation_service.validate(
    sentence=bundle.sentence,
    translation=bundle.translation,
    display_form=candidate.display_form,
    lemma=candidate.lemma,
    definitions_html=candidate.definitions_html,
    ...
)
```

Pass `candidate.korean_identity` to validation. Restore the same typed field in `_to_candidate()` (`generate_text_items.py:465-484`) so DB-loaded candidates do not lose morphology evidence.

**Repair chain** (`generate_text_items.py:371-449`): retry generation once, then optional Tatoeba, then persist review-required if still invalid. Preserve that shape, but Korean must never become accepted after an unavailable/ambiguous morphology result. Skip Korean Tatoeba fallback explicitly in this phase; generated retries still pass through the same morphology gate.

---

### `src/multilang/services/text_validation.py` (service, transform)

**Existing dependency injection** (`text_validation.py:177-205`):

```python
def __init__(
    self,
    *,
    language_identifier: LanguageIdentifier | None = None,
    morphological_analyzer: MorphologicalAnalyzer | None = None,
) -> None:
    self.language_identifier = language_identifier or CorpusLanguageIdentifier()
    self.morphological_analyzer = morphological_analyzer or OptionalStanzaMorphologicalAnalyzer()
```

Add a separate Korean matcher dependency; do not overload `OptionalStanzaMorphologicalAnalyzer` with Kiwi-specific analysis/extraction APIs.

**Insertion point** (`text_validation.py:268-319`):

```python
if context.target_language == "ja" and _japanese_contains_target(...):
    return
if context.target_language == "zh" and _mandarin_contains_target(...):
    return

candidates = _match_keys(display_form) | _match_keys(lemma)
...
morphology_result = self.morphological_analyzer.contains_target_lemma(...)
...
if heuristic_match:
    return
```

Add Korean **before** Japanese/Mandarin substring and generic `_match_keys` logic:

- require a persisted `KoreanLexicalIdentity`;
- call the Korean matcher with the entire sentence and target signature;
- accept only an unambiguous matched result;
- emit `MORPHOLOGY_MISMATCH` for mismatch, unavailable, ambiguous, or missing identity;
- never evaluate `heuristic_match` for `ko`.

Use Korean NFC/script validation in `detect_language_mismatch()` before corpus heuristics, analogous to the Mandarin early branch at `text_validation.py:560-573`, but with NFC and Korean script policy rather than Mandarin NFKC/Simplified policy.

The existing `MORPHOLOGY_MISMATCH` flag (`domain/text_quality.py:31-40`) is sufficient; avoid introducing several user-visible flag codes unless downstream review/reporting needs to distinguish them. Put the safe reason in `detail`.

---

### `src/multilang/runtime.py` (provider/composition root, request-response)

**Language name registry** (`runtime.py:79-102`):

```python
_LANGUAGE_NAMES = {
    ...
    SupportedLanguage.JA: "Japanese",
    SupportedLanguage.ZH: "Mandarin Chinese",
}
```

Add `SupportedLanguage.KO: "Korean"`. `_default_deck_name()` already derives from this map (`runtime.py:638-640`).

**Composition pattern** (`runtime.py:570-605,584-595`):

```python
text_validation_service = TextValidationService()
...
return RuntimeGenerateService(
    ...
    grounding_service=LexicalGroundingService(
        lookup=LexicalLookup(...),
        ...
    ),
    ...
    generate_text_items_service=GenerateTextItemsService(
        ...
        text_validation_service=text_validation_service,
        ...
    ),
)
```

Construct one lazy `KiwiKoreanMorphologyService` and inject that same instance into lexical grounding, highlight ingestion/preview where composed, and text validation. This prevents analyzer/version drift and repeated model initialization. Existing non-Korean runtime construction must still succeed if Kiwi reports unavailable; only Korean operations fail closed.

Do not add Korean-specific note type routing to `_note_type_name_for_rows()` in Phase 30. Its generic source profile fallback is the intended temporary path.

## Export And Snapshot Surfaces To Verify, Not Modify

These files are high-leverage regression surfaces, but the smallest Phase 30 implementation should not modify them unless a focused Korean contract test proves the generic fallback is insufficient.

### Generic field routing

`domain/exporting.py:237-252` already falls back by source type:

```python
if language_value == SupportedLanguage.LA.value:
    return LATIN_EXPORT_CARD_FIELD_NAMES
if language_value == SupportedLanguage.ZH.value and normalized_source_type in {"frequency", "word-list"}:
    return MANDARIN_EXPORT_CARD_FIELD_NAMES
if language_value == SupportedLanguage.JA.value and normalized_source_type == "frequency":
    return JAPANESE_EXPORT_CARD_FIELD_NAMES
return export_field_names_for_source_type(normalized_source_type)
```

Therefore `ko` should use:

- normal frequency fields for `frequency`;
- existing manual/highlight-style fields for `word-list`;
- existing highlight fields for `kindle-highlights`.

### Persisted language identity

`export_repository.py:142-168` reconstructs export identity from the job:

```python
identity=ExportCardIdentity(
    language=SupportedLanguage(row.job.language),
    source_type=row.job.source_type,
    ...
)
```

Once the job stores `ko`, export snapshot reload naturally restores `SupportedLanguage.KO`.

### Anki traceability tags

`export_anki_package.py:153-166` already uses the canonical enum value:

```python
tags = [
    "multilang",
    row.identity.language.value,
    row.identity.source_type.replace("-", "_"),
    ...
]
```

A focused test should prove the tag is exactly `ko` and never `ko-KR`.

### What to freeze

Phase 30 morphology is internal identity evidence. Persist it on `lexical_candidates`; keep canonical rendered word/sentence plus morphology-aware `lemma_key` in normal card snapshots. Do not add Korean-only card-export columns for data that is not learner-visible.

If a later phase adds learner-visible derived Korean fields, copy Mandarin's “derive once, persist, expire/reload, never recompute during export” pattern (`assemble_export_cards.py:107-146`; `export_repository.py:118-168`; `test_export_repository.py:172-210`). Do **not** copy Japanese's current derived-only path.

## Japanese Baseline Findings

### Historical Windows Fugashi failure: currently not reproducible

Mandarin verification recorded a Windows Fugashi `-d` dictionary-path failure (`027-VERIFICATION.md:168`) and excluded affected Japanese tests. On the current Windows/Python 3.13.7 worktree, the exact focused baseline is green:

```text
uv run pytest tests/services/test_japanese_furigana.py \
  tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa -q
7 passed in 0.33s
```

Do not carry the stale exclusion into Phase 30. Run the tests normally. If it recurs on another supported environment, report it separately with the actual Fugashi/UniDic path; do not weaken Korean or Japanese assertions.

### Confirmed current Japanese snapshot gap

`AssembleExportCardsService` derives `word_reading` and `sentence_furigana` (`assemble_export_cards.py:102-106,221-233`), but `CardExportModel`, `ExportRepository._card_payload()`, and `_to_card_domain()` do not persist those two fields. A live in-memory expire/reload check on 2026-08-03 returned:

```text
(stored.word_reading, stored.sentence_furigana,
 reloaded.word_reading, reloaded.sentence_furigana)
== (None, None, None, None)
```

This is pre-existing and outside the smallest Phase 30 touch set because Korean morphology belongs on lexical candidates and no Korean export fields are being added. Do not claim Japanese snapshot round-trip as Phase 30 evidence. If execution finds it must change `card_exports`/`ExportRepository`, stop and either isolate this Japanese repair as a prerequisite or include explicit migration/regression ownership; do not accidentally preserve or worsen the loss while copying patterns.

## Test Pattern Assignments

### `tests/domain/test_korean.py`

**Analog:** `tests/domain/test_latin_contracts.py:18-53` uses direct defaults plus parametrized validation failures.

Cover:

- canonical code is `ko`; provider locale is `ko-KR`;
- NFD learner text produces the expected NFC canonical value while submitted form is preserved;
- compatibility/halfwidth Hangul is rejected rather than NFKC-folded;
- resolved identity requires lemma, canonical POS, sense ID, non-empty morpheme signature, analyzer/version;
- unresolved/ambiguous/unavailable analysis cannot construct a resolved identity;
- deterministic identity key differs by POS and sense.

### `tests/services/test_korean_morphology.py`

**Analog:** `tests/services/test_mandarin_orthography.py:18-73` runs real deterministic derivations and parametrizes bad inputs. Also copy the fail-closed cases from `tests/services/test_latin_source_pack.py:107-144`.

Required golden categories:

| Category | Required assertion |
|---|---|
| noun + particle | `학교` identity matches `학교에서 ...`; particle is not part of lexical identity |
| regular predicate | `먹다` matches `먹었어요` through `먹/VV`, not suffix stripping |
| irregular predicate | one reviewed Kiwi-stable irregular fixture matches its dictionary lemma |
| adjective/predicate | `예쁘다` matches `예뻐요` with predicate POS |
| compound predicate | `공부하다` preserves `공부/NNG + 하/XSV` in one eojeol |
| homograph | reviewed noun and predicate identities with the same visible form do not cross-match |
| NFC/NFD | canonically equivalent Hangul yields the same signature/identity |
| unavailable | import/model failure returns unavailable and matching rejects |
| ambiguous/OOV | unresolved analysis rejects rather than picking the first tokenization |
| negative boundary | substring-only and unrelated suffix lookalikes do not match |

Use the real pinned Kiwi adapter for the linguistic goldens. Use an injected fake/importer only for unavailable/exception branches. Do not mock every positive case; that would test the fake, not KNLP-01.

### `tests/services/test_korean_language_support.py`

**Analog:** `tests/services/test_mandarin_language_support.py:51-310` centralizes registry/provider contracts with offline fakes.

Cover:

- `GenerationRequest` accepts `ko` for frequency, word-list, and highlights and rejects `ko-KR`;
- settings expose `ko` once;
- runtime/provider prompts say `Korean (ko)` and carry POS/sense evidence;
- internal request/cache/job/export/tag values remain `ko`;
- provider locale constant is `ko-KR`;
- no approved Azure Korean voice exists yet and selection raises `VoiceSelectionError` rather than `KeyError`;
- no Google/ElevenLabs Korean production fallback is registered;
- no default Korean Tatoeba network call occurs;
- no Korean frequency asset is built/required by build-all; explicit build is license-blocked;
- Korean definition/translation policy targets Portuguese.

### `tests/integration/test_korean_modern_flow.py`

**Analog:** `tests/integration/test_mandarin_modern_flow.py:146-195,244-333` builds a disposable SQLite runtime, uses local fakes, expires sessions, and inspects persistence/export artifacts.

Keep the Korean integration offline and smaller than Mandarin's final export proof:

1. Construct one shared fake/real-wrapper Korean morphology service and assert all three modes call it.
2. Frequency test-mode: use temporary/fake candidates only; do not create `assets/frequency/ko`.
3. Word list: submit an inflected/NFD form, preserve submitted form/order, persist NFC resolved identity.
4. Highlights: extract a valid one-syllable lexeme and an attached-particle form; preserve only hash/index provenance.
5. Commit, `session.expire_all()`, reload `LexicalCandidate`, and assert the complete Korean identity/analyzer version survives.
6. Build representative generic export rows/snapshots for all three source types and assert source field schemas remain unchanged, canonical language reloads as `ko`, Image stays blank, and Anki tags include `ko`.
7. Do not synthesize/approve Korean audio or claim final Korean APKG/template readiness.

### Existing exhaustive tests to update

- `tests/domain/test_jobs.py:16-40`: append exactly `ko`; add direct rejection for `ko-KR`.
- `tests/test_settings.py:8-32`: append `ko` once in expected order.
- `tests/services/test_audio_voice_registry.py:17-29`: stop asserting every enum has an approved voice; assert approved registry languages resolve and Korean fails with `VoiceSelectionError` until Phase 32.
- `tests/services/test_frequency_decks.py:363-374`: iterate the approved asset-capability list, not every selectable language; add explicit Korean license/missing-asset gate coverage.
- `tests/repositories/test_lexical_repository.py`: copy the upsert/expire/reload shape and assert typed identity equality, NFC values, POS/sense/signature, analyzer version, and `NULL` for non-Korean candidates.
- `tests/test_migration_schema_parity.py:53-66`: parity already catches the new column; add a named assertion for discoverability.
- `tests/services/test_text_validation.py:31-43,467-499`: add an injected Korean matcher fake, positive inflection, POS-homograph negative, and unavailable/ambiguous fail-closed cases. Keep existing generic analyzer/heuristic cases unchanged.
- `tests/services/test_highlight_candidate_extraction.py`: add one-syllable, particle/ending, compound, order, NFD/NFC, privacy, unavailable, and homograph cases; keep all existing language parametrization green.
- `tests/services/test_generate_text_items.py`: assert Korean failed validation retries but never calls default Tatoeba, and persisted review status remains review-required when morphology is unavailable.
- `tests/test_runtime.py`: monkeypatch the Korean analyzer constructor and prove one instance is shared by grounding and validation without importing/initializing Kiwi per item.

## Shared Patterns

### Canonical Code At Rest, Provider Values At Edges

**Sources:** `job_repository.py:27-57`, `export_repository.py:142-168`, `export_anki_package.py:153-166`

```python
language=request.language.value
...
language=SupportedLanguage(row.job.language)
...
row.identity.language.value
```

Apply to jobs, run keys, DB rows, lexical index paths, export identity, tags, and source-mode routing. `ko-KR` must never be accepted as `SupportedLanguage`, persisted job language, item key prefix, tag, or cache language.

### Fail Closed Without Breaking Other Languages

**Sources:** `morphology.py:47-64`, `text_validation.py:296-319`, `audio_voice_registry.py:171-173`

- Convert analyzer/import/runtime exceptions into typed unavailable evidence with exception class only, not raw learner text.
- Korean callers reject unavailable/ambiguous evidence.
- Non-Korean callers retain the existing Stanza/heuristic behavior.
- Missing Korean voice fails with `VoiceSelectionError`.
- Missing Korean asset fails with a license/missing-asset message.

### Persist Before Reuse

**Sources:** `lexical_repository.py:185-235`; Mandarin snapshot precedent at `export_repository.py:118-168`

- Persist structured Korean identity before text generation.
- Reload the identity from DB for generation/validation; do not re-run Kiwi opportunistically after resume.
- If analyzer version changes, require explicit reanalysis/review rather than silently mixing signatures.
- Do not parse identity back out of prose definitions or provenance notes.

### Privacy For Highlights

**Sources:** `highlight_candidate_extraction.py:200-226`, `generate_text_items.py:494-544`, `security/redaction.py:24-45`

```python
redacted = redact_sensitive_text(normalized_text)
return _bounded_context_snippet(
    redacted,
    display_form=candidate.display_form,
    lemma=candidate.lemma,
)
```

Morphology can process local highlight text in-process, but persisted safe candidates/provider telemetry must contain only canonical lexical evidence plus existing hashes/indexes. Do not include private paths, full excerpts, raw token dumps, prompts, or tracebacks in errors.

### Testing With Fakes At Boundaries, Real Libraries For Goldens

- Use real Kiwi for deterministic linguistic goldens.
- Use fakes for provider/network/audio, unavailable-import behavior, and orchestration call counts.
- Use real SQLite ORM commit/expire/reload for persistence.
- Use direct APKG/note construction only to prove existing generic schema/tag behavior; do not claim final Korean export readiness.

## Regression Matrix

### Phase 30 Focused Gates

```text
uv run pytest tests/domain/test_korean.py \
  tests/services/test_korean_morphology.py \
  tests/services/test_korean_language_support.py -q

uv run pytest tests/repositories/test_lexical_repository.py \
  tests/test_migration_schema_parity.py \
  tests/services/test_text_validation.py \
  tests/services/test_highlight_candidate_extraction.py -q

uv run pytest tests/integration/test_korean_modern_flow.py -q

uv lock --check
uv run python -c "import kiwipiepy; print(kiwipiepy.__version__)"
```

### Existing-Mode Anti-Regression Gates

```text
# Frequency, custom list, and highlight paths
uv run pytest tests/integration/test_frequency_e2e_export_flow.py \
  tests/integration/test_custom_word_list_e2e_export_flow.py \
  tests/integration/test_highlight_generation_audio_flow.py \
  tests/integration/test_v13_existing_modes_regression_evidence.py -q

# Japanese and Mandarin
uv run pytest tests/services/test_japanese_furigana.py \
  tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa \
  tests/integration/test_mandarin_modern_flow.py -q

# Latin and phoneme families
uv run pytest tests/integration/test_v21_latin_google_tts_final_audio.py \
  tests/services/test_russian_phoneme_deck.py -q
```

Current pre-change evidence for the Japanese/Mandarin/Latin/phoneme subset above: **32 passed in 5.98s** on Windows/Python 3.13.7.

### Canonical Identity Scan

After implementation, scan changed source/tests and require every `ko-KR` occurrence to be an explicit provider-locale contract. There should be no `SupportedLanguage("ko-KR")`, DB job language, run key, export tag, lexical index directory, or frequency asset language using the locale.

## No Analog Found

No proposed file lacks a structural in-repo analog. The following internal algorithm/sense-resolution surfaces have no exact implementation to copy:

| Surface | Why no exact analog exists | Planner instruction |
|---|---|---|
| Kiwi token/POS interpretation | Current morphology is optional Stanza lemma matching; Japanese only formats readings; Mandarin only validates/derives orthography. | Verify pinned Kiwi APIs/tags from current docs/runtime before writing action details. |
| Korean irregular lemma reconstruction | No current service reconstructs Korean predicates. | Rely on Kiwi's analyzed lexical forms and reviewed goldens; never hand-roll suffix tables. |
| Compound predicate identity | No current matcher preserves Korean `NNG + XSV/XSA` inside one eojeol. | Make boundary/signature behavior explicit in the domain result and golden tests. |
| Lexical sense assignment | Kiwi supplies morphology, not approved dictionary senses; current `LexicalRecord` has no sense ID. | Extend source-backed lexical records; unresolved senses stay pending/review-required. Do not hash an LLM gloss and call it a sense. |

## Planner Guardrails

1. Keep one shared analyzer instance and one typed Korean identity contract.
2. Put Korean special handling before generic token/substr/suffix paths; do not alter generic behavior for existing languages.
3. Make all three source modes produce the same persisted identity shape.
4. Treat the frequency route as capability + explicit license gate, not permission to commit an asset.
5. Treat `ko-KR` as locale metadata only; do not satisfy Phase 30 by guessing a voice.
6. Keep export/template source files no-touch unless a focused test proves generic fallback is insufficient.
7. Do not use the stale Windows Fugashi exclusion; current focused Japanese tests pass.
8. Do not broaden Phase 30 to repair the separate Japanese snapshot gap without explicit prerequisite ownership.
9. Run migration parity whenever ORM persistence changes.
10. Never include raw highlight text/path or raw analyzer dumps in persisted public evidence/errors.

## Metadata

**Analog search scope:** `src/multilang/domain`, `src/multilang/services`, `src/multilang/repositories`, `src/multilang/db`, `alembic/versions`, `scripts`, `tests/domain`, `tests/services`, `tests/repositories`, `tests/integration`, Japanese/Mandarin quick-task artifacts, Phase 29 summary/verification.
**Inventory scanned:** 100+ Python/planning files; 70+ targeted files directly read.
**Primary precedents:** committed Mandarin integration (`dc63333`), Japanese quick tasks 022-026/028, shared modern ingestion/validation/export, Latin fail-closed morphology contracts.
**Pattern extraction date:** 2026-08-03.
**Known live baseline:** pre-write worktree was clean; only this Phase 30 pattern artifact was added; `uv lock --check` passed; Python 3.13.7; focused existing-mode subset 32/32 passed.
