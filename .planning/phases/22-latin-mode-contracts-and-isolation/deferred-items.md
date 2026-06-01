# Deferred Items - Phase 22

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Pre-existing focused CLI test drift | `tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters` expects `fallback_audio_items=1`, but the runtime output omits that counter in the first run. This failure is unrelated to the Latin contracts/CLI changes and was not modified under the Phase 22 scope boundary. | Deferred for existing audio/runtime CLI drift repair | Plan 22-02 verification, 2026-06-01 |
