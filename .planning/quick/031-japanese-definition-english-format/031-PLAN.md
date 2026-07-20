# Quick Task 031 Plan: Japanese Definition English Format

## Objective

Make the Japanese frequency deck's `Definition` format explicit: English part-of-speech label plus English meaning, not Japanese POS labels.

No UI proof rationale: this task changes generation/validation rules and tests, not rendered app UI.

## Task 1: Add Explicit Provider Format Rules

<files>
- `src/multilang/services/provider_text_adapters.py`
- `tests/services/test_provider_text_adapters.py`
</files>

<action>
- Add Japanese-specific definition prompt rules requiring English POS labels and English meanings.
- Add a test proving the prompt rejects Japanese labels like `名詞` and gives English examples.
</action>

<verify>
- `uv run pytest tests/services/test_provider_text_adapters.py::test_litellm_definition_prompt_for_japanese_requires_english_format -q`
</verify>

## Task 2: Enforce English Definition Labels At Export

<files>
- `src/multilang/services/assemble_export_cards.py`
- `tests/services/test_assemble_export_cards.py`
</files>

<action>
- Restrict the definition template validator to canonical English POS labels plus `term`.
- Add a test proving Japanese labels like `名詞: 父` are rejected.
</action>

<verify>
- `uv run pytest tests/services/test_assemble_export_cards.py::test_assemble_export_cards_rejects_non_english_definition_label -q`
</verify>
