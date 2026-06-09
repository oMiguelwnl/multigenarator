# Coding Conventions

**Analysis Date:** 2026-06-09

## Mapping Scope

- Quality mapping verified live Python source and tests under `src/multilang/` and `tests/`, plus project configuration in `pyproject.toml`.
- `.planning/templates/delegates/mapper-quality.md` is referenced by the workflow but is not present on disk; this map follows the active GSDD mapper contract from `.agents/skills/gsdd-map-codebase/SKILL.md` and the live repository patterns.
- `.env` is present and intentionally not read. Treat runtime settings as environment-backed through `src/multilang/settings.py`, never by reading secret files.

## Naming Patterns

**Files:**
- Use lowercase snake_case module names for Python implementation files: `src/multilang/services/latin_export.py`, `src/multilang/services/latin_source_pack.py`, `src/multilang/services/provider_retry.py`.
- Place domain contracts under `src/multilang/domain/` with nouns that name the boundary: `src/multilang/domain/latin.py`, `src/multilang/domain/source_profiles.py`, `src/multilang/domain/exporting.py`.
- Place service behavior under `src/multilang/services/` with action or capability names: `src/multilang/services/audio_synthesis.py`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_translation_quality.py`.
- Test files use `test_*.py` and mirror the production area: `tests/services/test_latin_export.py`, `tests/domain/test_source_profiles.py`, `tests/cli/test_generate_latin_mvp_command.py`, `tests/integration/test_v20_final_milestone_evidence.py`.

**Functions:**
- Use snake_case and make behavior explicit: `build_latin_export_rows`, `export_latin_mvp_bundle`, `validate_latin_target_presence`, `retry_provider_call`.
- Use `load_*` for committed asset loaders that read and validate project-owned fixtures, as in `load_latin_mvp_source_pack` in `src/multilang/services/latin_source_pack.py` and `load_latin_audio_manifest` in `src/multilang/services/latin_audio.py`.
- Use `assert_*` for fail-closed validation gates that raise on invalid state, as in `assert_latin_records_export_ready` and `assert_latin_audio_manifest_export_ready` consumed by `src/multilang/services/latin_export.py`.
- Private helpers use a leading underscore and stay module-local: `_sound_tag`, `_public_source_text`, `_require_exact_item_key_order`, `_latin_media_files` in `src/multilang/services/latin_export.py`.

**Variables:**
- Use descriptive snake_case variables with domain meaning, not abbreviations: `source_pack`, `curated_records_loader`, `translation_pack_loader`, `audio_manifest_loader`, `media_index` in `src/multilang/services/latin_export.py`.
- Use `*_count`, `*_status`, and `*_path` suffixes consistently for emitted summaries and file references: CLI output in `src/multilang/cli.py` prints `card_count=`, `media_count=`, `note_type=`, and `export_status=`.

**Types and Constants:**
- Use PascalCase for dataclasses, Pydantic models, enums, and service classes: `LatinExportRow`, `LatinExportBundle`, `LatinDeckMetadata`, `LatinGenerationRequest`, `AudioSynthesisService`.
- Use uppercase constants for stable contracts and field tuples: `LATIN_EXPORT_FIELD_NAMES`, `LATIN_NOTE_TYPE_NAME`, `LATIN_MVP_CARD_COUNT`, `DEFAULT_LATIN_SOURCE_PACK_VERSION`.
- Prefer explicit `Literal[...]` unions for small closed vocabularies: `LatinSourceType`, `LatinLicenseGate`, and `LatinTargetMatchMode` in `src/multilang/services/latin_source_pack.py`; `SupportedLanguageCode` and provider choices in `src/multilang/settings.py`.

## Typing and Data Contracts

- Use Python 3.12 typing syntax (`str | None`, `list[str]`, `tuple[str, ...]`) throughout new code, matching `src/multilang/services/latin_export.py` and `src/multilang/settings.py`.
- Use Pydantic `BaseModel` for input/data contracts that require validation from JSON, environment, or user input: `LatinDeckMetadata` in `src/multilang/domain/latin.py`, `LatinMvpSourcePack` in `src/multilang/services/latin_source_pack.py`, and `Settings` in `src/multilang/settings.py`.
- Use frozen dataclasses for immutable in-memory results and rows: `LatinExportRow`, `LatinExportBundle`, `LatinExportArtifactResult` in `src/multilang/services/latin_export.py`; `RuntimeTextResult` and `RuntimeExportResult` in `src/multilang/runtime.py`.
- Prefer `@field_validator` and `@model_validator(mode="after")` for invariants that must fail at construction time. Examples: `LatinGenerationRequest.card_count_must_match_latin_mvp_scope` in `src/multilang/domain/latin.py` and `LatinMvpSourcePackEntry.validate_entry_contract` in `src/multilang/services/latin_source_pack.py`.
- For protocols and adapters, declare a `Protocol` when services depend on a callable surface instead of a concrete provider. `AudioSynthesisAdapter` in `src/multilang/services/audio_synthesis.py` defines `available_voice_ids()` and `synthesize(...)`.
- Keep public exports explicit with `__all__` at the bottom of modules that define contracts, as in `src/multilang/domain/latin.py`, `src/multilang/domain/source_profiles.py`, `src/multilang/services/latin_source_pack.py`, and `src/multilang/services/latin_export.py`.

## Code Style

**Formatting:**
- The repository does not define Black, Ruff, isort, or mypy configuration in `pyproject.toml`; format manually to the existing style.
- Use 4-space indentation, grouped imports, and readable line breaks for long calls and tuples. Long function calls in `src/multilang/services/latin_export.py` and long Typer annotations in `src/multilang/cli.py` are split across multiple lines.
- Keep module docstrings short and purpose-oriented: `"""Classical Latin MVP export row contracts."""` in `src/multilang/services/latin_export.py` and `"""Runtime settings for Multilang."""` in `src/multilang/settings.py`.
- Prefer keyword-only arguments for service entry points and builders. `build_latin_export_rows`, `export_latin_mvp_apkg`, `write_latin_tabular_export`, and `export_latin_mvp_bundle` in `src/multilang/services/latin_export.py` all use `*` to force named parameters.

**Linting:**
- No project lint command is configured in `pyproject.toml`; use tests as the active quality gate.
- Existing code uses targeted lint suppressions only where justified, e.g. `# noqa: BLE001` in `src/multilang/services/provider_retry.py` because provider adapters expose heterogeneous exception types.

## Import Organization

**Order:**
1. `from __future__ import annotations` when the module uses forward references or modern annotations, as in `src/multilang/services/latin_export.py` and `tests/services/test_latin_export.py`.
2. Standard library imports (`dataclasses`, `enum`, `pathlib`, `json`, `csv`, `sqlite3`, `zipfile`).
3. Third-party imports (`pydantic`, `pydantic_settings`, `genanki`, `pytest`, `typer.testing`).
4. Project imports from `multilang.*`.

**Path Aliases:**
- Import project modules through the installed package name `multilang.*`, not relative imports. `pyproject.toml` sets `pythonpath = ["src"]` for pytest.
- Do not create new path aliases; use concrete imports such as `from multilang.services.latin_export import export_latin_mvp_bundle` in `tests/integration/test_v20_final_milestone_evidence.py`.

## Error Handling

**Patterns:**
- Fail closed with `ValueError` for invalid domain state, asset mismatch, blocked export readiness, unsupported formats, and validation failures. Examples: `LatinExportRow.__post_init__` and `_require_exact_item_key_order` in `src/multilang/services/latin_export.py`.
- Convert Pydantic and JSON/file load failures into domain-specific `ValueError` messages at loader boundaries. `load_latin_mvp_source_pack` in `src/multilang/services/latin_source_pack.py` raises clear messages for missing, malformed, and validation-failed manifests.
- CLI commands catch `ValueError`, print the safe message, and exit with `typer.Exit(code=1)`, as in `review_latin_mvp`, `export_latin_mvp`, `export`, and `audit_deck` in `src/multilang/cli.py`.
- Provider errors must be redacted before being stored or exposed. Use `safe_provider_error_summary` and `redact_sensitive_text` via `src/multilang/services/provider_retry.py`; tests in `tests/services/test_provider_retry.py` assert secrets and prompt payloads are not present in retry exhaustion messages.
- Do not include user-provided unknown values in error text when they may contain private paths or secrets. `get_source_profile` in `src/multilang/domain/source_profiles.py` lists allowed source types and omits the unknown input; `tests/domain/test_source_profiles.py` verifies private path fragments and secret-like text are absent.

## Logging and Output

**Framework:**
- No application logger framework is used consistently in the inspected source; CLIs primarily use `typer.echo` and services return typed results.

**Patterns:**
- CLI output should be stable scanner-readable `key=value` lines for summaries, as in `src/multilang/cli.py` for `generate-latin-mvp`, `review-latin-mvp`, and `export-latin-mvp`.
- Public CLI summaries must expose aggregate counts and artifact paths only. Tests in `tests/cli/test_generate_latin_mvp_command.py` assert output omits `storage_path`, provider internals, `AZURE_`, `OPENAI_`, and local workstation paths.
- Provider call telemetry goes through repository records, not ad-hoc logs. `retry_provider_call` records retry attempts through `_log_retry_event` in `src/multilang/services/provider_retry.py` using `ProviderCallLogCreate`.

## Testing Patterns

**Framework:**
- Use pytest. Configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]` with `pythonpath = ["src"]`, `testpaths = ["tests"]`, and `asyncio_mode = "auto"`.
- Development dependencies in `pyproject.toml` include `pytest>=8.3,<9.0` and `pytest-asyncio>=0.25,<1.0`.

**Run Commands:**
```bash
uv run pytest -q
uv run pytest tests/services/test_latin_export.py -q
uv run pytest tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_final_milestone_evidence.py -q
```

**Test File Organization:**
- Unit/service tests live under `tests/services/`, domain tests under `tests/domain/`, CLI tests under `tests/cli/`, repository tests under `tests/repositories/`, security tests under `tests/security/`, and cross-flow evidence tests under `tests/integration/`.
- Co-locate test names with behavior: `test_latin_export_row_rejects_nonblank_image` in `tests/services/test_latin_export.py`, `test_latin_contracts_reject_any_card_count_other_than_50` in `tests/domain/test_latin_contracts.py`, and `test_export_latin_mvp_cli_writes_tabular_formats_without_audio_paths` in `tests/cli/test_generate_latin_mvp_command.py`.

**Fixtures and Test Data:**
- Use `tmp_path` for generated artifacts, temporary CSV/TSV/APKG files, and mutable copied curation data. Examples: `tests/services/test_latin_export.py` and `tests/cli/test_generate_latin_mvp_command.py`.
- Use fake adapters/classes inside tests instead of live providers. `FakeAudioAdapter`, `FlakyAudioAdapter`, `MissingFileAdapter`, and `RaisingAdapter` in `tests/services/test_audio_synthesis.py` make provider behavior deterministic.
- Use committed real assets when evidence must prove milestone behavior over project data. `tests/integration/test_v20_final_milestone_evidence.py` reads `data/latin_mvp/latin-mvp-50-v1.json`, `data/latin_mvp/latin-mvp-50-v1-curation.json`, `data/latin_mvp/latin-mvp-50-v1-pt.json`, and `data/latin_mvp/latin-mvp-50-v1-audio.json`.
- Shared environment fixture `local_text_providers` in `tests/conftest.py` forces local text and translation providers via `monkeypatch` to prevent live provider calls by default.

**Assertions:**
- Prefer behavioral assertions over snapshots. `tests/services/test_latin_export.py` opens generated APKG files, inspects SQLite note fields, parses CSV/TSV headers, and checks media manifests.
- Test both success and fail-closed behavior. For every export/gate path, include rejection cases with `pytest.raises(..., match=...)`, as in `tests/services/test_latin_export.py`, `tests/services/test_latin_audio.py`, and `tests/services/test_latin_source_pack.py`.
- Use `pytest.mark.parametrize` for closed vocabularies and repeated invalid cases: grammar case labels in `tests/services/test_latin_source_pack.py`, export formats in `tests/cli/test_generate_latin_mvp_command.py`, and card count boundaries in `tests/domain/test_latin_contracts.py`.
- For privacy/security gates, assert forbidden path and secret-looking fragments are absent from rendered outputs. Examples exist in `tests/integration/test_v20_final_milestone_evidence.py`, `tests/domain/test_source_profiles.py`, and `tests/cli/test_generate_latin_mvp_command.py`.

**Coverage and Review Gates:**
- No coverage threshold is configured in `pyproject.toml`; use focused milestone/evidence suites as the authoritative gates when broad-suite drift is documented.
- `.planning/STATE.md` records broad-suite drift; future claims that `uv run pytest -q` is authoritative must first repair that drift.
- Milestone evidence tests should define exact requirement sets and prove coverage. `tests/integration/test_v20_final_milestone_evidence.py` defines `V20_REQUIREMENTS` and asserts exact coverage from phase evidence modules.

## Fixture and Data Conventions

- Keep durable project-owned assets under `data/latin_mvp/` for Latin MVP JSON and committed audio metadata. Do not put private local source paths or provider responses into these assets.
- Keep local runtime data and generated user/private artifacts under ignored paths such as `.multilang/`, `.multilang/highlights/raw/`, and `.planning/.local/` per `.gitignore`.
- Do not read or depend on `.env` in tests. Build `Settings(_env_file=None)` for unit tests, as the `settings` fixture does in `tests/conftest.py`.
- For Anki/media tests, write generated artifacts into `tmp_path` and inspect output structure without committing generated `.apkg`, `.db`, `.sqlite`, `.wav`, or `.mp3` files unless they are intentional committed fixtures already present under `data/latin_mvp/audio/`.

## Function Design

**Size:**
- Keep domain validators small and single-purpose (`validate_latin_target_presence`, `validate_latin_gramatica`, `_require_exact_item_key_order`).
- Larger orchestrators are acceptable when they linearize a well-defined flow; `build_latin_export_rows` in `src/multilang/services/latin_export.py` loads assets, validates gates, checks ordering, joins rows, and returns a typed bundle.

**Parameters:**
- Prefer dependency injection for testability. `build_latin_export_rows` accepts loader and validator callables; tests in `tests/services/test_latin_export.py` replace them to assert fail-closed behavior.
- Require explicit keyword arguments on public functions that have multiple paths or collaborators. This avoids accidentally swapping `output_dir`, `deck_name`, and `repo_root` in export functions.

**Return Values:**
- Return typed dataclasses or Pydantic models rather than raw dictionaries. Examples: `LatinExportBundle`, `LatinExportArtifactResult`, `RuntimeTextResult`, and `RuntimeExportResult`.
- CLI functions should print primitive summaries from typed results rather than returning complex objects, following `export_latin_mvp` in `src/multilang/cli.py`.

## Module Design

**Exports:**
- Keep domain constants and public APIs in module-level `__all__` when they are intended for reuse by tests and other services.
- Do not expose private helper functions; test behavior through public functions such as `build_latin_export_rows`, `export_latin_mvp_bundle`, `validate_latin_gramatica`, and `get_source_profile`.

**Barrel Files:**
- `src/multilang/services/__init__.py` and `src/multilang/security/__init__.py` are empty; do not add broad barrel exports unless a strong import-stability need appears.

## Review Gates for Future Implementation

- Before adding a new feature, add or update tests in the matching `tests/{domain,services,cli,integration}/` area and include both success and invalid-state assertions.
- For Latin and export behavior, preserve fail-closed gates: source pack count/order, license approval, grammar approval, translation approval, audio approval, media existence, and stable field order are all enforced by `src/multilang/services/latin_source_pack.py`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_audio.py`, and `src/multilang/services/latin_export.py`.
- For user-facing CLI outputs, add tests that assert sensitive details are absent before considering the command complete.
- For provider integration changes, test retry, redaction, and circuit behavior with fake adapters; do not require network providers for standard unit tests.
- For Anki export changes, inspect generated APKG/CSV/TSV artifacts programmatically as in `tests/services/test_latin_export.py`; do not rely only on file existence.
- Respect source-profile isolation. Changes to `src/multilang/domain/source_profiles.py`, `src/multilang/services/export_anki_package.py`, `src/multilang/services/export_tabular_bundle.py`, or `src/multilang/services/latin_export.py` must include regression assertions for normal, manual, highlight, phonetics, and Latin note type/field contracts.

---

*Convention analysis: 2026-06-09*
