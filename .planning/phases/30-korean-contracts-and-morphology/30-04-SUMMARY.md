---
phase: 30-korean-contracts-and-morphology
plan: "04"
subsystem: korean-source-grounding-and-private-highlights
runtime: opencode
assurance: self_checked
tags: [korean, kiwi, morphology, lexical-identity, highlights, privacy, pydantic, tdd]
requires:
  - 30-01
  - 30-02
  - 30-03
provides:
  - Deterministic cached source-signature catalog with exact two-alternative consensus
  - One source-backed Korean identity path for frequency, word-list, and highlight inputs
  - Analyzer-backed private highlight extraction shared by preview and ingestion
  - Content-free Korean failures and generic serialization compatibility
affects: [30-05, 30-06, 30-07, 30-08, 33-korean-grammar-and-personal-sources]
tech-stack:
  added: []
  patterns:
    - Exact full ordered same-eojeol signature plus normalized source POS intersection
    - Source records remain the sole authority for lemma, POS, and sense identity
    - One injected morphology collaborator and project-owned fingerprint-keyed projections
    - Conditional Pydantic serialization for additive language-specific fields
key-files:
  created:
    - .planning/phases/30-korean-contracts-and-morphology/30-04-SUMMARY.md
  modified:
    - src/multilang/services/lexical_grounding.py
    - src/multilang/domain/highlights.py
    - src/multilang/services/highlight_candidate_extraction.py
    - src/multilang/services/highlight_import_preview.py
    - src/multilang/services/ingest_lexical_items.py
    - tests/services/test_lexical_grounding.py
    - tests/services/test_highlight_candidate_extraction.py
    - tests/services/test_highlight_import_preview.py
    - tests/services/test_highlight_ingest_lexical_items.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "A Korean binding passes only when explicit source-lemma analysis and both surface alternatives independently select the same exactly-one source lemma/POS/sense record by complete ordered same-eojeol signature plus normalized POS."
  - "Direct source binding rejects multi-eojeol source or surface analyses rather than accepting one matching word from a larger phrase."
  - "Korean highlights branch before every generic regex, NFKC, stopword, and length heuristic and expose only source identity plus existing hashes/indexes."
  - "Absent Korean identity and empty Korean extraction errors are excluded during serialization so generic language payload shapes remain unchanged."
patterns-established:
  - "Fail-closed source authority: morphology supplies evidence, while source inventory supplies lemma, POS, sense, and register."
  - "Private local analysis: raw highlights enter one injected resolver call and never cross the candidate/error persistence boundary."
requirements-advanced: [KMODE-01, KMODE-02, KNLP-01, KNLP-02]
requirements-completed: []
duration: 50m
completed: 2026-08-04
---

# Phase 30 Plan 04: Source-backed Korean Grounding and Private Highlights Summary

**Exact source-lemma/full-signature consensus now produces one durable Korean identity across frequency, word-list, and privacy-safe highlight paths while ambiguity, analyzer failure, and private context fail closed.**

## Performance

- **Execution duration:** approximately 50m
- **Completed checks:** 2026-08-04T19:08:29Z
- **Tasks:** 4/4
- **Execution-owned files created/modified:** 12, including this summary
- **Assurance:** `self_checked` (strict RED/GREEN cycles, real Python 3.12/Kiwi evidence, focused regressions, privacy scans, and high-leverage second pass)

## Accomplishments

- Built a deterministic Korean source catalog from `iter_candidates(language_code="ko")`, with NFC lemmas, explicit source POS normalization, nonblank source senses, and project-owned signature projections cached by analyzer fingerprint, lemma, POS, and sense.
- Required each top-two surface analysis to select exactly one catalog record by the complete ordered same-eojeol signature plus source POS, then required both alternatives to converge on the identical source lemma/POS/sense.
- Routed Korean frequency fixtures, submitted word-list forms, direct highlight grounding, and whole-highlight extraction through that one selector without frequency-seed, pronunciation, definition-provider, whitespace, substring, or suffix authority.
- Added a Korean extraction branch before generic regex/NFKC/stopword/length logic, retaining one-syllable words, attached-particle identities, compound predicates, full-identity homographs, canonical equivalents, first-seen provenance, and deterministic hashes.
- Passed the same injected resolver through count-only preview and actual ingestion, persisted exact identities without surface reanalysis, and kept raw excerpts/paths in the private highlight repository only.
- Preserved generic outputs by omitting empty Korean-only errors and absent Korean identity fields from Pydantic serialization.

## TDD Task Evidence

### Task 30-04-01: Build the deterministic source-signature catalog and exact record selector

- **RED:** The initial catalog/consensus command produced **9 failed, 47 passed** for absent real-Kiwi binding, deterministic source enumeration, exact signatures, source ambiguity, missing senses, POS conflict, unavailable/OOV analysis, fingerprint drift, and privacy-safe cache behavior.
- **GREEN:** Implemented `KoreanSourceBindingResult`, deterministic source projections, explicit POS mapping including `XSV -> verb` and `XSA -> adjective`, and exact top-two record consensus.
- **Final:** `uv run pytest tests/services/test_lexical_grounding.py tests/services/test_korean_morphology.py -q` produced **64 passed in 31.97s** after second-pass hardening.
- **Real Python 3.12/Kiwi:** The named `공부해요 -> 공부하다` test produced **1 passed, 39 deselected in 2.30s** with Python 3.12 through the isolated project environment.

### Task 30-04-02: Wire exact source selection into frequency, word-list, and highlight grounding

- **RED:** The mode-wiring additions produced **5 failed, 57 passed** for submitted-form retention, Portuguese output policy, frequency metadata, forbidden seed fallback, one-pass highlight resolution, and content-free failures.
- **GREEN:** Added early Korean branches to the existing grounding entry points and returned source identities or controlled pending/backfill outcomes before generic authority paths.
- **Final:** The exact task command produced **64 passed in 31.66s**.

### Task 30-04-03: Extract and preview privacy-safe Korean highlight identities

- **RED:** Korean extraction and preview tests produced **8 failed, 22 passed** for one-syllable nouns, particles, compounds, homographs, NFC/NFD, identity hashes, resolver failures, and count parity.
- **GREEN:** Added the typed candidate identity, Korean-first extraction, full-identity deduplication/hash payloads, controlled errors, and shared preview resolver seam.
- **Final:** `uv run pytest tests/services/test_highlight_candidate_extraction.py tests/services/test_highlight_import_preview.py -q` produced **30 passed in 0.36s**.

### Task 30-04-04: Wire shared Korean resolution through three-mode ingestion

- **RED:** Ingestion lifecycle tests produced **2 failed, 66 passed** for missing resolver injection and missing durable Korean identity handoff.
- **GREEN:** Passed the grounding service into Korean extraction, preserved private/public repository separation, persisted exact identity without surface reanalysis, and counted unresolved outcomes as blocked.
- **Final:** `uv run pytest tests/services/test_highlight_ingest_lexical_items.py tests/services/test_highlight_candidate_extraction.py tests/services/test_lexical_grounding.py -q` produced **71 passed in 6.79s**.

## Supplemental TDD and Second-Pass Evidence

- A forged persisted identity first passed source compatibility; the regression was added RED and then passed after exact catalog revalidation without surface reanalysis.
- A source-analysis outage initially collapsed to a missing-record result; a focused RED/GREEN cycle preserved the controlled `source_analysis_unavailable` outcome.
- Adding `resolution_errors` initially changed generic manifests; a focused RED/GREEN cycle limited that count to Korean manifests.
- Generic extraction initially serialized `errors: []`, then still serialized `korean_identity: null`; two **11-failure** RED runs drove `Field(exclude_if=...)` compatibility, followed by **11 passed, 14 deselected**.
- High-leverage review proved direct binding could accept one matching eojeol from a larger source/surface analysis. The new regression failed **1 test, 39 deselected**, then passed after requiring exactly one eojeol per direct source and surface alternative.
- Context7 Pydantic documentation confirmed field-level `exclude_if` applies to both `model_dump()` and `model_dump_json()`.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 grounding + morphology | `64 passed in 31.97s` |
| Real Python 3.12 named Kiwi binding | `1 passed, 39 deselected in 2.30s` |
| Task 2 grounding + morphology repeat | `64 passed in 31.66s` |
| Task 3 extraction + preview | `30 passed in 0.36s` |
| Task 4 ingestion + extraction + grounding | `71 passed in 6.79s` |
| Privacy/content-free focused selection | `10 passed, 66 deselected in 0.81s` |
| Existing local Kindle integration | `4 passed in 1.50s` |
| Existing frequency/word-list integration | `5 passed, 2 warnings in 24.79s` |
| Python compilation | Exit 0 with no output |
| Scoped patch whitespace check | Exit 0; only Windows LF-to-CRLF notices |
| Forbidden suffix/concatenation scan | No matches in the Plan 30-04 service files |
| Logging/path/prompt/vendor-leak scan | No matches in the Plan 30-04 public service files |
| Duplicate Kiwi construction scan | No matches in extraction, preview, ingestion, or grounding |

The two integration warnings are existing third-party Dateparser and Jsonlines warnings. No live provider, network, production lexical source, audio, template, export, or frequency-asset operation ran.

## Real Analyzer Evidence

The real pinned environment remained:

```text
Python: 3.12.13
kiwipiepy: 0.23.2
Kiwi model: 0.23.0
surface: 공부해요
source lemma: 공부하다
source POS: verb
resolved identity POS: VV
sense: fixture:study:1
signature: [(공부, NNG), (하, XSV)]
status: resolved
```

The record is explicitly synthetic/reviewed test evidence. It is not a production lexical asset or licensing decision.

## Files Created/Modified

### Created

- `.planning/phases/30-korean-contracts-and-morphology/30-04-SUMMARY.md` - TDD, source-consensus, privacy, regression, and handoff evidence.

### Modified

- `src/multilang/services/lexical_grounding.py` - Source catalog/cache, exact consensus, all-mode Korean branches, one-pass highlight resolver, existing-identity compatibility, and direct single-eojeol gate.
- `src/multilang/domain/highlights.py` - Optional validated Korean identity, controlled extraction error, and conditional language-specific serialization.
- `src/multilang/services/highlight_candidate_extraction.py` - Korean-first resolver branch, full-identity hashes/deduplication, and content-free failures.
- `src/multilang/services/highlight_import_preview.py` - Shared resolver injection while retaining count-only output.
- `src/multilang/services/ingest_lexical_items.py` - Korean resolver handoff, exact identity persistence, blocked counts, and Korean-only manifest error counts.
- `tests/services/test_lexical_grounding.py` - Catalog, exact consensus, mode wiring, privacy, real Kiwi, source compatibility, and multi-eojeol rejection evidence.
- `tests/services/test_highlight_candidate_extraction.py` - Korean units, homographs, normalization, failures, privacy, and generic serialization compatibility.
- `tests/services/test_highlight_import_preview.py` - Shared-resolver count parity and content-free preview evidence.
- `tests/services/test_highlight_ingest_lexical_items.py` - Disposable persistence lifecycle, private/public isolation, no-reanalysis, blocked outcomes, and generic regressions.
- `.planning/SPEC.md` - Current State advanced through Plan 30-04 without closing Phase 30.
- `.planning/.state-fingerprint.json` - Reviewed planning state rebaselined after the SPEC update.

## Git Actions

None. Per explicit user instruction carried forward for this milestone execution, no files were staged or committed, and no branch, push, PR, amend, reset, stash, clean, or other delivery action was performed.

## Decisions Made

- Kiwi evidence cannot author source identity. Only an explicit source record with nonblank POS and `sense_id` can supply lemma, POS, sense, and register.
- Source lemmas are analyzed under the same injected fingerprint as surfaces and cached only as project-owned immutable projections; vendor objects and private surfaces never enter the cache.
- Each direct source/surface analysis must contain exactly one eojeol. A matching word inside a larger phrase cannot promote the phrase into a lexical identity.
- Korean highlight text is analyzed once as a whole, then each aligned eojeol is independently intersected against the same source catalog; unresolved words are omitted and an entirely unresolved highlight produces a controlled error.
- Existing persisted Korean identity is checked against the current source catalog and fingerprint without rerunning surface morphology.
- Empty Korean-only fields are conditionally omitted rather than forcing generic callers to opt into `exclude_none` or `exclude_defaults` globally.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical validation] Revalidated supplied Korean highlight identity against source authority**
- **Found during:** Task 30-04-04 second pass.
- **Issue:** A typed identity carried by a candidate could bypass current source-record compatibility checks.
- **Fix:** Added exact fingerprint/lemma/POS/sense/register/signature catalog validation without reanalyzing the private surface.
- **Files modified:** `src/multilang/services/lexical_grounding.py`, `tests/services/test_highlight_ingest_lexical_items.py`.
- **Commit:** None by user instruction.

**2. [Rule 1 - Bug] Preserved unavailable source-analysis diagnostics**
- **Found during:** Source-catalog failure review.
- **Issue:** A source lemma whose analyzer call failed could be reported only as a missing source record.
- **Fix:** Retained project-owned observed issue metadata and returned the controlled `source_analysis_unavailable` outcome without exception or input content.
- **Files modified:** `src/multilang/services/lexical_grounding.py`, `tests/services/test_lexical_grounding.py`.
- **Commit:** None by user instruction.

**3. [Rule 1 - Regression] Kept Korean resolution counts out of generic manifests**
- **Found during:** Task 30-04-04 non-Korean regression pass.
- **Issue:** An unconditional zero-valued `resolution_errors` count changed existing generic manifest payloads.
- **Fix:** Added that count only for `SupportedLanguage.KO`.
- **Files modified:** `src/multilang/services/ingest_lexical_items.py`, `tests/services/test_highlight_ingest_lexical_items.py`.
- **Commit:** None by user instruction.

**4. [Rule 1 - Regression] Omitted absent Korean-only fields from generic serialization**
- **Found during:** Final generic output review.
- **Issue:** Additive fields serialized as `errors: []` and `korean_identity: null`, changing every generic extraction payload.
- **Fix:** Used documented Pydantic `Field(exclude_if=...)` behavior and added all-language serialization regressions.
- **Files modified:** `src/multilang/domain/highlights.py`, `tests/services/test_highlight_candidate_extraction.py`.
- **Commit:** None by user instruction.

**5. [Rule 1 - Bug] Rejected partial matches inside multi-eojeol direct analyses**
- **Found during:** Required high-leverage second pass.
- **Issue:** Catalog projection and direct surface selection could accept one matching eojeol while ignoring additional words, violating complete same-eojeol binding.
- **Fix:** Required every direct source and surface alternative to contain exactly one eojeol and fail with controlled existing invalid-analysis codes otherwise.
- **Files modified:** `src/multilang/services/lexical_grounding.py`, `tests/services/test_lexical_grounding.py`.
- **Commit:** None by user instruction.

**Total deviations:** Five correctness/security hardenings directly caused by this plan. No architecture, source-mode, provider, schema, production-data, template, export, or frequency-asset scope changed.

## Issues Encountered

- The first `uv run --python 3.12` attempt tried to replace the active `.venv`, whose executables were locked by VS Code language servers, and removed pytest from that environment. `uv sync --extra dev` restored it with no tracked impact.
- Real Python 3.12 verification then used `UV_PROJECT_ENVIRONMENT=C:/Users/MIGUEL~1.RAF/AppData/Local/Temp/opencode/multilang-30-04-py312`, avoiding the locked project environment while preserving the exact interpreter requirement.
- Existing Windows working-copy settings emit LF-to-CRLF notices during `git diff --check`; no whitespace error was reported.

## Security and Privacy Review

- Local highlight text is passed only to the one injected local resolver. Public candidates carry canonical identity, source content hash, first source index/ID, occurrence count, and item key—not excerpt, neighboring context, path, prompt, vendor token, or traceback.
- Resolver and source-inventory exceptions are collapsed into controlled reason codes; exception text is never serialized.
- Existing raw highlight storage remains isolated in `HighlightImportRepository`; lexical candidate persistence receives only safe provenance and the validated typed identity.
- Full identity keys include lemma, POS, and sense, preventing noun/predicate and distinct-sense homograph collisions.
- Source catalog records require explicit source-backed senses and normalized POS. Morphology, frequency seeds, providers, and submitted text cannot author a sense.
- No SQL, endpoint, authentication path, network call, schema migration, secret, production corpus, or unplanned trust boundary was added.

## Known Stubs

None. There is intentionally no approved production Korean source inventory, but that is an explicit plan non-goal and licensing blocker rather than a hidden implementation stub. Synthetic/reviewed records remain test-only.

## State and Handoff

- `.planning/SPEC.md` records Plans 30-01 through 30-04 complete while Phase 30 remains in progress.
- `.planning/ROADMAP.md` remains open at `[-]` and was not modified by this execution.
- No requirement checkbox was closed; `KMODE-01`, `KMODE-02`, `KNLP-01`, and `KNLP-02` still require later Phase 30 plans and phase verification.
- `node .planning/bin/gsdd.mjs session-fingerprint write` completed with fingerprint `4b67c2a36355a636787ffab7acc43115750ffad8629e125d3f1a6ed26efe0f1b`.
- Plan 30-05 can consume the exact durable identity and thread it through offline definition/sentence requests, grounded prompts, homograph-safe cache keys, and NFC provider-result boundaries without allowing provider output to reverse source authority.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All four RED/GREEN task cycles, every exact plan command, real Python 3.12/Kiwi evidence, generic source-mode integrations, privacy-focused serialization tests, compilation, heuristic/leak scans, and the required high-leverage second pass passed. Only existing dependency and Windows line-ending notices remain.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: passed
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: implementation_hardening
  impact: recoverable
  disposition: proceeded
  summary: Existing candidate identity is revalidated against exact current source evidence without private-surface reanalysis.
- class: diagnostic_correctness
  impact: recoverable
  disposition: proceeded
  summary: Source-analysis outages retain a controlled unavailable reason rather than collapsing to a missing record.
- class: anti_regression
  impact: recoverable
  disposition: proceeded
  summary: Korean-only manifest and Pydantic fields are absent from generic serialized outputs.
- class: exact_matching
  impact: recoverable
  disposition: proceeded
  summary: Direct binding now rejects source or surface alternatives containing more than one eojeol.
</deltas>

<judgment>
<active_constraints>
Keep `ko` as the sole internal language identity and `ko-KR` provider-only. Preserve NFC canonical values and exact submitted word-list evidence. Treat explicit source records as the sole lemma/POS/sense authority. Require exact full ordered same-eojeol signatures, one direct eojeol per alternative, the pinned top-two fingerprint, and same-record consensus. Keep raw highlights and paths private, and do not add production Korean records or frequency assets without approval.
</active_constraints>
<unresolved_uncertainty>
No approved production Korean lexical/frequency source or redistribution decision exists, so all successful records remain synthetic reviewed fixtures. Runtime provider composition, identity-aware request/cache contracts, generated-text acceptance, final runtime composition, audio, templates, and export evidence remain assigned to Plans 30-05 through 30-08 and later phases.
</unresolved_uncertainty>
<decision_posture>
Preserve ambiguity and block work rather than selecting a first sense or guessing a dictionary lemma. Reuse one injected morphology adapter and one source catalog contract across every mode. Carry exact validated identity forward; never reconstruct it from surface text after persistence.
</decision_posture>
<anti_regression>
Non-Korean extraction, preview, ingestion, frequency, and word-list payloads must keep their prior serialized shapes and behavior. Korean branches must remain before generic regex/NFKC/stopword/length and frequency-seed fallbacks. No later plan may use whitespace, substring, suffix stripping, morpheme concatenation, Kiwi token sense, or LLM output as Korean lexical authority.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All 12 execution-owned files exist, including the required summary, SPEC update, and state fingerprint.
- Every exact task command passed after the final high-leverage fix; supplemental integrations, privacy selection, compilation, and scoped whitespace checks also passed.
- The planning fingerprint write returned `4b67c2a36355a636787ffab7acc43115750ffad8629e125d3f1a6ed26efe0f1b` for the current ROADMAP/SPEC/config contents.
- Phase 30 remains open, no Plan 30-05-or-later summary exists, and no requirement was prematurely closed.
- Required structured sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) are present and substantive.
- The staging area is empty. No commit check applies because git delivery actions were explicitly prohibited.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 04*
*Completed: 2026-08-04*
