# Architecture

**Analysis Date:** 2026-06-09

## Pattern Overview

**Overall:** CLI-first, service-oriented batch pipeline with typed domain contracts, repository-backed persistence for modern-language jobs, and a separate curated-asset pipeline for Classical Latin MVP exports.

**Key Characteristics:**
- Entry points are Typer commands assembled in `src/multilang/cli.py`; commands delegate to injectable services so tests can substitute fake services and loaders.
- Runtime composition for modern-language generation is centralized in `src/multilang/runtime.py`, which wires SQLAlchemy repositories, text generation, audio synthesis, export assembly, provider retry/circuit breaking, and settings.
- Domain boundaries are Pydantic/dataclass contracts under `src/multilang/domain/`, with source-profile routing in `src/multilang/domain/source_profiles.py` and export row contracts in `src/multilang/domain/exporting.py`.
- Modern frequency/word-list/highlight flows persist state in SQLAlchemy models from `src/multilang/db/models.py`; Latin MVP flow uses committed JSON assets in `data/latin_mvp/` and dedicated validators in `src/multilang/services/latin_*.py`.
- External providers sit behind adapters (`src/multilang/services/provider_text_adapters.py`, `src/multilang/services/azure_speech_adapter.py`, `src/multilang/services/elevenlabs_speech_adapter.py`, `src/multilang/services/espeak_ng_speech_adapter.py`) and deterministic local/fallback adapters for tests.
- GSDD workflow assets in `.agents/skills/gsdd-*/SKILL.md` define planning/execution/verification conventions; codebase changes should preserve artifact-driven lifecycle boundaries and scanner-readable evidence patterns.

## Layers

**CLI / Operator Interface:**
- Purpose: Expose generation, review, audio, export, audit, highlight, WebDAV, phoneme, and Latin MVP commands.
- Location: `src/multilang/cli.py`
- Contains: Typer app factory `create_app()`, command validation, operator-facing key=value output, and injectable collaborators.
- Depends on: `src/multilang/runtime.py`, `src/multilang/domain/jobs.py`, `src/multilang/services/*`, and `src/multilang/settings.py`.
- Used by: `python -m multilang.cli` / console entry behavior tested under `tests/test_runtime.py`, `tests/services/*`, and `tests/integration/*`.
- Use this layer only for argument validation, command orchestration, and privacy-safe summaries; keep domain rules in services.

**Runtime Composition:**
- Purpose: Build the repository-backed modern-language generation runtime from settings and provider availability.
- Location: `src/multilang/runtime.py`
- Contains: `build_runtime_service()`, `RuntimeGenerateService`, provider selection, export quality gates, media indexing, and job export orchestration.
- Depends on: SQLAlchemy `Session`, repositories in `src/multilang/repositories/`, service classes in `src/multilang/services/`, and typed settings in `src/multilang/settings.py`.
- Used by: CLI `generate`, `export`, `repair-text`, `synthesize-audio`, and default test/runtime bootstrap.
- Keep new cross-cutting provider/repository wiring here rather than constructing concrete adapters inside individual services.

**Domain Contracts:**
- Purpose: Define stable request, job, source profile, audio, text, lexicon, highlight, export, and Latin contracts.
- Location: `src/multilang/domain/`
- Contains: `GenerationRequest` and `SupportedLanguage` in `src/multilang/domain/jobs.py`, `SourceProfile` and `SourceType` in `src/multilang/domain/source_profiles.py`, export rows in `src/multilang/domain/exporting.py`, and Latin metadata in `src/multilang/domain/latin.py`.
- Depends on: Pydantic v2, Python enums/literals/dataclasses.
- Used by: Services, repositories, CLI, and tests.
- Treat these files as contract surfaces; changing field names, enum values, or source profile meanings requires corresponding export and regression evidence.

**Persistence / Repository Layer:**
- Purpose: Store resumable modern-language job state, lexical candidates, text quality records, audio assets, export snapshots, provider telemetry, and private highlight imports.
- Location: `src/multilang/db/models.py`, `src/multilang/repositories/`, `alembic/`
- Contains: SQLAlchemy models such as `GenerationJob`, `GenerationItem`, `LexicalCandidate`, `TextQualityRecordModel`, `AudioAssetModel`, `CardExportModel`, `DeckExportModel`, `ProviderCallLogModel`, and highlight import tables.
- Depends on: SQLAlchemy ORM and database URL from `src/multilang/settings.py`.
- Used by: `src/multilang/runtime.py`, `src/multilang/services/ingest_lexical_items.py`, `src/multilang/services/generate_text_items.py`, `src/multilang/services/generate_audio_items.py`, `src/multilang/services/assemble_export_cards.py`, and export/report services.
- Preserve repository ownership: service code should call repository methods instead of directly importing ORM models outside repository/runtime seams.

**Modern-Language Generation Services:**
- Purpose: Convert frequency/custom/highlight inputs into grounded lexical candidates, generated/validated text, audio, review reports, and export snapshots.
- Location: `src/multilang/services/ingest_lexical_items.py`, `src/multilang/services/generate_job.py`, `src/multilang/services/generate_text_items.py`, `src/multilang/services/generate_audio_items.py`, `src/multilang/services/assemble_export_cards.py`
- Contains: Job start/resume/rerun partitioning, frequency level building, word-list parsing, Kindle highlight normalization/extraction, lexical grounding, text validation and repair, Tatoeba fallback, audio preparation/reuse, and export-card assembly.
- Depends on: Domain contracts, repositories, provider adapters, `src/multilang/services/text_validation.py`, `src/multilang/services/text_generation.py`, `src/multilang/services/audio_synthesis.py`, and source profiles.
- Used by: `RuntimeGenerateService` in `src/multilang/runtime.py` and CLI `generate`/`export` commands.
- Keep the shipped modern-language flow separate from Latin; `IngestLexicalItemsService.execute()` currently accepts only `frequency`, `word-list`, and `kindle-highlights` and deliberately rejects other source types.

**Classical Latin MVP Asset Pipeline:**
- Purpose: Generate, review, validate, and export a fixed 50-card Classical Latin MVP from committed assets without routing through the modern frequency pipeline.
- Location: `src/multilang/domain/latin.py`, `src/multilang/services/latin_mvp.py`, `src/multilang/services/latin_source_pack.py`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_translation_quality.py`, `src/multilang/services/latin_audio.py`, `src/multilang/services/latin_export.py`, `data/latin_mvp/`
- Contains: `LatinGenerationRequest`, validated source-pack loader, grammar/token validators, review gates, Portuguese QA, audio manifest readiness, Latin export row/model/template, and APKG/CSV/TSV writers.
- Depends on: Committed JSON assets `data/latin_mvp/latin-mvp-50-v1.json`, `data/latin_mvp/latin-mvp-50-v1-curation.json`, `data/latin_mvp/latin-mvp-50-v1-pt.json`, and `data/latin_mvp/latin-mvp-50-v1-audio.json` plus media under `data/latin_mvp/audio/`.
- Used by: CLI commands `generate-latin-mvp`, `review-latin-mvp`, and `export-latin-mvp` in `src/multilang/cli.py`, and evidence tests under `tests/integration/test_v20_*` and `tests/services/test_latin_*`.
- Extend Latin through these files; do not add `la` to `SupportedLanguage` in `src/multilang/domain/jobs.py` unless a future phase explicitly defines Latin scale through the modern job pipeline.

**Export / Packaging Layer:**
- Purpose: Produce Anki `.apkg`, CSV, and TSV artifacts with stable note models, field order, media references, and quality gates.
- Location: `src/multilang/services/export_anki_package.py`, `src/multilang/services/export_tabular_bundle.py`, `src/multilang/services/latin_export.py`, `src/multilang/domain/exporting.py`
- Contains: Generic normal/manual/highlight genanki model dispatch, generic tabular writer, Latin-specific genanki model, Latin tabular writer, GUID builders, media file checks, and field tuples.
- Depends on: `genanki`, source profiles, export rows, card templates in `src/multilang/templates/`, and audio/media manifests.
- Used by: Runtime `export_job()` for modern modes and CLI `export-latin-mvp` for Latin.
- Preserve note-model isolation: normal `Multilang::Card`, manual `Multilang::Manual Card`, highlight `Multilang::Highlight Card`, phoneme decks, and Latin `Multilang::Classical Latin MVP` have separate field contracts and model IDs.

**Settings / Provider Configuration:**
- Purpose: Load runtime configuration from environment variables while keeping secrets out of code and generated maps.
- Location: `src/multilang/settings.py`
- Contains: `Settings` with `env_prefix="MULTILANG_"`, database URL, provider names, API key fields, storage directories, retry/circuit settings, WebDAV settings, and supported modern languages.
- Depends on: `pydantic-settings` and `.env` loading. `.env` is present at repo root but must not be read or quoted.
- Used by: Runtime composition, audio adapters, text adapters, WebDAV services, and CLI smoke helpers.
- Keep settings typed and provider-neutral; service code should ask `Settings` for paths/providers, not read environment variables directly.

**Security / Privacy Utilities:**
- Purpose: Prevent private source text, paths, provider secrets, and unsafe context from leaking into committed artifacts or provider prompts.
- Location: `src/multilang/security/redaction.py`, privacy-sensitive highlight code in `src/multilang/services/generate_text_items.py`, Latin source text checks in `src/multilang/services/latin_export.py`
- Contains: Redaction helpers, bounded highlight context snippets, source-text forbidden-fragment checks, provider-safe error summaries in `src/multilang/services/provider_retry.py`.
- Depends on: Service callers using redacted/bounded context before persistence or provider calls.
- Used by: Kindle highlight generation, provider logging, Latin source/export evidence, and tests under `tests/security/`.
- Any new artifact/report path should emit hashes, counts, item keys, and public citations rather than raw private text or local absolute paths.

## Data Flow

**Modern Frequency / Word-list / Highlight Generation Flow:**

1. CLI `generate` in `src/multilang/cli.py` builds a `GenerationRequest` from operator options and validates source-specific flags.
2. `build_runtime_service()` in `src/multilang/runtime.py` wires repositories and services, then `IngestLexicalItemsService.execute()` in `src/multilang/services/ingest_lexical_items.py` starts or resumes a job through `GenerateJobService` in `src/multilang/services/generate_job.py`.
3. Ingestion creates lexical candidates from `wordfreq` levels (`src/multilang/services/frequency_decks.py`), word-list rows (`src/multilang/services/word_list_parser.py`), or Kindle highlight candidates (`src/multilang/services/kindle_highlight_parser.py`, `src/multilang/services/highlight_candidate_extraction.py`).
4. Grounded candidates are persisted through `src/multilang/repositories/lexical_repository.py` into `LexicalCandidate` rows in `src/multilang/db/models.py` and successful item stages are recorded through `src/multilang/repositories/job_repository.py`.
5. `GenerateTextItemsService` in `src/multilang/services/generate_text_items.py` claims candidates, calls `TextGenerationService` in `src/multilang/services/text_generation.py`, validates with `TextValidationService` in `src/multilang/services/text_validation.py`, attempts AI retry and Tatoeba fallback, then persists `TextQualityRecord` rows through `src/multilang/repositories/text_repository.py`.
6. `GenerateAudioItemsService` in `src/multilang/services/generate_audio_items.py` prepares word/sentence audio through `AudioSynthesisService` in `src/multilang/services/audio_synthesis.py`, reuses exact-match assets when safe, and persists audio assets through `src/multilang/repositories/audio_repository.py`.
7. CLI `export` calls `RuntimeGenerateService.export_job()` in `src/multilang/runtime.py`; `AssembleExportCardsService` freezes accepted records into `ExportCardRow` snapshots and the export quality gate in `src/multilang/domain/exporting.py` blocks invalid text/audio or incomplete final frequency decks.
8. `export_anki_package()` or `write_export_tabular_bundle()` writes the requested artifact and `src/multilang/services/generation_report.py` records scanner-readable evidence.

**Classical Latin MVP Flow:**

1. CLI `generate-latin-mvp` in `src/multilang/cli.py` builds a `LatinGenerationRequest` from `src/multilang/domain/latin.py` and invokes `LatinMvpGenerationService` in `src/multilang/services/latin_mvp.py`.
2. `LatinMvpGenerationService.start()` loads the committed source pack via `load_latin_mvp_source_pack()` in `src/multilang/services/latin_source_pack.py`, validates exact 50-card scope, `source_pack_version`, source/license gate status, target-form presence, and approved grammar evidence.
3. Optional `--portuguese-json` loads `data/latin_mvp/latin-mvp-50-v1-pt.json` through `src/multilang/services/latin_translation_quality.py` and returns aggregate Portuguese QA counts only.
4. Optional `--audio-json` loads `data/latin_mvp/latin-mvp-50-v1-audio.json` through `src/multilang/services/latin_audio.py` and returns aggregate audio readiness only.
5. CLI `review-latin-mvp` loads `data/latin_mvp/latin-mvp-50-v1-curation.json` through `src/multilang/services/latin_review.py`, updates exactly one gate when requested, and protects approved gates unless `--force` is supplied.
6. CLI `export-latin-mvp` calls `export_latin_mvp_bundle()` in `src/multilang/services/latin_export.py`; export joins source pack, curation records, Portuguese translations, audio manifest, and media files.
7. Latin export fails closed unless all source/translation/grammar/audio gates are approved, translation rows match source-pack order, audio text and storage paths pass readiness checks, and source text contains only public provenance.
8. Latin APKG/CSV/TSV output uses `LATIN_EXPORT_FIELD_NAMES` and the dedicated genanki model in `src/multilang/services/latin_export.py`; it does not use `ExportCardRow` or generic `export_anki_package()`.

**State Management:**
- Modern job state lives in database tables declared in `src/multilang/db/models.py`, with `run_key`/`source_fingerprint` determining duplicate-safe reruns and resume behavior.
- Modern runtime uses `JobStage` and `JobStatus` from `src/multilang/domain/jobs.py` to advance from ingest to generate text, synthesize audio, and export.
- Provider response cache and telemetry use `ProviderResponseCacheModel` and `ProviderCallLogModel` in `src/multilang/db/models.py`, with prompt/response hashes rather than raw secret values.
- Latin state is file-backed and asset-versioned under `data/latin_mvp/`; loaders validate every read, and export readiness is derived from the current source/curation/translation/audio assets.
- Planning and lifecycle state lives in `.planning/` artifacts such as `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, and `.planning/STATE.md`; workflow skills under `.agents/skills/` require reading and updating those artifacts during GSDD phases.

## Key Abstractions

**GenerationRequest / Job Lifecycle:**
- Purpose: Normalize modern-language generation inputs and resumable job execution.
- Examples: `src/multilang/domain/jobs.py`, `src/multilang/services/generate_job.py`, `src/multilang/repositories/job_repository.py`
- Pattern: Pydantic request object plus repository-backed orchestrator that partitions requested item keys into pending, skipped, and overwritten sets.

**SourceProfile:**
- Purpose: Route source-mode-specific validation, field exports, sentence token limits, note type names, and template names.
- Examples: `src/multilang/domain/source_profiles.py`, `src/multilang/domain/exporting.py`, `src/multilang/services/card_template_loader.py`
- Pattern: Central source profile registry; add source-mode behavior here before branching inside lower-level services.

**ExportCardRow / LatinExportRow:**
- Purpose: Freeze learner-facing export payloads in stable field order.
- Examples: `src/multilang/domain/exporting.py`, `src/multilang/services/assemble_export_cards.py`, `src/multilang/services/latin_export.py`
- Pattern: Generic modern export rows use Pydantic aliases and source-profile field tuples; Latin uses a separate dataclass contract and dedicated writer because its fields differ.

**Provider Adapters:**
- Purpose: Hide LiteLLM/DeepL/Google/Azure/ElevenLabs/eSpeak implementation details behind stable service methods.
- Examples: `src/multilang/services/provider_text_adapters.py`, `src/multilang/services/audio_synthesis.py`, `src/multilang/services/azure_speech_adapter.py`, `src/multilang/services/elevenlabs_speech_adapter.py`, `src/multilang/services/espeak_ng_speech_adapter.py`
- Pattern: Adapter protocols plus runtime-selected concrete adapters; tests should use fake/local adapters rather than live providers.

**Quality Gates:**
- Purpose: Fail before learner-facing export when text, translation, audio, source, grammar, or review status is unsafe.
- Examples: `src/multilang/domain/exporting.py`, `src/multilang/services/text_validation.py`, `src/multilang/services/text_field_remediation.py`, `src/multilang/services/audio_integrity.py`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_audio.py`, `src/multilang/services/latin_export.py`
- Pattern: Validate as close as possible to the boundary that consumes the data; raise `ValueError`/domain errors before writing artifacts.

**Committed Evidence Assets:**
- Purpose: Prove milestone requirements and protect against regression without relying on narrative claims.
- Examples: `tests/integration/test_v20_final_milestone_evidence.py`, `tests/integration/test_v20_existing_modes_regression_evidence.py`, `data/latin_mvp/latin-mvp-50-v1.json`, `.planning/phases/*/*-SUMMARY.md`, `.planning/phases/*/*-VERIFICATION.md`
- Pattern: Scanner-readable JSON/CSV-like evidence, focused tests, and exact requirement ID mappings.

## Entry Points

**CLI App Factory:**
- Location: `src/multilang/cli.py:create_app()`
- Triggers: `python -m multilang.cli ...` and tests that instantiate the Typer app.
- Responsibilities: Command registration, option validation, collaborator injection, and privacy-safe operator output.

**Modern Runtime Builder:**
- Location: `src/multilang/runtime.py:build_runtime_service()`
- Triggers: CLI commands when no test service is injected.
- Responsibilities: Create database engine/session, instantiate repositories, select providers, build orchestration services, and return `RuntimeGenerateService`.

**Modern Job Start/Resume:**
- Location: `src/multilang/services/generate_job.py:GenerateJobService.orchestrate()`
- Triggers: `IngestLexicalItemsService.execute()` from `src/multilang/services/ingest_lexical_items.py`.
- Responsibilities: Create new jobs, resume existing jobs, calculate pending/skipped/overwritten item keys, and surface resume diagnostics.

**Modern Export:**
- Location: `src/multilang/runtime.py:RuntimeGenerateService.export_job()`
- Triggers: CLI `export` command in `src/multilang/cli.py`.
- Responsibilities: Load or rebuild export snapshots, evaluate quality gates, package APKG/CSV/TSV artifacts, persist deck export metadata, and write generation reports.

**Latin Start / Review / Export:**
- Location: `src/multilang/cli.py` commands `generate-latin-mvp`, `review-latin-mvp`, `export-latin-mvp`
- Triggers: Operator CLI calls and v2.0 evidence tests.
- Responsibilities: Load and summarize Latin source packs, update review gates, and export approved Latin assets through `src/multilang/services/latin_export.py`.

**Database Model Creation:**
- Location: `src/multilang/runtime.py:build_runtime_service()` calls `Base.metadata.create_all(engine)` from `src/multilang/db/base.py`.
- Triggers: Runtime service construction.
- Responsibilities: Ensure ORM tables exist for local/runtime use; Alembic remains the migration mechanism via `alembic/` and `alembic.ini`.

## Error Handling

**Strategy:** Fail closed at validation/export boundaries, surface concise CLI messages, and persist recoverable job/item failures through repositories.

**Patterns:**
- CLI commands catch `ValueError`, echo the message, and exit non-zero in `src/multilang/cli.py` for commands such as `generate-latin-mvp`, `review-latin-mvp`, `export-latin-mvp`, `export`, and `audit-deck`.
- Provider calls are retried and logged through `src/multilang/services/provider_retry.py` and provider call repositories; error summaries are sanitized before persistence.
- Job orchestration stores failed item state via `JobRepository.record_item_failure()` from `src/multilang/repositories/job_repository.py` instead of crashing the whole run when item-level processing fails.
- Text generation uses validation status and review status rather than accepting weak outputs silently in `src/multilang/services/generate_text_items.py`.
- Export gates in `src/multilang/domain/exporting.py` and `src/multilang/services/latin_export.py` raise before artifact creation when required content/audio/review state is missing.
- Latin loaders wrap missing/malformed JSON and Pydantic validation failures with domain-specific `ValueError` messages in `src/multilang/services/latin_source_pack.py`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_translation_quality.py`, and `src/multilang/services/latin_audio.py`.

## Cross-Cutting Concerns

**Logging:** Provider telemetry is structured in `ProviderCallLogModel` in `src/multilang/db/models.py` and inserted through `src/multilang/repositories/provider_call_log_repository.py`; CLI output uses deterministic key=value lines from `src/multilang/cli.py`. There is no central application logger detected.

**Validation:** Validation is layered: Pydantic model validation for contracts, source profile checks in `src/multilang/domain/source_profiles.py`, text validation in `src/multilang/services/text_validation.py`, remediation checks in `src/multilang/services/text_field_remediation.py`, audio integrity in `src/multilang/services/audio_integrity.py`, export gates in `src/multilang/domain/exporting.py`, and Latin-specific source/review/translation/audio/export validators in `src/multilang/services/latin_*.py`.

**Authentication:** Runtime authentication is provider-key based through environment-backed `Settings` in `src/multilang/settings.py`; WebDAV credentials, LLM keys, DeepL keys, Azure Speech keys, and ElevenLabs keys are represented as settings fields. No user-auth/session layer is detected.

**Privacy and Secrets:** `.env` exists at the repository root and is intentionally not read. Do not add code or docs that quote API keys, provider secrets, WebDAV credentials, raw private highlight text, or local absolute paths. Use `src/multilang/security/redaction.py`, bounded snippets in `src/multilang/services/generate_text_items.py`, and public-source checks in `src/multilang/services/latin_export.py` as patterns.

**Concurrency:** Text generation has a `concurrency` option in `src/multilang/cli.py` and claim-oriented repository access in `src/multilang/services/generate_text_items.py`; comments note SQLite is conservative and PostgreSQL is recommended for real concurrency. Avoid introducing parallel writes that bypass repository claim/update semantics.

**Templates and Field Order:** Template selection for modern modes goes through `src/multilang/services/card_template_loader.py` and source profiles; Latin embeds its dedicated genanki template in `src/multilang/services/latin_export.py`. Field tuple changes are architectural changes and require targeted export/template regression tests.

**GSDD Workflow Boundaries:** `.agents/skills/gsdd-plan/SKILL.md`, `.agents/skills/gsdd-execute/SKILL.md`, `.agents/skills/gsdd-verify/SKILL.md`, and `.agents/skills/gsdd-map-codebase/SKILL.md` require lifecycle artifacts, phase plans, verifications, and codebase maps to remain disk-backed. Preserve `.planning/` as the source of project state and avoid relying on conversation-only context for implementation decisions.

## Extension Points

**New Modern Source Mode:**
- Add the source type to `SourceType` and `SOURCE_PROFILES` in `src/multilang/domain/source_profiles.py`.
- Extend CLI validation in `src/multilang/cli.py` and ingestion dispatch in `src/multilang/services/ingest_lexical_items.py`.
- Add source-specific grounding/normalization services under `src/multilang/services/` and repository methods if persistence differs.
- Update export field logic in `src/multilang/domain/exporting.py`, templates under `src/multilang/templates/`, and regression tests under `tests/integration/`.

**New Language in Existing Modern Flow:**
- Add to `SupportedLanguage` in `src/multilang/domain/jobs.py`, `DEFAULT_SUPPORTED_LANGUAGES` and `_LANGUAGE_NAMES` in `src/multilang/settings.py` / `src/multilang/runtime.py`, and voice selection in `src/multilang/services/audio_voice_registry.py`.
- Verify frequency assets, lexical cache, text generation, translation, audio, and export evidence; do not use this path for Latin MVP unless future requirements explicitly redefine Latin as a scalable modern-flow language.

**New Provider Adapter:**
- Implement the relevant protocol used by `src/multilang/services/text_generation.py` or `src/multilang/services/audio_synthesis.py`.
- Add settings fields in `src/multilang/settings.py` and selection logic in `src/multilang/runtime.py`.
- Add retry/logging integration through `src/multilang/services/provider_retry.py` and privacy-safe provider call records.

**New Latin Asset Gate:**
- Add Pydantic fields/validators in the appropriate Latin service (`src/multilang/services/latin_source_pack.py`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_translation_quality.py`, or `src/multilang/services/latin_audio.py`).
- Update `data/latin_mvp/*.json` assets and focused tests under `tests/services/test_latin_*.py` and `tests/integration/test_v20_*.py`.
- Keep CLI summaries aggregate-only unless the output is explicitly intended as learner-facing export content.

---

*Architecture analysis: 2026-06-09*
