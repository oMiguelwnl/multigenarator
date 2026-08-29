# Phase 33: Grammar and Personal Sources - Approach

**Explored:** 2026-08-28
**Status:** Ready for planning after user-confirmed approach exploration

## Alignment Proof

- `workflow.discuss`: true — `.planning/config.json` uses `discuss_mode="discuss"` and `skip_discuss=false`.
- `alignment_status`: user_confirmed
- `alignment_method`: A researched five-decision option matrix and the additional status/revision transition semantics were presented in the Phase 33 discussion. The user selected **"Aceitar todas (Recommended)"** and explicitly confirmed all recommendations.
- `user_confirmed_at`: 2026-08-28
- `explicit_skip_approved`: false
- `skip_scope`: N/A
- `skip_rationale`: N/A — discussion was completed and the user confirmed the recommended decisions.
- `confirmed_decisions`:
  - Use the exact active, approved Phase 31 foundation snapshot as the grammar known-state root, plus a small grammar-owned, learner-visible lexical bootstrap. Do not require Frequency Level 1 and do not treat grammar as standalone.
  - Use explicit `bridge`, `defer`, or `needs_review` decisions for custom-list ambiguity and excessive prerequisites. Never insert bridge cards automatically and do not create a v4-style adaptive queue.
  - Preserve every nonblank custom input row's immutable input position. Exact normalized duplicates become visible `duplicate_of` outcomes with only the first producing a card; distinct submitted forms remain distinct ordered items even when they resolve to the same lemma/POS/sense. Approved bridge cards may precede their dependent item without reordering user-submitted items.
  - Permit only bounded, redacted highlight context to reach a provider, and only under exact per-run private-processing authority. Without that authority, no highlight context is provider-visible.
  - Keep exact source excerpts in private local revisions, keep provider context as a separate derived/redacted/hash-bound artifact, and keep generated microexamples as separate reviewable content. Only the approved microexample and its audio are eligible for the existing highlight card fields.
  - Deliver Phase 33 through a CLI-first surface backed by service/repository contracts that can support a later API. Do not add FastAPI, a dashboard, or a review web UI in this phase.
  - Retain field history as immutable private revisions referenced by append-only audit events carrying before/after revision IDs and hashes. Do not copy field values into each event, and do not use hashes-only evidence that cannot reconstruct the change.
  - Treat `processed` as progress evidence rather than successful completion. Persist accepted, review-required, and failed outcomes separately; review or audio failures never count as completed, and one provider exception must not abort the remaining batch.
  - Regeneration creates a pending revision for only the selected field and never overwrites an approved revision. Rejecting a candidate leaves the last approved revision current. Approving a changed sentence makes the bound translation and sentence audio stale/review-required while retaining their prior revisions.

<domain>
## Phase Boundary

Phase 33 implements `KGRAM-01`, `KGRAM-02`, `KPERS-01`, `KPERS-02`, `GJOB-01`, and `GREV-01`:

- a reviewed Particles & Endings curriculum whose strict cards introduce exactly one form-function-register construction;
- a grammar-owned lexical bootstrap rooted in the exact approved Phase 31 foundation state;
- deterministic Korean custom-list ingestion with preserved submitted form, resolved identity, input order, and explicit bridge/defer outcomes;
- morphology-aware Korean highlight extraction with private excerpt, provider context, and generated microexample kept as different typed artifacts;
- item- and stage-level resumability that never mistakes processing, review, or failed audio for completion; and
- field-level list, approve, reject, edit, and regenerate operations backed by immutable revisions and auditable transitions.

The phase follows an **implement safely, bind exact upstream artifacts, and fail closed at external authority** posture:

- Offline contracts, additive migrations, deterministic fixtures, curriculum validators, review/revision services, CLI commands, refusal paths, and regressions may be completed without live providers or production assets.
- Production grammar known state must bind the exact active Phase 31 snapshot actually consumed.
- Production lexical identities, text routes, telemetry contracts, and Korean audio may consume Phase 32 artifacts only by exact version/hash; no dependency is inferred from a file merely existing.
- Missing upstream activation, source rights, private-processing authority, provider route/budget, AI-policy evidence, voice/profile approval, or exact media leaves the affected records blocked or review-required. It does not authorize a fallback.

### Requirement Disposition

| Requirement | Phase 33 implementation truth | Blocked/learner-ready truth |
|---|---|---|
| `KGRAM-01` | Versioned grammar/bootstrap source contracts, reviewed G0-G13 progression, normal-layout field projection, exact examples/translations/audio bindings, and readiness gates. | No learner-ready grammar claim while source, linguistic, Phase 31, provider, or exact-audio evidence is absent. |
| `KGRAM-02` | Import the exact Phase 31 known-state root, extend it additively with bootstrap/grammar concepts, recompute prerequisites/observed/unknown evidence, and require one construction target per strict grammar card. | A candidate flag or reviewer approval cannot rescue a false graph, hidden prerequisite, or non-atomic construction. |
| `KPERS-01` | Persist original row position, submitted form, NFC form, source-backed lemma/POS/sense, resolution evidence, duplicate outcome, and explicit bridge/defer/review decision. | Ambiguity, OOV evidence, excessive prerequisites, or analyzer drift never fabricates an identity or silently inserts content. |
| `KPERS-02` | Use local Kiwi extraction before deduplication; preserve one-syllable lexemes and attached morphology; type and separate exact excerpt, redacted context, microexample, and private provenance. | Exact/private context never enters ordinary persistence, telemetry, exports, provider payloads without authority, or scanner evidence. |
| `GJOB-01` | Add per-item/per-stage outcomes and processed facts; isolate exceptions; make resume idempotent; aggregate job status from persisted item truth. | Review-required and failed audio/text are never completed; a malformed/provider-failed item cannot stop the rest of the bounded batch. |
| `GREV-01` | Add field revisions, current approved pointers, append-only review events, dependency hashes, and CLI list/approve/reject/edit/regenerate operations. | Approved values are never updated in place; stale dependents and unresolved review states block learner-ready output. |

### Explicitly Outside This Phase

- Final all-family APKG/CSV/TSV closure, observed Anki Desktop/mobile import, rendering, font, responsive, and playback evidence, which remain Phase 34 work.
- Production worker leases/claims, PostgreSQL bounded worker rollout, and any SQLite concurrency increase beyond one, which remain under `GOPS-01` in Phase 34.
- A FastAPI surface, browser review dashboard, interactive review UI, authentication system, or remote private-content management.
- Frequency Level 1 as a grammar prerequisite, recuration of the 3000-entry frequency inventory, or mutation of frequency membership from personal-source history.
- v4 semantic GUID migration, form cards, APKG history import, learner mastery synchronization, adaptive prerequisite queues, and scheduling integration.
- Automatic publication, deck upload, redistributed-source commit, production database mutation, or paid/private provider use without separate exact authority.

</domain>

<decisions>
## Implementation Decisions

### Gray Areas Explored

| Gray area | Classification | Approaches researched | Locked disposition |
|---|---|---|---|
| Grammar learner baseline | Hybrid | Phase 31 + grammar bootstrap; Frequency Level 1 prerequisite; standalone grammar | Bind exact active Phase 31 and add the smallest reviewed learner-visible lexical bootstrap owned by grammar. |
| Custom ambiguity, prerequisites, duplicates, and order | Hybrid | Explicit decision ledger; automatic bridge insertion; adaptive queue | Persist explicit bridge/defer/review choices, never auto-insert, retain duplicate outcomes, and preserve user-row order. |
| Highlight context and excerpt semantics | Hybrid | No provider context; bounded redacted context with authority; full context to a local model | Allow bounded redacted provider context only with exact authority; keep exact excerpt local and microexample separate. |
| Delivery surface | Hybrid | CLI-first; CLI plus FastAPI | CLI-first with reusable application services; no API/UI expansion. |
| Audit retention | Technical | Copied before/after values; immutable revision references plus hashes; hashes only | Private immutable revisions plus append-only reference/hash events. |

### Grammar Authority, Bootstrap, and Frozen Inputs

**Chosen approach:** Build one versioned Phase 33 grammar bundle that imports, rather than copies or mutates, the exact active Phase 31 foundation authority and extends it with grammar-owned lexicon and grammar concepts.

**Why this approach:** Frequency Level 1 would impose a 1000-card, source/license/provider-dependent barrier before elementary grammar. A standalone grammar deck would hide orthographic, phonological, morphological, and lexical assumptions and could not prove `KGRAM-02`. The selected root supplies deterministic foundation knowledge while a bounded bootstrap teaches only the lexemes needed by grammar examples.

- Resolve the active Phase 31 snapshot once through the canonical snapshot boundary. Persist its bundle, receipt, and snapshot-root hashes in the Phase 33 bundle and downstream grammar evidence.
- Never read a mutable `current-candidate` pointer repeatedly during one operation. Resolve once, bind the immutable members, and reject pointer/hash drift before review or activation.
- Do not modify the Phase 31 concept registry or retroactively mark foundation candidates known. A Phase 33 registry overlay references imported concept IDs and adds stable `lexicon` and `grammar` IDs with collision, existence, acyclicity, closure, and sequence validation.
- The grammar lexical bootstrap is an explicit, ordered learner-visible prelude. Each bootstrap card targets one source-backed lexicon concept; it is not silently assumed mastered and is not counted as a grammar construction card.
- Keep the bootstrap no larger than the exact reviewed lexical prerequisites needed by approved grammar examples. It must not become an alternate frequency deck or a route around Phase 32 source/license decisions.
- Bootstrap identity selection is grammar-owned, but lemma/POS/sense authority is not. Reuse exact approved Phase 32 lexical records where available; otherwise a separately source-backed reviewed record is required. A provider or Kiwi cannot author sense identity.
- Store source pack, registry overlay, bootstrap inventory, grammar entries, review bindings, media bindings, and root/per-member hashes as immutable versioned artifacts. Corrections create a new version; they do not edit an approved snapshot in place.
- Committed candidate content may remain `needs_review`. Synthetic test fixtures may prove schemas and refusal behavior but cannot become production bootstrap or grammar authority.

### Strict Grammar Concept Graph and Progression

**Chosen approach:** Recompute strict curriculum evidence over the imported Phase 31 known root, the ordered lexical bootstrap, and the reviewed G0-G13 grammar progression.

- Preserve the approved progression categories: foundations of predicate-final structure and stems; core particles and polite present; location/existence/possession; additive/restrictive/comitative particles; direction/range/comparison; negation and tense/aspect; desire/ability/request/honorific; irregular paradigms; connectors; adnominals; nominalization/dependent nouns; speech levels; modality; and advanced reported/passive/causative/discourse forms.
- Each strict grammar card targets exactly one stable form-function-register construction concept. A pair such as `은/는` may be one concept only when its allomorph selection conditions are taught together and review confirms atomicity.
- Broad labels such as “irregular verbs,” “speech levels,” or “connectors” are not atomic targets. Paradigms and contrasts must be split until each card has one executable target and no hidden unknown.
- For every card, recompute:

  ```text
  known_before = approved Phase 31 concepts
               + validated earlier bootstrap targets
               + validated earlier grammar targets
  unknown = observed - known_before
  strict_pass = unknown == {target_concept_id}
  ```

- Require every lexical, orthographic, phonological, morphological, attachment, allomorph, and active register concept observed by the learner-facing form/example to exist in the graph.
- Require all declared prerequisites to precede the card and the target to occur in observed evidence. Reject repeated targets, unknown IDs, forward dependencies, missing active rules, serialized/recomputed disagreement, cycles, and source drift.
- Review and approval cannot override graph invalidity. AI-policy evidence assesses linguistic correctness and pedagogical atomicity; deterministic graph facts remain non-overridable.
- Use modern Standard-Seoul Korean. Default examples use everyday `해요체` unless the target construction itself teaches another register or exact context evidence requires it. Mixed unlabelled speech levels block review.
- Preserve canonical spelling, surface realization, function, attachment/allomorph rule, register, example, Portuguese translation, pronunciation/spoken sample, and provenance as separate source fields even where the normal learner layout renders a combined definition.

### Grammar Card Projection and Audio

**Chosen approach:** Reuse the normal Multilang learner layout without making the template calculate linguistic content.

- Project the reviewed grammar record as:

  ```text
  word             = reviewed construction form
  IPA              = reviewed pronunciation or approved display policy
  Definitions      = function + attachment/allomorph rule + register
  Example Sentence = reviewed Korean microexample
  Translation      = context-matched Portuguese translation
  word_audio       = approved spoken construction sample
  sentence_audio   = approved exact example audio
  Image            = ""
  ```

- Keep structured function/rule/register and graph evidence in source/revision contracts; rendering a combined `Definitions` value must be deterministic and reversible to its exact source revision.
- Do not redesign the normal card, add learner-visible telemetry/review fields, or mutate unrelated note types. Keep `Image` blank.
- A bound particle or ending must not be sent as an unexplained raw fragment to TTS. Word audio binds an explicit reviewed spoken form or minimal carrier context; sentence audio binds the exact approved example.
- Reuse an exact approved Phase 32 `ko-KR` voice/profile only when its route, voice, locale, SSML/profile, provider version, artifact policy, and authority hashes are current. There is no guessed voice, inherited fallback, or alternate provider.
- Synthesis success is pending evidence, not approval. Missing, fallback, stale, wrong-text, wrong-profile, hash-mismatched, or review-failed audio keeps the item review-required/failed and never completed.

### Custom-List Ordered Input Ledger

**Chosen approach:** Preserve an ordered outcome for every nonblank submitted row, while generating at most one card for an exact normalized duplicate.

- Persist `input_position`, exact bounded `submitted_form`, `canonical_nfc`, resolution status, resolved lemma/POS/sense/signature where available, and an outcome for every row.
- Build the exact-duplicate key only after Phase 30 script validation, NFC normalization, bounded whitespace normalization, and case folding where applicable. Never use NFKC to disguise Compatibility Jamo or halfwidth Hangul.
- The first exact-normalized occurrence is the card-bearing row. Later occurrences retain their own positions and become `duplicate_of=<first row identity>` outcomes; they are visible in local summaries and are not silently dropped.
- Distinct submitted forms remain distinct card-bearing items even when they resolve to the same lemma/POS/sense. This preserves intentional inflected-form study and the submitted form required by `KPERS-01`.
- Persist explicit input order rather than deriving it from an item-key sort. Repository listing, review listing, reports, and prepared rows order first by `input_position`; approved bridge cards may be interleaved immediately before the dependent item without changing relative user-item order.
- Preserve existing note GUID formulas and source-type behavior. Add order metadata without changing current GUID algorithms; if satisfying the final export order would require a GUID semantic change, stop and hand the conflict to Phase 34 rather than migrating identities here.
- The ordered source fingerprint must distinguish a reordered list while retaining stable per-item identities. Exact run-key/GUID compatibility details must be verified against existing custom-list rerun tests before adoption.

### Custom Morphology, Ambiguity, and Bridge/Defer Decisions

**Chosen approach:** Resolve locally and fail closed, then expose an explicit decision rather than changing the requested deck automatically.

- Preserve the submitted surface separately while Phase 30 NFC/Kiwi/source consensus resolves the dictionary lemma, normalized POS, source sense ID, ordered morpheme signature, register, and analyzer fingerprint.
- `먹었어요` may resolve to source-backed `먹다`; compound predicates such as `공부하다` retain their derivational signature and cannot collapse to a noun merely because it shares a surface component.
- Kiwi ambiguity, source-record ambiguity, OOV evidence, unavailable analysis, missing sense, conflicting POS, malformed signature, or fingerprint drift yields `needs_review`; no top-1, substring, whitespace, suffix, provider, or generic-language fallback may resolve it.
- Compute observed/prerequisite novelty under the adaptive personal-source policy. Persist deterministic counts and reason codes under a versioned bridge policy; do not label custom cards strict.
- Excessive or unresolved prerequisites create a typed proposal with exact prerequisite concept IDs and one of these user-facing choices:
  - `bridge`: explicitly select reviewed prerequisite cards/references to place before the item;
  - `defer`: retain the item and its original position but make it ineligible for current generation/export; or
  - `needs_review`: resolve identity or prerequisite uncertainty before either decision is valid.
- No proposal changes the deck. Only an explicit local decision schedules bridge content, and scheduling a new generated bridge remains subject to source, provider, review, and audio authority.
- Do not create an adaptive queue, silently lower the threshold, reorder user items for a better score, or mutate shared frequency/grammar content from personal history.

### Highlight Extraction and Private Trust Boundary

**Chosen approach:** Analyze full source text locally, persist only the exact normalized excerpt in the private store, and expose only separately typed safe derivatives outside it.

- Parse local Kindle/WebDAV content under the existing local-import boundary. Paths, credentials, raw source bytes, book/location metadata, and exact excerpts remain private.
- Run Kiwi locally over the bounded normalized highlight before generic regex, token-length, or stopword filters. Retain valid one-syllable lexemes, analyze attached `J*` particles and `E*` endings, preserve same-eojeol compound predicates, and deduplicate by complete lemma + POS + sense identity.
- Preserve first-source order and occurrence counts. Exact excerpts with distinct content hashes remain distinct private records even when they yield the same lexical identity.
- A private excerpt revision stores the exact parser-normalized source excerpt and private source linkage. Public lexical candidates retain only safe identity, content hashes, source indexes, and controlled counts.
- The exact excerpt is available only through a local review command with an explicit private-display option. Default list/report output is content-free and never prints the excerpt or path.
- The source excerpt is contextual `i+n`. It is never relabelled strict and is not inserted into the existing highlight card's `Example Sentence` field.
- The generated microexample is a separate field revision with its own provenance, validation, adaptive evidence, review state, and audio dependency. Only an approved microexample is eligible for the existing highlight learner fields.

### Bounded Provider Context Under Exact Authority

**Chosen approach:** Derive one redacted target-centered context artifact locally, but release it to an external provider only when an exact authority receipt covers the job, task, route, and private-data scope.

- If no valid authority receipt exists, set provider context to `None`; do not fail open to the current automatic context path.
- Authority binds at least job/run, source hash set, task, provider/model route, private-processing purpose, redaction policy version, maximum context bound, item/attempt ceiling, budget where applicable, authorized-at/expiry, and the authorizing project-owner identity.
- Apply deterministic redaction for paths, credentials, book/location metadata, analyzer dumps, identity/approval assignments, and prompt-injection patterns before context construction.
- Keep context target-centered and bounded to no more than the existing 24-token ceiling; implementation may choose a smaller cap. Re-sanitize at the typed request and provider-adapter boundaries.
- Treat the delimited context as untrusted data for sense guidance only. It cannot alter lemma/POS/sense/signature, approval state, provider route, tool behavior, or system instructions.
- Store the derived context value only in the private revision boundary when needed to audit disclosure. Provider telemetry stores its hash, redaction policy, bounded metrics, and authority ID—not the value, exact excerpt, prompt, completion, path, or payload.
- A receipt is not reusable outside its exact scope. Missing, expired, mismatched, over-budget, route-drifted, or policy-drifted authority blocks the provider call for that item.
- Full source context may be used by deterministic local parsing and Kiwi. It must never be sent to a remote provider. A future genuinely on-device language model requires a separate explicit design and is not introduced here.

### CLI-First Review and Decision Surface

**Chosen approach:** Add deterministic Typer commands over application services; keep command handlers thin and leave transport-independent contracts for a later API.

- Support machine-readable and human-readable forms of:
  - list items/fields by job, source, outcome, review state, and input order;
  - inspect one field's current and candidate revision metadata;
  - approve or reject one exact revision;
  - create an edited candidate revision;
  - regenerate one selected definition, sentence, translation, word-audio, or sentence-audio field;
  - record one custom `bridge` or `defer` decision; and
  - resume eligible item/stage work.
- Exact command names and option spelling are technical discretion, but every mutating command requires exact job/item/field/revision identity and deterministic conflict handling.
- Default output is privacy-safe and content-free where possible. Private excerpts or private revision values require an explicit local display option and never appear in aggregate JSON, shell diagnostics, logs, or telemetry.
- CLI success reports persisted outcomes and revision/event IDs. It never treats provider invocation, parsed output, synthesis success, or a database write alone as approval.
- Do not add FastAPI, network listeners, remote callbacks, browser pages, or a dashboard. No Phase 33 command accepts arbitrary modules, templates, URLs, provider names, or publication destinations.

### Immutable Field Revisions and Append-Only Audit Events

**Chosen approach:** Store field values once in immutable private revisions and record every transition as an append-only event referencing exact before/after revisions and hashes.

- Model reviewable fields explicitly: `definition`, `sentence`, `translation`, `word_audio`, and `sentence_audio`. A field revision carries value/artifact reference, canonical content hash, provenance, dependency revision/hash bindings, validation result, review state, creator type/identity, policy versions, and timestamp.
- Text revisions retain private values in the revision store. Audio revisions retain exact text/profile/request/artifact metadata, path identity, and byte hash; audit events do not duplicate media bytes.
- A current-field record points to the selected revision and, separately, the current approved revision where one exists. Approved revision rows are immutable.
- Every list/approve/reject/edit/regenerate/stale transition writes an event containing event ID, job/item/field, action, before revision ID/hash, after revision ID/hash, actor type/identifier, reason code, validation/policy snapshot identity, and timestamp.
- Write candidate revision, pointer transition, dependency staleness, and event atomically. Use optimistic conflict detection so two commands cannot silently approve different stale bases.
- Regeneration creates a new `needs_review` candidate for only the selected field. It neither updates the approved pointer nor invokes dependent regeneration automatically.
- Editing follows the same candidate path and validators as regeneration. There is no direct SQL/CLI edit of an approved value and no `--force` in-place overwrite bypass.
- Rejecting a candidate records the event and leaves the last approved revision current. If no approved revision exists, the field remains blocking.
- Approving a candidate records an explicit transition to the new revision. Prior approved revisions remain retained and addressable for audit; approval never deletes history.
- A changed sentence marks translations and sentence audio whose dependency hash names the previous sentence revision `stale`/`review_required`. Their old revisions remain present but are not current-ready for the changed sentence.
- Other dependencies fail closed by declared hash binding: a definition change invalidates a sentence only when the sentence revision records that definition as grounding; word audio invalidates when its spoken/display identity changes.
- Revisions and events are retained with the job and are not auto-pruned. A privacy purge/deletion policy is a separate future authority; Phase 33 does not silently cascade away audit evidence or orphan referenced media.
- Public reports and telemetry use revision/event IDs, hashes, states, and counts only. Exact values, paths, reviewer notes, prompts, provider payloads, and private context remain private.

### Item/Stage Outcomes, Isolation, and Resume

**Chosen approach:** Add an additive per-item/per-stage outcome model rather than continuing to use one coarse `completed` item flag as every stage's truth.

- Persist stage outcome independently for ingest, lexical resolution, text fields, review, audio fields, and prepared export readiness where applicable.
- Record `processed_at`/attempt facts separately from outcome. The controlled outcomes are at least `pending`, `processing`, `accepted`, `review_required`, and `failed`; only `accepted` advances that item's stage success.
- Automatic validation may produce `accepted`, while explicit field approval remains separate revision state. Final learner-ready/export gates require the current approved revisions required by policy, not merely an automatically accepted provider result.
- A review-required item is processed but incomplete. A failed or pending required audio asset is processed but incomplete. Neither contributes to completed-item counts.
- Catch provider, parsing, validation, persistence, and media exceptions at the item/task boundary. Roll back only the affected transaction, persist a controlled redacted reason and attempt count, then continue with remaining items unless a global authority/budget/policy circuit breaker requires a bounded stop.
- Aggregate job counts from persisted item/stage truth. Do not increment/decrement counters as independent authority and do not advance a whole job stage merely because one item succeeded.
- Default resume skips current accepted work, retries pending and policy-retryable failed work idempotently, and leaves review-required fields for explicit review/regeneration. Options may explicitly target a review-required field but cannot bulk-overwrite it.
- Idempotency uses exact job/item/task/input revision/provider-policy identities. Repeating a successful transition returns/reuses the same current state or records a duplicate-safe observation; it does not create duplicate provider calls, revisions, or events.
- Provider exceptions cannot silently abort the remaining batch. Reports must distinguish attempted, processed, accepted, review-required, failed, skipped-current, and not-attempted denominators.
- Preserve SQLite concurrency one. Do not add leases, worker pools, or claim that concurrent processing is safe; Phase 34 owns bounded PostgreSQL claims/workers.

### Exact Phase 31 and Phase 32 Dependency Joins

- **Phase 30 remains authoritative** for canonical `ko`, provider-only `ko-KR`, NFC boundaries, forbidden Compatibility/halfwidth behavior, source-backed lexical identity, exact Kiwi fingerprint, top-two consensus, persisted morphology, and fail-closed matching.
- **Phase 31 exact dependency:** production grammar binds the active foundation snapshot's exact bundle, receipt, concept registry, and snapshot-root hashes resolved through `resolve_active_korean_foundation_snapshot()`. Candidate, history-only, test, request-only, or stale snapshots are not known-state authority.
- **Phase 32 lexical dependency:** where grammar bootstrap, custom, or highlights consume Phase 32 lexical authority, persist the exact bundle/source/version/entry hash and selected identity. Grammar does not depend on completion of Frequency Level 1 and never infers known vocabulary from frequency membership.
- **Phase 32 provider dependency:** any generation, translation, judge/review, or audio work reuses only exact approved task-route, telemetry, budget, and retry contracts. No current generic fallback or first-response path is treated as final authority.
- **Phase 32 audio dependency:** grammar/custom/highlight audio may reuse only the exact approved `ko-KR` catalog/voice/profile and integrity/review policy actually activated. Phase 31 foundation media is not repurposed as grammar/personal audio.
- If an exact Phase 31/32 artifact is not active when a consuming production lane runs, complete only offline contracts and refusal tests. Record the missing hash/authority category and keep dependent content blocked.
- Joining an upstream artifact never authorizes provider spend, private-content processing, asset commit, publication, or production database mutation. Those remain separate project-owner capabilities.

### No-Provider, No-Upload, and No-Publication Authority

- This alignment and future plans do **not** authorize a live or paid provider call, use of credentials, upload of private highlight text, production database mutation, media/source acquisition, asset commit, deck publication, or external distribution.
- All tests and default planning/execution paths are offline and use deterministic synthetic fixtures that cannot satisfy production review or authority gates.
- External AI review is itself a provider operation when it leaves the local trust boundary. It requires the global AI policy plus exact provider/private-processing/budget authority; the policy does not grant legal or operational authority by itself.
- A future provider handoff must name exact provider/model or voice, route/task, credential boundary, input classification, allowed item set, context policy, attempt/concurrency/token/cost ceilings, expiry, and output destination.
- Source/license approval, private provider processing, paid spend, production mutation, asset commit, local learner-ready activation, and publication are independent decisions. Approval of one never implies another.
- Local/private approved output is not permission to commit it or publish it. Missing authority blocks only the consuming lane and is reported without leaking content.

### Anti-Regression and Privacy Boundaries

- Preserve `ko` as the sole product/persistence/tag identity and `ko-KR` only at provider/locale boundaries.
- Preserve NFC normalization, forbidden Compatibility/halfwidth rejection, exact source-backed lemma/POS/sense, Kiwi top-two consensus, analyzer fingerprint checks, and fail-closed Korean matching. No suffix, substring, whitespace, top-1, Stanza, generic, or provider-authored rescue.
- Preserve normal and highlight layouts, existing field orders, blank `Image`, current source modes, note identities, GUID formulas, and all existing language behavior. Phase 33 adds data/review contracts, not a visual redesign.
- Preserve existing frequency, custom-list, highlight, Japanese, Mandarin, Latin, phoneme, audio, persistence, and export regressions. Korean-specific strictness must branch explicitly and not tighten unrelated languages silently.
- Never auto-insert bridge cards, reorder user items, collapse distinct submitted forms, infer mastery from frequency, or mutate shared curriculum/content from personal history.
- Never place exact excerpts, private paths, book/location metadata, WebDAV credentials, prompt text, provider payloads, raw analyzer dumps, tracebacks, private revision values, or audit notes in ordinary candidate rows, telemetry, reports, errors, exports, tags, or evidence manifests.
- Re-sanitize at parser, typed request, provider adapter, persistence projection, CLI output, report, and exception boundaries. Raw untrusted highlight context never controls tools or authority fields.
- Never update an approved revision in place. Candidate generation, editing, rejection, approval, dependency staleness, and rollback/selection are explicit append-only events.
- Never count a review-required or failed text/audio item as completed, and never hide a provider exception by returning an aggregate success.
- Do not modify the current GUID formula, introduce semantic/form GUID migration, or use input isolation as a reason to pre-implement Phase 34 topology/history work.
- Do not add provider credentials, network tests, arbitrary URLs/paths, `--allow-unapproved`, approval-forcing flags, privacy bypasses, or publication switches.

### UI and Visual Claim Limits

Phase 33 adds no application page or visual-design deliverable. It reuses existing Anki layout contracts and adds CLI review/decision operations.

- Static tests may prove field projection, labels, source-mode selection, blank `Image`, and absence of private/evidence fields.
- Data tests may prove graph truth, order, revision history, state transitions, privacy separation, and provider refusal.
- Neither static checks nor prepared rows prove Anki import, rendering, font behavior, responsive layout, replay behavior, or in-Anki playback. Phase 34 owns those observed claims.

### Agent's Discretion

- Exact module, class, method, table, column, enum, event, and controlled reason-code names, provided all locked states and transitions remain explicit and migration-safe.
- Exact migration revision identifier derived from the unique live Alembic head, provided changes are additive and existing rows remain valid.
- Exact decomposition of revision values, current pointers, dependency bindings, and event tables, provided revisions are immutable, events append-only, values remain private, and before/after content is reconstructable.
- Exact CLI command/option names and JSON envelope, provided exact job/item/field/revision targeting, deterministic conflicts, local-only private display, and no provider/path/publication bypass are preserved.
- Exact conservative custom “excessive prerequisite” threshold and scoring details, provided they are deterministic, versioned, reported, adaptive rather than strict, and never trigger automatic insertion. Changing the policy version invalidates prior decisions for review.
- Exact redaction implementation and a context cap smaller than or equal to 24 tokens, provided the provider sees nothing without authority and all forbidden data remains excluded.
- Exact grammar bundle/member filenames, schema decomposition, stable concept-ID vocabulary, and hash canonicalization, provided imported Phase 31/32 authority is exact and source packs remain immutable.
- Exact grammar lexical-bootstrap size and selected learner examples within the smallest-prerequisite rule, provided every production identity is source-backed, every record passes the global AI review policy and deterministic validators, and it never expands into a frequency-level prerequisite.
- Exact G0-G13 card atomization and reviewed wording where more than one valid split exists, provided each final strict card has exactly one recomputed construction unknown and all content is hash-bound/reviewed.
- Exact transaction and optimistic-conflict implementation, retryable-failure taxonomy, report ordering, and synthetic fixtures, provided per-item isolation and status denominators remain truthful.
- No discretion extends to standalone grammar, a frequency-level prerequisite, automatic bridges, a v4 queue, full remote highlight context, API/UI delivery, hashes-only audit, copied event values, approved-field overwrite, heuristic Korean fallback, live/paid/private calls, asset commit, production mutation, publication, GUID migration, or Phase 34 claims.

</decisions>

<assumptions>
## Validated Assumptions

### 1. Technical Approach

- **[high confidence][confirmed by user]** The grammar known-state root is the exact active Phase 31 snapshot plus a grammar-owned learner-visible lexical bootstrap; Frequency Level 1 and standalone assumptions are rejected.
- **[high confidence][validated from live code]** The existing Korean concept domains already include `grammar` and `lexicon`, and the foundation path exposes immutable snapshot/hash boundaries suitable for exact import rather than registry mutation.
- **[high confidence][validated from live code]** Current word-list order is lost after parsing because request normalization and repository queries sort item keys. Phase 33 therefore requires explicit input-position persistence and ordered queries rather than a documentation-only promise.
- **[high confidence][validated from live code]** Current Korean highlight ingestion already separates private normalized text from safer lexical candidates, providing a viable boundary to strengthen with explicit context authority and typed excerpt/context/microexample revisions.
- **[high confidence][validated from live code]** Current text/audio repositories update rows in place and there is no general field revision/audit event model. Additive immutable revisions are required for `GREV-01`; existing mutable rows cannot serve as the audit log.
- **[high confidence][confirmed by user]** Revision references plus hashes are preferable to copied before/after values or hashes alone because they preserve inspectability without duplicating private content in every event.
- **[medium confidence][requires implementation validation]** Existing normal/highlight layouts can carry all learner-facing Phase 33 content through deterministic field projection without a new learner field. Structured rule/register/excerpt evidence remains source-side.

### 2. Implementation Order

- **[high confidence][accepted]** Establish failing contracts for ordered input, exact dependency joins, strict graph recomputation, private context refusal, stage outcomes, revision immutability, and approved-field preservation before wiring production services.
- **[high confidence][accepted]** Build the immutable grammar/bootstrap bundle and graph validators before content review/media joins; review revision contracts before mutating CLI commands; item-state truth before resume/report aggregation.
- **[high confidence][accepted]** Refactor highlight context so “no authority means no context” before any production provider path can consume private material.
- **[high confidence][accepted]** Complete safe offline behavior and existing-mode regressions before consuming an active Phase 31 snapshot, Phase 32 route/profile, or any external authority.
- **[medium confidence][parallelizable]** Grammar bundle/graph work, ordered personal-source contracts, and generic revision/job-state scaffolding can proceed in disjoint lanes, but production activation joins exact schema and upstream hashes before use.

### 3. Scope Boundaries

- **[high confidence][confirmed by user]** Phase 33 is CLI-first and introduces no FastAPI or review dashboard.
- **[high confidence][confirmed by roadmap]** Phase 34 retains final all-family export/evidence, observed Anki acceptance, and bounded production workers/claims.
- **[high confidence][confirmed]** Existing note GUID formulas, layouts, fields, and source-mode behavior remain unchanged; order and evidence are additive Phase 33 data contracts.
- **[high confidence][confirmed]** Adaptive queues, learner history/mastery, semantic/form identities, and personal-history mutation of shared content remain out of v3.0.
- **[high confidence][confirmed authority boundary]** Planning alignment authorizes no provider use, private upload, source/media acquisition, production mutation, commit, publication, or distribution.

### 4. Risk Areas

- **[high confidence][validated]** The largest correctness risks are false strict-i+1 claims, hidden lexical prerequisites, broad grammar targets, inflected-form misresolution, order loss, silent duplicate collapse, approved-field overwrite, stale dependents, and false completion.
- **[high confidence][validated]** The largest privacy risks are automatic provider context, exact excerpt/path leakage through provenance or CLI output, copied private values in audit events, provider payload telemetry, and unredacted exceptions.
- **[high confidence][confirmed policy]** A review-required false negative is preferable to a learner-facing false identity, grammar rule, context disclosure, or approval. Ambiguity and missing authority therefore fail closed.
- **[high confidence][confirmed by user]** Processed, accepted, review-required, and failed are distinct facts. Counters and resume behavior must be derived from persisted item/stage truth.
- **[medium confidence][requires content review]** The approved G0-G13 outline can be atomized into exactly-one-construction cards with a bounded bootstrap, but exact examples, prerequisites, allomorph grouping, and irregular splits require deterministic validation plus global-policy AI review.

### 5. Dependencies

- **[high confidence][satisfied baseline]** Verified Phase 30 code supplies canonical identity, NFC, Kiwi, source-backed lexical identity, persisted evidence, highlight-local analysis, and fail-closed target matching.
- **[high confidence][blocking exact dependency]** Production grammar cannot establish known state until a genuinely active approved Phase 31 snapshot supplies current bundle/receipt/snapshot-root hashes. Offline fixtures do not satisfy this dependency.
- **[high confidence][conditional exact dependency]** Phase 32 frequency completion is not a learner prerequisite, but any consumed lexical record, provider route, telemetry policy, Portuguese generation contract, or Korean audio profile must be the exact approved Phase 32 artifact/version.
- **[high confidence][blocking external dependency]** Production grammar curriculum copy, source-backed bootstrap identities, Korean/Portuguese review, and exact audio/review artifacts are not created by this approach document and cannot be fabricated by implementation.
- **[high confidence][blocking authority]** No exact provider/model/budget/private-processing or production synthesis authority is supplied by this discussion. External calls remain forbidden until a separate scoped handoff exists.
- **[high confidence][claim limit]** Final APKG/CSV/TSV and observed Anki evidence are unavailable and unnecessary for Phase 33's bounded contracts/review claim; Phase 34 must supply them.

</assumptions>

<deferred>
## Deferred Ideas

- **Phase 34:** Final grammar/custom/highlight APKG, CSV, and TSV packaging; all-family export gates; observed Anki Desktop/mobile import, rendering, font, responsive, and playback evidence; PostgreSQL claims; bounded workers; milestone scanner evidence.
- **Later API milestone:** FastAPI endpoints, authentication/authorization, remote review clients, private-data response policy, and a browser review dashboard after CLI/service contracts stabilize.
- **Later local-model investigation:** Full-context processing by a genuinely on-device model with an independently reviewed runtime, resource, security, and model-quality policy. Full context remains prohibited from remote providers.
- **Out of v3.0:** Learner-history synchronization, Anki scheduling import, adaptive prerequisite queues, semantic/form GUID migration, form-specific card families, personal-history mutation of shared curricula, Hanja, and regional dialect curricula.
- **Separate privacy lifecycle decision:** Authorized purge/retention expiration for private excerpts, revision values, and superseded media. Phase 33 retains audit history with the job and does not invent a destructive policy.
- **Separate rollout:** Applying the Phase 33 field-revision/job-outcome model to every historical/frozen Latin or foundation workflow beyond compatibility boundaries. Shared new generation may use the model, but frozen assets are not silently migrated.

The missing exact Phase 31 activation, Phase 32 lexical/provider/audio artifacts, grammar/bootstrap source content, global-policy review evidence, provider/private-processing authority, exact production audio, asset-commit authority, and publication authority are **not** silently deferred implementation conveniences. They are explicit consuming-lane gates. If absent, the correct result is complete offline machinery with blocked production records, not fabricated learner-ready output.

</deferred>

---

*Phase: 33-grammar-and-personal-sources*
*Approach explored and user-confirmed: 2026-08-28*
