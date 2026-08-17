# Phase 30: Korean Contracts and Morphology - Approach

**Explored:** 2026-08-03
**Status:** Ready for planning

## Alignment Proof

- `workflow.discuss`: true
- `alignment_status`: user_confirmed
- `alignment_method`: Direct user message in the Phase 30 planning conversation; the user selected **"Usar decisões existentes"** and explicitly approved the formalized `KOREAN-STRUCTURE.md` decisions, the conservative Kiwi top-two consensus policy, and retention of the Korean frequency-asset license block.
- `user_confirmed_at`: 2026-08-03
- `explicit_skip_approved`: false
- `skip_scope`: N/A
- `skip_rationale`: N/A — the user confirmed decisions rather than approving a discussion skip.
- `confirmed_decisions`:
  - Use the decisions formalized in `KOREAN-STRUCTURE.md` as the Phase 30 implementation baseline.
  - Keep `ko` as the sole product identity and reserve `ko-KR` for provider/locale boundaries.
  - Use pinned Kiwi analysis, NFC canonicalization, source-backed lemma/POS/sense identity, and morpheme-signature matching rather than generic Korean heuristics.
  - Require consensus across Kiwi's top two analyses; any disagreement fails closed to review.
  - Retain the block on committing or redistributing a 3000-entry Korean frequency asset until source, attribution, and redistribution terms are approved.

<domain>
## Phase Boundary

Phase 30 makes Korean a first-class language in the existing modern generation pipeline for frequency, word-list, and highlight modes. It establishes the canonical language/profile contracts, Unicode NFC boundary, pinned Kiwi adapter, source-backed lexical identity, persisted analyzer evidence, and morphology-aware target matcher required by `KMODE-01`, `KMODE-02`, `KNLP-01`, and `KNLP-02`.

The phase may prove that existing generic frequency/manual/highlight schemas carry canonical Korean text and the `ko` identity. It does **not** create learner-facing Korean curricula, final Korean note types, a production 3000-entry frequency asset, Korean audio, an approved Azure voice, final three-subdeck topology, or final APKG readiness. Those remain in Phases 31-34.

This is a backend/contracts phase. It introduces no page, component, layout, styling, interaction, responsive, or other UI design decision. Existing visual templates are no-touch by default.

</domain>

<decisions>
## Implementation Decisions

### Gray Areas Explored

| Gray area | Classification | Locked disposition |
|---|---|---|
| Korean identity and modern-pipeline routing | Technical | One canonical `ko` identity in the existing modern pipeline; locale/provider translation only at adapters. |
| Unicode, analyzer, and lexical-identity authority | Technical | Reject forbidden compatibility forms, normalize to NFC, use exact-pinned Kiwi as morphology evidence, and bind a source-backed sense before an identity is resolved. |
| Multi-analysis target matching | Technical | Compare ordered morpheme signatures and accept only when both top-two Kiwi analyses agree; all disagreement or inconclusive states require review. |
| Frequency capability versus licensing and later-phase assets | Hybrid (technical gate plus product-risk tolerance) | Expose Korean routing without creating the blocked production asset; retain an explicit, actionable license gate and later-phase boundaries. |

### Canonical Korean Identity and Routing

**Chosen approach:** Add Korean to the shared modern-language pipeline with `ko` as its single canonical product code.
**Alternatives considered:** A separate Korean generation pipeline; accepting both `ko` and `ko-KR` internally; translating codes ad hoc in each service.
**Why this one:** It satisfies the existing three-mode contract without duplicating orchestration, while preventing split cache, persistence, asset, and export identities. It follows the approved structure and existing Japanese/Mandarin modern-language precedent.

- `SupportedLanguage.KO` and all public/internal request, settings, job, run-key, lookup, cache, database, export-identity, and Anki-tag values use exactly `ko`.
- `ko-KR` is a boundary constant only for adapters that require a locale/provider value. It is not a supported language enum, source directory, lexical key prefix, persisted job language, or tag.
- Frequency, word-list, and highlights continue to use the existing source profiles and `GenerationRequest` pipeline; no Korean-only source mode or Latin-style isolated path is introduced.
- The Korean language profile identifies modern standard/Seoul Korean and uses Portuguese for definitions, glosses, and translations.
- Korean identity evidence must participate in typed generation requests and deterministic cache/request hashes so homographs with different POS or sense cannot reuse generated content.
- Provider output remains untrusted: Korean output is NFC-normalized at its typed boundary and must pass the same stored-identity morphology gate before acceptance.

### Unicode and Lexical Identity Contract

**Chosen approach:** Validate Korean script policy, canonicalize to NFC, analyze morphology, intersect analyses with source-backed lexical records, and persist one typed identity before generation.
**Alternatives considered:** NFKC compatibility folding; generic case/whitespace normalization; accepting Kiwi's top-ranked analysis as identity; deriving sense from an LLM or Kiwi's internal meaning number.
**Why this one:** Canonical equivalence must be deterministic without disguising invalid compatibility forms, and the project identity is lemma + POS + sense rather than an analyzer token or visible surface form.

- Preserve the submitted form separately. Derive canonical display values, analyzer input, stable keys, hashes, persistence values, and comparison values from NFC text.
- Re-normalize at every stable ingress/output/assembly boundary, including after concatenation and before hashing, lookup, persistence, comparison, or export.
- Reject Hangul Compatibility Jamo (`U+3130-U+318F`) and halfwidth Hangul (`U+FFA0-U+FFDC`) for canonical learner content. Do not silently repair them with NFKC.
- A resolved `KoreanLexicalIdentity` includes canonical NFC form, source-backed lemma, normalized lexical POS, source-backed `sense_id`, ordered morpheme signature, submitted form where applicable, register, analyzer fingerprint, and resolved status.
- A resolved identity cannot contain blank or unknown lemma/POS/sense, an empty signature, non-NFC canonical values, or unavailable/ambiguous analysis. Those conditions produce typed non-passing outcomes instead of placeholder identities.
- Kiwi morphology constrains lemma/POS/signature but does not author project sense identity. Until an approved production lexical source exists, use small reviewed/synthetic records for tests and leave production candidates unresolved.
- The deterministic Korean lexical key includes canonical lemma + normalized POS + source-backed sense ID. The structured identity remains authoritative; the key supports indexing, deduplication, cache isolation, and future GUID continuity.

### Kiwi Adapter, Versioning, and Persistence

**Chosen approach:** One shared, lazy, project-owned Kiwi adapter with exact analyzer/model pins and an explicit configuration fingerprint. Persist the resulting typed identity before generation or resume.
**Alternatives considered:** One Kiwi instance per service/card; eager import at application startup; optional Stanza or KoNLPy as the Korean authority; broad dependency ranges; reanalysis on every resume.
**Why this one:** A single adapter isolates vendor APIs, prevents model/configuration drift, avoids repeated model initialization, and allows non-Korean modes to boot when Korean analysis is unavailable.

- Pin `kiwipiepy==0.23.2` and `kiwipiepy-model==0.23.0`; both code and model versions affect persisted signatures.
- Use one runtime-composed lazy service shared by lexical grounding, Korean highlight extraction/preview, and text validation.
- Lock the initial profile to modern standard Korean with `model_type="cong"`, `num_workers=1`, `enabled_dialects="standard"`, explicit allomorph integration, no typo correction, no compatibility-jamo repair, no appended-coda repair, and no mutable user dictionary.
- Persist analyzer package version, model package version, model type, relevant options, and an application-owned policy/configuration version with resolved evidence.
- Store the typed Korean identity in one nullable JSON field on the shared lexical-candidate persistence boundary. Existing non-Korean records and constructors remain valid with `NULL` evidence.
- Serialize/restore through the Pydantic model, and prove commit/expire/reload plus Alembic/ORM schema parity. Do not hide analyzer evidence in prose notes or persist vendor token objects.
- If the runtime fingerprint differs from persisted evidence, require explicit reanalysis/review. Never silently combine evidence from different analyzer or policy versions.
- Import/model/runtime failures become privacy-safe typed `unavailable` outcomes. They block Korean work but do not prevent unrelated languages from starting or retaining their current behavior.

### Morpheme Signatures and Conservative Consensus

**Chosen approach:** Match the stored lexical identity against ordered Kiwi-derived lexical signatures within eojeol boundaries, using consensus across exactly the top two analyses.
**Alternatives considered:** Whitespace/subsequence/substring matching; naive suffix stripping; accepting Kiwi top-1; accepting when any analysis matches; selecting by an uncalibrated score threshold.
**Why this one:** Korean inflection and attached particles require morphology, while homographs and alternate analyses make permissive matching unsafe. The user explicitly selected the conservative false-negative-over-false-positive policy.

- Analyze with `top_n=2` under the locked configuration and include the policy version in the analyzer fingerprint.
- Project each analysis to ordered `(NFC form, normalized base POS)` lexical items grouped by Kiwi `word_position`.
- Remove particles (`J*`) and inflectional endings (`E*`) from lexical comparison; preserve derivational `XSV`/`XSA` and require compound predicate items to occur in order within the same eojeol.
- Normalize regular/irregular tag suffixes to their base lexical POS for matching while retaining raw irregularity as diagnostic evidence.
- Use lexical POS and source-backed sense identity to keep noun/predicate homographs distinct.
- Accept target presence only when **both** returned analyses independently match the full stored target signature.
- One matching and one non-matching analysis is `ambiguous`, not success. Two non-matching analyses are `mismatch`.
- Missing analyses, OOV evidence, unresolved sense, absent persisted identity, malformed signature, analyzer/model error, or any analysis disagreement all fail closed to review.
- Korean must branch before Japanese/Mandarin substring handling and before generic key, Stanza, suffix, or heuristic matching. A Korean result may never fall through to those paths.
- Required real-analyzer goldens cover noun + particle, regular predicate, reviewed irregular predicate, adjectival predicate, compound predicate, POS homograph, NFC/NFD equivalence, forbidden compatibility input, ambiguous context, OOV/unavailable analysis, and substring/cross-eojeol negatives.

### Three-Mode Grounding and Privacy

**Chosen approach:** Make all three existing source modes produce the same persisted Korean lexical-identity shape, with mode-specific input preservation and existing privacy boundaries intact.
**Alternatives considered:** Morphology only during sentence validation; separate identity shapes per source mode; persisting raw highlight excerpts or complete Kiwi analyses.
**Why this one:** Grounding identity once before provider generation makes reruns reproducible and lets validation use the exact same evidence without exposing private reading content.

- **Frequency:** Korean is a selectable routed capability, but Phase 30 tests it with temporary/reviewed fake candidates only. No production Korean frequency file is created.
- **Word list:** Preserve the submitted form and input order, canonicalize/analyze the surface form, resolve to source-backed lemma/POS/sense, and persist both submitted and resolved identity.
- **Highlights:** Analyze bounded text locally before generic regex/NFKC/length filters; retain valid one-syllable lexemes, attached-particle/endings analysis, and same-eojeol compounds; deduplicate by lemma + POS + sense.
- Highlight-safe candidates persist only canonical lexical evidence plus existing hashes and source indexes. Raw excerpts, local paths, neighboring context, prompt text, tracebacks, and vendor token dumps do not enter public persistence, telemetry, errors, or export.
- Provider-visible highlight context remains redacted, bounded, and clearly treated as untrusted data. LLM output cannot author or override morphology, POS, sense, or approval state.

### Frequency License and Downstream Capability Gates

**Chosen approach:** Separate “selectable languages” from “languages with approved committed frequency assets,” and retain an explicit fail-closed Korean asset gate.
**Alternatives considered:** Commit a provisional `wordfreq`-derived CSV; let build-all create Korean automatically; silently skip Korean; use a missing file or unrelated runtime exception as the gate.
**Why this one:** Phase 30 must expose routing without treating technical selectability as redistribution permission. The user explicitly retained the 3000-entry asset block.

- Do not create or commit `assets/frequency/ko/curated-v*.csv` or any other redistributed 3000-entry Korean asset in Phase 30.
- The approved-committed-asset capability list excludes `ko`, so normal build-all/check behavior remains deterministic for currently approved assets.
- An explicit Korean production asset build/check fails with an actionable license-gate/domain message; it must not seed an asset, silently skip, or imply approval.
- Approval of source, attribution text, redistribution terms, and the final 3000-entry inventory remains a Phase 32 gate.
- Do not add or guess an Azure Korean voice, synthesize Korean audio, register Google/ElevenLabs production fallbacks, or perform paid/live provider calls. Korean voice qualification belongs to Phase 32.
- Korean Tatoeba fallback is explicitly disabled before network access in this phase; a future reviewed reference integration would need Korean morphology matching and provenance.
- Keep generic export field schemas and the blank `Image` contract. Do not add Korean note/model/deck IDs, learner-visible morphology fields, or final export topology in Phase 30.

### Anti-Regression Boundaries

**Chosen approach:** Isolate Korean behavior at explicit language branches and additive nullable contracts; protect high-leverage shared surfaces with focused existing-mode and full-suite evidence.
**Alternatives considered:** Generalize existing matching/normalization globally; change templates/export models preemptively; weaken exhaustive registries to make `ko` pass.
**Why this one:** `KMODE-02` requires Korean support without contract drift, and the supplied pattern map identifies shared registries, persistence, audio, and export as high-leverage surfaces.

- Existing modern frequency, custom-list, and highlight generation/export behavior remains unchanged.
- Existing Japanese furigana/readings, Mandarin orthography/snapshots, isolated Latin flow/audio, and phoneme deck behavior remain unchanged.
- Generic non-Korean Stanza and heuristic matching behavior is not tightened or replaced by Korean policy.
- Kiwi unavailability affects Korean only; unrelated application startup and generation routes remain operational.
- Existing rows continue to round-trip with `korean_identity = NULL`; migration upgrade/downgrade and schema parity are mandatory.
- Audio registry exhaustion must produce the existing domain error for unapproved Korean voice selection, not a raw `KeyError`, and must not alter approved voices for other languages.
- Existing template and export source files are no-touch unless a focused Korean contract test proves the generic fallback insufficient. Any such need is a stop-and-challenge point, not permission for opportunistic redesign.
- Canonical scans must prove every changed-code occurrence of `ko-KR` is an explicit locale/provider contract and that stored/tagged identity is exactly `ko`.
- Focused evidence must cover all three Korean modes, persistence reload, analyzer goldens, ambiguity/unavailable failures, privacy-safe highlights, generic export identity, existing-mode regression suites, dependency-lock integrity, and the full test suite.
- The pre-existing Japanese export-snapshot gap is not a Phase 30 repair. If implementation would touch that surface, stop and isolate or explicitly re-scope it rather than claiming it as Korean work.
- Phase closure may claim canonical routing, morphology contracts, persistence, and matching only. It may not claim production Korean frequency content, approved audio, final templates, final APKG/import readiness, or learner-facing review UI.

### UI and Visual Design

No UI design choices apply in Phase 30. Do not introduce or revise screens, review dashboards, layout, colors, typography, responsive behavior, template styling, or learner-facing morphology displays. Later phases own Korean template/readability and review surfaces; this phase only preserves their backend prerequisites and existing visual contracts.

### Agent's Discretion

- Exact project-owned class, enum, method, and privacy-safe reason-code names, provided the locked typed states and invariants remain explicit.
- Internal method decomposition, bounded caching, and batching inside the single shared lazy Kiwi adapter.
- The exact immutable Pydantic submodels used for signature items and analyzer fingerprints, provided one coherent typed identity round-trips through the nullable JSON field.
- Test-module organization and the specific reviewed irregular/negative fixtures, provided every required golden category and existing-mode boundary is covered with real Kiwi positives and boundary fakes.
- Exact wording of actionable license/analyzer/voice errors, provided it is deterministic, domain-specific, and never echoes private input, paths, prompts, or raw analyzer dumps.
- Migration revision filename/identifier based on the unique live Alembic head at execution time; schema intent and parity requirements are locked.
- Minor provider-map wiring needed to identify Korean in grounded prompts, provided `ko` remains canonical, Portuguese remains the output target, no live call is required, and no unverified provider capability is asserted.
- No agent discretion extends to weakening top-two consensus, adding heuristic Korean fallback, committing the frequency asset, introducing UI work, or changing later-phase boundaries.

</decisions>

<assumptions>
## Validated Assumptions

### 1. Technical Approach

- **[confident][confirmed]** The existing Python/Pydantic/SQLAlchemy/Alembic/pytest modern pipeline remains the platform; Korean adds typed language-specific contracts and an adapter rather than replacing the architecture.
- **[confident][confirmed]** NFC plus a pinned Kiwi code/model pair is the authority for Korean morphology evidence; source-backed lexical data remains the authority for sense identity.
- **[corrected by user]** Research assumption A1 treated `top_n=2` consensus as provisional. The user has now locked it for Phase 30: both analyses must agree, and any disagreement goes to review.
- **[assuming][accepted under existing decisions]** One optional typed Korean identity on the shared candidate and one nullable JSON column are sufficient for Phase 30 persistence; final learner/export schemas need no Korean-only fields yet.

### 2. Implementation Order

- **[confident][accepted under existing decisions]** Establish failing contract/golden tests and exact dependency pins first; then add canonical registries and domain contracts; then the shared Kiwi adapter and persistence; then wire all three modes and strict validation; finally run focused and full anti-regression evidence.
- **[assuming][accepted under existing decisions]** Persistence is completed before provider-generation wiring so resume, cache, and matcher behavior all consume one frozen identity rather than reanalyzing opportunistically.
- **[confident][accepted under existing decisions]** Asset, audio, template, and final export work does not move earlier merely to make integration fixtures easier; use offline fakes and generic contracts instead.

### 3. Scope Boundaries

- **[confident][confirmed]** Phase 30 is contracts, registries, Unicode, Kiwi, persisted morphology evidence, and target matching only.
- **[confident][confirmed]** There are no UI or visual-design deliverables in this phase.
- **[confident][confirmed]** The 3000-entry Korean frequency asset remains blocked; technical routing does not authorize source redistribution.
- **[confident][accepted under existing decisions]** Small synthetic/reviewed lexical records may prove the contract, but they are test fixtures rather than a production source or partial frequency inventory.

### 4. Risk Areas

- **[confident][confirmed policy]** False-positive target acceptance is more harmful than a review-required false negative; ambiguity, OOV, missing sense, drift, or unavailable analysis therefore fails closed.
- **[assuming][accepted under existing decisions]** Top-two consensus may be conservative across the future 3000-entry inventory and authentic highlights. Phase 30 records counts/goldens but does not relax the locked policy without later calibration and a new policy fingerprint.
- **[confident][accepted under existing decisions]** The highest regression risks are shared registries, generic matching, persistence/migrations, audio exhaustiveness, frequency build-all behavior, and private highlight boundaries; these require explicit anti-regression evidence.
- **[confident][accepted under existing decisions]** Raw learner text, paths, analyzer dumps, and prompt instructions are untrusted/private and must not leak through errors, evidence, persistence, telemetry, or export.

### 5. Dependencies

- **[corrected by supplied pattern evidence]** `SPEC.md` still describes Mandarin quick task 027 as active, but `30-PATTERNS.md` records that its shared-code prerequisite was reconciled in committed code. Planning should use the reconciled live baseline and recheck it at execution rather than modifying the stale spec here.
- **[confident][accepted under existing decisions]** Exact Kiwi/model packages are available for supported Python environments, but are not yet in the project manifest/lock; installation and lock verification are Phase 30 work.
- **[confident][accepted under existing decisions]** No production Korean lexical/frequency source is approved yet. The contract is source-neutral, tests use reviewed/synthetic records, and production unresolved senses remain blocked.
- **[confident][accepted under existing decisions]** Phase 30 needs no live Korean provider, paid call, production PostgreSQL service, approved Azure voice, or redistributed corpus to prove its requirements; local Kiwi, existing SQLite test patterns, and offline provider fakes are sufficient.
- **[assuming][accepted under existing decisions]** The planner must resolve migration identifiers and any shared-file drift against the current execution head, while preserving the nullable additive schema and all listed regression boundaries.

</assumptions>

<deferred>
## Deferred Ideas

- **Phase 31:** Hangul foundations, pronunciation i+1 curriculum, Korean note/model/deck identities, template derivation, and reviewed pedagogical media.
- **Phase 32:** Approve the production Korean lexical/frequency source and redistribution policy; curate/freeze the 3000-entry asset; build three real 1000-card subdecks; define Korean sentence-quality/length policy; qualify live Azure `ko-KR` voice/audio; and calibrate the ambiguity policy against a reviewed larger corpus before any future version change.
- **Phase 33:** Full Particles & Endings curriculum and learner-facing custom/highlight bridge/defer pedagogy beyond the Phase 30 morphology/routing groundwork.
- **Phase 34:** Final Korean export topology, note/template readability, review-management surfaces, Desktop/mobile evidence, and milestone-wide requirement evidence.
- **Separate repair:** The pre-existing Japanese derived-reading snapshot persistence gap. It is not to be folded into Phase 30 without explicit ownership.
- **Out of v3.0:** Hanja curriculum, regional dialect decks, persistent lexical romanization, automatic phonetic-audio approval, unlicensed corpus mining/distribution, an interactive tutor, and learner-mastery synchronization with Anki scheduling.

</deferred>

---

*Phase: 30-korean-contracts-and-morphology*
*Approach explored: 2026-08-03*
