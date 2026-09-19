# Definition contract implementation plan

> **For agentic workers:** Execute inline with `superpowers:executing-plans`; use TDD and a final independent review.

**Goal:** Implement the user's approved Definition improvements: one selected sense, a common learner format, explicit lexical evidence and definition/example consistency.

**Architecture:** Share a versioned definition policy between legacy and native generation. Select meanings from source-declared sense mappings, bind native evidence to the persisted lexical identity, and use a strict advisory checker for the exact definition/example pair. Keep existing independent approval gates.

**Tech Stack:** Existing Python/Pydantic/provider cache/retry services; no new dependencies.

**Spec:** User-approved analysis in this conversation, 2026-09-19.

## Constraints and decisions

- No GSD. Work on the existing uncommitted implementation; do not commit or revert other work.
- Do not run Korean tests or modify Korean-specific pipelines. Keep their identity/approval contracts.
- Preserve historical request serialization/hashes when new optional evidence is absent.
- Keep explicit language policies per profile; standardize definition structure without relabelling existing text.
- Missing or ambiguous lexical evidence must not be guessed. An AI consistency verdict never supplies source/human approval.
- All verification is offline with fake providers.

## Tasks

- [x] Shared policy and source selection: test one-sense mappings, ambiguity, wrong POS, circular definitions and unsafe/multiline output; implement bounded evidence and common prompt/validation; invalidate changed definition prompt caches.
- [x] Native wiring: test canonical identity/evidence binding, spoofed context, missing evidence before provider, historical hashes, shared prompt and output validation. Resolve the exact lemma/POS/sense/source from the configured lexical cache for new generic generation.
- [x] Exact definition/example check: test consistent/mismatch/uncertain, strict verdict parsing, cache separation, rate limits and runtime wiring. Use bounded provider calls and existing telemetry for traditional generation; preserve native pending-review status.
- [x] Run affected suites, fix regressions, review the scoped changes and document the contract and migration behavior.

## Review focus

- Same spelling with different source senses must not select the first record.
- A matching word in a sentence does not establish semantic consistency.
- New fields must not silently invalidate old signed content.
- Provider output must not select its own POS/source/approval.
- Existing Korean and Latin specialized contracts must remain separate.

## Verification record

- TDD: initial 15 definition tests failed before implementation; native6 and consistency6 also failed before wiring. Source admission circular/HTML2, source snapshot3 and validator Unicode/circular6 regressions were reproduced before fixes.
- Main affected suite: 162 passed, 38 deselected (Korean/real-Kiwi excluded), `.multilang/verification/definition-contract-final.xml`.
- Lexical/validation/assembly/runtime suite: 108 passed, 51 deselected (Korean/real-Kiwi and preexisting Korean grammar contract test excluded), `.multilang/verification/definition-integration-final.xml`.
- Independent read-only review found source snapshot binding, Unicode line separators and circular article/infinitive definitions. All were fixed with regressions; reviewer confirmed the fixes.
- Final targeted suite: 37 passed, including frequency audio/export, both native dictionary/qualification edition paths, single-item CLI regeneration and trailing Unicode separator regressions; `.multilang/verification/definition-e2e-final.xml`.
- Ruff and scoped `git diff --check` passed on changed code/tests. All provider calls were synthetic/offline; no live linguistic quality pilot or Korean suite was run.

## Scoped commit verification

- Verified the selected commit in an isolated snapshot of HEAD, excluding unrelated audio, Korean pipeline and generation-lease work.
- 278 distinct targeted tests passed after updating synthetic orchestration fixtures to declare their mechanical-validation scope; no unresolved failures. Production semantic-checker wiring remains covered by dedicated tests.
- Scoped Ruff and patch whitespace checks passed. Commit verification artifacts: `.multilang/verification/definition-commit-20260919/`.
