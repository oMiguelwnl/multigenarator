# Phase 4: Audio Synthesis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `04-CONTEXT.md`.

**Date:** 2026-04-24
**Phase:** 04-audio-synthesis
**Areas discussed:** Scope and persistence, Synthesis gating, Voice and fallback policy, TTS input normalization

---

## Scope and persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Separate audio boundary | Persist audio in its own records and keep export formatting out of Phase 4. | ✓ |
| Extend text records | Store audio fields directly inside Phase 3 text records. | |
| Export-first audio | Skip an internal audio layer and only solve audio at export time. | |

**User's choice:** Separate audio boundary
**Notes:** Word and sentence audio should be generated and persisted as their own lifecycle artifacts, with one stable record per `(job_id, item_key, asset_kind)`.

---

## Synthesis gating

| Option | Description | Selected |
|--------|-------------|----------|
| Accepted text only | Generate audio only for cards whose Phase 3 text is accepted. | ✓ |
| Generate for all text | Synthesize even for review-required text to maximize coverage. | |
| Planner decides | Leave the gating policy open for planning. | |

**User's choice:** Accepted text only
**Notes:** Phase 4 should not spend synthesis work on weak text that the product would not ship yet.

---

## Voice and fallback policy

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit Azure fallback | Preferred voice, same-locale fallback, approved alternate locale, then fail visibly. | ✓ |
| Best-effort fallback | Let the runtime pick any available Azure voice. | |
| No fallback | Only one preferred voice per language. | |

**User's choice:** Explicit Azure fallback
**Notes:** Fallback behavior must be deterministic and persisted in provenance, with no silent omission of missing audio.

---

## TTS input normalization

| Option | Description | Selected |
|--------|-------------|----------|
| Separate `tts_text` | Keep synthesis input separate from the visible card text. | ✓ |
| Reuse display text | Always synthesize from the exact learner-facing field value. | |
| SSML everywhere | Require full SSML authoring for every item immediately. | |

**User's choice:** Separate `tts_text`
**Notes:** Phase 4 may normalize or wrap synthesis input for Azure safely, but that should not rewrite what the learner sees on the card.

---

## the agent's Discretion

- Exact repository/API names and schema column names.
- Exact storage directory structure and filename template.
- Exact CLI summary wording for audio counters and fallback diagnostics.

## Deferred Ideas

- Secondary TTS providers after Azure-first synthesis is stable.
- Rich SSML tuning after the baseline voice matrix is verified.
- Final Anki export formatting in Phase 5.
