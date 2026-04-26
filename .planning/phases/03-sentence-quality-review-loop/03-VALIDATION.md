---
phase: 3
slug: sentence-quality-review-loop
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-21
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/domain/test_text_quality.py tests/repositories/test_text_repository.py tests/services/test_text_generation.py tests/services/test_text_validation.py tests/services/test_generate_text_items.py tests/services/test_text_review.py tests/services/test_regenerate_text_item.py tests/cli/test_generate_command.py -q` |
| **Full phase command** | `uv run pytest tests/domain/test_text_quality.py tests/repositories/test_text_repository.py tests/services/test_text_generation.py tests/services/test_text_validation.py tests/services/test_generate_text_items.py tests/services/test_text_review.py tests/services/test_regenerate_text_item.py tests/cli/test_generate_command.py tests/integration/test_text_job_flow.py -q` |
| **Estimated runtime** | ~3-5 minutes |

---

## Sampling Rate

- **After every task commit:** Run the narrowest task command listed below.
- **After every plan wave:** Run `uv run pytest tests/domain/test_text_quality.py tests/repositories/test_text_repository.py tests/services/test_text_generation.py tests/services/test_text_validation.py tests/services/test_generate_text_items.py tests/services/test_text_review.py tests/services/test_regenerate_text_item.py tests/cli/test_generate_command.py tests/integration/test_text_job_flow.py -q`
- **Before Phase 3 re-verification:** Run the full phase command above. A full project-wide `tests -q` run can remain optional until slow-suite separation is planned.
- **Max feedback latency:** 5 minutes

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | TEXT-01 / TEXT-03 / TEXT-04 / TEXT-05 | T-03-01 | Typed records keep sentence, translation, review state, and machine-readable flags separate | unit | `uv run pytest tests/domain/test_text_quality.py -q` | ✅ | ✅ green |
| 3-01-02 | 01 | 1 | TEXT-04 / TEXT-05 | T-03-02 / T-03-03 | Repository upserts one row per `(job_id, item_key)` and preserves review/flag metadata | repository | `uv run pytest tests/repositories/test_text_repository.py -q` | ✅ | ✅ green |
| 3-01-03 | 01 | 1 | TEXT-04 / TEXT-05 | T-03-04 | Live schema exposes `text_quality_records` before downstream runtime wiring starts | integration | `MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase3-schema.db uv run alembic upgrade head && MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase3-schema.db uv run python -c "from sqlalchemy import create_engine, inspect; from multilang.settings import Settings; engine=create_engine(Settings().database_url); print(sorted(inspect(engine).get_table_names()))"` | ✅ | ✅ green |
| 3-02-01 | 02 | 2 | TEXT-01 / TEXT-03 | T-03-05 / T-03-06 | Sentence generation uses grounded lexical context and translation input is the generated sentence only | unit | `uv run pytest tests/services/test_text_generation.py -q` | ✅ | ✅ green |
| 3-02-02 | 02 | 2 | TEXT-01 / TEXT-03 | T-03-07 | Typed generation service returns structured sentence/translation provenance through fake adapters | unit | `uv run pytest tests/services/test_text_generation.py -q` | ✅ | ✅ green |
| 3-03-01 | 03 | 3 | TEXT-01 / TEXT-02 / TEXT-03 / TEXT-04 | T-03-08 / T-03-09 | Validation rejects missing-target, malformed, or translation-mismatch text and assigns confidence labels | unit | `uv run pytest tests/services/test_text_validation.py -q` | ✅ | ✅ green |
| 3-03-02 | 03 | 3 | TEXT-01 / TEXT-02 / TEXT-03 / TEXT-04 | T-03-10 / T-03-11 | Generate-text pipeline repairs once, then persists accepted or review-required rows with reasons | service | `uv run pytest tests/services/test_text_validation.py tests/services/test_generate_text_items.py -q` | ✅ | ✅ green |
| 3-04-01 | 04 | 4 | TEXT-04 | T-03-12 | Review queue serializes flagged rows with stable identity and triage ordering | unit | `uv run pytest tests/services/test_text_review.py -q` | ✅ | ✅ green |
| 3-04-02 | 04 | 4 | TEXT-04 | T-03-13 / T-03-14 | CLI prints flagged-card counts and saved review report path on `multilang generate` | cli | `uv run pytest tests/services/test_text_review.py tests/cli/test_generate_command.py -q` | ✅ | ✅ green |
| 3-05-01 | 05 | 5 | TEXT-05 | T-03-15 | Regeneration updates only the targeted flagged item and reuses the grounded lexical candidate | service | `uv run pytest tests/services/test_regenerate_text_item.py -q` | ✅ | ✅ green |
| 3-05-02 | 05 | 5 | TEXT-01 / TEXT-02 / TEXT-03 / TEXT-04 / TEXT-05 | T-03-16 / T-03-17 / T-03-18 | Shipped runtime performs Phase 3 text generation and single-item regeneration on the existing `multilang generate` path | cli/integration | `uv run pytest tests/services/test_regenerate_text_item.py tests/cli/test_generate_command.py tests/integration/test_text_job_flow.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Existing pytest infrastructure in `pyproject.toml`
- [x] Existing shared fixtures pattern in `tests/`
- [x] `tests/domain/test_text_quality.py` — text-quality contract tests
- [x] `tests/repositories/test_text_repository.py` — persistence and flagged-query tests
- [x] `tests/services/test_text_generation.py` — generation/translation seam tests
- [x] `tests/services/test_text_validation.py` — deterministic sentence/translation validation tests
- [x] `tests/services/test_generate_text_items.py` — one-repair pipeline tests
- [x] `tests/services/test_text_review.py` — review report ordering and identity tests
- [x] `tests/services/test_regenerate_text_item.py` — item-level regeneration tests
- [x] `tests/integration/test_text_job_flow.py` — shipped-path Phase 3 runtime tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Review a small sample of accepted example sentences for naturalness across at least two languages | TEXT-02 | Naturalness and pedagogy remain partly human-judged even with deterministic validators | Completed in `03-HUMAN-UAT.md`; user approved sampled English and French outputs as natural and learner-friendly |
| Inspect one generated review report and verify the highest-risk items are actionable for regeneration | TEXT-04 / TEXT-05 | Operator usefulness of the report is partly UX/content quality, not just schema correctness | Completed in `03-HUMAN-UAT.md`; user approved the seeded flagged review report as clear and actionable |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency is bounded and phase-focused
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** passed
