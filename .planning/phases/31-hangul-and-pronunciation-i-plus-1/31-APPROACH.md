# Phase 31: Hangul and Pronunciation i+1 - Approach

**Explored:** 2026-08-04
**Status:** Replanned for authoritative, explicit AI linguistic review with parallel media/rights execution

## Alignment Proof

- `workflow.discuss`: true
- `alignment_status`: user_confirmed
- `alignment_method`: Direct user decisions in the Korean milestone and Phase 31 planning conversations. On 2026-08-27 the user explicitly removed mandatory human linguistic review, assigned linguistic review to AI, and requested parallel plan execution.
- `user_confirmed_at`: 2026-08-27
- `explicit_skip_approved`: false
- `skip_scope`: N/A
- `skip_rationale`: N/A — discussion was not skipped; the user explicitly chose the implementation and blocking posture.
- `confirmed_decisions`:
  - Use the approved `KOREAN-STRUCTURE.md` decisions as the Phase 31 product and curriculum baseline.
  - Use the canonical phase slug `i-plus-1` and keep all Phase 31 artifacts under `.planning/phases/31-hangul-and-pronunciation-i-plus-1/`.
  - Implement the complete technical curriculum, contracts, frozen manifests, templates, exporters, review gates, and media gates now rather than waiting for unavailable human or media inputs.
  - Keep every checked-in production learner-ready record and artifact fail-closed until real licensed media bytes, deterministic validators, and all applicable AI-policy review passes are bound to exact source/media hashes.
  - Use an explicit bootstrap followed by one shared strict concept graph whose unknown evidence is recomputed rather than trusted from source files.
  - Keep pedagogical Compatibility Jamo display mapping separate from canonical modern conjoining-jamo identity and preserve Phase 30 canonicalization unchanged.
  - Create a Korean-owned Hangul template and extract only language-neutral phoneme mechanics while preserving existing public APIs and rendered behavior.
  - Build a deterministic dedicated exporter for both foundation families in APKG, CSV, and TSV that refuses unapproved production inputs before writing anything.
  - Permit synthetic fixture media only inside tests; production-generated audio is allowed only in the exact bounded owner-authorized Phase 31 media lane and must pass rights, integrity, and AI acoustic gates.
  - Permit the executor agent to author bounded, hash-bound, noncanonical `draft_only` learner-copy proposals outside `data/korean_foundations/` and `evidence-inbox/`; every proposal remains `needs_review`, has no promotion authority, and must be selected by exact hash before it can become a new candidate asset.
  - Replace Korean, Portuguese, phonetics, curriculum, and playback linguistic-human gates with `.planning/AI-LINGUISTIC-REVIEW-POLICY.md`; AI evidence must identify itself and never impersonate a human role.
  - Keep rights, provider spend/private processing, external production mutation, and publication authority separate from linguistic review.
  - Permit bounded Azure `ko-KR` foundation synthesis in Phase 31 after exact project-owner authorization of rights document hash, route, voice/profile, item set, attempt ceiling, and budget. The user confirmed this scope on 2026-08-27.
  - Keep instrumented Anki Desktop/mobile import, rendering, and playback acceptance in Phase 34; it does not block Phase 31 local activation/export after exact AI, rights, media, and integrity evidence passes.
  - Run disjoint plans concurrently in isolated worktrees and join by exact hashes; do not fabricate rights, synthesize a raw glyph, ship silence/dummy media, make an unauthorized live/paid call, or overclaim visual acceptance.

## 2026-08-27 AI-Review And Parallelism Amendment

This amendment supersedes every earlier Phase 31 statement that makes a human
linguist, native speaker, Portuguese reviewer, or human playback reviewer a
mandatory authority. Historical artifacts remain truthful records of the older
blocked posture but do not govern new execution.

- AI review is production authority only under `.planning/AI-LINGUISTIC-REVIEW-POLICY.md` and uses `ai_review_passed`, never a human role or credential.
- Standard records receive two independent fresh-context passes; P11-P13,
  strict-i+1, phonological rules, morphology-sensitive identity, and validator-
  flagged records receive three passes. Passes execute in parallel batches.
- Deterministic graph, Unicode, morphology, source, schema, media, and hash checks
  remain non-overridable. Disagreement or uncertainty blocks the exact record.
- Audio uses exact-byte integrity, decoding/acoustic checks, and AI acoustic review
  where supported. No AI record claims that a person heard the bytes.
- Rights/license, provider budget/private processing, network, external activation,
  and publication remain project-owner authorities and block only their own lane.
- The user explicitly authorized Phase 31 to plan bounded Azure `ko-KR`
  foundation synthesis. No call is authorized until the later exact media-rights
  hash, voice/route, items, attempts, credentials boundary, and budget handoff is
  supplied and consumed once.
- Plans 31-26 through 31-28 are historical/superseded. Plan 31-29 records one
  clean common runtime/baseline; 31-30 and 31-31 then run concurrently; 31-32
  is their exact-hash join.
- Phase 32 offline plans may start concurrently in an isolated worktree. Its
  production generation joins the exact active Phase 31 snapshot later.

## 2026-08-23 Assisted-Curation Amendment

The user clarified that the assistant is expected to perform the initial content curation. This historical amendment changed only preparation; the 2026-08-27 amendment now replaces its human-only authority limitation.

- AI-assisted output is written only under `curation-drafts/` as typed, hash-bound patches against exact source-entry hashes. It is never written directly into the canonical evidence inbox.
- Drafts may propose Hangul learner names/readings, sound guidance, mnemonics, Korean pronunciation examples, normative/surface pronunciation, and Portuguese learner copy. They must preserve item keys, sequence, graph identities, stages, categories, prerequisites, observed/unknown concepts, active rules, and media-slot identities.
- Every proposed field records source grounding or an explicit uncertainty code. Unsupported values remain unresolved; plausible wording is not promoted as fact merely to obtain complete coverage.
- The draft schema remains nonauthoritative. Promotion into AI review creates separate policy-bound evidence; drafts still cannot assert human qualification, rights/redistribution, media hashes, or production voice authority.
- A user checkpoint may select exact draft hashes for candidate promotion only. Selection does not constitute linguistic, Portuguese, legal, playback, release, or Anki acceptance.
- Selected drafts create new immutable `v2` candidate packs because the existing `v1` source packs are immutable. All regenerated curation/media manifests remain `candidate_only: true` and `needs_review`.
- Production evidence, receipt preparation, activation, and export remain separate gates; only the media/provider lane may make explicitly authorized bounded provider calls.

<domain>
## Phase Boundary

Phase 31 implements the complete technical foundation path for `KHAN-01`, `KHAN-02`, `KPRO-01`, and `KPRO-02`: modern Hangul identity/composition contracts, the H0-H10 and P0-P13 curriculum structures, executable strict-i+1 evidence, versioned source/review/media manifests, Korean note/model/deck identity, the Korean-owned Hangul template, shared phoneme mechanics, exact media-integrity gates, and deterministic APKG/CSV/TSV export for both foundation families.

The governing delivery posture is **implement and block**:

- Technical contracts, validators, candidate inventories, templates, exporters, CLI boundaries, and tests are implemented completely.
- Checked-in production curation and media state starts and remains `needs_review` wherever real evidence is absent.
- The production exporter must demonstrate that those inputs are blocked; it must not emit a learner-ready artifact merely to make a happy-path demo pass.
- Happy-path exporter tests use transient, generated media and approved-shaped records under test-owned temporary directories only. They do not modify production manifests and do not constitute human, licensing, playback, or release evidence.
- A technically complete implementation may be verified as implementing the blocked workflow, but Phase 31 may not be described as delivering reviewed learner-ready decks until the real approval checkpoints in this document are satisfied.

### Requirement Disposition

| Requirement | Phase 31 implementation truth | Release truth while approvals are missing |
|---|---|---|
| `KHAN-01` | Implement the complete Hangul inventory/coverage contracts, Korean note identity, template, media joins, and all-format export path. | Hangul production rows stay `needs_review`; no approved-media or learner-ready deck claim. |
| `KHAN-02` | Implement explicit bootstrap, shared concept registry, graph validation, NFC evidence, and recomputed exactly-one-unknown enforcement. | Deterministic validity plus policy-bound AI review is required for concept atomicity, names, strokes, mnemonics, and examples. |
| `KPRO-01` | Implement the exact shared nine-field learner schema, Korean-specific IDs, complete source evidence, media survival, and APKG/CSV/TSV structure. | No production pronunciation artifact exports until exact approved media and linguistic/Portuguese/playback evidence exist. |
| `KPRO-02` | Implement complete P0-P13 stage/category coverage rules, dependency order, active-rule accounting, and strict failure cases. | Candidate phonetic analyses, P11-P13 atomization, and recordings remain blocked until deterministic and critical multi-pass AI review passes. |

### Explicitly Outside This Phase

- The Korean 3000-entry frequency asset, source/redistribution decision, three 1000-card frequency subdecks, and frequency text generation.
- Unbounded provider calls, generic retry/fallback policy changes, frequency-deck voice qualification, or live provider operations outside the exact project-owner-authorized Phase 31 foundation-media manifest.
- Particles & Endings, Custom, and Highlights pedagogy beyond preserving the verified Phase 30 boundary.
- A database migration, job/runtime integration, or changes to generic modern export schemas for this frozen foundation path.
- A review-management UI, gate-editing UX, user-APKG ingestion, remote media acquisition, or arbitrary URL/path import.
- Final Anki Desktop/mobile import, rendering, font, responsive-layout, or playback acceptance; Phase 34 owns that observed evidence.

</domain>

<decisions>
## Implementation Decisions

### Gray Areas Explored

| Gray area | Classification | Approaches researched | Locked disposition |
|---|---|---|---|
| Foundation ownership and persistence | Technical | Embedded Python inventories; database-backed jobs; isolated frozen manifests | Use an isolated, versioned manifest path modeled on the Latin source/review/media boundary. Do not enter the modern runtime or add a migration. |
| Strict-i+1, bootstrap, and Hangul identity | Technical | Ordered syllabus/trusted unknowns; adaptive scoring; explicit graph with recomputation; NFKC/generic canonicalization; positional display mapping | Use one explicit bootstrap plus one shared strict graph, recompute all evidence, and model pedagogical display glyphs separately from canonical conjoining Jamo. |
| Template/model reuse without regression | Technical | Parameterize the Japanese template; duplicate all phoneme code; extract neutral mechanics with compatibility wrappers | Build a Korean-owned Hangul template and extract only language-neutral nine-field phoneme mechanics while preserving every existing API and rendered contract. |
| Export, media, and approval completion posture | Hybrid (technical pipeline plus release-risk posture) | Live/best-effort synthesis; generic exporter extension; dedicated fail-before-write exporter; wait for inputs; implement-and-block | Implement the dedicated all-format pipeline now and require real hash-bound rights, bounded owner-authorized media generation, deterministic checks, and policy-bound AI review before learner-ready export. |

### Canonical Slug and Isolated Foundation Ownership

**Chosen approach:** Use the canonical slug `i-plus-1` and a dedicated, frozen Korean foundation path.
**Alternatives considered:** Continue the earlier `i-plus-one` spelling; embed content in Python tuples; persist foundation curricula in the modern job database; thread richer foundation fields through generic exporters.
**Why this one:** The canonical directory mismatch is already reconciled, while versioned manifests provide auditable curriculum/review/media snapshots without widening Phase 30 runtime, persistence, or generic export contracts.

- All phase artifacts, internal documentation references, source-pack names, and deck naming use `i-plus-1`; do not reintroduce `i-plus-one`.
- Use one versioned UTF-8 JSON concept registry, one Hangul source pack, one pronunciation source pack, an independent curation/review manifest, and an independent media manifest.
- Load all manifests through frozen Pydantic v2 contracts with `extra="forbid"`, bounded values/counts, hidden input values in errors, deterministic ordering, and cross-record validation.
- Treat committed manifests as untrusted input. Reject malformed JSON, duplicate or unknown IDs, unsafe HTML/media markup, absolute/traversal/URL paths, unsupported scripts, unbounded values, and source/version/hash drift with privacy-safe reason codes.
- Source packs are immutable snapshots. A content, dependency, spoken-text, translation, provenance, or media-identity change requires a new source/media version and invalidates prior hash-bound review; it is not an in-place silent correction.
- “Complete technical curriculum” means all contracts, H0-H10/P0-P13 coverage rules, candidate inventory structures, review/media states, joins, output schemas, and failure modes exist. The agent may propose learner copy and review it under the global AI policy, but it cannot invent source or legal authority.
- Checked-in production candidate records may carry source-backed provisional content, but unresolved exact values remain explicitly pending. Conditional contracts require complete learner fields, provenance, rights, policy evidence, and media metadata before `ai_review_passed`; they must still represent a valid, actionable `needs_review` state when evidence is absent.
- Use a local operator CLI/service path like the Latin foundation flow. Only the exact owner-authorized media lane may instantiate Azure for the bounded `ko-KR` foundation manifest; validation/export never instantiate Kiwi, Azure, a database runtime, text generation, Tatoeba, or the frequency pipeline.

### Shared Concept Registry, Explicit Bootstrap, and Strict Graph

**Chosen approach:** Both foundation families reference one concept registry; validators independently recompute graph and strict-i+1 evidence before any review or export check.
**Alternatives considered:** Treat H/P stage order as sufficient; trust serialized `unknown_concept_ids`; exempt the first N notes implicitly; allow any review approval to override curriculum invalidity; use adaptive scoring for the foundation decks.
**Why this one:** The approved milestone defines curriculum i+1 as an executable invariant, and review cannot establish a graph fact that the data contradicts.

- The registry uses stable, atomic concept IDs and explicit prerequisite IDs. Validate uniqueness, referenced-ID existence, domain/family compatibility, acyclicity, prerequisite closure, deterministic sequence, and no forward dependency.
- The Hangul pack declares an ordered `bootstrap_concept_ids` list and `strict_start_sequence`; bootstrap is never inferred from file position or the first N records.
- H0 entry targets must equal the declared bootstrap list in order. Do not pre-mark the complete bootstrap as known: each H0 target becomes known only after its own entry passes the same one-unknown accounting.
- For every strict entry, compute `known_before` from successfully validated preceding targets, then recompute `unknown = observed - known_before` and require `unknown == {target_concept_id}`.
- Require the target in observed concepts, serialized unknown evidence to equal recomputed evidence, and every declared prerequisite to be known before the entry.
- Every active non-target orthographic/phonological rule must be an explicit known prerequisite. A stage/category label, broad “all batchim” concept, or hidden rule is not valid evidence.
- Validate exact H0-H10 and P0-P13 stage/category coverage and the prescriptive concept families recorded by `KOREAN-STRUCTURE.md` and `31-RESEARCH.md`. Automated coverage does not claim that candidate atomization is pedagogically approved.
- H7/H8 coda-position concepts and P2 pronunciation concepts share canonical registry identities where appropriate; do not duplicate an orthographic concept merely because another family observes it.
- Preserve canonical spelling, normative bracketed pronunciation, reviewed surface realization, optional IPA, register/context, active rule IDs, and source citations as distinct evidence. No template or exporter recomputes these values.
- An invalid graph, false i+1 record, missing active rule, broad/non-atomic candidate, source drift, or missing stage coverage is structurally invalid and cannot be rescued by an `approved` flag.

### Canonical Jamo Versus Pedagogical Display Glyphs

**Chosen approach:** Keep canonical machine identity in positional modern conjoining Jamo and represent learner-friendly standalone Compatibility Jamo through a separate reviewed mapping contract.
**Alternatives considered:** NFKC-fold display glyphs; relax Phase 30 `canonicalize_korean()`; use one display consonant as an onset/coda identity without position; ban standalone learner display entirely.
**Why this one:** Learners need familiar standalone forms, but visually similar Unicode characters are not interchangeable canonical identities and onset/coda position can change the machine mapping.

- Preserve the verified Phase 30 canonicalizer unchanged: canonical Korean content rejects Compatibility Jamo and halfwidth Hangul and normalizes to NFC.
- A pedagogical mapping records at least `display_glyph`, `canonical_jamo`, `jamo_position`, Unicode identity/name, source version/hash, and review status.
- Never send `display_glyph` through lexical canonicalization, use it in morphology/lexical keys, or infer its conjoining identity with NFKC.
- Halfwidth Hangul remains forbidden in both canonical and pedagogical data. Compatibility characters are permitted only in the explicitly typed display field.
- Canonical blocks, Korean words, names, sentences, and pronunciation strings remain NFC; NFC/NFD equivalents deduplicate at canonical boundaries without erasing submitted/display evidence.
- Implement Unicode algorithmic modern-Hangul composition/decomposition and exhaustively test all `19 × 21 × 28 = 11,172` combinations; curate representative learner notes rather than generating 11,172 cards.
- Traditional jamo names appear only after the orthographic concepts required to decode them are already known.

### Korean Note Identity and Templates

**Chosen approach:** Give each Korean foundation family its own stable identity while reusing only approved layout mechanics.
**Alternatives considered:** Reuse Japanese model/note IDs or template fields; parameterize the Japanese source/template; add Korean curriculum evidence to the shared pronunciation note; create a new pronunciation visual design.
**Why this one:** Korean needs independent Anki update identity and semantics, while `KPRO-01` explicitly requires the existing nine-field visual contract.

- Reserve the following currently unused signed-32-bit constants, with a mandatory global collision scan before they are committed:

  ```text
  KOREAN_HANGUL_MODEL_ID        = 1_762_801_001
  KOREAN_HANGUL_DECK_ID         = 1_762_801_002
  KOREAN_PRONUNCIATION_MODEL_ID = 1_762_801_003
  KOREAN_PRONUNCIATION_DECK_ID  = 1_762_801_004
  ```

- If any proposed ID collides on the live execution baseline, stop and replan the four-ID block; do not silently choose per-run IDs.
- Use exact deck names `Multilang Korean::Foundations::Hangul` and `Multilang Korean::Foundations::Pronunciation i+1`.
- Derive stable 32-hex Anki GUIDs from SHA-256 over immutable family + source-pack version + item key. Do not include mutable translation, mnemonic, template text, media filename, or Python `hash()`.
- The Hangul note fields are exactly, in order:

  ```text
  SortIndex, Category, JamoOrBlock, ReadingOrName, Sound, Mnemonic,
  Picture, Strokes, Gif, Audio, TargetConceptId, PrerequisiteConceptIds,
  ObservedConceptIds, UnknownConceptIds, IPlusOnePolicy
  ```

- Curriculum evidence fields are stored but not rendered as learner copy. Templates consume frozen values and never calculate concepts, pronunciation, or approval.
- Create a Korean-owned Hangul template by copying only the proven layout mechanics of the kana template. Do not import, parameterize, or mutate the Japanese template/source as the implementation path.
- Use Korean labels, class names, and an explicit Korean-capable font stack. Static scans reject Japanese/Kana/Romaji/Hiragana/Katakana labels, Japanese class names, and Japanese font tokens case-insensitively.
- Preserve conditional media sections, safe replay-button behavior, dark-canvas structure, and bounded responsive media rules, but make no rendered visual-quality claim from those static facts.
- The pronunciation learner fields remain exactly, in order:

  ```text
  Spellings, Sound, letter_audio, Example Word, word_audio,
  Word Translation, Example Sentence, sentence_audio, Sentence Translation
  ```

- Keep graph, normative/surface/IPA review, provenance, and gate data in source/review/media manifests; do not add fields to the nine-field learner schema.

### Language-Neutral Phoneme Mechanics With Compatibility Preservation

**Chosen approach:** Extract only language-neutral model/note/field/template/GUID mechanics from the existing Russian/Polish/Greek module, then keep existing names as wrappers or aliases.
**Alternatives considered:** Duplicate the full Russian module for Korean; rename/remove public Russian symbols; modify existing language inventories/voices/commands; create a Korean-specific pronunciation layout.
**Why this one:** It gives Korean the required shared contract without changing already-imported note identity or public code behavior.

- The neutral layer owns the exact nine-field tuple, model construction, ordered field mapping, note/GUID injection, and shared front/back/CSS mechanics only.
- Korean may append only the isolated Korean font override to the shared pronunciation CSS.
- Existing Russian, Polish, and Greek public imports, class/function names, model/deck IDs, note-type names, deck names, fields, GUID inputs, inventories, voices, commands, templates, CSS, APKG behavior, and audio behavior remain available and byte-for-byte equivalent where currently asserted.
- Do not “clean up” the legacy raw-letter synthesis or broad exception behavior as part of this extraction. It remains a regression-preserved existing path; Korean must not call or copy it.
- Any extraction that requires changing an existing field, rendered template/CSS byte sequence, stable ID, GUID input, or CLI surface is a stop-and-replan condition.

### AI Review and Media Gates

**Chosen approach:** Keep source validity, AI linguistic review, licensing, media-byte integrity, and acoustic review independent and hash-bound; initialize real production state as `needs_review`.
**Alternatives considered:** A single coarse approval flag; existence-only media checks; provider success as approval; untracked single-pass model approval; human-only review; filename-bound review; generated placeholders; silent fallback.
**Why this one:** Deterministic validation plus independent AI review can assess linguistic quality without waiting for human availability, while legal rights and exact-byte facts remain separate authorities.

- Linguistic gate states are `needs_review`, `ai_review_passed`, `ai_review_failed`, `blocked_uncertainty`, `blocked_disagreement`, and `stale`. Rights/media authority retains its own pending/approved/denied states.
- Separate applicable gates for source/content, curriculum/atomicity, Korean orthography, Korean phonetics/pronunciation, Portuguese, media license/redistribution, media completeness/integrity, and audio playback.
- Every non-passing gate has an actionable content-free reason. Every `ai_review_passed` gate records actor type, model/provider/prompt/schema/policy identity, timestamp, exact source/media version, validator results, independent-pass identities, and relevant hashes.
- Hangul and pronunciation records receive the standard or critical multi-pass scopes defined by the global policy, including Portuguese learner copy wherever present.
- Every non-original stroke, picture, GIF, mnemonic asset, or recording requires source, attribution, license, and explicit reuse/redistribution disposition before its bytes can be treated as production media.
- Jamo, contrast, and phonological-rule audio readiness is bound to exact bytes and requires deterministic decoding/acoustic checks plus critical multi-pass AI acoustic/linguistic review. Provider success alone cannot satisfy the gate.
- For audio/media, recompute SHA-256 from actual bytes and require `actual hash == artifact_hash == reviewed_artifact_hash`. Bind display/spoken/NFC text, text hash, provider/version where applicable, exact voice/recording identity, locale only where applicable, SSML/prosody hash where applicable, output format, duration, repository-relative path, source version, and reviewer roles.
- A change to bytes, spoken text, expected form, provider, voice, SSML, prosody, format, source version, policy, prompt, schema, or relevant content makes prior evidence `stale` and requires a new review.
- Raw standalone display glyphs are never sent to TTS as if they were phonemes. Letter-name and consonantal-sound audio use explicit approved Korean names or syllable/coda context.
- Do not commit silence, empty files, generated tones, stock/dummy images, or placeholder production media. Missing media remains an explicit pending slot and blocks production export.
- Do not use an untracked single-pass LLM result, G2P result, provider success, test fixture, or fake to set `ai_review_passed`; the complete policy evidence is mandatory.

### Test-Fixture Media Boundary

- Tests may generate deterministic, non-empty media bytes only under test-owned temporary directories to exercise header, path, hash, package, reference, and corruption behavior offline.
- Happy-path test records may be approved-shaped transient objects solely to exercise the exporter contract. They must use unmistakable test identifiers, remain outside checked-in production manifests/review artifacts, and never be reported as real review evidence.
- The production CLI defaults to fixed production manifests and has no `--allow-unapproved`, fake-review, no-media, synthesize-missing, or arbitrary-module/template escape hatch.
- Tests must prove that production manifests remain `needs_review`, that fixture execution does not rewrite them, and that generated temporary bytes cannot satisfy or leak into production readiness.
- No test constructs a live provider, performs a network call, consumes provider credentials, or sends a raw glyph to TTS.

### Deterministic All-Format Export

**Chosen approach:** Build a dedicated Korean foundation exporter for both families and all three formats; validate the complete join before creating output.
**Alternatives considered:** Extend the generic modern exporters; APKG-only support; tables with unresolved sound tags; export-time media generation; partial output followed by validation; one mixed-schema table.
**Why this one:** The two foundation families have distinct schemas and richer frozen evidence, while KPRO-01 requires media to survive APKG, CSV, and TSV without changing existing exporter contracts.

- Use separate frozen `HangulExportRow` and `KoreanPronunciationExportRow` mappings. Never mix the two note schemas in one tabular artifact.
- The deterministic join order is concept registry → family source pack → curation/review manifest → media manifest → export rows.
- Before any output path or directory is created, validate source/pack versions, item-key order, content hashes, graph evidence, all applicable review gates, media paths/basenames, exact bytes, reviewed hashes, field references, model/deck ID uniqueness, and template schemas.
- Any pending, rejected, missing, stale, ambiguous, unsafe, false-i+1, hash-mismatched, or unapproved input blocks APKG, CSV, and TSV consistently and leaves no partial artifact.
- APKG embeds exactly the approved bytes through `genanki`; archive/SQLite tests inspect model, deck, note, field, GUID, tag, and media-map identity.
- CSV/TSV use UTF-8 and `csv.writer`, preserve exact ordered fields and Anki headers, use basename-only media tags, and emit a deterministic sibling media directory plus checksum/reference manifest. A sound tag without resolvable exact bytes is a failure.
- Output order, names, headers, GUIDs, checksums, media-copy order, and diagnostics are deterministic. Diagnostics expose family/item key/gate/reason code only, not Korean source text, absolute paths, reviewer notes, provider payloads, or credentials.
- Complete validation precedes writing; use a secure temporary output and atomic replacement where appropriate, then inspect the temporary artifact before replacing the requested target.
- CLI selection is enum-constrained by family and format. It does not accept arbitrary Python modules, templates, source URLs, or remote media. Exact command names and aggregate scanner-safe wording are implementation details.
- Export performs no synthesis, translation, generation, morphology analysis, remote fetch, or fallback. It packages frozen, independently approved input only.

### Approval and Checkpoint Plan

1. **Technical implementation checkpoint — automatic/offline.** Complete contracts, graph/Unicode validation, pending production manifests, templates, shared mechanics, exporters, CLI, tests, scanners, and regression evidence without waiting for media or reviewers.
2. **AI-assisted draft checkpoint — automatic then user selection.** Produce grounded `draft_only` field patches, validate exact coverage and immutable structural bindings, and ask the user to select exact draft hashes for candidate promotion. No production gate changes here.
3. **Candidate promotion checkpoint — deterministic/offline.** Promote only the selected hashes into new immutable `v2` candidate packs, regenerate all pending manifests/request bindings, and prove learner-ready export remains blocked.
4. **AI linguistic checkpoint — automatic and parallel.** Review 100% of Hangul, pronunciation, P0-P13, Portuguese, and curriculum claims under the global policy; critical fresh-context passes run concurrently and disagreement fails closed.
5. **Media source/license checkpoint — external authority lane.** Record source, attribution, license, and reuse/redistribution disposition before adding each real production byte. Unknown rights remain pending; the AI never invents them.
6. **Exact-byte acoustic checkpoint — automatic and parallel.** Bind every recording to exact text/context/bytes, run deterministic media/acoustic checks, and apply AI acoustic review where supported without claiming human listening.
7. **Production export checkpoint — deterministic join.** Only after structural, AI, rights, media, and integrity gates pass may exact manifests emit learner-ready APKG/CSV/TSV artifacts.
8. **Observed visual/import checkpoint — deferred to Phase 34.** Instrumented Anki Desktop/mobile import, rendering, font, responsive-layout, and playback evidence must bind the exact application/environment/artifact tuple.

### Replanned Execution Map

- **31-11:** Build draft schemas and fixed tooling test-first; no content or canonical write.
- **31-12 through 31-15:** Curate H0-H10 in three bounded projections, then assemble and audit the complete Hangul family draft.
- **31-16 through 31-19:** Curate P0-P13 in three bounded projections, then assemble both family drafts and the exact 139-record manifest/report.
- **31-20:** Run exact read-only draft selection, persist the typed handoff, and implement no-write bundle-promotion primitives test-first.
- **31-21:** Publish four immutable v2 candidates as one hash-named bundle through one atomic visibility pointer.
- **31-22:** Implement, regenerate, and verify the fully pending v2 review/media requests.
- **31-23:** Migrate curriculum/review/media defaults to the exact v2 bundle while retaining explicit immutable v1 history.
- **31-24:** Migrate evidence/snapshot/export provenance to v2 and prove canonical production remains blocked/write-free.
- **31-25:** Migrate CLI/integration expectations, run the complete pre-evidence regression matrix, and build fixed safe Python 3.12 runtime-isolation tooling.
- **31-26 through 31-28:** Historical blocked human-evidence path, superseded by the 2026-08-27 amendment.
- **31-29 (launch preflight):** Prepare one isolated Python 3.12 runtime and record one clean integration baseline, protected-state fingerprint, and disjoint lane allowlists.
- **31-30 (parallel lane A):** Implement global-policy AI review contracts and review exact v2 linguistic/curriculum content.
- **31-31 (parallel lane B):** Resolve project/provider media rights, create exact media, and run deterministic plus AI acoustic review.
- **31-32 (join):** Rehash both lanes, write the canonical receipt/snapshot, validate staged outputs, activate locally, export six outputs, and run closure.

All checkpoint values flow through fixed typed JSON handoffs or canonical files. Plan commands never use brace placeholders or parse hashes from prose summaries.

If AI review, licensed media, rights authority, or exact bytes are unavailable, only the consuming lane stops. Other disjoint plans continue. No plan invents rights, bytes, or successful observations.

### Anti-Regression Boundaries

- Preserve the verified Phase 30 `ko` identity, `ko-KR` provider-locale boundary, NFC rules, Compatibility/halfwidth rejection, source-backed identity, top-two Kiwi consensus, persistence behavior, fail-closed matcher, and private-highlight posture.
- Do not change `canonicalize_korean()` to admit pedagogical display glyphs. The separate positional mapping is the only allowed boundary.
- Do not add or modify `assets/frequency/ko/`, the approved-frequency capability list, Korean Tatoeba routing, or a Korean production voice registry entry.
- Keep `src/multilang/runtime.py`, Alembic/database models/repositories, and generic modern export row/package/tabular schemas untouched unless execution proves a requirement cannot be met. Such a discovery is a stop-and-replan event, not permission for opportunistic widening.
- Keep Japanese kana source, generation, model, IDs, fields, template, fonts, media behavior, imports, and tests unchanged; it is a structural regression oracle only.
- Preserve every existing Russian/Polish/Greek phoneme public API and artifact identity/behavior while extracting shared mechanics.
- Preserve modern normal/manual/highlight, Japanese frequency, Mandarin, Latin, card-schema, blank-`Image`, audio, persistence, and export behavior.
- Korean foundation AI review remains tool-less over fixed projections. Only the explicitly authorized media lane may call the selected TTS provider; no foundation operation may call Tatoeba, arbitrary downloaders, or the frequency runtime.
- No export may catch a broad media/provider exception and continue with blank required fields. All required-media failures are typed and blocking.
- No approval bypass, `allow_unapproved`, generated-production-media switch, environment-controlled fake approval, or test backdoor enters production code.
- Keep model/deck IDs globally unique and GUID inputs immutable. Never “fix” a collision or changed output by regenerating IDs nondeterministically.
- Preserve exact learner field order and template-reference allowlists; evidence remains hidden/source-side where specified.
- Treat the completed-but-uncommitted Phase 30 worktree as the required baseline. Do not overwrite, revert, clean, or commit it as part of Phase 31 planning/execution without explicit authorization.
- Required evidence includes focused Phase 31 tests, kana and phoneme regressions, Latin media/export regressions, the Phase 30 Korean boundary suite, global ID scans, Python 3.12 compatibility, full offline tests, and no-provider/no-forbidden-surface scans.
- Closure may claim deterministic contracts, exact AI-policy review, licensed media where rights evidence exists, natural-language review under the named policy, and structurally valid exports. It may not claim human review or unobserved device/render/playback behavior.

### UI and Visual Claim Limits

Phase 31 creates Anki template source but no application page, review dashboard, interaction flow, or gate-management UI. No product UI work is authorized.

- Static tests may claim exact field/reference order, Korean-owned labels/classes/fonts, forbidden-Japanese-token absence, conditional media structure, and deterministic packaged HTML/CSS.
- Archive/table tests may claim model/deck/note/media structure and exact reference integrity.
- Neither static tests, synthetic fixture exports, archive inspection, screenshots of non-approved fixtures, nor agent inspection may claim acceptable appearance, readability, font rendering, responsive behavior, animation, actual playback, or successful import in Anki Desktop/mobile.
- Do not create a screenshot or visual-review artifact merely to imply acceptance. Phase 34 owns observed Desktop/mobile visual/import evidence after real content and media are approved.
- Any Phase 31 wording such as “visually verified,” “mobile-ready,” “rendering approved,” or “playback approved” is prohibited unless the corresponding later human evidence genuinely exists; otherwise narrow the claim to static template structure.

### Agent's Discretion

- Exact internal class, enum, reason-code, helper, and module decomposition, provided the frozen contracts and locked invariants remain explicit and testable.
- Exact note-type display names, tag vocabulary, and test-safe fixture identifiers, provided deck names, numeric IDs, schemas, and stable identity remain locked and globally unique.
- Exact JSON field decomposition and hash-canonicalization helper shape, provided manifests are versioned, frozen, deterministic, bounded, and reject extras/drift.
- Exact CLI command names and aggregate success/error wording, provided family/format options are enum-constrained, production defaults are fixed, diagnostics are privacy-safe, and there is no approval/provider/path bypass.
- Exact Korean CSS selectors, spacing, and font fallback order within the Korean-owned template, provided Korean identity is explicit, Japanese leakage is absent, shared mechanics remain recognizable, and no visual acceptance is claimed.
- Exact deterministic temporary media bytes and fixture factories used by tests, provided they live only under temporary test roots, are never committed as production evidence, and no live provider/raw-glyph path is used.
- Exact test-module split, parametrization, mutation cases, and scanner implementation, provided every required contract, all-format path, human-gate boundary, and anti-regression target is covered.
- Whether a read-only readiness/check command is separate from export or shared internally, provided it uses the same validators and never writes learner artifacts for blocked production inputs.
- Agent discretion extends to bounded learner-copy proposals and AI review under the global policy. It still does not extend to selecting rights dispositions, impersonating a human reviewer, weakening strict i+1, broadening canonical Hangul acceptance, changing locked graph/ID/deck contracts, making an unscoped live/paid call, or claiming visual acceptance. Foundation voice/route/items/budget remain fixed by the exact owner-authorized media handoff.

</decisions>

<assumptions>
## Validated Assumptions

### 1. Technical Approach

- **[confident][confirmed]** The approved `KOREAN-STRUCTURE.md` remains the product/curriculum baseline, with the contract reconciliations in `31-RESEARCH.md` and `31-PATTERNS.md`: stored Hangul evidence includes observed/unknown/policy fields, while pronunciation learner fields remain exactly nine.
- **[confident][confirmed]** The isolated frozen-manifest path is sufficient; Phase 31 does not need database-backed jobs or generic modern exporters. Its only live provider path is bounded Azure `ko-KR` foundation synthesis after exact project-owner authorization.
- **[confident][confirmed]** One concept registry and validator can serve both families while preserving family-specific source and learner schemas.
- **[corrected by user]** Human linguistic review is not required. The selected posture is deterministic validation plus explicit fail-closed multi-pass AI review, with legal rights and provider authority remaining external.
- **[confident][validated by Phase 30]** Existing `ko`, NFC, canonical-jamo rejection, morphology, privacy, and fail-closed contracts are working prerequisites and must be extended additively rather than reimplemented.

### 2. Implementation Order

- **[confident][accepted]** Begin with failing domain, graph, review, media, shared-phoneme, export, CLI, and integration contracts; then implement contracts/manifests; then templates/shared mechanics; then exporters/CLI; finally run focused and full regressions.
- **[confident][confirmed]** Production curation/media manifests are pending from their first checked-in version. Do not first mark them approved for integration convenience and attempt to “fix” status later.
- **[confident][accepted]** Validate curriculum/source before review readiness, review before media join, and the entire joined bundle before any output write.
- **[assuming][accepted with gate]** Candidate curriculum data can be versioned before policy review if all unresolved linguistic/atomicity claims are visibly `needs_review`, cannot export, and any review correction creates a new hash/version.

### 3. Scope Boundaries

- **[confirmed by user 2026-08-27]** Phase 31 owns bounded Azure `ko-KR` synthesis for its exact foundation media manifest after rights/budget authorization. Korean frequency voice policy, grammar/personal-source pedagogy, database runtime integration, and gate-management UI remain outside scope.
- **[confident][confirmed]** APKG, CSV, and TSV are all in technical scope for both foundation families; final observed all-family Anki acceptance remains Phase 34.
- **[confident][confirmed]** No visual claim is part of Phase 31. Template work yields static structure only.
- **[confident][confirmed]** Real rights-bound media and policy-valid AI review are release checkpoints, not optional agent-discretion work and not satisfied by fixtures.

### 4. Risk Areas

- **[confident][validated by research]** Highest risks are false i+1 evidence, Compatibility Jamo leaking into canonical identity, raw-glyph/silent audio, review/hash drift, unresolved CSV/TSV media, Japanese template leakage, shared-phoneme regression, unsafe paths/HTML, partial output, and human-evidence overclaiming.
- **[confident][confirmed policy]** A blocked false negative is preferable to a learner-facing false approval. Any ambiguity, missing evidence, role gap, source drift, or byte mismatch remains `needs_review` or blocks export.
- **[confident][accepted]** Automated tests prove deterministic structure/refusal; policy-bound AI review evaluates concept atomicity, orthography, phonetics, Portuguese naturalness, and acoustic quality. Neither grants licensing rights or unobserved device/visual acceptance.
- **[confirmed policy]** Exact P11 reductions and P12/P13 auditory/ordering records require critical three-pass AI linguistic/acoustic consensus plus deterministic validation; uncertainty or disagreement blocks.

### 5. Dependencies

- **[confident][validated by research]** Existing Python/Pydantic/stdlib graph/Unicode/genanki/csv/pytest dependencies are sufficient; no package upgrade or new runtime dependency is required for the core implementation.
- **[confident][validated]** The Phase 30 verification passed 30/30 truths and the full suite, establishing the required baseline; its completed uncommitted work must remain intact.
- **[confident][blocking external dependency]** Licensing/redistribution disposition, Azure credentials, and exact budget authority are not currently supplied. AI review cannot grant them.
- **[confident][blocking external dependency]** No real rights-bound Phase 31 media bytes or complete hash-bound AI review manifests currently exist. Generated test fixtures are not a fallback.
- **[assuming][checkpoint-bound]** PCM WAV is the preferred future reviewed-audio format because stdlib can inspect it offline. If approved real assets use MP3 or another format, stop and explicitly plan a validated inspection dependency rather than guessing duration/format support or transcoding silently.
- **[confident][claim limit]** Anki Desktop and mobile runtime evidence is unavailable and unnecessary for the bounded technical claim; Phase 34 must supply observed import/render/playback evidence before any final visual claim.

</assumptions>

<deferred>
## Deferred Ideas

- **Phase 32:** Approve and freeze the Korean frequency source/license decision and 3000-entry inventory; build three real 1000-card subdecks; qualify the frequency-deck Azure `ko-KR` voice/profile and production audio policy separately from the Phase 31 foundation manifest; generate/review Korean examples and Portuguese text.
- **Phase 33:** Full strict-i+1 Particles & Endings curriculum and learner-facing Custom/Highlights bridge/defer pedagogy.
- **Phase 34:** Gate-management/review UX, final all-family APKG/CSV/TSV evidence, real Anki Desktop/mobile import and rendering, responsive/font inspection, and observed playback/visual acceptance.
- **Separate explicit replan if needed:** Support for an approved non-PCM audio format requiring a new inspection/transcoding dependency, or touching any no-touch runtime/generic-export/database surface.
- **Out of v3.0:** Hanja curriculum, regional dialect decks, persistent lexical romanization, automatic phonetic/audio approval, unlicensed corpus/media mining or redistribution, interactive tutoring, and learner-mastery synchronization with Anki scheduling.

The missing rights-bound media and policy-valid Phase 31 AI evidence are **not** deferred product ideas. They remain unmet until lanes 31-30/31-31 execute, blocking learner-ready release. The selected approach is to expose blockers honestly while completing and verifying the technical system that enforces them.

</deferred>

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Approach explored: 2026-08-04*
