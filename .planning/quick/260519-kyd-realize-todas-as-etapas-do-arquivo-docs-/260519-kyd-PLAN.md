---
quick_id: 260519-kyd
type: quick
autonomous: true
source_requirements:
  - docs/ai-generation-improvement-prompts.md#etapa-4-through-etapa-11
files_modified:
  - src/multilang/cli.py
  - src/multilang/runtime.py
  - src/multilang/db/models.py
  - src/multilang/services/text_generation.py
  - src/multilang/services/generate_text_items.py
  - src/multilang/services/generate_audio_items.py
  - src/multilang/services/assemble_export_cards.py
  - src/multilang/repositories/text_repository.py
  - src/multilang/repositories/export_repository.py
  - src/multilang/services/provider_response_cache.py
  - src/multilang/services/provider_retry.py
  - src/multilang/services/polish_function_words.py
  - src/multilang/services/batch_text_generation.py
  - tests/cli/test_generate_command.py
  - tests/cli/test_export_command.py
  - tests/services/test_generate_text_items.py
  - tests/services/test_generate_audio_items.py
  - tests/services/test_text_generation.py
  - tests/services/test_provider_response_cache.py
  - tests/services/test_provider_retry.py
  - tests/services/test_polish_function_words.py
  - tests/services/test_batch_text_generation.py
---

# Quick Plan: Implementar Etapas 4-11 de melhorias de geração

<objective>
Implementar somente as Etapas 4 a 11 de `docs/ai-generation-improvement-prompts.md`: backoff, refresh de snapshots no export, comando separado de reparo, function words de polonês, cache de provider, comando separado de áudio, concorrência controlada e batch generation.

Purpose: tornar o fluxo de geração robusto para retomar jobs longos sem corromper progresso salvo, sem vazar payloads sensíveis e mantendo export/audio/text repair desacoplados.
Output: mudanças pequenas e testadas nos comandos e serviços existentes, com testes focados por área.
</objective>

<context>
@.planning/STATE.md
@AGENTS.md
@docs/ai-generation-improvement-prompts.md
@src/multilang/cli.py
@src/multilang/runtime.py
@src/multilang/services/generate_text_items.py
@src/multilang/services/generate_audio_items.py
@src/multilang/services/text_generation.py
@src/multilang/services/assemble_export_cards.py
@src/multilang/repositories/text_repository.py
@src/multilang/repositories/export_repository.py

STATE.md drift risk: full `python -m pytest -q` has known broad-suite collection drift from removed private runtime template adapters. Use focused tests below as authoritative for this quick task, and report if broad-suite drift still blocks full-suite execution.
</context>

<source_audit>
Covered source items from `docs/ai-generation-improvement-prompts.md`:
- Etapa 4 Backoff em Erro Temporario: Task 1.
- Etapa 5 `--refresh-snapshots` no Export: Task 2.
- Etapa 6 Separar Reparo de Texto: Task 2.
- Etapa 7 Function Words de Polones: Task 1.
- Etapa 8 Cache de Provider: Task 1.
- Etapa 9 Audio Separado: Task 2.
- Etapa 10 Concorrencia Controlada: Task 3.
- Etapa 11 Batch Generation: Task 3.

Explicit exclusions: do not implement Etapas 1-3, do not alter card templates in Etapa 5, do not expand function-word fixed data beyond Polish in Etapa 7, and do not add unrelated providers/features.
</source_audit>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Provider resilience, Polish function words, and provider cache</name>
  <files>src/multilang/services/provider_retry.py, src/multilang/services/provider_response_cache.py, src/multilang/services/polish_function_words.py, src/multilang/services/text_generation.py, src/multilang/services/generate_text_items.py, src/multilang/services/lexical_grounding.py, src/multilang/db/models.py, src/multilang/runtime.py, tests/services/test_provider_retry.py, tests/services/test_provider_response_cache.py, tests/services/test_polish_function_words.py, tests/services/test_text_generation.py, tests/services/test_generate_text_items.py</files>
  <behavior>
    - Etapa 4: fake provider failing with temporary 403, 429, timeout, or network error is retried after a small deterministic wait and succeeds without losing already saved item progress.
    - Etapa 4: exhausted attempts records a clear redacted failure; messages must not include API keys, raw prompts, card payloads, sentences, translations, or highlights.
    - Etapa 7: Polish words `w`, `i`, `nie`, `do`, `to`, `jak`, `co`, `czy` use small versioned local definitions/POS/IPA before provider calls; other Polish words keep existing fallback/provider behavior.
    - Etapa 8: identical provider/model/task_type/language/item_key-or-prompt-hash/prompt_version calls reuse persisted normalized responses and metadata; changing prompt_version naturally misses cache.
  </behavior>
  <action>Create retry/backoff and cache boundaries instead of embedding ad-hoc loops in adapters. Treat temporary provider errors exactly as: temporary 403, 429, timeout, and network error. Use a constant small attempt limit unless an existing settings pattern clearly supports configuration. Sanitize all recorded retry/failure text through existing redaction utilities or equivalent safe summarization. Add a persisted provider cache model/repository/service keyed by provider, model, task_type, language, item_key or prompt hash, and prompt_version; cache normalized response plus basic metadata only. Add a versioned Polish function-word data module and route Polish lexical grounding/definition/POS/IPA lookup through it before provider usage. Preserve current behavior for words outside that fixed Polish list and do not expand to other languages.</action>
  <verify>
    <automated>python -m pytest tests/services/test_provider_retry.py tests/services/test_provider_response_cache.py tests/services/test_polish_function_words.py tests/services/test_text_generation.py tests/services/test_generate_text_items.py -q</automated>
  </verify>
  <done>Backoff, redacted terminal failure, Polish fixed lexical data, and provider response cache all pass focused fake-provider tests; no Etapa 1-3 or unrelated provider behavior is changed.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Export snapshot refresh plus separate text repair and audio commands</name>
  <files>src/multilang/cli.py, src/multilang/runtime.py, src/multilang/services/generate_text_items.py, src/multilang/services/generate_audio_items.py, src/multilang/services/assemble_export_cards.py, src/multilang/repositories/text_repository.py, src/multilang/repositories/export_repository.py, tests/cli/test_export_command.py, tests/cli/test_generate_command.py, tests/services/test_generate_text_items.py, tests/services/test_generate_audio_items.py, tests/services/test_assemble_export_cards.py</files>
  <behavior>
    - Etapa 5: `export --refresh-snapshots` rebuilds `card_exports` from current accepted text/lexical/audio data before writing APKG, CSV, or TSV; without the flag export uses existing snapshots exactly as today.
    - Etapa 5: recent IPA and Definitions changes appear in exported rows only when refresh is requested; card templates are not altered.
    - Etapa 6: `repair-text --job-id <JOB_ID> --max-items N` processes only `text_quality_records` whose `review_status` is not `accepted`; `generate --missing-only` remains limited to cards with no text.
    - Etapa 9: `synthesize-audio --job-id <JOB_ID> --missing-only --max-items N` generates missing audio without invoking textual generation and skips/reports already existing audio when requested.
  </behavior>
  <action>Add CLI flags/commands using existing Typer patterns. Extend runtime export with `refresh_snapshots: bool` that calls `AssembleExportCardsService.execute` before artifact writing when true for all supported formats. Add repository selection for non-accepted text records and wire a repair-text service path that reuses the existing text regeneration/validation pipeline without broadening `generate --missing-only`. Extend audio generation to accept `missing_only` and `max_items`, then expose it through `synthesize-audio`; ensure this command never calls text-generation services. Keep all output diagnostics count/path based and avoid card text leakage.</action>
  <verify>
    <automated>python -m pytest tests/cli/test_export_command.py tests/cli/test_generate_command.py tests/services/test_generate_text_items.py tests/services/test_generate_audio_items.py tests/services/test_assemble_export_cards.py -q</automated>
  </verify>
  <done>Export refresh, repair-text, and synthesize-audio behavior is available from CLI and service layers with focused tests proving snapshot refresh, review-only repair selection, missing-only audio generation, and no template changes.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Controlled concurrency and batch text generation</name>
  <files>src/multilang/cli.py, src/multilang/runtime.py, src/multilang/services/generate_text_items.py, src/multilang/services/batch_text_generation.py, src/multilang/services/text_generation.py, src/multilang/repositories/text_repository.py, docs/ai-generation-improvement-prompts.md, tests/cli/test_generate_command.py, tests/services/test_generate_text_items.py, tests/services/test_batch_text_generation.py</files>
  <behavior>
    - Etapa 10: `generate --concurrency` defaults to 1, avoids two workers processing the same item, uses a safe DB session/worker mechanism or equivalent, and respects the existing global rate limiter.
    - Etapa 10: tests with fake providers prove deterministic work claiming and no duplicate item processing; docs mention SQLite risk and recommend Postgres for real concurrency.
    - Etapa 11: batch generation can request multiple cards per provider call with structured JSON response, validate each item individually, re-enqueue/retry only failed items, and keep the current per-item path as fallback.
    - Etapa 11: JSON partial success, invalid item, and retry-by-item are covered by focused tests.
  </behavior>
  <action>Add `--concurrency` to generate with default 1 and keep all current single-worker behavior unchanged at default. Implement item claiming at the repository/service boundary so workers cannot process the same item; if SQLite cannot guarantee real concurrent safety, keep behavior conservative and document that Postgres is recommended for real concurrent jobs. Ensure `SimpleRateLimiter` or its successor is shared globally across workers. Add a batch-generation service boundary that accepts eligible candidates, calls a structured JSON provider batch path, validates and persists each item independently, re-enqueues only failed/invalid items, and falls back to the current per-item generation path when batch mode is unavailable or unsafe. Do not remove or weaken per-item generation.</action>
  <verify>
    <automated>python -m pytest tests/cli/test_generate_command.py tests/services/test_generate_text_items.py tests/services/test_batch_text_generation.py -q</automated>
  </verify>
  <done>`--concurrency` and batch generation are implemented with default-compatible behavior, global rate-limit respect, duplicate-processing protection, per-item retry on partial batch failures, and documented SQLite/Postgres concurrency guidance.</done>
</task>

</tasks>

<verification>
Run the three focused commands listed in the tasks. If attempting the broad suite, treat failures from known STATE.md full-suite collection drift as separate debt and report them without blocking this quick-task completion.
</verification>

<success_criteria>
- Etapas 4-11 are implemented exactly within their listed scope.
- Existing generate/export behavior is preserved when new flags are omitted.
- Provider failures, cache, repair, audio, concurrency, and batch paths are tested with fakes and do not require live provider calls.
- Logs/diagnostics remain redacted and do not expose keys, prompts, payloads, sentences, translations, or highlights.
</success_criteria>

<output>
After execution, create `.planning/quick/260519-kyd-realize-todas-as-etapas-do-arquivo-docs-/260519-kyd-SUMMARY.md` with files changed, focused test commands/results, and any broad-suite drift observed.
</output>
