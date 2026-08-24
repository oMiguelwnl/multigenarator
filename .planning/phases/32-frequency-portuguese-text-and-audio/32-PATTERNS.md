# Phase 32: Frequency, Portuguese Text, and Audio - Pattern Map

**Mapped:** 2026-08-21
**Requirements:** KFREQ-01, KFREQ-02, KFREQ-03, KTXT-01, KAUD-01, GLEX-01, GLEX-02, GMOR-01, GTXT-01, GPRO-01, GAUD-01
**Files classified:** 68 inferred artifacts (40 production/data/evidence, 28 tests)
**Structural analogs found:** 68 / 68
**Exact Korean production-data/quality/voice analogs:** 0 / 4

## Inputs and Scope Truth

- This map was produced before `32-APPROACH.md`, `32-RESEARCH.md`, and the source decision existed. Those later user-aligned artifacts are authoritative where they supersede a pre-alignment assumption; the file analogs and live-code findings below remain applicable.
- Phase 32 depends on Phase 31. Plans 31-01 through 31-10 prove machinery with temporary fixtures, while the replanned sequence 31-11 through 31-28 owns assisted curation, genuine review, canonical snapshot authorization/activation, exact licensed media, and local production exports. Phase 32 consumes only the final active result from Plan 31-28 and must not manufacture or bypass those facts.
- NIKL `한국어 학습용 어휘 목록` is now the user-selected rank and initial lexical-authority path. Exact attachment bytes, KOGL terms evidence, attribution, transformation/modernity review, and repository redistribution remain unresolved; do not create or commit `assets/frequency/ko/` until `32-FREQUENCY-SOURCE-DECISION.md` is satisfied.
- Preserve the verified Phase 30 contract: `ko` is the sole product identity; `ko-KR` is provider-locale metadata only; Korean text is NFC; source-backed lemma/POS/sense plus the exact analyzer fingerprint are authoritative; ambiguity, OOV, unavailable analysis, and fingerprint drift fail closed; one lazy Kiwi instance is shared.
- Preserve the Phase 31 boundary: foundation jamo/rule audio comes only from the active hash-bound foundation snapshot. Phase 32 qualifies production frequency word/sentence audio; it must not reintroduce raw-glyph synthesis or mutate foundation candidates/reviews/media.
- Per the later user-confirmed approach, Phase 32 owns actual Korean parent/Level 1/2/3 child-deck packaging and structural proof. Phase 34 generalizes the behavior and owns final all-family APKG/import/render/playback evidence; Phase 32 still must not claim observed Desktop/mobile acceptance.

### Live Gaps the Plans Must Close

1. `runtime.py:599-604` still composes lexical grounding with `allow_frequency_seed_fallback=True`; final generation can therefore replace missing source grounding with a `wordfreq` seed.
2. `frequency_decks.py:174-185,362-434` still contains a live `iter_wordlist()` generation path. It is suitable only for bootstrap/test tooling, never final runtime.
3. `generate_text_items.py:373-413` calls ordinary generation again for repair. `text_generation.py:391-420` gives both calls the same `sentence` cache identity, so a repair can replay the initial cached response.
4. Text generation returns one response, not a bounded candidate set; validation therefore accepts or repairs the first response rather than choosing the best valid candidate.
5. Generic final repair can still promote Tatoeba (`generate_text_items.py:415-454`). Korean is already skipped, but GLEX/GTXT require no automatic Tatoeba final-deck fallback.
6. Definition calls in `lexical_grounding.py:1113-1129` bypass the retry/cache/telemetry orchestration used by sentence and translation calls.
7. Text calls made by `GenerateTextItemsService` do not pass `job_id` (`generate_text_items.py:187-193,385-391`), leaving otherwise-capable telemetry without job identity.
8. Azure discovery retains only `ShortName` values (`azure_speech_adapter.py:49-71`), not a hash-bound catalog receipt with locale/status/check time. The voice registry intentionally has no Korean entry (`audio_voice_registry.py:42-147`).
9. Audio persistence lacks provider version, catalog evidence, artifact SHA-256, review status/hash/role, and a controlled rejection reason (`domain/audio.py:54-65`; `audio_repository.py:38-57`).
10. `GenerateAudioItemsService` records item success after processing even when a required asset failed (`generate_audio_items.py:93-108`).
11. The export gate checks count/status/fallback but not exact-text hash alignment or audio approval (`domain/exporting.py:374-447`). `--allow-partial` must not turn an unapproved Korean production frequency deck into a final success.

## File Classification

### Production, Data, and Human Evidence

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `$PHASE_DIR/32-FREQUENCY-SOURCE-DECISION.md` **(create)** | config/review evidence | event-driven | Phase 31 review artifacts; `27-AUDIO-PLAYBACK-REVIEW.md` | exact role |
| `assets/frequency/ko/ATTRIBUTION.md` **(conditional create)** | config/legal evidence | file-I/O | Latin source provenance; Phase 31 rights evidence | role-match |
| `assets/frequency/ko/manifest-v1.json` **(conditional create)** | model/config | file-I/O, batch | `data/latin_mvp/latin-mvp-50-v1.json`; Korean foundation manifests | role-match |
| `assets/frequency/ko/curated-v1.csv` **(conditional create)** | model/data | file-I/O, batch | `assets/frequency/pt/curated-v1.csv` | structure-only |
| `assets/frequency/ko/rejections-v1.csv` **(conditional create)** | model/data | file-I/O, batch | `assets/frequency/pt/rejections-v1.csv` | role-match |
| `assets/frequency/ko/curation-report-v1.json` **(conditional create)** | report/config | batch, transform | `generation_report.py:23-116`; Latin QA summaries | role-match |
| `$PHASE_DIR/32-KOREAN-TEXT-REVIEW.md` **(create)** | config/review evidence | event-driven | Phase 31 curriculum/playback review artifacts | exact role |
| `$PHASE_DIR/32-AZURE-VOICE-REVIEW.md` **(create)** | config/review evidence | event-driven | `27-AUDIO-PLAYBACK-REVIEW.md`; Korean foundation media receipts | exact role |
| `data/korean_audio/azure-ko-KR-v1.json` **(create after qualification)** | model/config | file-I/O, event-driven | `korean-foundations-v1-media.json`; `latin-audio-samples.json` | role-match |
| `src/multilang/domain/korean.py` | model | transform | its frozen Korean contracts at `domain/korean.py:125-140,287-427,688-754` | exact |
| `src/multilang/domain/lexicon.py` | model | CRUD, transform | `LexicalProvenance`/`LexicalCardCandidate` at `domain/lexicon.py:35-75` | exact |
| `src/multilang/domain/text_quality.py` | model | CRUD, transform | `TextQualityRecord` at `domain/text_quality.py:31-98` | exact |
| `src/multilang/domain/audio.py` | model | CRUD, file-I/O | `AudioAssetRecord` at `domain/audio.py:38-84`; foundation media slot | exact role |
| `src/multilang/settings.py` | config | request-response | existing provider/retry/audio settings at `settings.py:85-133` | exact |
| `src/multilang/services/korean_frequency.py` **(create)** | service/model | file-I/O, batch, transform | `frequency_decks.py`; `korean_curriculum.py`; `latin_source_pack.py` | role-match |
| `scripts/build_frequency_assets.py` | utility/controller | file-I/O, batch | its current bootstrap/check split at `build_frequency_assets.py:54-209` | exact |
| `src/multilang/services/frequency_decks.py` | service | file-I/O, batch | current frozen loader at `frequency_decks.py:196-315` | exact |
| `src/multilang/services/ingest_lexical_items.py` | service | batch, CRUD | current frequency orchestration at `ingest_lexical_items.py:207-419` | exact |
| `src/multilang/services/lexical_grounding.py` | service | CRUD, transform, request-response | Korean source consensus path at `lexical_grounding.py:708-805` | exact |
| `src/multilang/services/korean_text_quality.py` **(create)** | service/model | transform, request-response | `latin_translation_quality.py`; `text_validation.py` | role-match |
| `src/multilang/services/text_generation.py` | service/model | request-response | current typed request/cache/telemetry boundary | exact |
| `src/multilang/services/provider_text_adapters.py` | provider | request-response | existing LiteLLM/DeepL structured adapters | exact |
| `src/multilang/services/text_validation.py` | service | transform | existing Korean-first morphology validation | exact |
| `src/multilang/services/generate_text_items.py` | service | batch, request-response, CRUD | current generate/validate/repair orchestration | exact |
| `src/multilang/services/regenerate_text_item.py` | service | request-response, CRUD | `GenerateTextItemsService` shared orchestration | role-match |
| `src/multilang/services/text_review.py` | service/report | file-I/O, batch | existing deterministic flagged-row report | exact |
| `src/multilang/services/generation_report.py` | service/report | file-I/O, batch | existing quality/provider report | exact |
| `src/multilang/services/azure_speech_adapter.py` | provider | request-response, file-I/O | current live catalog + synthesis adapter | exact |
| `src/multilang/services/audio_voice_registry.py` | config/service | request-response | existing approved voice plans and fail-closed selection | exact |
| `src/multilang/services/fallback_audio_adapter.py` | provider | request-response, file-I/O | current ordered provider chain | exact |
| `src/multilang/services/audio_synthesis.py` | service | request-response, file-I/O | current prepare/retry/hash/storage pattern | exact |
| `src/multilang/services/generate_audio_items.py` | service | batch, CRUD, file-I/O | current accepted-text audio orchestration | exact |
| `src/multilang/services/audio_integrity.py` | utility | transform, file-I/O | current exact word/text-hash guard | exact |
| `src/multilang/repositories/audio_repository.py` | repository | CRUD | current explicit payload/round-trip mapping | exact |
| `src/multilang/repositories/text_repository.py` | repository | CRUD | current text evidence JSON round-trip | exact |
| `src/multilang/db/models.py` | model | CRUD | current text/audio/provider persistence models | exact |
| `alembic/versions/20260821_18_frequency_text_audio_evidence.py` **(create)** | migration | CRUD | `20260804_17_korean_lexical_identity.py`; initial text/audio migrations | exact |
| `src/multilang/runtime.py` | provider/composition root | request-response, batch | current shared service composition at `runtime.py:471-634` | exact |
| `src/multilang/domain/exporting.py` | model/guard | transform | final frequency quality gate at `domain/exporting.py:374-466` | exact |
| `src/multilang/cli.py` | controller/route | request-response, file-I/O | fixed Korean foundation subapp at `cli.py:729-925` | exact role |

`assets/frequency/ko/*` is conditional: if the approved decision permits local use but not repository redistribution, use the same manifest schema under a private configured root and keep the repository paths absent. The decision artifact, loader behavior, and tests must make that disposition explicit; a planner must not assume “approved for use” means “approved to commit.”

### Tests

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/domain/test_korean.py` | test | transform | existing frozen Korean invariant tests | exact |
| `tests/domain/test_lexicon.py` | test | transform | Korean typed identity/provenance round-trip tests | exact |
| `tests/domain/test_text_quality.py` | test | transform | current status/repair-flow tests | exact |
| `tests/domain/test_audio.py` | test | transform | current hash/alignment model tests | exact |
| `tests/services/test_korean_frequency.py` **(create)** | test | file-I/O, batch, transform | `test_frequency_decks.py`; `test_korean_curriculum.py` | role-match |
| `tests/services/test_frequency_decks.py` | test | file-I/O, batch | current 3000/1000/duplicate asset tests | exact |
| `tests/services/test_lexical_grounding.py` | test | CRUD, request-response | existing Korean source-authority tests | exact |
| `tests/services/test_korean_text_quality.py` **(create)** | test | transform, request-response | `test_latin_translation_quality.py`; `test_text_validation.py` | role-match |
| `tests/services/test_text_generation.py` | test | request-response | current identity/cache/telemetry tests | exact |
| `tests/services/test_provider_text_adapters.py` | test | request-response | current fake-completion structured-output tests | exact |
| `tests/services/test_text_validation.py` | test | transform | current Korean morphology fail-closed matrix | exact |
| `tests/services/test_generate_text_items.py` | test | batch, request-response | current repair/review/Korean-no-Tatoeba tests | exact |
| `tests/services/test_regenerate_text_item.py` | test | request-response, CRUD | current one-item regeneration tests | exact |
| `tests/services/test_text_review.py` | test | file-I/O, batch | current sorted/redacted review report tests | exact |
| `tests/services/test_generation_report.py` | test | file-I/O, batch | current provider-call report test | exact |
| `tests/services/test_azure_speech_adapter.py` | test | request-response, file-I/O | current fake live-catalog/SDK tests | exact |
| `tests/services/test_audio_voice_registry.py` | test | request-response | current Korean-unapproved and alternate-order tests | exact |
| `tests/services/test_fallback_audio_adapter.py` | test | request-response, file-I/O | current provider-chain tests | exact |
| `tests/services/test_audio_synthesis.py` | test | request-response, file-I/O | current accepted-text/retry/integrity tests | exact |
| `tests/services/test_generate_audio_items.py` | test | batch, CRUD | current failure/fallback counters and reuse tests | exact |
| `tests/services/test_audio_integrity.py` | test | transform, file-I/O | current exact word/hash mismatch matrix | exact |
| `tests/repositories/test_audio_repository.py` | test | CRUD | current commit/reload/reuse tests | exact |
| `tests/repositories/test_text_repository.py` | test | CRUD | current text/cache round-trip tests | exact |
| `tests/test_migration_schema_parity.py` | test | CRUD | current real-Alembic parity and 17 upgrade cycle | exact |
| `tests/test_runtime.py` | test | request-response | current monkeypatched composition tests | exact |
| `tests/cli/test_korean_frequency_commands.py` **(create)** | test | request-response, file-I/O | Korean foundation `CliRunner` tests; generic generate command tests | role-match |
| `tests/integration/test_korean_frequency_text_audio_flow.py` **(create)** | test | batch, CRUD, request-response, file-I/O | `test_korean_modern_flow.py`; `test_frequency_e2e_export_flow.py` | role-match |
| `tests/integration/test_frequency_e2e_export_flow.py` | test | batch, CRUD, request-response, file-I/O | current file, converted to frozen-asset final-runtime evidence | exact |

## Pattern Assignments

### Frequency Source Decision, Frozen Asset, and `src/multilang/services/korean_frequency.py`

**Applies to:** the source-decision/attribution/manifest/CSV/report artifacts, `domain/korean.py`, `korean_frequency.py`, and `scripts/build_frequency_assets.py`.

**Primary analogs:** `latin_source_pack.py`, Korean foundation frozen models, and the generic frequency CSV loader. The Portuguese CSV is a field-order analog only, not a quality or licensing precedent.

**Frozen model pattern** (`domain/korean.py:125-132`):

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

Add the SPEC's `KoreanFrequencyEntry` here, not in a second Korean domain module. It must contain one resolved `KoreanLexicalIdentity`, final/source rank, level, source/version, license disposition, exact analyzer fingerprint/version, and controlled curation flags. Construction must reject unresolved identity, non-NFC values, function-morpheme POS, and inconsistent rank/level.

**Strict JSON loader/error pattern** (`latin_source_pack.py:300-314`, as used by Phase 31):

```python
try:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return SourcePack.model_validate(payload)
except FileNotFoundError as exc:
    raise ValueError("source pack is missing") from exc
except json.JSONDecodeError as exc:
    raise ValueError("source pack JSON is malformed") from exc
```

Keep public failures content-free. The source decision and manifest may expose approved public attribution/license identifiers, but errors must not echo private paths, legal notes, source rows, or lexical content.

**Existing CSV structure—not sufficient for Korean** (`assets/frequency/pt/curated-v1.csv:1-3`):

```csv
language,frequency_list_version,level,rank,source_rank,display_form,lemma,lemma_key,part_of_speech,definition_seed,source_provenance,curation_flags
pt,v1,1,1,1,de,de,de,unknown,de,wordfreq:pt,wordfreq_seeded;deterministically_filtered;structurally_curated
```

Do not copy `part_of_speech=unknown`, lemma-only deduplication, or `wordfreq:*` as final authority. Korean rows need flattened or canonical-JSON columns sufficient to reconstruct the complete typed identity without consulting live `wordfreq`, a provider, or a new Kiwi analysis.

**Fail-closed asset loader pattern** (`frequency_decks.py:196-212`):

```python
if not path.is_file():
    raise FileNotFoundError(f"missing curated frequency asset: {path}")
...
validate_curated_frequency_entries(entries, language=language, version=version)
validate_frequency_rejection_rows(language, version=version, assets_dir=assets_dir)
```

Extend this shape through `korean_frequency.py` so the manifest is loaded and hash-checked before either CSV. Required validation order:

1. approved source/use/redistribution disposition;
2. manifest version and exact SHA-256 bindings for attribution, curated rows, rejection rows, and report;
3. exact pinned analyzer fingerprint/version;
4. exactly 3000 final rows and contiguous ranks 1..3000;
5. exactly 1000 rows per level and level/rank agreement;
6. uniqueness by lemma + normalized POS + source sense, including no cross-level duplicates;
7. no unresolved/ambiguous/OOV identity, inflection duplicate, proper-name/script noise, standalone particle, or productive ending;
8. rejection/report numerator-denominator reconciliation with every source candidate accounted for;
9. deterministic order and reserve/replacement evidence;
10. no blank/placeholder/`unknown` provenance, license, POS, sense, analyzer, or curation value.

`wordfreq` remains allowed in the build script as a bootstrap candidate source after the decision permits it. It must not be imported by `korean_frequency.py`, and the build operation must validate the decision before creating a directory or opening a source stream.

---

### Final Frequency Runtime: `frequency_decks.py`, `ingest_lexical_items.py`, `lexical_grounding.py`, and `domain/lexicon.py`

**Primary analog:** the current full-size frozen asset path. **Anti-pattern:** current runtime fallback composition.

```python
# runtime.py:599-604 — must change for final frequency generation
grounding_service=LexicalGroundingService(
    lookup=LexicalLookup(data_dir=runtime_settings.lexicon_data_dir),
    pronunciation_generator=_build_pronunciation_adapter(runtime_settings),
    definition_generator=sentence_adapter,
    allow_frequency_seed_fallback=True,
    korean_morphology=korean_morphology,
),
```

For a production-size frequency request (`required_count_per_level == 1000`), the only legal path is:

```text
configured manifest/version
  -> hash-bound frozen Korean rows
  -> typed resolved KoreanFrequencyEntry
  -> persisted LexicalCardCandidate with exact Korean identity/provenance
  -> text generation
```

There is no final-runtime edge back to `iter_wordlist`, `_build_seed_candidate`, `_ground_frequency_seed_candidate`, first-sense lookup, or provider-authored identity. Small explicit test/smoke runs may use injected fixture entries, but must be visibly non-production and cannot satisfy GLEX/KFREQ evidence.

Extend `LexicalProvenance` with optional, typed/excluded-when-absent source version, source sense/POS, grounding confidence, and curation/ambiguity disposition. Existing non-Korean serialized payloads must remain unchanged. The complete Korean identity remains the stronger source of truth and must match those summary fields.

Definition generation may fill learner-facing Portuguese text only after identity is frozen. Route it through the same provider execution boundary as all other tasks; provider output cannot revise lemma, POS, sense, register, analyzer evidence, frequency rank, or curation approval.

---

### Adaptive i+1 Evidence and Deterministic Candidate Scoring

**Applies to:** `domain/korean.py`, `domain/text_quality.py`, `korean_frequency.py`, `korean_text_quality.py`, `text_repository.py`, and their tests.

**Structural analog 1:** persisted curriculum evidence (`domain/korean.py:318-369`) stores target, prerequisites, observed, unknown, and policy in a frozen model.

**Structural analog 2:** Tatoeba performs hard filtering before deterministic tuple scoring (`tatoeba_sentence_source.py:211-250,291-327`):

```python
eligible.append((self._score_candidate(...), candidate))
...
_, selected = sorted(
    eligible,
    key=lambda entry: (entry[0], entry[1].sentence_id),
    reverse=True,
)[0]
```

Copy the filter-then-score shape, not Tatoeba's source or generic suffix matching. Persist a frozen adaptive evidence object for every selected Korean frequency sentence containing at least:

- target lexical concept ID derived from the exact lemma/POS/sense identity;
- known concept IDs (active foundation snapshot plus earlier frozen frequency identities);
- observed concept IDs from the selected sentence;
- incidental/unknown concept IDs;
- policy=`adaptive`;
- deterministic score components and scorer/policy version;
- candidate hash and selected-candidate ordinal;
- independent naturalness/register/quality gate result.

Naturalness is a hard gate, not a positive score that can be traded for fewer unknowns. Rank only candidates that already pass NFC/script, morphology, target-sense, register, non-leakage, and translation requirements. Tie-break with immutable candidate hash/ordinal, never provider return timing.

There is no exact in-repo Korean concept extractor for arbitrary frequency sentences. Do not pretend every unrecognized morpheme is known, infer Phase 33 grammar mastery, or claim strict i+1. Inconclusive observed-concept extraction routes the item to review; the stored policy remains `adaptive`.

---

### Bounded Text Candidates, Distinct Repair, and Selection

**Applies to:** `text_generation.py`, `provider_text_adapters.py`, `generate_text_items.py`, `regenerate_text_item.py`, and `provider_response_cache` tests.

**Typed/cache-key pattern** (`provider_response_cache.py:11-42`):

```python
@dataclass(frozen=True, slots=True)
class ProviderCacheKey:
    provider: str
    model: str
    task_type: str
    language: str
    prompt_version: str
    item_key: str | None = None
    prompt_hash: str | None = None

    @classmethod
    def from_prompt(...):
        prompt_hash = hashlib.sha256(_stable_json(prompt).encode("utf-8")).hexdigest()
        return cls(..., task_type=task_type, prompt_hash=prompt_hash)
```

Use the existing `task_type` seam. Initial generation, repair, translation, judge, and definition need distinct task names and prompt versions, for example `sentence_generation`, `sentence_repair`, `translation`, `sentence_judge`, and `definition`. A repair request must also include controlled failed-validation codes and repair attempt identity, so it cannot collide with the initial request even if the lexical candidate is unchanged.

The provider adapter should return a strict bounded list of structured sentence candidates (with a configured hard maximum) rather than one sentence. Parse through Pydantic with `extra="forbid"`, reject missing/extra/malformed candidates individually, canonicalize Korean before cache, and never accept provider-supplied identity or approval fields.

The orchestrator order should be:

```text
generate bounded candidates
  -> deterministic local validation per candidate
  -> Korean adaptive-i+1/quality scoring
  -> translate viable candidate(s)
  -> translation validation + explicit judge route when configured
  -> select deterministic best passing bundle
  -> distinct repair request only if none pass
  -> review-required if repair yields no passing candidate
```

Preserve the current fail-closed Korean identity handoff (`generate_text_items.py:470-500`) and no-Korean-Tatoeba rule (`:427-428`). Strengthen the latter: automatic Tatoeba fallback must be absent from final frequency generation for every language. It may remain an explicitly invoked, provenance-preserving reference/review tool outside the final path.

`RegenerateTextItemService` must delegate to the same candidate/repair selector rather than maintain a second two-call algorithm. This ensures identical cache identities, scoring, telemetry, source-profile limits, and review behavior after regeneration.

---

### Korean Text and Portuguese Quality: `korean_text_quality.py`, `text_validation.py`, and Review Evidence

**Primary analog:** Korean-first target validation plus Latin's frozen Portuguese QA/report shape.

**Korean morphology gate** (`text_validation.py:287-346`):

```python
if context.target_language == KOREAN_LANGUAGE_CODE:
    self._check_korean_target(
        flags,
        sentence_text=context.sentence_text,
        korean_identity=korean_identity,
    )
    return
```

Keep this branch before Japanese/Mandarin/generic matching. The existing matched/mismatch/ambiguous/OOV/unavailable/fingerprint matrix is the GMOR-01 base and must remain fail-closed.

**Frozen QA result pattern** (`latin_translation_quality.py:120-205`):

```python
class LatinPortugueseTranslationQaResult(BaseModel):
    status: LatinPortugueseTranslationQaStatus
    issues: list[LatinPortugueseTranslationQaIssue] = Field(default_factory=list)
    entry_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    review_status_counts: dict[str, int] = Field(default_factory=dict)
```

Create Korean-owned quality contracts rather than putting Seoul speech-level logic into the generic validator. Deterministic checks should cover NFC, Korean/Portuguese language leakage, morphology target match, duplicate/template patterns, configured length, obvious speech-level mixing, and source identity alignment. A typed judge result may assess naturalness, omitted-context invention, sense/register fit, and Korean/Portuguese contradiction, but an LLM result cannot alter source identity or grant human approval.

The text review artifact must first lock the Portuguese regional policy (the current DeepL map defaults `pt` to `PT-BR` at `provider_text_adapters.py:71-93`), accepted standard-Seoul speech-level policy, judge/prompt/scorer versions, reviewer qualification, stratified sample, and exact reviewed hashes. Do not silently inherit Phase 31's unresolved Portuguese policy.

**Review report pattern** (`text_review.py:41-68`):

```python
items = [self._to_item(record) for record in self.text_repository.list_flagged_records(job_id)]
items.sort(key=self._sort_key)
...
return ReviewReportItem(
    job_id=record.job_id,
    item_key=record.item_key,
    example_sentence=redact_sensitive_text(record.example_sentence or "") or None,
    translation_text=redact_sensitive_text(record.translation_text or "") or None,
    validation_flags=[flag.code.value for flag in record.validation_flags],
)
```

Extend the report with controlled candidate-selection/adaptive/judge/review codes and hashes. Do not put prompts, full provider responses, private highlight context, or raw analyzer dumps in review telemetry.

---

### Explicit Provider Routes, Retry, Cache, and Telemetry

**Applies to:** `settings.py`, `runtime.py`, `text_generation.py`, `lexical_grounding.py`, `provider_text_adapters.py`, `audio_synthesis.py`, and `generation_report.py`.

**Composition pattern** (`runtime.py:471-520`): provider construction is centralized and fails on missing credentials or unsupported configured providers. Expand it to task-specific routes rather than calling adapters directly.

**Per-attempt telemetry pattern** (`provider_retry.py:227-254`):

```python
insert(
    ProviderCallLogCreate(
        job_id=context.job_id,
        item_key=context.item_key,
        operation=context.operation,
        provider=context.provider,
        model=context.model,
        voice_id=context.voice_id,
        attempt=attempt,
        latency_ms=latency_ms,
        status=status,
        error_code=error_code,
        error_summary=error_summary,
    )
)
```

Use `operation` as the canonical task route identifier. Every generation, repair, translation, judge, definition, word-audio, sentence-audio, and catalog-discovery attempt must carry the explicit route plus job/item where applicable. Successful calls record stable request/response hashes, tokens, estimated cost, latency, provider/model/voice, attempt, and fallback origin. Cache hits should be reported separately from provider attempts rather than counted as calls.

Pass `job_id` from `GenerateTextItemsService.execute()` into every text operation. Thread item/job context into definition grounding as well. Replace raw `str(exc)` telemetry with `safe_provider_error_summary()` or an equally content-free controlled summary before repository insertion.

Preserve the existing retry/circuit breaker. Do not add broad `except Exception` fallback that changes provider or task invisibly. A route may fallback only when its policy explicitly lists an approved fallback, and provenance/telemetry must identify both sides. Korean production audio has no consumer-TTS fallback.

`generation_report.py` should report per task route: attempts, retries, cache hits, provider/model/voice, fallback count/reason code, latency totals/p95, tokens, estimated cost, and missing telemetry denominator. Report only hashes and controlled identifiers, never prompt/response content.

---

### Live Azure `ko-KR` Qualification and Voice Registry

**Applies to:** Azure voice review/data, `azure_speech_adapter.py`, `audio_voice_registry.py`, `fallback_audio_adapter.py`, CLI, and tests.

**Current live inventory seam** (`azure_speech_adapter.py:49-71`):

```python
request = Request(
    self._voice_inventory_url,
    headers={
        "Ocp-Apim-Subscription-Key": self.settings.azure_speech_key,
        "Accept": "application/json",
    },
    method="GET",
)
with self._urlopen(request, timeout=10) as response:
    payload = json.loads(response.read().decode("utf-8"))
```

Retain validated catalog records—not just a set of IDs—and bind the reviewed machine artifact to the exact catalog payload hash, Azure region, checked-at time, SDK/provider version, `Locale == "ko-KR"`, selected GA `ShortName`, status/type, output format, sample request hashes, sample byte hashes, and human playback decision. Preview/HD novelty is not an approval criterion.

**Fail-closed registry pattern** (`audio_voice_registry.py:154-177`):

```python
plan = _VOICE_REGISTRY.get(language)
if plan is None:
    raise VoiceSelectionError(
        f"No approved Azure voice available for language {language.value}"
    )
```

Keep Korean absent until the exact machine artifact and human review both pass. Then add/load exactly the approved voice and bump the registry version. Do not paste a voice name from documentation or memory merely to make exhaustive tests pass.

`FallbackAudioAdapter` must enforce the Korean route policy: Azure `ko-KR` only unless a later separately qualified provider profile is explicitly approved. Exceptions and unavailable catalog entries fail; they do not silently advance to Google Translate or ElevenLabs.

Live calls belong to an explicit operator checkpoint, never an ordinary unit/integration test. Tests inject catalog JSON and SDK fakes; the review artifact records the separately authorized live evidence.

---

### Exact Audio Evidence, Persistence, Reuse, and Completion

**Applies to:** `domain/audio.py`, `audio_synthesis.py`, `generate_audio_items.py`, `audio_integrity.py`, `audio_repository.py`, DB/migration, export gate, and report.

**Hash-aligned input pattern** (`domain/audio.py:38-51`):

```python
class NormalizedTtsInput(BaseModel):
    display_text: str = Field(min_length=1)
    tts_text: str = Field(min_length=1)
    ssml_text: str | None = None
    text_hash: str | None = None
    ssml_hash: str | None = None

    @model_validator(mode="after")
    def populate_hashes(self) -> "NormalizedTtsInput":
        if self.text_hash is None:
            self.text_hash = _stable_hash(self.tts_text)
        if self.ssml_hash is None:
            self.ssml_hash = _stable_hash(self.ssml_text or self.tts_text)
        return self
```

For Korean, NFC-normalize before these hashes. Preserve distinct display/spoken/SSML values and require the exported word/sentence to match the exact approved input.

**Stronger approval analog** (`korean_foundation_media.py:373-420,565-639`):

```python
artifact_sha256: str | None = Field(default=None, max_length=64)
reviewed_artifact_sha256: str | None = Field(default=None, max_length=64)
metadata_sha256: str | None = Field(default=None, max_length=64)
reviewed_metadata_sha256: str | None = Field(default=None, max_length=64)
review_receipts: tuple[KoreanFoundationMediaReviewReceipt, ...] = Field(...)
...
if self.artifact_sha256 != self.reviewed_artifact_sha256:
    raise ValueError("reviewed artifact hash does not match artifact hash")
```

Extend normal audio provenance with the Phase 32 minimum: language, provider/version, registry version, voice/catalog status/check time, text/SSML hash, output format, artifact byte hash, duration, storage path, review status, reviewed artifact/metadata hash, reviewer role/ID, fallback status/from, and controlled generation/rejection reason.

Calculate `artifact_sha256` from final bytes after synthesis and verify file size/hash before status can become synthesized. Approval is a separate state from provider success. A successful SDK response may produce `synthesized_needs_review`; only hash-aligned reviewed evidence becomes exportable.

**Current completion anti-pattern** (`generate_audio_items.py:93-108`):

```python
for prepared_asset in assets:
    final_asset, reused = self._materialize_asset(prepared_asset)
    self.audio_repository.upsert_audio_asset(final_asset)
    ...
    if final_asset.provenance.status is AudioSynthesisStatus.FAILED:
        result.failed_items += 1

self.job_repository.record_item_success(
    job_id,
    item_key=text_record.item_key,
    completed_stage=JobStage.SYNTHESIZE_AUDIO,
)
```

Record item success only when every required asset for that source schema exists, matches exact text/SSML/provider/voice policy, has valid bytes/hash, is approved, and is not an unapproved fallback. Otherwise record an isolated item failure/review-required state and keep the job resumable.

Reuse identity must include asset kind, NFC text hash, SSML hash, provider/version, voice, locale, registry/policy version, format, artifact hash, and approval binding. Never reuse merely because `voice_id` and text hashes match.

The export quality gate must call exact word and sentence integrity checks, not only count rows. For a Korean production frequency job, missing/unapproved/stale/fallback audio is always blocking; `allow_partial` may create an explicitly non-final diagnostic artifact only if product policy retains that behavior, and it cannot set completed/final status.

Foundation jamo/phonological-rule assets are not generated here. Require the Phase 31 active snapshot/readiness boundary and consume its already reviewed exact bytes.

---

### Persistence and Migration

**Applies to:** domain records, `db/models.py`, text/audio repositories, and the new migration.

**Explicit repository mapping pattern** (`audio_repository.py:38-57`):

```python
payload = {
    "job_id": record.job_id,
    "item_key": record.item_key,
    "asset_kind": record.asset_kind.value,
    "display_text": record.display_text,
    "tts_text": record.normalized_input.tts_text,
    "ssml_text": record.normalized_input.ssml_text,
    "provider": record.provenance.provider.value,
    "voice_id": record.provenance.voice_id,
    "locale": record.provenance.locale,
    "text_hash": record.provenance.text_hash,
    "ssml_hash": record.provenance.ssml_hash,
    "status": record.provenance.status.value,
    "fallback_used": record.provenance.fallback_used,
}
```

Add every new field to domain, ORM, repository write, and repository reload in one plan. Persist text candidate-selection/adaptive/judge evidence as typed JSON; persist frequently gated audio identity/review fields explicitly or as one strictly typed JSON evidence column, but do not leave them only in logs or filenames.

**Additive migration pattern** (`20260804_17_korean_lexical_identity.py:15-23`):

```python
def upgrade() -> None:
    op.add_column(
        "lexical_candidates",
        sa.Column("korean_identity", sa.JSON(), nullable=True),
    )

def downgrade() -> None:
    op.drop_column("lexical_candidates", "korean_identity")
```

Use current head `20260804_17` as `down_revision`. New columns must be nullable or have safe defaults for historical non-Korean rows. Update the sole-head assertion and copy the real upgrade/downgrade/re-upgrade plus ORM parity pattern from `tests/test_migration_schema_parity.py:43-68,106-200`.

---

### Runtime, CLI, and Report Wiring

**Primary analog:** `build_runtime_service()` as the one composition root, and the fixed Korean foundation CLI subapp for controlled scanner-safe operations.

Construct one shared Kiwi service and one explicit provider policy. Inject the same candidate selector/quality service into generation and regeneration. Do not instantiate a second analyzer per candidate, judge, or report.

Provide fixed commands for:

- checking the frequency decision/manifest without writing;
- building/bootstrap curation only after the decision gate;
- validating the frozen 3000/rejection/report chain;
- capturing a live Azure catalog candidate receipt only with explicit operator authorization;
- validating voice/text review evidence;
- running final Korean frequency generation.

Commands should accept constrained versions/actions, not arbitrary Python modules, provider URLs, review roots, or approval booleans. Print aggregate scanner-safe keys (counts, status, versions, hashes, controlled reason codes), not source rows, prompts, Korean sentences, reviewer notes, local absolute paths, credentials, or provider payloads.

`generation_report.py` should add manifest/version/hash, level counts, lexical-resolution counts, rejection reasons, adaptive-i+1 distributions, candidate-selection counts, text quality/review counts, provider-route telemetry, and exact audio approval/fallback counts. Reports prove measurable gates, not linguistic truth by themselves.

## Test Pattern Assignments

### Frozen Frequency and Licensing Tests

**Sources:** `test_frequency_decks.py:191-374`, `test_korean_curriculum.py`, `test_migration_schema_parity.py`.

Cover exact 3000/1000/1000/1000 counts, contiguous ranks, identity uniqueness across levels, NFC, dictionary-form predicates, compound signatures, no particle/ending POS, no unresolved homographs, exact source/license/analyzer fields, manifest/hash drift, rejection accounting, and content-free missing/malformed errors.

Mutate one fact at a time: source hash, license disposition, analyzer version, rank, level, identity POS/sense/signature, duplicate identity, curation code, rejection reason, report total, and attribution hash. Every mutation must fail before candidate persistence or output creation.

Keep an explicit no-side-effect test for an unapproved Korean decision. If redistribution is not approved, assert repository paths remain absent while a configured private frozen asset can be validated.

### Text Selection and Quality Tests

**Cache identity analog** (`tests/services/test_text_generation.py:164-193`): complete Korean identity variants already produce distinct request dumps/cache keys. Add assertions that initial, repair, judge, translation, and definition routes also differ, and that repair failure codes/prompt version alter the key.

**Fail-closed morphology analog** (`tests/services/test_text_validation.py:640-735`): retain the injected matcher matrix and assertions that generic suffix/key paths never run and controlled details omit sentence, lemma, and sense.

Add a bounded-candidate table covering:

- first candidate invalid, later candidate valid and selected;
- multiple valid candidates ordered deterministically by hard quality then adaptive score;
- lower novelty never beats failed naturalness/register/sense/translation;
- same candidates in different provider order yield the same selected immutable identity;
- no passing candidate triggers a distinct cached repair, then review-required;
- wrong sense, English leakage, invented Portuguese subject/context, mixed speech level, unnatural/repetitive Korean, and contradictory translation block;
- Korean final frequency never calls Tatoeba;
- regeneration produces the same routing/scoring semantics and preserves prior evidence history as required by later review work.

Provider/judge tests use strict fake structured responses. Do not mock the Korean morphology positive goldens; continue using the real pinned Kiwi where KNLP/GMOR behavior is under test.

### Provider Policy and Telemetry Tests

**Source:** `tests/services/test_text_generation.py:600-630` already verifies operations, job ID, hash-only telemetry, and per-attempt retry status.

Expand to every task route and assert:

- job/item/task/provider/model-or-voice/attempt/latency/status/request hash/response hash are present;
- token/cost fields are captured when the adapter supplies them and reported with a denominator when absent;
- cache hit is not a provider attempt;
- retries and fallback origin are visible;
- definition and repair no longer bypass telemetry;
- errors contain controlled redacted summaries and never prompt/response/private context;
- missing or forbidden route/fallback fails closed.

### Azure and Audio Tests

**Catalog analog:** `tests/services/test_azure_speech_adapter.py:98-119` injects catalog JSON and proves one cached HTTP call. Extend the fake rows with `Locale`, `Status`, and voice type, preserve the exact payload hash, and reject non-`ko-KR`, preview/unapproved, stale, malformed, duplicate, or drifted selections.

**Current registry gate:** `tests/services/test_audio_voice_registry.py:17-36` proves Korean is absent and fails with `VoiceSelectionError`. Keep that test until qualification evidence exists; then replace it with “Korean resolves only from the exact approved artifact” plus mutations for missing review/hash/catalog voice.

**Foundation exact-media analog:** `tests/services/test_korean_foundation_media.py:371-624` mutates provider, voice, text, SSML, artifact, reviewed hash, rights, and reviewer roles. Copy the applicable exact-text/provider/voice/hash/review cases for frequency word/sentence audio, without copying raw-jamo synthesis.

Add the missing completion regression to `test_generate_audio_items.py`: if either required asset fails, is fallback, stale, or unapproved, `record_item_success` is not called; the failed/review state persists and can be resumed. Test that reuse rejects provider/version/locale/registry/format/hash/review drift.

### Integration and Existing-Mode Tests

**Frequency E2E analog** (`tests/integration/test_frequency_e2e_export_flow.py:81-168`) uses disposable SQLite, fake providers, real repositories, CLI, audio bytes, and all export formats. Its current `monkeypatch.setattr(frequency_decks, "iter_wordlist", ...)` at line 87 is specifically not the new final-runtime pattern. Replace final-path evidence with a temporary hash-bound frozen manifest/asset.

The new Korean integration should:

1. load the approved/fixture frozen Korean manifest without calling `wordfreq`;
2. ingest representative entries from all three levels and persist exact identity/provenance through commit/expire/reload;
3. generate bounded Korean candidates, reject a tempting invalid first candidate, and persist deterministic selected/adaptive evidence;
4. produce context-matched Portuguese definitions/translations through fake routed providers;
5. prove distinct generation/repair/judge/definition/translation telemetry;
6. synthesize fake Azure `ko-KR` word/sentence bytes under an injected approved catalog policy, hash them, apply review evidence, and reload them;
7. prove failed/unapproved/fallback audio blocks item success and final export;
8. verify the generic normal-card field order, blank `Image`, canonical `ko` tags, and preserved level identity without claiming Phase 34 real-subdeck/import/render closure;
9. prove no Tatoeba, consumer TTS, live `wordfreq`, live network, private prompt, or second Kiwi instance is reached;
10. run existing language, Japanese, Mandarin, Latin, phoneme, custom-list, highlight, and Phase 30/31 boundary suites unchanged.

Use fake network/provider boundaries in automated tests. The real approved 3000-row asset can be validated offline as data; live Azure qualification and human linguistic/playback judgments are separate explicit checkpoints.

## Shared Patterns

### Canonical Identity and Source Authority

- Store `ko`; use `ko-KR` only in Azure/catalog/media fields.
- NFC-normalize before identity, cache, text, SSML, artifact, and review hashes.
- Source-backed lemma/POS/sense and the persisted analyzer fingerprint remain immutable authority.
- Deduplicate frequency entries by lemma + normalized POS + source sense, never visible token alone.
- Provider, judge, frequency rank, or surface morphology cannot invent or overwrite source sense.

### Validate and Review Before Promotion

- Legal/source decision before any redistributed asset write.
- Frozen manifest before runtime candidates.
- Deterministic validation before scoring.
- Naturalness/sense/register/translation gate before adaptive ranking.
- Synthesis integrity before audio status.
- Exact human-review hash before audio approval.
- All required approved assets before item success or final export.

### Stable Hashing

Use canonical UTF-8 JSON (`ensure_ascii=False`, sorted keys, compact separators) for structured hashes and raw SHA-256 for artifact bytes. Do not use `repr(payload)` as a long-lived evidence hash. Bind review receipts to both exact content/artifact hash and metadata/policy hash so provider, prompt, scorer, voice, SSML, or review-policy drift invalidates approval.

### Privacy and LLM Security

- Keep current bounded/redacted highlight context and untrusted-data delimiters.
- Never persist or report prompts, provider responses, private excerpts/paths, raw analyzer dumps, credentials, or tracebacks.
- Validate structured provider output with strict typed schemas and bounds.
- Treat provider text as untrusted learner-content candidates, not identity, policy, or approval evidence.
- Errors and telemetry use controlled codes plus hashes only.

### Error Handling

- Missing/malformed/stale/license-blocked asset: fail before persistence or output.
- Ambiguous/OOV/unavailable/fingerprint-drift morphology: review/block; no suffix rescue.
- No passing text candidate or repair: persist review-required; no Tatoeba promotion.
- Provider route unavailable/exhausted: persist isolated failure; no invisible provider switch.
- Missing/unapproved/fallback/stale audio: no audio-stage success and no final export.
- Human approval cannot override a structurally invalid asset, false identity, failed quality gate, or byte/hash mismatch.

### Authentication / Authorization

No HTTP controller or authentication layer exists for this work; the interface is a local operator CLI. The effective guards are fixed commands, explicit live-call authorization, configured credentials, immutable manifests, qualified reviewer identities, and fail-before-write validation. Do not add a web auth surface in Phase 32.

### Existing-Mode Isolation

- Keep generic/Japanese/Mandarin/Latin/foundation templates and fields unchanged; Korean frequency reuses `normal_card.md` and keeps `Image` blank.
- Keep Phase 31 source/review/media/snapshot artifacts immutable; consume only its active readiness boundary.
- Do not change Japanese/Chinese matching or generic suffix behavior except to prevent it from being used when a required language adapter is inconclusive in final frequency acceptance.
- Do not add Google Translate consumer TTS or unqualified ElevenLabs as Korean production fallback.
- Do not add final Korean grammar/personal-source behavior (Phase 33) or claim final APKG subdeck/import/visual evidence (Phase 34).

## No Exact Analog Found

| File / Surface | Role | Data Flow | Why No Exact Analog Exists | Planner Instruction |
|---|---|---|---|---|
| `assets/frequency/ko/curated-v1.csv` and source decision | data/review evidence | file-I/O, batch, event-driven | No approved Korean source, attribution, or redistribution disposition exists; current assets are token/lemma CSVs with weak POS/sense data. | Start with the human/legal decision. Do not fabricate content or commit the path until approved. |
| `korean_frequency.py` adaptive concept evidence | service/model | transform, batch | Foundation code validates strict explicit graphs; no code extracts and scores observed Korean concepts from arbitrary frequency sentences. | Research/lock a versioned extractor and conservative unknown policy; naturalness remains a hard gate. |
| `korean_text_quality.py` semantic/naturalness checks | service | transform, request-response | Existing validation catches structural issues but cannot prove Seoul naturalness, intended sense, context fidelity, speech-level consistency, or translation entailment. | Combine deterministic gates, typed judge routing, and qualified hash-bound review; never auto-approve from an LLM. |
| `data/korean_audio/azure-ko-KR-v1.json` and voice review | model/review evidence | request-response, event-driven | The adapter can list IDs, but no live-discovered, playback-reviewed Korean voice receipt exists. | Perform an explicitly authorized live catalog/sample checkpoint and bind the exact reviewed voice/bytes/metadata hashes before registry activation. |

## Planner Guardrails

1. Plan source/license disposition before creating a Korean frequency directory or touching `wordfreq` output.
2. Treat Phase 31 activation/readiness as a dependency, not a fixture to copy into production.
3. Keep one canonical typed Korean frequency entry and one manifest/hash chain; do not split truth across CSV notes, provider prompts, and ad hoc reports.
4. Remove final-runtime live `wordfreq` and seed-grounding fallbacks before claiming GLEX-01.
5. Persist trusted POS/sense/source/version/confidence before any provider text request.
6. Generate a bounded candidate set, validate first, score second, and repair under a distinct cache/task identity.
7. Keep Tatoeba out of automatic final frequency generation.
8. Route definition/generation/repair/translation/judge/audio explicitly and pass job/item context to telemetry.
9. Qualify the exact Azure voice from a live catalog with human playback; do not guess or auto-select preview/HD voices.
10. Separate synthesis success from reviewed approval; hash final bytes and block failed/unapproved/fallback assets.
11. Never record audio item success unless all required assets are approved and exact-text aligned.
12. Use one additive migration and prove real Alembic/ORM/repository round trips.
13. Keep automated tests offline and deterministic; record live/human facts only through explicit review artifacts.
14. Preserve `ko`, NFC, Phase 30 morphology authority, Phase 31 immutable foundations, existing modes, blank `Image`, and the current normal-card schema.
15. Build and structurally verify the real Korean parent/Level 1/2/3 package in Phase 32; reserve generalized all-family and observed Anki import/render/playback claims for Phase 34.

## Metadata

**Analog search scope:** `.planning/SPEC.md`, `.planning/ROADMAP.md`, `KOREAN-STRUCTURE.md`, Phase 30/31 approach/research/pattern/summary/verification handoffs, `assets/frequency`, `data/latin_mvp`, `data/korean_foundations`, `scripts`, `src/multilang/domain`, `src/multilang/services`, `src/multilang/repositories`, `src/multilang/runtime.py`, `src/multilang/cli.py`, Alembic migrations, and focused domain/service/repository/CLI/integration tests.

**Primary precedents:** generic frozen frequency CSV validation; Phase 30 Korean source-backed morphology identity; Phase 31 immutable curriculum/review/media snapshots; deterministic Tatoeba filter/score mechanics only; Latin frozen Portuguese QA; typed provider cache/retry/telemetry; Azure live catalog seam; strict normal-audio integrity and export gates.

**Files indexed:** 100+ source/test/data/planning paths; 35+ high-leverage artifacts directly read in this mapping continuation in addition to the prior Phase 30/31 context.

**Pattern extraction date:** 2026-08-21.

**Worktree policy:** This mapping writes only this `32-PATTERNS.md`. Existing dirty planning-state files are pre-existing and must not be modified, reset, staged, or committed by the planner.
