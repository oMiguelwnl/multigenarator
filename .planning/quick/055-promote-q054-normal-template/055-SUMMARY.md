# Quick Task 055 Summary: Promote Q054 Normal Template

## Status

Completed and focused verification passed.

## Changes

- Promoted the approved Q054 layout into `src/multilang/templates/normal_card.md`.
- Updated normal template contract tests in `tests/services/test_card_template_loader.py`.
- Updated export model CSS assertions in `tests/services/test_export_anki_package.py`.

## Implemented Contract

- Black page/card theme remains active through the normal template CSS variables.
- The Anki `.card` container now uses top placement with `padding: 16px 12px 12px`, horizontal centering, and `align-items: flex-start`.
- Normal card width is constrained to `680px` through `#qa` and `.customCard`.
- Card padding is `32px 40px` on desktop.
- The `<=720px` layout keeps 12px outer horizontal gutters with `.customCard { width: calc(100vw - 24px); padding: 24px 20px; }`.
- Word and sentence audio controls are fixed into `32px` columns with grid rows.
- Definition, target word, example sentence, and translation text remain left-aligned/LTR with natural wrapping and no horizontal scroll rule.

## TDD Evidence

Red command:

```bash
uv run pytest tests/services/test_card_template_loader.py::test_normal_frequency_template_uses_production_dark_layout_contract tests/services/test_export_anki_package.py::test_build_multilang_model_uses_project_card_template_sections -q
```

Result: expected failure before the template edit, proving the old template still had `display: block`, `--max-width-card: none`, old full-width sizing, and old mobile padding.

Green command:

```bash
uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py::test_build_multilang_model_uses_project_card_template_sections tests/integration/test_v13_normal_template_export_contract.py::test_normal_apkg_omits_front_of_card_and_exports_responsive_sentence_layout -q
```

Result: `29 passed in 5.94s`.

## Notes

- Existing front/back HTML, field references, field order, and translation reveal script were preserved.
- No native Anki screenshot/runtime proof was newly generated in this quick task; the visual target was the previously approved Q054 dummy APKG.
- The repository already had many unrelated dirty tracked/untracked files before this task; this task only intentionally changed the files listed above and added this quick task directory.
