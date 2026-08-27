# Phase 32: Frequency, Portuguese Text, and Audio - Approach

**Explored:** 2026-08-21
**Status:** Ready for parallel execution under the global AI linguistic review policy and bounded external-authority lanes

## Alignment Proof

- `workflow.discuss`: true — `.planning/config.json` uses `discuss_mode="discuss"` and `skip_discuss=false`.
- `alignment_status`: user_confirmed
- `alignment_method`: Researched decision matrix presented through orchestrator questions; the user selected all four recommended options and then explicitly confirmed the five-dimension assumptions.
- `user_confirmed_at`: 2026-08-21
- `explicit_skip_approved`: false
- `skip_scope`: N/A
- `skip_rationale`: discussion was completed
- `confirmed_decisions`:
- The 2026-08-27 user amendment adopts `.planning/AI-LINGUISTIC-REVIEW-POLICY.md` for Korean, Portuguese, pronunciation, lexical, morphology, and text-quality review. Human linguistic review is optional and no longer blocks execution.
- Plans form a dependency DAG. Offline contract/ID lanes and source-readiness lanes run in parallel isolated worktrees; production generation joins exact Phase 31 output only when it consumes foundation known-state/media authority.
- Use one reusable shared final-mode contract, activated first for Korean through one atomic manifest-bound 3000-entry bundle; do not recurate all existing language assets in Phase 32.
- Use the National Institute of Korean Language (NIKL) `한국어 학습용 어휘 목록` as the selected rank and initial lexical-authority path. The official page identifies 5,965 entries and KOGL Type 1 use with specific source attribution; exact attachment bytes, terms evidence, attribution, transformation notes, modernity review, and repository-redistribution disposition must still pass their own checkpoint before any production asset is created or committed.
  - Create real Korean `Level 1`, `Level 2`, and `Level 3` child decks in Phase 32. Phase 34 generalizes the topology and owns final all-family export, import, rendering, playback, and evidence closure.
  - Let one dominant source-backed sense consume each frequency rank unless the approved frequency source itself supplies independently sense-specific ranks; unresolved homographs block or require review.
  - Define v3 adaptive i+1 from cumulative approved deck order, inherit only approved Phase 31 concept evidence, and make naturalness a hard gate before novelty scoring.
  - Use everyday Standard-Seoul `해요체` by default; another register requires explicit context evidence and review.
  - Produce pt-BR editorial copy while retaining canonical project language identity `pt`; provider-specific regional language codes exist only at provider boundaries, while editorial metadata uses a policy identifier rather than a second language identity.
  - Generate exactly two initial sentence candidates and permit at most one cache-distinct repair; pin one approved provider/model route per task and prohibit cross-provider fallback for final Korean output.
  - Require explicit approval for exact provider models, credentials, token/cost/latency ceilings, and every live or paid run.
  - Use one live-discovered and approved Azure `ko-KR` voice/profile for ordinary frequency word and sentence audio, with neutral SSML unless heard approval authorizes a different versioned profile and with no alternate provider or voice fallback.
  - Require human playback of at least 10% stratified samples of each ordinary frequency-audio type — at least 300 words and at least 300 sentences — plus 100% of flagged, homograph, and other risk cases; require exact automated integrity checks for 100% of assets.
  - Implement all safe offline contracts, tests, and refusal behavior before pausing at license/source, exact-asset, Phase 31 dependency, provider budget/model, live catalog, paid generation, human review, asset commit, and publication checkpoints.
  - Preserve verified Phase 30 `ko`, NFC, source-backed identity, Kiwi top-two consensus, matcher, persistence, and privacy contracts plus Phase 31 hash-bound gates; final mode never reaches live `wordfreq` or generic suffix rescue.
  - Persist only sanitized hashes and bounded provider metrics in telemetry, never prompts, private excerpts or paths, provider payloads, secrets, or raw analyzer dumps.
- Keep Phase 33 field-level review and job hardening, Phase 34 worker/generalized closure beyond the explicitly assigned Korean child decks, and all v4/GUID/history/adaptive-queue work outside Phase 32.

## 2026-08-27 AI-Review And Parallelism Amendment

This amendment supersedes earlier Phase 32 requirements for qualified human
Korean, pt-BR, native-speaker, or human playback review.

- Linguistic/text/source-curation review uses two standard or three critical
  fresh-context AI passes plus deterministic validators. Results are
  `ai_review_passed` and never impersonate human qualifications.
- Audio uses 100% integrity/decoder/acoustic validation and policy-bound AI
  acoustic review where a capable route exists. It does not claim human hearing.
- Legal/source rights, private provider processing, network access, paid budget,
  production database mutation, and publication remain project-owner powers.
- Existing plans that say "qualified human linguistic review" are interpreted as
  the global AI policy. Existing user checkpoints remain only when they grant an
  external side effect or legal/project-owner authority.
- Plans 32-01 and 32-10 may start together; 32-17 and 32-18 may start together;
  32-25 and 32-26 may start together. Each pair uses isolated worktrees and joins
  only after exact output hashes are current.
- Phase 32 offline execution no longer waits for Phase 31. Plan 32-27 is the
  production join and depends on exact Phase 31 Plan 31-32 output.

<domain>
## Phase Boundary

Phase 32 delivers the Korean-first production path for `KFREQ-01`, `KFREQ-02`, `KFREQ-03`, `KTXT-01`, `KAUD-01`, `GLEX-01`, `GLEX-02`, `GMOR-01`, `GTXT-01`, `GPRO-01`, and `GAUD-01`. It establishes one license-gated, manifest-bound 3000-entry Korean inventory; exact source-backed lexical and morphology evidence; adaptive deck-order i+1; natural Standard-Seoul examples; Brazilian Portuguese definitions, glosses, and translations; deterministic multi-candidate generation; explicit provider routes and budgets; exact approved Azure audio; and real Korean Level 1/2/3 child decks.

The phase uses a **Korean-first shared-contract posture**:

- Shared final-mode contracts, provider policy, telemetry, and integrity gates are reusable by other languages.
- Only Korean is migrated onto and activated through that stricter final mode in this phase.
- Existing frequency languages retain their current paths and are not silently recurated, re-ranked, or blocked by unavailable newly selected adapters.
- A later explicit rollout may qualify other language assets and adapters against the same contracts; Phase 32 does not claim that their current inventories already meet Korean-level evidence.

### Phase 32 Versus Phase 34 Ownership

The user explicitly resolved the earlier roadmap/pattern ambiguity:

- **Phase 32 owns actual Korean child-deck creation.** The exact frozen membership is routed into one package hierarchy with the existing canonical Korean parent deck and real child decks labeled `Level 1`, `Level 2`, and `Level 3`.
- Child-deck assignment must not change the existing note field set, blank `Image`, tags, or note GUID input/formula. Level membership comes from the approved frozen manifest, not inferred opportunistically from row position during export.
- **Phase 34 owns generalization and final closure.** It extends the real-subdeck behavior across applicable existing frequency paths and supplies final all-family APKG/CSV/TSV, Anki import, rendering, font, responsive-layout, playback, worker, and milestone evidence.
- Phase 32 may prove deterministic Korean APKG structure and local media resolution. It may not claim observed Anki Desktop/mobile acceptance, visual quality, publication, or the Phase 34 generalized export contract.

This user-confirmed disposition supersedes the pre-alignment assumption in `32-PATTERNS.md` that all real-subdeck packaging had to wait for Phase 34. The rest of that pattern map remains useful technical evidence where it does not conflict with this APPROACH.

### Technical Completion Versus Learner-Ready Completion

Phase 32 follows **implement safely, then block at real authority**:

- Contracts, strict loaders, migrations, adapters, candidate selection, scoring, review schemas, exact-hash gates, child-deck routing, reports, CLIs, deterministic fakes, refusal paths, and regression tests can be completed offline.
- Synthetic or reviewed test fixtures may prove technical success only. They cannot authorize a production frequency source, redistributed asset, provider spend, Korean or Portuguese quality, an Azure voice, exact production bytes, asset commit, or publication.
- If an external dependency is unavailable, execution completes and verifies the safe technical path, records the actionable blocker, and leaves production content non-exportable or `needs_review`.
- The phase goal may be claimed as learner-ready only after all applicable source, license, Phase 31, lexical, linguistic, Portuguese, provider, Azure, media, playback, commit, and release gates are genuinely satisfied.

### Requirement Disposition

| Requirement group | Phase 32 technical truth | Learner-ready truth while approvals are missing |
|---|---|---|
| `KFREQ-01`, `KFREQ-02`, `GLEX-01`, `GLEX-02`, `GMOR-01` | Implement one strict atomic source/manifest/inventory/rejection chain, selected-adapter acceptance, exact 1000/1000/1000 membership, and real Korean child-deck routing. | No redistributed or production inventory is committed or activated until its exact source, use, attribution, redistribution, lexical identities, and curation evidence are approved. |
| `KFREQ-03`, `KTXT-01` | Implement cumulative-order adaptive evidence, hard Korean quality gates, `해요체` default policy, pt-BR editorial contracts, bounded candidate selection, and hash-bound review evidence. | Automated scoring and an LLM judge cannot approve naturalness, sense, context, register, or Portuguese quality; absent qualified evidence remains review-required. |
| `GTXT-01`, `GPRO-01` | Implement two initial candidates, one distinct repair, deterministic complete-bundle selection, explicit task routes, retries, cache separation, budgets, and privacy-safe telemetry. | No model/provider route, credential use, budget, live pilot, or paid 3000-card run is authorized merely because the offline route works. |
| `KAUD-01`, `GAUD-01` | Implement exact catalog, voice/profile, request, SSML, byte, review, fallback, reuse, completion, and export gates for separate word/sentence assets. | Korean remains absent from approved production voice selection until live catalog evidence and the required heard review exist; synthesized but unapproved media cannot advance or export. |

### Explicitly Outside This Phase

- Phase 33 Particles & Endings content, personal-list/highlight pedagogy, resumable item/job hardening beyond the minimum Phase 32 audio/text correctness fixes, and field-level approve/reject/edit/regenerate commands.
- Phase 34 generalized real-subdeck rollout for existing languages, bounded worker/claim architecture, all-family export closure, milestone evidence, and observed Anki Desktop/mobile import, visual, responsive, font, and playback acceptance.
- Recuration or adapter qualification for every existing frequency language.
- v4 semantic/form identities, GUID migration, APKG-history adaptation, learner-history synchronization, adaptive queues, or scheduling integration.
- Application pages, dashboards, review-management UI, interaction design, or any other app UI work.
- Publication, upload, external distribution, or release claims without a separate explicit authorization.

</domain>

<decisions>
## Implementation Decisions

### Gray Areas Explored

| Gray area | Classification | Approaches researched | Locked disposition |
|---|---|---|---|
| Frozen frequency authority, morphology rollout, and subdeck delivery | Hybrid | Extend weak CSV/live fallback; atomic Korean-first release bundle; immediate global strict cutover | Use one atomic hash-bound bundle and reusable final-mode contract, activate Korean first, and create real Korean Level 1/2/3 child decks now without recurating all languages. |
| Executable adaptive i+1 and Korean/Portuguese editorial profile | Hybrid | Prompt-only simplicity; cumulative deck-order evidence; per-user history | Use cumulative approved order, approved Phase 31 concepts only, naturalness-before-novelty, default `해요체`, and pt-BR editorial output under canonical `pt`. |
| Multi-candidate text, repair, provider routes, and budgets | Technical | Current first-response flow; two candidates plus one pinned-route repair; cross-provider ensemble/judge | Use two candidates, one cache-distinct repair, deterministic selection, one pinned route per task, bounded budgets, and no final Korean cross-provider fallback. |
| Azure voice qualification and playback coverage | Hybrid | One profile with sampled approval; separate word/sentence profiles; 100% individual playback | Use one approved `ko-KR` profile, neutral SSML, at least 10% stratified playback per type plus all risk cases, 100% automated integrity, and no voice/provider fallback. |

### Korean-First Final Mode and Atomic Frequency Bundle

**Chosen approach:** Introduce one project-owned final-frequency mode whose complete authority is a versioned root manifest, and activate it first for Korean.

**Alternatives considered:** Add fields to the current two CSV files while preserving runtime seed fallback; switch every existing language to strict manifests/adapters now; use a mutable database snapshot as the primary release authority.

**Why this one:** Korean requires stronger identity, licensing, morphology, and reproducibility than the current token-oriented assets provide. A reviewed file bundle is diffable and hashable, while a Korean-first rollout avoids pretending the existing assets already carry source senses and conclusive selected-adapter evidence.

- The root bundle binds one exact version of the source decision, attribution, license/use/redistribution disposition, ranked source snapshot, lexical authority snapshot, curated inventory, rejection ledger, curation report, analyzer fingerprint, and every child-file SHA-256.
- One approved rank source and one approved lexical identity source may be different authorities. Their join must be explicit, deterministic, versioned, confidence-bearing, and reviewable; neither silently overrides the other.
- The root records the exact ordered 3000-entry identity set, one child digest per level, exact row and rejection counts, and one canonical bundle hash persisted with generation jobs and downstream evidence.
- Strict models use bounded values, `extra="forbid"`, hidden input values in errors, canonical UTF-8 JSON hashing, raw-byte SHA-256 for files, deterministic order, and content-free controlled failure reasons.
- No missing, malformed, stale, short, wrong-version, wrong-license, hash-drifted, non-contiguous, duplicate, unresolved, OOV, or analyzer-drifted bundle can produce final candidates or output.
- A production-size final request has no import, call, or recovery edge to `iter_wordlist`, `_build_seed_candidate`, seed grounding, first-match lookup, or provider-authored identity.
- `wordfreq` may remain isolated bootstrap tooling only after the source decision explicitly permits that use. It is never final authority, never a replacement source, and never contacted by final loading.
- If terms permit local use but not repository redistribution, the same bundle contract may live at an approved private configured root. That does not authorize `assets/frequency/ko/` creation or commit.
- Existing language generation remains unchanged unless and until another explicit rollout selects its asset and morphology adapter. Korean strictness must not be weakened to preserve legacy behavior.

### Selected NIKL Source Path

**Chosen approach:** Use the NIKL `한국어 학습용 어휘 목록` as the Phase 32 candidate rank and initial lexical source, subject to exact-artifact and redistribution verification.

**Alternatives considered:** A recent Leipzig-derived rank joined to NIKL identity after written license confirmation; a pinned Korean Wikipedia-derived rank isolated under CC BY-SA; `wordfreq` or SUBTLEX-KR output.

**Why this one:** The NIKL page is an official government source, identifies 5,965 learner-vocabulary entries, exposes 2002 frequency rank plus POS, homonym identity, gloss, and grade, and explicitly marks the work for KOGL Type 1 use with source attribution. It supplies a clearer public-asset path than sources whose exact derivative-list rights are unknown, noncommercial, no-derivatives, or ShareAlike-dependent.

- The primary selected page is `https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70`; the named attachment is `한국어 학습용 어휘 목록.txt`, published 2003-06-04 and last revised 2019-05-30. NIKL describes it as the same 5,965-entry list also offered as Excel and HWP; use the text artifact to avoid adding a legacy `.xls` parser.
- Selection does not itself approve unknown attachment bytes. Before source ingestion, record the final URL, raw SHA-256, byte size, retrieval time, publisher, source title/date, exact KOGL terms evidence, attribution text, intended transformations, storage mode, and public-Git redistribution disposition.
- Rights disposition is scope-specific. If qualified review explicitly approves transformation and local use but denies redistribution, Phase 32 may continue only from private/ignored storage to a local deck; source-derived data is mechanically ineligible for repository commit or publication. If local-use rights are missing or uncertain, stop before provider or production work. Public or committed source-derived assets require a separate explicit redistribution approval over exact bytes.
- Preserve the supplied rank, POS, homonym marker, gloss, and grade as source evidence. Project curation may reject or map rows, but it must never rewrite the original source rank or imply that a transformed final rank is the NIKL rank.
- The 2002 rank requires an explicit modernity review. Stale, obsolete, sensitive, proper-name, script-noise, function-morpheme, and unresolved rows are rejected with accounting; replacements come only from the same approved frozen 5,965-entry pool unless a new source decision is approved.
- NIKL source identity does not bypass Phase 30 NFC/Kiwi evidence or qualified sense review. Homonym/POS/gloss data constrains the dominant source-backed sense; unresolved joins remain blocked.
- Do not conflate this specifically KOGL-marked attachment with other NIKL, Sejong, or Modu corpus resources whose terms may differ.
- `wordfreq` remains excluded as final authority and is not a backfill source for this NIKL bundle.
- `.planning/phases/32-frequency-portuguese-text-and-audio/32-FREQUENCY-SOURCE-DECISION.md` is the canonical planning record for this selection and its remaining gates.

### Rank, Sense, Curation, and Selected Morphology

**Chosen approach:** Each final rank represents one complete source-backed Korean lemma + normalized POS + sense identity, with one dominant reviewed sense per ranked source item unless the frequency authority itself publishes sense-specific ranks.

**Alternatives considered:** Deduplicate visible surface forms only; let every mapped dictionary sense consume a slot at the same token rank; collapse all POS/sense homographs into one lemma card.

**Why this one:** Token frequency does not establish equal frequency for every dictionary sense. The chosen policy avoids fabricating sense ranks while preserving genuinely source-ranked sense distinctions.

- Distinct source-ranked senses may each consume a slot only when their rank evidence is independently supplied and auditable.
- A source token with multiple unresolved POS/sense mappings is rejected or routed to review; it is never resolved by taking the first lexical match or asking a provider.
- Inflected aliases sharing one lexical identity do not consume extra slots. Standalone particles, productive endings, script noise, sensitive proper names, malformed forms, and unresolved homographs are rejected with controlled reasons and accounted for in the report.
- Rejections are backfilled only from the approved frozen ranked candidate pool. Final ranks are reassigned contiguously in source order after curation, with source ranks preserved separately.
- Every accepted row stores the complete Phase 30 `KoreanLexicalIdentity`, trusted source/version, source rank, final rank, level, license decision, grounding confidence, curation decision, and exact Kiwi analyzer fingerprint.
- The persisted source identity remains authoritative. Frequency rank, provider output, generated definitions, surface morphology, or later review cannot rewrite lemma, POS, sense, register, signature, or analyzer evidence.
- Final acceptance requires conclusive selected-adapter evidence under the exact persisted Kiwi top-two consensus policy. Mismatch, ambiguity, OOV, unavailable analysis, malformed evidence, or fingerprint drift blocks.
- Korean target validation branches before generic token, Stanza, suffix, substring, Japanese, or Mandarin fallback. No generic suffix rescue can turn an inconclusive Korean result into acceptance.

### Real Korean Level Child Decks

**Chosen approach:** Package the approved Korean frequency inventory into real `Level 1`, `Level 2`, and `Level 3` child decks in Phase 32.

- The frozen manifest, not arithmetic inference at export time, assigns every entry to exactly one level with exactly 1000 identities.
- The parent follows the existing canonical Korean deck naming contract; child labels are exactly `Level 1`, `Level 2`, and `Level 3` beneath that parent.
- One package contains the three child decks and one compatible note model. The exporter must validate all rows and media before creating or replacing output.
- Deck/model identifiers are stable and collision-checked. A collision or any need to change note GUID inputs is a stop-and-replan condition.
- Moving a note between child decks cannot change its note GUID. Preserve current fields, field order, templates, tags, blank `Image`, and current GUID formula.
- Tests inspect the APKG deck table, note-to-deck routing, 1000/1000/1000 counts, fields, tags, GUIDs, and media references. These are structural claims, not observed Anki import or visual acceptance.
- Phase 34 consumes this Korean precedent, generalizes applicable shared frequency export behavior, and closes all-family/observed evidence. Phase 32 does not pre-implement Phase 34 workers or milestone closure.

### Adaptive Deck-Order i+1

**Chosen approach:** Define the v3 known state deterministically from approved curriculum and deck order, not from per-user scheduling history.

**Alternatives considered:** Prompt-only “simple sentence” instructions; strict exactly-one-unknown frequency sentences; user-specific Anki mastery/history.

**Why this one:** Frequency content must remain natural and adaptive, while v4 learner-history queues are explicitly excluded. A frozen order gives reproducible evidence without falsely claiming strict curriculum i+1.

- Known evidence begins with concepts from an approved active Phase 31 snapshot only. Candidate or temporary Phase 31 fixtures cannot become production known-state authority.
- For rank `n`, approved lexical identities at earlier final ranks are known; the current rank's complete lexical identity is the target lexeme.
- Persist target, known, observed, incidental/unknown concept IDs, candidate identity/hash, deterministic score components, selected ordinal, scorer version, and policy=`adaptive` for the chosen example.
- Naturalness, correct language, NFC, exact target morphology, source sense, register, non-leakage, and translation consistency are hard gates. A lower novelty score can never rescue a failed hard gate.
- Among hard-gate-passing candidates, deterministic scoring minimizes incidental lexical/concept novelty without forcing unnatural wording. Ties use immutable candidate identity/hash/ordinal, never provider return timing.
- Inconclusive observed-concept extraction requires review. Do not infer that unknown morphology is known, fabricate Phase 33 grammar mastery, or relabel adaptive evidence as strict.
- Particles and endings observed in examples remain incidental evidence; they do not become frequency-card targets or consume lexical ranks. Phase 33 owns their learner curriculum.

### Standard-Seoul Register and Brazilian Portuguese

**Chosen approach:** Use everyday modern Standard-Seoul Korean in `해요체` by default and Brazilian Portuguese learner copy under canonical project code `pt`.

- A different Korean register is allowed only when the source sense/context requires it, the record labels it explicitly, deterministic checks find no mixed speech level, and qualified review approves the exception.
- Provider output cannot set register authority. The source identity, Korean-specific register evidence, and human review control acceptance.
- Definitions, short glosses, and sentence translations follow one pt-BR editorial policy and must match the exact source-backed sense and Korean sentence context.
- Persisted project language and tags remain `pt`. A provider code such as `PT-BR` is used only inside the provider adapter; editorial evidence records a versioned Brazilian-Portuguese policy identifier rather than introducing `pt-BR` as a second product language identity.
- Validation blocks English leakage, wrong sense, invented omitted context or subjects, mixed Korean speech levels, unnatural/template Korean, isolated-word translations, contradictory translations, and provider-error payloads.
- LLM or translation-provider judgments may create typed candidate evidence but cannot grant linguistic, Portuguese, or release approval.
- Final learner-ready claims require exact hash-bound Korean and pt-BR review evidence from qualified reviewers. Missing reviewer authority remains `needs_review` rather than agent approval.

### Two Candidates, One Distinct Repair, and Deterministic Selection

**Chosen approach:** Generate a bounded set of exactly two initial sentence candidates, validate complete candidate bundles deterministically, and make at most one separately keyed repair request if neither produces an acceptable bundle.

**Alternatives considered:** Accept or regenerate one first response; generate an unbounded provider ensemble; let an LLM judge select or approve without deterministic gates.

**Why this one:** Two candidates provide a meaningful choice while bounding spend. A distinct repair fixes the current same-cache replay hazard, and deterministic hard gates prevent a judge from becoming authority.

- Initial generation returns exactly two strict structured candidates. Missing, extra, malformed, identity-bearing, or unbounded provider output fails safely.
- Initial generation and repair have distinct task names, prompt versions, request hashes, and cache identities. Repair includes only controlled validation reason codes and attempt identity, never private text or raw analyzer output.
- Candidate selection applies all Korean, sense, register, adaptive, Portuguese, duplication, and quality gates before deterministic scoring. It never accepts the first provider item merely because it parsed.
- At most one repair is allowed after both initial candidates fail complete-bundle acceptance. A failed repair persists a review-required or isolated failure state; it does not trigger another hidden chain.
- Regeneration delegates to the same selector, route policy, validation, scoring, cache, and telemetry semantics instead of maintaining a second algorithm.
- Tatoeba is never an automatic final-frequency source for Korean or any final-mode language. It may remain an explicit provenance-preserving reference tool outside final promotion.

### Explicit Task Routes, Budgets, Retry, Cache, and Telemetry

**Chosen approach:** Snapshot one explicitly approved provider/model route per task and prohibit cross-provider fallback for final Korean output.

- Definition, sentence generation, sentence repair, translation, optional judge, live Azure catalog, word audio, and sentence audio each have explicit route identities. A disabled task is explicit rather than silently substituted.
- Exact provider/model names, credentials, task attempt limits, token ceilings, estimated cost ceilings, latency ceilings, batch/concurrency limits, and any judge use require approval before live execution.
- Transport retries stay on the same pinned route, are bounded by policy, and remain distinct from candidate count and repair count. Exhaustion fails the item; it does not switch providers.
- Final Korean has no cross-provider text or audio fallback. Any future fallback requires a separately approved policy/version and cannot inherit approval from the primary route.
- Definition generation enters the same retry/cache/telemetry boundary as sentence and translation work. Every applicable call carries job, item, task, provider, model or voice, attempt, status, latency, and stable request/response hashes.
- Telemetry may store bounded token counts, estimated cost, latency, cache-hit state, controlled error/retry/fallback codes, manifest/policy versions, and sanitized hashes.
- Telemetry never stores prompts, completions, provider payloads, Korean learner text, translations, private highlight excerpts, local paths, reviewer notes, credentials, raw analyzer dumps, tracebacks, or unredacted exceptions.
- Stable evidence hashes use canonical serialized data, not `repr()` or process-dependent values. Cache hits are reported separately and never counted as provider attempts.
- Generation reports include denominators for missing token/cost metadata and do not overstate linguistic quality from provider metrics.

### One Approved Azure `ko-KR` Voice/Profile

**Chosen approach:** Qualify one exact live-discovered Azure `ko-KR` voice/profile and use it for both ordinary frequency word and sentence audio.

**Alternatives considered:** Separate voices for word and sentence assets; deterministic voice alternates; Google/ElevenLabs provider fallback; individual heard approval of every ordinary asset.

**Why this one:** One profile minimizes drift and review burden while the confirmed stratified-plus-risk review policy provides human evidence beyond provider success. Exact automated integrity still covers every file.

- Static documentation supplies candidates only. The selected voice must be present in the configured Azure region's live catalog, and the stored receipt binds exact catalog payload hash, region, checked-at time, provider/SDK version, `Locale="ko-KR"`, exact short name, catalog status/type, output format, and policy version.
- Korean stays absent from approved voice selection until both machine catalog evidence and human heard-profile approval pass. A guessed documentation voice cannot be registered to satisfy tests.
- Use neutral versioned SSML for both asset types initially. Do not inherit generic word pitch/rate/volume changes. Any heard-approved adjustment creates a new profile/SSML hash and invalidates prior dependent approval.
- Word and sentence audio remain separate assets and bind display text, NFC spoken text, text hash, exact SSML, request hash, provider, voice, locale, format, final byte size, artifact SHA-256, duration, storage identity, registry/profile version, and review evidence.
- Synthesis success is not approval. Provider success yields an integrity-checkable pending asset; only the approved profile plus exact current metadata/bytes can become exportable.
- Human playback covers at least 300 stratified word assets and at least 300 stratified sentence assets, with each sample set representing all three levels and relevant morphological/phonological strata.
- Every flagged pronunciation, homograph, register-sensitive, numeral/abbreviation, unusual morphology, or other policy-defined risk case receives heard review even when this exceeds the 10% minimum.
- All 6000 ordinary frequency assets receive exact NFC/text/request/SSML/provider/voice/locale/format/byte/hash/reference/integrity validation. Sample-based human approval never waives a failed per-asset structural check.
- No alternate voice, locale, or provider fallback is permitted. Catalog disappearance, provider failure, voice mismatch, stale approval, or risk-review failure blocks and remains resumable.
- Audio reuse requires complete request/profile/provider/voice/format/artifact/review identity. Matching text and voice alone are insufficient.
- An item reaches audio success only when both required assets are exact, non-fallback, integrity-valid, and approved under the current policy. A failed or pending asset cannot be counted as completed.
- Phase 31 remains authoritative for jamo and phonological-rule media. Phase 32 does not synthesize raw glyphs, replace foundation media, or reinterpret their approval.

### Approval and Checkpoint Plan

1. **Offline technical checkpoint — automatic.** Complete strict contracts, synthetic fixtures, final-mode refusal, persistence/migration, two-candidate selection, distinct repair, adaptive evidence, provider policy, privacy-safe telemetry, audio integrity, child-deck structure, reports, and regressions without network or paid calls.
2. **Phase 31 dependency checkpoint — blocking.** Final frequency known-state and learner-ready closure consume only a genuinely approved active Phase 31 snapshot. If Plan 31-28 evidence-bound activation is unavailable, continue only with technical fixtures and leave production blocked.
3. **Frequency source/license checkpoint — blocking human/legal decision.** Approve exact rank and lexical sources, versions, attribution, intended use, redistribution disposition, and allowed storage before opening source streams or creating/committing a production Korean asset path.
4. **Exact inventory checkpoint — blocking review.** Bind and review the final 3000 identities, rejection accounting, dominant senses, ranks, levels, analyzer evidence, license fields, and root/per-level hashes. Asset commit requires separate explicit authorization and terms that permit it.
5. **Korean and pt-BR content checkpoint — blocking human review.** Qualified reviewers approve the exact editorial policies and hash-bound evidence for naturalness, source sense, register, adaptive handling, glosses, and translations. Agent, provider, or judge output cannot satisfy this checkpoint.
6. **Provider/model/budget checkpoint — blocking operator approval.** Approve exact routes, models, credentials, token/cost/latency/batch ceilings, and a bounded live pilot before any paid generation. Full generation requires another explicit approval after pilot evidence.
7. **Azure catalog/profile checkpoint — blocking live and human review.** Authorize live catalog discovery and bounded samples, then approve one exact `ko-KR` voice and neutral or heard-adjusted SSML profile from exact sample bytes/hashes.
8. **Paid generation and synthesis checkpoint — blocking.** Authorize the bounded 3000-card text and 6000-asset audio runs under the approved routes/budgets. Persist item-isolated failures and stop on budget, catalog, or policy drift.
9. **Exact output review checkpoint — blocking.** Complete the confirmed stratified/risk playback coverage, all automated text/media checks, frozen review receipts, and 1000/1000/1000 child-deck structural inspection.
10. **Publication checkpoint — separately blocking.** Local approved artifacts do not authorize upload, publication, or distribution. Phase 34 still owns final all-family/observed Anki evidence, and external release requires explicit approval.

If any blocking source, reviewer, credential, budget, voice, byte, or authorization is unavailable, execution does not improvise. It records the missing category, proves fail-closed behavior, and narrows its claim to completed technical machinery.

### Anti-Regression Boundaries

- Preserve Phase 30 canonical `ko`, provider-only `ko-KR`, NFC normalization, compatibility/halfwidth rejection, source-backed lemma/POS/sense/register, exact Kiwi package/model/options fingerprint, top-two consensus, persistence, three-mode routing, target matcher, and highlight privacy.
- Preserve Phase 31 concept/source/review/media/receipt/snapshot/activation boundaries. Never copy a temporary fixture into production, mutate foundation candidates, or treat request-only artifacts as approval.
- Keep one shared lazy Kiwi service. Do not instantiate a second analyzer per candidate, scorer, judge, audio item, report, or exporter.
- Do not change Japanese, Mandarin, generic non-final morphology, Latin, foundation, custom-list, or highlight behavior merely to make Korean pass.
- Do not recurate or activate strict final mode for existing frequency languages in Phase 32.
- Do not let final Korean loading import or call `wordfreq`, use seed grounding, choose a first lexical sense, or invoke a provider to repair identity.
- Do not use generic suffix, token, substring, whitespace, Stanza-unavailable, or display-form heuristics as Korean final acceptance.
- Do not re-enable Tatoeba as automatic final-deck fallback.
- Keep current normal-card learner fields and blank `Image`; do not add learner-visible morphology, review, telemetry, or adaptive evidence fields.
- Preserve the current note GUID formula and inputs. Child-deck routing cannot trigger semantic IDs, history migration, or GUID changes.
- Do not allow `--allow-partial`, a test flag, a provider success, a fallback marker, or a manual database edit to promote blocked Korean production output to final success.
- All automated tests remain offline and use deterministic source/provider/catalog/audio fixtures. No test consumes real credentials or performs network, paid, asset-commit, publication, or raw-glyph synthesis work.
- Required regressions include Phase 30 Korean contracts, Phase 31 immutable foundation boundaries, existing modern languages, Japanese, Mandarin, Latin, custom lists, highlights, text/cache/retry/telemetry, audio, migrations, and current export field/GUID behavior.

### UI and Visual Claim Limits

Phase 32 adds no application page, dashboard, review-management UI, interaction flow, or visual design. Local CLI, data, provider, persistence, and Anki-package structure are the implementation surfaces.

- Static and archive tests may prove exact field order, child-deck membership, IDs, tags, GUIDs, media references, and deterministic package structure.
- Human heard review may prove the exact reviewed audio bytes under the approved coverage policy.
- Neither package inspection nor heard source-file review proves Anki Desktop/mobile import, rendering, fonts, responsive behavior, replay-button behavior, or in-Anki playback. Phase 34 owns those observed claims.
- Do not create screenshots or visual-proof artifacts in Phase 32 or describe structural tests as visual acceptance.

### Agent's Discretion

- Exact internal class, function, module, enum, reason-code, and helper names, provided all locked typed states and boundaries remain explicit.
- Internal implementation decomposition and plan/test file split, provided the source, identity, provider, audio, and child-deck authorities remain single and deterministic rather than duplicated.
- Exact migration revision identifier derived from the unique live Alembic head, provided the migration is additive, legacy-compatible, and fully round-tripped.
- Exact canonical serialization helper implementation, provided its externally stored hashes follow the locked canonical UTF-8 JSON/raw-byte SHA-256 rules.
- Exact synthetic lexical rows, provider candidates, catalog payloads, media bytes, and mutation fixtures used only in tests, provided they are unmistakably non-production, offline, and cannot satisfy approval.
- Exact deterministic tie-break helper and test parametrization after all locked hard gates and score priorities are honored.
- No agent discretion extends to product topology, rank/sense policy, Korean register, pt-BR policy, provider/model/budget selection, source/license terms, production lexical content, review coverage, reviewer authority, voice/profile choice, SSML approval, fallback, live/paid calls, asset commit, publication, Phase 31 evidence, or any excluded Phase 33/34/v4 work.

</decisions>

<assumptions>
## Validated Assumptions

### 1. Technical Approach

- **[high confidence][confirmed]** A Korean-first implementation of reusable strict final-mode infrastructure is preferable to immediate recuration of every existing frequency asset and adapter.
- **[high confidence][confirmed]** One atomic root bundle plus the Phase 30 source-backed identity and fail-closed matcher can provide reproducible authority from source decision through final child-deck membership.
- **[corrected by user]** The pre-alignment pattern assumption that Phase 34 exclusively owns real frequency-subdeck packaging is superseded. Phase 32 creates real Korean Level 1/2/3 child decks; Phase 34 generalizes and supplies final all-family/observed closure.
- **[corrected by user]** Portuguese regional policy is no longer unresolved for Phase 32: learner-facing output is pt-BR, while canonical project identity remains `pt`.
- **[high confidence][confirmed]** Current generic CSV, first-response generation, telemetry, and audio records are useful structural seams but are not sufficient production evidence; they must be extended additively rather than treated as approval.

### 2. Implementation Order

- **[high confidence][confirmed]** Complete all safe offline schemas, refusal paths, migrations, fakes, goldens, package structure, and regressions before any source acquisition, live catalog query, provider spend, or production asset write.
- **[high confidence][confirmed]** Validate source/license before asset creation; bundle before ingestion; identity/morphology before text; hard quality before adaptive scoring; route/budget before provider call; synthesis integrity before review; review before item success/export.
- **[high confidence][confirmed]** External checkpoints should not delay independent offline engineering, but fixture success must never be promoted into production authority.
- **[high confidence][confirmed]** Asset commit, local learner-ready artifact creation, and publication are distinct side effects with separate authorization.

### 3. Scope Boundaries

- **[high confidence][confirmed]** Phase 31 genuine gates remain prerequisites and cannot be bypassed, synthesized, or inferred from temporary exports.
- **[high confidence][confirmed]** Phase 32 owns the Korean frequency inventory, text, ordinary word/sentence audio, and actual Korean child decks, but not Phase 33 grammar/personal-source/field-review work.
- **[high confidence][confirmed]** Phase 34 retains workers, generalized existing-language subdeck closure, all-family export/evidence, and observed Anki visual/import/playback acceptance.
- **[high confidence][confirmed]** v4 identities, GUID/history migration, adaptive queues, and learner scheduling remain excluded.
- **[high confidence][confirmed]** No application UI or visual-proof deliverable exists in this phase.

### 4. Risk Areas

- **[high confidence][confirmed]** Silent final fallback is a greater risk than an actionable blocked item. Missing assets, unresolved senses, inconclusive morphology, failed candidates, route exhaustion, unavailable voice, failed audio, stale hashes, or absent approval therefore fail closed.
- **[high confidence][confirmed]** Privacy-safe telemetry is mandatory: only controlled identifiers, sanitized hashes, and bounded metrics persist; prompts, payloads, private excerpts/paths, secrets, and raw analyzer evidence never do.
- **[high confidence][confirmed]** Naturalness cannot be traded for a better i+1 score, and provider/judge success cannot grant source, linguistic, Portuguese, audio, or release approval.
- **[corrected by user]** Ordinary frequency audio does not require individual playback of every file: at least 10% stratified of each type plus all flagged/homograph/risk cases is the human coverage policy, while 100% exact automated integrity remains mandatory.
- **[high confidence][confirmed]** Child-deck changes are safe only when note GUID inputs, fields, tags, and media identity remain unchanged and stable IDs pass collision checks.

### 5. Dependencies

- **[high confidence][confirmed external dependency]** Source selection is now user-confirmed, but exact NIKL bytes, terms/attribution evidence, transformed-data redistribution disposition, and the reviewed 3000-entry bundle are not supplied by technical implementation.
- **[high confidence][confirmed source path]** NIKL `한국어 학습용 어휘 목록` is selected as the rank and initial lexical-authority path; exact attachment identity, attribution/terms evidence, transformation review, modernity curation, and asset commit remain external checkpoints rather than assumed approval.
- **[high confidence][confirmed external dependency]** Phase 31 active approved evidence, qualified Korean and pt-BR reviewers, and their exact hash-bound decisions are required for learner-ready closure.
- **[high confidence][confirmed external dependency]** Exact text provider/models, credentials, task budgets, token/cost/latency ceilings, and live/paid run approvals must be supplied explicitly.
- **[high confidence][confirmed external dependency]** Azure region/credentials, live catalog receipt, exact approved `ko-KR` voice/profile, sample bytes, heard decisions, and complete production audio are checkpoint-bound.
- **[high confidence][confirmed external dependency]** Production asset commit, local final-artifact activation where applicable, and any publication or distribution require explicit separate authorization.
- **[high confidence][confirmed]** None of these external dependencies is needed to prove the offline technical contracts and refusal behavior with strict deterministic fixtures.

</assumptions>

<deferred>
## Deferred Ideas

- **Phase 33:** Reviewed Particles & Endings curriculum, strict grammar i+1, personal-list/highlight bridge/defer behavior, resumable item-state hardening assigned there, and field-level approve/reject/edit/regenerate commands.
- **Phase 34:** Generalize real frequency child decks across applicable existing languages; bounded PostgreSQL workers/claims; all Korean-family APKG/CSV/TSV closure; final milestone evidence; and observed Anki Desktop/mobile import, rendering, font, responsive, and playback acceptance.
- **Later explicit rollout:** Recurate existing frequency inventories and qualify each selected language-specific morphology adapter before activating the shared strict final mode for those languages.
- **Out of v3.0:** Semantic/form-card identities, GUID migration, APKG history import/adaptation, learner-history synchronization, adaptive queues, scheduling integration, Hanja curricula, regional Korean dialect decks, and interactive tutoring.

The missing Phase 31 approvals, exact NIKL attachment/terms evidence, final 3000-entry asset, qualified Korean/pt-BR review, provider budgets/models, live Azure evidence, production media, asset-commit authorization, and publication authorization are **not** deferred product ideas. They are named Phase 32 completion checkpoints. If unavailable, the correct result is a verified blocked production path, not fabricated learner-ready output.

</deferred>

---

*Phase: 32-frequency-portuguese-text-and-audio*
*Approach explored: 2026-08-21*
