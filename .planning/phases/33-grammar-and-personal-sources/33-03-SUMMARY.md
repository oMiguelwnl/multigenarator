---
phase: 33-grammar-and-personal-sources
plan: "03"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 03 Summary

**Completed**: 2026-08-30
**Tasks**: 3
**Git Actions**: None; no staging, commit, or git config changes.
**Deviations**: `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were not updated because the direct execution request explicitly prohibited touching them.
**Decisions Made**: Highlight contracts now use frozen extra-forbid Pydantic models with hidden inputs in validation errors; provider-context metadata is hash-only and `not_disclosed` in this plan; microexample references are hash-only and export-eligible only when approved; Korean highlight analysis NFC-normalizes text before resolver calls while preserving exact source content hash scope.
**Notes for Verification**: All verification was offline with injected fixtures; no provider adapter, network constructor, export writer, or external path was invoked.
**Notes for Next Work**: Plan 04 owns private-processing authority/disclosure. This plan only establishes local morphology extraction, safe references, and typed artifact separation.

## Task Results

| Task | TDD Cycle | Result |
|---|---|---|
| 33-03-01 | RED: domain tests failed on missing private excerpt/provider-context/microexample imports. GREEN: added frozen private excerpt, safe reference, provider-context metadata, and microexample reference contracts. REFACTOR: line-wrap/readability cleanup with tests green. | Exact excerpt/provenance live only on `HighlightPrivateExcerptRevision`; safe references serialize IDs, hashes, indexes, and counts only. |
| 33-03-02 | RED: Korean NFC resolver test failed because NFD text reached the resolver; prompt/export reference test failed on missing safe serialization helper. GREEN: NFC-normalized Korean resolver input and added safe export reference serialization. REFACTOR: maintained scoped service change only. | Korean extraction keeps one-syllable, attached-form, compound, homograph, first-source order, complete identity, and excerpt-hash dedupe behavior without generic fallback. |
| 33-03-03 | RED: negative safe-model payloads and export-shaped reference tests proved missing rejection/serialization contracts. GREEN: added extra-forbid, controlled manifest count keys, bounded fields, hidden validation inputs, approved-only microexample export references, and no-strict contextual source labeling. | Safe candidates/manifests/errors/export-shaped references stay content-free and prompt-like text cannot alter identity, source index, authority, review, or policy fields. |

## Artifact Exposure Matrix

| Artifact | Exact excerpt | Private path/location | Provider context value | Learner microexample value | Safe serialization |
|---|---:|---:|---:|---:|---|
| `HighlightPrivateExcerptRevision` | yes | yes | no | no | local-only private model |
| `SafeHighlightExcerptReference` | no | no | no | no | IDs, hashes, source index, occurrence count |
| `HighlightProviderContextMetadata` | no | no | no | no | safe excerpt reference, context hash, redaction policy, bounded counts, `not_disclosed` |
| `HighlightMicroexampleRevisionReference` | no | no | no | no | safe excerpt reference, microexample hash, review state, adaptive/contextual evidence policy |
| `HighlightCandidate.to_safe_export_reference()` | no | no | no | no | candidate IDs/hashes/counts plus contextual source label and approved microexample hash/reference only |

## Extraction Goldens

| Case | Proven Behavior |
|---|---|
| One-syllable and attached forms | `물은` yields source-backed lemma `물` while preserving attached canonical form on the Korean identity. |
| Compound predicate | `공부해요` yields `공부하다` with compound lexical signature from local resolver identity. |
| Homograph identity | Same lemma with different POS/sense remains distinct; repeated complete identity increments occurrence count. |
| Excerpt scope | Same complete identity from distinct content hashes remains two candidates/private records. |
| First-source order | Candidates order by excerpt `source_index`, then resolver `word_position`; occurrence updates do not reorder first occurrence. |
| NFC/hash split | NFD/NFC Hangul reaches the resolver as NFC and shares the identity hash suffix, while exact source content hashes remain distinct. |
| Failure/fallback | Missing, empty, throwing, or malformed Korean resolution returns controlled errors and never enters generic token extraction. |
| Existing languages | Spanish candidate serialization remains unchanged by the new safe export helper. |

## Leakage Scan

| Surface | Result |
|---|---|
| Safe references | No exact text, source path, raw location, or normalized excerpt fields. |
| Safe manifests | Controlled count keys only; unknown prompt/payload/private-field inputs are rejected with hidden values. |
| Safe candidates | Unknown private/analyzer payload fields are rejected; Korean candidate identity must match lemma and complete lexical key. |
| Errors | Korean extraction errors expose only source index and reason code; no exception text, path, excerpt, prompt, payload, or analyzer dump. |
| Export-shaped reference | Emits contextual source evidence only, never `strict`, never exact excerpt, never provider context, and never review/authority fields from prompt-like text. |

## Verification

| Command | Result |
|---|---|
| `node .planning/bin/gsdd.mjs lifecycle-preflight execute 33 --expects-mutation phase-status` | allowed; warnings for pre-existing dirty canonical worktree and detached sibling worktrees. |
| `node .planning/bin/gsdd.mjs control-map --json` | completed; warnings matched acknowledged concurrent-lane dirty worktree state. |
| `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_highlights.py -k 'private_excerpt or safe_reference or provider_context or microexample or frozen or bounded or leakage or nfc' -q` | 7 passed, 1 deselected. |
| `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_highlight_candidate_extraction.py -k 'korean and (one_syllable or particle or ending or compound or homograph or order or excerpt or failure or fallback or nfc)' -q` | 10 passed, 20 deselected. |
| `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_highlights.py tests/services/test_highlight_candidate_extraction.py -k 'prompt or private or serialization or hash or contextual or existing or no_leak' -q` | 13 passed, 25 deselected. |
| `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_highlights.py tests/services/test_highlight_candidate_extraction.py -q` | 38 passed. |
| `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_kindle_highlight_parser.py tests/repositories/test_highlight_import_repository.py tests/services/test_highlight_ingest_lexical_items.py tests/services/test_lexical_grounding.py -q` | 59 passed in 152.42s after rerun with longer timeout; first 120s attempt timed out while progressing. |

## Bounded Claim

Plan 03 proves local Korean-first highlight morphology, complete identity/excerpt-hash dedupe, safe artifact separation, and content-free serialization/error boundaries. It does not claim provider disclosure authority, provider calls, learner-ready microexample content, export writer behavior, production persistence, or publication readiness.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified the scoped implementation with the three plan commands, full touched-file suites, and adjacent highlight parser/repository/ingestion/grounding regressions. Checked that safe models exclude exact excerpt/path/provider-context values and Korean failures do not fall through to generic extraction.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: unreviewed
plan_check_status: skipped
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `tests/domain/test_highlights.py` did not exist and was created as planned; `tests/domain/__init__.py` was already present from concurrent work and was not modified.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Lifecycle/control-map reported pre-existing dirty canonical and sibling worktree warnings; the direct request already acknowledged concurrent lanes, so execution stayed within the exact scoped write set.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: GSD state-update steps for SPEC, ROADMAP, and session fingerprint were intentionally skipped to honor the explicit no-touch constraint in the execution request.
</deltas>

<judgment>
<active_constraints>
Korean highlight analysis must run locally before any generic filters. One-syllable, attached-form, compound, homograph, and complete lemma/POS/sense identities remain source-backed. Exact excerpts, provider-context metadata, and generated microexamples are separate typed artifacts with separate exposure rules. Safe manifests, errors, reports, and export-shaped references must not contain exact excerpts, paths, book/location metadata, credentials, prompt/payload text, raw analyzer output, provider context values, or strict labels for authentic source text.
</active_constraints>
<unresolved_uncertainty>
Private retention/purge policy remains intentionally absent. Provider-context disclosure authority and any remote/private-processing route remain Plan 04 work. This plan does not validate production persistence of the new private excerpt revision type beyond domain/service contracts.
</unresolved_uncertainty>
<decision_posture>
Favor fail-closed local analysis and typed hash/reference boundaries over convenient excerpt reuse. Authentic highlight text is contextual evidence only; a generated microexample must be a separate approved artifact before it can be used as learner-facing content.
</decision_posture>
<anti_regression>
Do not add Korean generic fallback after resolver failure. Do not deduplicate Korean highlight candidates by lemma alone or across distinct excerpt content hashes. Do not serialize exact excerpt text, private paths, location/book metadata, provider context values, prompt/payload values, or analyzer dumps through safe candidates/manifests/errors/export-shaped references. Do not relabel authentic reading text as strict i+1 or as a generated microexample.
</anti_regression>
</judgment>
