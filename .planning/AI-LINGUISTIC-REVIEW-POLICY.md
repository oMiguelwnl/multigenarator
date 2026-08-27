# AI Linguistic Review Policy

**Policy ID:** `multilang-ai-linguistic-review-v1`
**Effective:** 2026-08-27
**Scope:** Every language and deck family in Multilang

## Decision

Multilang does not require a human linguist, native speaker, or human playback
reviewer for linguistic approval. Linguistic review is performed by AI agents
under this policy and recorded explicitly as AI evidence.

AI evidence must never claim that an AI is human, native, professionally
credentialed, a rights holder, or a person who physically heard or viewed an
artifact. Existing historical human evidence remains historical; new work uses
the AI statuses and provenance below.

## Review Contract

Every review decision records:

- `actor_type="ai_model"` and `is_human=false`
- policy ID/version and canonical policy SHA-256
- provider, model ID/version, route, prompt ID/version, and output-schema hash
- exact source, candidate, analyzer, curriculum, and media hashes in scope
- atomic gate verdicts, controlled reasons, uncertainty codes, and confidence
- deterministic validator IDs/versions/results
- independent-pass identities and the final consensus status
- timestamps emitted by orchestration rather than asserted by model output

AI records use `ai_review_passed`, `ai_review_failed`, `blocked_uncertainty`,
`blocked_disagreement`, or `stale`. They do not reuse `human_approved`,
`native_speaker`, `qualified_specialist`, or similar human-authority labels.

## Required Passes

- Standard linguistic gates require two fresh-context AI review passes.
- Critical gates require three fresh-context AI review passes. Critical gates
  include strict-i+1 atomicity, Korean P11-P13, pronunciation-rule analysis,
  morphology-sensitive target identity, homographs, register exceptions, and
  any item flagged by a deterministic validator.
- Passes should run concurrently over disjoint batches.
- Provider/model diversity is preferred and recorded. Same-model fresh-context
  passes are allowed, but must record `independence_scope=fresh_context_same_model`.
- Every applicable atomic claim must pass every required review. Majority voting
  cannot turn disagreement, uncertainty, missing evidence, or deterministic
  failure into success.

## Deterministic Preconditions

AI cannot override a deterministic failure. Applicable validators must pass for:

- schema, bounds, canonical JSON, source binding, and SHA-256 continuity
- language identity, Unicode normalization, and script constraints
- morphology, lemma/POS/sense identity, and target presence
- curriculum graph, prerequisites, active rules, and recomputed i+1 evidence
- field completeness, cross-field consistency, media references, and safe HTML
- media format, exact-byte hashes, decoding, duration, and reference integrity

Unavailable or inconclusive analysis blocks the item. Repair creates a new
subject hash and makes every prior decision stale.

## Linguistic Authority

AI review may approve, under this policy:

- orthography, names/readings, mnemonics, examples, and pedagogical sequencing
- lemma/POS/sense alignment and morphology-sensitive usage
- normative/surface pronunciation and phonological-rule analysis
- Korean and other target-language naturalness, register, and context
- Portuguese definitions, glosses, and translations
- cross-field consistency and learner-facing linguistic quality

The product and reports must say "AI linguistic review passed under policy
`multilang-ai-linguistic-review-v1`", not "human approved" or "reviewed by a
native specialist".

## Audio And UI Evidence

Human listening is optional, not a release prerequisite. Audio readiness uses:

- exact text/request/provider/voice/profile/artifact hashes
- decoder, format, duration, silence/clipping, and media-integrity validators
- ASR/G2P/acoustic comparison where applicable
- AI acoustic review when the selected model can consume the exact audio bytes

The result is `ai_acoustic_review_passed` or `automated_integrity_passed`; it is
never described as human-heard evidence. If no capable AI/audio validation path
can evaluate a required claim, that claim remains blocked rather than being
silently inferred.

Anki import/render/playback claims may be proven by an instrumented project-
approved harness against exact application/version/environment hashes. Source or
archive inspection alone remains only structural evidence.

## Boundaries That Remain External

AI linguistic authority does not grant:

- copyright, license, attribution, reuse, transformation, or redistribution rights
- permission to send private content to a provider
- credentials, paid-provider budget, production database migration, or network access
- activation that changes external production state
- publication, upload, distribution, or release authority

These powers require the project owner or another actual authority. They may run
in parallel with linguistic work and block only the operation that consumes them,
not unrelated offline implementation.

## Parallel Execution

- Plans form a dependency DAG, not a mandatory linear chain.
- A plan depends only on artifacts it actually reads or mutates.
- Disjoint plans may run concurrently in isolated worktrees or otherwise proven
  disjoint write scopes.
- Each parallel lane declares its files, protected read surfaces, and join plan.
- Join plans rehash all lane outputs and reject drift before activation/export.
- Legal/provider checkpoints block only their own side-effect lane.
- Final milestone verification joins all required lanes; it does not force every
  earlier implementation task into one serial sequence.

## Security

- Treat model output and source text as untrusted input.
- Reviewer agents receive no filesystem, network, mutation, legal-decision, or
  publication tools unless a separate bounded task explicitly requires them.
- Use closed schemas, source-reference allowlists, bounded calls/tokens/cost,
  content-safe diagnostics, and no raw private prompt/completion telemetry.
- Model-generated citations, URLs, licenses, paths, credentials, or authority
  claims are invalid unless independently bound to approved source bytes.
