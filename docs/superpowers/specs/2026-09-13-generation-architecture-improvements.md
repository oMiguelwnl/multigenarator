# Generation quality and modular architecture

The user approved implementation of the architecture review recommendations on
2026-09-13 and explicitly requested no GSD/GSDD workflow. This specification
records that scope; no additional design approval is required for the same work.

## Outcomes

1. A frequency seed without lexical evidence never becomes `GROUNDED` merely
   because an LLM returned text. Ambiguous source senses remain unresolved.
2. Definition generation receives source meaning, source language, target language,
   POS and source sense when available. Generated meaning is checked against its
   evidence; formatting and language checks alone never establish semantic truth.
3. Source fallback preserves actual language, source and fallback reason. An
   unavailable target-language fallback becomes review-required, not mislabeled.
4. Definition calls share bounded retries, cache, call logging and circuit-breaker
   controls. Prompt/schema/source changes invalidate cached results. Explicit
   request timeouts and output limits apply. No live paid calls during this task.
5. Native strict-i+1 can validate 3000 known concepts without sending thousands of
   opaque identifiers to the provider. The full set remains authoritative locally;
   provider prompt construction uses a bounded projection and is independently
   limited. No truncation of the local validation set.
6. The CLI and services are organized into modules by responsibility, preserving
   supported import paths, monkeypatch seams, command names/options, Anki fields,
   note identities and persisted hashes. Explicit transaction ownership protects
   composition of legacy repositories without removing standalone behavior.
7. CI checks every Python source/test file for the project's existing Ruff rules.
   Offline regression/evaluation cases exercise wrong meaning, wrong language,
   missing source, ambiguity and correctly recorded recovery. Synthetic evidence
   is never represented as human approval, a production deck or language licensing.

## Implementation decisions

- Evolve the current Python monolith. Introduce no database server, queue service,
  LLM library or external dependency. Reuse Pydantic, LiteLLM, SQLAlchemy and pytest.
- Use a source-backed definition service with typed input/output and explicit
  quality decisions. Semantic review may suggest acceptance but cannot mint human
  approval. Missing or inconclusive evidence fails closed in production paths.
- Keep HTML formatting at the export boundary. Keep source identity and review
  metadata out of student-facing Anki fields.
- Preserve Korean identity/privacy/review controls and existing Latin isolation.
- Implement compatibility adapters while relocating cohesive services. Package
  entry points have no eager network/model/database side effects.
- Preserve ongoing qualification work. Baseline copies/hashes and the original
  index status are under `.multilang/verification/generation-improvements/`.
- Work on the existing feature checkout to include its current functionality;
  do not reset, stash, stage unrelated files, merge, deploy or migrate a real DB.

## Acceptance evidence

Each behavioral change needs a regression observed failing before implementation,
then passing. Run affected integration/export tests, all Ruff checks, distribution
build and documentation checks. Run the offline regression suite with bounded
timeouts and separate expensive suites when appropriate. Report preexisting or
concurrent failures accurately. Preserve the plan and implementation record.

## Human evidence boundary

This task delivers software and evaluation mechanisms. It does not fabricate a
human-reviewed lexical gold set, approve redistribution, certify Anki clients or
spend on providers. The concurrent linguistic qualification workflow remains the
source of real review artifacts. Any remaining real-world validation is listed
explicitly in the implementation record.
