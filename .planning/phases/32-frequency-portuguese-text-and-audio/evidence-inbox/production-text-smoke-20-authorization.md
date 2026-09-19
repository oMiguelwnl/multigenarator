# Production text smoke authorization

This records the explicit authority supplied by the user in the current session. It is deliberately narrow and does not inherit or grant any later production power.

```json
{
  "authority_kind": "production-text-smoke",
  "authority_stage": "pilot_base",
  "authorized_item_count": 20,
  "unit_count": 2,
  "max_items_per_unit": 10,
  "job_id": "phase32-prod-text-smoke-20",
  "language": "ko",
  "source_type": "frequency",
  "model": "gpt-4.1-mini",
  "text_provider": "litellm-openai",
  "translation": "deepl-api-PT-BR",
  "max_attempts": 2,
  "max_concurrency": 1,
  "fallback": "none",
  "missing_only": true,
  "audio": false,
  "azure_allowed": false,
  "review_application_allowed": false,
  "export_allowed": false,
  "release_allowed": false,
  "publication_allowed": false,
  "delivery_allowed": false,
  "full_run_authorized": false,
  "maximum_total_items_authorized": 20,
  "terminal_state": "wait_for_user_before_3000_item_execution"
}
```

No 21st item, intermediate pilot, 3000-item operation, Azure or audio action, review application, export, release, publication, delivery, Git action, or Phase 32 closure is authorized. A successful smoke requires a fresh explicit user confirmation immediately before any 3000-item provider execution.
