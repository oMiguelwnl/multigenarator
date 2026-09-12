# Multilingual completion: approved implementation design

The user explicitly approved implementing all previously described remaining work
and proposals on 2026-09-12. This continues the native v4 feature branch and the
requirements in `info1.md`, `info2.md`, and the v4 master contract. No GSDD commands
or operational `.planning` dependencies. No deployment, as explicitly requested.

## Product contract

An identity is language + preserved normalized lemma + POS + source-backed sense.
Observed inflections remain separate surface forms. Approved important forms
produce cards displaying that exact form, its contextual meaning and analysis,
and matching audio, in the parent's level. Core contains 3000 identities and
3000 headword cards per modern language, with all approved form cards additional.
The 22 modern languages are pt/es/en/fr/de/it/pl/tr/ro/ru/nl/ko/da/nb/sv/fi/hu/cs/hr/el/ja/zh.
Classical Latin remains isolated. Existing per-language Anki fields and templates
are compatibility contracts; prototype Front/Back fields are insufficient.

User clarification during execution: preserve the exact existing field names
and order for each current card model. Do not rename/remove existing fields or
append metadata fields. Lexical/form linkage belongs in the database and package
manifest. A topology whose storage requires changing that field contract cannot
be silently adopted; retain it only as an explicitly experimental comparison.

## Implementation boundaries

1. Preserve field-based Anki exports, meanings, morphology, images, exact audio,
   safe templates, stable semantic IDs and the A/B evidence requirement. Actual
   Anki client acceptance is reported separately from package inspection.
2. Add source catalog and reproducible audits of legacy frequency assets, source
   and model availability, rights, provenance, coverage and unresolved entries.
3. Implement local contextual analyzer adapters and model preparation for all
   modern profiles: Stanza, existing Kiwi, Fugashi/UniDic and Mandarin tooling.
   Analyzers provide morphology; sense IDs require lexical evidence. Unknown or
   ambiguous data is quarantined, never silently accepted or guessed by an LLM.
4. Add bounded corpus/dictionary ingestion and vocabulary preparation with
   immutable manifests, source evidence, ranking inputs, forms, evaluation and
   workload forecasts. Integrate the CLI and existing runtime instead of adding
   an unrelated application. Real source extraction is distinct from approval.
5. Exercise real local models and source data where accessible, persist evaluation
   artifacts, and prepare review material. Download/package rights and access
   must be checked. Independent review must be real, not synthetic receipts.
6. Verify PostgreSQL backup/restore with disposable local databases when available,
   verify distribution and affected tests, and document actual remaining external
   requirements. Real database migration requires a concrete, hash-bound preview.

## Authorizations and boundaries

Continue in the explicitly requested feature branch and preserve existing user
changes, index entries and local assets. Downloads are necessary to the task;
sandbox escalation must be requested through the tool if required. API costs
require a concrete bounded forecast and an explicit budget before paid bulk jobs.
Do not invent human language reviews, redistribution decisions or device results.
Do not activate unqualified profiles. These are requirements, not implementation
shortcuts. Finish all independent implementable work before reporting a blocker.
