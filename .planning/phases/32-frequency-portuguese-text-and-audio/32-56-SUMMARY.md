---
phase: 32-frequency-portuguese-text-and-audio
plan: "56"
status: complete
scope: offline_helper_regression_only
completed: 2026-09-19
requirements_progress: partial_evidence_only
production_status: bounded_refailure_preserved
---

# Phase 32 Plan 56: Offline Runtime Return Regression

The pending helper already contained the return-path correction when reviewed on
2026-09-19. `build_runtime()` returns the constructed Korean frequency runtime and
supplies `ForbiddenAudioAdapter` through its runtime builder. The corresponding
regression test was also already present. This verification did not modify either
file or reproduce the historical missing-return failure; its first observed test
result was green. No red-before-fix result is claimed for this review.

## Verification

- The complete offline recovery test file passed: **12 passed in 7.49s**.
  It covers the returned runtime, authority and provider-policy arguments,
  forbidden audio adapter, protected artifact hashes, sidecar authorization,
  telemetry classification, cooldown, attempt limits, exclusive invocation
  markers in temporary directories, unit gating, and content-free log scanning.
- `--self-check-recovery` passed using local artifacts and synthetic telemetry.
- Both Python files compiled in memory, without producing bytecode files.
- The eight protected Plan 32-54/32-55 artifact hashes matched the constants in
  Plan 32-56. The recovery result envelope still reports `bounded_refailure` and
  binds the unchanged recovery preflight and invocation marker.
- Local scans of all 14 pending Plan 32-54/32-55/32-56 helper, test, and historical
  artifacts found no credential-shaped keys, raw database URLs, private home
  paths, or learner Hangul content. The helper's sample connection components
  are synthetic self-check fixtures. No `.env` secrets were loaded for this scan.
- Every directly imported project declaration used by the helper matches its
  committed declaration at `3c7c91a`. The referenced provider policy and prior
  production-job binding also match their committed bytes. Live execution still
  depends on the separately managed local frequency bundle and credentials;
  neither is required by these offline tests or included in this closeout.

Reproducible regression command:

```sh
env MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/planning/test_phase32_production_text_smoke_recovery.py -q -x --tb=short --timeout=180 --junitxml=.multilang/verification/korean-direct/phase32-smoke-helper-offline.xml
```

Offline self-check command:

```sh
env MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python .planning/phases/32-frequency-portuguese-text-and-audio/tools/production_text_smoke_20.py --self-check-recovery
```

The plan's `--verify-recovery-artifacts` command was deliberately not run:
its implementation loads production credentials and calls
`verify_recovery_result()`, which queries the production database. Local byte-hash,
envelope, binding, and artifact scans supplied the offline verification instead.
This follows the plan's explicit prohibition on production database access.

## Historical production result remains unchanged

The last recorded production evidence is dated 2026-09-09; production was not
queried during this verification. Plan 32-54 records two external rate-limited
attempts plus one aggregate failure row, zero generated text records, and no
second unit. Plan 32-55 records one consumed recovery invocation marker, zero
additional external attempts, and `bounded_refailure` before generation.
The evidence retains 20 candidates and zero generated texts, audio assets,
Azure calls, card exports, and deck exports. No 3000-item execution occurred.

The helper retains its historical schema anchor `20260828_19`. These artifacts
are an audit record of that bounded attempt, not current production preflight
evidence. The existing marker remains consumed; the local correction neither
removes it nor authorizes another invocation. A future production run requires
fresh bounded authority and current schema, policy, source, and review evidence.

No provider calls, production database reads or writes, recovery execution,
marker changes, audio generation, exports, or Git writes were performed in this
verification. Repository implementation completion is tracked separately from
the deferred production and delivery outcomes.
