---
phase: 2
slug: input-decks-lexical-grounding
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/domain/test_lexicon.py tests/repositories/test_lexical_repository.py tests/services/test_frequency_decks.py tests/services/test_word_list_parser.py tests/services/test_kaikki_lookup.py tests/services/test_lexical_grounding.py tests/cli/test_generate_command.py -q` |
| **Full suite command** | `uv run pytest tests -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/domain/test_lexicon.py tests/repositories/test_lexical_repository.py tests/services/test_frequency_decks.py tests/services/test_word_list_parser.py tests/services/test_kaikki_lookup.py tests/services/test_lexical_grounding.py tests/cli/test_generate_command.py -q`
- **After every plan wave:** Run `uv run pytest tests -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | LEX-01 / LEX-03 | T-02-01 / T-02-02 | Candidate contracts encode lemma, display form, provenance, and fixed output-language policy | unit | `uv run pytest tests/domain/test_lexicon.py -q` | ✅ | ⬜ pending |
| 2-01-02 | 01 | 1 | LEX-01 / LEX-02 / LEX-03 | T-02-03 / T-02-04 | Lexical candidates persist once per `(job_id, item_key)` and preserve warning/provenance state | repository | `uv run pytest tests/repositories/test_lexical_repository.py -q` | ✅ | ⬜ pending |
| 2-01-03 | 01 | 1 | LEX-01 | T-02-05 | Schema migration creates lexical-candidate storage before downstream wiring | integration | `MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase2-schema.db uv run alembic upgrade head && MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase2-schema.db uv run python -c "from sqlalchemy import create_engine, inspect; from multilang.settings import Settings; engine=create_engine(Settings().database_url); print(sorted(inspect(engine).get_table_names()))"` | ✅ | ⬜ pending |
| 2-02-01 | 02 | 2 | DECK-02 | T-02-06 / T-02-07 | Frequency builder enforces deterministic filter rules and rank ordering | unit | `uv run pytest tests/services/test_frequency_decks.py -q` | ✅ | ⬜ pending |
| 2-02-02 | 02 | 2 | DECK-02 / LEX-01 | T-02-08 | Level selector backfills until 1000 valid items remain per level | unit | `uv run pytest tests/services/test_frequency_decks.py -q` | ✅ | ⬜ pending |
| 2-03-01 | 03 | 2 | DECK-03 / LEX-01 | T-02-09 | Plain-text parser preserves original forms and emits duplicate/rejection diagnostics | unit | `uv run pytest tests/services/test_word_list_parser.py tests/services/test_kaikki_lookup.py -q` | ✅ | ⬜ pending |
| 2-03-02 | 03 | 2 | LEX-01 / LEX-02 / LEX-03 | T-02-10 / T-02-11 | Grounding never fabricates IPA, formats English definitions consistently, and marks custom misses pending | unit | `uv run pytest tests/services/test_lexical_grounding.py -q` | ✅ | ⬜ pending |
| 2-04-01 | 04 | 3 | DECK-02 / DECK-03 / LEX-01 | T-02-12 | Runtime coordinator writes lexical candidates without breaking resume/rerun semantics | integration | `uv run pytest tests/integration/test_lexical_job_flow.py -q` | ✅ | ⬜ pending |
| 2-04-02 | 04 | 3 | DECK-02 / DECK-03 / LEX-02 / LEX-03 | T-02-13 / T-02-14 | CLI surfaces backfill, rejected-row, and pending-grounding diagnostics with persisted lexical rows | cli/integration | `uv run pytest tests/cli/test_generate_command.py tests/integration/test_lexical_job_flow.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Existing pytest infrastructure in `pyproject.toml`
- [x] Existing shared fixtures pattern in `tests/`
- [ ] `tests/domain/test_lexicon.py` — lexical contract tests
- [ ] `tests/repositories/test_lexical_repository.py` — persistence tests
- [ ] `tests/services/test_frequency_decks.py` — deterministic ranking tests
- [ ] `tests/services/test_word_list_parser.py` — custom-list parsing tests
- [ ] `tests/services/test_kaikki_lookup.py` — fixture-cache lookup tests
- [ ] `tests/services/test_lexical_grounding.py` — trust-first grounding tests
- [ ] `tests/integration/test_lexical_job_flow.py` — shipped-path lexical flow tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Review a sample generated frequency deck for obvious proper-name/noise leakage | DECK-02 | Teachability quality is partially heuristic | Run a level-1 deck for one language, inspect the first 50 `display_form` values, and confirm no obvious names, URLs, or symbol junk survived |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
