# Quick Task Summary: Fix Phoneme Tablet Audio Icon

## Status
Completed with wrapper-timeout caveat on verification output.

## Changes
- Updated `src/multilang/templates/russian_phoneme_card.md` so phoneme cards no longer hide Anki's native replay SVG or draw an extra `.replay-button::before` triangle.
- Kept replay button sizing and color styling for native Anki SVG markup.
- Added regression assertions in `tests/services/test_russian_phoneme_deck.py` to prevent reintroducing the CSS-generated duplicate play icon.

## Verification
- Command: `uv run pytest tests/services/test_russian_phoneme_deck.py tests/integration/test_russian_phoneme_template_refresh_flow.py`
- Result printed by pytest: `10 passed in 118.47s`
- Caveat: the shell wrapper reported a timeout after the pytest summary because the command completed at the 120s boundary.

## Notes
- The Russian and Polish phoneme decks share this template, so both receive the fix.
- No card fields, audio references, or export APIs were changed.
