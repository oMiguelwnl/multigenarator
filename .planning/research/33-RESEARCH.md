# Phase 33: Grammar and Personal Sources - Research

**Researched:** 2026-08-28
**Phase:** 33-grammar-and-personal-sources
**Requirements:** KGRAM-01, KGRAM-02, KPERS-01, KPERS-02, GJOB-01, GREV-01
**Confidence:** HIGH for application architecture and safety contracts; MEDIUM for the exact production grammar sequence pending licensed source review

## Executive Summary

Phase 33 should extend the existing Python/Pydantic/SQLAlchemy/Typer architecture rather than introduce a new framework. The implementation has four domain seams and one controlled integration seam:

1. A frozen Korean grammar bundle imports the exact active Phase 31 foundation snapshot and adds a reviewed lexicon/grammar overlay. Strict-i+1 is recomputed, never accepted from serialized claims.
2. Personal-source ingestion persists ordered row outcomes before lexical resolution, preserving submitted forms, exact duplicates, ambiguity, and explicit bridge/defer decisions.
3. Highlight excerpts, derived provider context, and generated microexamples are different typed artifacts. Remote context is absent unless an exact private-processing authority permits it.
4. Immutable field revisions, append-only review events, and per-item/per-stage outcomes replace in-place approval and coarse completion semantics for new Phase 33 work.
5. A coordinator-owned migration/ORM/CLI/export join happens only after the Phase 32 contracts and live Alembic head are settled.

The difficult part is not framework selection. It is preserving truth across graph validation, source identity, private data, optimistic review transitions, resumability, and exact upstream hashes. The safe default is fail-closed: missing source, identity, authority, approval, or exact audio produces `review_required`, `failed`, or blocked readiness rather than a heuristic fallback.

## Research Questions and Conclusions

| Question | Conclusion | Confidence |
|---|---|---|
| How should grammar build on Hangul/pronunciation? | Resolve the active Phase 31 snapshot once, bind all exact hashes, and import its concept IDs as the known root. Add a Phase 33 overlay; never mutate or duplicate Phase 31. | HIGH |
| Should Frequency Level 1 be required first? | No. Use a minimal, learner-visible grammar bootstrap with source-backed identities. Frequency membership is not mastery. | HIGH |
| How is strict-i+1 proven? | Recompute `unknown = observed - known_before` in sequence and require `unknown == {target}` for every strict grammar card. Review cannot override graph invalidity. | HIGH |
| What curriculum can be used? | KSIF publicly documents Introduction and levels 1-6 based on standard beginner/intermediate/advanced curricula, but its page does not itself establish a reusable construction-by-construction dataset or redistribution rights. Use it as sequencing guidance only until exact source and rights are reviewed. | MEDIUM |
| How should custom-list order and duplicates behave? | Persist one ordered outcome per nonblank submitted row. Exact normalized repeats reference the first row as `duplicate_of`; distinct forms remain distinct even when they resolve to one lexical identity. | HIGH |
| How should highlights be handled? | Analyze full text locally with Kiwi. Keep exact excerpt private; derive separately redacted, bounded context; generate a separate microexample. Only approved microexamples enter learner cards. | HIGH |
| How should provider context be authorized? | A fixed-power, hash-bound receipt must match run, sources, task, route, policy, cap, budget, ceiling, authorizer, and expiry. No receipt means context is `None` and no accidental disclosure. | HIGH |
| How should field review be persisted? | Immutable value/media revisions plus current/approved pointers and append-only events referencing revision IDs and hashes. Use atomic compare-and-swap transitions. | HIGH |
| How should resumability count work? | Persist outcomes per item and task/stage. `processed` is evidence; only accepted required work advances completion, while explicit approval remains a separate gate. | HIGH |
| Does Phase 33 need FastAPI or a web UI? | No. Thin Typer commands over transport-independent services are sufficient and avoid expanding the privacy/authentication surface. | HIGH |

## Standard Stack

### Core Libraries

| Library | Existing role | Phase 33 use | Why |
|---|---|---|---|
| Python 3.12 | Runtime | Domain services, hashing, graph validation, batch isolation | Existing project baseline and strongest fit for Korean NLP/data workflows |
| Pydantic v2 | Typed contracts | Frozen bundles, revisions, receipts, stage outcomes, CLI request validation | `extra="forbid"`, frozen models, validators, and controlled serialization support fail-closed boundaries |
| SQLAlchemy 2.0 | Persistence | Explicit repositories and short atomic transitions | Existing project pattern; supports session transactions and optimistic guarded updates |
| Alembic | Schema migration | Additive tables/columns after the unique live head is known | Existing schema parity workflow |
| Typer | Operator CLI | Review, bridge/defer, resume, and safe inspection commands | Existing injected CLI composition; no HTTP/auth expansion required |
| kiwipiepy/Kiwi | Korean morphology | Local lexical/morpheme analysis for custom forms and highlights | Existing Phase 30 authority and appropriate Korean token/POS analysis |
| `graphlib.TopologicalSorter` | DAG validation | Cycle and ordering checks for the grammar overlay | Standard library; already used by Korean curriculum code |
| pytest | Verification | Contract, mutation, repository, CLI, privacy, and integration tests | Existing project test stack |

### Use Existing Project Facilities

- Canonical Korean JSON hashing and frozen contract patterns.
- `KoreanConcept` and `KoreanCurriculumEvidence` rather than a second graph vocabulary.
- `resolve_active_korean_foundation_snapshot()` as the only production Phase 31 entry point.
- Phase 30 NFC, script validation, source-backed identity, analyzer fingerprint, and fail-closed matching.
- Existing highlight private/safe persistence split, tightened with revision and authority contracts.
- Existing typed text/audio provider boundaries, with context authorization added before adapter invocation.
- Existing normal/highlight Anki layouts, field order, blank image policy, source modes, and GUID formulas.

### Do Not Add

- FastAPI, HTTP routes, a browser review dashboard, authentication, or remote callbacks.
- A second Korean analyzer, top-1 resolver, suffix/substring fallback, or provider-authored lexical identity.
- A workflow engine, event broker, distributed lock, worker pool, or PostgreSQL claim system; bounded workers remain Phase 34.
- A new Anki note type or GUID algorithm.
- Production grammar assets sourced from synthetic fixtures or unreviewed model output.

## Architecture

### 1. Grammar Bundle and Registry Overlay

Use one immutable root object whose members are independently hash-bound:

```text
KoreanGrammarBundle
  phase31_binding
    bundle_sha256
    receipt_sha256
    snapshot_manifest_sha256
    snapshot_root_sha256
    concept_registry_member_sha256
  source_pack_binding
  registry_overlay
  lexical_bootstrap
  grammar_entries
  review_bindings
  media_bindings
  member_hashes
  bundle_sha256
```

The resolver must read the active Phase 31 pointer once. Downstream services receive the immutable resolved object rather than rereading mutable state. The Phase 33 overlay may reference imported IDs and add `lexicon` and `grammar` concepts, but imported concepts are immutable.

Validate:

- canonical `ko` identity and NFC;
- exact upstream hashes and member existence;
- unique concept IDs across imported and overlay sets;
- referenced prerequisite existence;
- acyclicity and sequence order;
- complete transitive prerequisite closure;
- stable construction IDs and one target per grammar entry;
- serialized versus recomputed evidence equality;
- no repeated target and no hidden unknown;
- exact source/review/media bindings before learner-ready status.

### 2. Curriculum Progression

KSIF's official curriculum page documents this broad public progression:

- introductory Korean centered on Hangeul/basic vocabulary;
- beginner levels 1-2 based on standard beginner vocabulary and grammar expressions;
- intermediate levels 3-4 based on standard intermediate vocabulary and grammar expressions;
- advanced levels 5-6 based on standard advanced curriculum;
- beginner and intermediate basic programs each contain 40 lessons, while the introductory program contains 12 lessons.

This supports a staged beginner-to-advanced model but not direct extraction of a redistribution-ready grammar inventory. Implement the user-approved G0-G13 category outline as a versioned internal source pack with explicit provenance. Before any entry is production-approved, require:

- exact source and source-version identity;
- a documented license/use decision;
- linguistic review of form, function, attachment/allomorph, and register;
- modern Standard-Seoul applicability;
- Portuguese definition/translation review;
- strict graph recomputation;
- exact audio binding and review where audio is required.

Recommended broad ordering remains:

```text
G0  predicate-final structure and stems
G1  core particles and polite present
G2  location, existence, and possession
G3  additive, restrictive, and comitative particles
G4  direction, range, and comparison
G5  negation and tense/aspect
G6  desire, ability, request, and honorific constructions
G7  reviewed irregular paradigms split into atomic targets
G8  connectors
G9  adnominals
G10 nominalization and dependent nouns
G11 speech levels
G12 modality
G13 reported, passive, causative, and discourse constructions
```

The categories are planning order, not atomic cards. Broad concepts such as “irregular verbs” or “speech levels” must be split until each learner card introduces one form-function-register construction.

### 3. Strict-i+1 Algorithm

Reuse the existing graph evidence semantics:

```python
known = set(phase31_imported_concepts)

for bootstrap in ordered_bootstrap:
    validate_source_backed_identity(bootstrap)
    validate_observed_and_prerequisites(bootstrap, known)
    known.add(bootstrap.target_concept_id)

for card in ordered_grammar_cards:
    observed = tuple(card.evidence.observed_concept_ids)
    recomputed_unknown = tuple(
        concept_id for concept_id in observed if concept_id not in known
    )
    if recomputed_unknown != (card.target_concept_id,):
        raise StrictCurriculumError("exactly one target construction required")
    known.add(card.target_concept_id)
```

Every learner-visible lexical, orthographic, phonological, morphological, attachment/allomorph, and active-register concept must be represented. A reviewer can reject or approve linguistically valid content, but cannot approve a false graph.

### 4. Grammar Projection

Keep structured source data separate and project deterministically into the existing normal card:

```text
word             <- approved construction form
IPA              <- approved pronunciation/display policy
Definitions      <- approved function + attachment/allomorph + register
Example Sentence <- approved Korean microexample
Translation      <- approved Portuguese translation bound to that sentence
word_audio       <- approved spoken-form/carrier-context artifact
sentence_audio   <- approved exact-sentence artifact
Image            <- ""
```

The template must not infer grammar or register. A bound morpheme is synthesized from an approved spoken form or minimal carrier context, not as an unexplained raw fragment.

### 5. Ordered Custom-List Ledger

Parsing and resolution are separate stages. Persist every nonblank row first:

```text
PersonalSourceRow
  row_id
  job_id
  input_position
  submitted_form
  canonical_nfc
  normalized_duplicate_key
  duplicate_of_row_id?
  resolution_status
  lexical_identity?
  adaptive_evidence?
  prerequisite_decision?
```

Rules:

- Input position is monotonically assigned across parsed entries, including multiple entries from one source line.
- The ordered source fingerprint includes framed canonical entries and positions; reordering changes it.
- Stable item identity remains separate from run/source fingerprint and existing export GUID semantics.
- The first exact normalized occurrence is card-bearing.
- Later exact normalized occurrences remain visible outcomes referencing the first row.
- Distinct submitted forms remain distinct rows even when they resolve to the same lemma/POS/sense.
- Repository, review, and report order is `input_position`, not item-key sort.

Lexical resolution remains source-backed and morphology-aware. Ambiguity, OOV status, missing sense, analyzer drift, or conflicting POS yields `needs_review`. A model cannot invent the identity.

### 6. Bridge, Defer, and Review Decisions

Adaptive prerequisite assessment produces evidence and a proposal, never an automatic deck mutation:

```text
needs_review -> bridge
needs_review -> defer
bridge       -> needs_review  (policy or dependency drift)
defer        -> needs_review  (policy or dependency drift)
```

`bridge` stores the exact approved prerequisite concept/card references and may schedule them before the dependent item. `defer` preserves the item and position but blocks current generation/export. Relative ordering among user-submitted rows never changes.

The threshold and scoring algorithm may be selected during implementation, but must be deterministic, versioned, persisted, and invalidating on policy drift.

### 7. Highlight Privacy Boundary

Use three explicit artifact types:

| Artifact | Contains | Storage/exposure |
|---|---|---|
| Private excerpt revision | Exact parser-normalized highlight and private source linkage | Private local revision store only |
| Provider context revision | Deterministically redacted, target-centered, bounded derivative | Private store; value disclosed only under exact authority |
| Microexample revision | Generated learner sentence, provenance, validation, dependencies | Review store; only approved value can be exported |

Kiwi runs locally over the bounded full highlight before generic token-length or stopword filtering. Preserve one-syllable lexemes, attached `J*` particles, `E*` endings, complete compound predicates, first-source order, and occurrence counts. Deduplicate by complete source-backed lemma/POS/sense identity within an exact excerpt scope, not by whitespace tokens.

The source excerpt is contextual evidence and must never be copied into the learner `Example Sentence` field. Exact excerpt/path/book/location data are absent from safe manifests, ordinary CLI output, telemetry, errors, and exports.

### 8. Private Provider Context Authority

Sanitization is necessary but not authorization. Define a fixed-power receipt with at least:

```text
authority_id
job_id / run_key
source_hashes
task
provider and model route hash
purpose
redaction_policy_version
max_context_tokens (<= 24)
item and attempt ceilings
budget ceiling where applicable
authorized_by
authorized_at
expires_at
receipt_sha256
```

Validation occurs before typed request construction and again at the provider boundary. Missing, expired, route-drifted, source-drifted, policy-drifted, or exhausted authority returns no context and prevents any context-bearing provider call.

Treat provider context as untrusted data. It can guide sense/example generation only; it cannot set lexical identity, graph truth, authority, route, tool behavior, approval state, or instructions. This addresses prompt-injection and sensitive-information disclosure risks identified by OWASP for LLM applications.

Telemetry stores authority ID, hashes, policy version, attempts, bounded metrics, status, and controlled redacted errors. It never stores context, exact excerpt, prompt, completion, path, raw analyzer output, or provider payload.

### 9. Immutable Field Revisions

Recommended relational design:

```text
field_revisions
  immutable value or media reference
  canonical content/artifact hash
  field name and revision number
  provenance and creator
  validation/review state
  dependency revision IDs and hashes
  policy identities and timestamps

current_field_revisions
  selected_revision_id
  approved_revision_id?
  optimistic_version

field_review_events
  action
  before_revision_id/hash?
  after_revision_id/hash?
  actor and controlled reason
  validation/policy snapshot IDs
  timestamp
```

Revisions and events expose insert/list/get operations only. They do not expose update/delete methods. Current pointers are mutable only through one service-owned atomic transition.

Use a compare-and-swap condition such as:

```sql
UPDATE current_field_revisions
SET selected_revision_id = :new_revision_id,
    approved_revision_id = :approved_revision_id,
    optimistic_version = optimistic_version + 1
WHERE job_id = :job_id
  AND item_key = :item_key
  AND field_name = :field_name
  AND optimistic_version = :expected_version;
```

Require exactly one updated row. Zero rows is a deterministic stale-base conflict; it must leave no revision/event/pointer partial state. Provider calls and expensive validation happen before the short transition transaction.

Transition semantics:

- `edit` and `regenerate` create one field-local `needs_review` candidate.
- Regeneration never changes an approved pointer automatically.
- `reject` records an event and retains the last approved revision.
- `approve` moves the approved pointer after validation and expected-base checks.
- Changed sentence approval marks only bound translation and sentence-audio dependents stale/review-required.
- Prior revisions remain reconstructable through event references and hashes.

Pydantic's frozen models prevent application-level reassignment but are not a database immutability guarantee. Repository APIs, table permissions where available, and tests must enforce append-only behavior.

### 10. Item/Stage Outcomes and Resume

Persist outcome truth by item and task/stage:

```text
pending -> processing -> accepted
                      -> review_required
                      -> failed
```

Each outcome stores controlled stage/task, processed timestamp, attempt count, reason code, and exact input/output/authority/policy hashes. Required stages include, where applicable:

- ingest;
- lexical resolution;
- definition;
- sentence;
- translation;
- review;
- word audio;
- sentence audio;
- prepared export readiness.

`processed` is metadata, not a successful state. Automatic validation acceptance is also not explicit human/AI-policy approval. Final readiness is derived from required accepted outcomes plus current approved revisions and exact dependency hashes.

Default resume behavior:

- skip accepted current work;
- retry pending and policy-retryable failed work idempotently;
- leave review-required fields for explicit review/edit/regeneration;
- reject stale input, revision, authority, or policy identities;
- isolate one item/task exception and continue the bounded batch;
- stop only for a global authority, policy, or budget circuit breaker;
- derive aggregate counts from persisted outcomes rather than mutable counters.

Reports distinguish attempted, processed, accepted, review-required, failed, skipped-current, and not-attempted denominators.

### 11. CLI Surface

Add one coherent Typer group over injected services. Exact names are implementation discretion, but the capabilities are:

- list items and fields by job/source/outcome/review state in input order;
- inspect exact revision metadata;
- approve or reject one exact revision;
- edit or regenerate one exact field;
- record bridge or defer for one personal-source item;
- resume eligible item/stage work.

Mutating commands require job, item, field, revision, expected base/current identity, actor, and controlled reason as applicable. Do not add `--force`, `--allow-unapproved`, arbitrary provider/model/module/template/path/URL options, publication commands, or privacy bypasses.

Default output contains IDs, hashes, states, counts, and controlled reason codes. Private values require an explicit local display option and remain absent from aggregate JSON and error output.

## Data and Migration Guidance

### Additive Schema

Prefer new tables and nullable compatibility columns. Do not reinterpret historical mutable text/audio rows as immutable history. Potential tables include:

- `personal_source_rows`;
- `personal_source_decisions` or immutable decision events;
- `private_content_revisions` if not represented safely by generic field revisions;
- `field_revisions`;
- `current_field_revisions`;
- `field_review_events`;
- `generation_item_stage_outcomes`;
- grammar bundle/evidence references where persistence is required.

Use explicit keys, named unique constraints, bounded strings, timezone-aware timestamps, check constraints for controlled vocabularies, and indexed foreign keys. Composite indexes should match actual equality-prefix list/resume queries, for example:

- `(job_id, input_position)`;
- `(job_id, outcome, input_position)`;
- `(job_id, item_key, stage)`;
- `(job_id, item_key, field_name, revision_number)`;
- `(job_id, item_key, field_name)` for current pointers.

Do not create the migration until Phase 32 has settled a unique Alembic head. One integration owner must coordinate the migration, ORM, repositories, CLI signature, and schema-parity tests.

### Transaction Boundaries

- Never hold a database transaction during a provider call or remote read.
- Use database uniqueness plus atomic insert/conflict handling rather than SELECT-then-INSERT races.
- Insert a candidate, change pointers, mark dependents stale, and append the event in one transaction.
- Roll back only the affected item/task transaction on operational failure.
- SQLite remains single-concurrency for this phase; do not claim multi-worker safety.

## Security and Privacy

### Threats

| Threat | Required mitigation |
|---|---|
| Prompt injection in highlight text | Treat excerpt/context as delimited untrusted data; it cannot control identity, route, authority, tools, or approval |
| Sensitive excerpt/path disclosure | Separate private and safe stores; content-free telemetry/output; exact authority before context release |
| Excessive LLM agency | Providers propose text only; deterministic code owns identity, graph, policies, transitions, and publication gates |
| Unbounded provider consumption | Exact route, item/attempt, token/context, expiry, and budget authority; idempotent task identities |
| Output hallucination | Typed bounded schemas, source grounding, deterministic validators, review-required outcomes, no identity invention |
| Approval overwrite/race | Immutable revisions, append-only events, compare-and-swap pointers, atomic transitions |
| Error leakage | Controlled reason codes, `hide_input_in_errors`, no raw payloads/tracebacks in persisted/public output |
| Path/file abuse | Fixed local import boundaries; no arbitrary path/URL/provider switches in Phase 33 review commands |

### Authority Separation

These remain separate powers:

- source/license approval;
- private provider processing;
- paid provider spend;
- production database mutation;
- production synthesis;
- asset commit;
- local learner-ready activation;
- publication/distribution.

One approval never implies another. Planning and offline implementation authorize none of them.

## Testing Strategy

Follow test-driven development and begin with failing contracts.

### Contract and Domain Tests

- Frozen/forbid-extra/bounded grammar, personal-source, revision, authority, and outcome models.
- Canonical JSON hashing and NFC behavior.
- Imported/overlay concept collision, missing prerequisite, cycles, forward edges, closure, repeated target, and exact-one-unknown mutations.
- Production fixture refusal when source/review/upstream hashes are synthetic or absent.
- Ordered rows, visible exact duplicates, same identity with distinct submitted forms, reordered fingerprints, and stable existing GUID behavior.
- Ambiguous/OOV/analyzer-drift Korean forms remain review-required.

### Privacy and Provider Tests

- Full excerpt remains local and absent from safe manifests, telemetry, output, errors, and export.
- No authority produces `None` context and zero adapter calls.
- Expired, wrong source, wrong task, wrong route, over-budget, exhausted, or policy-drifted authority fails before provider invocation.
- Context is target-centered, redacted, and never over 24 tokens.
- Prompt-like excerpt text cannot alter authority, route, identity, or command behavior.
- Only approved generated microexamples are export-eligible.

### Repository and Migration Tests

- Revision/event rows are insert-only through public repositories.
- History reconstructs exact before/after values through revision references and matching hashes.
- Events contain no private values or media bytes.
- Two-session stale-base approval yields one winner and one controlled conflict.
- Failure during pointer/event/dependency transition rolls back all related writes.
- Changed sentence stales only declared translation/sentence-audio dependencies.
- Upgrade, downgrade, re-upgrade, sole head, ORM parity, foreign keys, constraints, and indexes.

### Job and CLI Tests

- Processed does not imply accepted or completed.
- Review-required and failed audio remain incomplete.
- One item exception does not abort remaining eligible items.
- Resume skips current accepted work and does not duplicate revisions, events, or provider calls.
- Aggregates are reconstructed from stage outcomes even when old counters are deliberately inconsistent.
- Exact option allowlists and injected service calls.
- No hidden network/provider construction in validation/refusal paths.
- Private display is explicit and local; default JSON/errors are content-free.

### Integration and Regression Tests

- Offline synthetic grammar flow from exact fixture snapshot through strict graph, review revisions, and normal-card projection.
- Ordered custom list through lexical outcomes, explicit bridge/defer, review, and prepared row order.
- Local highlight flow through Kiwi extraction, private excerpt persistence, absent-authority refusal, approved microexample, and highlight projection.
- Existing Korean Phase 30/31 behavior plus frequency, custom-list, highlight, Japanese, Mandarin, Latin, phoneme, audio, template, field-order, source-mode, and GUID regressions.
- Poison network, provider, asset publication, and production mutation facilities in offline tests.

Phase 33 tests may prove prepared rows and contract truth. They must not claim observed Anki Desktop/mobile import, rendering, font behavior, responsive behavior, or playback; Phase 34 owns those claims.

## Recommended Implementation Order

1. Add failing grammar overlay/bundle and exact Phase 31 join tests; implement frozen contracts and graph recomputation.
2. Add failing ordered personal-source ledger and adaptive decision tests; implement parser/fingerprint-compatible contracts and service logic without shared integration edits.
3. Add failing private excerpt/context/microexample tests; implement exact authority and no-context refusal before provider wiring.
4. Add failing immutable revision/event and optimistic conflict tests; implement domain, repository, and review service.
5. Add failing per-item/per-stage outcome and resume tests; implement truthful state and aggregate derivation.
6. After Phase 32 contracts and Alembic head settle, perform one coordinator-owned ORM/migration/repository integration.
7. Add the thin CLI group and exact safe-output tests.
8. Join grammar/custom/highlight approved revisions to existing card assembly while preserving templates, fields, GUIDs, and blank image.
9. Run focused, integration, migration-parity, privacy, and full regression suites.

## Suggested Plan Decomposition

The work is large enough for six execution plans with narrow write ownership:

| Plan | Goal | Primary ownership |
|---|---|---|
| 33-01 | Grammar bundle, exact Phase 31 root, overlay, strict graph | New grammar domain/service and focused tests |
| 33-02 | Ordered custom-list ledger, morphology-aware identity, bridge/defer | New personal-source domain/service plus parser/fingerprint coordination |
| 33-03 | Private highlight revisions and exact provider-context authority | Highlight/private-context services and focused privacy tests |
| 33-04 | Immutable field revisions, review service, and dependency invalidation | New revision domain/repository/service and tests |
| 33-05 | Per-item/per-stage outcomes, resume truth, additive migration | Job contracts plus coordinator-owned ORM/repository/migration join |
| 33-06 | CLI, approved projection, offline E2E, and regressions | Coordinator-owned shared integration surfaces |

Plans 33-01 through 33-04 can begin from new-file lanes, but shared dirty files must not be edited concurrently. Plan 33-05 waits for the unique post-Phase-32 migration head. Plan 33-06 integrates only exact landed contracts.

## Pitfalls to Avoid

- Treating the existence of a Phase 31/32 file as active authority.
- Copying or mutating the Phase 31 concept registry.
- Requiring Frequency Level 1 or silently assuming bootstrap vocabulary known.
- Serializing `unknown_concept_ids` without recomputation.
- Making one broad grammar category equal one target card.
- Copying curriculum content without source/version/license evidence.
- Dropping duplicate input rows or sorting items by normalized key.
- Collapsing distinct submitted forms after lemma resolution.
- Auto-inserting bridge cards or creating an adaptive queue.
- Treating sanitization as provider-disclosure authorization.
- Exporting exact highlights as example sentences.
- Recording private values in audit events or provider telemetry.
- Updating approved values in place.
- Marking successful synthesis or processing as approval/completion.
- Catching an exception around the entire batch rather than one item/task.
- Holding database transactions around provider calls.
- Creating a Phase 33 migration from an unsettled Phase 32 head.
- Changing note type, field order, source mode, template, or GUID semantics.

## Open Production Gates

The implementation can complete offline while these remain blocked:

- exact active approved Phase 31 snapshot at execution time;
- settled Phase 32 lexical/provider/audio contracts and hashes;
- reviewed grammar source pack and redistribution/use decision;
- reviewed lexical bootstrap identities;
- global AI-policy review evidence for grammar and generated content;
- exact provider/model/route/budget authority;
- exact private-processing authority for any highlight context;
- approved `ko-KR` voice/profile and exact audio integrity/review evidence;
- asset-commit, production-mutation, activation, and publication authority.

Missing gates produce complete offline machinery plus blocked or review-required records. They do not justify fabricated production content.

## Sources

### Official Framework and Runtime Documentation

- Pydantic models and configuration: https://docs.pydantic.dev/latest/concepts/models/
- Pydantic validators: https://docs.pydantic.dev/latest/concepts/validators/
- SQLAlchemy session transaction management: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
- SQLAlchemy version counters/optimistic concurrency: https://docs.sqlalchemy.org/en/20/orm/versioning.html
- Alembic operations: https://alembic.sqlalchemy.org/en/latest/ops.html
- Typer subcommands: https://typer.tiangolo.com/tutorial/subcommands/
- Python `graphlib`: https://docs.python.org/3/library/graphlib.html
- PostgreSQL constraints: https://www.postgresql.org/docs/current/ddl-constraints.html
- PostgreSQL index ordering: https://www.postgresql.org/docs/current/indexes-ordering.html

### Korean Language and Curriculum

- Kiwi/kiwipiepy documentation: https://bab2min.github.io/kiwipiepy/
- Online King Sejong Institute curriculum: https://www.iksi.or.kr/lms/main/curriculum.do
- National Institute of Korean Language: https://www.korean.go.kr/

### AI Security and Risk

- OWASP Top 10 for LLM Applications: https://genai.owasp.org/llm-top-10/
- OWASP LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OWASP LLM02 Sensitive Information Disclosure: https://genai.owasp.org/llmrisk/llm02-sensitive-information-disclosure/
- OWASP LLM06 Excessive Agency: https://genai.owasp.org/llmrisk/llm06-excessive-agency/
- OWASP LLM10 Unbounded Consumption: https://genai.owasp.org/llmrisk/llm10-unbounded-consumption/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework

### Project Evidence

- `.planning/SPEC.md`
- `.planning/ROADMAP.md`
- `.planning/phases/33-grammar-and-personal-sources/33-APPROACH.md`
- `.planning/phases/33-grammar-and-personal-sources/33-PATTERNS.md`
- `.planning/phases/30-korean-contracts-and-morphology/30-VERIFICATION.md`
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-32-PLAN.md`
- `.planning/phases/32-frequency-portuguese-text-and-audio/32-01-PLAN.md`

## Research Readiness

The architecture, safety boundaries, dependency joins, state semantics, and testing approach are sufficiently resolved for planning. The exact production grammar inventory remains intentionally gated on source/version/license and linguistic review; plans should implement the machinery and refusal behavior without inventing learner-ready content.

---

*Research completed: 2026-08-28*
