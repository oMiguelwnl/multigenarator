# Phase 7 Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| test-drift | `uv run pytest tests -q` fails during collection because `tests/test_runtime.py` and `tests/test_runtime_templates.py` import removed private symbols `_TemplateSentenceAdapter` / `_TemplateTranslationAdapter` from `multilang.runtime`. This was discovered after Phase 7 documentation/evidence changes and is unrelated to the edited planning artifacts. | deferred | 2026-04-29 Phase 7 regression gate |
