# Phase 05 Pattern Map — Anki-Safe Export Contract

## Relevant Existing Patterns

### 1) Typed domain contracts

**Analogs**
- `src/multilang/domain/lexicon.py`
- `src/multilang/domain/text_quality.py`
- `src/multilang/domain/audio.py`

**Pattern to copy**
- Pydantic `BaseModel` contracts
- small enums for lifecycle/status values
- deterministic helper properties/validators on the model

### 2) Repository boundaries

**Analogs**
- `src/multilang/repositories/text_repository.py`
- `src/multilang/repositories/audio_repository.py`

**Pattern to copy**
- constructor accepts `Session`
- upsert by stable `(job_id, item_key)`-style keys
- convert ORM rows to domain models in `_to_domain()`
- explicit query helpers for workflow-specific reads

### 3) Schema migration shape

**Analogs**
- `alembic/versions/20260421_03_text_quality_tables.py`
- `alembic/versions/20260424_04_audio_synthesis_tables.py`

**Pattern to copy**
- create table + indexes explicitly in Alembic
- keep string lengths and unique constraints concrete
- verify with disposable SQLite in tests

### 4) Service tests use fakes, not live providers

**Analogs**
- `tests/services/test_generate_audio_items.py`
- `tests/services/test_audio_synthesis.py`

**Pattern to copy**
- lightweight fake repositories/adapters
- assert counters, saved records, and deterministic outputs

### 5) Shipped-path CLI/integration tests

**Analogs**
- `tests/cli/test_generate_command.py`
- `tests/integration/test_audio_job_flow.py`

**Pattern to copy**
- `CliRunner()`-based command assertions
- real SQLite temp database for runtime integration
- monkeypatch runtime adapters instead of hitting live services

## Export-Specific New Files To Map

| New file | Closest analog | Why |
|----------|----------------|-----|
| `src/multilang/domain/exporting.py` | `src/multilang/domain/audio.py` | deterministic identity + validation-rich export contract |
| `src/multilang/repositories/export_repository.py` | `src/multilang/repositories/audio_repository.py` | snapshot/artifact persistence with upsert helpers |
| `src/multilang/services/assemble_export_cards.py` | `src/multilang/services/generate_audio_items.py` | compose multiple repositories into deterministic workflow output |
| `src/multilang/services/export_tabular_bundle.py` | `src/multilang/services/text_review.py` | writes a derived artifact from persisted job data |
| `src/multilang/services/export_anki_package.py` | `src/multilang/services/audio_synthesis.py` | external-library adapter boundary with deterministic results |
| `tests/integration/test_export_job_flow.py` | `tests/integration/test_audio_job_flow.py` | runtime path integration with persisted artifacts |

## Constraints To Preserve

- Export logic must consume **accepted** text rows and persisted audio assets from prior phases.
- Field order must never drift from roadmap/requirements.
- Audio field values must use basename-only references.
- Existing `multilang generate` path remains intact; export wiring should extend the shipped runtime, not replace prior phase behavior.
