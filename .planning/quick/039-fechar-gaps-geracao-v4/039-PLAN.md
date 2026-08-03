---
mode: quick
task: 039-fechar-gaps-geracao-v4
plan: 039
type: execute
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
autonomous: true
task_count: 3
requirements: []
files_modified:
  - docs/multilingual-lexical-adaptive-plan-v4.md
planned_normative_write_set:
  - docs/multilingual-lexical-adaptive-plan-v4.md
workflow_artifacts_are_separate: true
research_required: false
browser_proof_required: false
no_ui_proof_rationale: "This quick task changes only a preserved, inactive Markdown master plan. It implements no rendered UI and makes no browser or visual claim."
scope_sanity:
  classification: "full-ceremony advisory"
  risk: "Documentation-only and one-target, but broader than normal quick scope because complete contract propagation spans G0, Phases 35-51, four gates, decisions, migration, and traceability."
  disposition: "accepted only after explicit preview risk acceptance; do not split or switch workflows inside this plan"
execution_risk_gate:
  owner: "outer quick orchestrator"
  timing: "after plan preview and before executor delegation"
  required_signal: "proceed despite issues"
workflow_ownership:
  executor_log_update: "prohibited"
  orchestrator_post_verification_log_update: "required"
non_goals:
  - "Do not activate v4, promote it into active planning, start Phase 35, or alter the active v3.0 Korean milestone."
  - "Do not implement or modify schemas, migrations, source code, templates, tests, data/assets, providers, exports, Anki packages, CLI/API/UI behavior, or runtime configuration."
  - "Do not select the future Anki topology in this documentation task; specify the blocking Phase 35 prototype and decision evidence instead."
  - "Do not select unproven sources/providers/licenses or invent evidence-free numeric evaluation thresholds; retain their evidence-bearing G0/Phase 35 gates."
hard_boundaries:
  - "The execution-time normative edit set is exactly docs/multilingual-lexical-adaptive-plan-v4.md. The quick PLAN/SUMMARY/VERIFICATION artifacts are workflow records, not normative edits."
  - "Use apply_patch for every future edit to the master document; do not use broad formatters or generated replacements."
  - "Treat .planning/SPEC.md, .planning/ROADMAP.md, .planning/STATE.md, active v3 Korean artifacts, src/, templates, tests, data/assets, Quick 033 and Quick 035-038, and all non-task/non-workflow dirty paths as read-only."
  - "The executor must not stage, commit, amend, push, restore, reset, clean, stash, or update .planning/quick/LOG.md. The outer quick orchestrator owns the required post-verification LOG append."
  - "Fingerprint non-task/non-workflow paths outside the repository before editing; compare them after editing and never revert or attribute a concurrent mismatch without evidence."
anti_regression_assertions:
  - "Quick 033 remains authoritative: Core has exactly 3000 identities and 3000 default headword cards; every approved Core Important Form is an additional mandatory card in the lemma's same real frequency Level/deck ID."
  - "No cost cap, sample, edition setting, adaptive policy, or export limit may truncate an approved Core Important Form or route it to Expansion/a standalone forms deck."
  - "Separate Anki notes are not siblings under standard Anki sibling burying; any equivalent behavior must be explicitly named, tested, and described honestly."
  - "Shared Core definitions, examples, translations, and audio are canonical per signed deck edition and are never regenerated from an individual learner's history."
  - "The current one-row/one-note/one-template/single-deck export and job/rank-bearing GUID input are migration baseline facts, not proof that v4 is already satisfied."
must_haves:
  truths:
    - "A reader sees exactly 20 normative contract IDs: the existing 12 plus ANKI-01, RANK-01, FORM-04, DISPLAY-01, AUDIO-02, AISEC-01, CONTENT-01, and EVAL-01."
    - "Phase 35 leaves Anki topology unselected until a blocking real-client comparison proves note/card identity, update and scheduling behavior, prerequisites, burying or an honest alternative, dynamic form changes, and supported-client round-trip."
    - "Frequency ranking is reproducible from versioned corpus weights, surface-form allocations, dispersion, sense confidence, MWE overlap rules, analyzer versions, and deterministic tie-breaks."
    - "ImportantFormPolicy, form-card display, pronunciation cache identity, AI input/output isolation, canonical Core editions, and multilingual evaluation each have implementation-ready positive and fail-closed negative contracts."
    - "Core learner history can change only queue/module/order/eligibility; it cannot mutate shared Core content, content GUIDs, ranks, or signed edition assets, while Custom/Highlight remain private paths."
    - "G0 and Phases 35-51, all four transverse gates, dependency/ownership/traceability tables, fixed decisions, and the final audit consistently assign and block on the eight new contracts."
    - "Migration requirements explicitly start from today's one genanki.Note per row, one Card 1 template, one deck instance, and job_id/sort_index-sensitive GUID input, with alias/migration tests rather than a false v4-compliance claim."
    - "The v4 banner remains inactive and the 22-modern-plus-isolated-Latin matrix and Quick 033 formulas remain exact; the executor changes no non-task/non-workflow path, while any unrelated concurrent drift is reported exactly without reversion or attribution."
  artifacts:
    - path: docs/multilingual-lexical-adaptive-plan-v4.md
      provides: "Preserved inactive v4 master plan with 20 normative generation/export contracts, blocking gates, phase ownership, migration baseline, and traceability"
      contains: "ANKI-01, RANK-01, FORM-04, DISPLAY-01, AUDIO-02, AISEC-01, CONTENT-01, EVAL-01"
  key_links:
    - from: "Phase 35 ANKI-01 real-client prototype and signed topology decision"
      to: "Phase 36 persistence"
      via: "hard blocking gate; no topology/schema persistence before both candidate models are tested and one is selected"
    - from: "surface-form corpus observations"
      to: "frozen lexical identity rank"
      via: "RANK-01 allocation, corpus weighting, dispersion, MWE deduplication, confidence, analyzer version, and tie-break contract"
    - from: "ImportantFormPolicy approval"
      to: "mandatory Core form cards"
      via: "FORM-04 evidence score/threshold, attestation, deduplication, analysis confidence, deterministic order, and pre-approval workload forecast"
    - from: "DISPLAY-01 form-card identity"
      to: "selected Anki note/card model"
      via: "stable parent/form/analysis/sense/context IDs and an unambiguous prompt, including distinct same-spelling analyses of were"
    - from: "pronunciation-dependent display context"
      to: "audio cache reuse"
      via: "AUDIO-02 full pronunciation signature rather than a text-only hash"
    - from: "untrusted custom/highlight/corpus content and LLM output"
      to: "Anki fields and canonical lexical facts"
      via: "AISEC-01 isolation, limits, typed validation, escaping/allowlisting, hash-only audit, and non-authoritative LLM status"
    - from: "signed Core deck edition"
      to: "learner-specific adaptive queue"
      via: "CONTENT-01 immutable shared content boundary; only queue/module/order/eligibility may vary"
    - from: "current job/rank-sensitive one-note-per-row export"
      to: "selected semantic note/card topology"
      via: "Phase 46 compatibility plus Phase 50 migration/alias rehearsal and Phase 51 client preflight"
---

# Quick Task 039 Plan: Fechar gaps de geração v4

<objective>
Revise the preserved inactive v4 master document so all eight reviewed generation gaps become exact normative contracts with blocking decision evidence, phase deliverables and exits, transverse gates, acceptance examples, migration coverage, and complete traceability.

Purpose: prevent future v4 implementation from silently choosing an invalid Anki topology, producing unstable ranks/forms/audio/content, trusting private or LLM-controlled material, or approving quality without reproducible evidence.

Output: one internally consistent update to `docs/multilingual-lexical-adaptive-plan-v4.md`; no v4 implementation or activation.
</objective>

<context>
Read-only execution context:

- `AGENTS.md`
- `.planning/config.json`
- `.planning/SPEC.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/quick/033-formas-no-deck-de-frequencia/033-PLAN.md`
- `.planning/quick/033-formas-no-deck-de-frequencia/033-SUMMARY.md`
- `docs/multilingual-lexical-adaptive-plan-v4.md`
- `src/multilang/services/export_anki_package.py`
- `src/multilang/domain/exporting.py`
- `.agents/skills/llm-security/rules/prompt-injection.md`
- `.agents/skills/llm-security/rules/output-handling.md`
- `.agents/skills/llm-security/rules/sensitive-disclosure.md`
- `.agents/skills/llm-security/rules/unbounded-consumption.md`
- `.agents/skills/llm-security/rules/misinformation.md`
- `.agents/skills/code-security/rules/xss.md`

Discovery level 0: this is a static consistency revision of one existing master document using locked user decisions and inspected repository facts. No external dependency choice or research phase is authorized.

Current baseline facts that the document must state honestly:

- `export_anki_package()` builds one `genanki.Deck` and calls `deck.add_note(build_multilang_note(row, model=model))` once per `ExportCardRow`.
- `build_multilang_model()` defines exactly one template named `Card 1`; each row therefore currently becomes one note producing one card under this model.
- `ExportCardIdentity.stable_guid_input()` currently includes language, source type, `job_id`, `item_key`, `lemma_key`, and `sort_index`; `build_export_note_guid()` hashes that input.
- Current generated field strings can be interpreted as HTML by Anki templates; their present transport/rendering behavior is a safety baseline, not proof of the future `AISEC-01` output contract.
- These facts are a migration source shape. They do not satisfy the future semantic topology/GUID requirements and must not be described as if they do.
- Standard Anki sibling burying applies to cards generated from the same note. Separate notes linked only by metadata are not Anki siblings.

The worktree already contains Quick 033's uncommitted target-document change plus unrelated Quick 035-038, template, test, preview, LOG, and deleted-report work. During the executor window, only the target may receive a normative edit and the executor must not touch LOG or unrelated paths. Unrelated agents are not required to become quiescent: if they create or change paths during execution, report those paths exactly, stop further task-owned editing, and neither revert nor claim/attribute their work. After verification, the outer quick orchestrator—not the executor—must append Quick 039 to LOG.
</context>

## Locked Decisions

- **Q039-D01 — Anki model remains unselected:** Phase 35 must compare a lexical-family note with headword/form cards against separate semantically linked notes in real supported clients. Phase 36 cannot persist either topology until the blocking evidence and decision are signed. Native sibling behavior may be claimed only for cards of one note; separate notes require an explicitly honest alternative.
- **Q039-D02 — Canonical Core content boundary:** Definitions, examples, translations, and audio are signed/versioned per Core deck edition, never regenerated from learner history. Adaptation changes queue/module/order/eligibility only; private Custom/Highlight content remains isolated.
- **Q039-D03 — Quick 033 semantics remain exact:** Core is exactly 3000 lexical identities and 3000 headword cards; every approved Core Important Form is an additional mandatory card in the parent's real level/deck ID, never Expansion, optional truncation, or a standalone forms destination.

## Scope Advisory and Explicit Risk Gate

This remains documentation-only work over one normative target, but its required all-source propagation is broader than normal quick scope. Reducing that breadth would lose the user's complete goal, so the plan records a **full-ceremony advisory/risk** rather than omitting coverage. The outer quick orchestrator must show the plan preview and receive the exact response **`proceed despite issues`** before delegating execution. After that one pre-execution risk acceptance, all three tasks remain autonomous. Do not split this plan or route to another workflow from inside it.

## Document Trace IDs Added by This Revision

Extend the document's fixed-decision table from D-01..D-15 to D-01..D-23, preserving the first 15 rows and adding these one-to-one rows in this exact order:

| Fixed decision | Normative contract |
|---|---|
| D-16 | `ANKI-01` |
| D-17 | `RANK-01` |
| D-18 | `FORM-04` |
| D-19 | `DISPLAY-01` |
| D-20 | `AUDIO-02` |
| D-21 | `AISEC-01` |
| D-22 | `CONTENT-01` |
| D-23 | `EVAL-01` |

<tasks>

<task id="039-01" type="auto">
  <name>Task 1: Formalize the 20 contracts and the blocking Phase 35 decision surface</name>
  <files>docs/multilingual-lexical-adaptive-plan-v4.md</files>
  <action>
Before editing, create `C:/Users/MIGUEL~1.RAF/AppData/Local/Temp/opencode/quick-039-before.json` outside the repository. Build it from Git subprocess argument arrays (never `shell=True`) with this exact canonical, timestamp-free schema so the after object can compare by value:

```json
{
  "schema_version": 1,
  "excluded_worktree_paths": [
    "docs/multilingual-lexical-adaptive-plan-v4.md",
    ".planning/quick/039-fechar-gaps-geracao-v4/**",
    ".planning/quick/LOG.md"
  ],
  "non_task_status_sha256": "sha256(git status --porcelain=v1 -z over . with all three paths excluded)",
  "non_task_status_records": ["normalized status plus repo-relative path records"],
  "non_task_unstaged_diff_sha256": "sha256(git diff --binary over . with all three paths excluded)",
  "non_task_unstaged_path_hashes": {"tracked/repo/relative/path": "sha256(per-path binary diff)"},
  "non_task_untracked_files": {"untracked/repo/relative/path": "sha256(file bytes)"},
  "full_cached_diff_sha256": "sha256(git diff --cached --binary over the full repository)",
  "full_cached_path_hashes": {"staged/repo/relative/path": "sha256(per-path cached binary diff)"},
  "full_index_sha256": "sha256(git ls-files --stage -z over the full repository)",
  "full_index_path_hashes": {"tracked/repo/relative/path": "sha256(mode/blob/stage index records)"}
}
```

The three worktree exclusions have distinct owners: the normative target intentionally changes; Quick 039 PLAN/SUMMARY/VERIFICATION are workflow artifacts; and LOG is owned by the outer quick orchestrator after verifier completion. No `non_task_*` worktree/content field may include any of those three paths. Obtain `non_task_untracked_files` from `git ls-files --others --exclude-standard -z` with those exclusions. Build `non_task_unstaged_path_hashes` for every tracked path returned by the excluded-path `git diff --name-only -z`, preserving `MISSING` for deletions. Normalize separators to `/`, retain status code/rename source and destination in `non_task_status_records`, sort all records/keys, and hash bytes/diffs without recording content.

The `full_*` hashes/maps are separate Git-index integrity controls, not worktree-content preservation claims. They intentionally cover the whole repository so before/after equality proves that the executor staged nothing and changed no existing staged state, even when the baseline index is non-clean; the path maps make any staged/index drift attributable to exact paths. Never assert that the cached diff is empty. Serialize as UTF-8 with `sort_keys=True`, indentation, and one final newline. Do not include capture time, ignored files, file contents, or environment values. This baseline supports a claim only about non-task/non-workflow paths during the executor window plus unchanged index/staged state. If the external temp parent is unavailable or a listed path changes while being captured, report the exact path and stop; do not place the fingerprint in the repository.

Then use `apply_patch` only on the target document. Preserve its exact inactive banner, active-v3 boundary, 22-modern-plus-isolated-Latin matrix, isolated Latin policy, Quick 033 formulas, and current G0/Phase headings/dependencies. Implement Q039-D01 through Q039-D03 in §§1, 3, 4, G0, and Phase 35:

1. Expand the §3.5 normative table from exactly 12 to exactly 20 unique IDs. Preserve the existing rows `CARD-01`, `FORM-01`, `FORM-02`, `FORM-03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01`, and `GUID-01`; add exactly `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01`, and `EVAL-01`. Replace only stale contract-count phrases such as `12 contratos`, `todos os 12`, `12 IDs`, or `12 contract(s)` with the correct 20-contract wording. Do not treat a generic numeral 12 as stale; preserve the fixed-decision row `D-12` and the end-to-end flow row `| 12. Adaptação |` exactly once each.
2. Make `ANKI-01` a no-preselection contract. Require a Phase 35 blocking, signed, real-client prototype/decision comparing at least: **Modelo A — uma nota lexical por família com cards de headword/formas** and **Modelo B — notas separadas ligadas por metadados semânticos de família**. Both prototypes must measure actual Anki note GUID versus generated card identity/template ordinal, import/reimport/update and alias behavior, scheduling preservation, lemma-before-form behavior, sibling burying where native or the exact honest alternative where not, dynamic form add/remove, collision/duplication, and round-trip separately on Anki Desktop current, Anki Desktop previous supported version, current AnkiDroid, and current AnkiMobile. Include the literal negative rule **“notas separadas não são siblings no Anki padrão”**. No v4 schema/persistence may proceed before one model is selected from evidence; do not select it in this document revision.
3. Define `RANK-01` as a versioned deterministic aggregation contract. Require corpus IDs/checksums/token and document counts; nonnegative corpus weights summing to 1; analyzer/versioned surface-form candidates; confidence-scored lemma/POS/sense allocation shares summing to 1 only for accepted occurrences; quarantine rather than first-sense allocation below threshold; deterministic MWE longest-span/approved-overlap handling that prevents one token occurrence from being double-counted in the same counting channel; and this exact parameterized formula block, with all inputs, thresholds, natural-log behavior, and rounding precision versioned:
   `allocated_count(c,i) = sum_o occurrence_count(c,o) * allocation_share(o,i)`;
   `frequency_ppm(c,i) = 1_000_000 * allocated_count(c,i) / corpus_token_count(c)`;
   `dispersion(c,i) = document_frequency(c,i) / corpus_document_count(c)`;
   `rank_score(i) = round(sum_c corpus_weight(c) * ln(1 + frequency_ppm(c,i)) * dispersion(c,i), rank_precision)`.
   Final ordering is `rank_score DESC`, aggregate allocated frequency `DESC`, then `lexical_identity_id ASC`. Analyzer/policy/input drift must create a new ranking version, full diff, and reapproval; equal inputs/versions must reproduce ranks and manifest hash.
4. Define `FORM-04` as a per-language versioned `ImportantFormPolicy`. Require the exact score rule `important_form_score = round(sum_k evidence_weight(k) * evidence_value(k), score_precision)`, with nonnegative weights summing to 1 and normalized evidence values. Its schema must name minimum score, attestation threshold, analysis-confidence threshold, dedup key, same-spelling/different-analysis exception, prerequisite ordering, workload forecast, policy/version/hash, and approval evidence. Approval is exactly `score >= minimum_score AND attestation >= attestation_threshold AND analysis_confidence >= analysis_confidence_threshold` after deterministic deduplication. Sort approved forms by `prerequisite_depth ASC`, `important_form_score DESC`, normalized surface `ASC`, then `morphological_analysis_id ASC`. Forecast full mandatory card/audio/review cost before approval. After approval, no truncation, top-N cut, cost cap, edition cap, or 3000-card cap may remove it; changing eligibility requires a new policy version/diff/review, not silent export truncation.
5. Define `DISPLAY-01` with a structured form-card contract containing at least `form_card_id`, `parent_lexical_identity_id`, displayed parent lemma, `card_role`, `surface_form_id`, exact displayed surface text, `morphological_analysis_id`, normalized analysis features, `sense_id`, context/sense cue, definition/content version, pronunciation-signature reference, deck-edition ID, inherited real deck ID, prerequisite reference, and rendering-policy version. The front prompt must show enough context to ask what the exact form means/realizes here; an ambiguous spelling alone is forbidden. The answer must expose parent lemma, role, analysis, relevant sense/context, and exact-form audio. Distinct analyses of the same spelling retain distinct stable IDs/cards/cues.
6. Define `AUDIO-02` and name its cache tuple `pronunciation_signature`. It includes language and `LanguageProfile` version, exact displayed text, declared normalized text, contextual reading/phonemes, morphology analysis and sense when pronunciation depends on them, locale, voice, SSML/prosody, pronunciation-policy version, provider, and provider/model version. Reuse requires full-signature equality plus artifact integrity. A text-only hash is explicitly forbidden for heterophones/polyphony.
7. Define `AISEC-01` for custom, highlight, and corpus boundaries: treat all embedded instructions as untrusted data; separate control instructions from delimited/typed content; enforce versioned byte/character/token/record limits before provider calls; send only minimum authorized context and no secrets/raw private context; validate LLM output against closed typed schemas and lexical/source evidence; escape all Anki fields by output context or use a documented strict tag/attribute allowlist; reject scripts, event handlers, executable URLs, active markup, provider/tool commands, and unapproved Anki directives; enforce rate/concurrency/token/budget/retry limits; audit only hashes, IDs, versions, counts, decisions, and sanitized metadata; and state that LLM output is never authoritative for lexical identity, morphology, sense, rank, or pronunciation facts.
8. Define `CONTENT-01` around a signed `deck_edition_id` and versioned canonical Core content bundle. Core definitions, examples, translations, pronunciation signatures/audio assets, render policy, and review evidence are shared edition facts. Learner history cannot regenerate or mutate them or change their semantic GUID. A material correction creates a new edition/content version, machine-readable diff, review, alias/migration decision where needed, and release evidence. Custom/Highlight use isolated private content/version namespaces and never overwrite the shared Core bundle. Include these exact machine-searchable normative sentences: **“O conteúdo Core é canônico e versionado por edição assinada.”**, **“É proibido ao histórico do aprendiz regenerar ou mutar conteúdo Core compartilhado.”**, and **“A adaptação altera somente queue/module/order/eligibility.”**
9. Define `EVAL-01` with hash/versioned per-language reference datasets and risk strata for definition correctness/conciseness, form analysis, naturalness, target/sense match, translation, strict/adaptive/contextual i+1, pronunciation/audio, and HTML/Anki-field safety. Every metric must define numerator, denominator, sample/strata, evidence-derived threshold, drift tolerance, and blocker behavior. Use `dimension_pass_rate = passed_cases / eligible_cases`, `critical_failure_rate = critical_failures / eligible_cases`, and `regression_delta = current_dimension_pass_rate - signed_baseline_dimension_pass_rate`; subjective review dimensions use anchored scores `0=wrong/unsafe`, `1=major error`, `2=material correction required`, `3=correct with minor issue`, `4=release quality`. Structural/security/fail-closed checks remain deterministic and 100%-blocking where already required. Approval combines deterministic validators with independent specialist/human review; an LLM judge may be a secondary signal but can never be the sole approver. Dataset/analyzer/prompt/provider/policy drift reruns affected suites and blocks release below threshold or beyond allowed regression.
10. Extend `LanguageProfile` fields/capabilities for topology decision/version/client matrix, ranking inputs/formula, ImportantFormPolicy, form-display policy, pronunciation-signature policy, AI trust/limit/output policy, canonical edition/content policy, and evaluation datasets/thresholds/drift. All are `disabled`, `evidence_pending`, or `enabled` with evidence, and missing capability fails closed.
11. Update domain invariants and the end-to-end flow to connect ranking observations to identities, form approval to mandatory workload, display to semantic card identity, pronunciation signature to cache, untrusted input to typed/escaped output, signed edition content to adaptation, and evaluation to release. Do not mutate the meaning of flow step `12. Adaptação` merely to remove a valid numeral.
12. Expand G0 to inventory the current exporter/GUID source shape, require evaluation-threshold evidence and baseline fixtures, and explicitly state **“o comportamento atual não satisfaz automaticamente a v4”**. Phase 35 must close all 20 contracts, run the two Anki prototypes, publish the candidate comparison and signed decision, and block Phase 36 when any contract/prototype/client result is unresolved.

Add one machine-searchable positive/negative acceptance table covering at least these exact scenarios:

- same-note cards can demonstrate native sibling burying; separate notes linked by family metadata are **not** native siblings and need a named alternative;
- `be/is/was/were`: all accepted surface evidence aggregates reproducibly to the correct lemma/POS/sense rank, approved forms stay mandatory in `be`'s real level, and indicative/irrealis `were` get distinct prompts/analyses/cards without consuming Core identities;
- Mandarin `行` (`xíng`/`háng`) and Japanese `生` readings produce different pronunciation signatures/assets; same text alone never authorizes reuse;
- benign private custom/highlight text remains private and typed, while “ignore previous instructions...” is treated only as quoted data and cannot change controls;
- plain learner text is safely encoded, while `<script>`, event-handler, `javascript:` URL, or executable markup output is rejected rather than rendered;
- same semantic item across a new job/rank retains the selected future semantic identity, while today's `job_id`/`sort_index` GUID drift is detected and handled by a proven 1:1 alias/migration instead of being called stable.

Do not edit later phase/traceability sections in this task except where a short cross-reference is required; Task 2 owns full propagation.
  </action>
  <verify>
    <automated>test -s "C:/Users/MIGUEL~1.RAF/AppData/Local/Temp/opencode/quick-039-before.json"</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); expected={"CARD-01","FORM-01","FORM-02","FORM-03","SENSE-01","MWE-01","ROUTE-01","DEF-01","AUDIO-01","LOAD-01","DEPEND-01","GUID-01","ANKI-01","RANK-01","FORM-04","DISPLAY-01","AUDIO-02","AISEC-01","CONTENT-01","EVAL-01"}; ids=re.findall(r"^\| `([A-Z]+-\d{2})` \|",s,re.M); assert len(ids)==20 and set(ids)==expected and len(ids)==len(set(ids)),ids; patterns=(r"\b12\s+(?:contratos?|ids?|contracts?)\b",r"\btodos?\s+os?\s+12\b",r"\b(?:contratos?|ids?|contracts?)\b(?:\s+(?:normativos?|explícitos?|count))?\s*(?:(?:são|are|is)|:|=)?\s*12\b",r"\b(?:contract|contrato|id)[-_ ]?count\s*(?:(?:is|é)|:|=)?\s*12\b"); stale=[(i,l) for i,l in enumerate(s.splitlines(),1) if any(re.search(p,l,re.I) for p in patterns)]; assert not stale,stale; assert len(re.findall(r"\bD-12\b",s))==1 and s.count("| D-12 |")==1; assert s.count("| 12. Adaptação |")==1; print("20-contract set, stale contract-count phrases, D-12, and flow-12 OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8").casefold(); required=("modelo a","modelo b","notas separadas não são siblings no anki padrão","o comportamento atual não satisfaz automaticamente a v4","job_id","sort_index","rank_score desc","lexical_identity_id asc","importantformpolicy","form_card_id","pronunciation signature","text-only hash","ignore previous instructions","<script>","javascript:","行","xíng","háng","生","indicativo","irrealis"); missing=[x for x in required if x.casefold() not in s]; assert not missing,missing; print("blocking contracts and acceptance examples OK")'</automated>
    <automated>git diff --check -- "docs/multilingual-lexical-adaptive-plan-v4.md"</automated>
  </verify>
  <done>The master document contains exactly 20 implementation-ready contracts, an unselected but blocking two-model Anki decision gate, complete ranking/form/display/audio/security/content/evaluation boundaries, current-shape migration facts, and positive/negative examples without weakening Quick 033.</done>
</task>

<task id="039-02" type="auto">
  <name>Task 2: Propagate ownership through Phases 36-51, gates, decisions, and traceability</name>
  <files>docs/multilingual-lexical-adaptive-plan-v4.md</files>
  <action>
Using `apply_patch` only, perform a section-by-section propagation pass over every applicable G0/Phase 35-51 deliverable and blocking exit criterion, all four transverse gates, §7 dependencies/promotion text, and every §8 traceability table. Reference contract IDs literally so ownership can be scanned. Preserve the exact existing headings, dependency statements, and graph edges; annotate the `35 -> 36` edge with the blocking `ANKI-01` decision rather than inventing a bypass.

Apply this exact primary ownership:

- G0 records the current-export/GUID source baseline for `ANKI-01`/`GUID-01` and evidence-bearing dataset/threshold prerequisites for `EVAL-01`; these are prerequisites, not a topology selection or a v4-compliance claim.
- Phase 35 closes all 20 contracts and both real-client Anki prototypes/decision; unresolved evidence blocks all affected downstream work.
- Phase 36 persists only the selected note/card/GUID/alias model after `ANKI-01`; it must not encode either candidate before the gate.
- Phase 37 owns `RANK-01` corpus manifests, concrete weights, allocation outputs, formula parameters/rounding, dispersion, MWE dedup, drift diffs, deterministic ranks, and reproducibility evidence.
- Phase 38 owns `FORM-04`, `DISPLAY-01` linguistic analysis evidence, and `AUDIO-02` contextual pronunciation evidence/policies, including approval/workload before mandatory export.
- Phase 39 proves all 20 contracts with at least one applicable positive and negative case and includes the six named scenario families from Task 1.
- Phases 40-44 run family-specific `EVAL-01` datasets/rubrics and applicable `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, and `CONTENT-01` checks; no generic adapter or LLM-only judgment can waive a language failure.
- Phase 45 freezes signed `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01`, and `EVAL-01` policies/evidence, per-language reference datasets, and canonical Core edition content/diffs alongside the existing 66,000 identities/headwords and mandatory form workload.
- Phase 46 implements only the selected `ANKI-01` topology and tests `FORM-04`/`DISPLAY-01` semantic note/card identity, aliases, updates, scheduling, dynamic forms, real levels, supported-client structural compatibility, and migration from the current one-row/one-note model.
- Phase 47 maps read-only history under the selected `ANKI-01` model, distinguishing note GUID, generated card identity/template ordinal, `DISPLAY-01` card role/form analysis, and uncertain legacy mappings.
- Phase 48 enforces `CONTENT-01`: learner signals change only queue/module/order/eligibility; they never regenerate/mutate shared Core definition/example/translation/audio/content version/GUID. Preserve private Custom/Highlight adaptation.
- Phase 49 owns grounded `AISEC-01` generation, `DISPLAY-01` rendering, full `AUDIO-02` signatures/cache behavior, canonical Core edition materialization under `CONTENT-01`, and `EVAL-01` release evidence. Personal known concepts may condition private Custom/Highlight content but not canonical Core content.
- Phase 50 rehearses `ANKI-01` migration/aliases from today's one `genanki.Note` per row, one `Card 1` template, one deck instance, and `job_id`/`sort_index`-bearing GUID input to the selected semantic model. Test job/rank drift, 1:1 aliases, splits/merges, `FORM-04`/`DISPLAY-01` dynamic form add/remove, scheduling preservation/non-transfer on ambiguity, and rollback on each supported client fixture.
- Phase 51 runs preflight and real supported-client checks for the selected `ANKI-01` topology, `CONTENT-01` canonical edition hashes, `AISEC-01` secure output, full `AUDIO-02` pronunciation signatures, `EVAL-01` regression/drift thresholds, migration reconciliation, and release monitoring. A client/topology/evaluation failure blocks release.

For every phase/ID mapping above, place each required ID literally in both that phase's `**Entregáveis:**` subsection and its `**Critérios de saída:**` subsection. A mention elsewhere in the phase, another phase, a gate, or traceability table does not satisfy propagation. Keep each deliverable concrete and each corresponding exit criterion blocking/measurable.

Reconcile existing unconditional sibling language everywhere (`DEPEND-01`, `be/is/was/were`, Phases 38-51, gates, capabilities, migration invariants). Native sibling burying may be promised only when selected cards belong to one note and the supported client proves it. If separate notes are selected, state that they are not siblings and name/test the honest prerequisite/concurrent-exposure alternative; metadata alone cannot create sibling semantics. Keep lemma-before-form and non-concurrent exposure as required outcomes, but make the mechanism conditional on the selected/proven model.

Reconcile canonical/adaptive language everywhere: Core content generation is edition-wide and learner-independent; learner history only controls queue/module/order/eligibility. Any Core correction creates a new signed edition/content diff/review and never a learner-specific mutation. Custom/Highlight remain private. Remove or qualify any Phase 49 wording that conditions shared Core generation on personal `known concepts`.

Update each transverse gate with entry evidence, blockers, exit evidence, audit/retention, and rollback/revocation for the new contracts:

- Privacy: AI prompt/data isolation, private Custom/Highlight boundaries, no raw content/secrets, hash-only audit, canonical-vs-private content separation.
- License: corpus/rank manifests, canonical content and audio provenance, provider/policy versions, and derived form/evaluation dataset rights.
- Cost: input/token/rate/budget limits and full FORM-04 workload forecast; caps fail safely but never truncate already approved mandatory Core forms.
- Quality: all 20 contracts, real-client topology proof, deterministic ranking/forms/signatures, independent per-language EVAL-01 review, 100% HTML/script safety blockers, and no sole LLM judge.

Each gate must retain exactly one substantive subsection under each existing marker `**Evidência de entrada:**`, `**Condições bloqueantes:**`, `**Evidência de saída:**`, `**Auditoria e retenção:**`, and `**Rollback/revogação:**`. Do not satisfy a gate by mentioning an ID outside these five structures.

Update §7/§8 as follows:

1. Keep the existing 11 dependency graph lines exact. Add prose that Phase 36 is unreachable until the Phase 35 `ANKI-01` gate is signed and that transverse gate failures still block edges.
2. Expand fixed decisions from exactly D-01..D-15 to exactly D-01..D-23 using the mapping declared above. Preserve and update D-01..D-15, especially Core/form/topology/adaptation/security rows; add one evidence-bearing row per new contract.
3. Add exact capability/ownership rows for each of the eight new IDs and revise aggregate contract ownership from 12 to 20. Include the current-export-to-selected-model migration row.
4. Update every G0/35-51 row in the four-gate matrix where a new contract applies; no blank cell or generic “covered” claim.
5. Extend migration invariants for current note/card/GUID topology, semantic alias mapping, rank/job drift, dynamic forms, selected-model scheduling, canonical edition content, pronunciation signatures, prompt/HTML safety, and evaluation baselines.
6. Update the final statement to say exactly **“as 23 decisões fixas, os 20 contratos explícitos, as 23 linhas de requisitos linguísticos”**, while retaining the inactive/no-silent-approval conclusion.

Do not claim that current source behavior is v4-compliant, do not select an Anki candidate, and do not change any protected file.
  </action>
  <verify>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); heads=["### G0: Pré-requisitos de promoção e baseline congelada","### Fase 35: Contratos","### Fase 36: Persistência","### Fase 37: Fontes e cobertura","### Fase 38: Morfologia e curadoria","### Fase 39: Piloto representativo","### Fase 40: Rollout românico","### Fase 41: Rollout germânico","### Fase 42: Rollout eslavo e grego moderno","### Fase 43: Rollout aglutinativo","### Fase 44: Rollout do Leste Asiático","### Fase 45: Freeze multilíngue","### Fase 46: Edições e exportação","### Fase 47: Histórico Anki somente de leitura","### Fase 48: Ranking adaptativo","### Fase 49: `Definitions`, sentenças, i+1 e áudio exato","### Fase 50: Ensaio de migração","### Fase 51: Preflight, aplicação confirmada e release"]; assert all(s.count(h)==1 for h in heads); blocks=re.split(r"(?=^### (?:G0:|Fase \d+:))",s,flags=re.M); entries=[b for b in blocks if b.startswith("### G0:") or b.startswith("### Fase ")]; assert len(entries)==18; assert all(all(f"**{m}:**" in b for m in ("Resultado","Depende de","Entregáveis","Critérios de saída")) for b in entries); print("exact G0/35-51 headings and markers OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); expected={"G0":"Conclusão, verificação e arquivamento formais da v3.0; nenhuma dependência v4 pode substituir esse requisito.","35":"G0 aprovado e promoção separada registrada.","36":"Fase 35.","37":"Fase 35.","38":"Fase 35.","39":"Fases 36, 37 e 38.","40":"Fase 39.","41":"Fase 39.","42":"Fase 39.","43":"Fase 39.","44":"Fase 39.","45":"Fases 40, 41, 42, 43 e 44.","46":"Fase 45.","47":"Fase 46.","48":"Fases 45 e 47.","49":"Fases 45 e 48.","50":"Fases 46, 47, 48 e 49.","51":"Fase 50."}; blocks={}; starts=list(re.finditer(r"^### (G0|Fase (\d+)):",s,re.M)); [blocks.__setitem__("G0" if m.group(1)=="G0" else m.group(2),s[m.start():(starts[i+1].start() if i+1<len(starts) else len(s))]) for i,m in enumerate(starts)]; bad={k:v for k,v in expected.items() if f"**Depende de:** {v}" not in blocks[k]}; assert not bad,bad; graph=("G0 -> 35","35 -> 36, 37 and 38","36 + 37 + 38 -> 39","39 -> 40, 41, 42, 43 and 44","40 + 41 + 42 + 43 + 44 -> 45","45 -> 46","46 -> 47","45 + 47 -> 48","45 + 48 -> 49","46 + 47 + 48 + 49 -> 50","50 -> 51"); assert all(s.count(x)==1 for x in graph); print("exact dependency statements and graph OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); starts=list(re.finditer(r"^### (G0|Fase (\d+)):",s,re.M)); phase_end=s.index("\n## 6.",starts[-1].start()); blocks={("G0" if m.group(1)=="G0" else m.group(2)):s[m.start():(starts[i+1].start() if i+1<len(starts) else phase_end)] for i,m in enumerate(starts)}; all20=("CARD-01","FORM-01","FORM-02","FORM-03","SENSE-01","MWE-01","ROUTE-01","DEF-01","AUDIO-01","LOAD-01","DEPEND-01","GUID-01","ANKI-01","RANK-01","FORM-04","DISPLAY-01","AUDIO-02","AISEC-01","CONTENT-01","EVAL-01"); rollout=("RANK-01","FORM-04","DISPLAY-01","AUDIO-02","AISEC-01","CONTENT-01","EVAL-01"); required={"G0":("ANKI-01","GUID-01","EVAL-01"),"35":all20,"36":("ANKI-01",),"37":("RANK-01",),"38":("FORM-04","DISPLAY-01","AUDIO-02"),"39":all20,"40":rollout,"41":rollout,"42":rollout,"43":rollout,"44":rollout,"45":rollout,"46":("ANKI-01","FORM-04","DISPLAY-01"),"47":("ANKI-01","DISPLAY-01"),"48":("CONTENT-01",),"49":("DISPLAY-01","AUDIO-02","AISEC-01","CONTENT-01","EVAL-01"),"50":("ANKI-01","FORM-04","DISPLAY-01"),"51":("ANKI-01","AUDIO-02","AISEC-01","CONTENT-01","EVAL-01")}; assert set(blocks)==set(required),set(blocks); assert all(b.count("**Entregáveis:**")==1 and b.count("**Critérios de saída:**")==1 for b in blocks.values()); deliverables={p:b.split("**Entregáveis:**",1)[1].split("**Critérios de saída:**",1)[0] for p,b in blocks.items()}; criteria={p:b.split("**Critérios de saída:**",1)[1] for p,b in blocks.items()}; audit={p:{"Entregáveis":[x for x in ids if x not in deliverables[p]],"Critérios de saída":[x for x in ids if x not in criteria[p]]} for p,ids in required.items()}; bad={p:v for p,v in audit.items() if v["Entregáveis"] or v["Critérios de saída"]}; assert not bad,bad; print("G0/phase deliverable and blocking-exit propagation OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); starts=list(re.finditer(r"^### Gate de (privacidade|licença|custo|qualidade)$",s,re.M)); gate_end=s.index("\n## 7.",starts[-1].start()); blocks={m.group(1):s[m.start():(starts[i+1].start() if i+1<len(starts) else gate_end)] for i,m in enumerate(starts)}; markers=("**Evidência de entrada:**","**Condições bloqueantes:**","**Evidência de saída:**","**Auditoria e retenção:**","**Rollback/revogação:**"); assert set(blocks)=={"privacidade","licença","custo","qualidade"}; assert all(all(b.count(marker)==1 for marker in markers) for b in blocks.values()); parts={name:[b.split(markers[i],1)[1].split(markers[i+1],1)[0].strip() if i+1<len(markers) else b.split(markers[i],1)[1].strip() for i in range(len(markers))] for name,b in blocks.items()}; assert all(all(len(part)>=40 for part in gate_parts) for gate_parts in parts.values()),{k:[len(x) for x in v] for k,v in parts.items()}; required={"privacidade":("AISEC-01","CONTENT-01"),"licença":("RANK-01","FORM-04","AUDIO-02","CONTENT-01","EVAL-01"),"custo":("FORM-04","AUDIO-02","AISEC-01"),"qualidade":("ANKI-01","RANK-01","FORM-04","DISPLAY-01","AUDIO-02","AISEC-01","CONTENT-01","EVAL-01")}; missing={name:[x for x in ids if x not in blocks[name]] for name,ids in required.items() if any(x not in blocks[name] for x in ids)}; assert not missing,missing; print("all gate evidence/blocker/exit/audit/rollback structures OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); decisions=re.findall(r"^\| (D-\d{2}) \|",s,re.M); assert decisions==[f"D-{n:02d}" for n in range(1,24)],decisions; assert "as 23 decisões fixas, os 20 contratos explícitos, as 23 linhas de requisitos linguísticos" in s; print("fixed decisions and final audit count OK")'</automated>
  </verify>
  <done>Every new contract has concrete Phase 35-51 ownership and blockers; native versus non-native Anki behavior is honest; canonical Core content is separated from adaptation; all four gates, dependencies, D-01..D-23, ownership, migration, and final audit are consistent.</done>
</task>

<task id="039-03" type="auto">
  <name>Task 3: Run the exhaustive stale-reference and protected-scope audit</name>
  <files>docs/multilingual-lexical-adaptive-plan-v4.md</files>
  <action>
Perform a final line-by-line audit of the target and repair only that file with `apply_patch`. This is an acceptance gate, not a keyword-presence shortcut.

1. Print and inspect every occurrence (with line number/context) of stale contract-count phrases only: `12 contratos?`, `todos? os? 12`, `12 IDs?`, `12 contracts?`, and inverse count formulations such as `contratos normativos ... 12`; also inspect all 20 contract IDs, `sibling|bury|enterr`, `note|card|GUID|job_id|sort_index|Card 1|genanki`, `3000|Important Form|Expansion|frequency_card_count|frequency_level_card_count`, `rank|corpus|dispersion|sense allocation|MWE`, `known concepts|history|canonical|edition|adaptive`, `prompt|custom|highlight|corpus|HTML|script|URL|markup|escape|allowlist`, `audio|reading|phoneme|polyphony|polifonia`, `evaluation|rubric|threshold|drift|LLM judge`, and G0/Phase/gate/decision/ownership/migration references. Read each match in context and remove contradictions, not valid unrelated uses. Never treat every occurrence of the numeral 12 as stale.
2. Assert no stale 12-contract/count phrase remains. Separately assert the fixed-decision row `| D-12 |` and flow row `| 12. Adaptação |` each exist exactly once. Other legitimate numeral 12 occurrences are allowed.
3. Assert the normative table has the exact 20-ID set once each, Phase 39 says/proves all 20, the capability table owns all eight additions, fixed decisions are exactly D-01..D-23, and the final audit reports 23 decisions/20 contracts/23 language rows.
4. Recheck every sibling claim. The document must never imply separate notes are siblings, and all exported burying/prerequisite guarantees must identify the selected proven model or an honest alternative. Recheck that no wording preselects either model before Phase 35.
5. Recheck Q039-D02/Q039-D03: no personal history mutates/regenerates Core content; no form is dropped after approval; all four Quick 033 formulas remain literal; forms remain in the parent's real level/deck ID and outside identity quotas.
6. Recheck the six positive/negative acceptance scenario families, especially current GUID job/rank drift and migration aliases. Ensure the document says the current exporter is a source baseline, not current v4 compliance.
7. Preserve exactly 22 `Moderno` matrix rows and one `Latim isolado` row, all 23 per-language requirement codes, the inactive banner, G0 and all Phase 35-51 headings/dependencies, the 11 graph lines, and all four transverse gate headings.
8. Validate UTF-8 decoding, exactly one final newline, no trailing whitespace, and target-scoped `git diff --check -- docs/multilingual-lexical-adaptive-plan-v4.md`. Do not run broad tests or repository-wide whitespace checks for this static document.

After the target passes, create `C:/Users/MIGUEL~1.RAF/AppData/Local/Temp/opencode/quick-039-after.json` with the identical schema and three worktree exclusions used for the before manifest. Compare the non-task status records, per-path unstaged hashes, and untracked path hashes so the report can name every added, removed, or content-changed non-task/non-workflow path. Separately compare the full cached/index aggregate hashes and per-path maps; equality proves the executor left staged/index state exactly at its baseline regardless of whether that baseline was clean, while a mismatch names the affected staged/index path. Do not assert an empty index.

If non-task/non-workflow data differs, report the exact changed/new/removed paths and which manifest field detected each difference, stop further task-owned editing, and leave all states untouched. Unrelated agents may continue working; do not demand quiescence, revert their changes, absorb them, or attribute them to a specific actor without independent evidence. Keep both manifests outside the repository as execution evidence and narrow the executor claim to its own write scope plus observed fingerprint results.

Finally run diagnostic `git status --short` and confirm the only executor-owned normative path is the target; Quick 039 workflow artifacts may exist separately and LOG is outside executor ownership. The executor must not create UI proof, update LOG, stage, or commit. The outer quick orchestrator performs the required LOG append only after verification, as specified in the handoff below.
  </action>
  <verify>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); expected={"CARD-01","FORM-01","FORM-02","FORM-03","SENSE-01","MWE-01","ROUTE-01","DEF-01","AUDIO-01","LOAD-01","DEPEND-01","GUID-01","ANKI-01","RANK-01","FORM-04","DISPLAY-01","AUDIO-02","AISEC-01","CONTENT-01","EVAL-01"}; ids=re.findall(r"^\| `([A-Z]+-\d{2})` \|",s,re.M); assert len(ids)==20 and set(ids)==expected; patterns=(r"\b12\s+(?:contratos?|ids?|contracts?)\b",r"\btodos?\s+os?\s+12\b",r"\b(?:contratos?|ids?|contracts?)\b(?:\s+(?:normativos?|explícitos?|count))?\s*(?:(?:são|are|is)|:|=)?\s*12\b",r"\b(?:contract|contrato|id)[-_ ]?count\s*(?:(?:is|é)|:|=)?\s*12\b"); stale=[(i,l) for i,l in enumerate(s.splitlines(),1) if any(re.search(p,l,re.I) for p in patterns)]; assert not stale,stale; assert len(re.findall(r"\bD-12\b",s))==1 and s.count("| D-12 |")==1; assert s.count("| 12. Adaptação |")==1; assert "todos os 20" in s.casefold(); assert "notas separadas não são siblings no anki padrão" in s.casefold(); assert "o comportamento atual não satisfaz automaticamente a v4" in s.casefold(); print("contract-count, D-12, flow-12, and topology assertions OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); folded=s.casefold(); assert "core_identity_count = 3000" in s; assert "frequency_card_count = 3000 + N_important_form_cards + O_enabled_optional_role_cards" in s; assert "N_important_form_cards > 0 => frequency_card_count > 3000" in s; assert "frequency_level_card_count = 1000 + N_level_important_form_cards + O_level_enabled_optional_role_cards" in s; assert re.search(r"notas separadas.{0,80}não são siblings",s,re.I|re.S); assert "o conteúdo core é canônico e versionado por edição assinada.".casefold() in folded; assert "é proibido ao histórico do aprendiz regenerar ou mutar conteúdo core compartilhado.".casefold() in folded; assert "a adaptação altera somente queue/module/order/eligibility.".casefold() in folded; assert all(x in s for x in ("job_id","sort_index","Card 1","genanki.Note","<script>","javascript:","xíng","háng","indicativo","irrealis")); print("Quick 033, canonical-history boundary, adaptation allowlist, security, and migration assertions OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import re; from pathlib import Path; s=Path("docs/multilingual-lexical-adaptive-plan-v4.md").read_text(encoding="utf-8"); modern=re.findall(r"^\| Moderno \| ([a-z]{2}) \|",s,re.M); latin=re.findall(r"^\| Latim isolado \| ([a-z]{2}) \|",s,re.M); assert len(modern)==22 and len(set(modern))==22,modern; assert latin==["la"],latin; expected={"pt","es","en","fr","de","it","pl","tr","ro","ru","nl","ko","da","nb","sv","fi","hu","cs","hr","el","ja","zh"}; assert set(modern)==expected; assert s.count("> **ESTADO PRESERVADO — PROPOSTA v4, NÃO ATIVA.**")==1; assert all(s.count(f"### Fase {n}:")==1 for n in range(35,52)); assert s.count("### G0:")==1; print("inactive banner and 22+Latin matrix OK")'</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'from pathlib import Path; p=Path("docs/multilingual-lexical-adaptive-plan-v4.md"); b=p.read_bytes(); s=b.decode("utf-8"); assert not b.startswith(b"\xef\xbb\xbf"); assert s.endswith("\n") and not s.endswith("\n\n"); assert all(line.rstrip()==line for line in s.splitlines()); print("UTF-8/newline/trailing-whitespace OK")'</automated>
    <automated>git diff --check -- "docs/multilingual-lexical-adaptive-plan-v4.md"</automated>
    <automated>PYTHONIOENCODING=utf-8 uv run python -c 'import json; from pathlib import Path; a=json.loads(Path("C:/Users/MIGUEL~1.RAF/AppData/Local/Temp/opencode/quick-039-before.json").read_text(encoding="utf-8")); b=json.loads(Path("C:/Users/MIGUEL~1.RAF/AppData/Local/Temp/opencode/quick-039-after.json").read_text(encoding="utf-8")); map_fields=("non_task_unstaged_path_hashes","non_task_untracked_files","full_cached_path_hashes","full_index_path_hashes"); path_delta={field:{"new":sorted(set(b[field])-set(a[field])),"removed":sorted(set(a[field])-set(b[field])),"changed":sorted(k for k in set(a[field]).intersection(b[field]) if a[field][k]!=b[field][k])} for field in map_fields}; status_delta={"before_only":sorted(set(a["non_task_status_records"])-set(b["non_task_status_records"])),"after_only":sorted(set(b["non_task_status_records"])-set(a["non_task_status_records"]))}; aggregate_delta={field:(a[field],b[field]) for field in ("non_task_status_sha256","non_task_unstaged_diff_sha256","full_cached_diff_sha256","full_index_sha256") if a[field]!=b[field]}; report={"paths":path_delta,"status":status_delta,"aggregate_hashes":aggregate_delta}; assert a==b,report; print("non-task/non-workflow fingerprints and baseline-relative index/staged hashes unchanged")'</automated>
    <automated>git status --short</automated>
  </verify>
  <done>All stale contract-count phrases and contradictory topology/content/form claims are gone; exact IDs, subsection propagation, decisions, examples, formulas, headings/dependencies, gates, matrix, banner, UTF-8/whitespace, and target-scoped Git checks pass. Outside-repo evidence either proves non-task/non-workflow paths plus baseline-relative staged/index state unchanged during the executor window, or reports exact concurrent drift without reversion/attribution and stops further task-owned editing.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Preserved v4 contract -> future schema/export implementation | Ambiguous documentation could prematurely lock an Anki model, unstable identity, or false scheduling guarantee into irreversible persistence. |
| Corpora/surface analyses -> frozen ranks/forms/content | Untrusted, ambiguous, duplicated, or version-drifting evidence could corrupt canonical ranks and mandatory workload. |
| Custom/highlight/corpus/LLM text -> prompts and Anki-rendered fields | Direct/indirect prompt injection, private-data disclosure, and executable HTML/URL output can cross into provider or client contexts. |
| Current one-row/one-note GUID topology -> selected semantic topology | Job/rank-sensitive GUID drift or incorrect aliases can duplicate notes/cards or lose scheduling during migration. |
| Quick 039 edit -> dirty concurrent worktree | Broad editing, cleanup, staging, or restoration could overwrite Quick 033/035-038, template/test, active-v3, or unrelated user work. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q039-01 | Tampering | `ANKI-01` topology/GUID decision | mitigate | Keep both candidates unselected until signed real-client evidence proves note/card identity, updates, scheduling, prerequisites, dynamic forms, and round-trip; block Phase 36. |
| T-Q039-02 | Tampering / Repudiation | `RANK-01`, `FORM-04`, `CONTENT-01` | mitigate | Require checksummed inputs, explicit formulas/thresholds, deterministic tie-breaks, policy/edition versions, diffs, approvals, and reproducible hashes. |
| T-Q039-03 | Information Disclosure / Elevation of Privilege | `AISEC-01` custom/highlight/corpus prompts | mitigate | Require strict trust separation, size/token limits, minimal private context, no secrets, typed outputs, hash-only audit, and no LLM authority over lexical facts. |
| T-Q039-04 | Elevation of Privilege / Tampering | LLM output rendered in Anki fields | mitigate | Context-escape by default or enforce a strict markup allowlist; reject scripts, handlers, executable URLs/markup, and unapproved Anki directives before persistence/export. |
| T-Q039-05 | Spoofing / Tampering | `AUDIO-02` cache | mitigate | Key reuse on the complete versioned pronunciation signature and artifact hash, with explicit heterophone/polyphony negative fixtures. |
| T-Q039-06 | Denial of Service | LLM/audio/form workload | mitigate | Require bounded input/output, rate/concurrency/retry/budget controls and pre-approval workload forecasts without post-approval Core-form truncation. |
| T-Q039-07 | Tampering / Repudiation | Dirty worktree, workflow ownership, and Git index | mitigate | Exclude target, Quick 039 artifacts, and orchestrator-owned LOG from executor worktree fingerprints; compare per-path non-task evidence plus full cached/index hashes; report concurrent path drift without attribution/reversion; prohibit executor restore/stage/commit/LOG edits. |
</threat_model>

## Dependency Analysis

- `039-01` needs the existing preserved document, Quick 033 semantics, locked decisions, and read-only current exporter/GUID facts. It creates the exact 20-contract vocabulary, blocking Anki gate, domain/profile/flow changes, G0/Phase 35 requirements, and acceptance cases.
- `039-02` depends on `039-01` because phase ownership, gates, decisions, and traceability must refer to those exact contracts. It propagates them through later phases without changing the dependency graph.
- `039-03` depends on both prior tasks and is the exhaustive consistency/protected-scope closure gate. All three tasks intentionally share one target file and execute serially.
- No task creates an artifact consumed by active v3.0; v4 remains explicitly inactive.

## Source Coverage Audit

| Source | ID/item | Plan coverage | Status |
|---|---|---|---|
| GOAL | Incorporate all eight reviewed gaps as normative contracts, phases, gates, decisions, and traceability | Tasks 039-01 through 039-03 | COVERED |
| REQ | Quick mode has no active ROADMAP requirement IDs | `requirements: []`; active v3 files are protected | COVERED |
| RESEARCH | No research phase or external selection is authorized | Discovery level 0; evidence-dependent choices remain blocking G0/35 gates | COVERED |
| CONTEXT | Q039-D01 Anki architecture remains unselected with two real-client candidates and honest burying semantics | ANKI-01 in Task 039-01; phase/migration propagation in 039-02; sibling audit in 039-03 | COVERED |
| CONTEXT | Q039-D02 canonical Core edition content versus adaptation/private paths | CONTENT-01 in 039-01; Phases 45/48/49/51 in 039-02; contradiction scan in 039-03 | COVERED |
| CONTEXT | Q039-D03 exact Quick 033 Core/headword/form rules | FORM-04 plus preserved formulas/routes in 039-01/02; exact assertions in 039-03 | COVERED |
| CONTEXT | RANK-01 deterministic rank aggregation and drift | Contract/formula in 039-01; Phase 37/rollouts/freeze in 039-02; scan in 039-03 | COVERED |
| CONTEXT | DISPLAY-01 unambiguous form schema/prompt | Contract and were cases in 039-01; Phases 38/46/49 in 039-02 | COVERED |
| CONTEXT | AUDIO-02 full pronunciation signature, no text-only heterophone reuse | Contract and Mandarin/Japanese cases in 039-01; Phases 38/45/49/51 in 039-02 | COVERED |
| CONTEXT | AISEC-01 prompt injection, privacy, typed output, HTML/Anki safety, budgets, hash audit, non-authoritative LLM | Contract/examples in 039-01; four gates and Phase 49 in 039-02; safety scan in 039-03 | COVERED |
| CONTEXT | EVAL-01 per-language datasets/rubrics, independent review, drift blockers | Contract in 039-01; Phases 39-45/49/51 and quality gate in 039-02 | COVERED |
| CONTEXT | Current one-note-per-row/one-template/single-deck and job/rank GUID migration gap | Baseline facts/examples in 039-01; Phases 46/47/50/51 and migration invariants in 039-02 | COVERED |
| CONTEXT | Exact 20 contracts, ownership allocation, four gates, D-01..D-23, and final audit | Tasks 039-01/02 with exact commands; exhaustive Task 039-03 closure | COVERED |
| CONTEXT | Positive/negative examples: separate notes, be forms, CJK polyphony, injection, scripts, GUID drift | Acceptance table in 039-01 and exact final assertions in 039-03 | COVERED |
| CONTEXT | Preserve inactive banner, active v3, 22+Latin, protected files, dirty work, and correct executor/orchestrator LOG ownership | Hard boundaries, external manifests, Task 039-03 checks, and post-verification handoff | COVERED |

No source item is deferred or unplanned. No unrelated feature is introduced.

<verification>
Execution is authorized only after the outer quick orchestrator receives the exact preview response `proceed despite issues`. Then run every task-level automated command. Treat occurrence listings as review evidence: every match must be read in context, not merely counted. The document must be internally normative but must not claim that any v4 prototype, client behavior, source/provider choice, schema, migration, evaluation run, or release has already occurred. The executor must not run product tests, create UI proof, update LOG, stage, or commit.
</verification>

<handoff>
The executor and verifier do not own `.planning/quick/LOG.md`. After `.planning/quick/039-fechar-gaps-geracao-v4/039-VERIFICATION.md` is persisted and its final status is known, the **outer quick orchestrator is required** to append the single Quick 039 row to `.planning/quick/LOG.md` under the normal quick-workflow Step 6. The orchestrator must then verify that exactly one Quick 039 row/link exists and that its date, final verification status, description, and directory match the persisted workflow artifacts. This post-LOG check occurs after the executor fingerprint window and is an orchestrator obligation, not an executor command or normative-target edit.
</handoff>

<success_criteria>
- The target's normative table contains exactly the original 12 IDs plus the exact eight requested IDs, for exactly 20 unique contracts and no stale 12-contract wording.
- Phase 35 compares both required Anki models without preselection and blocks Phase 36 until real-client identity/update/scheduling/prerequisite/burying-or-alternative/dynamic-form/round-trip evidence selects one.
- RANK-01, FORM-04, DISPLAY-01, AUDIO-02, AISEC-01, CONTENT-01, and EVAL-01 are implementation-ready, versioned, reproducible, fail-closed contracts.
- Positive and negative examples cover separate-note non-siblings, `be/is/was/were`, Mandarin/Japanese polyphony, prompt injection, script/URL markup, and current GUID job/rank drift.
- G0 and all relevant Phase 35-51 deliverables/exits, all four transverse gates, dependencies, capability ownership, D-01..D-23, migration invariants, and final audit are consistent with the exact phase allocation.
- Quick 033's 3000-identity/headword and mandatory same-level form formulas/routing remain literal and cannot be weakened by cost, adaptation, topology, or evaluation language.
- The inactive banner, exact headings/dependencies/graph, 22 modern languages plus isolated Latin, UTF-8/final-newline/no-trailing-whitespace, and target-scoped `git diff --check -- docs/multilingual-lexical-adaptive-plan-v4.md` all pass.
- Executor before/after manifests match for non-task/non-workflow paths and full staged/index hashes; if unrelated concurrent drift occurs, exact changed/new/removed paths are reported and further task-owned editing stops without reversion, absorption, or unsupported attribution.
- The full-ceremony advisory is shown and `proceed despite issues` is explicitly received before execution; the plan remains one target and three tasks without an in-plan workflow switch.
- No source implementation, UI proof, stage, or commit is performed. The executor does not update LOG; the outer quick orchestrator appends and verifies exactly one Quick 039 LOG row after verification.
</success_criteria>
