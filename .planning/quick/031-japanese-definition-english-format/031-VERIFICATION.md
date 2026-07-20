# Quick Task 031 Verification: Japanese Definition English Format

## Verdict

Passed.

## Goal Check

The Japanese frequency pipeline now has an explicit definition format template requiring English labels and English meanings. Japanese POS labels such as `名詞:` are rejected for Japanese export rows, while non-Japanese decks keep their existing behavior.

## Evidence

- `provider_text_adapters._definition_prompt()` includes Japanese-specific English-format rules.
- `AssembleExportCardsService` uses the stricter English label template when `deck_language` is `SupportedLanguage.JA`.
- Focused tests passed, including rejection of `名詞: father` for Japanese rows.

## Remaining Gaps

- None.
