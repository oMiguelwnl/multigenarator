# Phase 31: Hangul and Pronunciation i+1 - Pattern Map

**Mapped:** 2026-08-04
**Requirements:** KHAN-01, KHAN-02, KPRO-01, KPRO-02
**Files classified:** 27 inferred new/modified artifacts (17 production/data/review, 10 tests)
**Structural analogs found:** 27 / 27
**Exact Korean curriculum/audio analogs:** 0 / 4

## Inputs And Scope Truth

- No Phase 31 `CONTEXT.md`, `APPROACH.md`, or `RESEARCH.md` exists. The file set below is inferred from `.planning/SPEC.md:45-53`, `.planning/ROADMAP.md:61-71`, `KOREAN-STRUCTURE.md:17-175,370-481`, the verified Phase 30 handoff, and the live codebase.
- Planning lifecycle preflight returned `allowed`. The control map reports Phase 31 as next and warns that the canonical `Monarch` worktree contains the completed-but-uncommitted Phase 30 set. Treat that dirty set as the required Phase 30 baseline; do not overwrite or revert it.
- The earlier Phase 31 slug mismatch has been reconciled. The canonical slug is now `i-plus-1`, and this map and all future Phase 31 planning artifacts belong under `.planning/phases/31-hangul-and-pronunciation-i-plus-1/`.
- Focused analog baseline passed on the live worktree:

  ```text
  UV_OFFLINE=1 uv run --extra dev pytest \
    tests/services/test_japanese_kana_deck.py \
    tests/services/test_japanese_kana_generated_deck.py \
    tests/services/test_russian_phoneme_deck.py \
    tests/services/test_card_template_loader.py \
    tests/services/test_export_anki_package.py \
    tests/services/test_export_tabular_bundle.py \
    tests/services/test_latin_audio.py \
    tests/services/test_latin_review.py \
    tests/services/test_latin_export.py -q
  # 123 passed in 4.28s
  ```

### Locked Outcomes

| Requirement | Concrete implication |
|---|---|
| KHAN-01 | A curated Hangul inventory gets a Korean-only note type, unique model/deck IDs, Korean labels/fonts, jamo/block/stroke/mnemonic fields, and complete approved media. The rendered model must contain no Japanese field, label, class, or font leakage. |
| KHAN-02 | Bootstrap is explicit. Every strict card persists target, prerequisite, observed, and unknown concept IDs; after bootstrap, `unknown_concept_ids == (target_concept_id,)`, prerequisites precede the card, and Korean text remains NFC-safe. |
| KPRO-01 | The Korean pronunciation note type uses exactly the existing nine phoneme study fields and the shared HTML/CSS layout, but receives Korean-specific identity/IDs and approved media that remain resolvable in APKG, CSV, and TSV bundles. |
| KPRO-02 | The source inventory covers P0-P13 in dependency order and rejects a card if any active non-target phonological concept is not already a prerequisite/known concept. Approval cannot override invalid i+1 evidence. |

### Contract Reconciliation Required In Code

1. `KOREAN-STRUCTURE.md:80-95` lists the visible Hangul pedagogical fields but omits `ObservedConceptIds`, `UnknownConceptIds`, and `IPlusOnePolicy`; the normative contracts in `.planning/SPEC.md:97-103` and KHAN-02 require that evidence to be stored. Keep the extra evidence as non-rendered note/source fields rather than dropping it.
2. `KOREAN-STRUCTURE.md:117-131` requires the pronunciation learner fields to remain exactly the existing nine-field contract. Keep curriculum and pronunciation evidence in the validated source record/manifest, not as extra study fields.
3. Phase 30 deliberately rejects Compatibility Jamo and halfwidth Hangul at lexical/canonical boundaries (`domain/korean.py:109-120`), while the approved foundation sequence illustrates standalone jamo with compatibility display glyphs. Do not weaken `canonicalize_korean()`. Add a separate, explicit pedagogical-glyph contract that records a reviewed display glyph and its canonical conjoining-jamo identity; never let that display representation enter lexical keys, morphology, or generic Korean canonicalization silently.

## Recommended Ownership Boundary

Use a dedicated, frozen foundation path like Latin, not the modern frequency/job runtime:

```text
domain/korean.py
  -> immutable concept/curriculum/pronunciation contracts
korean_curriculum.py
  -> load concept + Hangul + pronunciation manifests; validate graph/coverage/NFC
korean_foundation_review.py
  -> independent content/curriculum/media approval gates
korean_foundation_media.py
  -> exact-text/hash/path/reviewer-role readiness for pictures, strokes, GIFs, audio
phoneme_deck.py
  -> language-neutral nine-field model/note/template mechanics only
korean_foundation_export.py
  -> join frozen approved inputs; APKG/CSV/TSV + resolvable media bundles
cli.py
  -> thin local commands and controlled exit handling
```

This avoids threading foundation-only fields through `ExportCardRow`, `RuntimeGenerateService`, the database schema, or the production Korean voice registry. It also prevents the unsafe “generate TTS while exporting and silently omit failures” behavior in the legacy kana/phoneme exporters from becoming Korean policy.

## File Classification

### Production, Data, And Review Artifacts

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/multilang/domain/korean.py` | model | transform | existing frozen Korean contracts at `domain/korean.py:99-120,335-427`; `latin_source_pack.py:152-184` | exact role / partial behavior |
| `src/multilang/services/korean_curriculum.py` **(create)** | service/model | file-I/O, batch, transform | `latin_source_pack.py:219-313` | role-match |
| `src/multilang/services/korean_foundation_review.py` **(create)** | service/model | file-I/O, event-driven | `latin_review.py:56-70,120-210` | exact role |
| `src/multilang/services/korean_foundation_media.py` **(create)** | service/model | file-I/O, transform | `latin_audio.py:59-147,164-254`; `japanese_kana_deck.py:92-97` | role-match |
| `src/multilang/services/phoneme_deck.py` **(create)** | service/utility | transform | generic portions of `russian_phoneme_deck.py:35-71,178-249,465-486` | exact extraction |
| `src/multilang/services/russian_phoneme_deck.py` | service | batch, file-I/O | its current public API and inventories | exact regression-preserving refactor |
| `src/multilang/services/korean_foundation_export.py` **(create)** | service | file-I/O, batch, transform | `latin_export.py:43-90,130-333`; kana model at `japanese_kana_deck.py:345-416` | role-match |
| `src/multilang/templates/korean_hangul_card.md` **(create)** | config/template | transform | `templates/japanese_kana_card.md:23-223` | layout-match |
| `src/multilang/cli.py` | controller/route | request-response, file-I/O | dedicated Latin export command at `cli.py:1102-1138` | exact |
| `data/korean_foundations/korean-concepts-v1.json` **(create)** | model/config | file-I/O, batch | frozen source manifest in `data/latin_mvp/latin-mvp-50-v1.json` | role-match |
| `data/korean_foundations/hangul-v1.json` **(create)** | model/config | file-I/O, batch | `japanese_kana_generated_deck.py:34-170`; Latin source pack JSON | partial |
| `data/korean_foundations/pronunciation-i-plus-1-v1.json` **(create)** | model/config | file-I/O, batch | phoneme card tuples at `russian_phoneme_deck.py:74-175`; Latin source pack JSON | partial |
| `data/korean_foundations/korean-foundations-v1-curation.json` **(create)** | model/config | file-I/O, event-driven | `data/latin_mvp/latin-mvp-50-v1-curation.json:1-41` | exact role |
| `data/korean_foundations/korean-foundations-v1-media.json` **(create)** | model/config | file-I/O, batch | `data/latin_mvp/latin-mvp-50-v1-audio.json:1-29` | role-match |
| `data/korean_foundations/media/korean-foundations-v1/*` **(create set)** | asset | file-I/O | `data/latin_mvp/audio/latin-mvp-50-v1/*` | exact layout |
| `$PHASE_DIR/31-CURRICULUM-REVIEW.md` **(create)** | config/review evidence | event-driven | Phase 27 playback review artifact; Latin curation reviewer metadata | role-match |
| `$PHASE_DIR/31-AUDIO-PLAYBACK-REVIEW.md` **(create)** | config/review evidence | event-driven | `.planning/phases/27-latin-audio-policy-and-integrity/27-AUDIO-PLAYBACK-REVIEW.md:1-81` | exact role |

### Tests

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/domain/test_korean.py` | test | transform | current Korean frozen/NFC tests at `test_korean.py:61-102,127-238` | exact |
| `tests/services/test_korean_curriculum.py` **(create)** | test | file-I/O, batch, transform | `tests/services/test_latin_source_pack.py`; generated kana coverage tests | role-match |
| `tests/services/test_korean_foundation_review.py` **(create)** | test | event-driven, transform | `tests/services/test_latin_review.py:48-119` | exact |
| `tests/services/test_korean_foundation_media.py` **(create)** | test | file-I/O, transform | `tests/services/test_latin_audio.py:130-360` | exact role |
| `tests/services/test_phoneme_deck.py` **(create)** | test | transform | shared-model assertions in `test_russian_phoneme_deck.py:118-263` | exact extraction |
| `tests/services/test_russian_phoneme_deck.py` | test | batch, file-I/O | current file | exact regression |
| `tests/services/test_korean_foundation_export.py` **(create)** | test | file-I/O, batch | `tests/services/test_latin_export.py:27-299`; kana APKG tests | exact role |
| `tests/services/test_card_template_loader.py` | test | transform | kana/phoneme template assertions at `test_card_template_loader.py:535-563,737-775` | exact |
| `tests/cli/test_korean_foundation_commands.py` **(create)** | test | request-response, file-I/O | phoneme CLI tests at `test_generate_command.py:865-894`; Latin command shape | role-match |
| `tests/integration/test_korean_foundations_flow.py` **(create)** | test | file-I/O, batch | `test_v20_latin_export_evidence.py`; `test_russian_phoneme_template_refresh_flow.py` | role-match |

## Pattern Assignments

### `src/multilang/domain/korean.py` (model, transform)

**Primary analog:** the existing module itself. Extend it rather than creating a second source of Korean canonical constants.

**Frozen, strict model pattern** (`domain/korean.py:99-106`):

```python
class _FrozenContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )
```

Use this base for the SPEC contracts:

- `KoreanConcept` with `id`, domain, prerequisite IDs, and sequence;
- `KoreanCurriculumEvidence` with target, observed, prerequisite, unknown, and policy;
- `KoreanPronunciationEvidence` with canonical spelling, normative/surface pronunciation, IPA, rule IDs, and review status;
- a separate pedagogical jamo/display model that explicitly distinguishes compatibility display glyph from canonical conjoining-jamo identity.

**Canonical Korean pattern** (`domain/korean.py:109-120`):

```python
def canonicalize_korean(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KoreanTextError("Korean text must not be blank")
    if any(
        ord(character) in _HANGUL_COMPATIBILITY_JAMO
        or ord(character) in _HALFWIDTH_HANGUL
        for character in value
    ):
        raise KoreanTextError("Korean text contains forbidden compatibility Hangul")
    return unicodedata.normalize("NFC", value)
```

Copy this for syllable blocks, Korean names, words, and sentences. **Do not call it on an explicitly modeled compatibility display glyph and do not relax its rejection ranges.** Halfwidth Hangul stays forbidden everywhere.

**Cross-field invariant pattern** (`latin_source_pack.py:173-184`):

```python
@model_validator(mode="after")
def enforce_resolved_morphology(self) -> "LatinMorphologyEvidence":
    if self.grammar_review_status != "approved":
        raise ValueError("grammar_review_status must be approved")
    ...
    return self
```

For strict curriculum evidence, enforce at construction time:

```text
policy == strict
target_concept_id in observed_concept_ids
set(prerequisite_concept_ids) <= set(observed_concept_ids)
unknown_concept_ids == (target_concept_id,)
```

Do not accept caller-supplied `unknown_concept_ids` as truth without recomputing it against the pack's explicit bootstrap and preceding concepts.

---

### `src/multilang/services/korean_curriculum.py` and the three source manifests

**Primary analog:** `src/multilang/services/latin_source_pack.py`.

**Typed entry + pack invariant pattern** (`latin_source_pack.py:219-297`):

```python
class LatinMvpSourcePackEntry(...):
    item_key: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    ...

    @model_validator(mode="after")
    def validate_entry_contract(self) -> "LatinMvpSourcePackEntry":
        expected_key = f"latin-mvp-{self.sequence:04d}"
        if self.item_key != expected_key:
            raise ValueError(...)
        ...
        return self


class LatinMvpSourcePack(BaseModel):
    ...

    @model_validator(mode="after")
    def validate_pack_invariants(self) -> "LatinMvpSourcePack":
        ...
        if actual_sequences != list(range(1, LATIN_MVP_CARD_COUNT + 1)):
            raise ValueError("entries must have sequence numbers 1 through 50")
        ...
        return self
```

Use stable item keys such as `ko-hangul-0001` and `ko-pron-0001`, contiguous sequence numbers, explicit source-pack versions, and deterministic order. The concept catalog should be the single registry referenced by both inventories.

**Loader/error pattern** (`latin_source_pack.py:300-314`):

```python
def load_latin_mvp_source_pack(path: Path | None = None) -> LatinMvpSourcePack:
    manifest_path = path or DEFAULT_LATIN_MVP_SOURCE_PACK_PATH
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return LatinMvpSourcePack.model_validate(payload)
    except FileNotFoundError as exc:
        raise ValueError("Latin MVP source pack is missing ...") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Latin MVP source pack JSON is malformed ...") from exc
```

Use UTF-8 JSON, Pydantic validation, and content-free public errors. Do not echo Korean source text, media paths, or Pydantic input values.

**Inventory-content analogs:**

- Generated kana gives deterministic categories/order (`japanese_kana_generated_deck.py:114-170`) but embeds pedagogy in Python and has no review evidence. Copy only the deterministic builder/coverage-test idea, not the storage choice.
- Russian/Polish/Greek phoneme tuples (`russian_phoneme_deck.py:74-175`) prove that spelling, sound, word, translation, sentence, and sentence translation belong together. Move Korean content to validated JSON because each record also needs graph, pronunciation, provenance, and review metadata.

**Required curriculum checks with no exact in-repo analog:**

1. Pack-level `bootstrap_concept_ids` is explicit and cannot be inferred from the first card.
2. Every referenced concept exists exactly once.
3. Every prerequisite is bootstrap-known or has a lower sequence; cycles/forward references fail.
4. Recompute observed-minus-known and require exactly the target as the only unknown.
5. Hangul contains H0-H10 coverage; pronunciation contains P0-P13 and the required onset, batchim, liaison, tensification, nasalization, aspiration, palatalization, complex-coda, contraction, and connected-speech categories.
6. All canonical blocks/names/words/sentences equal their NFC form. Compatibility display jamo must carry explicit mapping metadata; halfwidth is rejected.
7. Traditional jamo names may appear only after every orthographic concept needed to decode the name is already known, matching `KOREAN-STRUCTURE.md:113`.

---

### `src/multilang/services/korean_foundation_review.py`, curation JSON, and review artifacts

**Primary analog:** `src/multilang/services/latin_review.py`.

**Gate model pattern** (`latin_review.py:56-70`):

```python
class LatinReviewGate(BaseModel):
    status: LatinReviewStatus
    reason: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None

    @model_validator(mode="after")
    def require_reason_for_blocking_status(self) -> "LatinReviewGate":
        if self.status in {"needs_review", "rejected"} and self.reason is None:
            raise ValueError("needs_review and rejected gates require a reason")
        return self
```

Use independent `content`, `curriculum`, `media`, and `audio` gates. Every Hangul and pronunciation record needs all gates; a record is learner-ready only when all are approved.

**Fail-closed summary/export pattern** (`latin_review.py:120-156`):

```python
def _blocking_gate_names(record: LatinCuratedRecord) -> list[str]:
    return [gate_name for field_name, gate_name in _GATE_FIELDS
            if getattr(record, field_name).status != "approved"]


def assert_latin_records_export_ready(records: list[LatinCuratedRecord]) -> None:
    summary = summarize_latin_review_records(records)
    if not summary.blocking_gates_by_item_key:
        return
    blockers = [
        f"latin_export_blocked item_key={item_key} gates={','.join(gates)}"
        for item_key, gates in summary.blocking_gates_by_item_key.items()
    ]
    raise ValueError("; ".join(blockers))
```

Use scanner-readable diagnostics containing only family, item key, and gate names. Approval cannot make an invalid curriculum record valid; source validation runs before review readiness.

**Drift protection pattern** (`latin_review.py:159-202`): compare each copied source identity/version/hash field against the frozen source pack before accepting curation. Preserve the approved-overwrite guard at `latin_review.py:220-260` if Phase 31 includes a review updater; otherwise keep updates manual and defer gate-management UX to KQA-01/Phase 34.

**Human-review artifact pattern** (`27-AUDIO-PLAYBACK-REVIEW.md:1-16`):

```yaml
review_artifact: latin-audio-playback-review
selected_provider: google-translate-tts
selected_voice: la
pronunciation_policy: google_translate_latin
playback_review_status: approved
reviewer: user
reviewed_at: 2026-06-17T00:00:00Z
```

For Korean, record the exact inventory/media version and artifact hashes. Jamo/phonological-rule TTS remains `needs_review` until both required reviewer roles are present: pronunciation specialist and independent native speaker. Neither an LLM response nor provider success may set `approved`.

---

### `src/multilang/services/korean_foundation_media.py` and media manifest/assets

**Primary analog:** `src/multilang/services/latin_audio.py`; **secondary analog:** kana media-reference extraction.

**Hash-aligned metadata pattern** (`latin_audio.py:34-95`):

```python
def latin_audio_text_hash(value: str) -> str:
    return sha256(normalize_latin_audio_text(value).encode("utf-8")).hexdigest()


class LatinAudioArtifact(BaseModel):
    audio_kind: LatinAudioKind
    provider: LatinAudioProvider
    provider_version: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    pronunciation_policy: str = Field(min_length=1)
    generated_text: str = Field(min_length=1)
    text_hash: str = Field(min_length=64, max_length=64)
    playback_review_status: LatinAudioReviewStatus
    storage_path: str = Field(min_length=1)
    ...
```

Korean needs the stricter metadata listed in `KOREAN-STRUCTURE.md:382-405`: display/spoken/NFC text, provider/version, locale, voice catalog status/time, SSML hash, output format, byte artifact hash, duration, storage path, review status, reviewed artifact hash, reviewer role, and generation/rejection reason. Verify `artifact_hash` from bytes and require it to equal `reviewed_artifact_hash`; the Latin analog does not yet provide that stronger check.

**Safe repository-relative path pattern** (`latin_audio.py:164-185`):

```python
relative_path = Path(path_text)
if relative_path.is_absolute() or ".." in relative_path.parts:
    return False

root = repo_root.resolve()
candidate = (root / relative_path).resolve(strict=False)
try:
    candidate.relative_to(root)
except ValueError:
    return False

if not candidate.is_file() or candidate.stat().st_size <= 0:
    return False
```

Copy the root-containment, existence, non-empty, and media-marker checks. Extend them with SHA-256 byte verification. Errors expose `item_key`, media kind, and failed field only—never absolute/private paths (`test_latin_audio.py:230-260`).

**Reference extraction pattern** (`japanese_kana_deck.py:92-97`):

```python
def referenced_media(self) -> set[str]:
    names: set[str] = set()
    for value in (self.picture, self.strokes, self.gif, self.audio):
        for match in _MEDIA_REF_RE.finditer(value):
            names.add(match.group(1) or match.group(2))
    return names
```

For Korean, extraction is only the first step. Require every declared picture/stroke/GIF/audio basename to resolve to exactly one manifest entry and every required media kind to be present. Reject absolute paths, traversal, URLs, basename mismatch, duplicate basename with different bytes, script/event-handler HTML, and unmanifested references.

**Raw-glyph TTS anti-pattern—do not copy** (`japanese_kana_generated_deck.py:224-241`):

```python
response = synthesizer.synthesize(
    ssml_text=card.kana,
    voice_id=KANA_VOICE_ID,
    locale=KANA_LOCALE,
    output_path=output_path,
    ...
)
...
except Exception:
    return card
```

The legacy phoneme exporter similarly synthesizes `card.letters` and swallows failures (`russian_phoneme_deck.py:353-418`). Korean production code must not import/call `AzureSpeechAdapter` during export, must not send an isolated display glyph as `spoken_text`, and must not write a deck with blank required audio after an exception. Use approved letter names, explicit syllable/coda contexts, or reviewed human recordings from the frozen manifest.

**Tracked media caveat:** `.gitignore:37-44` ignores `*.mp3` and `*.wav`. Existing Latin media were intentionally force-added (`27-04-SUMMARY.md:61-81`). Follow that narrow precedent or add a narrowly scoped Korean exception; do not remove the global runtime-audio ignore.

---

### `src/multilang/services/phoneme_deck.py` and `russian_phoneme_deck.py`

**Primary analog:** generic mechanics currently embedded in `russian_phoneme_deck.py`.

Extract only the shared visual/note contract; keep Russian, Polish, and Greek inventories, IDs, voices, commands, and current behavior in their existing module.

**Exact shared field tuple** (`russian_phoneme_deck.py:35-45`):

```python
PHONEME_FIELD_NAMES = (
    "Spellings",
    "Sound",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Example Sentence",
    "sentence_audio",
    "Sentence Translation",
)
```

**Generic model pattern** (`russian_phoneme_deck.py:202-216`):

```python
def _build_phoneme_model(*, model_id: int, note_type_name: str) -> genanki.Model:
    template = _load_phoneme_template()
    return genanki.Model(
        model_id,
        note_type_name,
        fields=[{"name": field_name} for field_name in PHONEME_FIELD_NAMES],
        templates=[{
            "name": "Phoneme Card",
            "qfmt": template["front"],
            "afmt": template["back"],
        }],
        css=template["css"],
    )
```

Promote this to a public language-neutral builder accepting model ID, note-type name, and optional additive CSS. The Korean model should use the exact front/back template and append only a Korean font override, analogous to Mandarin composing base + language CSS in `card_template_loader.py:63-81`. Russian/Polish/Greek rendered templates and CSS must remain byte-identical.

**Note/GUID injection pattern** (`russian_phoneme_deck.py:243-249`):

```python
note = RussianPhonemeNote(
    model=model,
    fields=_phoneme_card_fields(card),
)
note._multilang_guid = card.guid
return note
```

Rename the internal shared types to `PhonemeCard`/`PhonemeNote`; preserve `RussianPhonemeCard` and existing builders as aliases/wrappers so imports and tests do not break.

**Exact mapping pattern** (`russian_phoneme_deck.py:465-477`):

```python
values = {
    "Spellings": card.letters,
    "Sound": card.ipa,
    "letter_audio": card.letter_audio,
    "Example Word": card.example_word,
    "word_audio": card.word_audio,
    "Word Translation": card.example_word_translation,
    "Example Sentence": card.example_sentence,
    "sentence_audio": card.sentence_audio,
    "Sentence Translation": card.example_sentence_translation,
}
return [values[field_name] for field_name in PHONEME_FIELD_NAMES]
```

Korean source names may differ internally, but the exported mapping and order remain exactly this tuple.

---

### `src/multilang/templates/korean_hangul_card.md`

**Analog:** `src/multilang/templates/japanese_kana_card.md`.

Copy the layout sequence, not Japanese semantics:

```html
<!-- japanese_kana_card.md:25-53, structural source only -->
<div class="kanaCard kanaCard--front">
  <div class="kanaScript">{{Script}}</div>
  <div class="kanaGlyph jpFont">{{Kana}}</div>
  ...
</div>

<div class="kanaCard kanaCard--back">
  ...
  {{#Gif}}...{{Gif}}...{{/Gif}}
  <hr ... />
  ...{{Romaji}}...
  ...{{Audio}}...
  {{#Picture}}...{{Picture}}...{{/Picture}}
  {{#Strokes}}...{{Strokes}}...{{/Strokes}}
  {{#Mnemonic}}...{{Mnemonic}}...{{/Mnemonic}}
</div>
```

Use the Korean field contract in this order:

```text
SortIndex
Category
JamoOrBlock
ReadingOrName
Sound
Mnemonic
Picture
Strokes
Gif
Audio
TargetConceptId
PrerequisiteConceptIds
ObservedConceptIds
UnknownConceptIds
IPlusOnePolicy
```

Only the pedagogical fields render. The evidence fields remain stored but hidden.

Rename all structural classes (`hangulCard`, `hangulCategory`, `hangulGlyph`, `koFont`, and so on). A model/template regression should scan for at least these forbidden Japanese tokens, case-insensitively:

```text
Japanese, Kana, Romaji, Hiragana, Katakana, jpFont,
Yu Mincho, Hiragino, Noto Sans JP, Noto Serif JP
```

**Do not copy the Japanese font block** (`japanese_kana_card.md:107-124`). There is no Korean font analog in the repository. Use and statically assert an explicit Korean-capable stack, for example:

```css
.koFont,
.hangulCard {
  font-family: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic",
    "맑은 고딕", "Segoe UI", sans-serif;
}
```

Retain the proven responsive image rules, dark canvas, replay-button reset, and conditional media sections (`japanese_kana_card.md:79-105,112-221`). Desktop/mobile observed acceptance remains Phase 34; Phase 31 can claim static structure and generated artifact integrity only.

---

### `src/multilang/services/korean_foundation_export.py`

**Primary analog:** `src/multilang/services/latin_export.py`; **Hangul model analog:** `japanese_kana_deck.py`.

**Frozen row and ordered mapping** (`latin_export.py:43-90`):

```python
@dataclass(frozen=True)
class LatinExportRow:
    sort_index: int
    item_key: str
    ...

    def ordered_field_mapping(self) -> dict[str, object]:
        return {
            "SortIndex": self.sort_index,
            ...
            "Image": self.image,
        }
```

Use separate `HangulExportRow` and `KoreanPronunciationExportRow`; never put two schemas in one tabular file. Source records remain richer than learner-facing rows.

**Validate all frozen inputs before joining** (`latin_export.py:130-192`):

```python
source_pack = source_pack_loader()
records = curated_records_loader()
translations = translation_pack_loader()
audio_manifest = audio_manifest_loader()

records_ready_validator(records)
audio_ready_validator(audio_manifest, repo_root=repo_root)

_require_exact_item_key_order(...)
...
for source_entry in source_pack.entries:
    ...
```

The Korean join order should be: concept registry → family source pack → curation → media manifest → export rows. Require exact version, item-key order, source/content hash, review status, sound basename, and byte hash agreement before creating an output path.

**Model/note pattern** (`japanese_kana_deck.py:345-361`; `latin_export.py:195-231`):

```python
return genanki.Model(
    MODEL_ID,
    NOTE_TYPE_NAME,
    fields=[{"name": name} for name in FIELD_NAMES],
    templates=[{"name": "...", "qfmt": template["front"], "afmt": template["back"]}],
    css=template["css"],
)

note = DedicatedNote(model=model, fields=[...], tags=[...])
note._multilang_guid = deterministic_guid
```

Use dedicated constants and assert them against every existing ID. A safe unused contiguous proposal after the current `1_762_800_901` Mandarin model is:

```text
KOREAN_HANGUL_MODEL_ID          = 1_762_801_001
KOREAN_HANGUL_DECK_ID           = 1_762_801_002
KOREAN_PRONUNCIATION_MODEL_ID   = 1_762_801_003
KOREAN_PRONUNCIATION_DECK_ID    = 1_762_801_004
```

The planner may choose another unused signed-32-bit range, but must lock constants once and add a global collision test. Never derive IDs with Python `hash()`.

Use exact deck names from `KOREAN-STRUCTURE.md:20-21`:

```text
Multilang Korean::Foundations::Hangul
Multilang Korean::Foundations::Pronunciation i+1
```

**Stable GUID pattern** (`domain/exporting.py:95-117`; `latin_export.py:220-231`): hash immutable family/version/item identity, not mutable mnemonic, translation, audio filename, or template text. Tests should prove changing mutable content does not change GUID and changing family/item key does.

**APKG pattern** (`latin_export.py:259-278`):

```python
model = build_latin_anki_model()
deck = genanki.Deck(LATIN_DECK_ID, deck_name)
media_files = _latin_media_files(bundle, repo_root=root)
for row in sorted(bundle.rows, key=lambda row: (row.sort_index, row.item_key)):
    deck.add_note(build_latin_anki_note(row, model=model))
package = genanki.Package(deck)
package.media_files = [str(path) for path in media_files]
package.write_to_file(str(output_path))
```

Resolve and validate media before `output_path.parent.mkdir(...)`; failure must leave no partial artifact.

**CSV/TSV pattern** (`latin_export.py:285-333`; `export_tabular_bundle.py:19-54`): use UTF-8, deterministic row order, `csv.writer`, and the five Anki headers:

```text
#separator:Comma|Tab
#html:true
#notetype:<exact Korean note type>
#deck:<exact deck name>
#columns:<exact field order>
```

The current generic/Latin tabular writers preserve sound tags but do not package media. That alone is insufficient for KPRO-01 and `KOREAN-STRUCTURE.md:421`. The dedicated Korean writer should also copy or stage each approved basename into a deterministic sibling media directory and write a checksum manifest mapping every sound/image reference to that file. Tests must resolve every table reference through that bundle.

**Do not modify as the first choice:** `domain/exporting.py`, `export_anki_package.py`, `export_tabular_bundle.py`, or `runtime.py`. Their row models describe modern/Latin/Japanese/Mandarin job exports, not foundation curricula. Phase 34 can unify final all-family export evidence if needed.

---

### `src/multilang/cli.py`

**Primary analog:** dedicated Latin all-format command (`cli.py:1102-1138`), not the APKG-only legacy phoneme commands.

```python
@cli.command("export-latin-mvp")
def export_latin_mvp(
    format: Annotated[
        ExportArtifactFormat,
        typer.Option("--format", help="Latin export format: apkg, csv, or tsv."),
    ],
    output_dir: Annotated[Path, typer.Option("--output-dir", ...)],
    deck_name: Annotated[str, typer.Option("--deck-name", ...)] = LATIN_DECK_NAME,
) -> None:
    try:
        result = export_latin_mvp_bundle(...)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"artifact_path={result.output_path}")
    typer.echo(f"card_count={result.card_count}")
    typer.echo(f"media_count={result.media_count}")
    typer.echo(f"note_type={result.note_type_name}")
    typer.echo(f"export_status={result.export_status}")
```

Prefer two explicit family commands or one enum-constrained `--family`; do not allow arbitrary module/template/path selection. Keep output scanner-safe and aggregate. Do not print Korean source records, reviewer notes, local absolute paths, provider payloads, or credentials.

No authentication layer exists: this is a local operator CLI. The guard is source/review/media validation before file output.

**Runtime composition:** follow the isolated Latin command path. Do not instantiate Kiwi, Azure, the modern DB runtime, text generation, Tatoeba, or the Korean frequency pipeline merely to export frozen foundations. Tests should inject loaders/bundles or temporary repo roots rather than live providers.

---

## Test Pattern Assignments

### Domain And Curriculum Tests

**Sources:** `tests/domain/test_korean.py:69-102,127-238`; `tests/services/test_latin_source_pack.py`; `test_japanese_kana_generated_deck.py:22-56`.

Copy these styles:

- construct complete valid frozen models through helper factories, override one field per negative test, and expect Pydantic `ValidationError`;
- compare NFD/NFC canonical blocks while preserving explicit source/display evidence;
- parameterize compatibility/halfwidth negatives;
- assert exact stage/category coverage, unique item/concept IDs, contiguous order, and stable GUIDs;
- mutate forward prerequisite, unknown set, target, bootstrap, cycle, omitted category, duplicate ID, NFD text, and false rule evidence; each must fail before review/export;
- explicitly test the standalone-jamo display mapping boundary so compatibility display glyphs never weaken lexical canonicalization.

### Review And Media Tests

**Review analog** (`test_latin_review.py:104-119`):

```python
with pytest.raises(ValueError) as exc_info:
    assert_latin_records_export_ready(records)

assert "latin_export_blocked item_key=... gates=grammar,audio" in str(exc_info.value)
```

**Unsafe path/privacy analog** (`test_latin_audio.py:230-260`): test absolute Windows paths, `..`, missing, empty, wrong marker, basename mismatch, and outside-root resolution. Assert diagnostics omit the bad path and repo root.

**Exact text/hash analog** (`test_latin_audio.py:332-360`): mutate spoken text, text hash, artifact bytes, reviewed artifact hash, provider/voice/policy, source version, and item order. Every mismatch blocks.

Additional Korean cases:

- raw isolated jamo where `spoken_text == display_glyph` cannot become approved;
- letter-name audio requires the approved Korean name or human-recording evidence;
- consonant sound audio requires explicit syllable/coda context or human recording;
- phonological-rule audio requires both specialist and independent native-speaker approvals;
- provider/voice/SSML/prosody/spoken-text drift changes the asset identity and resets review;
- no test may obtain `approved` by calling a fake provider alone.

### Shared Phoneme Regression Tests

**Source:** `test_russian_phoneme_deck.py:118-263`.

Retain the existing assertions that Polish/Greek templates and CSS equal Russian, exact field order is preserved, only allowed template references occur, translations reveal on the back, and audio fields map exactly. Add Korean assertions:

```text
Korean fields == PHONEME_FIELD_NAMES
Korean front/back == shared front/back
Korean CSS starts with shared CSS and adds only the Korean font override
Russian/Polish/Greek templates and CSS remain byte-identical to the pre-refactor values
```

Do not weaken the current APKG and limited CLI tests to make the extraction pass.

### Template Tests

**Kana structure analog** (`test_card_template_loader.py:535-563`): assert exact field tuple, front/back class anchors, conditional media blocks, order of GIF/divider/reading/audio/picture/strokes/mnemonic, dark palette, and replay-button reset.

**Phoneme shared-layout analog** (`test_card_template_loader.py:737-775`): assert the exact reference list and identical shared models. Add Korean font presence and Japanese token/font absence scans.

Static checks in Phase 31 do not equal observed Anki Desktop/mobile acceptance; leave that claim to Phase 34.

### Export Tests

**APKG inspection analog** (`test_latin_export.py:190-231`; `test_export_anki_package.py:605-770`): open the archive, inspect `media`, extract `collection.anki2`, query models/notes/decks with SQLite, and assert model ID/name, field order, note count, deck name, GUID stability, tags, and blank/hidden evidence behavior. Mutated/missing media must fail before an output file exists.

**Tabular analog** (`test_latin_export.py:234-273`): parse both CSV and TSV with `csv.reader`, assert the exact five headers and field values/order, then resolve every media reference through the emitted media/checksum manifest.

**ID isolation analog** (`test_v20_existing_modes_regression_evidence.py:60-69`): assert both Korean note-type names and all four IDs are distinct from normal/manual/highlight, Japanese frequency, kana, Mandarin, Russian/Polish/Greek phoneme, and Latin IDs.

### CLI And Integration Tests

**CLI analog:** `test_generate_command.py:865-894` uses `CliRunner`, temporary output, a fake boundary, and scanner-stable output assertions. Korean tests should use real committed/fixture manifests and no provider object. Test APKG/CSV/TSV routing, invalid family/format, blocked review, false i+1, missing media, and no partial output.

**Integration flow:** build both real approved source packs into all requested formats; inspect APKG collections and tabular media bundles; then mutate one curriculum edge and one reviewed byte hash to prove fail-closed behavior. Keep external providers offline.

## Shared Patterns

### Deterministic Identity

**Sources:** `domain/exporting.py:95-117`, `japanese_kana_deck.py:87-90`, `latin_export.py:220-231`.

- Use SHA-256 truncated to 32 hex characters for Anki GUIDs.
- Hash immutable family/version/item identity only.
- Store model/deck IDs as literal constants and test global uniqueness.
- Preserve item keys across text/media/template corrections; a content correction should not duplicate a learner's note.

### Fail Before Writing

**Sources:** `latin_export.py:142-192,268-278`; `export_anki_package.py:121-139,211-220`.

Load and validate source, curriculum, review, and media; resolve all basenames; only then create the output directory/file. Missing, stale, ambiguous, false-i+1, or unapproved input blocks every format.

### Template References Are Schemas

**Source:** `card_template_loader.py:116-132`.

```python
for reference in _iter_template_references(template):
    if reference in allowed_fields or reference in _ALLOWED_NON_FIELD_HELPERS:
        continue
    invalid_references.append(reference)
if invalid_references:
    raise ValueError("card template references fields that are not exported: ...")
```

Run equivalent validation for the Hangul template and shared pronunciation template before constructing a model. Templates render frozen fields; they never calculate Korean concepts or pronunciation.

### Media Is Manifest Data, Not A Best-Effort Side Effect

- Every visible media/sound reference has one approved manifest record and existing checksum-aligned bytes.
- APKG embeds those exact bytes; CSV/TSV bundles preserve tags and ship a resolvable media/checksum mapping.
- No silent `except Exception`, no blank required audio, no live export-time synthesis, and no fallback provider.
- Never expose an absolute path in a public artifact or error.

### Korean Canonical Boundaries

- Keep product identity `ko`; `ko-KR` occurs only as explicit media/provider locale metadata.
- NFC-normalize Korean names, blocks, words, sentences, and pronunciations before hashing/storage.
- Keep an explicit pedagogical display mapping for standalone jamo; do not NFKC-fold or silently admit compatibility/halfwidth data into lexical identity.
- Romanization is not pronunciation truth and should not be introduced as a persistent pronunciation/frequency dependency.

### Existing Modes Stay Isolated

- Russian, Polish, and Greek public imports, IDs, inventories, templates, CSS, audio behavior, commands, and APKGs remain unchanged.
- Japanese kana source/template/code remains unchanged; copy its layout into a Korean-owned template rather than parameterizing Japanese fields.
- Modern normal/manual/highlight, Japanese frequency, Mandarin, and Latin exporter schemas remain unchanged.
- Phase 30 morphology/runtime tests remain green; foundation export does not create another Kiwi instance.

## No-Touch Regression Boundaries

| File/Surface | Why it should remain untouched in the first Phase 31 plan |
|---|---|
| `src/multilang/runtime.py` | Modern DB-backed lexical/text/audio composition; frozen foundations can use an isolated CLI/service path. |
| `src/multilang/domain/exporting.py` | Existing job-row schemas cannot represent two foundation field sets without unrelated drift. |
| `src/multilang/services/export_anki_package.py` | Existing generic packaging assumes one modern row schema and two audio kinds. Copy its strict basename checks into the dedicated exporter. |
| `src/multilang/services/export_tabular_bundle.py` | Existing writer has no media-bundle contract. Do not weaken existing outputs while adding one for Korean foundations. |
| `src/multilang/services/japanese_kana_deck.py` and template | Required as a regression oracle; Korean must not leak back into Japanese. |
| `src/multilang/services/audio_voice_registry.py` | Phase 30 intentionally leaves Korean without an approved production voice; live Azure voice qualification belongs to Phase 32. |
| `assets/frequency/ko/` | Licensing blocker and Phase 32 scope; foundation manifests are not a frequency asset. |
| Alembic/DB models/repositories | Curriculum/source/review/media evidence can be frozen manifests; no Phase 31 requirement demands job-table persistence. |

If execution discovers that a no-touch surface is genuinely required, stop and replan with a focused regression proof instead of adding an opportunistic Korean branch.

## Regression Matrix

### Phase 31 Focused Gates

```text
UV_OFFLINE=1 uv run --extra dev pytest \
  tests/domain/test_korean.py \
  tests/services/test_korean_curriculum.py \
  tests/services/test_korean_foundation_review.py \
  tests/services/test_korean_foundation_media.py -q

UV_OFFLINE=1 uv run --extra dev pytest \
  tests/services/test_phoneme_deck.py \
  tests/services/test_korean_foundation_export.py \
  tests/services/test_card_template_loader.py \
  tests/cli/test_korean_foundation_commands.py -q

UV_OFFLINE=1 uv run --extra dev pytest \
  tests/integration/test_korean_foundations_flow.py -q
```

### Direct Analog And Existing-Mode Gates

```text
# Kana + phoneme contracts
UV_OFFLINE=1 uv run --extra dev pytest \
  tests/services/test_japanese_kana_deck.py \
  tests/services/test_japanese_kana_generated_deck.py \
  tests/services/test_russian_phoneme_deck.py \
  tests/integration/test_russian_phoneme_template_refresh_flow.py -q

# Generic and Latin export/media behavior
UV_OFFLINE=1 uv run --extra dev pytest \
  tests/services/test_export_anki_package.py \
  tests/services/test_export_tabular_bundle.py \
  tests/services/test_latin_audio.py \
  tests/services/test_latin_review.py \
  tests/services/test_latin_export.py \
  tests/integration/test_v20_existing_modes_regression_evidence.py -q

# Verified Korean Phase 30 boundary
UV_OFFLINE=1 uv run --extra dev pytest \
  tests/services/test_korean_morphology.py \
  tests/services/test_korean_language_support.py \
  tests/integration/test_korean_modern_flow.py -q

# Final caused-regression gate
UV_OFFLINE=1 uv run --extra dev pytest -q
```

Also scan production foundation modules to require zero `AzureSpeechAdapter`, Tatoeba, LLM-provider, `assets/frequency/ko`, and unapproved raw-glyph synthesis paths.

## No Exact Analog Found

| Surface | Why no exact analog exists | Planner instruction |
|---|---|---|
| Strict curriculum graph and bootstrap | Existing inventories are ordered lists, not executable concept graphs. | Implement one shared validator over explicit concept IDs; recompute unknowns and fail on cycles/forward edges/false i+1. Do not infer prerequisites from sequence labels alone. |
| Standalone jamo versus Phase 30 canonicalization | Existing Korean contracts reject Compatibility Jamo, while foundation display needs reviewed standalone symbols. | Keep lexical canonicalization unchanged and model the display-to-conjoining-jamo mapping explicitly. Stop if product decisions require silently treating compatibility glyphs as canonical lexical text. |
| Specialist-reviewed pedagogical audio | Legacy kana/phoneme decks synthesize raw glyphs/letters and silently tolerate failure; Latin has human playback gates but not Korean reviewer-role/artifact-hash requirements. | Use frozen approved media, dual reviewer roles where required, and byte-hash alignment. No auto-approval or live export-time TTS. |
| CSV/TSV media survival | Existing tabular writers preserve sound tags but do not package a resolvable media bundle. | Add Korean-owned media/checksum bundle output and tests; do not claim KPRO-01 from text columns alone. |
| Korean font rendering | No existing template has a Korean-specific font stack or observed Anki Korean rendering evidence. | Add static Korean stack/leakage checks now; reserve Desktop/mobile observed acceptance for Phase 34. |
| Complete Korean pedagogical inventory | No in-repo source proves H0-H10/P0-P13 linguistic correctness. | Use `KOREAN-STRUCTURE.md` plus current authoritative research/specialist review; code analogs establish shape, not linguistic truth. |

## Planner Guardrails

1. Use the reconciled canonical Phase 31 slug `i-plus-1` for all plans and internal references.
2. Keep one concept registry and one strict validator shared by Hangul and pronunciation.
3. Keep complete curriculum/pronunciation metadata in frozen source records; expose only the approved learner field schemas.
4. Build a Korean-owned Hangul template; do not parameterize or mutate the Japanese template.
5. Extract only language-neutral phoneme mechanics and preserve every existing Russian/Polish/Greek public symbol and behavior.
6. Never reuse the legacy raw-letter/raw-glyph export-time TTS or silent exception patterns for Korean.
7. Require real specialist/native-speaker review evidence and exact reviewed byte hashes before `approved` media can export.
8. Treat all source/review/media manifests as untrusted input to Pydantic/path/hash validation even when committed.
9. Support exact APKG/CSV/TSV structural/media evidence for foundation families without claiming Phase 34's final all-family visual/import acceptance.
10. Do not add a Korean frequency asset, production voice registry entry, Tatoeba route, LLM approval path, DB migration, Hanja, dialect, or persistent romanization.
11. Preserve `ko` internally and allow `ko-KR` only in explicit media/provider locale fields.
12. Run the focused analog baseline, Phase 30 Korean boundary, global ID-collision test, and full suite before claiming no regression.

## Metadata

**Analog search scope:** `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `KOREAN-STRUCTURE.md`, Phase 30 handoff/verification/patterns, Phase 27 review artifacts, `src/multilang/domain`, `src/multilang/services`, `src/multilang/templates`, `src/multilang/runtime.py`, `src/multilang/cli.py`, `data/latin_mvp`, and relevant domain/service/CLI/integration tests.
**Primary precedents:** Japanese kana layout/model/media references; shared Russian/Polish/Greek phoneme contract; Latin frozen source/review/audio/export path; generic strict APKG/CSV/TSV packaging; Phase 30 Korean NFC/fail-closed contracts.
**Files directly read:** 35+ source, data, test, and planning artifacts; broader source/test inventories and ID usages searched.
**Pattern extraction date:** 2026-08-04.
**Known live baseline:** lifecycle preflight allowed with expected completed Phase 30 dirt; focused analog suite 123/123 passed offline; no source file was modified by this mapping task.
