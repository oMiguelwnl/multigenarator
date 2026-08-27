# Phase 31: Hangul and Pronunciation i+1 - Validation Strategy

**Updated:** 2026-08-27
**Scope:** Completed sequence 31-11 through 31-25 plus replacement sequence 31-29 through 31-32
**Requirements:** KHAN-01, KHAN-02, KPRO-01, KPRO-02
**Nyquist status:** Replanned; linguistic evidence is machine-readable AI-policy evidence, and only legal/provider/publication powers remain external authority.

## Validation Principles

1. Run the narrowest deterministic offline command during each task; do not defer first feedback to a later plan.
2. Every behavior-changing code task creates a named test first, witnesses an assertion failure, implements minimum GREEN behavior, then reruns its focused suite.
3. Draft selection, evidence confirmation, receipt identity, and activation authorization use fixed machine-readable artifacts or validated environment contracts. No command reads a hash from prose.
4. Candidate publication uses one immutable hash-named four-member bundle and one atomic pointer. Tests inject crashes and concurrent readers; four sibling file replacements are forbidden.
5. Linguistic judgment follows `.planning/AI-LINGUISTIC-REVIEW-POLICY.md`: two standard or three critical fresh-context passes plus non-overridable deterministic validators. AI never populates human qualification fields.
6. Failure occurs before canonical/output writes. Refusal is success when pending/inactive state is expected.
7. The complete offline Python 3.12 suite is the final gate after focused GREEN evidence, not a behavior-development feedback loop.

## Test Framework

| Property | Contract |
|---|---|
| Runner | `pytest` through `UV_OFFLINE=1 uv run --extra dev pytest` |
| Configuration | Repository `pyproject.toml`, `src`, and `tests` paths |
| Unit/service target | 5-120 seconds per focused command |
| CLI/integration target | 1-5 minutes per grouped command |
| Full-suite target | Expected 5-20 minutes only in 31-32-03, after focused GREEN; run once with `timeout 25m` and stop on timeout/failure |
| Network/provider policy | Offline; no provider or credential consumption in foundation operations |
| TDD plans | 31-11, 31-20, 31-21, 31-22, 31-23, 31-24, 31-25 |
| Historical user checkpoint | 31-20 candidate selection only |
| Parallel replacement plans | 31-29 common preflight; 31-30 and 31-31 parallel; exact join in 31-32 |

## Wave 0 And Prerequisite Tests

Plans 31-01 through 31-10 closed the original Wave 0 gaps. New test files are created before implementation by this sequence:

| Test file | Created by | Required first evidence |
|---|---|---|
| `tests/services/test_korean_foundation_ai_curation.py` | 31-11-01 | Named missing-contract RED |
| `tests/services/test_phase31_handoff.py` | 31-20-02 | Named fixed-handoff RED |
| `tests/services/test_phase31_runtime_isolation.py` | 31-25-01 | Named isolation-contract RED |

Existing curriculum, review, media, request, evidence, snapshot, export, CLI, integration, Korean, phoneme, template, Latin, and Mandarin suites remain regression prerequisites.

## Per-Task Validation Matrix

RED must exit exactly 1 through the expected assertion path. Collection, syntax, setup, or configuration errors never satisfy RED.

| Task | Automated validation | Target | Prerequisite/evidence |
|---|---|---:|---|
| 31-11-01 | Named curation-contract RED; full curation service GREEN | 5-45s | Immutable v1 inputs |
| 31-11-02 | Named fixed-script-surface RED; full curation service GREEN | 5-60s | 31-11-01 GREEN |
| 31-12-01 | Fixed `project-batch` + `validate-projection` for H0-H3 | 5-30s | 31-11 tooling |
| 31-12-02 | Fixed `validate-batch` for H0-H3 | 5-30s | Bounded projection and authored draft |
| 31-13-01 | Fixed `project-batch` + `validate-projection` for H4-H7 | 5-30s | Prior summary only; immutable v1 |
| 31-13-02 | Fixed `validate-batch` for H4-H7 | 5-30s | Bounded projection and authored draft |
| 31-14-01 | Fixed `project-batch` + `validate-projection` for H8-H10 | 5-30s | Prior summary only; immutable v1 |
| 31-14-02 | Fixed `validate-batch` for H8-H10 | 5-30s | Bounded projection and authored draft |
| 31-15-01 | Validate all three Hangul batches; fixed family assembly | 10-60s | Three valid stage drafts |
| 31-15-02 | Strictly read-only Hangul family validation | 5-30s | Complete 92-record family draft |
| 31-16-01 | Fixed `project-batch` + `validate-projection` for P0-P4 | 5-30s | 31-11 tooling |
| 31-16-02 | Fixed `validate-batch` for P0-P4 | 5-30s | Bounded projection and authored draft |
| 31-17-01 | Fixed `project-batch` + `validate-projection` for P5-P9 | 5-30s | Prior summary only; immutable v1 |
| 31-17-02 | Fixed `validate-batch` for P5-P9 | 5-30s | Bounded projection and authored draft |
| 31-18-01 | Fixed `project-batch` + `validate-projection` for P10-P13 | 5-30s | Prior summary only; immutable v1 |
| 31-18-02 | Fixed `validate-batch` for P10-P13 | 5-30s | Bounded projection and authored draft |
| 31-19-01 | Validate all three pronunciation batches; assemble and read-only validate family | 10-60s | Three valid stage drafts |
| 31-19-02 | Validate Hangul; assemble global manifest/report; strict global validation | 10-60s | Two complete family drafts |
| 31-20-01 | Strict global draft validation at read-only selection checkpoint | 5-30s | Exact manifest/report/31-19 summary |
| 31-20-02 | Named handoff RED; handoff GREEN; validated selection environment-to-JSON round trip | 5-60s | Exact `select-curation HASH` signal |
| 31-20-03 | Named structural/bundle primitive RED; curation + handoff GREEN; fixed `check-selection` | 10-120s | Current selection handoff |
| 31-21-01 | Named atomic-reader RED; focused then full curation GREEN with crash/concurrency cases | 10-120s | Promotion primitives; no candidate pointer |
| 31-21-02 | Getter-derived selection; fixed `promote`; read-only `verify-promoted` | 10-90s | Exact selection and immutable v1 |
| 31-22-01 | Named operation-absent RED; curation + request GREEN | 10-120s | Complete candidate bundle |
| 31-22-02 | Request projection test; fixed regenerate + verify; full request GREEN | 10-120s | Exact current-candidate pointer |
| 31-23-01 | Named default-v2 curriculum RED; Korean domain/curriculum GREEN | 10-120s | Bundle and requests |
| 31-23-02 | Named exact-v2/all-pending review-media RED; focused then full review + media GREEN | 30-180s | 31-23-01 GREEN |
| 31-24-01 | Named exact-v2 evidence RED; full evidence GREEN | 30-180s | First migration group GREEN |
| 31-24-02 | Named exact-v2/refusal snapshot-export RED; focused then full snapshot + export GREEN | 1-5m | 31-24-01 GREEN |
| 31-24-03 | Six migrated service suites together; protected-state digest equality | 1-5m | All migration tasks GREEN |
| 31-25-01 | Named runtime-isolation RED; full helper GREEN | 5-60s | Fixed temp/canonical prestates |
| 31-25-02 | CLI + integration suites with exact v2/GUID/refusal assertions | 1-5m | Coherent blocked v2 services |
| 31-25-03 | Exact shell refusals; exact Phase 30 focused matrix; exact normal/manual/highlight/Japanese/Mandarin/Latin/Russian existing-mode matrix; grouped foundation regressions | Each group <=5m | No genuine evidence or active pointer |
| 31-29-01 | Runtime fingerprint and parallel launch helper RED/GREEN | 10-180s | Plan 31-25 runtime helper |
| 31-29-02 | Frozen Python 3.12 sync plus clean common baseline/protected-state capture | 1-10m | Task 31-29-01 committed |
| 31-30-01 | AI-review contract RED/GREEN, non-impersonation, staleness, consensus truth table | 10-180s | Exact v2 candidates, global policy, common baseline |
| 31-30-02 | Parallel standard/critical review batches; deterministic aggregate and lane handoff | 1-10m | Fixed projections; no provider tools or mutation authority |
| 31-31-01 | Rights/provider/media preflight and exact authority handoff | 10s-10m | Common baseline and bounded external authority |
| 31-31-02 | 100% byte/decoder/acoustic validation plus AI acoustic review and lane handoff | 1-10m | Exact current media bytes |
| 31-32-01 | Seal exact final lane heads and verify/merge only their disjoint commits | 1-5m | Both lane commits/roots current |
| 31-32-02 | Integrate final consumers and stage source-bound receipt/snapshot/pointer/six outputs | 1-10m | Verified merged lane baseline |
| 31-32-03 | Inspect/test source-invariant staging, then all-or-nothing local install | Focused <=5m each; full 5-20m | Exact staged authority and safe fixed temp root |

## Slow-Command Strategy

- Commands expected over five minutes occur only for complete AI/media evidence inspection, immutable snapshot preparation, or the final full suite. They are validation gates over already-GREEN behavior.
- Plans 31-24/25/28 keep focused service, CLI, integration, and cross-mode commands grouped below five minutes before any slow gate.
- A slow command failure stops execution. Do not repair code, evidence, assets, state, dependencies, lockfiles, or `.venv` inside the gate.
- The final full suite runs once in fixed current-user mode-0700 `/tmp/multilang-phase31-py312`, directly beneath root-owned sticky `/tmp`, with a 25-minute timeout; timeout is failure, not permission to skip.

## Checkpoint And Hash Handoffs

| Authority event | Machine-readable source | Consumer | Missing/drift behavior |
|---|---|---|---|
| Draft selection | `select-curation HASH` -> `execution-handoffs/curation-selection.json` | 31-20/31-21 fixed getter | Stop before promotion; never repair stale/nonidentical state |
| Candidate visibility | Immutable `candidate-bundles/<hash>/` -> atomic `current-candidate.json` | 31-22 through 31-26 fixed resolver | Readers observe no/old or complete new bundle; conflict stops |
| Common parallel baseline | 31-29 local launch handoff | 31-30/31-31 lanes and 31-32 join | Different ancestry, overlap, or protected-state drift blocks |
| AI review root | 31-30 canonical aggregate/lane handoff | 31-32 join | Disagreement/uncertainty/staleness stops the affected records |
| Media/rights/acoustic root | 31-31 canonical aggregate/lane handoff | 31-32 join | Missing authority or byte drift stops media readiness |
| Receipt identity | Sole writer -> fixed `validation-receipt.json`; `get-receipt` hashes it | 31-32 | Drift fails continuity; no prose parsing |
| Local activation | Exact staged joined receipt/snapshot/outputs tuple | 31-32 | Test-before-install atomic local activation; publication remains separate |

Handoff JSON and the candidate pointer coordinate execution; neither is linguistic, legal, playback, receipt, or production activation evidence.

## Requirement Coverage

| Requirement | Automated evidence | Human-only evidence | Final bounded proof |
|---|---|---|---|
| KHAN-01 | Draft/v2 coverage, template/media joins, APKG/table/media inspection | Orthography, mnemonic/stroke, rights, exact playback | Active reviewed Hangul v2 plus six-output inspector; observed Anki remains Phase 34 |
| KHAN-02 | Graph/bootstrap/NFC/exactly-one-unknown suites and v2 structural equivalence | Curriculum atomicity acceptance | Receipt/snapshot retains exact strict-i+1 evidence |
| KPRO-01 | Nine-field completeness, placeholders, IDs/GUIDs, three-format media resolution | Korean phonetics, Portuguese policy/quality, exact playback | Active reviewed pronunciation v2 in APKG/CSV/TSV |
| KPRO-02 | P0-P13 coverage, rule/prerequisite/false-i+1 tests, structural projection | Six specialist scopes and item-level acceptance | Receipt/snapshot binds exact accepted P0-P13 evidence |

## External Authority And Observation Boundaries

- Source, attribution, license, reuse, transformation, redistribution, provider processing, and publication authority remain external.
- Linguistic, Portuguese, curriculum, pronunciation, and acoustic quality use the global AI policy.
- Audio decoder/acoustic evidence never claims that a human heard the bytes.
- Instrumented Anki Desktop/mobile evidence in Phase 34 must bind exact application, version, environment, artifact, and observation output.

AI and automation never manufacture legal authority or claim an observation method that was not used.

## Sampling And Escalation

- Curation validates every record; second passes revisit every uncertain/specialist-sensitive record and at least one record per stage.
- Migration validates every source/member/request join and compares protected-state hashes.
- Evidence validates 100% of records and exact bytes; rights, required media, and hashes are never sampled.
- Stop rather than widen when a command needs a provider, arbitrary source path, structural mutation, unsupported media, new public CLI option, fallback version, or authority bypass.

## Nyquist Checklist

- [x] Completed historical tasks and all nine replacement tasks have task-local automated validation.
- [x] Every behavior-changing task has explicit named RED and focused GREEN evidence.
- [x] New prerequisite test files are created before implementation.
- [x] Every remaining external-authority checkpoint has an exact resume signal and validated machine-readable handoff.
- [x] Candidate publication has crash/concurrency and single-pointer atomicity coverage.
- [x] Later plans derive hashes from fixed getters/canonical files, never summaries or placeholders.
- [x] Focused feedback precedes acknowledged slow gates.
- [x] AI, legal-authority, structural/integrity, acoustic, and device-observation claims remain explicitly separate.
- [x] Failure/refusal paths assert zero unauthorized mutation.
