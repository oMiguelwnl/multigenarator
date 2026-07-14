# Quick Task 016 Plan: German Etwas Pronoun

## Objective

Fix German definition label inference so `etwas` is treated as a pronoun rather than falling back to neutral `term:`.

## Task 1: Add German Indefinite Pronoun Inference
<files>
- `src/multilang/services/text_field_remediation.py`
- `tests/services/test_text_field_remediation.py`
</files>
<action>
Add `etwas` to the deterministic German pronoun inference map and update remediation tests so unlabeled `etwas` definitions become `pronoun: ...` while unrelated unknown words still fall back to `term:`.
</action>
<done>
`etwas` is normalized to `pronoun:` in definition remediation.
</done>
<verify>
Run `uv run pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py -q`.
</verify>

## No UI Proof Rationale

This task changes backend definition label inference only and has no rendered UI surface.
