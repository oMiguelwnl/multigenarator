---
mode: quick
task: 031-persistir-plano-mestre-v4
plan: 031
type: execute
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
autonomous: true
task_count: 2
requirements: []
files_modified:
  - docs/multilingual-lexical-adaptive-plan-v4.md
non_goals:
  - Do not promote v4 into the active milestone or alter current phase numbering, status, requirements, or execution state.
  - Do not implement any v4 model, migration, provider, queue, Anki integration, deck, CLI, API, UI, test, data asset, or configuration.
  - Do not choose an unapproved lexical source, redistribution license, provider, budget threshold, or quality threshold merely to make the document look resolved.
hard_boundaries:
  - The substantive execution write set is exactly docs/multilingual-lexical-adaptive-plan-v4.md.
  - Treat .planning/SPEC.md, .planning/ROADMAP.md, .planning/STATE.md, v3.0 Korean phase artifacts, and existing source files as read-only context; never edit, reformat, stage, restore, or otherwise mutate them.
  - Preserve the pre-existing dirty worktree exactly; record its baseline before writing and do not clean up or absorb unrelated changes.
  - Keep Classical Latin isolated from the modern-language architecture and migration path rather than silently routing it through modern assumptions.
escalation_triggers:
  - Stop rather than inventing a decision if repository evidence materially conflicts with a locked decision below.
  - Stop if completing the durable document would require changing an active planning artifact or any source, test, configuration, data, export, or generated file.
approval_gates:
  - Promotion of this v4 master plan into SPEC.md or ROADMAP.md requires a separate explicit user-approved milestone action after v3.0 is complete.
  - External source, license, provider, privacy, budget, and quality approvals remain named gates in the master plan and are not implied by documenting them.
anti_regression_targets:
  - Active v3.0 Korean phases 30-34, their Portuguese content policy, and their current state remain unchanged by this documentation task.
  - Existing modern-language and isolated Latin implementation behavior remains unchanged.
  - Existing unrelated dirty-tree work remains byte-for-byte untouched.
known_unknowns:
  - Exact source/provider selections and numeric cost/quality thresholds require evidence at their assigned v4 gates; the document must preserve those decisions as explicit prerequisites rather than fabricate approvals.
  - The active codebase may evolve before v4 promotion; G0 must require a fresh inventory and baseline reconciliation without weakening the locked v4 outcomes.
browser_proof_required: false
browser_proof_rationale: "Documentation-only work with no rendered UI or browser behavior claim."
no_ui_proof_rationale: "This quick task creates one durable Markdown master plan and does not modify or claim any UI behavior."
must_haves:
  truths:
    - "O documento mestre está integralmente em português, preservando em inglês apenas códigos, identificadores técnicos e valores de política que precisam manter sua grafia original."
    - "A reader can follow every prerequisite and phase from G0 through Phase 51, including dependencies, deliverables, and exit gates, without treating v4 as active work."
    - "The plan names all 22 modern target languages and isolated Latin and makes the explanation-language policy and Korean transition unambiguous."
    - "The plan distinguishes lexical identities from cards and forms, fixes the modern core at 3x1000 identities, and keeps optional expansion and Important Forms outside that quota."
    - "The plan connects personal sources, read-only APKG history, the adaptive queue, real subdecks, and safe in-place migration into one traceable architecture."
    - "Privacy, license, cost, and quality controls are concrete entry/exit gates rather than general aspirations."
    - "Active SPEC.md, ROADMAP.md, STATE.md, v3.0 Korean state, and source code remain unchanged."
  artifacts:
    - path: docs/multilingual-lexical-adaptive-plan-v4.md
      provides: "Standalone v4 multilingual lexical/adaptive master plan covering G0 and Phases 35-51"
      contains: "LanguageProfile, language policy, lexical identity, forms, APKG history, adaptive queue, export, migration, and gate contracts"
  key_links:
    - from: docs/multilingual-lexical-adaptive-plan-v4.md
      to: .planning/ROADMAP.md
      via: "G0 promotion boundary after completed and verified v3.0; read-only reference until a separate approved milestone action"
    - from: LanguageProfile
      to: "lexical identity, normalization, morphology, explanations, audio, and personal-source capabilities"
      via: "one fail-closed per-language capability contract"
    - from: "lemma + POS + sense identity"
      to: "SurfaceForms, Important Forms, MWE, routing, and card roles"
      via: "stable versioned references that do not inflate the 3000-identity core"
    - from: "read-only APKG history integration"
      to: "adaptive queue"
      via: "confidence-scored identity mapping without mutating Anki data"
    - from: "in-place Multilang migration"
      to: "existing data and study history"
      via: "preview, verified backup, explicit confirmation, idempotent execution, rollback, and audit evidence"
---

# Quick Task 031 Plan: Persist the v4 Multilingual Lexical/Adaptive Master Plan

<objective>
Persist the complete user-agreed v4 architecture and delivery sequence as a standalone durable document without changing the active v3.0 planning or implementation state.

Purpose: prevent the long-range multilingual lexical/adaptive decisions from being lost while preserving v3.0 Korean as the only active milestone.

Output: `docs/multilingual-lexical-adaptive-plan-v4.md` containing the normative scope, architecture, G0 prerequisite gate, Phases 35-51, dependency graph, migration contract, and cross-cutting release gates.
</objective>

<context>
Read-only orientation sources:
- `AGENTS.md`
- `.planning/PROJECT.md`
- `.planning/SPEC.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `docs/lexical-data.md`
- relevant v3.0 Korean phase artifacts when they exist

This is preservation work, not a milestone promotion. Current v3.0 phases 30-34 and their Portuguese Korean-content policy stay active and untouched. The v4 document must explicitly defer activation until G0 confirms v3.0 completion, verification, archive/baseline evidence, and a separate promotion decision.

Research is not part of this quick task: external source, provider, licensing, privacy, cost, and quality questions must be represented as evidence-bearing v4 gates. Do not convert a question into an approval without evidence.
</context>

## Locked Decisions

- **D-01 — Durable artifact and isolation:** The only substantive artifact is `docs/multilingual-lexical-adaptive-plan-v4.md`; active planning state and source code are immutable in this task.
- **D-02 — Complete sequence:** The document covers prerequisite **G0** and every phase **35 through 51**, with no missing or collapsed phase.
- **D-03 — Language scope:** Modern scope is exactly Portuguese (`pt`), Spanish (`es`), English (`en`), French (`fr`), German (`de`), Italian (`it`), Polish (`pl`), Turkish (`tr`), Romanian (`ro`), Russian (`ru`), Dutch (`nl`), Korean (`ko`), Danish (`da`), Norwegian Bokmål (`nb`), Swedish (`sv`), Finnish (`fi`), Hungarian (`hu`), Czech (`cs`), Croatian (`hr`), Modern Greek (`el`), Japanese (`ja`), and Mandarin Chinese (`zh`). Latin (`la`) remains an isolated Classical Latin path.
- **D-04 — Explanation language:** All modern target languages use English explanations except target English, which uses Portuguese. Korean deliberately transitions from Portuguese v3 content to English in v4. Latin remains Portuguese.
- **D-05 — Inventory sizes:** Each modern language has exactly 3000 ranked lexical identities in a frozen Core 3x1000. Optional expansion adds a configurable 0-3000 additional identities and never pads, renumbers, or replaces the core.
- **D-06 — Canonical model:** `LanguageProfile` is the language capability contract; lexical identity is versioned `language + normalized lemma + POS + sense`, not a spelling, card, or row.
- **D-07 — Forms and audio:** `SurfaceForms` and `Important Forms` are linked outside the 3000 quota. Form-specific `Definitions` carry applicable tense, mood, person, number, case, gender, aspect, and register metadata, and audio is synthesized/resolved for the exact displayed form.
- **D-08 — Linguistic/card roles:** MWE, sense resolution, source routing, and card roles are first-class and explicitly separated; ambiguity fails closed.
- **D-09 — Personal capabilities:** Custom lists and highlights are per-`LanguageProfile` capability gates. They preserve submitted form/private provenance and do not mutate shared core ranks.
- **D-10 — Anki history:** APKG history ingestion is read-only, maps study history to stable identities with confidence/quarantine behavior, and never writes to Anki, AnkiConnect, the imported package, or a user collection.
- **D-11 — Adaptation:** The adaptive queue is explainable, resettable, privacy-aware, and consumes identity/content/history signals without changing canonical frequency order or imported Anki history.
- **D-12 — Export topology:** APKG exports use real nested subdecks, not tags that merely imitate levels or roles.
- **D-13 — Migration safety:** Existing Multilang data migrates in place only through preflight, preview, verified backup, explicit confirmation, idempotent/resumable execution, rollback, and audit evidence; stable identity and study history are preserved wherever mapping is valid.
- **D-14 — Cross-cutting gates:** Privacy, license/redistribution, cost, and quality gates block progression and release when unresolved.
- **D-15 — No activation by documentation:** Writing this document does not edit active roadmap/spec/state, start Phase 35, or authorize implementation, provider calls, source redistribution, or migration.

<tasks>

<task id="031-01" type="auto">
  <name>Task 1: Author the canonical v4 contracts and G0-to-51 delivery sequence</name>
  <files>docs/multilingual-lexical-adaptive-plan-v4.md</files>
  <action>
Create `docs/multilingual-lexical-adaptive-plan-v4.md` in Portuguese as a standalone normative engineering/product master plan implementing D-01 through D-15 exactly. Preserve English only for code identifiers, canonical language codes, API/library names, and policy values whose literal spelling matters. Open with a prominent status boundary: this is a preserved v4 proposal, v3.0 phases 30-34 remain active, and no v4 phase starts or enters `.planning/SPEC.md`/`.planning/ROADMAP.md` until G0 and a separate promotion action pass. Use decisive language for locked outcomes and identify unresolved external choices only through named evidence and approval gates.

Give the document these substantive sections:

1. **Status, outcome, scope, and non-goals.** State the user outcome, the active-v3 boundary, the exact write/promotion boundary, and that v4 is an in-place evolution of Multilang rather than a parallel replacement product. Include the invariant that current implementations remain unchanged until approved phase execution.
2. **Matriz de idiomas e política de explicações.** Use uma tabela com as colunas `Família | Código | Idioma | Idioma das explicações | Transição no v4 | Estado da capacidade`. Include exactly 22 rows beginning `| Moderno |` for the D-03 modern languages and exactly one row beginning `| Latim isolado |`. Include these literal policy labels so the decisions remain searchable: `Política dos idiomas modernos: explicações em inglês`, `Exceção do idioma-alvo inglês: explicações em português`, `Migração coreana no v4: português -> inglês`, and `Isolamento do Latim: explicações em português`. State that the policy controls definitions, grammar/form explanations, example translations, and review criteria, not the target-language example itself.
   Add a second per-language requirements table covering every code individually: variant/locale policy, normalization/script, tokenization/segmentation, lemma/POS/sense behavior, morphology/form features, MWE/function-word routing, target matching, pronunciation/audio considerations, and mandatory golden cases. It must explicitly preserve German capitalization; Croatian-specific identity rather than final `sh`; Bokmål `nb` identity; Russian `е/ё`, stress and aspect; Romanian comma diacritics; Japanese UniDic lemma/POS/reading; Mandarin segmentation, Simplified/Traditional and polyphony; Korean NFC/Kiwi/morpheme matching; and isolated Classical Latin morphology.
3. **Normative domain model and invariants.** Define `LanguageProfile` fields and responsibilities: canonical code/provider locales, scripts and normalization (including NFC where required), tokenization/segmentation, morphology adapter and version, lemma/POS/sense rules, MWE support, target matching, explanation language, lexical/source registry, audio locale/voice policy, quality rules, privacy class, and explicit capability flags for Core, expansion, custom lists, highlights, APKG-history mapping, and adaptive behavior. Define stable/versioned `language + normalized lemma + POS + sense` identity, homograph/sense separation, first-class MWEs, aliases/provenance, and fail-closed ambiguity. Specify `Core 3x1000`, `Optional expansion 0-3000`, `SurfaceForms`, `Important Forms`, form-specific `Definitions`, `Exact-form audio`, routing roles, and card roles as distinct entities/relationships. Make it explicit that forms, cards, examples, audio assets, and duplicate spellings never consume additional core identity slots.
   Include the normative IDs `CARD-01`, `FORM-01`, `FORM-02`, `FORM-03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01`, and `GUID-01`. Lock one recognition card per lexical identity by default; optional reverse/listening/cloze cards disabled by default; Important Forms selected only for irregularity, frequency, unpredictability, ambiguity, unexpected pronunciation, prerequisite value, or difficulty inferred from the lemma; form cards outside the 3000 quota; concise meaning-first Definitions with contextual grammar; exact-form audio; prerequisite sequencing and sibling burying; GUID based on lexical identity + card role + form analysis; and a per-language workload/count report for every extra form deck.
4. **End-to-end capability flow.** Trace approved source -> versioned ingestion -> profile normalization/morphology -> lemma/POS/sense/MWE identity -> rank/core or expansion -> form/definition/example/translation enrichment -> exact-form and sentence audio -> source/sense/card routing -> real subdeck export -> read-only APKG-history mapping -> adaptive queue -> safe in-place migration. Include stable IDs, provenance, versioning, deterministic reruns, quarantine paths, and recovery behavior at each boundary.
5. **G0 e especificações das fases.** Give G0 and each Phase 35-51 its own level-three heading in the exact forms `### G0: ...` and `### Fase NN: ...`. Every one of the 18 entries must contain the exact markers `**Resultado:**`, `**Depende de:**`, `**Entregáveis:**`, and `**Critérios de saída:**`, with measurable artifacts/behavior and privacy/license/cost/quality implications where applicable. Preserve this exact allocation:
   - **G0 — Promotion prerequisites and frozen baseline:** require completed/verified/archived v3.0; a fresh inventory of schemas, persisted data, stable IDs, exports/APKG contracts, assets, tests, and dirty-worktree risks; recoverable baseline snapshots; restore rehearsal; approved v4 scope; language matrix; source/license feasibility; privacy processing rules; provider-cost budgets/caps; quality thresholds; and explicit promotion evidence. No Phase 35 work starts before G0 passes.
    - **Phase 35 — Contracts:** lock glossary, exact 3000/3x1000 counting, expansion, variants, explanation languages, Korean transition, card roles, form-card quota policy, module/tag semantics, GUID inputs, APKG feasibility, and all CARD/FORM/SENSE/MWE/ROUTE/DEF/AUDIO/LOAD/DEPEND/GUID contracts before assets or schemas.
    - **Phase 36 — Persistence:** inventory and restore-test immutable backups before mutation; add `LanguageProfile`, lexical identity/sense, SurfaceForm, MorphologicalAnalysis, CardTarget, collection/version/entry, deck edition and GUID alias contracts; extend candidate/snapshot metadata and fingerprints; stage all structures inactive until cutover; prove ORM/Alembic parity.
    - **Phase 37 — Sources and coverage:** create source/license/derivative/redistribution registry, balanced and held-out corpora, candidate pools larger than 3000, frequency/dispersion/contextual-diversity scoring, separate 1k/2k/3k/expansion coverage reports, and hard license gates; keep wordfreq bootstrap-only.
    - **Phase 38 — Morphology and curation:** select/pin analyzers, implement profile normalization, lemma/POS/sense/MWE/form analysis and routing, freeze reviewed reserves, remove live fallback, create at least 120 goldens per language and 200 for CJK/agglutinative languages, require 100% precision among accepted analyses, >=98% resolution of unambiguous cases, 100% fail-closed ambiguity and positive/negative target matching, plus high-risk and stratified human review.
    - **Phase 39 — Representative pilot:** process 100 offline candidates for `pt`, `en`, `de`, `pl`, `tr`, `ja`, `zh`, and `ko`; validate identities, forms, routing, `be/is/was/were`, Definitions, exact-form audio contracts, runtime/cost estimates and promotion/invalidation; paid-provider budget defaults to zero and rollout blocks on failed thresholds.
    - **Phase 40 — Romance rollout:** execute per-language source/license, locale, analyzer/goldens, candidate, identity/sense/form/MWE, exact Core, reserve, Important Forms, expansion, coverage, 90-card vertical sample, voice/audio and human-review plans for `pt`, `es`, `fr`, `it`, and `ro`.
    - **Phase 41 — Germanic rollout:** execute the same complete language plan for `en`, `de`, `nl`, `da`, `nb`, and `sv`, including capitalization, compounds, separable verbs, definiteness, pitch/stød and English-target Portuguese explanation rules.
    - **Phase 42 — Slavic and Modern Greek rollout:** execute the same complete language plan for `pl`, `ru`, `cs`, `hr`, and `el`, including case/aspect/animacy, reflexives, stress/script, Croatian-specific identity and Greek normalization.
    - **Phase 43 — Agglutinative rollout:** execute the same complete language plan for `tr`, `fi`, and `hu`, including suffix chains, harmony, case, derivation-versus-inflection, gradation, possession and conjugation systems.
    - **Phase 44 — East Asian rollout:** execute the same complete language plan for `ja`, `zh`, and `ko`, including Japanese UniDic identity/reading, Mandarin segmentation/scripts/polyphony, Korean NFC/Kiwi/morphemes, grammar routing and reviewed Korean Portuguese-to-English regeneration policy.
    - **Phase 45 — Multilingual freeze:** validate and freeze exactly 66,000 modern identities, 3000 and 1000/band per language, no unknown POS/duplicate identity/foreign contamination, approved licenses/manifests, form packs outside quota, expansions 0-3000 without core hash drift, and mandatory second-pass review.
    - **Phase 46 — Editions and export:** implement stable GUIDs by identity + card role + form analysis, real Core/Important Forms/Grammar/Expansion/Custom/Highlight subdecks, module tags, mixed editions, CSV/TSV manifests, blank Image, model/deck ID isolation, and 1:1 update tests.
    - **Phase 47 — Anki read-only history:** implement the local, sandboxed, size/time/member-limited scheduling APKG importer; never open/write live collections; map only Multilang identity/review evidence, derive minimized learner states, delete raw packages/content, support cold start/corruption, and pass privacy/security second review.
    - **Phase 48 — Adaptive ranking:** implement diagnostics, known-item marking, goals, history signals, separate editorial rank and adaptive priority, `core_first`/`balanced`/`reading_first`, prerequisite eligibility, expansion opt-in, personal provenance, deterministic 50-200 item modules, form-after-lemma sequencing and sibling burying.
    - **Phase 49 — Definitions, sentences, i+1 and exact audio:** generate with identity/sense/form/morphology/known concepts; enforce sense-aware target matching and natural/strict i+1 rules; render meaning-first contextual grammar; distinguish analyses such as indicative versus irrealis `were`; synthesize exact form/sentence audio; isolate/redact personal input; type/sanitize LLM output; enforce cache/rate/budget and drift invalidation.
    - **Phase 50 — Migration rehearsal:** inventory old token/rank/GUID data; classify 1:1/merge/split/drop/unresolved mappings; issue signed preview tied to source/target/backup hashes; rehearse only on restored clone; reuse old GUID only for proven 1:1 mappings; never transfer/delete scheduling for ambiguous mappings; test isolated scheduler preservation, interruption, journal, rollback, idempotency and unresolved blocking.
    - **Phase 51 — Preflight, confirmed apply and release:** run all structural/vertical/client/privacy/license/cost checks before apply; obtain hash-bound user confirmation; transact DB and stage/atomically switch assets with journal; postflight/rollback; validate Desktop current/previous, current AnkiDroid and AnkiMobile separately; release pilots then language families; monitor retention, leeches, time/item and abandonment; audit milestone.
6. **Contratos de gates transversais.** Add exact headings `### Gate de privacidade`, `### Gate de licença`, `### Gate de custo`, and `### Gate de qualidade`. For each, define entry evidence, blocking conditions, exit evidence, audit/retention requirements, and rollback/revocation behavior. Cover personal custom/highlight/APKG data minimization and consent; source redistribution/attribution; provider dry-run estimates, hard caps, caching and idempotency; and morphology/sense/target-match/content/audio/export/migration validation that fails closed.
7. **Dependencies and promotion path.** Include a dependency graph that permits only justified parallelism: `G0 -> 35`; `35 -> 36, 37 and 38`; `36 + 37 + 38 -> 39`; `39 -> 40, 41, 42, 43 and 44`; `40 + 41 + 42 + 43 + 44 -> 45`; `45 -> 46`; `46 -> 47`; `45 + 47 -> 48`; `45 + 48 -> 49`; `46 + 47 + 48 + 49 -> 50`; `50 -> 51`. Parallel language research is allowed only with disjoint ownership; integration remains controlled. Explain that active SPEC/ROADMAP edits occur only after the final separate promotion approval, not while persisting this document.

Do not include implementation patches, pseudo-status claiming a phase is active/done, human-hour estimates, or invented source/provider approvals. Do not edit any file other than the target document.
  </action>
  <verify>
    <automated>test -f docs/multilingual-lexical-adaptive-plan-v4.md && rg -q '^### G0:' docs/multilingual-lexical-adaptive-plan-v4.md && for n in {35..51}; do rg -q "^### Fase ${n}:" docs/multilingual-lexical-adaptive-plan-v4.md || exit 1; done</automated>
    <automated>f=docs/multilingual-lexical-adaptive-plan-v4.md; test "$(rg -c '^\| Moderno \|' "$f")" -eq 22 && test "$(rg -c '^\| Latim isolado \|' "$f")" -eq 1</automated>
    <automated>f=docs/multilingual-lexical-adaptive-plan-v4.md; for row in '| Moderno | pt | Português |' '| Moderno | es | Espanhol |' '| Moderno | en | Inglês |' '| Moderno | fr | Francês |' '| Moderno | de | Alemão |' '| Moderno | it | Italiano |' '| Moderno | pl | Polonês |' '| Moderno | tr | Turco |' '| Moderno | ro | Romeno |' '| Moderno | ru | Russo |' '| Moderno | nl | Neerlandês |' '| Moderno | ko | Coreano |' '| Moderno | da | Dinamarquês |' '| Moderno | nb | Norueguês Bokmål |' '| Moderno | sv | Sueco |' '| Moderno | fi | Finlandês |' '| Moderno | hu | Húngaro |' '| Moderno | cs | Tcheco |' '| Moderno | hr | Croata |' '| Moderno | el | Grego moderno |' '| Moderno | ja | Japonês |' '| Moderno | zh | Mandarim |' '| Latim isolado | la | Latim |'; do rg -Fq "$row" "$f" || exit 1; done</automated>
    <automated>f=docs/multilingual-lexical-adaptive-plan-v4.md; for label in 'LanguageProfile' 'language + normalized lemma + POS + sense' 'Core 3x1000' 'Optional expansion 0-3000' 'SurfaceForms' 'Important Forms' 'Definitions' 'Exact-form audio' 'MWE' 'read-only APKG history' 'adaptive queue' 'real subdecks' 'in-place Multilang migration'; do rg -Fqi "$label" "$f" || exit 1; done; for feature in tense mood person number case gender aspect register; do rg -qi "\b${feature}\b" "$f" || exit 1; done</automated>
  </verify>
  <done>The standalone document contains the complete locked architecture, exact language/policy matrix, G0, all 17 numbered phases, concrete deliverables/exit gates, and dependency path while leaving active planning and implementation untouched.</done>
</task>

<task id="031-02" type="auto">
  <name>Task 2: Audit traceability, safety gates, and write-scope isolation</name>
  <files>docs/multilingual-lexical-adaptive-plan-v4.md</files>
  <action>
Audit the target document against every D-01 through D-15 decision and repair omissions only in that document. Add a final **Traceability and coverage audit** with four explicit tables:

1. `Decisão fixa | Fase(s) principal(is) | Evidência posterior | Status`, with one row for every D-01 through D-15 and no status other than `Coberto`.
2. `Capacidade | Fase responsável | Dependências | Evidência de saída`, covering all language/profile, identity, core, expansion, morphology/forms, Definitions, audio, MWE/sense/routing/card-role, custom, highlights, APKG, adaptive queue, real-subdeck export, migration, and promotion capabilities.
3. `Fase | Privacidade | Licença | Custo | Qualidade`, with one row for G0 and every phase 35-51; use `N/A: justificativa` only where a gate genuinely does not apply, never a blank cell.
4. `Invariante de migração | Evidência da prévia | Evidência de backup/restauração | Confirmação | Comportamento de falha/rollback`, covering stable IDs, user/private data, study history, Korean Portuguese-to-English regeneration, target-English Portuguese explanations, Latin isolation, assets/media, provider costs, interruption/resume, and repeated-run idempotency.

Confirm the document explicitly resolves these common ambiguities per D-05 through D-13: the 3000 unit is a lexical identity rather than a card/form; expansion is additional and optional; `SurfaceForms`/`Important Forms` and their cards do not consume core slots; form-specific Definitions and exact-form audio bind to the shown form; MWEs and senses retain their own identity/routing semantics; custom/highlight data stays personal and cannot alter shared ranks; APKG integration and adaptive scoring never mutate Anki; level/role exports are actual subdecks; and migration cannot run without preview -> backup -> explicit confirmation. Preserve named unknowns as blocking gates with required evidence rather than deleting or silently resolving them.

Before and after editing, compare the dirty-worktree baseline. Do not restore or modify unrelated existing changes. Verify the protected active planning files have no diff and no task-created source/test/config/data/export changes exist. Do not stage or commit.
  </action>
  <verify>
    <automated>f=docs/multilingual-lexical-adaptive-plan-v4.md; for marker in Resultado 'Depende de' Entregáveis 'Critérios de saída'; do test "$(rg -c "^\*\*${marker}:\*\*" "$f")" -eq 18 || exit 1; done</automated>
    <automated>f=docs/multilingual-lexical-adaptive-plan-v4.md; for phrase in 'Política dos idiomas modernos: explicações em inglês' 'Exceção do idioma-alvo inglês: explicações em português' 'Migração coreana no v4: português -> inglês' 'Isolamento do Latim: explicações em português' 'prévia -> backup -> confirmação explícita'; do rg -Fq "$phrase" "$f" || exit 1; done</automated>
    <automated>f=docs/multilingual-lexical-adaptive-plan-v4.md; for gate in privacidade licença custo qualidade; do rg -Fq "### Gate de ${gate}" "$f" || exit 1; done; for id in D-{01..15}; do rg -q "^\| ${id} \|" "$f" || exit 1; done</automated>
    <automated>f=docs/multilingual-lexical-adaptive-plan-v4.md; for code in G0 {35..51}; do rg -q "^\| ${code} \|" "$f" || exit 1; done</automated>
    <automated>git diff --check</automated>
    <automated>python -c "from pathlib import Path; p=Path('docs/multilingual-lexical-adaptive-plan-v4.md'); s=p.read_text(encoding='utf-8'); assert s.endswith('\n'); assert all(line.rstrip()==line for line in s.splitlines()); print('v4 master-plan Markdown whitespace OK')"</automated>
    <automated>git diff --exit-code -- .planning/SPEC.md .planning/ROADMAP.md .planning/STATE.md</automated>
  </verify>
  <done>All 15 locked decisions and every G0/35-51 phase are traceably covered; language, capability, gate, and migration matrices are complete; whitespace checks pass; and no active planning or implementation file was changed by the task.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Personal custom/highlight/APKG input -> Multilang | Private user text and study history cross into future parsing, generation, and adaptation workflows. |
| External lexical/provider output -> curated assets | Potentially incorrect, unlicensed, costly, or manipulated data could become persistent/exported learner content. |
| Imported APKG/archive -> read-only history mapper | An untrusted archive and SQLite schema cross a file/parser boundary. |
| v3/current installation -> v4 migration | Irreplaceable data, stable identity, media, configuration, and study-history mappings cross a destructive-change boundary. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-031-01 | Information Disclosure | Custom lists, highlights, APKG history | mitigate | Require consent, minimization, redaction, private provenance, explicit provider authorization, retention/deletion/export controls, and no raw personal text in logs or redistributed assets. |
| T-031-02 | Tampering | In-place migration | mitigate | Require non-mutating preview, checksummed backup, restore rehearsal, explicit confirmation, transactional/idempotent batches, audit log, and tested rollback before mutation. |
| T-031-03 | Tampering / Denial of Service | APKG parser | mitigate | Require read-only access, archive path/size/count limits, schema/version validation, malformed SQLite rejection, resource limits, and quarantine; prohibit writes to Anki surfaces. |
| T-031-04 | Repudiation / Information Disclosure | Lexical and media provenance | mitigate | Require immutable source versions, attribution, redistribution decisions, content hashes, review evidence, revocation/rebuild paths, and release blocking for unknown rights. |
| T-031-05 | Denial of Service | LLM/translation/TTS provider usage | mitigate | Require preflight estimates, per-item/per-run hard caps, explicit confirmation above limits, caching, idempotency, retry ceilings, and resumable jobs. |
| T-031-06 | Spoofing / Tampering | Lemma/POS/sense and history mapping | mitigate | Require stable versioned identities, profile-pinned analyzers, confidence evidence, deterministic matching, ambiguity quarantine, and fail-closed routing. |
</threat_model>

## Dependency Analysis

- `031-01` needs only the locked task description and read-only repository context; it creates the complete draft artifact.
- `031-02` needs the artifact from `031-01`; it audits and repairs that same file, so the tasks are intentionally serial within one autonomous plan.
- No task creates an interface or artifact consumed by active v3.0 work.

## Source Coverage Audit

| Source type | Item | Coverage |
|---|---|---|
| GOAL | Persist one complete, durable v4 master plan without activating it | Tasks 031-01 and 031-02; D-01, D-02, D-15 |
| REQ | Quick mode has no active ROADMAP requirement IDs | `requirements: []`; active v3.0 requirements remain untouched |
| RESEARCH | No external selection is authorized by this preservation task | G0 plus Phases 38, 43, and 51 retain evidence-bearing source/provider/license/cost/quality gates |
| CONTEXT | All 22 modern languages plus isolated Latin | D-03; language matrix and Phase 35 |
| CONTEXT | English/Portuguese explanation policy and Korean transition | D-04; language matrix, Phases 35, 42, and 50 |
| CONTEXT | Core, expansion, identities, forms, Definitions, and exact audio | D-05 through D-07; Phases 36-43 |
| CONTEXT | MWE/sense/routing/card roles and personal gates | D-08 and D-09; Phases 44-46 |
| CONTEXT | Read-only APKG history, adaptive queue, and real subdecks | D-10 through D-12; Phases 47-49 |
| CONTEXT | In-place migration and privacy/license/cost/quality gates | D-13 and D-14; Phases 50-51 and cross-cutting gate contracts |

No user-deferred idea is included. No source item is unplanned.

<verification>
After both tasks, run every task-level automated command. Inspect `git status --short` against the recorded pre-task baseline: the only task-created substantive path must be `docs/multilingual-lexical-adaptive-plan-v4.md`; pre-existing unrelated changes must be identical. Do not stage, commit, update the quick log, or create UI proof as part of this plan.
</verification>

<success_criteria>
- `docs/multilingual-lexical-adaptive-plan-v4.md` exists as a standalone, substantive v4 master plan.
- G0 and every Phase 35-51 have an outcome, dependencies, concrete deliverables, and measurable exit gates.
- O documento está redigido em português, com exatamente 22 linhas de idiomas modernos e uma linha de Latim isolado, e registra a política confirmada de idiomas das explicações.
- Core/expansion quotas, LanguageProfile, lemma+POS+sense identity, forms/Definitions/audio, MWE/routing/card roles, personal gates, read-only APKG history, adaptive queue, real subdecks, and migration are all connected and traceable.
- Privacy, license, cost, and quality are blocking contracts with evidence and recovery behavior.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, v3.0 Korean artifacts, and all source/test/config/data/export files are untouched by execution.
- No UI proof artifact is created or claimed.
</success_criteria>
