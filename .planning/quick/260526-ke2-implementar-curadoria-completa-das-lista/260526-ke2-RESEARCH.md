# Quick Task 260526-ke2: Curadoria de frequência, telemetria de providers, retry/backoff/circuit breaker - Research

**Researched:** 2026-05-26  
**Domain:** Python generation pipeline, frequency-list assets, provider observability/resilience  
**Confidence:** HIGH for codebase inventory; MEDIUM for minimal design choices

## Summary

The requested task should be implemented as an incremental hardening of the existing Python/SQLAlchemy runtime, not as a PostgreSQL/queue migration. [VERIFIED: codebase read `AGENTS.md`, `.planning/PROJECT.md`, `src/multilang/runtime.py`] The current frequency-deck path still derives candidates directly from `wordfreq` at runtime through `src/multilang/services/frequency_decks.py`, with only lightweight token filtering, deterministic level windows, and backfill. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] The Polish generation analysis explicitly identifies raw `wordfreq` use, poor tokens, duplicated words, provider observability gaps, and retry without real backoff as root causes. [VERIFIED: codebase read `docs/polish-deck-generation-analysis-2a7473ce.md`]

Primary recommendation: add a small asset-backed curation layer plus a provider-call logging/resilience boundary around existing provider adapters, reusing the current DB/session and report wiring. [VERIFIED: codebase read `src/multilang/db/models.py`, `src/multilang/services/text_generation.py`, `src/multilang/services/audio_synthesis.py`, `src/multilang/services/generation_report.py`] Do not introduce queue workers, Redis, or a PostgreSQL-only assumption for this quick task because the user explicitly requested the minimal approach without PostgreSQL/queue migration. [VERIFIED: user request]

## User Constraints

- Implementar curadoria completa das listas de frequência para todas as línguas suportadas. [VERIFIED: user request]
- Implementar telemetria estruturada por chamada de provider com custo/tokens/latência. [VERIFIED: user request]
- Implementar retry/backoff/circuit breaker robusto para providers. [VERIFIED: user request]
- Validar com testes e registrar artefatos GSD. [VERIFIED: user request]
- Minimal implementation must avoid PostgreSQL/queue migration. [VERIFIED: user request]

## Project Constraints (from AGENTS.md)

- v1 supported languages are Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch. [VERIFIED: codebase read `AGENTS.md`]
- Frequency decks must be separated into 3 levels with 1000 cards per level. [VERIFIED: codebase read `AGENTS.md`]
- Example sentences and translations must be high quality; prior low-quality Tatoeba output is a known concern. [VERIFIED: codebase read `AGENTS.md`]
- Audio should use Azure TTS if required voices are available. [VERIFIED: codebase read `AGENTS.md`]
- Generated deck field set and formatting must remain consistent for Anki export usefulness. [VERIFIED: codebase read `AGENTS.md`]
- The codebase must follow architecture/good practices with tests and fallbacks. [VERIFIED: codebase read `AGENTS.md`]
- Do not leak sensitive WebDAV credentials, raw highlight exports, book metadata, private reading text, paths, prompts, reports, artifacts, or commits. [VERIFIED: codebase read `.planning/STATE.md`]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Curated frequency lists | Python service/assets | SQLite/SQLAlchemy persistence | Runtime already ingests frequency candidates through Python services and persists grounded lexical candidates. [VERIFIED: codebase read `src/multilang/services/ingest_lexical_items.py`, `src/multilang/repositories/lexical_repository.py`] |
| Provider telemetry | Python provider boundary | SQLAlchemy model + report writer | Provider calls currently pass through text/audio service boundaries before data is persisted and reported. [VERIFIED: codebase read `src/multilang/services/text_generation.py`, `src/multilang/services/audio_synthesis.py`, `src/multilang/services/generation_report.py`] |
| Retry/backoff/circuit breaker | Python provider boundary | Job repository for blocked status | `provider_retry.py` is already the retry boundary and `JobStatus.BLOCKED` already exists. [VERIFIED: codebase read `src/multilang/services/provider_retry.py`, `src/multilang/domain/jobs.py`] |
| Final evidence/tests | pytest | GSD artifact markdown/JSON | Existing targeted evidence uses pytest and GSD quick directories. [VERIFIED: codebase read tests list and `.planning/STATE.md`] |

## Current Codebase Inventory

### 1. Frequency lists/assets: defined, generated, loaded, validated, tested

| Area | Current implementation | Finding |
|------|------------------------|---------|
| Supported languages | `SupportedLanguage` enum and `DEFAULT_SUPPORTED_LANGUAGES` include `pt/es/en/fr/de/it/pl/tr/ro/ru/nl`. [VERIFIED: codebase read `src/multilang/domain/jobs.py`, `src/multilang/settings.py`] | Use these as the canonical language set. [VERIFIED: codebase read `src/multilang/domain/jobs.py`] |
| Candidate source | `iter_curated_frequency_candidates()` enumerates `wordfreq.iter_wordlist(language.value)` and stops at `scan_limit`. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] | Despite the name, this is runtime bootstrap filtering, not frozen full curation. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] |
| Current filters | `_is_curated_token()` rejects empty, digits, `http/https/www/nbsp`, dots, uppercase tokens, bad punctuation, and non-letter-only tokens except internal apostrophe/hyphen. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] | It does not validate language script, foreign words, brands/entities, abbreviations, curated approval, or rejection reasons. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] |
| Leveling | `LEVEL_WINDOWS` maps levels 1/2/3 to ranks 1-1000/1001-2000/2001-3000. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] | Preserve this contract. [VERIFIED: codebase read `AGENTS.md`, `src/multilang/services/frequency_decks.py`] |
| Backfill/dedup | `build_frequency_deck()` deduplicates selected lemma keys across levels; `build_frequency_level()` backfills beyond the window if needed. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] | Dedup is by raw casefolded token/lemma key, not by curated lemma with POS/source metadata. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`] |
| Ingestion | `_ingest_frequency_deck()` builds requested item keys and calls `_build_grounded_frequency_level()`, which repeatedly calls `build_frequency_level()` and grounds candidates. [VERIFIED: codebase read `src/multilang/services/ingest_lexical_items.py`] | The integration point for frozen assets is before `_build_grounded_frequency_level()` creates candidates. [VERIFIED: codebase read `src/multilang/services/ingest_lexical_items.py`] |
| Lexical grounding | `LexicalGroundingService` looks up `.multilang/lexicon/{language}/lexical-index.json`; with `allow_frequency_seed_fallback=True`, missing indexes can produce seed fallback records from `wordfreq`. [VERIFIED: codebase read `src/multilang/services/lexical_grounding.py`, `src/multilang/services/lexical_lookup.py`, `src/multilang/runtime.py`] | For curated production decks, avoid relying on seed fallback as proof of lexical quality. [VERIFIED: codebase read `docs/generation-process-improvement-plan.md`] |
| Frozen assets | No `data/` assets and no committed frequency asset files were found by glob; only `frequency_decks.py` and tests reference frequency assets. [VERIFIED: codebase glob `data/**/*`, `**/*frequency*`] | Add project-owned asset files. [VERIFIED: codebase glob `data/**/*`, `**/*frequency*`] |
| Tests | `tests/services/test_frequency_decks.py` covers noise filtering, order, three full levels, backfill, and cross-level dedup. [VERIFIED: codebase read `tests/services/test_frequency_decks.py`] | Extend these tests rather than replacing them. [VERIFIED: codebase read `tests/services/test_frequency_decks.py`] |

### 2. Current provider adapter/runtime architecture

| Provider area | Current implementation | Finding |
|---------------|------------------------|---------|
| Text generation | `TextGenerationService` calls `_sentence_adapter.generate_sentence()` and `_translation_adapter.translate_sentence()` via `retry_provider_call()`, with optional provider response cache. [VERIFIED: codebase read `src/multilang/services/text_generation.py`] | This is the best place to log LLM and translation provider calls. [VERIFIED: codebase read `src/multilang/services/text_generation.py`] |
| LLM adapter | `LiteLLMSentenceAdapter` calls `litellm.completion()` for sentence and definition generation and returns provenance with provider/model. [VERIFIED: codebase read `src/multilang/services/provider_text_adapters.py`] | Response usage/tokens are not extracted today. [VERIFIED: codebase read `src/multilang/services/provider_text_adapters.py`] |
| Translation adapters | DeepL, Google Translate, and `FallbackTranslationAdapter` exist; fallback provenance stores fallback origin/reason. [VERIFIED: codebase read `src/multilang/services/provider_text_adapters.py`] | Fallback is visible in provenance but not normalized as per-call telemetry. [VERIFIED: codebase read `src/multilang/services/provider_text_adapters.py`] |
| Audio | `AudioSynthesisService` prepares WORD/SENTENCE assets and calls `adapter.synthesize()`; Azure/ElevenLabs/fallback adapters exist. [VERIFIED: codebase read `src/multilang/services/audio_synthesis.py`, `src/multilang/runtime.py`] | This is the best place to log TTS provider calls. [VERIFIED: codebase read `src/multilang/services/audio_synthesis.py`] |
| Audio provenance | `AudioAssetModel` persists provider, voice, locale, format, hashes, byte size, duration, status, and fallback flag. [VERIFIED: codebase read `src/multilang/db/models.py`] | Audio provenance is asset-level, not attempt-level. [VERIFIED: codebase read `src/multilang/db/models.py`] |
| Final report | `generation_report.py` summarizes counts, level counts, export status/hash, and provider counts from text/audio provenance. [VERIFIED: codebase read `src/multilang/services/generation_report.py`] | It does not include latency, retries, tokens, or cost today. [VERIFIED: codebase read `src/multilang/services/generation_report.py`] |

### 3. Current telemetry/cost/token/latency/retry/circuit support

| Feature | Exists? | Evidence |
|---------|---------|----------|
| Provider response cache | Yes | `provider_response_cache` table/model/service stores normalized responses keyed by provider/model/task/language/item/prompt hash/version. [VERIFIED: codebase read `src/multilang/db/models.py`, `src/multilang/repositories/text_repository.py`] |
| Per-call provider telemetry table | No | No `provider_call_logs` model/repository was found; only response cache and provenance fields exist. [VERIFIED: codebase grep `provider_response_cache|latency_ms|estimated_cost|tokens|structlog`] |
| Latency tracking | Partial/no | `GenerateTextItemsService` tracks progress elapsed seconds but provider-call latency is not persisted. [VERIFIED: codebase read `src/multilang/services/generate_text_items.py`; codebase grep `latency_ms`] |
| Token/cost tracking | No | No token/cost persistence was found. [VERIFIED: codebase grep `estimated_cost|tokens`] |
| Retry | Partial | `retry_provider_call()` retries temporary 403/429/timeout/network errors but default `wait_seconds=0.0`. [VERIFIED: codebase read `src/multilang/services/provider_retry.py`] |
| Backoff/jitter | No | `retry_provider_call()` sleeps a fixed `wait_seconds` only when positive; no exponential backoff or jitter exists. [VERIFIED: codebase read `src/multilang/services/provider_retry.py`] |
| Retry-After support | No | No response/header extraction exists in `provider_retry.py`. [VERIFIED: codebase read `src/multilang/services/provider_retry.py`] |
| Circuit breaker | No | No circuit state/model/function was found; only `JobStatus.BLOCKED` exists as a status value. [VERIFIED: codebase read `src/multilang/services/provider_retry.py`, `src/multilang/domain/jobs.py`] |

## Minimal Implementation Approach

### A. Frequency curation without PostgreSQL/queue migration

1. Add versioned CSV fixtures under `assets/frequency/{language}/curated-v1.csv` and `assets/frequency/{language}/rejections-v1.csv`. [ASSUMED]  
   - Use fields: `language,frequency_list_version,level,rank,source_rank,display_form,lemma,lemma_key,part_of_speech,definition_seed,source_provenance,curation_flags`. [VERIFIED: codebase read `docs/generation-process-improvement-plan.md`]
   - For this quick task, seed minimal synthetic/curated fixture rows in tests and require the production loader to fail clearly if a full 3000-row asset is absent, unless explicit fallback/test mode is used. [ASSUMED]

2. Refactor `frequency_decks.py` into an asset-first API. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`]  
   - Add `CuratedFrequencyEntry` dataclass/Pydantic model and `load_curated_frequency_entries(language, version='v1', assets_dir=...)`. [ASSUMED]
   - Make `build_frequency_level()` load frozen entries and only use `wordfreq` bootstrap when an explicit `allow_frequency_seed_fallback`/test path is passed. [ASSUMED]
   - Preserve `LEVEL_WINDOWS`, `required_count_per_level`, item keys, and `frequency_rank/frequency_level` values. [VERIFIED: codebase read `src/multilang/services/frequency_decks.py`, `src/multilang/services/ingest_lexical_items.py`]

3. Add validation helpers in `frequency_decks.py` or new `frequency_curation.py`. [ASSUMED] Required checks: supported language, exactly 3000 rows for full production asset, exactly 1000 per level, no duplicate `lemma_key` across levels, no duplicate `display_form` casefolded per language, ranks contiguous by level, source ranks positive, non-empty provenance, and rejection rows with reason codes. [VERIFIED: codebase read `docs/generation-process-improvement-plan.md`]

4. Wire settings with `frequency_assets_dir: Path = Path('assets/frequency')` and `frequency_list_version: str = 'v1'`. [ASSUMED] Settings already centralize runtime paths and provider config. [VERIFIED: codebase read `src/multilang/settings.py`]

### B. Provider telemetry with existing DB/session

1. Add `ProviderCallLogModel` to `src/multilang/db/models.py` and a migration under `alembic/versions/`. [VERIFIED: codebase read `src/multilang/db/models.py`, alembic versions glob]  
   Minimum columns from the plan: `id, job_id nullable, item_key, task_type, provider, model, attempt, latency_ms, status, error_code, error_summary, fallback_from, prompt_hash, response_hash, input_tokens, output_tokens, total_tokens, estimated_cost, created_at`. [VERIFIED: codebase read `docs/generation-process-improvement-plan.md`]

2. Add `ProviderCallLogger` / repository service. [ASSUMED] It should accept a `ProviderCallContext(job_id, item_key, task_type, provider, model, prompt_hash)` and write one row per attempt with redacted errors. [VERIFIED: codebase read `src/multilang/security/redaction.py`, `src/multilang/services/provider_retry.py`]

3. Thread context through existing service calls. [VERIFIED: codebase read `src/multilang/services/generate_text_items.py`, `src/multilang/services/text_generation.py`, `src/multilang/services/audio_synthesis.py`]  
   - Text: pass `job_id` and `item_key` from `GenerateTextItemsService.execute()` into `TextGenerationService.generate_bundle()`. [VERIFIED: codebase read `src/multilang/services/generate_text_items.py`, `src/multilang/services/text_generation.py`]  
   - Definition/pronunciation during lexical grounding currently lacks item context; for minimal scope, log task type `definition`/`pronunciation` with best available language/lemma and nullable job/item, or extend grounding calls later. [VERIFIED: codebase read `src/multilang/services/lexical_grounding.py`]  
   - Audio: pass `job_id/item_key/asset_kind` from prepared asset into the logging wrapper in `AudioSynthesisService.synthesize_prepared_asset()`. [VERIFIED: codebase read `src/multilang/services/audio_synthesis.py`]

4. Extend `generation_report.py` to query provider call logs and summarize calls, attempts, latency totals/p95, status counts, token totals, estimated cost by provider/task, fallback counts, and circuit breaker blocks. [ASSUMED] Existing report writer already receives job/export/text/audio state and emits JSON/Markdown. [VERIFIED: codebase read `src/multilang/services/generation_report.py`]

### C. Retry/backoff/circuit breaker

1. Replace fixed-zero retry with exponential backoff + jitter in `provider_retry.py`. [VERIFIED: codebase read `src/multilang/services/provider_retry.py`]  
   Recommended deterministic signature: `retry_provider_call(operation, attempts, base_delay_seconds, max_delay_seconds, jitter_ratio, sleeper, monotonic, call_logger, circuit_breaker, context)`. [ASSUMED]

2. Add error classification object: `rate_limited` for 429/quota, `temporary_forbidden` for 403/unusual behavior, `timeout`, `network_error`, `server_error`, `permanent`. [VERIFIED: codebase read `docs/generation-process-improvement-plan.md`, `src/multilang/services/provider_retry.py`]

3. Respect `Retry-After` if the exception exposes headers/response. [ASSUMED] Current adapters expose heterogeneous exceptions, so implement best-effort helpers using `getattr(exc, 'response', None)`, `getattr(response, 'headers', {})`, and direct `headers` attributes. [ASSUMED]

4. Add in-memory `ProviderCircuitBreaker` keyed by provider/model/task with states closed/open/half_open and cooldown. [ASSUMED] This avoids DB/global service migration while preventing immediate retry storms within the current process. [VERIFIED: user request minimal without PostgreSQL/queue migration]

5. When a circuit opens or provider blocking/quota is classified as blocking, surface a `ProviderCircuitOpenError`/`ProviderBlockedError` to runtime; update job status to `blocked` where the orchestration catches generation failures. [ASSUMED] `JobStatus.BLOCKED` already exists and `JobRepository.update_job_status()` can persist it. [VERIFIED: codebase read `src/multilang/domain/jobs.py`, `src/multilang/repositories/job_repository.py`]

## Specific Files Likely Needing Changes

| File | Change |
|------|--------|
| `src/multilang/services/frequency_decks.py` | Asset loader, `CuratedFrequencyEntry`, validation, explicit fallback mode, rejection reason support. [VERIFIED: codebase read] |
| `src/multilang/settings.py` | Add frequency asset/version settings plus retry/backoff/circuit config knobs. [VERIFIED: codebase read] |
| `assets/frequency/{lang}/curated-v1.csv` | New frozen curated lists for 11 languages. [ASSUMED] |
| `assets/frequency/{lang}/rejections-v1.csv` | New rejection audit files for 11 languages. [ASSUMED] |
| `src/multilang/services/ingest_lexical_items.py` | Use asset-first frequency builder and preserve existing item keys/level counts. [VERIFIED: codebase read] |
| `src/multilang/db/models.py` | Add `ProviderCallLogModel`; optionally relationship from `GenerationJob`. [VERIFIED: codebase read] |
| `alembic/versions/<date>_provider_call_logs.py` | Add migration for provider-call logs. [VERIFIED: alembic versions glob] |
| `src/multilang/repositories/provider_call_log_repository.py` | New repository for telemetry writes/listing. [ASSUMED] |
| `src/multilang/services/provider_retry.py` | Add classification, exponential backoff, jitter, Retry-After, circuit breaker, attempt logging hooks. [VERIFIED: codebase read] |
| `src/multilang/services/text_generation.py` | Thread context and call retry/log wrapper for sentence/translation. [VERIFIED: codebase read] |
| `src/multilang/services/provider_text_adapters.py` | Extract LiteLLM usage metadata when present; expose provider/model consistently. [VERIFIED: codebase read] |
| `src/multilang/services/audio_synthesis.py` | Log TTS attempts and latency around `adapter.synthesize()`. [VERIFIED: codebase read] |
| `src/multilang/runtime.py` | Construct provider-call logger/circuit breaker; pass to text/audio services; include logs in report. [VERIFIED: codebase read] |
| `src/multilang/services/generation_report.py` | Include provider-call summaries with cost/tokens/latency/retries. [VERIFIED: codebase read] |

## Tests Likely Needing Changes

| Test file | Coverage to add |
|-----------|-----------------|
| `tests/services/test_frequency_decks.py` | Asset load success, missing asset failure, 1000-per-level validation, cross-level duplicate rejection, rejection reason parsing, explicit fallback only. [VERIFIED: codebase read] |
| `tests/integration/test_frequency_e2e_export_flow.py` | Frequency ingestion uses frozen curated assets and still exports exact expected counts in test mode. [VERIFIED: codebase read] |
| `tests/services/test_provider_retry.py` | Exponential backoff sequence, jitter bounded with injected RNG, Retry-After precedence, 403/429 classification, circuit open/half-open behavior, redacted errors. [VERIFIED: codebase read] |
| `tests/services/test_provider_text_adapters.py` | LiteLLM usage extraction into metadata/provenance and fallback telemetry fields. [VERIFIED: codebase read] |
| `tests/services/test_text_generation.py` | Provider-call logger receives sentence and translation attempts with prompt/response hashes and latency. [VERIFIED: codebase read] |
| `tests/services/test_audio_synthesis.py` | TTS call logging on success/failure with latency, provider, model/voice, error summary. [VERIFIED: codebase read] |
| `tests/services/test_generation_report.py` or existing integration test | Report includes provider cost/tokens/latency/retries. [VERIFIED: codebase read `src/multilang/services/generation_report.py`, existing report assertions in `tests/integration/test_frequency_e2e_export_flow.py`] |
| `tests/repositories/test_provider_call_log_repository.py` | Insert/list/summarize provider-call logs. [ASSUMED] |

## Don't Hand-Roll / Avoid

| Problem | Don't build | Use instead |
|---------|-------------|-------------|
| Production frequency decks | Do not keep using live `wordfreq` as final source. [VERIFIED: docs read] | Frozen curated CSV assets plus validation. [VERIFIED: docs read] |
| Provider observability | Do not infer latency/cost from final provenance only. [VERIFIED: codebase read `generation_report.py`] | Per-attempt `provider_call_logs`. [VERIFIED: docs read] |
| Retry loops | Do not retry immediate 403/429 with `wait_seconds=0.0`. [VERIFIED: codebase read `provider_retry.py`] | Exponential backoff + Retry-After + circuit breaker. [VERIFIED: docs read] |
| Secrets in telemetry | Do not persist raw prompts, private highlight text, API keys, tracebacks, or full provider errors. [VERIFIED: codebase read `.planning/STATE.md`, `src/multilang/security/redaction.py`] | Prompt/response hashes and redacted summaries. [VERIFIED: docs read] |

## Validation Architecture

| Property | Value |
|----------|-------|
| Framework | pytest. [VERIFIED: codebase glob `tests/**/*.py`] |
| Quick run command | `uv run python -m pytest tests/services/test_frequency_decks.py tests/services/test_provider_retry.py -q` [ASSUMED] |
| Integration run command | `uv run python -m pytest tests/integration/test_frequency_e2e_export_flow.py -q` [ASSUMED] |
| Config | No pytest config file was inspected in this research; existing tests are under `tests/`. [VERIFIED: codebase glob `tests/**/*.py`] |

Wave 0 gaps: add tests for curated asset loading/validation, provider call log repository, telemetry summary in report, and circuit breaker state transitions before changing runtime behavior. [ASSUMED]

## Common Pitfalls

1. Treating `wordfreq` filtering as “complete curation” will preserve known bad tokens and foreign homographs. [VERIFIED: docs read `docs/polish-deck-generation-analysis-2a7473ce.md`]
2. Logging full prompts/responses would violate existing privacy decisions for highlight/private reading text. [VERIFIED: codebase read `.planning/STATE.md`]
3. Adding telemetry only to text adapters would miss Azure/ElevenLabs TTS calls. [VERIFIED: codebase read `src/multilang/services/audio_synthesis.py`, `src/multilang/runtime.py`]
4. A process-local circuit breaker will not protect multiple processes, but it satisfies the quick-task “no queue/PostgreSQL migration” constraint better than a distributed design. [ASSUMED]
5. Full production curation for all 11 languages requires real asset content review; tests can validate structure, but cannot prove linguistic quality alone. [ASSUMED]

## Open Questions

1. Should this quick task commit full 3000-row production CSVs for all 11 languages, or implement the loader/validator with small fixtures and fail-fast placeholders until human curation is supplied? [ASSUMED]
2. What price table should be used for estimated cost per provider/model? The codebase has no pricing source today. [VERIFIED: codebase grep `estimated_cost|tokens`]
3. Should Google Translate remain a configured fallback after prior `Error 500` acceptance, or be disabled for final frequency decks? [VERIFIED: docs read `docs/generation-process-improvement-plan.md`]

## Assumptions Log

| # | Claim | Risk if Wrong |
|---|-------|---------------|
| A1 | Add frequency assets under `assets/frequency/...`. | Repo may prefer another asset root. |
| A2 | Use fail-fast production loader if full curated assets are absent. | User may expect full curated lists generated in this quick task. |
| A3 | Add a new provider-call repository/service. | Existing repository style may prefer extending `TextRepository`. |
| A4 | Use in-memory circuit breaker for minimal scope. | Long-running/multi-process generation may need persisted breaker state. |
| A5 | Suggested pytest commands use `uv run`. | Local environment may run tests via another command. |

## Sources

### Primary (HIGH confidence)
- `AGENTS.md` — project constraints. [VERIFIED: codebase read]
- `.planning/STATE.md`, `.planning/PROJECT.md` — current state and decisions. [VERIFIED: codebase read]
- `docs/generation-process-improvement-plan.md` — requested improvement plan, including telemetry/retry/curation requirements. [VERIFIED: codebase read]
- `docs/polish-deck-generation-analysis-2a7473ce.md` — root-cause evidence for Polish deck failures. [VERIFIED: codebase read]
- `src/multilang/services/frequency_decks.py`, `ingest_lexical_items.py`, `lexical_grounding.py` — frequency/lexical runtime. [VERIFIED: codebase read]
- `src/multilang/services/text_generation.py`, `provider_text_adapters.py`, `audio_synthesis.py`, `provider_retry.py` — provider runtime. [VERIFIED: codebase read]
- `src/multilang/db/models.py`, repositories, `generation_report.py` — persistence/reporting. [VERIFIED: codebase read]

### Secondary
- Existing tests listed/read under `tests/`. [VERIFIED: codebase glob/read]

## Metadata

**Confidence breakdown:**
- Frequency inventory: HIGH — direct code/doc inspection. [VERIFIED: codebase read]
- Provider inventory: HIGH — direct code/doc inspection. [VERIFIED: codebase read]
- Minimal design: MEDIUM — implementation pattern is consistent with current code but asset path and pricing policy need user confirmation. [ASSUMED]

**Research date:** 2026-05-26  
**Valid until:** 2026-06-02
