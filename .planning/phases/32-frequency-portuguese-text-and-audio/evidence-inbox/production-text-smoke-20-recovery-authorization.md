# Production text smoke recovery authorization

This sidecar records the user's explicit `Autorizar retry` decision for one contained recovery invocation of the existing job. It supplements, and does not replace or rebind, the original job authority.

```json
{
  "authority_kind": "production-text-smoke-recovery",
  "decision": "Autorizar retry",
  "job_id": "phase32-prod-text-smoke-20",
  "authorized_ranks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
  "original_result_sha256": "d512dd36cf528eb7d6904a0e1459b44d7b4916e5895ac7cd48f5f1433be914e8",
  "recovery_invocations": 1,
  "max_attempts_per_operation": 2,
  "unit_1_max_items": 10,
  "unit_2_gate_text_records": 10,
  "missing_only": true,
  "audio": false,
  "fallback": "none",
  "full_run_authorized": false,
  "terminal_state": "wait_for_user_before_3000_item_execution"
}
```

No second recovery invocation, altered provider/model/budget, replacement or 21st candidate, audio/Azure action, review application, export, release, publication, delivery, Git action, or 3000-item execution is authorized.
