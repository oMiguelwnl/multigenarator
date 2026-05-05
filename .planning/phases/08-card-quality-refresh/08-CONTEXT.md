# Phase 08: Card Quality Refresh - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning
**Source:** `total.md`

<domain>
## Phase Boundary

This phase updates generated non-phonetics Anki cards so the headword audio is more prominent, every generated card shows AI-generated IPA plus a spoken-form hint, and the deck CSS matches the user-provided blue style in `total.md`.

</domain>

<decisions>
## Decisions

### D-01 — Make `word_audio` more prominent with the voice service
The user wants `word_audio` to be more highlighted/prominent and explicitly said to research how to do this through the speech service. Implement the prominence in Azure Speech SSML for word audio generation.

### D-02 — Show spoken form beside IPA on every generated card
For all generated cards, the IPA display must include the readable spoken form next to the IPA value.

### D-03 — Generate IPA with AI for every generated card
Kaikki IPA is considered wrong by the user and must not be trusted as the final exported IPA. AI must generate IPA for every generated card.

### D-04 — Apply the provided deck CSS only to the normal card template
Change the deck styling to the CSS supplied in `total.md`. This CSS is not the template for the phonetics deck, so do not modify `src/multilang/services/russian_phoneme_deck.py` for this styling change.

## the agent's Discretion

- Choose the exact AI adapter shape and deterministic test stubs, using the existing LiteLLM/provider-adapter style.
- Choose storage details needed to preserve generated spoken forms across persistence and export.

</decisions>

<canonical_refs>
## Canonical References

- `total.md` — User-supplied requirements and exact CSS source for D-01 through D-04.
- `CARD_TEMPLATE.md` — Normal Anki deck template to update for D-04.
- `src/multilang/services/russian_phoneme_deck.py` — Must remain untouched by D-04.
</canonical_refs>

<deferred>
## Deferred Ideas

None.
</deferred>

---

*Phase: 08-card-quality-refresh*
