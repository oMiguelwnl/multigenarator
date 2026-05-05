# Phase 08: Card Quality Refresh - Research

## Question

How should Multilang implement the user-requested audio prominence, AI-generated pronunciation, and card-style changes without reducing existing export guarantees?

## Findings

### Azure Speech word-audio prominence

Azure Speech supports SSML customization with the `prosody` element. Microsoft documentation states that SSML can adjust pitch, pauses, pronunciation, speaking rate, volume, voices, styles, and languages. The `prosody` element supports `pitch`, `rate`, and `volume`; the synthesizer may treat values as suggestions and limit unsupported extremes.

Recommended implementation for this phase:

- Apply prominence only to `AudioAssetKind.WORD` assets per D-01.
- Wrap the headword text with `<prosody rate="-10%" pitch="+8%" volume="+20%">...</prosody>` before sending to Azure.
- Preserve regular sentence audio SSML unchanged so sentence rhythm remains natural.
- Update the Azure adapter so existing SSML fragments are not flattened into plain text; the current implementation extracts only text and would discard `<prosody>` tags.

### AI-generated IPA and spoken form

The existing code uses `LiteLLMSentenceAdapter` for structured JSON. Reuse this provider-adapter pattern for pronunciation generation:

- Add a pronunciation adapter that requests JSON with exact keys `ipa`, `spoken_form`, and `uncertainty_notes`.
- Ground the request with language, display form, lemma, and definitions.
- In lexical grounding, AI-generated pronunciation replaces Kaikki IPA as the card output per D-03.
- Keep Kaikki IPA only as provenance/context if useful; do not export it as the final card IPA.

### Spoken form export

The current `AssembleExportCardsService._render_ipa()` derives a rough hint from IPA. D-02 requires spoken form on every generated card, so the spoken form should be an explicit generated/persisted field, not an inferred best-effort fallback.

Recommended display format in the existing `IPA` field:

```text
/ipa/ (spoken-form)
```

### Deck CSS

`CARD_TEMPLATE.md` is the normal Anki card template consumed by `export_anki_package.py`. The user-provided CSS applies to this template only. Do not update `src/multilang/services/russian_phoneme_deck.py`.

## Validation Architecture

- Unit tests for word-only SSML prosody and Azure adapter preservation of `<prosody>`.
- Unit tests for deterministic AI pronunciation adapter parsing and grounding replacement of Kaikki IPA.
- Repository/export tests proving `spoken_form` persists and the exported `IPA` field contains `/ipa/ (spoken-form)`.
- Template/package tests proving the normal model CSS contains user-provided values and the phonetics deck file is unchanged.
