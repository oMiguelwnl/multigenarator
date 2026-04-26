---
phase: 05
slug: anki-safe-export-contract
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-26
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/domain/test_exporting.py tests/services/test_assemble_export_cards.py tests/services/test_export_tabular_bundle.py tests/services/test_export_anki_package.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/domain/test_exporting.py tests/services/test_assemble_export_cards.py tests/services/test_export_tabular_bundle.py tests/services/test_export_anki_package.py -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CARD-01, CARD-02 | T-05-01 | Export contract rejects field-order drift and preserves blank `Image` | unit | `uv run pytest tests/domain/test_exporting.py tests/repositories/test_export_repository.py -q` | ✅ | ⬜ pending |
| 05-01-02 | 01 | 1 | EXPT-01 | T-05-02 | Export snapshots stay job-scoped and deterministic | repository | `uv run pytest tests/repositories/test_export_repository.py -q` | ✅ | ⬜ pending |
| 05-01-03 | 01 | 1 | EXPT-01 | T-05-03 | Schema state matches ORM before downstream export work | migration | `MULTILANG_DATABASE_URL=sqlite+pysqlite:///$(pwd)/.tmp-phase05.db uv run alembic upgrade head && uv run pytest tests/repositories/test_export_repository.py -q` | ✅ | ⬜ pending |
| 05-02-01 | 02 | 2 | CARD-01, CARD-04, EXPT-03 | T-05-01 / T-05-04 | HTML escaping, `<br>` joins, basename-only sound refs, deterministic GUIDs | unit | `uv run pytest tests/services/test_assemble_export_cards.py -q` | ✅ | ⬜ pending |
| 05-02-02 | 02 | 2 | EXPT-02 | T-05-05 | CSV/TSV output is UTF-8, headered, and column-stable | unit | `uv run pytest tests/services/test_export_tabular_bundle.py -q` | ✅ | ⬜ pending |
| 05-03-01 | 03 | 3 | CARD-03, EXPT-01, EXPT-03 | T-05-04 / T-05-06 | Anki package bundles media, front hides translation, back reveals it | unit | `uv run pytest tests/services/test_export_anki_package.py -q` | ✅ | ⬜ pending |
| 05-04-01 | 04 | 4 | EXPT-01, EXPT-02, EXPT-03 | T-05-02 / T-05-06 | CLI export fails loudly on missing prerequisites and emits requested artifacts | integration | `uv run pytest tests/cli/test_export_command.py tests/integration/test_export_job_flow.py -q` | ✅ | ⬜ pending |
| 05-05-01 | 05 | 5 | CARD-03, EXPT-01, EXPT-03 | — | Human import confirms no remap, correct template behavior, playable audio | manual | `uv run pytest tests/services/test_export_anki_package.py tests/cli/test_export_command.py tests/integration/test_export_job_flow.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Import sample `.apkg` without field remapping | EXPT-01 | Requires real Anki import dialog behavior | Run `multilang export --job-id <job> --format apkg`, import into Anki Desktop, confirm import preview maps fields automatically |
| Translation hidden on front and shown on back | CARD-03 | Requires rendered-card behavior in Anki | Open imported note preview, review front and back of the generated card |
| Packaged audio plays after import | EXPT-03 | Requires Anki media playback | Review a sample imported card and trigger `word_audio` and `sentence_audio` playback |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
