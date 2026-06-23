# Quick Task Plan: Fix Phoneme Tablet Audio Icon

## Objective
Fix the tablet-only Russian phoneme card layout where a custom CSS play triangle appears alongside the Anki native audio button and overlaps nearby card content.

## Task 1: Remove Duplicate Custom Audio Glyph

<files>
- `src/multilang/templates/russian_phoneme_card.md`
</files>

<action>
Replace the phoneme template's custom `.replay-button::before` triangle and hidden SVG behavior with native Anki replay SVG styling, matching the safer pattern already used by normal/Latin card templates.
</action>

<verify>
- `uv run pytest tests/services/test_russian_phoneme_deck.py tests/integration/test_russian_phoneme_template_refresh_flow.py`
</verify>

## Task 2: Add Regression Coverage

<files>
- `tests/services/test_russian_phoneme_deck.py`
</files>

<action>
Assert that the phoneme CSS no longer injects a pseudo-element play triangle or hides the native replay SVG, while preserving audio field references.
</action>

<verify>
- `uv run pytest tests/services/test_russian_phoneme_deck.py tests/integration/test_russian_phoneme_template_refresh_flow.py`
</verify>

## UI Proof Slots

```json
{
  "slot_id": "phoneme-tablet-audio-icon",
  "claim": "Phoneme card CSS no longer creates a second play arrow beside the Anki native audio button.",
  "route_state": "Generated Russian/Polish phoneme Anki card front template with audio fields",
  "required_evidence_kinds": ["code", "test"],
  "minimum_observations": 2,
  "expected_artifact_types": ["template_css", "pytest_output"],
  "validation_command": "uv run pytest tests/services/test_russian_phoneme_deck.py tests/integration/test_russian_phoneme_template_refresh_flow.py",
  "environment": "local pytest; no live tablet renderer available in workspace",
  "viewport": "tablet issue inferred from provided screenshot; code-level prevention targets Anki replay markup across viewports",
  "manual_acceptance_required": true,
  "claim_limit": "Does not prove final AnkiDroid rendering on a physical tablet; validates removal of the duplicate CSS-generated arrow cause."
}
```
